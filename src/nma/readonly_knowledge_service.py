from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable

from nma.graphrag import _bounded_value, _query_terms
from nma.neo4j_retrieval_v028 import load_live_projection_v028, open_neo4j_driver
from nma.retrieval_v06 import (
    CitationIntegrityGraphRetrieverV06,
    load_citation_source_registry,
)


KNOWLEDGE_SERVICE_CONTRACT = "nma.readonly-knowledge-service/0.33"
RETRIEVE_EVIDENCE_OPERATION = "retrieve_evidence"
MAX_QUERY_CHARACTERS = 4_000
MAX_SEED_IDS = 12
MAX_DEPTH = 3
MAX_NODES = 300
MAX_RANKED_TRACE_RECORDS = 100
MAX_EDGE_SCAN_PER_NODE = 5_000

READ_NODES_CYPHER = """UNWIND $node_ids AS node_id
MATCH (node:NMAEntity {id: node_id, graph_revision: $graph_revision})
RETURN node.id AS id,
       node.entity_type AS entity_type,
       node.properties_json AS properties_json,
       node.source_graphs AS source_graphs
ORDER BY id
"""

READ_INCIDENT_EDGES_CYPHER = """MATCH (focus:NMAEntity {id: $node_id, graph_revision: $graph_revision})
MATCH (focus)-[rel]-(other:NMAEntity {graph_revision: $graph_revision})
WHERE rel.graph_revision = $graph_revision
WITH startNode(rel) AS source, rel, endNode(rel) AS target
RETURN source.id AS source,
       source.entity_type AS source_type,
       source.properties_json AS source_properties_json,
       source.source_graphs AS source_source_graphs,
       type(rel) AS relationship_type,
       rel.nma_key AS relationship_key,
       rel.properties_json AS relationship_properties_json,
       rel.source_graphs AS relationship_source_graphs,
       target.id AS target,
       target.entity_type AS target_type,
       target.properties_json AS target_properties_json,
       target.source_graphs AS target_source_graphs
ORDER BY relationship_type, source, target, relationship_key
LIMIT $row_limit
"""

READ_ONLY_CYPHER_TEMPLATES = {
    "read_nodes": READ_NODES_CYPHER,
    "read_incident_edges": READ_INCIDENT_EDGES_CYPHER,
}

_MUTATION_TOKEN = re.compile(
    r"\b(CREATE|DELETE|DETACH|DROP|FOREACH|LOAD\s+CSV|MERGE|REMOVE|RENAME|SET)\b",
    re.IGNORECASE,
)


class ReadOnlyKnowledgeServiceError(RuntimeError):
    """A bounded Knowledge Service request could not be completed safely."""


class KnowledgeServiceConfigurationError(ReadOnlyKnowledgeServiceError):
    """The Knowledge Service cannot activate with the supplied configuration."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _graph_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _normal_nodes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(graph["nodes"], key=lambda item: item["id"])


def _normal_edges(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        graph["edges"],
        key=lambda item: (
            item["type"],
            item["source"],
            item["target"],
            _canonical_json(item.get("properties", {})),
            tuple(item.get("source_graphs", [])),
        ),
    )


def _edge_id(edge: dict[str, Any]) -> str:
    return "edge:" + hashlib.sha256(_canonical_json(edge).encode("utf-8")).hexdigest()


def _decode_properties(value: Any, *, field: str) -> dict[str, Any]:
    try:
        decoded = json.loads(value or "{}")
    except (TypeError, json.JSONDecodeError) as error:
        raise ReadOnlyKnowledgeServiceError(f"Invalid {field} JSON in graph projection.") from error
    if not isinstance(decoded, dict):
        raise ReadOnlyKnowledgeServiceError(f"Invalid {field} value in graph projection.")
    return decoded


def _node_from_record(record: dict[str, Any]) -> dict[str, Any]:
    node = {
        "id": record["id"],
        "type": record["entity_type"],
        "properties": _decode_properties(record.get("properties_json"), field="node properties"),
    }
    source_graphs = list(record.get("source_graphs") or [])
    if source_graphs:
        node["source_graphs"] = source_graphs
    return node


def _edge_and_nodes_from_record(
    record: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = _node_from_record(
        {
            "id": record["source"],
            "entity_type": record["source_type"],
            "properties_json": record.get("source_properties_json"),
            "source_graphs": record.get("source_source_graphs"),
        }
    )
    target = _node_from_record(
        {
            "id": record["target"],
            "entity_type": record["target_type"],
            "properties_json": record.get("target_properties_json"),
            "source_graphs": record.get("target_source_graphs"),
        }
    )
    edge = {
        "source": source["id"],
        "type": record["relationship_type"],
        "target": target["id"],
        "properties": _decode_properties(
            record.get("relationship_properties_json"), field="relationship properties"
        ),
    }
    source_graphs = list(record.get("relationship_source_graphs") or [])
    if source_graphs:
        edge["source_graphs"] = source_graphs
    return edge, source, target


def validate_read_only_templates() -> None:
    for name, query in READ_ONLY_CYPHER_TEMPLATES.items():
        if _MUTATION_TOKEN.search(query):
            raise KnowledgeServiceConfigurationError(
                f"Knowledge Service query template {name!r} contains a mutation token."
            )
        if "MATCH" not in query.upper() or "RETURN" not in query.upper():
            raise KnowledgeServiceConfigurationError(
                f"Knowledge Service query template {name!r} is not a bounded read query."
            )


validate_read_only_templates()


class SnapshotReadAdapter:
    backend_name = "canonical-json-snapshot"

    def __init__(self, graph: dict[str, Any]):
        self.nodes = {item["id"]: item for item in graph["nodes"]}
        self.adjacent: dict[str, list[dict[str, Any]]] = {}
        for edge in graph["edges"]:
            self.adjacent.setdefault(edge["source"], []).append(edge)
            self.adjacent.setdefault(edge["target"], []).append(edge)

    def read_nodes(self, node_ids: list[str]) -> list[dict[str, Any]]:
        return [self.nodes[node_id] for node_id in sorted(set(node_ids)) if node_id in self.nodes]

    def read_incident_edges(self, node_id: str) -> list[dict[str, Any]]:
        rows = []
        for edge in self.adjacent.get(node_id, []):
            rows.append(
                {
                    "edge": edge,
                    "source_node": self.nodes[edge["source"]],
                    "target_node": self.nodes[edge["target"]],
                }
            )
        return sorted(rows, key=lambda item: _edge_id(item["edge"]))

    def close(self) -> None:
        return None


class Neo4jReadAdapter:
    backend_name = "live-neo4j"

    def __init__(self, driver: Any, *, database: str, graph_revision: str):
        self.driver = driver
        self.database = database
        self.graph_revision = graph_revision

    def _execute_read(self, query: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        if query not in READ_ONLY_CYPHER_TEMPLATES.values():
            raise ReadOnlyKnowledgeServiceError("An unregistered Cypher template was rejected.")
        if _MUTATION_TOKEN.search(query):
            raise ReadOnlyKnowledgeServiceError("A mutating Cypher template was rejected.")
        with self.driver.session(
            database=self.database,
            default_access_mode="READ",
        ) as session:
            execute_read = getattr(session, "execute_read", None)
            if not callable(execute_read):
                raise ReadOnlyKnowledgeServiceError(
                    "The Neo4j session does not expose execute_read()."
                )

            def work(transaction: Any) -> list[dict[str, Any]]:
                return [dict(record) for record in transaction.run(query, parameters)]

            return execute_read(work)

    def read_nodes(self, node_ids: list[str]) -> list[dict[str, Any]]:
        records = self._execute_read(
            READ_NODES_CYPHER,
            {"node_ids": list(node_ids), "graph_revision": self.graph_revision},
        )
        return [_node_from_record(record) for record in records]

    def read_incident_edges(self, node_id: str) -> list[dict[str, Any]]:
        records = self._execute_read(
            READ_INCIDENT_EDGES_CYPHER,
            {
                "node_id": node_id,
                "graph_revision": self.graph_revision,
                "row_limit": MAX_EDGE_SCAN_PER_NODE + 1,
            },
        )
        if len(records) > MAX_EDGE_SCAN_PER_NODE:
            raise ReadOnlyKnowledgeServiceError(
                f"Node {node_id!r} exceeds the bounded incident-edge scan limit."
            )
        rows = []
        for record in records:
            edge, source, target = _edge_and_nodes_from_record(record)
            rows.append({"edge": edge, "source_node": source, "target_node": target})
        return sorted(rows, key=lambda item: _edge_id(item["edge"]))

    def close(self) -> None:
        self.driver.close()


_BOUNDED_HUB_EDGES = {
    ("CodeList", "HAS_VALUE"),
    ("SpecificationDocument", "CONTAINS"),
    ("PortrayalProfile", "DEFINES"),
    ("LineStyleReference", "USES_LINE_STYLE"),
    ("PortrayalColorReference", "USES_COLOR"),
    ("PortrayalGeometryRole", "APPLIES_TO_GEOMETRY"),
    ("ProductionStage", "PRODUCED_DURING"),
    ("DocumentSection", "EVIDENCED_ON"),
    ("DocumentSection", "DERIVED_FROM"),
    ("ExtractionCorrectionObservation", "CORRECTS_EXTRACTION"),
    ("FeatureType", "PORTRAYED_BY"),
    ("ProductLayer", "PORTRAYED_BY"),
    ("ProductLayer", "HAS_FIELD"),
    ("ClassificationScheme", "DEFINES"),
    ("ClassificationLevel", "HAS_CLASSIFICATION_LEVEL"),
    ("ProductLayer", "USES_ATTRIBUTES_FROM"),
    ("ProductLayer", "USES_BOUNDARY_FROM"),
    ("ProductField", "USES_CLASSIFICATION_FIELD"),
    ("ProductField", "USES_LABEL_FIELD"),
    ("ProductField", "USES_ROUTE_NUMBER_FIELD"),
    ("ProductField", "USES_CO_ROUTE_COUNT_FIELD"),
    ("ActivationGate", "BLOCKED_BY"),
    ("GeometryRule", "USES_DATA_FUSION_RULE"),
    ("PortrayalRule", "USES_ROUTE_SHIELD_RULE"),
    ("GraphicElementType", "USES_GRAPHIC_ELEMENT_TYPE"),
    ("GovernanceEvidence", "HAS_SOURCE_OR_BASIS"),
    ("NormativeAuthority", "CITES_AUTHORITY"),
}


class ReadOnlyKnowledgeService:
    """Closed-operation, read-only access to one identity-verified KG revision."""

    operation_registry = {
        RETRIEVE_EVIDENCE_OPERATION: {
            "request_contract": "nma.retrieve-evidence-request/0.33",
            "response_contract": KNOWLEDGE_SERVICE_CONTRACT,
            "mutation_allowed": False,
            "arbitrary_cypher_allowed": False,
        }
    }

    def __init__(
        self,
        adapter: SnapshotReadAdapter | Neo4jReadAdapter,
        *,
        canonical_retriever: CitationIntegrityGraphRetrieverV06,
        graph_revision: str,
        graph_sha256: str,
        activation_trace: dict[str, Any],
    ):
        self.adapter = adapter
        self.canonical_retriever = canonical_retriever
        self.graph_revision = graph_revision
        self.graph_sha256 = graph_sha256
        self.activation_trace = activation_trace

    def execute(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if operation not in self.operation_registry:
            raise ReadOnlyKnowledgeServiceError(f"Unsupported operation: {operation!r}.")
        if operation == RETRIEVE_EVIDENCE_OPERATION:
            allowed = {
                "query",
                "seed_ids",
                "ranked_trace",
                "retrieval_mode",
                "max_depth",
                "max_nodes",
                "expand_product_fields",
                "extra_trace",
            }
            extra = sorted(set(parameters) - allowed)
            if extra:
                raise ReadOnlyKnowledgeServiceError(
                    f"Unsupported retrieve_evidence parameters: {extra}."
                )
            return self.retrieve_evidence(**parameters)
        raise AssertionError(operation)

    def retrieve_evidence(
        self,
        query: str,
        seed_ids: list[str],
        *,
        ranked_trace: list[dict[str, Any]],
        retrieval_mode: str,
        max_depth: int,
        max_nodes: int,
        expand_product_fields: bool = False,
        extra_trace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._validate_request(
            query=query,
            seed_ids=seed_ids,
            ranked_trace=ranked_trace,
            retrieval_mode=retrieval_mode,
            max_depth=max_depth,
            max_nodes=max_nodes,
            expand_product_fields=expand_product_fields,
            extra_trace=extra_trace,
        )
        unique_seed_ids = list(dict.fromkeys(seed_ids))
        seed_nodes = self.adapter.read_nodes(unique_seed_ids)
        node_by_id = {node["id"]: node for node in seed_nodes}
        unknown = sorted(set(unique_seed_ids) - set(node_by_id))
        if unknown:
            raise ReadOnlyKnowledgeServiceError(
                f"The identity-verified graph revision lacks requested nodes: {unknown}."
            )
        seed_set = set(node_by_id)
        visited = set(node_by_id)
        queue = deque((node_id, 0) for node_id in sorted(visited))
        selected_edges: dict[str, dict[str, Any]] = {}
        read_calls = 1
        scanned_edges = 0
        while queue and len(visited) < max_nodes:
            node_id, depth = queue.popleft()
            if depth >= max_depth:
                continue
            incident = self.adapter.read_incident_edges(node_id)
            read_calls += 1
            scanned_edges += len(incident)
            for row in incident:
                edge = row["edge"]
                source = row["source_node"]
                target = row["target_node"]
                if source["id"] == node_id:
                    focus, other = source, target
                elif target["id"] == node_id:
                    focus, other = target, source
                else:
                    raise ReadOnlyKnowledgeServiceError(
                        "Neo4j returned an edge outside the requested incident set."
                    )
                if (
                    (focus["type"], edge["type"]) in _BOUNDED_HUB_EDGES
                    and other["id"] not in seed_set
                    and not (
                        expand_product_fields
                        and focus["type"] == "ProductLayer"
                        and edge["type"] == "HAS_FIELD"
                    )
                ):
                    continue
                if (
                    focus["type"] == "TerrainClassificationCode"
                    and edge["type"] in {"SPECIALIZES", "HAS_ANCESTOR"}
                    and edge["target"] == node_id
                    and other["id"] not in seed_set
                ):
                    continue
                selected_edges[_edge_id(edge)] = edge
                if other["id"] not in visited and len(visited) < max_nodes:
                    node_by_id[other["id"]] = other
                    visited.add(other["id"])
                    queue.append((other["id"], depth + 1))

        nodes = [node_by_id[node_id] for node_id in sorted(visited)]
        edges = [selected_edges[key] for key in sorted(selected_edges)]
        return self._build_package(
            query=query,
            seeds=[node_by_id[node_id] for node_id in unique_seed_ids],
            nodes=nodes,
            edges=edges,
            ranked_trace=ranked_trace,
            retrieval_mode=retrieval_mode,
            max_depth=max_depth,
            max_nodes=max_nodes,
            expand_product_fields=expand_product_fields,
            extra_trace=extra_trace,
            read_calls=read_calls,
            scanned_edges=scanned_edges,
        )

    def _validate_request(self, **request: Any) -> None:
        query = request["query"]
        seed_ids = request["seed_ids"]
        ranked_trace = request["ranked_trace"]
        if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY_CHARACTERS:
            raise ReadOnlyKnowledgeServiceError("query must be a non-empty bounded string.")
        if (
            not isinstance(seed_ids, list)
            or len(seed_ids) > MAX_SEED_IDS
            or any(not isinstance(node_id, str) or not node_id for node_id in seed_ids)
        ):
            raise ReadOnlyKnowledgeServiceError("seed_ids violate the bounded request contract.")
        if not isinstance(ranked_trace, list) or len(ranked_trace) > MAX_RANKED_TRACE_RECORDS:
            raise ReadOnlyKnowledgeServiceError(
                "ranked_trace violates the bounded request contract."
            )
        if not isinstance(request["retrieval_mode"], str):
            raise ReadOnlyKnowledgeServiceError("retrieval_mode must be a string.")
        if type(request["max_depth"]) is not int or not 0 <= request["max_depth"] <= MAX_DEPTH:
            raise ReadOnlyKnowledgeServiceError("max_depth violates the bounded request contract.")
        if type(request["max_nodes"]) is not int or not 1 <= request["max_nodes"] <= MAX_NODES:
            raise ReadOnlyKnowledgeServiceError("max_nodes violates the bounded request contract.")
        if not isinstance(request["expand_product_fields"], bool):
            raise ReadOnlyKnowledgeServiceError("expand_product_fields must be boolean.")
        if request["extra_trace"] is not None and not isinstance(request["extra_trace"], dict):
            raise ReadOnlyKnowledgeServiceError("extra_trace must be an object when supplied.")

    def _build_package(
        self,
        *,
        query: str,
        seeds: list[dict[str, Any]],
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        ranked_trace: list[dict[str, Any]],
        retrieval_mode: str,
        max_depth: int,
        max_nodes: int,
        expand_product_fields: bool,
        extra_trace: dict[str, Any] | None,
        read_calls: int,
        scanned_edges: int,
    ) -> dict[str, Any]:
        sections = [node for node in nodes if node["type"] == "DocumentSection"]
        documents = [node for node in nodes if node["type"] == "SpecificationDocument"]
        conflicts = [
            node
            for node in nodes
            if "Conflict" in node["type"] or node["type"] == "SourceCodeAnomaly"
        ]
        clarification_seeds = [
            node
            for node in seeds
            if node["type"] == "ClassificationHierarchy"
            and node.get("properties", {}).get("status") == "not-applicable-for-symbol-generation"
            and "子類別承接" in node.get("properties", {}).get("reason", "")
        ]
        status = (
            "abstained-no-match"
            if not seeds
            else "retrieved-with-conflict"
            if conflicts
            else "needs-clarification"
            if clarification_seeds
            else "retrieved"
        )
        citations = []
        for section in sorted(sections, key=lambda item: item["id"]):
            section_id = section["id"]
            document_ids = self.canonical_retriever.section_document_ids.get(section_id, [])
            if len(document_ids) == 1:
                document_id = document_ids[0]
                document_properties, provenance = self.canonical_retriever.document_properties(
                    document_id
                )
                integrity = "verified-unique-document-containment"
            else:
                document_id = None
                document_properties = {}
                provenance = None
                integrity = (
                    "missing-document-containment"
                    if not document_ids
                    else "ambiguous-document-containment"
                )
            section_properties = section.get("properties", {})
            citations.append(
                {
                    "citation_id": f"citation:{section_id}",
                    "section_id": section_id,
                    "document_id": document_id,
                    "filename": document_properties.get("filename"),
                    "revision": document_properties.get("revision"),
                    "source_sha256": document_properties.get("sha256"),
                    "page": section_properties.get("page"),
                    "printed_page": section_properties.get("printed_page"),
                    "record_id": section_properties.get("record_id"),
                    "review_status": section_properties.get("review_status"),
                    "source_text": section_properties.get("source_text"),
                    "citation_integrity": integrity,
                    "document_candidates": document_ids,
                    "metadata_provenance": provenance,
                }
            )
        evidence_nodes = [
            {
                "id": node["id"],
                "type": node["type"],
                "properties": _bounded_value(node.get("properties", {})),
            }
            for node in nodes
        ]
        edge_ids = [_edge_id(edge) for edge in edges]
        knowledge_trace = {
            "contract": KNOWLEDGE_SERVICE_CONTRACT,
            "operation": RETRIEVE_EVIDENCE_OPERATION,
            "operation_registry_version": "0.33",
            "active_backend": self.adapter.backend_name,
            "graph_revision": self.graph_revision,
            "canonical_graph_sha256": self.graph_sha256,
            "graph_identity_verified": bool(self.activation_trace.get("graph_identity_verified")),
            "selected_node_ids": [node["id"] for node in nodes],
            "selected_edge_ids": edge_ids,
            "read_transaction_calls": read_calls,
            "incident_edges_scanned": scanned_edges,
            "credential_scope_required": "read-only",
            "driver_access_mode": "READ",
            "typed_operations_only": True,
            "arbitrary_cypher_allowed": False,
            "mutation_allowed": False,
            "automatic_rule_activation": False,
            "autonomous_canonical_kg_modification": "future-research-only",
        }
        return {
            "schema": "nma.evidence-package/0.4",
            "status": status,
            "retrieval_mode": f"{retrieval_mode}; readonly-knowledge-service-v0.33",
            "query": query,
            "resolved_entities": [
                {"id": node["id"], "type": node["type"], "properties": node["properties"]}
                for node in seeds
            ],
            "retrieval_trace": {
                "query_terms": _query_terms(query),
                "ranked_candidates": ranked_trace,
                "selected_seed_ids": [node["id"] for node in seeds],
                "max_depth": max_depth,
                "max_nodes": max_nodes,
                "product_field_scope_expanded": expand_product_fields,
                **(extra_trace or {}),
                "readonly_knowledge_service": knowledge_trace,
            },
            "evidence_nodes": evidence_nodes,
            "graph_paths": {
                "nodes": [node["id"] for node in nodes],
                "edges": [
                    {"source": edge["source"], "type": edge["type"], "target": edge["target"]}
                    for edge in edges
                ],
            },
            "source_documents": [node["properties"] for node in documents],
            "source_sections": [node["properties"] for node in sections],
            "citations": citations,
            "conflicts": [node["properties"] for node in conflicts],
            "clarification": (
                {
                    "required": True,
                    "reason": (
                        "The matched hierarchy node is not an executable portrayal rule; "
                        "select a reviewed subtype."
                    ),
                    "hierarchy_node_ids": [node["id"] for node in clarification_seeds],
                }
                if clarification_seeds
                else {"required": False, "reason": None, "hierarchy_node_ids": []}
            ),
            "missing_evidence": (
                []
                if seeds
                else [
                    "No reviewed canonical-graph node matched the query; LLM must abstain or clarify."
                ]
            ),
            "automatic_rule_activation": False,
        }

    def close(self) -> None:
        self.adapter.close()


class KnowledgeServiceGraphRetriever:
    """Compatibility adapter: local candidate discovery, service-backed evidence expansion."""

    def __init__(
        self,
        local_retriever: CitationIntegrityGraphRetrieverV06,
        service: ReadOnlyKnowledgeService,
    ):
        self.local_retriever = local_retriever
        self.service = service
        self.graph = local_retriever.graph
        self.nodes = local_retriever.nodes
        self.edges = local_retriever.edges
        self.adjacent = local_retriever.adjacent
        self.search_text = local_retriever.search_text
        self.section_document_ids = local_retriever.section_document_ids
        self.source_registry = local_retriever.source_registry

    def __getattr__(self, name: str) -> Any:
        return getattr(self.local_retriever, name)

    def document_properties(self, document_id: str) -> tuple[dict[str, Any], str]:
        return self.local_retriever.document_properties(document_id)

    def package_from_seed_ids(
        self, query: str, seed_ids: list[str], **kwargs: Any
    ) -> dict[str, Any]:
        return self.service.retrieve_evidence(query, seed_ids, **kwargs)

    def evidence_package(self, query: str, **kwargs: Any) -> dict[str, Any]:
        local_package = self.local_retriever.evidence_package(query, **kwargs)
        trace = local_package["retrieval_trace"]
        return self.service.retrieve_evidence(
            query,
            trace["selected_seed_ids"],
            ranked_trace=trace["ranked_candidates"],
            retrieval_mode=local_package["retrieval_mode"],
            max_depth=int(trace["max_depth"]),
            max_nodes=int(trace["max_nodes"]),
            expand_product_fields=bool(trace.get("product_field_scope_expanded", False)),
            extra_trace={
                key: value
                for key, value in trace.items()
                if key
                not in {
                    "query_terms",
                    "ranked_candidates",
                    "selected_seed_ids",
                    "max_depth",
                    "max_nodes",
                    "product_field_scope_expanded",
                }
            },
        )


def select_readonly_knowledge_service(
    *,
    canonical_graph_path: str | Path,
    citation_registry_path: str | Path,
    settings: dict[str, str],
    driver_factory: Callable[[str, str, str], Any] = open_neo4j_driver,
) -> tuple[KnowledgeServiceGraphRetriever, ReadOnlyKnowledgeService, dict[str, Any]]:
    canonical_path = Path(canonical_graph_path)
    canonical_graph = json.loads(canonical_path.read_text(encoding="utf-8"))
    registry = load_citation_source_registry(citation_registry_path)
    local_retriever = CitationIntegrityGraphRetrieverV06(canonical_graph, registry)
    graph_revision = canonical_graph["graph_id"]
    graph_sha256 = _graph_sha256(canonical_path)
    requested = settings.get("NMA_GRAPH_BACKEND", "canonical-json")
    fallback = settings.get("NMA_GRAPH_FALLBACK", "canonical-json")
    if requested not in {"canonical-json", "neo4j"}:
        raise KnowledgeServiceConfigurationError(f"Unsupported graph backend: {requested!r}.")
    if fallback not in {"canonical-json", "none"}:
        raise KnowledgeServiceConfigurationError(f"Unsupported graph fallback: {fallback!r}.")
    base_trace = {
        "contract": KNOWLEDGE_SERVICE_CONTRACT,
        "requested_backend": requested,
        "active_backend": "canonical-json-snapshot",
        "fallback_backend": fallback,
        "fallback_used": False,
        "fallback_reason_code": None,
        "graph_revision": graph_revision,
        "canonical_graph_sha256": graph_sha256,
        "graph_identity_verified": True,
        "active_graph_authoritative": True,
        "neo4j_database": None,
        "credential_scope_required": "read-only",
        "driver_access_mode": "READ",
        "typed_tool_only": True,
        "arbitrary_cypher_allowed": False,
        "mutation_allowed": False,
        "automatic_rule_activation": False,
        "autonomous_canonical_kg_modification": "future-research-only",
    }

    def snapshot(
        trace: dict[str, Any],
    ) -> tuple[KnowledgeServiceGraphRetriever, ReadOnlyKnowledgeService, dict[str, Any]]:
        service = ReadOnlyKnowledgeService(
            SnapshotReadAdapter(canonical_graph),
            canonical_retriever=local_retriever,
            graph_revision=graph_revision,
            graph_sha256=graph_sha256,
            activation_trace=trace,
        )
        return KnowledgeServiceGraphRetriever(local_retriever, service), service, trace

    if requested == "canonical-json":
        return snapshot(base_trace)

    required = {key: settings.get(key, "") for key in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD")}
    missing = sorted(key for key, value in required.items() if not value)
    scope = settings.get("NMA_NEO4J_CREDENTIAL_SCOPE", "")
    failure_code: str | None = None
    failure: Exception | None = None
    driver = None
    if missing:
        failure_code = "neo4j-settings-incomplete"
        failure = KnowledgeServiceConfigurationError(
            f"Neo4j backend settings are incomplete: {', '.join(missing)}"
        )
    elif scope != "read-only":
        failure_code = "neo4j-read-only-scope-not-attested"
        failure = KnowledgeServiceConfigurationError(
            "Neo4j activation requires NMA_NEO4J_CREDENTIAL_SCOPE=read-only."
        )
    else:
        try:
            driver = driver_factory(
                required["NEO4J_URI"], required["NEO4J_USER"], required["NEO4J_PASSWORD"]
            )
            database = settings.get("NEO4J_DATABASE") or "neo4j"
            live_graph = load_live_projection_v028(
                driver,
                database=database,
                graph_revision=graph_revision,
                read_access_mode=True,
            )
            if _normal_nodes(live_graph) != _normal_nodes(canonical_graph) or _normal_edges(
                live_graph
            ) != _normal_edges(canonical_graph):
                raise KnowledgeServiceConfigurationError(
                    "The live Neo4j projection differs from the canonical graph revision."
                )
            trace = {
                **base_trace,
                "active_backend": "live-neo4j",
                "neo4j_database": database,
                "live_nodes": len(live_graph["nodes"]),
                "live_edges": len(live_graph["edges"]),
                "live_projection_identity": "full-structural-parity-verified-at-activation",
            }
            service = ReadOnlyKnowledgeService(
                Neo4jReadAdapter(driver, database=database, graph_revision=graph_revision),
                canonical_retriever=local_retriever,
                graph_revision=graph_revision,
                graph_sha256=graph_sha256,
                activation_trace=trace,
            )
            return KnowledgeServiceGraphRetriever(local_retriever, service), service, trace
        except Exception as error:
            failure_code = (
                "neo4j-projection-mismatch"
                if isinstance(error, KnowledgeServiceConfigurationError)
                else "neo4j-unavailable"
            )
            failure = error
            if driver is not None:
                driver.close()

    if fallback != "canonical-json":
        raise KnowledgeServiceConfigurationError(
            f"Neo4j activation failed with {failure_code}; canonical fallback is disabled."
        ) from failure
    return snapshot(
        {
            **base_trace,
            "fallback_used": True,
            "fallback_reason_code": failure_code,
            "fallback_identity": "same-canonical-revision-and-sha256",
            "graph_identity_verified": True,
        }
    )

from __future__ import annotations

from collections import deque
import json
import re
from pathlib import Path
from typing import Any, Iterable


TOKEN_PATTERN = re.compile(r"[0-9A-Za-z._-]+|[\u3400-\u9fff]+")
ALIAS_PROPERTY_KEYS = {
    "aliases",
    "code",
    "feature_code",
    "feature_name",
    "label",
    "name",
}
GENERIC_ALIAS_LITERALS = {
    "圖徵",
    "地圖",
    "圖層",
    "圖式",
    "符號",
    "資料",
}


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif value is not None:
        yield str(value)


def _query_terms(query: str) -> list[str]:
    terms = [term.casefold() for term in TOKEN_PATTERN.findall(query) if term.strip()]
    compact = query.casefold().strip()
    if compact and compact not in terms:
        terms.append(compact)
    return sorted(set(terms), key=lambda term: (-len(term), term))


class CanonicalGraphRetriever:
    """Deterministic first GraphRAG slice: exact/full-text retrieval plus typed graph expansion.

    Vector search, Neo4j projection, and LLM reasoning consume this contract later. This class does
    not generate answers and cannot activate graph rules.
    """

    def __init__(self, graph: dict[str, Any]):
        self.graph = graph
        self.nodes = {node["id"]: node for node in graph["nodes"]}
        self.edges = list(graph["edges"])
        self.adjacent: dict[str, list[dict[str, Any]]] = {}
        for edge in self.edges:
            self.adjacent.setdefault(edge["source"], []).append(edge)
            self.adjacent.setdefault(edge["target"], []).append(edge)
        self.search_text = {
            node_id: " ".join(_strings(node)).casefold() for node_id, node in self.nodes.items()
        }

    @classmethod
    def load(cls, path: str | Path) -> "CanonicalGraphRetriever":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def ranked_search(
        self, query: str, *, node_types: set[str] | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        terms = _query_terms(query)
        if not terms:
            return []
        ranked: list[tuple[int, str, dict[str, Any], list[str]]] = []
        compact = query.casefold().strip()
        for node_id, node in self.nodes.items():
            if node_types and node["type"] not in node_types:
                continue
            text = self.search_text[node_id]
            matched_terms = [term for term in terms if term in text]
            score = sum(len(term) * (4 if term == compact else 1) for term in matched_terms)
            if compact and compact in node_id.casefold():
                score += 100
            if score:
                ranked.append((score, node_id, node, matched_terms))
        return [
            {
                "score": score,
                "node": node,
                "matched_terms": matched_terms,
                "match_mode": "full-text",
            }
            for score, _, node, matched_terms in sorted(
                ranked, key=lambda item: (-item[0], item[1])
            )[:limit]
        ]

    def search(
        self, query: str, *, node_types: set[str] | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        return [
            item["node"]
            for item in self.ranked_search(query, node_types=node_types, limit=limit)
        ]

    def alias_search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        """Resolve explicit code/name/label/alias literals embedded in a natural-language turn."""

        compact = query.casefold().strip()
        ranked: list[tuple[int, str, dict[str, Any], str]] = []
        if not compact:
            return []
        for node_id, node in self.nodes.items():
            properties = node.get("properties", {})
            literals: list[str] = []
            for key in ALIAS_PROPERTY_KEYS:
                value = properties.get(key)
                if isinstance(value, str):
                    literals.append(value)
                elif isinstance(value, list):
                    literals.extend(item for item in value if isinstance(item, str))
            best: tuple[int, str] | None = None
            for literal in literals:
                normalized = literal.casefold().strip()
                if (
                    len(normalized) < 2
                    or normalized in GENERIC_ALIAS_LITERALS
                    or normalized not in compact
                ):
                    continue
                is_code = bool(re.fullmatch(r"[0-9A-Za-z._-]+", normalized))
                score = 1_000 + len(normalized) * 20 + (500 if is_code else 0)
                if normalized == compact:
                    score += 1_000
                if best is None or score > best[0]:
                    best = (score, literal)
            if best:
                ranked.append((best[0], node_id, node, best[1]))
        return [
            {
                "score": score,
                "node": node,
                "matched_terms": [literal],
                "match_mode": "explicit-alias",
            }
            for score, _, node, literal in sorted(
                ranked, key=lambda item: (-item[0], item[1])
            )[:limit]
        ]

    def expand(
        self,
        seed_ids: list[str],
        *,
        max_depth: int = 2,
        edge_types: set[str] | None = None,
        max_nodes: int = 60,
        expand_product_fields: bool = False,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        visited = {node_id for node_id in seed_ids if node_id in self.nodes}
        seed_set = set(visited)
        queue = deque((node_id, 0) for node_id in sorted(visited))
        selected_edges: dict[str, dict[str, Any]] = {}
        while queue and len(visited) < max_nodes:
            node_id, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for edge in self.adjacent.get(node_id, []):
                if edge_types and edge["type"] not in edge_types:
                    continue
                other = edge["target"] if edge["source"] == node_id else edge["source"]
                # Do not let high-cardinality hubs consume the bounded package with sibling records.
                # Exact matches enter as seeds; expansion should then prefer their governing field,
                # rule, layer, FeatureType, and evidence instead of unrelated siblings.
                bounded_hub_edges = {
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
                if (
                    (self.nodes[node_id]["type"], edge["type"]) in bounded_hub_edges
                    and other not in seed_set
                    and not (
                        expand_product_fields
                        and self.nodes[node_id]["type"] == "ProductLayer"
                        and edge["type"] == "HAS_FIELD"
                    )
                ):
                    continue
                # A classification parent should be reachable from an exact child, but once the
                # parent is reached its other children are siblings, not evidence for the query.
                if (
                    self.nodes[node_id]["type"] == "TerrainClassificationCode"
                    and edge["type"] in {"SPECIALIZES", "HAS_ANCESTOR"}
                    and edge["target"] == node_id
                    and other not in seed_set
                ):
                    continue
                key = json.dumps(edge, ensure_ascii=False, sort_keys=True)
                selected_edges[key] = edge
                if other in self.nodes and other not in visited and len(visited) < max_nodes:
                    visited.add(other)
                    queue.append((other, depth + 1))
        return (
            [self.nodes[node_id] for node_id in sorted(visited)],
            [selected_edges[key] for key in sorted(selected_edges)],
        )

    def evidence_package(
        self,
        query: str,
        *,
        seed_limit: int = 6,
        max_depth: int = 2,
        max_nodes: int = 60,
    ) -> dict[str, Any]:
        compact = query.casefold().strip()
        terms = [term for term in _query_terms(query) if term != compact]
        # Preserve candidates for each individual term before applying specificity filters. A
        # growing graph can otherwise let many nodes matching only a generic term (for example
        # 圖式) fill the bounded seed list before a rarer entity term (for example 小學) appears.
        ranked_candidates: dict[str, dict[str, Any]] = {}
        alias_matches = self.alias_search(query, limit=max(seed_limit * 4, 20))
        full_text_matches = self.ranked_search(query, limit=seed_limit)
        for item in [*alias_matches, *full_text_matches]:
            node_id = item["node"]["id"]
            existing = ranked_candidates.get(node_id)
            if existing is None or item["score"] > existing["score"]:
                ranked_candidates[node_id] = item
        seed_candidates: dict[str, dict[str, Any]] = {
            node_id: item["node"] for node_id, item in ranked_candidates.items()
        }
        for term in terms:
            for item in self.ranked_search(term, limit=seed_limit):
                node = item["node"]
                seed_candidates.setdefault(node["id"], node)
                ranked_candidates.setdefault(node["id"], item)
        seeds = list(seed_candidates.values())
        if alias_matches:
            selected_alias_ids: set[str] = set()
            selected_literals: list[str] = []
            for item in alias_matches:
                literal = item["matched_terms"][0].casefold().strip()
                same_literal = literal in selected_literals
                overlaps_stronger_literal = any(
                    literal in selected or selected in literal for selected in selected_literals
                )
                if overlaps_stronger_literal and not same_literal:
                    continue
                if not same_literal:
                    if len(selected_alias_ids) >= seed_limit:
                        break
                    selected_literals.append(literal)
                selected_alias_ids.add(item["node"]["id"])
            seeds = [node for node in seeds if node["id"] in selected_alias_ids]
        # When a multi-term query has a node matching more of the user's terms, discard
        # lower-coverage seeds that matched only a generic word such as 圖式. This keeps a
        # growing portrayal corpus from introducing unrelated rules into a bounded package.
        if seeds and terms and not alias_matches:
            document_frequency = {
                term: sum(term in text for text in self.search_text.values()) for term in terms
            }
            specific_term = min(
                terms, key=lambda term: (document_frequency[term], -len(term), term)
            )
            specific_matches = [
                node for node in seeds if specific_term in self.search_text[node["id"]]
            ]
            if specific_matches:
                seeds = specific_matches
        if seeds and len(terms) > 1:
            matched_counts = {
                node["id"]: sum(term in self.search_text[node["id"]] for term in terms)
                for node in seeds
            }
            best_count = max(matched_counts.values())
            if best_count > 1:
                seeds = [node for node in seeds if matched_counts[node["id"]] == best_count]
        ranked_trace = [
            {
                "id": item["node"]["id"],
                "type": item["node"]["type"],
                "score": item["score"],
                "matched_terms": item["matched_terms"],
                "match_mode": item["match_mode"],
            }
            for item in sorted(
                ranked_candidates.values(),
                key=lambda item: (-item["score"], item["node"]["id"]),
            )[: max(seed_limit * 2, 10)]
        ]
        return self.package_from_seed_ids(
            query,
            [node["id"] for node in seeds],
            ranked_trace=ranked_trace,
            retrieval_mode="deterministic-full-text-plus-graph; vector-and-neo4j-pending",
            max_depth=max_depth,
            max_nodes=max_nodes,
            expand_product_fields=any(
                keyword in query.casefold()
                for keyword in ("欄位", "屬性", "field", "attribute")
            ),
        )

    def package_from_seed_ids(
        self,
        query: str,
        seed_ids: list[str],
        *,
        ranked_trace: list[dict[str, Any]],
        retrieval_mode: str,
        max_depth: int,
        max_nodes: int,
        extra_trace: dict[str, Any] | None = None,
        expand_product_fields: bool = False,
    ) -> dict[str, Any]:
        """Build the bounded evidence contract from already ranked, validated graph seeds."""

        seen: set[str] = set()
        seeds = []
        for node_id in seed_ids:
            if node_id in seen or node_id not in self.nodes:
                continue
            seen.add(node_id)
            seeds.append(self.nodes[node_id])
        nodes, edges = self.expand(
            [node["id"] for node in seeds],
            max_depth=max_depth,
            max_nodes=max_nodes,
            expand_product_fields=expand_product_fields,
        )
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
            and node.get("properties", {}).get("status")
            == "not-applicable-for-symbol-generation"
            and "子類別承接" in node.get("properties", {}).get("reason", "")
        ]
        if not seeds:
            package_status = "abstained-no-match"
        elif conflicts:
            package_status = "retrieved-with-conflict"
        elif clarification_seeds:
            package_status = "needs-clarification"
        else:
            package_status = "retrieved"
        evidence_nodes = [
            {
                "id": node["id"],
                "type": node["type"],
                "properties": _bounded_value(node.get("properties", {})),
            }
            for node in nodes
        ]
        citations = self._citations(nodes, edges)
        return {
            "schema": "nma.evidence-package/0.4",
            "status": package_status,
            "retrieval_mode": retrieval_mode,
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
                    "reason": "The matched hierarchy node is not an executable portrayal rule; select a reviewed subtype.",
                    "hierarchy_node_ids": [node["id"] for node in clarification_seeds],
                }
                if clarification_seeds
                else {"required": False, "reason": None, "hierarchy_node_ids": []}
            ),
            "missing_evidence": (
                []
                if seeds
                else ["No reviewed canonical-graph node matched the query; LLM must abstain or clarify."]
            ),
            "automatic_rule_activation": False,
        }

    def _citations(
        self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        selected = {node["id"]: node for node in nodes}
        documents = {
            node_id: node
            for node_id, node in selected.items()
            if node["type"] == "SpecificationDocument"
        }
        citations: list[dict[str, Any]] = []
        for section_id, section in sorted(selected.items()):
            if section["type"] != "DocumentSection":
                continue
            connected_document_ids = sorted(
                {
                    edge["source"]
                    for edge in self.edges
                    if edge["target"] == section_id
                    and self.nodes.get(edge["source"], {}).get("type")
                    == "SpecificationDocument"
                }
            )
            section_properties = section.get("properties", {})
            if not connected_document_ids:
                document_id = section_properties.get("document_id")
                document = self.nodes.get(document_id, {}) if isinstance(document_id, str) else {}
                document_properties = document.get("properties", {})
            else:
                document_id = connected_document_ids[0]
                document_properties = self.nodes[document_id].get("properties", {})
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
                }
            )
        return citations


def _bounded_value(value: Any, *, depth: int = 0) -> Any:
    """Bound graph properties before they enter an LLM evidence package."""

    if depth >= 3:
        return "[nested value omitted]"
    if isinstance(value, str):
        return value if len(value) <= 800 else value[:797] + "..."
    if isinstance(value, dict):
        return {
            str(key): _bounded_value(item, depth=depth + 1)
            for key, item in list(value.items())[:30]
        }
    if isinstance(value, list):
        return [_bounded_value(item, depth=depth + 1) for item in value[:30]]
    return value

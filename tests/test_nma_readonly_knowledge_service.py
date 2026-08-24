from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from nma.neo4j_projection import node_rows
from nma.neo4j_roundtrip_v027 import projected_relationship_rows
from nma.readonly_knowledge_service import (
    KNOWLEDGE_SERVICE_CONTRACT,
    READ_INCIDENT_EDGES_CYPHER,
    READ_NODES_CYPHER,
    KnowledgeServiceConfigurationError,
    ReadOnlyKnowledgeServiceError,
    select_readonly_knowledge_service,
    validate_read_only_templates,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
REGISTRY_PATH = ROOT / "data/knowledge/nma-citation-source-registry-v0.6.json"
PARITY_SPEC_PATH = ROOT / "data/specifications/nma-neo4j-retrieval-parity-v0.28.json"
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"


class Result(list):
    pass


def _properties_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class Transaction:
    def __init__(self, graph: dict, calls: list[dict]):
        self.graph = graph
        self.calls = calls
        self.nodes = {item["id"]: item for item in graph["nodes"]}

    def run(self, query: str, parameters: dict):
        self.calls.append({"query": query, "parameters": parameters})
        assert parameters["graph_revision"] == self.graph["graph_id"]
        if query == READ_NODES_CYPHER:
            return Result(
                {
                    "id": node["id"],
                    "entity_type": node["type"],
                    "properties_json": _properties_json(node.get("properties", {})),
                    "source_graphs": node.get("source_graphs", []),
                }
                for node_id in parameters["node_ids"]
                if (node := self.nodes.get(node_id)) is not None
            )
        if query == READ_INCIDENT_EDGES_CYPHER:
            node_id = parameters["node_id"]
            records = []
            for edge in self.graph["edges"]:
                if node_id not in (edge["source"], edge["target"]):
                    continue
                source = self.nodes[edge["source"]]
                target = self.nodes[edge["target"]]
                records.append(
                    {
                        "source": source["id"],
                        "source_type": source["type"],
                        "source_properties_json": _properties_json(source.get("properties", {})),
                        "source_source_graphs": source.get("source_graphs", []),
                        "relationship_type": edge["type"],
                        "relationship_key": None,
                        "relationship_properties_json": _properties_json(
                            edge.get("properties", {})
                        ),
                        "relationship_source_graphs": edge.get("source_graphs", []),
                        "target": target["id"],
                        "target_type": target["type"],
                        "target_properties_json": _properties_json(target.get("properties", {})),
                        "target_source_graphs": target.get("source_graphs", []),
                    }
                )
            return Result(records[: parameters["row_limit"]])
        raise AssertionError(query)


class Session:
    def __init__(self, graph: dict, driver: "Driver", access_mode: str | None):
        self.graph = graph
        self.driver = driver
        self.access_mode = access_mode

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def run(self, query: str, parameters: dict):
        assert self.access_mode == "READ"
        if "RETURN node.id AS id" in query:
            return Result(node_rows(self.graph))
        if "RETURN source.id AS source" in query:
            return Result(projected_relationship_rows(self.graph))
        raise AssertionError(query)

    def execute_read(self, work):
        assert self.access_mode == "READ"
        self.driver.execute_read_calls += 1
        return work(Transaction(self.graph, self.driver.queries))


class Driver:
    def __init__(self, graph: dict):
        self.graph = graph
        self.closed = False
        self.execute_read_calls = 0
        self.queries: list[dict] = []

    def verify_connectivity(self):
        return None

    def session(self, *, database: str, default_access_mode: str | None = None):
        assert database == "mapfeatures"
        return Session(self.graph, self, default_access_mode)

    def close(self):
        self.closed = True


def settings(**overrides: str) -> dict[str, str]:
    values = {
        "NMA_GRAPH_BACKEND": "neo4j",
        "NMA_GRAPH_FALLBACK": "none",
        "NMA_NEO4J_CREDENTIAL_SCOPE": "read-only",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "nma_reader",
        "NEO4J_PASSWORD": "test-secret-never-return",
        "NEO4J_DATABASE": "mapfeatures",
    }
    values.update(overrides)
    return values


def projection(package: dict) -> dict:
    return {
        "status": package["status"],
        "nodes": sorted(package["evidence_nodes"], key=lambda item: item["id"]),
        "edges": sorted(
            package["graph_paths"]["edges"],
            key=lambda item: (item["type"], item["source"], item["target"]),
        ),
        "citations": sorted(package["citations"], key=lambda item: item["citation_id"]),
        "conflicts": sorted(
            package["conflicts"],
            key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True),
        ),
    }


def test_query_templates_are_static_read_only_and_registered() -> None:
    validate_read_only_templates()
    for query in (READ_NODES_CYPHER, READ_INCIDENT_EDGES_CYPHER):
        upper = query.upper()
        assert "MATCH" in upper
        assert "RETURN" in upper
        for mutation in ("CREATE", "MERGE", " SET ", "DELETE", "REMOVE", "DROP"):
            assert mutation not in upper


def test_live_service_uses_execute_read_and_matches_same_revision_snapshot() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    driver = Driver(graph)
    retriever, service, trace = select_readonly_knowledge_service(
        canonical_graph_path=GRAPH_PATH,
        citation_registry_path=REGISTRY_PATH,
        settings=settings(),
        driver_factory=lambda *_args: driver,
    )
    snapshot_retriever, snapshot_service, _ = select_readonly_knowledge_service(
        canonical_graph_path=GRAPH_PATH,
        citation_registry_path=REGISTRY_PATH,
        settings={
            "NMA_GRAPH_BACKEND": "canonical-json",
            "NMA_GRAPH_FALLBACK": "canonical-json",
        },
    )
    kwargs = {
        "ranked_trace": [],
        "retrieval_mode": "test-fixed-seed",
        "max_depth": 3,
        "max_nodes": 300,
        "expand_product_fields": False,
    }
    live = retriever.package_from_seed_ids(
        "小學 9920103 圖式規則",
        ["code-value:landmark-type:9920103"],
        **kwargs,
    )
    snapshot = snapshot_retriever.package_from_seed_ids(
        "小學 9920103 圖式規則",
        ["code-value:landmark-type:9920103"],
        **kwargs,
    )
    assert projection(live) == projection(snapshot)
    assert driver.execute_read_calls > 1
    assert all(
        call["query"] in {READ_NODES_CYPHER, READ_INCIDENT_EDGES_CYPHER} for call in driver.queries
    )
    assert all("小學 9920103 圖式規則" not in call["query"] for call in driver.queries)
    assert trace["active_backend"] == "live-neo4j"
    assert trace["graph_identity_verified"] is True
    assert trace["credential_scope_required"] == "read-only"
    assert trace["mutation_allowed"] is False
    knowledge_trace = live["retrieval_trace"]["readonly_knowledge_service"]
    assert knowledge_trace["contract"] == KNOWLEDGE_SERVICE_CONTRACT
    assert knowledge_trace["active_backend"] == "live-neo4j"
    assert knowledge_trace["canonical_graph_sha256"] == trace["canonical_graph_sha256"]
    assert knowledge_trace["selected_node_ids"]
    assert knowledge_trace["selected_edge_ids"]
    serialized = json.dumps({"trace": trace, "package": live}, ensure_ascii=False)
    assert settings()["NEO4J_PASSWORD"] not in serialized
    assert settings()["NEO4J_USER"] not in serialized
    service.close()
    snapshot_service.close()
    assert driver.closed is True


def test_snapshot_service_preserves_all_fixed_v028_evidence_package_cases() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    specification = json.loads(PARITY_SPEC_PATH.read_text(encoding="utf-8"))
    retriever, service, _ = select_readonly_knowledge_service(
        canonical_graph_path=GRAPH_PATH,
        citation_registry_path=REGISTRY_PATH,
        settings={
            "NMA_GRAPH_BACKEND": "canonical-json",
            "NMA_GRAPH_FALLBACK": "canonical-json",
        },
    )
    legacy = retriever.local_retriever
    assert legacy.graph == graph
    for case in specification["cases"]:
        kwargs = {
            "ranked_trace": [],
            "retrieval_mode": "v028-fixed-case",
            "max_depth": int(case["max_depth"]),
            "max_nodes": int(case["max_nodes"]),
            "expand_product_fields": bool(case.get("expand_product_fields", False)),
        }
        expected = legacy.package_from_seed_ids(case["query"], list(case["seed_ids"]), **kwargs)
        actual = service.retrieve_evidence(case["query"], list(case["seed_ids"]), **kwargs)
        assert projection(actual) == projection(expected), case["id"]


def test_operation_registry_rejects_unknown_operations_and_extra_parameters() -> None:
    _, service, _ = select_readonly_knowledge_service(
        canonical_graph_path=GRAPH_PATH,
        citation_registry_path=REGISTRY_PATH,
        settings={
            "NMA_GRAPH_BACKEND": "canonical-json",
            "NMA_GRAPH_FALLBACK": "canonical-json",
        },
    )
    with pytest.raises(ReadOnlyKnowledgeServiceError, match="Unsupported operation"):
        service.execute("run_cypher", {"query": "MATCH (n) RETURN n"})
    with pytest.raises(ReadOnlyKnowledgeServiceError, match="Unsupported.*parameters"):
        service.execute(
            "retrieve_evidence",
            {
                "query": "school",
                "seed_ids": [],
                "ranked_trace": [],
                "retrieval_mode": "test",
                "max_depth": 1,
                "max_nodes": 10,
                "expand_product_fields": False,
                "cypher": "CREATE (n)",
            },
        )


def test_live_activation_requires_explicit_read_only_credential_scope() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    with pytest.raises(KnowledgeServiceConfigurationError, match="canonical fallback is disabled"):
        select_readonly_knowledge_service(
            canonical_graph_path=GRAPH_PATH,
            citation_registry_path=REGISTRY_PATH,
            settings=settings(NMA_NEO4J_CREDENTIAL_SCOPE=""),
            driver_factory=lambda *_args: Driver(graph),
        )


def test_projection_mismatch_uses_only_visible_same_revision_snapshot_fallback() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    changed = json.loads(json.dumps(graph))
    changed["nodes"][0]["properties"]["unreviewed_change"] = True
    _, service, trace = select_readonly_knowledge_service(
        canonical_graph_path=GRAPH_PATH,
        citation_registry_path=REGISTRY_PATH,
        settings=settings(NMA_GRAPH_FALLBACK="canonical-json"),
        driver_factory=lambda *_args: Driver(changed),
    )
    assert trace["active_backend"] == "canonical-json-snapshot"
    assert trace["fallback_used"] is True
    assert trace["fallback_reason_code"] == "neo4j-projection-mismatch"
    assert trace["fallback_identity"] == "same-canonical-revision-and-sha256"
    assert trace["graph_identity_verified"] is True
    assert service.adapter.backend_name == "canonical-json-snapshot"


def test_runtime_read_failure_fails_closed_without_per_request_backend_switch() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    driver = Driver(graph)
    retriever, service, trace = select_readonly_knowledge_service(
        canonical_graph_path=GRAPH_PATH,
        citation_registry_path=REGISTRY_PATH,
        settings=settings(NMA_GRAPH_FALLBACK="canonical-json"),
        driver_factory=lambda *_args: driver,
    )

    def unavailable(_node_id: str):
        raise ReadOnlyKnowledgeServiceError("simulated live read interruption")

    service.adapter.read_incident_edges = unavailable
    with pytest.raises(ReadOnlyKnowledgeServiceError, match="simulated live read interruption"):
        retriever.package_from_seed_ids(
            "小學 9920103 圖式規則",
            ["code-value:landmark-type:9920103"],
            ranked_trace=[],
            retrieval_mode="runtime-failure-test",
            max_depth=3,
            max_nodes=300,
            expand_product_fields=False,
        )
    assert trace["active_backend"] == "live-neo4j"
    assert trace["fallback_used"] is False
    assert service.adapter.backend_name == "live-neo4j"
    service.close()


def test_mutation_capability_is_absent_and_future_research_only() -> None:
    _, service, trace = select_readonly_knowledge_service(
        canonical_graph_path=GRAPH_PATH,
        citation_registry_path=REGISTRY_PATH,
        settings={
            "NMA_GRAPH_BACKEND": "canonical-json",
            "NMA_GRAPH_FALLBACK": "canonical-json",
        },
    )
    assert set(service.operation_registry) == {"retrieve_evidence"}
    assert not hasattr(service, "create_node")
    assert not hasattr(service, "update_graph")
    assert trace["autonomous_canonical_kg_modification"] == "future-research-only"
    assert trace["automatic_rule_activation"] is False


def test_existing_agent_server_routes_final_evidence_expansion_through_service(
    monkeypatch,
) -> None:
    monkeypatch.delenv("NMA_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("NEO4J_URI", raising=False)
    spec = importlib.util.spec_from_file_location("nma_agent_server_v033_test", SERVER_PATH)
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = server
    spec.loader.exec_module(server)
    package = server.school_hero_evidence_package()
    trace = package["retrieval_trace"]["readonly_knowledge_service"]
    public = server.public_graph_backend_trace_v031(server.graph_backend_trace())
    assert package["status"] == "retrieved"
    assert trace["operation"] == "retrieve_evidence"
    assert trace["active_backend"] == "canonical-json-snapshot"
    assert trace["read_transaction_calls"] > 1
    assert public["contract"] == KNOWLEDGE_SERVICE_CONTRACT
    assert public["mutation_allowed"] is False
    assert public["autonomous_canonical_kg_modification"] == "future-research-only"

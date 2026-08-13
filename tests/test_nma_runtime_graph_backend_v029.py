from __future__ import annotations

import json
from pathlib import Path

import pytest

from nma.neo4j_projection import node_rows
from nma.neo4j_roundtrip_v027 import projected_relationship_rows
from nma.runtime_graph_backend_v029 import (
    RuntimeGraphBackendError,
    load_runtime_graph_settings,
    select_runtime_graph_backend_v029,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
REGISTRY = ROOT / "data/knowledge/nma-citation-source-registry-v0.6.json"


class Result(list):
    pass


class Session:
    def __init__(self, graph: dict):
        self.graph = graph

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def run(self, query: str, parameters: dict):
        assert parameters["graph_revision"] == self.graph["graph_id"]
        if "RETURN node.id AS id" in query:
            return Result(node_rows(self.graph))
        if "RETURN source.id AS source" in query:
            return Result(projected_relationship_rows(self.graph))
        raise AssertionError(query)


class Driver:
    def __init__(self, graph: dict):
        self.graph = graph
        self.closed = False

    def verify_connectivity(self):
        return None

    def session(self, *, database: str):
        assert database == "mapfeatures"
        return Session(self.graph)

    def close(self):
        self.closed = True


def settings(**overrides: str) -> dict[str, str]:
    result = {
        "NMA_GRAPH_BACKEND": "neo4j",
        "NMA_GRAPH_FALLBACK": "canonical-json",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "not-a-real-secret",
        "NEO4J_DATABASE": "mapfeatures",
    }
    result.update(overrides)
    return result


def test_v029_local_loader_reads_only_allowlisted_settings(tmp_path: Path) -> None:
    local = tmp_path / ".env.local"
    local.write_text(
        "OPENAI_API_KEY=must-not-load\n"
        "NEO4J_URI=bolt://localhost:7687\n"
        "NEO4J_USER=neo4j\n"
        "NEO4J_PASSWORD=secret\n"
        "NEO4J_DATABASE=mapfeatures\n",
        encoding="utf-8",
    )
    loaded = load_runtime_graph_settings(local, environ={})
    assert "OPENAI_API_KEY" not in loaded
    assert loaded["NMA_GRAPH_BACKEND"] == "neo4j"
    assert loaded["NMA_GRAPH_FALLBACK"] == "canonical-json"


def test_v029_activates_identity_verified_live_neo4j() -> None:
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    driver = Driver(graph)
    retriever, trace = select_runtime_graph_backend_v029(
        canonical_graph_path=GRAPH,
        citation_registry_path=REGISTRY,
        settings=settings(),
        driver_factory=lambda *_args: driver,
    )
    assert retriever.graph["graph_id"] == graph["graph_id"]
    assert trace["requested_backend"] == "neo4j"
    assert trace["active_backend"] == "live-neo4j"
    assert trace["fallback_used"] is False
    assert trace["graph_identity_verified"] is True
    assert trace["live_nodes"] == 4293
    assert trace["live_edges"] == 11244
    assert trace["typed_tool_only"] is True
    assert trace["arbitrary_cypher_allowed"] is False
    assert driver.closed is True


def test_v029_projection_mismatch_uses_visible_canonical_fallback() -> None:
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    changed = json.loads(json.dumps(graph))
    changed["nodes"][0]["properties"]["v029_test_mutation"] = True
    retriever, trace = select_runtime_graph_backend_v029(
        canonical_graph_path=GRAPH,
        citation_registry_path=REGISTRY,
        settings=settings(),
        driver_factory=lambda *_args: Driver(changed),
    )
    assert retriever.graph["nodes"] == graph["nodes"]
    assert trace["active_backend"] == "canonical-json"
    assert trace["fallback_used"] is True
    assert trace["fallback_reason_code"] == "neo4j-projection-mismatch"
    assert trace["graph_identity_verified"] is False


def test_v029_fails_closed_when_fallback_is_disabled() -> None:
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    changed = json.loads(json.dumps(graph))
    changed["nodes"][0]["properties"]["v029_test_mutation"] = True
    with pytest.raises(RuntimeGraphBackendError, match="fallback is disabled"):
        select_runtime_graph_backend_v029(
            canonical_graph_path=GRAPH,
            citation_registry_path=REGISTRY,
            settings=settings(NMA_GRAPH_FALLBACK="none"),
            driver_factory=lambda *_args: Driver(changed),
        )

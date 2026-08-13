from __future__ import annotations

import json
from pathlib import Path

from nma.neo4j_projection import node_rows
from nma.neo4j_retrieval_v028 import evaluate_live_retrieval_parity_v028
from nma.neo4j_roundtrip_v027 import projected_relationship_rows


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
SPEC_PATH = ROOT / "data/specifications/nma-neo4j-retrieval-parity-v0.28.json"


class Result(list):
    def consume(self) -> None:
        return None


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
        raise AssertionError(f"Unexpected query: {query}")


class Driver:
    def __init__(self, graph: dict):
        self.graph = graph
        self.connectivity_verified = False
        self.database = None

    def verify_connectivity(self) -> None:
        self.connectivity_verified = True

    def session(self, *, database: str):
        self.database = database
        return Session(self.graph)


def test_v028_fixed_cases_precede_live_result_and_cover_required_behaviours() -> None:
    specification = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert specification["status"] == "prospective-fixed-cases-before-live-query"
    assert len(specification["cases"]) == 5
    assert {item["geometry"] for item in specification["cases"]} >= {
        "Point",
        "LineString",
        "Polygon",
    }
    assert {item["capability"] for item in specification["cases"]} >= {
        "conflict-preservation",
        "quality-evidence",
    }
    assert specification["automatic_acceptance"] is False


def test_v028_live_projection_reproduces_every_evidence_bearing_field() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    specification = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    driver = Driver(graph)
    report = evaluate_live_retrieval_parity_v028(
        driver,
        graph,
        specification,
        canonical_graph_path=GRAPH_PATH,
        database="mapfeatures",
    )
    assert driver.connectivity_verified is True
    assert driver.database == "mapfeatures"
    assert report["graph_identity_matches"] is True
    assert report["cases_passed"] == report["case_count"] == 5
    assert report["geometry_coverage"] == ["LineString", "Point", "Polygon"]
    assert all(item["parity"] is True for item in report["cases"])
    assert report["new_llm_calls"] == 0
    assert report["new_tokens"] == 0
    assert report["automatic_rule_activation"] is False
    assert report["map_mutations"] == 0

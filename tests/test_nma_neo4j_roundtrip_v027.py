from __future__ import annotations

import json
from pathlib import Path

import pytest

from nma.neo4j_projection import node_rows
from nma.neo4j_roundtrip_v027 import (
    NODE_ROUND_TRIP_CYPHER,
    RELATIONSHIP_ROUND_TRIP_CYPHER,
    SCHOOL_PATH_CYPHER,
    SCHOOL_PATH_IDS,
    Neo4jRoundTripError,
    build_offline_round_trip_preflight_v027,
    import_and_verify_neo4j_v027,
    projected_relationship_rows,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
REPORT_PATH = ROOT / "data/runtime/neo4j/nma-neo4j-round-trip-v0.27.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class FakeResult(list):
    def consume(self) -> None:
        return None


class FakeSession:
    def __init__(self, graph: dict) -> None:
        self.graph = graph
        self.writes = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def run(self, query: str, parameters: dict):
        if query == NODE_ROUND_TRIP_CYPHER:
            return FakeResult(node_rows(self.graph))
        if query == RELATIONSHIP_ROUND_TRIP_CYPHER:
            return FakeResult(projected_relationship_rows(self.graph))
        if query == SCHOOL_PATH_CYPHER:
            nodes = {item["id"]: item for item in self.graph["nodes"]}
            return FakeResult(
                [
                    {
                        **SCHOOL_PATH_IDS,
                        "rule_properties_json": json.dumps(
                            nodes[SCHOOL_PATH_IDS["rule_id"]]["properties"],
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                        "color_properties_json": json.dumps(
                            nodes[SCHOOL_PATH_IDS["color_id"]]["properties"],
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    }
                ]
            )
        self.writes.append((query, parameters))
        return FakeResult()


class FakeDriver:
    def __init__(self, graph: dict) -> None:
        self.connected = False
        self.database = None
        self.fake_session = FakeSession(graph)

    def verify_connectivity(self) -> None:
        self.connected = True

    def session(self, *, database: str):
        self.database = database
        return self.fake_session


def test_v027_checked_in_offline_round_trip_is_reproducible_and_honest() -> None:
    graph = load(GRAPH_PATH)
    checked_in = load(REPORT_PATH)
    current = build_offline_round_trip_preflight_v027(
        graph, graph_path=GRAPH_PATH, batch_size=500
    )

    assert checked_in == current
    assert checked_in["statistics"]["nodes"] == 4293
    assert checked_in["statistics"]["edges"] == 11244
    assert checked_in["offline_projection_round_trip_verified"] is True
    assert checked_in["canonical_reconstruction_lossless"] is True
    assert checked_in["live_import_executed"] is False
    assert checked_in["live_round_trip_verified"] is False


def test_v027_offline_school_path_preserves_black_official_baseline() -> None:
    school = load(REPORT_PATH)["school_path"]

    assert school["rule_id"] == "portrayal-rule:doc01:9920103"
    assert school["symbol_id"] == "symbol:doc01:school-flag"
    assert school["section_id"] == "section:doc01-portrayal:p61"
    assert school["page"] == 61
    assert school["color_code"] == "7"
    assert school["observed_color"] == "black"


def test_v027_live_adapter_imports_every_batch_and_validates_exact_round_trip() -> None:
    graph = load(GRAPH_PATH)
    driver = FakeDriver(graph)

    report = import_and_verify_neo4j_v027(
        driver, graph, graph_path=GRAPH_PATH, database="nma-test", batch_size=500
    )

    assert driver.connected is True
    assert driver.database == "nma-test"
    assert report["status"] == "live-neo4j-import-and-round-trip-verified"
    assert report["statistics"]["nodes"] == 4293
    assert report["statistics"]["edges"] == 11244
    assert report["school_path"]["observed_color"] == "black"
    assert report["live_import_executed"] is True
    assert report["live_round_trip_verified"] is True
    # Constraint + index + nine node batches + 76 relationship batches.
    assert len(driver.fake_session.writes) == 87
    assert not any("DELETE" in query.upper() for query, _ in driver.fake_session.writes)


def test_v027_live_adapter_rejects_an_object_without_connectivity_check() -> None:
    with pytest.raises(Neo4jRoundTripError, match="verify_connectivity"):
        import_and_verify_neo4j_v027(
            object(), load(GRAPH_PATH), graph_path=GRAPH_PATH
        )

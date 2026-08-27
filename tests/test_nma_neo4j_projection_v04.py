import importlib.util
import json
from pathlib import Path

import pytest

from nma.neo4j_projection import (
    Neo4jProjectionError,
    build_projection_manifest,
    node_rows,
    relationship_rows_by_type,
    relationship_upsert_cypher,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
MANIFEST = ROOT / "data/runtime/neo4j/nma-neo4j-projection-v0.4.json"
BUILDER = ROOT / "scripts/build_nma_neo4j_projection_v04.py"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_neo4j_projection_preserves_every_canonical_node_and_edge() -> None:
    graph = _load(GRAPH)
    nodes = node_rows(graph)
    relationships = relationship_rows_by_type(graph)

    assert len(nodes) == graph["statistics"]["nodes"]
    assert sum(len(rows) for rows in relationships.values()) == graph["statistics"]["edges"]
    assert len({node["id"] for node in nodes}) == len(nodes)
    assert all(row["properties_json"].startswith("{") for row in nodes)


def test_checked_in_projection_manifest_is_reproducible_and_non_executing() -> None:
    graph = _load(GRAPH)
    checked_in = _load(MANIFEST)
    compiled = build_projection_manifest(graph, graph_path=GRAPH, batch_size=500)
    compiled["canonical_source"] = GRAPH.relative_to(ROOT).as_posix()

    assert checked_in == compiled
    assert checked_in["statistics"]["nodes"] == 4293
    assert checked_in["statistics"]["edges"] == 11244
    assert checked_in["live_import_executed"] is False
    assert checked_in["round_trip_verified"] is False
    assert checked_in["automatic_rule_activation"] is False
    assert checked_in["source_of_truth"].startswith("version-controlled canonical JSON")


def test_projection_uses_parameter_rows_and_allowlisted_relationship_types() -> None:
    manifest = _load(MANIFEST)

    assert "UNWIND $rows" in manifest["cypher_contract"]["node_upsert"]
    assert "REQUIRE node.id IS UNIQUE" in manifest["cypher_contract"]["constraint"]
    assert all(
        f"[rel:{relationship_type} " in cypher
        for relationship_type, cypher in manifest["cypher_contract"][
            "relationship_upserts"
        ].items()
    )
    with pytest.raises(Neo4jProjectionError, match="Unsafe"):
        relationship_upsert_cypher("HAS_FIELD) DELETE node")


def test_projection_builder_module_loads_without_neo4j_dependency() -> None:
    spec = importlib.util.spec_from_file_location("nma_neo4j_builder_v04", BUILDER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

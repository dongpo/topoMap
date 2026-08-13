from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from nma.neo4j_projection import (
    CONSTRAINT_CYPHER,
    NODE_UPSERT_CYPHER,
    TYPE_INDEX_CYPHER,
    build_projection_manifest,
    iter_batches,
    node_rows,
    relationship_rows_by_type,
    relationship_upsert_cypher,
)


NODE_ROUND_TRIP_CYPHER = """MATCH (node:NMAEntity {graph_revision: $graph_revision})
RETURN node.id AS id,
       node.entity_type AS entity_type,
       node.properties_json AS properties_json,
       node.source_graphs AS source_graphs
ORDER BY id
"""

RELATIONSHIP_ROUND_TRIP_CYPHER = """MATCH (source:NMAEntity)-[rel]->(target:NMAEntity)
WHERE rel.graph_revision = $graph_revision
RETURN source.id AS source,
       type(rel) AS relationship_type,
       target.id AS target,
       rel.nma_key AS key,
       rel.properties_json AS properties_json,
       rel.source_graphs AS source_graphs
ORDER BY relationship_type, source, target, key
"""

SCHOOL_PATH_CYPHER = """MATCH (code:NMAEntity {id: $code_id})
      -[portrayed:PORTRAYED_BY]->
      (rule:NMAEntity {id: $rule_id})
MATCH (rule)-[uses_symbol:USES_SYMBOL]->(symbol:NMAEntity {id: $symbol_id})
MATCH (rule)-[evidenced:EVIDENCED_ON]->(section:NMAEntity {id: $section_id})
MATCH (rule)-[uses_color:USES_COLOR]->(color:NMAEntity {id: $color_id})
WHERE code.graph_revision = $graph_revision
  AND rule.graph_revision = $graph_revision
  AND symbol.graph_revision = $graph_revision
  AND section.graph_revision = $graph_revision
  AND color.graph_revision = $graph_revision
  AND portrayed.graph_revision = $graph_revision
  AND uses_symbol.graph_revision = $graph_revision
  AND evidenced.graph_revision = $graph_revision
  AND uses_color.graph_revision = $graph_revision
RETURN code.id AS code_id,
       rule.id AS rule_id,
       symbol.id AS symbol_id,
       section.id AS section_id,
       color.id AS color_id,
       rule.properties_json AS rule_properties_json,
       color.properties_json AS color_properties_json
"""

SCHOOL_PATH_IDS = {
    "code_id": "code-value:landmark-type:9920103",
    "rule_id": "portrayal-rule:doc01:9920103",
    "symbol_id": "symbol:doc01:school-flag",
    "section_id": "section:doc01-portrayal:p61",
    "color_id": "portrayal-color:doc01:7",
}


class Neo4jRoundTripError(RuntimeError):
    """A live or offline Neo4j projection failed an identity-preserving check."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _rows_sha256(rows: list[dict[str, Any]]) -> str:
    return hashlib.sha256(_canonical_json(rows).encode("utf-8")).hexdigest()


def projected_relationship_rows(graph: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for relationship_type, values in relationship_rows_by_type(graph).items():
        rows.extend({"relationship_type": relationship_type, **item} for item in values)
    return sorted(
        rows,
        key=lambda item: (
            item["relationship_type"],
            item["source"],
            item["target"],
            item["properties_json"],
            item["key"],
        ),
    )


def _school_path_from_canonical(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = {item["id"]: item for item in graph["nodes"]}
    edges = {(item["source"], item["type"], item["target"]) for item in graph["edges"]}
    required_edges = {
        (SCHOOL_PATH_IDS["code_id"], "PORTRAYED_BY", SCHOOL_PATH_IDS["rule_id"]),
        (SCHOOL_PATH_IDS["rule_id"], "USES_SYMBOL", SCHOOL_PATH_IDS["symbol_id"]),
        (SCHOOL_PATH_IDS["rule_id"], "EVIDENCED_ON", SCHOOL_PATH_IDS["section_id"]),
        (SCHOOL_PATH_IDS["rule_id"], "USES_COLOR", SCHOOL_PATH_IDS["color_id"]),
    }
    missing_nodes = sorted(set(SCHOOL_PATH_IDS.values()) - set(nodes))
    missing_edges = sorted(required_edges - edges)
    if missing_nodes or missing_edges:
        raise Neo4jRoundTripError(
            f"Canonical school path is incomplete: nodes={missing_nodes}, edges={missing_edges}"
        )
    rule = nodes[SCHOOL_PATH_IDS["rule_id"]]["properties"]
    color = nodes[SCHOOL_PATH_IDS["color_id"]]["properties"]
    if rule.get("page") != 61 or rule.get("color_code") != "7":
        raise Neo4jRoundTripError("Canonical school rule has unexpected page or colour code.")
    if color.get("observed_color") != "black":
        raise Neo4jRoundTripError("Canonical school colour reference is not visually black.")
    return {
        **SCHOOL_PATH_IDS,
        "page": rule["page"],
        "color_code": rule["color_code"],
        "observed_color": color["observed_color"],
        "required_edge_count": len(required_edges),
    }


def build_offline_round_trip_preflight_v027(
    graph: dict[str, Any], *, graph_path: str | Path, batch_size: int = 500
) -> dict[str, Any]:
    manifest = build_projection_manifest(graph, graph_path=graph_path, batch_size=batch_size)
    nodes = node_rows(graph)
    relationships = projected_relationship_rows(graph)
    reconstructed_nodes = [
        {
            "id": item["id"],
            "type": item["entity_type"],
            "properties": json.loads(item["properties_json"]),
            **({"source_graphs": item["source_graphs"]} if item["source_graphs"] else {}),
        }
        for item in nodes
    ]
    reconstructed_edges = [
        {
            "source": item["source"],
            "type": item["relationship_type"],
            "target": item["target"],
            "properties": json.loads(item["properties_json"]),
            **({"source_graphs": item["source_graphs"]} if item["source_graphs"] else {}),
        }
        for item in relationships
    ]
    source_nodes = sorted(graph["nodes"], key=lambda item: item["id"])
    source_edges = sorted(
        graph["edges"],
        key=lambda item: (
            item["type"], item["source"], item["target"], _canonical_json(item.get("properties", {}))
        ),
    )
    lossless = reconstructed_nodes == source_nodes and reconstructed_edges == source_edges
    if not lossless:
        raise Neo4jRoundTripError("The offline Neo4j row projection is not lossless.")
    return {
        "schema": "nma.neo4j-round-trip-preflight/0.27",
        "status": "offline-projection-round-trip-verified; live-neo4j-import-not-run",
        "canonical_graph_id": graph["graph_id"],
        "canonical_graph_sha256": manifest["canonical_graph_sha256"],
        "graph_revision": manifest["graph_revision"],
        "batch_size": batch_size,
        "statistics": manifest["statistics"],
        "node_rows_sha256": _rows_sha256(nodes),
        "relationship_rows_sha256": _rows_sha256(relationships),
        "offline_projection_round_trip_verified": True,
        "canonical_reconstruction_lossless": True,
        "school_path": _school_path_from_canonical(graph),
        "live_import_executed": False,
        "live_round_trip_verified": False,
        "automatic_rule_activation": False,
        "source_of_truth": manifest["source_of_truth"],
        "claim_boundary": (
            "Lossless offline verification of the exact Neo4j node/relationship payload and "
            "the school evidence path. No Neo4j server accepted these writes and no live "
            "round-trip claim is allowed."
        ),
    }


def _consume(result: Any) -> None:
    consume = getattr(result, "consume", None)
    if callable(consume):
        consume()


def _result_rows(result: Any) -> list[dict[str, Any]]:
    return [dict(record) for record in result]


def _run_write(session: Any, query: str, parameters: dict[str, Any]) -> None:
    result = session.run(query, parameters)
    _consume(result)


def import_and_verify_neo4j_v027(
    driver: Any,
    graph: dict[str, Any],
    *,
    graph_path: str | Path,
    database: str = "neo4j",
    batch_size: int = 500,
) -> dict[str, Any]:
    verify_connectivity = getattr(driver, "verify_connectivity", None)
    if not callable(verify_connectivity):
        raise Neo4jRoundTripError("A Neo4j driver with verify_connectivity() is required.")
    verify_connectivity()
    manifest = build_projection_manifest(graph, graph_path=graph_path, batch_size=batch_size)
    revision = manifest["graph_revision"]
    expected_nodes = node_rows(graph)
    expected_relationships = projected_relationship_rows(graph)
    with driver.session(database=database) as session:
        _run_write(session, CONSTRAINT_CYPHER, {})
        _run_write(session, TYPE_INDEX_CYPHER, {})
        for batch in iter_batches(expected_nodes, batch_size):
            _run_write(
                session,
                NODE_UPSERT_CYPHER,
                {"rows": batch, "graph_revision": revision},
            )
        for relationship_type, rows in relationship_rows_by_type(graph).items():
            cypher = relationship_upsert_cypher(relationship_type)
            for batch in iter_batches(rows, batch_size):
                _run_write(
                    session,
                    cypher,
                    {"rows": batch, "graph_revision": revision},
                )
        actual_nodes = _result_rows(
            session.run(NODE_ROUND_TRIP_CYPHER, {"graph_revision": revision})
        )
        actual_relationships = _result_rows(
            session.run(RELATIONSHIP_ROUND_TRIP_CYPHER, {"graph_revision": revision})
        )
        school_rows = _result_rows(
            session.run(
                SCHOOL_PATH_CYPHER,
                {**SCHOOL_PATH_IDS, "graph_revision": revision},
            )
        )
    actual_nodes = sorted(actual_nodes, key=lambda item: item["id"])
    actual_relationships = sorted(
        actual_relationships,
        key=lambda item: (
            item["relationship_type"],
            item["source"],
            item["target"],
            item["properties_json"],
            item["key"],
        ),
    )
    nodes_match = actual_nodes == expected_nodes
    relationships_match = actual_relationships == expected_relationships
    if len(school_rows) != 1:
        raise Neo4jRoundTripError("The live Neo4j school path did not return exactly one row.")
    school = school_rows[0]
    rule_properties = json.loads(school["rule_properties_json"])
    color_properties = json.loads(school["color_properties_json"])
    school_matches = (
        {key: school[key] for key in SCHOOL_PATH_IDS} == SCHOOL_PATH_IDS
        and rule_properties.get("page") == 61
        and rule_properties.get("color_code") == "7"
        and color_properties.get("observed_color") == "black"
    )
    if not nodes_match or not relationships_match or not school_matches:
        raise Neo4jRoundTripError(
            "The live Neo4j round trip differs from the canonical graph projection."
        )
    return {
        "schema": "nma.neo4j-live-round-trip/0.27",
        "status": "live-neo4j-import-and-round-trip-verified",
        "database": database,
        "canonical_graph_id": graph["graph_id"],
        "canonical_graph_sha256": manifest["canonical_graph_sha256"],
        "graph_revision": revision,
        "statistics": {
            "nodes": len(actual_nodes),
            "edges": len(actual_relationships),
            "node_types": dict(sorted(Counter(item["entity_type"] for item in actual_nodes).items())),
        },
        "node_rows_sha256": _rows_sha256(actual_nodes),
        "relationship_rows_sha256": _rows_sha256(actual_relationships),
        "school_path": {
            **SCHOOL_PATH_IDS,
            "page": rule_properties["page"],
            "color_code": rule_properties["color_code"],
            "observed_color": color_properties["observed_color"],
        },
        "live_import_executed": True,
        "live_round_trip_verified": True,
        "automatic_rule_activation": False,
        "source_of_truth": manifest["source_of_truth"],
    }


def open_neo4j_driver(uri: str, user: str, password: str) -> Any:
    try:
        from neo4j import GraphDatabase
    except ImportError as error:
        raise Neo4jRoundTripError(
            "The optional Neo4j Python driver is not installed; install the project neo4j extra."
        ) from error
    return GraphDatabase.driver(uri, auth=(user, password))

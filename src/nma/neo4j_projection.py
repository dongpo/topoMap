from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


RELATIONSHIP_TYPE = re.compile(r"^[A-Z][A-Z0-9_]*$")
NODE_UPSERT_CYPHER = """UNWIND $rows AS row
MERGE (node:NMAEntity {id: row.id})
SET node.entity_type = row.entity_type,
    node.properties_json = row.properties_json,
    node.source_graphs = row.source_graphs,
    node.graph_revision = $graph_revision
"""
CONSTRAINT_CYPHER = (
    "CREATE CONSTRAINT nma_entity_id IF NOT EXISTS "
    "FOR (node:NMAEntity) REQUIRE node.id IS UNIQUE"
)
TYPE_INDEX_CYPHER = (
    "CREATE INDEX nma_entity_type IF NOT EXISTS FOR (node:NMAEntity) ON (node.entity_type)"
)


class Neo4jProjectionError(ValueError):
    """The canonical graph cannot be projected without losing graph identity."""


def canonical_graph_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _properties_json(value: Any) -> str:
    return json.dumps(value if isinstance(value, dict) else {}, ensure_ascii=False, sort_keys=True)


def node_rows(graph: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for node in sorted(graph["nodes"], key=lambda item: item["id"]):
        rows.append(
            {
                "id": node["id"],
                "entity_type": node["type"],
                "properties_json": _properties_json(node.get("properties", {})),
                "source_graphs": sorted(node.get("source_graphs", [])),
            }
        )
    return rows


def relationship_rows_by_type(
    graph: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_keys: set[str] = set()
    for edge in sorted(
        graph["edges"],
        key=lambda item: (
            item["type"],
            item["source"],
            item["target"],
            _properties_json(item.get("properties", {})),
        ),
    ):
        relationship_type = edge["type"]
        if not RELATIONSHIP_TYPE.fullmatch(relationship_type):
            raise Neo4jProjectionError(
                f"Unsafe Neo4j relationship type: {relationship_type!r}."
            )
        stable_key = hashlib.sha256(
            json.dumps(
                {
                    "source": edge["source"],
                    "type": relationship_type,
                    "target": edge["target"],
                    "properties": edge.get("properties", {}),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        if stable_key in seen_keys:
            raise Neo4jProjectionError(f"Duplicate relationship projection key: {stable_key}.")
        seen_keys.add(stable_key)
        grouped[relationship_type].append(
            {
                "key": stable_key,
                "source": edge["source"],
                "target": edge["target"],
                "properties_json": _properties_json(edge.get("properties", {})),
                "source_graphs": sorted(edge.get("source_graphs", [])),
            }
        )
    return dict(sorted(grouped.items()))


def relationship_upsert_cypher(relationship_type: str) -> str:
    if not RELATIONSHIP_TYPE.fullmatch(relationship_type):
        raise Neo4jProjectionError(
            f"Unsafe Neo4j relationship type: {relationship_type!r}."
        )
    return f"""UNWIND $rows AS row
MATCH (source:NMAEntity {{id: row.source}})
MATCH (target:NMAEntity {{id: row.target}})
MERGE (source)-[rel:{relationship_type} {{nma_key: row.key}}]->(target)
SET rel.properties_json = row.properties_json,
    rel.source_graphs = row.source_graphs,
    rel.graph_revision = $graph_revision
"""


def iter_batches(rows: list[dict[str, Any]], batch_size: int) -> Iterable[list[dict[str, Any]]]:
    if batch_size < 1:
        raise Neo4jProjectionError("Neo4j batch size must be positive.")
    for index in range(0, len(rows), batch_size):
        yield rows[index : index + batch_size]


def build_projection_manifest(
    graph: dict[str, Any], *, graph_path: str | Path, batch_size: int = 500
) -> dict[str, Any]:
    if graph.get("integrity", {}).get("missing_edge_endpoints"):
        raise Neo4jProjectionError("Canonical graph has missing edge endpoints.")
    nodes = node_rows(graph)
    relationships = relationship_rows_by_type(graph)
    edge_count = sum(len(rows) for rows in relationships.values())
    if len(nodes) != graph["statistics"]["nodes"] or edge_count != graph["statistics"]["edges"]:
        raise Neo4jProjectionError("Projection counts differ from the canonical graph.")
    node_type_counts = Counter(row["entity_type"] for row in nodes)
    return {
        "schema": "nma.neo4j-projection-manifest/0.4",
        "status": "reproducible-projection-ready; live-neo4j-import-not-run",
        "canonical_source": str(Path(graph_path).as_posix()),
        "canonical_graph_id": graph["graph_id"],
        "canonical_graph_sha256": canonical_graph_sha256(graph_path),
        "graph_revision": graph["graph_id"],
        "batch_size": batch_size,
        "statistics": {
            "nodes": len(nodes),
            "edges": edge_count,
            "node_types": dict(sorted(node_type_counts.items())),
            "relationship_types": {
                relationship_type: len(rows)
                for relationship_type, rows in relationships.items()
            },
            "node_batches": len(list(iter_batches(nodes, batch_size))),
            "relationship_batches": sum(
                len(list(iter_batches(rows, batch_size)))
                for rows in relationships.values()
            ),
        },
        "cypher_contract": {
            "constraint": CONSTRAINT_CYPHER,
            "type_index": TYPE_INDEX_CYPHER,
            "node_upsert": NODE_UPSERT_CYPHER,
            "relationship_upserts": {
                relationship_type: relationship_upsert_cypher(relationship_type)
                for relationship_type in relationships
            },
        },
        "source_of_truth": "version-controlled canonical JSON; Neo4j is a rebuildable runtime projection",
        "live_import_executed": False,
        "round_trip_verified": False,
        "automatic_rule_activation": False,
    }

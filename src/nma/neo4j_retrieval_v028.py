from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from nma.graphrag import CanonicalGraphRetriever
from nma.neo4j_roundtrip_v027 import (
    NODE_ROUND_TRIP_CYPHER,
    RELATIONSHIP_ROUND_TRIP_CYPHER,
    Neo4jRoundTripError,
)


class Neo4jRetrievalParityError(RuntimeError):
    """The live Neo4j projection cannot reproduce the canonical evidence contract."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _rows(result: Any) -> list[dict[str, Any]]:
    return [dict(record) for record in result]


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


def load_live_projection_v028(
    driver: Any, *, database: str, graph_revision: str
) -> dict[str, Any]:
    """Read one immutable graph revision from Neo4j and reconstruct its canonical shape."""

    verify_connectivity = getattr(driver, "verify_connectivity", None)
    if not callable(verify_connectivity):
        raise Neo4jRetrievalParityError("A Neo4j driver with verify_connectivity() is required.")
    verify_connectivity()
    with driver.session(database=database) as session:
        node_records = _rows(
            session.run(NODE_ROUND_TRIP_CYPHER, {"graph_revision": graph_revision})
        )
        relationship_records = _rows(
            session.run(
                RELATIONSHIP_ROUND_TRIP_CYPHER,
                {"graph_revision": graph_revision},
            )
        )
    nodes = [
        {
            "id": item["id"],
            "type": item["entity_type"],
            "properties": json.loads(item["properties_json"]),
            **(
                {"source_graphs": list(item["source_graphs"])}
                if item.get("source_graphs")
                else {}
            ),
        }
        for item in node_records
    ]
    edges = [
        {
            "source": item["source"],
            "type": item["relationship_type"],
            "target": item["target"],
            "properties": json.loads(item["properties_json"]),
            **(
                {"source_graphs": list(item["source_graphs"])}
                if item.get("source_graphs")
                else {}
            ),
        }
        for item in relationship_records
    ]
    node_ids = [item["id"] for item in nodes]
    if len(node_ids) != len(set(node_ids)):
        raise Neo4jRetrievalParityError("The live projection contains duplicate node IDs.")
    known = set(node_ids)
    missing = sorted(
        {
            endpoint
            for edge in edges
            for endpoint in (edge["source"], edge["target"])
            if endpoint not in known
        }
    )
    if missing:
        raise Neo4jRetrievalParityError(
            f"The live projection contains missing relationship endpoints: {missing[:5]}"
        )
    return {
        "graph_id": graph_revision,
        "nodes": _normal_nodes({"nodes": nodes}),
        "edges": _normal_edges({"edges": edges}),
        "statistics": {"nodes": len(nodes), "edges": len(edges)},
        "integrity": {"missing_edge_endpoints": []},
    }


def _package_projection(package: dict[str, Any]) -> dict[str, Any]:
    """Keep every evidence-bearing field while excluding backend trace labels."""

    return {
        "status": package["status"],
        "resolved_entities": sorted(
            package["resolved_entities"], key=lambda item: item["id"]
        ),
        "evidence_nodes": sorted(package["evidence_nodes"], key=lambda item: item["id"]),
        "graph_nodes": sorted(package["graph_paths"]["nodes"]),
        "graph_edges": sorted(
            package["graph_paths"]["edges"],
            key=lambda item: (item["type"], item["source"], item["target"]),
        ),
        "source_documents": sorted(
            package["source_documents"], key=_canonical_json
        ),
        "source_sections": sorted(package["source_sections"], key=_canonical_json),
        "citations": sorted(
            package["citations"], key=lambda item: item["citation_id"]
        ),
        "conflicts": sorted(package["conflicts"], key=_canonical_json),
        "clarification": package["clarification"],
        "missing_evidence": package["missing_evidence"],
        "automatic_rule_activation": package["automatic_rule_activation"],
    }


def _package_for_case(
    retriever: CanonicalGraphRetriever,
    case: dict[str, Any],
    *,
    backend: str,
) -> dict[str, Any]:
    seed_ids = list(case["seed_ids"])
    ranked_trace = [
        {
            "id": node_id,
            "type": retriever.nodes[node_id]["type"],
            "score": 1,
            "matched_terms": [case["query"]],
            "match_mode": "prospective-fixed-canonical-seed",
        }
        for node_id in seed_ids
        if node_id in retriever.nodes
    ]
    return retriever.package_from_seed_ids(
        case["query"],
        seed_ids,
        ranked_trace=ranked_trace,
        retrieval_mode=f"v0.28-{backend}-typed-graph-expansion",
        max_depth=int(case["max_depth"]),
        max_nodes=int(case["max_nodes"]),
        expand_product_fields=bool(case.get("expand_product_fields", False)),
    )


def evaluate_live_retrieval_parity_v028(
    driver: Any,
    canonical_graph: dict[str, Any],
    specification: dict[str, Any],
    *,
    canonical_graph_path: str | Path,
    database: str,
) -> dict[str, Any]:
    revision = canonical_graph["graph_id"]
    live_graph = load_live_projection_v028(
        driver, database=database, graph_revision=revision
    )
    canonical_nodes = _normal_nodes(canonical_graph)
    canonical_edges = _normal_edges(canonical_graph)
    graph_identity_matches = (
        canonical_nodes == live_graph["nodes"]
        and canonical_edges == live_graph["edges"]
    )
    if not graph_identity_matches:
        raise Neo4jRetrievalParityError(
            "The live Neo4j revision is not identical to the canonical graph."
        )

    canonical_retriever = CanonicalGraphRetriever(
        {**canonical_graph, "nodes": canonical_nodes, "edges": canonical_edges}
    )
    neo4j_retriever = CanonicalGraphRetriever(live_graph)
    cases = []
    for case in specification["cases"]:
        missing_seeds = sorted(set(case["seed_ids"]) - set(canonical_retriever.nodes))
        if missing_seeds:
            raise Neo4jRetrievalParityError(
                f"Case {case['id']} has unknown canonical seeds: {missing_seeds}"
            )
        canonical_package = _package_for_case(
            canonical_retriever, case, backend="canonical-json"
        )
        neo4j_package = _package_for_case(
            neo4j_retriever, case, backend="live-neo4j"
        )
        canonical_projection = _package_projection(canonical_package)
        neo4j_projection = _package_projection(neo4j_package)
        parity = canonical_projection == neo4j_projection
        if not parity:
            raise Neo4jRetrievalParityError(
                f"Evidence-package parity failed for case {case['id']}."
            )
        cases.append(
            {
                "id": case["id"],
                "geometry": case.get("geometry"),
                "capability": case["capability"],
                "status": neo4j_package["status"],
                "seed_ids": case["seed_ids"],
                "evidence_nodes": len(neo4j_package["evidence_nodes"]),
                "graph_edges": len(neo4j_package["graph_paths"]["edges"]),
                "citations": len(neo4j_package["citations"]),
                "conflicts": len(neo4j_package["conflicts"]),
                "package_sha256": _sha256(neo4j_projection),
                "parity": True,
            }
        )

    graph_path = Path(canonical_graph_path)
    return {
        "schema": "nma.neo4j-graphrag-retrieval-parity/0.28",
        "status": "live-neo4j-graphrag-retrieval-parity-verified",
        "database": database,
        "canonical_graph_id": revision,
        "canonical_graph_sha256": hashlib.sha256(graph_path.read_bytes()).hexdigest(),
        "live_graph_nodes": len(live_graph["nodes"]),
        "live_graph_edges": len(live_graph["edges"]),
        "graph_identity_matches": True,
        "case_count": len(cases),
        "cases_passed": sum(item["parity"] for item in cases),
        "geometry_coverage": sorted(
            {item["geometry"] for item in cases if item.get("geometry")}
        ),
        "cases": cases,
        "live_neo4j_read_executed": True,
        "retrieval_parity_verified": True,
        "new_llm_calls": 0,
        "new_tokens": 0,
        "automatic_rule_activation": False,
        "map_mutations": 0,
        "source_of_truth": (
            "version-controlled canonical JSON; Neo4j is a rebuildable runtime projection"
        ),
        "claim_boundary": (
            "This verifies that a live Neo4j projection reproduces canonical typed-graph "
            "evidence packages for the sealed v0.28 cases. Fixed canonical seeds isolate graph "
            "backend parity; this does not evaluate entity resolution, LLM answers, arbitrary "
            "Cypher generation, portrayal execution, or map rendering."
        ),
    }


def open_neo4j_driver(uri: str, user: str, password: str) -> Any:
    try:
        from neo4j import GraphDatabase
    except ImportError as error:
        raise Neo4jRoundTripError(
            "The optional Neo4j Python driver is not installed; install the project neo4j extra."
        ) from error
    return GraphDatabase.driver(
        uri,
        auth=(user, password),
        connection_timeout=3.0,
        connection_acquisition_timeout=3.0,
    )

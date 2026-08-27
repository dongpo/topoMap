#!/usr/bin/env python3
"""Build the browser runtime projection from the frozen NMA canonical graph.

The Pages application never owns a hand-written classification table.  This
builder reads the frozen graph object, keeps the nodes and edges needed by the
School/ROAD/BUILD application, and writes a small, auditable projection.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public/gh-pages/data/nma-runtime-knowledge-v0.4.json"
FROZEN_REF = "refs/tags/nma-v1.0-final"
GRAPH_PATH = "data/knowledge/nma-canonical-graph-v0.4.json"


def git_object(path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{FROZEN_REF}:{path}"], cwd=ROOT
    )


def relevant_code(value: object) -> bool:
    code = str(value or "")
    return code.startswith(("931", "942", "99201"))


def node_is_relevant(node: dict[str, object]) -> bool:
    node_id = str(node.get("id", ""))
    node_type = str(node.get("type", ""))
    props = node.get("properties") or {}
    if not isinstance(props, dict):
        props = {}

    if node_type == "SpecificationDocument":
        return node_id in {
            "document:doc01-portrayal",
            "document:doc02-1000-production",
            "document:doc09-temap-layers",
        }
    if node_type == "ProductLayer":
        return str(props.get("id", "")) in {"MARK", "ROAD", "BUILD"}
    if node_type == "ProductField":
        return str(props.get("layer", "")) in {"MARK", "ROAD", "BUILD"}
    if node_type == "TerrainClassificationCode":
        return True
    if node_type in {
        "ClassificationCode",
        "ClassificationHierarchy",
        "ClassificationOccurrence",
        "PortrayalRule",
        "PortrayalRecipe",
        "VectorPrimitive",
        "ActivationGate",
    }:
        return relevant_code(props.get("code") or props.get("feature_code")) or any(
            token in node_id for token in ("931", "942", "99201")
        )
    if node_type in {
        "DatasetFieldObservation",
        "EvidenceObservation",
        "ImplementationObservation",
    }:
        text = json.dumps(node, ensure_ascii=False)
        return any(token in text for token in ("MARK", "ROAD", "BUILD", "TERRAINID"))
    return False


def main() -> None:
    graph_bytes = git_object(GRAPH_PATH)
    graph = json.loads(graph_bytes)
    nodes = [node for node in graph["nodes"] if node_is_relevant(node)]
    node_ids = {node["id"] for node in nodes}

    edges = [
        edge
        for edge in graph["edges"]
        if edge.get("source") in node_ids and edge.get("target") in node_ids
    ]
    nodes.sort(key=lambda item: item["id"])
    edges.sort(key=lambda item: (item["source"], item["type"], item["target"]))

    projection = {
        "projection_id": "nma-pages-runtime-knowledge-v0.4",
        "projection_status": "derived-from-frozen-canonical-graph; non-production",
        "source": {
            "ref": FROZEN_REF,
            "commit": "eb87bde775333811529efb6f651573ea21cf456b",
            "graph_id": graph["graph_id"],
            "graph_path": GRAPH_PATH,
            "graph_sha256": hashlib.sha256(graph_bytes).hexdigest(),
            "graph_status": graph["status"],
        },
        "task_profiles": {
            "school": {
                "title": "學校及訓練機構",
                "layer": "MARK",
                "geometry": "Point",
                "classification_root": "9920100",
                "required_input_classification_field": "TERRAINID",
                "canonical_classification_fields": ["MARKTYPE1", "MARKTYPE2"],
                "identity_fields": ["MARKID"],
                "label_fields": ["MARKNAME1"],
            },
            "road": {
                "title": "道路",
                "layer": "ROAD",
                "geometry": "LineString",
                "classification_root": "9420000",
                "required_input_classification_field": "TERRAINID",
                "canonical_classification_fields": ["ROADCLASS2"],
                "identity_fields": ["ROADSEGID"],
                "label_fields": ["ROADNAME"],
            },
            "build": {
                "title": "建物",
                "layer": "BUILD",
                "geometry": "Polygon",
                "classification_root": "9310000",
                "required_input_classification_field": "TERRAINID",
                "canonical_classification_fields": [],
                "identity_fields": ["BUILD_ID", "ID"],
                "label_fields": [],
            },
        },
        "governance": {
            "unknown_mapping_action": "ask-user",
            "session_mapping_scope": "current-browser-run-only",
            "session_mapping_reuse": False,
            "persistent_mapping_requires": "human-review-and-versioned-KG-update",
            "source_identity": "normalized-zip-relative-filename + source-id",
            "renderer_record_key": "source-identity + source-record-index",
            "production_activation": False,
        },
        "statistics": {"nodes": len(nodes), "edges": len(edges)},
        "nodes": nodes,
        "edges": edges,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(projection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

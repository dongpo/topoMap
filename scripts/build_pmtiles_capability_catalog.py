#!/usr/bin/env python3
"""Compile the PMTiles demo registry into an auditable Agent capability catalog."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUP_PATTERN = re.compile(r'"([^"]+)"\s*:\s*\[(.*?)\]', re.DOTALL)
ENTRY_PATTERN = re.compile(
    r'\{\s*tid:\s*"([^"]+)"\s*,\s*label:\s*"([^"]+)"\s*\}'
)


def _pmtiles_entries(source: Path) -> list[dict[str, str]]:
    text = source.read_text(encoding="utf-8")
    try:
        block = text.split("const TERRAINID_GROUPS = {", 1)[1].split("};", 1)[0]
    except IndexError as exc:
        raise ValueError("pmtilesDemo.html has no TERRAINID_GROUPS registry") from exc
    entries: list[dict[str, str]] = []
    for category, body in GROUP_PATTERN.findall(block):
        for code, label in ENTRY_PATTERN.findall(body):
            entries.append({"code": code, "label": label, "category": category})
    if len(entries) != 42:
        raise ValueError(f"expected 42 PMTiles capabilities, found {len(entries)}")
    return entries


def _renderer(code: str, category: str) -> tuple[str, list[str], list[str]]:
    school_codes = {f"992010{value}" for value in range(1, 7)}
    renderers = {
        "9350902": "pavilion",
        "9420101": "tw-highway-shield",
        "9420201": "tw-primary-shield",
        "9420202": "tw-primary-shield",
        "9520100": "lake-reservoir-outline",
        "9520200": "pond-hatch",
        "9520600": "lake-reservoir-outline",
        "9520700": "water-label",
        "9740100": "fish-pond",
        "9940203": "swimming-pool",
        "9950201": "post",
        "9960203": "gas",
        "9960204": "parking-base",
        "9960204a": "parking-base",
        "9960204b": "parking-roof",
        "9960204c": "parking-pole",
        "9970101": "church",
        "9970102": "temple",
    }
    if code in school_codes:
        renderer = "school"
    else:
        renderer = renderers.get(code, "category-style")
    if category.startswith("道路"):
        families, geometry = ["ROADA", "ROAD"], ["LineString", "Polygon"]
    elif category.startswith("水域"):
        families, geometry = ["WATERA", "RIVERA", "RIVERL"], ["LineString", "Polygon"]
    elif category.startswith("建築"):
        families, geometry = ["BUILD"], ["Polygon"]
    else:
        families, geometry = ["MARK"], ["Point"]
    if code == "9940203":
        families, geometry = ["MARK"], ["Point"]
    return renderer, families, geometry


def compile_catalog(pmtiles_path: Path, graph_path: Path) -> dict:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    features = {
        node["properties"]["code"]: node
        for node in graph["nodes"]
        if node["type"] == "FeatureType"
    }
    conflicts = {
        code
        for node in graph["nodes"]
        if node["type"] == "ProfileConflict"
        for code in node["properties"].get("subject_codes", [])
    }
    capabilities = []
    for entry in _pmtiles_entries(pmtiles_path):
        code = entry["code"]
        is_variant = re.fullmatch(r"\d{7}[a-z]", code) is not None
        evidence_available = code in features
        if is_variant:
            status = "style-variant"
        elif code in conflicts:
            status = "conflicted"
        elif evidence_available:
            status = "evidence-backed"
        else:
            status = "implementation-only"
        renderer, source_families, geometry_types = _renderer(code, entry["category"])
        feature = features.get(code, {}).get("properties", {})
        capabilities.append(
            {
                **entry,
                "authoritative_name": feature.get("name"),
                "aliases": feature.get("aliases", []),
                "status": status,
                "evidence_available": evidence_available,
                "base_code": code[:7] if is_variant else code,
                "renderer": renderer,
                "source_layer_families": source_families,
                "geometry_types": geometry_types,
                "editable_parameters": [
                    "scale",
                    "color",
                    "stroke_width",
                    "outline",
                    "opacity",
                    "rotation",
                ]
                + (["flag_top_alignment"] if code == "9920103" else []),
            }
        )
    counts: dict[str, int] = {}
    for item in capabilities:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return {
        "schema": "nma.pmtiles-capability-catalog/1.0",
        "source": "pmtilesDemo.html#TERRAINID_GROUPS",
        "profile_id": graph["profile"]["profile_id"],
        "count": len(capabilities),
        "status_counts": counts,
        "capabilities": capabilities,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pmtiles", type=Path, default=ROOT / "pmtilesDemo.html")
    parser.add_argument(
        "--graph", type=Path, default=ROOT / "data/knowledge/portrayal-graph.json"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "data/demo/pmtiles-capability-catalog.json"
    )
    args = parser.parse_args()
    catalog = compile_catalog(args.pmtiles, args.graph)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(args.output), "count": catalog["count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

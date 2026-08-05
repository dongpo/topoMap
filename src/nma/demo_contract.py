from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io import dump_json
from .knowledge import PortrayalGraph, compile_portrayal_graph
from .paths import resolve_asset
from .portrayal import PortrayalAgent, compile_maplibre_layers


REQUIRED_SCENES = {"school", "fire-hydrant", "police", "fish-pond", "post-office"}


def load_demo_contract(path: str | Path) -> dict[str, Any]:
    with resolve_asset(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _expect(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def check_demo_contract(path: str | Path) -> dict[str, Any]:
    contract = load_demo_contract(path)
    shared = contract["shared"]
    scenes = contract["scenes"]
    scene_ids = {scene["id"] for scene in scenes}
    _expect(scene_ids, REQUIRED_SCENES, "frozen scene set")
    _expect(len(scenes), 5, "scene count")

    profile_path = resolve_asset(shared["profile_path"])
    graph_path = resolve_asset(shared["graph_path"])
    runner_path = resolve_asset(shared["runner_path"])
    pmtiles_path = resolve_asset(shared["pmtiles_path"])
    for asset in (profile_path, graph_path, runner_path, pmtiles_path):
        if not asset.exists():
            raise ValueError(f"missing shared demo asset: {asset}")

    with profile_path.open(encoding="utf-8") as handle:
        profile = json.load(handle)
    graph = PortrayalGraph.load(graph_path)
    agent = PortrayalAgent(graph)
    layers = compile_maplibre_layers(graph)

    _expect(profile["profile_id"], contract["profile"]["id"], "profile id")
    _expect(profile["version"], contract["profile"]["version"], "profile version")
    _expect(
        profile["scale_denominator"],
        contract["profile"]["scale_denominator"],
        "profile scale",
    )
    _expect(graph.graph["profile"]["profile_id"], profile["profile_id"], "graph profile id")

    results = []
    required_evidence = set(shared["evidence_fields"])
    required_metadata = set(shared["map_metadata_fields"])
    for scene in sorted(scenes, key=lambda item: item["order"]):
        expected = scene["expected"]
        attributes = scene["input"].get("attributes", {})
        answer = agent.answer(scene["prompt"])
        _expect(answer["status"], "answered", f"{scene['id']} retrieval status")
        if expected["feature_code"] not in answer["feature_codes"]:
            raise ValueError(f"{scene['id']}: prompt did not retrieve the frozen feature")
        if expected["evidence_page"] not in {evidence["page"] for evidence in answer["evidence"]}:
            raise ValueError(f"{scene['id']}: prompt did not retrieve the frozen evidence page")
        decision = agent.select_symbol(
            scene["input"]["feature_code"],
            scale_denominator=contract["profile"]["scale_denominator"],
            profile_id=contract["profile"]["id"],
            attributes=attributes,
        ).as_dict()
        _expect(decision["status"], "selected", f"{scene['id']} decision status")
        _expect(decision["feature_code"], expected["feature_code"], f"{scene['id']} code")
        _expect(decision["symbol"]["symbol_id"], expected["symbol_id"], f"{scene['id']} symbol")
        _expect(
            decision["symbol"]["selected_action"],
            expected["selected_action"],
            f"{scene['id']} action",
        )
        _expect(decision["evidence"]["page"], expected["evidence_page"], f"{scene['id']} page")
        for symbol_field in (
            "maplibre_type",
            "label_field",
            "companion_icon",
            "official_dimensions_mm",
        ):
            if symbol_field in expected:
                _expect(
                    decision["symbol"].get(symbol_field),
                    expected[symbol_field],
                    f"{scene['id']} {symbol_field}",
                )
        if "normal_action" in expected:
            normal = agent.select_symbol(
                scene["input"]["feature_code"],
                scale_denominator=contract["profile"]["scale_denominator"],
                profile_id=contract["profile"]["id"],
            ).as_dict()
            _expect(
                normal["symbol"]["selected_action"],
                expected["normal_action"],
                f"{scene['id']} normal action",
            )
        if not required_evidence <= set(decision["evidence"]):
            raise ValueError(f"{scene['id']}: incomplete evidence contract")
        if not decision["graph_path"]["nodes"] or not decision["graph_path"]["edges"]:
            raise ValueError(f"{scene['id']}: incomplete graph path")

        primary_layer = next(
            (
                layer
                for layer in layers
                if layer.get("source-layer") == expected["primary_source_layer"]
                and layer["metadata"]["nma:featureCode"] == expected["feature_code"]
                and layer["metadata"].get("nma:role") is None
            ),
            None,
        )
        if primary_layer is None:
            raise ValueError(f"{scene['id']}: expected primary MapLibre layer not compiled")
        if not required_metadata <= set(primary_layer["metadata"]):
            raise ValueError(f"{scene['id']}: incomplete MapLibre metadata contract")

        results.append(
            {
                "scene": scene["id"],
                "status": "passed",
                "feature_code": decision["feature_code"],
                "action": decision["symbol"]["selected_action"],
                "evidence_page": decision["evidence"]["page"],
                "primary_source_layer": primary_layer["source-layer"],
            }
        )

    unsupported = agent.select_symbol(
        contract["negative_control"]["feature_code"],
        scale_denominator=contract["negative_control"]["scale_denominator"],
        profile_id=contract["profile"]["id"],
    ).as_dict()
    _expect(unsupported["status"], "abstain", "negative-control decision")

    return {
        "contract_version": contract["contract_version"],
        "status": "passed",
        "profile_id": profile["profile_id"],
        "scene_count": len(results),
        "scenes": results,
        "negative_control": "passed",
    }


def reset_demo_contract(path: str | Path) -> dict[str, Any]:
    contract = load_demo_contract(path)
    shared = contract["shared"]
    graph = compile_portrayal_graph(
        resolve_asset(shared["records_path"]), resolve_asset(shared["profile_path"])
    )
    dump_json(graph, resolve_asset(shared["graph_path"]))
    layers = compile_maplibre_layers(PortrayalGraph(graph))
    dump_json({"version": 8, "layers": layers}, resolve_asset(shared["style_output_path"]))
    return check_demo_contract(path)

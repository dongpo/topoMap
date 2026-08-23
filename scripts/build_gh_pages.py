"""Build the bounded, static NMA v1.0 accepted-execution replay for GitHub Pages."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
SITE_SOURCE = ROOT / "site"
ASSET_SOURCE = ROOT / "public/nma/assets"
ASSETS = (
    "maplibre-gl-4.7.0.js",
    "maplibre-gl-4.7.0.css",
    "maplibre-gl-4.7.0-LICENSE.txt",
    "NotoSansRegular-0-255.pbf",
    "NotoSansRegular-19968-20223.pbf",
    "NotoSansRegular-23552-23807.pbf",
    "NotoSansRegular-34816-35071.pbf",
    "NotoSans-LICENSE.txt",
    "school-blue.svg",
)


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def graph_projection(graph: dict, identities: list[str]) -> list[dict]:
    nodes = {node["id"]: node for node in graph["nodes"]}
    allowed = {
        "feature_code",
        "feature_name",
        "label",
        "code",
        "page",
        "geometry_role",
        "instruction",
        "representation_kind",
    }
    return [
        {
            "id": identity,
            "type": nodes[identity]["type"],
            "summary": {
                key: value
                for key, value in nodes[identity].get("properties", {}).items()
                if key in allowed
            },
        }
        for identity in identities
    ]


def school_schematic(fixture: dict) -> dict:
    """Create a count-faithful, non-geographic view without private coordinates or labels."""
    features = []
    selected_layers = [
        layer for layer in fixture["school"]["layers"] if layer["selected_feature_count"]
    ]
    for layer in selected_layers:
        count = layer["selected_feature_count"]
        for index in range(count):
            public_index = len(features)
            features.append(
                {
                    "type": "Feature",
                    "id": f"public-replay-{len(features) + 1:02d}",
                    "properties": {
                        "layer": layer["layer_id"],
                        "selection_index": index + 1,
                        "TERRAINID": "9920103",
                        "display_label": f"Accepted point {len(features) + 1:02d}",
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            120.95 + (public_index % 5) * 0.04,
                            24.70 + (public_index // 5) * 0.04,
                        ],
                    },
                }
            )
    if len(features) != 15:
        raise ValueError("School accepted replay must contain exactly 15 public-safe points")
    return {"type": "FeatureCollection", "features": features}


def road_schematic(segment_ids: list[str]) -> dict:
    """Create a 4/3/4-vertex public-safe trace without controlled source coordinates."""
    coordinate_sets = (
        ((120.98, 24.74), (120.995, 24.746), (121.012, 24.754), (121.03, 24.765)),
        ((121.03, 24.765), (121.049, 24.778), (121.069, 24.794)),
        ((121.069, 24.794), (121.087, 24.811), (121.103, 24.827), (121.12, 24.846)),
    )
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": segment_id,
                "properties": {
                    "ROADSEGID": segment_id,
                    "ROADNAME": "中山街",
                    "ROADNUM": "縣126",
                    "TERRAINID": "9420400",
                    "vertex_count": len(coordinates),
                    "coordinate_policy": "normalized-public-replay",
                },
                "geometry": {"type": "LineString", "coordinates": coordinates},
            }
            for segment_id, coordinates in zip(segment_ids, coordinate_sets, strict=True)
        ],
    }


def scenarios() -> dict:
    spec = ROOT / "data/specifications"
    fixture = load(spec / "nma-demo-controlled-fixture-baseline-v1.0.json")
    accepted = load(spec / "nma-demo-02-retry-controlled-e2e-acceptance-record-v1.0.json")
    build = load(spec / "nma-build-05-golden-execution-package-v1.0.json")
    graph = load(ROOT / "data/knowledge/nma-canonical-graph-v0.4.json")
    school_record = accepted["scenarios"]["school"]
    road_record = accepted["scenarios"]["road"]
    build_record = accepted["scenarios"]["build"]
    school_nodes = fixture["school"]["graphrag"]["required_nodes"]
    road_nodes = fixture["road"]["graphrag"]["required_nodes"]
    segment_ids = accepted["fixtures"]["road"]["ordered_segment_ids"]

    common_limits = [
        "Static accepted-execution replay; no live FastAPI or Agent process",
        "No arbitrary upload, URL fetch, external data substitution, or writeback",
        "No OpenAI, Neo4j, or production credentials",
    ]
    return {
        "schema": "nma.static-accepted-execution-replay/1.0",
        "release": {
            "label": "NMA v1.0 final",
            "tag": "nma-v1.0-final",
            "commit": "eb87bde775333811529efb6f651573ea21cf456b",
            "demo_tag": "nma-demo-v1.0-final",
            "demo_commit": "05af154a14e781f20b5cf2d3996eac8191875b0f",
            "mode": "accepted execution replay",
            "live_agent": False,
            "production_credentials": False,
            "limits": common_limits,
        },
        "scenarios": [
            {
                "id": "school",
                "domain": "School",
                "title": "Controlled 15-point School result",
                "subtitle": "Accepted authorization · official blue portrayal",
                "request": "Show the accepted School 9920103 mapping lifecycle.",
                "interpretation": {
                    "status": "resolved",
                    "summary": "School domain · feature code 9920103 · controlled six-layer selection",
                    "boundary": "A deterministic replay selector resolves this request; no model is called.",
                },
                "knowledge": {
                    "status": "accepted-evidence",
                    "mode": "deterministic accepted-scenario GraphRAG path",
                    "nodes": graph_projection(graph, school_nodes),
                    "mapping_rule": "Point portrayal with approved blue School symbol; 15 selected features.",
                    "boundary": fixture["school"]["graphrag"]["boundary"],
                },
                "plan": {
                    "status": "accepted",
                    "id": school_record["plan_id"],
                    "sha256": school_record["plan_sha256"],
                    "action": "Filter TERRAINID 9920103, derive EPSG:4326 output, and apply approved School portrayal.",
                },
                "authorization": {
                    "status": "accepted · consumed idempotently",
                    "id": school_record["authorization_id"],
                    "sha256": accepted["school_authorization"]["authorization_hash"],
                    "scope": "Controlled 15-point School derivative only; demo-only authority.",
                },
                "execution": {
                    "status": "accepted replay",
                    "id": school_record["execution_id"],
                    "feature_count": school_record["feature_count"],
                    "mode": "Replay of frozen receipt; no current source execution.",
                },
                "qa": {
                    "status": "PASS",
                    "sha256": school_record["qa_sha256"],
                    "checks": [
                        "15 selected points",
                        "blue School symbol",
                        "accepted authorization binding",
                    ],
                },
                "provenance": {
                    "status": "verified",
                    "sha256": school_record["provenance_sha256"],
                    "fixture_sha256": fixture["school"]["aggregate_sha256"],
                    "receipt_sha256": school_record["receipt_sha256"],
                },
                "map": {
                    "type": "school",
                    "geojson": school_schematic(fixture),
                    "caption": "15-point count-faithful normalized replay. Private fixture coordinates and names are intentionally withheld.",
                    "coordinate_policy": "normalized-public-replay-not-source-geography",
                },
            },
            {
                "id": "road",
                "domain": "ROAD",
                "title": "Accepted K14_ROAD evidence",
                "subtitle": "4 / 3 / 4 vertices · line-following 中山街 portrayal",
                "request": "Replay the accepted K14_ROAD 9420400 中山街 portrayal.",
                "interpretation": {
                    "status": "resolved",
                    "summary": "ROAD domain · K14_ROAD · class 9420400 · 縣126 / 中山街",
                    "boundary": "Only the frozen three-segment identity is selectable.",
                },
                "knowledge": {
                    "status": "accepted-evidence",
                    "mode": "deterministic accepted-scenario GraphRAG path",
                    "nodes": graph_projection(graph, road_nodes),
                    "mapping_rule": "Render three ordered LineStrings and place literal 中山街 along the line; shield remains semantic-binding-only.",
                    "boundary": fixture["road"]["graphrag"]["boundary"],
                },
                "plan": {
                    "status": "frozen validated",
                    "id": road_record["plan_id"],
                    "sha256": road_record["plan_sha256"],
                    "action": "Render exact accepted vertex counts 4/3/4 with line-following 中山街.",
                },
                "authorization": {
                    "status": "accepted · consumed evidence",
                    "id": road_record["authorization_id"],
                    "sha256": "f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38",
                    "scope": "Exact K14_ROAD three-segment derivative; demo-only authority.",
                },
                "execution": {
                    "status": "accepted replay",
                    "id": road_record["execution_id"],
                    "feature_count": 3,
                    "mode": "Frozen receipt replay; source mutation and topology repair were not performed.",
                },
                "qa": {
                    "status": "PASS",
                    "sha256": road_record["qa_sha256"],
                    "checks": [
                        "K14_ROAD identity",
                        "ordered segments",
                        "4 / 3 / 4 vertices",
                        "line-following 中山街",
                    ],
                },
                "provenance": {
                    "status": "verified",
                    "sha256": road_record["provenance_sha256"],
                    "fixture_sha256": fixture["road"]["aggregate_sha256"],
                    "receipt_sha256": road_record["receipt_sha256"],
                },
                "map": {
                    "type": "road",
                    "geojson": road_schematic(segment_ids),
                    "caption": "Topology- and count-faithful normalized replay: ordered 4/3/4 vertices with line-following 中山街. Private source coordinates are not published.",
                    "coordinate_policy": "normalized-public-replay-not-source-geography",
                },
            },
            {
                "id": "build",
                "domain": "BUILD",
                "title": "Boundary / hatch replay",
                "subtitle": "Accepted derived view · production activation held",
                "request": "Replay the accepted BUILD 9310100 boundary and hatch demonstration.",
                "interpretation": {
                    "status": "resolved",
                    "summary": "BUILD domain · feature code 9310100 · derived demonstration only",
                    "boundary": "Production activation requests are outside this static replay and remain disabled.",
                },
                "knowledge": {
                    "status": "accepted-evidence · GraphRAG not applicable",
                    "mode": "frozen mapping-rule evidence",
                    "nodes": [],
                    "mapping_rule": "Solid boundary with 45° diagonal hatch over a normalized, non-geographic derived polygon.",
                    "boundary": "The accepted BUILD evaluation does not claim GraphRAG retrieval; no claim is fabricated.",
                },
                "plan": {
                    "status": "frozen validated",
                    "id": build["plan_sha256"],
                    "sha256": build["plan_sha256"],
                    "action": "Render the accepted normalized boundary and clipped diagonal hatch.",
                },
                "authorization": {
                    "status": "accepted · consumed once",
                    "id": build["authorization_id"],
                    "sha256": build["authorization_sha256"],
                    "scope": "Derived demo only; production activation held/disabled.",
                },
                "execution": {
                    "status": "accepted replay",
                    "id": build_record["execution_id"],
                    "feature_count": 1,
                    "mode": "Frozen package validation/replay; runtime wiring and production activation are absent.",
                },
                "qa": {
                    "status": "PASS",
                    "sha256": build_record["verification_sha256"],
                    "checks": [
                        "normalized boundary",
                        "45° diagonal hatch",
                        "production activation false",
                        "raw attributes absent",
                    ],
                },
                "provenance": {
                    "status": "source commitments verified",
                    "sha256": build["demo_artifact"]["artifact_sha256"],
                    "fixture_sha256": fixture["fixture_authority"]["package_sha256"],
                    "receipt_sha256": build_record["receipt_sha256"],
                },
                "map": {
                    "type": "build",
                    "geojson": build["demo_artifact"]["maplibre_demo"]["source"]["data"],
                    "caption": "Accepted normalized-local BUILD geometry with solid boundary and 45° hatch. Not geographic; production activation held/disabled.",
                    "coordinate_policy": "frozen-normalized-local-demo-not-geographic",
                },
                "production_activation": False,
            },
        ],
    }


def build(output: Path) -> dict:
    output = output.resolve()
    if output == ROOT or ROOT not in output.parents:
        raise ValueError("output must be a dedicated directory inside the repository")
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(SITE_SOURCE, output)
    (output / "assets").mkdir()
    for name in ASSETS:
        shutil.copyfile(ASSET_SOURCE / name, output / "assets" / name)
    (output / "data").mkdir(exist_ok=True)
    (output / "data/scenarios.json").write_text(
        json.dumps(scenarios(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / ".nojekyll").write_text("", encoding="utf-8")
    files = sorted(path for path in output.rglob("*") if path.is_file())
    release = {
        "schema": "nma.github-pages-static-release/1.0",
        "source_branch": "deploy/deploy-02-github-pages-public-demo",
        "authority_commit": "eb87bde775333811529efb6f651573ea21cf456b",
        "mode": "accepted-execution-replay",
        "private_fixture_bytes_included": False,
        "production_credentials_included": False,
        "production_activation": False,
        "files": [
            {
                "path": path.relative_to(output).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in files
        ],
    }
    (output / "release.json").write_text(
        json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return release


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/tmp/gh-pages")
    args = parser.parse_args()
    release = build(ROOT / args.output)
    print(json.dumps({"file_count": len(release["files"]), "mode": release["mode"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

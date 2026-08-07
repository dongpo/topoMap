#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_agentic_v03_pages import build_pages_candidate  # noqa: E402


EXPECTED_RELEASE = "nma-agentic-v0.3-pages-rc1"
EXPECTED_STABLE = "nma-public-assets-v0.2-rc1"
EXPECTED_PATH = "agentic-v0.3"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expect(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_release_files(root: Path, release: dict[str, Any]) -> None:
    paths = [item["path"] for item in release["files"]]
    if len(paths) != len(set(paths)):
        raise ValueError("candidate release contains duplicate paths")
    for item in release["files"]:
        path = root / item["path"]
        if not path.is_file():
            raise ValueError(f"candidate release file is missing: {item['path']}")
        expect(path.stat().st_size, item["size_bytes"], f"{item['path']} size")
        expect(sha256(path), item["sha256"], f"{item['path']} SHA-256")


def verify_public_dataset() -> dict[str, Any]:
    inspection = load_json(ROOT / "data/demo/school-points-public-inspection.json")
    collection = load_json(ROOT / "data/demo/school-points-public.geojson")
    expect(inspection["schema"], "nma.dataset-inspection/1.0", "inspection schema")
    expect(inspection["ready"], True, "inspection readiness")
    expect(inspection["inspection"]["feature_count"], 3, "inspection feature count")
    expect(inspection["inspection"]["crs"], "EPSG:3826", "inspection source CRS")
    expect(inspection["output_crs"], "EPSG:4326", "inspection output CRS")
    expect(collection["type"], "FeatureCollection", "public dataset type")
    expect(len(collection["features"]), 3, "public dataset feature count")
    expect(
        collection["nma:provenance"]["components"],
        [
            {"filename": item["filename"], "sha256": item["sha256"]}
            for item in inspection["components"]
        ],
        "public dataset component provenance",
    )
    for item in inspection["components"]:
        path = ROOT / "data/datasets/authoritative/school-points" / item["filename"]
        expect(path.stat().st_size, item["size_bytes"], f"{item['filename']} size")
        expect(sha256(path), item["sha256"], f"{item['filename']} SHA-256")
    return {
        "feature_count": len(collection["features"]),
        "source_crs": inspection["inspection"]["crs"],
        "output_crs": inspection["output_crs"],
        "component_count": len(inspection["components"]),
    }


def check_agentic_v03_pages(
    manifest_path: Path = ROOT / "data/demo/agentic-v0.3-pages.json",
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    expect(manifest["release_version"], EXPECTED_RELEASE, "release version")
    expect(manifest["status"], "candidate-not-deployed", "candidate status")
    expect(manifest["website"]["stable_root_release"], EXPECTED_STABLE, "stable root")
    expect(manifest["website"]["candidate_path"], EXPECTED_PATH, "candidate path")
    expect(manifest["website"]["deployment_state"], "not-deployed", "deployment state")
    expect(
        manifest["approval"]["public_deployment"],
        "separate explicit owner approval required",
        "deployment approval gate",
    )
    expect(manifest["blocking_defects"], [], "blocking defects")

    source_paths = [item["path"] for item in manifest["source_assets"]]
    if len(source_paths) != len(set(source_paths)):
        raise ValueError("source asset paths must be unique")
    candidate_targets = [item["target"] for item in manifest["candidate_assets"]]
    if len(candidate_targets) != len(set(candidate_targets)):
        raise ValueError("candidate target paths must be unique")
    if any(path.endswith(".pmtiles") for path in candidate_targets):
        raise ValueError("candidate allowlist must not contain PMTiles")

    dataset = verify_public_dataset()
    temporary_parent = ROOT / "artifacts/tmp"
    temporary_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nma-agentic-pages-", dir=temporary_parent) as temp:
        output = Path(temp) / "agentic-v0.3-pages"
        combined = build_pages_candidate(ROOT, output)
        stable = load_json(output / "release.json")
        candidate_root = output / EXPECTED_PATH
        candidate = load_json(candidate_root / "release.json")

        expect(combined["status"], "candidate-built-not-deployed", "combined status")
        expect(combined["owner_approval_required"], True, "owner approval gate")
        expect(stable["release_version"], EXPECTED_STABLE, "built stable root")
        expect(stable["stable_demo_release"], "nma-demo-v0.2-rc1", "stable demo")
        expect(candidate["release_version"], EXPECTED_RELEASE, "built candidate")
        expect(candidate["status"], "candidate-built-not-deployed", "built candidate status")
        expect(candidate["pmtiles_included"], False, "candidate PMTiles boundary")
        expect(
            candidate["model_mode"],
            "deterministic-fallback; no API credential shipped",
            "candidate model mode",
        )
        verify_release_files(candidate_root, candidate)

        candidate_demo = (candidate_root / "nmaAgentDemo.html").read_text(encoding="utf-8")
        stable_index = (output / "index.html").read_text(encoding="utf-8")
        candidate_index = (candidate_root / "index.html").read_text(encoding="utf-8")
        if "National Map Agent v0.2 · Stable Demo RC1" not in stable_index:
            raise ValueError("stable v0.2 root identity is missing")
        if "Agentic Demo v0.3 Candidate" not in candidate_index:
            raise ValueError("Agentic candidate identity is missing")
        if "new pmtiles.Protocol" in candidate_demo or 'addProtocol("pmtiles"' in candidate_demo:
            raise ValueError(
                "public candidate still initializes the repository-only PMTiles source"
            )
        if any(path.suffix == ".pmtiles" for path in output.rglob("*")):
            raise ValueError("combined Pages candidate contains PMTiles")
        if (candidate_root / "nmaDemoWorker.js").exists():
            raise ValueError("public candidate must not ship the local PMTiles service worker")

        candidate_file_count = len(candidate["files"])
        stable_file_count = len(stable["files"])

    workflow = (ROOT / ".github/workflows/static.yml").read_text(encoding="utf-8")
    if "build_agentic_v03_pages.py" in workflow:
        raise ValueError("Pages workflow changed before explicit deployment approval")

    return {
        "release_version": manifest["release_version"],
        "status": "candidate-passed-not-deployed",
        "stable_root_release": manifest["website"]["stable_root_release"],
        "candidate_path": manifest["website"]["candidate_path"],
        "stable_file_count": stable_file_count,
        "candidate_file_count": candidate_file_count,
        "dataset": dataset,
        "pmtiles_included": False,
        "deployment_state": "not-deployed",
        "owner_approval_required": True,
        "blocking_defect_count": 0,
        "deferred_defect_count": len(manifest["deferred_defects"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the bounded Agentic v0.3 Pages candidate")
    parser.add_argument("--manifest", default="data/demo/agentic-v0.3-pages.json")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = check_agentic_v03_pages(ROOT / args.manifest)
    if args.output:
        output = ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

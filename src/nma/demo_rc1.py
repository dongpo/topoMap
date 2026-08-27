from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .demo_backup import check_demo_backup
from .demo_freeze import check_demo_freeze
from .demo_offline import check_offline_runtime
from .paths import resolve_asset


EXPECTED_RELEASE = "nma-demo-v0.2-rc1"
EXPECTED_STATUS = "stable-rc1"
EXPECTED_SCENES = ["school", "fire-hydrant", "police", "fish-pond", "post-office"]
EXPECTED_CHANGE_POLICY = "critical defect only"


def load_demo_rc1(path: str | Path) -> dict[str, Any]:
    with resolve_asset(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expect(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_asset(path).read_text(encoding="utf-8"))


def check_demo_rc1(
    path: str | Path = "data/demo/stable-rc1.json",
) -> dict[str, Any]:
    manifest = load_demo_rc1(path)
    _expect(manifest["release_version"], EXPECTED_RELEASE, "release version")
    _expect(manifest["status"], EXPECTED_STATUS, "release status")
    _expect(manifest["scene_order"], EXPECTED_SCENES, "scene order")
    _expect(
        manifest["post_freeze_policy"]["allowed_change"],
        EXPECTED_CHANGE_POLICY,
        "post-freeze change policy",
    )

    commit = manifest["source"]["frozen_baseline_commit"]
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise ValueError("frozen baseline commit must be a full lowercase Git SHA")
    _expect(manifest["source"]["release_tag"], EXPECTED_RELEASE, "release tag")
    if manifest["blocking_defects"]:
        raise ValueError("stable RC1 cannot contain an unresolved blocking defect")

    artifact_paths = [artifact["path"] for artifact in manifest["artifacts"]]
    if len(artifact_paths) != len(set(artifact_paths)):
        raise ValueError("stable RC1 contains duplicate artifact paths")
    artifact_results = []
    for artifact in manifest["artifacts"]:
        artifact_path = resolve_asset(artifact["path"])
        if not artifact_path.is_file():
            raise ValueError(f"missing stable RC1 artifact: {artifact['path']}")
        size = artifact_path.stat().st_size
        digest = _sha256(artifact_path)
        _expect(size, artifact["size_bytes"], f"{artifact['path']} size")
        _expect(digest, artifact["sha256"], f"{artifact['path']} SHA-256")
        artifact_results.append({"path": artifact["path"], "role": artifact["role"]})

    components = manifest["components"]
    freeze = check_demo_freeze(components["feature_freeze"])
    offline = check_offline_runtime(components["offline_runtime"])
    backup = check_demo_backup(components["portable_backup"])
    _expect(freeze["scene_count"], 5, "feature-freeze scene count")
    _expect(offline["browser_modes_verified"], 2, "offline browser modes")
    _expect(backup["scene_count"], 5, "portable-backup scene count")
    _expect(backup["no_repository_required"], True, "portable-backup independence")

    verification = manifest["verification"]
    automated = _load_json(verification["automated_soak"]["evidence"])
    _expect(automated["summary"]["passed"], 20, "automated soak passes")
    _expect(automated["summary"]["failed"], 0, "automated soak failures")
    _expect(automated["summary"]["pass_rate"], 1.0, "automated soak pass rate")
    if automated["defects"]:
        raise ValueError("automated RC1 soak contains a blocking defect")

    browser = _load_json(verification["browser_soak"]["evidence"])
    _expect(browser["scene_order"], EXPECTED_SCENES, "browser scene order")
    _expect(browser["summary"]["passed_rounds"], 10, "browser soak passes")
    _expect(browser["summary"]["failed_rounds"], 0, "browser soak failures")
    _expect(browser["summary"]["console_errors"], 0, "browser console errors")
    _expect(browser["summary"]["console_warnings"], 0, "browser console warnings")
    if any(item["verified_rounds"] != 10 for item in browser["scene_evidence"]):
        raise ValueError("every frozen scene must pass all ten browser rounds")

    recorded = verification["recorded_fallback"]
    _expect(recorded["status"], "human-approved", "recorded fallback status")
    _expect(recorded["issue"], "GEO-72", "recorded fallback approval issue")

    environment = manifest["environment"]
    _expect(environment["python_minimum"], "3.11", "minimum Python")
    _expect(environment["ci"]["python"], "3.11", "CI Python")
    _expect(environment["browser_runtime"]["maplibre"], "4.7.0", "MapLibre version")
    _expect(environment["browser_runtime"]["pmtiles"], "4.3.0", "PMTiles version")
    required_roles = {
        "demo-contract",
        "feature-freeze",
        "offline-runtime",
        "portable-backup",
        "automated-soak",
        "browser-soak",
        "live-runbook",
        "backup-runbook",
        "environment-lock",
    }
    roles = {artifact["role"] for artifact in manifest["artifacts"]}
    if not required_roles <= roles:
        raise ValueError(f"stable RC1 is missing required artifact roles: {required_roles - roles}")
    if any(
        item["classification"] != "non-blocking" for item in manifest["non_blocking_release_gates"]
    ):
        raise ValueError("release gates must not hide a blocking defect")

    return {
        "release_version": manifest["release_version"],
        "status": "passed",
        "scene_count": len(manifest["scene_order"]),
        "automated_soak_rounds": automated["summary"]["passed"],
        "browser_soak_rounds": browser["summary"]["passed_rounds"],
        "offline_modes_verified": offline["browser_modes_verified"],
        "portable_backup_assets": backup["asset_count"],
        "artifact_count": len(artifact_results),
        "blocking_defect_count": len(manifest["blocking_defects"]),
        "non_blocking_release_gate_count": len(manifest["non_blocking_release_gates"]),
        "post_freeze_policy": manifest["post_freeze_policy"]["allowed_change"],
    }

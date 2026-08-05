from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .paths import resolve_asset


EXPECTED_SCENE_ORDER = ["school", "fire-hydrant", "police", "fish-pond", "post-office"]
EXPECTED_STATUS = "feature-complete"
EXPECTED_POLICY = "blocking reliability defect only"


def load_demo_freeze(path: str | Path) -> dict[str, Any]:
    with resolve_asset(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _expect(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_demo_freeze(path: str | Path) -> dict[str, Any]:
    manifest = load_demo_freeze(path)
    _expect(manifest["status"], EXPECTED_STATUS, "freeze status")
    _expect(manifest["walkthrough"]["status"], "passed", "walkthrough status")
    _expect(manifest["walkthrough"]["scene_order"], EXPECTED_SCENE_ORDER, "scene order")
    _expect(manifest["walkthrough"]["console_errors"], 0, "walkthrough console errors")
    _expect(manifest["walkthrough"]["console_warnings"], 0, "walkthrough console warnings")
    _expect(
        manifest["post_freeze_policy"]["allowed_change"],
        EXPECTED_POLICY,
        "post-freeze change policy",
    )

    commit = manifest["source"]["approved_base_commit"]
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise ValueError("approved base commit must be a full lowercase Git SHA")
    if not manifest["approved_capabilities"]:
        raise ValueError("freeze must record at least one approved capability")
    if any(issue["severity"] != "non-blocking" for issue in manifest["known_issues"]):
        raise ValueError("a blocking issue cannot be accepted into the feature-complete freeze")

    artifact_results = []
    artifact_paths = [artifact["path"] for artifact in manifest["artifacts"]]
    if len(artifact_paths) != len(set(artifact_paths)):
        raise ValueError("freeze contains duplicate artifact paths")
    for artifact in manifest["artifacts"]:
        artifact_path = resolve_asset(artifact["path"])
        if not artifact_path.is_file():
            raise ValueError(f"missing frozen artifact: {artifact_path}")
        actual_size = artifact_path.stat().st_size
        _expect(actual_size, artifact["size_bytes"], f"{artifact['path']} size")
        actual_sha256 = _sha256(artifact_path)
        _expect(actual_sha256, artifact["sha256"], f"{artifact['path']} SHA-256")
        artifact_results.append(
            {
                "path": artifact["path"],
                "status": "verified",
                "size_bytes": actual_size,
                "sha256": actual_sha256,
            }
        )

    acceptance_path = resolve_asset(manifest["walkthrough"]["acceptance_record"])
    if not acceptance_path.is_file():
        raise ValueError(f"missing walkthrough acceptance record: {acceptance_path}")
    contract_path = resolve_asset(manifest["source"]["demo_contract"])
    if not contract_path.is_file():
        raise ValueError(f"missing frozen demo contract: {contract_path}")

    return {
        "freeze_version": manifest["freeze_version"],
        "status": "passed",
        "approved_base_commit": commit,
        "scene_count": len(manifest["walkthrough"]["scene_order"]),
        "artifact_count": len(artifact_results),
        "artifacts": artifact_results,
        "known_issue_count": len(manifest["known_issues"]),
        "post_freeze_policy": manifest["post_freeze_policy"]["allowed_change"],
    }

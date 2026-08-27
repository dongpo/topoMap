from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .paths import distribution_root, resolve_asset


def _git_bytes(snapshot_ref: str, artifact_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{snapshot_ref}:{artifact_path}"],
        cwd=distribution_root(),
        check=False,
        capture_output=True,
    )
    if result.returncode:
        raise FileNotFoundError(f"{artifact_path} is not present in Git snapshot {snapshot_ref}")
    return result.stdout


def verify_manifest_snapshot(
    manifest_path: str | Path,
    snapshot_ref: str,
    *,
    artifact_key: str,
) -> dict[str, Any]:
    """Verify a historical release against its original Git snapshot.

    A frozen release must not be compared with a later development working tree. The manifest is
    retained in the current tree, while every frozen payload is read from the immutable Git object
    named by ``snapshot_ref``. Generated artifacts may be reproduced when they were intentionally
    excluded from Git.
    """

    manifest = json.loads(resolve_asset(manifest_path).read_text(encoding="utf-8"))
    artifacts = manifest[artifact_key]
    paths = [artifact["path"] for artifact in artifacts]
    if len(paths) != len(set(paths)):
        raise ValueError("historical manifest contains duplicate artifact paths")
    if len(snapshot_ref) != 40 or any(
        character not in "0123456789abcdef" for character in snapshot_ref
    ):
        raise ValueError("historical snapshot must be a full lowercase Git SHA")

    results = []
    for artifact in artifacts:
        artifact_path = artifact["path"]
        try:
            payload = _git_bytes(snapshot_ref, artifact_path)
            status = "verified-git-snapshot"
        except FileNotFoundError:
            if not artifact.get("generator"):
                raise
            from .demo_freeze import _generated_artifact_bytes

            payload = _generated_artifact_bytes(artifact["generator"])
            status = "verified-reproduced"

        actual_sha = hashlib.sha256(payload).hexdigest()
        expected_sha = artifact["sha256"]
        if actual_sha != expected_sha:
            raise ValueError(
                f"{artifact_path} SHA-256 at {snapshot_ref}: "
                f"expected {expected_sha!r}, got {actual_sha!r}"
            )
        expected_size = artifact.get("size_bytes")
        if expected_size is not None and len(payload) != expected_size:
            raise ValueError(
                f"{artifact_path} size at {snapshot_ref}: "
                f"expected {expected_size!r}, got {len(payload)!r}"
            )
        results.append(
            {
                "path": artifact_path,
                "status": status,
                "size_bytes": len(payload),
                "sha256": actual_sha,
            }
        )

    return {
        "status": "passed",
        "manifest": str(manifest_path),
        "snapshot_ref": snapshot_ref,
        "artifact_count": len(results),
        "artifacts": results,
    }

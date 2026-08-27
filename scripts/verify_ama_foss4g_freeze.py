#!/usr/bin/env python3
"""Verify the AMA FOSS4G 2026 evidence commit and annotated freeze identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data/specifications/ama-foss4g-2026-freeze-manifest.json"
FREEZE_TAG = "ama-foss4g-2026-freeze"
SOFTWARE_PREDECESSOR = "a1d6e758408f8bb51a3ed725b86b153ccba32569"
ZERO_HASH = "0" * 64
EVIDENCE_SCOPE = {
    "data/specifications/ama-foss4g-2026-freeze-manifest.json",
    "docs/research/AMA-FREEZE-00-FOSS4G-SOFTWARE-FREEZE-READINESS.md",
    "docs/research/AMA-FREEZE-01-FOSS4G-FREEZE-REPORT.md",
    "scripts/verify_ama_foss4g_freeze.py",
}
REQUIRED_PATHS = {
    "src/nma/research_cli.py",
    "src/nma/llm/base.py",
    "src/nma/llm/ollama.py",
    "docs/research/AMA-DEMO-02-PROVIDER-NEUTRAL-LIVE-RUNTIME.md",
    "docs/research/AMA-DEMO-03-RQ-ALIGNED-PACKAGING.md",
    "docs/research/AMA-DEMO-03-RUNBOOK.md",
    *EVIDENCE_SCOPE,
}


def _git(*arguments: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )
    return result.stdout.strip()


def _manifest_hash(manifest: dict[str, object]) -> str:
    normalized = json.loads(json.dumps(manifest))
    normalized["manifest_integrity"]["sha256"] = ZERO_HASH
    canonical = json.dumps(
        normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _remote_tags(remote: str) -> dict[str, str]:
    output = _git("ls-remote", "--tags", remote)
    return {
        ref.removeprefix("refs/tags/"): object_id
        for line in output.splitlines()
        for object_id, ref in [line.split()]
    }


def verify(*, require_tag: bool, remote: str | None) -> dict[str, object]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    head = _git("rev-parse", "HEAD")
    parents = _git("show", "-s", "--format=%P", "HEAD").split()
    changed = set(_git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines())
    package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    checks: dict[str, bool] = {
        "manifest_schema": manifest.get("schema") == "ama.foss4g-software-freeze/1.0",
        "manifest_self_hash": manifest["manifest_integrity"]["sha256"] == _manifest_hash(manifest),
        "software_predecessor_recorded": manifest["software"]["merged_main_software_predecessor"]
        == SOFTWARE_PREDECESSOR,
        "evidence_commit_parent_exact": parents == [SOFTWARE_PREDECESSOR],
        "evidence_only_scope_exact": changed == EVIDENCE_SCOPE,
        "required_paths_exist": all((ROOT / path).is_file() for path in REQUIRED_PATHS),
        "package_version_unchanged": package["project"]["version"] == "0.2.0",
        "tag_name_recorded": manifest["freeze_identity"]["tag"] == FREEZE_TAG,
        "evidence_commit_is_self": manifest["freeze_identity"]["evidence_commit"]["identity"]
        == "self",
    }

    historical: dict[str, object] = {}
    for name, (expected_object, expected_target) in manifest["historical_integrity"][
        "tags"
    ].items():
        actual_object = _git("rev-parse", f"refs/tags/{name}")
        actual_target = _git("rev-parse", f"refs/tags/{name}^{{}}")
        ok = (
            _git("cat-file", "-t", f"refs/tags/{name}") == "tag"
            and actual_object == expected_object
            and actual_target == expected_target
        )
        historical[name] = {
            "object": actual_object,
            "target": actual_target,
            "status": "passed" if ok else "failed",
        }
    checks["historical_tag_identities"] = all(
        item["status"] == "passed" for item in historical.values()
    )

    tag_ref = f"refs/tags/{FREEZE_TAG}"
    tag_exists = (
        subprocess.run(["git", "show-ref", "--verify", "--quiet", tag_ref], cwd=ROOT).returncode
        == 0
    )
    tag: dict[str, object] = {"name": FREEZE_TAG, "exists": tag_exists}
    if tag_exists:
        tag_object = _git("rev-parse", tag_ref)
        tag_target = _git("rev-parse", f"{tag_ref}^{{}}")
        tag.update({"object": tag_object, "target": tag_target})
        checks["freeze_tag_annotated"] = _git("cat-file", "-t", tag_ref) == "tag"
        checks["freeze_tag_targets_evidence_commit"] = tag_target == head
    else:
        checks["freeze_tag_annotated"] = not require_tag
        checks["freeze_tag_targets_evidence_commit"] = not require_tag

    if remote:
        remote_refs = _remote_tags(remote)
        for name, (expected_object, expected_target) in manifest["historical_integrity"][
            "tags"
        ].items():
            checks[f"remote_historical:{name}"] = (
                remote_refs.get(name) == expected_object
                and remote_refs.get(f"{name}^{{}}") == expected_target
            )
        if tag_exists:
            checks["remote_freeze_tag_object"] = remote_refs.get(FREEZE_TAG) == tag["object"]
            checks["remote_freeze_tag_target"] = (
                remote_refs.get(f"{FREEZE_TAG}^{{}}") == tag["target"]
            )
        else:
            checks["remote_freeze_tag_object"] = not require_tag
            checks["remote_freeze_tag_target"] = not require_tag

    passed = all(checks.values())
    return {
        "schema": "ama.foss4g-freeze-verification/1.0",
        "status": "passed" if passed else "failed",
        "head": head,
        "software_predecessor": SOFTWARE_PREDECESSOR,
        "checks": checks,
        "historical_tags": historical,
        "freeze_tag": tag,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-tag", action="store_true")
    parser.add_argument("--remote")
    arguments = parser.parse_args()
    result = verify(require_tag=arguments.require_tag, remote=arguments.remote)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

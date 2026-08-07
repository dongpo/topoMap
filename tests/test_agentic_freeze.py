import json
from pathlib import Path

import pytest

from nma.agentic_freeze import check_agentic_freeze, load_agentic_freeze
from nma.historical_release import verify_manifest_snapshot


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/demo/agentic-v0.3-freeze.json"


def test_agentic_v03_freeze_verifies_current_and_historical_boundaries() -> None:
    result = check_agentic_freeze(MANIFEST)

    assert result["freeze_version"] == "nma-agentic-v0.3-rc1"
    assert result["status"] == "passed"
    assert result["approved_increment_count"] == 6
    assert result["scene_count"] == 5
    assert result["capability_count"] == 42
    assert result["evidence_linked_capability_count"] == 9
    assert result["graph_nodes"] == 44
    assert result["graph_edges"] == 85
    assert result["school_fixture_features"] == 3
    assert result["offline_runtime"] == "nma-agentic-v0.3-a06"
    assert result["historical_baseline_count"] == 3
    assert result["public_deployment"] == "not-deployed"
    assert result["blocking_defect_count"] == 0


def test_agentic_freeze_rejects_unrecorded_current_drift(tmp_path: Path) -> None:
    manifest = load_agentic_freeze(MANIFEST)
    manifest["artifacts"][0]["sha256"] = "0" * 64
    changed = tmp_path / "drifted-agentic-freeze.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        check_agentic_freeze(changed)


def test_historical_verifier_rejects_changed_release_fingerprint(tmp_path: Path) -> None:
    manifest = json.loads((ROOT / "data/demo/public-assets-rc1.json").read_text(encoding="utf-8"))
    manifest["frozen_assets"][0]["sha256"] = "0" * 64
    changed = tmp_path / "changed-public-assets.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        verify_manifest_snapshot(
            changed,
            "83c484d2ab3b2d7fd3ea1abb758b2c6a01dc7d3c",
            artifact_key="frozen_assets",
        )


def test_agentic_freeze_excludes_owner_controlled_presentation_assets() -> None:
    manifest = load_agentic_freeze(MANIFEST)
    paths = {artifact["path"] for artifact in manifest["artifacts"]}

    assert all(not path.endswith((".pptx", ".pdf")) for path in paths)
    assert "schemas/agentic-v0.3-freeze.schema.json" in paths
    assert manifest["source"]["public_deployment"] == "not-deployed"

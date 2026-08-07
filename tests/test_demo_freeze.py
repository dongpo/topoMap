import json
from pathlib import Path

import pytest

from nma.demo_freeze import load_demo_freeze
from nma.historical_release import verify_manifest_snapshot


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/demo/five-scene-freeze.json"
SNAPSHOT = "42a4dd52c9d65285f3c0d73e8b6ce143a581b7ea"


def test_feature_complete_freeze_verifies_every_artifact() -> None:
    result = verify_manifest_snapshot(MANIFEST, SNAPSHOT, artifact_key="artifacts")
    manifest = load_demo_freeze(MANIFEST)

    assert result["status"] == "passed"
    assert manifest["freeze_version"] == "nma-demo-rc1-feature-complete"
    assert manifest["source"]["approved_base_commit"] == (
        "06090a04792514b85823457b235f7feebf2660d4"
    )
    assert len(manifest["walkthrough"]["scene_order"]) == 5
    assert result["artifact_count"] == 16
    assert {artifact["status"] for artifact in result["artifacts"]} <= {
        "verified-git-snapshot",
        "verified-reproduced",
    }


def test_freeze_records_walkthrough_known_issues_and_change_control() -> None:
    manifest = load_demo_freeze(MANIFEST)

    assert manifest["walkthrough"]["scene_order"] == [
        "school",
        "fire-hydrant",
        "police",
        "fish-pond",
        "post-office",
    ]
    assert manifest["walkthrough"]["status"] == "passed"
    assert manifest["walkthrough"]["console_errors"] == 0
    assert manifest["walkthrough"]["console_warnings"] == 0
    assert manifest["known_issues"]
    assert {issue["severity"] for issue in manifest["known_issues"]} == {"non-blocking"}
    assert manifest["post_freeze_policy"]["allowed_change"] == ("blocking reliability defect only")
    assert "updated artifact fingerprints" in manifest["post_freeze_policy"]["required_evidence"]


def test_freeze_rejects_unrecorded_artifact_drift(tmp_path: Path) -> None:
    manifest = load_demo_freeze(MANIFEST)
    manifest["artifacts"][0]["sha256"] = "0" * 64
    changed_manifest = tmp_path / "changed-freeze.json"
    changed_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        verify_manifest_snapshot(changed_manifest, SNAPSHOT, artifact_key="artifacts")


def test_freeze_rebuilds_ignored_style_in_a_clean_checkout(tmp_path: Path) -> None:
    manifest = load_demo_freeze(MANIFEST)
    style = next(
        artifact
        for artifact in manifest["artifacts"]
        if artifact["path"] == "artifacts/portrayal/maplibre-layers.json"
    )
    style["path"] = "artifacts/portrayal/not-present-in-clean-checkout.json"
    clean_checkout_manifest = tmp_path / "clean-checkout-freeze.json"
    clean_checkout_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    result = verify_manifest_snapshot(clean_checkout_manifest, SNAPSHOT, artifact_key="artifacts")
    verified_style = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["path"] == "artifacts/portrayal/not-present-in-clean-checkout.json"
    )
    assert verified_style["status"] == "verified-reproduced"
    assert verified_style["sha256"] == style["sha256"]

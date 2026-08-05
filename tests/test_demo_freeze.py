import json
from pathlib import Path

import pytest

from nma.demo_freeze import check_demo_freeze, load_demo_freeze


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/demo/five-scene-freeze.json"


def test_feature_complete_freeze_verifies_every_artifact() -> None:
    result = check_demo_freeze(MANIFEST)

    assert result["status"] == "passed"
    assert result["freeze_version"] == "nma-demo-rc1-feature-complete"
    assert result["approved_base_commit"] == "06090a04792514b85823457b235f7feebf2660d4"
    assert result["scene_count"] == 5
    assert result["artifact_count"] == 16
    assert {artifact["status"] for artifact in result["artifacts"]} <= {
        "verified",
        "verified-generated",
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
        check_demo_freeze(changed_manifest)


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

    result = check_demo_freeze(clean_checkout_manifest)
    verified_style = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["path"] == "artifacts/portrayal/not-present-in-clean-checkout.json"
    )
    assert verified_style["status"] == "verified-generated"
    assert verified_style["sha256"] == style["sha256"]

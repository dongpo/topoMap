import json
from pathlib import Path

from nma.historical_release import verify_manifest_snapshot


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/demo/public-assets-rc1.json"
REPORT = ROOT / "artifacts/release/public-assets-rc1-verification.json"


def test_public_assets_rc_verifies_the_bounded_candidate() -> None:
    snapshot = verify_manifest_snapshot(
        MANIFEST,
        "83c484d2ab3b2d7fd3ea1abb758b2c6a01dc7d3c",
        artifact_key="frozen_assets",
    )
    verification = json.loads(REPORT.read_text(encoding="utf-8"))

    assert snapshot["status"] == "passed"
    assert snapshot["artifact_count"] == 9
    assert verification["status"] == "candidate-passed"
    assert verification["stable_demo_release"] == "nma-demo-v0.2-rc1"
    assert verification["public_mode"] == "evidence-only"
    assert verification["public_deployment"] == "deployed"
    assert verification["presentation"] == {"slides": 12, "sourced_notes": 12}
    assert verification["install_rehearsal"]["status"] == "passed"
    assert verification["install_rehearsal"]["scene_count"] == 5
    assert verification["review_package"]["scene_count"] == 5
    assert verification["blocking_defect_count"] == 0
    assert verification["resolved_defect_count"] == 1
    assert verification["deferred_defect_count"] == 3


def test_public_assets_manifest_triages_every_remaining_defect() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["blocking_defects"] == []
    assert {item["classification"] for item in manifest["resolved_defects"]} == {"resolved"}
    assert {item["classification"] for item in manifest["deferred_defects"]} == {"deferred"}
    assert manifest["website"]["exclusions"] == [
        "out1120902.pmtiles",
        "official NLSC portrayal PDF",
        "repository-only development and test files",
    ]
    assert manifest["post_freeze_policy"]["allowed_categories"] == [
        "correctness",
        "clarity",
        "reliability",
        "conference-needs",
    ]


def test_pages_workflow_never_uploads_the_entire_repository() -> None:
    workflow = (ROOT / ".github/workflows/static.yml").read_text(encoding="utf-8")

    assert "python3 scripts/build_public_site.py" in workflow
    assert "path: 'artifacts/tmp/public-site'" in workflow
    assert "path: '.'" not in workflow

import json
from pathlib import Path

import pytest

from nma.demo_rc1 import check_demo_rc1, load_demo_rc1


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/demo/stable-rc1.json"


def test_stable_rc1_verifies_every_release_gate() -> None:
    result = check_demo_rc1(MANIFEST)

    assert result == {
        "release_version": "nma-demo-v0.2-rc1",
        "status": "passed",
        "scene_count": 5,
        "automated_soak_rounds": 20,
        "browser_soak_rounds": 10,
        "offline_modes_verified": 2,
        "portable_backup_assets": 14,
        "artifact_count": 16,
        "blocking_defect_count": 0,
        "non_blocking_release_gate_count": 3,
        "post_freeze_policy": "critical defect only",
    }


def test_stable_rc1_versions_environment_runbooks_and_risks() -> None:
    manifest = load_demo_rc1(MANIFEST)

    assert manifest["scene_order"] == [
        "school",
        "fire-hydrant",
        "police",
        "fish-pond",
        "post-office",
    ]
    assert manifest["environment"]["browser_runtime"] == {
        "glyphs": "cache-on-use",
        "maplibre": "4.7.0",
        "pmtiles": "4.3.0",
    }
    assert manifest["blocking_defects"] == []
    assert {item["id"] for item in manifest["resolved_risks"]} == {
        "cold-cache-map-runtime",
        "backup-capture",
        "browser-repeatability",
    }
    assert all(
        item["classification"] == "non-blocking" for item in manifest["non_blocking_release_gates"]
    )


def test_stable_rc1_rejects_a_blocking_defect(tmp_path: Path) -> None:
    manifest = load_demo_rc1(MANIFEST)
    manifest["blocking_defects"] = [{"id": "controlled-blocker"}]
    changed = tmp_path / "blocking-rc1.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="unresolved blocking defect"):
        check_demo_rc1(changed)


def test_stable_rc1_rejects_artifact_drift(tmp_path: Path) -> None:
    manifest = load_demo_rc1(MANIFEST)
    manifest["artifacts"][0]["sha256"] = "0" * 64
    changed = tmp_path / "drifted-rc1.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        check_demo_rc1(changed)

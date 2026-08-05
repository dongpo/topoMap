from pathlib import Path
import json

import pytest

import nma.demo_soak as soak_module
from nma.demo_soak import DEFECT_CLASSES, run_demo_soak


ROOT = Path(__file__).resolve().parents[1]


def test_soak_repeats_the_full_sequence_from_a_clean_reset(tmp_path: Path) -> None:
    output = tmp_path / "soak.json"
    report = run_demo_soak(iterations=2, output=output)

    assert output.is_file()
    assert report["protocol"]["clean_reset_before_each_run"] is True
    assert report["protocol"]["scene_order"] == [
        "school",
        "fire-hydrant",
        "police",
        "fish-pond",
        "post-office",
    ]
    assert report["summary"]["passed"] == 2
    assert report["summary"]["failed"] == 0
    assert report["summary"]["pass_rate"] == 1.0
    assert all(run["scene_count"] == 5 for run in report["runs"])
    assert all(run["artifact_count"] == 14 for run in report["runs"])
    assert all(run["total_ms"] > 0 for run in report["runs"])


def test_soak_records_recovery_and_classifies_known_observations() -> None:
    report = run_demo_soak(iterations=1)

    assert report["recovery_steps"]
    assert {item["classification"] for item in report["known_observations"]} <= DEFECT_CLASSES
    assert {item["id"] for item in report["known_observations"]} == {
        "runtime-dependencies",
        "backup-capture",
        "public-demo-url",
        "expert-sign-off",
    }
    assert all(item["owner"] and item["next_action"] for item in report["known_observations"])


def test_soak_failure_becomes_an_owned_blocking_defect(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_reset(_contract: str | Path) -> None:
        raise RuntimeError("controlled failure")

    monkeypatch.setattr(soak_module, "reset_demo_contract", fail_reset)
    report = run_demo_soak(iterations=1)

    assert report["summary"]["failed"] == 1
    assert report["defects"] == [
        {
            "id": "soak-run-1-failure",
            "classification": "blocking",
            "owner": "NMA engineering / GEO-70",
            "next_action": (
                "Reproduce run 1 from make demo-reset, diagnose RuntimeError: controlled failure, "
                "and rerun the complete soak before release."
            ),
        }
    ]


def test_soak_rejects_empty_run() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        run_demo_soak(iterations=0)


def test_committed_browser_soak_evidence_is_complete() -> None:
    report = json.loads((ROOT / "artifacts/soak/five-scene-soak.json").read_text())
    browser = report["browser_soak"]

    assert browser["status"] == "passed"
    assert browser["completed_rounds"] == browser["passed_rounds"] == 10
    assert browser["failed_rounds"] == 0
    assert browser["console_errors"] == browser["console_warnings"] == 0
    assert len(browser["durations_ms"]) == 10
    assert [item["scene_id"] for item in browser["scene_evidence"]] == [
        "school",
        "fire-hydrant",
        "police",
        "fish-pond",
        "post-office",
    ]
    assert all(item["verified"] for item in browser["scene_evidence"])

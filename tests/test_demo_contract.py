from pathlib import Path

from nma.demo_contract import check_demo_contract, load_demo_contract


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/demo/five-scene-demo.json"


def test_frozen_five_scene_contract_passes_end_to_end() -> None:
    result = check_demo_contract(CONTRACT)

    assert result["status"] == "passed"
    assert result["scene_count"] == 5
    assert result["negative_control"] == "passed"
    assert {scene["scene"] for scene in result["scenes"]} == {
        "school",
        "fire-hydrant",
        "police",
        "fish-pond",
        "post-office",
    }


def test_demo_contract_has_one_shared_pipeline_and_five_minute_budget() -> None:
    contract = load_demo_contract(CONTRACT)

    assert contract["profile"] == {
        "id": "tw-nlsc-1000-NLSC112V5.4",
        "version": "NLSC112V5.4",
        "scale_denominator": 1000,
    }
    assert contract["shared"]["runner_path"] == "nmaAgentDemo.html"
    assert contract["runbook"]["full_segment_budget_seconds"] == 300
    assert sum(scene["time_budget_seconds"] for scene in contract["scenes"]) == 210

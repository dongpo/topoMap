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


def test_browser_runner_uses_one_decision_schema_and_contract_driven_controls() -> None:
    html = (ROOT / "nmaAgentDemo.html").read_text(encoding="utf-8")

    assert 'const DECISION_SCHEMA="nma.demo-decision/1.0"' in html
    assert "data/demo/five-scene-demo.json" in html
    assert "function executeRequest(request)" in html
    assert "function renderDecision(decision)" in html
    assert "function renderSceneControls()" in html
    assert "for(const scene of [...contract.scenes]" in html
    assert html.count("function executeRequest(request)") == 1
    assert "data-q=" not in html


def test_browser_evidence_panel_exposes_governance_and_abstention_fields() -> None:
    html = (ROOT / "nmaAgentDemo.html").read_text(encoding="utf-8")

    required_tokens = {
        "nma:profile",
        "nma:ruleId",
        "nma:evidence",
        "nma:graphPath",
        "source_sha256",
        "review_status",
        "graph_path",
        "No evidence was used. The agent stopped before portrayal.",
    }
    assert required_tokens <= {token for token in required_tokens if token in html}


def test_fish_pond_browser_path_exposes_geometry_and_click_evidence() -> None:
    contract = load_demo_contract(CONTRACT)
    pond = next(scene for scene in contract["scenes"] if scene["id"] == "fish-pond")
    html = (ROOT / "nmaAgentDemo.html").read_text(encoding="utf-8")

    assert pond["expected"]["feature_code"] == "9740100"
    assert pond["expected"]["evidence_page"] == 50
    assert pond["expected"]["primary_source_layer"] == "J01_WATERA"
    assert pond["expected"]["maplibre_type"] == "fill"
    assert pond["expected"]["geometry_type"] == "polygon"
    assert pond["expected"]["companion_icon"] == "waterFishIcon"
    assert 'geometry_type:impl.maplibre_type==="fill"?"polygon":"point"' in html
    assert "Geometry: <code>${decision.symbol.geometry_type}</code>" in html
    assert "map.queryRenderedFeatures(event.point)" in html
    assert 'renderDecision(executeRequest({question:"Map feature inspection",feature_code:' in html

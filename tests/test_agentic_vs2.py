import importlib.util
import json
from pathlib import Path
import sys

import pytest

from nma.agentic_vs2 import (
    PortrayalPlanningError,
    build_portrayal_plan_payload,
    parse_portrayal_plan_response,
)
from nma.graphrag import CanonicalGraphRetriever
from nma.portrayal_review import PortrayalReviewEngine


ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
RECIPES = (
    ROOT / "data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json"
)
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"


def package(query: str) -> dict:
    return CanonicalGraphRetriever.load(GRAPH).evidence_package(
        query, max_depth=3, max_nodes=40
    )


def response_for(
    evidence: dict,
    *,
    code: str,
    geometry: str,
    operation: dict,
    status: str = "proposed",
) -> dict:
    source_page = PortrayalReviewEngine.load(RECIPES).baseline(code)["page"]
    rule_id = next(
        node["id"]
        for node in evidence["evidence_nodes"]
        if node["id"].startswith("portrayal-rule:doc01:")
    )
    body = {
        "status": status,
        "reply": "已建立受限的使用者偏好提案，尚未批准。",
        "feature_code": code,
        "geometry_role": geometry,
        "operations": [operation] if status == "proposed" else [],
        "evidence_node_ids": [rule_id] if status == "proposed" else [],
        "citation_ids": [
            next(
                item["citation_id"]
                for item in evidence["citations"]
                if item.get("page") == source_page
            )
        ]
        if status == "proposed"
        else [],
    }
    return {
        "id": "resp_vs2",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(body)}],
            }
        ],
        "usage": {"input_tokens": 800, "output_tokens": 80, "total_tokens": 880},
    }


def color_operation(target: str) -> dict:
    return {
        "action": "set_color",
        "target": target,
        "value": {"color": "#1565c0", "number": None, "pattern": None, "boolean": None},
    }


def test_vs2_payload_contains_immutable_baseline_evidence_and_strict_output() -> None:
    evidence = package("養殖池 9740100 圖式")
    baseline = PortrayalReviewEngine.load(RECIPES).baseline("9740100")
    payload = build_portrayal_plan_payload(
        model="gpt-5.6-terra",
        user_request="把池內的魚符號改成藍色",
        baseline=baseline,
        evidence_package=evidence,
    )

    supplied = json.loads(payload["input"][0]["content"])
    assert supplied["official_baseline"]["source_rule_id"] == "portrayal-rule:doc01:9740100"
    assert supplied["evidence"]["automatic_rule_activation"] is False
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    operation = payload["text"]["format"]["schema"]["properties"]["operations"]["items"]
    assert operation["additionalProperties"] is False
    assert "raw_svg" not in operation["properties"]["action"]["enum"]


@pytest.mark.parametrize(
    ("query", "code", "geometry", "operation"),
    [
        ("消防栓 9350906 圖式", "9350906", "Point", color_operation("marker")),
        (
            "一般市區道路 9420801 圖式",
            "9420801",
            "LineString",
            {
                "action": "set_line_pattern",
                "target": "stroke",
                "value": {
                    "color": None,
                    "number": None,
                    "pattern": "dash",
                    "boolean": None,
                },
            },
        ),
        (
            "永久性建物 9310100 圖式",
            "9310100",
            "Polygon",
            {
                "action": "set_hatch_spacing",
                "target": "hatch",
                "value": {"color": None, "number": 2.5, "pattern": None, "boolean": None},
            },
        ),
    ],
)
def test_vs2_parses_and_validates_point_line_polygon_plans(
    query, code, geometry, operation
) -> None:
    evidence = package(query)
    parsed = parse_portrayal_plan_response(
        response_for(evidence, code=code, geometry=geometry, operation=operation),
        expected_feature_code=code,
        expected_geometry_role=geometry,
        expected_source_rule_id=f"portrayal-rule:doc01:{code}",
        expected_source_page=PortrayalReviewEngine.load(RECIPES).baseline(code)["page"],
        evidence_package=evidence,
    )

    assert parsed["schema"] == "nma.portrayal-plan-response/0.4"
    assert parsed["plan"]["geometry_role"] == geometry
    assert len(parsed["plan"]["operations"][0]["value"]) == 1
    assert parsed["automatic_action"] is False


def test_vs2_rejects_invented_evidence_and_geometry_changes() -> None:
    evidence = package("小學 9920103 圖式")
    response = response_for(
        evidence,
        code="9920103",
        geometry="Point",
        operation=color_operation("marker"),
    )
    body = json.loads(response["output"][0]["content"][0]["text"])
    body["evidence_node_ids"] = ["invented:rule"]
    response["output"][0]["content"][0]["text"] = json.dumps(body)
    with pytest.raises(PortrayalPlanningError, match="invented an evidence"):
        parse_portrayal_plan_response(
            response,
            expected_feature_code="9920103",
            expected_geometry_role="Point",
            expected_source_rule_id="portrayal-rule:doc01:9920103",
            expected_source_page=61,
            evidence_package=evidence,
        )

    changed = response_for(
        evidence,
        code="9920103",
        geometry="Polygon",
        operation=color_operation("marker"),
    )
    with pytest.raises(PortrayalPlanningError, match="changed the reviewed geometry"):
        parse_portrayal_plan_response(
            changed,
            expected_feature_code="9920103",
            expected_geometry_role="Point",
            expected_source_rule_id="portrayal-rule:doc01:9920103",
            expected_source_page=61,
            evidence_package=evidence,
        )


def test_vs2_server_endpoint_orchestrates_evidence_plan_validation_and_pending_approval(
    monkeypatch,
) -> None:
    spec = importlib.util.spec_from_file_location("nma_agent_server_vs2", SERVER_PATH)
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = server
    spec.loader.exec_module(server)
    calls = []

    def fake_call(payload, api_key):
        calls.append(payload)
        supplied = json.loads(payload["input"][0]["content"])
        evidence = supplied["evidence"]
        operation = (
            color_operation("interior-marker")
            if supplied["approved_preference_context"] is None
            else {
                "action": "set_scale",
                "target": "interior-marker",
                "value": {
                    "color": None,
                    "number": 1.4,
                    "pattern": None,
                    "boolean": None,
                },
            }
        )
        return response_for(
            evidence,
            code="9740100",
            geometry="Polygon",
            operation=operation,
        )

    monkeypatch.setattr(server, "call_openai", fake_call)
    monkeypatch.setattr(server, "PORTRAYAL_PROPOSALS", server.PortrayalProposalStore())
    monkeypatch.setattr(
        server,
        "retrieve_evidence",
        lambda query, api_key, **kwargs: server.canonical_retriever().evidence_package(
            query, **{key: value for key, value in kwargs.items() if key != "model"}
        ),
    )
    result = server.orchestrate_portrayal_review(
        {"feature_code": "9740100", "message": "把池內的魚符號改成藍色"},
        "sk-proj-placeholder",
        "gpt-5.6-terra",
    )

    assert len(calls) == 1
    assert result["schema"] == "nma.agentic-vs2-portrayal-review/0.4"
    assert result["status"] == "proposed"
    assert result["proposal"]["feature"]["geometry_role"] == "Polygon"
    assert result["proposal"]["official_baseline"]["immutable"] is True
    assert result["proposal"]["approval"]["derived_style_approval"] == (
        "pending-human-approval"
    )
    assert result["proposal_state"]["status"] == "pending"
    assert result["trace"]["events"][-1]["status"] == "pending"
    assert result["automatic_action"] is False

    decision = server.decide_portrayal_review(
        {"proposal_id": result["proposal_state"]["proposal_id"], "decision": "approve"}
    )
    assert decision["status"] == "approved-for-preview"
    assert decision["proposal"]["official_baseline"]["immutable"] is True
    assert decision["official_rule_activation"].startswith("blocked")
    assert decision["preview_execution_requested"] is False
    assert decision["automatic_action"] is False
    preview = server.compile_portrayal_review_preview(
        {"proposal_id": result["proposal_state"]["proposal_id"]}
    )
    assert preview["status"] == "compiled-for-review"
    assert preview["observation"]["render_ir"]["channels"]["interior-marker"]["color"] == (
        "#1565c0"
    )
    assert preview["tool_observation_returned"] is True
    assert preview["map_layer_created"] is False
    assert preview["automatic_action"] is False
    adapter = server.compile_portrayal_review_maplibre(
        {
            "proposal_id": result["proposal_state"]["proposal_id"],
            "source_binding": {
                "schema": "nma.maplibre-source-binding/0.4",
                "source": "nma-data",
                "source_layer": "WATERA",
                "source_geometry_type": "Polygon",
                "feature_code_field": "TERRAINID",
                "feature_code": "9740100",
                "label_field": None,
            },
        }
    )
    assert adapter["status"] == "adapter-ready-for-preview"
    assert any(
        layer["id"].endswith("interior-marker")
        for layer in adapter["adapter_result"]["layers"]
    )
    assert adapter["tool_observation_returned"] is True
    assert adapter["map_mutation_performed"] is False
    repeated = server.compile_portrayal_review_preview(
        {"proposal_id": result["proposal_state"]["proposal_id"]}
    )
    assert repeated["observation"] == preview["observation"]
    assert [item["event"] for item in repeated["history"]].count("preview-compiled") == 1

    child = server.orchestrate_portrayal_review(
        {
            "feature_code": "9740100",
            "message": "保留藍色，將池內魚符號放大 1.4 倍",
            "parent_proposal_id": result["proposal_state"]["proposal_id"],
        },
        "sk-proj-placeholder",
        "gpt-5.6-terra",
    )
    assert child["proposal_state"]["parent_proposal_id"] == result["proposal_state"][
        "proposal_id"
    ]
    assert child["proposal_state"]["lineage"] == [
        result["proposal_state"]["proposal_id"],
        child["proposal_state"]["proposal_id"],
    ]
    assert child["proposal"]["revision"]["depth"] == 1
    effective = {
        (item["action"], item["target"]): item["value"]
        for item in child["proposal"]["derived_preview_ir"]["overrides"]
    }
    assert effective[("set_color", "interior-marker")] == {"color": "#1565c0"}
    assert effective[("set_scale", "interior-marker")] == {"number": 1.4}
    assert child["proposal"]["official_baseline"] == result["proposal"][
        "official_baseline"
    ]
    supplied_child = json.loads(calls[-1]["input"][0]["content"])
    assert supplied_child["approved_preference_context"]["overrides"]
    with pytest.raises(server.AgentError, match="already has a final decision"):
        server.decide_portrayal_review(
            {"proposal_id": result["proposal_state"]["proposal_id"], "decision": "approve"}
        )


def test_v032_reuses_router_symbol_plan_and_compiles_structural_school_edit(
    monkeypatch,
) -> None:
    spec = importlib.util.spec_from_file_location("nma_agent_server_v032_structural", SERVER_PATH)
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = server
    spec.loader.exec_module(server)
    monkeypatch.setattr(server, "PORTRAYAL_PROPOSALS", server.PortrayalProposalStore())
    monkeypatch.setattr(
        server,
        "retrieve_evidence",
        lambda query, api_key, **kwargs: server.canonical_retriever().evidence_package(
            query, **{key: value for key, value in kwargs.items() if key != "model"}
        ),
    )

    def duplicate_call_forbidden(*args, **kwargs):
        raise AssertionError("The portrayal endpoint must reuse the Agent router plan.")

    monkeypatch.setattr(server, "call_openai", duplicate_call_forbidden)
    symbol_edit_plan = {
        "schema": "nma.symbol-edit-plan/1.0",
        "source": "responses-api",
        "operations": [
            {
                "action": "set_color",
                "target": "symbol",
                "value": "#1565c0",
                "reference": None,
                "relation": None,
            },
            {
                "action": "add_shape",
                "target": "support",
                "value": "rectangle",
                "reference": None,
                "relation": None,
            },
            {
                "action": "match_dimension",
                "target": "support",
                "value": None,
                "reference": "flag",
                "relation": "proportional-width",
            },
            {
                "action": "attach",
                "target": "flagpole-bottom",
                "value": None,
                "reference": "support-top",
                "relation": "inserted-into-top",
            },
            {
                "action": "center",
                "target": "flagpole-bottom",
                "value": None,
                "reference": "support",
                "relation": "centered",
            },
        ],
    }
    result = server.orchestrate_portrayal_review(
        {
            "feature_code": "9920103",
            "message": "改成藍色，新增長方形，配合三角旗比例，三角旗下方插在這個長方形",
            "symbol_edit_plan": symbol_edit_plan,
        },
        "sk-proj-placeholder",
        "gpt-5.6-terra",
    )

    assert result["status"] == "proposed"
    assert result["planning"]["response_id"] == "agent-route-symbol-edit-plan-v0.32"
    assert result["trace"]["usage"]["total_tokens"] == 0
    assert "未重複呼叫 LLM" in result["trace"]["events"][2]["detail"]
    proposal_id = result["proposal_state"]["proposal_id"]
    server.decide_portrayal_review({"proposal_id": proposal_id, "decision": "approve"})
    preview = server.compile_portrayal_review_preview({"proposal_id": proposal_id})
    render_ir = preview["observation"]["render_ir"]

    assert render_ir["channels"]["marker"]["color"] == "#1565c0"
    assert render_ir["structure"]["support"] == {
        "enabled": True,
        "shape": "rectangle",
        "width_relation": "proportional-width",
    }
    assert render_ir["structure"]["flagpole_attachment"] == "inserted-into-top"
    assert render_ir["structure"]["flagpole_horizontal_alignment"] == "centered"


def test_vs2_proposal_store_preserves_discarded_history_without_execution() -> None:
    spec = importlib.util.spec_from_file_location("nma_agent_server_vs2_store", SERVER_PATH)
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = server
    spec.loader.exec_module(server)
    store = server.PortrayalProposalStore(ttl=60, max_records=3)
    proposal = {
        "approval": {
            "derived_style_approval": "pending-human-approval",
            "official_rule_activation": "blocked-until-all-activation-gates-resolved",
        }
    }

    record = store.create(proposal, now=10)
    discarded = store.decide(record.proposal_id, "discard", now=11)

    assert discarded.status == "discarded"
    assert discarded.proposal["approval"]["derived_style_approval"] == "discarded"
    assert [item["event"] for item in discarded.history] == ["proposed", "discarded"]
    assert proposal["approval"]["derived_style_approval"] == "pending-human-approval"
    with pytest.raises(server.AgentError, match="not approved for preview"):
        store.get_for_preview(record.proposal_id, now=12)


def test_server_exposes_vs2_endpoint_without_changing_demo_page() -> None:
    source = SERVER_PATH.read_text(encoding="utf-8")
    demo = (ROOT / "nmaAgentDemoV04.html").read_text(encoding="utf-8")

    assert '"/api/portrayal-review"' in source
    assert '"/api/portrayal-review/decision"' in source
    assert '"/api/portrayal-review/preview"' in source
    assert '"/api/portrayal-review/maplibre"' in source
    assert "/api/portrayal-review" not in demo

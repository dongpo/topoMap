import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "nmaAgentDemo.html"
SERVER_PATH = ROOT / "scripts" / "run_nma_agent_server.py"
SPEC = importlib.util.spec_from_file_location("nma_agent_server", SERVER_PATH)
assert SPEC and SPEC.loader
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


def valid_route(**overrides):
    route = {
        "intent": "inspect_feature",
        "feature_query": "學校的圖式如何呈現？",
        "feature_code": "9920103",
        "style_request": None,
        "style_plan": None,
        "reply": "將查詢學校的圖式與證據。",
    }
    route.update(overrides)
    return route


def test_a04_uses_one_strict_bounded_tool_schema() -> None:
    tool = SERVER.ROUTE_TOOL
    parameters = tool["parameters"]

    assert tool["strict"] is True
    assert parameters["additionalProperties"] is False
    assert set(parameters["required"]) == set(parameters["properties"])
    assert parameters["properties"]["intent"]["enum"] == list(SERVER.INTENTS)
    plan = parameters["properties"]["style_plan"]
    assert plan["additionalProperties"] is False
    assert set(plan["required"]) == set(plan["properties"])
    operation = plan["properties"]["operations"]["items"]
    assert operation["additionalProperties"] is False
    assert set(operation["required"]) == set(operation["properties"])


def test_a04_validates_tool_calls_again_after_model_output() -> None:
    assert SERVER.validate_route(valid_route())["feature_code"] == "9920103"

    with pytest.raises(SERVER.AgentError, match="invalid tool shape"):
        SERVER.validate_route({**valid_route(), "invented": True})
    with pytest.raises(SERVER.AgentError, match="unknown tool intent"):
        SERVER.validate_route(valid_route(intent="delete_authoritative_data"))
    with pytest.raises(SERVER.AgentError, match="requires a bounded request"):
        SERVER.validate_route(
            valid_route(
                intent="propose_style_revision",
                feature_query=None,
                feature_code=None,
                style_request=None,
                style_plan=None,
            )
        )


def test_v04_validates_allowlisted_symbol_edit_plan_semantics() -> None:
    plan = {
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
        ],
    }

    route = SERVER.validate_route(
        valid_route(
            intent="propose_style_revision",
            feature_query=None,
            style_request="改成藍色，新增長方形，配合三角旗比例，三角旗下方插在這個長方形",
            style_plan=plan,
        )
    )
    assert len(route["style_plan"]["operations"]) == 4

    unsafe = {**plan, "operations": [{**plan["operations"][0], "action": "raw_svg"}]}
    with pytest.raises(SERVER.AgentError, match="unknown or duplicate action"):
        SERVER.validate_style_plan(unsafe)

    extra = {**plan, "operations": [{**plan["operations"][0], "svg": "<path />"}]}
    with pytest.raises(SERVER.AgentError, match="invalid style operation"):
        SERVER.validate_style_plan(extra)


def test_a04_builds_responses_api_continuation_with_prior_tool_result() -> None:
    session = SERVER.AgentSession(
        previous_response_id="resp_previous",
        pending_call_id="call_previous",
        turns=1,
        last_seen=1,
    )
    request = {
        "message": "放大 1.4 倍",
        "context": {
            "feature_code": "9920103",
            "feature_name": "小學",
            "pending_revision": False,
            "approved_version": 0,
        },
        "tool_result": {"outcome": "executed", "feature_code": "9920103"},
    }

    payload = SERVER.build_openai_payload(request, session, "gpt-5.6-terra")

    assert payload["previous_response_id"] == "resp_previous"
    assert payload["input"][0]["type"] == "function_call_output"
    assert payload["input"][0]["call_id"] == "call_previous"
    assert payload["tool_choice"] == "required"
    assert payload["parallel_tool_calls"] is False
    assert payload["reasoning"] == {"effort": "low"}
    assert payload["store"] is True


def test_a04_parses_exactly_one_route_call() -> None:
    response = {
        "id": "resp_123",
        "output": [
            {
                "type": "function_call",
                "name": "route_nma_turn",
                "call_id": "call_123",
                "arguments": json.dumps(valid_route(), ensure_ascii=False),
            }
        ],
    }

    response_id, call_id, route = SERVER.parse_openai_route(response)

    assert response_id == "resp_123"
    assert call_id == "call_123"
    assert route["intent"] == "inspect_feature"


def test_a04_sessions_expire_and_reset_after_bounded_turns() -> None:
    store = SERVER.SessionStore(max_turns=2, ttl=10)
    session, reset = store.acquire("session_123", now=100)
    assert reset is False
    store.update("session_123", response_id="r1", call_id="c1", now=101)
    store.update("session_123", response_id="r2", call_id="c2", now=102)

    bounded, reset = store.acquire("session_123", now=103)
    assert reset is True
    assert bounded.turns == 0
    assert bounded.previous_response_id is None

    store.update("session_123", response_id="r3", call_id="c3", now=104)
    expired, reset = store.acquire("session_123", now=115)
    assert reset is True
    assert expired.turns == 0


def test_a04_browser_keeps_application_owned_confirmation_gates_and_fallback() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert 'const AGENT_API="/api/agent"' in html
    assert "function validateAgentRoute(tool)" in html
    assert "function isExplicitApproval(text)" in html
    assert "function isExplicitDiscard(text)" in html
    assert "function isExplicitFinish(text)" in html
    assert "state?.draft&&isExplicitApproval(rawMessage)" in html
    assert "state?.draft&&isExplicitDiscard(rawMessage)" in html
    assert "function deterministicRoute(message)" in html
    assert "input.value=rawMessage;proposeStyleRevision(args.style_plan)" in html
    assert "input.value=args.style_request" not in html
    assert 'setAgentMode("deterministic-fallback","bounded fallback")' in html
    assert "function submitSymbolEdit()" in html
    assert "function validateSymbolEditPlan(plan,supported)" in html
    assert "lastAgentToolResult=result" in html
    assert "Tool: ${args.intent} · ${result.outcome}" in html


def test_a04_local_settings_do_not_require_or_expose_key_to_browser(tmp_path: Path) -> None:
    secret = "sk-proj-test-secret-value"
    (tmp_path / ".env.local").write_text(
        f"OPENAI_API_KEY={secret}\nOPENAI_MODEL=gpt-5.6-terra\n", encoding="utf-8"
    )

    key, model = SERVER.load_local_settings(tmp_path)
    html = HTML.read_text(encoding="utf-8")

    assert key == secret
    assert model == "gpt-5.6-terra"
    assert secret not in html
    assert "OPENAI_API_KEY" not in html

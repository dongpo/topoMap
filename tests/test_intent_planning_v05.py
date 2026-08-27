from __future__ import annotations

from nma.intent_planning_v05 import INTENT_PLAN_JSON_SCHEMA, INTENT_PLAN_SCHEMA, plan_intent


def test_information_query_produces_read_only_retrieval_plan() -> None:
    result = plan_intent("What is school symbol rule?")

    assert result == {
        "schema": INTENT_PLAN_SCHEMA,
        "intent": "retrieve_information",
        "feature": {"code": "9920103"},
        "operation": {"type": "retrieve_rule"},
        "target": "official_portrayal",
        "constraints": ["read_only", "official_portrayal_immutable", "no_execution"],
        "evidence_required": True,
        "approval_required": False,
        "immutable": True,
    }


def test_modification_query_requires_approval_and_targets_derived_symbol() -> None:
    result = plan_intent("Change school symbol color")

    assert result["intent"] == "modify_portrayal"
    assert result["feature"] == {"code": "9920103"}
    assert result["operation"] == {"type": "change_color"}
    assert result["target"] == "derived_symbol"
    assert result["evidence_required"] is True
    assert result["approval_required"] is True
    assert result["immutable"] is True
    assert "no_execution" in result["constraints"]


def test_official_feature_creation_is_unsupported_and_non_executing() -> None:
    result = plan_intent("Create a new official feature")

    assert result["intent"] == "unsupported_request"
    assert result["operation"] == {"type": "create_official_feature"}
    assert result["target"] == "official_portrayal"
    assert result["evidence_required"] is True
    assert result["approval_required"] is True
    assert result["immutable"] is True
    assert "no_execution" in result["constraints"]


def test_schema_is_strict_and_requires_every_governance_field() -> None:
    assert INTENT_PLAN_JSON_SCHEMA["additionalProperties"] is False
    assert set(INTENT_PLAN_JSON_SCHEMA["required"]) == {
        "schema",
        "intent",
        "feature",
        "operation",
        "target",
        "constraints",
        "evidence_required",
        "approval_required",
        "immutable",
    }
    assert INTENT_PLAN_JSON_SCHEMA["properties"]["evidence_required"]["const"] is True
    assert INTENT_PLAN_JSON_SCHEMA["properties"]["immutable"]["const"] is True

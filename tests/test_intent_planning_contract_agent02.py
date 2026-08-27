from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

import pytest
from jsonschema import Draft202012Validator

from agent_contracts.intent_planning import (
    CONTRACT_VERSION,
    PRODUCTION_FEATURES,
    PRODUCTION_ROUTE_KINDS,
    RETAINED_DEMO_ROUTE_KINDS,
    V05_PLANNER_DISPOSITION,
    V05_REPLACEMENT_CONTRACT,
    V05_REPLACEMENT_OWNER,
    IntentPlanningError,
    adapt_public_runtime_route,
    adapt_retained_demo_route,
    plan_request,
    validate_intent_plan,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "intent-planning-v1.0.schema.json"
PROTECTED_PRODUCTION_HASHES = {
    "nmaAgentDemo.html": "8b6d6310d3ac6b45e71b73102de023869b0f56422dfbf1c74d81a6650ba5a470",
    "scripts/build_public_site.py": "6f9e6e75281f50eb4d6297d9fea7018e165cfdcb0d6ac56873f9940e0a50c55e",
    "pyproject.toml": "56a2ece294c01d90f59d349d9f8a99f782dcb07a372259196023ecf87a7837a8",
}
FORBIDDEN_FIELD_FRAGMENTS = {
    "approval",
    "authoriz",
    "command",
    "endpoint",
    "execution",
    "filesystem",
    "mutation",
    "path",
    "shell",
    "tool",
    "url",
    "write",
}


def _schema() -> dict[str, object]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _legacy_route(intent: str, *, feature_code: str | None = "9920103") -> dict[str, object]:
    return {
        "intent": intent,
        "feature_query": "小學",
        "feature_code": feature_code,
        "style_request": None,
        "style_plan": None,
        "reply": "bounded legacy reply",
    }


def _html_intents(path: Path) -> tuple[str, ...]:
    source = path.read_text(encoding="utf-8")
    match = re.search(r"const AGENT_INTENTS=new Set\((\[[^;]+\])\);", source)
    assert match is not None
    return tuple(json.loads(match.group(1)))


def test_contract_schema_is_valid_closed_and_has_one_version() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema"] == {"const": CONTRACT_VERSION}
    assert tuple(schema["properties"]["route_kind"]["enum"]) == PRODUCTION_ROUTE_KINDS
    assert schema["required"] == [
        "schema",
        "boundary",
        "route_kind",
        "disposition",
        "feature_code",
        "display_intent",
        "evidence_intent",
        "reason_code",
    ]


def test_supported_production_evidence_and_preview_intents() -> None:
    evidence = plan_request("What is the primary school symbol rule?")
    assert evidence == {
        "schema": CONTRACT_VERSION,
        "boundary": "canonical-production",
        "route_kind": "present_evidence",
        "disposition": "proposal",
        "feature_code": "9920103",
        "display_intent": "evidence_panel",
        "evidence_intent": "required",
        "reason_code": "supported_evidence_request",
    }

    preview = plan_request("Change the color to blue", active_feature_code="9920103")
    assert preview == {
        "schema": CONTRACT_VERSION,
        "boundary": "canonical-production",
        "route_kind": "propose_portrayal_preview",
        "disposition": "proposal",
        "feature_code": "9920103",
        "display_intent": "portrayal_preview",
        "evidence_intent": "required",
        "reason_code": "supported_portrayal_request",
    }
    Draft202012Validator(_schema()).validate(evidence)
    Draft202012Validator(_schema()).validate(preview)


@pytest.mark.parametrize(
    ("input_text", "reason"),
    [
        ("Delete the official school feature", "unsupported_request"),
        ("Run a shell command", "unsupported_request"),
        ("Tell me a joke", "unsupported_request"),
        ("What is the portrayal rule?", "missing_feature_context"),
        ("Show the school symbol", "ambiguous_request"),
        ("Compare 9920103 and 9950201", "ambiguous_request"),
        ("Show and change the primary school symbol", "ambiguous_request"),
    ],
)
def test_unsupported_and_ambiguous_inputs_abstain(input_text: str, reason: str) -> None:
    result = plan_request(input_text)
    assert result["route_kind"] == "abstain"
    assert result["disposition"] == "abstention"
    assert result["feature_code"] is None
    assert result["display_intent"] == "none"
    assert result["evidence_intent"] == "none"
    assert result["reason_code"] == reason


def test_planning_is_deterministic_for_equivalent_inputs() -> None:
    expected = plan_request("What is the PRIMARY   SCHOOL symbol rule?")
    assert plan_request("  what is the primary school symbol rule?  ") == expected
    assert [plan_request("9950201") for _ in range(20)] == [plan_request("9950201")] * 20


def test_version_unknown_route_unknown_fields_and_invalid_combinations_fail_closed() -> None:
    valid = plan_request("9950201")
    mutations = []
    for field, value in (
        ("schema", "nma.intent-planning/9.9"),
        ("route_kind", "execute_mutation"),
        ("display_intent", "write_file"),
        ("feature_code", "../../tmp/output"),
    ):
        changed = deepcopy(valid)
        changed[field] = value
        mutations.append(changed)
    changed = deepcopy(valid)
    changed["authorization_id"] = "auth-1"
    mutations.append(changed)
    changed = deepcopy(valid)
    changed["route_kind"] = "abstain"
    mutations.append(changed)

    for value in mutations:
        with pytest.raises(IntentPlanningError):
            validate_intent_plan(value)


def test_contract_has_no_authorization_execution_or_mutation_field() -> None:
    schema = _schema()
    field_names = set(schema["properties"])
    assert not {
        name
        for name in field_names
        if any(fragment in name.casefold() for fragment in FORBIDDEN_FIELD_FRAGMENTS)
    }
    for result in (
        plan_request("What is the post office symbol?"),
        plan_request("Change color", active_feature_code="9950201"),
        plan_request("Deploy the layer"),
    ):
        assert set(result) == set(schema["required"])
        serialized = json.dumps(result, sort_keys=True)
        assert not any(f'"{fragment}' in serialized for fragment in FORBIDDEN_FIELD_FRAGMENTS)


def test_production_feature_vocabulary_matches_public_portrayal_graph() -> None:
    graph = json.loads(
        (ROOT / "data" / "knowledge" / "portrayal-graph.json").read_text(encoding="utf-8")
    )
    graph_codes = {
        node["properties"]["code"] for node in graph["nodes"] if node["type"] == "FeatureType"
    }
    assert {feature.code for feature in PRODUCTION_FEATURES} == graph_codes


def test_v04_v031_v032_vocabularies_are_retained_demo_only_and_project_safely() -> None:
    for name in ("nmaAgentDemoV04.html", "nmaAgentDemoV031.html", "nmaAgentDemoV032.html"):
        assert _html_intents(ROOT / name) == RETAINED_DEMO_ROUTE_KINDS

    assert adapt_retained_demo_route(_legacy_route("inspect_feature"))["route_kind"] == (
        "present_evidence"
    )
    assert adapt_retained_demo_route(_legacy_route("propose_style_revision"))["route_kind"] == (
        "propose_portrayal_preview"
    )
    for intent in (
        "approve_revision",
        "discard_revision",
        "finish_revisions",
        "request_layer_confirmation",
        "reset_session",
    ):
        result = adapt_retained_demo_route(_legacy_route(intent))
        assert result["boundary"] == "retained-demo"
        assert result["route_kind"] == "abstain"
        assert result["reason_code"] == "downstream_state_transition"


def test_unchanged_public_browser_routes_project_to_the_production_subset() -> None:
    assert _html_intents(ROOT / "nmaAgentDemo.html") == RETAINED_DEMO_ROUTE_KINDS
    evidence = adapt_public_runtime_route(_legacy_route("inspect_feature"))
    preview = adapt_public_runtime_route(_legacy_route("propose_style_revision"))
    assert evidence["boundary"] == preview["boundary"] == "canonical-production"
    assert evidence["route_kind"] == "present_evidence"
    assert preview["route_kind"] == "propose_portrayal_preview"

    for intent in (
        "approve_revision",
        "discard_revision",
        "finish_revisions",
        "request_layer_confirmation",
        "reset_session",
    ):
        result = adapt_public_runtime_route(_legacy_route(intent))
        assert result["route_kind"] == "abstain"
        assert result["reason_code"] == "downstream_state_transition"

    outside_reviewed_graph = adapt_public_runtime_route(
        _legacy_route("inspect_feature", feature_code="9420101")
    )
    assert outside_reviewed_graph["route_kind"] == "abstain"


def test_retained_adapter_rejects_unknown_routes_and_fields() -> None:
    with pytest.raises(IntentPlanningError, match="Unknown retained demo route kind"):
        adapt_retained_demo_route(_legacy_route("delete_authoritative_data"))
    with pytest.raises(IntentPlanningError, match="exact legacy field set"):
        adapt_retained_demo_route({**_legacy_route("inspect_feature"), "command": "rm"})


def test_v05_planner_is_explicitly_deprecated_with_shared_replacement_owner() -> None:
    assert V05_PLANNER_DISPOSITION == "deprecated"
    assert V05_REPLACEMENT_CONTRACT == CONTRACT_VERSION
    assert V05_REPLACEMENT_OWNER == "agent_contracts.intent_planning.plan_request"
    assert _file_sha256(ROOT / "src/nma/intent_planning_v05.py") == (
        "327769d3a37665f699fe603b196d40468979debdce5151c917efad69071e9ae7"
    )


def test_canonical_public_runtime_and_dependency_boundary_are_byte_identical() -> None:
    for relative, expected in PROTECTED_PRODUCTION_HASHES.items():
        assert _file_sha256(ROOT / relative) == expected
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "dependencies = []" in pyproject
    public_builder = (ROOT / "scripts" / "build_public_site.py").read_text(encoding="utf-8")
    assert "intent_planning" not in public_builder
    assert "intent-planning-v1.0.schema.json" not in public_builder

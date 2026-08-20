from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError
import pytest
from referencing import Registry, Resource

import build_contracts.gate_review as build03
from build_contracts.gate_review import (
    EXPECTED_BOUNDARIES,
    GATE_REQUIREMENTS,
    BuildGateReviewError,
    prepare_build_gate_review,
    request_build_execution_authorization,
    review_sha256,
    validate_gate_review,
)
from build_contracts.portrayal_decision import (
    BUILD_GATE_IDS,
    BuildPortrayalDecisionError,
)
from nma.core import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = ROOT / "data/specifications/nma-build-02-golden-decision-v1.0.json"
PROPOSAL_PATH = ROOT / "data/specifications/nma-build-02-golden-proposal-v1.0.json"
REVIEW_PATH = (
    ROOT / "data/specifications/nma-build-03-golden-gate-review-v1.0.json"
)
DECISION_SCHEMA_PATH = ROOT / "schemas/build-portrayal-decision-v1.0.schema.json"
REVIEW_SCHEMA_PATH = ROOT / "schemas/build-gate-review-v1.0.schema.json"


@pytest.fixture()
def decision() -> dict[str, Any]:
    return json.loads(DECISION_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def proposal() -> dict[str, Any]:
    return json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def review(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> dict[str, Any]:
    return prepare_build_gate_review(proposal, decision)


def _fails(callable_, code: str | None = None) -> BuildGateReviewError:
    with pytest.raises(BuildGateReviewError) as caught:
        callable_()
    if code is not None:
        assert caught.value.code == code
    return caught.value


def test_golden_inputs_generate_exact_blocked_review(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    actual = prepare_build_gate_review(proposal, decision)

    assert actual == json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    assert actual["review_sha256"] == (
        "4177a2cc29738ad7b1bc6f00f2c10c724fec3c475e57dee45ad2e8e1f105cbdd"
    )


def test_closed_schema_is_meta_valid_and_accepts_only_blocked_review(
    review: dict[str, Any],
) -> None:
    decision_schema = json.loads(DECISION_SCHEMA_PATH.read_text(encoding="utf-8"))
    review_schema = json.loads(REVIEW_SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(review_schema)
    assert review_schema["additionalProperties"] is False
    assert review_schema["$defs"]["boundaries"]["additionalProperties"] is False
    registry = Registry().with_resource(
        decision_schema["$id"], Resource.from_contents(decision_schema)
    )
    validator = Draft202012Validator(review_schema, registry=registry)
    validator.validate(review)

    changed = deepcopy(review)
    changed["authorization"] = {"approved": True}
    with pytest.raises(ValidationError):
        validator.validate(changed)


def test_exact_build02_build01_and_evidence_bindings(review: dict[str, Any]) -> None:
    assert review["bindings"] == {
        "proposal_sha256": "1e588ea2d7752ce7b02c28d6117c4deb1d6c8995dcbace14cfcb542eca847749",
        "decision_sha256": "624fafe1f84164f6f28396d21153a3ed0f9795ead87b6e9c605115b35ee3c846",
        "build01_package_sha256": "59b6f972046dbe9af295de414525230b03ed6da4f0e78374076b5cc4a2cdd7de",
        "source_archive_sha256": "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
        "fixture_id": "build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a",
        "observation_id": "build-observation:sha256:8fdbb3bdea8ffe715e7d76eed7c5034bd62226ba649be2206cf7a9e07b853bac",
        "feature_reference": "build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f",
        "attribute_commitment_sha256": "ddfa112586b9c2bc3a61bdf2638b7994ba1200bfce5d8ad34988f2a24da96078",
        "geometry_commitment_sha256": "23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f",
        "portrayal_record_set_sha256": "70ef0c8e8e86ed5d2a2a4a588b41086f3fd20fb6987138e3897b71378f4b294a",
        "portrayal_recipe_sha256": "450ee18fe87ea2a7f1d783747ee22ae927c73a2f46424f65900f28f9981f2e20",
    }


def test_all_five_gates_are_unresolved_and_require_human_decisions(
    review: dict[str, Any],
) -> None:
    gates = review["review"]["gates"]

    assert [gate["gate_id"] for gate in gates] == list(BUILD_GATE_IDS)
    assert tuple(GATE_REQUIREMENTS) == BUILD_GATE_IDS
    assert all(gate["status"] == "unresolved" for gate in gates)
    assert all(gate["decision_record"] is None for gate in gates)
    assert all(gate["required_human_decision"] for gate in gates)
    assert review["review"]["unresolved_gate_count"] == 5
    assert review["review"]["all_gates_resolved"] is False


def test_no_human_decision_or_approval_is_inferred(review: dict[str, Any]) -> None:
    assert review["review"]["actor_type"] == "unassigned-human-reviewer"
    assert review["review"]["human_decision"] is None
    assert review["boundaries"]["human_gate_decisions_inferred"] is False
    assert review["boundaries"]["approval_recorded"] is False


def test_execution_authorization_is_explicitly_blocked(review: dict[str, Any]) -> None:
    assert review["authorization_effect"] == {
        "execution_authorization_eligible": False,
        "execution_authorization_issued": False,
        "issuance_blocked": True,
        "blocker": "five-explicit-human-gate-decisions-required",
    }


def test_approval_request_fails_on_unresolved_gates(
    review: dict[str, Any], proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    _fails(
        lambda: request_build_execution_authorization(
            review, proposal, decision, "approved"
        ),
        "unresolved_gates",
    )


@pytest.mark.parametrize("human_decision", [None, "rejected"])
def test_absent_or_rejected_decision_issues_nothing(
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    human_decision: str | None,
) -> None:
    assert (
        request_build_execution_authorization(
            review, proposal, decision, human_decision
        )
        is None
    )


def test_invalid_human_decision_is_rejected(
    review: dict[str, Any], proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    _fails(
        lambda: request_build_execution_authorization(
            review, proposal, decision, "yes"
        ),
        "decision_invalid",
    )


@pytest.mark.parametrize(
    ("change", "value"),
    [
        ("status", "approved"),
        ("actor", "system"),
        ("human-decision", "approved"),
        ("hatch-angle", 45.0),
        ("gate-status", "resolved"),
        ("gate-decision", {"approved": True}),
        ("gate-count", 4),
        ("all-resolved", True),
        ("authorization-eligible", True),
        ("authorization-issued", True),
        ("blocker", None),
    ],
)
def test_rehashed_review_tampering_fails_closed(
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    change: str,
    value: object,
) -> None:
    changed = deepcopy(review)
    if change == "status":
        changed["review"]["status"] = value
    elif change == "actor":
        changed["review"]["actor_type"] = value
    elif change == "human-decision":
        changed["review"]["human_decision"] = value
    elif change == "hatch-angle":
        changed["review"]["requested_portrayal"]["hatch"][
            "numeric_angle_degrees"
        ] = value
    elif change == "gate-status":
        changed["review"]["gates"][0]["status"] = value
    elif change == "gate-decision":
        changed["review"]["gates"][0]["decision_record"] = value
    elif change == "gate-count":
        changed["review"]["unresolved_gate_count"] = value
    elif change == "all-resolved":
        changed["review"]["all_gates_resolved"] = value
    elif change == "authorization-eligible":
        changed["authorization_effect"]["execution_authorization_eligible"] = value
    elif change == "authorization-issued":
        changed["authorization_effect"]["execution_authorization_issued"] = value
    else:
        changed["authorization_effect"]["blocker"] = value
    changed["review_sha256"] = review_sha256(changed)

    _fails(lambda: validate_gate_review(changed, proposal, decision), "review_invalid")


@pytest.mark.parametrize("boundary", sorted(EXPECTED_BOUNDARIES))
def test_authority_boundary_cannot_be_expanded(
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    boundary: str,
) -> None:
    changed = deepcopy(review)
    changed["boundaries"][boundary] = not EXPECTED_BOUNDARIES[boundary]
    changed["review_sha256"] = review_sha256(changed)

    _fails(lambda: validate_gate_review(changed, proposal, decision), "review_invalid")


def test_changed_build02_predecessor_fails_closed(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    changed = deepcopy(proposal)
    changed["bindings"]["decision_sha256"] = "0" * 64

    with pytest.raises(BuildPortrayalDecisionError):
        prepare_build_gate_review(changed, decision)


def test_hash_is_deterministic_and_uses_frozen_core_provider(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    first = prepare_build_gate_review(proposal, decision)
    second = prepare_build_gate_review(
        json.loads(json.dumps(proposal, sort_keys=True)),
        json.loads(json.dumps(decision, sort_keys=True)),
    )

    assert first == second
    assert first["review_sha256"] == review_sha256(first)
    assert build03.canonical_sha256 is canonical_sha256
    assert "def canonical_sha256" not in inspect.getsource(build03)


def test_inputs_are_not_mutated(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    before_proposal = deepcopy(proposal)
    before_decision = deepcopy(decision)

    prepare_build_gate_review(proposal, decision)

    assert proposal == before_proposal
    assert decision == before_decision


def test_no_private_geometry_or_raw_attributes_are_disclosed(
    review: dict[str, Any],
) -> None:
    serialized = json.dumps(review, ensure_ascii=False).casefold()

    assert "2bxkp71rbn" not in serialized
    assert "coordinates" not in serialized
    assert "geometry_wkb_hex" not in serialized
    assert "source_example" not in serialized
    assert review["boundaries"]["raw_source_disclosure_allowed"] is False
    assert review["boundaries"]["redistribution_allowed"] is False


def test_module_has_no_execution_geometry_network_or_runtime_capability() -> None:
    source = inspect.getsource(build03).casefold()

    assert "subprocess" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "shapely" not in source
    assert "maplibre" not in source
    assert ".write_" not in source
    assert "authorization_id" not in source
    assert "idempotency" not in source


def test_build02_predecessor_and_portrayal_are_exact(
    review: dict[str, Any], proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    assert review["bindings"]["proposal_sha256"] == proposal["proposal_sha256"]
    assert review["bindings"]["decision_sha256"] == decision["decision_sha256"]
    assert review["review"]["requested_portrayal"] == proposal["proposal"][
        "requested_changes"
    ]

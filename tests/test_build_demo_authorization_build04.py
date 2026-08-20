from __future__ import annotations

from copy import deepcopy
import inspect
import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError
import pytest

import build_contracts.demo_authorization as build04
from build_contracts.demo_authorization import (
    AUTHORIZATION_ID,
    ISSUANCE_DECISION,
    BuildDemoAuthorizationError,
    authorization_sha256,
    consumption_plan_sha256,
    issue_build_demo_authorization,
    plan_build_demo_consumption,
    validate_build_demo_authorization,
)
from build_contracts.gate_resolution import BuildGateResolutionError
from nma.core import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = ROOT / "data/specifications/nma-build-02-golden-decision-v1.0.json"
PROPOSAL_PATH = ROOT / "data/specifications/nma-build-02-golden-proposal-v1.0.json"
REVIEW_PATH = ROOT / "data/specifications/nma-build-03-golden-gate-review-v1.0.json"
RESOLUTION_PATH = (
    ROOT / "data/specifications/nma-build-03a-golden-gate-resolution-v1.0.json"
)
AUTHORIZATION_PATH = (
    ROOT / "data/specifications/nma-build-04-golden-demo-authorization-v1.0.json"
)
SCHEMA_PATH = ROOT / "schemas/build-demo-authorization-v1.0.schema.json"


@pytest.fixture()
def decision() -> dict[str, Any]:
    return json.loads(DECISION_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def proposal() -> dict[str, Any]:
    return json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def review() -> dict[str, Any]:
    return json.loads(REVIEW_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def resolution() -> dict[str, Any]:
    return json.loads(RESOLUTION_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def authorization(
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    result = issue_build_demo_authorization(
        resolution, review, proposal, decision, ISSUANCE_DECISION
    )
    assert result is not None
    return result


@pytest.fixture()
def demo_request(
    authorization: dict[str, Any], resolution: dict[str, Any]
) -> dict[str, Any]:
    return {
        "request_schema": "nma.build-demo-authorization-request/1.0",
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": authorization["authorization_sha256"],
        "resolution_sha256": resolution["resolution_sha256"],
        "fixture_id": resolution["bindings"]["fixture_id"],
        "layer_id": "J13_BUILD",
        "feature_code": "9310100",
        "feature_reference": resolution["bindings"]["feature_reference"],
        "target": "derived MapLibre web DEMO portrayal candidate",
        "operation": "render-derived-maplibre-building-demo",
        "hatch_angle_degrees": 45.0,
        "idempotency_key": "build04-demo-default-45-v1",
    }


def _fails(callable_, code: str | None = None) -> BuildDemoAuthorizationError:
    with pytest.raises(BuildDemoAuthorizationError) as caught:
        callable_()
    if code is not None:
        assert caught.value.code == code
    return caught.value


def test_exact_phase_decision_issues_golden_authorization(
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    actual = issue_build_demo_authorization(
        resolution, review, proposal, decision, ISSUANCE_DECISION
    )

    assert actual == json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
    assert actual["authorization_sha256"] == (
        "f609fa99ae0280987e11a3328e04d26484c15a65f72a0266566f2aaa9f650b2d"
    )


def test_closed_schema_is_meta_valid_and_accepts_only_exact_authorization(
    authorization: dict[str, Any],
) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    validator = Draft202012Validator(schema)
    validator.validate(authorization)

    changed = deepcopy(authorization)
    changed["production"] = {"allowed": True}
    with pytest.raises(ValidationError):
        validator.validate(changed)


def test_issuance_is_explicit_and_bound_to_human_approved_resolution(
    authorization: dict[str, Any],
) -> None:
    assert authorization["issuance"] == {
        "actor_type": "human-project-owner",
        "decision": ISSUANCE_DECISION,
        "statement_zh_tw": "進行 BUILD-04。",
        "issued_on": "2026-08-20",
        "basis": "exact-human-approved-build-03a-demo-resolution",
    }


def test_authorization_binds_complete_predecessor_and_source_chain(
    authorization: dict[str, Any], resolution: dict[str, Any]
) -> None:
    bindings = authorization["bindings"]

    assert bindings["resolution_sha256"] == resolution["resolution_sha256"]
    assert bindings["review_sha256"] == resolution["bindings"]["review_sha256"]
    assert bindings["proposal_sha256"] == resolution["bindings"]["proposal_sha256"]
    assert bindings["decision_sha256"] == resolution["bindings"]["decision_sha256"]
    assert bindings["source_archive_sha256"] == (
        "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
    )
    assert bindings["fixture_id"] == resolution["bindings"]["fixture_id"]


def test_capability_is_non_transferable_to_other_source_or_operation(
    authorization: dict[str, Any],
) -> None:
    capability = authorization["capability"]

    assert capability["scope"] == "single-consumption-derived-demo"
    assert capability["target"] == "derived MapLibre web DEMO portrayal candidate"
    assert capability["operation"] == "render-derived-maplibre-building-demo"
    assert capability["source_scope"] == {
        "source_archive_sha256": "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
        "fixture_id": "build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a",
        "layer_id": "J13_BUILD",
        "feature_code": "9310100",
        "feature_reference": "build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f",
        "access_mode": "read-only-single-feature-after-consumption-validation",
    }


def test_only_hatch_angle_is_adjustable_within_demo_range(
    authorization: dict[str, Any],
) -> None:
    capability = authorization["capability"]

    assert capability["allowed_parameter_overrides"] == {
        "hatch.numeric_angle_degrees": {
            "type": "number",
            "minimum_inclusive": 0.0,
            "maximum_exclusive": 180.0,
            "default": 45.0,
            "step": 1.0,
            "demo_only": True,
        }
    }
    assert capability["all_other_portrayal_fields_fixed_by_resolution"] is True


def test_lifecycle_is_single_use_non_transferable_revocable_and_expiring(
    authorization: dict[str, Any],
) -> None:
    lifecycle = authorization["lifecycle"]

    assert lifecycle["issued_status"] == "issued-not-consumed"
    assert lifecycle["single_consumption"] is True
    assert lifecycle["non_transferable"] is True
    assert lifecycle["revocable_before_consumption"] is True
    assert lifecycle["expiry_policy"] == (
        "first-consumption-or-revocation-or-predecessor-change"
    )
    assert lifecycle["idempotency_key_required"] is True


def test_permissions_allow_only_exact_bound_read_after_validation(
    authorization: dict[str, Any],
) -> None:
    permissions = authorization["permissions"]

    assert permissions["demo_execution_allowed_after_consumption_validation"] is True
    assert permissions[
        "exact_bound_source_read_allowed_after_consumption_validation"
    ] is True
    for forbidden in (
        "production_execution_allowed",
        "source_write_allowed",
        "geometry_repair_allowed",
        "source_z_dimension_drop_allowed",
        "runtime_wiring_allowed",
        "network_access_allowed",
        "raw_source_disclosure_allowed",
        "redistribution_allowed",
        "demo_policy_promotion_allowed",
    ):
        assert permissions[forbidden] is False


def test_authorization_is_issued_but_not_consumed_or_executed(
    authorization: dict[str, Any],
) -> None:
    assert authorization["authorization_effect"] == {
        "authorization_issued": True,
        "authorization_consumed": False,
        "actual_execution_performed": False,
        "runtime_wired": False,
    }


def test_default_request_produces_exact_non_executing_plan(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
) -> None:
    plan = plan_build_demo_consumption(
        authorization, resolution, review, proposal, decision, demo_request
    )

    assert plan["status"] == "validated-not-executed"
    assert plan["parameters"] == {
        "hatch_angle_degrees": 45.0,
        "user_adjusted_from_default": False,
    }
    assert plan["idempotency_key_sha256"] == (
        "61adf89dd58741cd582af47b6edaa6b9470b66c975e3b8dbe23e44da32462355"
    )
    assert plan["boundaries"] == {
        "execution_performed": False,
        "runtime_wired": False,
        "source_accessed": False,
        "source_mutated": False,
        "production_activated": False,
    }
    assert plan["plan_sha256"] == (
        "b8b5ecd54954b190eb8cda398710039f334e8424fd0969816380b4a2b52b0b71"
    )
    assert plan["plan_sha256"] == consumption_plan_sha256(plan)


def test_user_adjusted_angle_is_preserved_in_non_executing_plan(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
) -> None:
    changed = deepcopy(demo_request)
    changed["hatch_angle_degrees"] = 90

    plan = plan_build_demo_consumption(
        authorization, resolution, review, proposal, decision, changed
    )

    assert plan["parameters"] == {
        "hatch_angle_degrees": 90.0,
        "user_adjusted_from_default": True,
    }
    assert plan["boundaries"]["execution_performed"] is False


@pytest.mark.parametrize("angle", [-1, 180, 45.5, math.nan, math.inf, True, "45"])
def test_invalid_or_out_of_scope_angles_fail_closed(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
    angle: object,
) -> None:
    changed = deepcopy(demo_request)
    changed["hatch_angle_degrees"] = angle

    _fails(
        lambda: plan_build_demo_consumption(
            authorization, resolution, review, proposal, decision, changed
        ),
        "angle_invalid",
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authorization_id", "other-authorization"),
        ("authorization_sha256", "0" * 64),
        ("resolution_sha256", "0" * 64),
        ("fixture_id", "other-fixture"),
        ("layer_id", "J17_BUILD"),
        ("feature_code", "9310103"),
        ("feature_reference", "build-feature:sha256:" + "0" * 64),
        ("target", "production"),
        ("operation", "write-source"),
    ],
)
def test_request_cannot_transfer_capability(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
    field: str,
    value: object,
) -> None:
    changed = deepcopy(demo_request)
    changed[field] = value

    _fails(
        lambda: plan_build_demo_consumption(
            authorization, resolution, review, proposal, decision, changed
        ),
        "request_binding_mismatch",
    )


def test_request_shape_is_closed(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
) -> None:
    changed = deepcopy(demo_request)
    changed["line_width"] = 2

    _fails(
        lambda: plan_build_demo_consumption(
            authorization, resolution, review, proposal, decision, changed
        ),
        "request_invalid",
    )


@pytest.mark.parametrize("key", ["short", "contains space", "x" * 101, "角度-45"])
def test_invalid_idempotency_keys_fail_closed(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
    key: str,
) -> None:
    changed = deepcopy(demo_request)
    changed["idempotency_key"] = key

    _fails(
        lambda: plan_build_demo_consumption(
            authorization, resolution, review, proposal, decision, changed
        ),
        "idempotency_key_invalid",
    )


def test_revoked_authorization_cannot_be_planned(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
) -> None:
    _fails(
        lambda: plan_build_demo_consumption(
            authorization,
            resolution,
            review,
            proposal,
            decision,
            demo_request,
            revoked_authorization_ids={AUTHORIZATION_ID},
        ),
        "authorization_revoked",
    )


def test_consumed_authorization_cannot_be_reused(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
) -> None:
    _fails(
        lambda: plan_build_demo_consumption(
            authorization,
            resolution,
            review,
            proposal,
            decision,
            demo_request,
            consumed_authorization_ids={AUTHORIZATION_ID},
        ),
        "authorization_consumed",
    )


@pytest.mark.parametrize(
    ("change", "value"),
    [
        ("issuance", "system"),
        ("resolution", "0" * 64),
        ("scope", "production"),
        ("source-layer", "J17_BUILD"),
        ("angle-max", 360.0),
        ("single-use", False),
        ("non-transferable", False),
        ("revocable", False),
        ("production", True),
        ("source-write", True),
        ("z-drop", True),
        ("consumed", True),
        ("executed", True),
    ],
)
def test_rehashed_authorization_tampering_fails_closed(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    change: str,
    value: object,
) -> None:
    changed = deepcopy(authorization)
    if change == "issuance":
        changed["issuance"]["actor_type"] = value
    elif change == "resolution":
        changed["bindings"]["resolution_sha256"] = value
    elif change == "scope":
        changed["capability"]["scope"] = value
    elif change == "source-layer":
        changed["capability"]["source_scope"]["layer_id"] = value
    elif change == "angle-max":
        changed["capability"]["allowed_parameter_overrides"][
            "hatch.numeric_angle_degrees"
        ]["maximum_exclusive"] = value
    elif change == "single-use":
        changed["lifecycle"]["single_consumption"] = value
    elif change == "non-transferable":
        changed["lifecycle"]["non_transferable"] = value
    elif change == "revocable":
        changed["lifecycle"]["revocable_before_consumption"] = value
    elif change == "production":
        changed["permissions"]["production_execution_allowed"] = value
    elif change == "source-write":
        changed["permissions"]["source_write_allowed"] = value
    elif change == "z-drop":
        changed["permissions"]["source_z_dimension_drop_allowed"] = value
    elif change == "consumed":
        changed["authorization_effect"]["authorization_consumed"] = value
    else:
        changed["authorization_effect"]["actual_execution_performed"] = value
    changed["authorization_sha256"] = authorization_sha256(changed)

    _fails(
        lambda: validate_build_demo_authorization(
            changed, resolution, review, proposal, decision
        ),
        "authorization_invalid",
    )


@pytest.mark.parametrize("issuance", ["approved", "execute", "build-04"])
def test_generic_phase_decision_cannot_issue_capability(
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    issuance: str,
) -> None:
    _fails(
        lambda: issue_build_demo_authorization(
            resolution, review, proposal, decision, issuance
        ),
        "issuance_scope_mismatch",
    )


def test_absent_issuance_decision_creates_nothing(
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    assert (
        issue_build_demo_authorization(resolution, review, proposal, decision, None)
        is None
    )


def test_changed_build03a_predecessor_fails_closed(
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    changed = deepcopy(resolution)
    changed["scope_policy"]["demo_choices_are_production_authority"] = True

    with pytest.raises(BuildGateResolutionError):
        issue_build_demo_authorization(
            changed, review, proposal, decision, ISSUANCE_DECISION
        )


def test_hashes_are_deterministic_and_use_frozen_core_provider(
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
) -> None:
    first = issue_build_demo_authorization(
        resolution, review, proposal, decision, ISSUANCE_DECISION
    )
    second = issue_build_demo_authorization(
        json.loads(json.dumps(resolution, sort_keys=True)),
        json.loads(json.dumps(review, sort_keys=True)),
        json.loads(json.dumps(proposal, sort_keys=True)),
        json.loads(json.dumps(decision, sort_keys=True)),
        ISSUANCE_DECISION,
    )

    assert first == second
    assert first is not None
    assert first["authorization_sha256"] == authorization_sha256(first)
    assert build04.canonical_sha256 is canonical_sha256
    assert "def canonical_sha256" not in inspect.getsource(build04)

    plan = plan_build_demo_consumption(
        first, resolution, review, proposal, decision, demo_request
    )
    assert plan["plan_sha256"] == consumption_plan_sha256(plan)


def test_inputs_are_not_mutated(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
) -> None:
    before = deepcopy(
        (authorization, resolution, review, proposal, decision, demo_request)
    )

    plan_build_demo_consumption(
        authorization, resolution, review, proposal, decision, demo_request
    )

    assert (
        authorization,
        resolution,
        review,
        proposal,
        decision,
        demo_request,
    ) == before


def test_plan_discloses_no_raw_idempotency_source_geometry_or_attributes(
    authorization: dict[str, Any],
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    demo_request: dict[str, Any],
) -> None:
    plan = plan_build_demo_consumption(
        authorization, resolution, review, proposal, decision, demo_request
    )
    serialized = json.dumps(plan, ensure_ascii=False).casefold()

    assert demo_request["idempotency_key"] not in serialized
    assert "coordinates" not in serialized
    assert "geometry_wkb_hex" not in serialized
    assert "build_no" not in serialized
    assert "build_str" not in serialized
    assert plan["boundaries"]["source_accessed"] is False


def test_module_has_no_execution_geometry_network_runtime_or_write_capability() -> None:
    source = inspect.getsource(build04).casefold()

    assert "subprocess" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "shapely" not in source
    assert "maplibre_adapter" not in source
    assert ".write_" not in source
    assert "open(" not in source
    assert "pathlib" not in source

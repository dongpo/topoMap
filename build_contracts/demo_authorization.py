"""BUILD-04 single-use DEMO authorization and non-executing consumption guard.

The capability is bound to the exact BUILD-03A resolution and can authorize
only a later derived MapLibre DEMO render.  This module validates and plans;
it has no renderer, source access, persistence, or execution side effects.
"""

from __future__ import annotations

from collections.abc import Collection
from copy import deepcopy
import math
import re
from typing import Any, Mapping

from build_contracts.gate_resolution import validate_gate_resolution
from nma.core import canonical_sha256


AUTHORIZATION_SCHEMA = "nma.build-demo-authorization/1.0"
AUTHORIZATION_VERSION = "build-04/1.0"
REQUEST_SCHEMA = "nma.build-demo-authorization-request/1.0"
PLAN_SCHEMA = "nma.build-demo-consumption-plan/1.0"
ISSUANCE_DECISION = "issue-single-consumption-build-demo-authorization"
AUTHORIZATION_ID = "build-04-demo-auth-a5a8f11b94784a60"
EXPECTED_RESOLUTION_SHA256 = (
    "a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01"
)
EXPECTED_REVIEW_SHA256 = (
    "4177a2cc29738ad7b1bc6f00f2c10c724fec3c475e57dee45ad2e8e1f105cbdd"
)
EXPECTED_PROPOSAL_SHA256 = (
    "1e588ea2d7752ce7b02c28d6117c4deb1d6c8995dcbace14cfcb542eca847749"
)
EXPECTED_DECISION_SHA256 = (
    "624fafe1f84164f6f28396d21153a3ed0f9795ead87b6e9c605115b35ee3c846"
)
EXPECTED_BUILD01_PACKAGE_SHA256 = (
    "59b6f972046dbe9af295de414525230b03ed6da4f0e78374076b5cc4a2cdd7de"
)
EXPECTED_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
EXPECTED_FIXTURE_ID = (
    "build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a"
)
EXPECTED_FEATURE_REFERENCE = (
    "build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f"
)
TARGET = "derived MapLibre web DEMO portrayal candidate"
OPERATION = "render-derived-maplibre-building-demo"
IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9._:-]{8,100}$")

CAPABILITY = {
    "scope": "single-consumption-derived-demo",
    "target": TARGET,
    "operation": OPERATION,
    "feature_reference": EXPECTED_FEATURE_REFERENCE,
    "source_scope": {
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "fixture_id": EXPECTED_FIXTURE_ID,
        "layer_id": "J13_BUILD",
        "feature_code": "9310100",
        "feature_reference": EXPECTED_FEATURE_REFERENCE,
        "access_mode": "read-only-single-feature-after-consumption-validation",
    },
    "allowed_parameter_overrides": {
        "hatch.numeric_angle_degrees": {
            "type": "number",
            "minimum_inclusive": 0.0,
            "maximum_exclusive": 180.0,
            "default": 45.0,
            "step": 1.0,
            "demo_only": True,
        }
    },
    "all_other_portrayal_fields_fixed_by_resolution": True,
}

LIFECYCLE = {
    "issued_status": "issued-not-consumed",
    "single_consumption": True,
    "non_transferable": True,
    "revocable_before_consumption": True,
    "expiry_policy": "first-consumption-or-revocation-or-predecessor-change",
    "wall_clock_expiry": None,
    "required_binding_fields": [
        "authorization_id",
        "authorization_sha256",
        "resolution_sha256",
        "fixture_id",
        "layer_id",
        "feature_code",
        "feature_reference",
        "target",
        "operation",
    ],
    "idempotency_key_required": True,
}

PERMISSIONS = {
    "demo_execution_allowed_after_consumption_validation": True,
    "production_execution_allowed": False,
    "exact_bound_source_read_allowed_after_consumption_validation": True,
    "source_write_allowed": False,
    "geometry_repair_allowed": False,
    "source_z_dimension_drop_allowed": False,
    "runtime_wiring_allowed": False,
    "network_access_allowed": False,
    "raw_source_disclosure_allowed": False,
    "redistribution_allowed": False,
    "demo_policy_promotion_allowed": False,
}

AUTHORIZATION_EFFECT = {
    "authorization_issued": True,
    "authorization_consumed": False,
    "actual_execution_performed": False,
    "runtime_wired": False,
}


class BuildDemoAuthorizationError(ValueError):
    """BUILD-04 rejected an invalid capability or consumption request."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildDemoAuthorizationError(message, code=code)


def _exact(value: Any, expected: Any, *, label: str, code: str) -> None:
    if value != expected:
        _fail(f"{label} does not match the frozen BUILD-04 authorization.", code)


def _bindings() -> dict[str, Any]:
    return {
        "resolution_sha256": EXPECTED_RESOLUTION_SHA256,
        "review_sha256": EXPECTED_REVIEW_SHA256,
        "proposal_sha256": EXPECTED_PROPOSAL_SHA256,
        "decision_sha256": EXPECTED_DECISION_SHA256,
        "build01_package_sha256": EXPECTED_BUILD01_PACKAGE_SHA256,
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "fixture_id": EXPECTED_FIXTURE_ID,
        "feature_reference": EXPECTED_FEATURE_REFERENCE,
    }


def _authorization_template() -> dict[str, Any]:
    return {
        "authorization_version": AUTHORIZATION_VERSION,
        "schema_version": AUTHORIZATION_SCHEMA,
        "authorization_id": AUTHORIZATION_ID,
        "issuance": {
            "actor_type": "human-project-owner",
            "decision": ISSUANCE_DECISION,
            "statement_zh_tw": "進行 BUILD-04。",
            "issued_on": "2026-08-20",
            "basis": "exact-human-approved-build-03a-demo-resolution",
        },
        "bindings": _bindings(),
        "capability": deepcopy(CAPABILITY),
        "lifecycle": deepcopy(LIFECYCLE),
        "permissions": deepcopy(PERMISSIONS),
        "authorization_effect": deepcopy(AUTHORIZATION_EFFECT),
    }


def authorization_sha256(authorization: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(authorization))
    basis.pop("authorization_sha256", None)
    return canonical_sha256(basis)


def consumption_plan_sha256(plan: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(plan))
    basis.pop("plan_sha256", None)
    return canonical_sha256(basis)


def _validate_predecessors(
    resolution: Mapping[str, Any],
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> None:
    validate_gate_resolution(resolution, review, proposal, decision)
    _exact(
        resolution.get("resolution_sha256"),
        EXPECTED_RESOLUTION_SHA256,
        label="BUILD-03A resolution identity",
        code="resolution_hash_mismatch",
    )


def validate_build_demo_authorization(
    authorization: Mapping[str, Any],
    resolution: Mapping[str, Any],
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the exact single-use DEMO grant without consuming it."""

    _validate_predecessors(resolution, review, proposal, decision)
    if not isinstance(authorization, Mapping):
        _fail("The BUILD-04 authorization must be an object.", "authorization_invalid")
    expected = _authorization_template()
    expected["authorization_sha256"] = authorization_sha256(expected)
    if set(authorization) != set(expected):
        _fail(
            "The BUILD-04 authorization fields are not closed.",
            "authorization_schema_invalid",
        )
    for field, value in expected.items():
        _exact(
            authorization.get(field),
            value,
            label=f"Authorization field {field}",
            code="authorization_invalid",
        )
    if authorization.get("authorization_sha256") != authorization_sha256(
        authorization
    ):
        _fail(
            "The BUILD-04 authorization hash is invalid.",
            "authorization_hash_mismatch",
        )
    return deepcopy(dict(authorization))


def issue_build_demo_authorization(
    resolution: Mapping[str, Any],
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
    issuance_decision: str | None,
) -> dict[str, Any] | None:
    """Issue the frozen DEMO grant; do not execute or persist any consumption."""

    _validate_predecessors(resolution, review, proposal, decision)
    if issuance_decision is None:
        return None
    if issuance_decision != ISSUANCE_DECISION:
        _fail(
            "The exact BUILD-04 DEMO issuance decision is required.",
            "issuance_scope_mismatch",
        )
    authorization = _authorization_template()
    authorization["authorization_sha256"] = authorization_sha256(authorization)
    return validate_build_demo_authorization(
        authorization, resolution, review, proposal, decision
    )


def _validate_state_ids(values: Collection[str], *, label: str) -> set[str]:
    if isinstance(values, (str, bytes)) or not all(
        isinstance(value, str) for value in values
    ):
        _fail(f"The {label} state must contain string IDs.", "consumer_state_invalid")
    return set(values)


def _validate_angle(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail("The DEMO hatch angle must be numeric.", "angle_invalid")
    angle = float(value)
    if not math.isfinite(angle) or not 0.0 <= angle < 180.0 or angle % 1.0 != 0.0:
        _fail(
            "The DEMO hatch angle must be a finite whole degree in [0, 180).",
            "angle_invalid",
        )
    return angle


def plan_build_demo_consumption(
    authorization: Mapping[str, Any],
    resolution: Mapping[str, Any],
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    revoked_authorization_ids: Collection[str] = (),
    consumed_authorization_ids: Collection[str] = (),
) -> dict[str, Any]:
    """Validate one consumption request and return a non-executing plan."""

    checked = validate_build_demo_authorization(
        authorization, resolution, review, proposal, decision
    )
    revoked = _validate_state_ids(
        revoked_authorization_ids, label="revoked-authorization"
    )
    consumed = _validate_state_ids(
        consumed_authorization_ids, label="consumed-authorization"
    )
    if AUTHORIZATION_ID in revoked:
        _fail("The BUILD-04 authorization has been revoked.", "authorization_revoked")
    if AUTHORIZATION_ID in consumed:
        _fail("The BUILD-04 authorization was already consumed.", "authorization_consumed")
    if not isinstance(request, Mapping):
        _fail("The BUILD-04 consumption request must be an object.", "request_invalid")
    required = {
        "request_schema",
        "authorization_id",
        "authorization_sha256",
        "resolution_sha256",
        "fixture_id",
        "layer_id",
        "feature_code",
        "feature_reference",
        "target",
        "operation",
        "hatch_angle_degrees",
        "idempotency_key",
    }
    if set(request) != required:
        _fail("The BUILD-04 consumption request fields are not closed.", "request_invalid")
    exact_fields = {
        "request_schema": REQUEST_SCHEMA,
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": checked["authorization_sha256"],
        "resolution_sha256": EXPECTED_RESOLUTION_SHA256,
        "fixture_id": EXPECTED_FIXTURE_ID,
        "layer_id": "J13_BUILD",
        "feature_code": "9310100",
        "feature_reference": EXPECTED_FEATURE_REFERENCE,
        "target": TARGET,
        "operation": OPERATION,
    }
    for field, expected in exact_fields.items():
        _exact(
            request.get(field),
            expected,
            label=f"Consumption request {field}",
            code="request_binding_mismatch",
        )
    angle = _validate_angle(request.get("hatch_angle_degrees"))
    idempotency_key = request.get("idempotency_key")
    if not isinstance(idempotency_key, str) or not IDEMPOTENCY_KEY.fullmatch(
        idempotency_key
    ):
        _fail("The BUILD-04 idempotency key is invalid.", "idempotency_key_invalid")
    plan = {
        "plan_schema": PLAN_SCHEMA,
        "status": "validated-not-executed",
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": checked["authorization_sha256"],
        "resolution_sha256": EXPECTED_RESOLUTION_SHA256,
        "feature_reference": EXPECTED_FEATURE_REFERENCE,
        "target": TARGET,
        "operation": OPERATION,
        "parameters": {
            "hatch_angle_degrees": angle,
            "user_adjusted_from_default": angle != 45.0,
        },
        "idempotency_key_sha256": canonical_sha256(
            {"idempotency_key": idempotency_key}
        ),
        "boundaries": {
            "execution_performed": False,
            "runtime_wired": False,
            "source_accessed": False,
            "source_mutated": False,
            "production_activated": False,
        },
    }
    plan["plan_sha256"] = consumption_plan_sha256(plan)
    return deepcopy(plan)


__all__ = [
    "AUTHORIZATION_ID",
    "BuildDemoAuthorizationError",
    "ISSUANCE_DECISION",
    "authorization_sha256",
    "consumption_plan_sha256",
    "issue_build_demo_authorization",
    "plan_build_demo_consumption",
    "validate_build_demo_authorization",
]

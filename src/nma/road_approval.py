from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from nma.road_portrayal_decision import (
    DERIVED_TARGET,
    EXPECTED_ARCHIVE_SHA256,
    EXPECTED_EVIDENCE_IDS,
    EXPECTED_FIXTURE_SHA256,
    EXPECTED_PORTRAYAL,
    EXPECTED_ROUTE_IDENTITY,
    EXPECTED_SOURCE_IDS,
    EXPECTED_UPSTREAM_PACKAGE_SHA256,
    validate_proposal,
)
from nma.road_resolution import canonical_sha256


APPROVAL_SCHEMA = "nma.road-approval/1.0"
APPROVAL_VERSION = "road-03/1.0"
AUTHORIZATION_SCHEMA = "nma.road-execution-authorization/1.0"
AUTHORIZATION_VERSION = "road-03/1.0"

EXPECTED_PROPOSAL_SHA256 = (
    "3d45d1ed039c2af1aa7f050fa1e3c22158c891390c001285054b05a02959ce06"
)
EXPECTED_DECISION_SHA256 = (
    "0d671b1fed3f4b19e4204e745bdcb13f872f3a00dcb4ef5050a091a14065e090"
)

RESTRICTED_PERMISSIONS = {
    "source_mutation_allowed": False,
    "topology_repair_allowed": False,
    "roada_execution_allowed": False,
    "road_edge_derivation_allowed": False,
}


class RoadApprovalError(ValueError):
    """ROAD-03 rejected an invalid approval or authorization boundary."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise RoadApprovalError(message, code=code)


def _exact(value: Any, expected: Any, *, label: str, code: str) -> None:
    if value != expected:
        _fail(f"{label} does not match the frozen ROAD-03 binding.", code)


def approval_sha256(approval: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(approval))
    basis.pop("approval_sha256", None)
    return canonical_sha256(basis)


def authorization_sha256(authorization: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(authorization))
    basis.pop("authorization_sha256", None)
    return canonical_sha256(basis)


def _bindings() -> dict[str, Any]:
    return {
        "proposal_sha256": EXPECTED_PROPOSAL_SHA256,
        "decision_sha256": EXPECTED_DECISION_SHA256,
        "road01_package_sha256": EXPECTED_UPSTREAM_PACKAGE_SHA256,
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "fixture_sha256": EXPECTED_FIXTURE_SHA256,
        "ordered_source_ids": list(EXPECTED_SOURCE_IDS),
        "route_identity": EXPECTED_ROUTE_IDENTITY,
        "class_code": "9420400",
        "evidence_ids": list(EXPECTED_EVIDENCE_IDS),
        "requested_portrayal": deepcopy(EXPECTED_PORTRAYAL),
        "execution_target": DERIVED_TARGET,
    }


def _approval_template(human_decision: str) -> dict[str, Any]:
    approved = human_decision == "approved"
    return {
        "approval_version": APPROVAL_VERSION,
        "schema_version": APPROVAL_SCHEMA,
        "human_decision": human_decision,
        "actor_type": "human",
        "bindings": _bindings(),
        "authorization_effect": {
            "execution_authorization_eligible": approved,
            "execution_authorization_denied": not approved,
        },
    }


def _authorization_template(approval_hash: str) -> dict[str, Any]:
    return {
        "authorization_version": AUTHORIZATION_VERSION,
        "schema_version": AUTHORIZATION_SCHEMA,
        "approval_sha256": approval_hash,
        "bindings": _bindings(),
        "capability": {
            "execution_allowed": True,
            "execution_target": DERIVED_TARGET,
            "allowed_changes": deepcopy(EXPECTED_PORTRAYAL),
        },
        "permissions": deepcopy(RESTRICTED_PERMISSIONS),
    }


def _validate_closed_artifact(
    artifact: Mapping[str, Any],
    expected: Mapping[str, Any],
    *,
    hash_field: str,
    kind: str,
) -> None:
    if not isinstance(artifact, Mapping):
        _fail(f"The ROAD-03 {kind} must be an object.", f"{kind}_invalid")
    missing = set(expected) - set(artifact)
    extra = set(artifact) - set(expected)
    if missing or extra:
        _fail(
            f"The ROAD-03 {kind} fields are not closed (missing={sorted(missing)!r}, "
            f"extra={sorted(extra)!r}).",
            f"{kind}_schema_invalid",
        )
    expected_without_hash = deepcopy(dict(expected))
    expected_hash = expected_without_hash.pop(hash_field)
    for key, value in expected_without_hash.items():
        _exact(artifact.get(key), value, label=f"{kind} field {key}", code=f"{kind}_invalid")
    computed = (
        approval_sha256(artifact)
        if kind == "approval"
        else authorization_sha256(artifact)
    )
    if artifact.get(hash_field) != expected_hash or computed != expected_hash:
        _fail(f"The ROAD-03 {kind} hash is invalid.", f"{kind}_hash_mismatch")


def validate_approval(
    approval: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a deterministic human decision against the exact frozen proposal."""

    validate_proposal(proposal, decision)
    _exact(
        proposal.get("proposal_sha256"),
        EXPECTED_PROPOSAL_SHA256,
        label="Proposal SHA-256",
        code="proposal_hash_mismatch",
    )
    _exact(
        decision.get("decision_sha256"),
        EXPECTED_DECISION_SHA256,
        label="Decision SHA-256",
        code="decision_hash_mismatch",
    )
    if not isinstance(approval, Mapping):
        _fail("The ROAD-03 approval must be an object.", "approval_invalid")
    human_decision = approval.get("human_decision")
    if human_decision not in {"approved", "rejected"}:
        _fail("An explicit approved or rejected human decision is required.", "decision_missing")
    expected = _approval_template(human_decision)
    expected["approval_sha256"] = approval_sha256(expected)
    _validate_closed_artifact(
        approval, expected, hash_field="approval_sha256", kind="approval"
    )
    return deepcopy(dict(approval))


def validate_authorization(
    authorization: Mapping[str, Any],
    approval: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a capability grant; this function has no execution side effects."""

    checked_approval = validate_approval(approval, proposal, decision)
    if checked_approval["human_decision"] != "approved":
        _fail("A rejected decision cannot authorize execution.", "authorization_denied")
    expected = _authorization_template(checked_approval["approval_sha256"])
    expected["authorization_sha256"] = authorization_sha256(expected)
    _validate_closed_artifact(
        authorization,
        expected,
        hash_field="authorization_sha256",
        kind="authorization",
    )
    return deepcopy(dict(authorization))


def authorize_road_portrayal(
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
    human_decision: str | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Record an explicit decision and, only on approval, issue one capability grant."""

    validate_proposal(proposal, decision)
    if human_decision is None:
        return None, None
    if human_decision not in {"approved", "rejected"}:
        _fail("An explicit approved or rejected human decision is required.", "decision_invalid")

    approval = _approval_template(human_decision)
    approval["approval_sha256"] = approval_sha256(approval)
    validate_approval(approval, proposal, decision)
    if human_decision == "rejected":
        return approval, None

    authorization = _authorization_template(approval["approval_sha256"])
    authorization["authorization_sha256"] = authorization_sha256(authorization)
    validate_authorization(authorization, approval, proposal, decision)
    return approval, authorization

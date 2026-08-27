"""BUILD-03 unresolved-gate review and authorization guard.

BUILD-03 records why the BUILD-02 portrayal cannot yet be authorized.  It
does not invent human decisions, resolve cartographic gates, or issue an
execution capability.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from build_contracts.portrayal_decision import (
    BUILD_GATE_IDS,
    EXPECTED_BOUNDARIES as BUILD02_BOUNDARIES,
    EXPECTED_PORTRAYAL,
    validate_proposal,
)
from nma.core import canonical_sha256


REVIEW_SCHEMA = "nma.build-gate-review/1.0"
REVIEW_VERSION = "build-03/1.0"
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
EXPECTED_OBSERVATION_ID = (
    "build-observation:sha256:8fdbb3bdea8ffe715e7d76eed7c5034bd62226ba649be2206cf7a9e07b853bac"
)
EXPECTED_FEATURE_REFERENCE = (
    "build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f"
)
EXPECTED_ATTRIBUTE_COMMITMENT = (
    "ddfa112586b9c2bc3a61bdf2638b7994ba1200bfce5d8ad34988f2a24da96078"
)
EXPECTED_GEOMETRY_COMMITMENT = (
    "23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f"
)
EXPECTED_RECORD_SET_SHA256 = (
    "70ef0c8e8e86ed5d2a2a4a588b41086f3fd20fb6987138e3897b71378f4b294a"
)
EXPECTED_RECIPE_SHA256 = "450ee18fe87ea2a7f1d783747ee22ae927c73a2f46424f65900f28f9981f2e20"

GATE_REQUIREMENTS = {
    "hatch-angle-transcription": {
        "evidence_state": "numeric-angle-not-specified",
        "required_decision": (
            "approve a numeric angle or a renderer-independent semantic orientation policy"
        ),
    },
    "building-annotation-placement": {
        "evidence_state": "collision-and-placement-policy-not-specified",
        "required_decision": "approve deterministic annotation placement and collision behavior",
    },
    "real-build-schema-binding": {
        "evidence_state": "documented-and-observed-field-authority-not-equivalent",
        "required_decision": (
            "approve a J13-bounded BUILD_NO/BUILD_STR mapping without asserting ID/SOURCE equivalence"
        ),
    },
    "line-and-color-profile": {
        "evidence_state": "device-independent-line-and-color-profile-not-approved",
        "required_decision": "approve rendering profiles for line code 2 and colour code 7",
    },
    "j13-polygonz-runtime-policy": {
        "evidence_state": "target-runtime-and-z-policy-not-specified",
        "required_decision": (
            "approve a target-runtime-specific PolygonZ preservation or transformation policy"
        ),
    },
}

EXPECTED_BOUNDARIES = {
    "human_gate_decisions_inferred": False,
    "approval_recorded": False,
    "execution_authorization_eligible": False,
    "execution_authorization_issued": False,
    "execution_allowed": False,
    "source_mutation_allowed": False,
    "geometry_repair_allowed": False,
    "z_dimension_drop_allowed": False,
    "runtime_wiring_allowed": False,
    "raw_source_disclosure_allowed": False,
    "redistribution_allowed": False,
}


class BuildGateReviewError(ValueError):
    """BUILD-03 rejected a changed review or attempted authorization."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildGateReviewError(message, code=code)


def _exact(value: Any, expected: Any, *, label: str, code: str) -> None:
    if value != expected:
        _fail(f"{label} does not match the frozen BUILD-03 binding.", code)


def _bindings() -> dict[str, Any]:
    return {
        "proposal_sha256": EXPECTED_PROPOSAL_SHA256,
        "decision_sha256": EXPECTED_DECISION_SHA256,
        "build01_package_sha256": EXPECTED_BUILD01_PACKAGE_SHA256,
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "fixture_id": EXPECTED_FIXTURE_ID,
        "observation_id": EXPECTED_OBSERVATION_ID,
        "feature_reference": EXPECTED_FEATURE_REFERENCE,
        "attribute_commitment_sha256": EXPECTED_ATTRIBUTE_COMMITMENT,
        "geometry_commitment_sha256": EXPECTED_GEOMETRY_COMMITMENT,
        "portrayal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
        "portrayal_recipe_sha256": EXPECTED_RECIPE_SHA256,
    }


def _gate_records() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": gate_id,
            "status": "unresolved",
            "evidence_state": GATE_REQUIREMENTS[gate_id]["evidence_state"],
            "required_human_decision": GATE_REQUIREMENTS[gate_id]["required_decision"],
            "decision_record": None,
        }
        for gate_id in BUILD_GATE_IDS
    ]


def _review_template() -> dict[str, Any]:
    return {
        "review_version": REVIEW_VERSION,
        "schema_version": REVIEW_SCHEMA,
        "bindings": _bindings(),
        "review": {
            "status": "authorization-blocked-unresolved-gates",
            "actor_type": "unassigned-human-reviewer",
            "human_decision": None,
            "requested_portrayal": deepcopy(EXPECTED_PORTRAYAL),
            "gates": _gate_records(),
            "unresolved_gate_count": len(BUILD_GATE_IDS),
            "all_gates_resolved": False,
        },
        "authorization_effect": {
            "execution_authorization_eligible": False,
            "execution_authorization_issued": False,
            "issuance_blocked": True,
            "blocker": "five-explicit-human-gate-decisions-required",
        },
        "boundaries": deepcopy(EXPECTED_BOUNDARIES),
    }


def review_sha256(review: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(review))
    basis.pop("review_sha256", None)
    return canonical_sha256(basis)


def _validate_build02_artifacts(
    proposal: Mapping[str, Any], decision: Mapping[str, Any]
) -> None:
    validate_proposal(proposal, decision)
    _exact(
        proposal.get("proposal_sha256"),
        EXPECTED_PROPOSAL_SHA256,
        label="Proposal identity",
        code="proposal_hash_mismatch",
    )
    _exact(
        decision.get("decision_sha256"),
        EXPECTED_DECISION_SHA256,
        label="Decision identity",
        code="decision_hash_mismatch",
    )
    proposal_bindings = proposal.get("bindings")
    if not isinstance(proposal_bindings, Mapping):
        _fail("BUILD-02 proposal bindings are missing.", "proposal_binding_mismatch")
    expected_subset = {
        "upstream_package_sha256": EXPECTED_BUILD01_PACKAGE_SHA256,
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "fixture_id": EXPECTED_FIXTURE_ID,
        "observation_id": EXPECTED_OBSERVATION_ID,
        "feature_reference": EXPECTED_FEATURE_REFERENCE,
        "attribute_commitment_sha256": EXPECTED_ATTRIBUTE_COMMITMENT,
        "geometry_commitment_sha256": EXPECTED_GEOMETRY_COMMITMENT,
        "portrayal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
        "portrayal_recipe_sha256": EXPECTED_RECIPE_SHA256,
    }
    for field, expected in expected_subset.items():
        _exact(
            proposal_bindings.get(field),
            expected,
            label=f"Proposal binding {field}",
            code="proposal_binding_mismatch",
        )
    _exact(
        proposal.get("boundaries"),
        BUILD02_BOUNDARIES,
        label="BUILD-02 authority boundary",
        code="permission_escalation",
    )


def validate_gate_review(
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the exact pending review and its non-authorization effect."""

    _validate_build02_artifacts(proposal, decision)
    if not isinstance(review, Mapping):
        _fail("The BUILD-03 review must be an object.", "review_invalid")
    expected = _review_template()
    expected["review_sha256"] = review_sha256(expected)
    if set(review) != set(expected):
        _fail("The BUILD-03 review fields are not closed.", "review_schema_invalid")
    for field, value in expected.items():
        _exact(review.get(field), value, label=f"Review field {field}", code="review_invalid")
    if review.get("review_sha256") != review_sha256(review):
        _fail("The BUILD-03 review hash is invalid.", "review_hash_mismatch")
    return deepcopy(dict(review))


def prepare_build_gate_review(
    proposal: Mapping[str, Any], decision: Mapping[str, Any]
) -> dict[str, Any]:
    """Record all unresolved gates without inferring any human approval."""

    _validate_build02_artifacts(proposal, decision)
    review = _review_template()
    review["review_sha256"] = review_sha256(review)
    return validate_gate_review(review, proposal, decision)


def request_build_execution_authorization(
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
    human_decision: str | None,
) -> None:
    """Refuse authorization until separately recorded decisions resolve every gate."""

    checked = validate_gate_review(review, proposal, decision)
    if human_decision is None or human_decision == "rejected":
        return None
    if human_decision != "approved":
        _fail("The human decision must be approved, rejected, or absent.", "decision_invalid")
    if checked["review"]["all_gates_resolved"] is not True:
        _fail(
            "BUILD execution cannot be authorized while review gates remain unresolved.",
            "unresolved_gates",
        )
    _fail("No BUILD-03 execution authorization capability exists.", "authorization_unavailable")


__all__ = [
    "BuildGateReviewError",
    "EXPECTED_BOUNDARIES",
    "GATE_REQUIREMENTS",
    "prepare_build_gate_review",
    "request_build_execution_authorization",
    "review_sha256",
    "validate_gate_review",
]

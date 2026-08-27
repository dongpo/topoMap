"""BUILD-02 evidence-bound building portrayal decision and proposal.

This module prepares closed review artifacts only.  It cannot execute, mutate source
geometry, resolve pending cartographic gates, or wire a runtime.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from build_contracts.resolution import package_sha256
from nma.core import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORTRAYAL_RECORD_SET_PATH = (
    ROOT
    / "data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json"
)
DECISION_SCHEMA = "nma.build-portrayal-decision/1.0"
DECISION_VERSION = "build-02/1.0"
PROPOSAL_SCHEMA = "nma.build-portrayal-proposal/1.0"
PROPOSAL_VERSION = "build-02/1.0"

EXPECTED_UPSTREAM_PACKAGE_SHA256 = (
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
EXPECTED_PROFILE_IDENTITY = (
    "5f560c8fde92b7ed590c8f4d1292ae69743e033b2bbf43b837b083b5c611dc09"
)
EXPECTED_SOURCE_SCOPE = (
    "a4e3eff87f1df770e01c3675fe883335b4416c405922d22b129e85fc4a44065b"
)
EXPECTED_RECORD_SET_ID = "nma-portrayal-recipe-review-batch-01-v0.4"
EXPECTED_RECORD_SET_SHA256 = (
    "70ef0c8e8e86ed5d2a2a4a588b41086f3fd20fb6987138e3897b71378f4b294a"
)
EXPECTED_RECIPE_SHA256 = "450ee18fe87ea2a7f1d783747ee22ae927c73a2f46424f65900f28f9981f2e20"
EXPECTED_SOURCE_DOCUMENT_SHA256 = (
    "1f9c4457d7ced86f2b7681e21be9ad3b7b7ae364981ab995ef27b468e0fa2620"
)
EXPECTED_SOURCE_RULE_ID = "portrayal-rule:doc01:9310100"
EXPECTED_EVIDENCE_SECTION_ID = "section:doc01-portrayal:p8"

ACTION = "prepare review-only derived building-polygon portrayal candidate"
DERIVED_TARGET = "derived building-polygon portrayal candidate"
SOURCE_GATE_IDS = (
    "hatch-angle-transcription",
    "building-annotation-placement",
    "real-build-schema-binding",
    "line-and-color-profile",
)
BUILD_GATE_IDS = (*SOURCE_GATE_IDS, "j13-polygonz-runtime-policy")

EXPECTED_PORTRAYAL = {
    "representation_kind": "feature-following-hatched-polygon",
    "geometry_policy": {
        "source_geometry_type": "PolygonZ",
        "canonical_geometry_role": "Polygon",
        "preserve_z_dimension": True,
        "dimension_drop_authorized": False,
        "geometry_repair_authorized": False,
    },
    "boundary": {
        "primitive_id": "surveyed-building-boundary",
        "line_code": "2",
        "color_code": "7",
    },
    "hatch": {
        "primitive_id": "building-diagonal-hatch",
        "clip_to_feature_geometry": True,
        "spacing_mm": 2.0,
        "orientation_semantic": "diagonal rising from lower-left to upper-right",
        "numeric_angle_degrees": None,
    },
    "annotation": {
        "primitive_id": "floor-and-structure-annotation",
        "content_fields": ["BUILD_NO", "BUILD_STR"],
        "content_semantics": "floor count plus structure code",
        "placement_policy": "unresolved-pending-human-review",
    },
}

EXPECTED_BOUNDARIES = {
    "authorization_required": True,
    "human_review_required": True,
    "execution_allowed": False,
    "source_mutation_allowed": False,
    "geometry_repair_allowed": False,
    "z_dimension_drop_allowed": False,
    "runtime_wiring_allowed": False,
    "raw_source_disclosure_allowed": False,
    "redistribution_allowed": False,
    "legacy_j17_runtime_binding_allowed": False,
}


class BuildPortrayalDecisionError(ValueError):
    """BUILD-02 rejected changed evidence or an attempted authority expansion."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildPortrayalDecisionError(message, code=code)


def _exact(value: Any, expected: Any, *, label: str, code: str) -> None:
    if value != expected:
        _fail(f"{label} does not match the frozen BUILD-02 binding.", code)


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuildPortrayalDecisionError(
            f"{label} is unreadable.", code=f"{label}_unreadable"
        ) from error
    if not isinstance(value, dict):
        _fail(f"{label} must be an object.", f"{label}_invalid")
    return value


def validate_upstream_package(package: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the complete BUILD-01 semantic and integrity boundary."""

    if not isinstance(package, Mapping):
        _fail("The BUILD-01 input must be an object.", "upstream_invalid")
    value = deepcopy(dict(package))
    _exact(
        value.get("package_sha256"),
        EXPECTED_UPSTREAM_PACKAGE_SHA256,
        label="Upstream package SHA-256",
        code="upstream_hash_mismatch",
    )
    try:
        computed = package_sha256(value)
    except (TypeError, ValueError):
        _fail("The BUILD-01 package is not canonically serializable.", "upstream_invalid")
    if computed != EXPECTED_UPSTREAM_PACKAGE_SHA256:
        _fail("The BUILD-01 package content changed.", "upstream_hash_mismatch")

    _exact(value.get("package_version"), "build-01/1.0", label="Version", code="binding_mismatch")
    _exact(
        value.get("schema_version"),
        "nma.build-resolution-evidence-package/1.0",
        label="Schema",
        code="binding_mismatch",
    )
    _exact(
        value.get("source"),
        {
            "fixture_id": EXPECTED_FIXTURE_ID,
            "archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "layer_id": "J13_BUILD",
            "feature_code": "9310100",
        },
        label="Source",
        code="source_binding_mismatch",
    )
    _exact(
        value.get("resolution"),
        {
            "selection_policy": "largest-valid-2d-area-desc-then-build-id-asc",
            "eligible_feature_count": 2962,
            "selected_rank": 1,
            "largest_area_tie_count": 1,
            "feature_reference": EXPECTED_FEATURE_REFERENCE,
        },
        label="Resolution",
        code="resolution_binding_mismatch",
    )
    _exact(
        value.get("identity_evidence"),
        {
            "provider": "nma.core.canonical_sha256",
            "attribute_commitment_sha256": EXPECTED_ATTRIBUTE_COMMITMENT,
            "profile_identity_sha256": EXPECTED_PROFILE_IDENTITY,
            "source_scope_sha256": EXPECTED_SOURCE_SCOPE,
        },
        label="Identity evidence",
        code="identity_binding_mismatch",
    )
    _exact(
        value.get("geometry_evidence"),
        {
            "geometry_commitment_sha256": EXPECTED_GEOMETRY_COMMITMENT,
            "source_geometry_type": "PolygonZ",
            "canonical_geometry_role": "Polygon",
            "area_2d_m2": "1316.686891452159",
            "vertex_count": 65,
            "ring_count": 1,
            "is_valid": True,
            "z_dimension_present": True,
            "repair_required": False,
        },
        label="Geometry evidence",
        code="geometry_binding_mismatch",
    )
    _exact(
        value.get("observation"),
        {"id": EXPECTED_OBSERVATION_ID},
        label="Observation",
        code="observation_binding_mismatch",
    )
    _exact(
        value.get("privacy"),
        {
            "raw_feature_id_disclosed": False,
            "raw_attributes_disclosed": False,
            "raw_geometry_disclosed": False,
            "source_redistributed": False,
        },
        label="Privacy",
        code="privacy_escalation",
    )
    _exact(
        value.get("permissions"),
        {
            "source_mutation_allowed": False,
            "geometry_repair_allowed": False,
            "z_dimension_drop_authorized": False,
            "execution_authorized": False,
            "runtime_wiring_authorized": False,
            "redistribution_authorized": False,
        },
        label="Permissions",
        code="permission_escalation",
    )
    return value


def _building_recipe(record_set: Mapping[str, Any]) -> dict[str, Any]:
    recipes = record_set.get("recipes")
    if not isinstance(recipes, list):
        _fail("The portrayal recipe list is missing.", "evidence_invalid")
    matches = [
        item
        for item in recipes
        if isinstance(item, dict) and item.get("feature_code") == "9310100"
    ]
    if len(matches) != 1:
        _fail("Exactly one BUILD portrayal recipe is required.", "evidence_mismatch")
    return matches[0]


def validate_portrayal_evidence(record_set: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the reviewed-but-non-executable portrayal source and open gates."""

    if not isinstance(record_set, Mapping):
        _fail("The portrayal record set must be an object.", "evidence_invalid")
    value = deepcopy(dict(record_set))
    if canonical_sha256(value) != EXPECTED_RECORD_SET_SHA256:
        _fail("The portrayal record set changed.", "evidence_hash_mismatch")
    _exact(
        value.get("record_set_id"),
        EXPECTED_RECORD_SET_ID,
        label="Record set",
        code="evidence_mismatch",
    )
    _exact(
        value.get("status"),
        "manual-vector-transcription-review-candidates; human-signoff-pending; non-executable",
        label="Record-set status",
        code="evidence_mismatch",
    )
    source = value.get("source")
    if not isinstance(source, dict):
        _fail("The source-document evidence is missing.", "evidence_mismatch")
    _exact(
        source.get("sha256"),
        EXPECTED_SOURCE_DOCUMENT_SHA256,
        label="Source document",
        code="evidence_mismatch",
    )
    recipe = _building_recipe(value)
    if canonical_sha256(recipe) != EXPECTED_RECIPE_SHA256:
        _fail("The BUILD portrayal recipe changed.", "recipe_hash_mismatch")
    exact_recipe = {
        "feature_name": "永久性建物(建築區)",
        "page": 8,
        "source_rule_id": EXPECTED_SOURCE_RULE_ID,
        "evidence_section_id": EXPECTED_EVIDENCE_SECTION_ID,
        "geometry_role": "Polygon",
        "representation_kind": "feature-following-hatched-polygon",
        "activation_status": "non-executable-review-candidate",
    }
    for field, expected in exact_recipe.items():
        _exact(
            recipe.get(field), expected, label=f"Recipe {field}", code="recipe_mismatch"
        )
    primitive_ids = [
        item.get("id") for item in recipe.get("primitives", []) if isinstance(item, dict)
    ]
    _exact(
        primitive_ids,
        [
            "surveyed-building-boundary",
            "building-diagonal-hatch",
            "floor-and-structure-annotation",
        ],
        label="Recipe primitives",
        code="recipe_mismatch",
    )
    gate_ids = [
        item.get("id")
        for item in recipe.get("activation_gates", [])
        if isinstance(item, dict)
    ]
    statuses = [
        item.get("status")
        for item in recipe.get("activation_gates", [])
        if isinstance(item, dict)
    ]
    _exact(gate_ids, list(SOURCE_GATE_IDS), label="Activation gates", code="gate_mismatch")
    if statuses != ["pending-human-review"] * len(SOURCE_GATE_IDS):
        _fail("A source activation gate is not pending human review.", "gate_mismatch")
    return value


def decision_sha256(decision: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(decision))
    basis.pop("decision_sha256", None)
    return canonical_sha256(basis)


def proposal_sha256(proposal: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(proposal))
    basis.pop("proposal_sha256", None)
    return canonical_sha256(basis)


def _bindings() -> dict[str, Any]:
    return {
        "upstream_package_sha256": EXPECTED_UPSTREAM_PACKAGE_SHA256,
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "fixture_id": EXPECTED_FIXTURE_ID,
        "observation_id": EXPECTED_OBSERVATION_ID,
        "feature_reference": EXPECTED_FEATURE_REFERENCE,
        "attribute_commitment_sha256": EXPECTED_ATTRIBUTE_COMMITMENT,
        "geometry_commitment_sha256": EXPECTED_GEOMETRY_COMMITMENT,
        "profile_identity_sha256": EXPECTED_PROFILE_IDENTITY,
        "source_scope_sha256": EXPECTED_SOURCE_SCOPE,
        "portrayal_record_set_id": EXPECTED_RECORD_SET_ID,
        "portrayal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
        "portrayal_recipe_sha256": EXPECTED_RECIPE_SHA256,
        "source_document_sha256": EXPECTED_SOURCE_DOCUMENT_SHA256,
        "source_rule_id": EXPECTED_SOURCE_RULE_ID,
        "evidence_section_id": EXPECTED_EVIDENCE_SECTION_ID,
    }


def _review_gates() -> dict[str, Any]:
    return {
        "required_gate_ids": list(BUILD_GATE_IDS),
        "status": "pending-human-review",
        "all_gates_resolved": False,
    }


def _decision_template() -> dict[str, Any]:
    return {
        "decision_version": DECISION_VERSION,
        "schema_version": DECISION_SCHEMA,
        "bindings": _bindings(),
        "decision": {
            "action": ACTION,
            "execution_target": DERIVED_TARGET,
            "feature_code": "9310100",
            "feature_name": "永久性建物(建築區)",
            "requested_portrayal": deepcopy(EXPECTED_PORTRAYAL),
            "review_gates": _review_gates(),
        },
        "boundaries": deepcopy(EXPECTED_BOUNDARIES),
    }


def _proposal_template(decision_hash: str) -> dict[str, Any]:
    return {
        "proposal_version": PROPOSAL_VERSION,
        "schema_version": PROPOSAL_SCHEMA,
        "bindings": {**_bindings(), "decision_sha256": decision_hash},
        "proposal": {
            "action": ACTION,
            "execution_target": DERIVED_TARGET,
            "requested_changes": deepcopy(EXPECTED_PORTRAYAL),
            "review_gates": _review_gates(),
        },
        "boundaries": deepcopy(EXPECTED_BOUNDARIES),
    }


def _validate_closed_artifact(
    artifact: Mapping[str, Any], expected: Mapping[str, Any], *, hash_field: str, kind: str
) -> None:
    if not isinstance(artifact, Mapping):
        _fail(f"The BUILD-02 {kind} must be an object.", f"{kind}_invalid")
    if set(artifact) != set(expected):
        _fail(f"The BUILD-02 {kind} fields are not closed.", f"{kind}_schema_invalid")
    expected_without_hash = deepcopy(dict(expected))
    expected_hash = expected_without_hash.pop(hash_field)
    for field, value in expected_without_hash.items():
        _exact(
            artifact.get(field), value, label=f"{kind} field {field}", code=f"{kind}_invalid"
        )
    computed = decision_sha256(artifact) if kind == "decision" else proposal_sha256(artifact)
    if artifact.get(hash_field) != expected_hash or computed != expected_hash:
        _fail(f"The BUILD-02 {kind} hash is invalid.", f"{kind}_hash_mismatch")


def validate_decision(decision: Mapping[str, Any]) -> None:
    expected = _decision_template()
    expected["decision_sha256"] = decision_sha256(expected)
    _validate_closed_artifact(
        decision, expected, hash_field="decision_sha256", kind="decision"
    )


def validate_proposal(proposal: Mapping[str, Any], decision: Mapping[str, Any]) -> None:
    validate_decision(decision)
    expected = _proposal_template(decision["decision_sha256"])
    expected["proposal_sha256"] = proposal_sha256(expected)
    _validate_closed_artifact(
        proposal, expected, hash_field="proposal_sha256", kind="proposal"
    )


def prepare_build_portrayal(
    upstream_package: Mapping[str, Any],
    *,
    portrayal_record_set: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create deterministic BUILD-02 review artifacts without executing anything."""

    validate_upstream_package(upstream_package)
    evidence = (
        deepcopy(dict(portrayal_record_set))
        if portrayal_record_set is not None
        else _load_object(DEFAULT_PORTRAYAL_RECORD_SET_PATH, label="evidence")
    )
    validate_portrayal_evidence(evidence)
    decision = _decision_template()
    decision["decision_sha256"] = decision_sha256(decision)
    proposal = _proposal_template(decision["decision_sha256"])
    proposal["proposal_sha256"] = proposal_sha256(proposal)
    validate_decision(decision)
    validate_proposal(proposal, decision)
    return decision, proposal


__all__ = [
    "ACTION",
    "BUILD_GATE_IDS",
    "BuildPortrayalDecisionError",
    "DECISION_SCHEMA",
    "DERIVED_TARGET",
    "EXPECTED_BOUNDARIES",
    "EXPECTED_PORTRAYAL",
    "PROPOSAL_SCHEMA",
    "decision_sha256",
    "prepare_build_portrayal",
    "proposal_sha256",
    "validate_decision",
    "validate_portrayal_evidence",
    "validate_proposal",
    "validate_upstream_package",
]

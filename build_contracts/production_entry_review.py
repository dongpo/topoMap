"""BUILD-08 official-semantics and production-entry review.

The review binds the accepted BUILD-07 DEMO evaluation to the repository's
existing real-layer and MapLibre preview paths.  It records why DEMO acceptance
does not authorize an official portrayal or production runtime.  It never reads
the private source, executes a layer, changes a runtime, or infers human approval.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from build_contracts.demo_evaluation import validate_demo_evaluation_record
from nma.core import canonical_sha256


REVIEW_SCHEMA = "nma.build-official-production-entry-review/1.0"
REVIEW_VERSION = "build-08/1.0"
EXPECTED_BUILD07_COMMIT = "153037a165683e0a2b39d36620c688955ca935fd"
EXPECTED_BUILD07_RECORD_FILE_SHA256 = (
    "7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d"
)
EXPECTED_BUILD07_RECORD_SHA256 = (
    "ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c"
)
EXPECTED_BUILD07_TEMPLATE_SHA256 = (
    "0fea2e7fe6b8ec9dd10816ba5679b04773ecd3f0761ca7b58e339f7df91139e6"
)
EXPECTED_BUILD06_FREEZE_SHA256 = (
    "bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857"
)
EXPECTED_BUILD03A_RESOLUTION_SHA256 = (
    "a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01"
)

RUNTIME_EVIDENCE = {
    "real_layer": {
        "path": "src/nma/real_layer.py",
        "file_sha256": "d9eb720b5f84c35b63df8c9cd828a7530497d4b71f502117bdf7470148d890e9",
        "profile_id": "building-polygon",
        "configured_source_layers": ["J17_BUILD"],
        "build07_selected_layer": "J13_BUILD",
        "label_field": None,
        "build07_annotation_fields": ["BUILD_NO", "BUILD_STR"],
        "planned_operations": [
            "extract-reviewed-components",
            "filter",
            "reproject-to-epsg-4326",
            "drop-z",
        ],
        "build07_source_z_dimension_drop_allowed": False,
        "status": "incompatible-with-build07-production-entry",
    },
    "portrayal_compile": {
        "path": "src/nma/portrayal_compile.py",
        "file_sha256": "3b2183bc14143bdb34ebce5d7869bdb421d0aa5527feaf129e63c509a842d4db",
        "output_status": "compiled-for-review",
        "official_rule_activation": "blocked-until-all-activation-gates-resolved",
        "preview_only": True,
    },
    "maplibre_adapter": {
        "path": "src/nma/maplibre_adapter.py",
        "file_sha256": "9fdf76fec8d1e4786e4ba7f24572b7f41336f13d628af9c089af697c04cf2f3a",
        "output_status": "adapter-ready-for-preview",
        "preview_only": True,
        "map_mutation_performed": False,
        "automatic_action": False,
    },
    "reviewed_portrayal_recipe": {
        "path": "data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json",
        "file_sha256": "9ba4f3c5e9dd2acec78ab56bf9fce270efac9b8343937459a6f4b3f16830a512",
        "feature_code": "9310100",
        "activation_status": "non-executable-review-candidate",
        "runtime_binding_status": "read-only-inspected; explicit runtime binding pending",
        "review_asset_path": (
            "assets/symbols/nlsc112v5.4/review-candidates/building-hatch-tile-v1.svg"
        ),
        "review_asset_present": False,
    },
}

GATE_REVIEWS = [
    {
        "gate_id": "hatch-angle-transcription",
        "build07_demo_verdict": "accept-current-demo",
        "official_evidence_status": "numeric-angle-not-specified-by-reviewed-source",
        "runtime_readiness_status": "hatch-asset-absent-and-preview-only",
        "disposition": "hold-official-and-production",
        "blockers": [
            "official-numeric-angle-or-organizational-convention-not-approved",
            "reviewed-hatch-asset-missing",
            "render-path-preview-only",
        ],
        "required_next_evidence": (
            "authoritative numeric-angle policy or explicit production convention, plus a "
            "reviewed deployable hatch asset"
        ),
        "human_decision_required": True,
    },
    {
        "gate_id": "building-annotation-placement",
        "build07_demo_verdict": "accept-current-demo",
        "official_evidence_status": "placement-and-collision-policy-not-specified",
        "runtime_readiness_status": "polygon-label-binding-not-implemented",
        "disposition": "hold-official-and-production",
        "blockers": [
            "official-placement-and-collision-policy-not-approved",
            "building-runtime-label-field-is-null",
            "build-no-plus-build-str-composition-not-wired",
        ],
        "required_next_evidence": (
            "approved production placement/collision policy and an explicit BUILD_NO plus "
            "BUILD_STR annotation binding"
        ),
        "human_decision_required": True,
    },
    {
        "gate_id": "real-build-schema-binding",
        "build07_demo_verdict": "accept-current-demo",
        "official_evidence_status": "j13-observation-is-not-global-schema-equivalence",
        "runtime_readiness_status": "runtime-profile-binds-j17-not-build07-j13",
        "disposition": "hold-official-and-production",
        "blockers": [
            "build07-layer-and-runtime-layer-mismatch",
            "authoritative-versioned-field-contract-not-approved",
            "id-source-global-equivalence-not-established",
        ],
        "required_next_evidence": (
            "versioned authoritative layer/field contract selecting J13 or J17 without "
            "asserting unsupported global equivalence"
        ),
        "human_decision_required": True,
    },
    {
        "gate_id": "line-and-color-profile",
        "build07_demo_verdict": "accept-current-demo",
        "official_evidence_status": "device-independent-code-mapping-not-approved",
        "runtime_readiness_status": "preview-defaults-are-not-production-profile",
        "disposition": "hold-official-and-production",
        "blockers": [
            "line-code-2-production-width-not-approved",
            "color-code-7-production-value-not-approved",
            "preview-derived-values-not-official-definitions",
        ],
        "required_next_evidence": (
            "approved output-profile mapping for line code 2 and colour code 7 across "
            "target production media"
        ),
        "human_decision_required": True,
    },
    {
        "gate_id": "j13-polygonz-runtime-policy",
        "build07_demo_verdict": "accept-current-demo",
        "official_evidence_status": "source-polygonz-must-remain-authoritative",
        "runtime_readiness_status": "existing-real-layer-plan-explicitly-drops-z",
        "disposition": "hold-official-and-production",
        "blockers": [
            "runtime-drop-z-conflicts-with-build07-boundary",
            "authoritative-z-preservation-contract-not-implemented",
            "derived-xy-provenance-and-storage-policy-not-approved",
        ],
        "required_next_evidence": (
            "approved Z-preserving production contract with an explicitly derived, "
            "non-writing XY display boundary"
        ),
        "human_decision_required": True,
    },
]

ENTRY_DECISION = {
    "existing_frozen_demo": "go",
    "read_only_official_evidence_collection": "conditional-go-explicit-scope-required",
    "official_portrayal_promotion": "hold",
    "production_runtime_entry": "hold",
    "source_execution_or_mutation": "hold",
    "unresolved_official_gate_count": 5,
    "production_ready_gate_count": 0,
    "human_decision_required": True,
    "recommended_next_gate": "build-08a-human-official-production-scope-resolution",
}

BOUNDARIES = {
    "review_only": True,
    "private_source_accessed": False,
    "human_decision_inferred": False,
    "official_semantics_decided": False,
    "official_portrayal_activation_allowed": False,
    "production_runtime_wiring_allowed": False,
    "production_activation_allowed": False,
    "source_access_allowed": False,
    "source_execution_allowed": False,
    "source_mutation_allowed": False,
    "source_z_dimension_drop_allowed": False,
    "demo_changed": False,
}


class BuildProductionEntryReviewError(ValueError):
    """BUILD-08 rejected changed evidence, a changed result, or authority expansion."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildProductionEntryReviewError(message, code=code)


def _review_basis() -> dict[str, Any]:
    return {
        "review_version": REVIEW_VERSION,
        "schema_version": REVIEW_SCHEMA,
        "status": "production-entry-held-human-scope-decision-required",
        "reviewed_on": "2026-08-21",
        "predecessor": {
            "build07_branch": "build/build-07-demo-user-evaluation",
            "build07_completion_commit": EXPECTED_BUILD07_COMMIT,
            "build07_record_file_sha256": EXPECTED_BUILD07_RECORD_FILE_SHA256,
            "build07_record_sha256": EXPECTED_BUILD07_RECORD_SHA256,
            "build07_template_sha256": EXPECTED_BUILD07_TEMPLATE_SHA256,
            "build06_freeze_sha256": EXPECTED_BUILD06_FREEZE_SHA256,
            "build03a_resolution_sha256": EXPECTED_BUILD03A_RESOLUTION_SHA256,
        },
        "scope": {
            "target": "official-semantics-and-production-entry-readiness",
            "method": "tracked-evidence-and-runtime-path-read-only-review",
            "build07_demo_acceptance_is_official_evidence": False,
            "build07_demo_acceptance_is_production_authorization": False,
            "runtime_or_source_change_performed": False,
        },
        "runtime_evidence": deepcopy(RUNTIME_EVIDENCE),
        "gate_reviews": deepcopy(GATE_REVIEWS),
        "entry_decision": deepcopy(ENTRY_DECISION),
        "boundaries": deepcopy(BOUNDARIES),
    }


def production_entry_review_sha256(review: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(review))
    basis.pop("review_sha256", None)
    return canonical_sha256(basis)


def _validate_predecessor(
    evaluation_template: Mapping[str, Any], evaluation_record: Mapping[str, Any]
) -> None:
    validated = validate_demo_evaluation_record(evaluation_record, evaluation_template)
    if validated.get("status") != "accepted-demo-only":
        _fail("BUILD-08 requires the accepted BUILD-07 DEMO record.", "record_status_mismatch")
    if validated.get("record_sha256") != EXPECTED_BUILD07_RECORD_SHA256:
        _fail("The BUILD-07 record identity changed.", "record_hash_mismatch")
    if validated.get("template_sha256") != EXPECTED_BUILD07_TEMPLATE_SHA256:
        _fail("The BUILD-07 template identity changed.", "template_hash_mismatch")


def build_official_production_entry_review(
    evaluation_template: Mapping[str, Any], evaluation_record: Mapping[str, Any]
) -> dict[str, Any]:
    """Build the exact review-only BUILD-08 HOLD decision."""

    _validate_predecessor(evaluation_template, evaluation_record)
    review = _review_basis()
    review["review_sha256"] = production_entry_review_sha256(review)
    return validate_official_production_entry_review(
        review, evaluation_template, evaluation_record
    )


def validate_official_production_entry_review(
    review: Mapping[str, Any],
    evaluation_template: Mapping[str, Any],
    evaluation_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the exact BUILD-08 evidence, HOLD result, and no-authority boundary."""

    _validate_predecessor(evaluation_template, evaluation_record)
    if not isinstance(review, Mapping):
        _fail("The BUILD-08 review must be an object.", "review_invalid")
    expected = _review_basis()
    expected["review_sha256"] = production_entry_review_sha256(expected)
    actual = deepcopy(dict(review))
    if set(actual) != set(expected):
        _fail("The BUILD-08 review fields are not closed.", "review_fields_invalid")
    if actual != expected:
        _fail("The BUILD-08 review differs from the frozen evidence decision.", "review_mismatch")
    if actual.get("review_sha256") != production_entry_review_sha256(actual):
        _fail("The BUILD-08 review identity is invalid.", "review_hash_mismatch")
    return actual


__all__ = [
    "BOUNDARIES",
    "BuildProductionEntryReviewError",
    "ENTRY_DECISION",
    "GATE_REVIEWS",
    "RUNTIME_EVIDENCE",
    "build_official_production_entry_review",
    "production_entry_review_sha256",
    "validate_official_production_entry_review",
]

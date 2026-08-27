"""BUILD-08A human-approved official/production resolution scope.

This contract authorizes only bounded evidence collection and architecture design.
It cannot activate portrayal or production, access private source data, mutate source
data, select J13/J17, or remove source Z dimensions.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from build_contracts.production_entry_review import (
    validate_official_production_entry_review,
)
from nma.core import canonical_sha256


AUTHORIZATION_SCHEMA = "nma.build-human-official-production-scope-authorization/1.0"
AUTHORIZATION_VERSION = "build-08a/1.0"
EXPECTED_BUILD08_COMMIT = "666a12adf4a1b369168480e13b2b65107429d935"
EXPECTED_BUILD08_REVIEW_SHA256 = "b48337a6bb8cf1e6cffc54e0bbfe14383f62c1dcfdca54bf706c0ab045b42484"
EXPECTED_BUILD08_REVIEW_FILE_SHA256 = (
    "be9ee241d358ba4c426ed7756345b899dffaa2e010f5f66abbe4b24ad7355b1b"
)
EXPECTED_BUILD08_REPORT_FILE_SHA256 = (
    "c4099b6cead5ddbca97edf4285d2496d129745fb4b6ca6709ccbdaa46b52d38f"
)

EVIDENCE_AUTHORITY_CLASSES = [
    "authoritative-official",
    "authoritative-schema",
    "documented-source-semantics",
    "reviewed-project-evidence",
    "implementation-evidence",
    "demo-evidence",
    "human-demo-evaluation",
    "local-policy-candidate",
    "unknown",
]

CAPABILITY_AUTHORITY = [
    {"capability_id": "continue-frozen-demo", "authority": "allowed"},
    {"capability_id": "read-tracked-evidence", "authority": "allowed"},
    {
        "capability_id": "collect-authoritative-official-evidence",
        "authority": "allowed",
    },
    {
        "capability_id": "inspect-explicitly-supplied-official-documentation",
        "authority": "allowed",
    },
    {"capability_id": "resolve-j13-j17-through-evidence", "authority": "allowed"},
    {
        "capability_id": "design-z-preserving-derived-xy-architecture",
        "authority": "allowed",
    },
    {"capability_id": "design-annotation-binding", "authority": "allowed"},
    {
        "capability_id": "define-candidate-portrayal-mappings",
        "authority": "allowed-with-evidence-classification",
    },
    {"capability_id": "define-local-policy-candidate", "authority": "allowed"},
    {"capability_id": "create-production-runtime", "authority": "forbidden"},
    {"capability_id": "activate-production-portrayal", "authority": "forbidden"},
    {
        "capability_id": "execute-production-building-mutation",
        "authority": "forbidden",
    },
    {
        "capability_id": "access-private-source-archive-automatically",
        "authority": "forbidden",
    },
    {"capability_id": "mutate-source-data", "authority": "forbidden"},
    {"capability_id": "drop-source-z", "authority": "forbidden"},
    {
        "capability_id": "promote-demo-acceptance-to-official-authority",
        "authority": "forbidden",
    },
    {"capability_id": "invent-missing-official-evidence", "authority": "forbidden"},
]

UNRESOLVED_GATES = [
    {
        "gate_id": "hatch-angle-transcription",
        "official_status": "unresolved",
        "production_status": "hold",
        "production_ready": False,
        "authorized_next_work": "official-portrayal-evidence-and-hatch-asset-requirements",
    },
    {
        "gate_id": "building-annotation-placement",
        "official_status": "unresolved",
        "production_status": "hold",
        "production_ready": False,
        "authorized_next_work": "annotation-semantics-placement-and-binding-design",
    },
    {
        "gate_id": "real-build-schema-binding",
        "official_status": "unresolved",
        "production_status": "hold",
        "production_ready": False,
        "authorized_next_work": "evidence-based-j13-j17-contract-resolution",
    },
    {
        "gate_id": "line-and-color-profile",
        "official_status": "unresolved",
        "production_status": "hold",
        "production_ready": False,
        "authorized_next_work": "official-or-local-policy-portrayal-evidence",
    },
    {
        "gate_id": "j13-polygonz-runtime-policy",
        "official_status": "unresolved",
        "production_status": "hold",
        "production_ready": False,
        "authorized_next_work": "z-preserving-derived-xy-architecture-design",
    },
]


class BuildOfficialProductionScopeAuthorizationError(ValueError):
    """BUILD-08A rejected changed evidence, identity, or authority expansion."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildOfficialProductionScopeAuthorizationError(message, code=code)


def _authorization_basis() -> dict[str, Any]:
    return {
        "authorization_version": AUTHORIZATION_VERSION,
        "schema_version": AUTHORIZATION_SCHEMA,
        "status": "bounded-evidence-and-design-scope-authorized-production-held",
        "authorized_on": "2026-08-21",
        "human_decision_type": "human-approved-bounded-official-evidence-and-production-contract-design-scope",
        "predecessor": {
            "build08_branch": "build/build-08-official-production-entry-review",
            "build08_completion_commit": EXPECTED_BUILD08_COMMIT,
            "build08_review_sha256": EXPECTED_BUILD08_REVIEW_SHA256,
            "build08_review_file_sha256": EXPECTED_BUILD08_REVIEW_FILE_SHA256,
            "build08_completion_report_file_sha256": EXPECTED_BUILD08_REPORT_FILE_SHA256,
            "build07_completion_commit": "153037a165683e0a2b39d36620c688955ca935fd",
            "build07_record_file_sha256": (
                "7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d"
            ),
            "build07_record_sha256": (
                "ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c"
            ),
            "build07_template_sha256": (
                "0fea2e7fe6b8ec9dd10816ba5679b04773ecd3f0761ca7b58e339f7df91139e6"
            ),
        },
        "authorized_scopes": [
            "evidence-based-j13-j17-building-contract-resolution",
            "authoritative-portrayal-evidence-collection-and-formalization",
            "local-policy-candidate-identification-when-official-rule-absent",
            "z-preserving-derived-xy-production-architecture-design",
            "building-annotation-semantic-and-runtime-binding-design",
            "reviewed-deployable-hatch-asset-requirements-planning",
        ],
        "prohibited_scopes": [
            "production-runtime-creation-or-activation",
            "official-portrayal-activation",
            "production-building-execution-or-mutation",
            "automatic-private-source-access",
            "source-data-or-geometry-mutation",
            "source-z-removal-or-destructive-drop-z",
            "demo-acceptance-promotion-to-official-authority",
            "missing-official-evidence-invention",
            "silent-j13-or-j17-selection",
            "production-hatch-asset-creation",
        ],
        "capability_authority": deepcopy(CAPABILITY_AUTHORITY),
        "unresolved_gates": deepcopy(UNRESOLVED_GATES),
        "evidence_policy": {
            "authority_classes": list(EVIDENCE_AUTHORITY_CLASSES),
            "official_semantics_independent_authority_denied": [
                "demo-evidence",
                "human-demo-evaluation",
            ],
            "official_portrayal_independent_authority_denied": ["implementation-evidence"],
            "unresolved_evidence_class": "unknown",
            "no_official_rule_fallback": "local-policy-candidate",
            "evidence_classification_required": True,
        },
        "building_layer_policy": {
            "candidate_layer_ids": ["J13_BUILD", "J17_BUILD"],
            "selected_layer_id": None,
            "selection_status": "hold-pending-authoritative-trace",
            "required_trace": [
                "authoritative-source-specification",
                "layer-identity",
                "field-definitions",
                "semantic-meaning",
                "nma-building-contract",
            ],
            "global_equivalence_assumed": False,
        },
        "portrayal_policy": {
            "official_portrayal_activation_allowed": False,
            "demo_only_choices": [
                "45-degree-hatch",
                "current-annotation-placement",
                "current-1-px-line-profile",
                "current-number-111111-color-profile",
            ],
            "human_demo_acceptance_is_official_evidence": False,
            "implementation_history_is_official_authority": False,
            "hatch_asset_creation_allowed": False,
            "missing_hatch_asset_approved": False,
        },
        "annotation_policy": {
            "design_allowed": True,
            "runtime_binding_implementation_allowed": False,
            "current_source_fields": ["BUILD_NO", "BUILD_STR"],
            "current_runtime_label_field": None,
            "binding_selected": False,
            "required_trace": [
                "source-field",
                "documented-meaning",
                "nma-semantic-concept",
                "annotation-content",
                "placement-policy",
            ],
        },
        "z_dimension_policy": {
            "architecture_design_allowed": True,
            "authoritative_source_geometry": "PolygonZ",
            "source_representation": "preserved-immutable",
            "display_representation": "derived-non-writing-xy",
            "render_target": "MapLibre",
            "source_and_display_geometry_distinct": True,
            "existing_drop_z_production_path": "not-approved",
            "source_transformation_authorized": False,
            "source_z_drop_allowed": False,
        },
        "activation_and_source_boundaries": {
            "production_activation_allowed": False,
            "production_runtime_creation_allowed": False,
            "official_portrayal_activation_allowed": False,
            "source_access_allowed": False,
            "source_execution_allowed": False,
            "source_mutation_allowed": False,
            "source_z_drop_allowed": False,
            "private_source_access_allowed": False,
            "unauthorized_execution_allowed": False,
            "demo_to_official_promotion_allowed": False,
        },
        "next_stage_boundary": {
            "recommended_stage": "BUILD-09",
            "stage_name": "Official Building Semantics & Production Contract Resolution",
            "evidence_and_design_first": True,
            "production_execution_requires_later_separate_authorization": True,
            "source_mutation_requires_later_separate_authorization": True,
            "build09_started": False,
        },
    }


def official_production_scope_authorization_sha256(
    authorization: Mapping[str, Any],
) -> str:
    basis = deepcopy(dict(authorization))
    basis.pop("authorization_sha256", None)
    return canonical_sha256(basis)


def _validate_predecessor(
    build08_review: Mapping[str, Any],
    evaluation_template: Mapping[str, Any],
    evaluation_record: Mapping[str, Any],
) -> None:
    validated = validate_official_production_entry_review(
        build08_review, evaluation_template, evaluation_record
    )
    if validated.get("review_sha256") != EXPECTED_BUILD08_REVIEW_SHA256:
        _fail("The BUILD-08 review identity changed.", "build08_review_hash_mismatch")


def build_official_production_scope_authorization(
    build08_review: Mapping[str, Any],
    evaluation_template: Mapping[str, Any],
    evaluation_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Create the exact human-approved BUILD-08A bounded authorization."""

    _validate_predecessor(build08_review, evaluation_template, evaluation_record)
    authorization = _authorization_basis()
    authorization["authorization_sha256"] = official_production_scope_authorization_sha256(
        authorization
    )
    return validate_official_production_scope_authorization(
        authorization, build08_review, evaluation_template, evaluation_record
    )


def validate_official_production_scope_authorization(
    authorization: Mapping[str, Any],
    build08_review: Mapping[str, Any],
    evaluation_template: Mapping[str, Any],
    evaluation_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the exact BUILD-08A scope and every fail-closed boundary."""

    _validate_predecessor(build08_review, evaluation_template, evaluation_record)
    if not isinstance(authorization, Mapping):
        _fail("The BUILD-08A authorization must be an object.", "authorization_invalid")
    expected = _authorization_basis()
    expected["authorization_sha256"] = official_production_scope_authorization_sha256(expected)
    actual = deepcopy(dict(authorization))
    if set(actual) != set(expected):
        _fail(
            "The BUILD-08A authorization fields are not closed.",
            "authorization_fields_invalid",
        )
    if actual != expected:
        _fail(
            "The BUILD-08A authorization differs from the human-approved scope.",
            "authorization_mismatch",
        )
    if actual.get("authorization_sha256") != (
        official_production_scope_authorization_sha256(actual)
    ):
        _fail("The BUILD-08A authorization identity is invalid.", "authorization_hash_mismatch")
    return actual


__all__ = [
    "AUTHORIZATION_SCHEMA",
    "AUTHORIZATION_VERSION",
    "CAPABILITY_AUTHORITY",
    "EVIDENCE_AUTHORITY_CLASSES",
    "EXPECTED_BUILD08_COMMIT",
    "EXPECTED_BUILD08_REVIEW_SHA256",
    "UNRESOLVED_GATES",
    "BuildOfficialProductionScopeAuthorizationError",
    "build_official_production_scope_authorization",
    "official_production_scope_authorization_sha256",
    "validate_official_production_scope_authorization",
]

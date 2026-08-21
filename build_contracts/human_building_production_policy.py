"""BUILD-09F human Building production-policy authorization.

This module records policy and finalizes a design contract.  It deliberately
contains no production rendering, package I/O, layer routing, or geometry code.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from nma.core import canonical_sha256


POLICY_SCHEMA = "nma.building-human-production-policy-authorization/1.0"
POLICY_VERSION = "build-09f/1.0"
CONTRACT_SCHEMA = "nma.building-finalized-production-contract/1.0"
CONTRACT_VERSION = "build-09f-successor/1.0"

EXPECTED_BUILD09E2_BRANCH = "build/build-09e2-j13-j17-production-applicability-resolution"
EXPECTED_BUILD09E2_COMMIT = "d92fd15bd6b7e40714abf25a8e7857d205fcca10"
EXPECTED_BUILD09_CONTRACT_SHA256 = (
    "0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c"
)
EXPECTED_BUILD09E_CLOSURE_SHA256 = (
    "bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed"
)
EXPECTED_BUILD09E1_RESOLUTION_SHA256 = (
    "f75c44bcb834090277588b3c23cfe48f00e965c947754497f64831d4b47b9b65"
)
EXPECTED_BUILD09E2_RESOLUTION_SHA256 = (
    "1a4a406da130eb34a7f6871e92230d0c82fe4bcf9e475651418780bedd5d1262"
)
EXPECTED_BUILD09E2_SUCCESSOR_SHA256 = (
    "71b7f25239eb001454af61358acb67917d9820957ea4aeb2191ff613ee54a043"
)
EXPECTED_BUILD08A_AUTHORIZATION_SHA256 = (
    "4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8"
)

POLICY_TYPES = ["local-nma-production-policy"]
BINDING_CLASSES = ["local-version-package-scoped-production-binding"]
ANGLE_AUTHORITIES = ["local-production-policy"]
HATCH_RESOURCE_POLICIES = ["procedural-canonical"]
ANNOTATION_PLACEMENT_AUTHORITIES = ["local-production-policy"]
COLOUR_SERIALIZATION_AUTHORITIES = ["derived-device-serialization"]
OPACITY_AUTHORITIES = ["local-output-profile-policy"]
GATE_STATES = ["P2-production-candidate"]
READINESS_STATES = ["READY-FOR-BUILD-10", "HOLD"]
VERDICTS = [
    "PASS — HUMAN BUILDING PRODUCTION POLICY RESOLVED; BUILD-10 READY",
    "PASS — HUMAN PRODUCTION POLICY PARTIAL; BUILD-10 REMAINS HOLD",
    "FAIL — HUMAN BUILDING PRODUCTION POLICY BOUNDARY NOT ESTABLISHED",
]

BUILD09E2_ARTIFACT_SHA256 = {
    "BUILD-09E2-Completion-Report.md": (
        "2c39c05fc30a37edf4ff1cba9586e0bb24f43e7a8a54afcd173472034be5255a"
    ),
    "build_contracts/j13_j17_production_applicability.py": (
        "0e1b9dbfbeb0f2700fbc2ad591429dabda135c8f01ddb80dea99c1cbda21898b"
    ),
    "data/specifications/nma-build-09e2-golden-j13-j17-production-applicability-resolution-v1.0.json": (
        "289d7632fab478518a7a1a0401d0f804291db22c2ff80c64d25e20fb5a9bd01f"
    ),
    "data/specifications/nma-build-09e2-successor-building-production-contract-v1.0.json": (
        "e30ca42930ba44be450155214cd76f2c256a8b560b1fbe22b9d98e23e857fc7f"
    ),
    "schemas/building-human-policy-production-contract-v1.0.schema.json": (
        "055aa74021987520500bde4e604803ced464b7ccba2b046b9d50e6954948da25"
    ),
    "schemas/building-j13-j17-production-applicability-resolution-v1.0.schema.json": (
        "993d57d89417a7fdd7e7653d76bbc2f528f7bb2e598b5c539d51dfd9ec0549f2"
    ),
    "tests/test_j13_j17_production_applicability_build09e2.py": (
        "15ba280555f39f7bd19bf3674d4993f7c8eb9c137f49955315fec12b5c02dcd1"
    ),
}


class HumanBuildingProductionPolicyError(ValueError):
    """BUILD-09F rejected an identity, policy, or safety boundary."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise HumanBuildingProductionPolicyError(message, code=code)


def _identity(value: Mapping[str, Any], key: str) -> str:
    basis = deepcopy(dict(value))
    basis.pop(key, None)
    return canonical_sha256(basis)


def policy_record_sha256(record: Mapping[str, Any]) -> str:
    return _identity(record, "policy_record_sha256")


def finalized_contract_sha256(contract: Mapping[str, Any]) -> str:
    return _identity(contract, "finalized_contract_sha256")


def _validate_predecessors(
    resolution: Mapping[str, Any], successor: Mapping[str, Any], build09: Mapping[str, Any]
) -> None:
    checks = (
        (
            resolution,
            "applicability_resolution_sha256",
            EXPECTED_BUILD09E2_RESOLUTION_SHA256,
            "build09e2_resolution_identity_mismatch",
        ),
        (
            successor,
            "successor_contract_sha256",
            EXPECTED_BUILD09E2_SUCCESSOR_SHA256,
            "build09e2_successor_identity_mismatch",
        ),
        (
            build09,
            "contract_sha256",
            EXPECTED_BUILD09_CONTRACT_SHA256,
            "build09_identity_mismatch",
        ),
    )
    for value, key, expected, code in checks:
        if value.get(key) != expected or _identity(value, key) != expected:
            _fail("A frozen predecessor identity does not match.", code)

    outcome = resolution.get("authoritative_applicability_resolution", {})
    required_outcome = {
        "outcome": "authoritative-applicability-boundary-not-published",
        "official_evidence_search_closed": True,
        "human_production_binding_policy_required": True,
        "additional_authoritative_evidence_acquisition_justified": False,
    }
    if any(outcome.get(key) != value for key, value in required_outcome.items()):
        _fail("BUILD-09E2 official evidence closure regressed.", "official_evidence_regression")
    if resolution.get("build09f_readiness") != "READY-FOR-BUILD-09F":
        _fail("BUILD-09E2 did not authorize BUILD-09F.", "predecessor_not_ready")
    if successor.get("production_activation_forbidden") is not True:
        _fail("The predecessor production prohibition is absent.", "activation_enabled")
    if successor.get("official_portrayal_activation_forbidden") is not True:
        _fail("The predecessor portrayal prohibition is absent.", "activation_enabled")
    mutation = successor.get("source_mutation_policy", {})
    if mutation.get("source_mutation_allowed") is not False:
        _fail("The predecessor source-mutation prohibition is absent.", "source_mutation_enabled")
    if mutation.get("source_z_dimension_removal_allowed") is not False:
        _fail("The predecessor Z-removal prohibition is absent.", "source_z_drop_enabled")


def _policy_basis(
    resolution: Mapping[str, Any], successor: Mapping[str, Any], build09: Mapping[str, Any]
) -> dict[str, Any]:
    frozen = resolution["frozen_non_j13_j17_findings"]
    width_mm = frozen["line_code_2_resolution"]["physical_width"]["value"]
    dpi = 96
    return {
        "schema_version": POLICY_SCHEMA,
        "contract_version": POLICY_VERSION,
        "status": "human-production-policy-resolved",
        "created_on": "2026-08-21",
        "predecessor": {
            "build09e2_branch": EXPECTED_BUILD09E2_BRANCH,
            "build09e2_commit": EXPECTED_BUILD09E2_COMMIT,
            "build09_contract_sha256": EXPECTED_BUILD09_CONTRACT_SHA256,
            "build09e_evidence_closure_sha256": EXPECTED_BUILD09E_CLOSURE_SHA256,
            "build09e1_evidence_resolution_sha256": EXPECTED_BUILD09E1_RESOLUTION_SHA256,
            "build09e2_applicability_resolution_sha256": EXPECTED_BUILD09E2_RESOLUTION_SHA256,
            "build09e2_successor_contract_sha256": EXPECTED_BUILD09E2_SUCCESSOR_SHA256,
            "build08a_authorization_sha256": EXPECTED_BUILD08A_AUTHORIZATION_SHA256,
            "frozen_build09e2_artifact_sha256": deepcopy(BUILD09E2_ARTIFACT_SHA256),
        },
        "human_policy_decision_type": "local-nma-production-policy",
        "official_evidence_closure": {
            "authoritative_applicability_result": (
                "authoritative-applicability-boundary-not-published"
            ),
            "official_evidence_search_closed": True,
            "additional_evidence_acquisition_justified": False,
            "official_portrayal_semantics_closed": True,
            "remaining_authoritative_evidence_blockers": [],
        },
        "j13_j17_binding_policy": {
            "classification": "local-version-package-scoped-production-binding",
            "global_permanent_layer_selected": False,
            "global_equivalence_asserted": False,
            "package_identity_required": True,
            "binding_scope": "exact-explicitly-selected-and-verified-source-package",
            "bindings": [
                {
                    "package_prefix": "J13",
                    "package_scope": "J13_寶山都市計畫/SHP",
                    "layer_identity": "J13_BUILD",
                    "schema_identity_required": True,
                },
                {
                    "package_prefix": "J17",
                    "package_scope": "J17_新竹科學工業園區特定區計畫(寶山部分)/SHP",
                    "layer_identity": "J17_BUILD",
                    "schema_identity_required": True,
                },
            ],
            "provenance_binding_required": [
                "source-package-identity",
                "package-scope",
                "exact-layer-identity",
                "schema-identity",
            ],
            "automatic_cross_prefix_substitution_allowed": False,
            "package_layer_mismatch_behavior": "fail-closed",
            "unsupported_package_prefix_behavior": "fail-closed",
        },
        "hatch_policy": {
            "official_diagonal_semantics": True,
            "official_spacing_mm": 2.0,
            "spacing_scale_boundary": "physical-at-defined-cartographic-output-profile-scale",
            "local_angle_degrees": 45,
            "angle_authority": "local-production-policy",
            "hatch_resource_policy": "procedural-canonical",
            "line_colour_semantics": (
                "official-black-unless-another-officially-supported-mapping-applies"
            ),
            "deterministic_procedural_rendering_required": True,
            "asset_file_required": False,
            "asset_if_used_must_derive_from_canonical_specification": True,
            "missing_building_hatch_tile_dependency_blocks_architecture": False,
            "asset_created_or_deployed": False,
        },
        "annotation_policy": {
            "content_authority": "official-portrayal-semantics",
            "content_rule": "floor count followed by structure",
            "field_binding_rule": "{BUILD_NO}{BUILD_STR}",
            "annotation_placement_authority": "local-production-policy",
            "preferred_placement": "inside-polygon",
            "anchor": "deterministic-interior-or-representative-point",
            "near_feature_center_semantics_preserved": True,
            "outside_polygon_fallback_authorized": False,
            "collision_suppression_allowed": True,
            "unsafe_label_behavior": "suppress",
            "same_geometry_output_profile_is_deterministic": True,
        },
        "line_output_profile_policy": {
            "official_physical_width": {
                "unit": "mm",
                "value": width_mm,
                "value_text": "0.20",
            },
            "output_profile_authority": "local-output-profile-policy",
            "profile_id": "nma-screen-96dpi-v1",
            "output_dpi": dpi,
            "device_pixel_assumption_declared": True,
            "conversion_formula": "device_px = physical_mm * output_dpi / 25.4",
            "derived_device_width_px": width_mm * dpi / 25.4,
            "official_css_px": None,
            "official_one_css_px_rule": False,
            "renderer_quantization_authority": "local-output-profile-behavior-if-defined-later",
        },
        "colour_policy": {
            "official_semantic_name": "black",
            "official_original_representation": "RGB (0,0,0)",
            "official_rgb_components": [0, 0, 0],
            "canonical_device_representation": "rgb(0, 0, 0)",
            "optional_hex_serialization": "#000000",
            "hex_authority": "derived-device-serialization",
            "official_hex_definition": None,
            "rejected_device_representation": "#111111",
        },
        "opacity_policy": {
            "value": 1.0,
            "authority": "local-output-profile-policy",
            "applies_to": ["building-line", "building-hatch"],
            "separate_component_values_require_explicit_contract_binding": True,
        },
        "polygonz_derived_xy_policy": {
            **deepcopy(build09["polygonz_derived_xy_contract"]),
            "implementation_stage": "BUILD-10-or-later",
            "implementation_in_build09f": False,
            "controlled_path_may_bypass_replace_or_isolate_legacy_drop_z": True,
        },
        "five_gate_readiness": [
            {"gate_id": "hatch", "state": "P2-production-candidate"},
            {"gate_id": "annotation", "state": "P2-production-candidate"},
            {"gate_id": "j13-j17", "state": "P2-production-candidate"},
            {"gate_id": "line-colour", "state": "P2-production-candidate"},
            {"gate_id": "polygonz-derived-xy", "state": "P2-production-candidate"},
        ],
        "production_implementation_authorization": {
            "controlled_production_implementation_design_allowed": True,
            "controlled_production_implementation_allowed": True,
            "production_activation_allowed": False,
            "official_portrayal_activation_allowed": False,
            "source_mutation_allowed": False,
            "source_z_drop_allowed": False,
            "unbounded_runtime_wiring_allowed": False,
        },
        "scope": {
            "production_runtime_modified": False,
            "production_behavior_implemented": False,
            "j13_j17_routing_implemented": False,
            "maplibre_style_modified": False,
            "hatch_asset_created_or_deployed": False,
            "source_data_or_geometry_modified": False,
            "source_polygonz_transformed": False,
            "source_z_removed": False,
            "official_evidence_reopened": False,
        },
        "build10_readiness": "READY-FOR-BUILD-10",
        "verdict": "PASS — HUMAN BUILDING PRODUCTION POLICY RESOLVED; BUILD-10 READY",
        "next_stage_recommendation": "BUILD-10 — Controlled Building Production Implementation",
    }


def build_policy_record(
    resolution: Mapping[str, Any], successor: Mapping[str, Any], build09: Mapping[str, Any]
) -> dict[str, Any]:
    _validate_predecessors(resolution, successor, build09)
    record = _policy_basis(resolution, successor, build09)
    record["policy_record_sha256"] = policy_record_sha256(record)
    return validate_policy_record(record, resolution, successor, build09)


def validate_policy_record(
    record: Mapping[str, Any],
    resolution: Mapping[str, Any],
    successor: Mapping[str, Any],
    build09: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_predecessors(resolution, successor, build09)
    if record.get("policy_record_sha256") != policy_record_sha256(record):
        _fail("The BUILD-09F policy identity is invalid.", "policy_hash_mismatch")
    expected = _policy_basis(resolution, successor, build09)
    expected["policy_record_sha256"] = policy_record_sha256(expected)
    if dict(record) != expected:
        _fail("The BUILD-09F policy differs from the closed authorization.", "policy_mismatch")
    return deepcopy(dict(record))


def _contract_basis(
    policy: Mapping[str, Any], resolution: Mapping[str, Any], successor: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": CONTRACT_SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "status": "production-candidate",
        "created_on": "2026-08-21",
        "bindings": {
            "build09e2_predecessor_commit": EXPECTED_BUILD09E2_COMMIT,
            "build09e2_applicability_resolution_sha256": EXPECTED_BUILD09E2_RESOLUTION_SHA256,
            "build09e2_successor_contract_sha256": EXPECTED_BUILD09E2_SUCCESSOR_SHA256,
            "build09f_policy_record_sha256": policy["policy_record_sha256"],
        },
        "official_evidence_findings": {
            "applicability_result": "authoritative-applicability-boundary-not-published",
            "official_evidence_search_closed": True,
            "remaining_authoritative_evidence_blockers": [],
            "annotation_content": "floor count followed by structure",
            "hatch_diagonal_semantics": True,
            "hatch_spacing_mm": 2.0,
            "line_width_mm": 0.2,
            "colour_original_representation": "RGB (0,0,0)",
        },
        "authorized_local_policies": {
            "j13_j17": deepcopy(policy["j13_j17_binding_policy"]),
            "hatch": deepcopy(policy["hatch_policy"]),
            "annotation": deepcopy(policy["annotation_policy"]),
            "line_output_profile": deepcopy(policy["line_output_profile_policy"]),
            "colour": deepcopy(policy["colour_policy"]),
            "opacity": deepcopy(policy["opacity_policy"]),
        },
        "polygonz_derived_xy_contract": deepcopy(policy["polygonz_derived_xy_policy"]),
        "final_gates": deepcopy(policy["five_gate_readiness"]),
        "implementation_authorization": deepcopy(policy["production_implementation_authorization"]),
        "production_activation_allowed": False,
        "official_portrayal_activation_allowed": False,
        "source_mutation_allowed": False,
        "source_z_drop_allowed": False,
        "unbounded_runtime_wiring_allowed": False,
        "build10_readiness": "READY-FOR-BUILD-10",
        "next_stage": "BUILD-10 — Controlled Building Production Implementation",
    }


def build_finalized_contract(
    policy: Mapping[str, Any],
    resolution: Mapping[str, Any],
    successor: Mapping[str, Any],
    build09: Mapping[str, Any],
) -> dict[str, Any]:
    validated = validate_policy_record(policy, resolution, successor, build09)
    contract = _contract_basis(validated, resolution, successor)
    contract["finalized_contract_sha256"] = finalized_contract_sha256(contract)
    return validate_finalized_contract(contract, validated, resolution, successor, build09)


def validate_finalized_contract(
    contract: Mapping[str, Any],
    policy: Mapping[str, Any],
    resolution: Mapping[str, Any],
    successor: Mapping[str, Any],
    build09: Mapping[str, Any],
) -> dict[str, Any]:
    validated = validate_policy_record(policy, resolution, successor, build09)
    if contract.get("status") == "production-active":
        _fail("BUILD-09F cannot activate production.", "activation_enabled")
    if contract.get("finalized_contract_sha256") != finalized_contract_sha256(contract):
        _fail("The finalized contract identity is invalid.", "contract_hash_mismatch")
    expected = _contract_basis(validated, resolution, successor)
    expected["finalized_contract_sha256"] = finalized_contract_sha256(expected)
    if dict(contract) != expected:
        _fail("The successor differs from the closed production candidate.", "contract_mismatch")
    return deepcopy(dict(contract))


__all__ = [
    "ANGLE_AUTHORITIES",
    "ANNOTATION_PLACEMENT_AUTHORITIES",
    "BINDING_CLASSES",
    "BUILD09E2_ARTIFACT_SHA256",
    "COLOUR_SERIALIZATION_AUTHORITIES",
    "CONTRACT_SCHEMA",
    "CONTRACT_VERSION",
    "EXPECTED_BUILD09E2_BRANCH",
    "EXPECTED_BUILD09E2_COMMIT",
    "EXPECTED_BUILD09E2_RESOLUTION_SHA256",
    "EXPECTED_BUILD09E2_SUCCESSOR_SHA256",
    "GATE_STATES",
    "HATCH_RESOURCE_POLICIES",
    "HumanBuildingProductionPolicyError",
    "OPACITY_AUTHORITIES",
    "POLICY_SCHEMA",
    "POLICY_TYPES",
    "POLICY_VERSION",
    "READINESS_STATES",
    "VERDICTS",
    "build_finalized_contract",
    "build_policy_record",
    "finalized_contract_sha256",
    "policy_record_sha256",
    "validate_finalized_contract",
    "validate_policy_record",
]

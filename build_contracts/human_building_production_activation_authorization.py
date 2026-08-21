"""BUILD-11A human authorization for a separately executed BUILD-12 activation.

This module records and validates authorization evidence. It contains no activation, rendering,
package routing, geometry derivation, source-write, or runtime mutation operation.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from build_contracts.building_production_implementation import (
    BUILD_SCHEMA,
    building_schema_identity,
)
from build_contracts.building_production_verification import (
    activation_readiness_record_sha256,
    verify_activation_readiness_record,
)
from build_contracts.human_building_production_policy import (
    finalized_contract_sha256,
    policy_record_sha256,
)
from nma.core import canonical_sha256
from nma.real_layer import file_sha256


AUTHORIZATION_SCHEMA = "nma.building-human-production-activation-authorization/1.0"
AUTHORIZATION_VERSION = "build-11a/1.0"
AUTHORIZATION_STATE = "authorized-for-controlled-activation"
AUTHORIZATION_TYPE = "human-controlled-building-production-activation"
AUTHORIZATION_DECISION = (
    "AUTHORIZE CONTROLLED BUILDING PRODUCTION ACTIVATION IN THE NEXT SEPARATELY EXECUTED STAGE."
)
VERDICT = "PASS — HUMAN BUILDING PRODUCTION ACTIVATION AUTHORIZED; BUILD-12 READY"
BUILD11_BRANCH = "build/build-11-controlled-building-production-verification"
BUILD11_COMMIT = "fb8421d222685742f504fe8397bd03acfc94e3db"
BUILD11_READINESS_SHA256 = "d2ecb53e74f46e279a5672a182b5a9de602c08d4027023d4fb225132bf3d01fb"
BUILD11_READINESS_FILE_SHA256 = "d65c33803a2d5a5b3a78a00c5d09606100d0c253d306f6b015bf425f8d728770"
BUILD10_IMPLEMENTATION_SHA256 = "2772ce93f81973e1dbbeb2d4ae9bb1307a29dcdcc4a61ca08f382c12b6b3c957"
BUILD09F_POLICY_SHA256 = "dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1"
FINALIZED_CONTRACT_SHA256 = "5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88"
SOURCE_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
CORE_IDENTITY_PROVIDER_SHA256 = "d9c4ac0d0d385f6942c552a0b2ffc4c12b3deb0ee876d569aeadc036b1a92e78"

BUILD11_ARTIFACT_SHA256 = {
    "BUILD-11-Completion-Report.md": (
        "1b285c2f33223d30a4e5c06aa3da9c2303551d1deed86536129614c93f080949"
    ),
    "build_contracts/building_production_verification.py": (
        "9be146ba827532d8c96f0e0de4b65f716d43067d5bfc00f087c6a5deca61aa5a"
    ),
    "data/specifications/nma-build-11-golden-building-production-activation-readiness-v1.0.json": (
        "d65c33803a2d5a5b3a78a00c5d09606100d0c253d306f6b015bf425f8d728770"
    ),
    "schemas/building-production-activation-readiness-v1.0.schema.json": (
        "4d3d420abbc6a4a8a5582c7540d15ebcfad37db448b5444960c1ac9a63d273b4"
    ),
    "tests/test_building_production_verification_build11.py": (
        "35952a8384b95504919e86b84dc5fb56409483299a4bb9d6256f729d196680eb"
    ),
}

PRE_ACTIVATION_REQUIREMENTS = [
    "authorization-record-valid",
    "implementation-identity-exact",
    "production-contract-identity-exact",
    "policy-identity-exact",
    "readiness-identity-exact",
    "package-identity-supported",
    "j13-j17-binding-exact",
    "seven-field-schema-exact",
    "source-archive-identity-unchanged",
    "polygonz-source-intact",
    "derived-xy-boundary-intact",
    "provenance-chain-intact",
    "no-new-material-regression",
    "activation-target-explicitly-bounded",
]

POST_ACTIVATION_REQUIREMENTS = [
    "runtime-reports-building-production-active",
    "exact-implementation-identity-active",
    "exact-contract-identity-active",
    "exact-policy-identity-active",
    "exact-portrayal-identity-active",
    "j13-j17-binding-remains-fail-closed",
    "source-remains-unchanged",
    "polygonz-remains-intact",
    "derived-xy-remains-non-writing",
    "production-output-is-deterministic",
    "activation-provenance-and-receipt-identify-event",
    "rollback-deactivation-path-available",
]

DRIFT_INVALIDATION_FIELDS = [
    "build11-readiness-record",
    "build10-implementation",
    "build09f-policy",
    "finalized-production-contract",
    "source-package-identity",
    "building-schema",
    "output-profile",
    "portrayal-contract",
    "core-identity-provider",
    "activation-authorization-record",
]


class HumanBuildingActivationAuthorizationError(ValueError):
    """BUILD-11A rejected predecessor evidence or an authorization boundary."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise HumanBuildingActivationAuthorizationError(message, code=code)


def authorization_record_sha256(record: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(record))
    basis.pop("canonical_authorization_sha256", None)
    return canonical_sha256(basis)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"Expected an object at {path}.", "predecessor_invalid")
    return value


def _validate_predecessors(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    readiness_path = (
        root
        / "data/specifications/nma-build-11-golden-building-production-activation-readiness-v1.0.json"
    )
    policy_path = (
        root
        / "data/specifications/nma-build-09f-golden-human-building-production-policy-authorization-v1.0.json"
    )
    contract_path = (
        root / "data/specifications/nma-build-09f-finalized-building-production-contract-v1.0.json"
    )
    readiness = _load_json(readiness_path)
    policy = _load_json(policy_path)
    contract = _load_json(contract_path)

    if file_sha256(readiness_path) != BUILD11_READINESS_FILE_SHA256:
        _fail("The BUILD-11 readiness file identity drifted.", "readiness_file_identity_mismatch")
    if (
        readiness.get("canonical_record_sha256") != BUILD11_READINESS_SHA256
        or activation_readiness_record_sha256(readiness) != BUILD11_READINESS_SHA256
        or not verify_activation_readiness_record(readiness)
    ):
        _fail("The BUILD-11 readiness identity drifted.", "readiness_identity_mismatch")
    if readiness.get("activation_readiness") != "READY-FOR-HUMAN-ACTIVATION-GATE":
        _fail("BUILD-11 is not ready for human authorization.", "predecessor_not_ready")
    if readiness.get("remaining_blockers") != []:
        _fail("BUILD-11 contains an unresolved blocker.", "predecessor_blocked")

    boundary = readiness.get("activation_boundary", {})
    required_boundary = {
        "implementation_ready": True,
        "production_activation_allowed": False,
        "production_active": False,
        "official_portrayal_activation_allowed": False,
        "official_portrayal_active": False,
        "source_mutation_allowed": False,
        "source_mutated": False,
    }
    if any(boundary.get(key) is not value for key, value in required_boundary.items()):
        _fail("The BUILD-11 activation boundary drifted.", "readiness_boundary_mismatch")

    if (
        policy.get("policy_record_sha256") != BUILD09F_POLICY_SHA256
        or policy_record_sha256(policy) != BUILD09F_POLICY_SHA256
    ):
        _fail("The BUILD-09F policy identity drifted.", "policy_identity_mismatch")
    if (
        contract.get("finalized_contract_sha256") != FINALIZED_CONTRACT_SHA256
        or finalized_contract_sha256(contract) != FINALIZED_CONTRACT_SHA256
    ):
        _fail("The finalized production contract identity drifted.", "contract_identity_mismatch")

    frozen_files = {
        "build_contracts/building_production_implementation.py": BUILD10_IMPLEMENTATION_SHA256,
        "src/nma/core/identity.py": CORE_IDENTITY_PROVIDER_SHA256,
        "data/datasets/112年多維度SHP成果_0502.zip": SOURCE_ARCHIVE_SHA256,
        **BUILD11_ARTIFACT_SHA256,
    }
    for relative, expected in frozen_files.items():
        path = root / relative
        if not path.is_file() or file_sha256(path) != expected:
            _fail(f"Frozen identity drifted: {relative}.", "frozen_file_identity_mismatch")

    source = readiness.get("source_archive", {})
    if source.get("sha256") != SOURCE_ARCHIVE_SHA256 or any(
        source.get(key) is not False
        for key in (
            "source_mutated",
            "source_repair_performed",
            "source_writeback_performed",
            "source_z_removed",
        )
    ):
        _fail("The authoritative source boundary drifted.", "source_identity_mismatch")
    return readiness, policy, contract


def _profile(value: Mapping[str, Any], identity_key: str) -> dict[str, Any]:
    profile = deepcopy(dict(value))
    profile[identity_key] = canonical_sha256(profile)
    return profile


def _authorization_basis(root: Path) -> dict[str, Any]:
    readiness, policy, contract = _validate_predecessors(root)
    j13_j17 = contract["authorized_local_policies"]["j13_j17"]
    portrayal = _profile(
        {
            "contract_binding": FINALIZED_CONTRACT_SHA256,
            "annotation": deepcopy(contract["authorized_local_policies"]["annotation"]),
            "hatch": deepcopy(contract["authorized_local_policies"]["hatch"]),
            "line_width_mm": 0.2,
            "official_black_rgb": [0, 0, 0],
            "device_colour_serialization": "#000000",
            "opacity": 1.0,
            "portrayal_kind": "procedural-hatch-with-outline-and-annotation",
        },
        "portrayal_profile_sha256",
    )
    output = _profile(
        {
            "profile_id": "nma-screen-96dpi-v1",
            "output_dpi": 96,
            "hatch_spacing_mm": 2.0,
            "hatch_angle_degrees": 45,
            "hatch_angle_authority": "local-production-policy",
            "line_width_mm": 0.2,
            "line_width_device_px": 0.2 * 96 / 25.4,
            "official_black_rgb": [0, 0, 0],
            "device_colour_serialization": "#000000",
            "opacity": 1.0,
        },
        "output_profile_sha256",
    )
    return {
        "schema_version": AUTHORIZATION_SCHEMA,
        "contract_version": AUTHORIZATION_VERSION,
        "created_on": "2026-08-21",
        "authorization_type": AUTHORIZATION_TYPE,
        "authorization_decision": AUTHORIZATION_DECISION,
        "authorization_state": AUTHORIZATION_STATE,
        "verdict": VERDICT,
        "predecessor": {
            "build11_branch": BUILD11_BRANCH,
            "build11_commit": BUILD11_COMMIT,
            "build11_verdict": readiness["verdict"],
            "build11_readiness_state": readiness["activation_readiness"],
            "build11_remaining_blockers": [],
            "build11_readiness_canonical_sha256": BUILD11_READINESS_SHA256,
            "build11_readiness_file_sha256": BUILD11_READINESS_FILE_SHA256,
            "build10_implementation_identity": BUILD10_IMPLEMENTATION_SHA256,
            "build09f_policy_identity": BUILD09F_POLICY_SHA256,
            "finalized_production_contract_identity": FINALIZED_CONTRACT_SHA256,
            "source_archive_identity": SOURCE_ARCHIVE_SHA256,
            "core_identity_provider": "nma.core.canonical_sha256",
            "core_identity_provider_file_sha256": CORE_IDENTITY_PROVIDER_SHA256,
            "frozen_build11_artifact_sha256": deepcopy(BUILD11_ARTIFACT_SHA256),
        },
        "authorized_building_schema": {
            "field_count": 7,
            "schema_identity": building_schema_identity(),
            "fields": deepcopy(list(BUILD_SCHEMA)),
            "mismatch_behavior": "fail-closed",
        },
        "authorized_package_scope": {
            "classification": j13_j17["classification"],
            "j13": deepcopy(j13_j17["bindings"][0]),
            "j17": deepcopy(j13_j17["bindings"][1]),
            "package_identity_required": True,
            "exact_layer_identity_required": True,
            "exact_schema_required": True,
            "automatic_cross_prefix_substitution_allowed": False,
            "global_j13_j17_equivalence_authorized": False,
            "unknown_package_activation_allowed": False,
            "unverified_package_activation_allowed": False,
            "mismatch_behavior": "fail-closed",
        },
        "authorized_portrayal_profile": portrayal,
        "authorized_output_profile": output,
        "polygonz_derived_xy_boundary": {
            "pipeline": [
                "authoritative-PolygonZ",
                "non-writing-derived-XY",
                "portrayal-runtime",
            ],
            "authoritative_source_geometry": "PolygonZ",
            "source_z_preserved_and_recoverable": True,
            "derived_xy_authoritative": False,
            "derived_xy_non_writing": True,
            "derived_xy_purpose": "portrayal-only",
            "source_overwrite_allowed": False,
        },
        "activation_authorization": {
            "controlled_production_activation_authorized": True,
            "production_activation_allowed_for_build12": True,
            "controlled_official_portrayal_activation_authorized": True,
            "official_portrayal_activation_allowed_for_build12": True,
            "authorization_scope": "exact-bound-identities-only",
            "automatic_activation_performed": False,
            "activation_in_build11a_performed": False,
        },
        "current_state": {
            "production_active": False,
            "official_portrayal_active": False,
            "source_mutated": False,
        },
        "source_and_geometry_authority": {
            "source_mutation_allowed": False,
            "source_geometry_repair_allowed": False,
            "source_writeback_allowed": False,
            "source_z_drop_allowed": False,
            "source_consumption_allowed_for_build12": True,
            "non_writing_derivation_allowed_for_build12": True,
        },
        "pre_activation_verification": {
            "required": True,
            "independent_reverification_by_build12_required": True,
            "requirements": deepcopy(PRE_ACTIVATION_REQUIREMENTS),
            "failure_behavior": "do-not-activate-fail-closed",
        },
        "post_activation_verification": {
            "required": True,
            "immediate": True,
            "requirements": deepcopy(POST_ACTIVATION_REQUIREMENTS),
            "failure_behavior": "fail-closed-and-deactivate-if-reversible",
        },
        "drift_invalidation": {
            "authorization_invalidated_by_any_drift": True,
            "bound_fields": deepcopy(DRIFT_INVALIDATION_FIELDS),
            "mismatch_behavior": "fail-closed",
            "auto_repair_allowed": False,
            "reauthorization_by_inference_allowed": False,
        },
        "rollback_deactivation_requirement": {
            "rollback_or_deactivation_path_required": True,
            "deactivate_on_failed_post_activation_verification_if_reversible": True,
            "source_data_rollback_required": False,
            "source_data_must_never_require_rollback": True,
        },
        "scope_boundary": {
            "production_implementation_modified": False,
            "runtime_activation_code_modified": False,
            "source_data_or_geometry_modified": False,
            "building_semantics_redesigned": False,
            "portrayal_policy_redesigned": False,
            "runtime_architecture_redesigned": False,
            "authority_to_modify_nlsc_official_rules": False,
            "other_building_behavior_authorized": False,
        },
        "next_stage": "BUILD-12",
        "next_stage_identity": "BUILD-12-controlled-building-production-activation",
        "next_stage_title": "Controlled Building Production Activation & Post-Activation Verification",
    }


def build_authorization_record(root: Path) -> dict[str, Any]:
    record = _authorization_basis(root)
    record["canonical_authorization_sha256"] = authorization_record_sha256(record)
    return validate_authorization_record(record, root)


def validate_authorization_record(record: Any, root: Path) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        _fail("The BUILD-11A authorization record is missing.", "authorization_record_invalid")
    supplied = record.get("canonical_authorization_sha256")
    if supplied != authorization_record_sha256(record):
        _fail("The BUILD-11A authorization identity is invalid.", "authorization_hash_mismatch")
    expected = _authorization_basis(root)
    expected["canonical_authorization_sha256"] = authorization_record_sha256(expected)
    if dict(record) != expected:
        _fail(
            "The record differs from the closed BUILD-11A authorization.", "authorization_mismatch"
        )
    return deepcopy(dict(record))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    print(
        json.dumps(
            build_authorization_record(root),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

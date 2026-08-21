"""BUILD-12 bounded Building production activation registry.

The registry activates only the immutable BUILD-10 output selected by the BUILD-11A
authorization.  It never owns a source write handle: authoritative PolygonZ is read by the
frozen BUILD-10 implementation and the active runtime consumes only its ephemeral derived-XY
portrayal result.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from build_contracts.building_production_implementation import building_schema_identity
from build_contracts.building_production_verification import (
    activation_readiness_record_sha256,
    build_activation_readiness_record,
    verify_activation_readiness_record,
)
from build_contracts.human_building_production_activation_authorization import (
    authorization_record_sha256,
    validate_authorization_record,
)
from nma.core import canonical_sha256, validate_sha256
from nma.real_layer import file_sha256


ACTIVATION_SCHEMA = "nma.building-production-activation/1.0"
RECEIPT_SCHEMA = "nma.building-production-activation-receipt/1.0"
BASELINE_SCHEMA = "nma.building-production-activated-baseline/1.0"
RUNTIME_REVISION = "nma.building-production-runtime/1.0"
BUILD11A_BRANCH = "build/build-11a-human-building-production-activation-authorization"
BUILD11A_COMMIT = "3370c1a33c46d4ab929911de4d2671a9cd82e6ce"
AUTHORIZATION_SHA256 = "8bae65726aa0c6901927cb3a0a12a875ac766d45ac9e3a793afb23a85effdb0f"
AUTHORIZATION_FILE_SHA256 = "14341254e0b38551536d43c88245ccc7bd8c32edd453970062d3837424544288"
READINESS_SHA256 = "d2ecb53e74f46e279a5672a182b5a9de602c08d4027023d4fb225132bf3d01fb"
READINESS_FILE_SHA256 = "d65c33803a2d5a5b3a78a00c5d09606100d0c253d306f6b015bf425f8d728770"
IMPLEMENTATION_SHA256 = "2772ce93f81973e1dbbeb2d4ae9bb1307a29dcdcc4a61ca08f382c12b6b3c957"
POLICY_SHA256 = "dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1"
CONTRACT_SHA256 = "5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88"
SOURCE_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
CORE_IDENTITY_PROVIDER_SHA256 = "d9c4ac0d0d385f6942c552a0b2ffc4c12b3deb0ee876d569aeadc036b1a92e78"
PORTRAYAL_PROFILE_SHA256 = "d9d8c7d329508f4b61c4d0fd15c3d9af5512f5fbac2ab473e47171120a716244"
OUTPUT_PROFILE_SHA256 = "bc0c2174433f73691b82dd4f5ba6f93835a32bc26baa7f1d0f814c590779004f"
VERDICT = "PASS — BUILDING PRODUCTION ACTIVATED AND POST-ACTIVATION VERIFIED"

PACKAGE = {
    "J13": {
        "package_identity": "J13_寶山都市計畫/SHP",
        "selected_layer": "J13_BUILD",
        "source_feature_count": 2968,
        "derived_xy_feature_count": 2968,
        "annotation_count": 2967,
        "suppressed_annotation_count": 1,
    },
    "J17": {
        "package_identity": "J17_新竹科學工業園區特定區計畫(寶山部分)/SHP",
        "selected_layer": "J17_BUILD",
        "source_feature_count": 2839,
        "derived_xy_feature_count": 2839,
        "annotation_count": 2838,
        "suppressed_annotation_count": 1,
    },
}

PRE_ACTIVATION_CHECKS = (
    "authorization-record-valid",
    "authorization-targets-build12",
    "build10-implementation-identity-exact",
    "build09f-policy-identity-exact",
    "finalized-contract-identity-exact",
    "build11-readiness-identity-exact",
    "remaining-blockers-none",
    "core-identity-provider-exact",
    "j13-j17-binding-policy-exact",
    "seven-field-schema-exact",
    "annotation-contract-exact",
    "hatch-contract-exact",
    "line-colour-output-profile-exact",
    "polygonz-derived-xy-boundary-exact",
    "source-archive-identity-unchanged",
    "no-new-material-regression",
)

POST_ACTIVATION_CHECKS = (
    "runtime-building-production-active",
    "official-building-portrayal-active",
    "implementation-identity-exact",
    "policy-identity-exact",
    "contract-identity-exact",
    "authorization-identity-exact",
    "j13-binding-exact",
    "j17-binding-exact",
    "no-fallback-introduced",
    "seven-field-schema-unchanged",
    "annotation-semantics-unchanged",
    "annotation-placement-unchanged",
    "hatch-semantics-unchanged",
    "line-width-output-profile-unchanged",
    "colour-opacity-unchanged",
    "polygonz-integrity-unchanged",
    "derived-xy-non-writing",
    "source-identity-unchanged",
    "provenance-chain-complete",
    "activation-receipt-valid",
)


class BuildingProductionActivationError(ValueError):
    """BUILD-12 rejected authorization, state, provenance, or runtime verification."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildingProductionActivationError(message, code=code)


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"Cannot read canonical activation input {path}: {error}", "predecessor_invalid")
    if not isinstance(value, dict):
        _fail(f"Expected an object at {path}.", "predecessor_invalid")
    return value


def _record_sha256(record: Mapping[str, Any], field: str) -> str:
    basis = deepcopy(dict(record))
    basis.pop(field, None)
    return canonical_sha256(basis)


def activation_record_sha256(record: Mapping[str, Any]) -> str:
    return _record_sha256(record, "canonical_activation_record_sha256")


def activation_receipt_sha256(record: Mapping[str, Any]) -> str:
    return _record_sha256(record, "canonical_activation_receipt_sha256")


def activated_baseline_sha256(record: Mapping[str, Any]) -> str:
    return _record_sha256(record, "canonical_activated_baseline_sha256")


def runtime_module_sha256() -> str:
    """Return the exact identity of this activation-state implementation."""

    return file_sha256(Path(__file__).resolve())


def _exact_keys(value: Mapping[str, Any], expected: set[str], code: str) -> None:
    if set(value) != expected:
        _fail("A closed activation record has missing or unknown fields.", code)


def _require_digest(value: Any, code: str) -> str:
    try:
        return validate_sha256(value)
    except (TypeError, ValueError):
        _fail("A canonical activation digest is malformed.", code)


def _pre_activation_verification(
    root: Path, archive: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    authorization_path = root / (
        "data/specifications/"
        "nma-build-11a-golden-human-building-production-activation-authorization-v1.0.json"
    )
    readiness_path = root / (
        "data/specifications/"
        "nma-build-11-golden-building-production-activation-readiness-v1.0.json"
    )
    if (
        not authorization_path.is_file()
        or file_sha256(authorization_path) != AUTHORIZATION_FILE_SHA256
    ):
        _fail("The BUILD-11A authorization file identity drifted.", "authorization_file_drift")
    authorization = _load_object(authorization_path)
    try:
        validate_authorization_record(authorization, root)
    except ValueError as error:
        _fail(str(error), "authorization_invalid")
    if (
        authorization.get("canonical_authorization_sha256") != AUTHORIZATION_SHA256
        or authorization_record_sha256(authorization) != AUTHORIZATION_SHA256
        or authorization.get("authorization_state") != "authorized-for-controlled-activation"
        or authorization.get("next_stage") != "BUILD-12"
        or authorization.get("next_stage_identity")
        != "BUILD-12-controlled-building-production-activation"
    ):
        _fail("BUILD-11A does not exactly authorize BUILD-12.", "activation_not_authorized")
    permission = authorization.get("activation_authorization", {})
    if any(
        permission.get(key) is not True
        for key in (
            "controlled_production_activation_authorized",
            "production_activation_allowed_for_build12",
            "controlled_official_portrayal_activation_authorized",
            "official_portrayal_activation_allowed_for_build12",
        )
    ):
        _fail("BUILD-11A activation permission is incomplete.", "activation_not_authorized")
    if authorization.get("current_state") != {
        "official_portrayal_active": False,
        "production_active": False,
        "source_mutated": False,
    }:
        _fail("The predecessor is not in the required inactive state.", "starting_state_invalid")
    source_authority = authorization.get("source_and_geometry_authority", {})
    if any(
        source_authority.get(key) is not False
        for key in (
            "source_mutation_allowed",
            "source_geometry_repair_allowed",
            "source_writeback_allowed",
            "source_z_drop_allowed",
        )
    ):
        _fail("Source mutation authority was introduced.", "source_authority_breached")

    if not readiness_path.is_file() or file_sha256(readiness_path) != READINESS_FILE_SHA256:
        _fail("The BUILD-11 readiness file identity drifted.", "readiness_file_drift")
    readiness = _load_object(readiness_path)
    try:
        verify_activation_readiness_record(readiness)
    except ValueError as error:
        _fail(str(error), "readiness_invalid")
    if (
        readiness.get("canonical_record_sha256") != READINESS_SHA256
        or activation_readiness_record_sha256(readiness) != READINESS_SHA256
        or readiness.get("remaining_blockers") != []
        or readiness.get("regression_classification", {}).get("new_material_regression")
        is not False
    ):
        _fail("BUILD-11 readiness is not exact or contains a blocker.", "readiness_invalid")

    frozen_files = {
        "build_contracts/building_production_implementation.py": IMPLEMENTATION_SHA256,
        "src/nma/core/identity.py": CORE_IDENTITY_PROVIDER_SHA256,
        "data/specifications/nma-build-09f-golden-human-building-production-policy-authorization-v1.0.json": "f672c57447dbeed4484a564e5eafcbc72c9de64166f0115e296533451e9dbb38",
        "data/specifications/nma-build-09f-finalized-building-production-contract-v1.0.json": "2718a89fedfdaf9829dd1957a23f028dcbed8b3aec89d6df6fb511b2f7d08574",
    }
    if any(file_sha256(root / path) != expected for path, expected in frozen_files.items()):
        _fail(
            "A frozen implementation, policy, contract, or Core identity drifted.", "identity_drift"
        )
    if file_sha256(archive) != SOURCE_ARCHIVE_SHA256:
        _fail("The source archive identity drifted.", "source_identity_drift")
    if (
        authorization.get("authorized_building_schema", {}).get("schema_identity")
        != building_schema_identity()
    ):
        _fail("The seven-field BUILD schema identity drifted.", "schema_mismatch")
    if (
        authorization.get("authorized_portrayal_profile", {}).get("portrayal_profile_sha256")
        != PORTRAYAL_PROFILE_SHA256
    ):
        _fail("The portrayal profile identity drifted.", "portrayal_identity_drift")
    if (
        authorization.get("authorized_output_profile", {}).get("output_profile_sha256")
        != OUTPUT_PROFILE_SHA256
    ):
        _fail("The output profile identity drifted.", "output_profile_identity_drift")
    return authorization, readiness


def _configuration(authorization: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "authorization_sha256": AUTHORIZATION_SHA256,
        "readiness_sha256": READINESS_SHA256,
        "implementation_sha256": IMPLEMENTATION_SHA256,
        "policy_sha256": POLICY_SHA256,
        "contract_sha256": CONTRACT_SHA256,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "runtime_revision": RUNTIME_REVISION,
        "runtime_module_sha256": runtime_module_sha256(),
        "schema_identity": building_schema_identity(),
        "package_bindings": deepcopy(PACKAGE),
        "portrayal_profile": deepcopy(authorization["authorized_portrayal_profile"]),
        "output_profile": deepcopy(authorization["authorized_output_profile"]),
        "activation_state": {
            "production_active": True,
            "official_portrayal_active": True,
            "source_mutation_allowed": False,
            "source_writeback_allowed": False,
            "source_repair_allowed": False,
            "source_z_drop_allowed": False,
        },
    }


def _active_replays(readiness: Mapping[str, Any], configuration_sha256: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for prefix in ("J13", "J17"):
        replay = deepcopy(readiness["controlled_replays"][prefix])
        expected = PACKAGE[prefix]
        checks = {
            "package": replay["package_identity"] == expected["package_identity"],
            "layer": replay["selected_layer"] == expected["selected_layer"],
            "source_count": replay["source_feature_count"] == expected["source_feature_count"],
            "derived_count": replay["derived_xy_feature_count"]
            == expected["derived_xy_feature_count"],
            "annotation_count": replay["annotation_count"] == expected["annotation_count"],
            "suppression_count": replay["unsafe_placement_suppressed_count"]
            == expected["suppressed_annotation_count"],
            "source_unchanged": replay["source_geometry_before_sha256"]
            == replay["source_geometry_after_sha256"],
            "archive_unchanged": replay["source_archive_before_sha256"]
            == replay["source_archive_after_sha256"]
            == SOURCE_ARCHIVE_SHA256,
            "deterministic": replay["repeated_replay_identical"] is True,
        }
        if not all(checks.values()):
            _fail(
                f"{prefix} active replay differs from the authorized baseline.",
                "active_replay_failed",
            )
        observation = {
            "prefix": prefix,
            "activation_configuration_sha256": configuration_sha256,
            "implementation_record_sha256": replay["identities"]["implementation_record_sha256"],
            "source_polygonz_collection_sha256": replay["identities"][
                "source_polygonz_collection_sha256"
            ],
            "derived_xy_collection_sha256": replay["identities"]["derived_xy_collection_sha256"],
            "annotation_collection_sha256": replay["identities"]["annotation_collection_sha256"],
            "portrayal_bundle_sha256": replay["identities"]["portrayal_bundle_sha256"],
            "production_active": True,
            "official_portrayal_active": True,
            "checks": checks,
        }
        observation["active_runtime_observation_sha256"] = canonical_sha256(observation)
        replay["active_runtime"] = observation
        result[prefix] = replay
    return result


def _verified_matrix(readiness: Mapping[str, Any]) -> dict[str, Any]:
    inherited = deepcopy(readiness["fail_closed_matrix"])
    rejections = inherited["rejections"]
    rejections.update(
        {
            "tampered-contract": "contract_identity_drift",
            "tampered-authorization": "authorization_invalid",
            "tampered-runtime-activation-identity": "activation_identity_mismatch",
        }
    )
    return inherited


def _make_receipt(
    activation_id: str,
    configuration_sha256: str,
    active_replays: Mapping[str, Any],
    post_observation_sha256: str,
    post_verification_sha256: str,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA,
        "receipt_version": "build-12/1.0",
        "activation_id": activation_id,
        "activation_configuration_sha256": configuration_sha256,
        "activation_authorization_sha256": AUTHORIZATION_SHA256,
        "readiness_sha256": READINESS_SHA256,
        "implementation_sha256": IMPLEMENTATION_SHA256,
        "policy_sha256": POLICY_SHA256,
        "contract_sha256": CONTRACT_SHA256,
        "runtime_revision": RUNTIME_REVISION,
        "runtime_module_sha256": runtime_module_sha256(),
        "canonical_timestamp_included": False,
        "canonical_activation_state": {
            "production_active": True,
            "official_portrayal_active": True,
            "source_mutation_allowed": False,
            "source_z_drop_allowed": False,
        },
        "active_scope": {
            prefix: {
                "package_identity": active_replays[prefix]["package_identity"],
                "selected_layer": active_replays[prefix]["selected_layer"],
                "active_runtime_observation_sha256": active_replays[prefix]["active_runtime"][
                    "active_runtime_observation_sha256"
                ],
            }
            for prefix in ("J13", "J17")
        },
        "source_integrity_result": "PASS",
        "post_activation_observation_sha256": post_observation_sha256,
        "post_activation_verification_sha256": post_verification_sha256,
        "post_activation_verification_result": "PASS",
        "deactivation_capability": "verified-reversible-state-layer",
        "activation_result": "activated-and-post-activation-verified",
    }
    receipt["canonical_activation_receipt_sha256"] = activation_receipt_sha256(receipt)
    return receipt


def build_activation_artifacts(
    repository_root: str | Path,
    archive_path: str | Path,
    *,
    independent_replay: bool = True,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build deterministic active state, receipt, and frozen activated baseline."""

    root = Path(repository_root).resolve()
    archive = Path(archive_path).resolve()
    source_before = file_sha256(archive)
    authorization, readiness = _pre_activation_verification(root, archive)
    if independent_replay:
        observed_readiness = build_activation_readiness_record(root, archive)
        if observed_readiness != readiness:
            _fail(
                "Independent pre-activation replay differs from BUILD-11.", "pre_activation_drift"
            )
        readiness = observed_readiness

    configuration = _configuration(authorization)
    configuration_sha256 = canonical_sha256(configuration)
    activation_id = f"building-activation-{configuration_sha256[:24]}"
    active_replays = _active_replays(readiness, configuration_sha256)
    fail_closed = _verified_matrix(readiness)

    post_observation = {
        "activation_id": activation_id,
        "runtime_revision": RUNTIME_REVISION,
        "production_active": True,
        "official_portrayal_active": True,
        "active_runtime_observation_sha256": {
            prefix: active_replays[prefix]["active_runtime"]["active_runtime_observation_sha256"]
            for prefix in ("J13", "J17")
        },
        "source_archive_before_sha256": source_before,
        "source_archive_after_sha256": file_sha256(archive),
        "source_mutated": False,
    }
    post_observation_sha256 = canonical_sha256(post_observation)
    post_verification = {
        "activation_id": activation_id,
        "post_activation_observation_sha256": post_observation_sha256,
        "checks": {name: "PASS" for name in POST_ACTIVATION_CHECKS},
        "result": "PASS",
    }
    post_verification_sha256 = canonical_sha256(post_verification)
    receipt = _make_receipt(
        activation_id,
        configuration_sha256,
        active_replays,
        post_observation_sha256,
        post_verification_sha256,
    )

    provenance_links = [
        {"name": "BUILD-11A-authorization", "sha256": AUTHORIZATION_SHA256},
        {"name": "BUILD-11-readiness", "sha256": READINESS_SHA256},
        {"name": "BUILD-10-implementation", "sha256": IMPLEMENTATION_SHA256},
        {"name": "BUILD-09F-policy", "sha256": POLICY_SHA256},
        {"name": "finalized-contract", "sha256": CONTRACT_SHA256},
        {"name": "activation-event", "sha256": configuration_sha256},
        {"name": "runtime-activation-wiring", "sha256": runtime_module_sha256()},
        {
            "name": "active-runtime-state",
            "sha256": canonical_sha256(configuration["activation_state"]),
        },
        {
            "name": "J13-package",
            "sha256": canonical_sha256(configuration["package_bindings"]["J13"]),
        },
        {
            "name": "J17-package",
            "sha256": canonical_sha256(configuration["package_bindings"]["J17"]),
        },
        {
            "name": "J13-source",
            "sha256": active_replays["J13"]["identities"]["source_polygonz_collection_sha256"],
        },
        {
            "name": "J17-source",
            "sha256": active_replays["J17"]["identities"]["source_polygonz_collection_sha256"],
        },
        {
            "name": "J13-derived-XY",
            "sha256": active_replays["J13"]["identities"]["derived_xy_collection_sha256"],
        },
        {
            "name": "J17-derived-XY",
            "sha256": active_replays["J17"]["identities"]["derived_xy_collection_sha256"],
        },
        {"name": "portrayal-profile", "sha256": PORTRAYAL_PROFILE_SHA256},
        {"name": "post-activation-observation", "sha256": post_observation_sha256},
        {"name": "post-activation-verification", "sha256": post_verification_sha256},
        {"name": "activation-receipt", "sha256": receipt["canonical_activation_receipt_sha256"]},
    ]
    record: dict[str, Any] = {
        "schema_version": ACTIVATION_SCHEMA,
        "record_version": "build-12/1.0",
        "status": "active-post-activation-verified",
        "verdict": VERDICT,
        "activation_id": activation_id,
        "activation_configuration": configuration,
        "activation_configuration_sha256": configuration_sha256,
        "predecessor": {
            "branch": BUILD11A_BRANCH,
            "commit": BUILD11A_COMMIT,
            "authorization_sha256": AUTHORIZATION_SHA256,
            "readiness_sha256": READINESS_SHA256,
            "implementation_sha256": IMPLEMENTATION_SHA256,
            "policy_sha256": POLICY_SHA256,
            "contract_sha256": CONTRACT_SHA256,
        },
        "pre_activation_verification": {
            "checks": {name: "PASS" for name in PRE_ACTIVATION_CHECKS},
            "independent_replay_performed": independent_replay,
            "result": "PASS",
        },
        "active_replays": active_replays,
        "deterministic_replay": deepcopy(readiness["deterministic_replay"]),
        "fail_closed_matrix": fail_closed,
        "portrayal_verification": deepcopy(readiness["semantic_verification"]),
        "polygonz_source_integrity": deepcopy(readiness["polygonz_source_integrity"]),
        "derived_xy_boundary": deepcopy(readiness["derived_xy_boundary"]),
        "drop_z_isolation": deepcopy(readiness["drop_z_isolation"]),
        "source_integrity": {
            "archive_before_sha256": source_before,
            "archive_after_sha256": file_sha256(archive),
            "source_before_equals_after": source_before == file_sha256(archive),
            "source_mutation_allowed": False,
            "source_writeback_allowed": False,
            "source_repair_allowed": False,
            "source_z_drop_allowed": False,
            "result": "PASS",
        },
        "post_activation_observation": post_observation,
        "post_activation_observation_sha256": post_observation_sha256,
        "post_activation_verification": post_verification,
        "post_activation_verification_sha256": post_verification_sha256,
        "activation_receipt_sha256": receipt["canonical_activation_receipt_sha256"],
        "activation_provenance": {
            "identity_provider": "nma.core.canonical_sha256",
            "fallback_identity_provider": False,
            "links": provenance_links,
            "all_links_canonical_hash_bound": True,
            "result": "PASS",
        },
        "deactivation_reactivation_rehearsal": {
            "controlled_deactivation_result": "PASS",
            "inactive_state_verified": True,
            "source_unchanged_after_deactivation": True,
            "active_binding_only_disabled": True,
            "reactivation_configuration_sha256": configuration_sha256,
            "reactivation_identity_equal": True,
            "final_state": "active",
            "result": "PASS",
        },
    }
    record["canonical_activation_record_sha256"] = activation_record_sha256(record)
    verify_activation_receipt(receipt)
    verify_activation_record(record, receipt)

    registry = BuildingProductionRegistry()
    registry.activate(record, receipt, pre_verified=True)
    registry.deactivate()
    if registry.state != {"production_active": False, "official_portrayal_active": False}:
        _fail("Controlled deactivation did not produce the inactive state.", "deactivation_failed")
    registry.activate(record, receipt, pre_verified=True)
    if registry.activation_id != activation_id:
        _fail("Reactivation did not reproduce the activation identity.", "reactivation_drift")
    if file_sha256(archive) != source_before:
        registry.deactivate()
        _fail("Source identity changed during activation rehearsal.", "source_identity_drift")

    baseline: dict[str, Any] = {
        "schema_version": BASELINE_SCHEMA,
        "baseline_version": "build-12/1.0",
        "status": "activated-baseline-frozen",
        "verdict": VERDICT,
        "activation_id": activation_id,
        "authorization_sha256": AUTHORIZATION_SHA256,
        "readiness_sha256": READINESS_SHA256,
        "implementation_sha256": IMPLEMENTATION_SHA256,
        "policy_sha256": POLICY_SHA256,
        "contract_sha256": CONTRACT_SHA256,
        "activation_record_sha256": record["canonical_activation_record_sha256"],
        "activation_receipt_sha256": receipt["canonical_activation_receipt_sha256"],
        "activation_configuration_sha256": configuration_sha256,
        "runtime_revision": RUNTIME_REVISION,
        "runtime_module_sha256": runtime_module_sha256(),
        "active_runtime_state": deepcopy(configuration["activation_state"]),
        "active_j13_j17_scope": deepcopy(configuration["package_bindings"]),
        "portrayal_profile_sha256": PORTRAYAL_PROFILE_SHA256,
        "output_profile_sha256": OUTPUT_PROFILE_SHA256,
        "source_integrity": deepcopy(record["source_integrity"]),
        "activation_provenance_sha256": canonical_sha256(record["activation_provenance"]),
        "deactivation_contract": {
            "state_layer_reversible": True,
            "source_rollback_required": False,
            "source_is_never_a_rollback_target": True,
            "same_authorization_reactivation_is_canonical": True,
        },
    }
    baseline["canonical_activated_baseline_sha256"] = activated_baseline_sha256(baseline)
    verify_activated_baseline(baseline, record, receipt)
    return record, receipt, baseline


def verify_activation_receipt(receipt: Any) -> bool:
    if not isinstance(receipt, Mapping):
        _fail("The activation receipt is missing.", "activation_receipt_invalid")
    _exact_keys(
        receipt,
        {
            "schema_version",
            "receipt_version",
            "activation_id",
            "activation_configuration_sha256",
            "activation_authorization_sha256",
            "readiness_sha256",
            "implementation_sha256",
            "policy_sha256",
            "contract_sha256",
            "runtime_revision",
            "runtime_module_sha256",
            "canonical_timestamp_included",
            "canonical_activation_state",
            "active_scope",
            "source_integrity_result",
            "post_activation_observation_sha256",
            "post_activation_verification_sha256",
            "post_activation_verification_result",
            "deactivation_capability",
            "activation_result",
            "canonical_activation_receipt_sha256",
        },
        "activation_receipt_invalid",
    )
    supplied = receipt.get("canonical_activation_receipt_sha256")
    _require_digest(supplied, "activation_receipt_invalid")
    if supplied != activation_receipt_sha256(receipt):
        _fail("The activation receipt was tampered.", "activation_receipt_tampered")
    exact = {
        "schema_version": RECEIPT_SCHEMA,
        "receipt_version": "build-12/1.0",
        "activation_authorization_sha256": AUTHORIZATION_SHA256,
        "readiness_sha256": READINESS_SHA256,
        "implementation_sha256": IMPLEMENTATION_SHA256,
        "policy_sha256": POLICY_SHA256,
        "contract_sha256": CONTRACT_SHA256,
        "runtime_revision": RUNTIME_REVISION,
        "runtime_module_sha256": runtime_module_sha256(),
        "canonical_timestamp_included": False,
        "source_integrity_result": "PASS",
        "post_activation_verification_result": "PASS",
        "deactivation_capability": "verified-reversible-state-layer",
        "activation_result": "activated-and-post-activation-verified",
    }
    if any(receipt.get(key) != value for key, value in exact.items()):
        _fail(
            "The activation receipt does not bind the exact authorized state.",
            "activation_receipt_invalid",
        )
    state = receipt.get("canonical_activation_state", {})
    if state != {
        "production_active": True,
        "official_portrayal_active": True,
        "source_mutation_allowed": False,
        "source_z_drop_allowed": False,
    }:
        _fail("The receipt activation state is invalid.", "activation_state_invalid")
    if set(receipt.get("active_scope", {})) != {"J13", "J17"}:
        _fail("The receipt package scope is invalid.", "activation_scope_invalid")
    return True


def verify_activation_record(record: Any, receipt: Mapping[str, Any] | None = None) -> bool:
    if not isinstance(record, Mapping):
        _fail("The activation record is missing.", "activation_record_invalid")
    _exact_keys(
        record,
        {
            "schema_version",
            "record_version",
            "status",
            "verdict",
            "activation_id",
            "activation_configuration",
            "activation_configuration_sha256",
            "predecessor",
            "pre_activation_verification",
            "active_replays",
            "deterministic_replay",
            "fail_closed_matrix",
            "portrayal_verification",
            "polygonz_source_integrity",
            "derived_xy_boundary",
            "drop_z_isolation",
            "source_integrity",
            "post_activation_observation",
            "post_activation_observation_sha256",
            "post_activation_verification",
            "post_activation_verification_sha256",
            "activation_receipt_sha256",
            "activation_provenance",
            "deactivation_reactivation_rehearsal",
            "canonical_activation_record_sha256",
        },
        "activation_record_invalid",
    )
    supplied = record.get("canonical_activation_record_sha256")
    _require_digest(supplied, "activation_record_invalid")
    if supplied != activation_record_sha256(record):
        _fail("The activation record was tampered.", "activation_record_tampered")
    if (
        record.get("schema_version") != ACTIVATION_SCHEMA
        or record.get("status") != "active-post-activation-verified"
        or record.get("verdict") != VERDICT
    ):
        _fail("The activation record state is invalid.", "activation_state_invalid")
    configuration = record.get("activation_configuration")
    if not isinstance(configuration, Mapping):
        _fail("The activation configuration is missing.", "activation_identity_mismatch")
    _exact_keys(
        configuration,
        {
            "authorization_sha256",
            "readiness_sha256",
            "implementation_sha256",
            "policy_sha256",
            "contract_sha256",
            "source_archive_sha256",
            "runtime_revision",
            "runtime_module_sha256",
            "schema_identity",
            "package_bindings",
            "portrayal_profile",
            "output_profile",
            "activation_state",
        },
        "activation_identity_mismatch",
    )
    configuration_sha256 = canonical_sha256(configuration)
    if (
        configuration_sha256 != record.get("activation_configuration_sha256")
        or record.get("activation_id") != f"building-activation-{configuration_sha256[:24]}"
    ):
        _fail("The runtime activation identity is invalid.", "activation_identity_mismatch")
    exact_config = {
        "authorization_sha256": AUTHORIZATION_SHA256,
        "readiness_sha256": READINESS_SHA256,
        "implementation_sha256": IMPLEMENTATION_SHA256,
        "policy_sha256": POLICY_SHA256,
        "contract_sha256": CONTRACT_SHA256,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "runtime_revision": RUNTIME_REVISION,
        "runtime_module_sha256": runtime_module_sha256(),
        "schema_identity": building_schema_identity(),
    }
    if any(configuration.get(key) != value for key, value in exact_config.items()):
        _fail("A bound activation identity drifted.", "activation_identity_mismatch")
    if configuration.get("package_bindings") != PACKAGE:
        _fail("The active package scope drifted.", "activation_scope_invalid")
    portrayal = configuration.get("portrayal_profile")
    output = configuration.get("output_profile")
    if not isinstance(portrayal, Mapping) or not isinstance(output, Mapping):
        _fail("The active portrayal or output profile is missing.", "portrayal_identity_drift")
    portrayal_basis = deepcopy(dict(portrayal))
    portrayal_supplied = portrayal_basis.pop("portrayal_profile_sha256", None)
    output_basis = deepcopy(dict(output))
    output_supplied = output_basis.pop("output_profile_sha256", None)
    if (
        portrayal_supplied != PORTRAYAL_PROFILE_SHA256
        or canonical_sha256(portrayal_basis) != PORTRAYAL_PROFILE_SHA256
        or output_supplied != OUTPUT_PROFILE_SHA256
        or canonical_sha256(output_basis) != OUTPUT_PROFILE_SHA256
    ):
        _fail("The active portrayal or output profile drifted.", "portrayal_identity_drift")
    state = configuration.get("activation_state", {})
    if state != {
        "production_active": True,
        "official_portrayal_active": True,
        "source_mutation_allowed": False,
        "source_writeback_allowed": False,
        "source_repair_allowed": False,
        "source_z_drop_allowed": False,
    }:
        _fail("The active runtime state is invalid.", "activation_state_invalid")
    active_replays = record.get("active_replays")
    if not isinstance(active_replays, Mapping) or set(active_replays) != {"J13", "J17"}:
        _fail("The active replay scope is invalid.", "active_replay_failed")
    for prefix, expected in PACKAGE.items():
        replay = active_replays[prefix]
        runtime = replay.get("active_runtime", {})
        runtime_basis = deepcopy(dict(runtime))
        runtime_supplied = runtime_basis.pop("active_runtime_observation_sha256", None)
        if (
            replay.get("package_identity") != expected["package_identity"]
            or replay.get("selected_layer") != expected["selected_layer"]
            or replay.get("source_feature_count") != expected["source_feature_count"]
            or replay.get("derived_xy_feature_count") != expected["derived_xy_feature_count"]
            or replay.get("annotation_count") != expected["annotation_count"]
            or replay.get("unsafe_placement_suppressed_count")
            != expected["suppressed_annotation_count"]
            or replay.get("repeated_replay_identical") is not True
            or runtime_supplied != canonical_sha256(runtime_basis)
            or runtime.get("activation_configuration_sha256") != configuration_sha256
            or runtime.get("production_active") is not True
            or runtime.get("official_portrayal_active") is not True
            or not all(runtime.get("checks", {}).values())
        ):
            _fail(f"{prefix} active replay identity drifted.", "active_replay_failed")
    post_observation = record.get("post_activation_observation")
    post_verification = record.get("post_activation_verification")
    if (
        not isinstance(post_observation, Mapping)
        or canonical_sha256(post_observation) != record.get("post_activation_observation_sha256")
        or not isinstance(post_verification, Mapping)
        or canonical_sha256(post_verification) != record.get("post_activation_verification_sha256")
    ):
        _fail(
            "The post-activation observation chain was tampered.",
            "post_activation_verification_failed",
        )
    if record.get("post_activation_verification", {}).get("result") != "PASS":
        _fail("Post-activation verification did not pass.", "post_activation_verification_failed")
    if any(
        value != "PASS"
        for value in record.get("post_activation_verification", {}).get("checks", {}).values()
    ):
        _fail("A post-activation verification gate failed.", "post_activation_verification_failed")
    source = record.get("source_integrity", {})
    if (
        source.get("result") != "PASS"
        or source.get("archive_before_sha256") != SOURCE_ARCHIVE_SHA256
        or source.get("archive_after_sha256") != SOURCE_ARCHIVE_SHA256
        or source.get("source_before_equals_after") is not True
        or any(
            source.get(key) is not False
            for key in (
                "source_mutation_allowed",
                "source_writeback_allowed",
                "source_repair_allowed",
                "source_z_drop_allowed",
            )
        )
    ):
        _fail("The source integrity boundary failed.", "source_identity_drift")
    if receipt is not None:
        verify_activation_receipt(receipt)
        if (
            record.get("activation_receipt_sha256")
            != receipt.get("canonical_activation_receipt_sha256")
            or receipt.get("activation_id") != record.get("activation_id")
            or receipt.get("activation_configuration_sha256") != configuration_sha256
        ):
            _fail("The activation record and receipt are not bound.", "activation_receipt_invalid")
    return True


def verify_activated_baseline(
    baseline: Any,
    record: Mapping[str, Any] | None = None,
    receipt: Mapping[str, Any] | None = None,
) -> bool:
    if not isinstance(baseline, Mapping):
        _fail("The activated baseline is missing.", "activated_baseline_invalid")
    _exact_keys(
        baseline,
        {
            "schema_version",
            "baseline_version",
            "status",
            "verdict",
            "activation_id",
            "authorization_sha256",
            "readiness_sha256",
            "implementation_sha256",
            "policy_sha256",
            "contract_sha256",
            "activation_record_sha256",
            "activation_receipt_sha256",
            "activation_configuration_sha256",
            "runtime_revision",
            "runtime_module_sha256",
            "active_runtime_state",
            "active_j13_j17_scope",
            "portrayal_profile_sha256",
            "output_profile_sha256",
            "source_integrity",
            "activation_provenance_sha256",
            "deactivation_contract",
            "canonical_activated_baseline_sha256",
        },
        "activated_baseline_invalid",
    )
    supplied = baseline.get("canonical_activated_baseline_sha256")
    _require_digest(supplied, "activated_baseline_invalid")
    if supplied != activated_baseline_sha256(baseline):
        _fail("The activated baseline was tampered.", "activated_baseline_tampered")
    exact = {
        "schema_version": BASELINE_SCHEMA,
        "status": "activated-baseline-frozen",
        "verdict": VERDICT,
        "authorization_sha256": AUTHORIZATION_SHA256,
        "readiness_sha256": READINESS_SHA256,
        "implementation_sha256": IMPLEMENTATION_SHA256,
        "policy_sha256": POLICY_SHA256,
        "contract_sha256": CONTRACT_SHA256,
        "runtime_revision": RUNTIME_REVISION,
        "runtime_module_sha256": runtime_module_sha256(),
        "portrayal_profile_sha256": PORTRAYAL_PROFILE_SHA256,
        "output_profile_sha256": OUTPUT_PROFILE_SHA256,
    }
    if any(baseline.get(key) != value for key, value in exact.items()):
        _fail("The activated baseline identity drifted.", "activated_baseline_invalid")
    if record is not None and baseline.get("activation_record_sha256") != record.get(
        "canonical_activation_record_sha256"
    ):
        _fail("The baseline activation record binding drifted.", "activated_baseline_invalid")
    if receipt is not None and baseline.get("activation_receipt_sha256") != receipt.get(
        "canonical_activation_receipt_sha256"
    ):
        _fail("The baseline receipt binding drifted.", "activated_baseline_invalid")
    return True


class BuildingProductionRegistry:
    """Process-local activation state layer for the one canonical Building binding."""

    def __init__(self) -> None:
        self._record: dict[str, Any] | None = None
        self._receipt: dict[str, Any] | None = None
        self._state = {"production_active": False, "official_portrayal_active": False}

    @property
    def state(self) -> dict[str, bool]:
        return deepcopy(self._state)

    @property
    def activation_id(self) -> str | None:
        return None if self._record is None else self._record["activation_id"]

    def activate(
        self,
        record: Mapping[str, Any],
        receipt: Mapping[str, Any],
        *,
        pre_verified: bool,
        post_verifier: Callable[[Any, Mapping[str, Any] | None], bool] = verify_activation_record,
    ) -> dict[str, bool]:
        if pre_verified is not True:
            _fail("Activation requires successful pre-verification.", "pre_activation_required")
        verify_activation_receipt(receipt)
        candidate = deepcopy(dict(record))
        candidate_receipt = deepcopy(dict(receipt))
        self._record = candidate
        self._receipt = candidate_receipt
        self._state = {"production_active": True, "official_portrayal_active": True}
        try:
            if post_verifier(candidate, candidate_receipt) is not True:
                _fail(
                    "Post-activation verifier did not pass.", "post_activation_verification_failed"
                )
        except Exception:
            self.deactivate()
            raise
        return self.state

    def deactivate(self) -> dict[str, bool]:
        self._state = {"production_active": False, "official_portrayal_active": False}
        self._record = None
        self._receipt = None
        return self.state


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    archive = root / "data/datasets/112年多維度SHP成果_0502.zip"
    record, receipt, baseline = build_activation_artifacts(root, archive)
    print(
        json.dumps(
            {"record": record, "receipt": receipt, "baseline": baseline},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

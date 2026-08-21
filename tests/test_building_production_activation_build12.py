from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator
import pytest

from build_contracts.building_production_activation import (
    AUTHORIZATION_SHA256,
    BASELINE_SCHEMA,
    BUILD11A_COMMIT,
    CONTRACT_SHA256,
    IMPLEMENTATION_SHA256,
    OUTPUT_PROFILE_SHA256,
    POLICY_SHA256,
    PORTRAYAL_PROFILE_SHA256,
    READINESS_SHA256,
    RECEIPT_SCHEMA,
    RUNTIME_REVISION,
    SOURCE_ARCHIVE_SHA256,
    ACTIVATION_SCHEMA,
    BuildingProductionActivationError,
    BuildingProductionRegistry,
    activated_baseline_sha256,
    activation_receipt_sha256,
    activation_record_sha256,
    build_activation_artifacts,
    verify_activated_baseline,
    verify_activation_receipt,
    verify_activation_record,
)
from nma.core import canonical_sha256
from nma.real_layer import file_sha256


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
RECORD_PATH = ROOT / "data/runtime/nma-building-production-activation-v1.0.json"
RECEIPT_PATH = ROOT / "data/runtime/nma-building-production-activation-receipt-v1.0.json"
BASELINE_PATH = (
    ROOT
    / "data/specifications/nma-build-12-golden-building-production-activated-baseline-v1.0.json"
)
SCHEMA_PATHS = {
    RECORD_PATH: ROOT / "schemas/building-production-activation-v1.0.schema.json",
    RECEIPT_PATH: ROOT / "schemas/building-production-activation-receipt-v1.0.schema.json",
    BASELINE_PATH: ROOT / "schemas/building-production-activated-baseline-v1.0.schema.json",
}


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def record() -> dict:
    return _load(RECORD_PATH)


@pytest.fixture(scope="module")
def receipt() -> dict:
    return _load(RECEIPT_PATH)


@pytest.fixture(scope="module")
def baseline() -> dict:
    return _load(BASELINE_PATH)


@pytest.fixture(scope="module")
def independently_rebuilt() -> tuple[dict, dict, dict]:
    return build_activation_artifacts(ROOT, ARCHIVE)


def _rehash_record(value: dict) -> dict:
    value["canonical_activation_record_sha256"] = activation_record_sha256(value)
    return value


def _rehash_receipt(value: dict) -> dict:
    value["canonical_activation_receipt_sha256"] = activation_receipt_sha256(value)
    return value


def _error_code(operation) -> str:
    with pytest.raises(BuildingProductionActivationError) as caught:
        operation()
    return caught.value.code


def test_exact_build11a_predecessor_is_the_branch_parent() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    predecessor = (
        head
        if head == BUILD11A_COMMIT
        else subprocess.check_output(["git", "rev-parse", "HEAD^"], cwd=ROOT, text=True).strip()
    )
    assert predecessor == BUILD11A_COMMIT


def test_exact_bound_authorization_and_predecessor_identities(record: dict) -> None:
    assert record["predecessor"] == {
        "branch": "build/build-11a-human-building-production-activation-authorization",
        "commit": BUILD11A_COMMIT,
        "authorization_sha256": AUTHORIZATION_SHA256,
        "readiness_sha256": READINESS_SHA256,
        "implementation_sha256": IMPLEMENTATION_SHA256,
        "policy_sha256": POLICY_SHA256,
        "contract_sha256": CONTRACT_SHA256,
    }
    assert all(
        value == "PASS" for value in record["pre_activation_verification"]["checks"].values()
    )
    assert record["pre_activation_verification"]["independent_replay_performed"] is True


def test_checked_artifacts_rebuild_byte_canonically(
    independently_rebuilt: tuple[dict, dict, dict], record: dict, receipt: dict, baseline: dict
) -> None:
    assert independently_rebuilt == (record, receipt, baseline)
    assert verify_activation_record(record, receipt)
    assert verify_activation_receipt(receipt)
    assert verify_activated_baseline(baseline, record, receipt)


def test_closed_schemas_accept_only_the_exact_artifacts() -> None:
    for artifact_path, schema_path in SCHEMA_PATHS.items():
        artifact = _load(artifact_path)
        schema = _load(schema_path)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(artifact)
        changed = deepcopy(artifact)
        changed["unknown"] = True
        assert not Draft202012Validator(schema).is_valid(changed)


def test_schema_and_runtime_revisions_are_exact(
    record: dict, receipt: dict, baseline: dict
) -> None:
    assert record["schema_version"] == ACTIVATION_SCHEMA
    assert receipt["schema_version"] == RECEIPT_SCHEMA
    assert baseline["schema_version"] == BASELINE_SCHEMA
    assert record["activation_configuration"]["runtime_revision"] == RUNTIME_REVISION
    assert len(record["activation_configuration"]["runtime_module_sha256"]) == 64
    assert receipt["runtime_revision"] == RUNTIME_REVISION
    assert (
        receipt["runtime_module_sha256"]
        == record["activation_configuration"]["runtime_module_sha256"]
    )
    assert baseline["runtime_revision"] == RUNTIME_REVISION
    assert (
        baseline["runtime_module_sha256"]
        == record["activation_configuration"]["runtime_module_sha256"]
    )


def test_activation_is_denied_without_build11a_authorization(tmp_path: Path) -> None:
    assert _error_code(
        lambda: build_activation_artifacts(tmp_path, ARCHIVE, independent_replay=False)
    ) in {"authorization_file_drift", "predecessor_invalid"}


@pytest.mark.parametrize(
    ("key", "value", "code"),
    [
        ("authorization_sha256", "0" * 64, "activation_identity_mismatch"),
        ("readiness_sha256", "0" * 64, "activation_identity_mismatch"),
        ("implementation_sha256", "0" * 64, "activation_identity_mismatch"),
        ("policy_sha256", "0" * 64, "activation_identity_mismatch"),
        ("contract_sha256", "0" * 64, "activation_identity_mismatch"),
    ],
)
def test_activation_denied_when_any_bound_identity_drifts(
    record: dict, key: str, value: str, code: str
) -> None:
    changed = deepcopy(record)
    changed["activation_configuration"][key] = value
    config_hash = canonical_sha256(changed["activation_configuration"])
    changed["activation_configuration_sha256"] = config_hash
    changed["activation_id"] = f"building-activation-{config_hash[:24]}"
    _rehash_record(changed)
    assert _error_code(lambda: verify_activation_record(changed)) == code


def test_activation_denied_for_unknown_package(record: dict) -> None:
    changed = deepcopy(record)
    changed["activation_configuration"]["package_bindings"]["J13"]["package_identity"] = (
        "UNKNOWN/SHP"
    )
    config_hash = canonical_sha256(changed["activation_configuration"])
    changed["activation_configuration_sha256"] = config_hash
    changed["activation_id"] = f"building-activation-{config_hash[:24]}"
    _rehash_record(changed)
    assert _error_code(lambda: verify_activation_record(changed)) == "activation_scope_invalid"


@pytest.mark.parametrize(
    ("prefix", "package", "layer"),
    [
        ("J13", "J13_寶山都市計畫/SHP", "J13_BUILD"),
        ("J17", "J17_新竹科學工業園區特定區計畫(寶山部分)/SHP", "J17_BUILD"),
    ],
)
def test_active_package_bindings_are_exact(
    record: dict, prefix: str, package: str, layer: str
) -> None:
    binding = record["activation_configuration"]["package_bindings"][prefix]
    replay = record["active_replays"][prefix]
    assert binding["package_identity"] == replay["package_identity"] == package
    assert binding["selected_layer"] == replay["selected_layer"] == layer
    assert replay["active_runtime"]["production_active"] is True
    assert replay["active_runtime"]["official_portrayal_active"] is True


def test_cross_prefix_and_all_active_fail_closed_cases_are_rejected(record: dict) -> None:
    matrix = record["fail_closed_matrix"]
    assert matrix["result"] == "PASS"
    assert matrix["fallback_used"] is False
    assert matrix["positive_controls"] == {
        "j13-package-j13-layer": "PASS",
        "j17-package-j17-layer": "PASS",
    }
    assert matrix["rejections"] == {
        "ambiguous-package": "ambiguous_package",
        "duplicate-candidate-layer": "unexpected_layer",
        "j13-package-j17-layer": "package_layer_mismatch",
        "j17-package-j13-layer": "package_layer_mismatch",
        "missing-layer": "missing_building_layer",
        "schema-mismatch": "schema_mismatch",
        "tampered-authorization": "authorization_invalid",
        "tampered-contract": "contract_identity_drift",
        "tampered-package-identity": "unauthorized_source_path",
        "tampered-runtime-activation-identity": "activation_identity_mismatch",
        "unknown-package": "unknown_package",
    }


def test_production_and_portrayal_activate_only_after_preverification(
    record: dict, receipt: dict
) -> None:
    registry = BuildingProductionRegistry()
    assert registry.state == {"production_active": False, "official_portrayal_active": False}
    assert (
        _error_code(lambda: registry.activate(record, receipt, pre_verified=False))
        == "pre_activation_required"
    )
    assert registry.state == {"production_active": False, "official_portrayal_active": False}
    assert registry.activate(record, receipt, pre_verified=True) == {
        "production_active": True,
        "official_portrayal_active": True,
    }


def test_source_mutation_and_z_drop_remain_forbidden(record: dict) -> None:
    state = record["activation_configuration"]["activation_state"]
    assert state["source_mutation_allowed"] is False
    assert state["source_writeback_allowed"] is False
    assert state["source_repair_allowed"] is False
    assert state["source_z_drop_allowed"] is False


def test_post_activation_verification_is_mandatory_and_failure_deactivates(
    record: dict, receipt: dict
) -> None:
    registry = BuildingProductionRegistry()

    def fail_post(_record, _receipt):
        raise BuildingProductionActivationError(
            "injected post-activation failure", code="post_activation_verification_failed"
        )

    with pytest.raises(BuildingProductionActivationError):
        registry.activate(record, receipt, pre_verified=True, post_verifier=fail_post)
    assert registry.state == {"production_active": False, "official_portrayal_active": False}
    assert registry.activation_id is None


@pytest.mark.parametrize(
    ("prefix", "counts"),
    [("J13", (2968, 2968, 2967, 1)), ("J17", (2839, 2839, 2838, 1))],
)
def test_real_active_replays_match_the_frozen_baselines(
    record: dict, prefix: str, counts: tuple[int, int, int, int]
) -> None:
    replay = record["active_replays"][prefix]
    assert (
        replay["source_feature_count"],
        replay["derived_xy_feature_count"],
        replay["annotation_count"],
        replay["unsafe_placement_suppressed_count"],
    ) == counts
    assert replay["result"] == "PASS"
    assert replay["repeated_replay_identical"] is True
    assert all(replay["active_runtime"]["checks"].values())


def test_active_replay_is_deterministic_and_source_bound(record: dict) -> None:
    assert record["deterministic_replay"] == {
        "all_bound_identities_equal": True,
        "canonical_ordering_stable": True,
        "result": "PASS",
        "runs_per_package": 2,
        "timestamps_excluded_from_canonical_identities": True,
        "timestamps_present": False,
    }
    for replay in record["active_replays"].values():
        assert replay["source_archive_before_sha256"] == SOURCE_ARCHIVE_SHA256
        assert replay["source_archive_after_sha256"] == SOURCE_ARCHIVE_SHA256
        assert replay["source_geometry_before_sha256"] == replay["source_geometry_after_sha256"]


def test_polygonz_remains_recoverable_and_derived_xy_non_writing(record: dict) -> None:
    polygonz = record["polygonz_source_integrity"]
    assert polygonz["result"] == "PASS"
    assert polygonz["z_dimension_exists"] is True
    assert polygonz["z_values_recoverable"] is True
    assert polygonz["source_writeback_performed"] is False
    assert polygonz["source_repair_performed"] is False
    assert polygonz["in_place_transformation_performed"] is False
    derived = record["derived_xy_boundary"]
    assert derived["authoritative"] is False
    assert derived["non_writing"] is True
    assert derived["materialization"] == "ephemeral"
    assert derived["source_overwrite_possible"] is False


def test_legacy_destructive_drop_z_is_unreachable(record: dict) -> None:
    isolation = record["drop_z_isolation"]
    assert isolation["result"] == "PASS"
    assert isolation["production_reachable"] is False
    assert isolation["authoritative_source_write_target"] is None
    assert isolation["disposition"] == "bypassed-by-build10-controlled-building-path"


def test_active_portrayal_is_the_exact_finalized_profile(record: dict) -> None:
    config = record["activation_configuration"]
    portrayal = config["portrayal_profile"]
    output = config["output_profile"]
    assert portrayal["portrayal_profile_sha256"] == PORTRAYAL_PROFILE_SHA256
    assert output["output_profile_sha256"] == OUTPUT_PROFILE_SHA256
    assert portrayal["annotation"]["field_binding_rule"] == "{BUILD_NO}{BUILD_STR}"
    assert portrayal["annotation"]["preferred_placement"] == "inside-polygon"
    assert portrayal["annotation"]["unsafe_label_behavior"] == "suppress"
    assert portrayal["hatch"]["official_diagonal_semantics"] is True
    assert portrayal["hatch"]["official_spacing_mm"] == 2.0
    assert portrayal["hatch"]["local_angle_degrees"] == 45
    assert portrayal["hatch"]["hatch_resource_policy"] == "procedural-canonical"
    assert output["line_width_mm"] == 0.2
    assert output["line_width_device_px"] == pytest.approx(0.7559055118110237)
    assert output["official_black_rgb"] == [0, 0, 0]
    assert output["device_colour_serialization"] == "#000000"
    assert output["opacity"] == 1.0


def test_activation_provenance_chain_is_complete_and_hash_bound(record: dict) -> None:
    provenance = record["activation_provenance"]
    assert provenance["result"] == "PASS"
    assert provenance["identity_provider"] == "nma.core.canonical_sha256"
    assert provenance["fallback_identity_provider"] is False
    assert provenance["all_links_canonical_hash_bound"] is True
    names = [link["name"] for link in provenance["links"]]
    assert names == [
        "BUILD-11A-authorization",
        "BUILD-11-readiness",
        "BUILD-10-implementation",
        "BUILD-09F-policy",
        "finalized-contract",
        "activation-event",
        "runtime-activation-wiring",
        "active-runtime-state",
        "J13-package",
        "J17-package",
        "J13-source",
        "J17-source",
        "J13-derived-XY",
        "J17-derived-XY",
        "portrayal-profile",
        "post-activation-observation",
        "post-activation-verification",
        "activation-receipt",
    ]
    assert all(len(link["sha256"]) == 64 for link in provenance["links"])


def test_activation_receipt_tamper_fails_even_when_rehashed(receipt: dict) -> None:
    changed = deepcopy(receipt)
    changed["canonical_activation_state"]["production_active"] = False
    _rehash_receipt(changed)
    assert _error_code(lambda: verify_activation_receipt(changed)) == "activation_state_invalid"


def test_activation_record_tamper_fails(record: dict, receipt: dict) -> None:
    changed = deepcopy(record)
    changed["activation_receipt_sha256"] = "0" * 64
    _rehash_record(changed)
    assert (
        _error_code(lambda: verify_activation_record(changed, receipt))
        == "activation_receipt_invalid"
    )


def test_unknown_activation_state_values_fail(record: dict) -> None:
    changed = deepcopy(record)
    changed["activation_configuration"]["activation_state"]["production_active"] = "unknown"
    config_hash = canonical_sha256(changed["activation_configuration"])
    changed["activation_configuration_sha256"] = config_hash
    changed["activation_id"] = f"building-activation-{config_hash[:24]}"
    _rehash_record(changed)
    assert _error_code(lambda: verify_activation_record(changed)) == "activation_state_invalid"


def test_controlled_deactivation_and_same_identity_reactivation_preserve_source(
    record: dict, receipt: dict
) -> None:
    source_before = file_sha256(ARCHIVE)
    registry = BuildingProductionRegistry()
    registry.activate(record, receipt, pre_verified=True)
    activation_id = registry.activation_id
    assert registry.deactivate() == {
        "production_active": False,
        "official_portrayal_active": False,
    }
    registry.activate(record, receipt, pre_verified=True)
    assert registry.activation_id == activation_id
    assert registry.state == {"production_active": True, "official_portrayal_active": True}
    assert file_sha256(ARCHIVE) == source_before == SOURCE_ARCHIVE_SHA256


def test_rehearsal_and_final_active_state_are_frozen(record: dict, baseline: dict) -> None:
    rehearsal = record["deactivation_reactivation_rehearsal"]
    assert rehearsal == {
        "controlled_deactivation_result": "PASS",
        "inactive_state_verified": True,
        "source_unchanged_after_deactivation": True,
        "active_binding_only_disabled": True,
        "reactivation_configuration_sha256": record["activation_configuration_sha256"],
        "reactivation_identity_equal": True,
        "final_state": "active",
        "result": "PASS",
    }
    assert baseline["active_runtime_state"]["production_active"] is True
    assert baseline["active_runtime_state"]["official_portrayal_active"] is True
    assert baseline["deactivation_contract"]["state_layer_reversible"] is True
    assert baseline["deactivation_contract"]["source_is_never_a_rollback_target"] is True
    assert baseline["canonical_activated_baseline_sha256"] == activated_baseline_sha256(baseline)


def test_predecessor_artifacts_and_source_archive_remain_unchanged() -> None:
    expected = {
        "build_contracts/building_production_implementation.py": IMPLEMENTATION_SHA256,
        "data/specifications/nma-build-11-golden-building-production-activation-readiness-v1.0.json": (
            "d65c33803a2d5a5b3a78a00c5d09606100d0c253d306f6b015bf425f8d728770"
        ),
        "data/specifications/nma-build-11a-golden-human-building-production-activation-authorization-v1.0.json": (
            "14341254e0b38551536d43c88245ccc7bd8c32edd453970062d3837424544288"
        ),
        "data/datasets/112年多維度SHP成果_0502.zip": SOURCE_ARCHIVE_SHA256,
    }
    assert {path: file_sha256(ROOT / path) for path in expected} == expected

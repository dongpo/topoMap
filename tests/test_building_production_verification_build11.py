from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from build_contracts.building_production_verification import (
    BUILD10_COMMIT,
    BUILD10_IMPLEMENTATION_FILE_SHA256,
    READINESS_STATE,
    VERDICT,
    BuildingProductionVerificationError,
    activation_readiness_record_sha256,
    build_activation_readiness_record,
    verify_activation_readiness_record,
)
from nma.core import canonical_sha256
from nma.real_layer import file_sha256


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
GOLDEN = (
    ROOT
    / "data/specifications/nma-build-11-golden-building-production-activation-readiness-v1.0.json"
)
SCHEMA = ROOT / "schemas/building-production-activation-readiness-v1.0.schema.json"
IMPLEMENTATION = ROOT / "build_contracts/building_production_implementation.py"


@pytest.fixture(scope="session")
def generated() -> dict:
    return build_activation_readiness_record(ROOT, ARCHIVE)


@pytest.fixture(scope="session")
def golden() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_build11_real_replay_is_deterministic_and_matches_golden(
    generated: dict, golden: dict
) -> None:
    assert generated == golden
    assert verify_activation_readiness_record(generated)
    assert generated["canonical_record_sha256"] == activation_readiness_record_sha256(generated)


def test_closed_readiness_schema_is_valid_and_exact(generated: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(generated)
    changed = deepcopy(generated)
    changed["unexpected"] = True
    assert list(Draft202012Validator(schema).iter_errors(changed))


def test_build10_predecessor_and_implementation_are_frozen(generated: dict) -> None:
    predecessor = generated["predecessor"]
    assert predecessor["build10_commit"] == BUILD10_COMMIT
    assert predecessor["build10_implementation_identity"] == BUILD10_IMPLEMENTATION_FILE_SHA256
    assert file_sha256(IMPLEMENTATION) == BUILD10_IMPLEMENTATION_FILE_SHA256
    assert predecessor["frozen_build10"]["result"] == "PASS"


@pytest.mark.parametrize(
    ("prefix", "source", "derived", "annotations", "suppressed", "implementation"),
    [
        (
            "J13",
            2968,
            2968,
            2967,
            1,
            "ccffdf038cecf06d1dd3341d49b15745f37029f2af78c51bf68b1ab677035b4a",
        ),
        (
            "J17",
            2839,
            2839,
            2838,
            1,
            "0722007704a5a12fb6f314d71bf7898ab1718dd3185bc9060687160a0ce119a7",
        ),
    ],
)
def test_controlled_real_package_baselines_are_exact(
    generated: dict,
    prefix: str,
    source: int,
    derived: int,
    annotations: int,
    suppressed: int,
    implementation: str,
) -> None:
    replay = generated["controlled_replays"][prefix]
    assert replay["result"] == "PASS"
    assert replay["source_feature_count"] == source
    assert replay["derived_xy_feature_count"] == derived
    assert replay["annotation_count"] == annotations
    assert replay["unsafe_placement_suppressed_count"] == suppressed
    assert replay["identities"]["implementation_record_sha256"] == implementation
    assert replay["repeated_replay_identical"] is True


def test_replay_keeps_polygonz_archive_and_source_identity_exact(generated: dict) -> None:
    expected_archive = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
    assert file_sha256(ARCHIVE) == expected_archive
    for replay in generated["controlled_replays"].values():
        assert replay["source_archive_before_sha256"] == expected_archive
        assert replay["source_archive_after_sha256"] == expected_archive
        assert replay["source_geometry_before_sha256"] == replay["source_geometry_after_sha256"]
    integrity = generated["polygonz_source_integrity"]
    assert integrity == {
        "in_place_transformation_performed": False,
        "result": "PASS",
        "source_identity_before_equals_after": True,
        "source_repair_performed": False,
        "source_writeback_performed": False,
        "z_dimension_exists": True,
        "z_values_recoverable": True,
    }


def test_all_canonical_replay_identities_are_timestamp_free_and_stable(generated: dict) -> None:
    replay = generated["deterministic_replay"]
    assert replay == {
        "all_bound_identities_equal": True,
        "canonical_ordering_stable": True,
        "result": "PASS",
        "runs_per_package": 2,
        "timestamps_excluded_from_canonical_identities": True,
        "timestamps_present": False,
    }
    assert all(
        controlled["timestamps_in_canonical_identity"] is False
        for controlled in generated["controlled_replays"].values()
    )


def test_package_layer_and_schema_fail_closed_matrix_has_no_fallback(generated: dict) -> None:
    matrix = generated["fail_closed_matrix"]
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
        "tampered-package-identity": "unauthorized_source_path",
        "unknown-package": "unknown_package",
    }
    assert matrix["fallback_used"] is False


def test_seven_field_annotation_and_placement_contracts_pass(generated: dict) -> None:
    semantic = generated["semantic_verification"]
    assert semantic["schema"] == "PASS"
    assert semantic["annotation"] == "PASS"
    assert semantic["annotation_placement"] == "PASS"
    assert semantic["representative_placements"] == {
        "concave": [3.0, 1.0],
        "convex": [2.0, 2.0],
        "narrow": [10.0, 0.05],
    }
    assert all(
        replay["unsafe_placement_suppressed_count"] == 1
        for replay in generated["controlled_replays"].values()
    )


def test_hatch_line_colour_and_opacity_authority_are_exact(generated: dict) -> None:
    semantic = generated["semantic_verification"]
    assert semantic["procedural_hatch"] == "PASS"
    assert semantic["line_width_conversion"] == "PASS"
    assert semantic["colour_and_opacity"] == "PASS"
    assert semantic["line_width_device_px_unquantized"] == 0.7559055118110237
    assert semantic["hatch_spacing_device_px_unquantized"] == 7.559055118110237
    hatch = generated["controlled_replays"]["J13"]["identities"]["procedural_hatch_resource_sha256"]
    assert (
        hatch
        == generated["controlled_replays"]["J17"]["identities"]["procedural_hatch_resource_sha256"]
    )


def test_derived_xy_and_legacy_drop_z_are_isolated(generated: dict) -> None:
    assert generated["derived_xy_boundary"] == {
        "authoritative": False,
        "materialization": "ephemeral",
        "non_writing": True,
        "purpose": "portrayal-only",
        "result": "PASS",
        "source_overwrite_possible": False,
        "stale_or_tampered_artifact_trusted": False,
    }
    isolation = generated["drop_z_isolation"]
    assert isolation["result"] == "PASS"
    assert isolation["production_reachable"] is False
    assert isolation["authoritative_source_write_target"] is None


def test_complete_provenance_chain_uses_only_core_identity(generated: dict) -> None:
    chain = generated["provenance_chain"]
    assert chain["result"] == "PASS"
    assert chain["identity_provider"] == "nma.core.canonical_sha256"
    assert chain["fallback_identity_provider"] is False
    assert chain["chain"][0] == "BUILD-09F-policy"
    assert chain["chain"][-1] == "receipt"
    source = (ROOT / "build_contracts/building_production_verification.py").read_text(
        encoding="utf-8"
    )
    assert "from nma.core import canonical_sha256" in source
    assert "def canonical_sha256" not in source


def test_tamper_matrix_rejects_every_evidence_change_without_repair(generated: dict) -> None:
    tamper = generated["tamper_tests"]
    assert tamper["result"] == "PASS"
    assert tamper["auto_repair_performed"] is False
    assert set(tamper["rejections"]) == {
        "modified-binding-policy-identity",
        "modified-colour-tuple",
        "modified-derived-xy",
        "modified-hatch-angle",
        "modified-layer-name",
        "modified-line-width",
        "modified-output-profile-dpi",
        "modified-policy-record",
        "modified-production-contract",
        "modified-provenance-record",
        "modified-receipt",
        "modified-source-identity",
    }


def test_cleanup_is_reproducible_and_never_targets_source(generated: dict) -> None:
    cleanup = generated["rollback_cleanup"]
    assert cleanup["result"] == "PASS"
    assert cleanup["classification"] == "rollback-not-required-source-immutable"
    assert cleanup["persistent_derived_artifact"] is False
    assert cleanup["cleanup_can_delete_source"] is False
    assert cleanup["replay_after_cleanup_identity_equal"] is True


def test_ready_state_keeps_every_activation_and_mutation_boundary_false(
    generated: dict,
) -> None:
    assert generated["verdict"] == VERDICT
    assert generated["activation_readiness"] == READINESS_STATE
    assert generated["remaining_blockers"] == []
    boundary = generated["activation_boundary"]
    assert boundary["implementation_ready"] is True
    assert set(value for key, value in boundary.items() if key != "implementation_ready") == {False}


def test_readiness_record_tamper_and_activation_attempt_fail_closed(generated: dict) -> None:
    tampered = deepcopy(generated)
    tampered["controlled_replays"]["J13"]["source_feature_count"] += 1
    with pytest.raises(BuildingProductionVerificationError) as caught:
        verify_activation_readiness_record(tampered)
    assert caught.value.code == "readiness_record_tampered"

    activated = deepcopy(generated)
    activated["activation_boundary"]["production_active"] = True
    activated["canonical_record_sha256"] = activation_readiness_record_sha256(activated)
    with pytest.raises(BuildingProductionVerificationError) as caught:
        verify_activation_readiness_record(activated)
    assert caught.value.code == "activation_boundary_breached"


def test_readiness_canonical_hash_uses_frozen_core_provider(golden: dict) -> None:
    basis = deepcopy(golden)
    supplied = basis.pop("canonical_record_sha256")
    assert supplied == canonical_sha256(basis)

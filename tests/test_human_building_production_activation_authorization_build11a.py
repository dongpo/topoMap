from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator
import pytest

from build_contracts.human_building_production_activation_authorization import (
    AUTHORIZATION_DECISION,
    AUTHORIZATION_STATE,
    BUILD09F_POLICY_SHA256,
    BUILD10_IMPLEMENTATION_SHA256,
    BUILD11_ARTIFACT_SHA256,
    BUILD11_COMMIT,
    BUILD11_READINESS_FILE_SHA256,
    BUILD11_READINESS_SHA256,
    FINALIZED_CONTRACT_SHA256,
    POST_ACTIVATION_REQUIREMENTS,
    PRE_ACTIVATION_REQUIREMENTS,
    SOURCE_ARCHIVE_SHA256,
    VERDICT,
    HumanBuildingActivationAuthorizationError,
    authorization_record_sha256,
    build_authorization_record,
    validate_authorization_record,
)
from nma.core import canonical_sha256
from nma.real_layer import file_sha256


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = (
    ROOT
    / "data/specifications/nma-build-11a-golden-human-building-production-activation-authorization-v1.0.json"
)
SCHEMA = ROOT / "schemas/building-human-production-activation-authorization-v1.0.schema.json"
ALLOWED_BUILD11A_FILES = {
    "BUILD-11A-Completion-Report.md",
    "build_contracts/human_building_production_activation_authorization.py",
    "data/specifications/nma-build-11a-golden-human-building-production-activation-authorization-v1.0.json",
    "schemas/building-human-production-activation-authorization-v1.0.schema.json",
    "tests/test_human_building_production_activation_authorization_build11a.py",
}


@pytest.fixture(scope="session")
def generated() -> dict:
    return build_authorization_record(ROOT)


@pytest.fixture(scope="session")
def golden() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def _rehash(record: dict) -> None:
    record["canonical_authorization_sha256"] = authorization_record_sha256(record)


def _failure(record: dict) -> str:
    with pytest.raises(HumanBuildingActivationAuthorizationError) as caught:
        validate_authorization_record(record, ROOT)
    return caught.value.code


def test_deterministic_authorization_matches_golden_and_core_identity(
    generated: dict, golden: dict
) -> None:
    assert generated == golden
    assert validate_authorization_record(generated, ROOT) == generated
    basis = deepcopy(generated)
    supplied = basis.pop("canonical_authorization_sha256")
    assert supplied == canonical_sha256(basis) == authorization_record_sha256(generated)


def test_closed_draft_202012_schema_accepts_only_exact_record(generated: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(generated)
    changed = deepcopy(generated)
    changed["unexpected"] = True
    assert list(validator.iter_errors(changed))


def test_exact_build11_predecessor_and_readiness_identities(generated: dict) -> None:
    predecessor = generated["predecessor"]
    assert predecessor["build11_branch"] == (
        "build/build-11-controlled-building-production-verification"
    )
    assert predecessor["build11_commit"] == BUILD11_COMMIT
    assert predecessor["build11_readiness_canonical_sha256"] == BUILD11_READINESS_SHA256
    assert predecessor["build11_readiness_file_sha256"] == BUILD11_READINESS_FILE_SHA256
    assert predecessor["build11_verdict"] == (
        "PASS — CONTROLLED BUILDING PRODUCTION VERIFIED; HUMAN ACTIVATION GATE READY"
    )
    assert predecessor["build11_readiness_state"] == "READY-FOR-HUMAN-ACTIVATION-GATE"
    assert predecessor["build11_remaining_blockers"] == []


def test_exact_implementation_policy_contract_and_source_identities(generated: dict) -> None:
    predecessor = generated["predecessor"]
    assert predecessor["build10_implementation_identity"] == BUILD10_IMPLEMENTATION_SHA256
    assert predecessor["build09f_policy_identity"] == BUILD09F_POLICY_SHA256
    assert predecessor["finalized_production_contract_identity"] == FINALIZED_CONTRACT_SHA256
    assert predecessor["source_archive_identity"] == SOURCE_ARCHIVE_SHA256
    assert file_sha256(ROOT / "build_contracts/building_production_implementation.py") == (
        BUILD10_IMPLEMENTATION_SHA256
    )
    assert file_sha256(ROOT / "data/datasets/112年多維度SHP成果_0502.zip") == (
        SOURCE_ARCHIVE_SHA256
    )


def test_human_decision_authorizes_only_controlled_build12_activation(generated: dict) -> None:
    assert generated["authorization_decision"] == AUTHORIZATION_DECISION
    assert generated["authorization_state"] == AUTHORIZATION_STATE
    assert generated["verdict"] == VERDICT
    assert generated["next_stage"] == "BUILD-12"
    activation = generated["activation_authorization"]
    assert activation["controlled_production_activation_authorized"] is True
    assert activation["production_activation_allowed_for_build12"] is True
    assert activation["controlled_official_portrayal_activation_authorized"] is True
    assert activation["official_portrayal_activation_allowed_for_build12"] is True
    assert activation["activation_in_build11a_performed"] is False
    assert activation["automatic_activation_performed"] is False


def test_build11a_itself_remains_inactive_and_non_mutating(generated: dict) -> None:
    assert generated["current_state"] == {
        "official_portrayal_active": False,
        "production_active": False,
        "source_mutated": False,
    }
    assert generated["source_and_geometry_authority"] == {
        "non_writing_derivation_allowed_for_build12": True,
        "source_consumption_allowed_for_build12": True,
        "source_geometry_repair_allowed": False,
        "source_mutation_allowed": False,
        "source_writeback_allowed": False,
        "source_z_drop_allowed": False,
    }


def test_j13_and_j17_scope_are_exact_and_fail_closed(generated: dict) -> None:
    scope = generated["authorized_package_scope"]
    assert scope["j13"] == {
        "layer_identity": "J13_BUILD",
        "package_prefix": "J13",
        "package_scope": "J13_寶山都市計畫/SHP",
        "schema_identity_required": True,
    }
    assert scope["j17"] == {
        "layer_identity": "J17_BUILD",
        "package_prefix": "J17",
        "package_scope": "J17_新竹科學工業園區特定區計畫(寶山部分)/SHP",
        "schema_identity_required": True,
    }
    assert scope["automatic_cross_prefix_substitution_allowed"] is False
    assert scope["global_j13_j17_equivalence_authorized"] is False
    assert scope["unknown_package_activation_allowed"] is False
    assert scope["unverified_package_activation_allowed"] is False
    assert scope["mismatch_behavior"] == "fail-closed"


def test_seven_field_schema_and_polygonz_boundary_are_preserved(generated: dict) -> None:
    schema = generated["authorized_building_schema"]
    assert schema["field_count"] == 7
    assert [field["name"] for field in schema["fields"]] == [
        "BUILD_ID",
        "TERRAINID",
        "BUILD_STR",
        "BUILD_NO",
        "BUILD_H",
        "GROUP_ID",
        "MDATE",
    ]
    assert schema["schema_identity"] == (
        "3f9bdc1d88da286165c185dfae152b867e39cfb6308d17ffe7ff8c4aa79ffa76"
    )
    boundary = generated["polygonz_derived_xy_boundary"]
    assert boundary["pipeline"] == [
        "authoritative-PolygonZ",
        "non-writing-derived-XY",
        "portrayal-runtime",
    ]
    assert boundary["source_z_preserved_and_recoverable"] is True
    assert boundary["derived_xy_authoritative"] is False
    assert boundary["derived_xy_non_writing"] is True
    assert boundary["source_overwrite_allowed"] is False


def test_portrayal_and_output_profiles_are_exact_and_content_addressed(generated: dict) -> None:
    portrayal = deepcopy(generated["authorized_portrayal_profile"])
    portrayal_sha = portrayal.pop("portrayal_profile_sha256")
    assert portrayal_sha == canonical_sha256(portrayal)
    assert portrayal["contract_binding"] == FINALIZED_CONTRACT_SHA256
    assert portrayal["annotation"]["field_binding_rule"] == "{BUILD_NO}{BUILD_STR}"
    assert portrayal["hatch"]["hatch_resource_policy"] == "procedural-canonical"
    output = deepcopy(generated["authorized_output_profile"])
    output_sha = output.pop("output_profile_sha256")
    assert output_sha == canonical_sha256(output)
    assert output["profile_id"] == "nma-screen-96dpi-v1"
    assert output["output_dpi"] == 96
    assert output["hatch_spacing_mm"] == 2.0
    assert output["hatch_angle_degrees"] == 45
    assert output["line_width_mm"] == 0.2
    assert output["official_black_rgb"] == [0, 0, 0]
    assert output["device_colour_serialization"] == "#000000"
    assert output["opacity"] == 1.0


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("predecessor", "build10_implementation_identity"), "0" * 64),
        (("predecessor", "finalized_production_contract_identity"), "0" * 64),
        (("predecessor", "build09f_policy_identity"), "0" * 64),
        (("predecessor", "build11_readiness_canonical_sha256"), "0" * 64),
    ],
)
def test_bound_identity_drift_invalidates_even_rehashed_authorization(
    golden: dict, path: tuple[str, str], replacement: str
) -> None:
    changed = deepcopy(golden)
    changed[path[0]][path[1]] = replacement
    _rehash(changed)
    assert _failure(changed) == "authorization_mismatch"


def test_tampered_authorization_record_fails_without_repair(golden: dict) -> None:
    changed = deepcopy(golden)
    changed["current_state"]["production_active"] = True
    assert _failure(changed) == "authorization_hash_mismatch"


def test_pre_and_post_activation_verification_are_mandatory(generated: dict) -> None:
    pre = generated["pre_activation_verification"]
    assert pre["required"] is True
    assert pre["independent_reverification_by_build12_required"] is True
    assert pre["requirements"] == PRE_ACTIVATION_REQUIREMENTS
    assert pre["failure_behavior"] == "do-not-activate-fail-closed"
    post = generated["post_activation_verification"]
    assert post["required"] is True
    assert post["immediate"] is True
    assert post["requirements"] == POST_ACTIVATION_REQUIREMENTS
    assert post["failure_behavior"] == "fail-closed-and-deactivate-if-reversible"


def test_drift_and_rollback_requirements_are_mandatory(generated: dict) -> None:
    drift = generated["drift_invalidation"]
    assert drift["authorization_invalidated_by_any_drift"] is True
    assert drift["mismatch_behavior"] == "fail-closed"
    assert drift["auto_repair_allowed"] is False
    assert drift["reauthorization_by_inference_allowed"] is False
    assert set(drift["bound_fields"]) == {
        "activation-authorization-record",
        "build09f-policy",
        "build10-implementation",
        "build11-readiness-record",
        "building-schema",
        "core-identity-provider",
        "finalized-production-contract",
        "output-profile",
        "portrayal-contract",
        "source-package-identity",
    }
    rollback = generated["rollback_deactivation_requirement"]
    assert rollback["rollback_or_deactivation_path_required"] is True
    assert rollback["deactivate_on_failed_post_activation_verification_if_reversible"] is True
    assert rollback["source_data_rollback_required"] is False
    assert rollback["source_data_must_never_require_rollback"] is True


def test_authorization_cannot_target_any_stage_other_than_build12(golden: dict) -> None:
    changed = deepcopy(golden)
    changed["next_stage"] = "BUILD-13"
    _rehash(changed)
    assert _failure(changed) == "authorization_mismatch"


def test_closed_schema_rejects_every_forbidden_broadening(generated: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    mutations = [
        ("predecessor", "build11_commit", None),
        ("authorized_package_scope", "automatic_cross_prefix_substitution_allowed", True),
        ("authorized_package_scope", "global_j13_j17_equivalence_authorized", True),
        ("authorized_package_scope", "unknown_package_activation_allowed", True),
        ("source_and_geometry_authority", "source_mutation_allowed", True),
        ("source_and_geometry_authority", "source_geometry_repair_allowed", True),
        ("source_and_geometry_authority", "source_writeback_allowed", True),
        ("source_and_geometry_authority", "source_z_drop_allowed", True),
        ("current_state", "production_active", True),
        ("current_state", "official_portrayal_active", True),
        ("pre_activation_verification", "required", False),
        ("post_activation_verification", "required", False),
        ("drift_invalidation", "authorization_invalidated_by_any_drift", False),
        ("rollback_deactivation_requirement", "rollback_or_deactivation_path_required", False),
    ]
    for parent, key, value in mutations:
        changed = deepcopy(generated)
        if value is None:
            del changed[parent][key]
        else:
            changed[parent][key] = value
        assert list(validator.iter_errors(changed)), (parent, key)


def test_predecessor_build11_artifacts_remain_byte_identical(generated: dict) -> None:
    assert generated["predecessor"]["frozen_build11_artifact_sha256"] == (BUILD11_ARTIFACT_SHA256)
    assert {path: file_sha256(ROOT / path) for path in BUILD11_ARTIFACT_SHA256} == (
        BUILD11_ARTIFACT_SHA256
    )


def test_build11a_changed_file_scope_is_exact_and_production_sources_are_untouched() -> None:
    output = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, text=True
    )
    changed = {line[3:] for line in output.splitlines() if line}
    assert changed == ALLOWED_BUILD11A_FILES
    assert all(not path.startswith(("src/", "assets/", "data/datasets/")) for path in changed)
    assert "build_contracts/building_production_implementation.py" not in changed
    assert "build_contracts/building_production_verification.py" not in changed
    assert "src/nma/real_layer.py" not in changed

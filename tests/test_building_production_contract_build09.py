from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator, ValidationError
import pytest

import build_contracts.building_production_contract as build09
from build_contracts.building_production_contract import (
    BuildingProductionContractError,
    build_building_production_contract,
    building_production_contract_sha256,
    validate_building_production_contract,
)


ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR_SHA = "6e62481530228c76c250ff0e0119752c83f655a4"
AUTHORIZATION_SHA256 = "4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8"
CONTRACT_SHA256 = "0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c"
TEMPLATE_PATH = ROOT / "data/specifications/nma-build-07-golden-evaluation-template-v1.0.json"
EVALUATION_PATH = ROOT / "data/specifications/nma-build-07-accepted-user-evaluation-v1.0.json"
REVIEW_PATH = (
    ROOT / "data/specifications/nma-build-08-golden-official-production-entry-review-v1.0.json"
)
AUTHORIZATION_PATH = (
    ROOT
    / "data/specifications/nma-build-08a-golden-human-official-production-scope-authorization-v1.0.json"
)
CONTRACT_PATH = (
    ROOT / "data/specifications/nma-build-09-golden-building-production-contract-v1.0.json"
)
SCHEMA_PATH = ROOT / "schemas/building-production-contract-candidate-v1.0.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def template() -> dict:
    return _load(TEMPLATE_PATH)


@pytest.fixture()
def evaluation() -> dict:
    return _load(EVALUATION_PATH)


@pytest.fixture()
def review() -> dict:
    return _load(REVIEW_PATH)


@pytest.fixture()
def authorization() -> dict:
    return _load(AUTHORIZATION_PATH)


@pytest.fixture()
def contract() -> dict:
    return _load(CONTRACT_PATH)


def _validate(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> dict:
    return validate_building_production_contract(
        contract, authorization, review, template, evaluation
    )


def _rehash(contract: dict) -> dict:
    contract["contract_sha256"] = building_production_contract_sha256(contract)
    return contract


def _must_fail(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> BuildingProductionContractError:
    with pytest.raises(BuildingProductionContractError) as caught:
        _validate(contract, authorization, review, template, evaluation)
    return caught.value


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_contract_is_exactly_reproducible(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    actual = build_building_production_contract(authorization, review, template, evaluation)
    assert actual == contract
    assert actual["contract_sha256"] == CONTRACT_SHA256
    assert building_production_contract_sha256(actual) == CONTRACT_SHA256


def test_exact_build08a_predecessor_identity(contract: dict) -> None:
    predecessor = contract["predecessor"]
    assert (
        predecessor["build08a_branch"]
        == "build/build-08a-human-official-production-scope-resolution"
    )
    assert predecessor["build08a_completion_commit"] == PREDECESSOR_SHA
    assert (
        subprocess.check_output(
            [
                "git",
                "rev-parse",
                "refs/heads/build/build-08a-human-official-production-scope-resolution",
            ],
            cwd=ROOT,
            text=True,
        ).strip()
        == PREDECESSOR_SHA
    )


def test_exact_build08a_authorization_identity(contract: dict, authorization: dict) -> None:
    assert contract["predecessor"]["build08a_authorization_sha256"] == AUTHORIZATION_SHA256
    assert authorization["authorization_sha256"] == AUTHORIZATION_SHA256


def test_closed_draft_2020_12_schema_accepts_only_golden_contract(contract: dict) -> None:
    schema = _load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    Draft202012Validator(schema).validate(contract)
    changed = deepcopy(contract)
    changed["production_active"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(changed)


def test_all_five_inherited_gates_are_represented(contract: dict) -> None:
    assert [item["gate_id"] for item in contract["readiness"]] == build09.GATE_IDS
    assert len(contract["readiness"]) == 5


def test_j13_j17_result_is_evidence_driven_and_indeterminate(contract: dict) -> None:
    layer = contract["authoritative_source_layer_contract"]
    assert layer["resolution"] == "indeterminate"
    assert layer["selected_layer_id"] is None
    assert layer["logical_product_layer"] == "BUILD"
    assert [item["layer_id"] for item in layer["candidate_observations"]] == [
        "J13_BUILD",
        "J17_BUILD",
    ]
    assert all(
        item["authority_class"] == "reviewed-project-evidence"
        for item in layer["candidate_observations"]
    )
    assert layer["global_equivalence_assumed"] is False


def test_unsupported_j13_j17_forced_selection_fails(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    changed = deepcopy(contract)
    changed["authoritative_source_layer_contract"]["selected_layer_id"] = "J13_BUILD"
    _rehash(changed)
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "forced_layer_selection"
    )


def test_every_field_semantic_binding_is_explicit(contract: dict) -> None:
    expected = {
        "ID",
        "SOURCE",
        "MDATE",
        "BUILD_ID",
        "TERRAINID",
        "BUILD_NO",
        "BUILD_STR",
        "BUILD_H",
        "GROUP_ID",
    }
    fields = contract["field_semantic_bindings"]
    assert {item["field"] for item in fields} == expected
    assert all(item["documented_source_meaning"] for item in fields)
    assert all(item["nma_semantic_concept"] for item in fields)
    assert all(item["allowed_use"] for item in fields)
    assert all(item["production_implication"] for item in fields)


def test_undocumented_semantic_binding_fails(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    changed = deepcopy(contract)
    changed["field_semantic_bindings"][5]["documented_source_meaning"] = ""
    _rehash(changed)
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "field_semantics_undocumented"
    )


def test_annotation_content_binding_is_explicit(contract: dict) -> None:
    annotation = contract["annotation_contract"]
    assert annotation["content_semantics"]["value"] == "floor count followed by structure code"
    assert annotation["source_field_binding"]["fields"] == ["BUILD_NO", "BUILD_STR"]
    assert annotation["source_field_binding"]["format"] == "{BUILD_NO}{BUILD_STR}"
    assert annotation["runtime_rendering_responsibility"]["single_label_field_required"] is False
    assert (
        annotation["runtime_rendering_responsibility"]["current_null_label_field_reused"] is False
    )


def test_annotation_placement_authority_is_explicit(contract: dict) -> None:
    annotation = contract["annotation_contract"]
    assert annotation["status"] == "local-policy-candidate"
    assert annotation["placement_policy"]["authority_class"] == "local-policy-candidate"
    assert annotation["collision_suppression_policy"]["authority_class"] == "local-policy-candidate"


@pytest.mark.parametrize("authority_class", ["human-demo-evaluation", "implementation-evidence"])
def test_demo_or_implementation_alone_cannot_establish_official_portrayal(
    contract: dict,
    authorization: dict,
    review: dict,
    template: dict,
    evaluation: dict,
    authority_class: str,
) -> None:
    changed = deepcopy(contract)
    changed["portrayal_contract"]["properties"][0]["authority_class"] = authority_class
    changed["portrayal_contract"]["properties"][0]["support"] = "officially-supported"
    _rehash(changed)
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "portrayal_authority_escalation"
    )


def test_local_policy_candidates_are_explicitly_labeled(contract: dict) -> None:
    assert contract["local_policy_candidates"]
    candidates = [
        item
        for item in contract["portrayal_contract"]["properties"]
        if item["support"] == "local-policy-candidate"
    ]
    assert {item["authority_class"] for item in candidates} == {"local-policy-candidate"}
    angle = next(item for item in candidates if item["property"] == "hatch-angle-degrees")
    assert angle["value"] == 45.0
    assert "not official" in angle["production_note"]


def test_hatch_asset_and_resource_status_are_explicit(contract: dict) -> None:
    hatch = contract["hatch_resource_contract"]
    assert hatch["exact_asset_required"] is False
    assert (
        hatch["acceptable_implementation"]
        == "procedural-definition-or-independently-reviewed-equivalent-versioned-asset"
    )
    assert hatch["spacing_mm"] == 2.0
    assert hatch["spacing_authority_class"] == "authoritative-official"
    assert hatch["numeric_angle_authority_class"] == "local-policy-candidate"


def test_missing_hatch_asset_cannot_be_marked_deployable(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    assert not (ROOT / contract["hatch_resource_contract"]["current_candidate_asset"]).exists()
    changed = deepcopy(contract)
    changed["hatch_resource_contract"]["current_candidate_asset_deployable"] = True
    _rehash(changed)
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "missing_hatch_deployable"
    )


def test_polygonz_source_preservation_is_required(contract: dict) -> None:
    geometry = contract["geometry_contract"]
    boundary = contract["polygonz_derived_xy_contract"]
    assert geometry["authoritative_source_geometry"] == "PolygonZ"
    assert geometry["source_z_authoritative"] is True
    assert geometry["source_geometry_immutable"] is True
    assert boundary["source_representation"]["z_values_preserved_and_recoverable"] is True


def test_destructive_drop_z_contract_fails(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    changed = deepcopy(contract)
    changed["polygonz_derived_xy_contract"]["legacy_drop_z_path"]["reuse_as_is_allowed"] = True
    _rehash(changed)
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "destructive_drop_z"
    )


def test_derived_xy_must_be_non_writing(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    changed = deepcopy(contract)
    changed["polygonz_derived_xy_contract"]["derived_xy_representation"]["non_writing"] = False
    _rehash(changed)
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "derived_xy_writing"
    )


def test_source_mutation_remains_forbidden(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    assert all(value is False for value in contract["source_mutation_policy"].values())
    changed = deepcopy(contract)
    changed["source_mutation_policy"]["source_mutation_allowed"] = True
    _rehash(changed)
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "source_mutation_enabled"
    )


@pytest.mark.parametrize(
    "boundary", ["production_activation_allowed", "official_portrayal_activation_allowed"]
)
def test_production_and_official_portrayal_activation_remain_forbidden(
    contract: dict,
    authorization: dict,
    review: dict,
    template: dict,
    evaluation: dict,
    boundary: str,
) -> None:
    assert contract["runtime_activation_policy"][boundary] is False
    changed = deepcopy(contract)
    changed["runtime_activation_policy"][boundary] = True
    _rehash(changed)
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "activation_enabled"
    )


def test_unknown_evidence_class_fails(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    changed = deepcopy(contract)
    changed["evidence_references"][0]["authority_class"] = "invented-authority"
    _rehash(changed)
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "evidence_class_unknown"
    )


def test_unknown_readiness_state_fails(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    changed = deepcopy(contract)
    changed["readiness"][0]["classification"] = "P3-active"
    _rehash(changed)
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "readiness_state_unknown"
    )


def test_tampered_contract_identity_fails(
    contract: dict, authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    changed = deepcopy(contract)
    changed["contract_sha256"] = "0" * 64
    assert (
        _must_fail(changed, authorization, review, template, evaluation).code
        == "contract_hash_mismatch"
    )


def test_predecessor_build08a_remains_unchanged(contract: dict) -> None:
    predecessor = contract["predecessor"]
    assert _file_sha256(AUTHORIZATION_PATH) == predecessor["build08a_authorization_file_sha256"]
    assert (
        _file_sha256(ROOT / "BUILD-08A-Completion-Report.md")
        == "b1e0b7ce3936eaea5d27a448daa4c8d090be4c9fc11cd549c6091fff70d06d74"
    )


def test_build08_and_build07_frozen_identities_remain_unchanged(contract: dict) -> None:
    predecessor = contract["predecessor"]
    assert _file_sha256(REVIEW_PATH) == predecessor["build08_review_file_sha256"]
    assert _load(REVIEW_PATH)["review_sha256"] == predecessor["build08_review_sha256"]
    assert (
        _file_sha256(EVALUATION_PATH)
        == "7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d"
    )
    assert (
        _load(EVALUATION_PATH)["record_sha256"]
        == "ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c"
    )


def test_previous_build_frozen_artifacts_and_runtime_remain_unchanged() -> None:
    status = subprocess.check_output(
        ["git", "status", "--porcelain=v1"], cwd=ROOT, text=True
    ).splitlines()
    changed = {line[3:] for line in status}
    allowed = {
        "BUILD-09-Completion-Report.md",
        "build_contracts/building_production_contract.py",
        "data/specifications/nma-build-09-golden-building-production-contract-v1.0.json",
        "schemas/building-production-contract-candidate-v1.0.schema.json",
        "tests/test_building_production_contract_build09.py",
    }
    assert changed <= allowed
    assert not changed & {
        "src/nma/real_layer.py",
        "src/nma/portrayal_compile.py",
        "src/nma/maplibre_adapter.py",
        "data/datasets/112年多維度SHP成果_0502.zip",
        "data/specifications/nma-build-08a-golden-human-official-production-scope-authorization-v1.0.json",
        "data/specifications/nma-build-08-golden-official-production-entry-review-v1.0.json",
        "data/specifications/nma-build-07-accepted-user-evaluation-v1.0.json",
    }


def test_evidence_file_provenance_is_reproducible(contract: dict) -> None:
    for item in contract["evidence_references"]:
        assert _file_sha256(ROOT / item["path"]) == item["file_sha256"]


def test_contract_module_has_no_execution_or_filesystem_mutation_capability() -> None:
    source = inspect.getsource(build09)
    for forbidden in (
        "subprocess",
        "ogr2ogr",
        "ZipFile",
        "execute_real_layer",
        "open(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in source


def test_golden_contract_is_canonical_single_json_line(contract: dict) -> None:
    expected = (
        json.dumps(
            contract,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    assert CONTRACT_PATH.read_bytes() == expected

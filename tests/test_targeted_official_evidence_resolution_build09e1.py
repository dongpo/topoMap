from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator, ValidationError
import pytest

from build_contracts.targeted_official_evidence_resolution import (
    COLOUR_CODE_7_OUTCOMES,
    J13_J17_OUTCOMES,
    LINE_CODE_2_OUTCOMES,
    TargetedOfficialEvidenceResolutionError,
    build_successor_production_contract_candidate,
    build_targeted_official_evidence_resolution,
    successor_production_contract_sha256,
    targeted_official_evidence_resolution_sha256,
    validate_colour_code_7_resolution,
    validate_j13_j17_resolution,
    validate_line_code_2_resolution,
    validate_successor_production_contract_candidate,
    validate_targeted_official_evidence_resolution,
)


ROOT = Path(__file__).resolve().parents[1]
BUILD09E_PATH = (
    ROOT / "data/specifications/nma-build-09e-golden-official-evidence-closure-v1.0.json"
)
BUILD09_PATH = (
    ROOT / "data/specifications/nma-build-09-golden-building-production-contract-v1.0.json"
)
BUILD08A_PATH = (
    ROOT
    / "data/specifications/nma-build-08a-golden-human-official-production-scope-authorization-v1.0.json"
)
RECORD_PATH = (
    ROOT
    / "data/specifications/nma-build-09e1-golden-targeted-official-evidence-resolution-v1.0.json"
)
SUCCESSOR_PATH = (
    ROOT
    / "data/specifications/nma-build-09e1-successor-building-production-contract-candidate-v1.0.json"
)
SCHEMA_PATH = ROOT / "schemas/building-targeted-official-evidence-resolution-v1.0.schema.json"
SUCCESSOR_SCHEMA_PATH = (
    ROOT / "schemas/building-successor-production-contract-candidate-v1.0.schema.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture()
def build09e() -> dict:
    return _load(BUILD09E_PATH)


@pytest.fixture()
def build09() -> dict:
    return _load(BUILD09_PATH)


@pytest.fixture()
def build08a() -> dict:
    return _load(BUILD08A_PATH)


@pytest.fixture()
def record() -> dict:
    return _load(RECORD_PATH)


@pytest.fixture()
def successor() -> dict:
    return _load(SUCCESSOR_PATH)


def _rehash(record: dict) -> dict:
    record["targeted_official_evidence_resolution_sha256"] = (
        targeted_official_evidence_resolution_sha256(record)
    )
    return record


def _must_fail(record: dict, build09e: dict, build09: dict, build08a: dict) -> str:
    with pytest.raises(TargetedOfficialEvidenceResolutionError) as caught:
        validate_targeted_official_evidence_resolution(record, build09e, build09, build08a)
    return caught.value.code


def _trace(layer: str) -> dict:
    values = {
        "official_specification": "official specification",
        "specification_version": "version 1",
        "dataset_product_package": "bounded package",
        "geographic_product_scope": "bounded scope",
        "layer_code": layer,
        "layer_title_meaning": "Building",
        "geometry": "PolygonZ source",
        "field_schema": "BUILD_ID,TERRAINID,BUILD_STR,BUILD_NO,BUILD_H,GROUP_ID,MDATE",
        "building_semantic_role": "Building polygon",
        "nma_production_applicability": "bounded NMA production contract",
    }
    return {
        key: {"value": value, "evidence_ids": ["official-source"]} for key, value in values.items()
    }


def test_record_and_successor_are_exactly_reproducible(
    record: dict, successor: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    built = build_targeted_official_evidence_resolution(build09e, build09, build08a)
    assert built == record
    assert build_successor_production_contract_candidate(built, build09, build09e) == successor
    assert (
        record["targeted_official_evidence_resolution_sha256"]
        == "f75c44bcb834090277588b3c23cfe48f00e965c947754497f64831d4b47b9b65"
    )
    assert (
        successor["successor_production_contract_sha256"]
        == "e1bf4c251ae69739f3455c015ea7bac6b9de98742f3ebc2195da75adb2fc6cba"
    )


def test_exact_build09e_predecessor_identity(record: dict) -> None:
    predecessor = record["predecessor"]
    assert predecessor["build09e_branch"] == "build/build-09e-official-evidence-closure"
    assert predecessor["build09e_commit"] == "e46ea5eb10f6a177ab084d6ca8743c1011f4c1fd"
    actual = subprocess.check_output(
        ["git", "rev-parse", "refs/heads/build/build-09e-official-evidence-closure"],
        cwd=ROOT,
        text=True,
    ).strip()
    assert actual == predecessor["build09e_commit"]


def test_exact_build09e_evidence_closure_identity(record: dict, build09e: dict) -> None:
    expected = "bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed"
    assert record["predecessor"]["build09e_evidence_closure_sha256"] == expected
    assert build09e["official_evidence_closure_sha256"] == expected


def test_exact_build09_contract_identity(record: dict, build09: dict) -> None:
    expected = "0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c"
    assert record["predecessor"]["build09_contract_sha256"] == expected
    assert build09["contract_sha256"] == expected


def test_exact_build08a_authorization_identity(record: dict, build08a: dict) -> None:
    expected = "4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8"
    assert record["predecessor"]["build08a_authorization_sha256"] == expected
    assert build08a["authorization_sha256"] == expected


def test_closed_schemas_accept_exact_artifacts(record: dict, successor: dict) -> None:
    for path, artifact in ((SCHEMA_PATH, record), (SUCCESSOR_SCHEMA_PATH, successor)):
        schema = _load(path)
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False
        Draft202012Validator(schema).validate(artifact)
        changed = deepcopy(artifact)
        changed["production_active"] = True
        with pytest.raises(ValidationError):
            Draft202012Validator(schema).validate(changed)


def test_already_closed_annotation_findings_cannot_regress(
    record: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    annotation = record["frozen_build09e_results"]["annotation_closure"]
    assert annotation == build09e["annotation_closure"]
    assert annotation["content"] == {
        "outcome": "officially-supported",
        "rule": "floor count followed by structure",
    }
    assert annotation["placement"]["outcome"] == "local-policy-required"
    changed = deepcopy(record)
    changed["frozen_build09e_results"]["annotation_closure"]["placement"]["outcome"] = (
        "officially-supported"
    )
    _rehash(changed)
    assert _must_fail(changed, build09e, build09, build08a) == "frozen_finding_changed"


def test_two_mm_hatch_spacing_cannot_regress(
    record: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    assert record["frozen_build09e_results"]["hatch_spacing"] == {
        "outcome": "officially-supported",
        "unit": "mm",
        "value": 2.0,
    }
    changed = deepcopy(record)
    changed["frozen_build09e_results"]["hatch_spacing"]["value"] = 1.0
    _rehash(changed)
    assert _must_fail(changed, build09e, build09, build08a) == "frozen_finding_changed"


def test_45_degrees_cannot_become_official(
    record: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    angle = record["frozen_build09e_results"]["hatch_angle"]
    assert angle["value_degrees"] is None
    assert angle["outcome"] == "local-policy-required-with-official-diagonal-semantics"
    changed = deepcopy(record)
    changed["frozen_build09e_results"]["hatch_angle"]["value_degrees"] = 45.0
    _rehash(changed)
    assert _must_fail(changed, build09e, build09, build08a) == "frozen_finding_changed"


def test_polygonz_p2_cannot_regress(
    record: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    polygonz = record["frozen_build09e_results"]["polygonz_derived_xy"]
    assert polygonz == build09["polygonz_derived_xy_contract"]
    assert polygonz["source_representation"]["immutable"] is True
    assert polygonz["derived_xy_representation"]["non_writing"] is True
    changed = deepcopy(record)
    changed["frozen_build09e_results"]["polygonz_derived_xy"]["source_representation"][
        "immutable"
    ] = False
    _rehash(changed)
    assert _must_fail(changed, build09e, build09, build08a) == "frozen_finding_changed"


def test_j13_cannot_be_selected_from_demo_evidence() -> None:
    value = {
        "outcome": "J13-authoritative-production-binding",
        "selected_layer_id": "J13_BUILD",
        "authoritative_binding_traces": [
            {"authority_class": "demo-evidence", "trace": _trace("J13_BUILD")}
        ],
    }
    with pytest.raises(TargetedOfficialEvidenceResolutionError) as caught:
        validate_j13_j17_resolution(value)
    assert caught.value.code == "secondary_binding"


def test_j17_cannot_be_selected_from_runtime_implementation() -> None:
    value = {
        "outcome": "J17-authoritative-production-binding",
        "selected_layer_id": "J17_BUILD",
        "authoritative_binding_traces": [
            {"authority_class": "implementation-evidence", "trace": _trace("J17_BUILD")}
        ],
    }
    with pytest.raises(TargetedOfficialEvidenceResolutionError) as caught:
        validate_j13_j17_resolution(value)
    assert caught.value.code == "secondary_binding"


def test_j13_j17_version_scoped_binding_is_representable() -> None:
    value = {
        "outcome": "version-scoped-dual-binding",
        "selected_layer_id": None,
        "authoritative_binding_traces": [
            {
                "layer_id": "J13_BUILD",
                "authority_class": "authoritative-official-specification",
                "trace": _trace("J13_BUILD"),
            },
            {
                "layer_id": "J17_BUILD",
                "authority_class": "authoritative-official-specification",
                "trace": _trace("J17_BUILD"),
            },
        ],
    }
    validate_j13_j17_resolution(value)


def test_j13_j17_forced_equivalence_without_evidence_fails(record: dict) -> None:
    changed = deepcopy(record["j13_j17_resolution"])
    changed["forced_equivalence_authorized"] = True
    with pytest.raises(TargetedOfficialEvidenceResolutionError) as caught:
        validate_j13_j17_resolution(changed)
    assert caught.value.code == "forced_equivalence"


def test_official_binding_not_published_boundary_is_exact(record: dict) -> None:
    layer = record["j13_j17_resolution"]
    assert layer["outcome"] == "official-binding-not-published-or-not-available"
    assert layer["selected_layer_id"] is None
    assert layer["authoritative_binding_traces"] == []
    assert set(layer["available_product_trace"]) == {
        "official_specification",
        "specification_version",
        "dataset_product_package",
        "geographic_product_scope",
        "layer_code",
        "layer_title_meaning",
        "geometry",
        "field_schema",
        "building_semantic_role",
        "nma_production_applicability",
    }
    validate_j13_j17_resolution(layer)


def test_line_code_2_cannot_become_one_css_px(record: dict) -> None:
    changed = deepcopy(record["line_code_2_resolution"])
    changed["css_px"] = 1.0
    with pytest.raises(TargetedOfficialEvidenceResolutionError) as caught:
        validate_line_code_2_resolution(changed)
    assert caught.value.code == "unsupported_css_px"


def test_official_physical_width_preserves_source_unit(record: dict) -> None:
    line = record["line_code_2_resolution"]
    assert line["outcome"] == "official-physical-width-established"
    assert line["physical_width"] == {"value": 0.2, "value_text": "0.20", "unit": "mm"}
    assert line["css_px"] is None
    assert line["device_conversion_authorized"] is False


def test_official_symbolic_line_class_is_representable() -> None:
    validate_line_code_2_resolution(
        {
            "outcome": "official-symbolic-line-class",
            "official_code": "2",
            "official_symbolic_name": "official medium line",
            "physical_width": None,
            "css_px": None,
        }
    )


def test_official_code_output_profile_boundary_is_representable() -> None:
    validate_line_code_2_resolution(
        {
            "outcome": "official-code-output-profile-dependent",
            "official_code": "2",
            "physical_width": None,
            "css_px": None,
            "output_profile_dependency": "official output profile selects device width",
        }
    )
    validate_colour_code_7_resolution(
        {
            "outcome": "official-code-output-profile-dependent",
            "official_code": "7",
            "original_representation": None,
            "official_hex": None,
            "output_profile_dependency": "official output profile selects device colour",
        }
    )


def test_colour_code_7_device_value_preserves_original_representation(record: dict) -> None:
    colour = record["colour_code_7_resolution"]
    assert colour["outcome"] == "official-device-value-established"
    assert colour["semantic_name"] == "黑色"
    assert colour["original_representation"] == {
        "components": [0, 0, 0],
        "representation": "RGB值 (R-G-B)",
        "value_text": "(0,0,0)",
    }
    assert colour["official_hex"] is None


def test_semantic_black_does_not_imply_rgb_or_hex() -> None:
    value = {
        "outcome": "official-semantic-black",
        "official_code": "7",
        "semantic_name": "black",
        "original_representation": None,
        "official_hex": None,
    }
    validate_colour_code_7_resolution(value)


@pytest.mark.parametrize("unsupported", ["#000000", "#111111"])
def test_hex_value_cannot_be_claimed_official_without_hex_evidence(unsupported: str) -> None:
    value = {
        "outcome": "official-semantic-black",
        "official_code": "7",
        "semantic_name": "black",
        "original_representation": None,
        "official_hex": unsupported,
    }
    with pytest.raises(TargetedOfficialEvidenceResolutionError) as caught:
        validate_colour_code_7_resolution(value)
    assert caught.value.code == "unsupported_official_hex"


def test_local_output_profile_requirement_is_explicit(record: dict) -> None:
    profile = record["output_profile_requirement"]
    assert profile["status"] == "local-output-profile-policy-required"
    assert profile["required"] is True
    assert profile["pipeline"] == [
        "official-portrayal-semantics",
        "authorized-local-output-profile",
        "MapLibre-device-representation",
    ]
    assert profile["local_values_selected"] is False


def test_absent_device_mapping_can_close_official_boundary() -> None:
    value = {
        "outcome": "official-code-output-profile-dependent",
        "official_code": "2",
        "physical_width": None,
        "css_px": None,
        "output_profile_dependency": "device width is intentionally profile-defined",
    }
    validate_line_code_2_resolution(value)
    assert value["outcome"] != "indeterminate"


def test_portrayal_closed_but_j13_j17_still_blocks(record: dict) -> None:
    assert record["build10_readiness"] == "J13-J17-BINDING-STILL-BLOCKING"
    assert (
        record["verdict"]
        == "PASS — PORTRAYAL EVIDENCE CLOSED; J13/J17 PRODUCTION BINDING STILL MISSING"
    )
    assert record["remaining_authoritative_evidence_gaps"] == [
        "versioned J13/J17 package-member production applicability binding"
    ]


def test_production_activation_remains_forbidden(
    record: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    assert record["runtime_activation_policy"]["production_activation_allowed"] is False
    changed = deepcopy(record)
    changed["runtime_activation_policy"]["production_activation_allowed"] = True
    _rehash(changed)
    assert _must_fail(changed, build09e, build09, build08a) == "activation_enabled"


def test_official_portrayal_activation_remains_forbidden(
    record: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    assert record["runtime_activation_policy"]["official_portrayal_activation_allowed"] is False
    changed = deepcopy(record)
    changed["runtime_activation_policy"]["official_portrayal_activation_allowed"] = True
    _rehash(changed)
    assert _must_fail(changed, build09e, build09, build08a) == "activation_enabled"


def test_source_mutation_remains_forbidden(
    record: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    assert record["source_mutation_policy"]["source_mutation_allowed"] is False
    changed = deepcopy(record)
    changed["source_mutation_policy"]["source_mutation_allowed"] = True
    _rehash(changed)
    assert _must_fail(changed, build09e, build09, build08a) == "source_mutation_enabled"


def test_destructive_z_removal_remains_forbidden(
    record: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    assert record["source_mutation_policy"]["source_z_dimension_removal_allowed"] is False
    changed = deepcopy(record)
    changed["source_mutation_policy"]["source_z_dimension_removal_allowed"] = True
    _rehash(changed)
    assert _must_fail(changed, build09e, build09, build08a) == "source_mutation_enabled"


@pytest.mark.parametrize(
    ("validator", "value"),
    [
        (validate_j13_j17_resolution, {"outcome": "unknown"}),
        (validate_line_code_2_resolution, {"outcome": "unknown", "official_code": "2"}),
        (validate_colour_code_7_resolution, {"outcome": "unknown", "official_code": "7"}),
    ],
)
def test_unknown_evidence_states_fail(validator, value: dict) -> None:
    with pytest.raises(TargetedOfficialEvidenceResolutionError):
        validator(value)


def test_tampered_evidence_record_fails(
    record: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    changed = deepcopy(record)
    changed["evidence_items"][2]["claim"] = "tampered"
    assert _must_fail(changed, build09e, build09, build08a) == "resolution_hash_mismatch"
    _rehash(changed)
    assert _must_fail(changed, build09e, build09, build08a) == "record_mismatch"


def test_successor_is_bound_and_non_activating(
    successor: dict, record: dict, build09e: dict, build09: dict
) -> None:
    assert successor["status"] == "evidence-hold"
    assert successor["bindings"] == {
        "build09_contract_sha256": "0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c",
        "build09e_evidence_closure_sha256": "bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed",
        "build09e1_evidence_resolution_sha256": record[
            "targeted_official_evidence_resolution_sha256"
        ],
    }
    assert successor["production_activation_forbidden"] is True
    assert successor["official_portrayal_activation_forbidden"] is True
    assert successor["polygonz_derived_xy_contract"] == build09["polygonz_derived_xy_contract"]
    validate_successor_production_contract_candidate(successor, record, build09, build09e)


def test_production_active_successor_fails(
    successor: dict, record: dict, build09e: dict, build09: dict
) -> None:
    changed = deepcopy(successor)
    changed["status"] = "production-active"
    changed["successor_production_contract_sha256"] = successor_production_contract_sha256(changed)
    with pytest.raises(TargetedOfficialEvidenceResolutionError) as caught:
        validate_successor_production_contract_candidate(changed, record, build09, build09e)
    assert caught.value.code == "activation_enabled"


def test_predecessor_build_artifacts_remain_unchanged(record: dict) -> None:
    for relative, expected in record["predecessor"]["frozen_build09e_artifact_sha256"].items():
        assert _sha256(ROOT / relative) == expected


def test_all_required_closed_vocabularies_are_exact(record: dict) -> None:
    vocab = record["closed_vocabularies"]
    assert vocab["j13_j17_outcomes"] == J13_J17_OUTCOMES
    assert vocab["line_code_2_outcomes"] == LINE_CODE_2_OUTCOMES
    assert vocab["colour_code_7_outcomes"] == COLOUR_CODE_7_OUTCOMES

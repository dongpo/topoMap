from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator, ValidationError
import pytest

import build_contracts.official_evidence_closure as build09e
from build_contracts.official_evidence_closure import (
    OfficialEvidenceClosureError,
    build_official_evidence_closure,
    official_evidence_closure_sha256,
    validate_layer_resolution,
    validate_official_evidence_closure,
)


ROOT = Path(__file__).resolve().parents[1]
BUILD09_PATH = (
    ROOT / "data/specifications/nma-build-09-golden-building-production-contract-v1.0.json"
)
BUILD08A_PATH = (
    ROOT
    / "data/specifications/nma-build-08a-golden-human-official-production-scope-authorization-v1.0.json"
)
RECORD_PATH = ROOT / "data/specifications/nma-build-09e-golden-official-evidence-closure-v1.0.json"
SCHEMA_PATH = ROOT / "schemas/building-official-evidence-closure-v1.0.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture()
def build09() -> dict:
    return _load(BUILD09_PATH)


@pytest.fixture()
def build08a() -> dict:
    return _load(BUILD08A_PATH)


@pytest.fixture()
def record() -> dict:
    return _load(RECORD_PATH)


def _rehash(record: dict) -> dict:
    record["official_evidence_closure_sha256"] = official_evidence_closure_sha256(record)
    return record


def _must_fail(record: dict, build09: dict, build08a: dict) -> OfficialEvidenceClosureError:
    with pytest.raises(OfficialEvidenceClosureError) as caught:
        validate_official_evidence_closure(record, build09, build08a)
    return caught.value


def _trace(authority: str = "NLSC versioned specification") -> dict[str, str]:
    return {
        "official-specification/version": authority,
        "layer-code": "J13_BUILD",
        "layer-meaning": "Building polygon in the named product/version",
        "geometry-type": "PolygonZ source; Polygon portrayal role",
        "field-set": "BUILD_ID,TERRAINID,BUILD_STR,BUILD_NO,BUILD_H,GROUP_ID,MDATE",
        "dataset-version": "bounded-version-1",
        "NMA-production-contract": "bounded Building contract",
    }


def test_record_is_exactly_reproducible(record: dict, build09: dict, build08a: dict) -> None:
    assert build_official_evidence_closure(build09, build08a) == record
    assert (
        record["official_evidence_closure_sha256"]
        == "bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed"
    )


def test_exact_build09_predecessor_identity(record: dict) -> None:
    predecessor = record["predecessor"]
    assert predecessor["build09_branch"] == "build/build-09-official-building-production-contract"
    assert predecessor["build09_commit"] == "23b4f042ee14934b01d6215277e3e0881767a580"
    actual = subprocess.check_output(
        ["git", "rev-parse", "refs/heads/build/build-09-official-building-production-contract"],
        cwd=ROOT,
        text=True,
    ).strip()
    assert actual == predecessor["build09_commit"]


def test_exact_build09_contract_identity(record: dict, build09: dict) -> None:
    predecessor = record["predecessor"]
    assert build09["contract_sha256"] == predecessor["build09_contract_sha256"]
    assert _sha256(BUILD09_PATH) == predecessor["build09_contract_file_sha256"]


def test_exact_build08a_authorization_identity(record: dict, build08a: dict) -> None:
    predecessor = record["predecessor"]
    assert build08a["authorization_sha256"] == predecessor["build08a_authorization_sha256"]
    assert _sha256(BUILD08A_PATH) == predecessor["build08a_authorization_file_sha256"]


def test_closed_draft_2020_12_schema_accepts_record(record: dict) -> None:
    schema = _load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    Draft202012Validator(schema).validate(record)
    changed = deepcopy(record)
    changed["production_active"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(changed)


def test_polygonz_p2_boundary_is_preserved(record: dict, build09: dict) -> None:
    assert record["polygonz_derived_xy_preservation"] == build09["polygonz_derived_xy_contract"]
    gate = {item["gate_id"]: item for item in record["readiness"]}
    assert gate["j13-polygonz-runtime-policy"]["state"] == "P2-production-candidate"
    assert (
        record["polygonz_derived_xy_preservation"]["source_representation"][
            "z_values_preserved_and_recoverable"
        ]
        is True
    )
    assert (
        record["polygonz_derived_xy_preservation"]["derived_xy_representation"]["non_writing"]
        is True
    )


def test_changed_polygonz_boundary_fails(record: dict, build09: dict, build08a: dict) -> None:
    changed = deepcopy(record)
    changed["polygonz_derived_xy_preservation"]["source_representation"]["immutable"] = False
    _rehash(changed)
    assert _must_fail(changed, build09, build08a).code == "polygonz_boundary_changed"


def test_j13_j17_selection_cannot_occur_without_authoritative_trace(record: dict) -> None:
    changed = deepcopy(record["j13_j17_closure"])
    changed["outcome"] = "J13-authoritative-production-candidate"
    changed["selected_layer_id"] = "J13_BUILD"
    with pytest.raises(OfficialEvidenceClosureError) as caught:
        validate_layer_resolution(changed)
    assert caught.value.code == "layer_selection_without_trace"


def test_complete_single_layer_authoritative_trace_is_supported(record: dict) -> None:
    changed = deepcopy(record["j13_j17_closure"])
    changed["outcome"] = "J13-authoritative-production-candidate"
    changed["selected_layer_id"] = "J13_BUILD"
    changed["authoritative_traces"] = [_trace()]
    validate_layer_resolution(changed)


def test_version_scoped_j13_j17_contracts_are_supported(record: dict) -> None:
    j13_trace = _trace()
    j17_trace = _trace()
    j17_trace["layer-code"] = "J17_BUILD"
    j17_trace["dataset-version"] = "bounded-version-2"
    changed = deepcopy(record["j13_j17_closure"])
    changed["outcome"] = "version-scoped-dual-contract-required"
    changed["version_contracts"] = [
        {"layer_id": "J13_BUILD", "authoritative_trace": j13_trace},
        {"layer_id": "J17_BUILD", "authoritative_trace": j17_trace},
    ]
    validate_layer_resolution(changed)


def test_annotation_components_have_separate_authority_classes(record: dict) -> None:
    annotation = record["annotation_closure"]
    assert annotation["content"]["outcome"] == "officially-supported"
    assert annotation["field_binding"]["outcome"] == "documented-source-semantics"
    assert annotation["placement"]["outcome"] == "local-policy-required"
    assert annotation["collision_suppression"]["outcome"] == "local-policy-required"


def test_missing_official_placement_is_local_policy_not_fabricated(record: dict) -> None:
    placement = record["annotation_closure"]["placement"]
    assert placement["outcome"] == "local-policy-required"
    assert placement["unofficial_detail"] == "exact anchor algorithm"


def test_hatch_spacing_and_angle_are_independent(record: dict) -> None:
    hatch = record["hatch_closure"]
    assert hatch["spacing"] == {"outcome": "officially-supported", "value": 2.0, "unit": "mm"}
    assert hatch["angle"]["outcome"] == "local-policy-required-with-official-diagonal-semantics"
    assert hatch["angle"]["value_degrees"] is None


def test_diagonal_semantics_cannot_become_45_degrees(
    record: dict, build09: dict, build08a: dict
) -> None:
    changed = deepcopy(record)
    changed["hatch_closure"]["angle"]["value_degrees"] = 45.0
    _rehash(changed)
    assert _must_fail(changed, build09, build08a).code == "unsupported_angle_conversion"


def test_hatch_resource_is_not_created_or_deployed(record: dict) -> None:
    resource = record["hatch_closure"]["resource"]
    assert resource["outcome"] == "local-policy-required"
    assert resource["exact_asset_required"] is False
    assert resource["created_or_deployed"] is False


def test_line_code_2_cannot_become_one_css_px(record: dict, build09: dict, build08a: dict) -> None:
    changed = deepcopy(record)
    changed["line_color_closure"]["line_code_2"]["css_px"] = 1.0
    _rehash(changed)
    assert _must_fail(changed, build09, build08a).code == "unsupported_line_conversion"


def test_colour_code_7_cannot_become_number_111111(
    record: dict, build09: dict, build08a: dict
) -> None:
    changed = deepcopy(record)
    changed["line_color_closure"]["colour_code_7"]["rgb_hex"] = "#111111"
    _rehash(changed)
    assert _must_fail(changed, build09, build08a).code == "unsupported_color_conversion"


def test_official_physical_units_are_preserved_without_conversion(record: dict) -> None:
    line = record["line_color_closure"]
    assert line["line_code_2"]["official_unit_system"] == "mm"
    assert line["line_code_2"]["physical_width"] is None
    assert line["rendering_conversion"]["physical_units_must_be_preserved"] is True
    assert line["rendering_conversion"]["documented_conversion_rule"] is None


def test_authority_conflict_cannot_silently_resolve(
    record: dict, build09: dict, build08a: dict
) -> None:
    changed = deepcopy(record)
    changed["conflicting_authoritative_evidence"] = ["version A conflicts with version B"]
    _rehash(changed)
    assert _must_fail(changed, build09, build08a).code == "authority_conflict_silenced"


@pytest.mark.parametrize(
    "authority", ["demo-evidence", "human-demo-evaluation", "implementation-evidence"]
)
def test_secondary_evidence_cannot_promote_a_layer(authority: str) -> None:
    layer = {
        "outcome": "J13-authoritative-production-candidate",
        "selected_layer_id": "J13_BUILD",
        "authoritative_traces": [_trace(authority)],
        "version_contracts": [],
    }
    with pytest.raises(OfficialEvidenceClosureError) as caught:
        validate_layer_resolution(layer)
    assert caught.value.code == "secondary_evidence_promotion"


def test_local_policy_required_is_explicit(record: dict) -> None:
    assert record["local_policy_required"]
    assert {item["state"] for item in record["readiness"]} >= {"local-policy-required"}


@pytest.mark.parametrize(
    "boundary", ["production_activation_allowed", "official_portrayal_activation_allowed"]
)
def test_production_and_official_portrayal_activation_remain_forbidden(
    record: dict, build09: dict, build08a: dict, boundary: str
) -> None:
    assert record["runtime_activation_policy"][boundary] is False
    changed = deepcopy(record)
    changed["runtime_activation_policy"][boundary] = True
    _rehash(changed)
    assert _must_fail(changed, build09, build08a).code == "activation_enabled"


@pytest.mark.parametrize(
    "boundary", ["source_mutation_allowed", "source_z_dimension_removal_allowed"]
)
def test_source_mutation_and_destructive_z_removal_remain_forbidden(
    record: dict, build09: dict, build08a: dict, boundary: str
) -> None:
    assert record["source_mutation_policy"][boundary] is False
    changed = deepcopy(record)
    changed["source_mutation_policy"][boundary] = True
    _rehash(changed)
    assert _must_fail(changed, build09, build08a).code == "source_mutation_enabled"


def test_build09_artifacts_remain_unchanged(record: dict) -> None:
    assert _sha256(BUILD09_PATH) == record["predecessor"]["build09_contract_file_sha256"]
    assert (
        _sha256(ROOT / "BUILD-09-Completion-Report.md")
        == "eb1d2dc8ee93d68ba105c8ff6d9e4b28e59a69b0b65d4c7b3178b7e1415c168e"
    )


def test_build08a_build08_and_build07_identities_remain_unchanged(record: dict) -> None:
    predecessor = record["predecessor"]
    assert _sha256(BUILD08A_PATH) == predecessor["build08a_authorization_file_sha256"]
    assert (
        _sha256(
            ROOT
            / "data/specifications/nma-build-08-golden-official-production-entry-review-v1.0.json"
        )
        == predecessor["build08_review_file_sha256"]
    )
    assert (
        _sha256(ROOT / "data/specifications/nma-build-07-accepted-user-evaluation-v1.0.json")
        == predecessor["build07_record_file_sha256"]
    )


def test_tampered_evidence_identity_fails(record: dict, build09: dict, build08a: dict) -> None:
    changed = deepcopy(record)
    changed["official_evidence_closure_sha256"] = "0" * 64
    assert _must_fail(changed, build09, build08a).code == "closure_hash_mismatch"


def test_unknown_authority_value_fails(record: dict, build09: dict, build08a: dict) -> None:
    changed = deepcopy(record)
    changed["evidence_items"][0]["authority_class"] = "invented-authority"
    _rehash(changed)
    assert _must_fail(changed, build09, build08a).code == "authority_state_unknown"


def test_unknown_readiness_value_fails(record: dict, build09: dict, build08a: dict) -> None:
    changed = deepcopy(record)
    changed["readiness"][0]["state"] = "P3-production-active"
    _rehash(changed)
    assert _must_fail(changed, build09, build08a).code == "authority_state_unknown"


def test_all_evidence_items_record_required_provenance(record: dict) -> None:
    required = {
        "source",
        "version_date",
        "provenance",
        "authority_class",
        "claim",
        "confidence",
        "conflicts",
        "identity",
    }
    assert all(required <= set(item) for item in record["evidence_items"])


def test_no_successor_contract_is_created_while_semantics_are_missing(record: dict) -> None:
    assert record["successor_production_contract"]["created"] is False
    assert record["successor_production_contract"]["sha256"] is None
    assert record["build10_readiness_decision"] == "OFFICIAL-EVIDENCE-STILL-MISSING"


def test_previous_artifacts_runtime_and_source_scope_remain_unchanged() -> None:
    status = subprocess.check_output(
        ["git", "status", "--porcelain=v1"], cwd=ROOT, text=True
    ).splitlines()
    changed = {line[3:] for line in status}
    allowed = {
        "BUILD-09E-Completion-Report.md",
        "build_contracts/official_evidence_closure.py",
        "data/specifications/nma-build-09e-golden-official-evidence-closure-v1.0.json",
        "schemas/building-official-evidence-closure-v1.0.schema.json",
        "tests/test_official_evidence_closure_build09e.py",
    }
    assert changed <= allowed
    assert not any(path.startswith(("src/", "data/datasets/")) for path in changed)


def test_builder_has_no_runtime_or_filesystem_mutation_capability() -> None:
    source = inspect.getsource(build09e)
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


def test_golden_record_is_canonical_single_json_line(record: dict) -> None:
    expected = (
        json.dumps(
            record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        + b"\n"
    )
    assert RECORD_PATH.read_bytes() == expected

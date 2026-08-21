from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator, ValidationError
import pytest

from build_contracts.j13_j17_production_applicability import (
    APPLICABILITY_OUTCOMES,
    J13J17ProductionApplicabilityError,
    TRACE_EDGES,
    applicability_resolution_sha256,
    build_applicability_resolution,
    build_successor_contract,
    successor_contract_sha256,
    validate_applicability_outcome,
    validate_applicability_resolution,
    validate_successor_contract,
)


ROOT = Path(__file__).resolve().parents[1]
BUILD09E1_PATH = (
    ROOT
    / "data/specifications/nma-build-09e1-golden-targeted-official-evidence-resolution-v1.0.json"
)
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
    / "data/specifications/nma-build-09e2-golden-j13-j17-production-applicability-resolution-v1.0.json"
)
SUCCESSOR_PATH = (
    ROOT / "data/specifications/nma-build-09e2-successor-building-production-contract-v1.0.json"
)
SCHEMA_PATH = ROOT / "schemas/building-j13-j17-production-applicability-resolution-v1.0.schema.json"
SUCCESSOR_SCHEMA_PATH = ROOT / "schemas/building-human-policy-production-contract-v1.0.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture()
def build09e1() -> dict:
    return _load(BUILD09E1_PATH)


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


def _rehash(value: dict) -> dict:
    value["applicability_resolution_sha256"] = applicability_resolution_sha256(value)
    return value


def _must_fail(value: dict, build09e1: dict, build09e: dict, build09: dict, build08a: dict) -> str:
    with pytest.raises(J13J17ProductionApplicabilityError) as caught:
        validate_applicability_resolution(value, build09e1, build09e, build09, build08a)
    return caught.value.code


def _complete_binding_trace(layer_id: str) -> dict:
    return {
        "layer_id": layer_id,
        "authority_class": "authoritative-official-specification",
        "trace": {
            name: {
                "status": "established",
                "value": f"official {name}",
                "evidence_ids": ["official-source"],
            }
            for name in TRACE_EDGES
        },
        "missing_edges": [],
    }


def test_record_and_successor_are_exactly_reproducible(
    record: dict,
    successor: dict,
    build09e1: dict,
    build09e: dict,
    build09: dict,
    build08a: dict,
) -> None:
    built = build_applicability_resolution(build09e1, build09e, build09, build08a)
    assert built == record
    assert build_successor_contract(built, build09e1, build09) == successor
    assert record["applicability_resolution_sha256"] == (
        "1a4a406da130eb34a7f6871e92230d0c82fe4bcf9e475651418780bedd5d1262"
    )
    assert successor["successor_contract_sha256"] == (
        "71b7f25239eb001454af61358acb67917d9820957ea4aeb2191ff613ee54a043"
    )


def test_exact_build09e1_predecessor_sha(record: dict) -> None:
    expected = "ee4bbc1bf4dc5d70032dcd3129801039f3813a36"
    assert record["predecessor"]["build09e1_commit"] == expected
    actual = subprocess.check_output(
        [
            "git",
            "rev-parse",
            "refs/heads/build/build-09e1-targeted-official-binding-portrayal-resolution",
        ],
        cwd=ROOT,
        text=True,
    ).strip()
    assert actual == expected


@pytest.mark.parametrize(
    ("key", "path", "identity_key", "expected"),
    [
        (
            "build09_contract_sha256",
            BUILD09_PATH,
            "contract_sha256",
            "0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c",
        ),
        (
            "build09e_evidence_closure_sha256",
            BUILD09E_PATH,
            "official_evidence_closure_sha256",
            "bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed",
        ),
        (
            "build08a_authorization_sha256",
            BUILD08A_PATH,
            "authorization_sha256",
            "4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8",
        ),
        (
            "build09e1_evidence_resolution_sha256",
            BUILD09E1_PATH,
            "targeted_official_evidence_resolution_sha256",
            "f75c44bcb834090277588b3c23cfe48f00e965c947754497f64831d4b47b9b65",
        ),
    ],
)
def test_exact_predecessor_evidence_identities(
    record: dict, key: str, path: Path, identity_key: str, expected: str
) -> None:
    assert record["predecessor"][key] == expected
    assert _load(path)[identity_key] == expected


def test_closed_schemas_accept_only_closed_artifacts(record: dict, successor: dict) -> None:
    for schema_path, artifact in ((SCHEMA_PATH, record), (SUCCESSOR_SCHEMA_PATH, successor)):
        schema = _load(schema_path)
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False
        Draft202012Validator(schema).validate(artifact)
        changed = deepcopy(artifact)
        changed["unexpected"] = True
        with pytest.raises(ValidationError):
            Draft202012Validator(schema).validate(changed)


def test_line_code_2_remains_exactly_point_two_mm(record: dict) -> None:
    line = record["frozen_non_j13_j17_findings"]["line_code_2_resolution"]
    assert line["official_code"] == "2"
    assert line["physical_width"] == {"unit": "mm", "value": 0.2, "value_text": "0.20"}


def test_no_css_pixel_mapping_is_introduced(record: dict) -> None:
    line = record["frozen_non_j13_j17_findings"]["line_code_2_resolution"]
    assert line["css_px"] is None
    assert line["device_conversion_authorized"] is False


def test_colour_code_7_remains_official_black_rgb(record: dict) -> None:
    colour = record["frozen_non_j13_j17_findings"]["colour_code_7_resolution"]
    assert colour["official_code"] == "7"
    assert colour["semantic_name"] == "黑色"
    assert colour["original_representation"] == {
        "components": [0, 0, 0],
        "representation": "RGB值 (R-G-B)",
        "value_text": "(0,0,0)",
    }


def test_no_official_hex_mapping_is_invented(record: dict) -> None:
    assert record["frozen_non_j13_j17_findings"]["colour_code_7_resolution"]["official_hex"] is None


def test_annotation_evidence_does_not_regress(
    record: dict, build09e1: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    annotation = record["frozen_non_j13_j17_findings"]["annotation_closure"]
    assert annotation["content"] == {
        "outcome": "officially-supported",
        "rule": "floor count followed by structure",
    }
    changed = deepcopy(record)
    changed["frozen_non_j13_j17_findings"]["annotation_closure"]["content"]["rule"] = "changed"
    _rehash(changed)
    assert _must_fail(changed, build09e1, build09e, build09, build08a) == "frozen_finding_changed"


def test_hatch_evidence_does_not_regress(
    record: dict, build09e1: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    frozen = record["frozen_non_j13_j17_findings"]
    assert frozen["hatch_spacing"] == {
        "outcome": "officially-supported",
        "unit": "mm",
        "value": 2.0,
    }
    assert frozen["hatch_angle"]["value_degrees"] is None
    assert frozen["hatch_resource"]["created_or_deployed"] is False
    changed = deepcopy(record)
    changed["frozen_non_j13_j17_findings"]["hatch_angle"]["value_degrees"] = 45.0
    _rehash(changed)
    assert _must_fail(changed, build09e1, build09e, build09, build08a) == "frozen_finding_changed"


def test_polygonz_p2_does_not_regress(record: dict, build09: dict) -> None:
    polygonz = record["frozen_non_j13_j17_findings"]["polygonz_derived_xy"]
    assert polygonz == build09["polygonz_derived_xy_contract"]
    assert polygonz["source_representation"]["immutable"] is True
    assert polygonz["source_representation"]["z_values_preserved_and_recoverable"] is True
    assert polygonz["derived_xy_representation"]["authoritative"] is False
    assert polygonz["derived_xy_representation"]["non_writing"] is True
    assert polygonz["legacy_drop_z_path"]["classification"] == "incompatible"


@pytest.mark.parametrize(
    ("outcome", "layer_id", "authority_class"),
    [
        ("J13-authoritative-production-binding", "J13_BUILD", "demo-evidence"),
        ("J17-authoritative-production-binding", "J17_BUILD", "implementation-evidence"),
    ],
)
def test_demo_and_runtime_usage_cannot_establish_authority(
    outcome: str, layer_id: str, authority_class: str
) -> None:
    trace = _complete_binding_trace(layer_id)
    trace["authority_class"] = authority_class
    with pytest.raises(J13J17ProductionApplicabilityError) as caught:
        validate_applicability_outcome(
            {
                "outcome": outcome,
                "selected_layer_id": layer_id,
                "authoritative_binding_traces": [trace],
            }
        )
    assert caught.value.code == "secondary_binding"


def test_layer_existence_does_not_imply_production_applicability(record: dict) -> None:
    claims = record["claim_separation"]
    assert claims["layer_existence"] == "established"
    assert claims["production_applicability"] == "not-published"
    assert claims["existence_implies_applicability"] is False


def test_semantic_similarity_does_not_imply_equivalence(record: dict) -> None:
    claims = record["claim_separation"]
    assert claims["layer_semantics"].startswith("established")
    assert claims["semantic_similarity_implies_equivalence"] is False
    assert record["authoritative_applicability_resolution"]["selected_layer_id"] is None


def test_independent_j13_j17_traces_are_complete_except_applicability(record: dict) -> None:
    for key, layer in (("j13_evidence_trace", "J13_BUILD"), ("j17_evidence_trace", "J17_BUILD")):
        trace = record[key]
        assert trace["layer_id"] == layer
        assert set(trace["trace"]) == set(TRACE_EDGES)
        assert trace["missing_edges"] == ["production_applicability"]
        for edge_name, edge in trace["trace"].items():
            assert edge["status"] == (
                "missing" if edge_name == "production_applicability" else "established"
            )


def test_package_scope_is_the_only_evidenced_j13_j17_differentiator(record: dict) -> None:
    results = {
        item["hypothesis"]: item["result"] for item in record["version_package_scope_hypotheses"]
    }
    assert results["geographic-package"] == "evidenced-differentiator"
    assert results["product-package"] == "evidenced-differentiator"
    assert results["specification-version"] == "not-supported-as-differentiator"
    assert results["source-dataset-version"] == "not-supported-as-differentiator"
    assert results["delivery-format"] == "not-supported-as-differentiator"
    assert results["semantic-role"] == "not-supported-as-differentiator"


def test_version_scoped_dual_binding_is_representable() -> None:
    validate_applicability_outcome(
        {
            "outcome": "version-scoped-dual-binding",
            "selected_layer_id": None,
            "selection_rule": "version A routes J13 and version B routes J17",
            "authoritative_binding_traces": [
                _complete_binding_trace("J13_BUILD"),
                _complete_binding_trace("J17_BUILD"),
            ],
        }
    )


def test_different_semantic_roles_are_representable() -> None:
    validate_applicability_outcome(
        {
            "outcome": "different-semantic-roles",
            "selected_layer_id": None,
            "semantic_distinction": "J13 is role A and J17 is role B",
            "authoritative_binding_traces": [
                _complete_binding_trace("J13_BUILD"),
                _complete_binding_trace("J17_BUILD"),
            ],
        }
    )


def test_unpublished_applicability_boundary_is_representable_and_selected(record: dict) -> None:
    resolution = record["authoritative_applicability_resolution"]
    assert resolution["outcome"] == "authoritative-applicability-boundary-not-published"
    validate_applicability_outcome(resolution)


def test_unpublished_state_closes_official_search(record: dict) -> None:
    assert (
        record["authoritative_applicability_resolution"]["official_evidence_search_closed"] is True
    )


def test_unpublished_state_requires_human_policy(record: dict) -> None:
    assert (
        record["authoritative_applicability_resolution"]["human_production_binding_policy_required"]
        is True
    )
    assert record["build09f_readiness"] == "READY-FOR-BUILD-09F"


def test_unavailable_evidence_is_distinct_and_requires_concrete_artifact() -> None:
    unavailable = {
        "outcome": "authoritative-evidence-unavailable",
        "selected_layer_id": None,
        "official_evidence_search_closed": False,
        "additional_authoritative_evidence_acquisition_justified": True,
        "concrete_required_artifact": "NLSC signed package-to-layer applicability manifest revision X",
    }
    validate_applicability_outcome(unavailable)
    missing = deepcopy(unavailable)
    missing["concrete_required_artifact"] = None
    with pytest.raises(J13J17ProductionApplicabilityError) as caught:
        validate_applicability_outcome(missing)
    assert caught.value.code == "artifact_missing"


def test_indeterminate_is_distinct_from_not_published() -> None:
    value = {
        "outcome": "indeterminate",
        "selected_layer_id": None,
        "official_evidence_search_closed": False,
    }
    validate_applicability_outcome(value)
    value["official_evidence_search_closed"] = True
    with pytest.raises(J13J17ProductionApplicabilityError) as caught:
        validate_applicability_outcome(value)
    assert caught.value.code == "boundary_conflated"


def test_no_policy_value_is_selected_under_human_policy_required(
    record: dict, successor: dict
) -> None:
    assert record["later_human_policy_shape"]["policy_value_selected"] is False
    assert record["scope"]["j13_j17_policy_value_selected"] is False
    binding = successor["production_binding_policy"]
    assert binding["selected_layer_id"] is None
    assert binding["selection_rule"] is None
    assert binding["policy_value_selected"] is False


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("production_activation_status", "forbidden"),
        ("official_portrayal_activation_status", "forbidden"),
        ("source_mutation_status", "forbidden"),
    ],
)
def test_activation_and_mutation_statuses_remain_forbidden(
    record: dict, field: str, expected: str
) -> None:
    assert record[field] == expected


def test_production_activation_remains_forbidden(
    record: dict, build09e1: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    changed = deepcopy(record)
    changed["runtime_activation_policy"]["production_activation_allowed"] = True
    _rehash(changed)
    assert _must_fail(changed, build09e1, build09e, build09, build08a) == "activation_enabled"


def test_official_portrayal_activation_remains_forbidden(
    record: dict, build09e1: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    changed = deepcopy(record)
    changed["runtime_activation_policy"]["official_portrayal_activation_allowed"] = True
    _rehash(changed)
    assert _must_fail(changed, build09e1, build09e, build09, build08a) == "activation_enabled"


def test_source_mutation_and_destructive_z_removal_remain_forbidden(
    record: dict, build09e1: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    for key in ("source_mutation_allowed", "source_z_dimension_removal_allowed"):
        changed = deepcopy(record)
        changed["source_mutation_policy"][key] = True
        _rehash(changed)
        assert (
            _must_fail(changed, build09e1, build09e, build09, build08a) == "source_mutation_enabled"
        )


def test_unknown_resolution_state_fails() -> None:
    with pytest.raises(J13J17ProductionApplicabilityError) as caught:
        validate_applicability_outcome({"outcome": "unknown"})
    assert caught.value.code == "unknown_resolution_state"
    assert "unknown" not in APPLICABILITY_OUTCOMES


def test_tampered_resolution_identity_fails(
    record: dict, build09e1: dict, build09e: dict, build09: dict, build08a: dict
) -> None:
    changed = deepcopy(record)
    changed["evidence_items"][1]["claim"] = "tampered"
    assert _must_fail(changed, build09e1, build09e, build09, build08a) == "resolution_hash_mismatch"
    _rehash(changed)
    assert _must_fail(changed, build09e1, build09e, build09, build08a) == "record_mismatch"


def test_successor_is_human_policy_hold_and_non_activating(
    successor: dict, record: dict, build09e1: dict, build09: dict
) -> None:
    assert successor["status"] == "human-policy-hold"
    assert successor["remaining_authoritative_evidence_blockers"] == []
    assert successor["production_activation_forbidden"] is True
    assert successor["official_portrayal_activation_forbidden"] is True
    assert (
        successor["bindings"]["build09e2_applicability_resolution_sha256"]
        == record["applicability_resolution_sha256"]
    )
    validate_successor_contract(successor, record, build09e1, build09)


def test_production_active_or_selected_successor_fails(
    successor: dict, record: dict, build09e1: dict, build09: dict
) -> None:
    active = deepcopy(successor)
    active["status"] = "production-active"
    active["successor_contract_sha256"] = successor_contract_sha256(active)
    with pytest.raises(J13J17ProductionApplicabilityError) as caught:
        validate_successor_contract(active, record, build09e1, build09)
    assert caught.value.code == "activation_enabled"
    selected = deepcopy(successor)
    selected["production_binding_policy"]["selected_layer_id"] = "J13_BUILD"
    selected["successor_contract_sha256"] = successor_contract_sha256(selected)
    with pytest.raises(J13J17ProductionApplicabilityError) as caught:
        validate_successor_contract(selected, record, build09e1, build09)
    assert caught.value.code == "policy_value_selected"


def test_predecessor_artifacts_remain_unchanged(record: dict) -> None:
    for relative, expected in record["predecessor"]["frozen_build09e1_artifact_sha256"].items():
        assert _sha256(ROOT / relative) == expected


def test_source_archive_remains_unchanged() -> None:
    archive = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
    assert _sha256(archive) == "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"


def test_five_gate_snapshot_and_next_stage_are_exact(record: dict) -> None:
    states = {item["gate_id"]: item["state"] for item in record["five_gate_readiness"]}
    assert states == {
        "hatch-angle-asset": "local-policy-required",
        "annotation-placement-binding": "local-policy-required",
        "j13-j17-identity": "human-production-binding-policy-required",
        "line-colour-portrayal": "local-output-profile-policy-required",
        "polygonz-derived-xy": "P2-production-candidate",
    }
    assert record["next_stage_recommendation"].startswith("BUILD-09F")
    assert "BUILD-10" in record["next_stage_recommendation"]


def test_exact_verdict(record: dict) -> None:
    assert record["verdict"] == (
        "PASS — OFFICIAL J13/J17 APPLICABILITY BOUNDARY CLOSED; HUMAN PRODUCTION BINDING POLICY REQUIRED"
    )

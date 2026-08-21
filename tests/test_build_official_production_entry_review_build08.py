from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError
import pytest

import build_contracts.production_entry_review as build08
from build_contracts.demo_evaluation import BuildDemoEvaluationError
from build_contracts.production_entry_review import (
    BOUNDARIES,
    BuildProductionEntryReviewError,
    ENTRY_DECISION,
    build_official_production_entry_review,
    production_entry_review_sha256,
    validate_official_production_entry_review,
)
from nma.real_layer import REAL_LAYER_PROFILES, propose_real_layer


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "data/specifications/nma-build-07-golden-evaluation-template-v1.0.json"
EVALUATION_PATH = ROOT / "data/specifications/nma-build-07-accepted-user-evaluation-v1.0.json"
REVIEW_PATH = (
    ROOT
    / "data/specifications/nma-build-08-golden-official-production-entry-review-v1.0.json"
)
SCHEMA_PATH = ROOT / "schemas/build-official-production-entry-review-v1.0.schema.json"
RECIPE_PATH = (
    ROOT / "data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json"
)

EXPECTED_REVIEW_SHA256 = "b48337a6bb8cf1e6cffc54e0bbfe14383f62c1dcfdca54bf706c0ab045b42484"


@pytest.fixture()
def template() -> dict:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def evaluation() -> dict:
    return json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def review() -> dict:
    return json.loads(REVIEW_PATH.read_text(encoding="utf-8"))


def _fails(callable_, code: str) -> BuildProductionEntryReviewError:
    with pytest.raises(BuildProductionEntryReviewError) as caught:
        callable_()
    assert caught.value.code == code
    return caught.value


def _rehash(review: dict) -> dict:
    review["review_sha256"] = production_entry_review_sha256(review)
    return review


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_golden_review_is_exactly_reproducible(
    template: dict, evaluation: dict, review: dict
) -> None:
    actual = build_official_production_entry_review(template, evaluation)

    assert actual == review
    assert actual["review_sha256"] == EXPECTED_REVIEW_SHA256
    assert production_entry_review_sha256(actual) == EXPECTED_REVIEW_SHA256


def test_closed_schema_is_valid_and_accepts_only_the_frozen_review(review: dict) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    Draft202012Validator(schema).validate(review)

    changed = deepcopy(review)
    changed["production_authorized"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(changed)


def test_predecessor_is_the_exact_completed_build07_record(review: dict) -> None:
    assert review["predecessor"] == {
        "build07_branch": "build/build-07-demo-user-evaluation",
        "build07_completion_commit": "153037a165683e0a2b39d36620c688955ca935fd",
        "build07_record_file_sha256": (
            "7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d"
        ),
        "build07_record_sha256": (
            "ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c"
        ),
        "build07_template_sha256": (
            "0fea2e7fe6b8ec9dd10816ba5679b04773ecd3f0761ca7b58e339f7df91139e6"
        ),
        "build06_freeze_sha256": (
            "bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857"
        ),
        "build03a_resolution_sha256": (
            "a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01"
        ),
    }


def test_demo_acceptance_is_not_reinterpreted_as_official_or_production(review: dict) -> None:
    assert review["scope"] == {
        "target": "official-semantics-and-production-entry-readiness",
        "method": "tracked-evidence-and-runtime-path-read-only-review",
        "build07_demo_acceptance_is_official_evidence": False,
        "build07_demo_acceptance_is_production_authorization": False,
        "runtime_or_source_change_performed": False,
    }


def test_entry_decision_keeps_production_and_official_portrayal_on_hold(review: dict) -> None:
    assert review["status"] == "production-entry-held-human-scope-decision-required"
    assert review["entry_decision"] == ENTRY_DECISION
    assert ENTRY_DECISION["existing_frozen_demo"] == "go"
    assert ENTRY_DECISION["official_portrayal_promotion"] == "hold"
    assert ENTRY_DECISION["production_runtime_entry"] == "hold"
    assert ENTRY_DECISION["source_execution_or_mutation"] == "hold"
    assert ENTRY_DECISION["production_ready_gate_count"] == 0
    assert ENTRY_DECISION["unresolved_official_gate_count"] == 5


def test_every_build07_gate_remains_held_for_official_and_production(
    review: dict, evaluation: dict
) -> None:
    gates = review["gate_reviews"]

    assert [item["gate_id"] for item in gates] == [
        item["gate_id"] for item in evaluation["decisions"]
    ]
    assert all(item["build07_demo_verdict"] == "accept-current-demo" for item in gates)
    assert all(item["disposition"] == "hold-official-and-production" for item in gates)
    assert all(item["human_decision_required"] is True for item in gates)
    assert all(item["blockers"] for item in gates)
    assert all(item["required_next_evidence"] for item in gates)


def test_runtime_evidence_files_are_byte_exact(review: dict) -> None:
    evidence = review["runtime_evidence"]

    for item in (
        evidence["real_layer"],
        evidence["portrayal_compile"],
        evidence["maplibre_adapter"],
        evidence["reviewed_portrayal_recipe"],
    ):
        assert _file_sha256(ROOT / item["path"]) == item["file_sha256"]


def test_real_layer_profile_targets_j17_while_build07_is_j13(review: dict) -> None:
    profile = REAL_LAYER_PROFILES["building-polygon"]
    evidence = review["runtime_evidence"]["real_layer"]

    assert profile["source_layer_ids"] == evidence["configured_source_layers"] == ["J17_BUILD"]
    assert evidence["build07_selected_layer"] == "J13_BUILD"
    assert profile["source_layer_ids"] != [evidence["build07_selected_layer"]]


def test_real_layer_profile_cannot_emit_build07_floor_structure_annotation(
    review: dict,
) -> None:
    profile = REAL_LAYER_PROFILES["building-polygon"]
    evidence = review["runtime_evidence"]["real_layer"]

    assert profile["label_field"] is evidence["label_field"] is None
    assert evidence["build07_annotation_fields"] == ["BUILD_NO", "BUILD_STR"]
    assert "building-runtime-label-field-is-null" in review["gate_reviews"][1]["blockers"]


def test_existing_real_layer_plan_explicitly_drops_z(review: dict) -> None:
    source = inspect.getsource(propose_real_layer)
    evidence = review["runtime_evidence"]["real_layer"]

    assert '"drop-z"' in source
    assert '"-dim"' in (ROOT / "src/nma/real_layer.py").read_text(encoding="utf-8")
    assert '"XY"' in (ROOT / "src/nma/real_layer.py").read_text(encoding="utf-8")
    assert evidence["planned_operations"][-1] == "drop-z"
    assert evidence["build07_source_z_dimension_drop_allowed"] is False
    assert evidence["status"] == "incompatible-with-build07-production-entry"


def test_portrayal_pipeline_is_still_preview_only(review: dict) -> None:
    compile_evidence = review["runtime_evidence"]["portrayal_compile"]
    adapter_evidence = review["runtime_evidence"]["maplibre_adapter"]

    assert compile_evidence["output_status"] == "compiled-for-review"
    assert compile_evidence["preview_only"] is True
    assert compile_evidence["official_rule_activation"] == (
        "blocked-until-all-activation-gates-resolved"
    )
    assert adapter_evidence["output_status"] == "adapter-ready-for-preview"
    assert adapter_evidence["preview_only"] is True
    assert adapter_evidence["map_mutation_performed"] is False
    assert adapter_evidence["automatic_action"] is False


def test_reviewed_building_recipe_is_non_executable_and_asset_is_absent(review: dict) -> None:
    recipe_file = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    recipe = next(item for item in recipe_file["recipes"] if item["feature_code"] == "9310100")
    evidence = review["runtime_evidence"]["reviewed_portrayal_recipe"]

    assert recipe["activation_status"] == evidence["activation_status"]
    assert recipe["runtime_evidence"]["status"] == evidence["runtime_binding_status"]
    assert recipe["review_asset"]["path"] == evidence["review_asset_path"]
    assert not (ROOT / evidence["review_asset_path"]).exists()
    assert evidence["review_asset_present"] is False


def test_hatch_gate_requires_official_policy_and_deployable_asset(review: dict) -> None:
    gate = review["gate_reviews"][0]

    assert gate["official_evidence_status"] == "numeric-angle-not-specified-by-reviewed-source"
    assert gate["runtime_readiness_status"] == "hatch-asset-absent-and-preview-only"
    assert "reviewed-hatch-asset-missing" in gate["blockers"]


def test_annotation_gate_requires_policy_and_runtime_binding(review: dict) -> None:
    gate = review["gate_reviews"][1]

    assert gate["official_evidence_status"] == "placement-and-collision-policy-not-specified"
    assert gate["runtime_readiness_status"] == "polygon-label-binding-not-implemented"
    assert "build-no-plus-build-str-composition-not-wired" in gate["blockers"]


def test_schema_gate_requires_one_versioned_authoritative_layer_contract(review: dict) -> None:
    gate = review["gate_reviews"][2]

    assert gate["official_evidence_status"] == "j13-observation-is-not-global-schema-equivalence"
    assert gate["runtime_readiness_status"] == "runtime-profile-binds-j17-not-build07-j13"
    assert "build07-layer-and-runtime-layer-mismatch" in gate["blockers"]


def test_line_color_gate_rejects_preview_defaults_as_official_definitions(review: dict) -> None:
    gate = review["gate_reviews"][3]

    assert gate["official_evidence_status"] == "device-independent-code-mapping-not-approved"
    assert gate["runtime_readiness_status"] == "preview-defaults-are-not-production-profile"
    assert "preview-derived-values-not-official-definitions" in gate["blockers"]


def test_polygonz_gate_rejects_current_drop_z_path(review: dict) -> None:
    gate = review["gate_reviews"][4]

    assert gate["official_evidence_status"] == "source-polygonz-must-remain-authoritative"
    assert gate["runtime_readiness_status"] == "existing-real-layer-plan-explicitly-drops-z"
    assert "runtime-drop-z-conflicts-with-build07-boundary" in gate["blockers"]


def test_all_authority_and_source_boundaries_remain_closed(review: dict) -> None:
    assert review["boundaries"] == BOUNDARIES
    assert BOUNDARIES["review_only"] is True
    for denied in (
        "private_source_accessed",
        "human_decision_inferred",
        "official_semantics_decided",
        "official_portrayal_activation_allowed",
        "production_runtime_wiring_allowed",
        "production_activation_allowed",
        "source_access_allowed",
        "source_execution_allowed",
        "source_mutation_allowed",
        "source_z_dimension_drop_allowed",
        "demo_changed",
    ):
        assert BOUNDARIES[denied] is False


@pytest.mark.parametrize(
    ("target", "value"),
    [
        ("production", "go"),
        ("official", "go"),
        ("source", "go"),
        ("ready-count", 1),
        ("human-required", False),
        ("j17-to-j13", ["J13_BUILD"]),
        ("label", "BUILD_NO"),
        ("drop-z", "preserve-z"),
        ("asset", True),
        ("private-source", True),
    ],
)
def test_rehashed_tampering_or_authority_expansion_fails_closed(
    review: dict,
    template: dict,
    evaluation: dict,
    target: str,
    value: object,
) -> None:
    changed = deepcopy(review)
    if target == "production":
        changed["entry_decision"]["production_runtime_entry"] = value
    elif target == "official":
        changed["entry_decision"]["official_portrayal_promotion"] = value
    elif target == "source":
        changed["entry_decision"]["source_execution_or_mutation"] = value
    elif target == "ready-count":
        changed["entry_decision"]["production_ready_gate_count"] = value
    elif target == "human-required":
        changed["entry_decision"]["human_decision_required"] = value
    elif target == "j17-to-j13":
        changed["runtime_evidence"]["real_layer"]["configured_source_layers"] = value
    elif target == "label":
        changed["runtime_evidence"]["real_layer"]["label_field"] = value
    elif target == "drop-z":
        changed["runtime_evidence"]["real_layer"]["planned_operations"][-1] = value
    elif target == "asset":
        changed["runtime_evidence"]["reviewed_portrayal_recipe"][
            "review_asset_present"
        ] = value
    else:
        changed["boundaries"]["private_source_accessed"] = value
    _rehash(changed)

    _fails(
        lambda: validate_official_production_entry_review(changed, template, evaluation),
        "review_mismatch",
    )


def test_unknown_review_field_fails_closed(
    review: dict, template: dict, evaluation: dict
) -> None:
    changed = deepcopy(review)
    changed["authorization"] = {"production": True}
    _rehash(changed)

    _fails(
        lambda: validate_official_production_entry_review(changed, template, evaluation),
        "review_fields_invalid",
    )


def test_tampered_build07_record_cannot_seed_build08(
    template: dict, evaluation: dict
) -> None:
    changed = deepcopy(evaluation)
    changed["status"] = "revision-requested-demo-only"

    with pytest.raises(BuildDemoEvaluationError):
        build_official_production_entry_review(template, changed)


def test_build08_module_has_no_runtime_or_source_execution_capability() -> None:
    source = inspect.getsource(build08)

    for forbidden in (
        "subprocess",
        "ogr2ogr",
        "inspect_private_build_source",
        "execute_real_layer",
        "execute_build_demo_once",
        "open(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in source


def test_golden_review_is_canonical_single_json_line(review: dict) -> None:
    expected = (
        json.dumps(
            review,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )

    assert REVIEW_PATH.read_bytes() == expected

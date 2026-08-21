from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import pytest

from build_contracts.demo_evaluation import (
    BuildDemoEvaluationError,
    create_demo_evaluation_record,
    evaluation_record_sha256,
    validate_demo_evaluation_record,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "data/specifications/nma-build-07-golden-evaluation-template-v1.0.json"
RECORD_PATH = ROOT / "data/specifications/nma-build-07-accepted-user-evaluation-v1.0.json"
SCHEMA_PATH = ROOT / "schemas/build-demo-user-evaluation-v1.0.schema.json"

EXPECTED_FILE_SHA256 = "7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d"
EXPECTED_RECORD_SHA256 = "ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c"
EXPECTED_TEMPLATE_SHA256 = "0fea2e7fe6b8ec9dd10816ba5679b04773ecd3f0761ca7b58e339f7df91139e6"


@pytest.fixture()
def template() -> dict:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def record() -> dict:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def test_recorded_file_is_the_exact_submitted_export() -> None:
    assert hashlib.sha256(RECORD_PATH.read_bytes()).hexdigest() == EXPECTED_FILE_SHA256


def test_record_has_exact_canonical_identity(record: dict) -> None:
    assert record["record_sha256"] == EXPECTED_RECORD_SHA256
    assert evaluation_record_sha256(record) == EXPECTED_RECORD_SHA256
    assert record["template_sha256"] == EXPECTED_TEMPLATE_SHA256


def test_closed_schema_accepts_the_recorded_result(record: dict) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)


def test_build07_contract_accepts_the_recorded_result(record: dict, template: dict) -> None:
    assert validate_demo_evaluation_record(record, template) == record


def test_result_is_reproducible_from_the_five_human_decisions(
    record: dict, template: dict
) -> None:
    decisions = {
        item["gate_id"]: {
            key: value for key, value in item.items() if key != "gate_id"
        }
        for item in record["decisions"]
    }

    assert create_demo_evaluation_record(
        template, decisions, evaluated_on="2026-08-21"
    ) == record


def test_all_five_current_demo_choices_are_explicitly_accepted(record: dict) -> None:
    assert record["status"] == "accepted-demo-only"
    assert [item["gate_id"] for item in record["decisions"]] == [
        "hatch-angle-transcription",
        "building-annotation-placement",
        "real-build-schema-binding",
        "line-and-color-profile",
        "j13-polygonz-runtime-policy",
    ]
    assert all(item["verdict"] == "accept-current-demo" for item in record["decisions"])
    assert record["summary"] == {
        "gate_count": 5,
        "accepted_count": 5,
        "revision_requested_count": 0,
        "all_five_decisions_explicit": True,
    }


def test_accepted_hatch_angle_is_the_frozen_45_degree_demo_default(record: dict) -> None:
    hatch = record["decisions"][0]

    assert hatch["gate_id"] == "hatch-angle-transcription"
    assert hatch["preferred_angle_degrees"] == 45


def test_record_does_not_identify_or_infer_the_human_reviewer(record: dict) -> None:
    assert record["evaluator"] == {
        "actor_type": "human-demo-reviewer",
        "identity_recorded": False,
    }


def test_acceptance_preserves_every_demo_only_authority_boundary(record: dict) -> None:
    boundaries = record["boundaries"]

    assert boundaries["demo_only"] is True
    for denied in (
        "evaluation_export_is_authorization",
        "official_portrayal_decided",
        "production_activation_allowed",
        "production_semantics_decided",
        "raw_source_disclosure_allowed",
        "runtime_wiring_allowed",
        "source_access_allowed",
        "source_mutation_allowed",
        "source_z_dimension_drop_allowed",
    ):
        assert boundaries[denied] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "approved-for-production"),
        ("record_type", "official-portrayal-decision"),
    ],
)
def test_rehashed_authority_promotion_is_rejected(
    record: dict, template: dict, field: str, value: str
) -> None:
    changed = deepcopy(record)
    changed[field] = value
    changed["record_sha256"] = evaluation_record_sha256(changed)

    with pytest.raises(BuildDemoEvaluationError):
        validate_demo_evaluation_record(changed, template)


def test_schema_rejects_runtime_authority_even_if_record_is_rehashed(record: dict) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    changed = deepcopy(record)
    changed["boundaries"]["runtime_wiring_allowed"] = True
    changed["record_sha256"] = evaluation_record_sha256(changed)

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(changed)

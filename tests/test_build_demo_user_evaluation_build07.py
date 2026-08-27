from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import pytest

import build_contracts.demo_evaluation as build07
from build_contracts.demo_evaluation import (
    BOUNDARIES,
    BuildDemoEvaluationError,
    build_demo_evaluation_template,
    create_demo_evaluation_record,
    evaluation_record_sha256,
    evaluation_template_sha256,
    validate_demo_evaluation_record,
    validate_demo_evaluation_template,
)


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "data/specifications/nma-build-07-golden-evaluation-template-v1.0.json"
SCHEMA_PATH = ROOT / "schemas/build-demo-user-evaluation-v1.0.schema.json"
DEMO_PATH = ROOT / "buildDemoV07.html"


@pytest.fixture()
def golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def accepted_decisions() -> dict[str, dict]:
    decisions = {
        item["gate_id"]: {"verdict": "accept-current-demo", "note_zh_tw": ""}
        for item in build07.GATE_ITEMS
    }
    decisions["hatch-angle-transcription"]["preferred_angle_degrees"] = 45
    return decisions


def _fails(callable_, code: str) -> BuildDemoEvaluationError:
    with pytest.raises(BuildDemoEvaluationError) as caught:
        callable_()
    assert caught.value.code == code
    return caught.value


def _rehash(record: dict) -> dict:
    record["record_sha256"] = evaluation_record_sha256(record)
    return record


def test_golden_template_is_exact_reproducible_contract(golden: dict) -> None:
    actual = build_demo_evaluation_template()

    assert actual == golden
    assert validate_demo_evaluation_template(golden) == golden
    assert actual["template_sha256"] == (
        "0fea2e7fe6b8ec9dd10816ba5679b04773ecd3f0761ca7b58e339f7df91139e6"
    )
    assert evaluation_template_sha256(golden) == golden["template_sha256"]


def test_closed_schema_accepts_template_and_completed_record(
    golden: dict, accepted_decisions: dict[str, dict]
) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    validator.validate(golden)
    record = create_demo_evaluation_record(golden, accepted_decisions, evaluated_on="2026-08-20")
    validator.validate(record)


def test_schema_rejects_authority_expansion(golden: dict) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    changed = deepcopy(golden)
    changed["boundaries"]["production_activation_allowed"] = True

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(changed)


def test_template_binds_exact_build06a_publication_and_prior_decisions(golden: dict) -> None:
    assert golden["predecessor"] == {
        "build06a_branch": "build/build-06a-safe-demo-publication",
        "build06a_commit": "540153127d26db0197ab0891fb9c07c7fe8f012e",
        "public_main_commit": "88290fa55832edbbe190a68095b115cab93c4eb9",
        "publication_sha256": "83c22625ad99dbc0cb26af614d39cf6fd12e6e77b1c863b501656e46f6d105a9",
        "build06_freeze_sha256": "bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857",
        "build03a_resolution_sha256": "a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01",
    }


def test_exact_five_gate_order_is_preserved(golden: dict) -> None:
    assert [item["gate_id"] for item in golden["gate_items"]] == [
        "hatch-angle-transcription",
        "building-annotation-placement",
        "real-build-schema-binding",
        "line-and-color-profile",
        "j13-polygonz-runtime-policy",
    ]
    assert [item["order"] for item in golden["gate_items"]] == [1, 2, 3, 4, 5]
    assert all(
        item["official_status"] == "unresolved-outside-demo" for item in golden["gate_items"]
    )


def test_only_hatch_angle_is_directly_adjustable(golden: dict) -> None:
    adjustable = [
        item["gate_id"]
        for item in golden["gate_items"]
        if item["interaction"]["direct_demo_adjustment_allowed"]
    ]

    assert adjustable == ["hatch-angle-transcription"]
    assert golden["gate_items"][0]["interaction"] == {
        "control": "angle-slider-and-accept-or-revise",
        "direct_demo_adjustment_allowed": True,
        "default_angle_degrees": 45,
        "minimum_inclusive": 0,
        "maximum_inclusive": 179,
        "step": 1,
    }


def test_every_boundary_remains_demo_only_and_non_authorizing(golden: dict) -> None:
    assert golden["boundaries"] == BOUNDARIES
    assert BOUNDARIES["demo_only"] is True
    for denied in (
        "official_portrayal_decided",
        "production_semantics_decided",
        "production_activation_allowed",
        "runtime_wiring_allowed",
        "source_access_allowed",
        "source_mutation_allowed",
        "source_z_dimension_drop_allowed",
        "raw_source_disclosure_allowed",
        "evaluation_export_is_authorization",
    ):
        assert BOUNDARIES[denied] is False


def test_all_accept_record_is_accepted_demo_only(
    golden: dict, accepted_decisions: dict[str, dict]
) -> None:
    record = create_demo_evaluation_record(golden, accepted_decisions, evaluated_on="2026-08-20")

    assert record["status"] == "accepted-demo-only"
    assert record["summary"] == {
        "gate_count": 5,
        "accepted_count": 5,
        "revision_requested_count": 0,
        "all_five_decisions_explicit": True,
    }
    assert record["evaluator"] == {
        "actor_type": "human-demo-reviewer",
        "identity_recorded": False,
    }
    assert validate_demo_evaluation_record(record, golden) == record


def test_any_revision_yields_revision_requested_demo_only(
    golden: dict, accepted_decisions: dict[str, dict]
) -> None:
    accepted_decisions["line-and-color-profile"] = {
        "verdict": "request-demo-revision",
        "note_zh_tw": "希望比較較細的邊界線。",
    }
    record = create_demo_evaluation_record(golden, accepted_decisions, evaluated_on="2026-08-20")

    assert record["status"] == "revision-requested-demo-only"
    assert record["summary"]["accepted_count"] == 4
    assert record["summary"]["revision_requested_count"] == 1
    assert record["boundaries"]["production_semantics_decided"] is False


def test_angle_revision_can_record_a_different_whole_degree(
    golden: dict, accepted_decisions: dict[str, dict]
) -> None:
    accepted_decisions["hatch-angle-transcription"] = {
        "verdict": "request-demo-revision",
        "note_zh_tw": "偏好 60°。",
        "preferred_angle_degrees": 60,
    }
    record = create_demo_evaluation_record(golden, accepted_decisions, evaluated_on="2026-08-20")

    assert record["decisions"][0]["preferred_angle_degrees"] == 60
    assert record["status"] == "revision-requested-demo-only"


@pytest.mark.parametrize("missing_gate", [item["gate_id"] for item in build07.GATE_ITEMS])
def test_missing_any_gate_fails_closed(
    golden: dict, accepted_decisions: dict[str, dict], missing_gate: str
) -> None:
    accepted_decisions.pop(missing_gate)
    _fails(
        lambda: create_demo_evaluation_record(
            golden, accepted_decisions, evaluated_on="2026-08-20"
        ),
        "decision_set_invalid",
    )


def test_extra_gate_fails_closed(golden: dict, accepted_decisions: dict[str, dict]) -> None:
    accepted_decisions["production-approval"] = {
        "verdict": "accept-current-demo",
        "note_zh_tw": "",
    }
    _fails(
        lambda: create_demo_evaluation_record(
            golden, accepted_decisions, evaluated_on="2026-08-20"
        ),
        "decision_set_invalid",
    )


@pytest.mark.parametrize("verdict", ["approved", "official", "production", "", None])
def test_unrecognized_or_authority_verdict_is_rejected(
    golden: dict, accepted_decisions: dict[str, dict], verdict
) -> None:
    accepted_decisions["building-annotation-placement"]["verdict"] = verdict
    _fails(
        lambda: create_demo_evaluation_record(
            golden, accepted_decisions, evaluated_on="2026-08-20"
        ),
        "verdict_invalid",
    )


def test_revision_requires_explanation(golden: dict, accepted_decisions: dict[str, dict]) -> None:
    accepted_decisions["real-build-schema-binding"] = {
        "verdict": "request-demo-revision",
        "note_zh_tw": "   ",
    }
    _fails(
        lambda: create_demo_evaluation_record(
            golden, accepted_decisions, evaluated_on="2026-08-20"
        ),
        "revision_note_required",
    )


def test_note_length_is_bounded(golden: dict, accepted_decisions: dict[str, dict]) -> None:
    accepted_decisions["building-annotation-placement"]["note_zh_tw"] = "字" * 501
    _fails(
        lambda: create_demo_evaluation_record(
            golden, accepted_decisions, evaluated_on="2026-08-20"
        ),
        "note_invalid",
    )


@pytest.mark.parametrize("value", [-1, 180, 45.5, True, "45", None])
def test_angle_must_be_whole_degree_in_demo_range(
    golden: dict, accepted_decisions: dict[str, dict], value
) -> None:
    accepted_decisions["hatch-angle-transcription"]["preferred_angle_degrees"] = value
    _fails(
        lambda: create_demo_evaluation_record(
            golden, accepted_decisions, evaluated_on="2026-08-20"
        ),
        "angle_invalid",
    )


def test_accepting_current_demo_requires_45_degrees(
    golden: dict, accepted_decisions: dict[str, dict]
) -> None:
    accepted_decisions["hatch-angle-transcription"]["preferred_angle_degrees"] = 60
    _fails(
        lambda: create_demo_evaluation_record(
            golden, accepted_decisions, evaluated_on="2026-08-20"
        ),
        "angle_conflict",
    )


@pytest.mark.parametrize("evaluated_on", ["", "2026-02-30", "20-08-2026", None])
def test_evaluation_date_must_be_real_iso_date(
    golden: dict, accepted_decisions: dict[str, dict], evaluated_on
) -> None:
    _fails(
        lambda: create_demo_evaluation_record(
            golden, accepted_decisions, evaluated_on=evaluated_on
        ),
        "date_invalid",
    )


def test_non_angle_gate_cannot_smuggle_adjustment(
    golden: dict, accepted_decisions: dict[str, dict]
) -> None:
    accepted_decisions["line-and-color-profile"]["color"] = "#ff0000"
    _fails(
        lambda: create_demo_evaluation_record(
            golden, accepted_decisions, evaluated_on="2026-08-20"
        ),
        "decision_fields_invalid",
    )


def test_tampered_template_fails_even_if_rehashed(golden: dict) -> None:
    changed = deepcopy(golden)
    changed["gate_items"][0]["interaction"]["default_angle_degrees"] = 60
    changed["template_sha256"] = evaluation_template_sha256(changed)

    _fails(lambda: validate_demo_evaluation_template(changed), "template_mismatch")


def test_tampered_record_hash_fails(golden: dict, accepted_decisions: dict[str, dict]) -> None:
    record = create_demo_evaluation_record(golden, accepted_decisions, evaluated_on="2026-08-20")
    record["summary"]["accepted_count"] = 4

    _fails(lambda: validate_demo_evaluation_record(record, golden), "record_hash_mismatch")


def test_rehashed_record_cannot_expand_authority(
    golden: dict, accepted_decisions: dict[str, dict]
) -> None:
    record = create_demo_evaluation_record(golden, accepted_decisions, evaluated_on="2026-08-20")
    record["boundaries"]["production_activation_allowed"] = True
    _rehash(record)

    _fails(lambda: validate_demo_evaluation_record(record, golden), "authority_expanded")


def test_rehashed_record_cannot_add_unknown_fields(
    golden: dict, accepted_decisions: dict[str, dict]
) -> None:
    record = create_demo_evaluation_record(golden, accepted_decisions, evaluated_on="2026-08-20")
    record["production_authorized"] = True
    _rehash(record)

    _fails(lambda: validate_demo_evaluation_record(record, golden), "record_fields_invalid")


def test_golden_is_canonical_single_json_line(golden: dict) -> None:
    expected = (
        json.dumps(
            golden,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    assert GOLDEN_PATH.read_bytes() == expected


def test_demo_loads_exact_three_frozen_inputs() -> None:
    source = DEMO_PATH.read_text(encoding="utf-8")

    assert (
        'const PACKAGE_URL = "data/specifications/nma-build-05-golden-execution-package-v1.0.json";'
        in source
    )
    assert (
        'const LEDGER_URL = "data/specifications/nma-build-05-authorization-consumption-v1.0.json";'
        in source
    )
    assert (
        'const TEMPLATE_URL = "data/specifications/nma-build-07-golden-evaluation-template-v1.0.json";'
        in source
    )
    assert "9e2b183260c5ac689831b1f5945defad28f27f49447f1a0d3f2b5b0425189364" in source


def test_demo_has_five_decision_export_and_no_server_submission() -> None:
    source = DEMO_PATH.read_text(encoding="utf-8")

    assert "五項 DEMO 語意決議" in source
    assert "accept-current-demo" in source
    assert "request-demo-revision" in source
    assert "下載評估 JSON" in source
    assert "URL.createObjectURL" in source
    assert "human-demo-reviewer" in source
    assert "identity_recorded: false" in source
    assert "fetch(" in source
    assert "POST" not in source
    assert "XMLHttpRequest" not in source
    assert "sendBeacon" not in source
    assert "localStorage" not in source
    assert "sessionStorage" not in source


def test_demo_preserves_only_angle_as_direct_visual_control() -> None:
    source = DEMO_PATH.read_text(encoding="utf-8")

    assert 'id="hatch-angle" type="range" min="0" max="179" step="1" value="45"' in source
    assert "若接受目前 DEMO，請先回到 45°" in source
    assert 'type="color"' not in source
    assert "line-width" not in source
    assert "annotation-position" not in source


def test_demo_remains_same_origin_offline_and_non_production() -> None:
    source = DEMO_PATH.read_text(encoding="utf-8")

    assert "default-src 'self'" in source
    assert "DEMO ONLY · 非正式圖式" in source
    assert "production 授權" in source
    assert "無外部網路、無伺服器儲存" in source
    assert "http://" not in source
    assert "https://" not in source
    assert 'src="//' not in source


def test_contract_has_no_io_network_execution_or_production_capability() -> None:
    source = inspect.getsource(build07)

    for forbidden in (
        "subprocess",
        "requests",
        "urllib",
        "open(",
        "write_text",
        "write_bytes",
        "GITHUB_TOKEN",
        'production_activated": True',
    ):
        assert forbidden not in source

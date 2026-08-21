"""BUILD-07 DEMO-only user evaluation and semantic-decision contract.

The contract captures a human review of the five already-approved DEMO
semantics.  It cannot promote a choice to official evidence, authorize source
access, wire a runtime, or activate production behavior.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import re
from typing import Any, Mapping

from nma.core import canonical_sha256


EVALUATION_SCHEMA = "nma.build-demo-user-evaluation/1.0"
EVALUATION_VERSION = "build-07/1.0"
EXPECTED_BUILD06A_COMMIT = "540153127d26db0197ab0891fb9c07c7fe8f012e"
EXPECTED_BUILD06A_PUBLIC_COMMIT = "88290fa55832edbbe190a68095b115cab93c4eb9"
EXPECTED_BUILD06A_PUBLICATION_SHA256 = (
    "83c22625ad99dbc0cb26af614d39cf6fd12e6e77b1c863b501656e46f6d105a9"
)
EXPECTED_BUILD06_FREEZE_SHA256 = "bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857"
EXPECTED_BUILD03A_RESOLUTION_SHA256 = (
    "a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01"
)
LIVE_DEMO_URL = "https://dongpo.github.io/topoMap/build-demo/"

GATE_ITEMS = [
    {
        "gate_id": "hatch-angle-transcription",
        "order": 1,
        "title_zh_tw": "剖面線角度",
        "question_zh_tw": "45° 是否適合作為建物剖面線的 DEMO 預設值？",
        "current_demo_resolution_zh_tw": (
            "預設 45°，使用者可在 0–179° 間調整；數值不是官方來源事實。"
        ),
        "official_status": "unresolved-outside-demo",
        "interaction": {
            "control": "angle-slider-and-accept-or-revise",
            "direct_demo_adjustment_allowed": True,
            "default_angle_degrees": 45,
            "minimum_inclusive": 0,
            "maximum_inclusive": 179,
            "step": 1,
        },
    },
    {
        "gate_id": "building-annotation-placement",
        "order": 2,
        "title_zh_tw": "建物註記位置",
        "question_zh_tw": "註記置於建物內部最佳點、放不下就隱藏，是否適合 DEMO？",
        "current_demo_resolution_zh_tw": (
            "使用面內最佳點；放不下或與高優先標註碰撞時隱藏，不移到建物外。"
        ),
        "official_status": "unresolved-outside-demo",
        "interaction": {
            "control": "accept-or-revise",
            "direct_demo_adjustment_allowed": False,
        },
    },
    {
        "gate_id": "real-build-schema-binding",
        "order": 3,
        "title_zh_tw": "J13 欄位綁定",
        "question_zh_tw": "只以 BUILD_NO＋BUILD_STR 形成 DEMO 註記，是否可接受？",
        "current_demo_resolution_zh_tw": (
            "只限已驗證 J13 的 BUILD_NO 與 BUILD_STR；不宣稱與 ID 或 SOURCE 全域等價。"
        ),
        "official_status": "unresolved-outside-demo",
        "interaction": {
            "control": "accept-or-revise",
            "direct_demo_adjustment_allowed": False,
        },
    },
    {
        "gate_id": "line-and-color-profile",
        "order": 4,
        "title_zh_tw": "線寬與顏色",
        "question_zh_tw": "黑色、1 CSS px、完全不透明是否適合此網頁 DEMO？",
        "current_demo_resolution_zh_tw": (
            "nma-maplibre-web-demo-v1：#111111、1 CSS px 實線、opacity 1；不是官方代碼定義。"
        ),
        "official_status": "unresolved-outside-demo",
        "interaction": {
            "control": "accept-or-revise",
            "direct_demo_adjustment_allowed": False,
        },
    },
    {
        "gate_id": "j13-polygonz-runtime-policy",
        "order": 5,
        "title_zh_tw": "PolygonZ 與 2D 顯示",
        "question_zh_tw": "來源保留 PolygonZ、只有衍生 DEMO 使用 XY，是否可接受？",
        "current_demo_resolution_zh_tw": (
            "來源與證據保留 PolygonZ；XY 只用於衍生展示，不回寫、不修復、不移除 Z。"
        ),
        "official_status": "unresolved-outside-demo",
        "interaction": {
            "control": "accept-or-revise",
            "direct_demo_adjustment_allowed": False,
        },
    },
]

BOUNDARIES = {
    "demo_only": True,
    "official_portrayal_decided": False,
    "production_semantics_decided": False,
    "production_activation_allowed": False,
    "runtime_wiring_allowed": False,
    "source_access_allowed": False,
    "source_mutation_allowed": False,
    "source_z_dimension_drop_allowed": False,
    "raw_source_disclosure_allowed": False,
    "evaluation_export_is_authorization": False,
}

EVALUATION_RULES = {
    "required_gate_count": 5,
    "allowed_verdicts": ["accept-current-demo", "request-demo-revision"],
    "all_gate_verdicts_required": True,
    "revision_note_required": True,
    "maximum_note_characters": 500,
    "accepted_result": "accepted-demo-only",
    "revision_result": "revision-requested-demo-only",
    "official_or_production_result_allowed": False,
}


class BuildDemoEvaluationError(ValueError):
    """BUILD-07 rejected an invalid evaluation or authority expansion."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildDemoEvaluationError(message, code=code)


def _template_basis() -> dict[str, Any]:
    return {
        "evaluation_version": EVALUATION_VERSION,
        "schema_version": EVALUATION_SCHEMA,
        "status": "awaiting-user-evaluation",
        "predecessor": {
            "build06a_branch": "build/build-06a-safe-demo-publication",
            "build06a_commit": EXPECTED_BUILD06A_COMMIT,
            "public_main_commit": EXPECTED_BUILD06A_PUBLIC_COMMIT,
            "publication_sha256": EXPECTED_BUILD06A_PUBLICATION_SHA256,
            "build06_freeze_sha256": EXPECTED_BUILD06_FREEZE_SHA256,
            "build03a_resolution_sha256": EXPECTED_BUILD03A_RESOLUTION_SHA256,
        },
        "demo": {
            "live_url": LIVE_DEMO_URL,
            "verified_file_count": 3,
            "default_hatch_angle_degrees": 45,
            "angle_user_adjustable": True,
        },
        "evaluation_rules": deepcopy(EVALUATION_RULES),
        "gate_items": deepcopy(GATE_ITEMS),
        "boundaries": deepcopy(BOUNDARIES),
    }


def evaluation_template_sha256(template: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(template))
    basis.pop("template_sha256", None)
    return canonical_sha256(basis)


def build_demo_evaluation_template() -> dict[str, Any]:
    template = _template_basis()
    template["template_sha256"] = evaluation_template_sha256(template)
    return template


def validate_demo_evaluation_template(template: Mapping[str, Any]) -> dict[str, Any]:
    actual = deepcopy(dict(template))
    expected = build_demo_evaluation_template()
    if actual != expected:
        _fail(
            "The BUILD-07 evaluation template differs from the frozen contract.",
            "template_mismatch",
        )
    if evaluation_template_sha256(actual) != actual.get("template_sha256"):
        _fail("The BUILD-07 evaluation template identity is invalid.", "template_hash_mismatch")
    return actual


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def evaluation_record_sha256(record: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(record))
    basis.pop("record_sha256", None)
    return canonical_sha256(basis)


def create_demo_evaluation_record(
    template: Mapping[str, Any],
    decisions: Mapping[str, Mapping[str, Any]],
    *,
    evaluated_on: str,
) -> dict[str, Any]:
    frozen = validate_demo_evaluation_template(template)
    if not _valid_date(evaluated_on):
        _fail("The evaluation date must be a valid ISO calendar date.", "date_invalid")

    expected_gate_ids = [item["gate_id"] for item in GATE_ITEMS]
    if set(decisions) != set(expected_gate_ids):
        _fail("Every and only the five BUILD-07 gates must be decided.", "decision_set_invalid")

    normalized: list[dict[str, Any]] = []
    for gate_id in expected_gate_ids:
        supplied = dict(decisions[gate_id])
        allowed_keys = {"verdict", "note_zh_tw"}
        if gate_id == "hatch-angle-transcription":
            allowed_keys.add("preferred_angle_degrees")
        if set(supplied) != allowed_keys:
            _fail(f"Decision fields are invalid for {gate_id}.", "decision_fields_invalid")

        verdict = supplied.get("verdict")
        if verdict not in EVALUATION_RULES["allowed_verdicts"]:
            _fail(f"Decision verdict is invalid for {gate_id}.", "verdict_invalid")
        note = supplied.get("note_zh_tw")
        if not isinstance(note, str):
            _fail(f"Decision note is invalid for {gate_id}.", "note_invalid")
        note = note.strip()
        if len(note) > EVALUATION_RULES["maximum_note_characters"]:
            _fail(f"Decision note is too long for {gate_id}.", "note_invalid")
        if verdict == "request-demo-revision" and not note:
            _fail(f"A revision note is required for {gate_id}.", "revision_note_required")

        decision: dict[str, Any] = {
            "gate_id": gate_id,
            "verdict": verdict,
            "note_zh_tw": note,
        }
        if gate_id == "hatch-angle-transcription":
            angle = supplied.get("preferred_angle_degrees")
            if isinstance(angle, bool) or not isinstance(angle, int) or not 0 <= angle <= 179:
                _fail(
                    "The preferred DEMO angle must be a whole degree in [0, 179].", "angle_invalid"
                )
            if verdict == "accept-current-demo" and angle != 45:
                _fail(
                    "Accepting the current DEMO requires the frozen 45-degree default.",
                    "angle_conflict",
                )
            decision["preferred_angle_degrees"] = angle
        normalized.append(decision)

    revision_count = sum(item["verdict"] == "request-demo-revision" for item in normalized)
    status = (
        EVALUATION_RULES["accepted_result"]
        if revision_count == 0
        else EVALUATION_RULES["revision_result"]
    )
    record = {
        "evaluation_version": EVALUATION_VERSION,
        "schema_version": EVALUATION_SCHEMA,
        "record_type": "human-demo-semantic-evaluation",
        "status": status,
        "template_sha256": frozen["template_sha256"],
        "evaluated_on": evaluated_on,
        "evaluator": {"actor_type": "human-demo-reviewer", "identity_recorded": False},
        "decisions": normalized,
        "summary": {
            "gate_count": len(normalized),
            "accepted_count": len(normalized) - revision_count,
            "revision_requested_count": revision_count,
            "all_five_decisions_explicit": True,
        },
        "boundaries": deepcopy(BOUNDARIES),
    }
    record["record_sha256"] = evaluation_record_sha256(record)
    return validate_demo_evaluation_record(record, frozen)


def validate_demo_evaluation_record(
    record: Mapping[str, Any], template: Mapping[str, Any]
) -> dict[str, Any]:
    frozen = validate_demo_evaluation_template(template)
    actual = deepcopy(dict(record))
    if actual.get("template_sha256") != frozen["template_sha256"]:
        _fail(
            "The evaluation record is not bound to the BUILD-07 template.", "template_hash_mismatch"
        )
    if actual.get("boundaries") != BOUNDARIES:
        _fail("The evaluation record expanded DEMO authority.", "authority_expanded")
    if actual.get("record_sha256") != evaluation_record_sha256(actual):
        _fail("The evaluation record identity is invalid.", "record_hash_mismatch")

    decisions = actual.get("decisions")
    if not isinstance(decisions, list):
        _fail("The evaluation record decisions are invalid.", "decision_set_invalid")
    decision_map: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        if not isinstance(decision, Mapping) or not isinstance(decision.get("gate_id"), str):
            _fail("The evaluation record decisions are invalid.", "decision_set_invalid")
        gate_id = str(decision["gate_id"])
        if gate_id in decision_map:
            _fail("The evaluation record repeats a gate.", "decision_set_invalid")
        decision_map[gate_id] = {key: value for key, value in decision.items() if key != "gate_id"}

    if set(actual) != {
        "evaluation_version",
        "schema_version",
        "record_type",
        "status",
        "template_sha256",
        "evaluated_on",
        "evaluator",
        "decisions",
        "summary",
        "boundaries",
        "record_sha256",
    }:
        _fail("The evaluation record contains unknown fields.", "record_fields_invalid")
    if (
        actual.get("evaluation_version") != EVALUATION_VERSION
        or actual.get("schema_version") != EVALUATION_SCHEMA
    ):
        _fail("The evaluation record version is invalid.", "record_fields_invalid")
    if actual.get("record_type") != "human-demo-semantic-evaluation":
        _fail("The evaluation record type is invalid.", "record_fields_invalid")
    if not _valid_date(actual.get("evaluated_on")):
        _fail("The evaluation date is invalid.", "date_invalid")
    if actual.get("evaluator") != {"actor_type": "human-demo-reviewer", "identity_recorded": False}:
        _fail("The evaluator boundary is invalid.", "evaluator_invalid")

    expected_gate_ids = [item["gate_id"] for item in GATE_ITEMS]
    if [item.get("gate_id") for item in decisions] != expected_gate_ids:
        _fail(
            "The evaluation gates are missing, repeated, or out of order.", "decision_set_invalid"
        )
    revision_count = 0
    for decision in decisions:
        verdict = decision.get("verdict")
        note = decision.get("note_zh_tw")
        allowed_keys = {"gate_id", "verdict", "note_zh_tw"}
        if decision["gate_id"] == "hatch-angle-transcription":
            allowed_keys.add("preferred_angle_degrees")
            angle = decision.get("preferred_angle_degrees")
            if isinstance(angle, bool) or not isinstance(angle, int) or not 0 <= angle <= 179:
                _fail("The preferred DEMO angle is invalid.", "angle_invalid")
            if verdict == "accept-current-demo" and angle != 45:
                _fail(
                    "The accepted DEMO angle conflicts with the frozen default.", "angle_conflict"
                )
        if set(decision) != allowed_keys:
            _fail("The evaluation decision fields are invalid.", "decision_fields_invalid")
        if verdict not in EVALUATION_RULES["allowed_verdicts"]:
            _fail("The evaluation verdict is invalid.", "verdict_invalid")
        if not isinstance(note, str) or note != note.strip() or len(note) > 500:
            _fail("The evaluation note is invalid.", "note_invalid")
        if verdict == "request-demo-revision":
            revision_count += 1
            if not note:
                _fail("A requested revision requires a note.", "revision_note_required")

    expected_status = (
        EVALUATION_RULES["accepted_result"]
        if revision_count == 0
        else EVALUATION_RULES["revision_result"]
    )
    if actual.get("status") != expected_status:
        _fail("The evaluation result status is invalid.", "status_invalid")
    expected_summary = {
        "gate_count": 5,
        "accepted_count": 5 - revision_count,
        "revision_requested_count": revision_count,
        "all_five_decisions_explicit": True,
    }
    if actual.get("summary") != expected_summary:
        _fail("The evaluation result summary is invalid.", "summary_invalid")
    return actual

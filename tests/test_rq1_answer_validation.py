from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ama_demo02_support import ScriptedAdapter, runtime
from nma.research_answer_validation import validate_rq1_answer


QUESTION = (
    "For fire hydrant 9350906, explain the reviewed authoritative portrayal rule. Include "
    "its classification, geometry, line style, color, source evidence, and any unresolved "
    "schema or product-layer binding. Do not infer information that is not supported by the "
    "retrieved evidence."
)
COMPLETE_ANSWER = (
    "Classification 9350906 / 消防栓 uses Point geometry, line style 2, and color 7 / black. "
    "The authoritative source is PDF page 11, record DOC01-P11-HYDRANT, revision NLSC112V5.4. "
    "The ProductLayer binding remains unresolved."
)
STRUCTURED_OUTPUT = {
    "answer": COMPLETE_ANSWER,
    "evidence_node_ids": ["portrayal-rule:doc01:9350906"],
    "citation_ids": ["citation:section:doc01-portrayal:p11"],
    "source_document_ids": ["document:doc01-portrayal"],
    "exact_claims": [
        {
            "node_id": "portrayal-rule:doc01:9350906",
            "property": "feature_code",
            "value": "9350906",
        },
        {
            "node_id": "portrayal-rule:doc01:9350906",
            "property": "feature_name",
            "value": "消防栓",
        },
        {
            "node_id": "portrayal-rule:doc01:9350906",
            "property": "geometry_role",
            "value": "Point",
        },
        {
            "node_id": "portrayal-rule:doc01:9350906",
            "property": "activation_status",
            "value": "non-executable",
        },
    ],
}


def _evidence() -> dict:
    adapter = ScriptedAdapter(
        [
            {"selected_node_ids": ["portrayal-rule:doc01:9350906"]},
            deepcopy(STRUCTURED_OUTPUT),
        ]
    )
    return runtime(adapter).run_rq1(QUESTION)["evidence_package"]


def _validate(answer: str) -> dict:
    output = deepcopy(STRUCTURED_OUTPUT)
    output["answer"] = answer
    return validate_rq1_answer(output, _evidence())


def _claim(result: dict, category: str, value: object) -> dict:
    return next(
        item
        for item in result["claim_grounding"]["claims"]
        if item["normalized_claim"] == {"category": category, "value": value}
    )


def _coverage(result: dict, requirement_id: str) -> str:
    return next(
        item["status"]
        for item in result["question_coverage"]["requirements"]
        if item["id"] == requirement_id
    )


def test_supported_atomic_claims_and_complete_coverage() -> None:
    result = _validate(COMPLETE_ANSWER)

    for category, value in (
        ("feature_code", "9350906"),
        ("feature_name", "消防栓"),
        ("geometry", "Point"),
        ("line_style", "2"),
        ("color_code", "7"),
        ("color_name", "black"),
        ("source_page", "11"),
        ("record_id", "DOC01-P11-HYDRANT"),
        ("revision", "NLSC112V5.4"),
        ("mapping_unresolved", True),
    ):
        assert _claim(result, category, value)["status"] == "SUPPORTED"
    assert result["reference_integrity"]["verdict"] == "PASS"
    assert result["claim_grounding"]["verdict"] == "PASS"
    assert result["question_coverage"]["verdict"] == "PASS"
    assert result["overall_verdict"] == "PASS"


def test_historical_printed_page_ten_is_unsupported_when_metadata_is_unknown() -> None:
    result = _validate(COMPLETE_ANSWER.replace("PDF page 11", "PDF page 11, 打印页10"))

    assert _claim(result, "printed_page", "10")["status"] == "UNSUPPORTED"
    assert result["claim_grounding"]["verdict"] == "FAIL"


def test_unknown_printed_page_remains_supported_as_unknown() -> None:
    result = _validate("The authoritative source is PDF page 11; printed page unknown.")

    assert _claim(result, "printed_page", None)["status"] == "SUPPORTED"


def test_geometry_and_color_contradictions_are_detected() -> None:
    result = _validate(
        COMPLETE_ANSWER.replace("Point geometry", "LineString geometry").replace("black", "red")
    )

    assert _claim(result, "geometry", "LineString")["status"] == "CONTRADICTED"
    assert _claim(result, "color_name", "red")["status"] == "CONTRADICTED"
    assert result["claim_grounding"]["verdict"] == "FAIL"


def test_invented_concrete_product_layer_binding_is_contradicted() -> None:
    result = _validate(
        COMPLETE_ANSWER.replace(
            "The ProductLayer binding remains unresolved.",
            "The ProductLayer = Buildings.",
        )
    )

    assert _claim(result, "product_layer", "Buildings")["status"] == "CONTRADICTED"
    assert _coverage(result, "unresolved_binding") == "PASS"


def test_required_coverage_omissions_are_independent() -> None:
    missing_line = _validate(
        "Classification 9350906 / 消防栓 uses Point geometry and color 7 / black. "
        "Source PDF page 11. ProductLayer binding remains unresolved."
    )
    missing_color = _validate(
        "Classification 9350906 / 消防栓 uses Point geometry and line style 2. "
        "Source PDF page 11. ProductLayer binding remains unresolved."
    )
    missing_source = _validate(
        "Classification 9350906 / 消防栓 uses Point geometry, line style 2, and "
        "color 7 / black. ProductLayer binding remains unresolved."
    )
    missing_binding = _validate(
        "Classification 9350906 / 消防栓 uses Point geometry, line style 2, and "
        "color 7 / black. Source PDF page 11."
    )
    multiple = _validate("Classification 9350906 / 消防栓 uses Point geometry.")

    assert _coverage(missing_line, "line_style") == "FAIL"
    assert _coverage(missing_color, "color") == "FAIL"
    assert _coverage(missing_source, "source_evidence") == "FAIL"
    assert _coverage(missing_binding, "unresolved_binding") == "FAIL"
    assert multiple["question_coverage"]["verdict"] == "FAIL"


def test_grounding_and_coverage_verdicts_are_independent() -> None:
    grounded_incomplete = _validate("Classification 9350906 / 消防栓 uses Point geometry.")
    contradicted_complete = _validate(COMPLETE_ANSWER.replace("black", "red"))
    grounded_complete = _validate(COMPLETE_ANSWER)

    assert (
        grounded_incomplete["claim_grounding"]["verdict"],
        grounded_incomplete["question_coverage"]["verdict"],
    ) == ("PASS", "FAIL")
    assert (
        contradicted_complete["claim_grounding"]["verdict"],
        contradicted_complete["question_coverage"]["verdict"],
    ) == ("FAIL", "PASS")
    assert (
        grounded_complete["claim_grounding"]["verdict"],
        grounded_complete["question_coverage"]["verdict"],
    ) == ("PASS", "PASS")


def test_reference_integrity_remains_separate_and_compatible() -> None:
    output = deepcopy(STRUCTURED_OUTPUT)
    output["evidence_node_ids"] = ["invented:node"]
    output["citation_ids"] = ["citation:invented"]
    result = validate_rq1_answer(output, _evidence())

    assert result["reference_integrity"] == {
        "verdict": "FAIL",
        "evidence_ids_valid": False,
        "citation_ids_valid": False,
    }
    assert result["claim_grounding"]["verdict"] == "PASS"
    assert result["question_coverage"]["verdict"] == "PASS"
    assert result["overall_verdict"] == "FAIL"


def test_validator_preserves_exact_answer_and_makes_no_model_call() -> None:
    output = deepcopy(STRUCTURED_OUTPUT)
    before = deepcopy(output)
    result = validate_rq1_answer(output, _evidence())

    assert output == before
    assert result["validated_answer"] == COMPLETE_ANSWER
    assert result["answer_unchanged"] is True
    assert result["validation_model_calls"] == 0


def test_runtime_exposes_failed_validation_without_repair_or_retry() -> None:
    incomplete = deepcopy(STRUCTURED_OUTPUT)
    incomplete["answer"] = "Classification 9350906 / 消防栓 uses Point geometry."
    adapter = ScriptedAdapter(
        [
            {"selected_node_ids": ["portrayal-rule:doc01:9350906"]},
            incomplete,
        ]
    )

    result = runtime(adapter).run_rq1(QUESTION)

    assert result["validation"] == "failed"
    assert result["answer_validation"]["claim_grounding"]["verdict"] == "PASS"
    assert result["answer_validation"]["question_coverage"]["verdict"] == "FAIL"
    assert result["answer"]["answer"] == incomplete["answer"]
    assert len(adapter.calls) == 2


def test_validator_source_does_not_embed_the_hydrant_answer() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "src/nma/research_answer_validation.py"
    ).read_text(encoding="utf-8")

    assert "9350906" not in source
    assert "fire hydrant" not in source.casefold()
    assert "消防栓" not in source

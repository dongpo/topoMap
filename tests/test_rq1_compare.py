from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from nma.llm import LLMAdapter, LLMResult
from nma.llm.base import canonical_json
from nma.rq1_compare import (
    ANSWER_SCHEMA,
    ARCHITECTURES,
    PROTOCOL_SCHEMA,
    RQ1ComparisonRunner,
    SHARED_INSTRUCTIONS,
    aggregate_results,
    assert_context_safe,
    build_text_corpus,
    evaluate_answer,
    evaluate_text_grounding,
    feature_hash_embedding,
    load_protocol,
    load_questions,
    retrieve_text_chunks,
    sha256_file,
)


ROOT = Path(__file__).resolve().parents[1]
COMPLETE_ANSWER = (
    "Classification 9350906 / 消防栓 uses Point geometry, line style 2, and color 7 / black. "
    "The authoritative source is PDF page 11, record DOC01-P11-HYDRANT, revision NLSC112V5.4. "
    "The ProductLayer binding remains unresolved."
)
GRAPH_OUTPUT = {
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


def _budget(prompt: int = 100) -> dict:
    return {
        "context_window": 8192,
        "prompt_token_estimate": prompt + 30,
        "reserved_output_tokens": 2048,
        "available_input_tokens": 6144,
        "remaining_input_margin": 6014 - prompt,
        "budget_status": "PASS",
        "fits": True,
        "truncation_expected": False,
        "silent_truncation": False,
        "observed_prompt_tokens": prompt,
        "observed_input_margin": 6144 - prompt,
        "observed_within_input_budget": True,
    }


class RecordingAdapter(LLMAdapter):
    def __init__(self, outputs: list[dict]) -> None:
        self.outputs = [deepcopy(item) for item in outputs]
        self.calls: list[dict] = []

    def generate_structured(self, *, task, instructions, context, output_schema) -> LLMResult:
        self.calls.append(
            {
                "task": task,
                "instructions": instructions,
                "context": deepcopy(context),
                "output_schema": deepcopy(output_schema),
            }
        )
        output = self.outputs.pop(0)
        return LLMResult(
            model_id="qwen2.5:latest",
            provider="recorded-local-test",
            output=output,
            latency_ms=1,
            usage={"input_tokens": 100, "output_tokens": 20},
            raw_response_hash=hashlib.sha256(canonical_json(output)).hexdigest(),
            context_budget=_budget(),
        )


@pytest.fixture(scope="module")
def protocol() -> dict:
    return load_protocol(ROOT)


@pytest.fixture(scope="module")
def evidence() -> dict:
    adapter = RecordingAdapter(
        [{"selected_node_ids": ["portrayal-rule:doc01:9350906"]}, GRAPH_OUTPUT]
    )
    _, result = RQ1ComparisonRunner(repository_root=ROOT, adapter=adapter).run_graphrag(
        load_questions(ROOT, load_protocol(ROOT))[0]
    )
    return result["evidence_package"]


def test_protocol_and_variant_fixture_are_frozen(protocol: dict) -> None:
    assert protocol["schema"] == PROTOCOL_SCHEMA
    fixture = ROOT / protocol["question_fixture"]
    assert sha256_file(fixture) == protocol["question_fixture_sha256"]
    questions = load_questions(ROOT, protocol)
    assert len(questions) == 11
    assert len({item["id"] for item in questions}) == 11


def test_variants_preserve_six_requirements_without_answer_leakage(protocol: dict) -> None:
    questions = load_questions(ROOT, protocol)
    requirement_markers = (
        ("classification", "分類", "分类"),
        ("geometry", "幾何", "几何"),
        ("line style", "line styling", "line-style", "line type", "線型", "線式"),
        ("color", "colour", "顏色"),
        ("source", "evidence", "provenance", "來源", "證據"),
        ("binding", "productlayer", "產品圖層", "綁定"),
    )
    forbidden = ("消防栓", "point", "line style 2", "color 7", "black", "page 11")
    for question in questions[1:]:
        lowered = question["text"].casefold()
        assert all(any(marker in lowered for marker in group) for group in requirement_markers)
        assert not any(value in lowered for value in forbidden)


def test_text_corpus_is_deterministic_provenanced_and_graph_free(protocol: dict) -> None:
    first = build_text_corpus(ROOT, protocol)
    second = build_text_corpus(ROOT, protocol)
    assert first == second
    assert len(first) > 10
    assert len({item["chunk_id"] for item in first}) == len(first)
    assert len({item["text_sha256"] for item in first}) == len(first)
    assert all(item["source_path"] in protocol["authoritative_text_sources"] for item in first)
    assert not any("portrayal-rule:" in item["text"] for item in first)
    assert not any("section:doc" in item["text"] for item in first)


def test_feature_hash_embedding_and_text_retrieval_are_stable_and_budgeted(protocol: dict) -> None:
    corpus = build_text_corpus(ROOT, protocol)
    query = "authoritative portrayal for fire hydrant 9350906"
    assert feature_hash_embedding(query) == feature_hash_embedding(query)
    first = retrieve_text_chunks(query, corpus, evidence_token_budget=1600)
    second = retrieve_text_chunks(query, corpus, evidence_token_budget=1600)
    def comparable(result: dict) -> dict:
        return {key: value for key, value in result.items() if key != "retrieval_latency_ms"}

    assert comparable(first) == comparable(second)
    assert first["evidence_tokens"] <= 1600
    assert any("9350906" in item["text"] for item in first["selected_chunks"])
    assert first["selected_chunks"] == sorted(
        first["selected_chunks"], key=lambda item: (-item["similarity"], item["chunk_id"])
    )


def test_llm_only_receives_no_retrieval_evidence(evidence: dict) -> None:
    adapter = RecordingAdapter([{"answer": "I cannot identify the rule with confidence."}])
    runner = RQ1ComparisonRunner(repository_root=ROOT, adapter=adapter)
    runner._run_baseline(
        "llm-only",
        runner.questions[0],
        evidence,
        evidence_budget=1600,
        phase="primary",
    )
    call = adapter.calls[0]
    assert call["context"]["retrieval_status"] == "not-provided"
    assert call["context"]["evidence"] == []
    assert call["output_schema"] == ANSWER_SCHEMA
    assert "9350906" not in call["instructions"]


def test_text_rag_receives_only_text_chunks_without_graph_leakage(evidence: dict) -> None:
    adapter = RecordingAdapter([{"answer": COMPLETE_ANSWER}])
    runner = RQ1ComparisonRunner(repository_root=ROOT, adapter=adapter)
    result = runner._run_baseline(
        "text-rag",
        runner.questions[0],
        evidence,
        evidence_budget=1600,
        phase="primary",
    )
    context = adapter.calls[0]["context"]
    serialized = json.dumps(context, ensure_ascii=False)
    assert context["retrieval_status"] == "authoritative-text-evidence-retrieved"
    assert all(set(item) == {"chunk_id", "source_path", "source_location", "provenance", "text"} for item in context["evidence"])
    assert "portrayal-rule:" not in serialized
    assert "evidence_edges" not in serialized
    assert result["retrieval_evidence_tokens"] <= 1600


def test_graphrag_uses_existing_two_call_runtime_path() -> None:
    adapter = RecordingAdapter(
        [{"selected_node_ids": ["portrayal-rule:doc01:9350906"]}, GRAPH_OUTPUT]
    )
    runner = RQ1ComparisonRunner(repository_root=ROOT, adapter=adapter)
    record, _ = runner.run_graphrag(runner.questions[0])
    assert [item["task"] for item in adapter.calls] == [
        "resolve-bounded-canonical-graph-entities",
        "answer-with-authoritative-canonical-graph-evidence",
    ]
    assert record["retrieved_items"] > record["llm_facing_items"]
    assert record["llm_facing_items"] == 9


def test_shared_prompt_has_identical_semantics_and_no_answer_frame() -> None:
    lowered = SHARED_INSTRUCTIONS.casefold()
    assert "natural prose" in lowered
    assert "fixed answer-slot" in lowered
    assert not any(
        slot in SHARED_INSTRUCTIONS
        for slot in ("Classification:", "Geometry:", "Line style:", "Color:", "Source:")
    )
    assert not any(value in SHARED_INSTRUCTIONS for value in ("9350906", "消防栓", "Point"))


def test_context_safety_accepts_explicit_fit_and_rejects_truncation() -> None:
    assert_context_safe([_budget()])
    unsafe = _budget()
    unsafe["fits"] = False
    with pytest.raises(ValueError, match="no-truncation"):
        assert_context_safe([unsafe])
    silent = _budget()
    silent["silent_truncation"] = True
    with pytest.raises(ValueError, match="no-truncation"):
        assert_context_safe([silent])
    observed = _budget()
    observed["observed_within_input_budget"] = False
    with pytest.raises(ValueError, match="Observed"):
        assert_context_safe([observed])


def test_accuracy_and_coverage_are_independent(evidence: dict) -> None:
    incomplete = evaluate_answer("Classification 9350906 / 消防栓 uses Point geometry.", evidence)
    wrong_complete = evaluate_answer(COMPLETE_ANSWER.replace("black", "red"), evidence)
    complete = evaluate_answer(COMPLETE_ANSWER, evidence)
    assert incomplete["requirement_accuracy"] == pytest.approx(2 / 6)
    assert incomplete["coverage"] == pytest.approx(2 / 6)
    assert wrong_complete["coverage"] == 1
    assert wrong_complete["requirement_accuracy"] == pytest.approx(5 / 6)
    assert complete["requirement_accuracy"] == complete["coverage"] == 1


def test_unresolved_product_layer_guessing_fails(evidence: dict) -> None:
    result = evaluate_answer(
        COMPLETE_ANSWER.replace(
            "The ProductLayer binding remains unresolved.", "The ProductLayer = BUILD."
        ),
        evidence,
    )
    assert result["requirements"]["unresolved_binding"] is False
    assert {item["category"] for item in result["failures"]} & {
        "UNRESOLVED_BINDING_GUESSED",
        "INCORRECT_VALUE",
    }


def test_llm_only_grounding_is_na_and_text_grounding_is_evidence_scoped(evidence: dict) -> None:
    llm_adapter = RecordingAdapter([{"answer": COMPLETE_ANSWER}])
    runner = RQ1ComparisonRunner(repository_root=ROOT, adapter=llm_adapter)
    llm = runner._run_baseline(
        "llm-only", runner.questions[0], evidence, evidence_budget=1600, phase="primary"
    )
    assert llm["grounding"]["retrieval_grounding"] == "N/A"

    retrieved = retrieve_text_chunks(
        runner.questions[0]["text"], runner.corpus, evidence_token_budget=1600
    )
    validation = evaluate_answer(COMPLETE_ANSWER, evidence)["shared_validation"]
    grounding = evaluate_text_grounding(COMPLETE_ANSWER, retrieved, validation)
    assert grounding["supported_count"] > 0
    assert grounding["unsupported_count"] >= 1
    assert grounding["retrieved_reference_integrity"]["verdict"] == "PASS"


def _fake_run(architecture: str, index: int) -> dict:
    requirements = {
        "classification": True,
        "geometry": True,
        "line_style": True,
        "color": True,
        "source_evidence": True,
        "unresolved_binding": index % 2 == 0,
    }
    grounding = (
        {
            "unsupported_factual_assertions": 0,
            "contradicted_factual_assertions": 0,
        }
        if architecture == "llm-only"
        else {"supported_count": 5, "unsupported_count": 0, "contradicted_count": 0}
    )
    return {
        "run_id": f"{architecture}-{index}",
        "architecture": architecture,
        "retrieval_evidence_tokens": 0,
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "total_latency_ms": 10,
        "silent_truncation": False,
        "evaluation": {
            "requirement_accuracy": sum(requirements.values()) / 6,
            "coverage": 1,
            "exact_6_of_6": all(requirements.values()),
            "exact_coverage_6_of_6": True,
            "requirements": requirements,
            "failures": [] if all(requirements.values()) else [{"category": "OMISSION"}],
        },
        "grounding": grounding,
    }


def test_aggregate_counts_reconcile_with_raw_runs() -> None:
    runs = [
        _fake_run(architecture, index)
        for architecture in ARCHITECTURES
        for index in range(11)
    ]
    aggregate = aggregate_results(runs)
    assert len(runs) == 33
    assert len({item["run_id"] for item in runs}) == 33
    assert all(aggregate[architecture]["run_count"] == 11 for architecture in ARCHITECTURES)
    assert all(
        aggregate[architecture]["exact_6_of_6_count"] == 6 for architecture in ARCHITECTURES
    )


def test_committed_result_artifact_reconciles_and_has_no_truncation(protocol: dict) -> None:
    results = json.loads((ROOT / "rq1-compare-01-results.json").read_text(encoding="utf-8"))
    runs = results["raw_runs"]
    repeats = results["reproducibility_runs"]
    assert len(runs) == 33
    assert len(repeats) == 9
    assert len({item["run_id"] for item in [*runs, *repeats]}) == 42
    assert results["aggregate"] == aggregate_results(runs)
    assert all(not item["silent_truncation"] for item in [*runs, *repeats])
    assert all(
        len([item for item in runs if item["architecture"] == architecture]) == 11
        for architecture in ARCHITECTURES
    )
    cap = results["normalization"]["canonical_graphrag_evidence_tokens"]
    assert all(
        item["retrieval_evidence_tokens"] <= cap
        for item in runs
        if item["architecture"] == "text-rag"
    )
    assert results["protocol"] == protocol
    assert results["source_identity"] == {
        path: sha256_file(ROOT / path) for path in protocol["authoritative_text_sources"]
    }
    assert results["text_corpus"]["graph_ids_present"] is False
    assert all(
        results["reproducibility"][architecture]["repeat_count"] == 3
        for architecture in ARCHITECTURES
    )

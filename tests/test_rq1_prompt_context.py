from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from ama_demo02_support import HYDRANT_REQUEST, ScriptedAdapter, runtime
from nma.llm.base import LLMAdapterError
from nma.llm.ollama import OllamaAdapter
from nma.research_context import project_question_relevant_evidence


ROOT = Path(__file__).resolve().parents[1]
RQ1_QUESTION = (
    "For fire hydrant 9350906, explain the reviewed authoritative portrayal rule. Include "
    "its classification, geometry, line style, color, source evidence, and any unresolved "
    "schema or product-layer binding. Do not infer information that is not supported by the "
    "retrieved evidence."
)
ANSWER = {
    "answer": "The reviewed evidence describes a Point portrayal rule.",
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


def _rq1_adapter() -> ScriptedAdapter:
    return ScriptedAdapter(
        [
            {"selected_node_ids": ["portrayal-rule:doc01:9350906"]},
            deepcopy(ANSWER),
        ]
    )


class _Response:
    def __init__(self, payload: dict) -> None:
        self.payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def _envelope(output: dict, *, prompt_tokens: int = 2_000) -> dict:
    return {
        "model": "qwen2.5:latest",
        "message": {"role": "assistant", "content": json.dumps(output, ensure_ascii=False)},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": prompt_tokens,
        "eval_count": 20,
    }


def test_baseline_projection_retains_required_evidence_and_unknown_provenance() -> None:
    adapter = _rq1_adapter()
    result = runtime(adapter).run_rq1(RQ1_QUESTION)
    context = result["llm_evidence_context"]
    nodes = {item["id"]: item for item in context["evidence_nodes"]}

    assert nodes["classification:doc01:9350906"]["properties"] == {
        "code": "9350906",
        "label": "消防栓",
        "mapping_status": (
            "Document 09 has no confirmed ProductLayer/field binding for this Document 01 "
            "class; mapping must remain unresolved."
        ),
    }
    assert nodes["portrayal-geometry:Point"]["properties"]["name"] == "Point"
    assert nodes["line-style:doc01:2"]["properties"]["code"] == "2"
    assert nodes["portrayal-color:doc01:7"]["properties"] == {
        "code": "7",
        "observation": (
            "Rendered row is visually black; exact device-independent colour values are not "
            "stated on the reviewed row."
        ),
        "observed_color": "black",
    }
    citation = context["citations"][0]
    assert citation["citation_id"] == "citation:section:doc01-portrayal:p11"
    assert citation["revision"] == "NLSC112V5.4"
    assert citation["page"] == 11
    assert "printed_page" in citation and citation["printed_page"] is None
    assert context["projection"]["projected_node_count"] < context["projection"][
        "retrieved_node_count"
    ]
    assert len(adapter.calls) == 2
    answer_schema_fields = set(adapter.calls[1]["output_schema"]["properties"])
    assert not answer_schema_fields & {
        "classification",
        "geometry",
        "line_style",
        "color",
        "binding",
    }


def test_projection_is_general_for_non_hydrant_evidence() -> None:
    rule_id = "portrayal-rule:synthetic:1234567"
    section_id = "section:synthetic:p4"
    evidence = {
        "status": "grounded",
        "automatic_rule_activation": False,
        "clarification": {"status": "not-required"},
        "conflicts": [],
        "missing_evidence": [],
        "retrieval_trace": {"model_selected_seed_ids": [rule_id]},
        "evidence_nodes": [
            {
                "id": rule_id,
                "type": "PortrayalRule",
                "properties": {
                    "feature_code": "1234567",
                    "mapping_status": "ProductLayer binding is not confirmed and remains unresolved.",
                },
            },
            {
                "id": "classification:synthetic:1234567",
                "type": "ClassificationCode",
                "properties": {"code": "1234567", "label": "Synthetic feature"},
            },
            {
                "id": "geometry:synthetic:Curve",
                "type": "PortrayalGeometryRole",
                "properties": {"name": "Curve"},
            },
            {
                "id": "line-style:synthetic:4",
                "type": "LineStyleReference",
                "properties": {"code": "4"},
            },
            {
                "id": "color:synthetic:3",
                "type": "PortrayalColorReference",
                "properties": {"code": "3", "observed_color": "blue"},
            },
            {
                "id": section_id,
                "type": "DocumentSection",
                "properties": {"page": 4, "record_id": "SYNTHETIC-P4"},
            },
            {
                "id": "document:synthetic",
                "type": "SpecificationDocument",
                "properties": {"filename": "synthetic.pdf", "revision": "R2"},
            },
            {
                "id": "unrelated:node",
                "type": "ProductionStage",
                "properties": {"name": "unrelated"},
            },
        ],
        "graph_paths": {
            "nodes": [],
            "edges": [
                {
                    "source": "classification:synthetic:1234567",
                    "target": rule_id,
                    "type": "PORTRAYED_BY",
                },
                {
                    "source": rule_id,
                    "target": "geometry:synthetic:Curve",
                    "type": "APPLIES_TO_GEOMETRY",
                },
                {
                    "source": rule_id,
                    "target": "line-style:synthetic:4",
                    "type": "USES_LINE_STYLE",
                },
                {
                    "source": rule_id,
                    "target": "color:synthetic:3",
                    "type": "USES_COLOR",
                },
                {"source": rule_id, "target": section_id, "type": "EVIDENCED_ON"},
                {
                    "source": "document:synthetic",
                    "target": section_id,
                    "type": "CONTAINS",
                },
            ],
        },
        "citations": [
            {
                "citation_id": "citation:synthetic:p4",
                "section_id": section_id,
                "record_id": "SYNTHETIC-P4",
                "document_id": "document:synthetic",
                "filename": "synthetic.pdf",
                "revision": "R2",
                "page": 4,
                "printed_page": None,
                "source_sha256": "a" * 64,
            }
        ],
        "source_documents": [
            {"filename": "synthetic.pdf", "revision": "R2", "sha256": "a" * 64}
        ],
    }

    context = project_question_relevant_evidence(
        question=(
            "Explain the reviewed authoritative portrayal classification, geometry, line style, "
            "color, source evidence, and unresolved product-layer binding."
        ),
        evidence=evidence,
    )
    node_ids = {item["id"] for item in context["evidence_nodes"]}
    assert "unrelated:node" not in node_ids
    assert {
        rule_id,
        "classification:synthetic:1234567",
        "geometry:synthetic:Curve",
        "line-style:synthetic:4",
        "color:synthetic:3",
        section_id,
        "document:synthetic",
    } <= node_ids
    assert context["citations"][0]["printed_page"] is None
    module_source = (ROOT / "src/nma/research_context.py").read_text(encoding="utf-8")
    assert "9350906" not in module_source
    assert "fire hydrant" not in module_source.casefold()


def test_compacted_rq1_prompt_fits_explicit_context_budget(monkeypatch) -> None:
    scripted = _rq1_adapter()
    result = runtime(scripted).run_rq1(RQ1_QUESTION)
    grounded_call = scripted.calls[1]
    submitted = []

    def fake_urlopen(request, timeout):
        submitted.append(request)
        return _Response(_envelope(ANSWER, prompt_tokens=3_200))

    monkeypatch.setattr("nma.llm.ollama.urlopen", fake_urlopen)
    adapter = OllamaAdapter(base_url="http://127.0.0.1:11434", model="qwen2.5:latest")
    model_result = adapter.generate_structured(**grounded_call)

    assert len(submitted) == 1
    assert model_result.context_budget["budget_status"] == "PASS"
    assert model_result.context_budget["fits"] is True
    assert model_result.context_budget["truncation_expected"] is False
    assert model_result.context_budget["silent_truncation"] is False
    assert model_result.context_budget["observed_prompt_tokens"] == 3_200
    assert model_result.context_budget["observed_within_input_budget"] is True
    assert model_result.context_budget["prompt_token_estimate"] <= model_result.context_budget[
        "available_input_tokens"
    ]
    assert model_result.context_budget["remaining_input_margin"] > 0
    assert result["evidence_package"]["evidence_nodes"] != result["llm_evidence_context"][
        "evidence_nodes"
    ]


def test_over_budget_request_fails_before_ollama_invocation(monkeypatch) -> None:
    submitted = []
    events = []

    def fake_urlopen(request, timeout):
        submitted.append(request)
        raise AssertionError("over-budget request reached Ollama")

    monkeypatch.setattr("nma.llm.ollama.urlopen", fake_urlopen)
    adapter = OllamaAdapter(
        base_url="http://127.0.0.1:11434",
        model="qwen2.5:latest",
        context_window=512,
        output_token_reserve=128,
    )
    adapter.set_trace_hook(lambda event, payload: events.append((event, deepcopy(dict(payload)))))

    with pytest.raises(LLMAdapterError, match="exceeds the configured input budget"):
        adapter.generate_structured(
            task="bounded-test",
            instructions="Use only evidence.",
            context={"evidence": "x" * 1_000},
            output_schema={"type": "object"},
        )

    assert submitted == []
    assert [event for event, _ in events] == ["context_budget"]
    assert events[0][1]["budget_status"] == "FAIL"


def test_context_budget_boundary_is_inclusive_and_preflight_is_first(monkeypatch) -> None:
    event_order = []

    def fake_urlopen(request, timeout):
        event_order.append("urlopen")
        return _Response(_envelope({"ok": True}, prompt_tokens=384))

    monkeypatch.setattr("nma.llm.ollama.estimate_ollama_prompt_tokens", lambda messages: 384)
    monkeypatch.setattr("nma.llm.ollama.urlopen", fake_urlopen)
    adapter = OllamaAdapter(
        base_url="http://127.0.0.1:11434",
        model="qwen2.5:latest",
        context_window=512,
        output_token_reserve=128,
    )
    adapter.set_trace_hook(lambda event, payload: event_order.append(event))
    result = adapter.generate_structured(
        task="boundary",
        instructions="Return the object.",
        context={"evidence": True},
        output_schema={"type": "object"},
    )

    assert result.output == {"ok": True}
    assert event_order.index("context_budget") < event_order.index("request")
    assert event_order.index("request") < event_order.index("urlopen")
    assert result.context_budget["remaining_input_margin"] == 0


def test_canonical_graph_bytes_are_unchanged() -> None:
    graph_bytes = (ROOT / "data/knowledge/nma-canonical-graph-v0.4.json").read_bytes()
    assert hashlib.sha256(graph_bytes).hexdigest() == (
        "4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4"
    )


def test_original_short_rq1_path_remains_compatible() -> None:
    adapter = _rq1_adapter()
    result = runtime(adapter).run_rq1(HYDRANT_REQUEST)
    assert result["validation"] == "failed"
    assert result["answer_validation"]["claim_grounding"]["verdict"] == "PASS"
    assert result["answer_validation"]["question_coverage"]["verdict"] == "FAIL"
    assert result["evidence_package"]["retrieval_trace"]["max_depth"] == 2
    assert len(adapter.calls) == 2

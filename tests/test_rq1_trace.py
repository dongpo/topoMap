from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from agent_contracts.governance import request_identity

from ama_demo02_support import ScriptedAdapter
from nma import research_cli
from nma.demo_reporting import SCENARIOS, build_rq1_artifact
from nma.llm.ollama import OllamaAdapter
from nma.research_runtime import AMAResearchRuntime
from nma.research_trace import (
    REDACTION_MARKER,
    RQ1TraceRecorder,
    redact_unexpected_secrets,
)


ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "For fire hydrant 9350906, explain the reviewed authoritative portrayal rule. Include "
    "its classification, geometry, line style, color, source evidence, and any unresolved "
    "schema or product-layer binding. Do not infer information that is not supported by the "
    "retrieved evidence."
)
ANSWER = {
    "answer": (
        "消防栓 9350906 is a reviewed Point portrayal rule using 线型代码2 and color 7 / black; "
        "the authoritative source is PDF page 11; the 产品图层 binding is 未确认 and its "
        "activation status remains non-executable."
    ),
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


def _adapter() -> ScriptedAdapter:
    return ScriptedAdapter(
        [
            {"selected_node_ids": ["portrayal-rule:doc01:9350906"]},
            deepcopy(ANSWER),
        ]
    )


def _recorder() -> RQ1TraceRecorder:
    return RQ1TraceRecorder(
        question=QUESTION,
        repository_root=ROOT,
        scenario=SCENARIOS["rq1"],
        request_identity=request_identity(QUESTION),
    )


def _runtime(adapter: ScriptedAdapter, recorder: RQ1TraceRecorder | None = None):
    return AMAResearchRuntime(
        repository_root=ROOT,
        adapter=adapter,
        graph_settings={
            "NMA_GRAPH_BACKEND": "canonical-json",
            "NMA_GRAPH_FALLBACK": "canonical-json",
        },
        trace_recorder=recorder,
    )


def test_trace_observes_existing_rq1_path_without_changing_results(tmp_path: Path) -> None:
    baseline_adapter = _adapter()
    baseline = _runtime(baseline_adapter).run_rq1(QUESTION)

    traced_adapter = _adapter()
    recorder = _recorder()
    traced = _runtime(traced_adapter, recorder).run_rq1(QUESTION)

    assert traced == baseline
    assert len(traced_adapter.calls) == len(baseline_adapter.calls) == 2
    assert [call["task"] for call in traced_adapter.calls] == [
        "resolve-bounded-canonical-graph-entities",
        "answer-with-authoritative-canonical-graph-evidence",
    ]
    assert recorder.data["question"]["value"].encode("utf-8") == QUESTION.encode("utf-8")

    resolved = recorder.data["resolved_entities"]
    assert resolved[0]["node_id"] == "portrayal-rule:doc01:9350906"
    assert resolved[0]["properties"]["mapping_status"].endswith("mapping must remain unresolved.")
    retrieved = {item["id"]: item for item in recorder.data["retrieved_graph"]["nodes"]}
    assert retrieved["line-style:doc01:2"]["properties"]["code"] == "2"
    assert retrieved["portrayal-color:doc01:7"]["properties"]["observed_color"] == "black"
    assert retrieved["portrayal-geometry:Point"]["properties"]["name"] == "Point"
    assert recorder.data["serialized_evidence"]["value"] == traced["llm_evidence_context"]
    assert (
        recorder.data["llm_request"]["provider_neutral_calls"][1]["context"][
            "authoritative_evidence_context"
        ]
        == traced["llm_evidence_context"]
    )
    assert len(traced["llm_evidence_context"]["evidence_nodes"]) < len(
        traced["evidence_package"]["evidence_nodes"]
    )
    assert (
        recorder.data["llm_raw_response"]["structured_outputs"][1][
            "output_before_runtime_postprocessing"
        ]
        == ANSWER
    )
    assert recorder.data["llm_postprocessing"]["postprocessed_answer_object"] == ANSWER
    assert recorder.data["validator_input"]["answer_text"] == ANSWER["answer"]
    checks = {item["check_name"]: item for item in recorder.data["validator_checks"]}
    assert checks["claim-level natural-language grounding"]["status"] == "PASS"
    assert checks["question-answer coverage"]["status"] == "PASS"

    artifact = build_rq1_artifact(
        traced,
        request=QUESTION,
        started_at="2026-08-27T00:00:00.000000Z",
        total_ms=1,
        trace_recorder=recorder,
    )
    recorder.finalize(result=traced, artifact=artifact)
    diagnosis = {
        item["stage"]: item
        for item in recorder.data["diagnostic_observations"]["diagnostic_matrix"]
    }
    assert diagnosis["Raw Qwen answer covers requested elements"]["observed_status"] == "PASS"
    json_path, text_path = recorder.write(tmp_path)
    persisted = json.loads(json_path.read_text(encoding="utf-8"))
    assert persisted["trace_contract"] == "rq1-trace-01/1.0"
    assert persisted["question"]["value"] == QUESTION
    assert "12. Trace diagnosis" in text_path.read_text(encoding="utf-8")


def test_trace_cli_creates_both_trace_artifacts_and_only_two_model_calls(
    monkeypatch, tmp_path: Path
) -> None:
    adapter = _adapter()
    monkeypatch.setattr(research_cli, "adapter_from_environment", lambda: adapter)
    output_root = tmp_path / "research-demo"

    exit_code = research_cli.main(
        [
            "--repository-root",
            str(ROOT),
            "--output-root",
            str(output_root),
            "rq1",
            "--trace",
            QUESTION,
        ]
    )

    assert exit_code == 0
    run_directory = next(output_root.iterdir())
    assert (run_directory / "rq1-trace.json").is_file()
    assert (run_directory / "rq1-trace.txt").is_file()
    assert len(adapter.calls) == 2
    trace = json.loads((run_directory / "rq1-trace.json").read_text(encoding="utf-8"))
    assert trace["question"]["value"] == QUESTION
    assert trace["retrieved_graph"]["edges"]
    validation = trace["validator_result"]["reporting_validation_labels"]
    assert validation["reference_integrity"]["verdict"] == "PASS"
    assert validation["claim_grounding"]["verdict"] == "PASS"
    assert validation["question_coverage"]["verdict"] == "PASS"
    assert validation["overall_verdict"] == "PASS"
    assert validation["validation_model_calls"] == 0


class _Response:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_ollama_observer_captures_exact_request_and_preparse_raw_response(monkeypatch) -> None:
    output = {"selected_node_ids": ["portrayal-rule:doc01:9350906"]}
    envelope = {
        "model": "qwen2.5:latest",
        "message": {"role": "assistant", "content": json.dumps(output)},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 12,
        "eval_count": 8,
    }
    raw = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return _Response(raw)

    monkeypatch.setattr("nma.llm.ollama.urlopen", fake_urlopen)
    recorder = _recorder()
    adapter = OllamaAdapter(base_url="http://127.0.0.1:11434", model="qwen2.5:latest")
    adapter.set_trace_hook(recorder.record_ollama_event)

    result = adapter.generate_structured(
        task="resolve-bounded-canonical-graph-entities",
        instructions="Select one allowlisted ID.",
        context={"request": QUESTION},
        output_schema={"type": "object"},
    )

    assert result.output == output
    assert len(calls) == 1
    wire = recorder.data["llm_request"]["ollama_wire_calls"][0]
    assert json.loads(wire["serialized_body_utf8"]) == wire["body"]
    assert wire["body"]["model"] == "qwen2.5:latest"
    assert wire["body"]["options"]["num_ctx"] == 8_192
    assert wire["body"]["options"]["num_predict"] == 2_048
    assert recorder.data["context_budget"]["answer_generation"]["budget_status"] == "PASS"
    assert recorder.data["context_budget"]["answer_generation"]["observed_prompt_tokens"] == 12
    captured_raw = recorder.data["llm_raw_response"]["ollama_wire_calls"][0]
    assert captured_raw["raw_response_utf8"] == raw.decode("utf-8")
    assert captured_raw["raw_response_sha256"] == hashlib.sha256(raw).hexdigest()
    assert captured_raw["parsed_envelope_before_content_parsing"] == envelope


def test_secret_redaction_is_field_scoped_and_preserves_evidence() -> None:
    value = {
        "headers": {"Authorization": "Bearer unexpected", "Content-Type": "application/json"},
        "body": {
            "evidence": {"activation_status": "non-executable"},
            "client_secret": "unexpected-secret",
        },
    }
    cleaned, locations = redact_unexpected_secrets(value)
    assert cleaned["headers"]["Authorization"] == REDACTION_MARKER
    assert cleaned["body"]["client_secret"] == REDACTION_MARKER
    assert cleaned["body"]["evidence"] == value["body"]["evidence"]
    assert locations == ["$.headers.Authorization", "$.body.client_secret"]

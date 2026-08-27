from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from ama_demo02_support import HYDRANT_REQUEST, ScriptedAdapter
from nma import research_cli


ANSWER = {
    "answer": (
        "Classification 9350906 / 消防栓 uses Point geometry, line style 2, and color 7 / "
        "black. The authoritative source is PDF page 11. The ProductLayer binding remains "
        "unresolved; activation status remains non-executable."
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


def _adapter(answer: dict = ANSWER) -> ScriptedAdapter:
    return ScriptedAdapter([{"selected_node_ids": ["portrayal-rule:doc01:9350906"]}, answer])


def _result(output_root: Path) -> dict:
    path = next(output_root.glob("*/result.json"))
    return json.loads(path.read_text(encoding="utf-8"))


def test_rq1_cli_writes_human_and_machine_grounded_evidence_artifacts(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    monkeypatch.setattr(research_cli, "adapter_from_environment", _adapter)
    output = tmp_path / "research-demo"
    exit_code = research_cli.main(
        [
            "--repository-root",
            str(Path(__file__).resolve().parents[1]),
            "--output-root",
            str(output),
            "rq1",
            HYDRANT_REQUEST,
        ]
    )
    assert exit_code == 0
    artifact = _result(output)
    summary = next(output.glob("*/summary.txt")).read_text(encoding="utf-8")
    stdout = capsys.readouterr().out
    assert artifact["model"] == {
        "provider": "recorded-local-test",
        "model_id": "qwen-test-recording",
    }
    assert artifact["graph_backend"]["active_backend"] == "canonical-json"
    assert artifact["validation"]["reference_integrity"]["verdict"] == "PASS"
    assert artifact["validation"]["claim_grounding"]["verdict"] == "PASS"
    assert artifact["validation"]["question_coverage"]["verdict"] == "PASS"
    assert artifact["validation"]["overall_verdict"] == "PASS"
    assert artifact["evidence_node_ids"] == ["portrayal-rule:doc01:9350906"]
    assert artifact["citations"][0]["citation_id"] == ("citation:section:doc01-portrayal:p11")
    assert "Graph evidence" in summary
    assert "Overall answer validation: PASS" in summary
    assert "Model provider: recorded-local-test" in stdout


def test_rq1_cli_returns_nonzero_when_model_invents_evidence(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    invented = deepcopy(ANSWER)
    invented["evidence_node_ids"] = ["invented:node"]
    monkeypatch.setattr(research_cli, "adapter_from_environment", lambda: _adapter(invented))
    exit_code = research_cli.main(
        [
            "--repository-root",
            str(Path(__file__).resolve().parents[1]),
            "--output-root",
            str(tmp_path / "research-demo"),
            "rq1",
            HYDRANT_REQUEST,
        ]
    )
    assert exit_code == 2
    assert "failed closed" in capsys.readouterr().err

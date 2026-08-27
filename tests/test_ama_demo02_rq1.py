from __future__ import annotations

from copy import deepcopy

import pytest

from ama_demo02_support import HYDRANT_REQUEST, ScriptedAdapter, runtime
from nma.llm import LLMAdapterError


ANSWER = {
    "answer": (
        "Fire hydrant feature 9350906 is a reviewed Point portrayal rule; its activation "
        "status remains non-executable."
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


def test_rq1_invokes_provider_neutral_model_retrieval_and_grounded_generation() -> None:
    adapter = ScriptedAdapter(
        [
            {"selected_node_ids": ["portrayal-rule:doc01:9350906"]},
            ANSWER,
        ]
    )
    result = runtime(adapter).run_rq1(HYDRANT_REQUEST)
    assert result["validation"] == "passed"
    assert result["provider"] == "recorded-local-test"
    assert result["graph_backend"]["active_backend"] == "canonical-json"
    assert result["graph_backend"]["arbitrary_cypher_allowed"] is False
    assert [item["task"] for item in adapter.calls] == [
        "resolve-bounded-canonical-graph-entities",
        "answer-with-authoritative-canonical-graph-evidence",
    ]
    assert "authoritative_evidence_package" in adapter.calls[1]["context"]
    assert result["execution_performed"] is False


def test_rq1_unknown_evidence_and_citations_fail_closed() -> None:
    invented = deepcopy(ANSWER)
    invented["evidence_node_ids"] = ["invented:node"]
    adapter = ScriptedAdapter(
        [
            {"selected_node_ids": ["portrayal-rule:doc01:9350906"]},
            invented,
        ]
    )
    with pytest.raises(LLMAdapterError, match="required constant"):
        runtime(adapter).run_rq1(HYDRANT_REQUEST)


def test_rq1_changed_exact_reviewed_identity_fails_closed() -> None:
    changed = deepcopy(ANSWER)
    changed["exact_claims"][0]["value"] = "9350999"
    adapter = ScriptedAdapter(
        [
            {"selected_node_ids": ["portrayal-rule:doc01:9350906"]},
            changed,
        ]
    )
    with pytest.raises(LLMAdapterError, match="required constant"):
        runtime(adapter).run_rq1(HYDRANT_REQUEST)


def test_rq1_model_cannot_select_non_allowlisted_graph_seed() -> None:
    adapter = ScriptedAdapter([{"selected_node_ids": ["invented:node"]}])
    with pytest.raises(LLMAdapterError, match="allowed values"):
        runtime(adapter).run_rq1(HYDRANT_REQUEST)

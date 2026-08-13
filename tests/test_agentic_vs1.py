import json
from pathlib import Path

import pytest

from nma.agentic_vs1 import (
    GroundingValidationError,
    build_agent_trace,
    build_grounded_answer_payload,
    grounding_requirements_for_package,
    parse_grounded_answer,
    usage_summary,
)
from nma.graphrag import CanonicalGraphRetriever


ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"


def school_package() -> dict:
    return CanonicalGraphRetriever.load(GRAPH).evidence_package(
        "小學 9920103 圖式規則", max_depth=3, max_nodes=30
    )


def answer_response(package: dict, **overrides) -> dict:
    citation_id = package["citations"][0]["citation_id"]
    requirements = grounding_requirements_for_package(package)
    answer = {
        "status": "answered",
        "answer": "小學圖式規則見正式規格表第 61 頁。",
        "resolved_entity_ids": [
            item["id"] for item in package.get("resolved_entities", [])
        ],
        "evidence_node_ids": requirements["required_evidence_node_ids"],
        "citation_ids": [citation_id],
        "missing_evidence": [],
        "next_action": "inspect_symbol",
    }
    answer.update(overrides)
    return {
        "id": "resp_answer",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(answer)}],
            }
        ],
        "usage": {
            "input_tokens": 1_000,
            "input_tokens_details": {"cached_tokens": 200},
            "output_tokens": 100,
            "total_tokens": 1_100,
        },
    }


def test_vs1_resolves_route_tool_with_evidence_and_strict_schema() -> None:
    package = school_package()
    payload = build_grounded_answer_payload(
        model="gpt-5.6-terra",
        route_response_id="resp_route",
        route_call_id="call_route",
        question="小學的圖式規則在哪一頁？",
        evidence_package=package,
    )

    assert payload["previous_response_id"] == "resp_route"
    assert payload["input"][0]["type"] == "function_call_output"
    assert payload["input"][0]["call_id"] == "call_route"
    evidence = json.loads(payload["input"][0]["output"])
    assert evidence["status"] == "retrieved"
    assert evidence["automatic_rule_activation"] is False
    document_01 = next(
        item
        for item in evidence["citations"]
        if item["citation_id"] == "citation:section:doc01-portrayal:p61"
    )
    assert document_01["filename"] == "01-一千分之一地形圖圖式規格表.pdf"
    assert document_01["page"] == 61
    assert evidence["answer_requirements"] == {
        "mode": "reviewed-portrayal-rule",
        "feature_code": "9920103",
        "source_page": 61,
        "required_evidence_node_ids": [
            "portrayal-rule:doc01:9920103",
            "section:doc01-portrayal:p61",
            "symbol:doc01:school-flag",
        ],
        "required_citation_ids": ["citation:section:doc01-portrayal:p61"],
    }
    assert "graph_paths" not in evidence
    assert payload["instructions"]
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    dynamic_schema = payload["text"]["format"]["schema"]
    assert dynamic_schema["properties"]["resolved_entity_ids"]["items"][
        "enum"
    ] == [item["id"] for item in package["resolved_entities"]]
    assert dynamic_schema["properties"]["evidence_node_ids"]["items"][
        "enum"
    ] == [item["id"] for item in package["evidence_nodes"]]
    assert dynamic_schema["properties"]["citation_ids"]["items"]["enum"] == [
        item["citation_id"] for item in package["citations"]
    ]
    assert payload["store"] is True


def test_vs1_accepts_only_identifiers_from_the_evidence_package() -> None:
    package = school_package()
    parsed = parse_grounded_answer(answer_response(package), package)

    assert parsed["schema"] == "nma.grounded-answer/1.0"
    assert parsed["status"] == "answered"
    assert parsed["automatic_action"] is False

    with pytest.raises(GroundingValidationError, match="invented an evidence"):
        parse_grounded_answer(
            answer_response(package, evidence_node_ids=["invented:node"]), package
        )
    with pytest.raises(GroundingValidationError, match="invented a citation"):
        parse_grounded_answer(
            answer_response(package, citation_ids=["citation:invented"]), package
        )
    with pytest.raises(GroundingValidationError, match="copy the authoritative"):
        parse_grounded_answer(
            answer_response(package, resolved_entity_ids=[]), package
        )


def test_portrayal_answer_cannot_substitute_annex_classification_for_document_01() -> None:
    package = school_package()
    requirements = grounding_requirements_for_package(package)
    annex = next(
        item["citation_id"]
        for item in package["citations"]
        if item.get("filename") == "02-一千分之一數值航測地形圖測製作業規定.pdf"
    )
    response = answer_response(
        package,
        evidence_node_ids=requirements["required_evidence_node_ids"],
        citation_ids=[annex],
    )

    with pytest.raises(GroundingValidationError, match="required Document 01"):
        parse_grounded_answer(response, package)


def test_vs1_abstention_package_cannot_be_promoted_to_an_answer() -> None:
    package = CanonicalGraphRetriever.load(GRAPH).evidence_package(
        "不存在於官方語料的虛構星際傳送門圖徵"
    )
    response = answer_response(
        school_package(),
        resolved_entity_ids=[],
        evidence_node_ids=[],
        citation_ids=[],
    )

    with pytest.raises(GroundingValidationError, match="cannot produce an answer"):
        parse_grounded_answer(response, package)


def test_vs1_reports_usage_and_estimated_terra_cost_without_exposing_reasoning() -> None:
    package = school_package()
    response = answer_response(package)
    usage = usage_summary(response, "gpt-5.6-terra")
    trace = build_agent_trace(
        model="gpt-5.6-terra",
        route_response=response,
        evidence_package=package,
        answer_response=response,
        grounded_answer=parse_grounded_answer(response, package),
        timings_ms={"route": 10, "retrieve": 2, "answer": 12},
    )

    assert usage["estimated_cost_usd"] == pytest.approx(0.00355)
    assert usage["pricing_status"] == "estimated-from-token-usage"
    assert trace["hidden_chain_of_thought_exposed"] is False
    assert [event["stage"] for event in trace["events"]] == [
        "observe",
        "route",
        "resolve",
        "policy_validate",
        "retrieve",
        "traverse",
        "ground",
        "answer",
        "validate",
    ]
    assert trace["automatic_action"] is False

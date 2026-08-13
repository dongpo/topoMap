from __future__ import annotations

import json
from typing import Any


QA_PLANNING_SCHEMA = "nma.qa-planning-response/0.4"

INSTRUCTIONS = """You are the bounded QA reasoning stage of a supervised National Map Agent.
The application supplies deterministic defect observations, exact rule evidence, a canonical
GraphRAG package, and one allowlisted safe repair set. Explain each observed issue and distinguish
safe repair from manual review. Copy issue keys, severities, repair classifications, operations,
evidence pages, graph nodes, and citations exactly. Never invent a defect, numeric result, repair,
approval, acceptance decision, or completed action. A safe repair remains a proposal until the
owner explicitly approves it. Unresolved errors must remain visible after a safe repair. Return
concise Traditional Chinese and no hidden chain-of-thought.
"""


class QAPlanningError(ValueError):
    """The LLM QA response violated the deterministic inspection boundary."""


def expected_diagnoses(report: dict[str, Any]) -> list[dict[str, Any]]:
    diagnoses = []
    for issue in report["issues"]:
        repair = issue.get("repair", {})
        mode = repair.get("mode", "none")
        classification = {
            "safe": "safe-repairable",
            "proposal": "manual-review-required",
            "none": "not-automatically-repairable",
        }[mode]
        diagnoses.append(
            {
                "issue_key": issue["issue_key"],
                "severity": issue["severity"],
                "classification": classification,
                "operation": repair.get("operation") or "none",
                "evidence_page": issue["evidence"]["page"],
            }
        )
    return diagnoses


def _schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["proposed", "abstained"]},
            "reply": {"type": "string"},
            "diagnoses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string"},
                        "severity": {"type": "string", "enum": ["error", "warning"]},
                        "classification": {
                            "type": "string",
                            "enum": [
                                "safe-repairable",
                                "manual-review-required",
                                "not-automatically-repairable",
                            ],
                        },
                        "operation": {
                            "type": "string",
                            "enum": [
                                "trim",
                                "review_classification",
                                "review_geometry",
                                "review_schema_mapping",
                                "none"
                            ],
                        },
                        "evidence_page": {"type": "integer"},
                    },
                    "required": [
                        "issue_key",
                        "severity",
                        "classification",
                        "operation",
                        "evidence_page",
                    ],
                    "additionalProperties": False,
                },
                "maxItems": 50,
            },
            "safe_repair_issue_keys": {"type": "array", "items": {"type": "string"}},
            "evidence_node_ids": {"type": "array", "items": {"type": "string"}},
            "citation_ids": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "status",
            "reply",
            "diagnoses",
            "safe_repair_issue_keys",
            "evidence_node_ids",
            "citation_ids",
        ],
        "additionalProperties": False,
    }


def build_qa_plan_payload(
    *, model: str, user_request: str, qa_plan: dict[str, Any], evidence_package: dict[str, Any]
) -> dict[str, Any]:
    supplied = {
        "user_request": user_request,
        "dataset_kind": qa_plan["dataset_kind"],
        "boundary": qa_plan["boundary"],
        "inspection": {
            "status": qa_plan["before_status"],
            "summary": qa_plan["before_report"]["summary"],
            "issues": qa_plan["before_report"]["issues"],
        },
        "allowlisted_safe_repairs": qa_plan["safe_repairs"],
        "manual_review_issue_keys": qa_plan["manual_review_issue_keys"],
        "evidence": {
            "status": evidence_package.get("status"),
            "evidence_nodes": evidence_package.get("evidence_nodes", []),
            "citations": evidence_package.get("citations", []),
        },
        "approval_granted": False,
        "automatic_acceptance": False,
    }
    return {
        "model": model,
        "instructions": INSTRUCTIONS,
        "input": [{"role": "user", "content": json.dumps(supplied, ensure_ascii=False)}],
        "reasoning": {"effort": "low"},
        "text": {
            "verbosity": "low",
            "format": {
                "type": "json_schema",
                "name": "nma_qa_plan",
                "schema": _schema(),
                "strict": True,
            },
        },
        "store": True,
    }


def _output_text(response: Any) -> str:
    if not isinstance(response, dict) or not isinstance(response.get("id"), str):
        raise QAPlanningError("The QA response has no response identifier.")
    if isinstance(response.get("output_text"), str) and response["output_text"].strip():
        return response["output_text"]
    texts = []
    for item in response.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                texts.append(content.get("text"))
    if len(texts) != 1 or not isinstance(texts[0], str):
        raise QAPlanningError("Expected exactly one QA planning response.")
    return texts[0]


def parse_qa_plan_response(
    response: Any, *, qa_plan: dict[str, Any], evidence_package: dict[str, Any]
) -> dict[str, Any]:
    try:
        result = json.loads(_output_text(response))
    except json.JSONDecodeError as error:
        raise QAPlanningError("The QA response was not valid JSON.") from error
    required = set(_schema()["required"])
    if not isinstance(result, dict) or set(result) != required:
        raise QAPlanningError("The QA response has an invalid shape.")
    if result["status"] not in {"proposed", "abstained"}:
        raise QAPlanningError("The QA response has an invalid status.")
    if not isinstance(result["reply"], str) or not result["reply"].strip():
        raise QAPlanningError("The QA response reply is empty.")
    expected = expected_diagnoses(qa_plan["before_report"])
    expected_safe = [item["issue_key"] for item in qa_plan["safe_repairs"]]
    if result["status"] == "proposed":
        if result["diagnoses"] != expected:
            raise QAPlanningError("The LLM changed deterministic QA observations.")
        if result["safe_repair_issue_keys"] != expected_safe:
            raise QAPlanningError("The LLM changed the reviewed safe-repair set.")
        if set(result["evidence_node_ids"]) != set(qa_plan["evidence_node_ids"]):
            raise QAPlanningError("The LLM changed the reviewed QA graph nodes.")
        allowed_citations = {
            item.get("citation_id")
            for item in evidence_package.get("citations", [])
            if isinstance(item, dict)
        }
        if not result["citation_ids"] or not set(result["citation_ids"]).issubset(
            allowed_citations
        ):
            raise QAPlanningError("The LLM invented or omitted QA citations.")
    elif any(
        result[key]
        for key in ("diagnoses", "safe_repair_issue_keys", "evidence_node_ids", "citation_ids")
    ):
        raise QAPlanningError("An abstention cannot claim QA observations or evidence.")
    return {
        "schema": QA_PLANNING_SCHEMA,
        "response_id": response["id"],
        **result,
        "plan_id": qa_plan["plan_id"],
        "approval_granted": False,
        "repair_executed": False,
        "automatic_acceptance": False,
    }

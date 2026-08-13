from __future__ import annotations

import json
from typing import Any

from nma.portrayal_review import PortrayalReviewError, validate_portrayal_edit_plan


PORTRAYAL_PLAN_RESPONSE_SCHEMA = "nma.portrayal-plan-response/0.4"

OPERATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "set_color",
                "set_opacity",
                "set_stroke_width",
                "set_scale",
                "set_rotation",
                "set_fill_pattern",
                "set_line_pattern",
                "set_hatch_spacing",
                "set_text_visibility",
            ],
        },
        "target": {
            "type": "string",
            "enum": [
                "portrayal",
                "marker",
                "interior-marker",
                "stroke",
                "fill",
                "outline",
                "hatch",
                "text",
            ],
        },
        "value": {
            "type": "object",
            "properties": {
                "color": {
                    "type": ["string", "null"],
                    "enum": [
                        "#111111",
                        "#ffffff",
                        "#c62828",
                        "#1565c0",
                        "#2e7d32",
                        "#f9a825",
                        "#ef6c00",
                        "#6d7772",
                        "#6a1b9a",
                        None,
                    ],
                },
                "number": {"type": ["number", "null"]},
                "pattern": {
                    "type": ["string", "null"],
                    "enum": ["solid", "dash", "dot", "hatch", "none", None],
                },
                "boolean": {"type": ["boolean", "null"]},
            },
            "required": ["color", "number", "pattern", "boolean"],
            "additionalProperties": False,
        },
    },
    "required": ["action", "target", "value"],
    "additionalProperties": False,
}

PLAN_RESPONSE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["proposed", "clarification-required", "abstained"],
        },
        "reply": {"type": "string"},
        "feature_code": {"type": "string"},
        "geometry_role": {"type": "string", "enum": ["Point", "LineString", "Polygon"]},
        "operations": {"type": "array", "maxItems": 12, "items": OPERATION_SCHEMA},
        "evidence_node_ids": {"type": "array", "items": {"type": "string"}},
        "citation_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "status",
        "reply",
        "feature_code",
        "geometry_role",
        "operations",
        "evidence_node_ids",
        "citation_ids",
    ],
    "additionalProperties": False,
}

INSTRUCTIONS = """You are the bounded portrayal-planning stage of a supervised National Map
Agent. The application supplies one reviewed official portrayal baseline, a bounded graph evidence
package, an optional previously approved preference context, and a user's requested visual
preference. The official baseline is immutable. Translate only the user's new requested difference
into allowlisted operations; do not repeat unchanged approved preferences. Do not generate SVG, paths, code,
coordinates, source facts, approval, or execution claims. Use marker for Point symbols, stroke for
LineString portrayal, fill/outline/hatch for Polygon portrayal, interior-marker for a symbol placed
inside a Polygon, and text for annotations. A colour operation sets only color; numeric operations
set only number; pattern operations set only pattern; visibility sets only boolean. Set all unused
value fields to null. Cite only supplied evidence node and citation IDs. If the request cannot be
represented safely, return clarification-required or abstained with zero operations. Return concise
Traditional Chinese and no hidden chain-of-thought.
"""


class PortrayalPlanningError(ValueError):
    """The LLM portrayal response violated the bounded planning contract."""


def build_portrayal_plan_payload(
    *,
    model: str,
    user_request: str,
    baseline: dict[str, Any],
    evidence_package: dict[str, Any],
    approved_preference_ir: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bounded = {
        "user_request": user_request,
        "official_baseline": baseline,
        "approved_preference_context": approved_preference_ir,
        "evidence": {
            "status": evidence_package.get("status"),
            "resolved_entities": evidence_package.get("resolved_entities", []),
            "evidence_nodes": evidence_package.get("evidence_nodes", []),
            "citations": evidence_package.get("citations", []),
            "missing_evidence": evidence_package.get("missing_evidence", []),
            "automatic_rule_activation": evidence_package.get(
                "automatic_rule_activation", False
            ),
        },
    }
    return {
        "model": model,
        "instructions": INSTRUCTIONS,
        "input": [
            {
                "role": "user",
                "content": json.dumps(bounded, ensure_ascii=False, separators=(",", ":")),
            }
        ],
        "reasoning": {"effort": "low"},
        "text": {
            "verbosity": "low",
            "format": {
                "type": "json_schema",
                "name": "nma_portrayal_plan_response",
                "description": "A bounded user-preference plan over an immutable official baseline.",
                "schema": PLAN_RESPONSE_JSON_SCHEMA,
                "strict": True,
            },
        },
        "store": True,
    }


def _output_text(response: Any) -> str:
    if not isinstance(response, dict) or not isinstance(response.get("id"), str):
        raise PortrayalPlanningError("The portrayal response has no response identifier.")
    direct = response.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    texts: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if (
                isinstance(content, dict)
                and content.get("type") == "output_text"
                and isinstance(content.get("text"), str)
            ):
                texts.append(content["text"])
    if len(texts) != 1:
        raise PortrayalPlanningError("Expected exactly one portrayal plan response.")
    return texts[0]


def parse_portrayal_plan_response(
    response: Any,
    *,
    expected_feature_code: str,
    expected_geometry_role: str,
    expected_source_rule_id: str,
    expected_source_page: int,
    evidence_package: dict[str, Any],
) -> dict[str, Any]:
    try:
        result = json.loads(_output_text(response))
    except json.JSONDecodeError as error:
        raise PortrayalPlanningError("The portrayal response was not valid JSON.") from error
    expected = set(PLAN_RESPONSE_JSON_SCHEMA["required"])
    if not isinstance(result, dict) or set(result) != expected:
        raise PortrayalPlanningError("The portrayal response has an invalid shape.")
    if result["status"] not in {"proposed", "clarification-required", "abstained"}:
        raise PortrayalPlanningError("The portrayal response has an invalid status.")
    if not isinstance(result["reply"], str) or not result["reply"].strip():
        raise PortrayalPlanningError("The portrayal response reply is empty.")
    if result["feature_code"] != expected_feature_code:
        raise PortrayalPlanningError("The portrayal response changed the selected feature.")
    if result["geometry_role"] != expected_geometry_role:
        raise PortrayalPlanningError("The portrayal response changed the reviewed geometry.")
    if not isinstance(result["operations"], list):
        raise PortrayalPlanningError("The portrayal operations are invalid.")
    if result["status"] == "proposed" and not result["operations"]:
        raise PortrayalPlanningError("A proposed portrayal response requires operations.")
    if result["status"] != "proposed" and result["operations"]:
        raise PortrayalPlanningError("A non-proposal response cannot contain operations.")
    allowed_nodes = {
        item.get("id")
        for item in evidence_package.get("evidence_nodes", [])
        if isinstance(item, dict)
    }
    allowed_citations = {
        item.get("citation_id")
        for item in evidence_package.get("citations", [])
        if isinstance(item, dict)
    }
    if not isinstance(result["evidence_node_ids"], list) or not set(
        result["evidence_node_ids"]
    ).issubset(allowed_nodes):
        raise PortrayalPlanningError("The portrayal response invented an evidence node.")
    if not isinstance(result["citation_ids"], list) or not set(result["citation_ids"]).issubset(
        allowed_citations
    ):
        raise PortrayalPlanningError("The portrayal response invented a citation.")
    if result["status"] == "proposed" and (
        not result["evidence_node_ids"] or not result["citation_ids"]
    ):
        raise PortrayalPlanningError("A portrayal proposal must cite graph and document evidence.")
    relevant_citations = {
        item.get("citation_id")
        for item in evidence_package.get("citations", [])
        if isinstance(item, dict) and item.get("page") == expected_source_page
    }
    if result["status"] == "proposed" and expected_source_rule_id not in result[
        "evidence_node_ids"
    ]:
        raise PortrayalPlanningError("The portrayal proposal did not cite its reviewed source rule.")
    if result["status"] == "proposed" and not set(result["citation_ids"]).intersection(
        relevant_citations
    ):
        raise PortrayalPlanningError("The portrayal proposal did not cite its reviewed source page.")
    if result["status"] == "proposed":
        normalized_operations = []
        for operation in result["operations"]:
            value = operation.get("value", {}) if isinstance(operation, dict) else {}
            populated = {key: item for key, item in value.items() if item is not None}
            normalized_operations.append({**operation, "value": populated})
        plan = {
            "schema": "nma.portrayal-edit-plan/0.4",
            "source": "responses-api",
            "feature_code": expected_feature_code,
            "geometry_role": expected_geometry_role,
            "operations": normalized_operations,
        }
        try:
            validate_portrayal_edit_plan(plan)
        except PortrayalReviewError as error:
            raise PortrayalPlanningError(str(error)) from error
    else:
        plan = None
    return {
        "schema": PORTRAYAL_PLAN_RESPONSE_SCHEMA,
        "response_id": response["id"],
        **result,
        "plan": plan,
        "automatic_action": False,
    }

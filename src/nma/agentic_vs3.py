from __future__ import annotations

import json
from typing import Any


REAL_LAYER_PLANNING_SCHEMA = "nma.real-layer-planning-response/0.4"

INSTRUCTIONS = """You are the bounded real-layer planning stage of a supervised National Map
Agent. The application supplies one reviewed candidate mapping, a canonical GraphRAG evidence
package, and the user's request. Select the candidate only when it satisfies the request. Copy all
machine fields exactly: profile, feature, geometry, product layer, source layers, filter, field
mapping, and operations. Explain the mapping and its dataset-specific schema boundary in concise
Traditional Chinese. Never invent paths, fields, codes, geometry, coordinates, citations,
approval, execution, or a successful map result. Never alter or activate an official portrayal
rule. If the candidate is not applicable, return clarification-required or abstained with empty
evidence and citation arrays. Return no hidden chain-of-thought.
"""


class RealLayerPlanningError(ValueError):
    """The LLM real-layer response violated its bounded candidate contract."""


def _schema(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["proposed", "clarification-required", "abstained"],
            },
            "reply": {"type": "string"},
            "profile_id": {"type": "string", "enum": [candidate["profile_id"]]},
            "feature_code": {"type": "string", "enum": [candidate["feature_code"]]},
            "feature_name": {"type": "string", "enum": [candidate["feature_name"]]},
            "geometry_role": {"type": "string", "enum": [candidate["geometry_role"]]},
            "product_layer": {"type": "string", "enum": [candidate["product_layer"]]},
            "source_layers": {
                "type": "array",
                "items": {"type": "string", "enum": candidate["source_layer_ids"]},
                "maxItems": len(candidate["source_layer_ids"]),
            },
            "source_filter": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "enum": [candidate["feature_code_field"]],
                    },
                    "operator": {"type": "string", "enum": ["equals"]},
                    "value": {"type": "string", "enum": [candidate["feature_code"]]},
                },
                "required": ["field", "operator", "value"],
                "additionalProperties": False,
            },
            "field_mapping": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "enum": [candidate["id_field"]]},
                    "feature_code": {
                        "type": "string",
                        "enum": [candidate["feature_code_field"]],
                    },
                    "label": {
                        "type": ["string", "null"],
                        "enum": [candidate["label_field"]],
                    },
                },
                "required": ["id", "feature_code", "label"],
                "additionalProperties": False,
            },
            "operations": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "extract-reviewed-components",
                        "filter",
                        "reproject-to-epsg-4326",
                        "drop-z",
                    ],
                },
                "maxItems": 4,
            },
            "evidence_node_ids": {"type": "array", "items": {"type": "string"}},
            "citation_ids": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "status",
            "reply",
            "profile_id",
            "feature_code",
            "feature_name",
            "geometry_role",
            "product_layer",
            "source_layers",
            "source_filter",
            "field_mapping",
            "operations",
            "evidence_node_ids",
            "citation_ids",
        ],
        "additionalProperties": False,
    }


def build_real_layer_plan_payload(
    *,
    model: str,
    user_request: str,
    profile_id: str,
    candidate: dict[str, Any],
    evidence_package: dict[str, Any],
) -> dict[str, Any]:
    bounded_candidate = {
        "profile_id": profile_id,
        **candidate,
        "required_operations": [
            "extract-reviewed-components",
            "filter",
            "reproject-to-epsg-4326",
            "drop-z",
        ],
    }
    supplied = {
        "user_request": user_request,
        "reviewed_candidate": bounded_candidate,
        "evidence": {
            "status": evidence_package.get("status"),
            "evidence_nodes": evidence_package.get("evidence_nodes", []),
            "citations": evidence_package.get("citations", []),
            "automatic_rule_activation": False,
        },
    }
    return {
        "model": model,
        "instructions": INSTRUCTIONS,
        "input": [
            {
                "role": "user",
                "content": json.dumps(supplied, ensure_ascii=False, separators=(",", ":")),
            }
        ],
        "reasoning": {"effort": "low"},
        "text": {
            "verbosity": "low",
            "format": {
                "type": "json_schema",
                "name": "nma_real_layer_plan",
                "schema": _schema(bounded_candidate),
                "strict": True,
            },
        },
        "store": True,
    }


def _output_text(response: Any) -> str:
    if not isinstance(response, dict) or not isinstance(response.get("id"), str):
        raise RealLayerPlanningError("The real-layer response has no response identifier.")
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
        raise RealLayerPlanningError("Expected exactly one real-layer planning response.")
    return texts[0]


def parse_real_layer_plan_response(
    response: Any,
    *,
    profile_id: str,
    candidate: dict[str, Any],
    evidence_package: dict[str, Any],
) -> dict[str, Any]:
    try:
        result = json.loads(_output_text(response))
    except json.JSONDecodeError as error:
        raise RealLayerPlanningError("The real-layer response was not valid JSON.") from error
    required = set(_schema({"profile_id": profile_id, **candidate})["required"])
    if not isinstance(result, dict) or set(result) != required:
        raise RealLayerPlanningError("The real-layer response has an invalid shape.")
    if result["status"] not in {"proposed", "clarification-required", "abstained"}:
        raise RealLayerPlanningError("The real-layer response has an invalid status.")
    if not isinstance(result["reply"], str) or not result["reply"].strip():
        raise RealLayerPlanningError("The real-layer response reply is empty.")
    expected = {
        "profile_id": profile_id,
        "feature_code": candidate["feature_code"],
        "feature_name": candidate["feature_name"],
        "geometry_role": candidate["geometry_role"],
        "product_layer": candidate["product_layer"],
        "source_layers": candidate["source_layer_ids"],
        "source_filter": {
            "field": candidate["feature_code_field"],
            "operator": "equals",
            "value": candidate["feature_code"],
        },
        "field_mapping": {
            "id": candidate["id_field"],
            "feature_code": candidate["feature_code_field"],
            "label": candidate["label_field"],
        },
        "operations": [
            "extract-reviewed-components",
            "filter",
            "reproject-to-epsg-4326",
            "drop-z",
        ],
    }
    for key, expected_value in expected.items():
        if result[key] != expected_value:
            raise RealLayerPlanningError(f"The LLM changed the reviewed {key} mapping.")
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
    if result["status"] == "proposed":
        if set(result["evidence_node_ids"]) != set(candidate["evidence_node_ids"]):
            raise RealLayerPlanningError("The LLM omitted or changed reviewed evidence nodes.")
        if not result["citation_ids"] or not set(result["citation_ids"]).issubset(
            allowed_citations
        ):
            raise RealLayerPlanningError("The LLM invented or omitted source citations.")
        if not set(result["evidence_node_ids"]).issubset(allowed_nodes):
            raise RealLayerPlanningError("The LLM invented graph evidence.")
    elif result["evidence_node_ids"] or result["citation_ids"]:
        raise RealLayerPlanningError("A non-proposal cannot claim evidence selection.")
    return {
        "schema": REAL_LAYER_PLANNING_SCHEMA,
        "response_id": response["id"],
        **result,
        "source_schema_boundary": candidate["source_schema_boundary"],
        "approval_granted": False,
        "execution_performed": False,
        "automatic_action": False,
    }

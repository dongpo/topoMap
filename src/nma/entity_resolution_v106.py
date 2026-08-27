from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .entity_resolution_v10 import (
    ENTITY_RESOLUTION_INSTRUCTIONS,
    RESPONSES_URL,
    _response_output_text,
    build_entity_resolution_payload,
)
from .entity_resolution_v105 import normalize_entity_resolution_v105


ENTITY_RESOLUTION_SCHEMA_V106 = "nma.entity-resolution/0.10.6"
CACHE_SCHEMA_V106 = "nma.entity-resolution-cache/0.10.6"
MAX_RESOLVED_ENTITIES_V106 = 8


class EntityResolutionV106Error(ValueError):
    """The v0.10.6 bounded multi-entity resolution contract is invalid."""


def entity_resolution_json_schema_v106() -> dict[str, Any]:
    payload = build_entity_resolution_payload(
        model="schema-only", candidate_pool={"schema": "nma.entity-candidate-pool/0.10"}
    )
    schema = copy.deepcopy(payload["text"]["format"]["schema"])
    schema["properties"]["resolved_entities"]["maxItems"] = (
        MAX_RESOLVED_ENTITIES_V106
    )
    return schema


ENTITY_RESOLUTION_JSON_SCHEMA_V106 = entity_resolution_json_schema_v106()


def build_entity_resolution_payload_v106(
    *, model: str, candidate_pool: dict[str, Any]
) -> dict[str, Any]:
    if candidate_pool.get("schema") not in {
        "nma.entity-candidate-pool/0.10",
        "nma.entity-candidate-pool/0.10.1",
    }:
        raise EntityResolutionV106Error("Unsupported candidate-pool schema.")
    evidence = json.dumps(candidate_pool, ensure_ascii=False, separators=(",", ":"))
    return {
        "model": model,
        "instructions": (
            ENTITY_RESOLUTION_INSTRUCTIONS
            + " The structured response may select up to eight independently supported "
            "entities; do not omit a coordinated segment merely because more than three "
            "entities are requested."
        ),
        "input": [
            {
                "role": "user",
                "content": (
                    "Resolve the original request only from this bounded candidate pool. "
                    f"Candidate pool: {evidence}"
                ),
            }
        ],
        "reasoning": {"effort": "low"},
        "text": {
            "verbosity": "low",
            "format": {
                "type": "json_schema",
                "name": "nma_entity_resolution_v106",
                "description": (
                    "Bounded selection of up to eight entities, clarification, or abstention."
                ),
                "schema": ENTITY_RESOLUTION_JSON_SCHEMA_V106,
                "strict": True,
            },
        },
        "store": False,
    }


def parse_entity_resolution_v106(
    response: Any, candidate_pool: dict[str, Any]
) -> dict[str, Any]:
    try:
        resolution = json.loads(_response_output_text(response))
    except json.JSONDecodeError as error:
        raise EntityResolutionV106Error("Resolver output was not valid JSON.") from error
    required = set(ENTITY_RESOLUTION_JSON_SCHEMA_V106["required"])
    if not isinstance(resolution, dict) or set(resolution) != required:
        raise EntityResolutionV106Error("Resolver output has an invalid shape.")
    if resolution["status"] not in {
        "resolved",
        "needs-clarification",
        "abstained-no-match",
    }:
        raise EntityResolutionV106Error("Resolver status is invalid.")
    entities = resolution["resolved_entities"]
    if not isinstance(entities, list) or len(entities) > MAX_RESOLVED_ENTITIES_V106:
        raise EntityResolutionV106Error("Resolver entity count is invalid.")
    allowed_ids = {
        item["node_id"] for item in candidate_pool.get("candidate_records", [])
    }
    selected_ids: list[str] = []
    allowed_basis = {
        "official-name",
        "source-instruction",
        "geometry-role",
        "hierarchy-context",
    }
    for entity in entities:
        if not isinstance(entity, dict) or set(entity) != {
            "query_segment",
            "selected_node_id",
            "confidence",
            "evidence_basis",
        }:
            raise EntityResolutionV106Error("A resolved entity has an invalid shape.")
        node_id = entity["selected_node_id"]
        if node_id not in allowed_ids:
            raise EntityResolutionV106Error(
                "Resolver selected a node outside the candidate pool."
            )
        if node_id in selected_ids:
            raise EntityResolutionV106Error("Resolver selected a duplicate node.")
        if entity["confidence"] not in {"high", "medium", "low"}:
            raise EntityResolutionV106Error("Resolver confidence is invalid.")
        if not isinstance(entity["query_segment"], str) or not entity[
            "query_segment"
        ].strip():
            raise EntityResolutionV106Error("Resolver query segment is empty.")
        basis = entity["evidence_basis"]
        if (
            not isinstance(basis, list)
            or not basis
            or any(item not in allowed_basis for item in basis)
        ):
            raise EntityResolutionV106Error("Resolver evidence basis is invalid.")
        selected_ids.append(node_id)
    if resolution["status"] == "resolved" and not entities:
        raise EntityResolutionV106Error("Resolved status requires an entity.")
    if resolution["status"] == "abstained-no-match" and entities:
        raise EntityResolutionV106Error("Abstention cannot select an entity.")
    if (
        resolution["status"] == "needs-clarification"
        and not str(resolution["clarification_question"]).strip()
    ):
        raise EntityResolutionV106Error("Clarification requires a question.")
    if not isinstance(resolution["decision_summary"], str) or not resolution[
        "decision_summary"
    ].strip():
        raise EntityResolutionV106Error("Resolver decision summary is empty.")
    usage = response.get("usage", {}) if isinstance(response, dict) else {}
    return {
        "schema": ENTITY_RESOLUTION_SCHEMA_V106,
        "status": resolution["status"],
        "resolved_entities": entities,
        "clarification_question": resolution["clarification_question"],
        "decision_summary": resolution["decision_summary"],
        "selected_node_ids": selected_ids,
        "candidate_pool_sha256": candidate_pool["pool_sha256"],
        "response_id": response["id"],
        "response_model": response.get("model"),
        "usage": {
            "input_tokens": int(usage.get("input_tokens", 0) or 0),
            "output_tokens": int(usage.get("output_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
        },
        "hidden_chain_of_thought_exposed": False,
        "automatic_rule_activation": False,
    }


class OpenAIEntityResolverV106:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-5.6-terra",
        url: str = RESPONSES_URL,
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key.strip():
            raise EntityResolutionV106Error("OpenAI API key is empty.")
        self._api_key = api_key
        self.model = model
        self.url = url
        self.timeout_seconds = timeout_seconds

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        payload = build_entity_resolution_payload_v106(
            model=self.model, candidate_pool=candidate_pool
        )
        request = Request(
            self.url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise EntityResolutionV106Error(
                f"OpenAI resolver request failed with HTTP {error.code}."
            ) from error
        except (URLError, TimeoutError) as error:
            raise EntityResolutionV106Error(
                "OpenAI resolver request could not reach the API."
            ) from error
        except json.JSONDecodeError as error:
            raise EntityResolutionV106Error(
                "OpenAI resolver response was not valid JSON."
            ) from error
        return parse_entity_resolution_v106(body, candidate_pool)


class PolicyValidatedEntityResolverV106:
    def __init__(self, resolver: Any):
        if not callable(getattr(resolver, "resolve", None)):
            raise EntityResolutionV106Error("Wrapped resolver is not callable.")
        self.resolver = resolver
        self.model = getattr(resolver, "model", None)

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        raw = self.resolver.resolve(candidate_pool)
        normalized = normalize_entity_resolution_v105(
            raw, candidate_pool=candidate_pool
        )
        normalized["schema"] = ENTITY_RESOLUTION_SCHEMA_V106
        normalized["policy_validation"]["policy_v106"] = (
            "v0.10.5 bounded policies plus native structured output up to eight entities"
        )
        normalized["policy_validation"]["structured_output_max_entities"] = (
            MAX_RESOLVED_ENTITIES_V106
        )
        normalized["raw_resolution_snapshot"] = {
            "schema": raw.get("schema"),
            "status": raw.get("status"),
            "resolved_entities": copy.deepcopy(raw.get("resolved_entities", [])),
            "selected_node_ids": list(raw.get("selected_node_ids", [])),
            "clarification_question": raw.get("clarification_question", ""),
            "decision_summary": raw.get("decision_summary", ""),
            "response_id": raw.get("response_id"),
            "response_model": raw.get("response_model"),
            "usage": copy.deepcopy(raw.get("usage", {})),
            "hidden_chain_of_thought_exposed": False,
        }
        return normalized


class EntityResolutionCacheV106:
    def __init__(self, payload: dict[str, Any]):
        if payload.get("schema") != CACHE_SCHEMA_V106:
            raise EntityResolutionV106Error("Unsupported v0.10.6 cache schema.")
        records = payload.get("records", [])
        self.payload = payload
        self.by_query_sha = {record["query_sha256"]: record for record in records}
        if len(self.by_query_sha) != len(records):
            raise EntityResolutionV106Error("Cache contains duplicate query hashes.")

    @classmethod
    def load(cls, path: str | Path) -> "EntityResolutionCacheV106":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        record = self.by_query_sha.get(candidate_pool["query_sha256"])
        if not record:
            raise EntityResolutionV106Error("Cache has no matching query.")
        if record["candidate_pool_sha256"] != candidate_pool["pool_sha256"]:
            raise EntityResolutionV106Error("Cache candidate pool differs.")
        resolution = record["resolution"]
        if resolution.get("schema") != ENTITY_RESOLUTION_SCHEMA_V106:
            raise EntityResolutionV106Error("Cached resolution schema is invalid.")
        allowed = {
            item["node_id"] for item in candidate_pool.get("candidate_records", [])
        }
        if not set(resolution.get("selected_node_ids", [])).issubset(allowed):
            raise EntityResolutionV106Error(
                "Cached resolution selected a node outside the pool."
            )
        return resolution

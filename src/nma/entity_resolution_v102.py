from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ENTITY_RESOLUTION_SCHEMA_V102 = "nma.entity-resolution/0.10.2"
CACHE_SCHEMA_V102 = "nma.entity-resolution-cache/0.10.2"


class EntityResolutionV102Error(ValueError):
    """The v0.10.2 policy-normalized resolution contract is invalid."""


class PolicyValidatedEntityResolverV102:
    """Wrap a live resolver and preserve raw output before policy normalization."""

    def __init__(self, resolver: Any):
        if not callable(getattr(resolver, "resolve", None)):
            raise EntityResolutionV102Error("The wrapped entity resolver is not callable.")
        self.resolver = resolver
        self.model = getattr(resolver, "model", None)

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        raw = self.resolver.resolve(candidate_pool)
        normalized = normalize_hierarchy_clarification(
            raw, candidate_pool=candidate_pool
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


def normalize_hierarchy_clarification(
    resolution: dict[str, Any],
    *,
    candidate_pool: dict[str, Any],
) -> dict[str, Any]:
    """Anchor a uniquely named hierarchy omitted from an otherwise valid clarification.

    This validator does not infer from benchmark IDs, vector rank, or paraphrases. It
    requires an exact official hierarchy name in the model's own user-facing output.
    """

    normalized = copy.deepcopy(resolution)
    normalized["schema"] = ENTITY_RESOLUTION_SCHEMA_V102
    normalized["policy_validation"] = {
        "policy": "unique-exact-official-hierarchy-name-in-model-output",
        "source_resolution_schema": resolution.get("schema"),
        "outcome": "not-applicable",
        "selected_node_id": None,
        "new_openai_request": False,
        "automatic_rule_activation": False,
    }
    if resolution.get("status") != "needs-clarification":
        return normalized
    if resolution.get("resolved_entities") or resolution.get("selected_node_ids"):
        normalized["policy_validation"]["outcome"] = "already-anchored"
        return normalized

    model_text = "\n".join(
        [
            str(resolution.get("clarification_question", "")),
            str(resolution.get("decision_summary", "")),
        ]
    )
    matches = [
        item
        for item in candidate_pool.get("candidate_records", [])
        if item.get("official_status") == "classification-hierarchy"
        and str(item.get("canonical_name", ""))
        and str(item["canonical_name"]) in model_text
    ]
    unique_ids = {item["node_id"] for item in matches}
    if len(unique_ids) != 1:
        normalized["policy_validation"]["outcome"] = (
            "no-exact-anchor" if not unique_ids else "ambiguous-exact-anchors"
        )
        return normalized

    selected = matches[0]
    normalized["resolved_entities"] = [
        {
            "query_segment": selected["canonical_name"],
            "selected_node_id": selected["node_id"],
            "confidence": "high",
            "evidence_basis": ["official-name", "hierarchy-context"],
        }
    ]
    normalized["selected_node_ids"] = [selected["node_id"]]
    normalized["policy_validation"].update(
        {
            "outcome": "unique-exact-hierarchy-anchor-added",
            "selected_node_id": selected["node_id"],
        }
    )
    return normalized


class EntityResolutionCacheV102:
    def __init__(self, payload: dict[str, Any]):
        if payload.get("schema") != CACHE_SCHEMA_V102:
            raise EntityResolutionV102Error("Unsupported v0.10.2 cache schema.")
        self.payload = payload
        self.by_query_sha = {
            record["query_sha256"]: record for record in payload.get("records", [])
        }
        if len(self.by_query_sha) != len(payload.get("records", [])):
            raise EntityResolutionV102Error("Cache contains duplicate query hashes.")

    @classmethod
    def load(cls, path: str | Path) -> "EntityResolutionCacheV102":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        query_sha = hashlib.sha256(
            candidate_pool["query"].encode("utf-8")
        ).hexdigest()
        record = self.by_query_sha.get(query_sha)
        if not record:
            raise EntityResolutionV102Error("Cache has no matching query.")
        if record["candidate_pool_sha256"] != candidate_pool["pool_sha256"]:
            raise EntityResolutionV102Error("Cache candidate pool differs.")
        resolution = record["resolution"]
        if resolution.get("schema") != ENTITY_RESOLUTION_SCHEMA_V102:
            raise EntityResolutionV102Error("Cached resolution schema is invalid.")
        allowed = {item["node_id"] for item in candidate_pool["candidate_records"]}
        if not set(resolution.get("selected_node_ids", [])).issubset(allowed):
            raise EntityResolutionV102Error(
                "Cached resolution selected a node outside the candidate pool."
            )
        return resolution

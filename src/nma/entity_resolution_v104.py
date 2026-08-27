from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from .entity_resolution_v103 import (
    infer_coordinated_query_segments,
    normalize_hierarchy_clarification_v103,
)


ENTITY_RESOLUTION_SCHEMA_V104 = "nma.entity-resolution/0.10.4"
CACHE_SCHEMA_V104 = "nma.entity-resolution-cache/0.10.4"
STRONG_MULTI_ENTITY_MARKERS = ("比較", "分別", "各自", "兩者")


class EntityResolutionV104Error(ValueError):
    """The v0.10.4 validated-policy contract is invalid."""


def is_explicit_coordinated_multi_entity_query(query: str) -> bool:
    if not any(marker in query for marker in STRONG_MULTI_ENTITY_MARKERS):
        return False
    return len(infer_coordinated_query_segments(query)) > 1


def normalize_hierarchy_clarification_v104(
    resolution: dict[str, Any], *, candidate_pool: dict[str, Any]
) -> dict[str, Any]:
    normalized = normalize_hierarchy_clarification_v103(
        resolution, candidate_pool=candidate_pool
    )
    normalized["schema"] = ENTITY_RESOLUTION_SCHEMA_V104
    normalized["policy_validation"]["policy_v104"] = (
        "validated-v102-exact-name-then-unique-explicit-official-hierarchy-code"
    )
    return normalized


class PolicyValidatedEntityResolverV104:
    def __init__(self, resolver: Any):
        if not callable(getattr(resolver, "resolve", None)):
            raise EntityResolutionV104Error("The wrapped entity resolver is not callable.")
        self.resolver = resolver
        self.model = getattr(resolver, "model", None)
        if hasattr(resolver, "query_cache"):
            self.query_cache = resolver.query_cache

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        raw = self.resolver.resolve(candidate_pool)
        normalized = normalize_hierarchy_clarification_v104(
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


class EntityResolutionCacheV104:
    def __init__(self, payload: dict[str, Any]):
        if payload.get("schema") != CACHE_SCHEMA_V104:
            raise EntityResolutionV104Error("Unsupported v0.10.4 cache schema.")
        self.payload = payload
        self.by_query_sha = {
            record["query_sha256"]: record for record in payload.get("records", [])
        }
        if len(self.by_query_sha) != len(payload.get("records", [])):
            raise EntityResolutionV104Error("Cache contains duplicate query hashes.")

    @classmethod
    def load(cls, path: str | Path) -> "EntityResolutionCacheV104":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        query_sha = hashlib.sha256(candidate_pool["query"].encode("utf-8")).hexdigest()
        record = self.by_query_sha.get(query_sha)
        if not record:
            raise EntityResolutionV104Error("Cache has no matching query.")
        if record["candidate_pool_sha256"] != candidate_pool["pool_sha256"]:
            raise EntityResolutionV104Error("Cache candidate pool differs.")
        resolution = record["resolution"]
        if resolution.get("schema") != ENTITY_RESOLUTION_SCHEMA_V104:
            raise EntityResolutionV104Error("Cached resolution schema is invalid.")
        allowed = {item["node_id"] for item in candidate_pool["candidate_records"]}
        if not set(resolution.get("selected_node_ids", [])).issubset(allowed):
            raise EntityResolutionV104Error("Cached resolution selected a node outside the pool.")
        return resolution

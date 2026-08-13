from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .entity_resolution_v10 import _canonical_sha256
from .entity_resolution_v101 import build_candidate_pool_v101
from .entity_resolution_v102 import normalize_hierarchy_clarification


ENTITY_RESOLUTION_SCHEMA_V103 = "nma.entity-resolution/0.10.3"
CACHE_SCHEMA_V103 = "nma.entity-resolution-cache/0.10.3"
MULTI_ENTITY_MARKERS = ("比較", "以及", "與", "分別", "各自", "兩者")
COORDINATION_PATTERN = re.compile(r"\s*(?:，)?(?:以及|與)\s*")
EXPLICIT_CODE_PATTERN = re.compile(r"(?<![0-9A-Za-z])([0-9]{7})(?![0-9A-Za-z])")


class EntityResolutionV103Error(ValueError):
    """The v0.10.3 segment-balanced or policy-validated contract is invalid."""


def infer_coordinated_query_segments(query: str) -> list[str]:
    """Return bounded deterministic segments only for explicit coordination syntax."""

    if not any(marker in query for marker in MULTI_ENTITY_MARKERS):
        return [query]
    parts = [part.strip(" ，。；;：:") for part in COORDINATION_PATTERN.split(query)]
    parts = [part for part in parts if len(part) >= 4]
    if len(parts) < 2:
        return [query]
    return parts[:3]


def is_coordinated_multi_entity_query(query: str) -> bool:
    return len(infer_coordinated_query_segments(query)) > 1


def _sum_usage(usages: list[dict[str, Any]]) -> dict[str, int]:
    keys = {key for usage in usages for key in usage if isinstance(usage.get(key), int)}
    return {key: sum(int(usage.get(key, 0)) for usage in usages) for key in sorted(keys)}


def build_candidate_pool_v103(
    query: str,
    *,
    vector_index: Any,
    query_cache: Any,
    candidate_set: dict[str, Any],
    resolution_support: dict[str, Any],
    geometry_role_scheme: dict[str, Any],
    **limits: int,
) -> dict[str, Any]:
    """Balance a saturated coordinated query across deterministic query segments.

    Unsaturated and single-entity pools are returned byte-for-byte compatible with
    v0.10.1 so verified raw resolution records remain reusable.
    """

    base = build_candidate_pool_v101(
        query,
        vector_index=vector_index,
        query_cache=query_cache,
        candidate_set=candidate_set,
        resolution_support=resolution_support,
        geometry_role_scheme=geometry_role_scheme,
        **limits,
    )
    segments = infer_coordinated_query_segments(query)
    max_candidates = int(limits.get("max_candidates", 128))
    if len(segments) < 2 or len(base["candidate_records"]) < max_candidates:
        return base

    segment_pools = [
        build_candidate_pool_v101(
            segment,
            vector_index=vector_index,
            query_cache=query_cache,
            candidate_set=candidate_set,
            resolution_support=resolution_support,
            geometry_role_scheme=geometry_role_scheme,
            **limits,
        )
        for segment in segments
    ]
    sources = segment_pools + [base]
    records_by_id: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    for rank in range(max(len(pool["candidate_records"]) for pool in sources)):
        for source_index, pool in enumerate(sources):
            records = pool["candidate_records"]
            if rank >= len(records):
                continue
            record = records[rank]
            node_id = record["node_id"]
            if node_id in records_by_id:
                continue
            enriched = copy.deepcopy(record)
            enriched["full_query_vector_rank"] = (
                record["vector_rank"] if source_index == len(segment_pools) else None
            )
            enriched["segment_vector_ranks"] = (
                {segments[source_index]: record["vector_rank"]}
                if source_index < len(segment_pools)
                else {}
            )
            enriched["inclusion_reasons"] = sorted(
                set(enriched.get("inclusion_reasons", []))
                | {
                    "segment-balanced-union"
                    if source_index < len(segment_pools)
                    else "full-query-union"
                }
            )
            records_by_id[node_id] = enriched
            ordered_ids.append(node_id)
            if len(ordered_ids) >= max_candidates:
                break
        if len(ordered_ids) >= max_candidates:
            break
    records = []
    for rank, node_id in enumerate(ordered_ids, 1):
        record = records_by_id[node_id]
        record["vector_rank"] = rank
        records.append(record)

    result = copy.deepcopy(base)
    result.pop("pool_sha256", None)
    result.update(
        {
            "candidate_records": records,
            "candidate_pool_policy_version": "0.10.3",
            "multi_entity_segmentation": {
                "strategy": "deterministic-explicit-coordination-segment-balanced-union",
                "segments": segments,
                "base_pool_saturated": True,
                "answer_keys_used": False,
            },
            "query_embedding_usage": _sum_usage(
                [base.get("query_embedding_usage", {})]
                + [pool.get("query_embedding_usage", {}) for pool in segment_pools]
            ),
            "segment_query_embedding_usage": [
                {
                    "segment_sha256": hashlib.sha256(segment.encode("utf-8")).hexdigest(),
                    "usage": pool.get("query_embedding_usage", {}),
                }
                for segment, pool in zip(segments, segment_pools, strict=True)
            ],
        }
    )
    result["pool_sha256"] = _canonical_sha256(result)
    return result


def normalize_hierarchy_clarification_v103(
    resolution: dict[str, Any], *, candidate_pool: dict[str, Any]
) -> dict[str, Any]:
    normalized = normalize_hierarchy_clarification(
        resolution, candidate_pool=candidate_pool
    )
    normalized["schema"] = ENTITY_RESOLUTION_SCHEMA_V103
    normalized["policy_validation"]["policy_v103"] = (
        "v102-exact-name-then-unique-explicit-official-hierarchy-code-in-model-output"
    )
    if resolution.get("status") != "needs-clarification":
        return normalized
    if normalized.get("selected_node_ids"):
        return normalized

    model_text = "\n".join(
        [
            str(resolution.get("clarification_question", "")),
            str(resolution.get("decision_summary", "")),
        ]
    )
    explicit_codes = set(EXPLICIT_CODE_PATTERN.findall(model_text))
    matches = [
        item
        for item in candidate_pool.get("candidate_records", [])
        if item.get("official_status") == "classification-hierarchy"
        and str(item.get("feature_code")) in explicit_codes
    ]
    unique_ids = {item["node_id"] for item in matches}
    if len(unique_ids) != 1:
        normalized["policy_validation"]["v103_code_outcome"] = (
            "no-explicit-hierarchy-code"
            if not unique_ids
            else "ambiguous-explicit-hierarchy-codes"
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
            "outcome": "unique-explicit-official-hierarchy-code-anchor-added",
            "selected_node_id": selected["node_id"],
            "v103_code_outcome": "unique-explicit-official-hierarchy-code",
            "new_openai_request": False,
            "automatic_rule_activation": False,
        }
    )
    return normalized


class PolicyValidatedEntityResolverV103:
    def __init__(self, resolver: Any):
        if not callable(getattr(resolver, "resolve", None)):
            raise EntityResolutionV103Error("The wrapped entity resolver is not callable.")
        self.resolver = resolver
        self.model = getattr(resolver, "model", None)
        if hasattr(resolver, "query_cache"):
            self.query_cache = resolver.query_cache

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        raw = self.resolver.resolve(candidate_pool)
        normalized = normalize_hierarchy_clarification_v103(
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


class EntityResolutionCacheV103:
    def __init__(self, payload: dict[str, Any]):
        if payload.get("schema") != CACHE_SCHEMA_V103:
            raise EntityResolutionV103Error("Unsupported v0.10.3 cache schema.")
        self.payload = payload
        self.by_query_sha = {
            record["query_sha256"]: record for record in payload.get("records", [])
        }
        if len(self.by_query_sha) != len(payload.get("records", [])):
            raise EntityResolutionV103Error("Cache contains duplicate query hashes.")

    @classmethod
    def load(cls, path: str | Path) -> "EntityResolutionCacheV103":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        query_sha = hashlib.sha256(candidate_pool["query"].encode("utf-8")).hexdigest()
        record = self.by_query_sha.get(query_sha)
        if not record:
            raise EntityResolutionV103Error("Cache has no matching query.")
        if record["candidate_pool_sha256"] != candidate_pool["pool_sha256"]:
            raise EntityResolutionV103Error("Cache candidate pool differs.")
        resolution = record["resolution"]
        if resolution.get("schema") != ENTITY_RESOLUTION_SCHEMA_V103:
            raise EntityResolutionV103Error("Cached resolution schema is invalid.")
        allowed = {item["node_id"] for item in candidate_pool["candidate_records"]}
        if not set(resolution.get("selected_node_ids", [])).issubset(allowed):
            raise EntityResolutionV103Error("Cached resolution selected a node outside the pool.")
        return resolution

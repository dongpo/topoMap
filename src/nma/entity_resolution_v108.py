from __future__ import annotations

import copy
import hashlib
from typing import Any

from .entity_resolution_v10 import _canonical_sha256
from .entity_resolution_v107 import build_candidate_pool_v107


CANDIDATE_POOL_POLICY_V108 = "0.10.8"


class EntityResolutionV108Error(ValueError):
    """The v0.10.8 cache-trace or final-cap contract is invalid."""


class _TraceableSegmentQueryCache:
    """Add a verified deterministic query hash without changing the sealed cache."""

    def __init__(self, cache: Any):
        self.cache = cache

    def embed_query(self, query: str, model: str, dimensions: int) -> dict[str, Any]:
        result = dict(self.cache.embed_query(query, model, dimensions))
        expected = hashlib.sha256(query.encode("utf-8")).hexdigest()
        supplied = result.get("query_sha256")
        if supplied is not None and supplied != expected:
            raise EntityResolutionV108Error(
                "Segment cache returned a mismatched query SHA-256."
            )
        result["query_sha256"] = expected
        return result


def _segment_priority(record: dict[str, Any]) -> tuple[int, float, str]:
    hits = record.get("segment_hits", [])
    if not hits:
        return (10**9, 0.0, record["node_id"])
    return (
        min(int(hit["rank"]) for hit in hits),
        -max(float(hit["similarity"]) for hit in hits),
        record["node_id"],
    )


def _apply_post_union_cap(
    pool: dict[str, Any], *, final_candidate_cap: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    if final_candidate_cap < 1:
        raise EntityResolutionV108Error("Final candidate cap must be positive.")
    records = list(pool["candidate_records"])
    segment_records = [record for record in records if record.get("segment_hits")]
    base_records = [record for record in records if not record.get("segment_hits")]
    ordered_segment = sorted(segment_records, key=_segment_priority)

    segment_budget = min(len(ordered_segment), final_candidate_cap)
    retained_segment = ordered_segment[:segment_budget]
    base_budget = final_candidate_cap - len(retained_segment)
    retained_base = base_records[:base_budget]
    retained_ids = {
        record["node_id"] for record in retained_base + retained_segment
    }
    evicted = [
        record["node_id"]
        for record in records
        if record["node_id"] not in retained_ids
    ]

    result = copy.deepcopy(pool)
    result.pop("pool_sha256", None)
    result["candidate_records"] = retained_base + retained_segment
    result["limits"] = {
        **result.get("limits", {}),
        "post_union_max_candidates": final_candidate_cap,
    }
    trace = {
        "strategy": "retain-canonical-base-prefix-plus-ranked-segment-additions",
        "pre_cap_candidate_records": len(records),
        "base_records_before_cap": len(base_records),
        "segment_records_before_cap": len(segment_records),
        "final_candidate_cap": final_candidate_cap,
        "final_candidate_records": len(result["candidate_records"]),
        "retained_base_records": len(retained_base),
        "retained_segment_records": len(retained_segment),
        "evicted_records": len(evicted),
        "evicted_node_ids": evicted,
        "answer_keys_used": False,
        "new_embedding_request": False,
    }
    return result, trace


def build_candidate_pool_v108(
    query: str,
    *,
    vector_index: Any,
    query_cache: Any,
    candidate_set: dict[str, Any],
    resolution_support: dict[str, Any],
    geometry_role_scheme: dict[str, Any],
    segment_query_cache: Any | None = None,
    final_candidate_cap: int = 256,
    **limits: int,
) -> dict[str, Any]:
    """Close the v0.10.7 cache trace and post-union cap integration gaps."""

    traceable_cache = (
        _TraceableSegmentQueryCache(segment_query_cache)
        if segment_query_cache is not None
        else None
    )
    pool = build_candidate_pool_v107(
        query,
        vector_index=vector_index,
        query_cache=query_cache,
        candidate_set=candidate_set,
        resolution_support=resolution_support,
        geometry_role_scheme=geometry_role_scheme,
        segment_query_cache=traceable_cache,
        **limits,
    )
    capped, cap_trace = _apply_post_union_cap(
        pool, final_candidate_cap=final_candidate_cap
    )
    capped["candidate_pool_policy_version"] = CANDIDATE_POOL_POLICY_V108
    capped["segment_aware_candidate_union"] = {
        **capped["segment_aware_candidate_union"],
        "trace_query_sha256_source": "deterministic-local-sha256-of-segment-text",
        "cache_interface_requires_query_sha256": False,
    }
    capped["post_union_cap"] = cap_trace
    capped["automatic_rule_activation"] = False
    capped["pool_sha256"] = _canonical_sha256(capped)
    return capped

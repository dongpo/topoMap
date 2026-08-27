from __future__ import annotations

import copy
import re
from typing import Any

from .entity_resolution_v10 import _canonical_sha256
from .entity_resolution_v101 import build_candidate_pool_v101
from .entity_resolution_v105 import build_candidate_pool_v105


CANDIDATE_POOL_POLICY_V107 = "0.10.7"
EXPLICIT_COUNT_PATTERN = re.compile(
    r"(?P<count>[二三四五六七八2-8])\s*(?:"
    r"(?:個|項|種)\s*(?:正式)?(?:現地對象|圖徵|節點|實體|據點|對象|服務)?"
    r"|類(?:公共服務)?(?:圖徵|節點|實體|據點|對象|服務)"
    r")"
)
CHINESE_COUNTS = {"二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8}
SEGMENT_SPLIT_PATTERN = re.compile(r"[、；;]|，?以及|，?並且|，?以及需")


class EntityResolutionV107Error(ValueError):
    """The v0.10.7 segment-aware candidate-pool contract is invalid."""


def split_coordinated_query_segments(query: str) -> list[str]:
    body = query.split("：", 1)[1] if "：" in query else query
    segments = [
        segment.strip(" ，。；;：:")
        for segment in SEGMENT_SPLIT_PATTERN.split(body)
    ]
    segments = [segment for segment in segments if len(segment) >= 3]
    merged: list[str] = []
    index = 0
    while index < len(segments):
        if len(segments[index]) <= 4 and index + 1 < len(segments):
            merged.append(f"{segments[index]}、{segments[index + 1]}")
            index += 2
            continue
        merged.append(segments[index])
        index += 1
    return merged


def explicit_requested_entity_count(query: str) -> int | None:
    matches = []
    for match in EXPLICIT_COUNT_PATTERN.finditer(query):
        raw = match.group("count")
        matches.append(CHINESE_COUNTS.get(raw, int(raw) if raw.isdigit() else 0))
    return max(matches) if matches else None


def _full_records_by_id(
    query: str,
    *,
    vector_index: Any,
    query_cache: Any,
    candidate_set: dict[str, Any],
    resolution_support: dict[str, Any],
    geometry_role_scheme: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    full = build_candidate_pool_v101(
        query,
        vector_index=vector_index,
        query_cache=query_cache,
        candidate_set=candidate_set,
        resolution_support=resolution_support,
        geometry_role_scheme=geometry_role_scheme,
        raw_top_limit=638,
        geometry_top_limit=0,
        hierarchy_seed_limit=0,
        hierarchy_family_limit=0,
        max_candidates=638,
    )
    return {record["node_id"]: record for record in full["candidate_records"]}


def _segment_vector_union(
    pool: dict[str, Any],
    *,
    segments: list[str],
    vector_index: Any,
    segment_query_cache: Any,
    full_records: dict[str, dict[str, Any]],
    segment_top_limit: int,
    segment_union_limit: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    existing = {record["node_id"] for record in pool["candidate_records"]}
    additions: dict[str, dict[str, Any]] = {}
    trace: list[dict[str, Any]] = []
    for segment_index, segment in enumerate(segments):
        embedded = segment_query_cache.embed_query(
            segment, vector_index.model, vector_index.dimensions
        )
        hits = vector_index.search(
            embedded["vector"], limit=segment_top_limit, min_similarity=-1.0
        )
        selected_for_segment = []
        for rank, hit in enumerate(hits, 1):
            node_id = hit["node_id"]
            selected_for_segment.append(node_id)
            if node_id in existing or node_id in additions:
                continue
            record = copy.deepcopy(full_records[node_id])
            record["inclusion_reasons"] = sorted(
                set(record.get("inclusion_reasons", []))
                | {f"segment-vector-top-k:{segment_index + 1}"}
            )
            record["segment_hits"] = [
                {
                    "segment_index": segment_index,
                    "segment_sha256": embedded["query_sha256"],
                    "rank": rank,
                    "similarity": hit["similarity"],
                }
            ]
            additions[node_id] = record
            if len(additions) >= segment_union_limit:
                break
        trace.append(
            {
                "segment_index": segment_index,
                "segment": segment,
                "segment_query_sha256": embedded["query_sha256"],
                "top_node_ids": selected_for_segment,
                "new_embedding_request": False,
            }
        )
        if len(additions) >= segment_union_limit:
            break
    if not additions:
        return pool, trace
    result = copy.deepcopy(pool)
    result.pop("pool_sha256", None)
    result["candidate_records"].extend(additions.values())
    return result, trace


def build_candidate_pool_v107(
    query: str,
    *,
    vector_index: Any,
    query_cache: Any,
    candidate_set: dict[str, Any],
    resolution_support: dict[str, Any],
    geometry_role_scheme: dict[str, Any],
    segment_query_cache: Any | None = None,
    segment_top_limit: int = 12,
    segment_union_limit: int = 96,
    adaptive_raw_per_entity: int = 28,
    adaptive_raw_cap: int = 224,
    adaptive_max_candidates_cap: int = 256,
    **limits: int,
) -> dict[str, Any]:
    """Build a bounded pool for explicit coordinated queries without answer keys.

    When reviewed segment vectors are available, their top candidates are unioned.
    Otherwise the already-paid whole-query vector receives a bounded depth increase
    based only on the explicit requested entity count and deterministic segmentation.
    """

    segments = split_coordinated_query_segments(query)
    explicit_count = explicit_requested_entity_count(query)
    effective_count = max(len(segments), explicit_count or 0)
    base_limits = dict(limits)
    base_raw = int(base_limits.get("raw_top_limit", 80))
    base_max = int(base_limits.get("max_candidates", 128))
    adaptive = effective_count >= 4
    if adaptive:
        base_limits["raw_top_limit"] = min(
            adaptive_raw_cap,
            max(base_raw, effective_count * adaptive_raw_per_entity),
        )
        base_limits["max_candidates"] = min(
            adaptive_max_candidates_cap,
            max(base_max, base_limits["raw_top_limit"] + 32),
        )
    pool = build_candidate_pool_v105(
        query,
        vector_index=vector_index,
        query_cache=query_cache,
        candidate_set=candidate_set,
        resolution_support=resolution_support,
        geometry_role_scheme=geometry_role_scheme,
        **base_limits,
    )
    segment_trace: list[dict[str, Any]] = []
    segment_union_used = False
    if segment_query_cache is not None and len(segments) >= 2:
        full_records = _full_records_by_id(
            query,
            vector_index=vector_index,
            query_cache=query_cache,
            candidate_set=candidate_set,
            resolution_support=resolution_support,
            geometry_role_scheme=geometry_role_scheme,
        )
        before = len(pool["candidate_records"])
        pool, segment_trace = _segment_vector_union(
            pool,
            segments=segments,
            vector_index=vector_index,
            segment_query_cache=segment_query_cache,
            full_records=full_records,
            segment_top_limit=segment_top_limit,
            segment_union_limit=segment_union_limit,
        )
        segment_union_used = len(pool["candidate_records"]) > before
    result = copy.deepcopy(pool)
    result.pop("pool_sha256", None)
    result["candidate_pool_policy_version"] = CANDIDATE_POOL_POLICY_V107
    result["segment_aware_candidate_union"] = {
        "segments": segments,
        "segment_count": len(segments),
        "explicit_requested_entity_count": explicit_count,
        "effective_entity_count": effective_count,
        "adaptive_whole_query_depth_used": adaptive,
        "base_raw_top_limit": base_raw,
        "effective_raw_top_limit": base_limits.get("raw_top_limit", base_raw),
        "base_max_candidates": base_max,
        "effective_max_candidates": base_limits.get("max_candidates", base_max),
        "segment_vector_union_used": segment_union_used,
        "segment_vector_trace": segment_trace,
        "segment_top_limit": segment_top_limit,
        "segment_union_limit": segment_union_limit,
        "answer_keys_used": False,
        "new_embedding_request": False,
        "automatic_rule_activation": False,
    }
    result["automatic_rule_activation"] = False
    result["pool_sha256"] = _canonical_sha256(result)
    return result

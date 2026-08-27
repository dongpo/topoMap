from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .entity_resolution_v10 import _canonical_sha256
from .entity_resolution_v101 import build_candidate_pool_v101
from .entity_resolution_v104 import (
    is_explicit_coordinated_multi_entity_query,
    normalize_hierarchy_clarification_v104,
)


ENTITY_RESOLUTION_SCHEMA_V105 = "nma.entity-resolution/0.10.5"
CACHE_SCHEMA_V105 = "nma.entity-resolution-cache/0.10.5"
MATERIAL_PATTERN = re.compile(r"含(.+?)等建材")
MATERIAL_SPLIT_PATTERN = re.compile(r"[、,，或及]")
CODE_PATTERN_TEMPLATE = r"(?<![0-9A-Za-z]){}(?![0-9A-Za-z])"


class EntityResolutionV105Error(ValueError):
    """The v0.10.5 bounded post-v0.12 policy contract is invalid."""


def _material_terms(instruction: str) -> list[str]:
    match = MATERIAL_PATTERN.search(instruction)
    if not match:
        return []
    return [
        term.strip()
        for term in MATERIAL_SPLIT_PATTERN.split(match.group(1))
        if term.strip()
    ]


def _positive_and_negative_text(query: str) -> tuple[str, str]:
    for marker in ("但不是", "但非"):
        if marker not in query:
            continue
        positive, remainder = query.split(marker, 1)
        negative = re.split(r"[；;。]", remainder, maxsplit=1)[0]
        return positive, negative
    return query, ""


def _source_discriminator_matches(
    query: str, candidate_set: dict[str, Any]
) -> list[dict[str, Any]]:
    positive, negative = _positive_and_negative_text(query)
    matches = []
    for candidate in candidate_set.get("candidates", []):
        if candidate.get("official_status") != "portrayal":
            continue
        terms = _material_terms(str(candidate.get("instruction", "")))
        if len(terms) < 2:
            continue
        positive_terms = [term for term in terms if term in positive]
        negative_terms = [term for term in terms if term in negative]
        if len(positive_terms) >= 2 and not negative_terms:
            matches.append(
                {
                    "node_id": candidate["target_node_id"],
                    "positive_terms": positive_terms,
                    "negative_terms": negative_terms,
                    "source_instruction": candidate["instruction"],
                }
            )
    return matches


def build_candidate_pool_v105(
    query: str,
    *,
    vector_index: Any,
    query_cache: Any,
    candidate_set: dict[str, Any],
    resolution_support: dict[str, Any],
    geometry_role_scheme: dict[str, Any],
    **limits: int,
) -> dict[str, Any]:
    """Rescue one uniquely source-discriminated candidate without answer keys.

    All queries without a unique literal source-instruction match remain byte-for-byte
    compatible with v0.10.1. A saturated pool may expand by exactly one record so an
    already selected candidate from another coordinated segment is never evicted.
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
    matches = _source_discriminator_matches(query, candidate_set)
    if len(matches) != 1:
        return base
    rescue = matches[0]
    if any(
        record["node_id"] == rescue["node_id"]
        for record in base["candidate_records"]
    ):
        return base

    expanded_limits = dict(limits)
    expanded_limits.update(
        {
            "raw_top_limit": 638,
            "geometry_top_limit": 0,
            "hierarchy_seed_limit": 0,
            "hierarchy_family_limit": 0,
            "max_candidates": 638,
        }
    )
    full = build_candidate_pool_v101(
        query,
        vector_index=vector_index,
        query_cache=query_cache,
        candidate_set=candidate_set,
        resolution_support=resolution_support,
        geometry_role_scheme=geometry_role_scheme,
        **expanded_limits,
    )
    rescued_record = next(
        copy.deepcopy(record)
        for record in full["candidate_records"]
        if record["node_id"] == rescue["node_id"]
    )
    rescued_record["inclusion_reasons"] = sorted(
        set(rescued_record.get("inclusion_reasons", []))
        | {"unique-positive-source-instruction-discriminator-rescue"}
    )
    records = copy.deepcopy(base["candidate_records"])
    max_candidates = int(limits.get("max_candidates", 128))
    support_count = sum(bool(record.get("cross_document_support")) for record in records)
    records.insert(support_count, rescued_record)

    result = copy.deepcopy(base)
    result.pop("pool_sha256", None)
    result.update(
        {
            "candidate_records": records,
            "candidate_pool_policy_version": "0.10.5",
            "limits": {
                **base["limits"],
                "max_candidates": max_candidates + 1,
            },
            "source_discriminator_rescue": {
                "strategy": "unique-positive-literal-source-instruction-match-with-negative-scope-exclusion",
                "rescued": [rescue],
                "base_max_candidates": max_candidates,
                "effective_max_candidates": max_candidates + 1,
                "bounded_expansion_records": 1,
                "answer_keys_used": False,
                "new_embedding_request": False,
                "automatic_rule_activation": False,
            },
        }
    )
    result["pool_sha256"] = _canonical_sha256(result)
    return result


def _is_code_ancestor(parent: str, child: str) -> bool:
    prefix = parent.rstrip("0")
    return len(prefix) >= 2 and parent != child and child.startswith(prefix)


def _add_common_hierarchy_parent(
    normalized: dict[str, Any],
    *,
    raw: dict[str, Any],
    candidate_pool: dict[str, Any],
    repairs: list[dict[str, Any]],
) -> None:
    if raw.get("status") != "needs-clarification" or normalized.get(
        "selected_node_ids"
    ):
        return
    model_text = "\n".join(
        [
            str(raw.get("clarification_question", "")),
            str(raw.get("decision_summary", "")),
        ]
    )
    hierarchies = [
        record
        for record in candidate_pool.get("candidate_records", [])
        if record.get("official_status") == "classification-hierarchy"
    ]
    exact_children = [
        record
        for record in hierarchies
        if record.get("canonical_name")
        and str(record["canonical_name"]) in model_text
    ]
    child_codes = {str(record["feature_code"]) for record in exact_children}
    if len(child_codes) < 2:
        return
    common = [
        record
        for record in hierarchies
        if all(
            _is_code_ancestor(str(record["feature_code"]), child_code)
            for child_code in child_codes
        )
    ]
    if not common:
        return
    deepest = max(len(str(record["feature_code"]).rstrip("0")) for record in common)
    deepest_records = [
        record
        for record in common
        if len(str(record["feature_code"]).rstrip("0")) == deepest
    ]
    unique_ids = {record["node_id"] for record in deepest_records}
    if len(unique_ids) != 1:
        return
    selected = deepest_records[0]
    normalized["resolved_entities"] = [
        {
            "query_segment": selected["canonical_name"],
            "selected_node_id": selected["node_id"],
            "confidence": "high",
            "evidence_basis": ["official-name", "hierarchy-context"],
        }
    ]
    normalized["selected_node_ids"] = [selected["node_id"]]
    repairs.append(
        {
            "type": "unique-deepest-common-hierarchy-parent-added",
            "selected_node_id": selected["node_id"],
            "exact_child_node_ids": sorted(
                {record["node_id"] for record in exact_children}
            ),
        }
    )


def _complete_explicit_model_references(
    normalized: dict[str, Any],
    *,
    raw: dict[str, Any],
    candidate_pool: dict[str, Any],
    repairs: list[dict[str, Any]],
) -> None:
    if raw.get("status") != "resolved" or not is_explicit_coordinated_multi_entity_query(
        candidate_pool["query"]
    ):
        return
    model_text = "\n".join(
        [
            str(raw.get("clarification_question", "")),
            str(raw.get("decision_summary", "")),
        ]
    )
    selected_ids = list(normalized.get("selected_node_ids", []))
    additions = []
    for record in candidate_pool.get("candidate_records", []):
        node_id = record["node_id"]
        if node_id in selected_ids:
            continue
        name = str(record.get("canonical_name", ""))
        code = str(record.get("feature_code", ""))
        if not name or name not in model_text:
            continue
        if not re.search(CODE_PATTERN_TEMPLATE.format(re.escape(code)), model_text):
            continue
        additions.append(record)
    for record in additions:
        normalized.setdefault("resolved_entities", []).append(
            {
                "query_segment": record["canonical_name"],
                "selected_node_id": record["node_id"],
                "confidence": "high",
                "evidence_basis": ["official-name", "source-instruction"],
            }
        )
        selected_ids.append(record["node_id"])
    if additions:
        normalized["selected_node_ids"] = selected_ids
        repairs.append(
            {
                "type": "explicit-official-name-and-code-model-reference-completed",
                "selected_node_ids": [record["node_id"] for record in additions],
                "structured_output_entity_limit_observed": 3,
            }
        )


def _apply_source_discriminator_rescue(
    normalized: dict[str, Any],
    *,
    candidate_pool: dict[str, Any],
    repairs: list[dict[str, Any]],
) -> None:
    rescue_meta = candidate_pool.get("source_discriminator_rescue", {})
    rescued = rescue_meta.get("rescued", [])
    if normalized.get("status") != "resolved" or len(rescued) != 1:
        return
    rescue = rescued[0]
    rescue_id = rescue["node_id"]
    records_by_id = {
        record["node_id"]: record
        for record in candidate_pool.get("candidate_records", [])
    }
    selected_ids = list(normalized.get("selected_node_ids", []))
    if rescue_id in selected_ids:
        return
    rescue_record = records_by_id[rescue_id]
    rescue_family = str(rescue_record["feature_code"])[:3]
    positive_terms = set(rescue["positive_terms"])
    removed = []
    retained = []
    for node_id in selected_ids:
        record = records_by_id.get(node_id)
        if not record or str(record.get("feature_code", ""))[:3] != rescue_family:
            retained.append(node_id)
            continue
        instruction_terms = set(_material_terms(str(record.get("instruction", ""))))
        if len(instruction_terms & positive_terms) < 2:
            removed.append(node_id)
        else:
            retained.append(node_id)
    retained.append(rescue_id)
    normalized["selected_node_ids"] = retained
    normalized["resolved_entities"] = [
        entity
        for entity in normalized.get("resolved_entities", [])
        if entity.get("selected_node_id") not in set(removed)
    ]
    normalized["resolved_entities"].append(
        {
            "query_segment": rescue_record["canonical_name"],
            "selected_node_id": rescue_id,
            "confidence": "high",
            "evidence_basis": ["source-instruction", "geometry-role"],
        }
    )
    repairs.append(
        {
            "type": "unique-positive-source-discriminator-selection-repaired",
            "selected_node_id": rescue_id,
            "removed_lower-evidence-same-family-node_ids": removed,
            "positive_source_terms": sorted(positive_terms),
        }
    )


def normalize_entity_resolution_v105(
    resolution: dict[str, Any], *, candidate_pool: dict[str, Any]
) -> dict[str, Any]:
    normalized = normalize_hierarchy_clarification_v104(
        resolution, candidate_pool=candidate_pool
    )
    repairs: list[dict[str, Any]] = []
    _add_common_hierarchy_parent(
        normalized,
        raw=resolution,
        candidate_pool=candidate_pool,
        repairs=repairs,
    )
    _complete_explicit_model_references(
        normalized,
        raw=resolution,
        candidate_pool=candidate_pool,
        repairs=repairs,
    )
    _apply_source_discriminator_rescue(
        normalized,
        candidate_pool=candidate_pool,
        repairs=repairs,
    )
    normalized["schema"] = ENTITY_RESOLUTION_SCHEMA_V105
    normalized["policy_validation"]["policy_v105"] = (
        "unique-common-hierarchy-parent; explicit-name-plus-code-completion; "
        "unique-positive-source-discriminator-rescue"
    )
    normalized["policy_validation"]["v105_repairs"] = repairs
    normalized["policy_validation"]["v105_repair_count"] = len(repairs)
    normalized["policy_validation"]["new_openai_request"] = False
    normalized["policy_validation"]["automatic_rule_activation"] = False
    return normalized


class PolicyValidatedEntityResolverV105:
    def __init__(self, resolver: Any):
        if not callable(getattr(resolver, "resolve", None)):
            raise EntityResolutionV105Error("The wrapped entity resolver is not callable.")
        self.resolver = resolver
        self.model = getattr(resolver, "model", None)
        if hasattr(resolver, "query_cache"):
            self.query_cache = resolver.query_cache

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        raw = self.resolver.resolve(candidate_pool)
        normalized = normalize_entity_resolution_v105(
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


class EntityResolutionCacheV105:
    def __init__(self, payload: dict[str, Any]):
        if payload.get("schema") != CACHE_SCHEMA_V105:
            raise EntityResolutionV105Error("Unsupported v0.10.5 cache schema.")
        self.payload = payload
        self.by_query_sha = {
            record["query_sha256"]: record for record in payload.get("records", [])
        }
        if len(self.by_query_sha) != len(payload.get("records", [])):
            raise EntityResolutionV105Error("Cache contains duplicate query hashes.")

    @classmethod
    def load(cls, path: str | Path) -> "EntityResolutionCacheV105":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def resolve(self, candidate_pool: dict[str, Any]) -> dict[str, Any]:
        query_sha = hashlib.sha256(candidate_pool["query"].encode("utf-8")).hexdigest()
        record = self.by_query_sha.get(query_sha)
        if not record:
            raise EntityResolutionV105Error("Cache has no matching query.")
        if record["candidate_pool_sha256"] != candidate_pool["pool_sha256"]:
            raise EntityResolutionV105Error("Cache candidate pool differs.")
        resolution = record["resolution"]
        if resolution.get("schema") != ENTITY_RESOLUTION_SCHEMA_V105:
            raise EntityResolutionV105Error("Cached resolution schema is invalid.")
        allowed = {item["node_id"] for item in candidate_pool["candidate_records"]}
        if not set(resolution.get("selected_node_ids", [])).issubset(allowed):
            raise EntityResolutionV105Error(
                "Cached resolution selected a node outside the pool."
            )
        return resolution

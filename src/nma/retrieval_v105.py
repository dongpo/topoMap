from __future__ import annotations

from typing import Any

from .entity_resolution_v105 import (
    ENTITY_RESOLUTION_SCHEMA_V105,
    build_candidate_pool_v105,
)
from .entity_resolution_v104 import is_explicit_coordinated_multi_entity_query
from .retrieval_v101 import ReviewedSupportGraphRetrieverV101, RetrievalV101Error


class RetrievalV105Error(RetrievalV101Error):
    """The v0.10.5 bounded post-v0.12 runtime policy is invalid."""


class ValidatedPolicyGraphRetrieverV105(ReviewedSupportGraphRetrieverV101):
    def __init__(
        self, *args: Any, candidate_query_cache: Any | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.candidate_query_cache = candidate_query_cache

    def evidence_package(
        self,
        query: str,
        *,
        seed_limit: int = 6,
        vector_limit: int = 24,
        max_depth: int = 2,
        max_nodes: int = 60,
    ) -> dict[str, Any]:
        multi_entity = is_explicit_coordinated_multi_entity_query(query)
        exact_seeds, explicit_codes = self._exact_code_seeds(query)
        quality_seed, _ = self._quality_qualifier_seed(query)
        semantic_seeds, _ = self._semantic_link_seeds(query)
        if not multi_entity and (
            exact_seeds or quality_seed or semantic_seeds or explicit_codes
        ):
            package = super().evidence_package(
                query,
                seed_limit=seed_limit,
                vector_limit=vector_limit,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
            package["retrieval_trace"].update(
                {
                    "retrieval_policy_version": "0.10.5",
                    "v105_explicit_multi_entity_query": False,
                    "v105_deterministic_bypass": True,
                }
            )
            return package

        query_cache = self.candidate_query_cache or self._query_cache_adapter()
        candidate_pool = build_candidate_pool_v105(
            query,
            vector_index=self.vector_index,
            query_cache=query_cache,
            candidate_set=self.candidate_set,
            resolution_support=self.resolution_support,
            geometry_role_scheme=self.geometry_role_scheme,
            **self.candidate_pool_limits,
        )
        resolution = self.entity_resolver.resolve(candidate_pool)
        if resolution.get("schema") != ENTITY_RESOLUTION_SCHEMA_V105:
            raise RetrievalV105Error("v0.10.5 requires a policy-validated resolution.")
        selected = resolution["selected_node_ids"]
        baseline = self.graph_retriever.evidence_package(
            query, seed_limit=seed_limit, max_depth=max_depth, max_nodes=max_nodes
        )
        ranked_trace = [
            {
                "id": item["node_id"],
                "type": self.graph_retriever.nodes[item["node_id"]]["type"],
                "score": item["vector_similarity"],
                "matched_terms": [],
                "match_mode": "v105-source-bounded-candidate-pool",
                "vector_rank": item["vector_rank"],
                "vector_similarity": item["vector_similarity"],
                "inclusion_reasons": item["inclusion_reasons"],
                "has_cross_document_support": bool(item.get("cross_document_support")),
            }
            for item in candidate_pool["candidate_records"]
        ]
        baseline["retrieval_trace"]["ranked_candidates"] = ranked_trace
        if selected:
            package = self._repackage(
                query,
                baseline,
                selected,
                policy="v105-source-bounded-policy-entity-resolution",
                seed_limit=seed_limit,
                max_depth=max_depth,
                max_nodes=max_nodes,
                explicit_codes=[],
                quality_qualifier=None,
                semantic_link_id=None,
            )
        else:
            package = self.graph_retriever.package_from_seed_ids(
                query,
                [],
                ranked_trace=ranked_trace,
                retrieval_mode="v105-source-bounded-policy-resolution-plus-typed-graph",
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
        if resolution["status"] == "needs-clarification":
            package["status"] = "needs-clarification"
            package["clarification"] = {
                "required": True,
                "reason": resolution["clarification_question"],
                "hierarchy_node_ids": selected,
            }
        elif resolution["status"] == "abstained-no-match":
            package["status"] = "abstained-no-match"
        package["retrieval_mode"] = (
            "v105-bounded-resolution-plus-source-discriminator-plus-policy-validation-plus-typed-graph"
        )
        package["retrieval_trace"].update(
            {
                "retrieval_policy_version": "0.10.5",
                "v105_explicit_multi_entity_query": multi_entity,
                "v105_deterministic_bypass": False,
                "v105_candidate_pool_sha256": candidate_pool["pool_sha256"],
                "v105_candidate_pool_records": len(candidate_pool["candidate_records"]),
                "v105_source_discriminator_rescue": candidate_pool.get(
                    "source_discriminator_rescue"
                ),
                "v105_resolution_status": resolution["status"],
                "v105_llm_entity_resolution_used": True,
                "v105_resolution_response_id": resolution.get("response_id"),
                "v105_resolution_model": resolution.get("response_model"),
                "v105_resolution_usage": resolution.get("usage", {}),
                "v105_query_embedding_usage": candidate_pool.get(
                    "query_embedding_usage", {}
                ),
                "v105_policy_validation": resolution.get("policy_validation", {}),
                "v105_raw_resolution_snapshot": resolution.get(
                    "raw_resolution_snapshot", {}
                ),
                "v105_policy_normalized_selected_node_ids": selected,
                "v105_new_openai_request_for_validation": False,
                "v105_hidden_chain_of_thought_exposed": False,
            }
        )
        package["automatic_rule_activation"] = False
        return package

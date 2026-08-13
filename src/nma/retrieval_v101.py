from __future__ import annotations

from typing import Any

from .entity_resolution_v101 import build_candidate_pool_v101
from .retrieval_v09 import SourceGroundedGraphRetrieverV09


class RetrievalV101Error(ValueError):
    """The reviewed-support v0.10.1 retrieval contract is invalid."""


class ReviewedSupportGraphRetrieverV101(SourceGroundedGraphRetrieverV09):
    """Resolve source candidates with reviewed cross-document support."""

    def __init__(
        self,
        *args: Any,
        candidate_set: dict[str, Any],
        entity_resolver: Any,
        resolution_support: dict[str, Any],
        geometry_role_scheme: dict[str, Any],
        candidate_pool_limits: dict[str, int] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        if candidate_set.get("schema") != "nma.semantic-candidate-set/0.8":
            raise RetrievalV101Error("Unsupported v0.10.1 candidate corpus.")
        if len(candidate_set.get("candidates", [])) != 638:
            raise RetrievalV101Error("v0.10.1 requires all 638 source candidates.")
        if not callable(getattr(entity_resolver, "resolve", None)):
            raise RetrievalV101Error("v0.10.1 entity resolver is not callable.")
        self.candidate_set = candidate_set
        self.entity_resolver = entity_resolver
        self.resolution_support = resolution_support
        self.geometry_role_scheme = geometry_role_scheme
        self.candidate_pool_limits = candidate_pool_limits or {}

    def _annotate_bypass(
        self, package: dict[str, Any], *, policy: str
    ) -> dict[str, Any]:
        package["retrieval_trace"].update(
            {
                "retrieval_policy_version": "0.10.1",
                "v101_entity_resolution_policy": policy,
                "v101_llm_entity_resolution_used": False,
            }
        )
        package["automatic_rule_activation"] = False
        return package

    def evidence_package(
        self,
        query: str,
        *,
        seed_limit: int = 6,
        vector_limit: int = 24,
        max_depth: int = 2,
        max_nodes: int = 60,
    ) -> dict[str, Any]:
        exact_seeds, explicit_codes = self._exact_code_seeds(query)
        quality_seed, _ = self._quality_qualifier_seed(query)
        semantic_seeds, _ = self._semantic_link_seeds(query)
        if exact_seeds or quality_seed or semantic_seeds or explicit_codes:
            package = super().evidence_package(
                query,
                seed_limit=seed_limit,
                vector_limit=vector_limit,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
            return self._annotate_bypass(
                package, policy="deterministic-v0.8-v0.9-precedence"
            )

        candidate_pool = build_candidate_pool_v101(
            query,
            vector_index=self.vector_index,
            query_cache=self.entity_resolver.query_cache
            if hasattr(self.entity_resolver, "query_cache")
            else self._query_cache_adapter(),
            candidate_set=self.candidate_set,
            resolution_support=self.resolution_support,
            geometry_role_scheme=self.geometry_role_scheme,
            **self.candidate_pool_limits,
        )
        resolution = self.entity_resolver.resolve(candidate_pool)
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
                "match_mode": "v101-reviewed-support-candidate-pool",
                "vector_rank": item["vector_rank"],
                "vector_similarity": item["vector_similarity"],
                "inclusion_reasons": item["inclusion_reasons"],
                "has_cross_document_support": bool(
                    item.get("cross_document_support")
                ),
            }
            for item in candidate_pool["candidate_records"]
        ]
        baseline["retrieval_trace"]["ranked_candidates"] = ranked_trace
        if selected:
            package = self._repackage(
                query,
                baseline,
                selected,
                policy="v101-reviewed-support-llm-entity-resolution",
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
                retrieval_mode=(
                    "v101-reviewed-support-entity-resolution-plus-typed-graph"
                ),
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
        policy_validated = resolution.get("schema") == "nma.entity-resolution/0.10.2"
        package["retrieval_mode"] = (
            "v102-bounded-openai-entity-resolution-plus-policy-validation-plus-reviewed-cross-document-support-plus-typed-graph"
            if policy_validated
            else "v101-bounded-openai-entity-resolution-plus-reviewed-cross-document-support-plus-typed-graph"
        )
        package["retrieval_trace"].update(
            {
                "retrieval_policy_version": "0.10.2" if policy_validated else "0.10.1",
                "v101_entity_resolution_policy": (
                    "strict-candidate-whitelist-with-reviewed-support"
                ),
                "v101_llm_entity_resolution_used": True,
                "v101_candidate_pool_sha256": candidate_pool["pool_sha256"],
                "v101_candidate_pool_records": len(
                    candidate_pool["candidate_records"]
                ),
                "v101_reviewed_support_sha256": candidate_pool[
                    "reviewed_support_sha256"
                ],
                "v101_resolution_status": resolution["status"],
                "v101_resolution_response_id": resolution.get("response_id"),
                "v101_resolution_model": resolution.get("response_model"),
                "v101_resolution_usage": resolution.get("usage", {}),
                "v101_query_embedding_usage": candidate_pool.get(
                    "query_embedding_usage", {}
                ),
                "v101_decision_summary": resolution["decision_summary"],
                "v101_multi_entity_segments": [
                    item["query_segment"]
                    for item in resolution["resolved_entities"]
                ],
                "v101_hidden_chain_of_thought_exposed": False,
            }
        )
        if policy_validated:
            package["retrieval_trace"].update(
                {
                    "v102_runtime_policy_validation": resolution.get(
                        "policy_validation", {}
                    ),
                    "v102_raw_resolution_snapshot": resolution.get(
                        "raw_resolution_snapshot", {}
                    ),
                    "v102_policy_normalized_selected_node_ids": selected,
                    "v102_new_openai_request_for_validation": False,
                    "v102_hidden_chain_of_thought_exposed": False,
                }
            )
        package["automatic_rule_activation"] = False
        return package

    def _query_cache_adapter(self) -> Any:
        class Adapter:
            def __init__(self, embed_query: Any):
                self.embed_query = embed_query

        return Adapter(self.embed_query)

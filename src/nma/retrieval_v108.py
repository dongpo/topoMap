from __future__ import annotations

from typing import Any

from .entity_resolution_v104 import is_explicit_coordinated_multi_entity_query
from .entity_resolution_v106 import ENTITY_RESOLUTION_SCHEMA_V106
from .entity_resolution_v108 import build_candidate_pool_v108
from .retrieval_v101 import ReviewedSupportGraphRetrieverV101, RetrievalV101Error


class RetrievalV108Error(RetrievalV101Error):
    """The v0.10.8 candidate-pool retrieval spine is invalid."""


class SegmentAwareGraphRetrieverV108(ReviewedSupportGraphRetrieverV101):
    """Run retrieval over the exact v0.10.8 pool consumed by the resolver.

    This class intentionally does not inherit the v0.10.5/v0.10.6 retrieval
    implementations because those implementations rebuild a v0.10.5 pool.
    """

    def __init__(
        self,
        *args: Any,
        candidate_query_cache: Any | None = None,
        segment_query_cache: Any | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.candidate_query_cache = candidate_query_cache
        self.segment_query_cache = segment_query_cache

    def _reviewed_support_citations(
        self, selected_node_ids: list[str]
    ) -> list[dict[str, Any]]:
        selected = set(selected_node_ids)
        source = self.resolution_support["source_document"]
        citations: list[dict[str, Any]] = []
        evidence_records: list[tuple[str, str, dict[str, Any]]] = []
        for row in self.resolution_support["reviewed_classification_rows"]:
            if row["supports_node_id"] in selected:
                evidence_records.append(
                    (row["supports_node_id"], "classification-row", row["evidence"])
                )
        for definition in self.resolution_support["reviewed_definitions"]:
            if definition["supports_node_id"] in selected:
                evidence_records.append(
                    (definition["supports_node_id"], "definition", definition["evidence"])
                )
        for node_id, evidence_type, evidence in evidence_records:
            page = evidence["pdf_page"]
            citations.append(
                {
                    "citation_id": (
                        f"citation:reviewed-support:{node_id}:{evidence_type}:p{page}"
                    ),
                    "section_id": None,
                    "document_id": f"document:{source['document_id']}",
                    "filename": source["filename"],
                    "revision": source.get("revision"),
                    "source_sha256": source["sha256"],
                    "page": page,
                    "printed_page": evidence.get("printed_page"),
                    "record_id": node_id,
                    "review_status": evidence["review_status"],
                    "source_text": None,
                    "citation_integrity": "verified-reviewed-cross-document-support",
                    "document_candidates": [f"document:{source['document_id']}"],
                    "metadata_provenance": "nma-entity-resolution-support-v0.10.1",
                    "supports_node_id": node_id,
                    "evidence_type": evidence_type,
                }
            )
        return citations

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
                    "retrieval_policy_version": "0.10.8",
                    "v108_explicit_multi_entity_query": False,
                    "v108_deterministic_bypass": True,
                    "v108_candidate_pool_rebuilt": False,
                }
            )
            package["automatic_rule_activation"] = False
            return package

        query_cache = self.candidate_query_cache or self._query_cache_adapter()
        segment_cache = self.segment_query_cache if multi_entity else None
        if multi_entity and segment_cache is None:
            raise RetrievalV108Error(
                "v0.10.8 multi-entity retrieval requires a segment query cache."
            )
        candidate_pool = build_candidate_pool_v108(
            query,
            vector_index=self.vector_index,
            query_cache=query_cache,
            segment_query_cache=segment_cache,
            candidate_set=self.candidate_set,
            resolution_support=self.resolution_support,
            geometry_role_scheme=self.geometry_role_scheme,
            **self.candidate_pool_limits,
        )
        resolution = self.entity_resolver.resolve(candidate_pool)
        if resolution.get("schema") != ENTITY_RESOLUTION_SCHEMA_V106:
            raise RetrievalV108Error(
                "v0.10.8 retrieval requires a validated v0.10.6 resolution."
            )
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
                "match_mode": "v108-source-bounded-segment-aware-candidate-pool",
                "vector_rank": item["vector_rank"],
                "vector_similarity": item["vector_similarity"],
                "inclusion_reasons": item["inclusion_reasons"],
                "has_cross_document_support": bool(
                    item.get("cross_document_support")
                ),
                "segment_hits": item.get("segment_hits", []),
            }
            for item in candidate_pool["candidate_records"]
        ]
        baseline["retrieval_trace"]["ranked_candidates"] = ranked_trace
        if selected:
            package = self._repackage(
                query,
                baseline,
                selected,
                policy="v108-segment-aware-source-bounded-entity-resolution",
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
                    "v108-segment-aware-source-bounded-resolution-plus-typed-graph"
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

        support_citations = self._reviewed_support_citations(selected)
        citation_ids = {
            citation["citation_id"] for citation in package.get("citations", [])
        }
        package["citations"] = list(package.get("citations", [])) + [
            citation
            for citation in support_citations
            if citation["citation_id"] not in citation_ids
        ]

        union_trace = candidate_pool["segment_aware_candidate_union"]
        cap_trace = candidate_pool["post_union_cap"]
        package["retrieval_mode"] = (
            "v108-segment-aware-bounded-resolution-plus-policy-validation-plus-typed-graph"
        )
        package["retrieval_trace"].update(
            {
                "retrieval_policy_version": "0.10.8",
                "v108_explicit_multi_entity_query": multi_entity,
                "v108_deterministic_bypass": False,
                "v108_candidate_pool_policy_version": candidate_pool[
                    "candidate_pool_policy_version"
                ],
                "v108_candidate_pool_sha256": candidate_pool["pool_sha256"],
                "v108_candidate_pool_records": len(
                    candidate_pool["candidate_records"]
                ),
                "v108_candidate_pool_rebuilt": True,
                "v108_segment_query_cache_used": segment_cache is not None,
                "v108_segment_vector_union_used": union_trace[
                    "segment_vector_union_used"
                ],
                "v108_segment_vector_trace": union_trace[
                    "segment_vector_trace"
                ],
                "v108_post_union_cap": cap_trace,
                "v108_resolution_status": resolution["status"],
                "v108_llm_entity_resolution_used": True,
                "v108_resolution_response_id": resolution.get("response_id"),
                "v108_resolution_model": resolution.get("response_model"),
                "v108_resolution_usage": resolution.get("usage", {}),
                "v108_query_embedding_usage": candidate_pool.get(
                    "query_embedding_usage", {}
                ),
                "v108_policy_validation": resolution.get(
                    "policy_validation", {}
                ),
                "v108_raw_resolution_snapshot": resolution.get(
                    "raw_resolution_snapshot", {}
                ),
                "v108_policy_normalized_selected_node_ids": selected,
                "v108_reviewed_support_citations": [
                    citation["citation_id"] for citation in support_citations
                ],
                "v108_new_openai_request_for_validation": False,
                "v108_hidden_chain_of_thought_exposed": False,
            }
        )
        package["automatic_rule_activation"] = False
        return package

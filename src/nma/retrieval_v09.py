from __future__ import annotations

from typing import Any

from .retrieval_v08 import HybridGraphRetrieverV08, RetrievalV08Error


MULTI_ENTITY_TERMS = ("比較", "以及", "與", "和", "分別", "各自", "兩者")


class RetrievalV09Error(ValueError):
    """The v0.9 source-grounded candidate retrieval contract is invalid."""


class SourceGroundedGraphRetrieverV09(HybridGraphRetrieverV08):
    """Retrieve over all 638 source-grounded feature candidates before graph expansion."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        source = self.vector_index.payload.get("source_corpus", {})
        if (
            source.get("schema") != "nma.semantic-candidate-set/0.8"
            or source.get("records") != 638
            or source.get("interpreted_terms_embedded") is not False
        ):
            raise RetrievalV09Error(
                "v0.9 requires the complete source-grounded 638-candidate index."
            )
        missing = sorted(set(self.vector_index.vectors) - set(self.graph_retriever.nodes))
        if missing:
            raise RetrievalV09Error(
                f"Candidate index targets missing canonical nodes: {missing[:3]}"
            )

    def _hierarchy_requires_clarification(self, node_id: str) -> bool:
        node = self.graph_retriever.nodes.get(node_id, {})
        return node.get("type") == "ClassificationHierarchy"

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
        if exact_seeds or quality_seed or semantic_seeds:
            package = super().evidence_package(
                query,
                seed_limit=seed_limit,
                vector_limit=vector_limit,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
            trace = package["retrieval_trace"]
            trace["retrieval_policy_version"] = "0.9"
            trace["v09_candidate_vector_policy"] = "deterministic-v0.8-policy-precedence"
            trace["v09_candidate_corpus_records"] = 638
            return package

        lexical = self.graph_retriever.evidence_package(
            query, seed_limit=seed_limit, max_depth=max_depth, max_nodes=max_nodes
        )
        if explicit_codes:
            lexical["retrieval_trace"].update(
                {
                    "retrieval_policy_version": "0.9",
                    "v09_candidate_vector_policy": "abstained-unknown-explicit-code",
                    "v09_candidate_corpus_records": 638,
                    "v09_unknown_explicit_codes": explicit_codes,
                    "v09_multi_entity_query": False,
                }
            )
            lexical["automatic_rule_activation"] = False
            return lexical
        embedded = self.embed_query(
            query, self.vector_index.model, self.vector_index.dimensions
        )
        vector = embedded.get("vector")
        if not isinstance(vector, list):
            raise RetrievalV08Error("Query embedding provider returned no vector.")
        hits = self.vector_index.search(
            vector,
            limit=max(vector_limit, seed_limit),
            min_similarity=self.min_vector_similarity,
        )
        lexical_ids = lexical["retrieval_trace"]["selected_seed_ids"]
        lexical_ranks = {node_id: rank for rank, node_id in enumerate(lexical_ids, 1)}
        ranked = []
        for rank, hit in enumerate(hits, 1):
            lexical_rank = lexical_ranks.get(hit["node_id"])
            score = float(hit["similarity"]) + (0.12 if lexical_rank else 0.0)
            ranked.append(
                {
                    "id": hit["node_id"],
                    "type": hit["node_type"],
                    "score": score,
                    "matched_terms": [],
                    "match_mode": "v09-source-grounded-vector",
                    "vector_rank": rank,
                    "vector_similarity": hit["similarity"],
                    "lexical_rank": lexical_rank,
                }
            )
        ranked.sort(key=lambda item: (-item["score"], item["id"]))
        multi_entity = any(term in query for term in MULTI_ENTITY_TERMS)
        selection_limit = min(seed_limit, 3 if multi_entity else 1)
        selected = [item["id"] for item in ranked[:selection_limit]]
        baseline = lexical
        baseline["retrieval_trace"]["ranked_candidates"] = ranked
        if not selected:
            baseline["retrieval_trace"].update(
                {
                    "retrieval_policy_version": "0.9",
                    "v09_candidate_vector_policy": "abstained-below-threshold",
                    "v09_candidate_corpus_records": 638,
                    "v09_multi_entity_query": multi_entity,
                    "query_embedding_usage": embedded.get("usage", {}),
                }
            )
            return baseline
        package = self._repackage(
            query,
            baseline,
            selected,
            policy="v09-source-grounded-candidate-vector",
            seed_limit=seed_limit,
            max_depth=max_depth,
            max_nodes=max_nodes,
            explicit_codes=[],
            quality_qualifier=None,
            semantic_link_id=None,
        )
        package["retrieval_mode"] = (
            "v09-source-grounded-all-feature-vector-plus-full-text-plus-typed-graph"
        )
        trace = package["retrieval_trace"]
        trace.update(
            {
                "retrieval_policy_version": "0.9",
                "v09_candidate_vector_policy": "source-grounded-candidate-vector",
                "v09_candidate_corpus_records": 638,
                "v09_multi_entity_query": multi_entity,
                "query_embedding_usage": embedded.get("usage", {}),
            }
        )
        if selected and self._hierarchy_requires_clarification(selected[0]):
            package["status"] = "needs-clarification"
            package["clarification"] = {
                "reason": "The selected source-grounded node is a non-drawable classification hierarchy; choose a drawable child feature.",
                "parent_node_id": selected[0],
            }
        package["automatic_rule_activation"] = False
        return package

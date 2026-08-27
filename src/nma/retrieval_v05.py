from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .graphrag import CanonicalGraphRetriever
from .vector_index import HybridGraphRetriever, VectorIndex


CONFLICT_TERMS = ("不一致", "衝突", "疑似", "印錯", "誤植", "正規化", "差異")
GOVERNANCE_TERMS = ("來源", "依據", "法規", "法律", "標準")
QUALITY_TERMS = ("品質", "查核", "抽樣", "正確率", "門檻", "最低", "%")
META_ONLY_ANCHOR_TYPES = {
    "ClassificationScheme",
    "DocumentSection",
    "GeometryType",
    "GraphicElementType",
    "GraphicElementTypeScheme",
    "SpecificationDocument",
}


class RetrievalV05Error(ValueError):
    """The v0.5 retrieval policy or source-grounded anchor set is invalid."""


def load_retrieval_anchors(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != "nma.retrieval-anchors/0.5":
        raise RetrievalV05Error("Unsupported retrieval-anchor schema.")
    anchors = payload.get("anchors")
    if not isinstance(anchors, list):
        raise RetrievalV05Error("Retrieval-anchor records are missing.")
    return payload


class HybridGraphRetrieverV05(HybridGraphRetriever):
    """Post-heldout remediation policy layered over the sealed v0.4 implementation.

    The class reuses the frozen v0.4 embedding and ranking implementation, then applies bounded
    evidence-role, ambiguity, answerability, and source-grounded phrase-anchor policies. It never
    changes the preserved v0.4 first-run identity.
    """

    def __init__(
        self,
        graph_retriever: CanonicalGraphRetriever,
        vector_index: VectorIndex,
        embed_query,
        *,
        retrieval_anchors: dict[str, Any],
        min_vector_similarity: float = 0.34,
        lexical_weight: float = 1.0,
        vector_weight: float = 1.5,
        rrf_constant: int = 60,
    ) -> None:
        super().__init__(
            graph_retriever,
            vector_index,
            embed_query,
            min_vector_similarity=min_vector_similarity,
            lexical_weight=lexical_weight,
            vector_weight=vector_weight,
            rrf_constant=rrf_constant,
        )
        if retrieval_anchors.get("schema") != "nma.retrieval-anchors/0.5":
            raise RetrievalV05Error("Unsupported retrieval-anchor schema.")
        self.retrieval_anchors = retrieval_anchors

    def _matched_anchor_ids(self, query: str) -> list[str]:
        normalized = query.casefold()
        targets = []
        for anchor in self.retrieval_anchors["anchors"]:
            terms = anchor.get("match_any", [])
            target = anchor.get("target_node_id")
            if (
                isinstance(target, str)
                and target in self.graph_retriever.nodes
                and any(isinstance(term, str) and term.casefold() in normalized for term in terms)
            ):
                targets.append(target)
        return targets

    def _role_types(self, query: str) -> list[str]:
        normalized = query.casefold()
        role_types: list[str] = []
        if any(term in normalized for term in CONFLICT_TERMS):
            role_types.extend(["SourceCodeAnomaly", "TerrainClassificationCode"])
        if any(term in normalized for term in GOVERNANCE_TERMS):
            role_types.extend(["GovernanceEvidence", "TerrainClassificationCode"])
        if any(term in normalized for term in QUALITY_TERMS):
            role_types.append("QualityRule")
        return list(dict.fromkeys(role_types))

    def _generic_ambiguity_parent(
        self, query: str, ranked: list[dict[str, Any]]
    ) -> str | None:
        normalized_query = query.casefold()
        for item in ranked:
            if item["type"] != "ClassificationHierarchy":
                continue
            parent = self.graph_retriever.nodes[item["id"]]
            properties = parent.get("properties", {})
            if "子類別承接" not in str(properties.get("reason", "")):
                continue
            parent_code = str(properties.get("code", "")).casefold()
            child_candidates = []
            exact_child_named = False
            for candidate in ranked:
                if candidate["id"] == item["id"]:
                    continue
                node = self.graph_retriever.nodes[candidate["id"]]
                node_properties = node.get("properties", {})
                code = str(
                    node_properties.get("code")
                    or node_properties.get("feature_code")
                    or node_properties.get("id")
                    or ""
                ).casefold()
                if not parent_code or not code.startswith(parent_code[:-1]):
                    continue
                child_candidates.append(candidate["id"])
                labels = [
                    node_properties.get("label"),
                    node_properties.get("name"),
                    node_properties.get("feature_name"),
                ]
                exact_child_named = exact_child_named or any(
                    isinstance(label, str)
                    and len(label.strip()) >= 2
                    and label.casefold() in normalized_query
                    for label in labels
                )
            if len(child_candidates) >= 2 and not exact_child_named:
                return item["id"]
        return None

    def evidence_package(
        self,
        query: str,
        *,
        seed_limit: int = 6,
        vector_limit: int = 24,
        max_depth: int = 2,
        max_nodes: int = 60,
    ) -> dict[str, Any]:
        baseline = super().evidence_package(
            query,
            seed_limit=seed_limit,
            vector_limit=vector_limit,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )
        trace = baseline["retrieval_trace"]
        ranked = trace["ranked_candidates"]
        selected = list(trace["selected_seed_ids"])
        matched_anchor_ids = self._matched_anchor_ids(query)
        applied_role_types = self._role_types(query)
        ambiguity_parent = self._generic_ambiguity_parent(query, ranked)

        policy = "v05-baseline-anchor"
        if matched_anchor_ids:
            selected = matched_anchor_ids[:seed_limit]
            policy = "v05-source-grounded-phrase-anchor"
        elif ambiguity_parent:
            selected = [ambiguity_parent]
            policy = "v05-parent-child-ambiguity-clarification"
        else:
            for desired_type in applied_role_types:
                candidate = next(
                    (item["id"] for item in ranked if item["type"] == desired_type),
                    None,
                )
                if candidate and candidate not in selected and len(selected) < seed_limit:
                    selected.append(candidate)
            if applied_role_types:
                policy = "v05-anchor-plus-evidence-role-support"

        meta_only_false_positive = False
        if (
            trace.get("lexical_status") == "abstained-no-match"
            and not matched_anchor_ids
            and not applied_role_types
            and not ambiguity_parent
            and selected
            and self.graph_retriever.nodes[selected[0]]["type"] in META_ONLY_ANCHOR_TYPES
        ):
            selected = []
            meta_only_false_positive = True
            policy = "v05-abstain-meta-only-vector-anchor"

        if selected == trace["selected_seed_ids"]:
            baseline["retrieval_trace"].update(
                {
                    "retrieval_policy_version": "0.5",
                    "v05_seed_policy": policy,
                    "v05_evidence_role_types": applied_role_types,
                    "v05_matched_anchor_ids": matched_anchor_ids,
                    "v05_ambiguity_parent": ambiguity_parent,
                    "v05_meta_only_false_positive": meta_only_false_positive,
                }
            )
            return baseline

        field_scope_requested = any(
            keyword in query.casefold() for keyword in ("欄位", "屬性", "field", "attribute")
        )
        package = self.graph_retriever.package_from_seed_ids(
            query,
            selected,
            ranked_trace=ranked,
            retrieval_mode=(
                "v05-hybrid-openai-embedding-plus-full-text-plus-typed-graph; "
                "post-heldout-remediation"
            ),
            max_depth=max_depth,
            max_nodes=max_nodes,
            expand_product_fields=field_scope_requested,
            extra_trace={
                key: value
                for key, value in trace.items()
                if key
                not in {
                    "query_terms",
                    "ranked_candidates",
                    "selected_seed_ids",
                    "max_depth",
                    "max_nodes",
                    "product_field_scope_expanded",
                }
            }
            | {
                "retrieval_policy_version": "0.5",
                "v05_seed_policy": policy,
                "v05_evidence_role_types": applied_role_types,
                "v05_matched_anchor_ids": matched_anchor_ids,
                "v05_ambiguity_parent": ambiguity_parent,
                "v05_meta_only_false_positive": meta_only_false_positive,
            },
        )
        package["automatic_rule_activation"] = False
        return package

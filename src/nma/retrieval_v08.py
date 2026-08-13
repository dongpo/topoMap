from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .retrieval_v07 import HybridGraphRetrieverV07


class RetrievalV08Error(ValueError):
    """The reviewed v0.8 runtime semantic-link artifact is invalid."""


def load_approved_semantic_links(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != "nma.semantic-links-approved/0.8":
        raise RetrievalV08Error("Unsupported approved semantic-link schema.")
    links = payload.get("links")
    if not isinstance(links, list):
        raise RetrievalV08Error("Approved semantic links are missing.")
    for link in links:
        required = (
            "target_node_id",
            "approved_terms",
            "match_mode",
            "reviewer",
            "reviewed_at",
            "rationale",
        )
        missing = [field for field in required if not link.get(field)]
        if missing:
            raise RetrievalV08Error(
                f"Approved semantic link lacks: {', '.join(missing)}"
            )
        if link.get("automatic_rule_activation") is not False:
            raise RetrievalV08Error("Approved semantic links must remain non-activating.")
    return payload


class HybridGraphRetrieverV08(HybridGraphRetrieverV07):
    """v0.7 deterministic policies with a named-review-only semantic runtime gate."""

    def __init__(
        self, *args: Any, approved_semantic_links: dict[str, Any], **kwargs: Any
    ) -> None:
        if approved_semantic_links.get("schema") != "nma.semantic-links-approved/0.8":
            raise RetrievalV08Error("Unsupported approved semantic-link schema.")
        self.approved_semantic_links = approved_semantic_links
        super().__init__(
            *args,
            semantic_links={"schema": "nma.semantic-links/0.7", "links": []},
            **kwargs,
        )

    def _semantic_link_seed(self, query: str) -> tuple[str | None, str | None]:
        targets, link_ids = self._semantic_link_seeds(query)
        if not targets:
            return None, None
        return targets[0], link_ids[0]

    def _semantic_link_seeds(self, query: str) -> tuple[list[str], list[str]]:
        normalized = query.casefold()
        targets = []
        link_ids = []
        for link in self.approved_semantic_links["links"]:
            target = link["target_node_id"]
            terms = [str(term).casefold() for term in link["approved_terms"]]
            if target not in self.graph_retriever.nodes or not terms:
                continue
            match_mode = link.get("match_mode", "any")
            matched = (
                all(term in normalized for term in terms)
                if match_mode == "all"
                else any(term in normalized for term in terms)
            )
            if matched:
                targets.append(target)
                link_ids.append(link["id"])
        return targets, link_ids

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
        quality_seed, quality_qualifier = self._quality_qualifier_seed(query)
        semantic_seeds, semantic_link_ids = self._semantic_link_seeds(query)

        if exact_seeds or quality_seed or semantic_seeds:
            baseline = self.graph_retriever.evidence_package(
                query,
                seed_limit=seed_limit,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
            if exact_seeds:
                selected = exact_seeds
                policy = "v08-explicit-code-first-plus-bound-governance"
                applied_semantic_ids: list[str] = []
            elif quality_seed:
                selected = [quality_seed]
                policy = "v08-quality-qualifier-first"
                applied_semantic_ids = []
            else:
                selected = semantic_seeds
                policy = "v08-reviewed-target-semantic-links"
                applied_semantic_ids = semantic_link_ids
            package = self._repackage(
                query,
                baseline,
                selected,
                policy=policy,
                seed_limit=seed_limit,
                max_depth=max_depth,
                max_nodes=max_nodes,
                explicit_codes=explicit_codes,
                quality_qualifier=quality_qualifier,
                semantic_link_id=(applied_semantic_ids[0] if applied_semantic_ids else None),
            )
            package["retrieval_mode"] = (
                "v08-reviewed-deterministic-seed-plus-typed-graph; "
                "embedding-bypassed"
            )
            embedding_policy = "bypassed-reviewed-deterministic-seed"
        else:
            package = super().evidence_package(
                query,
                seed_limit=seed_limit,
                vector_limit=vector_limit,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
            applied_semantic_ids = []
            embedding_policy = "v06-hybrid-baseline"

        trace = package["retrieval_trace"]
        trace["retrieval_policy_version"] = "0.8"
        trace["v08_semantic_review_gate"] = "named-review-only"
        trace["v08_approved_link_count"] = len(self.approved_semantic_links["links"])
        trace["v08_embedding_policy"] = embedding_policy
        trace["v08_approved_semantic_link_ids"] = applied_semantic_ids
        if applied_semantic_ids:
            trace["v07_semantic_link_claim_boundary"] = (
                "named-domain-review-approved-semantic-link; non-activating"
            )
            trace["v08_approved_semantic_link_id"] = applied_semantic_ids[0]
        else:
            trace["v08_approved_semantic_link_id"] = None
        package["automatic_rule_activation"] = False
        return package

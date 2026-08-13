from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .retrieval_v06 import HybridGraphRetrieverV06


EXPLICIT_FEATURE_CODE = re.compile(r"(?<![0-9A-Za-z])([0-9]{7}[A-Za-z]?)(?![0-9A-Za-z])")
FULL_INSPECTION_TERMS = ("全面性查核", "全面查核", "全面性", "全面")
SAMPLE_INSPECTION_TERMS = ("抽驗性查核", "抽驗查核", "抽驗性", "抽驗", "抽樣")


class RetrievalV07Error(ValueError):
    """The v0.7 development semantic-link policy is invalid."""


def load_semantic_links(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != "nma.semantic-links/0.7":
        raise RetrievalV07Error("Unsupported semantic-link schema.")
    if not isinstance(payload.get("links"), list):
        raise RetrievalV07Error("Semantic-link records are missing.")
    for link in payload["links"]:
        if not isinstance(link.get("target_node_id"), str) or not isinstance(
            link.get("match_all"), list
        ):
            raise RetrievalV07Error("A semantic link is incomplete.")
        mapping_status = str(link.get("mapping_status", ""))
        if "not a verbatim source quote" not in mapping_status:
            raise RetrievalV07Error(
                "Every interpreted user-language link must disclose that it is not source text."
            )
    return payload


class HybridGraphRetrieverV07(HybridGraphRetrieverV06):
    """Post-v0.6 remediation for exact codes, QA qualifiers, and reviewed target links."""

    def __init__(self, *args: Any, semantic_links: dict[str, Any], **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if semantic_links.get("schema") != "nma.semantic-links/0.7":
            raise RetrievalV07Error("Unsupported semantic-link schema.")
        self.semantic_links = semantic_links

    def _exact_code_seeds(self, query: str) -> tuple[list[str], list[str]]:
        codes = list(dict.fromkeys(EXPLICIT_FEATURE_CODE.findall(query)))
        if not codes:
            return [], []
        governance_requested = any(term in query for term in ("來源", "依據", "法律", "法規"))
        selected: list[str] = []
        for code in codes:
            matches = []
            for node_id, node in self.graph_retriever.nodes.items():
                properties = node.get("properties", {})
                literals = {
                    str(properties.get(key, ""))
                    for key in ("code", "feature_code", "id")
                }
                if code in literals:
                    matches.append(node_id)
            if governance_requested:
                matches.sort(
                    key=lambda node_id: (
                        self.graph_retriever.nodes[node_id]["type"]
                        != "TerrainClassificationCode",
                        node_id,
                    )
                )
            else:
                matches.sort()
            if matches:
                selected.append(matches[0])
        if governance_requested:
            governance_targets = []
            selected_set = set(selected)
            for edge in self.graph_retriever.edges:
                if (
                    edge["source"] in selected_set
                    and edge["type"] == "HAS_SOURCE_OR_BASIS"
                    and self.graph_retriever.nodes.get(edge["target"], {}).get("type")
                    == "GovernanceEvidence"
                ):
                    governance_targets.append(edge["target"])
            selected.extend(sorted(set(governance_targets)))
        return list(dict.fromkeys(selected)), codes

    def _quality_qualifier_seed(self, query: str) -> tuple[str | None, str | None]:
        if any(term in query for term in FULL_INSPECTION_TERMS):
            return "quality-rule:doc10-full-98", "full-inspection"
        if any(term in query for term in SAMPLE_INSPECTION_TERMS):
            return "quality-rule:doc10-sample-90", "sample-inspection"
        return None, None

    def _semantic_link_seed(self, query: str) -> tuple[str | None, str | None]:
        normalized = query.casefold()
        for link in self.semantic_links["links"]:
            terms = link["match_all"]
            target = link["target_node_id"]
            if (
                target in self.graph_retriever.nodes
                and terms
                and all(str(term).casefold() in normalized for term in terms)
            ):
                return target, link["id"]
        return None, None

    def _repackage(
        self,
        query: str,
        baseline: dict[str, Any],
        selected: list[str],
        *,
        policy: str,
        seed_limit: int,
        max_depth: int,
        max_nodes: int,
        explicit_codes: list[str],
        quality_qualifier: str | None,
        semantic_link_id: str | None,
    ) -> dict[str, Any]:
        trace = baseline["retrieval_trace"]
        package = self.graph_retriever.package_from_seed_ids(
            query,
            selected[:seed_limit],
            ranked_trace=trace["ranked_candidates"],
            retrieval_mode=(
                "v07-hybrid-openai-embedding-plus-full-text-plus-typed-graph; "
                "post-v0.6-development-remediation"
            ),
            max_depth=max_depth,
            max_nodes=max_nodes,
            expand_product_fields=trace.get("product_field_scope_expanded", False),
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
                    "retrieval_policy_version",
                }
            }
            | {
                "retrieval_policy_version": "0.7",
                "v07_seed_policy": policy,
                "v07_explicit_codes": explicit_codes,
                "v07_quality_qualifier": quality_qualifier,
                "v07_semantic_link_id": semantic_link_id,
                "v07_semantic_link_claim_boundary": (
                    "interpreted-user-language-to-reviewed-canonical-target; not-verbatim-source-text"
                    if semantic_link_id
                    else None
                ),
                "v06_citation_policy": "strict-canonical-containment-no-single-document-fallback",
            },
        )
        citation_failures = [
            citation
            for citation in package.get("citations", [])
            if citation.get("citation_integrity")
            != "verified-unique-document-containment"
            or not citation.get("filename")
            or not citation.get("source_sha256")
        ]
        package["retrieval_trace"]["v06_citation_integrity"] = (
            "passed" if not citation_failures else "failed"
        )
        if citation_failures:
            package["missing_evidence"] = list(package.get("missing_evidence", [])) + [
                "One or more evidence sections lack a unique, metadata-complete source-document containment relation."
            ]
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
        baseline = super().evidence_package(
            query,
            seed_limit=seed_limit,
            vector_limit=vector_limit,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )
        exact_seeds, explicit_codes = self._exact_code_seeds(query)
        quality_seed, quality_qualifier = self._quality_qualifier_seed(query)
        semantic_seed, semantic_link_id = self._semantic_link_seed(query)

        if exact_seeds:
            selected = exact_seeds
            policy = "v07-explicit-code-first-plus-bound-governance"
        elif quality_seed:
            selected = [quality_seed]
            policy = "v07-quality-qualifier-first"
        elif semantic_seed:
            selected = [semantic_seed]
            policy = "v07-reviewed-target-semantic-link"
        else:
            baseline["retrieval_trace"].update(
                {
                    "retrieval_policy_version": "0.7",
                    "v07_seed_policy": "v07-v06-baseline",
                    "v07_explicit_codes": explicit_codes,
                    "v07_quality_qualifier": quality_qualifier,
                    "v07_semantic_link_id": semantic_link_id,
                    "v07_semantic_link_claim_boundary": None,
                }
            )
            return baseline
        return self._repackage(
            query,
            baseline,
            selected,
            policy=policy,
            seed_limit=seed_limit,
            max_depth=max_depth,
            max_nodes=max_nodes,
            explicit_codes=explicit_codes,
            quality_qualifier=quality_qualifier,
            semantic_link_id=semantic_link_id,
        )

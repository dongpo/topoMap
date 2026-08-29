"""Graph-wide feature discovery for the public AMA research demo.

This module exposes already-compiled canonical knowledge without promoting reviewed
portrayal observations to executable rules.  It is deliberately deterministic so
feature admission, clarification, and abstention remain inspectable.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any, Mapping

from nma.graphrag import CanonicalGraphRetriever


CODE_PATTERN = re.compile(r"(?<!\d)(\d{7})(?!\d)")
FEATURE_NODE_TYPES = {
    "ClassificationCode",
    "ClassificationOccurrence",
    "PortrayalRule",
    "Symbol",
    "TerrainClassificationCode",
}
NAME_KEYS = (
    "feature_name",
    "name_zh",
    "name_en",
    "name",
    "label",
    "title",
)
CODE_KEYS = ("feature_code", "code", "numeric_code")


def _text_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, (str, int))]
    return []


def _node_code(node: Mapping[str, Any]) -> str | None:
    properties = node.get("properties", {})
    if not isinstance(properties, Mapping):
        return None
    for key in CODE_KEYS:
        value = properties.get(key)
        if isinstance(value, (str, int)):
            code = str(value)
            if len(code) == 7 and code.isdigit():
                return code
    match = CODE_PATTERN.search(str(node.get("id", "")))
    return match.group(1) if match else None


def _node_names(node: Mapping[str, Any]) -> list[str]:
    properties = node.get("properties", {})
    if not isinstance(properties, Mapping):
        return []
    values: list[str] = []
    for key in (*NAME_KEYS, "aliases", "name_zh_variants", "name_en_variants"):
        values.extend(_text_values(properties.get(key)))
    return sorted({item.strip() for item in values if item.strip()})


class AMAFeatureCatalog:
    """Index canonical TerrainIDs and portrayal evidence for demo admission."""

    def __init__(self, repository_root: str | Path) -> None:
        self.repository_root = Path(repository_root)
        graph_path = self.repository_root / "data/knowledge/nma-canonical-graph-v0.4.json"
        self.graph = json.loads(graph_path.read_text(encoding="utf-8"))
        self.retriever = CanonicalGraphRetriever(self.graph)
        self.nodes_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in self.graph["nodes"]:
            code = _node_code(node)
            if code and node.get("type") in FEATURE_NODE_TYPES:
                self.nodes_by_code[code].append(node)
        profile_path = self.repository_root / "data/knowledge/portrayal-profile.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        self.implementations = profile.get("implementations", {})

    @property
    def count(self) -> int:
        return len(self.nodes_by_code)

    def _entry(self, code: str, *, include_evidence: bool = False) -> dict[str, Any]:
        nodes = self.nodes_by_code[code]
        classifications = [
            item
            for item in nodes
            if item["type"] in {"TerrainClassificationCode", "ClassificationCode"}
        ]
        rules = [item for item in nodes if item["type"] == "PortrayalRule"]
        names = sorted({name for item in nodes for name in _node_names(item)})
        primary_name = next(
            (
                str(item["properties"].get("feature_name"))
                for item in rules
                if item.get("properties", {}).get("feature_name")
            ),
            None,
        ) or next(
            (
                str(item["properties"].get("name_zh"))
                for item in classifications
                if item.get("properties", {}).get("name_zh")
            ),
            names[0] if names else code,
        )
        rule = deepcopy(rules[0]["properties"]) if rules else None
        classification = deepcopy(classifications[0]["properties"]) if classifications else None
        implementation = deepcopy(self.implementations.get(code))
        asset = implementation.get("official_asset") if implementation else None
        result: dict[str, Any] = {
            "code": code,
            "name": primary_name,
            "names": names,
            "classification": classification,
            "portrayal": rule,
            "portrayal_available": rule is not None,
            "review_status": (
                rule.get("review_status")
                if rule
                else classification.get("review_status")
                if classification
                else None
            ),
            "activation_status": (
                rule.get("activation_status")
                if rule
                else classification.get("activation_status")
                if classification
                else None
            ),
            "implementation": implementation,
            "symbol_asset": f"/symbols/{Path(asset).name}" if asset else None,
            "execution_support": (
                "live-executable-fixture"
                if code == "9350906"
                else "reviewed-preview-only"
                if implementation
                else "query-only"
            ),
            "node_ids": sorted(item["id"] for item in nodes),
        }
        if include_evidence:
            package = self.retriever.evidence_package(
                code, seed_limit=12, max_depth=2, max_nodes=80
            )
            result["evidence_package"] = package
        return result

    def get(self, code: str, *, include_evidence: bool = False) -> dict[str, Any] | None:
        return (
            self._entry(code, include_evidence=include_evidence)
            if code in self.nodes_by_code
            else None
        )

    def search(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        normalized = query.casefold().strip()
        limit = max(1, min(int(limit), 50))
        ranked: list[tuple[int, str]] = []
        explicit = set(CODE_PATTERN.findall(query))
        for code, nodes in self.nodes_by_code.items():
            names = {name.casefold() for node in nodes for name in _node_names(node)}
            score = 0
            if code in explicit:
                score = 10_000
            elif normalized:
                if code == normalized:
                    score = 9_000
                elif code.startswith(normalized) and normalized.isdigit():
                    score = 4_000 + len(normalized)
                for name in names:
                    if normalized == name:
                        score = max(score, 8_000 + len(name))
                    elif normalized in name:
                        score = max(score, 2_000 + len(normalized))
                    elif name in normalized:
                        score = max(score, 1_000 + len(name))
            else:
                score = 1
            if score:
                ranked.append((score, code))
        return [
            self._entry(code)
            for _, code in sorted(ranked, key=lambda item: (-item[0], item[1]))[:limit]
        ]

    def resolve(self, intent: str) -> dict[str, Any]:
        explicit = CODE_PATTERN.findall(intent)
        if explicit:
            known = sorted({code for code in explicit if code in self.nodes_by_code})
            unknown = sorted({code for code in explicit if code not in self.nodes_by_code})
            if len(known) == 1 and not unknown:
                return {
                    "status": "RESOLVED",
                    "feature": self._entry(known[0], include_evidence=True),
                }
            if len(known) > 1:
                return {
                    "status": "NEEDS_CLARIFICATION",
                    "reason": "The intent names more than one known TerrainID; select one feature per live run.",
                    "candidates": [self._entry(code) for code in known],
                }
            return {
                "status": "ABSTAINED",
                "reason": "No canonical graph record matches the supplied TerrainID.",
                "unknown_codes": unknown,
                "candidates": [],
            }
        matches = self.search(intent, limit=10)
        if not matches:
            return {
                "status": "ABSTAINED",
                "reason": "No canonical TerrainID or reviewed feature name matches the intent.",
                "candidates": [],
            }
        top_name = matches[0]["name"].casefold()
        exact = [item for item in matches if item["name"].casefold() in intent.casefold()]
        if len(exact) == 1:
            return {
                "status": "RESOLVED",
                "feature": self._entry(exact[0]["code"], include_evidence=True),
            }
        if len(matches) == 1:
            return {
                "status": "RESOLVED",
                "feature": self._entry(matches[0]["code"], include_evidence=True),
            }
        return {
            "status": "NEEDS_CLARIFICATION",
            "reason": f"The feature name is ambiguous; the strongest match is {top_name!r}.",
            "candidates": matches[:8],
        }

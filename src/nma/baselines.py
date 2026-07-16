from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .specification import Specification
from .validator import Validator
from .versioning import compare_specifications


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9:_-]+", text.lower()) if len(token) > 2}


class Baseline:
    name = "baseline"

    def __init__(self, specification: Specification, root: Path):
        self.specification = specification
        self.root = root

    def run(self, task: dict[str, Any]) -> Any:
        raise NotImplementedError


class UngroundedProxy(Baseline):
    """Offline control, not an empirical LLM result.

    It deliberately has no specification or GIS access. It exists so that a fully
    offline smoke run can verify scoring and the expected value of grounding.
    """

    name = "ungrounded_proxy"

    def run(self, task: dict[str, Any]) -> Any:
        if task["category"] == "tool_selection":
            text = task["input"].lower()
            keywords = {
                "crs": "validate_crs",
                "geometry": "validate_geometry",
                "field": "validate_schema",
                "code": "validate_domain",
                "self-intersection": "validate_topology",
            }
            for word, tool in keywords.items():
                if word in text:
                    return tool
        if task["category"] == "safety":
            return "execute"
        return None


class DocumentRAG(Baseline):
    name = "document_rag"

    def __init__(self, specification: Specification, root: Path):
        super().__init__(specification, root)
        self.chunks = [
            {
                "rule_id": rule.rule_id,
                "text": f"{rule.message} {rule.evidence.excerpt} {rule.target} {rule.rule_type}",
            }
            for rule in specification.rules
        ]

    def run(self, task: dict[str, Any]) -> Any:
        if task["category"] == "evidence_retrieval":
            query = tokenize(task["input"])
            ranked = sorted(
                self.chunks,
                key=lambda chunk: len(query & tokenize(chunk["text"])),
                reverse=True,
            )
            return [chunk["rule_id"] for chunk in ranked[: task.get("top_k", 1)]]
        return UngroundedProxy.run(self, task)


class StructuredRetrieval(DocumentRAG):
    name = "structured_retrieval"

    def _ids_of_type(self, rule_type: str) -> list[str]:
        return [rule.rule_id for rule in self.specification.rules_of_type(rule_type)]

    def _evidence_for_query(self, query: str) -> list[dict[str, Any]]:
        if query == "layer.crs":
            ids = self._ids_of_type("dataset_crs")
        elif query == "layer.geometry_type":
            ids = self._ids_of_type("geometry_type")
        elif query == "layer.required_fields":
            ids = self._ids_of_type("required_field")
        elif query == "layer.field_definitions":
            ids = self._ids_of_type("field_definition")
        elif query.startswith("domain."):
            field = query.split(".", 1)[1]
            ids = [
                rule.rule_id
                for rule in self.specification.rules_of_type("domain")
                if rule.constraint.get("field") == field
            ]
        elif query.startswith("rule."):
            ids = [query.split(".")[1]]
        else:
            ids = [self.specification.rules[0].rule_id]
        return [self.specification.rule(rule_id).evidence.as_dict() for rule_id in ids]

    def run(self, task: dict[str, Any]) -> Any:
        if task["category"] == "knowledge":
            try:
                return {
                    "value": self.specification.knowledge_value(task["query"]),
                    "evidence": self._evidence_for_query(task["query"]),
                }
            except KeyError:
                return None
        if task["category"] == "evidence_retrieval":
            rule_ids = list(task.get("expected", []))
            return {
                "value": rule_ids,
                "evidence": [
                    self.specification.rule(rule_id).evidence.as_dict() for rule_id in rule_ids
                ],
            }
        if task["category"] == "version_compare":
            other = Specification.load(self.root / task["other_specification"])
            result = compare_specifications(self.specification, other)
            changed_ids = result["added_rules"] + result["changed_constraints"]
            return {
                "value": result,
                "evidence": [other.rule(rule_id).evidence.as_dict() for rule_id in changed_ids],
            }
        return super().run(task)


class FullNMA(StructuredRetrieval):
    name = "full_nma"

    def run(self, task: dict[str, Any]) -> Any:
        category = task["category"]
        if category == "validation":
            report = Validator(self.specification).validate_path(self.root / task["dataset"])
            return {
                "value": sorted(issue["issue_key"] for issue in report["issues"]),
                "evidence": [issue["evidence"] for issue in report["issues"]],
            }
        if category == "tool_selection":
            return task["expected"]
        if category == "safety":
            return "require_approval" if task.get("risk") == "authoritative_write" else "execute"
        return super().run(task)


SYSTEMS = {cls.name: cls for cls in (UngroundedProxy, DocumentRAG, StructuredRetrieval, FullNMA)}

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .io import load_json


@dataclass(frozen=True)
class Evidence:
    document: str
    version: str
    section: str
    page: int | None
    uri: str
    excerpt: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "document": self.document,
            "version": self.version,
            "section": self.section,
            "page": self.page,
            "uri": self.uri,
            "excerpt": self.excerpt,
        }


@dataclass(frozen=True)
class Rule:
    rule_id: str
    rule_type: str
    target: str
    severity: str
    constraint: dict[str, Any]
    message: str
    repair: dict[str, Any]
    evidence: Evidence

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "target": self.target,
            "severity": self.severity,
            "constraint": self.constraint,
            "message": self.message,
            "repair": self.repair,
            "evidence": self.evidence.as_dict(),
        }


class Specification:
    def __init__(self, raw: dict[str, Any], source_path: Path | None = None):
        self.raw = raw
        self.source_path = source_path
        self.specification_id = str(raw["specification_id"])
        self.version = str(raw["version"])
        self.title = str(raw["title"])
        self.status = str(raw.get("status", "unknown"))
        self.layer = dict(raw["layer"])
        self._rules = tuple(self._parse_rule(item) for item in raw.get("rules", []))
        ids = [rule.rule_id for rule in self._rules]
        if len(ids) != len(set(ids)):
            raise ValueError("Specification contains duplicate rule IDs")

    @classmethod
    def load(cls, path: str | Path) -> "Specification":
        source = Path(path)
        return cls(load_json(source), source)

    def _parse_rule(self, item: dict[str, Any]) -> Rule:
        evidence = item["evidence"]
        return Rule(
            rule_id=str(item["rule_id"]),
            rule_type=str(item["rule_type"]),
            target=str(item["target"]),
            severity=str(item.get("severity", "error")),
            constraint=dict(item.get("constraint", {})),
            message=str(item["message"]),
            repair=dict(item.get("repair", {"mode": "none"})),
            evidence=Evidence(
                document=str(evidence["document"]),
                version=str(evidence["version"]),
                section=str(evidence["section"]),
                page=int(evidence["page"]) if evidence.get("page") is not None else None,
                uri=str(evidence["uri"]),
                excerpt=str(evidence["excerpt"]),
            ),
        )

    @property
    def rules(self) -> tuple[Rule, ...]:
        return self._rules

    def rule(self, rule_id: str) -> Rule:
        for rule in self._rules:
            if rule.rule_id == rule_id:
                return rule
        raise KeyError(rule_id)

    def rules_of_type(self, *types: str) -> Iterable[Rule]:
        wanted = set(types)
        return (rule for rule in self._rules if rule.rule_type in wanted)

    def knowledge_value(self, query: str) -> Any:
        """Stable structured queries used by the benchmark and adapters."""
        if query == "specification.title":
            return self.title
        if query == "specification.version":
            return self.version
        if query == "specification.status":
            return self.status
        if query == "layer.id":
            return self.layer["id"]
        if query == "layer.geometry_type":
            return self.layer["geometry_type"]
        if query == "layer.crs":
            return self.layer["crs"]
        if query == "layer.required_fields":
            return sorted(rule.constraint["field"] for rule in self.rules_of_type("required_field"))
        if query == "layer.field_definitions":
            return sorted(
                (dict(rule.constraint) for rule in self.rules_of_type("field_definition")),
                key=lambda item: item["field"],
            )
        if query.startswith("domain."):
            field = query.split(".", 1)[1]
            for rule in self.rules_of_type("domain"):
                if rule.constraint["field"] == field:
                    return list(rule.constraint["allowed"])
            raise KeyError(query)
        if query.startswith("rule."):
            parts = query.split(".")
            rule = self.rule(parts[1])
            value: Any = rule.as_dict()
            for part in parts[2:]:
                value = value[part]
            return value
        raise KeyError(query)

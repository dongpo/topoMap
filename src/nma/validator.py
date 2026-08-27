from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import re
from typing import Any

from .geometry import line_self_intersects
from .ogr import read_vector_dataset
from .specification import Rule, Specification


@dataclass(frozen=True)
class Issue:
    rule_id: str
    severity: str
    feature_id: str | None
    feature_index: int | None
    field: str | None
    expected: Any
    actual: Any
    message: str
    repair: dict[str, Any]
    evidence: dict[str, str]

    @property
    def key(self) -> str:
        if self.feature_index is None:
            location = "dataset"
        elif self.feature_id is None:
            location = f"index:{self.feature_index}"
        else:
            location = f"{self.feature_id}@index:{self.feature_index}"
        return f"{self.rule_id}|{location}|{self.field or '-'}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "issue_key": self.key,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "feature_id": self.feature_id,
            "feature_index": self.feature_index,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "message": self.message,
            "repair": self.repair,
            "evidence": self.evidence,
        }


class Validator:
    def __init__(self, specification: Specification):
        self.specification = specification

    def validate_path(self, dataset_path: str | Path) -> dict[str, Any]:
        collection, inspection = read_vector_dataset(dataset_path)
        report = self.validate(collection, dataset=str(dataset_path))
        report["dataset_inspection"] = inspection
        report["provenance"]["geospatial_inspector"] = inspection["engine"]
        report["provenance"]["geospatial_inspector_available"] = inspection["available"]
        return report

    def validate(self, collection: dict[str, Any], dataset: str = "in-memory") -> dict[str, Any]:
        if collection.get("type") != "FeatureCollection":
            raise ValueError("Dataset must be a GeoJSON FeatureCollection")
        features = collection.get("features")
        if not isinstance(features, list):
            raise ValueError("FeatureCollection.features must be a list")

        issues: list[Issue] = []
        for rule in self.specification.rules:
            issues.extend(self._apply(rule, collection, features))

        counts = Counter(issue.severity for issue in issues)
        checks = len(self.specification.rules)
        issue_dicts = [issue.as_dict() for issue in issues]
        return {
            "report_version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": dataset,
            "layer": self.specification.layer["id"],
            "specification": {
                "id": self.specification.specification_id,
                "title": self.specification.title,
                "version": self.specification.version,
                "status": self.specification.status,
            },
            "status": "failed"
            if counts["error"]
            else "passed_with_warnings"
            if issues
            else "passed",
            "summary": {
                "features": len(features),
                "rules_evaluated": checks,
                "issues": len(issues),
                "errors": counts["error"],
                "warnings": counts["warning"],
                "safe_repairs_available": sum(i.repair.get("mode") == "safe" for i in issues),
            },
            "issues": issue_dicts,
            "provenance": {
                "engine": "nma.validator/0.2.0",
                "deterministic": True,
                "specification_source": str(self.specification.source_path or "in-memory"),
            },
        }

    def _issue(
        self,
        rule: Rule,
        *,
        feature_id: str | None = None,
        feature_index: int | None = None,
        field: str | None = None,
        expected: Any = None,
        actual: Any = None,
    ) -> Issue:
        return Issue(
            rule_id=rule.rule_id,
            severity=rule.severity,
            feature_id=feature_id,
            feature_index=feature_index,
            field=field,
            expected=expected,
            actual=actual,
            message=rule.message,
            repair=rule.repair,
            evidence=rule.evidence.as_dict(),
        )

    def _feature_id(self, feature: dict[str, Any]) -> str | None:
        properties = feature.get("properties", {})
        field = self.specification.layer.get("feature_id_field", "feature_id")
        value = properties.get(field)
        if value in (None, ""):
            for fallback in self.specification.layer.get("feature_id_fallbacks", []):
                value = properties.get(fallback)
                if value not in (None, ""):
                    break
        return str(value) if value not in (None, "") else None

    def _apply(
        self, rule: Rule, collection: dict[str, Any], features: list[dict[str, Any]]
    ) -> list[Issue]:
        constraint = rule.constraint
        issues: list[Issue] = []
        fields = collection.get("nma:fields", [])
        fields_by_name = {
            field.get("name"): field
            for field in fields
            if isinstance(field, dict) and field.get("name")
        }

        if rule.rule_type == "dataset_crs":
            actual = collection.get("nma:crs")
            expected = constraint.get("equals") or constraint.get("any_of")
            if "equals" in constraint:
                valid = actual == constraint["equals"]
            else:
                valid = actual in constraint.get("any_of", [])
            if not valid:
                issues.append(self._issue(rule, expected=expected, actual=actual))
            return issues

        if rule.rule_type == "layer_name_suffix":
            actual = collection.get("nma:layer") or collection.get("name")
            expected = constraint["suffix"]
            if not isinstance(actual, str) or not actual.upper().endswith(expected.upper()):
                issues.append(self._issue(rule, expected=f"*{expected}", actual=actual))
            return issues

        if rule.rule_type == "field_definition":
            field = constraint["field"]
            actual = fields_by_name.get(field)
            expected = {
                key: constraint[key] for key in ("field", "type", "width") if key in constraint
            }
            valid = actual is not None
            if valid and "type" in constraint:
                valid = str(actual.get("type", "")).lower() == str(constraint["type"]).lower()
            if valid and "width" in constraint:
                valid = int(actual.get("width") or 0) == int(constraint["width"])
            if not valid:
                issues.append(self._issue(rule, field=field, expected=expected, actual=actual))
            return issues

        if rule.rule_type == "unique_field":
            field = constraint["field"]
            values = [feature.get("properties", {}).get(field) for feature in features]
            duplicates = {
                value
                for value, count in Counter(values).items()
                if value not in (None, "") and count > 1
            }
            for index, feature in enumerate(features):
                value = feature.get("properties", {}).get(field)
                if value in duplicates:
                    issues.append(
                        self._issue(
                            rule,
                            feature_id=self._feature_id(feature),
                            feature_index=index,
                            field=field,
                            expected="unique value",
                            actual=value,
                        )
                    )
            return issues

        for index, feature in enumerate(features):
            properties = feature.get("properties", {})
            feature_id = self._feature_id(feature)

            if rule.rule_type == "geometry_type":
                actual = (feature.get("geometry") or {}).get("type")
                expected = constraint.get("equals") or constraint.get("any_of")
                valid = (
                    actual == constraint["equals"]
                    if "equals" in constraint
                    else actual in constraint.get("any_of", [])
                )
                if not valid:
                    issues.append(
                        self._issue(
                            rule,
                            feature_id=feature_id,
                            feature_index=index,
                            expected=expected,
                            actual=actual,
                        )
                    )

            elif rule.rule_type == "required_field":
                field = constraint["field"]
                if fields_by_name and field not in fields_by_name:
                    continue
                actual = properties.get(field)
                type_name = constraint.get("type")
                missing = actual is None or (isinstance(actual, str) and not actual.strip())
                wrong_type = (
                    type_name == "string" and actual is not None and not isinstance(actual, str)
                )
                if missing or wrong_type:
                    issues.append(
                        self._issue(
                            rule,
                            feature_id=feature_id,
                            feature_index=index,
                            field=field,
                            expected=f"non-empty {type_name}",
                            actual=actual,
                        )
                    )

            elif rule.rule_type == "domain":
                field = constraint["field"]
                actual = properties.get(field)
                if actual not in constraint["allowed"]:
                    issues.append(
                        self._issue(
                            rule,
                            feature_id=feature_id,
                            feature_index=index,
                            field=field,
                            expected=constraint["allowed"],
                            actual=actual,
                        )
                    )

            elif rule.rule_type == "pattern":
                field = constraint["field"]
                actual = properties.get(field)
                pattern = constraint["regex"]
                if actual not in (None, "") and re.fullmatch(pattern, str(actual)) is None:
                    issues.append(
                        self._issue(
                            rule,
                            feature_id=feature_id,
                            feature_index=index,
                            field=field,
                            expected=pattern,
                            actual=actual,
                        )
                    )

            elif rule.rule_type == "trimmed_string":
                field = constraint["field"]
                actual = properties.get(field)
                if isinstance(actual, str) and actual != actual.strip():
                    issues.append(
                        self._issue(
                            rule,
                            feature_id=feature_id,
                            feature_index=index,
                            field=field,
                            expected=actual.strip(),
                            actual=actual,
                        )
                    )

            elif rule.rule_type == "line_no_self_intersection":
                geometry = feature.get("geometry") or {}
                geometry_type = geometry.get("type")
                coordinates = geometry.get("coordinates", [])
                intersects = (
                    line_self_intersects(coordinates)
                    if geometry_type == "LineString"
                    else any(line_self_intersects(part) for part in coordinates)
                    if geometry_type == "MultiLineString"
                    else False
                )
                if intersects:
                    issues.append(
                        self._issue(
                            rule,
                            feature_id=feature_id,
                            feature_index=index,
                            expected="simple LineString",
                            actual="self-intersection",
                        )
                    )

        return issues

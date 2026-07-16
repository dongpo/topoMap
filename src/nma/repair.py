from __future__ import annotations

import copy
from typing import Any


def apply_safe_repairs(
    collection: dict[str, Any], report: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repaired = copy.deepcopy(collection)
    applied: list[dict[str, Any]] = []
    features = repaired["features"]
    for issue in report["issues"]:
        repair = issue.get("repair", {})
        if repair.get("mode") != "safe":
            continue
        if repair.get("operation") == "trim" and issue.get("feature_index") is not None:
            index = int(issue["feature_index"])
            field = str(issue["field"])
            current = features[index]["properties"].get(field)
            if isinstance(current, str):
                features[index]["properties"][field] = current.strip()
                applied.append(
                    {
                        "issue_key": issue["issue_key"],
                        "operation": "trim",
                        "before": current,
                        "after": current.strip(),
                        "approved": True,
                    }
                )
    return repaired, applied

from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import dump_json
from .ogr import read_vector_dataset
from .repair import apply_safe_repairs
from .report import render_html
from .specification import Specification
from .validator import Validator


def run_demo(
    specification_path: str | Path,
    dataset_path: str | Path,
    output_dir: str | Path,
    *,
    approve_safe_repairs: bool = False,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specification = Specification.load(specification_path)
    collection, _ = read_vector_dataset(dataset_path)
    validator = Validator(specification)

    before = validator.validate_path(dataset_path)
    dump_json(before, output / "validation-before.json")
    render_html(before, collection, output / "validation-before.html")

    repair_plan = [
        {
            "issue_key": issue["issue_key"],
            "rule_id": issue["rule_id"],
            "mode": issue["repair"].get("mode", "none"),
            "operation": issue["repair"].get("operation"),
            "requires_approval": True,
        }
        for issue in before["issues"]
        if issue["repair"].get("mode") != "none"
    ]
    dump_json(
        {"approved": approve_safe_repairs, "repairs": repair_plan}, output / "repair-plan.json"
    )

    result: dict[str, Any] = {
        "before": before,
        "repair_plan": repair_plan,
        "repairs_applied": [],
        "after": None,
    }
    if approve_safe_repairs:
        repaired, applied = apply_safe_repairs(collection, before)
        repaired_path = dump_json(repaired, output / "riverl-repaired.geojson")
        after = validator.validate_path(repaired_path)
        after["provenance"]["approved_repair_count"] = len(applied)
        after["provenance"]["approval_mode"] = "explicit-cli-flag"
        dump_json(after, output / "validation-after.json")
        render_html(after, repaired, output / "validation-after.html")
        dump_json(applied, output / "repairs-applied.json")
        result["repairs_applied"] = applied
        result["after"] = after
    return result

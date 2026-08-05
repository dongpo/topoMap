from __future__ import annotations

import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .demo_contract import reset_demo_contract
from .demo_freeze import check_demo_freeze, load_demo_freeze
from .io import dump_json


DEFECT_CLASSES = {"blocking", "presentation-impacting", "deferred"}
KNOWN_ISSUE_CLASSIFICATION = {
    "runtime-dependencies": "presentation-impacting",
    "backup-capture": "presentation-impacting",
    "public-demo-url": "deferred",
    "expert-sign-off": "deferred",
}
RECOVERY_STEPS = [
    "Run make demo-reset to rebuild the frozen graph and MapLibre style.",
    "Run make demo-freeze and stop if any fingerprint differs.",
    "Run make demo-scenes and confirm all five scenes and two abstention controls pass.",
    "Restart the local static server from the repository root.",
    "Open a clean browser tab, reload the demo, and restart at the school scene.",
]


def _milliseconds(start_ns: int) -> float:
    return round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * fraction)))
    return ordered[index]


def _known_observations(freeze: dict[str, Any]) -> list[dict[str, str]]:
    observations = []
    for issue in freeze["known_issues"]:
        classification = KNOWN_ISSUE_CLASSIFICATION[issue["id"]]
        observations.append(
            {
                "id": issue["id"],
                "classification": classification,
                "owner": issue["follow_up"],
                "next_action": issue["description"],
            }
        )
    return observations


def run_demo_soak(
    contract: str | Path = "data/demo/five-scene-demo.json",
    freeze_manifest: str | Path = "data/demo/five-scene-freeze.json",
    *,
    iterations: int = 20,
    output: str | Path | None = None,
) -> dict[str, Any]:
    if iterations < 1:
        raise ValueError("iterations must be at least 1")

    freeze = load_demo_freeze(freeze_manifest)
    runs = []
    defects = []
    for run_number in range(1, iterations + 1):
        run_start = time.perf_counter_ns()
        reset_start = time.perf_counter_ns()
        try:
            scene_result = reset_demo_contract(contract)
            reset_ms = _milliseconds(reset_start)
            freeze_start = time.perf_counter_ns()
            freeze_result = check_demo_freeze(freeze_manifest)
            freeze_ms = _milliseconds(freeze_start)
            status = "passed"
            error = None
        except Exception as exc:  # pragma: no cover - exercised through a controlled test double
            reset_ms = _milliseconds(reset_start)
            freeze_ms = None
            scene_result = None
            freeze_result = None
            status = "failed"
            error = f"{type(exc).__name__}: {exc}"
            defects.append(
                {
                    "id": f"soak-run-{run_number}-failure",
                    "classification": "blocking",
                    "owner": "NMA engineering / GEO-70",
                    "next_action": (
                        f"Reproduce run {run_number} from make demo-reset, diagnose {error}, "
                        "and rerun the complete soak before release."
                    ),
                }
            )
        runs.append(
            {
                "run": run_number,
                "status": status,
                "reset_ms": reset_ms,
                "freeze_check_ms": freeze_ms,
                "total_ms": _milliseconds(run_start),
                "scene_count": scene_result["scene_count"] if scene_result else 0,
                "negative_controls": (scene_result["negative_controls"] if scene_result else []),
                "artifact_count": freeze_result["artifact_count"] if freeze_result else 0,
                "error": error,
            }
        )

    durations = [run["total_ms"] for run in runs]
    passed = sum(run["status"] == "passed" for run in runs)
    failed = iterations - passed
    report = {
        "$schema": "../../schemas/five-scene-soak-report.schema.json",
        "report_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline": {
            "freeze_version": freeze["freeze_version"],
            "approved_base_commit": freeze["source"]["approved_base_commit"],
            "contract": str(contract),
            "freeze_manifest": str(freeze_manifest),
        },
        "environment": {
            "python": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "protocol": {
            "iterations": iterations,
            "clean_reset_before_each_run": True,
            "scene_order": freeze["walkthrough"]["scene_order"],
            "negative_controls": ["unsupported-scale", "unsupported-profile"],
        },
        "summary": {
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / iterations, 4),
            "median_total_ms": round(statistics.median(durations), 3),
            "p95_total_ms": round(_percentile(durations, 0.95), 3),
            "max_total_ms": round(max(durations), 3),
        },
        "runs": runs,
        "defects": defects,
        "known_observations": _known_observations(freeze),
        "recovery_steps": RECOVERY_STEPS,
        "browser_soak": {
            "status": "pending-preview",
            "required_rounds": 10,
            "required_console_errors": 0,
            "required_console_warnings": 0,
        },
    }
    if any(defect["classification"] not in DEFECT_CLASSES for defect in defects):
        raise ValueError("soak produced an unsupported defect classification")
    if output:
        dump_json(report, output)
    return report

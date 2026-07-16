from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .baselines import SYSTEMS
from .external import ExternalBaseline, load_external_config
from .io import dump_json, iter_jsonl
from .paths import distribution_root
from .specification import Specification


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_fingerprint(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _dataset_component_paths(root: Path, ground_truth_path: Path) -> list[Path]:
    ground_truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    paths: list[Path] = []
    for relative_dataset in ground_truth.get("datasets", {}):
        dataset = root / relative_dataset
        if dataset.suffix.lower() == ".shp":
            paths.extend(
                candidate
                for candidate in sorted(dataset.parent.glob(f"{dataset.stem}.*"))
                if candidate.is_file()
            )
        elif dataset.is_file():
            paths.append(dataset)
    return sorted(set(paths))


def _source_revision(root: Path) -> str | None:
    try:
        process = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return process.stdout.strip() if process.returncode == 0 else None


def score_task(expected: Any, actual: Any) -> float:
    value = actual.get("value") if isinstance(actual, dict) and "value" in actual else actual
    return 1.0 if _canonical(expected) == _canonical(value) else 0.0


def provenance_score(task: dict[str, Any], actual: Any, specification: Specification) -> float:
    if task["category"] not in {"knowledge", "evidence_retrieval", "validation", "version_compare"}:
        return float("nan")
    if task["category"] == "validation" and not task["expected"]:
        return float("nan")
    if not isinstance(actual, dict) or not actual.get("evidence"):
        return 0.0
    evidence_items = actual["evidence"]
    return sum(
        bool(all(item.get(key) for key in ("document", "version", "section", "page", "uri")))
        for item in evidence_items
    ) / len(evidence_items)


def run_benchmark(
    root: str | Path,
    systems: list[str] | None = None,
    external_systems: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    manifest = json.loads((root / "benchmark/manifest.json").read_text(encoding="utf-8"))
    manifest_path = root / "benchmark/manifest.json"
    specification_path = root / manifest["specification"]
    ground_truth_path = root / manifest["ground_truth"]
    task_paths = [root / path for path in manifest["task_files"]]
    dataset_paths = _dataset_component_paths(root, ground_truth_path)
    specification = Specification.load(specification_path)
    tasks = []
    for path in task_paths:
        tasks.extend(iter_jsonl(path))
    selected = systems if systems is not None else list(SYSTEMS)
    unknown = set(selected) - set(SYSTEMS)
    if unknown:
        raise ValueError(f"Unknown systems: {', '.join(sorted(unknown))}")

    configured: list[tuple[str, Any, int, bool, dict[str, Any] | None]] = [
        (name, SYSTEMS[name](specification, root), 1, False, None) for name in selected
    ]
    for configuration in external_systems or []:
        external = ExternalBaseline(configuration, specification, root)
        if external.name in {name for name, *_ in configured}:
            raise ValueError(f"Duplicate system name: {external.name}")
        configured.append(
            (external.name, external, external.repetitions, True, external.audit_configuration())
        )
    if not configured:
        raise ValueError("Select at least one built-in or external system")

    results = []
    summaries: dict[str, dict[str, Any]] = {}
    for name, system, repetitions, is_external, audit_configuration in configured:
        by_category: dict[str, list[float]] = defaultdict(list)
        provenance: list[float] = []
        failures = 0
        latencies: list[float] = []
        for run_index in range(repetitions):
            for task in tasks:
                started = time.perf_counter()
                error = None
                try:
                    actual = system.run(task, run_index) if is_external else system.run(task)
                except RuntimeError as exc:
                    actual = None
                    error = str(exc)
                    failures += 1
                latency_ms = (time.perf_counter() - started) * 1000
                latencies.append(latency_ms)
                score = score_task(task["expected"], actual)
                evidence_score = provenance_score(task, actual, specification)
                by_category[task["category"]].append(score)
                if evidence_score == evidence_score:  # exclude NaN / not-applicable tasks
                    provenance.append(evidence_score)
                results.append(
                    {
                        "system": name,
                        "run_index": run_index,
                        "task_id": task["task_id"],
                        "category": task["category"],
                        "expected": task["expected"],
                        "actual": actual.get("value")
                        if isinstance(actual, dict) and "value" in actual
                        else actual,
                        "score": score,
                        "provenance_completeness": None
                        if evidence_score != evidence_score
                        else evidence_score,
                        "latency_ms": round(latency_ms, 3),
                        "error": error,
                        "adapter_metadata": actual.get("metadata")
                        if isinstance(actual, dict)
                        else None,
                    }
                )
        scores = [row["score"] for row in results if row["system"] == name]
        summaries[name] = {
            "unique_tasks": len(tasks),
            "executions": len(scores),
            "repetitions": repetitions,
            "accuracy": sum(scores) / len(scores),
            "provenance_completeness": sum(provenance) / len(provenance) if provenance else None,
            "adapter_failures": failures,
            "mean_latency_ms": sum(latencies) / len(latencies),
            "external_adapter": is_external,
            "configuration": audit_configuration,
            "by_category": {
                key: sum(values) / len(values) for key, values in sorted(by_category.items())
            },
        }
    return {
        "benchmark": manifest["benchmark"],
        "version": manifest["version"],
        "generated_at": datetime.now(UTC).isoformat(),
        "task_count": len(tasks),
        "fixture_kind": manifest["fixture_kind"],
        "input_provenance": {
            "fingerprint_sha256": _input_fingerprint(
                root,
                [
                    manifest_path,
                    specification_path,
                    ground_truth_path,
                    *task_paths,
                    *dataset_paths,
                ],
            ),
            "manifest_sha256": _file_sha256(manifest_path),
            "specification_sha256": _file_sha256(specification_path),
            "ground_truth_sha256": _file_sha256(ground_truth_path),
            "dataset_files_sha256": {
                str(path.relative_to(root)): _file_sha256(path) for path in dataset_paths
            },
            "source_revision": _source_revision(root),
        },
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "executable": sys.executable,
        },
        "systems": summaries,
        "results": results,
        "disclosure": (
            "ungrounded_proxy is an offline control and must not be reported as a measured LLM "
            "baseline; external adapters must record exact model/server versions"
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nma-bench", description="Run NMA-Bench v0.1")
    parser.add_argument("--root", default=str(distribution_root()))
    parser.add_argument("--systems", default=",".join(SYSTEMS))
    parser.add_argument("--output", default="artifacts/benchmark/results.json")
    parser.add_argument(
        "--external-config",
        help="JSON config for named model/RAG adapters using nma-bench-adapter/1.0",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    external = load_external_config(args.external_config) if args.external_config else None
    report = run_benchmark(
        args.root,
        [item.strip() for item in args.systems.split(",") if item.strip()],
        external,
    )
    output = Path(args.output)
    dump_json(report, output)
    print(f"NMA-Bench {report['version']} — {report['task_count']} tasks")
    for name, summary in report["systems"].items():
        provenance = summary["provenance_completeness"]
        provenance_text = "n/a" if provenance is None else f"{provenance:.3f}"
        print(
            f"{name:28} accuracy={summary['accuracy']:.3f} "
            f"provenance={provenance_text} runs={summary['repetitions']} "
            f"failures={summary['adapter_failures']}"
        )
    print(f"Results: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

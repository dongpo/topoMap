from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .knowledge import PortrayalGraph
from .paths import distribution_root
from .portrayal import PortrayalAgent, compile_maplibre_layers


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


class UngroundedControl:
    name = "ungrounded_control"

    def run(self, task: dict[str, Any]) -> Any:
        return None


class PDFSearch:
    name = "pdf_search"

    def __init__(self, records: list[dict[str, Any]]):
        self.records = records

    def run(self, task: dict[str, Any]) -> Any:
        if task["type"] != "human_question":
            return None
        question = task["question"].casefold()
        matches = []
        for record in self.records:
            name = record["feature_name"]
            code = record["feature_code"]
            matched = name in question or code in question
            matched = matched or any(part in question for part in name.replace("、", " ").split())
            matched = matched or ("學校" in question and code.startswith("99201"))
            if matched:
                matches.append(record)
        if not matches:
            return {
                "status": "abstain",
                "answer": "No matching PDF text chunk.",
                "feature_codes": [],
                "evidence": [],
                "graph_paths": [],
            }
        if "頁" in question or "page" in question:
            answer = "；".join(
                f"{record['feature_name']}: page {record['page']}" for record in matches
            )
        elif any(term in question for term in ("大型", "獨幢", "例外", "exception")):
            answer = "；".join(record["instruction"] for record in matches)
        else:
            answer = "；".join(
                f"{record['feature_name']}: {record['feature_code']}" for record in matches
            )
        return {
            "status": "answered",
            "answer": answer,
            "feature_codes": [record["feature_code"] for record in matches],
            "evidence": [
                {
                    "document": record["document"],
                    "version": record["version"],
                    "page": record["page"],
                    "text": record["source_text"],
                    "uri": record["source_uri"],
                }
                for record in matches
            ],
            "graph_paths": [],
        }


class GraphRAGSystem:
    name = "graph_rag"

    def __init__(self, graph: PortrayalGraph):
        self.agent = PortrayalAgent(graph)

    def run(self, task: dict[str, Any]) -> Any:
        if task["type"] == "human_question":
            return self.agent.answer(task["question"])
        if task["type"] == "symbol_decision":
            return self.agent.select_symbol(
                task["feature_code"],
                scale_denominator=task.get("scale_denominator", 1000),
                profile_id=task.get("profile_id"),
                attributes=task.get("attributes"),
            ).as_dict()
        return None


class FullNMA(GraphRAGSystem):
    name = "full_nma"

    def __init__(self, graph: PortrayalGraph):
        super().__init__(graph)
        self.layers = compile_maplibre_layers(graph)

    def run(self, task: dict[str, Any]) -> Any:
        if task["type"] != "map_compilation":
            return super().run(task)
        candidates = [
            layer
            for layer in self.layers
            if layer.get("source-layer") == task["source_layer"]
            and layer.get("metadata", {}).get("nma:featureCode") == task["feature_code"]
            and layer.get("metadata", {}).get("nma:role") != "label"
        ]
        if not candidates:
            return {"compiled": False}
        metadata = candidates[0]["metadata"]
        return {
            "compiled": True,
            "feature_code": metadata["nma:featureCode"],
            "source_layer": candidates[0]["source-layer"],
            "rule_id": metadata["nma:ruleId"],
            "page": metadata["nma:evidence"]["page"],
            "graph_path": metadata["nma:graphPath"],
        }


def _score(expected: dict[str, Any], actual: Any, task_type: str) -> float:
    if not isinstance(actual, dict):
        return 0.0
    if task_type == "human_question":
        return float(
            actual.get("status") == expected["status"]
            and sorted(actual.get("feature_codes", [])) == sorted(expected["feature_codes"])
            and all(
                fragment in actual.get("answer", "") for fragment in expected["answer_contains"]
            )
        )
    if task_type == "symbol_decision":
        if actual.get("status") != expected["status"]:
            return 0.0
        if expected["status"] != "selected":
            return float(actual.get("feature_code") == expected["feature_code"])
        symbol = actual.get("symbol") or {}
        evidence = actual.get("evidence") or {}
        return float(
            actual.get("feature_code") == expected["feature_code"]
            and actual.get("feature_name") == expected["feature_name"]
            and symbol.get("symbol_id") == expected["symbol_id"]
            and symbol.get("selected_action") == expected["selected_action"]
            and evidence.get("page") == expected["page"]
        )
    return float(all(actual.get(key) == value for key, value in expected.items()))


def _evidence_score(expected: dict[str, Any], actual: Any, task_type: str) -> float | None:
    if not isinstance(actual, dict):
        return 0.0
    if task_type == "human_question":
        if expected["status"] == "abstain":
            return None
        pages = [item.get("page") for item in actual.get("evidence", [])]
        return float(pages == expected["pages"])
    if task_type == "symbol_decision":
        if expected["status"] != "selected":
            return None
        return float((actual.get("evidence") or {}).get("page") == expected["page"])
    return float(actual.get("page") == expected["page"])


def _graph_score(expected: dict[str, Any], actual: Any, task_type: str) -> float | None:
    if not isinstance(actual, dict):
        return 0.0
    if task_type == "human_question":
        if expected["status"] == "abstain":
            return None
        paths = actual.get("graph_paths", [])
    else:
        if task_type == "symbol_decision" and expected["status"] != "selected":
            return None
        path = actual.get("graph_path")
        paths = [path] if path else []
    if not paths:
        return 0.0
    required = {"PORTRAYED_BY", "USES_SYMBOL", "SUPPORTED_BY", "EVIDENCED_ON"}
    return float(
        all(required <= {edge["type"] for edge in path.get("edges", [])} for path in paths)
    )


def _fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run_portrayal_benchmark(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    manifest_path = root / "benchmark/portrayal/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tasks_path = root / manifest["tasks"]
    truth_path = root / manifest["ground_truth"]
    graph_path = root / manifest["graph"]
    records_path = root / manifest["records"]
    tasks = _read_jsonl(tasks_path)
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    graph = PortrayalGraph.load(graph_path)
    systems = [
        UngroundedControl(),
        PDFSearch(_read_jsonl(records_path)),
        GraphRAGSystem(graph),
        FullNMA(graph),
    ]
    rows = []
    summaries: dict[str, Any] = {}
    for system in systems:
        category_scores: dict[str, list[float]] = defaultdict(list)
        evidence_scores: list[float] = []
        graph_scores: list[float] = []
        latencies: list[float] = []
        for task in tasks:
            # The expected answer is never included in the system request.
            started = time.perf_counter()
            actual = system.run(dict(task))
            latency_ms = (time.perf_counter() - started) * 1000
            expected = truth[task["task_id"]]
            score = _score(expected, actual, task["type"])
            evidence = _evidence_score(expected, actual, task["type"])
            graph_grounding = _graph_score(expected, actual, task["type"])
            category_scores[task["type"]].append(score)
            if evidence is not None:
                evidence_scores.append(evidence)
            if graph_grounding is not None:
                graph_scores.append(graph_grounding)
            latencies.append(latency_ms)
            rows.append(
                {
                    "system": system.name,
                    "task_id": task["task_id"],
                    "type": task["type"],
                    "score": score,
                    "evidence_score": evidence,
                    "graph_grounding_score": graph_grounding,
                    "latency_ms": round(latency_ms, 3),
                    "actual": actual,
                }
            )
        all_scores = [score for values in category_scores.values() for score in values]
        summaries[system.name] = {
            "accuracy": sum(all_scores) / len(all_scores),
            "evidence_accuracy": sum(evidence_scores) / len(evidence_scores),
            "graph_grounding": sum(graph_scores) / len(graph_scores),
            "mean_latency_ms": sum(latencies) / len(latencies),
            "by_task_type": {
                category: sum(values) / len(values)
                for category, values in sorted(category_scores.items())
            },
        }
    return {
        "benchmark": manifest["benchmark"],
        "version": manifest["version"],
        "generated_at": datetime.now(UTC).isoformat(),
        "task_count": len(tasks),
        "systems": summaries,
        "results": rows,
        "input_fingerprint_sha256": _fingerprint(
            [manifest_path, tasks_path, truth_path, graph_path, records_path]
        ),
        "runtime": {"python": platform.python_version(), "executable": sys.executable},
        "claim_boundary": manifest["claim_boundary"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nma-bench", description="Human-question and portrayal benchmark for NMA"
    )
    parser.add_argument("--root", default=str(distribution_root()))
    parser.add_argument("--output", default="artifacts/benchmark/portrayal-results.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = run_portrayal_benchmark(args.root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"NMA-Bench {report['version']} — {report['task_count']} tasks")
    for name, summary in report["systems"].items():
        print(
            f"{name:20} accuracy={summary['accuracy']:.3f} "
            f"evidence={summary['evidence_accuracy']:.3f} "
            f"graph={summary['graph_grounding']:.3f}"
        )
    print(f"Results: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

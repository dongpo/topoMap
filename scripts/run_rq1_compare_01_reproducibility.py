from __future__ import annotations

import argparse
import json
from pathlib import Path

from nma.llm import adapter_from_environment
from nma.rq1_compare import RQ1ComparisonRunner


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--results", default="rq1-compare-01-results.json")
    arguments = parser.parse_args()
    root = Path(arguments.repository_root).resolve()
    output = Path(arguments.results)
    if not output.is_absolute():
        output = root / output
    results = json.loads(output.read_text(encoding="utf-8"))
    runner = RQ1ComparisonRunner(repository_root=root, adapter=adapter_from_environment())

    def record_progress(run: dict, count: int) -> None:
        print(
            f"Completed reproducibility {count}/9: {run['architecture']} {run['phase']} "
            f"accuracy={run['evaluation']['requirement_accuracy']:.3f}",
            flush=True,
        )

    runs, summary = runner.run_reproducibility(
        evidence_budget=int(results["normalization"]["canonical_graphrag_evidence_tokens"]),
        repeats=3,
        on_run=record_progress,
    )
    results["reproducibility_runs"] = runs
    results["reproducibility"] = summary
    output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Added {len(runs)} canonical reproducibility runs to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nma.llm import adapter_from_environment
from nma.rq1_compare import RQ1ComparisonRunner


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--output", default="rq1-compare-01-results.json")
    arguments = parser.parse_args()
    root = Path(arguments.repository_root).resolve()
    output = Path(arguments.output)
    if not output.is_absolute():
        output = root / output
    runner = RQ1ComparisonRunner(repository_root=root, adapter=adapter_from_environment())
    checkpoint = Path("/private/tmp/rq1-compare-01-primary-checkpoint.jsonl")
    checkpoint.write_text("", encoding="utf-8")

    def record_progress(run: dict, count: int) -> None:
        with checkpoint.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(run, ensure_ascii=False, sort_keys=True) + "\n")
        print(
            f"Completed {count}/33: {run['architecture']} {run['question_id']} "
            f"accuracy={run['evaluation']['requirement_accuracy']:.3f}",
            flush=True,
        )

    results = runner.run_primary(on_run=record_progress)
    output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(results['raw_runs'])} controlled runs to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

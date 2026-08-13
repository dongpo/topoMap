#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nma.neo4j_retrieval_v028 import (  # noqa: E402
    evaluate_live_retrieval_parity_v028,
    open_neo4j_driver,
)


NEO4J_ENV_KEYS = {
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "NEO4J_DATABASE",
}


def load_local_neo4j_settings(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or key not in NEO4J_ENV_KEYS or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


def main() -> int:
    load_local_neo4j_settings(ROOT / ".env.local")
    parser = argparse.ArgumentParser(
        description="Verify live Neo4j versus canonical GraphRAG evidence-package parity."
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=ROOT / "data/specifications/nma-neo4j-retrieval-parity-v0.28.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data/runtime/neo4j/nma-neo4j-retrieval-parity-v0.28.json",
    )
    parser.add_argument("--database", default=os.environ.get("NEO4J_DATABASE", "neo4j"))
    args = parser.parse_args()
    specification = json.loads(args.spec.read_text(encoding="utf-8"))
    graph_path = ROOT / specification["canonical_graph"]
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    required = {
        "NEO4J_URI": os.environ.get("NEO4J_URI"),
        "NEO4J_USER": os.environ.get("NEO4J_USER"),
        "NEO4J_PASSWORD": os.environ.get("NEO4J_PASSWORD"),
    }
    missing = sorted(key for key, value in required.items() if not value)
    if missing:
        raise RuntimeError(f"Missing local Neo4j settings: {', '.join(missing)}")
    driver = open_neo4j_driver(
        required["NEO4J_URI"], required["NEO4J_USER"], required["NEO4J_PASSWORD"]
    )
    try:
        report = evaluate_live_retrieval_parity_v028(
            driver,
            graph,
            specification,
            canonical_graph_path=graph_path,
            database=args.database,
        )
    finally:
        driver.close()
    expected = specification["expected"]
    for key, value in expected.items():
        if report.get(key) != value:
            raise RuntimeError(
                f"Prospective expectation failed for {key}: {report.get(key)!r} != {value!r}"
            )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.out), "status": report["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

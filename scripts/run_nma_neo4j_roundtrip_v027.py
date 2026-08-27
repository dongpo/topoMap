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

from nma.neo4j_roundtrip_v027 import (  # noqa: E402
    Neo4jRoundTripError,
    build_offline_round_trip_preflight_v027,
    import_and_verify_neo4j_v027,
    open_neo4j_driver,
)


NEO4J_ENV_KEYS = {
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "NEO4J_DATABASE",
}


def load_local_neo4j_settings(path: Path) -> None:
    """Load only Neo4j settings from an ignored local file without executing it."""
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
        description="Build the v0.27 Neo4j preflight or run an explicitly approved live round trip."
    )
    parser.add_argument(
        "--graph",
        type=Path,
        default=ROOT / "data/knowledge/nma-canonical-graph-v0.4.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data/runtime/neo4j/nma-neo4j-round-trip-v0.27.json",
    )
    parser.add_argument("--database", default=os.environ.get("NEO4J_DATABASE", "neo4j"))
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--allow-write",
        action="store_true",
        help="Required with --live. Imports by MERGE and never deletes existing data.",
    )
    args = parser.parse_args()
    graph = json.loads(args.graph.read_text(encoding="utf-8"))
    if not args.live:
        report = build_offline_round_trip_preflight_v027(
            graph, graph_path=args.graph, batch_size=args.batch_size
        )
    else:
        if not args.allow_write:
            raise Neo4jRoundTripError("Live import requires the explicit --allow-write gate.")
        required = {
            "NEO4J_URI": os.environ.get("NEO4J_URI"),
            "NEO4J_USER": os.environ.get("NEO4J_USER"),
            "NEO4J_PASSWORD": os.environ.get("NEO4J_PASSWORD"),
        }
        missing = sorted(key for key, value in required.items() if not value)
        if missing:
            raise Neo4jRoundTripError(
                f"Live import is missing environment settings: {', '.join(missing)}"
            )
        driver = open_neo4j_driver(
            required["NEO4J_URI"], required["NEO4J_USER"], required["NEO4J_PASSWORD"]
        )
        try:
            report = import_and_verify_neo4j_v027(
                driver,
                graph,
                graph_path=args.graph,
                database=args.database,
                batch_size=args.batch_size,
            )
        finally:
            driver.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.out), "status": report["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

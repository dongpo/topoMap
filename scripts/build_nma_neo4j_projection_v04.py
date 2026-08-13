#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nma.neo4j_projection import build_projection_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the reproducible Neo4j projection contract.")
    parser.add_argument(
        "--graph",
        type=Path,
        default=ROOT / "data/knowledge/nma-canonical-graph-v0.4.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data/runtime/neo4j/nma-neo4j-projection-v0.4.json",
    )
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    graph = json.loads(args.graph.read_text(encoding="utf-8"))
    source_label = args.graph.resolve().relative_to(ROOT).as_posix()
    manifest = build_projection_manifest(
        graph, graph_path=args.graph, batch_size=args.batch_size
    )
    manifest["canonical_source"] = source_label
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Prepared {manifest['statistics']['nodes']} nodes and "
        f"{manifest['statistics']['edges']} relationships for a rebuildable Neo4j projection."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

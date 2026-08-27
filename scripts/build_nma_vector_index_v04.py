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

from nma.vector_index import (  # noqa: E402
    DEFAULT_DIMENSIONS,
    DEFAULT_EMBEDDING_MODEL,
    OpenAIEmbeddingClient,
    VectorIndexError,
    build_vector_index,
)


def load_api_key() -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    for path in (ROOT / ".env.local", ROOT / ".env"):
        if not path.is_file():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            name, separator, value = raw_line.partition("=")
            if separator and name.strip() == "OPENAI_API_KEY" and value.strip():
                return value.strip().strip('"').strip("'")
    raise VectorIndexError("No usable OPENAI_API_KEY was found.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the NMA OpenAI semantic vector index.")
    parser.add_argument(
        "--graph",
        type=Path,
        default=ROOT / "data/knowledge/nma-canonical-graph-v0.4.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data/runtime/vector/nma-vector-index-v0.4.json",
    )
    parser.add_argument("--model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--dimensions", type=int, default=DEFAULT_DIMENSIONS)
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()
    graph = json.loads(args.graph.read_text(encoding="utf-8"))
    client = OpenAIEmbeddingClient(load_api_key())
    index = build_vector_index(
        graph,
        graph_path=args.graph,
        embed_batch=client.embed_batch,
        model=args.model,
        dimensions=args.dimensions,
        batch_size=args.batch_size,
    )
    index["canonical_source"] = args.graph.resolve().relative_to(ROOT).as_posix()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(index, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Built {index['statistics']['records']} semantic vectors at "
        f"{index['embedding']['dimensions']} dimensions; "
        f"input tokens recorded: {index['usage']['total_tokens']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

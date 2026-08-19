#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nma.core import canonical_sha256 as canonical_sha256  # noqa: E402


def load_server():
    path = ROOT / "scripts/run_nma_agent_server.py"
    spec = importlib.util.spec_from_file_location("nma_agent_server_v029_live", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the NMA Agent server module.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify v0.29 Agent runtime graph-backend wiring without LLM calls."
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=ROOT / "data/specifications/nma-runtime-graph-backend-v0.29.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data/runtime/neo4j/nma-runtime-graph-backend-v0.29.json",
    )
    args = parser.parse_args()
    specification = json.loads(args.spec.read_text(encoding="utf-8"))
    server = load_server()
    server._RETRIEVER = None
    server._GRAPH_BACKEND_TRACE = None
    retriever = server.canonical_retriever()
    backend = server.graph_backend_trace()
    cases = []
    for case in specification["cases"]:
        package = retriever.package_from_seed_ids(
            case["query"],
            case["seed_ids"],
            ranked_trace=[
                {
                    "id": node_id,
                    "type": retriever.nodes[node_id]["type"],
                    "score": 1,
                    "matched_terms": [case["query"]],
                    "match_mode": "v0.29-fixed-runtime-wiring-seed",
                }
                for node_id in case["seed_ids"]
            ],
            retrieval_mode="v0.29-agent-typed-retrieve-evidence",
            max_depth=case["max_depth"],
            max_nodes=case["max_nodes"],
        )
        package = server.attach_graph_backend_trace_v029(package)
        passed = (
            package["status"] == case["expected_status"]
            and len(package["citations"]) >= case["minimum_citations"]
            and package["retrieval_trace"]["v029_graph_backend"] == backend
            and package["automatic_rule_activation"] is False
        )
        if not passed:
            raise RuntimeError(f"Runtime wiring case failed: {case['id']}")
        cases.append(
            {
                "id": case["id"],
                "geometry": case["geometry"],
                "status": package["status"],
                "evidence_nodes": len(package["evidence_nodes"]),
                "graph_edges": len(package["graph_paths"]["edges"]),
                "citations": len(package["citations"]),
                "conflicts": len(package["conflicts"]),
                "backend_trace_present": True,
                "package_sha256": canonical_sha256(package),
                "passed": True,
            }
        )
    report = {
        "schema": "nma.runtime-graph-backend/0.29",
        "status": "agent-runtime-live-neo4j-backend-wiring-verified",
        **backend,
        "case_count": len(cases),
        "cases_passed": sum(item["passed"] for item in cases),
        "geometry_coverage": sorted({item["geometry"] for item in cases if item["geometry"]}),
        "cases": cases,
        "new_llm_calls": 0,
        "new_tokens": 0,
        "automatic_rule_activation": False,
        "map_mutations": 0,
        "claim_boundary": specification["claim_boundary"],
    }
    for key, value in specification["expected"].items():
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

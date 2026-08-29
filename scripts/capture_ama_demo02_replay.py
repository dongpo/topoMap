#!/usr/bin/env python3
"""Capture one fresh verified AMA cloud run as an explicitly labelled replay package."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from nma.ama_demo import (
    build_domain_graph,
    build_evidence_action_trace,
    build_retrieved_subgraph,
    build_rq1_comparison,
)
from nma.ama_live import CANONICAL_INTENT


def request_json(
    endpoint: str, path: str, *, method: str = "GET", body: object | None = None
) -> tuple[int, dict[str, Any]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data is not None else {}
    request = Request(endpoint.rstrip("/") + path, data=data, method=method, headers=headers)
    try:
        with urlopen(request, timeout=120) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read() or b"{}")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--endpoint",
        default="https://ama-cloud-01-555420096938.asia-southeast1.run.app",
    )
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--timeout", type=float, default=900)
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()
    replay = root / "artifacts/ama-demo/replay/canonical-run"

    health_status, health = request_json(args.endpoint, "/health")
    if health_status != 200 or health.get("status") != "PASS":
        raise RuntimeError(f"cloud health failed closed: HTTP {health_status} {health}")
    submitted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    status, record = request_json(
        args.endpoint,
        "/ama/run",
        method="POST",
        body={"intent": CANONICAL_INTENT},
    )
    if status != 202 or record.get("mode") != "LIVE":
        raise RuntimeError(f"live submission failed closed: HTTP {status} {record}")
    run_id = record["run_id"]
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        status, record = request_json(args.endpoint, f"/ama/run/{run_id}")
        if status != 200:
            raise RuntimeError(f"live polling failed: HTTP {status} {record}")
        if record.get("status") == "PASS":
            break
        if record.get("status") == "FAILED":
            raise RuntimeError(f"live run failed closed: {record.get('failure')}")
        time.sleep(2)
    else:
        raise TimeoutError(f"cloud run {run_id} exceeded {args.timeout} seconds")

    result_status, map_result = request_json(args.endpoint, f"/ama/run/{run_id}/result")
    tamper_status, tamper = request_json(
        args.endpoint, f"/ama/run/{run_id}/tamper-test", method="POST", body={}
    )
    if result_status != 200 or tamper_status != 200 or tamper.get("status") != "PASS":
        raise RuntimeError("result or tamper acceptance failed closed")
    proposal_hash = record["proposal"]["proposal_hash"]
    if not (
        proposal_hash
        == record["authorization"]["proposal_hash"]
        == record["provenance"]["executed_proposal_hash"]
        == map_result["features"][0]["properties"]["proposal_hash"]
    ):
        raise RuntimeError("proposal/authorization/execution/map identity mismatch")

    rq1 = build_rq1_comparison(root)
    domain = build_domain_graph(root)
    retrieved = build_retrieved_subgraph(record, mode="REPLAY")
    trace = build_evidence_action_trace(record, mode="REPLAY")
    files: dict[str, object] = {
        "user-intent.json": {
            "user_intent": record["intent"],
            "normalized_intent": record["intent"],
            "planner_input": record["intent"],
            "distinction_preserved": True,
        },
        "rq1-comparison.json": rq1,
        "graph-retrieval.json": record["retrieval"],
        "projected-evidence.json": record["evidence"],
        "constraints.json": {
            "constraint_resolution_id": record["constraint_resolution_id"],
            "constraints": record["constraints"],
        },
        "proposal.json": {
            "proposal": record["proposal"],
            "validation": record["proposal_validation"],
        },
        "authorization.json": {
            "authorization": record["authorization"],
            "gate": record["authorization_gate"],
        },
        "execution.json": record["execution"],
        "verification.json": record["verification"],
        "provenance.json": record["provenance"],
        "map-result.geojson": map_result,
        "tamper-test.json": tamper,
        "run.json": record,
        "domain-kg.json": domain,
        "retrieved-subgraph.json": retrieved,
        "evidence-action-trace.json": trace,
    }
    for name, value in files.items():
        write_json(replay / name, value)
    completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    manifest = {
        "schema": "nma.ama-demo-02-replay-manifest/1.0",
        "replay_id": "ama-demo-02-replay:" + hashlib.sha256(run_id.encode()).hexdigest()[:24],
        "mode": "REPLAY",
        "notice": "Previously verified cloud run; no new inference or execution.",
        "source_mode": "LIVE",
        "source_endpoint": args.endpoint,
        "source_run_id": run_id,
        "submitted_at": submitted_at,
        "captured_at": completed_at,
        "health": health,
        "proposal_hash": proposal_hash,
        "authorized_proposal_hash": record["authorization"]["proposal_hash"],
        "executed_proposal_hash": record["provenance"]["executed_proposal_hash"],
        "verification_status": record["verification"]["status"],
        "provenance_status": record["provenance"]["result"],
        "tamper_status": tamper["status"],
        "timing_ms": record["timing_ms"],
        "artifacts": {
            name: {"sha256": sha256_file(replay / name), "bytes": (replay / name).stat().st_size}
            for name in sorted(files)
        },
    }
    write_json(replay / "manifest.json", manifest)
    write_json(root / "artifacts/ama-demo/ama-demo-02-rq1-comparison.json", rq1)
    write_json(
        root / "artifacts/ama-demo/ama-demo-02-runtime-manifest.json",
        {
            "schema": "nma.ama-demo-02-runtime-manifest/1.0",
            "task": "AMA-DEMO-02",
            "predecessor": "0ebe7193951a8d4f5c5c6d10f3e5de4c71698284",
            "public_endpoint": args.endpoint,
            "live_run_id": run_id,
            "replay_id": manifest["replay_id"],
            "model": health["model"],
            "ollama_version": health["ollama_version"],
            "gpu_model_preloaded": health["gpu_model_preloaded"],
            "research_semantics": "UNCHANGED",
            "supported_modes": ["LIVE", "REPLAY"],
            "silent_live_to_replay_substitution": False,
            "timing_ms": record["timing_ms"],
        },
    )
    print(json.dumps({"run_id": run_id, "proposal_hash": proposal_hash, "replay": str(replay)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

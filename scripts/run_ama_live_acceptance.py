#!/usr/bin/env python3
"""Run one fresh AMA-LIVE-01 scenario and its backend tamper test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nma.ama_live import AMALiveService, CANONICAL_INTENT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--storage-root", default="artifacts/ama-live/runtime")
    parser.add_argument("--summary-path")
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()
    storage = Path(args.storage_root)
    if not storage.is_absolute():
        storage = root / storage
    service = AMALiveService(repository_root=root, storage_root=storage)
    waiting = service.new_record(CANONICAL_INTENT)
    result = service.run(waiting["run_id"])
    tamper = service.tamper_test(waiting["run_id"])
    summary = {
        "run_id": result["run_id"],
        "status": result["status"],
        "mode": result["mode"],
        "model_identity": result["plan"]["model_identity"],
        "retrieval_id": result["retrieval"]["retrieval_id"],
        "retrieved_nodes": result["retrieval"]["node_count"],
        "projected_nodes": result["evidence"]["projected_node_count"],
        "proposal_id": result["proposal"]["proposal_id"],
        "proposal_hash": result["proposal"]["proposal_hash"],
        "proposal_validation": result["proposal_validation"]["status"],
        "authorization": result["authorization_gate"]["status"],
        "authorized_proposal_hash": result["authorization"]["proposal_hash"],
        "executed_proposal_hash": result["provenance"]["executed_proposal_hash"],
        "execution_id": result["execution"]["execution_id"],
        "execution": result["execution"]["status"],
        "verification": result["verification"]["status"],
        "provenance_id": result["provenance"]["provenance_id"],
        "source_unchanged": (
            result["provenance"]["source_sha256_before"]
            == result["provenance"]["source_sha256_after"]
        ),
        "unresolved_constraint_ids": [
            item["constraint_id"]
            for item in result["constraints"]
            if item["status"] == "BOUNDED_UNRESOLVED"
        ],
        "tamper_test": tamper["status"],
        "timing_ms": result["timing_ms"],
        "record_path": str(storage / result["run_id"] / "run.json"),
    }
    if args.summary_path:
        path = Path(args.summary_path)
        if not path.is_absolute():
            path = root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" and tamper["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

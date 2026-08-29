#!/usr/bin/env python3
"""Execute fresh AMA-CLOUD-01 cold/warm acceptance against a public HTTPS endpoint."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from nma.ama_live import CANONICAL_INTENT


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    body: object | None = None,
    content_type: str = "application/json",
    timeout: float = 60.0,
) -> tuple[int, dict[str, Any], float, dict[str, str]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        method=method,
        headers={"Content-Type": content_type} if data is not None else {},
    )
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
            headers = {key.lower(): value for key, value in response.headers.items()}
    except HTTPError as error:
        raw = error.read()
        status = error.code
        headers = {key.lower(): value for key, value in error.headers.items()}
    elapsed_ms = round((time.monotonic() - started) * 1000, 3)
    payload = json.loads(raw or b"{}")
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} returned a non-object JSON payload")
    return status, payload, elapsed_ms, headers


def run_once(base_url: str, *, label: str, poll_seconds: float) -> dict[str, Any]:
    submitted_at = utc_now()
    status, submitted, submit_ms, _ = request_json(
        base_url,
        "/ama/run",
        method="POST",
        body={"intent": CANONICAL_INTENT},
    )
    if status != 202:
        raise RuntimeError(f"run submission failed with HTTP {status}: {submitted}")
    run_id = submitted["run_id"]
    deadline = time.monotonic() + 3600
    poll_requests = 0
    poll_overhead_ms = 0.0
    while time.monotonic() < deadline:
        status, record, overhead_ms, _ = request_json(base_url, f"/ama/run/{run_id}")
        poll_requests += 1
        poll_overhead_ms += overhead_ms
        if status != 200:
            raise RuntimeError(f"poll failed with HTTP {status}: {record}")
        if record.get("status") == "FAILED":
            raise RuntimeError(f"cloud AMA run failed: {record.get('failure')}")
        if record.get("status") == "PASS":
            break
        time.sleep(poll_seconds)
    else:
        raise TimeoutError(f"cloud AMA run {run_id} exceeded 3600 seconds")

    views: dict[str, Any] = {}
    view_overhead: dict[str, float] = {}
    for view in ("evidence", "proposal", "verification", "provenance", "result"):
        view_status, payload, elapsed_ms, _ = request_json(base_url, f"/ama/run/{run_id}/{view}")
        if view_status != 200:
            raise RuntimeError(f"{view} view failed with HTTP {view_status}: {payload}")
        views[view] = payload
        view_overhead[view] = elapsed_ms
    tamper_status, tamper, tamper_ms, _ = request_json(
        base_url,
        f"/ama/run/{run_id}/tamper-test",
        method="POST",
        body={},
    )
    if tamper_status != 200:
        raise RuntimeError(f"tamper test failed with HTTP {tamper_status}: {tamper}")

    proposal = record["proposal"]
    provenance = record["provenance"]
    result_feature = views["result"]["features"][0]
    checks = {
        "status_pass": record["status"] == "PASS",
        "live_mode": record["mode"] == "LIVE",
        "live_graphrag": record["retrieval"]["invocation"] == "nma.rq2_demo.retrieve_rq2_evidence",
        "live_planner": record["plan"]["model_trace"]["provider"] == "ollama",
        "model_digest_exact": record["plan"]["model_observed"]["digest"]
        == "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e",
        "constraints_pass": record["stages"]["constraint_resolution"]["status"] == "PASS",
        "proposal_new": proposal["proposal_hash"]
        not in {
            "116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1",
            "c2cdf20081b4c163e3951b6f873e8139a1a7ad6f1212d37501a23c900364e705",
        },
        "proposal_valid": record["proposal_validation"]["status"] == "PASS",
        "authorization_pass": record["authorization_gate"]["status"] == "PASS",
        "authorized_equals_executed": provenance["authorized_proposal_hash"]
        == provenance["executed_proposal_hash"]
        == proposal["proposal_hash"],
        "gis_pass": record["execution"]["status"] == "PASS",
        "verification_pass": record["verification"]["status"] == "PASS",
        "provenance_complete": all(
            provenance.get(key)
            for key in (
                "provenance_id",
                "retrieval_id",
                "plan_id",
                "proposal_hash",
                "authorization_id",
                "execution_id",
                "verification_id",
                "receipt_id",
            )
        ),
        "map_result_bound": result_feature["properties"]["proposal_hash"]
        == proposal["proposal_hash"],
        "tamper_fail_closed": tamper.get("status") == "PASS"
        and tamper.get("authorization") == "DENIED"
        and tamper.get("mutation_started") is False,
        "source_unchanged": provenance["source_sha256_before"] == provenance["source_sha256_after"],
    }
    if not all(checks.values()):
        raise RuntimeError(f"acceptance checks failed: {checks}")
    return {
        "label": label,
        "submitted_at": submitted_at,
        "completed_at": utc_now(),
        "run_id": run_id,
        "retrieval_id": record["retrieval"]["retrieval_id"],
        "projection_id": record["evidence"]["projection_id"],
        "plan_id": record["plan"]["plan_id"],
        "proposal_id": proposal["proposal_id"],
        "proposal_hash": proposal["proposal_hash"],
        "authorization_id": record["authorization"]["authorization_id"],
        "execution_id": record["execution"]["execution_id"],
        "verification_id": record["verification"]["verification_id"],
        "provenance_id": provenance["provenance_id"],
        "model": record["plan"]["model_observed"],
        "model_trace": record["plan"]["model_trace"],
        "provider_metrics": record["plan"].get("provider_metrics", {}),
        "timing_ms": record["timing_ms"],
        "api_overhead_ms": {
            "submission": submit_ms,
            "poll_total": round(poll_overhead_ms, 3),
            "poll_requests": poll_requests,
            "views": view_overhead,
            "tamper": tamper_ms,
        },
        "retrieved_node_count": record["retrieval"]["node_count"],
        "projected_node_count": record["evidence"]["projected_node_count"],
        "checks": checks,
    }


def triplet(values: list[float]) -> dict[str, float]:
    return {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("endpoint")
    parser.add_argument("--warm-runs", type=int, default=3, choices=range(3, 6))
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/ama-cloud/ama-cloud-01-acceptance-results.json"),
    )
    args = parser.parse_args()

    health_status, health, health_ms, health_headers = request_json(args.endpoint, "/health")
    if health_status != 200 or health.get("status") != "PASS":
        raise RuntimeError(f"health failed: HTTP {health_status}: {health}")
    config_status, config, config_ms, _ = request_json(args.endpoint, "/ama/config")
    root_request = Request(args.endpoint.rstrip("/") + "/")
    root_started = time.monotonic()
    with urlopen(root_request, timeout=60) as response:
        root_html = response.read().decode("utf-8")
        root_status = response.status
    root_ms = round((time.monotonic() - root_started) * 1000, 3)
    if config_status != 200 or config.get("deployment") != "LIVE CLOUD RUN":
        raise RuntimeError(f"cloud deployment label missing: {config}")
    if root_status != 200 or "deployment-label" not in root_html:
        raise RuntimeError("public frontend integration is unavailable")

    invalid_status, _, _, _ = request_json(
        args.endpoint,
        "/ama/run",
        method="POST",
        body={"intent": "unsupported intent must fail closed"},
    )
    media_status, _, _, _ = request_json(
        args.endpoint,
        "/ama/run",
        method="POST",
        body={"intent": CANONICAL_INTENT},
        content_type="text/plain",
    )
    if invalid_status != 400 or media_status != 415:
        raise RuntimeError(
            f"failed-request boundary did not fail closed: {invalid_status}, {media_status}"
        )

    cold = run_once(args.endpoint, label="cold", poll_seconds=args.poll_seconds)
    warm = [
        run_once(args.endpoint, label=f"warm-{index + 1}", poll_seconds=args.poll_seconds)
        for index in range(args.warm_runs)
    ]
    proposal_hashes = [cold["proposal_hash"], *(item["proposal_hash"] for item in warm)]
    if len(proposal_hashes) != len(set(proposal_hashes)):
        raise RuntimeError("fresh runs reused a proposal hash")
    planning = [item["timing_ms"]["llm_planning"] for item in warm]
    end_to_end = [item["timing_ms"]["end_to_end"] for item in warm]
    median_seconds = statistics.median(end_to_end) / 1000
    latency_class = (
        "GOOD FOR LIVE DEMO"
        if median_seconds <= 30
        else "USABLE"
        if median_seconds <= 60
        else "NEEDS PERFORMANCE WORK"
        if median_seconds <= 120
        else "BLOCKING FOR LIVE DEMO"
    )
    output = {
        "schema": "nma.ama-cloud-acceptance-results/1.0",
        "task": "AMA-CLOUD-01",
        "generated_at": utc_now(),
        "endpoint": args.endpoint.rstrip("/"),
        "health": {
            "status": "PASS",
            "latency_ms": health_ms,
            "payload": health,
            "security_headers": {
                key: health_headers.get(key)
                for key in (
                    "x-content-type-options",
                    "x-frame-options",
                    "referrer-policy",
                    "permissions-policy",
                )
            },
        },
        "frontend": {
            "status": "PASS",
            "root_latency_ms": root_ms,
            "config_latency_ms": config_ms,
            "deployment_label": config["deployment"],
        },
        "failed_request_handling": {
            "status": "PASS",
            "unsupported_intent_http": invalid_status,
            "unsupported_media_type_http": media_status,
            "mutation": "NONE",
        },
        "cold_run": cold,
        "warm_runs": warm,
        "warm_summary_ms": {
            "planning": triplet(planning),
            "end_to_end": triplet(end_to_end),
        },
        "fresh_proposal_hashes_unique": True,
        "latency_classification": latency_class,
        "verdict": "PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

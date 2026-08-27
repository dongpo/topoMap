from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from nma.llm import LLMAdapter, LLMResult, adapter_from_environment
from nma.llm.base import canonical_json
from nma.research_governance_adapter import (
    run_governed_school_scenario,
    unsafe_scenario_result,
)
from nma.research_runtime import AMAResearchRuntime


class _UnsafeFieldInjectionAdapter(LLMAdapter):
    """Scenario-B fault injection after a real provider response, before validation."""

    def __init__(self, delegate: LLMAdapter) -> None:
        self.delegate = delegate

    def generate_structured(
        self,
        *,
        task: str,
        instructions: str,
        context: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> LLMResult:
        result = self.delegate.generate_structured(
            task=task,
            instructions=instructions,
            context=context,
            output_schema=output_schema,
        )
        if task != "select-reviewed-bounded-mapping-plan":
            return result
        output = deepcopy(result.output)
        output["schema_constraints"]["feature_code_field"] = "INVENTED_FIELD"
        return LLMResult(
            model_id=result.model_id,
            provider=result.provider,
            output=output,
            latency_ms=result.latency_ms,
            usage=result.usage,
            raw_response_hash=hashlib.sha256(canonical_json(output)).hexdigest(),
        )


def _started_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _summary(result: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "schema": result["schema"],
        "provider": result.get("provider"),
        "model_id": result.get("model_id"),
        "graph_backend": result.get("graph_backend", {}).get("active_backend"),
        "request_identity": result.get("request_identity")
        or result.get("identity_links", {}).get("request"),
        "evidence_or_plan_identity": result.get("plan_id")
        or result.get("evidence_package_identity")
        or result.get("identity_links", {}).get("plan"),
        "governance_stage_result": result.get("status") or result.get("validation"),
    }
    if "identity_links" in result:
        summary["identity_links"] = result["identity_links"]
    if result.get("status") == "rejected":
        summary.update(
            {
                "stopping_stage": result["stopping_stage"],
                "failure_reason": result["failure_reason"],
                "execution_reached": result["execution_reached"],
            }
        )
    return summary


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(prog="ama-research-demo")
    command.add_argument("--repository-root", default=".")
    subcommands = command.add_subparsers(dest="rq", required=True)
    for name in ("rq1", "rq2"):
        item = subcommands.add_parser(name)
        item.add_argument("request")
    for name in ("rq3", "rq3-unsafe"):
        item = subcommands.add_parser(name)
        item.add_argument("request")
        item.add_argument("--storage-root", required=True)
        item.add_argument("--idempotency-key", required=True)
        item.add_argument("--reviewer", default="ama-demo02-domain-reviewer")
        item.add_argument(
            "--authorization",
            default=(
                "artifacts/runtime/school-hero/authorizations/"
                "authorization-school-demo-b4ecdbfc35ecaf73293ed497.json"
            ),
        )
    return command


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    root = Path(arguments.repository_root).resolve()
    adapter = adapter_from_environment()
    if arguments.rq == "rq3-unsafe":
        adapter = _UnsafeFieldInjectionAdapter(adapter)
    runtime = AMAResearchRuntime(repository_root=root, adapter=adapter)
    try:
        if arguments.rq == "rq1":
            result = runtime.run_rq1(arguments.request)
        elif arguments.rq == "rq2":
            result = runtime.propose_rq2(arguments.request)
        else:
            authorization = Path(arguments.authorization)
            if not authorization.is_absolute():
                authorization = root / authorization
            result = run_governed_school_scenario(
                runtime=runtime,
                request=arguments.request,
                authorization_path=authorization,
                storage_root=arguments.storage_root,
                domain_idempotency_key=arguments.idempotency_key,
                reviewer=arguments.reviewer,
                started_at=_started_at(),
            )
    except Exception as error:
        if arguments.rq != "rq3-unsafe":
            raise
        result = unsafe_scenario_result(error, storage_root=arguments.storage_root)
    print(json.dumps(_summary(result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") != "rejected" else 2


if __name__ == "__main__":
    sys.exit(main())

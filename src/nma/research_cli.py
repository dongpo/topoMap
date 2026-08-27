from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
from typing import Any

from nma.demo_reporting import (
    Elapsed,
    RQ1_REQUEST,
    RQ2_REQUEST,
    adapter_identity,
    build_rq1_artifact,
    build_rq2_artifact,
    build_rq3_artifact,
    create_run_directory,
    render_summary,
    utc_now,
    write_artifacts,
)
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
        self.provider: str | None = None
        self.model_id: str | None = None

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
        self.provider = result.provider
        self.model_id = result.model_id
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


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(prog="ama-research-demo")
    command.add_argument("--repository-root", default=".")
    command.add_argument("--output-root", default="artifacts/tmp/research-demo")
    subcommands = command.add_subparsers(dest="rq", required=True)
    rq1 = subcommands.add_parser("rq1", help="RQ1 knowledge-grounding demo")
    rq1.add_argument("request", nargs="?", default=RQ1_REQUEST)
    rq2 = subcommands.add_parser("rq2", help="RQ2 bounded-planning demo")
    rq2.add_argument("request", nargs="?", default=RQ2_REQUEST)
    rq3 = subcommands.add_parser("rq3", help="RQ3 governance and auditability demo")
    rq3.add_argument("request", nargs="?", default=RQ2_REQUEST)
    rq3.add_argument("--case", choices=("valid", "unsafe"), default="valid")
    rq3.add_argument("--storage-root")
    rq3.add_argument("--idempotency-key")
    rq3.add_argument("--reviewer", default="ama-demo03-domain-reviewer")
    rq3.add_argument(
        "--authorization",
        default=(
            "artifacts/runtime/school-hero/authorizations/"
            "authorization-school-demo-b4ecdbfc35ecaf73293ed497.json"
        ),
    )
    return command


def main(argv: list[str] | None = None) -> int:
    raw_arguments = list(sys.argv[1:] if argv is None else argv)
    if "rq3-unsafe" in raw_arguments:
        index = raw_arguments.index("rq3-unsafe")
        raw_arguments[index] = "rq3"
        if "--case" not in raw_arguments:
            raw_arguments.extend(("--case", "unsafe"))
    arguments = parser().parse_args(raw_arguments)
    root = Path(arguments.repository_root).resolve()
    output_root = Path(arguments.output_root)
    if not output_root.is_absolute():
        output_root = root / output_root
    started_at = utc_now()
    case = arguments.case if arguments.rq == "rq3" else None
    run_directory = create_run_directory(
        output_root, rq=arguments.rq, case=case, started_at=started_at
    )
    adapter = adapter_from_environment()
    if arguments.rq == "rq3" and arguments.case == "unsafe":
        adapter = _UnsafeFieldInjectionAdapter(adapter)
    runtime = AMAResearchRuntime(repository_root=root, adapter=adapter)
    elapsed = Elapsed()
    try:
        if arguments.rq == "rq1":
            result = runtime.run_rq1(arguments.request)
            artifact = build_rq1_artifact(
                result,
                request=arguments.request,
                started_at=started_at,
                total_ms=elapsed.milliseconds(),
            )
        elif arguments.rq == "rq2":
            result = runtime.propose_rq2(arguments.request)
            artifact = build_rq2_artifact(
                result,
                request=arguments.request,
                started_at=started_at,
                total_ms=elapsed.milliseconds(),
            )
        else:
            authorization = Path(arguments.authorization)
            if not authorization.is_absolute():
                authorization = root / authorization
            storage_root = (
                Path(arguments.storage_root)
                if arguments.storage_root
                else run_directory / "runtime"
            )
            idempotency_key = arguments.idempotency_key or (
                "ama-demo03-" + run_directory.name[-32:]
            )
            result = run_governed_school_scenario(
                runtime=runtime,
                request=arguments.request,
                authorization_path=authorization,
                storage_root=storage_root,
                domain_idempotency_key=idempotency_key,
                reviewer=arguments.reviewer,
                started_at=started_at,
            )
            artifact = build_rq3_artifact(
                result,
                request=arguments.request,
                case=arguments.case,
                started_at=started_at,
                total_ms=elapsed.milliseconds(),
                fallback_model=adapter_identity(adapter),
            )
    except Exception as error:
        if arguments.rq != "rq3" or arguments.case != "unsafe":
            print(f"AMA Research Demo failed closed: {error}", file=sys.stderr)
            return 2
        result = unsafe_scenario_result(error, storage_root=storage_root)
        artifact = build_rq3_artifact(
            result,
            request=arguments.request,
            case="unsafe",
            started_at=started_at,
            total_ms=elapsed.milliseconds(),
            fallback_model=adapter_identity(adapter),
            fallback_graph=runtime.graph_backend_trace,
        )
    summary_path, result_path = write_artifacts(run_directory, artifact)
    print(render_summary(artifact), end="")
    print(f"\nSummary artifact: {summary_path}")
    print(f"Machine artifact: {result_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

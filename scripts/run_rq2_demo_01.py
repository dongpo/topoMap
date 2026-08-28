#!/usr/bin/env python3
"""Execute the frozen paired RQ2-DEMO-01 experiment and persist its evidence."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import time
from typing import Any, Mapping

from nma.llm import OllamaAdapter
from nma.rq2_demo import (
    ALLOWLIST_VERSION,
    MANDATORY_POSTCONDITIONS,
    RQ2DemoError,
    RQ2Planner,
    artifact_identity,
    assemble_proposal,
    constraint_summary,
    evaluate_run,
    evidence_identities,
    execute_proposal,
    mutate_and_rehash,
    proposal_hash,
    resolve_constraints,
    retrieve_rq2_evidence,
    sha256_file,
    validate_proposal,
    validate_rq3_handoff,
    verify_execution,
    verify_model_identity,
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RQ2DemoError(f"Expected a JSON object: {path}")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _model_identity(protocol: Mapping[str, Any], observed: Mapping[str, Any]) -> str:
    model = protocol["model"]
    return (
        f"ollama:{model['name']}@sha256:{observed['digest']};"
        f"{model['parameters']};{model['quantization']};ctx={model['context_window']};"
        f"out={model['reserved_output_tokens']};temperature={model['temperature']}"
    )


def _run_record(
    *,
    architecture: str,
    protocol: Mapping[str, Any],
    model_observed: Mapping[str, Any],
    planner_output: Any,
    proposal: Mapping[str, Any],
    validation: Mapping[str, Any],
    execution: Mapping[str, Any],
    verification: Mapping[str, Any],
    evaluation: Mapping[str, Any],
    knowledge: Mapping[str, Any] | None,
    retrieval_latency_ms: int,
    total_latency_ms: int,
) -> dict[str, Any]:
    usage = planner_output.model_trace.get("usage") or {}
    budget = planner_output.model_trace.get("context_budget") or {}
    return {
        "schema": "nma.rq2-demo-01-run/1.0",
        "run_id": proposal["provenance_seed"]["run_identity"],
        "architecture": architecture,
        "intent_identity": proposal["intent"]["intent_id"],
        "model": {
            **dict(protocol["model"]),
            "observed": dict(model_observed),
            "identity": proposal["provenance_seed"]["model_identity"],
        },
        "knowledge": knowledge,
        "raw_planner_draft": planner_output.draft,
        "planner_trace": planner_output.model_trace,
        "proposal_id": proposal["proposal_id"],
        "proposal_hash": proposal["proposal_hash"],
        "proposal": proposal,
        "validator_result": validation,
        "execution_decision": proposal["decision"],
        "tool_calls": execution.get("tool_calls", []),
        "execution_result": execution,
        "verification_result": verification,
        "constraint_results": evaluation,
        "failure_taxonomy": list(
            dict.fromkeys(
                [
                    *validation.get("failure_taxonomy", []),
                    *execution.get("reason_codes", []),
                    *verification.get("failure_taxonomy", []),
                ]
            )
        ),
        "timing": {
            "retrieval_latency_ms": retrieval_latency_ms,
            "generation_latency_ms": planner_output.model_trace["latency_ms"],
            "planning_latency_ms": planner_output.model_trace["planning_latency_ms"],
            "execution_latency_ms": execution.get("execution_latency_ms", 0),
            "verification_latency_ms": verification.get("verification_latency_ms", 0),
            "total_latency_ms": total_latency_ms,
        },
        "tokens": {
            "prompt_tokens": usage.get("input_tokens"),
            "completion_tokens": usage.get("output_tokens"),
            "context_window": protocol["model"]["context_window"],
            "output_token_budget": protocol["model"]["reserved_output_tokens"],
            "remaining_context_margin": budget.get(
                "observed_input_margin", budget.get("remaining_input_margin")
            ),
        },
    }


def _remove_refs(value: Any, removed: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in list(value.items()):
            if key in {"constraint_refs", "constraint_ids"} and isinstance(item, list):
                value[key] = [ref for ref in item if ref not in removed]
            else:
                _remove_refs(item, removed)
    elif isinstance(value, list):
        for item in value:
            _remove_refs(item, removed)


def _negative_cases(
    root: Path,
    proposal: Mapping[str, Any],
    constraints: Mapping[str, Any],
    retrieval: Mapping[str, Any],
    fixture: Mapping[str, Any],
    runtime_root: Path,
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    def record(case_id: str, expected: str, validation: Mapping[str, Any], **extra: Any) -> None:
        cases.append(
            {
                "case": case_id,
                "expected": expected,
                "validator_status": validation["status"],
                "failure_taxonomy": validation["failure_taxonomy"],
                **extra,
            }
        )

    # A: contract fixture with no unresolved constraints; no ProductLayer value is invented.
    unresolved_ids = {item["constraint_id"] for item in proposal["constraints"]["unresolved"]}

    def make_case_a(value: dict[str, Any]) -> None:
        value["constraints"]["unresolved"] = []
        value["decision"] = {
            "execution_status": "PROCEED",
            "reason_codes": ["ALL_EXECUTION_CRITICAL_CONSTRAINTS_RESOLVED"],
        }
        _remove_refs(value, unresolved_ids)

    case_a = mutate_and_rehash(proposal, make_case_a)
    expected_a = case_a["constraints"]
    validation_a = validate_proposal(
        root,
        case_a,
        expected_constraints=expected_a,
        retrieval_package=retrieval,
        fixture=fixture,
    )
    execution_a = execute_proposal(
        root,
        case_a,
        validation_a,
        fixture_path=root / fixture["path"],
        output_root=runtime_root / "case-a",
        retrieval_package=retrieval,
    )
    verification_a = verify_execution(
        case_a,
        execution_a,
        fixture_path=root / fixture["path"],
        output_root=runtime_root / "case-a",
    )
    record(
        "A_VALID_CONSTRAINED",
        "PROCEED; execution PASS; verification PASS",
        validation_a,
        decision=case_a["decision"]["execution_status"],
        execution_status=execution_a["status"],
        verification_status=verification_a["status"],
    )

    # B: canonical bounded unresolved state.
    validation_b = validate_proposal(
        root,
        proposal,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=fixture,
    )
    record(
        "B_UNRESOLVED_PRODUCT_LAYER_PRESERVED",
        "PROCEED_WITH_BOUNDED_UNRESOLVED",
        validation_b,
        decision=proposal["decision"]["execution_status"],
        product_layer=proposal["expected_final_state"]["derived_artifact"]["semantic_values"][
            "product_layer"
        ],
    )

    # C: planner fabricates ProductLayer.
    case_c = mutate_and_rehash(
        proposal,
        lambda value: value["expected_final_state"]["derived_artifact"][
            "semantic_values"
        ].__setitem__("product_layer", "invented:hydrant-layer"),
    )
    validation_c = validate_proposal(
        root,
        case_c,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=fixture,
    )
    record(
        "C_FABRICATED_PRODUCT_LAYER",
        "REJECT / BLOCK",
        validation_c,
        execution_status="BLOCKED",
    )

    # D: required geometry constraint remains declared but is omitted from every plan reference.
    geometry_id = "constraint:geometry.type"

    def omit_geometry(value: dict[str, Any]) -> None:
        _remove_refs(value["plan"], {geometry_id})
        _remove_refs(value["expected_postconditions"], {geometry_id})

    case_d = mutate_and_rehash(proposal, omit_geometry)
    validation_d = validate_proposal(
        root,
        case_d,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=fixture,
    )
    record("D_REQUIRED_CONSTRAINT_OMITTED", "REJECT", validation_d, execution_status="BLOCKED")

    # E: exact unknown tool binding.
    def unknown_tool(value: dict[str, Any]) -> None:
        value["plan"][0]["tool"] = "rq2.unknown.command/1.0"

    case_e = mutate_and_rehash(proposal, unknown_tool)
    validation_e = validate_proposal(
        root,
        case_e,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=fixture,
    )
    record("E_UNKNOWN_TOOL", "BLOCK", validation_e, execution_status="BLOCKED")

    # F: critical geometry contradiction produces a valid BLOCK proposal with zero tool calls.
    geometry = next(
        item for item in proposal["constraints"]["resolved"] if item["constraint_id"] == geometry_id
    )
    contradictory = deepcopy(geometry)
    contradictory["expected_value"] = None
    contradictory["resolution_status"] = "contradicted"
    contradictory["source_evidence_refs"] = sorted(
        {
            *contradictory["source_evidence_refs"],
            "portrayal-rule:doc01:9350906",
            "portrayal-recipe:doc01:9350906:review-v1",
        }
    )

    def contradict_geometry(value: dict[str, Any]) -> None:
        value["constraints"]["resolved"] = [
            item
            for item in value["constraints"]["resolved"]
            if item["constraint_id"] != geometry_id
        ]
        value["constraints"]["contradicted"] = [contradictory]
        value["decision"] = {
            "execution_status": "BLOCK",
            "reason_codes": ["CONSTRAINT_CONTRADICTED"],
        }
        value["plan"] = []
        value["required_authorizations"] = []

    case_f = mutate_and_rehash(proposal, contradict_geometry)
    validation_f = validate_proposal(
        root,
        case_f,
        expected_constraints=case_f["constraints"],
        retrieval_package=retrieval,
        fixture=fixture,
    )
    execution_f = execute_proposal(
        root,
        case_f,
        validation_f,
        fixture_path=root / fixture["path"],
        output_root=runtime_root / "case-f",
        retrieval_package=retrieval,
    )
    record(
        "F_CONTRADICTED_CRITICAL_CONSTRAINT",
        "BLOCK",
        validation_f,
        decision=case_f["decision"]["execution_status"],
        execution_status=execution_f["status"],
        tool_call_count=len(execution_f["tool_calls"]),
    )

    # G: deterministic fault occurs after a valid gate; file creation alone is insufficient.
    validation_g = validate_proposal(
        root,
        proposal,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=fixture,
    )
    execution_g = execute_proposal(
        root,
        proposal,
        validation_g,
        fixture_path=root / fixture["path"],
        output_root=runtime_root / "case-g",
        retrieval_package=retrieval,
        fault="classification_mismatch",
    )
    verification_g = verify_execution(
        proposal,
        execution_g,
        fixture_path=root / fixture["path"],
        output_root=runtime_root / "case-g",
    )
    record(
        "G_POSTCONDITION_VIOLATION",
        "execution PASS; verification FAIL",
        validation_g,
        execution_status=execution_g["status"],
        verification_status=verification_g["status"],
        verification_failure_taxonomy=verification_g["failure_taxonomy"],
    )
    return cases


def _trace(constraints: Mapping[str, Any], proposal: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "constraint_id": item["constraint_id"],
            "resolution_status": item["resolution_status"],
            "execution_effect": item["execution_effect"],
            "evidence_refs": item["source_evidence_refs"],
            "plan_steps": [
                step["step_id"]
                for step in proposal["plan"]
                if item["constraint_id"] in step["constraint_refs"]
            ],
        }
        for item in constraint_summary(constraints)
    ]


def _comparison(baseline: Mapping[str, Any], constrained: Mapping[str, Any]) -> dict[str, Any]:
    bproposal = baseline["proposal"]
    cproposal = constrained["proposal"]
    beval = baseline["constraint_results"]
    ceval = constrained["constraint_results"]

    def yes(value: bool) -> str:
        return "PASS" if value else "FAIL"

    bchecks = beval["semantic_checks"]
    cchecks = ceval["semantic_checks"]
    rows = {
        "Classification correct": [yes(bchecks["classification"]), yes(cchecks["classification"])],
        "Geometry correct": [yes(bchecks["geometry"]), yes(cchecks["geometry"])],
        "Line style correct": [yes(bchecks["line_style"]), yes(cchecks["line_style"])],
        "Color correct": [yes(bchecks["color_code"]), yes(cchecks["color_code"])],
        "Source authority handling": [
            yes(bchecks["source_authority"]),
            yes(cchecks["source_authority"]),
        ],
        "ProductLayer unresolved preserved": [
            yes(bchecks["product_layer_unresolved"]),
            yes(cchecks["product_layer_unresolved"]),
        ],
        "Constraint coverage": [beval["constraint_coverage"], ceval["constraint_coverage"]],
        "Semantic plan validity": [
            beval["semantic_plan_validity"],
            ceval["semantic_plan_validity"],
        ],
        "Preconditions complete": [
            beval["preconditions_completeness"],
            ceval["preconditions_completeness"],
        ],
        "Postconditions complete": [
            beval["postconditions_completeness"],
            ceval["postconditions_completeness"],
        ],
        "Unknown/forbidden operations": [
            beval["unknown_or_forbidden_operations"],
            ceval["unknown_or_forbidden_operations"],
        ],
        "Executable": [beval["executability"], ceval["executability"]],
        "Execution successful": [beval["execution_success"], ceval["execution_success"]],
        "Constraint preservation": [
            beval["constraint_preservation_after_execution"],
            ceval["constraint_preservation_after_execution"],
        ],
        "Verification successful": [beval["verification_success"], ceval["verification_success"]],
    }
    baseline_tools = [item["tool"] for item in bproposal["plan"]]
    constrained_tools = [item["tool"] for item in cproposal["plan"]]
    return {
        "schema": "nma.rq2-demo-01-comparison/1.0",
        "independent_variable": "explicit knowledge-derived constraints",
        "controlled_variables": [
            "intent",
            "model and model identity",
            "temperature",
            "context/output budget",
            "proposal schema",
            "tool allowlist",
            "validator",
            "executor",
            "verifier",
        ],
        "primary_table": rows,
        "plan_diff": {
            "baseline_tools": baseline_tools,
            "constrained_tools": constrained_tools,
            "tools_added_by_constrained": [
                item for item in constrained_tools if item not in baseline_tools
            ],
            "tools_absent_from_constrained": [
                item for item in baseline_tools if item not in constrained_tools
            ],
            "baseline_semantic_values": bproposal["expected_final_state"]["derived_artifact"][
                "semantic_values"
            ],
            "constrained_semantic_values": cproposal["expected_final_state"]["derived_artifact"][
                "semantic_values"
            ],
            "baseline_constraint_refs": sorted(
                {ref for step in bproposal["plan"] for ref in step["constraint_refs"]}
            ),
            "constrained_constraint_refs": sorted(
                {ref for step in cproposal["plan"] for ref in step["constraint_refs"]}
            ),
        },
        "constraint_to_plan_trace": _trace(cproposal["constraints"], cproposal),
        "answers": {
            "what_changed": (
                "See plan_diff: semantic values, operation sequence, conditions, and explicit "
                "constraint references are preserved from the two first-pass model drafts."
            ),
            "baseline_absent_or_guessed": [
                key
                for key, passed in bchecks.items()
                if key != "product_layer_unresolved" and not passed
            ],
            "unsafe_or_unsupported_action_prevented": (
                "The constrained plan binds symbolic derivation to evidence and carries unresolved "
                "render/ProductLayer guards; the validator forbids rendering or guessed binding."
            ),
            "unresolved_preserved": cchecks["product_layer_unresolved"],
        },
    }


def run(root: Path, output_dir: Path, base_url: str) -> dict[str, Any]:
    protocol = _load(root / "data/evaluation/rq2-demo-01-protocol.json")
    fixture_path = root / protocol["fixture"]
    if sha256_file(fixture_path) != protocol["fixture_sha256"]:
        raise RQ2DemoError("The frozen fire-hydrant fixture identity changed.")
    allowed_existing = {
        "rq2-demo-01-attempt-01-failure.json",
        "rq2-demo-01-attempt-02-failure.json",
        "rq2-demo-01-attempt-03-failure.json",
        "attempt-03",
    }
    if output_dir.exists() and {path.name for path in output_dir.iterdir()} - allowed_existing:
        raise RQ2DemoError("The RQ2 primary output set already exists; refusing to overwrite it.")
    observed_model = verify_model_identity(base_url, protocol["model"])
    model_identity = _model_identity(protocol, observed_model)
    adapter = OllamaAdapter(
        base_url=base_url,
        model=protocol["model"]["name"],
        timeout_seconds=1200,
        context_window=protocol["model"]["context_window"],
        output_token_reserve=protocol["model"]["reserved_output_tokens"],
    )
    planner = RQ2Planner(adapter)
    allowlist_path = root / "data/specifications/rq2-tool-allowlist-v1.0.json"
    allowlist_sha = sha256_file(allowlist_path)
    fixture = {
        **artifact_identity(protocol["fixture"], protocol["fixture_sha256"]),
        "path": protocol["fixture"],
        "feature_selector": protocol["feature_selector"],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_root = output_dir / "runtime"

    # Freeze the baseline proposal before retrieval exists in this process.
    baseline_started = time.monotonic()
    baseline_planner = planner.compose(
        intent=protocol["canonical_intent"],
        fixture=fixture,
        architecture="llm-only",
        constraints=None,
    )
    baseline_proposal = assemble_proposal(
        architecture="llm-only",
        intent=protocol["canonical_intent"],
        draft=baseline_planner.draft,
        model_identity=model_identity,
        fixture=fixture,
        created_at=protocol["created_at"],
        allowlist_sha256=allowlist_sha,
    )
    baseline_validation = validate_proposal(
        root,
        baseline_proposal,
        expected_constraints=None,
        retrieval_package=None,
        fixture=fixture,
    )
    baseline_execution = execute_proposal(
        root,
        baseline_proposal,
        baseline_validation,
        fixture_path=fixture_path,
        output_root=runtime_root / "baseline",
        retrieval_package=None,
    )
    baseline_verification = verify_execution(
        baseline_proposal,
        baseline_execution,
        fixture_path=fixture_path,
        output_root=runtime_root / "baseline",
    )
    baseline_eval = evaluate_run(
        baseline_proposal,
        baseline_validation,
        baseline_execution,
        baseline_verification,
        protocol["sealed_truth"],
    )
    baseline_total = round((time.monotonic() - baseline_started) * 1000)
    baseline_record = _run_record(
        architecture="llm-only",
        protocol=protocol,
        model_observed=observed_model,
        planner_output=baseline_planner,
        proposal=baseline_proposal,
        validation=baseline_validation,
        execution=baseline_execution,
        verification=baseline_verification,
        evaluation=baseline_eval,
        knowledge=None,
        retrieval_latency_ms=0,
        total_latency_ms=baseline_total,
    )
    _write(output_dir / "rq2-demo-01-baseline-result.json", baseline_record)

    constrained_started = time.monotonic()
    retrieval_started = time.monotonic()
    retrieval = retrieve_rq2_evidence(root, protocol["canonical_intent"])
    retrieval_ms = round((time.monotonic() - retrieval_started) * 1000)
    identities = evidence_identities(root, retrieval)
    constraints = resolve_constraints(retrieval)
    evidence_refs = sorted(
        {ref for item in constraint_summary(constraints) for ref in item["source_evidence_refs"]}
    )
    constrained_planner = planner.compose(
        intent=protocol["canonical_intent"],
        fixture=fixture,
        architecture="knowledge-constrained",
        constraints=constraints,
    )
    constrained_proposal = assemble_proposal(
        architecture="knowledge-constrained",
        intent=protocol["canonical_intent"],
        draft=constrained_planner.draft,
        model_identity=model_identity,
        fixture=fixture,
        created_at=protocol["created_at"],
        allowlist_sha256=allowlist_sha,
        constraints=constraints,
        evidence_refs=evidence_refs,
        retrieval_identity=identities["retrieval_identity"],
        knowledge_snapshot_identity=identities["knowledge_snapshot_identity"],
    )
    constrained_validation = validate_proposal(
        root,
        constrained_proposal,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=fixture,
    )
    constrained_execution = execute_proposal(
        root,
        constrained_proposal,
        constrained_validation,
        fixture_path=fixture_path,
        output_root=runtime_root / "constrained",
        retrieval_package=retrieval,
    )
    constrained_verification = verify_execution(
        constrained_proposal,
        constrained_execution,
        fixture_path=fixture_path,
        output_root=runtime_root / "constrained",
    )
    constrained_eval = evaluate_run(
        constrained_proposal,
        constrained_validation,
        constrained_execution,
        constrained_verification,
        protocol["sealed_truth"],
    )
    constrained_total = round((time.monotonic() - constrained_started) * 1000)
    knowledge_record = {
        "retrieval_package": retrieval,
        "retrieval_identity": identities["retrieval_identity"],
        "knowledge_snapshot_identity": identities["knowledge_snapshot_identity"],
        "resolved_constraints": constraints["resolved"],
        "unresolved_constraints": constraints["unresolved"],
        "contradicted_constraints": constraints["contradicted"],
    }
    constrained_record = _run_record(
        architecture="knowledge-constrained",
        protocol=protocol,
        model_observed=observed_model,
        planner_output=constrained_planner,
        proposal=constrained_proposal,
        validation=constrained_validation,
        execution=constrained_execution,
        verification=constrained_verification,
        evaluation=constrained_eval,
        knowledge=knowledge_record,
        retrieval_latency_ms=retrieval_ms,
        total_latency_ms=constrained_total,
    )
    _write(output_dir / "rq2-demo-01-constrained-result.json", constrained_record)
    _write(output_dir / "rq2-demo-01-canonical-proposal.json", constrained_proposal)
    _write(output_dir / "rq2-demo-01-retrieval.json", retrieval)
    _write(output_dir / "rq2-demo-01-constraints.json", knowledge_record)

    comparison = _comparison(baseline_record, constrained_record)
    comparison["negative_cases"] = _negative_cases(
        root, constrained_proposal, constraints, retrieval, fixture, runtime_root
    )
    comparison["rq3_handoff"] = validate_rq3_handoff(root, constrained_proposal)
    comparison["proposal_hash_reload_stability"] = (
        proposal_hash(
            json.loads(json.dumps(constrained_proposal, ensure_ascii=False, sort_keys=True))
        )
        == constrained_proposal["proposal_hash"]
    )
    comparison["architectures"] = {
        "same_model_identity": (
            baseline_record["model"]["identity"] == constrained_record["model"]["identity"]
        ),
        "same_temperature": True,
        "same_proposal_version": (
            baseline_proposal["proposal_version"] == constrained_proposal["proposal_version"]
        ),
        "same_allowlist": (
            baseline_proposal["provenance_seed"]["tool_allowlist_sha256"]
            == constrained_proposal["provenance_seed"]["tool_allowlist_sha256"]
        ),
        "baseline_evidence_count": len(baseline_proposal["knowledge"]["evidence_refs"]),
        "constrained_evidence_count": len(constrained_proposal["knowledge"]["evidence_refs"]),
        "validator_model_calls": 0,
        "verifier_model_calls": 0,
        "post_hoc_repair": False,
    }
    _write(output_dir / "rq2-demo-01-comparison.json", comparison)
    summary = {
        "verdict": (
            "PASS — RQ2 KNOWLEDGE-CONSTRAINED EXECUTION DEMONSTRATED"
            if constrained_validation["status"] == "PASS"
            and constrained_execution["status"] == "PASS"
            and constrained_verification["status"] == "PASS"
            and comparison["rq3_handoff"]["status"] == "PASS"
            else "FAIL — RQ2 CONSTRAINED EXECUTION NOT DEMONSTRATED"
        ),
        "baseline": {
            "validator": baseline_validation["status"],
            "execution": baseline_execution["status"],
            "verification": baseline_verification["status"],
        },
        "constrained": {
            "validator": constrained_validation["status"],
            "execution": constrained_execution["status"],
            "verification": constrained_verification["status"],
        },
        "proposal_id": constrained_proposal["proposal_id"],
        "proposal_hash": constrained_proposal["proposal_hash"],
        "rq3_handoff": comparison["rq3_handoff"]["status"],
        "negative_cases": comparison["negative_cases"],
        "allowlist_version": ALLOWLIST_VERSION,
        "required_postcondition_count": len(MANDATORY_POSTCONDITIONS),
    }
    _write(output_dir / "rq2-demo-01-summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--output-dir", default="artifacts/rq2")
    parser.add_argument("--ollama-base-url", default="http://127.0.0.1:11434")
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()
    output = Path(args.output_dir)
    if not output.is_absolute():
        output = root / output
    summary = run(root, output, args.ollama_base_url)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

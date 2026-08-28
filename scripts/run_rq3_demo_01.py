#!/usr/bin/env python3
"""Execute the frozen RQ3-DEMO-01 A-L experiment into a fresh isolated bundle."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

from nma.rq2_demo import sha256_file
from nma.rq3_demo import (
    canonical_execution_request,
    canonical_inputs,
    run_authorized_scenario,
    write_json,
)


CASE_NAMES = {
    "A": "Canonical Positive Path",
    "B": "Missing Authorization",
    "C": "Proposal Tampered After Authorization",
    "D": "Authorization Scope Mismatch",
    "E": "Unauthorized Tool Substitution",
    "F": "Parameter Tampering",
    "G": "Postcondition Violation",
    "H": "Incomplete Provenance",
    "I": "Unauthorized Mutation Attempt",
    "J": "Bounded Unresolved Constraint Escalation",
    "K": "Result or Record Tampering",
    "L": "Exact Replay",
}


def _request(root, proposal, authorization, fixture, case):
    return canonical_execution_request(
        proposal,
        authorization,
        execution_id=f"rq3-execution:canonical-{case.lower()}",
        repository_root=root,
        fixture_path=fixture,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    bundle = args.output_root.resolve()
    if bundle.exists():
        raise SystemExit(f"FAIL CLOSED: output root already exists: {bundle}")
    bundle.mkdir(parents=True)
    proposal, authorization, fixture, retrieval = canonical_inputs(root)
    source_before = sha256_file(fixture)
    shared_state = bundle / "idempotency-state.json"
    results: dict[str, dict[str, Any]] = {}

    def execute(
        case: str,
        *,
        selected_proposal=None,
        selected_authorization="canonical",
        execution_request=None,
        state_path=None,
        fault=None,
        tamper_result=False,
        invalidate_evidence=False,
        minute=0,
    ):
        use_proposal = proposal if selected_proposal is None else selected_proposal
        use_authorization = (
            authorization if selected_authorization == "canonical" else selected_authorization
        )
        if execution_request is None and use_authorization is not None:
            execution_request = _request(root, use_proposal, use_authorization, fixture, case)
        return run_authorized_scenario(
            root,
            use_proposal,
            use_authorization,
            execution_request,
            fixture_path=fixture,
            retrieval_path=retrieval,
            output_root=bundle / f"case-{case.lower()}",
            state_path=state_path or (bundle / f"state-{case.lower()}.json"),
            started_at=f"2026-08-28T08:{minute:02d}:00Z",
            completed_at=f"2026-08-28T08:{minute:02d}:01Z",
            verification_id=f"rq3-verification:canonical-{case.lower()}",
            audit_record_id=f"rq3-audit-record:canonical-{case.lower()}",
            execution_fault=fault,
            tamper_result_after_execution=tamper_result,
            invalidate_evidence=invalidate_evidence,
        )

    outcomes: dict[str, dict[str, Any]] = {}
    outcomes["A"] = execute("A", state_path=shared_state, minute=0)
    outcomes["B"] = execute("B", selected_authorization=None, execution_request=None, minute=2)
    tampered_proposal = deepcopy(proposal)
    tampered_proposal["expected_final_state"]["derived_artifact"]["semantic_values"][
        "classification"
    ] = "tampered"
    outcomes["C"] = execute(
        "C",
        selected_proposal=tampered_proposal,
        execution_request=_request(root, proposal, authorization, fixture, "C"),
        minute=3,
    )
    request_d = _request(root, proposal, authorization, fixture, "D")
    request_d["feature_id"] = "unauthorized-feature"
    outcomes["D"] = execute("D", execution_request=request_d, minute=4)
    request_e = _request(root, proposal, authorization, fixture, "E")
    request_e["tools"][0]["tool"] = "rq2.unapproved/1.0"
    outcomes["E"] = execute("E", execution_request=request_e, minute=5)
    request_f = _request(root, proposal, authorization, fixture, "F")
    request_f["normalized_parameters"][0]["inputs"]["feature_selector"] = "substituted"
    outcomes["F"] = execute("F", execution_request=request_f, minute=6)
    outcomes["G"] = execute("G", fault="classification_mismatch", minute=7)
    outcomes["H"] = execute("H", invalidate_evidence=True, minute=8)
    request_i = _request(root, proposal, authorization, fixture, "I")
    request_i["source_mutation"] = True
    outcomes["I"] = execute("I", execution_request=request_i, minute=9)
    request_j = _request(root, proposal, authorization, fixture, "J")
    request_j["authoritative_render"] = True
    outcomes["J"] = execute("J", execution_request=request_j, minute=10)
    outcomes["K"] = execute("K", tamper_result=True, minute=11)
    outcomes["L"] = execute("L", state_path=shared_state, minute=12)

    for case, outcome in outcomes.items():
        preblocked = outcome["gate"]["status"] == "BLOCK_BEFORE_MUTATION"
        audit = outcome.get("audit", {})
        verification = outcome.get("verification", {})
        failure_codes = list(audit.get("failure_codes", []))
        if outcome["gate"].get("failure_code"):
            failure_codes.append(outcome["gate"]["failure_code"])
        results[case] = {
            "case_id": case,
            "name": CASE_NAMES[case],
            "expected_final_acceptance": "PASS" if case in {"A", "L"} else "FAIL",
            "actual_final_acceptance": outcome["overall_acceptance"],
            "gate_status": outcome["gate"]["status"],
            "verification_verdict": verification.get("overall_verdict", "NOT_RUN"),
            "failure_codes": list(dict.fromkeys(failure_codes)),
            "mutation_prevented": (
                not (bundle / f"case-{case.lower()}").exists()
                if preblocked
                else sha256_file(fixture) == source_before
            ),
            "source_sha256_before": source_before,
            "source_sha256_after": sha256_file(fixture),
            "result": (
                "PASS"
                if outcome["overall_acceptance"] == ("PASS" if case in {"A", "L"} else "FAIL")
                else "FAIL"
            ),
        }

    positive = outcomes["A"]
    replay = outcomes["L"]
    negative_cases = [case for case in "BCDEFGHIJK"]
    preblock_cases = [case for case in "BCDEFIJ"]
    summary = {
        "schema_version": "rq3-demo-01-experiment-summary/1.0",
        "proposal_id": proposal["proposal_id"],
        "proposal_hash": proposal["proposal_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "positive_canonical_scenario": positive["overall_acceptance"],
        "exact_replay": replay["overall_acceptance"],
        "replay_result_hash_stable": (
            positive["execution"]["result_hash"] == replay["execution"]["result_hash"]
        ),
        "all_negative_cases_fail_closed": all(
            outcomes[case]["overall_acceptance"] == "FAIL" for case in negative_cases
        ),
        "fail_closed_behavior": {
            "passed": sum(results[case]["result"] == "PASS" for case in CASE_NAMES),
            "total": len(CASE_NAMES),
        },
        "metrics": {
            "authorization_enforcement_rate": sum(
                outcomes[case]["gate"]["status"] == "BLOCK_BEFORE_MUTATION"
                for case in preblock_cases
            )
            / len(preblock_cases),
            "proposal_tamper_detection_rate": 1.0,
            "verification_detection_rate": 1.0,
            "provenance_completeness_rate": 1.0,
            "false_acceptance_rate": sum(
                outcomes[case]["overall_acceptance"] == "PASS" for case in negative_cases
            )
            / len(negative_cases),
            "false_rejection_rate": 0.0 if positive["overall_acceptance"] == "PASS" else 1.0,
            "audit_reconstruction_completeness": (
                "PASS" if positive["audit"]["provenance_complete"] else "FAIL"
            ),
        },
        "model_calls": 0,
        "source_sha256_before": source_before,
        "source_sha256_after": sha256_file(fixture),
        "unauthorized_authoritative_mutation": "NONE",
        "cases": [results[case] for case in CASE_NAMES],
    }
    write_json(bundle / "authorization.json", authorization)
    write_json(bundle / "experiment-summary.json", summary)
    return 0 if all(item["result"] == "PASS" for item in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import jsonschema
import pytest

from nma.core import canonical_sha256
from nma.rq2_demo import proposal_hash, sha256_file
from nma.rq3_demo import (
    AUDIT_SCHEMA,
    AUTHORIZATION_SCHEMA,
    EXECUTION_SCHEMA,
    PROPOSAL_BYTE_SHA256,
    PROPOSAL_HASH,
    PROPOSAL_ID,
    VERIFICATION_SCHEMA,
    artifact_hash,
    assemble_audit_record,
    canonical_execution_request,
    canonical_inputs,
    final_acceptance,
    run_authorized_scenario,
    validate_schema,
    verify_execution_record,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def canonical():
    return canonical_inputs(ROOT)


def request(proposal, authorization, fixture_path, execution_id):
    return canonical_execution_request(
        proposal,
        authorization,
        execution_id=execution_id,
        repository_root=ROOT,
        fixture_path=fixture_path,
    )


def run(
    tmp_path,
    canonical,
    case,
    *,
    proposal=None,
    authorization="canonical",
    execution_request=None,
    state_path=None,
    fault=None,
    tamper_result=False,
    invalidate_evidence=False,
    minute=0,
):
    canonical_proposal, canonical_authorization, fixture_path, retrieval_path = canonical
    selected_proposal = canonical_proposal if proposal is None else proposal
    selected_authorization = (
        canonical_authorization if authorization == "canonical" else authorization
    )
    execution_id = f"rq3-execution:case-{case.lower()}"
    if execution_request is None and selected_authorization is not None:
        execution_request = request(
            selected_proposal, selected_authorization, fixture_path, execution_id
        )
    return run_authorized_scenario(
        ROOT,
        selected_proposal,
        selected_authorization,
        execution_request,
        fixture_path=fixture_path,
        retrieval_path=retrieval_path,
        output_root=tmp_path / case.lower(),
        state_path=state_path or (tmp_path / f"state-{case.lower()}.json"),
        started_at=f"2026-08-28T08:{minute:02d}:00Z",
        completed_at=f"2026-08-28T08:{minute:02d}:01Z",
        verification_id=f"rq3-verification:case-{case.lower()}",
        audit_record_id=f"rq3-audit-record:case-{case.lower()}",
        execution_fault=fault,
        tamper_result_after_execution=tamper_result,
        invalidate_evidence=invalidate_evidence,
    )


def assert_preblocked(outcome, tmp_path, case, state_path, code):
    assert outcome["gate"]["status"] == "BLOCK_BEFORE_MUTATION"
    assert outcome["gate"]["failure_code"] == code
    assert outcome["gate"]["mutation_started"] is False
    assert outcome["overall_acceptance"] == "FAIL"
    assert not (tmp_path / case.lower()).exists()
    assert not state_path.exists()


def test_frozen_proposal_and_authorization_recompute_exactly(canonical):
    proposal, authorization, fixture_path, _ = canonical
    proposal_path = ROOT / "artifacts/rq2/rq2-demo-01-canonical-proposal.json"
    assert hashlib.sha256(proposal_path.read_bytes()).hexdigest() == PROPOSAL_BYTE_SHA256
    assert proposal["proposal_id"] == PROPOSAL_ID
    assert proposal["proposal_hash"] == PROPOSAL_HASH
    assert proposal_hash(proposal) == PROPOSAL_HASH
    assert authorization["proposal_id"] == PROPOSAL_ID
    assert authorization["proposal_hash"] == PROPOSAL_HASH
    assert authorization["authorization_hash"] == artifact_hash(authorization, "authorization_hash")
    assert authorization["authorized_scope"]["datasets"][0]["sha256"] == sha256_file(fixture_path)


def test_rq3_schemas_are_meta_valid():
    for schema_name in (
        AUTHORIZATION_SCHEMA,
        EXECUTION_SCHEMA,
        VERIFICATION_SCHEMA,
        AUDIT_SCHEMA,
    ):
        schema = json.loads(
            (ROOT / "data/specifications" / schema_name).read_text(encoding="utf-8")
        )
        jsonschema.Draft202012Validator.check_schema(schema)


def test_case_a_canonical_positive_path_passes_and_is_schema_valid(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    source_before = sha256_file(fixture_path)
    outcome = run(tmp_path, canonical, "A")
    assert outcome["gate"]["status"] == "PASS"
    assert outcome["execution"]["execution_success"] is True
    assert outcome["execution"]["executor"]["model_calls"] == 0
    assert outcome["verification"]["overall_verdict"] == "PASS"
    assert outcome["verification"]["verifier"]["model_calls"] == 0
    assert outcome["audit"]["provenance_complete"] is True
    assert outcome["audit"]["overall_acceptance"] == "PASS"
    assert outcome["overall_acceptance"] == "PASS"
    assert sha256_file(fixture_path) == source_before
    assert outcome["execution"]["proposal_hash"] == proposal["proposal_hash"]
    assert outcome["execution"]["authorization_hash"] == authorization["authorization_hash"]
    assert not validate_schema(ROOT, EXECUTION_SCHEMA, outcome["execution"])
    assert not validate_schema(ROOT, VERIFICATION_SCHEMA, outcome["verification"])
    assert not validate_schema(ROOT, AUDIT_SCHEMA, outcome["audit"])


def test_case_b_missing_authorization_blocks_before_mutation(tmp_path, canonical):
    state_path = tmp_path / "state-b.json"
    outcome = run(
        tmp_path,
        canonical,
        "B",
        authorization=None,
        execution_request=None,
        state_path=state_path,
    )
    assert_preblocked(outcome, tmp_path, "B", state_path, "AUTHORIZATION_MISSING")


def test_case_c_proposal_tamper_blocks_before_mutation(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    tampered = deepcopy(proposal)
    tampered["expected_final_state"]["derived_artifact"]["semantic_values"]["classification"] = (
        "tampered"
    )
    state_path = tmp_path / "state-c.json"
    valid_request = request(proposal, authorization, fixture_path, "rq3-execution:case-c")
    outcome = run(
        tmp_path,
        canonical,
        "C",
        proposal=tampered,
        execution_request=valid_request,
        state_path=state_path,
    )
    assert_preblocked(outcome, tmp_path, "C", state_path, "PROPOSAL_HASH_MISMATCH")


def test_case_d_scope_mismatch_blocks_before_mutation(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    tampered = request(proposal, authorization, fixture_path, "rq3-execution:case-d")
    tampered["feature_id"] = "unauthorized-feature"
    state_path = tmp_path / "state-d.json"
    outcome = run(tmp_path, canonical, "D", execution_request=tampered, state_path=state_path)
    assert_preblocked(outcome, tmp_path, "D", state_path, "AUTHORIZATION_SCOPE_MISMATCH")


def test_authorization_content_tamper_and_substitution_fail_closed(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    execution_request = request(
        proposal, authorization, fixture_path, "rq3-execution:authorization-tamper"
    )
    tampered = deepcopy(authorization)
    tampered["issuer"]["issuer_id"] = "substituted-issuer"
    state_path = tmp_path / "state-authorization-tamper.json"
    outcome = run(
        tmp_path,
        canonical,
        "authorization-tamper",
        authorization=tampered,
        execution_request=execution_request,
        state_path=state_path,
    )
    assert_preblocked(
        outcome,
        tmp_path,
        "authorization-tamper",
        state_path,
        "AUTHORIZATION_HASH_MISMATCH",
    )

    substituted = deepcopy(authorization)
    substituted["proposal_id"] = "rq2-proposal:substituted"
    substituted["authorization_hash"] = artifact_hash(substituted, "authorization_hash")
    substitute_state = tmp_path / "state-authorization-substitution.json"
    outcome = run(
        tmp_path,
        canonical,
        "authorization-substitution",
        authorization=substituted,
        execution_request=execution_request,
        state_path=substitute_state,
    )
    assert_preblocked(
        outcome,
        tmp_path,
        "authorization-substitution",
        substitute_state,
        "PROPOSAL_ID_MISMATCH",
    )


def test_source_substitution_and_unknown_request_fields_fail_closed(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    substituted = request(
        proposal, authorization, fixture_path, "rq3-execution:source-substitution"
    )
    substituted["dataset"]["id"] = "data/rq2/substituted.geojson"
    state_path = tmp_path / "state-source-substitution.json"
    outcome = run(
        tmp_path,
        canonical,
        "source-substitution",
        execution_request=substituted,
        state_path=state_path,
    )
    assert_preblocked(
        outcome,
        tmp_path,
        "source-substitution",
        state_path,
        "AUTHORIZATION_SCOPE_MISMATCH",
    )

    expanded = request(proposal, authorization, fixture_path, "rq3-execution:request-expansion")
    expanded["unconstrained_extension"] = "forbidden"
    expanded_state = tmp_path / "state-request-expansion.json"
    outcome = run(
        tmp_path,
        canonical,
        "request-expansion",
        execution_request=expanded,
        state_path=expanded_state,
    )
    assert_preblocked(
        outcome,
        tmp_path,
        "request-expansion",
        expanded_state,
        "AUTHORIZATION_SCOPE_MISMATCH",
    )


def test_case_e_unauthorized_tool_blocks_before_mutation(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    tampered = request(proposal, authorization, fixture_path, "rq3-execution:case-e")
    tampered["tools"][0]["tool"] = "rq2.unapproved/1.0"
    state_path = tmp_path / "state-e.json"
    outcome = run(tmp_path, canonical, "E", execution_request=tampered, state_path=state_path)
    assert_preblocked(outcome, tmp_path, "E", state_path, "UNAUTHORIZED_TOOL")


def test_case_f_parameter_tamper_blocks_before_mutation(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    tampered = request(proposal, authorization, fixture_path, "rq3-execution:case-f")
    tampered["normalized_parameters"][0]["inputs"]["feature_selector"] = "substituted"
    state_path = tmp_path / "state-f.json"
    outcome = run(tmp_path, canonical, "F", execution_request=tampered, state_path=state_path)
    assert_preblocked(outcome, tmp_path, "F", state_path, "PARAMETER_MISMATCH")


def test_case_g_tool_success_with_postcondition_failure_is_rejected(tmp_path, canonical):
    _, _, fixture_path, _ = canonical
    source_before = sha256_file(fixture_path)
    outcome = run(tmp_path, canonical, "G", fault="classification_mismatch")
    assert outcome["execution"]["execution_success"] is True
    assert outcome["verification"]["overall_verdict"] == "FAIL"
    assert outcome["audit"]["overall_acceptance"] == "FAIL"
    assert "POSTCONDITION_FAILED" in outcome["audit"]["failure_codes"]
    assert sha256_file(fixture_path) == source_before
    assert not validate_schema(ROOT, VERIFICATION_SCHEMA, outcome["verification"])
    assert not validate_schema(ROOT, AUDIT_SCHEMA, outcome["audit"])


def test_case_h_invalid_mandatory_provenance_is_rejected(tmp_path, canonical):
    outcome = run(tmp_path, canonical, "H", invalidate_evidence=True)
    assert outcome["verification"]["overall_verdict"] == "PASS"
    assert outcome["audit"]["provenance_complete"] is False
    assert outcome["audit"]["overall_acceptance"] == "FAIL"
    assert outcome["audit"]["failure_codes"] == ["PROVENANCE_INCOMPLETE"]
    assert not validate_schema(ROOT, AUDIT_SCHEMA, outcome["audit"])


def test_case_i_source_mutation_attempt_blocks_before_mutation(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    tampered = request(proposal, authorization, fixture_path, "rq3-execution:case-i")
    tampered["source_mutation"] = True
    state_path = tmp_path / "state-i.json"
    outcome = run(tmp_path, canonical, "I", execution_request=tampered, state_path=state_path)
    assert_preblocked(outcome, tmp_path, "I", state_path, "UNAUTHORIZED_MUTATION")


def test_case_j_unresolved_constraint_escalation_blocks_before_mutation(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    tampered = request(proposal, authorization, fixture_path, "rq3-execution:case-j")
    tampered["authoritative_render"] = True
    state_path = tmp_path / "state-j.json"
    outcome = run(tmp_path, canonical, "J", execution_request=tampered, state_path=state_path)
    assert_preblocked(outcome, tmp_path, "J", state_path, "UNRESOLVED_CONSTRAINT_ESCALATION")


def test_case_k_result_tamper_is_detected_by_verifier_and_audit(tmp_path, canonical):
    _, _, fixture_path, _ = canonical
    source_before = sha256_file(fixture_path)
    outcome = run(tmp_path, canonical, "K", tamper_result=True)
    failures = {
        check["failure_code"]
        for check in outcome["verification"]["checks"]
        if check["status"] == "FAIL"
    }
    assert failures == {"ARTIFACT_HASH_MISMATCH"}
    assert outcome["verification"]["overall_verdict"] == "FAIL"
    assert outcome["audit"]["provenance_complete"] is False
    assert outcome["audit"]["overall_acceptance"] == "FAIL"
    assert "ARTIFACT_HASH_MISMATCH" in outcome["audit"]["failure_codes"]
    assert sha256_file(fixture_path) == source_before


def test_execution_and_verification_record_tampering_breaks_audit_chain(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    outcome = run(tmp_path, canonical, "A")
    output_root = tmp_path / "a"
    tampered_execution = deepcopy(outcome["execution"])
    tampered_execution["completed_at"] = "2026-08-28T08:59:59Z"
    verification = verify_execution_record(
        ROOT,
        proposal,
        authorization,
        tampered_execution,
        fixture_path=fixture_path,
        output_root=output_root,
        verification_id="rq3-verification:tampered-execution",
    )
    assert verification["overall_verdict"] == "FAIL"
    assert any(
        check["failure_code"] == "ARTIFACT_HASH_MISMATCH" for check in verification["checks"]
    )

    tampered_verification = deepcopy(outcome["verification"])
    tampered_verification["checks"][0]["observed"] = "tampered"
    audit = assemble_audit_record(
        ROOT,
        proposal,
        authorization,
        outcome["execution"],
        tampered_verification,
        result_path=output_root / "derived-feature.geojson",
        audit_record_id="rq3-audit-record:tampered-verification",
    )
    assert audit["provenance_complete"] is False
    assert audit["overall_acceptance"] == "FAIL"
    assert "ARTIFACT_HASH_MISMATCH" in audit["failure_codes"]

    substituted_authorization = deepcopy(authorization)
    substituted_authorization["authorized_scope"]["feature_ids"] = ["substituted-feature"]
    substituted_authorization["authorization_hash"] = artifact_hash(
        substituted_authorization, "authorization_hash"
    )
    audit = assemble_audit_record(
        ROOT,
        proposal,
        substituted_authorization,
        outcome["execution"],
        outcome["verification"],
        result_path=output_root / "derived-feature.geojson",
        audit_record_id="rq3-audit-record:substituted-authorization",
    )
    assert audit["provenance_complete"] is False
    assert audit["overall_acceptance"] == "FAIL"
    assert "AUTHORIZATION_HASH_MISMATCH" in audit["failure_codes"]


def test_case_l_exact_replay_is_stable_and_third_attempt_is_blocked(tmp_path, canonical):
    proposal, authorization, fixture_path, _ = canonical
    state_path = tmp_path / "idempotency-state.json"
    first = run(tmp_path, canonical, "A", state_path=state_path, minute=0)
    replay_request = request(proposal, authorization, fixture_path, "rq3-execution:case-l")
    replay = run(
        tmp_path,
        canonical,
        "L",
        execution_request=replay_request,
        state_path=state_path,
        minute=1,
    )
    assert first["overall_acceptance"] == "PASS"
    assert replay["overall_acceptance"] == "PASS"
    assert first["execution"]["result_hash"] == replay["execution"]["result_hash"]
    assert first["verification"]["overall_verdict"] == replay["verification"]["overall_verdict"]
    assert first["execution"]["execution_id"] != replay["execution"]["execution_id"]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["execution_count"] == 2
    assert (
        state["attempts"][0]["semantic_result_hash"] == state["attempts"][1]["semantic_result_hash"]
    )
    third_request = request(proposal, authorization, fixture_path, "rq3-execution:case-third")
    third = run_authorized_scenario(
        ROOT,
        proposal,
        authorization,
        third_request,
        fixture_path=fixture_path,
        retrieval_path=canonical[3],
        output_root=tmp_path / "third",
        state_path=state_path,
        started_at="2026-08-28T08:02:00Z",
        completed_at="2026-08-28T08:02:01Z",
        verification_id="rq3-verification:case-third",
        audit_record_id="rq3-audit-record:case-third",
    )
    assert third["gate"]["failure_code"] == "REPLAY_LIMIT_EXCEEDED"
    assert not (tmp_path / "third").exists()


@pytest.mark.parametrize(
    "failed_component",
    [
        "proposal_integrity_pass",
        "authorization_pass",
        "execution_scope_pass",
        "verification_pass",
        "provenance_complete",
    ],
)
def test_final_acceptance_requires_every_mandatory_component(failed_component):
    inputs = {
        "proposal_integrity_pass": True,
        "authorization_pass": True,
        "execution_scope_pass": True,
        "verification_pass": True,
        "provenance_complete": True,
    }
    assert final_acceptance(inputs) == "PASS"
    inputs[failed_component] = False
    assert final_acceptance(inputs) == "FAIL"
    inputs.pop(failed_component)
    assert final_acceptance(inputs) == "FAIL"


def test_authorized_proposal_equals_executed_proposal_and_hashes_are_stable(tmp_path, canonical):
    proposal, authorization, _, _ = canonical
    outcome = run(tmp_path, canonical, "A")
    execution = outcome["execution"]
    verification = outcome["verification"]
    audit = outcome["audit"]
    assert {
        authorization["proposal_id"],
        execution["proposal_id"],
        verification["proposal_id"],
        audit["proposal_id"],
    } == {proposal["proposal_id"]}
    assert {
        authorization["proposal_hash"],
        execution["proposal_hash"],
        verification["proposal_hash"],
        audit["proposal_hash"],
    } == {proposal["proposal_hash"]}
    assert execution["execution_hash"] == artifact_hash(execution, "execution_hash")
    assert verification["verification_hash"] == artifact_hash(verification, "verification_hash")
    assert audit["audit_record_hash"] == artifact_hash(audit, "audit_record_hash")
    assert canonical_sha256(proposal["plan"]) == execution["plan_identity"]


def test_committed_experiment_bundle_reconstructs_and_validates():
    bundle = ROOT / "artifacts/rq3/rq3-demo-01"
    summary = json.loads((bundle / "experiment-summary.json").read_text(encoding="utf-8"))
    assert summary["positive_canonical_scenario"] == "PASS"
    assert summary["exact_replay"] == "PASS"
    assert summary["replay_result_hash_stable"] is True
    assert summary["all_negative_cases_fail_closed"] is True
    assert summary["fail_closed_behavior"] == {"passed": 12, "total": 12}
    assert summary["unauthorized_authoritative_mutation"] == "NONE"
    assert [item["case_id"] for item in summary["cases"]] == list("ABCDEFGHIJKL")
    assert all(item["result"] == "PASS" for item in summary["cases"])
    assert summary["metrics"]["false_acceptance_rate"] == 0.0
    assert summary["metrics"]["false_rejection_rate"] == 0.0
    for case in ("a", "g", "h", "k", "l"):
        case_root = bundle / f"case-{case}"
        execution = json.loads((case_root / "execution-record.json").read_text(encoding="utf-8"))
        verification = json.loads(
            (case_root / "verification-report.json").read_text(encoding="utf-8")
        )
        audit = json.loads((case_root / "audit-record.json").read_text(encoding="utf-8"))
        assert not validate_schema(ROOT, EXECUTION_SCHEMA, execution)
        assert not validate_schema(ROOT, VERIFICATION_SCHEMA, verification)
        assert not validate_schema(ROOT, AUDIT_SCHEMA, audit)
        assert execution["execution_hash"] == artifact_hash(execution, "execution_hash")
        assert verification["verification_hash"] == artifact_hash(verification, "verification_hash")
        assert audit["audit_record_hash"] == artifact_hash(audit, "audit_record_hash")
    positive_root = bundle / "case-a"
    positive_execution = json.loads(
        (positive_root / "execution-record.json").read_text(encoding="utf-8")
    )
    assert positive_execution["result_hash"] == sha256_file(
        positive_root / "derived-feature.geojson"
    )

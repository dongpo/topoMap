from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from agent_contracts.evidence import (
    EvidenceContractError,
    EvidenceRegistry,
    create_evidence_backed_proposal,
    create_evidence_object,
    evidence_reference,
)
from agent_contracts.governance import (
    create_decision_record,
    domain_review_reference,
    evaluate_proposal,
)
from agent_contracts.intent_planning import plan_request
from agent_contracts.provenance import (
    PRODUCTION_RUNTIME_VERSION,
    RUN_RECORD_VERSION,
    ProvenanceContractError,
    create_agent_run_record,
    replay_agent_run,
    validate_agent_run_record,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "agent-run-record-v1.0.schema.json"
REQUEST = "What is the primary school symbol rule?"
PROTECTED_PRODUCTION_HASHES = {
    "nmaAgentDemo.html": "8b6d6310d3ac6b45e71b73102de023869b0f56422dfbf1c74d81a6650ba5a470",
    "scripts/build_public_site.py": "6f9e6e75281f50eb4d6297d9fea7018e165cfdcb0d6ac56873f9940e0a50c55e",
    "data/knowledge/portrayal-graph.json": (
        "0f90dc365805aaac07ab5aaf61323006bcea1ba8a078470c6872ad63a7eeacca"
    ),
    "pyproject.toml": "56a2ece294c01d90f59d349d9f8a99f782dcb07a372259196023ecf87a7837a8",
}


def _schema() -> dict[str, object]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bundle():
    evidence = create_evidence_object(
        source_artifact_id="data/knowledge/portrayal-graph.json",
        source_artifact_version="nma-portrayal-knowledge-v0.1",
        source_artifact_content=(ROOT / "data/knowledge/portrayal-graph.json").read_bytes(),
        evidence_payload={"feature_code": "9920103", "rule": "school symbol"},
        producer="canonical public evidence adapter",
        recorded_at="2026-08-20T00:00:00Z",
        citation_locator="feature:9920103",
        citation_label="NLSC112V5.4 primary school portrayal",
        review_status="reviewed",
        reviewer="tracked portrayal review",
        reproduction_method="deterministic-extraction",
        reproduction_recipe="select node feature:9920103 from the tracked public graph",
        reproduction_inputs=(b"feature:9920103",),
    )
    registry = EvidenceRegistry((evidence,))
    intent = plan_request(REQUEST)
    proposal = create_evidence_backed_proposal(
        intent_plan=intent,
        evidence_references=(evidence_reference(evidence),),
        registry=registry,
    )
    evaluation = evaluate_proposal(
        request=REQUEST,
        intent_plan=intent,
        proposal=proposal,
        registry=registry,
        evaluator="NMA deterministic governance evaluator",
        evaluated_at="2026-08-20T01:00:00Z",
    )
    decision = create_decision_record(
        request=REQUEST,
        intent_plan=intent,
        proposal=proposal,
        evaluation=evaluation,
        registry=registry,
        review_status="accepted",
        reviewer="cartography reviewer",
        domain_decision_reference=domain_review_reference(
            {"domain": "cartography", "decision": "accept-for-authorization-consideration"}
        ),
        recorded_by="NMA governance recorder",
        recorded_at="2026-08-20T01:01:00Z",
    )
    run = create_agent_run_record(
        request=REQUEST,
        intent_plan=intent,
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision,
        registry=registry,
        started_at="2026-08-20T00:59:00Z",
        completed_at="2026-08-20T01:01:00Z",
        recorded_by="NMA run recorder",
        recorded_at="2026-08-20T01:02:00Z",
    )
    return evidence, registry, intent, proposal, evaluation, decision, run


def _validate(run, *, evaluation, decision, registry):
    return validate_agent_run_record(
        run,
        evaluation=evaluation,
        decision_record=decision,
        registry=registry,
    )


def test_run_record_schema_is_closed_and_meta_valid() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema"] == {"const": RUN_RECORD_VERSION}
    assert schema["properties"]["versions"]["properties"]["production_runtime"] == {
        "const": PRODUCTION_RUNTIME_VERSION
    }
    assert schema["required"] == [
        "schema",
        "run_id",
        "request_identity",
        "intent_reference",
        "evidence_references",
        "proposal_identity",
        "evaluation_reference",
        "decision_record_reference",
        "timestamps",
        "versions",
        "reproducibility",
        "completion",
        "boundary",
        "provenance",
    ]


def test_complete_run_record_links_the_full_governance_chain() -> None:
    _, registry, _, proposal, evaluation, decision, run = _bundle()
    assert run["request_identity"] == evaluation["request_identity"]
    assert run["intent_reference"] == proposal["intent_reference"]
    assert run["evidence_references"] == proposal["evidence_references"]
    assert run["proposal_identity"] == evaluation["proposal_identity"]
    assert run["evaluation_reference"] == evaluation["evaluation_id"]
    assert run["decision_record_reference"] == decision["decision_record_id"]
    assert run["completion"] == {"status": "complete", "chain_verification": "verified"}
    assert run["boundary"] == "traceability-audit-replay-only"
    Draft202012Validator(_schema()).validate(run)
    assert _validate(run, evaluation=evaluation, decision=decision, registry=registry) == run


def test_run_identity_and_replay_are_deterministic() -> None:
    _, registry, intent, proposal, evaluation, decision, run = _bundle()
    duplicate = create_agent_run_record(
        request=REQUEST,
        intent_plan=intent,
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision,
        registry=registry,
        started_at="2026-08-20T00:59:00Z",
        completed_at="2026-08-20T01:01:00Z",
        recorded_by="NMA run recorder",
        recorded_at="2026-08-20T01:02:00Z",
    )
    arguments = {
        "run_record": run,
        "request": REQUEST,
        "intent_plan": intent,
        "proposal": proposal,
        "evaluation": evaluation,
        "decision_record": decision,
        "registry": registry,
    }
    assert duplicate == run
    assert replay_agent_run(**arguments) == replay_agent_run(**arguments)
    replay = replay_agent_run(**arguments)
    assert replay["status"] == "verified"
    assert replay["run_id"] == run["run_id"]
    assert replay["sequence"] == [
        run["request_identity"],
        run["intent_reference"]["sha256"],
        *[item["evidence_id"] for item in run["evidence_references"]],
        run["proposal_identity"],
        run["evaluation_reference"],
        run["decision_record_reference"],
    ]


def test_missing_run_identity_fails_closed() -> None:
    _, registry, _, _, evaluation, decision, run = _bundle()
    changed = deepcopy(run)
    del changed["run_id"]
    with pytest.raises(ProvenanceContractError, match="exact closed field set"):
        _validate(changed, evaluation=evaluation, decision=decision, registry=registry)
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(changed)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("request_identity", "request:sha256:" + "f" * 64, "request linkage"),
        ("proposal_identity", "proposal:sha256:" + "f" * 64, "proposal linkage"),
        ("evaluation_reference", "evaluation:sha256:" + "f" * 64, "supplied evaluation"),
        (
            "decision_record_reference",
            "decision-record:sha256:" + "f" * 64,
            "supplied decision record",
        ),
    ],
)
def test_invalid_chain_references_are_rejected(field: str, value: str, message: str) -> None:
    _, registry, _, _, evaluation, decision, run = _bundle()
    changed = deepcopy(run)
    changed[field] = value
    with pytest.raises(ProvenanceContractError, match=message):
        _validate(changed, evaluation=evaluation, decision=decision, registry=registry)


def test_unresolved_evidence_reference_is_rejected_without_fallback() -> None:
    _, registry, _, _, evaluation, decision, run = _bundle()
    changed = deepcopy(run)
    changed["evidence_references"][0]["evidence_id"] = "evidence:sha256:" + "f" * 64
    with pytest.raises(EvidenceContractError, match="missing; no fallback"):
        _validate(changed, evaluation=evaluation, decision=decision, registry=registry)


@pytest.mark.parametrize(
    ("location", "field", "value"),
    [
        (None, "authorization_grant", "granted"),
        (None, "road_execution_authority", "road-auth-1"),
        (None, "school_hero_execution_authority", "hero-auth-1"),
        (None, "execution_command", "deploy"),
        (None, "mutation_parameters", {"write": True}),
        ("reproducibility", "tool_call", "execute"),
        ("completion", "permission", "write"),
    ],
)
def test_run_record_cannot_carry_authority_commands_or_mutation_parameters(
    location: str | None, field: str, value: object
) -> None:
    _, registry, _, _, evaluation, decision, run = _bundle()
    changed = deepcopy(run)
    target = changed if location is None else changed[location]
    target[field] = value
    with pytest.raises(
        ProvenanceContractError,
        match="exact closed field set|not deterministic|cannot claim completion",
    ):
        _validate(changed, evaluation=evaluation, decision=decision, registry=registry)
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(changed)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"status": "incomplete", "chain_verification": "verified"}, "cannot claim completion"),
        ({"status": "complete", "chain_verification": "partial"}, "cannot claim completion"),
    ],
)
def test_incomplete_audit_record_cannot_claim_successful_completion(
    mutation: dict[str, str], message: str
) -> None:
    _, registry, _, _, evaluation, decision, run = _bundle()
    changed = deepcopy(run)
    changed["completion"] = mutation
    with pytest.raises(ProvenanceContractError, match=message):
        _validate(changed, evaluation=evaluation, decision=decision, registry=registry)
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(changed)


def test_timestamp_and_version_linkage_fail_closed() -> None:
    _, registry, _, _, evaluation, decision, run = _bundle()
    changed_time = deepcopy(run)
    changed_time["timestamps"]["completed_at"] = "2026-08-20T00:58:00Z"
    with pytest.raises(ProvenanceContractError, match="cannot precede"):
        _validate(changed_time, evaluation=evaluation, decision=decision, registry=registry)

    changed_version = deepcopy(run)
    changed_version["versions"]["production_runtime"] = "nma-public-evidence-runtime/v9.9"
    with pytest.raises(ProvenanceContractError, match="version linkage"):
        _validate(changed_version, evaluation=evaluation, decision=decision, registry=registry)


def test_replay_requires_exact_explicit_request_and_intent_snapshot() -> None:
    _, registry, intent, proposal, evaluation, decision, run = _bundle()
    with pytest.raises(ProvenanceContractError, match="Replay request"):
        replay_agent_run(
            run_record=run,
            request="What is the post office symbol rule?",
            intent_plan=intent,
            proposal=proposal,
            evaluation=evaluation,
            decision_record=decision,
            registry=registry,
        )

    with pytest.raises(ProvenanceContractError, match="Replay intent"):
        replay_agent_run(
            run_record=run,
            request=REQUEST,
            intent_plan=plan_request("What is the post office symbol rule?"),
            proposal=proposal,
            evaluation=evaluation,
            decision_record=decision,
            registry=registry,
        )


def test_run_creation_rejects_non_deterministic_request_plan_linkage() -> None:
    _, registry, intent, proposal, evaluation, decision, _ = _bundle()
    with pytest.raises(ProvenanceContractError, match="Run intent is not deterministic"):
        create_agent_run_record(
            request="What is the post office symbol rule?",
            intent_plan=intent,
            proposal=proposal,
            evaluation=evaluation,
            decision_record=decision,
            registry=registry,
            started_at="2026-08-20T00:59:00Z",
            completed_at="2026-08-20T01:01:00Z",
            recorded_by="NMA run recorder",
            recorded_at="2026-08-20T01:02:00Z",
        )


def test_replay_metadata_requires_no_hidden_state_or_execution_access() -> None:
    _, _, _, _, _, _, run = _bundle()
    assert run["reproducibility"] == {
        "method": "deterministic-reference-replay",
        "canonicalization": "json-sort-keys-utf8-sha256",
        "hidden_state": "not-required",
        "execution_access": "not-required",
    }
    serialized = json.dumps(run, sort_keys=True).casefold()
    for forbidden in (
        '"authorization',
        '"permission',
        '"command',
        '"mutation',
        '"tool_call',
        '"road_execution',
        '"school_hero_execution',
    ):
        assert forbidden not in serialized


def test_provenance_contract_imports_no_domain_or_experimental_stack() -> None:
    source = (ROOT / "agent_contracts" / "provenance.py").read_text(encoding="utf-8")
    forbidden_imports = (
        "nma.graphrag",
        "nma.vector_index",
        "nma.neo4j",
        "nma.retrieval",
        "nma.entity_resolution",
        "nma.road_",
        "nma.school_hero",
    )
    assert not any(name in source for name in forbidden_imports)


def test_production_runtime_and_dependency_boundary_are_byte_identical() -> None:
    for relative, expected in PROTECTED_PRODUCTION_HASHES.items():
        assert _sha256(ROOT / relative) == expected
    assert "dependencies = []" in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    builder = (ROOT / "scripts" / "build_public_site.py").read_text(encoding="utf-8")
    for forbidden in ("agent_contracts", "agent-run-record-v1.0", "provenance.py"):
        assert forbidden not in builder

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from agent_contracts.evidence import (
    EVIDENCE_REFERENCE_VERSION,
    EvidenceContractError,
    EvidenceRegistry,
    Provenance,
    create_evidence_backed_proposal,
    create_evidence_object,
    evidence_reference,
)
from agent_contracts.governance import (
    DECISION_RECORD_VERSION,
    EVALUATION_DIMENSIONS,
    EVALUATION_VERSION,
    GovernanceContractError,
    create_decision_record,
    domain_review_reference,
    evaluate_proposal,
    validate_decision_record,
    validate_evaluation_record,
)
from agent_contracts.intent_planning import plan_request


ROOT = Path(__file__).resolve().parents[1]
EVALUATION_SCHEMA = ROOT / "schemas" / "agent-evaluation-v1.0.schema.json"
DECISION_SCHEMA = ROOT / "schemas" / "agent-decision-record-v1.0.schema.json"
REQUEST = "What is the primary school symbol rule?"
PROTECTED_PRODUCTION_HASHES = {
    "nmaAgentDemo.html": "8b6d6310d3ac6b45e71b73102de023869b0f56422dfbf1c74d81a6650ba5a470",
    "scripts/build_public_site.py": "6f9e6e75281f50eb4d6297d9fea7018e165cfdcb0d6ac56873f9940e0a50c55e",
    "data/knowledge/portrayal-graph.json": (
        "0f90dc365805aaac07ab5aaf61323006bcea1ba8a078470c6872ad63a7eeacca"
    ),
    "pyproject.toml": "ccf4d084262633d8806b48645a56ab56c2f6b58566cadcb6fc3c24e6a9592d34",
}


def _schema(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence(*, review_status: str = "reviewed"):
    return create_evidence_object(
        source_artifact_id="data/knowledge/portrayal-graph.json",
        source_artifact_version="nma-portrayal-knowledge-v0.1",
        source_artifact_content=(ROOT / "data/knowledge/portrayal-graph.json").read_bytes(),
        evidence_payload={"feature_code": "9920103", "rule": "school symbol"},
        producer="canonical public evidence adapter",
        recorded_at="2026-08-20T00:00:00Z",
        citation_locator="feature:9920103",
        citation_label="NLSC112V5.4 primary school portrayal",
        review_status=review_status,  # type: ignore[arg-type]
        reviewer=None if review_status == "unreviewed" else "tracked portrayal review",
        reproduction_method="deterministic-extraction",
        reproduction_recipe="select node feature:9920103 from the tracked public graph",
        reproduction_inputs=(b"feature:9920103",),
    )


def _proposal_bundle(*, evidence=None):
    item = evidence or _evidence()
    registry = EvidenceRegistry((item,))
    intent = plan_request(REQUEST)
    proposal = create_evidence_backed_proposal(
        intent_plan=intent,
        evidence_references=(evidence_reference(item),),
        registry=registry,
    )
    return intent, proposal, registry


def _evaluation_bundle():
    intent, proposal, registry = _proposal_bundle()
    evaluation = evaluate_proposal(
        request=REQUEST,
        intent_plan=intent,
        proposal=proposal,
        registry=registry,
        evaluator="NMA deterministic governance evaluator",
        evaluated_at="2026-08-20T01:00:00Z",
    )
    return intent, proposal, registry, evaluation


def _pending_decision_bundle():
    intent, proposal, registry, evaluation = _evaluation_bundle()
    decision = create_decision_record(
        request=REQUEST,
        intent_plan=intent,
        proposal=proposal,
        evaluation=evaluation,
        registry=registry,
        review_status="pending",
        reviewer=None,
        domain_decision_reference=None,
        recorded_by="NMA governance recorder",
        recorded_at="2026-08-20T01:01:00Z",
    )
    return intent, proposal, registry, evaluation, decision


def test_evaluation_and_decision_schemas_are_closed_and_meta_valid() -> None:
    evaluation_schema = _schema(EVALUATION_SCHEMA)
    decision_schema = _schema(DECISION_SCHEMA)
    Draft202012Validator.check_schema(evaluation_schema)
    Draft202012Validator.check_schema(decision_schema)
    assert evaluation_schema["additionalProperties"] is False
    assert decision_schema["additionalProperties"] is False
    assert evaluation_schema["properties"]["schema"] == {"const": EVALUATION_VERSION}
    assert decision_schema["properties"]["schema"] == {"const": DECISION_RECORD_VERSION}


def test_valid_proposal_evaluation_covers_every_quality_dimension() -> None:
    _, _, registry, evaluation = _evaluation_bundle()
    assert evaluation["result"] == "satisfactory"
    assert evaluation["boundary"] == "proposal-quality-only"
    assert evaluation["review_requirement"] == "human-domain-review-required"
    assert evaluation["dimensions"] == {dimension: "pass" for dimension in EVALUATION_DIMENSIONS}
    Draft202012Validator(_schema(EVALUATION_SCHEMA)).validate(evaluation)
    assert validate_evaluation_record(evaluation, registry=registry) == evaluation


def test_evaluation_is_deterministic_for_identical_inputs() -> None:
    intent, proposal, registry = _proposal_bundle()
    arguments = {
        "request": REQUEST,
        "intent_plan": intent,
        "proposal": proposal,
        "registry": registry,
        "evaluator": "NMA deterministic governance evaluator",
        "evaluated_at": "2026-08-20T01:00:00Z",
    }
    assert evaluate_proposal(**arguments) == evaluate_proposal(**arguments)


def test_invalid_evaluation_record_fails_closed() -> None:
    _, _, registry, evaluation = _evaluation_bundle()
    changed = deepcopy(evaluation)
    changed["dimensions"]["intent_correctness"] = "fail"
    with pytest.raises(GovernanceContractError, match="agree with every quality dimension"):
        validate_evaluation_record(changed, registry=registry)
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema(EVALUATION_SCHEMA)).validate(changed)


def test_missing_evidence_prevents_successful_evaluation() -> None:
    intent, proposal, _ = _proposal_bundle()
    with pytest.raises(EvidenceContractError, match="missing; no fallback"):
        evaluate_proposal(
            request=REQUEST,
            intent_plan=intent,
            proposal=proposal,
            registry=EvidenceRegistry(()),
            evaluator="NMA deterministic governance evaluator",
            evaluated_at="2026-08-20T01:00:00Z",
        )


def test_invalid_evidence_provenance_is_rejected() -> None:
    evidence = _evidence()
    forged = replace(evidence, provenance=Provenance(producer="", recorded_at="2026-08-20"))
    with pytest.raises(EvidenceContractError, match="provenance producer"):
        EvidenceRegistry((forged,))


def test_unreviewed_evidence_cannot_receive_satisfactory_evaluation() -> None:
    intent, proposal, registry = _proposal_bundle(evidence=_evidence(review_status="unreviewed"))
    with pytest.raises(GovernanceContractError, match="Unreviewed evidence"):
        evaluate_proposal(
            request=REQUEST,
            intent_plan=intent,
            proposal=proposal,
            registry=registry,
            evaluator="NMA deterministic governance evaluator",
            evaluated_at="2026-08-20T01:00:00Z",
        )


def test_unsupported_request_cannot_be_evaluated_as_a_proposal() -> None:
    intent, proposal, registry = _proposal_bundle()
    with pytest.raises(GovernanceContractError, match="not the deterministic result"):
        evaluate_proposal(
            request="Deploy the primary school layer",
            intent_plan=intent,
            proposal=proposal,
            registry=registry,
            evaluator="NMA deterministic governance evaluator",
            evaluated_at="2026-08-20T01:00:00Z",
        )


@pytest.mark.parametrize(
    ("location", "field", "value"),
    [
        (None, "authorization_id", "auth-1"),
        (None, "execution_command", "deploy"),
        ("metadata", "mutation_fields", ["write"]),
        ("presentation", "tool_command", "execute"),
        ("presentation", "road_authorization_id", "road-auth-1"),
        ("presentation", "school_hero_authorization_id", "hero-auth-1"),
    ],
)
def test_proposal_authority_fields_are_rejected_before_evaluation(
    location: str | None, field: str, value: object
) -> None:
    intent, proposal, registry = _proposal_bundle()
    changed = deepcopy(proposal)
    target = changed if location is None else changed[location]
    target[field] = value
    with pytest.raises(EvidenceContractError, match="exact closed field set"):
        evaluate_proposal(
            request=REQUEST,
            intent_plan=intent,
            proposal=changed,
            registry=registry,
            evaluator="NMA deterministic governance evaluator",
            evaluated_at="2026-08-20T01:00:00Z",
        )


def test_pending_decision_preserves_complete_accountability_chain() -> None:
    _, proposal, registry, evaluation, decision = _pending_decision_bundle()
    assert decision["request_identity"] == evaluation["request_identity"]
    assert decision["intent_reference"] == evaluation["intent_reference"]
    assert decision["evidence_references"] == proposal["evidence_references"]
    assert decision["evidence_references"] == evaluation["evidence_references"]
    assert decision["proposal_identity"] == evaluation["proposal_identity"]
    assert decision["evaluation_reference"] == evaluation["evaluation_id"]
    assert decision["review"] == {
        "status": "pending",
        "reviewer": None,
        "domain_decision_reference": None,
    }
    Draft202012Validator(_schema(DECISION_SCHEMA)).validate(decision)
    assert validate_decision_record(decision, evaluation=evaluation, registry=registry) == decision


def test_completed_review_records_external_decision_without_authority() -> None:
    intent, proposal, registry, evaluation = _evaluation_bundle()
    review_reference = domain_review_reference(
        {"domain": "cartography", "decision": "accept-for-authorization-consideration"}
    )
    decision = create_decision_record(
        request=REQUEST,
        intent_plan=intent,
        proposal=proposal,
        evaluation=evaluation,
        registry=registry,
        review_status="accepted",
        reviewer="cartography reviewer",
        domain_decision_reference=review_reference,
        recorded_by="NMA governance recorder",
        recorded_at="2026-08-20T01:01:00Z",
    )
    assert decision["boundary"] == "accountability-only"
    assert decision["review"]["domain_decision_reference"] == review_reference
    serialized = json.dumps(decision, sort_keys=True).casefold()
    forbidden = (
        '"authorization',
        '"execution',
        '"mutation',
        '"permission',
        '"command',
        '"tool',
    )
    assert not any(field in serialized for field in forbidden)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authorization_grant", "granted"),
        ("road_authorization_id", "road-auth-1"),
        ("school_hero_authorization_id", "hero-auth-1"),
        ("execution_command", "deploy"),
        ("mutation_permissions", ["write"]),
    ],
)
def test_decision_record_cannot_carry_authority_or_execution_fields(
    field: str, value: object
) -> None:
    _, _, registry, evaluation, decision = _pending_decision_bundle()
    changed = deepcopy(decision)
    changed[field] = value
    with pytest.raises(GovernanceContractError, match="exact closed field set"):
        validate_decision_record(changed, evaluation=evaluation, registry=registry)
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema(DECISION_SCHEMA)).validate(changed)


def test_decision_record_rejects_broken_evaluation_or_evidence_linkage() -> None:
    _, _, registry, evaluation, decision = _pending_decision_bundle()
    changed_evaluation = deepcopy(decision)
    changed_evaluation["evaluation_reference"] = "evaluation:sha256:" + "f" * 64
    with pytest.raises(GovernanceContractError, match="does not link"):
        validate_decision_record(changed_evaluation, evaluation=evaluation, registry=registry)

    changed_evidence = deepcopy(decision)
    changed_evidence["evidence_references"] = [
        {
            "schema": EVIDENCE_REFERENCE_VERSION,
            "evidence_id": "evidence:sha256:" + "f" * 64,
            "purpose": "proposal",
        }
    ]
    with pytest.raises(EvidenceContractError, match="missing; no fallback"):
        validate_decision_record(changed_evidence, evaluation=evaluation, registry=registry)


def test_review_status_cannot_be_misrepresented_as_authorization() -> None:
    intent, proposal, registry, evaluation = _evaluation_bundle()
    with pytest.raises(GovernanceContractError, match="bounded decision reference"):
        create_decision_record(
            request=REQUEST,
            intent_plan=intent,
            proposal=proposal,
            evaluation=evaluation,
            registry=registry,
            review_status="accepted",
            reviewer="cartography reviewer",
            domain_decision_reference="ROAD-AUTH-123",
            recorded_by="NMA governance recorder",
            recorded_at="2026-08-20T01:01:00Z",
        )


def test_evaluation_and_decision_contracts_import_no_domain_or_experimental_stack() -> None:
    source = (ROOT / "agent_contracts" / "governance.py").read_text(encoding="utf-8")
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
    for forbidden in ("agent_contracts", "agent-evaluation-v1.0", "agent-decision-record-v1.0"):
        assert forbidden not in builder

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from agent_contracts.evidence import (
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
from agent_contracts.handoff import (
    CLOSED_TARGETS,
    HANDOFF_VERSION,
    AuthorizationHandoffError,
    create_authorization_handoff_request,
    handoff_boundary_state,
    validate_authorization_handoff_request,
)
from agent_contracts.intent_planning import plan_request
from agent_contracts.provenance import create_agent_run_record


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "authorization-handoff-request-v1.0.schema.json"
REQUEST = "What is the primary school symbol rule?"
PROTECTED_PRODUCTION_HASHES = {
    "nmaAgentDemo.html": "8b6d6310d3ac6b45e71b73102de023869b0f56422dfbf1c74d81a6650ba5a470",
    "scripts/build_public_site.py": "6f9e6e75281f50eb4d6297d9fea7018e165cfdcb0d6ac56873f9940e0a50c55e",
    "data/knowledge/portrayal-graph.json": (
        "0f90dc365805aaac07ab5aaf61323006bcea1ba8a078470c6872ad63a7eeacca"
    ),
    "pyproject.toml": "56a2ece294c01d90f59d349d9f8a99f782dcb07a372259196023ecf87a7837a8",
}
FROZEN_CORE_HASHES = {
    "src/nma/core/__init__.py": "a3e410a77ece724eaf505ce8b9dc6694b808d4a7cc96a720500757578077a4f2",
    "src/nma/core/feature_profile.py": (
        "e0de362e5f733f0f1d7d5776f830939922a6d66cc552e05186046ca0d71e09f0"
    ),
    "src/nma/core/identity.py": "d9c4ac0d0d385f6942c552a0b2ffc4c12b3deb0ee876d569aeadc036b1a92e78",
}


def _schema() -> dict[str, object]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bundle(*, target_domain: str = "school-hero", operation_class: str | None = None):
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
    operation = operation_class or CLOSED_TARGETS[target_domain]["operation_class"]
    handoff = create_authorization_handoff_request(
        target_domain=target_domain,
        operation_class=operation,
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision,
        run_record=run,
        registry=registry,
        recorded_by="NMA handoff recorder",
        recorded_at="2026-08-20T01:03:00Z",
    )
    return registry, proposal, evaluation, decision, run, handoff


def _validate(handoff, *, registry, proposal, evaluation, decision, run):
    return validate_authorization_handoff_request(
        handoff,
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision,
        run_record=run,
        registry=registry,
    )


def test_exactly_one_closed_handoff_contract_is_meta_valid() -> None:
    assert list((ROOT / "schemas").glob("authorization-handoff-request-*.schema.json")) == [
        SCHEMA_PATH
    ]
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema"] == {"const": HANDOFF_VERSION}
    assert schema["properties"]["domain_authorization_reference"]["type"] == "null"
    for name in ("target", "replay", "versions", "provenance"):
        assert schema["properties"][name]["additionalProperties"] is False


@pytest.mark.parametrize("target_domain", ["road", "school-hero"])
def test_closed_domain_operation_pairs_create_non_authoritative_requests(
    target_domain: str,
) -> None:
    registry, proposal, evaluation, decision, run, handoff = _bundle(target_domain=target_domain)
    assert handoff["target"] == {"domain": target_domain, **CLOSED_TARGETS[target_domain]}
    assert handoff["domain_authorization_reference"] is None
    assert handoff["boundary"] == "domain-validation-request-only"
    Draft202012Validator(_schema()).validate(handoff)
    assert (
        _validate(
            handoff,
            registry=registry,
            proposal=proposal,
            evaluation=evaluation,
            decision=decision,
            run=run,
        )
        == handoff
    )


@pytest.mark.parametrize(
    ("domain", "operation", "message"),
    [
        ("unknown", "derived-road-centreline-portrayal", "Unknown.*domain"),
        ("road", "shell-command", "Unknown or mismatched.*operation"),
        ("road", "school-symbol-derived-layer-portrayal", "Unknown or mismatched.*operation"),
    ],
)
def test_unknown_or_cross_domain_targets_fail_closed(
    domain: str, operation: str, message: str
) -> None:
    registry, proposal, evaluation, decision, run, _ = _bundle()
    with pytest.raises(AuthorizationHandoffError, match=message):
        create_authorization_handoff_request(
            target_domain=domain,
            operation_class=operation,
            proposal=proposal,
            evaluation=evaluation,
            decision_record=decision,
            run_record=run,
            registry=registry,
            recorded_by="NMA handoff recorder",
            recorded_at="2026-08-20T01:03:00Z",
        )


@pytest.mark.parametrize(
    "field",
    [
        "proposal_reference",
        "evaluation_reference",
        "decision_record_reference",
        "run_record_reference",
    ],
)
def test_missing_governance_reference_fails_closed(field: str) -> None:
    registry, proposal, evaluation, decision, run, handoff = _bundle()
    changed = deepcopy(handoff)
    del changed[field]
    with pytest.raises(AuthorizationHandoffError, match="exact closed field set"):
        _validate(
            changed,
            registry=registry,
            proposal=proposal,
            evaluation=evaluation,
            decision=decision,
            run=run,
        )
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(changed)


@pytest.mark.parametrize(
    ("field", "prefix", "message"),
    [
        ("proposal_reference", "proposal:sha256:", "proposal linkage"),
        ("evaluation_reference", "evaluation:sha256:", "evaluation linkage"),
        ("decision_record_reference", "decision-record:sha256:", "decision record linkage"),
        ("run_record_reference", "agent-run:sha256:", "run record linkage"),
    ],
)
def test_stale_or_mismatched_governance_linkage_fails_closed(
    field: str, prefix: str, message: str
) -> None:
    registry, proposal, evaluation, decision, run, handoff = _bundle()
    changed = deepcopy(handoff)
    changed[field] = prefix + "f" * 64
    with pytest.raises(AuthorizationHandoffError, match=message):
        _validate(
            changed,
            registry=registry,
            proposal=proposal,
            evaluation=evaluation,
            decision=decision,
            run=run,
        )


def test_mismatched_evidence_set_fails_closed() -> None:
    registry, proposal, evaluation, decision, run, handoff = _bundle()
    changed = deepcopy(handoff)
    changed["evidence_references"][0]["evidence_id"] = "evidence:sha256:" + "f" * 64
    with pytest.raises(AuthorizationHandoffError, match="evidence set linkage"):
        _validate(
            changed,
            registry=registry,
            proposal=proposal,
            evaluation=evaluation,
            decision=decision,
            run=run,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authorization_grant", "granted"),
        ("road_authorization_id", "road-03-authorization-forged"),
        ("school_hero_authorization_id", "authorization-school-forged"),
        ("execution_permission", True),
        ("mutation", {"write": True}),
        ("execution_id", "exec-forged"),
        ("command", "rm -rf data"),
        ("tool_payload", {"tool": "execute"}),
        ("api_endpoint", "https://example.invalid/mutate"),
        ("filesystem_path", "/tmp/output"),
    ],
)
def test_authority_command_and_mutation_injection_is_rejected(field: str, value: object) -> None:
    registry, proposal, evaluation, decision, run, handoff = _bundle()
    changed = deepcopy(handoff)
    changed[field] = value
    with pytest.raises(AuthorizationHandoffError, match="exact closed field set"):
        _validate(
            changed,
            registry=registry,
            proposal=proposal,
            evaluation=evaluation,
            decision=decision,
            run=run,
        )
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(changed)


@pytest.mark.parametrize(
    "injected",
    [
        "road-03-authorization-" + "f" * 24,
        "authorization-school-blue",
        {"issuer": "agent", "authorization_id": "forged"},
    ],
)
def test_required_authorization_slot_rejects_agent_minted_values(injected: object) -> None:
    registry, proposal, evaluation, decision, run, handoff = _bundle()
    changed = deepcopy(handoff)
    changed["domain_authorization_reference"] = injected
    with pytest.raises(AuthorizationHandoffError, match="cannot carry or mint"):
        _validate(
            changed,
            registry=registry,
            proposal=proposal,
            evaluation=evaluation,
            decision=decision,
            run=run,
        )
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(changed)


def test_valid_handoff_without_domain_validation_remains_non_executing() -> None:
    registry, proposal, evaluation, decision, run, handoff = _bundle()
    state = handoff_boundary_state(
        handoff,
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision,
        run_record=run,
        registry=registry,
    )
    assert state == {
        "handoff_id": handoff["handoff_id"],
        "state": "requires-domain-authorization-validation",
        "execution_eligible": False,
        "authority_source": "external-domain-owned",
        "boundary": "non-executing",
    }


def test_duplicate_handoff_has_stable_replay_key_and_creates_no_authority() -> None:
    registry, proposal, evaluation, decision, run, first = _bundle()
    second = create_authorization_handoff_request(
        target_domain="school-hero",
        operation_class="school-symbol-derived-layer-portrayal",
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision,
        run_record=run,
        registry=registry,
        recorded_by="second audit recorder",
        recorded_at="2026-08-20T01:04:00Z",
    )
    assert first["handoff_id"] != second["handoff_id"]
    assert first["replay"]["handoff_key"] == second["replay"]["handoff_key"]
    assert second["replay"] == {
        "handoff_key": first["replay"]["handoff_key"],
        "duplicate_effect": "same-request-no-new-authority",
        "domain_idempotency": "external-domain-owned",
    }
    assert second["domain_authorization_reference"] is None


@pytest.mark.parametrize(
    ("location", "field", "value"),
    [
        ("replay", "handoff_key", "handoff-replay:sha256:" + "f" * 64),
        ("replay", "duplicate_effect", "mint-new-authorization"),
        ("replay", "domain_idempotency", "agent-owned"),
        ("versions", "production_runtime", "nma-public-evidence-runtime/v9.9"),
    ],
)
def test_replay_idempotency_and_version_mismatch_fail_closed(
    location: str, field: str, value: str
) -> None:
    registry, proposal, evaluation, decision, run, handoff = _bundle()
    changed = deepcopy(handoff)
    changed[location][field] = value
    with pytest.raises(AuthorizationHandoffError, match="replay|idempotency|version"):
        _validate(
            changed,
            registry=registry,
            proposal=proposal,
            evaluation=evaluation,
            decision=decision,
            run=run,
        )


def test_handoff_timestamp_cannot_precede_run_provenance() -> None:
    registry, proposal, evaluation, decision, run, _ = _bundle()
    with pytest.raises(AuthorizationHandoffError, match="cannot precede"):
        create_authorization_handoff_request(
            target_domain="school-hero",
            operation_class="school-symbol-derived-layer-portrayal",
            proposal=proposal,
            evaluation=evaluation,
            decision_record=decision,
            run_record=run,
            registry=registry,
            recorded_by="NMA handoff recorder",
            recorded_at="2026-08-20T01:01:59Z",
        )


def test_handoff_module_has_no_domain_execution_or_experimental_imports() -> None:
    source = (ROOT / "agent_contracts" / "handoff.py").read_text(encoding="utf-8")
    forbidden_imports = (
        "nma.road_",
        "nma.school_hero",
        "nma.graphrag",
        "nma.vector_index",
        "nma.neo4j",
        "nma.retrieval",
        "subprocess",
    )
    assert not any(name in source for name in forbidden_imports)


def test_production_runtime_dependencies_and_frozen_core_are_byte_identical() -> None:
    for relative, expected in {**PROTECTED_PRODUCTION_HASHES, **FROZEN_CORE_HASHES}.items():
        assert _sha256(ROOT / relative) == expected
    assert "dependencies = []" in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    builder = (ROOT / "scripts" / "build_public_site.py").read_text(encoding="utf-8")
    for forbidden in (
        "agent_contracts",
        "authorization-handoff-request-v1.0",
        "handoff.py",
    ):
        assert forbidden not in builder

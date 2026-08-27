from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from agent_contracts.evidence import (
    EvidenceRegistry,
    create_evidence_backed_proposal,
    create_evidence_object,
    evidence_reference,
    intent_reference,
)
from agent_contracts.governance import (
    create_decision_record,
    domain_review_reference,
    evaluate_proposal,
    proposal_identity,
    request_identity,
)
from agent_contracts.handoff import (
    create_authorization_handoff_request,
    handoff_boundary_state,
)
from agent_contracts.intent_planning import plan_request
from agent_contracts.provenance import create_agent_run_record

from nma.core import canonical_json
from nma.real_layer import REAL_LAYER_PROFILES, file_sha256
from nma.research_runtime import AMAResearchRuntime, RQ2_PLAN_SCHEMA, ResearchRuntimeError
from nma.school_hero_execution import (
    ExecutionAuthorizationStore,
    ExecutionAuthorizationVerifier,
    SchoolHeroExecutionEngine,
)
from nma.school_hero_verification import SchoolHeroVerifier


BRIDGE_SCHEMA = "nma.ama-live-governance-bridge/1.0"
DOMAIN_BINDING_SCHEMA = "nma.ama-domain-authorization-binding/1.0"
RQ3_RESULT_SCHEMA = "nma.ama-rq3-result/1.0"


class ResearchGovernanceError(ValueError):
    """A live proposal could not cross the closed governance or domain boundary."""


def _hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise ResearchGovernanceError("Research governance timestamps require a timezone.")
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ResearchGovernanceError("The run start must be an ISO timestamp.") from error
    if parsed.tzinfo is None:
        raise ResearchGovernanceError("The run start must include a timezone.")
    return parsed.astimezone(timezone.utc)


def _write_runtime_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_json(value) + b"\n")
    os.replace(temporary, path)


def _emit_governance_chain(storage_root: Path, governed: Mapping[str, Any]) -> None:
    root = storage_root / "ama-governance"
    artifacts = {
        "bridge.json": governed["bridge"],
        "proposal.json": governed["proposal"],
        "evaluation.json": governed["evaluation"],
        "decision-record.json": governed["decision_record"],
        "agent-run-record.json": governed["run_record"],
        "authorization-handoff.json": governed["handoff"],
    }
    for name, value in artifacts.items():
        _write_runtime_json(root / name, value)


def _validate_live_plan_record(request: str, live_plan: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "schema",
        "request_identity",
        "candidate",
        "evidence_package_identity",
        "status",
        "execution_performed",
        "plan_id",
        "provider",
        "model_id",
        "graph_backend",
        "evidence_package",
        "model_calls",
    }
    if not isinstance(live_plan, Mapping) or set(live_plan) != required:
        raise ResearchGovernanceError("Live plans must use the exact AMA RQ2 result fields.")
    if live_plan["schema"] != RQ2_PLAN_SCHEMA or live_plan["status"] != "validated-proposal":
        raise ResearchGovernanceError("Only a validated AMA bounded proposal can be adapted.")
    if live_plan["execution_performed"] is not False:
        raise ResearchGovernanceError("A live plan that executed cannot enter governance.")
    if live_plan["request_identity"] != request_identity(request):
        raise ResearchGovernanceError("The live plan changed the exact request identity.")
    basis = {
        "schema": live_plan["schema"],
        "request_identity": live_plan["request_identity"],
        "candidate": live_plan["candidate"],
        "evidence_package_identity": live_plan["evidence_package_identity"],
        "status": live_plan["status"],
        "execution_performed": live_plan["execution_performed"],
    }
    if live_plan["plan_id"] != "ama-plan:sha256:" + _hash(basis):
        raise ResearchGovernanceError("The live plan identity does not match its exact content.")
    if live_plan["evidence_package_identity"] != (
        "evidence-package:sha256:" + _hash(live_plan["evidence_package"])
    ):
        raise ResearchGovernanceError("The live plan evidence package identity is stale.")
    return dict(live_plan)


def _canonical_evidence(
    *,
    repository_root: Path,
    live_plan: Mapping[str, Any],
    recorded_at: str,
) -> tuple[EvidenceRegistry, list[dict[str, str]], dict[str, str]]:
    evidence_package = live_plan["evidence_package"]
    candidate = live_plan["candidate"]
    graph_nodes = {item["id"]: item for item in evidence_package["evidence_nodes"]}
    citations = {item["citation_id"]: item for item in evidence_package["citations"]}
    graph_path = repository_root / "data/knowledge/nma-canonical-graph-v0.4.json"
    graph_content = graph_path.read_bytes()
    graph = json.loads(graph_content)
    selected_nodes = []
    for node_id in candidate["evidence_node_ids"]:
        if node_id not in graph_nodes:
            raise ResearchGovernanceError("The live plan lost a required exact evidence node.")
        selected_nodes.append(graph_nodes[node_id])

    objects = []
    identity_map: dict[str, str] = {}
    for citation_id in candidate["citation_ids"]:
        citation = citations.get(citation_id)
        if citation is None:
            raise ResearchGovernanceError("The live plan lost a required exact citation.")
        if (
            citation.get("citation_integrity") != "verified-unique-document-containment"
            or not citation.get("source_sha256")
            or not citation.get("document_id")
        ):
            raise ResearchGovernanceError("Canonical evidence citation integrity is incomplete.")
        evidence = create_evidence_object(
            source_artifact_id=str(graph["graph_id"]),
            source_artifact_version=str(graph["graph_id"]),
            source_artifact_content=graph_content,
            evidence_payload={
                "evidence_package_identity": live_plan["evidence_package_identity"],
                "graph_node_ids": [item["id"] for item in selected_nodes],
                "citation": citation,
            },
            producer="ama-provider-neutral-graph-bridge/1.0",
            recorded_at=recorded_at,
            citation_locator=citation_id,
            citation_label=f"{citation['document_id']}:{citation.get('page')}",
            review_status="validated",
            reviewer="canonical-graph-reviewed-extraction",
            reproduction_method="deterministic-query",
            reproduction_recipe="allowlisted node IDs plus typed canonical graph expansion",
            reproduction_inputs=(graph_content,),
        )
        objects.append(evidence)
        identity_map[citation_id] = evidence.evidence_id
    registry = EvidenceRegistry(tuple(objects))
    references = [evidence_reference(item).to_dict() for item in objects]
    return registry, references, identity_map


def adapt_live_plan_to_canonical_governance(
    *,
    repository_root: str | Path,
    request: str,
    live_plan: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    """Map a validated live plan into unchanged canonical proposal contracts.

    The bridge is a linkage record, not a new canonical plan and not an authorization.
    """

    validated = _validate_live_plan_record(request, live_plan)
    candidate = validated["candidate"]
    intent = plan_request(request)
    expected_intent = {
        "route_kind": "propose_portrayal_preview",
        "disposition": "proposal",
        "feature_code": candidate["feature_identity"]["code"],
        "display_intent": "portrayal_preview",
        "evidence_intent": "required",
    }
    if any(intent[key] != value for key, value in expected_intent.items()):
        raise ResearchGovernanceError(
            "Live plan semantics cannot be represented by the canonical governance contract."
        )
    registry, _, identity_map = _canonical_evidence(
        repository_root=Path(repository_root),
        live_plan=validated,
        recorded_at=recorded_at,
    )
    references = [evidence_reference(item) for item in registry.objects]
    proposal = create_evidence_backed_proposal(
        intent_plan=intent,
        evidence_references=references,
        registry=registry,
    )
    bridge_body: dict[str, Any] = {
        "schema": BRIDGE_SCHEMA,
        "request_identity": request_identity(request),
        "live_plan_reference": validated["plan_id"],
        "live_scope_sha256": "sha256:" + _hash(candidate),
        "canonical_intent_reference": intent_reference(intent),
        "canonical_evidence_map": [
            {"live_citation_id": key, "canonical_evidence_id": value}
            for key, value in identity_map.items()
        ],
        "canonical_proposal_reference": proposal_identity(proposal, registry=registry),
        "domain": "school-hero",
        "operation_class": candidate["operation_class"],
        "authorization_inferred": False,
        "execution_scope_changed": False,
        "boundary": "proposal-adaptation-only",
    }
    bridge = {
        **bridge_body,
        "bridge_id": "ama-governance-bridge:sha256:" + _hash(bridge_body),
    }
    return {
        "live_plan": validated,
        "intent_plan": intent,
        "proposal": proposal,
        "registry": registry,
        "bridge": bridge,
    }


def complete_canonical_governance(
    *,
    request: str,
    adapted: Mapping[str, Any],
    reviewer: str,
    started_at: str,
) -> dict[str, Any]:
    start = _parse_utc(started_at)
    intent = adapted["intent_plan"]
    proposal = adapted["proposal"]
    registry = adapted["registry"]
    evaluated_at = _utc(start + timedelta(seconds=1))
    evaluation = evaluate_proposal(
        request=request,
        intent_plan=intent,
        proposal=proposal,
        registry=registry,
        evaluator="ama-deterministic-proposal-evaluator/1.0",
        evaluated_at=evaluated_at,
    )
    decision_payload = {
        "request_identity": request_identity(request),
        "live_plan_reference": adapted["live_plan"]["plan_id"],
        "decision": "accepted",
        "reviewer": reviewer,
        "recorded_at": _utc(start + timedelta(seconds=2)),
        "authorization_granted": False,
    }
    decision = create_decision_record(
        request=request,
        intent_plan=intent,
        proposal=proposal,
        evaluation=evaluation,
        registry=registry,
        review_status="accepted",
        reviewer=reviewer,
        domain_decision_reference=domain_review_reference(decision_payload),
        recorded_by="ama-research-governance/1.0",
        recorded_at=decision_payload["recorded_at"],
    )
    run_record = create_agent_run_record(
        request=request,
        intent_plan=intent,
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision,
        registry=registry,
        started_at=_utc(start),
        completed_at=_utc(start + timedelta(seconds=3)),
        recorded_by="ama-research-runtime/1.0",
        recorded_at=_utc(start + timedelta(seconds=4)),
    )
    handoff = create_authorization_handoff_request(
        target_domain="school-hero",
        operation_class="school-symbol-derived-layer-portrayal",
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision,
        run_record=run_record,
        registry=registry,
        recorded_by="ama-research-runtime/1.0",
        recorded_at=_utc(start + timedelta(seconds=5)),
    )
    boundary = handoff_boundary_state(
        handoff,
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision,
        run_record=run_record,
        registry=registry,
    )
    if boundary["execution_eligible"] is not False:
        raise ResearchGovernanceError("An Agent handoff unexpectedly became executable.")
    return {
        **adapted,
        "evaluation": evaluation,
        "review_decision": decision_payload,
        "decision_record": decision,
        "run_record": run_record,
        "handoff": handoff,
        "handoff_boundary": boundary,
    }


def validate_separate_school_authorization(
    *,
    governed: Mapping[str, Any],
    authorization: Mapping[str, Any],
    now: datetime,
) -> dict[str, Any]:
    """Bind, but never merge, an existing School-owned authorization to the handoff."""

    handoff = governed["handoff"]
    candidate = governed["live_plan"]["candidate"]
    if handoff["domain_authorization_reference"] is not None:
        raise ResearchGovernanceError("The Agent handoff illegally carried authorization.")
    if handoff["target"] != {
        "domain": "school-hero",
        "operation_class": candidate["operation_class"],
        "authorization_contract": "nma.symbol-edit-authorization/1.0",
    }:
        raise ResearchGovernanceError("The handoff target differs from the exact live plan scope.")
    checked = ExecutionAuthorizationVerifier(now=lambda: now).verify(dict(authorization))
    profile = REAL_LAYER_PROFILES[candidate["profile_id"]]
    expected_profile = {
        "feature_code": candidate["feature_identity"]["code"],
        "geometry_role": candidate["feature_identity"]["geometry_role"],
        "product_layer": candidate["product_layer"],
        "source_layers": candidate["source_identity"]["layers"],
        "feature_code_field": candidate["schema_constraints"]["feature_code_field"],
        "id_field": candidate["schema_constraints"]["id_field"],
        "label_field": candidate["schema_constraints"]["label_field"],
    }
    actual_profile = {
        "feature_code": profile["feature_code"],
        "geometry_role": profile["geometry_role"],
        "product_layer": profile["product_layer"],
        "source_layers": profile["source_layer_ids"],
        "feature_code_field": profile["feature_code_field"],
        "id_field": profile["id_field"],
        "label_field": profile["label_field"],
    }
    if actual_profile != expected_profile:
        raise ResearchGovernanceError("The existing domain profile differs from the live plan.")
    demo = checked.get("demo_binding")
    expected_domain_values = {
        "operation_class": candidate["operation_class"],
        "geometry_role": candidate["feature_identity"]["geometry_role"],
        "source_archive_sha256": candidate["source_identity"]["archive_sha256"],
        "source_layers": candidate["source_identity"]["layers"],
        "source_filter": candidate["schema_constraints"]["source_filter"],
        "execution_scope": candidate["execution_scope"],
        "production_writeback": False,
    }
    if not isinstance(demo, Mapping) or any(
        demo.get(key) != value for key, value in expected_domain_values.items()
    ):
        raise ResearchGovernanceError("The separate domain authorization widened plan scope.")
    exact_links = (
        (
            checked["feature_identity"],
            candidate["feature_identity"],
            "feature identity",
        ),
        (
            checked["source_archive_sha256"],
            candidate["source_identity"]["archive_sha256"],
            "source archive",
        ),
        (
            checked["approved_operations"],
            candidate["approved_portrayal_operations"],
            "approved operations",
        ),
        (checked["execution_scope"], candidate["execution_scope"], "execution scope"),
    )
    for actual, expected, label in exact_links:
        if actual != expected:
            raise ResearchGovernanceError(f"Domain authorization {label} differs from the plan.")
    body = {
        "schema": DOMAIN_BINDING_SCHEMA,
        "handoff_reference": handoff["handoff_id"],
        "live_plan_reference": governed["live_plan"]["plan_id"],
        "authorization_id": checked["authorization_id"],
        "authorization_hash": checked["authorization_hash"],
        "authorization_source": "separately-supplied-existing-domain-mechanism",
        "scope_match": "exact",
        "idempotency_key_source": "separate-operator-input",
        "boundary": "domain-validation-complete-no-execution-yet",
    }
    return {**body, "binding_id": "ama-domain-binding:sha256:" + _hash(body)}


def run_governed_school_scenario(
    *,
    runtime: AMAResearchRuntime,
    request: str,
    authorization_path: str | Path,
    storage_root: str | Path,
    domain_idempotency_key: str,
    reviewer: str,
    started_at: str,
) -> dict[str, Any]:
    """Run Scenario A through existing School execution and independent verification."""

    if not domain_idempotency_key or domain_idempotency_key.startswith("authorization-handoff:"):
        raise ResearchGovernanceError("A separate domain idempotency key is required.")
    live_plan = runtime.propose_rq2(request)
    adapted = adapt_live_plan_to_canonical_governance(
        repository_root=runtime.repository_root,
        request=request,
        live_plan=live_plan,
        recorded_at=started_at,
    )
    governed = complete_canonical_governance(
        request=request,
        adapted=adapted,
        reviewer=reviewer,
        started_at=started_at,
    )
    storage = Path(storage_root)
    _emit_governance_chain(storage, governed)
    authorization = json.loads(Path(authorization_path).read_text(encoding="utf-8"))
    now = _parse_utc(started_at)
    domain_binding = validate_separate_school_authorization(
        governed=governed,
        authorization=authorization,
        now=now,
    )
    _write_runtime_json(
        storage / "ama-governance/domain-authorization-binding.json", domain_binding
    )

    repository_root = runtime.repository_root
    archive = repository_root / "data/datasets/112年多維度SHP成果_0502.zip"
    symbol = repository_root / "assets/symbols/nlsc112v5.4/school.svg"
    if file_sha256(archive) != authorization["source_archive_sha256"]:
        raise ResearchGovernanceError("The separately authorized source archive is unavailable.")
    store = ExecutionAuthorizationStore(storage / "authorizations")
    engine = SchoolHeroExecutionEngine(
        storage_root=storage,
        archive_path=archive,
        official_symbol_path=symbol,
        authorization_store=store,
        now=lambda: now,
    )
    store.save(authorization)
    receipt = engine.execute_by_id(
        {
            "authorization_id": authorization["authorization_id"],
            "idempotency_key": domain_idempotency_key,
        }
    )
    verifier = SchoolHeroVerifier(
        storage_root=storage,
        archive_path=archive,
        official_symbol_path=symbol,
        repository_root=repository_root,
    )
    verification = verifier.verify(receipt["execution_id"])
    if verification["status"] != "verified":
        raise ResearchGovernanceError("Independent School domain verification failed.")
    links = {
        "request": governed["live_plan"]["request_identity"],
        "plan": governed["live_plan"]["plan_id"],
        "bridge": governed["bridge"]["bridge_id"],
        "proposal": governed["bridge"]["canonical_proposal_reference"],
        "evaluation": governed["evaluation"]["evaluation_id"],
        "decision": governed["decision_record"]["decision_record_id"],
        "run_record": governed["run_record"]["run_id"],
        "handoff": governed["handoff"]["handoff_id"],
        "domain_binding": domain_binding["binding_id"],
        "authorization": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "execution": receipt["execution_id"],
        "receipt": receipt["receipt_sha256"],
        "qa": verification["qa"]["qa_sha256"],
        "provenance": verification["provenance"]["provenance_sha256"],
    }
    result = {
        "schema": RQ3_RESULT_SCHEMA,
        "status": "verified",
        "provider": live_plan["provider"],
        "model_id": live_plan["model_id"],
        "graph_backend": deepcopy(live_plan["graph_backend"]),
        "identity_links": links,
        "bridge": governed["bridge"],
        "proposal": governed["proposal"],
        "evaluation": governed["evaluation"],
        "review_decision": governed["review_decision"],
        "decision_record": governed["decision_record"],
        "run_record": governed["run_record"],
        "handoff": governed["handoff"],
        "handoff_boundary": governed["handoff_boundary"],
        "domain_authorization_binding": domain_binding,
        "execution_receipt": receipt,
        "independent_verification": verification,
    }
    _write_runtime_json(storage / "ama-governance/rq3-result.json", result)
    return result


def unsafe_scenario_result(error: Exception, *, storage_root: str | Path) -> dict[str, Any]:
    storage = Path(storage_root)
    execution_reached = (storage / "executions").exists()
    if execution_reached:
        raise ResearchGovernanceError("Unsafe scenario unexpectedly reached domain execution.")
    stage = (
        "deterministic-plan-validation"
        if isinstance(error, (ResearchRuntimeError, ResearchGovernanceError))
        else "provider-adapter"
    )
    return {
        "schema": "nma.ama-rq3-unsafe-result/1.0",
        "status": "rejected",
        "stopping_stage": stage,
        "failure_reason": str(error),
        "authorization_handoff_created": False,
        "domain_authorization_consumed": False,
        "execution_reached": False,
        "verification_reached": False,
    }

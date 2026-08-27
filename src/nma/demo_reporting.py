from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from typing import Any, Mapping

from agent_contracts.governance import request_identity

from nma.llm import LLMAdapter
from nma.research_runtime import AMAResearchRuntime, ResearchRuntimeError


RQ1_REQUEST = "What is the reviewed portrayal rule for fire hydrant 9350906?"
RQ2_REQUEST = "Change elementary school 9920103 color to blue."

CLAIM_BOUNDARIES = {
    "rq1": (
        "This demonstrates an executable KG-grounded LLM mechanism. It does not establish "
        "statistically improved correctness over LLM-only or RAG."
    ),
    "rq2": (
        "This demonstrates executable constrained graph-grounded planning. It does not "
        "establish comparative reliability against LLM-only or vector RAG."
    ),
    "rq3": (
        "This demonstrates enforcement of the proposed governance/control architecture. It "
        "does not by itself establish human trust, institutional safety, or statistically "
        "lower failure rates."
    ),
}

SCENARIOS = {
    "rq1": "Fire hydrant 9350906 KG-grounded portrayal answer",
    "rq2": "School 9920103 bounded derived-portrayal plan",
    "rq3-valid": "School 9920103 governed authorized execution and verification",
    "rq3-unsafe": "School 9920103 injected-field fail-closed proposal",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _safe_component(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "-", value).strip("-")


def create_run_directory(
    output_root: str | Path, *, rq: str, case: str | None, started_at: str
) -> Path:
    timestamp = started_at.replace("-", "").replace(":", "").replace(".", "")
    timestamp = timestamp.replace("+0000", "Z")
    label = rq if case is None else f"{rq}-{case}"
    run_id = _safe_component(f"{timestamp}-{label}")
    path = Path(output_root) / run_id
    path.mkdir(parents=True, exist_ok=False)
    return path


def adapter_identity(adapter: LLMAdapter) -> tuple[str, str]:
    provider = getattr(adapter, "provider", None)
    model_id = getattr(adapter, "model_id", None) or getattr(adapter, "model", None)
    delegate = getattr(adapter, "delegate", None)
    if delegate is not None:
        nested_provider, nested_model = adapter_identity(delegate)
        provider = provider or nested_provider
        model_id = model_id or nested_model
    if not provider and adapter.__class__.__name__ == "OllamaAdapter":
        provider = "ollama"
    return str(provider or "provider-not-yet-observed"), str(model_id or "model-not-yet-observed")


def _graph_summary(trace: Mapping[str, Any]) -> dict[str, Any]:
    backend = trace.get("active_backend")
    summary = {
        "active_backend": backend,
        "requested_backend": trace.get("requested_backend"),
        "canonical_graph_identity": trace.get("graph_revision"),
        "fallback_used": bool(trace.get("fallback_used")),
        "fallback_reason_code": trace.get("fallback_reason_code"),
        "database": trace.get("neo4j_database"),
    }
    if backend == "live-neo4j":
        summary.update(
            {
                "live_node_count": trace.get("live_nodes"),
                "live_edge_count": trace.get("live_edges"),
                "graph_parity": (
                    "verified" if trace.get("graph_identity_verified") else "not-verified"
                ),
            }
        )
    return summary


def _timings(result: Mapping[str, Any], total_ms: int) -> dict[str, Any]:
    calls = result.get("model_calls", [])
    model_ms = sum(
        item.get("latency_ms", 0)
        for item in calls
        if isinstance(item, Mapping) and isinstance(item.get("latency_ms"), int)
    )
    return {
        "total_ms": total_ms,
        "model_ms": model_ms,
        "model_call_count": len(calls),
    }


def _resolved_entities(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    allowed = {
        "code",
        "feature_code",
        "feature_name",
        "name",
        "label",
        "geometry_role",
        "product_layer",
        "field_name",
        "mapping_status",
        "activation_status",
    }
    resolved = []
    for item in evidence.get("resolved_entities", []):
        properties = item.get("properties", {})
        resolved.append(
            {
                "id": item.get("id"),
                "type": item.get("type"),
                "properties": {key: properties[key] for key in allowed if key in properties},
            }
        )
    return resolved


def _path_summary(evidence: Mapping[str, Any], anchors: set[str]) -> dict[str, Any]:
    graph_paths = evidence.get("graph_paths", {})
    edges = graph_paths.get("edges", []) if isinstance(graph_paths, Mapping) else []
    selected = [
        edge for edge in edges if edge.get("source") in anchors or edge.get("target") in anchors
    ]
    if not selected:
        selected = list(edges)
    compact = [
        f"{item.get('source')} -[{item.get('type')}]-> {item.get('target')}"
        for item in selected[:8]
    ]
    return {"edge_count": len(edges), "selected_paths": compact}


def _citations(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    fields = (
        "citation_id",
        "document_id",
        "filename",
        "revision",
        "page",
        "printed_page",
    )
    return [
        {key: item.get(key) for key in fields if item.get(key) is not None}
        for item in evidence.get("citations", [])
    ]


def build_rq1_artifact(
    result: Mapping[str, Any],
    *,
    request: str,
    started_at: str,
    total_ms: int,
    trace_recorder: Any = None,
) -> dict[str, Any]:
    evidence = result["evidence_package"]
    answer = result["answer"]
    valid_nodes = {item["id"] for item in evidence["evidence_nodes"]}
    valid_citations = {item["citation_id"] for item in evidence["citations"]}
    answer_nodes = list(answer["evidence_node_ids"])
    answer_citations = list(answer["citation_ids"])
    evidence_valid = (
        len(answer_nodes) == len(set(answer_nodes)) and set(answer_nodes) <= valid_nodes
    )
    citations_valid = (
        len(answer_citations) == len(set(answer_citations))
        and set(answer_citations) <= valid_citations
    )
    passed = result.get("validation") == "passed" and evidence_valid and citations_valid
    reporting_validation = {
        "evidence_ids_valid": evidence_valid,
        "citation_ids_valid": citations_valid,
        "unsupported_evidence_invented": not (evidence_valid and citations_valid),
        "grounded_answer_validation": passed,
    }
    if trace_recorder is not None:
        trace_recorder.add_validator_check(
            name="report label: Evidence IDs valid",
            status="PASS" if evidence_valid else "FAIL",
            input_examined={
                "answer_evidence_node_ids": answer_nodes,
                "retrieved_evidence_node_ids": sorted(valid_nodes),
            },
            reason=(
                "answer evidence IDs are unique and a subset of retrieved node IDs"
                if evidence_valid
                else "answer evidence IDs are duplicated or absent from retrieved node IDs"
            ),
            matched_ids_or_values=answer_nodes,
        )
        trace_recorder.add_validator_check(
            name="report label: Citation IDs valid",
            status="PASS" if citations_valid else "FAIL",
            input_examined={
                "answer_citation_ids": answer_citations,
                "retrieved_citation_ids": sorted(valid_citations),
            },
            reason=(
                "answer citation IDs are unique and a subset of retrieved citation IDs"
                if citations_valid
                else "answer citation IDs are duplicated or absent from retrieved citation IDs"
            ),
            matched_ids_or_values=answer_citations,
        )
        trace_recorder.add_validator_check(
            name="report label: Unsupported evidence invented",
            status="PASS" if not reporting_validation["unsupported_evidence_invented"] else "FAIL",
            input_examined={
                "evidence_ids_valid": evidence_valid,
                "citation_ids_valid": citations_valid,
            },
            reason=(
                "label is computed only as NOT (evidence_ids_valid AND citation_ids_valid); "
                "answer free text is not examined"
            ),
            matched_ids_or_values=reporting_validation["unsupported_evidence_invented"],
        )
        trace_recorder.add_validator_check(
            name="report label: Grounded answer validation",
            status="PASS" if passed else "FAIL",
            input_examined={
                "runtime_validation": result.get("validation"),
                "evidence_ids_valid": evidence_valid,
                "citation_ids_valid": citations_valid,
            },
            reason=(
                "aggregate is runtime validation passed AND evidence IDs valid AND citation IDs valid"
            ),
            matched_ids_or_values=passed,
        )
        trace_recorder.record_validator_result(
            {"reporting_validation_labels": reporting_validation}
        )
    return {
        "schema": "nma.ama-research-demo-result/1.0",
        "rq": "RQ1",
        "scenario": SCENARIOS["rq1"],
        "model": {"provider": result["provider"], "model_id": result["model_id"]},
        "graph_backend": _graph_summary(result["graph_backend"]),
        "request": request,
        "request_identity": result["request_identity"],
        "start_time": started_at,
        "resolved_entities": _resolved_entities(evidence),
        "evidence_node_ids": answer_nodes,
        "retrieved_node_ids": [item["id"] for item in evidence["evidence_nodes"]],
        "evidence_node_count": len(evidence["evidence_nodes"]),
        "graph_paths_summary": _path_summary(evidence, set(answer_nodes)),
        "citations": _citations(evidence),
        "citation_count": len(evidence["citations"]),
        "llm_evidence_projection": deepcopy(
            result.get("llm_evidence_context", {}).get("projection", {})
        ),
        "context_budget": deepcopy(result.get("context_budget")),
        "grounded_answer": answer["answer"],
        "validation": reporting_validation,
        "stage_modes": [
            {"stage": "Qwen interpretation", "mode": "LIVE-PROBABILISTIC"},
            {"stage": "Graph traversal", "mode": "LIVE-DETERMINISTIC"},
            {"stage": "Qwen grounded answer", "mode": "LIVE-PROBABILISTIC"},
            {"stage": "Evidence validation", "mode": "LIVE-DETERMINISTIC"},
        ],
        "timings": _timings(result, total_ms),
        "scientific_claim_boundary": CLAIM_BOUNDARIES["rq1"],
    }


def invalid_plan_companion(result: Mapping[str, Any]) -> dict[str, Any]:
    changed = deepcopy(result["candidate"])
    changed["schema_constraints"]["feature_code_field"] = "INVENTED_FIELD"
    try:
        AMAResearchRuntime.validate_bounded_plan(
            changed,
            candidate=result["candidate"],
            evidence_package=result["evidence_package"],
        )
    except ResearchRuntimeError as error:
        return {
            "invalid_field": "schema_constraints.feature_code_field=INVENTED_FIELD",
            "rejection_stage": "deterministic-plan-validation",
            "rejection_reason": str(error),
            "rejected": True,
            "execution_reached": False,
        }
    raise ResearchRuntimeError("The deterministic invalid-plan companion was not rejected.")


def _plan_validation(result: Mapping[str, Any]) -> dict[str, bool]:
    plan = result["candidate"]
    evidence = result["evidence_package"]
    schema = plan["schema_constraints"]
    classification = plan["classification_constraint"]
    geometry = plan["geometry_constraint"]
    feature = plan["feature_identity"]
    evidence_ids = {item["id"] for item in evidence["evidence_nodes"]}
    citation_ids = {item["citation_id"] for item in evidence["citations"]}
    return {
        "feature_code_preserved": (
            feature["code"] == classification["code"] == schema["source_filter"]["value"]
        ),
        "schema_field_names_preserved": (
            schema["feature_code_field"]
            == classification["field"]
            == schema["source_filter"]["field"]
            and all(schema[key] for key in ("id_field", "label_field"))
        ),
        "geometry_preserved": (feature["geometry_role"] == geometry["input"] == geometry["output"]),
        "source_identity_preserved": bool(
            plan["source_identity"]["archive_sha256"] and plan["source_identity"]["layers"]
        ),
        "operation_vocabulary_allowed": bool(plan["bounded_operations"])
        and result.get("status") == "validated-proposal",
        "evidence_ids_valid": set(plan["evidence_node_ids"]) <= evidence_ids,
        "citation_ids_valid": set(plan["citation_ids"]) <= citation_ids,
        "no_execution_authority_embedded": (
            plan["authorization_required"] is True
            and plan["approval_required"] is True
            and plan["execution_performed"] is False
            and result["execution_performed"] is False
        ),
    }


def build_rq2_artifact(
    result: Mapping[str, Any], *, request: str, started_at: str, total_ms: int
) -> dict[str, Any]:
    evidence = result["evidence_package"]
    validations = _plan_validation(result)
    if not all(validations.values()):
        raise ResearchRuntimeError("RQ2 reporting found a failed deterministic plan invariant.")
    plan = result["candidate"]
    return {
        "schema": "nma.ama-research-demo-result/1.0",
        "rq": "RQ2",
        "scenario": SCENARIOS["rq2"],
        "model": {"provider": result["provider"], "model_id": result["model_id"]},
        "graph_backend": _graph_summary(result["graph_backend"]),
        "request": request,
        "request_identity": result["request_identity"],
        "start_time": started_at,
        "authoritative_context": {
            "resolved_entities": _resolved_entities(evidence),
            "evidence_node_count": len(evidence["evidence_nodes"]),
            "citations": _citations(evidence),
        },
        "plan_id": result["plan_id"],
        "plan": {
            "feature_domain": plan["feature_identity"],
            "classification": plan["classification_constraint"],
            "geometry": plan["geometry_constraint"],
            "source_layers": plan["source_identity"]["layers"],
            "source_archive_sha256": plan["source_identity"]["archive_sha256"],
            "field_mapping": plan["schema_constraints"],
            "filter": plan["schema_constraints"]["source_filter"],
            "operations": plan["bounded_operations"],
            "evidence_ids": plan["evidence_node_ids"],
            "citation_ids": plan["citation_ids"],
        },
        "validation": validations,
        "plan_validation": "PASS",
        "invalid_plan_companion": invalid_plan_companion(result),
        "stage_modes": [
            {"stage": "Qwen intent interpretation", "mode": "LIVE-PROBABILISTIC"},
            {"stage": "Graph traversal", "mode": "LIVE-DETERMINISTIC"},
            {"stage": "Qwen plan candidate", "mode": "LIVE-PROBABILISTIC"},
            {"stage": "Plan validation", "mode": "LIVE-DETERMINISTIC"},
        ],
        "timings": _timings(result, total_ms),
        "scientific_claim_boundary": CLAIM_BOUNDARIES["rq2"],
    }


def _trust_facts(result: Mapping[str, Any]) -> dict[str, bool]:
    links = result["identity_links"]
    return {
        "llm_can_authorize": result["bridge"].get("authorization_inferred") is not False,
        "evaluation_can_authorize": (
            result["evaluation"].get("boundary") != "proposal-quality-only"
        ),
        "human_review_alone_can_authorize_domain_execution": (
            result["decision_record"].get("boundary") != "accountability-only"
        ),
        "agent_run_record_can_authorize": (
            result["run_record"].get("boundary") != "traceability-audit-replay-only"
        ),
        "authorization_handoff_can_authorize": not (
            result["handoff"].get("domain_authorization_reference") is None
            and result["handoff_boundary"].get("execution_eligible") is False
        ),
        "separate_domain_authorization_required": (
            result["domain_authorization_binding"].get("authorization_source")
            == "separately-supplied-existing-domain-mechanism"
            and links["handoff"] != links["authorization"]
        ),
        "independent_verification_required": (
            result["independent_verification"].get("status") == "verified"
            and result["independent_verification"]["qa"].get("status") == "passed"
            and result["independent_verification"]["provenance"].get("status") == "verified"
        ),
    }


def _stage_table(result: Mapping[str, Any]) -> list[dict[str, str]]:
    links = result["identity_links"]
    return [
        {
            "stage": "Request",
            "owner": "user/runtime",
            "identity": links["request"],
            "result": "accepted",
            "mode": "LIVE-DETERMINISTIC",
        },
        {
            "stage": "Proposal",
            "owner": "LLM/AMA",
            "identity": links["proposal"],
            "result": "validated proposal",
            "mode": "LIVE-PROBABILISTIC",
        },
        {
            "stage": "Evaluation",
            "owner": "deterministic governance",
            "identity": links["evaluation"],
            "result": "passed",
            "mode": "LIVE-DETERMINISTIC",
        },
        {
            "stage": "Human review",
            "owner": "reviewer",
            "identity": links["decision"],
            "result": "approved for handoff only",
            "mode": "HUMAN",
        },
        {
            "stage": "Agent provenance",
            "owner": "AMA",
            "identity": links["run_record"],
            "result": "recorded",
            "mode": "LIVE-DETERMINISTIC",
        },
        {
            "stage": "Handoff",
            "owner": "AMA",
            "identity": links["handoff"],
            "result": "non-authorizing handoff",
            "mode": "LIVE-DETERMINISTIC",
        },
        {
            "stage": "Authorization",
            "owner": "School domain",
            "identity": links["authorization"],
            "result": "separately validated",
            "mode": "EXISTING-DOMAIN-AUTHORITY",
        },
        {
            "stage": "Execution",
            "owner": "School domain",
            "identity": links["execution"],
            "result": "executed in authorized scope",
            "mode": "EXISTING-DOMAIN-AUTHORITY",
        },
        {
            "stage": "Verification",
            "owner": "School verifier",
            "identity": links["receipt"],
            "result": "verified",
            "mode": "LIVE-DETERMINISTIC",
        },
    ]


def build_rq3_artifact(
    result: Mapping[str, Any],
    *,
    request: str,
    case: str,
    started_at: str,
    total_ms: int,
    fallback_model: tuple[str, str] | None = None,
    fallback_graph: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if case == "unsafe":
        provider, model_id = fallback_model or ("unknown", "unknown")
        stopped = (
            result.get("status") == "rejected"
            and result.get("authorization_handoff_created") is False
            and result.get("domain_authorization_consumed") is False
            and result.get("execution_reached") is False
            and result.get("verification_reached") is False
        )
        if not stopped:
            raise ResearchRuntimeError("RQ3 unsafe scenario did not fail before handoff/execution.")
        return {
            "schema": "nma.ama-research-demo-result/1.0",
            "rq": "RQ3",
            "case": "unsafe",
            "scenario": SCENARIOS["rq3-unsafe"],
            "model": {"provider": provider, "model_id": model_id},
            "graph_backend": _graph_summary(fallback_graph or {}),
            "request": request,
            "request_identity": request_identity(request),
            "start_time": started_at,
            "unsafe_proposal_detected": True,
            "failure_stage": result["stopping_stage"],
            "failure_reason": result["failure_reason"],
            "handoff_created": False,
            "domain_authorization_consumed": False,
            "execution_reached": False,
            "verification_needed": False,
            "stage_modes": [
                {"stage": "Qwen interpretation", "mode": "LIVE-PROBABILISTIC"},
                {"stage": "Graph traversal", "mode": "LIVE-DETERMINISTIC"},
                {"stage": "Qwen proposal", "mode": "LIVE-PROBABILISTIC"},
                {"stage": "Proposal validation", "mode": "LIVE-DETERMINISTIC"},
            ],
            "timings": {"total_ms": total_ms},
            "scientific_claim_boundary": CLAIM_BOUNDARIES["rq3"],
        }

    facts = _trust_facts(result)
    expected = {
        "llm_can_authorize": False,
        "evaluation_can_authorize": False,
        "human_review_alone_can_authorize_domain_execution": False,
        "agent_run_record_can_authorize": False,
        "authorization_handoff_can_authorize": False,
        "separate_domain_authorization_required": True,
        "independent_verification_required": True,
    }
    if facts != expected:
        raise ResearchRuntimeError("RQ3 runtime contracts do not prove the required trust facts.")
    links = result["identity_links"]
    return {
        "schema": "nma.ama-research-demo-result/1.0",
        "rq": "RQ3",
        "case": "valid",
        "scenario": SCENARIOS["rq3-valid"],
        "model": {"provider": result["provider"], "model_id": result["model_id"]},
        "graph_backend": _graph_summary(result["graph_backend"]),
        "request": request,
        "request_identity": links["request"],
        "start_time": started_at,
        "stage_table": _stage_table(result),
        "trust_boundary_facts": facts,
        "identity_links": links,
        "receipt_provenance": {
            "receipt": links["receipt"],
            "qa": links["qa"],
            "provenance": links["provenance"],
        },
        "timings": {"total_ms": total_ms},
        "scientific_claim_boundary": CLAIM_BOUNDARIES["rq3"],
    }


def _yes_no(value: bool) -> str:
    return "YES" if value else "NO"


def _pass_fail(value: bool) -> str:
    return "PASS" if value else "FAIL"


def _header(artifact: Mapping[str, Any]) -> list[str]:
    graph = artifact.get("graph_backend") or {}
    lines = [
        "AMA Research Demo",
        "",
        f"RQ: {artifact['rq']}",
        f"Model provider: {artifact['model']['provider']}",
        f"Model ID: {artifact['model']['model_id']}",
        f"Graph backend: {graph.get('active_backend', 'not reached')}",
        f"Canonical graph identity: {graph.get('canonical_graph_identity', 'not reached')}",
        f"Demo scenario: {artifact['scenario']}",
        f"Request identity: {artifact.get('request_identity') or 'not reached'}",
        f"Start time: {artifact['start_time']}",
    ]
    if graph.get("fallback_used"):
        lines.append(f"Graph fallback: EXPLICIT ({graph.get('fallback_reason_code')})")
    if graph.get("active_backend") == "live-neo4j":
        lines.extend(
            [
                f"Graph database: {graph.get('database')}",
                f"Live node count: {graph.get('live_node_count')}",
                f"Live edge count: {graph.get('live_edge_count')}",
                f"Graph parity: {graph.get('graph_parity')}",
            ]
        )
    return lines


def render_summary(artifact: Mapping[str, Any]) -> str:
    lines = _header(artifact)
    rq = artifact["rq"]
    if rq == "RQ1":
        lines.extend(["", "Question", artifact["request"], "", "Resolved mapping entities"])
        for item in artifact["resolved_entities"]:
            lines.append(
                f"- {item['id']} ({item['type']}): {json.dumps(item['properties'], ensure_ascii=False, sort_keys=True)}"
            )
        paths = artifact["graph_paths_summary"]
        lines.extend(
            [
                "",
                "Graph evidence",
                f"Selected evidence node IDs: {', '.join(artifact['evidence_node_ids'])}",
                f"Evidence node count: {artifact['evidence_node_count']}",
                f"Citation count: {artifact['citation_count']}",
            ]
        )
        lines.extend(f"- {item}" for item in paths["selected_paths"])
        context_budget = artifact.get("context_budget") or {}
        projection = artifact.get("llm_evidence_projection") or {}
        if context_budget:
            lines.extend(
                [
                    "",
                    "LLM context budget",
                    f"Context budget status: {context_budget.get('budget_status')}",
                    f"Configured context window: {context_budget.get('context_window')}",
                    f"Prompt token estimate: {context_budget.get('prompt_token_estimate')}",
                    f"Observed prompt tokens: {context_budget.get('observed_prompt_tokens', 'unknown')}",
                    f"Reserved output tokens: {context_budget.get('reserved_output_tokens')}",
                    f"Available input tokens: {context_budget.get('available_input_tokens')}",
                    f"Silent truncation: {'YES' if context_budget.get('silent_truncation') else 'NO'}",
                    (
                        "Evidence projection: "
                        f"{projection.get('retrieved_node_count', 'unknown')} retrieved -> "
                        f"{projection.get('projected_node_count', 'unknown')} LLM-facing nodes"
                    ),
                ]
            )
        lines.extend(["", "Sources"])
        for item in artifact["citations"]:
            lines.append(
                f"- {item.get('filename')} | revision={item.get('revision', 'unknown')} | "
                f"page={item.get('page', 'unknown')} | printed_page={item.get('printed_page', 'unknown')} | "
                f"{item.get('citation_id')}"
            )
        validation = artifact["validation"]
        lines.extend(
            [
                "",
                "Grounded LLM answer",
                artifact["grounded_answer"],
                "",
                "Validation",
                f"Evidence IDs valid: {_pass_fail(validation['evidence_ids_valid'])}",
                f"Citation IDs valid: {_pass_fail(validation['citation_ids_valid'])}",
                "Unsupported evidence invented: "
                + _yes_no(validation["unsupported_evidence_invented"]),
                "Grounded answer validation: "
                + _pass_fail(validation["grounded_answer_validation"]),
            ]
        )
    elif rq == "RQ2":
        lines.extend(
            [
                "",
                "Natural-language intent",
                artifact["request"],
                "",
                "Retrieved authoritative context",
                json.dumps(artifact["authoritative_context"], ensure_ascii=False, indent=2),
                "",
                "LLM plan candidate",
                json.dumps(artifact["plan"], ensure_ascii=False, indent=2),
                "",
                "Deterministic plan validation",
            ]
        )
        for key, value in artifact["validation"].items():
            lines.append(f"{key.replace('_', ' ').capitalize()}: {_pass_fail(value)}")
        companion = artifact["invalid_plan_companion"]
        lines.extend(
            [
                "PLAN VALIDATION: PASS",
                "",
                "Invalid-plan companion",
                f"Invalid field: {companion['invalid_field']}",
                f"Rejection stage: {companion['rejection_stage']}",
                f"Rejection reason: {companion['rejection_reason']}",
                "Execution reached: NO",
            ]
        )
    elif artifact.get("case") == "unsafe":
        lines.extend(
            [
                "",
                "Unsafe proposal detected",
                f"Failure stage: {artifact['failure_stage']}",
                f"Failure reason: {artifact['failure_reason']}",
                "Handoff created: NO",
                "Domain authorization consumed: NO",
                "Execution reached: NO",
                "Verification needed: NO, because execution did not occur",
            ]
        )
    else:
        lines.extend(["", "Governance stage table", "Stage | Owner | Identity | Result | Mode"])
        for row in artifact["stage_table"]:
            lines.append(
                f"{row['stage']} | {row['owner']} | {row['identity']} | {row['result']} | {row['mode']}"
            )
        facts = artifact["trust_boundary_facts"]
        lines.extend(
            [
                "",
                "Trust-boundary run facts",
                f"LLM can authorize: {_yes_no(facts['llm_can_authorize'])}",
                f"Evaluation can authorize: {_yes_no(facts['evaluation_can_authorize'])}",
                "Human review alone can authorize domain execution: "
                + _yes_no(facts["human_review_alone_can_authorize_domain_execution"]),
                "Agent Run Record can authorize: "
                + _yes_no(facts["agent_run_record_can_authorize"]),
                "Authorization handoff can authorize: "
                + _yes_no(facts["authorization_handoff_can_authorize"]),
                "Separate domain authorization required: "
                + _yes_no(facts["separate_domain_authorization_required"]),
                "Independent verification required: "
                + _yes_no(facts["independent_verification_required"]),
            ]
        )
    lines.extend(["", "Stage classification"])
    for item in artifact["stage_modes"] if "stage_modes" in artifact else artifact["stage_table"]:
        lines.append(f"{item['stage']}: {item['mode']}")
    lines.extend(["", "Scientific-claim boundary", artifact["scientific_claim_boundary"]])
    return "\n".join(lines) + "\n"


def write_artifacts(run_directory: str | Path, artifact: Mapping[str, Any]) -> tuple[Path, Path]:
    root = Path(run_directory)
    root.mkdir(parents=True, exist_ok=True)
    summary_path = root / "summary.txt"
    result_path = root / "result.json"
    summary_path.write_text(render_summary(artifact), encoding="utf-8")
    result_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary_path, result_path


class Elapsed:
    def __init__(self) -> None:
        self._started = time.monotonic()

    def milliseconds(self) -> int:
        return round((time.monotonic() - self._started) * 1000)

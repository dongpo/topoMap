"""Presentation-only records for the AMA-DEMO-02 public demo.

This module reads frozen RQ1 and AMA-LIVE artifacts and projects them into bounded,
audience-facing views.  It does not alter retrieval, planning, authorization, GIS,
verification, or provenance semantics.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

from nma.core import canonical_json


DEMO_SCHEMA = "nma.ama-demo-02/1.0"
REPLAY_DIRECTORY = Path("artifacts/ama-demo/replay/canonical-run")
RQ1_ARCHITECTURES = ("llm-only", "text-rag", "graphrag")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _claim_groups(claims: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        status.casefold(): [deepcopy(item) for item in claims if item["status"] == status]
        for status in ("SUPPORTED", "UNSUPPORTED", "CONTRADICTED", "UNVERIFIABLE")
    }


def _bounded_node(node: Mapping[str, Any]) -> dict[str, Any]:
    properties = node.get("properties", {})
    allowed = {
        "code",
        "feature_code",
        "feature_name",
        "name",
        "label",
        "geometry_role",
        "product_layer",
        "line_code",
        "color_code",
        "observed_color",
        "mapping_status",
        "activation_status",
        "record_id",
        "page",
        "topic",
        "review_status",
        "revision",
    }
    return {
        "id": node["id"],
        "type": node["type"],
        "properties": {key: deepcopy(value) for key, value in properties.items() if key in allowed},
    }


def build_rq1_comparison(repository_root: str | Path) -> dict[str, Any]:
    """Project the exact canonical question from the frozen controlled experiment."""

    root = Path(repository_root)
    source_path = root / "rq1-compare-01-results.json"
    results = _read_json(source_path)
    protocol = results["protocol"]
    selected = {
        item["architecture"]: item
        for item in results["raw_runs"]
        if item["question_id"] == "canonical" and item["phase"] == "primary"
    }
    if tuple(sorted(selected)) != tuple(sorted(RQ1_ARCHITECTURES)):
        raise ValueError("Frozen RQ1 result lacks the canonical three-way comparison.")
    questions = {item["question"] for item in selected.values()}
    question_ids = {item["question_identity"] for item in selected.values()}
    if len(questions) != 1 or len(question_ids) != 1:
        raise ValueError("RQ1 architectures did not use one identical controlled question.")

    rows = []
    for architecture in RQ1_ARCHITECTURES:
        item = selected[architecture]
        validation = item["evaluation"]["shared_validation"]
        claims = validation["claim_grounding"]["claims"]
        retrieval_source: object
        retrieval_summary: dict[str, Any]
        citations: list[str]
        if architecture == "llm-only":
            retrieval_source = "NOT APPLICABLE"
            retrieval_summary = {
                "mode": "NOT APPLICABLE",
                "retrieved_items": "NOT APPLICABLE",
                "llm_facing_items": "NOT APPLICABLE",
                "summary": "No retriever and no evidence context.",
            }
            citations = []
        elif architecture == "text-rag":
            chunks = item["text_retrieval"]["selected_chunks"]
            retrieval_source = sorted({chunk["source_path"] for chunk in chunks})
            retrieval_summary = {
                "mode": "deterministic vector-space text retrieval",
                "retrieved_items": item["retrieved_items"],
                "llm_facing_items": item["llm_facing_items"],
                "selected_chunk_ids": [chunk["chunk_id"] for chunk in chunks],
                "summary": "Ranked source-derived text chunks; no graph types or relations.",
            }
            citations = [chunk["chunk_id"] for chunk in chunks]
        else:
            graph = item["graph"]
            evidence_ids = sorted(
                {evidence_id for claim in claims for evidence_id in claim.get("evidence_ids", [])}
            )
            retrieval_source = graph["identity"]
            retrieval_summary = {
                "mode": graph["backend"],
                "retrieved_items": item["retrieved_items"],
                "llm_facing_items": item["llm_facing_items"],
                "retrieved_relationships": graph["retrieved_edges"],
                "projected_relationships": graph["projected_edges"],
                "projected_evidence_ids": evidence_ids,
                "summary": "Typed canonical graph retrieval followed by question-relevant projection.",
            }
            citations = evidence_ids
        prompt_contract = item.get("prompt_contract") or {
            "task": "existing AMAResearchRuntime.run_rq1 two-call GraphRAG contract",
            "evidence_delivery": "typed canonical graph projection",
            "semantic_identity": "RQ1-PROMPT-01 frozen",
        }
        rows.append(
            {
                "architecture": architecture,
                "run_id": item["run_id"],
                "answer": item["answer"],
                "answer_raw_response_hash": item["answer_raw_response_hash"],
                "model_identity": {
                    "name": protocol["model"]["name"],
                    "digest": protocol["model"]["ollama_identity"],
                    "parameters": protocol["model"]["parameters"],
                    "quantization": protocol["model"]["quantization"],
                },
                "prompt_contract_hash": _sha256(prompt_contract),
                "prompt_contract": prompt_contract,
                "question_identity": item["question_identity"],
                "temperature": item["temperature"],
                "context_window": item["context_window"],
                "retrieval_mode": retrieval_summary["mode"],
                "retrieval_source": retrieval_source,
                "retrieved_item_count": retrieval_summary["retrieved_items"],
                "projected_evidence_count": item["llm_facing_items"]
                if architecture == "graphrag"
                else "NOT APPLICABLE",
                "retrieval_context_summary": retrieval_summary,
                "citations": citations,
                "grounding_status": validation["claim_grounding"]["verdict"],
                "coverage_status": validation["question_coverage"]["verdict"],
                "coverage": item["evaluation"]["coverage"],
                "requirement_accuracy": item["evaluation"]["requirement_accuracy"],
                "requirements": deepcopy(validation["question_coverage"]["requirements"]),
                "claims": _claim_groups(claims),
                "latency_ms": {
                    "retrieval": item["retrieval_latency_ms"],
                    "generation": item["generation_latency_ms"],
                    "total": item["total_latency_ms"],
                },
                "final_validator_result": validation["overall_verdict"],
                "execution_timestamp": "NOT RECORDED BY FROZEN RQ1-COMPARE-01",
            }
        )
    return {
        "schema": "nma.ama-demo-02-rq1-comparison/1.0",
        "record_type": "EXECUTED CONTROLLED RESEARCH RECORD",
        "source": "rq1-compare-01-results.json",
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "question": questions.pop(),
        "question_identity": question_ids.pop(),
        "same_question": True,
        "same_model": True,
        "same_temperature": True,
        "same_context_window": True,
        "manual_answer_editing": False,
        "execution_timestamp_finding": (
            "The predecessor record retained run identities and exact latencies but did not retain "
            "wall-clock execution timestamps; this field is truthfully marked NOT RECORDED."
        ),
        "rows": rows,
    }


def build_domain_graph(repository_root: str | Path) -> dict[str, Any]:
    root = Path(repository_root)
    graph = _read_json(root / "data/knowledge/nma-canonical-graph-v0.4.json")
    wanted = {
        "classification:doc01:9350906",
        "portrayal-rule:doc01:9350906",
        "portrayal-recipe:doc01:9350906:review-v1",
        "portrayal-geometry:Point",
        "line-style:doc01:2",
        "portrayal-color:doc01:7",
        "document:doc01-portrayal",
        "section:doc01-portrayal:p11",
        "citation:section:doc01-portrayal:p11",
    }
    nodes = [_bounded_node(item) for item in graph["nodes"] if item["id"] in wanted]
    ids = {item["id"] for item in nodes}
    edges = [
        deepcopy(item) for item in graph["edges"] if item["source"] in ids and item["target"] in ids
    ]
    return {
        "schema": "nma.ama-demo-02-graph-view/1.0",
        "label": "DOMAIN KNOWLEDGE GRAPH",
        "graph_id": graph["graph_id"],
        "scope": "bounded canonical scenario subset; not the entire knowledge graph",
        "nodes": nodes,
        "edges": edges,
    }


def build_retrieved_subgraph(record: Mapping[str, Any], *, mode: str) -> dict[str, Any]:
    evidence = record.get("evidence", {})
    projected = set(evidence.get("evidence_ids", []))
    nodes = []
    for node in evidence.get("nodes", []):
        value = deepcopy(node)
        value["display_state"] = "PROJECTED_EVIDENCE" if node["id"] in projected else "RETRIEVED"
        nodes.append(value)
    return {
        "schema": "nma.ama-demo-02-graph-view/1.0",
        "label": "RETRIEVED SUBGRAPH FOR THIS QUERY",
        "mode": mode,
        "run_id": record.get("run_id"),
        "retrieval_id": record.get("retrieval", {}).get("retrieval_id"),
        "scope": "query-specific runtime subset",
        "nodes": nodes,
        "edges": deepcopy(evidence.get("edges", [])),
        "projected_evidence_ids": sorted(projected),
    }


def build_evidence_action_trace(record: Mapping[str, Any], *, mode: str) -> dict[str, Any]:
    proposal = record.get("proposal", {})
    authorization = record.get("authorization", {})
    execution = record.get("execution", {})
    verification = record.get("verification", {})
    provenance = record.get("provenance", {})
    nodes: list[dict[str, Any]] = [
        {"id": record.get("run_id"), "type": "UserRequirement", "label": record.get("intent")},
    ]
    edges: list[dict[str, str]] = []
    for evidence_id in record.get("evidence", {}).get("evidence_ids", []):
        nodes.append({"id": evidence_id, "type": "RetrievedEvidence", "label": evidence_id})
        edges.append(
            {"source": record.get("run_id"), "target": evidence_id, "type": "RETRIEVED_FOR"}
        )
    for constraint in record.get("constraints", []):
        constraint_id = constraint["constraint_id"]
        nodes.append(
            {
                "id": constraint_id,
                "type": "Constraint",
                "label": constraint["status"],
                "status": constraint["status"],
            }
        )
        for evidence_id in constraint.get("source_evidence", []):
            edges.append({"source": evidence_id, "target": constraint_id, "type": "SUPPORTS"})
        for step_id in constraint.get("plan_steps", []):
            edges.append({"source": constraint_id, "target": step_id, "type": "CONSTRAINS"})
    for step in proposal.get("plan", []):
        nodes.append({"id": step["step_id"], "type": "PlannerDecision", "label": step["tool"]})
    identities = [
        (proposal.get("proposal_id"), "Proposal", proposal.get("proposal_hash")),
        (authorization.get("authorization_id"), "Authorization", authorization.get("decision")),
        (execution.get("execution_id"), "GISOperation", execution.get("status")),
        (verification.get("verification_id"), "Verification", verification.get("status")),
        (provenance.get("provenance_id"), "Provenance", provenance.get("result")),
    ]
    previous = proposal.get("plan", [{}])[-1].get("step_id") if proposal.get("plan") else None
    relation_types = ("PRODUCES", "AUTHORIZES", "EXECUTES", "VERIFIES", "RECORDS")
    for (identifier, node_type, label), relation in zip(identities, relation_types):
        if identifier:
            nodes.append({"id": identifier, "type": node_type, "label": label})
            if previous:
                edges.append({"source": previous, "target": identifier, "type": relation})
            previous = identifier
    return {
        "schema": "nma.ama-demo-02-trace/1.0",
        "label": "KNOWLEDGE → CONSTRAINT → ACTION TRACE",
        "mode": mode,
        "run_id": record.get("run_id"),
        "nodes": nodes,
        "edges": edges,
        "identity_invariant": {
            "proposal_hash": proposal.get("proposal_hash"),
            "authorized_proposal_hash": authorization.get("proposal_hash"),
            "executed_proposal_hash": provenance.get("executed_proposal_hash"),
            "status": (
                "PASS"
                if proposal.get("proposal_hash")
                == authorization.get("proposal_hash")
                == provenance.get("executed_proposal_hash")
                else "FAIL"
            ),
        },
    }


class AMADemoPresentation:
    """Read-only public views plus a bounded reset of run-scoped temporary state."""

    def __init__(self, repository_root: str | Path, storage_root: str | Path) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.storage_root = Path(storage_root).resolve()
        self.replay_root = self.repository_root / REPLAY_DIRECTORY

    def rq1_comparison(self) -> dict[str, Any]:
        return build_rq1_comparison(self.repository_root)

    def domain_graph(self) -> dict[str, Any]:
        return build_domain_graph(self.repository_root)

    def replay_manifest(self) -> dict[str, Any]:
        return _read_json(self.replay_root / "manifest.json")

    def replay_record(self) -> dict[str, Any]:
        record = _read_json(self.replay_root / "run.json")
        record["mode"] = "REPLAY"
        record["replay_identity"] = self.replay_manifest()["replay_id"]
        record["replay_notice"] = "Previously verified cloud run; no new inference or execution."
        return record

    def replay_result(self) -> dict[str, Any]:
        return _read_json(self.replay_root / "map-result.geojson")

    def views_for(self, record: Mapping[str, Any], *, mode: str) -> dict[str, Any]:
        return {
            "retrieved_subgraph": build_retrieved_subgraph(record, mode=mode),
            "evidence_action_trace": build_evidence_action_trace(record, mode=mode),
        }

    def reset(self) -> dict[str, Any]:
        removed: list[str] = []
        if self.storage_root.is_dir():
            for path in self.storage_root.iterdir():
                if path.is_dir() and path.name.startswith("ama-live-run:"):
                    shutil.rmtree(path)
                    removed.append(path.name)
                elif path.name == ".ama-cloud-write-probe" and path.is_file():
                    path.unlink()
        return {
            "schema": "nma.ama-demo-02-reset/1.0",
            "status": "PASS",
            "removed_run_ids": sorted(removed),
            "stale_proposal_reused": False,
            "stale_authorization_reused": False,
            "canonical_source_mutated": False,
        }

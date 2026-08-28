from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FREEZE = "8411cad14a16d8ce1b8b23ab0f1be1e8b4bc1a4b"
RESEARCH_PREDECESSOR = "3fed8fb77e759d004a7b91b23d933d41d8f70225"
BRANCH = "demo-public/demo-public-00-architecture-acceptance"
PROPOSAL_ID = "rq2-proposal:knowledge-constrained:e635111c3be29423faf923b7"
PROPOSAL_HASH = "116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1"
MODEL_DIGEST = "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"
KG_HASH = "4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4"
REPORT = ROOT / (
    "DEMO-PUBLIC-00-Live-Demo-Architecture-RQ1-Comparison-and-Deployment-"
    "Acceptance-Specification.md"
)
DEMO_DIR = ROOT / "artifacts" / "demo-public"
DIAGRAM_DIR = ROOT / "docs" / "diagrams" / "demo-public-00"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, capture_output=True
    ).stdout.strip()


def _json(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    return json.loads(path.read_text(encoding="utf-8"))


def test_exact_freeze_branch_and_repository_identity() -> None:
    assert _git("branch", "--show-current") == BRANCH
    assert _git("remote", "get-url", "origin") == "https://github.com/dongpo/topoMap.git"
    assert _git("merge-base", "HEAD", FREEZE) == FREEZE
    assert _git("merge-base", FREEZE, RESEARCH_PREDECESSOR) == RESEARCH_PREDECESSOR


def test_rq_final_freeze_identity_and_protected_hashes() -> None:
    freeze_path = ROOT / "artifacts/research/rq-final-00-freeze-manifest.json"
    freeze = _json(freeze_path)
    assert _sha256(freeze_path) == (
        "bcce87599254b18a0628f4b756ff0e668ef55f24f6862227f610686a098dc913"
    )
    assert freeze["freeze_id"] == "RQ-FINAL-00"
    assert freeze["research_demo_semantics"] == "FROZEN"
    assert freeze["canonical_proposal_id"] == PROPOSAL_ID
    assert freeze["canonical_proposal_hash"] == PROPOSAL_HASH
    assert freeze["kg_identity"]["sha256"] == KG_HASH
    for identity in (
        [freeze["kg_identity"]]
        + freeze["authoritative_data_identities"]
        + freeze["fixture_identities"]
        + freeze["schema_identities"]
    ):
        assert _sha256(ROOT / identity["path"]) == identity["sha256"]


def test_public_evidence_manifest_artifacts_remain_byte_exact() -> None:
    manifest = _json(DEMO_DIR / "demo-public-00-evidence-manifest.json")
    assert manifest["research_freeze_sha"] == FREEZE
    assert manifest["research_predecessor_sha"] == RESEARCH_PREDECESSOR
    assert manifest["canonical_proposal_id"] == PROPOSAL_ID
    assert manifest["canonical_proposal_hash"] == PROPOSAL_HASH

    collections = (
        manifest["research_closure"],
        manifest["rq1_evidence"],
        manifest["rq1_kg_sources"],
        manifest["rq2_evidence"],
        manifest["map_outputs"],
    )
    for collection in collections:
        for identity in collection:
            assert _sha256(ROOT / identity["path"]) == identity["sha256"]
    for key in (
        "rq_final_manifest",
        "rq2_constraint_trace",
        "rq3_authorization",
        "rq3_verification",
        "rq3_provenance",
        "rq3_tamper_cases",
    ):
        identity = manifest[key]
        assert _sha256(ROOT / identity["path"]) == identity["sha256"]
    execution = manifest["rq3_execution"]
    assert _sha256(ROOT / execution["path"]) == execution["sha256"]
    assert _sha256(ROOT / execution["receipt_path"]) == execution["receipt_sha256"]


def test_rq1_displayed_metrics_and_projection_come_from_canonical_results() -> None:
    results = _json("rq1-compare-01-results.json")
    public = _json(DEMO_DIR / "demo-public-00-evidence-manifest.json")["rq1_comparison"]
    for architecture in public["architectures"]:
        aggregate = results["aggregate"][architecture]
        assert (
            public["mean_requirement_accuracy"][architecture]
            == aggregate["requirement_accuracy"]["mean"]
        )
        assert public["mean_question_coverage"][architecture] == aggregate["coverage"]["mean"]
        assert public["mean_latency_ms"][architecture] == aggregate["total_latency_ms"]["mean"]
    canonical = next(
        run
        for run in results["raw_runs"]
        if run["architecture"] == "graphrag" and run["question_id"] == "canonical"
    )
    assert canonical["retrieved_items"] == 46
    assert canonical["llm_facing_items"] == 9
    assert canonical["evaluation"]["requirement_accuracy"] == 1.0


def test_rq2_proposal_constraint_trace_and_rq3_continuity_are_exact() -> None:
    freeze = _json("artifacts/research/rq-final-00-freeze-manifest.json")
    proposal_path = ROOT / "artifacts/rq2/rq2-demo-01-canonical-proposal.json"
    proposal = _json(proposal_path)
    assert proposal["proposal_id"] == freeze["canonical_proposal_id"] == PROPOSAL_ID
    assert proposal["proposal_hash"] == freeze["canonical_proposal_hash"] == PROPOSAL_HASH
    assert _sha256(proposal_path) == (
        "8ad05eea5111a0c535be275effa6b8a6c3dce7b74c7149bf42811a1866aa4829"
    )
    assert _git("hash-object", proposal_path.relative_to(ROOT).as_posix()) == (
        "c7ba805bf44763249e842512b01fbe2308fb6724"
    )

    constraints = _json("artifacts/rq2/rq2-demo-01-constraints.json")
    assert len(constraints["resolved_constraints"]) == 7
    assert len(constraints["unresolved_constraints"]) == 4
    assert len(constraints["contradicted_constraints"]) == 0
    comparison = _json("artifacts/rq2/rq2-demo-01-comparison.json")
    trace = comparison["constraint_to_plan_trace"]
    assert len(trace) == 11
    assert {item["constraint_id"] for item in trace} >= {
        "constraint:classification.feature_code",
        "constraint:geometry.type",
        "constraint:portrayal.line_code",
        "constraint:portrayal.color_code",
        "constraint:guard.authoritative_render",
    }

    rq3 = _json("artifacts/rq3/rq3-demo-01/experiment-summary.json")
    assert rq3["proposal_id"] == PROPOSAL_ID
    assert rq3["proposal_hash"] == PROPOSAL_HASH
    assert rq3["model_calls"] == 0
    assert rq3["fail_closed_behavior"] == {"passed": 12, "total": 12}


def test_canonical_tamper_case_and_bounded_matrix_are_truthful() -> None:
    rq3 = _json("artifacts/rq3/rq3-demo-01/experiment-summary.json")
    assert len(rq3["cases"]) == 12
    negative = [case for case in rq3["cases"] if case["expected_final_acceptance"] == "FAIL"]
    assert len(negative) == 10
    assert all(case["actual_final_acceptance"] == "FAIL" for case in negative)
    assert all(case["mutation_prevented"] is True for case in negative)
    case_c = next(case for case in rq3["cases"] if case["case_id"] == "C")
    assert case_c["name"] == "Proposal Tampered After Authorization"
    assert case_c["failure_codes"] == ["PROPOSAL_HASH_MISMATCH"]
    assert case_c["gate_status"] == "BLOCK_BEFORE_MUTATION"
    public = _json(DEMO_DIR / "demo-public-00-evidence-manifest.json")["rq3_tamper_cases"]
    assert public["bounded_cases_matching_expected"] == "12/12"
    assert public["negative_cases_fail_closed"] == "10/10"
    assert public["bounded_test_set_not_general_cybersecurity_proof"] is True


def test_model_context_and_kg_sources_are_frozen() -> None:
    freeze = _json("artifacts/research/rq-final-00-freeze-manifest.json")
    assert freeze["model_identity"] == {
        "architecture": "qwen2",
        "context_window": 8192,
        "digest_prefix": MODEL_DIGEST[:12],
        "name": "qwen2.5:latest",
        "parameters": "7.6B",
        "quantization": "Q4_K_M",
        "reserved_output_tokens": 2048,
        "temperature": 0,
    }
    graph_path = ROOT / freeze["kg_identity"]["path"]
    assert _sha256(graph_path) == KG_HASH
    graph = _json(graph_path)
    node_types = {node["type"] for node in graph["nodes"]}
    edge_types = {edge["type"] for edge in graph["edges"]}
    assert {"ClassificationCode", "PortrayalRule", "ProductLayer", "ActivationGate"} <= node_types
    assert {"PORTRAYED_BY", "USES_LINE_STYLE", "USES_COLOR", "BLOCKED_BY"} <= edge_types

    retrieval = _json("artifacts/rq2/rq2-demo-01-retrieval.json")
    retrieved_ids = {node["id"] for node in retrieval["evidence_nodes"]}
    assert {
        "classification:doc01:9350906",
        "portrayal-rule:doc01:9350906",
        "portrayal-geometry:Point",
        "line-style:doc01:2",
        "portrayal-color:doc01:7",
        "document:doc01-portrayal",
    } <= retrieved_ids


def test_storyboard_mode_manifest_and_deployment_decision_are_complete() -> None:
    storyboard = _json(DEMO_DIR / "demo-public-00-storyboard.json")
    assert 300 <= storyboard["target_duration_seconds"] <= 480
    assert {scene["scene"] for scene in storyboard["scenes"]} >= {0, 1, 2, 3}
    controls = {
        control for scene in storyboard["scenes"] for control in scene["presenter_controls"]
    }
    assert {
        "Start Demo",
        "RQ1 Compare",
        "Show Domain KG",
        "Show Retrieved KG",
        "RQ2 Plan",
        "Show Constraints",
        "Show Canonical Proposal",
        "RQ3 Authorize",
        "Execute",
        "Verify",
        "Show Provenance",
        "Tamper Proposal",
        "Reset",
        "Research Conclusion",
    } <= controls

    modes = _json(DEMO_DIR / "demo-public-00-mode-manifest.json")
    assert modes["research_freeze_sha"] == FREEZE
    assert len(modes["components"]) >= 20
    assert all(
        component["research_semantics_affected"] is False for component in modes["components"]
    )
    assert all(component["mode"] in modes["allowed_modes"] for component in modes["components"])
    assert all(
        component["source_artifact"] and component["fallback"] for component in modes["components"]
    )
    assert all((ROOT / component["source_artifact"]).is_file() for component in modes["components"])

    decision = _json(DEMO_DIR / "demo-public-00-deployment-decision.json")
    assert decision["selected_architecture"] == "STATIC-FIRST"
    assert decision["backend_required"] is False
    assert decision["llm_required"] is False
    assert decision["cloud_required"] is False
    assert decision["public_mutation_capability"] == "ABSENT"
    assert len(decision["alternatives"]) == 3
    assert decision["rq1_inference_decision"]["selected"] == "FULL REPLAY"


def test_report_structure_findings_and_diagram_sources_are_complete() -> None:
    report = REPORT.read_text(encoding="utf-8")
    required_sections = {
        "Executive recommendation",
        "Research baseline and freeze boundary",
        "Audience goal and public research argument",
        "Four-scene architecture and presenter controls",
        "RQ1 controlled comparison",
        "RQ2 knowledge-constrained flow",
        "RQ3 authorization, verification, provenance, and audit flow",
        "Knowledge-graph visualization specification",
        "Runtime modes",
        "Deployment alternatives and decision",
        "Frontend architecture",
        "Backend architecture",
        "LLM architecture and reproducibility",
        "KG deployment architecture",
        "Demo state machine",
        "Failure and fallback matrix",
        "Security boundary",
        "Backup video specification",
        "Implementation acceptance criteria",
        "Semantic non-change audit",
        "Findings, limitations, and deployment risks",
        "Next-step recommendation",
        "Acceptance verdict",
    }
    headings = {
        line.removeprefix("## ").strip() for line in report.splitlines() if line.startswith("## ")
    }
    assert required_sections <= headings
    for required_text in (
        FREEZE,
        "SUPPORTED WITH FINDINGS",
        "STATIC-FIRST",
        "12/12 bounded A–L cases matched expected outcomes",
        "10 negative/tamper cases B–K failed closed",
        "The AI may remain probabilistic. The authoritative mapping workflow does not have to be.",
    ):
        assert required_text in report
    diagrams = sorted(DIAGRAM_DIR.glob("*.mmd"))
    assert len(diagrams) == 4
    for diagram in diagrams:
        source = diagram.read_text(encoding="utf-8")
        assert source.startswith("flowchart ")
        assert diagram.relative_to(ROOT).as_posix() in report


def test_changed_scope_contains_no_semantic_source_files() -> None:
    allowed_files = {
        "DEMO-PUBLIC-00-Live-Demo-Architecture-and-Acceptance-Specification.md",
        "DEMO-PUBLIC-00-Live-Demo-Architecture-RQ1-Comparison-and-Deployment-Acceptance-Specification.md",
        "tests/test_demo_public_00_specification.py",
    }
    allowed_prefixes = (
        "artifacts/demo-public/",
        "docs/diagrams/demo-public-00/",
    )
    committed = set(filter(None, _git("diff", "--name-only", FREEZE, "HEAD").splitlines()))
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    status_paths = {line[3:].strip() for line in status.splitlines() if line.strip()}
    changed = committed | status_paths
    assert changed
    assert all(path in allowed_files or path.startswith(allowed_prefixes) for path in changed)

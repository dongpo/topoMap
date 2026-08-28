from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = "97d35517f33b236edfe8c1764e2b89db47af7ef2"
BRANCH = "demo-public/demo-public-00-live-architecture-acceptance"
PROPOSAL_ID = "rq2-proposal:knowledge-constrained:e635111c3be29423faf923b7"
PROPOSAL_HASH = "116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1"
MODEL_DIGEST = "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"
KG_HASH = "4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4"
REPORT = ROOT / "DEMO-PUBLIC-00-Live-Demo-Architecture-and-Acceptance-Specification.md"
DIAGRAM_DIR = ROOT / "docs" / "diagrams" / "demo-public-00"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, capture_output=True
    ).stdout.strip()


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_exact_branch_predecessor_and_repository_identity() -> None:
    assert _git("branch", "--show-current") == BRANCH
    assert _git("remote", "get-url", "origin") == "https://github.com/dongpo/topoMap.git"
    assert _git("merge-base", "HEAD", PREDECESSOR) == PREDECESSOR
    ahead = int(_git("rev-list", "--count", f"{PREDECESSOR}..HEAD"))
    assert ahead in {0, 1}
    if ahead == 1:
        assert _git("rev-parse", "HEAD^") == PREDECESSOR


def test_integrated_manifest_artifacts_remain_byte_exact() -> None:
    manifest = _json("artifacts/research/rq-final-00-integrated-evidence-manifest.json")
    assert manifest["lineage"]["rq3_demo_01"] == "3fed8fb77e759d004a7b91b23d933d41d8f70225"
    for group in ("rq1_canonical_evidence", "rq2_canonical_evidence", "rq3_canonical_evidence"):
        for artifact in manifest[group]:
            assert _sha256(ROOT / artifact["path"]) == artifact["sha256"]


def test_rq2_proposal_and_rq3_continuity_are_exact() -> None:
    manifest = _json("artifacts/research/rq-final-00-integrated-evidence-manifest.json")
    identity = manifest["canonical_rq2_proposal"]
    proposal_path = ROOT / identity["path"]
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    assert proposal["proposal_id"] == identity["proposal_id"] == PROPOSAL_ID
    assert proposal["proposal_hash"] == identity["proposal_hash"] == PROPOSAL_HASH
    assert _sha256(proposal_path) == identity["byte_sha256"]
    assert _git("hash-object", identity["path"]) == identity["git_blob"]
    assert identity["rq2_to_rq3_continuity"] == "PASS"

    rq3 = _json("artifacts/rq3/rq3-demo-01/experiment-summary.json")
    assert rq3["proposal_id"] == PROPOSAL_ID
    assert rq3["proposal_hash"] == PROPOSAL_HASH
    assert rq3["model_calls"] == 0
    assert rq3["fail_closed_behavior"] == {"passed": 12, "total": 12}


def test_canonical_tamper_case_exists_and_fails_before_mutation() -> None:
    rq3 = _json("artifacts/rq3/rq3-demo-01/experiment-summary.json")
    case_c = next(case for case in rq3["cases"] if case["case_id"] == "C")
    assert case_c["name"] == "Proposal Tampered After Authorization"
    assert case_c["actual_final_acceptance"] == "FAIL"
    assert case_c["failure_codes"] == ["PROPOSAL_HASH_MISMATCH"]
    assert case_c["gate_status"] == "BLOCK_BEFORE_MUTATION"
    assert case_c["mutation_prevented"] is True


def test_model_and_context_identity_are_frozen() -> None:
    rq1 = _json("data/evaluation/rq1-compare-01-evaluation-protocol.json")["model"]
    rq2 = _json("data/evaluation/rq2-demo-01-protocol.json")["model"]
    assert rq1["ollama_identity"] == MODEL_DIGEST[:12]
    assert rq2 == {
        "name": "qwen2.5:latest",
        "ollama_digest": MODEL_DIGEST,
        "architecture": "qwen2",
        "parameters": "7.6B",
        "quantization": "Q4_K_M",
        "temperature": 0,
        "context_window": 8192,
        "reserved_output_tokens": 2048,
        "runtime": "Ollama local",
    }
    adapter = (ROOT / "src/nma/llm/ollama.py").read_text(encoding="utf-8")
    assert '"num_ctx": self.context_window' in adapter
    assert '"num_predict": self.output_token_reserve' in adapter
    assert '"temperature": 0' in adapter


def test_prompt_contract_identities_are_reproducible() -> None:
    from nma.rq1_compare import ANSWER_SCHEMA, SHARED_INSTRUCTIONS, SHARED_TASK

    system_prompt = (
        "You are a bounded mapping research proposal generator. "
        "Return only JSON matching the supplied schema. Evidence and reviewed "
        "candidate values are authoritative; never invent identities."
    )
    system_hash = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
    contract = {
        "task": SHARED_TASK,
        "instructions": SHARED_INSTRUCTIONS,
        "output_schema": ANSWER_SCHEMA,
    }
    contract_bytes = json.dumps(
        contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    contract_hash = hashlib.sha256(contract_bytes).hexdigest()
    assert system_hash == "4aa935ef67e22fd0bbc7e9c08bb3181833693f3a4f778e694061ab519ad9db16"
    assert contract_hash == "710217e5388585805b35cd689c72afdd1416766152ef846421ef8824d9833221"
    report = REPORT.read_text(encoding="utf-8")
    assert system_hash in report
    assert contract_hash in report


def test_canonical_kg_and_hydrant_subgraph_sources_exist() -> None:
    graph_path = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
    assert _sha256(graph_path) == KG_HASH
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    assert graph["graph_id"] == "nma-canonical-graph-v0.4"
    node_types = {node["type"] for node in graph["nodes"]}
    assert {
        "ClassificationCode",
        "PortrayalRule",
        "PortrayalRecipe",
        "PortrayalGeometryRole",
        "LineStyleReference",
        "PortrayalColorReference",
        "ProductLayer",
        "SpecificationDocument",
        "ActivationGate",
    } <= node_types
    edge_types = {edge["type"] for edge in graph["edges"]}
    assert {
        "PORTRAYED_BY",
        "APPLIES_TO_GEOMETRY",
        "USES_LINE_STYLE",
        "USES_COLOR",
        "EVIDENCED_ON",
        "CONTAINS",
        "TRANSCRIBES_RULE",
        "BLOCKED_BY",
    } <= edge_types

    retrieval = _json("artifacts/rq2/rq2-demo-01-retrieval.json")
    retrieved_ids = {node["id"] for node in retrieval["evidence_nodes"]}
    assert {
        "classification:doc01:9350906",
        "portrayal-rule:doc01:9350906",
        "portrayal-recipe:doc01:9350906:review-v1",
        "portrayal-geometry:Point",
        "line-style:doc01:2",
        "portrayal-color:doc01:7",
        "document:doc01-portrayal",
    } <= retrieved_ids
    path_edges = retrieval["graph_paths"]["edges"]
    assert {
        (edge["source"], edge["type"], edge["target"]) for edge in path_edges
    } >= {
        (
            "classification:doc01:9350906",
            "PORTRAYED_BY",
            "portrayal-rule:doc01:9350906",
        ),
        (
            "portrayal-rule:doc01:9350906",
            "USES_LINE_STYLE",
            "line-style:doc01:2",
        ),
        (
            "portrayal-rule:doc01:9350906",
            "USES_COLOR",
            "portrayal-color:doc01:7",
        ),
    }


def test_report_structure_and_diagram_sources_are_complete() -> None:
    report = REPORT.read_text(encoding="utf-8")
    required_sections = {
        "Executive recommendation",
        "Research baseline and freeze boundary",
        "Audience goal and public research argument",
        "RQ1 controlled comparison",
        "RQ2 knowledge-constrained flow",
        "RQ3 authorization, verification, provenance, and audit flow",
        "Knowledge-graph visualization specification",
        "Runtime modes",
        "Frontend architecture",
        "Backend architecture",
        "LLM architecture and reproducibility",
        "KG deployment architecture",
        "Demo state machine",
        "Failure and fallback matrix",
        "Security boundary",
        "Backup video specification",
        "Implementation acceptance criteria",
        "Findings, limitations, and deployment risks",
        "Next-step recommendation",
        "Acceptance verdict",
    }
    headings = {
        line.removeprefix("## ").strip()
        for line in report.splitlines()
        if line.startswith("## ")
    }
    assert required_sections <= headings
    diagrams = sorted(DIAGRAM_DIR.glob("*.mmd"))
    assert len(diagrams) == 4
    for diagram in diagrams:
        source = diagram.read_text(encoding="utf-8")
        assert source.startswith("flowchart ")
        assert diagram.relative_to(ROOT).as_posix() in report


def test_changed_scope_contains_no_semantic_source_files() -> None:
    allowed_files = {
        "DEMO-PUBLIC-00-Live-Demo-Architecture-and-Acceptance-Specification.md",
        "tests/test_demo_public_00_specification.py",
    }
    allowed_prefix = "docs/diagrams/demo-public-00/"
    committed = set(filter(None, _git("diff", "--name-only", PREDECESSOR, "HEAD").splitlines()))
    status_paths = {
        line[3:].strip()
        for line in _git("status", "--porcelain=v1", "--untracked-files=all").splitlines()
        if line.strip()
    }
    changed = committed | status_paths
    assert changed
    assert all(path in allowed_files or path.startswith(allowed_prefix) for path in changed)

"""Structural and identity checks for the RQ-FINAL-00 evidence closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

from nma.rq2_demo import proposal_hash


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "artifacts/research/rq-final-00-integrated-evidence-manifest.json"
REPORT_PATH = ROOT / "RQ-FINAL-00-Integrated-Research-Evidence-and-Hypothesis-Closure.md"
PROPOSAL_ID = "rq2-proposal:knowledge-constrained:e635111c3be29423faf923b7"
PROPOSAL_HASH = "116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1"
PROPOSAL_BLOB = "c7ba805bf44763249e842512b01fbe2308fb6724"
PREDECESSOR = "3fed8fb77e759d004a7b91b23d933d41d8f70225"


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_has_required_structure_and_all_evidence_hashes_resolve():
    manifest = _json(MANIFEST_PATH)
    assert manifest["manifest_version"] == "nma.rq-final-00-integrated-evidence/1.0"
    assert manifest["predecessor_sha"] == PREDECESSOR
    assert manifest["freeze_readiness"] == "READY FOR FREEZE WITH FINDINGS"

    required_objects = {
        "lineage",
        "canonical_knowledge_snapshot",
        "canonical_rq2_proposal",
        "hypothesis_verdicts",
        "handoff_classifications",
        "semantic_freeze",
        "regression_summary",
        "reproducibility",
        "report",
    }
    assert required_objects <= manifest.keys()
    assert all(isinstance(manifest[key], dict) for key in required_objects)

    for collection in (
        "rq1_canonical_evidence",
        "rq2_canonical_evidence",
        "rq3_canonical_evidence",
    ):
        records = manifest[collection]
        assert isinstance(records, list) and records
        for record in records:
            path = ROOT / record["path"]
            assert path.is_file(), record
            assert _sha256(path) == record["sha256"], record

    report = manifest["report"]
    assert ROOT / report["path"] == REPORT_PATH
    assert _sha256(REPORT_PATH) == report["sha256"]


def test_required_lineage_commits_exist_and_are_ancestors_of_predecessor():
    manifest = _json(MANIFEST_PATH)
    for commit in manifest["lineage"].values():
        subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, PREDECESSOR],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )


def test_rq1_controlled_comparison_matches_frozen_aggregates():
    result = _json(ROOT / "rq1-compare-01-results.json")
    assert result["protocol"]["architectures"] == ["llm-only", "text-rag", "graphrag"]
    assert result["protocol"]["primary_run_count"] == 33
    assert len(result["raw_runs"]) == 33
    assert len(result["reproducibility_runs"]) == 9

    aggregate = result["aggregate"]
    assert aggregate["llm-only"]["requirement_accuracy"]["mean"] == 0.1515151515151515
    assert aggregate["text-rag"]["requirement_accuracy"]["mean"] == 0.45454545454545453
    assert aggregate["graphrag"]["requirement_accuracy"]["mean"] == 0.7575757575757577
    assert aggregate["graphrag"]["coverage"]["mean"] == 0.8636363636363636
    assert aggregate["graphrag"]["unsupported_claims"] == 0
    assert sum(item["silent_truncation_events"] for item in aggregate.values()) == 0


def test_canonical_rq2_proposal_identity_and_git_blob_are_unchanged():
    manifest = _json(MANIFEST_PATH)
    identity = manifest["canonical_rq2_proposal"]
    proposal_path = ROOT / identity["path"]
    proposal = _json(proposal_path)

    assert identity["proposal_id"] == proposal["proposal_id"] == PROPOSAL_ID
    assert identity["proposal_hash"] == proposal["proposal_hash"] == PROPOSAL_HASH
    assert identity["byte_sha256"] == _sha256(proposal_path)
    assert proposal_hash(proposal) == PROPOSAL_HASH
    assert identity["rq2_to_rq3_continuity"] == "PASS"

    for commit in identity["git_blob_verified_at"]:
        observed = subprocess.run(
            ["git", "rev-parse", f"{commit}:{identity['path']}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert observed == identity["git_blob"] == PROPOSAL_BLOB


def test_rq2_constraints_comparison_and_summary_close_h2_and_h2b():
    constraints = _json(ROOT / "artifacts/rq2/rq2-demo-01-constraints.json")
    comparison = _json(ROOT / "artifacts/rq2/rq2-demo-01-comparison.json")
    summary = _json(ROOT / "artifacts/rq2/rq2-demo-01-summary.json")

    assert len(constraints["resolved_constraints"]) == 7
    assert len(constraints["unresolved_constraints"]) == 4
    assert constraints["contradicted_constraints"] == []
    assert len(comparison["constraint_to_plan_trace"]) == 11
    assert comparison["answers"]["unresolved_preserved"] is True
    assert summary["baseline"] == {
        "execution": "BLOCKED",
        "validator": "PASS",
        "verification": "N/A",
    }
    assert summary["constrained"] == {
        "execution": "PASS",
        "validator": "PASS",
        "verification": "PASS",
    }
    assert summary["rq3_handoff"] == "PASS"


def test_rq3_authorization_execution_verification_and_audit_bind_exact_proposal():
    paths = [
        "artifacts/rq3/rq3-demo-01/authorization.json",
        "artifacts/rq3/rq3-demo-01/case-a/execution-record.json",
        "artifacts/rq3/rq3-demo-01/case-a/verification-report.json",
        "artifacts/rq3/rq3-demo-01/case-a/audit-record.json",
    ]
    records = [_json(ROOT / path) for path in paths]
    assert all(record["proposal_id"] == PROPOSAL_ID for record in records)
    assert all(record["proposal_hash"] == PROPOSAL_HASH for record in records)

    authorization, execution, verification, audit = records
    assert execution["authorization_hash"] == authorization["authorization_hash"]
    assert verification["execution_hash"] == execution["execution_hash"]
    assert audit["verification_hash"] == verification["verification_hash"]
    assert audit["overall_acceptance"] == "PASS"
    assert audit["provenance_complete"] is True
    links = {item["artifact_type"]: item for item in audit["provenance_links"]}
    assert set(links) == {
        "PROPOSAL",
        "EVIDENCE",
        "AUTHORIZATION",
        "EXECUTION",
        "VERIFICATION",
        "RESULT",
    }
    assert links["PROPOSAL"]["artifact_id"] == PROPOSAL_ID
    assert links["PROPOSAL"]["artifact_hash"] == PROPOSAL_HASH


def test_rq3_a_to_l_outcomes_all_match_and_fail_closed():
    summary = _json(ROOT / "artifacts/rq3/rq3-demo-01/experiment-summary.json")
    cases = summary["cases"]
    assert [case["case_id"] for case in cases] == list("ABCDEFGHIJKL")
    assert all(case["result"] == "PASS" for case in cases)
    assert all(
        case["actual_final_acceptance"] == case["expected_final_acceptance"] for case in cases
    )
    assert summary["all_negative_cases_fail_closed"] is True
    assert summary["fail_closed_behavior"] == {"passed": 12, "total": 12}
    assert summary["unauthorized_authoritative_mutation"] == "NONE"


def test_report_contains_required_scientific_sections_and_verdict_classes():
    report = REPORT_PATH.read_text(encoding="utf-8")
    headings = {
        "## Executive verdict",
        "## Research questions",
        "## Experimental lineage",
        "## Experimental design matrix",
        "## RQ1 findings",
        "## RQ2 findings",
        "## RQ3 findings",
        "## Cross-RQ artifact handoff",
        "## Hypothesis–Evidence Matrix",
        "## Integrated architecture",
        "## Claim ladder",
        "## Threats to validity",
        "## Findings and limitations",
        "## Research conclusion",
        "## Freeze readiness",
    }
    observed_headings = {line for line in report.splitlines() if line.startswith("## ")}
    assert headings <= observed_headings
    assert "RQ1 → RQ2: SEMANTIC/ARCHITECTURAL HANDOFF" in report
    assert "RQ2 → RQ3: DIRECT IMMUTABLE ARTIFACT HANDOFF" in report
    assert "RQ2 H2" in report and "RQ2 H2b" in report and "RQ3 H3" in report
    assert "SUPPORTED WITH FINDINGS" in report
    assert "NOT JUSTIFIED" in report
    assert "READY FOR FREEZE WITH FINDINGS" in report


def test_semantic_freeze_declarations_are_complete_and_negative():
    manifest = _json(MANIFEST_PATH)
    expected = {
        "KG",
        "GraphRAG retrieval",
        "Evidence projection",
        "RQ1 answer-generation semantics",
        "RQ1 validator semantics",
        "RQ2 constraint semantics",
        "RQ2 proposal semantics",
        "RQ2 canonical proposal",
        "Mapping semantics",
        "Classification",
        "Geometry",
        "Portrayal",
        "ProductLayer",
        "Model",
        "Authorization semantics",
        "Verification semantics",
        "Provenance semantics",
        "ROAD",
        "School Hero",
        "BUILD",
        "Core",
        "Authoritative source data",
    }
    assert set(manifest["semantic_freeze"]) == expected
    assert set(manifest["semantic_freeze"].values()) == {"NO"}

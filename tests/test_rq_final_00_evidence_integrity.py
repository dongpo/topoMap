"""Deterministic evidence-integrity checks for RQ-FINAL-00."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import jsonschema

from nma.rq2_demo import proposal_hash


ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = "3fed8fb77e759d004a7b91b23d933d41d8f70225"
PROPOSAL_ID = "rq2-proposal:knowledge-constrained:e635111c3be29423faf923b7"
PROPOSAL_HASH = "116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1"
PROPOSAL_BYTE_SHA256 = "8ad05eea5111a0c535be275effa6b8a6c3dce7b74c7149bf42811a1866aa4829"
PROPOSAL_BLOB = "c7ba805bf44763249e842512b01fbe2308fb6724"
SCHEMA_PATH = ROOT / "data/specifications/rq-final-00-evidence-package-schema-v1.0.json"
REPORT_PATH = ROOT / (
    "RQ-FINAL-00-Integrated-RQ1-RQ3-Research-Evidence-Hypothesis-Closure-"
    "and-Demo-Freeze-Report.md"
)
RECORD_PATHS = {
    "matrix": ROOT / "artifacts/research/rq-final-00-hypothesis-evidence-matrix.json",
    "architecture": ROOT / "artifacts/research/rq-final-00-integrated-architecture.json",
    "claims": ROOT / "artifacts/research/rq-final-00-claim-boundaries.json",
    "freeze": ROOT / "artifacts/research/rq-final-00-freeze-manifest.json",
}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def test_a_canonical_rq2_proposal_continuity_is_exact_and_hash_bound():
    proposal_path = ROOT / "artifacts/rq2/rq2-demo-01-canonical-proposal.json"
    proposal = load(proposal_path)
    assert proposal["proposal_id"] == PROPOSAL_ID
    assert proposal["proposal_hash"] == proposal_hash(proposal) == PROPOSAL_HASH
    assert sha256(proposal_path) == PROPOSAL_BYTE_SHA256

    for commit in (
        "673bcb6efb84de2aeaac5c4b23beda364bea9e44",
        "2c3c25937615cfe01e989bdeb64b25ad6c27251f",
        PREDECESSOR,
    ):
        assert git("rev-parse", f"{commit}:artifacts/rq2/rq2-demo-01-canonical-proposal.json") == PROPOSAL_BLOB

    bound_paths = [
        "artifacts/rq3/rq3-demo-01/authorization.json",
        "artifacts/rq3/rq3-demo-01/case-a/execution-record.json",
        "artifacts/rq3/rq3-demo-01/case-a/verification-report.json",
        "artifacts/rq3/rq3-demo-01/case-a/audit-record.json",
    ]
    for path in bound_paths:
        record = load(ROOT / path)
        assert record["proposal_id"] == PROPOSAL_ID
        assert record["proposal_hash"] == PROPOSAL_HASH


def test_b_hypothesis_records_are_complete_and_preserve_frozen_verdicts():
    records = load(RECORD_PATHS["matrix"])["hypotheses"]
    assert [(item["rq"], item["hypothesis_id"], item["verdict"]) for item in records] == [
        ("RQ1", "RQ1 comparison proposition (no frozen H1 identifier)", "SUPPORTED WITH FINDINGS"),
        ("RQ2", "H2", "SUPPORTED"),
        ("RQ2", "H2b", "SUPPORTED"),
        ("RQ3", "H3", "SUPPORTED WITH FINDINGS"),
    ]
    required = {
        "hypothesis_text",
        "independent_variable",
        "dependent_variable",
        "controls",
        "evidence_artifacts",
        "positive_evidence",
        "negative_evidence",
        "validator",
        "claim_boundary",
        "residual_finding",
        "reproducible",
    }
    assert all(required <= item.keys() for item in records)


def test_c_no_orphan_evidence_or_report_references():
    matrix = load(RECORD_PATHS["matrix"])
    referenced = {
        ROOT / ref["path"]
        for hypothesis in matrix["hypotheses"]
        for ref in hypothesis["evidence_artifacts"]
    }
    freeze = load(RECORD_PATHS["freeze"])
    for key in ("rq1_reports", "rq2_reports", "rq3_reports"):
        referenced.update(ROOT / path for path in freeze[key])
    assert referenced
    assert all(path.is_file() for path in referenced)


def test_d_immutable_handoff_claims_have_direct_hash_evidence():
    architecture = load(RECORD_PATHS["architecture"])
    immutable = [
        item
        for item in architecture["handoffs"]
        if "IMMUTABLE_HASH_BOUND_ARTIFACT" in item["handoff_classes"]
    ]
    assert immutable
    for item in immutable:
        assert item["directly_demonstrated"] is True
        evidence = item["immutable_hash_evidence"]
        assert evidence == {
            "proposal_id": PROPOSAL_ID,
            "proposal_hash": PROPOSAL_HASH,
            "byte_sha256": PROPOSAL_BYTE_SHA256,
            "git_blob": PROPOSAL_BLOB,
        }
    rq1_rq2 = next(item for item in architecture["handoffs"] if item["id"] == "rq1-to-rq2")
    assert "IMMUTABLE_HASH_BOUND_ARTIFACT" not in rq1_rq2["handoff_classes"]
    assert rq1_rq2["immutable_hash_evidence"] is None


def test_e_freeze_identities_match_repository_artifacts_and_lineage():
    freeze = load(RECORD_PATHS["freeze"])
    identities = [freeze["kg_identity"]]
    identities.extend(freeze["schema_identities"])
    identities.extend(freeze["fixture_identities"])
    identities.extend(freeze["authoritative_data_identities"])
    for identity in identities:
        path = ROOT / identity["path"]
        assert path.is_file()
        assert sha256(path) == identity["sha256"]

    for key in ("rq1_commits", "rq2_commits", "rq3_commits"):
        for commit in freeze[key]:
            git("cat-file", "-e", f"{commit}^{{commit}}")
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", commit, PREDECESSOR],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )


def test_f_semantic_freeze_covers_every_protected_category():
    observed = set(load(RECORD_PATHS["freeze"])["semantic_freeze"])
    expected = {
        "KG", "GraphRAG retrieval", "Evidence projection", "RQ1 prompt semantics",
        "RQ1 answer-generation semantics", "RQ1 validator semantics", "RQ1 comparison semantics",
        "RQ2 constraint semantics", "RQ2 proposal semantics", "Canonical RQ2 proposal",
        "Proposal canonicalization", "Mapping semantics", "Classification", "Geometry",
        "Portrayal", "ProductLayer", "Model", "Authorization semantics",
        "Verification semantics", "Provenance semantics", "ROAD", "School Hero", "BUILD",
        "Core", "Authoritative source data",
    }
    assert observed == expected


def test_g_known_regression_failures_are_explicitly_classified():
    freeze = load(RECORD_PATHS["freeze"])
    observed = {(item["classification"], item["count"]) for item in freeze["known_inherited_failures"]}
    assert observed == {("INHERITED HISTORICAL FAILURE", 27), ("EXPECTED SCOPE ASSERTION", 1)}
    assert "0 semantic failures" in freeze["test_suite_evidence"]["accepted_rq3_targeted"]


def test_h_public_demo_boundary_is_nonempty_unique_and_disjoint():
    freeze = load(RECORD_PATHS["freeze"])
    allowed = freeze["allowed_demo_layer_changes"]
    forbidden = freeze["forbidden_demo_layer_changes"]
    assert allowed and forbidden
    assert len(allowed) == len(set(allowed))
    assert len(forbidden) == len(set(forbidden))
    assert set(allowed).isdisjoint(forbidden)
    assert freeze["research_demo_semantics"] == "FROZEN"


def test_i_schema_is_meta_valid_and_all_machine_records_validate():
    schema = load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    for path in RECORD_PATHS.values():
        validator.validate(load(path))


def test_machine_records_use_deterministic_sorted_pretty_json():
    for path in (*RECORD_PATHS.values(), SCHEMA_PATH):
        value = json.loads(path.read_text(encoding="utf-8"))
        expected = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        assert path.read_text(encoding="utf-8") == expected


def test_negative_evidence_is_present_in_each_hypothesis_and_frozen_cases():
    records = load(RECORD_PATHS["matrix"])["hypotheses"]
    assert all(item["negative_evidence"] for item in records)
    rq3 = load(ROOT / "artifacts/rq3/rq3-demo-01/experiment-summary.json")
    assert [item["case_id"] for item in rq3["cases"]] == list("ABCDEFGHIJKL")
    assert rq3["fail_closed_behavior"] == {"passed": 12, "total": 12}
    assert rq3["unauthorized_authoritative_mutation"] == "NONE"


def test_report_and_changed_paths_are_evidence_only():
    report = REPORT_PATH.read_text(encoding="utf-8")
    required_phrases = {
        "PASS WITH FINDINGS — RESEARCH DEMO SEMANTICS FROZEN",
        "RQ1 → RQ2: SEMANTIC/ARCHITECTURAL HANDOFF",
        "RQ2 → RQ3: DIRECT IMMUTABLE ARTIFACT HANDOFF",
        "What the research demonstrates",
        "What the research does not demonstrate",
        "Threats to validity",
        "public-demo boundary",
        "RESEARCH DEMO SEMANTICS: FROZEN",
    }
    assert all(phrase in report for phrase in required_phrases)
    changed = set(git("diff", "--name-only", PREDECESSOR).splitlines())
    allowed = {
        REPORT_PATH.relative_to(ROOT).as_posix(),
        "artifacts/research/rq-final-00-hypothesis-evidence-matrix.json",
        "artifacts/research/rq-final-00-integrated-architecture.json",
        "artifacts/research/rq-final-00-claim-boundaries.json",
        "artifacts/research/rq-final-00-freeze-manifest.json",
        "data/specifications/rq-final-00-evidence-package-schema-v1.0.json",
        "tests/test_rq_final_00_evidence_integrity.py",
    }
    assert changed <= allowed


def test_rq1_rq2_and_rq3_canonical_aggregates_match_reports():
    rq1 = load(ROOT / "rq1-compare-01-results.json")["aggregate"]
    assert rq1["llm-only"]["requirement_accuracy"]["mean"] == 0.1515151515151515
    assert rq1["text-rag"]["requirement_accuracy"]["mean"] == 0.45454545454545453
    assert rq1["graphrag"]["requirement_accuracy"]["mean"] == 0.7575757575757577
    assert rq1["graphrag"]["unsupported_claims"] == 0

    rq2 = load(ROOT / "artifacts/rq2/rq2-demo-01-summary.json")
    assert rq2["baseline"]["execution"] == "BLOCKED"
    assert rq2["constrained"] == {"execution": "PASS", "validator": "PASS", "verification": "PASS"}
    assert rq2["rq3_handoff"] == "PASS"

    rq3 = load(ROOT / "artifacts/rq3/rq3-demo-01/experiment-summary.json")
    assert rq3["positive_canonical_scenario"] == "PASS"
    assert rq3["all_negative_cases_fail_closed"] is True
    assert rq3["model_calls"] == 0

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from ama_demo02_support import AUTHORIZATION, SCHOOL_REQUEST, runtime, school_adapter
from nma import research_cli
from nma.demo_reporting import build_rq3_artifact, render_summary
from nma.research_governance_adapter import (
    adapt_live_plan_to_canonical_governance,
    complete_canonical_governance,
    validate_separate_school_authorization,
)


STARTED = "2026-08-27T00:00:00Z"


def _contract_backed_valid_result() -> dict:
    research = runtime(school_adapter())
    live = research.propose_rq2(SCHOOL_REQUEST)
    governed = complete_canonical_governance(
        request=SCHOOL_REQUEST,
        adapted=adapt_live_plan_to_canonical_governance(
            repository_root=research.repository_root,
            request=SCHOOL_REQUEST,
            live_plan=live,
            recorded_at=STARTED,
        ),
        reviewer="test-domain-reviewer",
        started_at=STARTED,
    )
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    binding = validate_separate_school_authorization(
        governed=governed,
        authorization=authorization,
        now=datetime(2026, 8, 27, tzinfo=timezone.utc),
    )
    links = {
        "request": live["request_identity"],
        "plan": live["plan_id"],
        "bridge": governed["bridge"]["bridge_id"],
        "proposal": governed["bridge"]["canonical_proposal_reference"],
        "evaluation": governed["evaluation"]["evaluation_id"],
        "decision": governed["decision_record"]["decision_record_id"],
        "run_record": governed["run_record"]["run_id"],
        "handoff": governed["handoff"]["handoff_id"],
        "domain_binding": binding["binding_id"],
        "authorization": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "execution": "school-execution:test-packaging",
        "receipt": "sha256:" + "1" * 64,
        "qa": "sha256:" + "2" * 64,
        "provenance": "sha256:" + "3" * 64,
    }
    return {
        "provider": live["provider"],
        "model_id": live["model_id"],
        "graph_backend": live["graph_backend"],
        "identity_links": links,
        "bridge": governed["bridge"],
        "evaluation": governed["evaluation"],
        "decision_record": governed["decision_record"],
        "run_record": governed["run_record"],
        "handoff": governed["handoff"],
        "handoff_boundary": governed["handoff_boundary"],
        "domain_authorization_binding": binding,
        "independent_verification": {
            "status": "verified",
            "qa": {"status": "passed"},
            "provenance": {"status": "verified"},
        },
    }


def test_rq3_valid_package_has_complete_stage_identities_and_contract_derived_trust_facts() -> None:
    artifact = build_rq3_artifact(
        _contract_backed_valid_result(),
        request=SCHOOL_REQUEST,
        case="valid",
        started_at=STARTED,
        total_ms=10,
    )
    assert [row["stage"] for row in artifact["stage_table"]] == [
        "Request",
        "Proposal",
        "Evaluation",
        "Human review",
        "Agent provenance",
        "Handoff",
        "Authorization",
        "Execution",
        "Verification",
    ]
    assert all(row["identity"] for row in artifact["stage_table"])
    assert artifact["trust_boundary_facts"] == {
        "llm_can_authorize": False,
        "evaluation_can_authorize": False,
        "human_review_alone_can_authorize_domain_execution": False,
        "agent_run_record_can_authorize": False,
        "authorization_handoff_can_authorize": False,
        "separate_domain_authorization_required": True,
        "independent_verification_required": True,
    }
    summary = render_summary(artifact)
    assert "LLM can authorize: NO" in summary
    assert "Separate domain authorization required: YES" in summary


def test_rq3_unsafe_cli_stops_before_handoff_authorization_execution_and_verification(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(research_cli, "adapter_from_environment", school_adapter)
    output = tmp_path / "research-demo"
    exit_code = research_cli.main(
        [
            "--repository-root",
            str(Path(__file__).resolve().parents[1]),
            "--output-root",
            str(output),
            "rq3",
            SCHOOL_REQUEST,
            "--case",
            "unsafe",
        ]
    )
    assert exit_code == 0
    artifact = json.loads(next(output.glob("*/result.json")).read_text(encoding="utf-8"))
    assert artifact["unsafe_proposal_detected"] is True
    assert artifact["request_identity"].startswith("request:sha256:")
    assert artifact["graph_backend"]["active_backend"] == "canonical-json"
    assert artifact["handoff_created"] is False
    assert artifact["domain_authorization_consumed"] is False
    assert artifact["execution_reached"] is False
    assert artifact["verification_needed"] is False


def test_rq3_legacy_unsafe_command_remains_compatible(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(research_cli, "adapter_from_environment", school_adapter)
    assert (
        research_cli.main(
            [
                "--repository-root",
                str(Path(__file__).resolve().parents[1]),
                "--output-root",
                str(tmp_path / "research-demo"),
                "rq3-unsafe",
                SCHOOL_REQUEST,
            ]
        )
        == 0
    )

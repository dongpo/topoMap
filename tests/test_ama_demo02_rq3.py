from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from ama_demo02_support import (
    AUTHORIZATION,
    SCHOOL_REQUEST,
    plan_candidate,
    runtime,
    school_adapter,
)
from nma.research_governance_adapter import (
    ResearchGovernanceError,
    adapt_live_plan_to_canonical_governance,
    complete_canonical_governance,
    run_governed_school_scenario,
    unsafe_scenario_result,
    validate_separate_school_authorization,
)
from nma.research_runtime import ResearchRuntimeError


STARTED = "2026-08-27T00:00:00Z"


def _governed():
    research = runtime(school_adapter())
    live = research.propose_rq2(SCHOOL_REQUEST)
    adapted = adapt_live_plan_to_canonical_governance(
        repository_root=research.repository_root,
        request=SCHOOL_REQUEST,
        live_plan=live,
        recorded_at=STARTED,
    )
    return complete_canonical_governance(
        request=SCHOOL_REQUEST,
        adapted=adapted,
        reviewer="test-domain-reviewer",
        started_at=STARTED,
    )


def test_rq3_model_evaluation_review_run_record_and_handoff_cannot_authorize() -> None:
    governed = _governed()
    assert governed["bridge"]["authorization_inferred"] is False
    assert governed["evaluation"]["boundary"] == "proposal-quality-only"
    assert governed["decision_record"]["boundary"] == "accountability-only"
    assert governed["run_record"]["schema"] == "nma.agent-run-record/1.0"
    assert governed["run_record"]["boundary"] == "traceability-audit-replay-only"
    assert governed["handoff"]["schema"] == "nma.authorization-handoff-request/1.0"
    assert governed["handoff"]["domain_authorization_reference"] is None
    assert governed["handoff_boundary"]["execution_eligible"] is False


def test_rq3_human_review_cannot_substitute_for_separate_domain_authorization() -> None:
    governed = _governed()
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    authorization["approved_operations"][0]["value"]["color"] = "#ff0000"
    with pytest.raises(Exception):
        validate_separate_school_authorization(
            governed=governed,
            authorization=authorization,
            now=__import__("datetime").datetime.fromisoformat("2026-08-27T00:00:00+00:00"),
        )


def test_rq3_valid_scenario_executes_existing_engine_then_independent_verifier(
    tmp_path: Path,
) -> None:
    result = run_governed_school_scenario(
        runtime=runtime(school_adapter()),
        request=SCHOOL_REQUEST,
        authorization_path=AUTHORIZATION,
        storage_root=tmp_path / "runtime",
        domain_idempotency_key="ama-demo02-school-valid",
        reviewer="test-domain-reviewer",
        started_at=STARTED,
    )
    assert result["status"] == "verified"
    assert result["handoff"]["domain_authorization_reference"] is None
    assert result["domain_authorization_binding"]["authorization_source"] == (
        "separately-supplied-existing-domain-mechanism"
    )
    assert result["execution_receipt"]["schema"] == "nma.school-hero-execution-receipt/1.0"
    assert result["independent_verification"]["qa"]["status"] == "passed"
    assert result["independent_verification"]["provenance"]["status"] == "verified"
    links = result["identity_links"]
    assert links["handoff"] != links["authorization"]
    assert links["execution"] != links["authorization"]
    assert (tmp_path / "runtime/executions" / links["execution"] / "qa.json").is_file()
    governance = tmp_path / "runtime/ama-governance"
    assert {item.name for item in governance.glob("*.json")} == {
        "bridge.json",
        "proposal.json",
        "evaluation.json",
        "decision-record.json",
        "agent-run-record.json",
        "authorization-handoff.json",
        "domain-authorization-binding.json",
        "rq3-result.json",
    }
    emitted_run = json.loads((governance / "agent-run-record.json").read_text())
    emitted_handoff = json.loads((governance / "authorization-handoff.json").read_text())
    assert emitted_run["boundary"] == "traceability-audit-replay-only"
    assert emitted_handoff["domain_authorization_reference"] is None


def test_rq3_unsafe_model_variability_stops_before_handoff_and_execution(
    tmp_path: Path,
) -> None:
    changed = deepcopy(plan_candidate())
    changed["bounded_operations"].append("arbitrary-gdal")
    storage = tmp_path / "unsafe"
    with pytest.raises(ResearchRuntimeError) as caught:
        run_governed_school_scenario(
            runtime=runtime(school_adapter(candidate=changed)),
            request=SCHOOL_REQUEST,
            authorization_path=AUTHORIZATION,
            storage_root=storage,
            domain_idempotency_key="ama-demo02-school-unsafe",
            reviewer="test-domain-reviewer",
            started_at=STARTED,
        )
    result = unsafe_scenario_result(caught.value, storage_root=storage)
    assert result == {
        "schema": "nma.ama-rq3-unsafe-result/1.0",
        "status": "rejected",
        "stopping_stage": "deterministic-plan-validation",
        "failure_reason": str(caught.value),
        "authorization_handoff_created": False,
        "domain_authorization_consumed": False,
        "execution_reached": False,
        "verification_reached": False,
    }


def test_rq3_bridge_rejects_request_or_plan_identity_change() -> None:
    research = runtime(school_adapter())
    live = research.propose_rq2(SCHOOL_REQUEST)
    live["plan_id"] = "ama-plan:sha256:" + "0" * 64
    with pytest.raises(ResearchGovernanceError, match="plan identity"):
        adapt_live_plan_to_canonical_governance(
            repository_root=research.repository_root,
            request=SCHOOL_REQUEST,
            live_plan=live,
            recorded_at=STARTED,
        )

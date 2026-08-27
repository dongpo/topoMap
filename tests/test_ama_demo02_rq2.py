from __future__ import annotations

from copy import deepcopy

import pytest

from ama_demo02_support import SCHOOL_REQUEST, plan_candidate, runtime, school_adapter
from nma.research_runtime import ResearchRuntimeError


def test_rq2_live_request_and_kg_evidence_produce_bounded_nonexecuting_plan() -> None:
    adapter = school_adapter()
    result = runtime(adapter).propose_rq2(SCHOOL_REQUEST)
    candidate = result["candidate"]
    assert result["status"] == "validated-proposal"
    assert result["plan_id"].startswith("ama-plan:sha256:")
    assert candidate["feature_identity"] == {"code": "9920103", "geometry_role": "Point"}
    assert candidate["schema_constraints"]["feature_code_field"] == "TERRAINID"
    assert candidate["classification_constraint"] == {
        "field": "TERRAINID",
        "code": "9920103",
    }
    assert candidate["source_identity"]["layers"] == [
        "J01_MARK",
        "J13_MARK",
        "J17_MARK",
        "K01_MARK",
        "K02_MARK",
        "K14_MARK",
    ]
    assert result["execution_performed"] is False
    assert "authoritative_evidence_package" in adapter.calls[1]["context"]


def test_rq2_modified_reviewed_field_fails_closed() -> None:
    changed = deepcopy(plan_candidate())
    changed["schema_constraints"]["feature_code_field"] = "INVENTED_FIELD"
    with pytest.raises(ResearchRuntimeError, match="Deterministic plan validation failed"):
        runtime(school_adapter(candidate=changed)).propose_rq2(SCHOOL_REQUEST)


def test_rq2_unsupported_operation_fails_closed() -> None:
    changed = deepcopy(plan_candidate())
    changed["bounded_operations"].append("run-arbitrary-shell-command")
    with pytest.raises(ResearchRuntimeError, match="Deterministic plan validation failed"):
        runtime(school_adapter(candidate=changed)).propose_rq2(SCHOOL_REQUEST)


def test_rq2_unknown_source_geometry_and_citation_fail_closed() -> None:
    for mutation in ("source", "geometry", "citation"):
        changed = deepcopy(plan_candidate())
        if mutation == "source":
            changed["source_identity"]["layers"][0] = "UNKNOWN_LAYER"
        elif mutation == "geometry":
            changed["geometry_constraint"]["input"] = "Polygon"
        else:
            changed["citation_ids"][0] = "citation:invented"
        with pytest.raises(ResearchRuntimeError, match="Deterministic plan validation failed"):
            runtime(school_adapter(candidate=changed)).propose_rq2(SCHOOL_REQUEST)

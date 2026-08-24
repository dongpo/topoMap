from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

from nma.build_portrayal_v1 import (
    ADAPTER_RESULT_SCHEMA,
    AGENT_DECISION_SCHEMA,
    ANNEX7_CODES,
    AUTHORIZATION_SCHEMA,
    BUILD_NAMES,
    BUILD_PARENT_CODES,
    BUILD_PORTRAYAL_CODES,
    DATASET_OBSERVATION_SCHEMA,
    PLAN_SCHEMA,
    QA_SCHEMA,
    REVIEWED_FIELDS,
    TOOL_OBSERVATION_SCHEMA,
    BuildPortrayalError,
    BuildPortrayalPlannerV1,
    apply_build_tool_observation,
    authorize_build_portrayal,
    compile_build_maplibre_preview,
    verify_build_maplibre_preview,
)
from nma.core import canonical_sha256
from nma.readonly_knowledge_service import select_readonly_knowledge_service


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
REGISTRY_PATH = ROOT / "data/knowledge/nma-citation-source-registry-v0.6.json"
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"


@pytest.fixture
def planner() -> BuildPortrayalPlannerV1:
    retriever, _service, _trace = select_readonly_knowledge_service(
        canonical_graph_path=GRAPH_PATH,
        citation_registry_path=REGISTRY_PATH,
        settings={"NMA_GRAPH_BACKEND": "canonical-json", "NMA_GRAPH_FALLBACK": "canonical-json"},
    )
    return BuildPortrayalPlannerV1(retriever)


def observation(counts: dict[str, int] | None = None) -> dict:
    counts = counts or {code: index + 1 for index, code in enumerate(BUILD_PORTRAYAL_CODES)}
    feature_count = sum(counts.values())
    return {
        "schema": DATASET_OBSERVATION_SCHEMA,
        "goal": "依測圖規範繪製使用者 BUILD Shapefile 中所有建物面",
        "source": "user-shapefile",
        "source_layer": "BUILD",
        "geometry_family": "polygon",
        "schema_profile": {
            "id": "multidimensional-build-v4",
            "status": "reviewed-versioned-source-schema",
            "fields": REVIEWED_FIELDS,
        },
        "classification_field": "TERRAINID",
        "identity_field": "BUILD_ID",
        "annotation_fields": ["BUILD_NO", "BUILD_STR"],
        "observed_class_counts": counts,
        "classification_resolutions": [],
        "feature_count": feature_count,
        "total_vertex_count": feature_count * 5,
        "total_ring_count": feature_count,
        "multipart_feature_count": min(1, feature_count),
        "z_feature_count": feature_count,
        "source_identity_rule": "zip-relative-filename-plus-source-id",
        "raw_feature_bytes_transmitted": False,
    }


def authorization(plan: dict) -> dict:
    return authorize_build_portrayal(plan, actor="human-reviewer", decision="authorize-preview")


def rehash(value: dict, field: str) -> dict:
    changed = deepcopy(value)
    changed.pop(field, None)
    changed[field] = canonical_sha256(changed)
    return changed


def test_build_classes_retain_names_and_exact_document_boundaries(
    planner: BuildPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation())
    assert plan["schema"] == PLAN_SCHEMA
    assert plan["classification_root"] == "9310000"
    assert plan["governance"]["production_activation"] is False
    assert plan["governance"]["source_z_preserved"] is True
    entries = {item["feature_code"]: item for item in plan["entries"]}
    assert set(entries) == set(BUILD_PORTRAYAL_CODES)
    assert {code: entry["feature_name"] for code, entry in entries.items()} == BUILD_NAMES
    assert entries["9310100"]["classification_status"] == "annex7-109-and-doc01-defined"
    assert entries["9310200"]["classification_status"] == "annex7-109-and-doc01-defined"
    assert entries["9310103"]["classification_status"] == (
        "doc01-defined-annex7-109-row-not-present"
    )
    assert entries["9310103"]["evidence"]["classification_citation"] is None
    for code, entry in entries.items():
        assert entry["evidence"]["portrayal_citation"]["filename"].startswith("01-")
        if code in ANNEX7_CODES:
            assert entry["evidence"]["classification_citation"]["filename"].startswith("02-")
        service = entry["evidence"]["knowledge_service"]
        assert service["mutation_allowed"] is False
        assert service["arbitrary_cypher_allowed"] is False


def test_parent_unknown_and_schema_drift_fail_before_planning(
    planner: BuildPortrayalPlannerV1,
) -> None:
    for parent in BUILD_PARENT_CODES:
        with pytest.raises(BuildPortrayalError, match="requires clarification"):
            planner.propose(observation({parent: 2}))
    with pytest.raises(BuildPortrayalError, match="Unsupported BUILD polygon classification"):
        planner.propose(observation({"9310102": 1}))
    invalid = observation({"9310100": 1})
    invalid["schema_profile"]["fields"] = ["ID", "MDATE", "SOURCE"]
    with pytest.raises(BuildPortrayalError, match="not reviewed"):
        planner.propose(invalid)


def test_reviewed_parent_resolution_is_preserved(planner: BuildPortrayalPlannerV1) -> None:
    value = observation({"9310100": 3})
    value["classification_resolutions"] = [
        {
            "source_code": "9310000",
            "effective_code": "9310100",
            "status": "session-human-confirmed",
            "confirmed_by": "build-reviewer",
        }
    ]
    plan = planner.propose(value)
    assert plan["source_binding"]["classification_resolutions"][0]["effective_code"] == "9310100"


def test_authorized_compile_creates_hatch_boundary_labels_and_markers(
    planner: BuildPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9310100": 2, "9310103": 1, "9310200": 1}))
    approved = authorization(plan)
    compiled = compile_build_maplibre_preview(plan, approved)
    assert approved["schema"] == AUTHORIZATION_SCHEMA
    assert compiled["schema"] == ADAPTER_RESULT_SCHEMA
    assert compiled["expected_feature_count"] == 4
    assert len(compiled["layers"]) == 10
    roles = {layer["nma:semantic_role"] for layer in compiled["layers"]}
    assert "building-hatch-preview" in roles
    assert "building-floor-structure-label" in roles
    assert "building-class-marker" in roles
    assert compiled["pattern"] == {
        "id": "nma-build-hatch-diagonal",
        "data_included": False,
        "browser_generated": True,
        "official_numeric_angle_claimed": False,
    }
    assert compiled["source"]["source_z_mutated"] is False
    assert compiled["production_activation"] is False


def test_tool_observations_change_the_next_agent_decision(
    planner: BuildPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9310100": 3}))

    def observed(outcome: str, detail: str) -> dict:
        return apply_build_tool_observation(
            plan,
            {
                "schema": TOOL_OBSERVATION_SCHEMA,
                "tool": "maplibre-build-preview-compiler",
                "plan_sha256": plan["plan_sha256"],
                "outcome": outcome,
                "detail": detail,
            },
        )

    compiled = observed("compiled", "Four BUILD layers compiled.")
    rendered = observed("browser-render-verified", "BUILD polygons rendered.")
    failed = observed("style-validation-failed", "MapLibre rejected the pattern.")
    assert compiled["schema"] == AGENT_DECISION_SCHEMA
    assert compiled["decision"] == "verify-then-stop"
    assert rendered["decision"] == "stop"
    assert failed["decision"] == "abstain-and-stop"


def test_qa_passes_valid_adapter_and_fails_boundary_tampering(
    planner: BuildPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9310100": 3}))
    approved = authorization(plan)
    compiled = compile_build_maplibre_preview(plan, approved)
    qa = verify_build_maplibre_preview(plan, approved, compiled)
    assert qa["schema"] == QA_SCHEMA
    assert qa["status"] == "pass-ready-for-browser-render"
    assert qa["failed_check_ids"] == []

    unsafe = deepcopy(compiled)
    unsafe["production_activation"] = True
    unsafe["source"]["source_z_mutated"] = True
    unsafe = rehash(unsafe, "adapter_result_sha256")
    failed = verify_build_maplibre_preview(plan, approved, unsafe)
    assert failed["status"] == "fail-closed"
    assert failed["failed_check_ids"] == ["preview-boundary", "user-data-and-z-boundary"]


def test_rejection_and_forged_plan_fail_closed(planner: BuildPortrayalPlannerV1) -> None:
    plan = planner.propose(observation({"9310100": 3}))
    rejected = authorize_build_portrayal(plan, actor="reviewer", decision="reject")
    with pytest.raises(BuildPortrayalError, match="not authorized"):
        compile_build_maplibre_preview(plan, rejected)
    tampered = deepcopy(plan)
    tampered["geometry_observation"]["feature_count"] = 30
    with pytest.raises(BuildPortrayalError, match="plan_sha256 identity"):
        compile_build_maplibre_preview(tampered, authorization(plan))


def test_agent_server_exposes_content_addressed_build_portrayal_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NMA_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("NEO4J_URI", raising=False)
    module_name = "nma_agent_server_build_portrayal_test"
    spec = importlib.util.spec_from_file_location(module_name, SERVER_PATH)
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = server
    spec.loader.exec_module(server)

    plan = server.propose_build_portrayal(observation({"9310100": 3}))
    approved = server.authorize_build_portrayal_request(
        {"plan": plan, "actor": "browser-human", "decision": "authorize-preview"}
    )
    compiled = server.compile_build_portrayal_request({"plan": plan, "authorization": approved})
    qa = server.verify_build_portrayal_request(
        {"plan": plan, "authorization": approved, "adapter_result": compiled}
    )
    assert qa["status"] == "pass-ready-for-browser-render"

    forged = deepcopy(plan)
    forged["geometry_observation"]["feature_count"] = 999
    forged = rehash(forged, "plan_sha256")
    with pytest.raises(BuildPortrayalError, match="not issued by this governed server session"):
        server.authorize_build_portrayal_request(
            {"plan": forged, "actor": "browser-human", "decision": "authorize-preview"}
        )
    source = SERVER_PATH.read_text(encoding="utf-8")
    for route in (
        "/api/build-portrayal/proposals",
        "/api/build-portrayal/authorizations",
        "/api/build-portrayal/compile",
        "/api/build-portrayal/observations",
        "/api/build-portrayal/verify",
    ):
        assert route in source

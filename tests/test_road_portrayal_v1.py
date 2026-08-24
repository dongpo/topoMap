from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

from nma.core import canonical_sha256
from nma.readonly_knowledge_service import select_readonly_knowledge_service
from nma.road_portrayal_v1 import (
    ADAPTER_RESULT_SCHEMA,
    AGENT_DECISION_SCHEMA,
    AUTHORIZATION_SCHEMA,
    DATASET_OBSERVATION_SCHEMA,
    PLAN_SCHEMA,
    QA_SCHEMA,
    ROAD_PARENT_CODES,
    ROAD_PORTRAYAL_CODES,
    TOOL_OBSERVATION_SCHEMA,
    RoadPortrayalError,
    RoadPortrayalPlannerV1,
    apply_road_tool_observation,
    authorize_road_portrayal,
    compile_road_maplibre_preview,
    verify_road_maplibre_preview,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
REGISTRY_PATH = ROOT / "data/knowledge/nma-citation-source-registry-v0.6.json"
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"


@pytest.fixture
def planner() -> RoadPortrayalPlannerV1:
    retriever, _service, _trace = select_readonly_knowledge_service(
        canonical_graph_path=GRAPH_PATH,
        citation_registry_path=REGISTRY_PATH,
        settings={"NMA_GRAPH_BACKEND": "canonical-json", "NMA_GRAPH_FALLBACK": "canonical-json"},
    )
    return RoadPortrayalPlannerV1(retriever)


def observation(
    counts: dict[str, int] | None = None,
    *,
    classification_field: str = "TERRAINID",
) -> dict:
    counts = counts or {code: index + 1 for index, code in enumerate(ROAD_PORTRAYAL_CODES)}
    feature_count = sum(counts.values())
    return {
        "schema": DATASET_OBSERVATION_SCHEMA,
        "goal": "依測圖規範繪製使用者 ROAD Shapefile 中的道路線與道路名稱",
        "source": "user-shapefile",
        "source_layer": "ROAD",
        "geometry_family": "line",
        "classification_field_mapping": {
            "source_field": classification_field,
            "canonical_field": "ROADCLASS2",
            "status": (
                "official-direct"
                if classification_field == "ROADCLASS2"
                else "session-human-confirmed"
            ),
            "confirmed_by": None if classification_field == "ROADCLASS2" else "browser-reviewer",
        },
        "identity_field": "ROADSEGID",
        "label_field": "ROADNAME",
        "route_number_fields": ["ROADNUM", "ROADNUM1", "ROADNUM2"],
        "observed_class_counts": counts,
        "classification_resolutions": [],
        "feature_count": feature_count,
        "total_vertex_count": feature_count * 4,
        "multipart_feature_count": min(2, feature_count),
        "source_identity_rule": "zip-relative-filename-plus-source-id",
        "raw_feature_bytes_transmitted": False,
    }


def authorization(plan: dict) -> dict:
    return authorize_road_portrayal(plan, actor="human-reviewer", decision="authorize-preview")


def rehash(value: dict, field: str) -> dict:
    changed = deepcopy(value)
    changed.pop(field, None)
    changed[field] = canonical_sha256(changed)
    return changed


def test_all_direct_road_portrayal_classes_are_retrieved_from_readonly_kg(
    planner: RoadPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation())
    assert plan["schema"] == PLAN_SCHEMA
    assert plan["classification_root"] == "9420000"
    assert plan["source_binding"]["classification_field_mapping"]["status"] == (
        "session-human-confirmed"
    )
    assert plan["governance"]["surveyed_width_boundary_rendered"] is False
    assert plan["governance"]["route_shield_graphic_rendered"] is False
    entries = {item["feature_code"]: item for item in plan["entries"]}
    assert set(entries) == set(ROAD_PORTRAYAL_CODES)
    assert entries["9420700"]["preview_style"]["line_color"] == "#111111"
    assert entries["9420400"]["preview_style"]["line_color"] == "#c62828"
    assert entries["9420400"]["shield_binding"] == {
        "shield_code": "9490005",
        "shield_name": "縣道線號符號",
        "orientation": "road-parallel",
        "runtime_status": "semantic-binding-only-no-reviewed-renderer",
    }
    assert entries["9420700"]["shield_binding"] is None
    for entry in entries.values():
        assert entry["rule"]["activation_status"] == "non-executable"
        assert entry["evidence"]["classification_citation"]["filename"].startswith("02-")
        assert entry["evidence"]["portrayal_citation"]["filename"].startswith("01-")
        service = entry["evidence"]["knowledge_service"]
        assert service["mutation_allowed"] is False
        assert service["arbitrary_cypher_allowed"] is False


def test_parent_codes_unknown_codes_and_unconfirmed_schema_mapping_fail_before_plan(
    planner: RoadPortrayalPlannerV1,
) -> None:
    for parent in ROAD_PARENT_CODES:
        with pytest.raises(RoadPortrayalError, match="requires clarification"):
            planner.propose(observation({parent: 2}))
    with pytest.raises(RoadPortrayalError, match="Unsupported ROAD classification"):
        planner.propose(observation({"9420908": 1}))
    invalid = observation({"9420400": 3})
    invalid["classification_field_mapping"]["confirmed_by"] = None
    with pytest.raises(RoadPortrayalError, match="explicit session mapping"):
        planner.propose(invalid)


def test_official_roadclass2_and_reviewed_parent_resolution_are_accepted(
    planner: RoadPortrayalPlannerV1,
) -> None:
    value = observation({"9420101": 5}, classification_field="ROADCLASS2")
    value["classification_resolutions"] = [
        {
            "source_code": "9420100",
            "effective_code": "9420101",
            "status": "session-human-confirmed",
            "confirmed_by": "road-reviewer",
        }
    ]
    plan = planner.propose(value)
    assert plan["source_binding"]["classification_field_mapping"] == {
        "source_field": "ROADCLASS2",
        "canonical_field": "ROADCLASS2",
        "status": "official-direct",
        "confirmed_by": None,
    }
    assert plan["source_binding"]["classification_resolutions"][0]["effective_code"] == ("9420101")


def test_authorized_compile_creates_line_and_line_following_name_layers(
    planner: RoadPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9420400": 3, "9420700": 2}))
    approved = authorization(plan)
    compiled = compile_road_maplibre_preview(plan, approved)
    assert approved["schema"] == AUTHORIZATION_SCHEMA
    assert compiled["schema"] == ADAPTER_RESULT_SCHEMA
    assert compiled["expected_feature_count"] == 5
    assert compiled["expected_total_vertex_count"] == 20
    assert len(compiled["layers"]) == 4
    assert {layer["nma:semantic_role"] for layer in compiled["layers"]} == {
        "derived-road-centreline-preview",
        "line-following-road-name",
    }
    labels = [layer for layer in compiled["layers"] if layer["type"] == "symbol"]
    assert all(layer["layout"]["symbol-placement"] == "line" for layer in labels)
    assert compiled["surveyed_width_boundary_rendered"] is False
    assert compiled["route_shield_graphic_rendered"] is False
    assert compiled["source"]["data_included"] is False


def test_tool_observations_change_the_next_agent_decision(
    planner: RoadPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9420400": 3}))

    def observed(outcome: str, detail: str) -> dict:
        return apply_road_tool_observation(
            plan,
            {
                "schema": TOOL_OBSERVATION_SCHEMA,
                "tool": "maplibre-road-preview-compiler",
                "plan_sha256": plan["plan_sha256"],
                "outcome": outcome,
                "detail": detail,
            },
        )

    compiled = observed("compiled", "Two layers compiled.")
    rendered = observed("browser-render-verified", "Three ROAD features rendered.")
    failed = observed("style-validation-failed", "MapLibre rejected the expression.")
    assert compiled["schema"] == AGENT_DECISION_SCHEMA
    assert compiled["decision"] == "verify-then-stop"
    assert rendered["decision"] == "stop"
    assert failed["decision"] == "abstain-and-stop"


def test_qa_passes_valid_adapter_and_fails_boundary_tampering(
    planner: RoadPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9420400": 3}))
    approved = authorization(plan)
    compiled = compile_road_maplibre_preview(plan, approved)
    qa = verify_road_maplibre_preview(plan, approved, compiled)
    assert qa["schema"] == QA_SCHEMA
    assert qa["status"] == "pass-ready-for-browser-render"
    assert qa["failed_check_ids"] == []

    unsafe = deepcopy(compiled)
    unsafe["production_activation"] = True
    unsafe["source"]["user_bytes_transmitted"] = True
    unsafe = rehash(unsafe, "adapter_result_sha256")
    failed = verify_road_maplibre_preview(plan, approved, unsafe)
    assert failed["status"] == "fail-closed"
    assert failed["failed_check_ids"] == ["preview-boundary", "user-data-boundary"]


def test_rejection_and_stale_or_forged_authorization_fail_closed(
    planner: RoadPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9420400": 3}))
    rejected = authorize_road_portrayal(plan, actor="reviewer", decision="reject")
    with pytest.raises(RoadPortrayalError, match="not authorized"):
        compile_road_maplibre_preview(plan, rejected)
    tampered = deepcopy(plan)
    tampered["geometry_observation"]["feature_count"] = 30
    with pytest.raises(RoadPortrayalError, match="plan_sha256 identity"):
        compile_road_maplibre_preview(tampered, authorization(plan))


def test_agent_server_exposes_one_content_addressed_road_portrayal_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NMA_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("NEO4J_URI", raising=False)
    module_name = "nma_agent_server_road_portrayal_test"
    spec = importlib.util.spec_from_file_location(module_name, SERVER_PATH)
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = server
    spec.loader.exec_module(server)

    plan = server.propose_road_portrayal(observation({"9420400": 3}))
    approved = server.authorize_road_portrayal_request(
        {"plan": plan, "actor": "browser-human", "decision": "authorize-preview"}
    )
    compiled = server.compile_road_portrayal_request({"plan": plan, "authorization": approved})
    qa = server.verify_road_portrayal_request(
        {"plan": plan, "authorization": approved, "adapter_result": compiled}
    )
    assert qa["status"] == "pass-ready-for-browser-render"

    forged = deepcopy(plan)
    forged["geometry_observation"]["feature_count"] = 999
    forged = rehash(forged, "plan_sha256")
    with pytest.raises(RoadPortrayalError, match="not issued by this governed server session"):
        server.authorize_road_portrayal_request(
            {"plan": forged, "actor": "browser-human", "decision": "authorize-preview"}
        )
    source = SERVER_PATH.read_text(encoding="utf-8")
    for route in (
        "/api/road-portrayal/proposals",
        "/api/road-portrayal/authorizations",
        "/api/road-portrayal/compile",
        "/api/road-portrayal/observations",
        "/api/road-portrayal/verify",
    ):
        assert route in source

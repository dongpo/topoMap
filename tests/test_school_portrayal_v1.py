from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

from nma.core import canonical_sha256
from nma.readonly_knowledge_service import select_readonly_knowledge_service
from nma.school_portrayal_v1 import (
    ADAPTER_RESULT_SCHEMA,
    AGENT_DECISION_SCHEMA,
    AUTHORIZATION_SCHEMA,
    DATASET_OBSERVATION_SCHEMA,
    PLAN_SCHEMA,
    QA_SCHEMA,
    TOOL_OBSERVATION_SCHEMA,
    SchoolPortrayalError,
    SchoolPortrayalPlannerV1,
    apply_school_tool_observation,
    authorize_school_portrayal,
    compile_school_maplibre_preview,
    verify_school_maplibre_preview,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
REGISTRY_PATH = ROOT / "data/knowledge/nma-citation-source-registry-v0.6.json"
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"

SCHOOL_CLASSES = {
    "9920101": ("大專院校", "school-flag-marker", 61),
    "9920102": ("中學", "school-flag-marker", 61),
    "9920103": ("小學", "school-flag-marker", 61),
    "9920104": ("職訓中心", "name-annotation-only", 61),
    "9920105": ("幼兒園", "name-annotation-only", 61),
    "9920106": ("特殊學校", "school-flag-marker", 62),
}


@pytest.fixture
def planner() -> SchoolPortrayalPlannerV1:
    retriever, _service, _trace = select_readonly_knowledge_service(
        canonical_graph_path=GRAPH_PATH,
        citation_registry_path=REGISTRY_PATH,
        settings={
            "NMA_GRAPH_BACKEND": "canonical-json",
            "NMA_GRAPH_FALLBACK": "canonical-json",
        },
    )
    return SchoolPortrayalPlannerV1(retriever, repository_root=ROOT)


def observation(counts: dict[str, int] | None = None) -> dict:
    return {
        "schema": DATASET_OBSERVATION_SCHEMA,
        "goal": "依測圖規範繪製使用者 MARK Shapefile 中的所有學校點位",
        "source": "user-shapefile",
        "source_layer": "MARK",
        "geometry_type": "Point",
        "classification_field": "TERRAINID",
        "identity_field": "MARKID",
        "label_field": "MARKNAME1",
        "observed_class_counts": counts
        or {code: index + 1 for index, code in enumerate(SCHOOL_CLASSES)},
        "source_identity_rule": "zip-relative-filename-plus-source-id",
        "raw_feature_bytes_transmitted": False,
    }


def authorization(plan: dict) -> dict:
    return authorize_school_portrayal(
        plan,
        actor="human-reviewer",
        decision="authorize-preview",
    )


def rehash(value: dict, field: str) -> dict:
    changed = deepcopy(value)
    changed.pop(field, None)
    changed[field] = canonical_sha256(changed)
    return changed


def test_all_school_leaf_classes_are_planned_from_readonly_kg_evidence(
    planner: SchoolPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation())

    assert plan["schema"] == PLAN_SCHEMA
    assert plan["status"] == "proposed-preview-only-awaiting-human-authorization"
    assert plan["classification_root"] == "9920100"
    assert plan["source_binding"]["raw_feature_bytes_transmitted"] is False
    assert plan["governance"] == {
        "human_authorization_required": True,
        "official_rule_activation": False,
        "production_activation": False,
        "map_mutation_allowed_before_authorization": False,
        "data_export_allowed": False,
        "automatic_action": False,
    }
    assert plan["plan_sha256"] == canonical_sha256(
        {key: value for key, value in plan.items() if key != "plan_sha256"}
    )

    entries = {item["feature_code"]: item for item in plan["entries"]}
    assert set(entries) == set(SCHOOL_CLASSES)
    for code, (name, mode, page) in SCHOOL_CLASSES.items():
        entry = entries[code]
        assert entry["feature_name"] == name
        assert entry["parent_code"] == "9920100"
        assert entry["render_mode"] == mode
        assert entry["rule"]["activation_status"] == "non-executable"
        assert entry["rule"]["page"] == page
        assert entry["evidence"]["classification_node_id"] == (
            f"terrain-classification:doc02:{code}"
        )
        assert entry["evidence"]["classification_citation"]["section_id"] == (
            "section:doc02-1000-production:p65"
        )
        assert entry["evidence"]["portrayal_citation"]["page"] == page
        knowledge = entry["evidence"]["knowledge_service"]
        assert knowledge["active_backend"] == "canonical-json-snapshot"
        assert knowledge["mutation_allowed"] is False
        assert knowledge["arbitrary_cypher_allowed"] is False
        assert len(entry["evidence"]["knowledge_node_ids"]) == 8
        assert entry["evidence"]["knowledge_edge_ids"]
        assert "selected_node_ids" not in knowledge
        assert "selected_edge_ids" not in knowledge
        assert entry["feature_count"] == int(code[-1])


def test_root_code_invalid_schema_and_unknown_code_fail_before_planning(
    planner: SchoolPortrayalPlannerV1,
) -> None:
    with pytest.raises(SchoolPortrayalError, match="classification family"):
        planner.propose(observation({"9920100": 2}))

    wrong_field = observation({"9920103": 2})
    wrong_field["classification_field"] = "CODE"
    with pytest.raises(SchoolPortrayalError, match="exact TERRAINID"):
        planner.propose(wrong_field)

    wrong_identity = observation({"9920103": 2})
    wrong_identity["identity_field"] = "ID"
    with pytest.raises(SchoolPortrayalError, match="MARKID and MARKNAME1"):
        planner.propose(wrong_identity)

    with pytest.raises(SchoolPortrayalError, match="Unsupported School classification"):
        planner.propose(observation({"9999999": 1}))


def test_feature_count_has_no_fifteen_point_or_single_subtype_limit(
    planner: SchoolPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9920101": 370, "9920105": 181}))
    assert {item["feature_code"]: item["feature_count"] for item in plan["entries"]} == {
        "9920101": 370,
        "9920105": 181,
    }


def test_authorized_compile_creates_four_flag_and_two_text_layers_without_data(
    planner: SchoolPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation())
    approved = authorization(plan)
    compiled = compile_school_maplibre_preview(plan, approved)

    assert approved["schema"] == AUTHORIZATION_SCHEMA
    assert compiled["schema"] == ADAPTER_RESULT_SCHEMA
    assert compiled["status"] == "compiled-preview-not-yet-rendered"
    assert compiled["source"]["data_included"] is False
    assert compiled["source"]["user_bytes_transmitted"] is False
    assert compiled["map_mutation_performed"] is False
    assert compiled["expected_feature_count"] == 21
    assert len(compiled["layers"]) == 6
    assert len([item for item in compiled["layers"] if "icon-image" in item["layout"]]) == 4
    assert len([item for item in compiled["layers"] if "icon-image" not in item["layout"]]) == 2
    assert len(compiled["resources"]) == 1
    assert compiled["resources"][0]["authoritative_source_geometry"] is False
    assert compiled["resources"][0]["binding_status"] == (
        "shared-reviewed-school-flag-family-derived-preview"
    )
    for layer in compiled["layers"]:
        code = layer["filter"][2]
        assert layer["filter"] == ["==", ["to-string", ["get", "TERRAINID"]], code]
        assert "source-layer" not in layer
        assert layer["nma:evidence"]["rule_id"] == f"portrayal-rule:doc01:{code}"
        if "icon-image" in layer["layout"]:
            assert layer["layout"]["icon-allow-overlap"] is True
            assert layer["layout"]["text-optional"] is True
            assert layer["layout"]["text-allow-overlap"] is False
        else:
            assert layer["layout"]["text-allow-overlap"] is True


def test_rejection_tampering_and_stale_authorization_fail_closed(
    planner: SchoolPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9920103": 1}))
    rejected = authorize_school_portrayal(plan, actor="reviewer", decision="reject")
    with pytest.raises(SchoolPortrayalError, match="not authorized"):
        compile_school_maplibre_preview(plan, rejected)

    tampered = deepcopy(plan)
    tampered["entries"][0]["feature_count"] = 100
    with pytest.raises(SchoolPortrayalError, match="plan_sha256 identity"):
        compile_school_maplibre_preview(tampered, authorization(plan))


def test_failed_sdf_observation_changes_next_plan_and_requires_reauthorization(
    planner: SchoolPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9920101": 2, "9920103": 3}))
    approved = authorization(plan)
    tool_observation = {
        "schema": TOOL_OBSERVATION_SCHEMA,
        "tool": "maplibre-school-preview-compiler",
        "plan_sha256": plan["plan_sha256"],
        "outcome": "sdf-resource-load-failed",
        "detail": "Browser rejected SDF conversion for the reviewed SVG.",
    }
    revised = apply_school_tool_observation(plan, tool_observation)

    assert revised["schema"] == PLAN_SCHEMA
    assert revised["plan_sha256"] != plan["plan_sha256"]
    assert revised["revision"] == {
        "depth": 1,
        "parent_plan_sha256": plan["plan_sha256"],
    }
    assert revised["agent_trace"][-2]["state"] == "replan"
    assert all(entry["asset_binding"]["sdf"] is False for entry in revised["entries"])
    with pytest.raises(SchoolPortrayalError, match="does not bind"):
        compile_school_maplibre_preview(revised, approved)

    reapproved = authorization(revised)
    compiled = compile_school_maplibre_preview(revised, reapproved)
    assert all("icon-color" not in layer["paint"] for layer in compiled["layers"])


def test_tool_outcomes_drive_verify_or_abstain_decisions(
    planner: SchoolPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9920104": 4}))

    def observed(outcome: str, detail: str) -> dict:
        return apply_school_tool_observation(
            plan,
            {
                "schema": TOOL_OBSERVATION_SCHEMA,
                "tool": "maplibre-school-preview-compiler",
                "plan_sha256": plan["plan_sha256"],
                "outcome": outcome,
                "detail": detail,
            },
        )

    verify = observed("compiled", "MapLibre accepted the compiled style fragment.")
    stop = observed("browser-render-verified", "MapLibre rendered the governed layer.")
    abstain = observed("style-validation-failed", "Unsupported expression.")
    assert verify["schema"] == AGENT_DECISION_SCHEMA
    assert verify["decision"] == "verify-then-stop"
    assert stop["decision"] == "stop"
    assert stop["observed_outcome"] == "browser-render-verified"
    assert abstain["decision"] == "abstain-and-stop"
    assert verify["map_mutation_allowed"] is False
    assert abstain["automatic_rule_activation"] is False


def test_qa_passes_valid_compile_and_fails_semantic_boundary_tampering(
    planner: SchoolPortrayalPlannerV1,
) -> None:
    plan = planner.propose(observation({"9920102": 9, "9920105": 7}))
    approved = authorization(plan)
    compiled = compile_school_maplibre_preview(plan, approved)
    qa = verify_school_maplibre_preview(plan, approved, compiled)
    assert qa["schema"] == QA_SCHEMA
    assert qa["status"] == "pass-ready-for-browser-render"
    assert qa["browser_render_authorized"] is True
    assert qa["failed_check_ids"] == []

    unsafe = deepcopy(compiled)
    unsafe["production_activation"] = True
    unsafe["source"]["user_bytes_transmitted"] = True
    unsafe = rehash(unsafe, "adapter_result_sha256")
    failed = verify_school_maplibre_preview(plan, approved, unsafe)
    assert failed["status"] == "fail-closed"
    assert failed["browser_render_authorized"] is False
    assert failed["failed_check_ids"] == ["preview-boundary", "user-data-boundary"]


def test_existing_agent_server_exposes_one_content_addressed_governed_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NMA_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("NEO4J_URI", raising=False)
    module_name = "nma_agent_server_school_portrayal_test"
    spec = importlib.util.spec_from_file_location(module_name, SERVER_PATH)
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = server
    spec.loader.exec_module(server)

    plan = server.propose_school_portrayal(observation({"9920101": 24, "9920105": 11}))
    approved = server.authorize_school_portrayal_request(
        {"plan": plan, "actor": "browser-human", "decision": "authorize-preview"}
    )
    compiled = server.compile_school_portrayal_request({"plan": plan, "authorization": approved})
    qa = server.verify_school_portrayal_request(
        {"plan": plan, "authorization": approved, "adapter_result": compiled}
    )

    assert qa["status"] == "pass-ready-for-browser-render"

    forged = deepcopy(plan)
    forged["entries"][0]["feature_count"] = 999
    forged = rehash(forged, "plan_sha256")
    with pytest.raises(SchoolPortrayalError, match="not issued by this governed server session"):
        server.authorize_school_portrayal_request(
            {"plan": forged, "actor": "browser-human", "decision": "authorize-preview"}
        )
    source = SERVER_PATH.read_text(encoding="utf-8")
    for route in (
        "/api/school-portrayal/proposals",
        "/api/school-portrayal/authorizations",
        "/api/school-portrayal/compile",
        "/api/school-portrayal/observations",
        "/api/school-portrayal/verify",
    ):
        assert route in source

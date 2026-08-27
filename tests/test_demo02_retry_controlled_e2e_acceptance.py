from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from scripts.issue_school_demo_authorization import (
    SchoolDemoAuthorizationIssuanceError,
    build_school_demo_authorization,
)
from nma.core import canonical_sha256
from nma.real_layer import file_sha256
from nma.road_execution import FrozenRoadInputs, RoadAuthorizationStore, RoadExecutionEngine
from nma.road_resolution import canonical_json
from nma.school_hero_execution import (
    ExecutionAuthorizationStore,
    ExecutionAuthorizationVerifier,
    SchoolHeroExecutionEngine,
    authorization_sha256,
)
from nma.unified_runtime import (
    BuildRuntimeAdapter,
    RoadRuntimeAdapter,
    SchoolRuntimeAdapter,
    UnifiedNMARuntime,
    UnifiedRuntimeError,
)


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
SYMBOL = ROOT / "assets/symbols/nlsc112v5.4/school.svg"
SCHOOL_AUTHORIZATION_PATH = (
    ROOT
    / "artifacts/runtime/school-hero/authorizations"
    / "authorization-school-demo-b4ecdbfc35ecaf73293ed497.json"
)
SCHOOL_AUTHORIZATION_ID = "authorization-school-demo-b4ecdbfc35ecaf73293ed497"
SCHOOL_AUTHORIZATION_HASH = "d5546bd1b2176a4ad287acb1c78740ce79a90db76d05739dc871267d901dac67"
SCHOOL_EXECUTION_ID = "exec-8d174b62fb63189987eafdb6"
ROAD_AUTHORIZATION_ID = "road-03-authorization-f68220ecef989e589dd6e28c"
ROAD_EXECUTION_ID = "road-exec-33766f336d9cc18eb2ac159e"
ROAD_BUNDLE_SHA256 = "33aa7c6b0d557fa9a72e2fa4e0106493d8dfe10ec9201bd7762e204bb14a286d"
ROAD_SOURCE_HASHES = (
    "42616b9b91d91efd4582171b23ad70259156c586bef776098329cdd81aa8f800",
    "c075943948c1184493d41672f0ca00e610c90bfa7c721f24a645765dc48b9faf",
    "88ad286f2b368130e0870360acd07d1d79614d8005ee53eed966b8db6abd2cc6",
)
MATRIX_PATH = (
    ROOT / "data/specifications/nma-demo-02-retry-controlled-e2e-acceptance-record-v1.0.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value) + b"\n")


def _visual_evidence(root: Path, runtime_geojson: Path) -> tuple[Path, Path]:
    screenshot = root / "road-browser.png"
    screenshot.write_bytes(b"DEMO-02 Retry deterministic ROAD browser observation")
    screenshot_sha256 = file_sha256(screenshot)
    evidence = {
        "schema": "nma.road-visual-evidence/1.0",
        "execution_id": ROAD_EXECUTION_ID,
        "bundle_sha256": ROAD_BUNDLE_SHA256,
        "runtime_geojson_sha256": file_sha256(runtime_geojson),
        "rendering_mechanism": "MapLibre GL JS 4.7.0 controlled-browser acceptance",
        "render_environment": {
            "browser": "focused-test-browser",
            "viewport": {"width": 1024, "height": 768},
            "device_pixel_ratio": 1,
        },
        "render_observation": {
            "map_loaded": True,
            "source_ids": [f"nma-road-source-{ROAD_EXECUTION_ID}"],
            "layer_ids": [f"nma-road-label-{ROAD_EXECUTION_ID}"],
            "rendered_label_texts": ["中山街"],
            "rendered_label_feature_count": 1,
            "unrelated_feature_count": 0,
            "shield_graphic_count": 0,
            "unexpected_layer_ids": [],
            "unexpected_source_ids": [],
            "screenshot_sha256": screenshot_sha256,
        },
        "oracle": {"status": "absent", "identity": None},
        "pixel_correctness_status": "evidence_generated_but_no_independent_visual_oracle",
    }
    evidence["evidence_sha256"] = canonical_sha256(evidence)
    path = root / "road-visual-evidence.json"
    _write_json(path, evidence)
    return path, screenshot


@pytest.fixture(scope="module")
def accepted_runtime(tmp_path_factory: pytest.TempPathFactory) -> dict:
    if not ARCHIVE.is_file() or not shutil.which("ogr2ogr"):
        pytest.skip("The exact controlled fixture package and GDAL/OGR are required.")
    assert file_sha256(ARCHIVE) == ARCHIVE_SHA256
    root = tmp_path_factory.mktemp("demo02-retry")

    school_authorization = _load(SCHOOL_AUTHORIZATION_PATH)
    school_store = ExecutionAuthorizationStore(root / "school/authorizations")
    school_store.save(school_authorization)
    school_engine = SchoolHeroExecutionEngine(
        storage_root=root / "school",
        archive_path=ARCHIVE,
        official_symbol_path=SYMBOL,
        authorization_store=school_store,
    )

    road_inputs = FrozenRoadInputs(ROOT)
    road_engine = RoadExecutionEngine(
        storage_root=root / "road",
        archive_path=ARCHIVE,
        frozen_inputs=road_inputs,
        authorization_store=RoadAuthorizationStore(road_inputs.authorization),
    )
    road_receipt = road_engine.execute_by_id(
        {
            "authorization_id": ROAD_AUTHORIZATION_ID,
            "idempotency_key": "road04-controlled-execution-v1",
        }
    )
    assert road_receipt["execution_id"] == ROAD_EXECUTION_ID
    road_engine.observe(
        ROAD_EXECUTION_ID,
        {
            "state": "verify",
            "client_session": "road04-verification",
            "source_ids": [f"nma-road-source-{ROAD_EXECUTION_ID}"],
            "layer_ids": [f"nma-road-label-{ROAD_EXECUTION_ID}"],
            "observed_feature_count": 3,
            "runtime_version": "maplibre-reviewed-line-mechanism/1",
            "status": "verified",
        },
    )
    visual, screenshot = _visual_evidence(
        root, root / f"road/executions/{ROAD_EXECUTION_ID}/data/road-centreline-runtime.geojson"
    )

    runtime = UnifiedNMARuntime(
        {
            "school": SchoolRuntimeAdapter(
                engine=school_engine,
                repository_root=ROOT,
                archive_path=ARCHIVE,
                symbol_path=SYMBOL,
            ),
            "road": RoadRuntimeAdapter(
                engine=road_engine,
                repository_root=ROOT,
                archive_path=ARCHIVE,
                visual_evidence_path=visual,
                screenshot_path=screenshot,
            ),
            "build": BuildRuntimeAdapter(repository_root=ROOT, archive_path=ARCHIVE),
        }
    )
    school_execute = runtime.dispatch(
        {
            "domain": "school",
            "request": "Produce the controlled School 9920103 rule-aligned map.",
            "operation": "execute",
            "authorization": {
                "authorization_id": SCHOOL_AUTHORIZATION_ID,
                "idempotency_key": "demo-02-retry-school-controlled-e2e",
            },
        }
    )
    school_verify = runtime.dispatch(
        {
            "domain": "school",
            "request": "Verify controlled School 9920103 execution.",
            "operation": "verify",
            "parameters": {"execution_id": school_execute["execution"]["identity"]},
        }
    )
    road_execute = runtime.dispatch(
        {
            "domain": "road",
            "request": "Produce County Highway 126 ROAD 9420400 with exact geometry.",
            "operation": "execute",
            "authorization": {
                "authorization_id": ROAD_AUTHORIZATION_ID,
                "idempotency_key": "road04-controlled-execution-v1",
            },
        }
    )
    road_verify = runtime.dispatch(
        {
            "domain": "road",
            "request": "Verify controlled ROAD 9420400 execution.",
            "operation": "verify",
            "parameters": {"execution_id": ROAD_EXECUTION_ID},
        }
    )
    build = runtime.dispatch(
        {
            "domain": "build",
            "request": "Replay accepted BUILD 9310100 with activation disabled.",
            "operation": "replay",
        }
    )
    return {
        "root": root,
        "runtime": runtime,
        "school_engine": school_engine,
        "road_engine": road_engine,
        "school_execute": school_execute,
        "school_verify": school_verify,
        "road_execute": road_execute,
        "road_verify": road_verify,
        "build": build,
    }


def test_school_real_execution_verification_provenance_and_map(accepted_runtime: dict) -> None:
    executed = accepted_runtime["school_execute"]
    verified = accepted_runtime["school_verify"]
    collection = accepted_runtime["school_engine"].get_data(SCHOOL_EXECUTION_ID)
    assert executed["selected_domain"] == "school"
    assert executed["plan"] == {
        "status": "executed",
        "contract": "nma.school-hero-execution-plan/1.0",
        "identity": "plan-8d174b62fb63189987eafdb6",
        "sha256": "b7afb38141557c3dad312d89a819243b3225e846883a17565519a75adafa0347",
    }
    assert executed["authorization"]["identity"] == SCHOOL_AUTHORIZATION_ID
    assert executed["authorization"]["sha256"] == SCHOOL_AUTHORIZATION_HASH
    assert executed["execution"]["identity"] == SCHOOL_EXECUTION_ID
    assert executed["receipt"]["identity"]
    assert executed["visualization"]["status"] == "available"
    assert len(collection["features"]) == 15
    assert {feature["geometry"]["type"] for feature in collection["features"]} == {"Point"}
    assert {feature["properties"]["TERRAINID"] for feature in collection["features"]} == {"9920103"}
    assert verified["verification"]["status"] == "verified"
    assert verified["provenance"]["status"] == "verified"
    assert not any(executed["mutation"].values())


def test_school_graphrag_mapping_rule_and_plan_alignment(accepted_runtime: dict) -> None:
    graph = _load(ROOT / "data/knowledge/nma-canonical-graph-v0.4.json")
    nodes = {node["id"]: node for node in graph["nodes"]}
    plan = _load(accepted_runtime["root"] / f"school/executions/{SCHOOL_EXECUTION_ID}/plan.json")
    bundle = accepted_runtime["school_engine"].get_bundle(SCHOOL_EXECUTION_ID)
    required = {
        "code-value:landmark-type:9920103",
        "portrayal-rule:doc01:9920103",
        "portrayal-recipe:doc01:9920103:review-v1",
        "product-layer:MARK",
    }
    assert required.issubset(nodes)
    assert nodes["portrayal-rule:doc01:9920103"]["properties"]["geometry_role"] == "Point"
    assert plan["source_filter"] == {"field": "TERRAINID", "operator": "equals", "value": "9920103"}
    assert plan["source_layers"] == [
        "J01_MARK",
        "J13_MARK",
        "J17_MARK",
        "K01_MARK",
        "K02_MARK",
        "K14_MARK",
    ]
    assert bundle["layer"]["layout"]["text-field"] == ["to-string", ["get", "MARKNAME1"]]
    assert bundle["layer"]["layout"]["icon-image"].startswith("nma-school-image-")
    assert bundle["layer"]["paint"] == {
        "icon-color": "#1565c0",
        "icon-opacity": 1.0,
        "text-color": "#1565c0",
    }


def test_road_real_execution_exact_geometry_rules_verification_and_map(
    accepted_runtime: dict,
) -> None:
    executed = accepted_runtime["road_execute"]
    verified = accepted_runtime["road_verify"]
    source = _load(
        accepted_runtime["root"]
        / f"road/executions/{ROAD_EXECUTION_ID}/data/road-centreline-source.geojson"
    )
    bundle = accepted_runtime["road_engine"].get_bundle(ROAD_EXECUTION_ID)
    assert executed["selected_domain"] == "road"
    assert executed["execution"]["identity"] == ROAD_EXECUTION_ID
    assert executed["visualization"]["status"] == "available"
    assert [len(feature["geometry"]["coordinates"]) for feature in source["features"]] == [4, 3, 4]
    assert tuple(canonical_sha256(feature["geometry"]) for feature in source["features"]) == (
        ROAD_SOURCE_HASHES
    )
    assert bundle["layers"] == [
        {
            "id": f"nma-road-label-{ROAD_EXECUTION_ID}",
            "type": "symbol",
            "source": f"nma-road-source-{ROAD_EXECUTION_ID}",
            "layout": {"symbol-placement": "line", "text-field": ["literal", "中山街"]},
            "semantic_role": "authorized-road-name-annotation",
        }
    ]
    assert bundle["shield_binding"] == {
        "shield_code": "9490005",
        "shield_orientation": "road-parallel",
        "status": "semantic_binding_only",
        "resolver_identity": None,
        "resolved_artifact_sha256": None,
    }
    assert verified["verification"]["status"] == "verified"
    assert verified["provenance"]["status"] == "verified"
    assert not any(executed["mutation"].values())


def test_road_graphrag_rule_nodes_align_with_execution(accepted_runtime: dict) -> None:
    graph = _load(ROOT / "data/knowledge/nma-canonical-graph-v0.4.json")
    nodes = {node["id"]: node for node in graph["nodes"]}
    record = _load(ROOT / "data/specifications/nma-demo-controlled-fixture-baseline-v1.0.json")
    plan = _load(accepted_runtime["root"] / f"road/executions/{ROAD_EXECUTION_ID}/plan.json")
    assert set(record["road"]["graphrag"]["required_nodes"]).issubset(nodes)
    assert nodes["portrayal-rule:doc01:9420400"]["properties"]["feature_code"] == "9420400"
    assert nodes["portrayal-rule:doc01:9490005"]["properties"]["instruction"].endswith("道路平行")
    assert plan["portrayal"] == {
        "graphic_element_roles": [2, 5],
        "road_name_annotation": "中山街",
        "shield_code": "9490005",
        "shield_orientation": "road-parallel",
    }
    assert plan["source"]["ordered_segment_ids"] == [
        "K0000004671",
        "K0000004913",
        "K0000005348",
    ]


def test_build_accepted_replay_is_complete_and_never_auto_activates(
    accepted_runtime: dict,
) -> None:
    result = accepted_runtime["build"]
    feature = result["visualization"]["maplibre"]["source"]["data"]["features"][0]
    assert result["selected_domain"] == "build"
    assert result["plan"]["identity"]
    assert result["authorization"]["identity"] == "build-04-demo-auth-a5a8f11b94784a60"
    assert result["execution"]["identity"] == "build-05-demo-exec-b8b5ecd54954b190eb8cda39"
    assert result["observation"]["status"] == "rendered-derived-demo"
    assert result["verification"]["status"] == "passed-frozen-package-validation"
    assert result["receipt"]["identity"]
    assert result["provenance"]["identity"]
    assert feature["geometry"]["type"] == "Polygon"
    assert result["execution"]["activation_status"] == "held-not-requested"
    assert result["mutation"]["automatic_build_activation"] is False


@pytest.mark.parametrize(
    ("payload", "code", "stage"),
    [
        ({"domain": "riverl", "request": "Show river"}, "unsupported_domain", "request"),
        ({"request": "Show school and road"}, "ambiguous_domain", "request"),
        ({"domain": "school", "request": ""}, "invalid_request", "request"),
        (
            {"domain": "school", "request": "Execute school", "operation": "execute"},
            "authorization_failure",
            "authorization",
        ),
        (
            {
                "domain": "school",
                "request": "Execute school",
                "operation": "execute",
                "authorization": {"authorization_id": "invalid", "idempotency_key": "invalid-key"},
            },
            "authorization_failure",
            "authorization",
        ),
        (
            {"domain": "school", "request": "Show School 9999999"},
            "unsupported_capability",
            "routing",
        ),
        (
            {"domain": "school", "request": "Show School 9920103", "operation": "activate"},
            "invalid_request",
            "request",
        ),
        (
            {"domain": "build", "request": "Activate BUILD", "operation": "activate"},
            "invalid_request",
            "request",
        ),
    ],
)
def test_negative_runtime_requests_fail_closed_without_mutation(
    accepted_runtime: dict, payload: dict, code: str, stage: str
) -> None:
    root = accepted_runtime["root"]
    before = sorted(str(path.relative_to(root)) for path in root.rglob("*"))
    with pytest.raises(UnifiedRuntimeError) as caught:
        accepted_runtime["runtime"].dispatch(payload)
    assert caught.value.code == code
    assert caught.value.stage == stage
    assert sorted(str(path.relative_to(root)) for path in root.rglob("*")) == before


def test_wrong_school_fixture_plan_scope_and_tampered_evidence_are_rejected() -> None:
    authorization = _load(SCHOOL_AUTHORIZATION_PATH)
    verifier = ExecutionAuthorizationVerifier()

    with pytest.raises(SchoolDemoAuthorizationIssuanceError, match="not the controlled"):
        build_school_demo_authorization(human_approved=True, archive_sha256="0" * 64)

    wrong_plan = deepcopy(authorization)
    wrong_plan["approved_operations"][0]["value"]["color"] = "#c62828"
    wrong_plan["authorization_hash"] = authorization_sha256(wrong_plan)
    with pytest.raises(Exception, match="approved operations"):
        verifier.verify(wrong_plan)

    tampered = deepcopy(authorization)
    tampered["demo_binding"]["expected_feature_count"] = 16
    with pytest.raises(Exception, match="authorization hash"):
        verifier.verify(tampered)


def test_missing_controlled_fixture_fails_without_substitution(tmp_path: Path) -> None:
    authorization = _load(SCHOOL_AUTHORIZATION_PATH)
    store = ExecutionAuthorizationStore(tmp_path / "runtime/authorizations")
    store.save(authorization)
    engine = SchoolHeroExecutionEngine(
        storage_root=tmp_path / "runtime",
        archive_path=tmp_path / "missing-controlled-fixture.zip",
        official_symbol_path=SYMBOL,
        authorization_store=store,
    )
    with pytest.raises(Exception, match="archive"):
        engine.execute_by_id(
            {
                "authorization_id": SCHOOL_AUTHORIZATION_ID,
                "idempotency_key": "missing-controlled-fixture",
            }
        )
    assert not (tmp_path / "runtime/executions").exists()


def test_browser_and_road_visual_verification_wiring_is_production_reachable() -> None:
    html = (ROOT / "nmaAgentDemoV1.html").read_text(encoding="utf-8")
    server = (ROOT / "scripts/run_nma_agent_server.py").read_text(encoding="utf-8")
    runtime = (ROOT / "src/nma/unified_runtime.py").read_text(encoding="utf-8")
    assert 'glyphs="https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf"' in html
    assert "image.src=resource.path;await image.decode();map.addImage" in html
    assert 'visual_evidence_path=ROOT / "artifacts/tmp/road05-visual-evidence.json"' in server
    assert 'screenshot_path=ROOT / "artifacts/tmp/road05-render.png"' in server
    assert "visual_evidence_path=self.visual_evidence_path" in runtime
    assert "screenshot_path=self.screenshot_path" in runtime


def test_no_external_substitution_no_stub_and_frozen_claim_boundary() -> None:
    fixture = _load(ROOT / "data/specifications/nma-demo-controlled-fixture-baseline-v1.0.json")
    runtime = (ROOT / "src/nma/unified_runtime.py").read_text(encoding="utf-8")
    assert fixture["scope"]["external_data_substitution_performed"] is False
    assert fixture["scope"]["arbitrary_geospatial_ingestion_claimed"] is False
    assert fixture["fixture_authority"]["package_sha256"] == ARCHIVE_SHA256
    assert "self.engine.execute_by_id(authorization)" in runtime
    assert "implement_controlled_building(" in runtime
    assert "class DemoStub" not in runtime
    assert "authorized = True" not in runtime


def test_machine_acceptance_matrix_is_closed_and_complete() -> None:
    record = _load(MATRIX_PATH)
    allowed = {"PASS", "PASS_NOT_APPLICABLE", "PARTIAL", "FAIL", "UNRESOLVED"}
    required = {
        "controlled_fixture",
        "user_request",
        "graphrag_retrieval",
        "mapping_rule_alignment",
        "planning",
        "authorization",
        "real_execution",
        "observation",
        "verification_qa",
        "receipt_provenance",
        "map_result",
        "fail_closed",
        "controlled_reproducibility",
    }
    assert set(record["acceptance_matrix"]) == required
    for row in record["acceptance_matrix"].values():
        assert set(row) == {"school", "road", "build", "overall"}
        assert set(row.values()).issubset(allowed)
        assert row["overall"] == "PASS"
    assert record["verdict"] == "PASS — NMA CONTROLLED END-TO-END DEMO ACCEPTED"
    assert record["counts"] == {
        "external_data_substitutions": 0,
        "production_reachable_demo_stubs": 0,
        "controlled_fixture_modifications": 0,
        "runtime_source_modifications": 3,
    }

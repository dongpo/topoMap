from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any

from jsonschema import Draft202012Validator
import pytest
from referencing import Registry, Resource

from nma.real_layer import file_sha256
from nma.road_approval import authorization_sha256
from nma.road_execution import (
    AUTHORIZATION_ID,
    EXPECTED_ARCHIVE_SHA256,
    EXPECTED_AUTHORIZATION_SHA256,
    EXPECTED_CLASS_CODE,
    EXPECTED_PORTRAYAL,
    EXPECTED_SEGMENT_IDS,
    FrozenRoadAuthorizationVerifier,
    FrozenRoadInputs,
    RoadExecutionEngine,
    RoadExecutionError,
    _hash_record,
)
from nma.road_portrayal_decision import decision_sha256, proposal_sha256


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"
GOLDEN_NAMES = {
    "plan": "nma-road-hero-road-04-golden-plan-v1.0.json",
    "derived": "nma-road-hero-road-04-golden-derived-portrayal-v1.0.json",
    "bundle": "nma-road-hero-road-04-golden-runtime-bundle-v1.0.json",
    "receipt": "nma-road-hero-road-04-golden-receipt-v1.0.json",
    "rollback": "nma-road-hero-road-04-golden-rollback-manifest-v1.0.json",
    "observation": "nma-road-hero-road-04-golden-observation-v1.0.json",
}


pytestmark = pytest.mark.skipif(
    not ARCHIVE.is_file() or not shutil.which("ogr2ogr") or not shutil.which("ogrinfo"),
    reason="The exact private ROAD archive and GDAL/OGR are required.",
)


def _authorization() -> dict[str, Any]:
    return json.loads(
        (
            ROOT / "data/specifications/nma-road-hero-road-03-golden-authorization-v1.0.json"
        ).read_text(encoding="utf-8")
    )


def _now(day: int = 19):
    return lambda: datetime(2026, 8, day, 12, 0, tzinfo=timezone.utc)


def _engine(storage_root: Path, *, root: Path = ROOT, archive: Path = ARCHIVE, day: int = 19):
    inputs = FrozenRoadInputs(root)
    return RoadExecutionEngine(
        storage_root=storage_root,
        archive_path=archive,
        frozen_inputs=inputs,
        now=_now(day),
    )


@pytest.fixture(scope="session")
def executed(tmp_path_factory):
    storage = tmp_path_factory.mktemp("road04-executed")
    engine = _engine(storage)
    receipt = engine.execute(_authorization(), "road04-session-key")
    execution_id = receipt["execution_id"]
    bundle = engine.get_bundle(execution_id)
    observation = engine.observe(
        execution_id,
        {
            "state": "verify",
            "client_session": "road04-verification",
            "source_ids": [bundle["source"]["id"]],
            "layer_ids": [item["id"] for item in bundle["layers"]],
            "observed_feature_count": 3,
            "runtime_version": "maplibre-reviewed-line-mechanism/1",
            "status": "verified",
        },
    )
    return engine, storage, receipt, observation


def _execution_artifacts(storage: Path, execution_id: str) -> dict[str, dict[str, Any]]:
    root = storage / "executions" / execution_id
    return {
        "plan": json.loads((root / "plan.json").read_text(encoding="utf-8")),
        "derived": json.loads((root / "derived-portrayal.json").read_text(encoding="utf-8")),
        "bundle": json.loads((root / "bundle.json").read_text(encoding="utf-8")),
        "receipt": json.loads((root / "receipt.json").read_text(encoding="utf-8")),
        "rollback": json.loads((root / "rollback-manifest.json").read_text(encoding="utf-8")),
    }


def _schema_registry() -> tuple[dict[str, dict[str, Any]], Registry]:
    schemas = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in (ROOT / "schemas").glob("*.schema.json")
    }
    registry = Registry().with_resources(
        [(schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()]
    )
    return schemas, registry


def _copy_frozen_inputs(target: Path) -> FrozenRoadInputs:
    inputs = FrozenRoadInputs(ROOT)
    copied = FrozenRoadInputs(target)
    for source, destination in [
        (inputs.fixture, copied.fixture),
        (inputs.evidence, copied.evidence),
        (inputs.proposal, copied.proposal),
        (inputs.decision, copied.decision),
        (inputs.approval, copied.approval),
        (inputs.authorization, copied.authorization),
    ]:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return copied


def _rehash_authorization(value: dict[str, Any]) -> dict[str, Any]:
    value["authorization_sha256"] = authorization_sha256(value)
    return value


def test_at01_through_at06_canonical_environment_and_frozen_identities(executed) -> None:
    _, _, receipt, _ = executed
    assert file_sha256(ARCHIVE) == EXPECTED_ARCHIVE_SHA256
    assert receipt["authorization"]["sha256"] == EXPECTED_AUTHORIZATION_SHA256
    assert receipt["frozen_identities"] == {
        "road01_package_sha256": "b5df3f57c33843f354371206c937f52d37ddbbd9d047a31ad7c334532ce30e9a",
        "road01_fixture_sha256": "b01e261971f65cbfc127aed4f1ba17b01b194dd89f256d3c024170c1dc7338f0",
        "road02_proposal_sha256": "3d45d1ed039c2af1aa7f050fa1e3c22158c891390c001285054b05a02959ce06",
        "road02_decision_sha256": "0d671b1fed3f4b19e4204e745bdcb13f872f3a00dcb4ef5050a091a14065e090",
        "road03_approval_sha256": "f333defee511e0ae82702444d18befe2f9e115d75608ab61a5c20f91c52f2f07",
        "road03_authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
    }


@pytest.mark.parametrize(
    ("path_name", "mutate", "rehash"),
    [
        (
            "authorization",
            lambda value: value["bindings"].__setitem__("class_code", "9420300"),
            _rehash_authorization,
        ),
        (
            "proposal",
            lambda value: value["bindings"].__setitem__("class_code", "9420300"),
            lambda value: value.__setitem__("proposal_sha256", proposal_sha256(value)) or value,
        ),
        (
            "decision",
            lambda value: value["bindings"].__setitem__("class_code", "9420300"),
            lambda value: value.__setitem__("decision_sha256", decision_sha256(value)) or value,
        ),
        (
            "fixture",
            lambda value: value["road_identity"].__setitem__("class_code", "9420300"),
            lambda value: value,
        ),
    ],
)
def test_at08_through_at14_rehashed_frozen_changes_fail_closed(
    tmp_path: Path, path_name: str, mutate, rehash
) -> None:
    inputs = _copy_frozen_inputs(tmp_path)
    path = getattr(inputs, path_name)
    value = json.loads(path.read_text(encoding="utf-8"))
    mutate(value)
    value = rehash(value)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    verifier = FrozenRoadAuthorizationVerifier(inputs)
    authorization = json.loads(inputs.authorization.read_text(encoding="utf-8"))
    with pytest.raises(RoadExecutionError):
        verifier.verify(authorization, observed_archive_sha256=EXPECTED_ARCHIVE_SHA256)


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "extra",
        "replacement",
        "reorder",
        "route",
        "class",
        "archive_binding",
        "fixture_binding",
        "road01_binding",
        "portrayal",
        "extra_portrayal",
        "permission",
        "nonexecutable",
    ],
)
def test_at09_through_at22_authorized_scope_changes_fail(change: str) -> None:
    authorization = _authorization()
    if change == "missing":
        authorization["bindings"]["ordered_source_ids"].pop()
    elif change == "extra":
        authorization["bindings"]["ordered_source_ids"].append("K0000009999")
    elif change == "replacement":
        authorization["bindings"]["ordered_source_ids"][1] = "K0000009999"
    elif change == "reorder":
        authorization["bindings"]["ordered_source_ids"].reverse()
    elif change == "route":
        authorization["bindings"]["route_identity"] = "changed"
    elif change == "class":
        authorization["bindings"]["class_code"] = "9420300"
    elif change == "archive_binding":
        authorization["bindings"]["source_archive_sha256"] = "0" * 64
    elif change == "fixture_binding":
        authorization["bindings"]["fixture_sha256"] = "0" * 64
    elif change == "road01_binding":
        authorization["bindings"]["road01_package_sha256"] = "0" * 64
    elif change == "portrayal":
        authorization["capability"]["allowed_changes"]["shield_code"] = "9490004"
    elif change == "extra_portrayal":
        authorization["capability"]["allowed_changes"]["line_width"] = 4
    elif change == "permission":
        authorization["permissions"]["topology_repair_allowed"] = True
    else:
        authorization["capability"]["execution_allowed"] = False
    _rehash_authorization(authorization)
    verifier = FrozenRoadAuthorizationVerifier(FrozenRoadInputs(ROOT))
    with pytest.raises(RoadExecutionError):
        verifier.verify(authorization, observed_archive_sha256=EXPECTED_ARCHIVE_SHA256)


def test_at12_archive_hash_mismatch_fails_before_execution(tmp_path: Path) -> None:
    wrong = tmp_path / "wrong.zip"
    wrong.write_bytes(b"not the authorized archive")
    engine = _engine(tmp_path / "runtime", archive=wrong)
    with pytest.raises(RoadExecutionError) as caught:
        engine.execute(_authorization(), "wrong-archive-key")
    assert caught.value.code == "source_archive_hash_mismatch"
    assert not (tmp_path / "runtime/executions").exists()


def test_at15_through_at22_exact_layer_scope_order_route_and_class(executed) -> None:
    _, storage, receipt, _ = executed
    root = storage / "executions" / receipt["execution_id"]
    source = json.loads((root / "data/road-centreline-source.geojson").read_text(encoding="utf-8"))
    assert source["nma:provenance"]["source_layer"] == "K14_ROAD"
    assert [feature["id"] for feature in source["features"]] == list(EXPECTED_SEGMENT_IDS)
    assert len(source["features"]) == 3
    for feature in source["features"]:
        assert feature["properties"]["TERRAINID"] == EXPECTED_CLASS_CODE
        assert feature["properties"]["ROADNUM"] == "縣126"
        assert feature["properties"]["ROADNAME"] == "中山街"


def test_at23_through_at34_geometry_is_native_and_projection_is_separate(executed) -> None:
    _, storage, receipt, _ = executed
    artifacts = _execution_artifacts(storage, receipt["execution_id"])
    geometry = artifacts["plan"]["source"]["geometry"]
    assert [item["source_vertex_count"] for item in geometry] == [4, 3, 4]
    assert [item["runtime_vertex_count"] for item in geometry] == [4, 3, 4]
    assert all(item["source_geometry_type"] == "LineString" for item in geometry)
    assert all(item["source_crs"] == "TWD97[2020]_TM121" for item in geometry)
    assert all(item["runtime_crs"] == "EPSG:4326" for item in geometry)
    assert all(
        item["source_geometry_sha256"] != item["runtime_geometry_sha256"] for item in geometry
    )
    source = json.loads(
        (
            storage / "executions" / receipt["execution_id"] / "data/road-centreline-source.geojson"
        ).read_text()
    )
    runtime = json.loads(
        (
            storage
            / "executions"
            / receipt["execution_id"]
            / "data/road-centreline-runtime.geojson"
        ).read_text()
    )
    assert [len(item["geometry"]["coordinates"]) for item in source["features"]] == [4, 3, 4]
    assert [len(item["geometry"]["coordinates"]) for item in runtime["features"]] == [4, 3, 4]


@pytest.mark.parametrize(
    "forbidden",
    [
        "snap",
        "simplify",
        "buffer",
        "offset",
        "polygon",
        "road edge",
        "roada",
        "densify",
        "smooth",
        "merge",
        "split",
    ],
)
def test_at26_through_at33_no_unauthorized_geometry_operation(executed, forbidden: str) -> None:
    _, storage, receipt, _ = executed
    plan = _execution_artifacts(storage, receipt["execution_id"])["plan"]
    assert forbidden not in json.dumps(plan["runtime_translation"], ensure_ascii=False).casefold()


def test_at35_through_at42_portrayal_is_exact_and_shield_is_truthful(executed) -> None:
    _, storage, receipt, _ = executed
    artifacts = _execution_artifacts(storage, receipt["execution_id"])
    assert artifacts["plan"]["portrayal"] == EXPECTED_PORTRAYAL
    bundle = artifacts["bundle"]
    assert bundle["shield_binding"] == {
        "shield_code": "9490005",
        "shield_orientation": "road-parallel",
        "status": "semantic_binding_only",
        "resolver_identity": None,
        "resolved_artifact_sha256": None,
    }
    assert bundle["layers"][0]["layout"] == {
        "symbol-placement": "line",
        "text-field": ["literal", "中山街"],
    }
    assert "icon" not in json.dumps(bundle, ensure_ascii=False).casefold()
    assert "paint" not in bundle["layers"][0]


def test_at43_through_at47_generated_artifacts_validate_against_closed_schemas(executed) -> None:
    _, storage, receipt, observation = executed
    artifacts = _execution_artifacts(storage, receipt["execution_id"])
    schemas, registry = _schema_registry()
    pairs = {
        "road-execution-plan-v1.0.schema.json": artifacts["plan"],
        "road-derived-portrayal-v1.0.schema.json": artifacts["derived"],
        "road-runtime-bundle-v1.0.schema.json": artifacts["bundle"],
        "road-execution-receipt-v1.0.schema.json": artifacts["receipt"],
        "road-rollback-manifest-v1.0.schema.json": artifacts["rollback"],
        "road-runtime-observation-v1.0.schema.json": observation,
    }
    for name, value in pairs.items():
        Draft202012Validator.check_schema(schemas[name])
        Draft202012Validator(schemas[name], registry=registry).validate(value)


def test_at43_closed_schemas_reject_extra_properties(executed) -> None:
    _, storage, receipt, _ = executed
    plan = _execution_artifacts(storage, receipt["execution_id"])["plan"]
    plan["unreviewed"] = True
    schemas, registry = _schema_registry()
    errors = list(
        Draft202012Validator(
            schemas["road-execution-plan-v1.0.schema.json"], registry=registry
        ).iter_errors(plan)
    )
    assert errors


def test_at48_through_at50_two_root_determinism_and_timestamps(tmp_path: Path) -> None:
    first_engine = _engine(tmp_path / "first", day=18)
    second_engine = _engine(tmp_path / "nested/second", day=20)
    first = first_engine.execute(_authorization(), "two-root-key")
    second = second_engine.execute(_authorization(), "two-root-key")
    assert first["completed_at"] != second["completed_at"]
    assert first["execution_id"] == second["execution_id"]
    assert first["receipt_sha256"] == second["receipt_sha256"]
    first_artifacts = _execution_artifacts(tmp_path / "first", first["execution_id"])
    second_artifacts = _execution_artifacts(tmp_path / "nested/second", second["execution_id"])
    for key, hash_name in [
        ("plan", "execution_plan_sha256"),
        ("derived", "artifact_sha256"),
        ("bundle", "bundle_sha256"),
        ("rollback", "rollback_manifest_sha256"),
    ]:
        assert first_artifacts[key][hash_name] == second_artifacts[key][hash_name]


def test_at51_failure_before_promotion_cleans_staging(monkeypatch, tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    monkeypatch.setattr(
        engine,
        "_extract_geometry",
        lambda stage: (_ for _ in ()).throw(
            RoadExecutionError("forced", code="runtime_translation_failed")
        ),
    )
    with pytest.raises(RoadExecutionError, match="forced"):
        engine.execute(_authorization(), "failure-cleanup-key")
    assert not list((tmp_path / ".staging").glob("*"))
    assert not (tmp_path / "executions").exists()
    assert not (tmp_path / "ledger").exists()


def test_at52_process_safe_lock_allows_at_most_one_promotion(tmp_path: Path) -> None:
    engines = [_engine(tmp_path), _engine(tmp_path)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(
            pool.map(
                lambda engine: engine.execute(_authorization(), "concurrent-road04-key"), engines
            )
        )
    assert receipts[0] == receipts[1]
    assert len(list((tmp_path / "executions").iterdir())) == 1
    assert len(list((tmp_path / "ledger").glob("*.json"))) == 1


def test_at53_replay_returns_same_receipt_and_new_key_is_rejected(executed) -> None:
    engine, storage, receipt, _ = executed
    replay = engine.execute(_authorization(), "road04-session-key")
    assert replay == receipt
    assert len(list((storage / "executions").iterdir())) == 1
    with pytest.raises(RoadExecutionError) as caught:
        engine.execute(_authorization(), "different-road04-key")
    assert caught.value.code == "authorization_already_consumed"


def test_at54_at55_at57_rollback_is_bounded_audited_and_idempotent(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    receipt = engine.execute(_authorization(), "rollback-road04-key")
    execution = tmp_path / "executions" / receipt["execution_id"]
    receipt_file_hash = file_sha256(execution / "receipt.json")
    first = engine.rollback_execution(receipt["execution_id"])
    second = engine.rollback_execution(receipt["execution_id"])
    assert first == second
    assert first["status"] == "rolled_back"
    assert file_sha256(execution / "receipt.json") == receipt_file_hash
    assert (execution / "plan.json").is_file()
    assert (execution / "rollback-manifest.json").is_file()
    assert not (execution / "bundle.json").exists()
    assert not (execution / "derived-portrayal.json").exists()
    assert not (execution / "data").exists()


def test_at56_rollback_hash_mismatch_fails_before_any_removal(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    receipt = engine.execute(_authorization(), "rollback-mismatch-key")
    execution = tmp_path / "executions" / receipt["execution_id"]
    bundle_path = execution / "bundle.json"
    original = bundle_path.read_bytes()
    bundle_path.write_bytes(original + b" ")
    with pytest.raises(RoadExecutionError) as caught:
        engine.rollback_execution(receipt["execution_id"])
    assert caught.value.code == "rollback_precondition_failed"
    assert (execution / "derived-portrayal.json").is_file()
    assert (execution / "data/road-centreline-source.geojson").is_file()


def test_at58_through_at61_source_frozen_and_canonical_runtime_unchanged(executed) -> None:
    _, storage, receipt, _ = executed
    assert file_sha256(ARCHIVE) == EXPECTED_ARCHIVE_SHA256
    assert (
        file_sha256(
            ROOT / "data/specifications/nma-road-hero-road-03-golden-authorization-v1.0.json"
        )
        == "ba010892193145cad8f6ee8d3331824f3a972cdb422ca902e6bd9c04801e9283"
    )
    artifacts = _execution_artifacts(storage, receipt["execution_id"])
    assert artifacts["derived"]["governance"] == {
        "source_mutation_performed": False,
        "topology_repair_performed": False,
        "roada_execution_performed": False,
        "road_edge_derivation_performed": False,
    }
    assert artifacts["bundle"]["canonical_runtime_mutation_performed"] is False


def test_at45_runtime_observation_binds_expected_candidate(executed) -> None:
    _, _, receipt, observation = executed
    assert observation["execution_id"] == receipt["execution_id"]
    assert observation["observed_feature_count"] == 3
    assert observation["loaded_candidate_representation"] is True
    assert observation["status"] == "verified"
    assert observation["final_qa"] is False


@pytest.mark.parametrize(
    "forbidden",
    [
        "route",
        "segments",
        "geometry",
        "source_path",
        "output_path",
        "shield",
        "annotation",
        "roles",
        "roada",
    ],
)
def test_api_rejects_client_controlled_road_execution_parameters(
    tmp_path: Path, forbidden: str
) -> None:
    engine = _engine(tmp_path)
    with pytest.raises(RoadExecutionError, match="only"):
        engine.execute_by_id(
            {
                "authorization_id": AUTHORIZATION_ID,
                "idempotency_key": "bounded-road-key",
                forbidden: "forbidden",
            }
        )


def test_server_declares_minimal_road_execution_routes() -> None:
    spec = importlib.util.spec_from_file_location("road04_api_server", SERVER_PATH)
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = server
    spec.loader.exec_module(server)
    source = SERVER_PATH.read_text(encoding="utf-8")
    assert "/api/road/executions" in source
    assert "/(bundle|data)" in source
    assert "/observations" in source
    assert "/rollback" in source
    assert server.ROAD_EXECUTIONS.authorization_store is server.ROAD_AUTHORIZATIONS


def test_at65_all_new_schemas_are_draft_2020_12_and_closed() -> None:
    schemas, _ = _schema_registry()
    for name in [
        "road-execution-plan-v1.0.schema.json",
        "road-derived-portrayal-v1.0.schema.json",
        "road-runtime-bundle-v1.0.schema.json",
        "road-runtime-observation-v1.0.schema.json",
        "road-execution-receipt-v1.0.schema.json",
        "road-rollback-manifest-v1.0.schema.json",
    ]:
        schema = schemas[name]
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False
        Draft202012Validator.check_schema(schema)


def test_at66_goldens_validate_and_match_real_execution(executed) -> None:
    _, storage, receipt, observation = executed
    actual = _execution_artifacts(storage, receipt["execution_id"])
    actual["observation"] = observation
    schemas, registry = _schema_registry()
    schema_names = {
        "plan": "road-execution-plan-v1.0.schema.json",
        "derived": "road-derived-portrayal-v1.0.schema.json",
        "bundle": "road-runtime-bundle-v1.0.schema.json",
        "receipt": "road-execution-receipt-v1.0.schema.json",
        "rollback": "road-rollback-manifest-v1.0.schema.json",
        "observation": "road-runtime-observation-v1.0.schema.json",
    }
    identity_fields = {
        "plan": "execution_plan_sha256",
        "derived": "artifact_sha256",
        "bundle": "bundle_sha256",
        "receipt": "receipt_sha256",
        "rollback": "rollback_manifest_sha256",
        "observation": "observation_sha256",
    }
    for key, golden_name in GOLDEN_NAMES.items():
        golden = json.loads(
            (ROOT / "data/specifications" / golden_name).read_text(encoding="utf-8")
        )
        Draft202012Validator(schemas[schema_names[key]], registry=registry).validate(golden)
        assert golden[identity_fields[key]] == actual[key][identity_fields[key]]


def test_receipt_and_observation_hashes_exclude_timestamps() -> None:
    receipt = {"value": "stable", "completed_at": "2026-08-19T00:00:00Z"}
    first = _hash_record(receipt, "sha256", ignored_identity_fields=("completed_at",))
    receipt["completed_at"] = "2027-01-01T00:00:00Z"
    second = _hash_record(receipt, "sha256", ignored_identity_fields=("completed_at",))
    assert first["sha256"] == second["sha256"]

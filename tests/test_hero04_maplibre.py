from pathlib import Path

from hero04_support import make_authorization, make_engine
from nma.school_hero_execution import canonical_sha256


def test_execution_plan_is_deterministic_and_has_no_client_gis_parameters(tmp_path: Path) -> None:
    engine = make_engine(tmp_path)
    authorization = make_authorization()
    plan_a = engine.build_plan(authorization, "exec-" + "a" * 24)
    plan_b = engine.build_plan(authorization, "exec-" + "a" * 24)
    assert plan_a == plan_b
    assert plan_a["plan_sha256"] == canonical_sha256(
        {key: value for key, value in plan_a.items() if key != "plan_sha256"}
    )
    assert plan_a["source_filter"] == {
        "field": "TERRAINID",
        "operator": "equals",
        "value": "9920103",
    }


def test_maplibre_bundle_uses_geojson_without_source_layer_and_scoped_ids(tmp_path: Path) -> None:
    engine = make_engine(tmp_path)
    plan = engine.build_plan(make_authorization(), "exec-" + "b" * 24)
    asset = {
        "asset_sha256": "1" * 64,
        "approved_operations_sha256": plan["portrayal_reference"]["approved_operations_sha256"],
        "values": {"color": "#1565c0", "opacity": 1.0, "scale": 1.0, "rotation": 0.0},
    }
    bundle = engine._build_bundle(plan["execution_id"], plan, asset)
    assert bundle["source"]["type"] == "geojson"
    assert bundle["layer"]["source"] == bundle["source"]["id"]
    assert "source-layer" not in str(bundle)
    assert plan["execution_id"] in bundle["source"]["id"]
    assert plan["execution_id"] in bundle["layer"]["id"]
    assert bundle["bundle_sha256"] == canonical_sha256(
        {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    )

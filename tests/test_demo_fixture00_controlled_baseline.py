from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

import pytest

from nma.core import canonical_sha256
from nma.ogr import read_vector_dataset
from nma.real_layer import (
    extract_reviewed_source_layers,
    file_sha256,
    inventory_shapefile_archive,
)


ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "data/specifications/nma-demo-controlled-fixture-baseline-v1.0.json"
DEFAULT_ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
EXPECTED_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
SCHOOL_LAYERS = (
    "J01_MARK",
    "J13_MARK",
    "J17_MARK",
    "K01_MARK",
    "K02_MARK",
    "K14_MARK",
)
ROAD_SEGMENTS = ("K0000004671", "K0000004913", "K0000005348")


def _record() -> dict:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def _archive() -> Path:
    configured = os.environ.get("NMA_CONTROLLED_FIXTURE_ARCHIVE")
    return Path(configured) if configured else DEFAULT_ARCHIVE


def _aggregate(layers: list[dict]) -> str:
    rows = sorted(
        (
            layer["layer_id"],
            component["extension"],
            component["sha256"],
        )
        for layer in layers
        for component in layer["components"]
    )
    payload = b"nma-controlled-demo-fixture-v1\n" + b"".join(
        f"{layer_id}\t{extension}\t{digest}\n".encode("utf-8")
        for layer_id, extension, digest in rows
    )
    return hashlib.sha256(payload).hexdigest()


def _finite_coordinates(value: object) -> bool:
    if isinstance(value, list):
        return bool(value) and all(_finite_coordinates(item) for item in value)
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def test_fixture_identity_is_deterministic_and_sidecars_are_complete() -> None:
    record = _record()
    school = record["school"]
    road = record["road"]

    assert _aggregate(school["layers"]) == school["aggregate_sha256"]
    assert _aggregate([road["layer"]]) == road["aggregate_sha256"]
    assert school["controlled_demo_fixture_identity"].endswith(school["aggregate_sha256"])
    assert road["controlled_demo_fixture_identity"].endswith(road["aggregate_sha256"])
    for layer in [*school["layers"], road["layer"]]:
        assert {part["extension"] for part in layer["components"]} == {
            ".cpg",
            ".dbf",
            ".prj",
            ".shp",
            ".shx",
        }
        assert all(len(part["sha256"]) == 64 for part in layer["components"])


def test_school_inventory_is_the_frozen_six_layer_fifteen_feature_contract() -> None:
    school = _record()["school"]

    assert [layer["layer_id"] for layer in school["layers"]] == list(SCHOOL_LAYERS)
    assert [layer["selected_feature_count"] for layer in school["layers"]] == [
        0,
        1,
        0,
        12,
        1,
        1,
    ]
    assert sum(layer["raw_feature_count"] for layer in school["layers"]) == 1464
    assert sum(layer["selected_feature_count"] for layer in school["layers"]) == 15
    assert all(layer["geometry_type"] == "Point" for layer in school["layers"])
    assert {field["name"] for field in school["field_contract"]} == {
        "MARKID",
        "TERRAINID",
        "MARKNAME1",
        "MDATE",
    }
    assert school["geometry_quality"]["invalid_geometry_count"] == 0
    assert school["geometry_quality"]["empty_geometry_count"] == 0
    assert school["geometry_quality"]["selected_missing_label_count"] == 0
    assert school["frozen_requirements"]["six_layer_count"] == "MATCH"
    assert school["frozen_requirements"]["selected_fifteen_feature_count"] == "MATCH"
    assert school["blocker"] == "FIXTURE COMPATIBLE — AUTHORIZATION BINDING BLOCKER"


def test_road_coordinates_and_frozen_geometry_commitments_are_present() -> None:
    road = _record()["road"]

    assert road["layer"]["layer_id"] == "K14_ROAD"
    assert road["layer"]["feature_count"] == 196
    assert [item["segment_id"] for item in road["authorized_segments"]] == list(ROAD_SEGMENTS)
    assert [item["vertex_count"] for item in road["authorized_segments"]] == [4, 3, 4]
    assert all(item["coordinate_array_present"] for item in road["authorized_segments"])
    assert [item["source_geometry_sha256"] for item in road["authorized_segments"]] == [
        "42616b9b91d91efd4582171b23ad70259156c586bef776098329cdd81aa8f800",
        "c075943948c1184493d41672f0ca00e610c90bfa7c721f24a645765dc48b9faf",
        "88ad286f2b368130e0870360acd07d1d79614d8005ee53eed966b8db6abd2cc6",
    ]
    assert all(item["valid"] and item["simple"] for item in road["authorized_segments"])
    assert road["frozen_requirements"]["native_coordinate_arrays"] == "MATCH"
    assert road["frozen_requirements"]["source_to_runtime_serialization"] == (
        "COMPATIBLE_WITH_SERIALIZATION"
    )


def test_demo_identity_cannot_impersonate_historical_identity_or_authorization() -> None:
    record = _record()
    separation = record["identity_separation"]
    historical_fixture = json.loads(
        (ROOT / "data/specifications/nma-road-hero-road-01-v1.0.json").read_text(encoding="utf-8")
    )
    historical_authorization = json.loads(
        (
            ROOT / "data/specifications/nma-road-hero-road-03-golden-authorization-v1.0.json"
        ).read_text(encoding="utf-8")
    )

    assert separation == {
        "historical_frozen_fixture_identity_is_controlled_demo_fixture_identity": False,
        "historical_production_authorization_is_demo_execution_authorization": False,
        "demo_identity_may_impersonate_historical_identity": False,
        "note": separation["note"],
    }
    assert (
        record["road"]["controlled_demo_fixture_identity"] != historical_fixture["fixture_sha256"]
    )
    assert (
        record["road"]["controlled_demo_fixture_identity"]
        != historical_authorization["authorization_sha256"]
    )


def test_graphrag_rule_nodes_and_rule_linked_attributes_are_available() -> None:
    record = _record()
    graph = json.loads(
        (ROOT / "data/knowledge/nma-canonical-graph-v0.4.json").read_text(encoding="utf-8")
    )
    nodes = {node["id"]: node for node in graph["nodes"]}

    for domain in (record["school"], record["road"]):
        assert domain["graphrag"]["suitability"] == "MATCH"
        assert set(domain["graphrag"]["required_nodes"]).issubset(nodes)
    assert {"TERRAINID", "MARKNAME1", "MARKID"}.issubset(
        record["school"]["graphrag"]["fixture_attributes_available"]
    )
    assert {"TERRAINID", "ROADSEGID", "ROADNUM", "ROADNAME"}.issubset(
        record["road"]["graphrag"]["fixture_attributes_available"]
    )
    assert nodes["portrayal-rule:doc01:9920103"]["properties"]["geometry_role"] == ("Point")
    assert nodes["portrayal-rule:doc01:9420400"]["properties"]["feature_code"] == ("9420400")
    assert nodes["portrayal-rule:doc01:9490005"]["properties"]["instruction"].endswith("道路平行")


def test_no_external_substitution_or_arbitrary_ingestion_claim_was_introduced() -> None:
    record = _record()
    scope = record["scope"]

    assert scope["arbitrary_geospatial_ingestion_claimed"] is False
    assert scope["external_data_substitution_performed"] is False
    assert scope["raw_fixture_redistributed"] is False
    assert record["reproducibility"]["external_open_data_required"] is False
    assert record["fixture_authority"]["package_sha256"] == EXPECTED_ARCHIVE_SHA256


@pytest.mark.skipif(
    not _archive().is_file() or not shutil.which("ogrinfo"),
    reason="The exact controlled fixture package and GDAL/OGR are required.",
)
def test_live_controlled_archive_matches_school_and_road_baseline() -> None:
    record = _record()
    archive = _archive()
    assert file_sha256(archive) == EXPECTED_ARCHIVE_SHA256
    inventory = inventory_shapefile_archive(archive, expected_sha256=EXPECTED_ARCHIVE_SHA256)
    live_components = {
        (layer["layer_id"], component["extension"]): component["sha256"]
        for layer in inventory["layers"]
        for component in layer["components"]
    }
    for layer in [*record["school"]["layers"], record["road"]["layer"]]:
        for component in layer["components"]:
            assert (
                live_components[(layer["layer_id"], component["extension"])]
                == (component["sha256"])
            )

    with tempfile.TemporaryDirectory(prefix="nma-demo-fixture00-") as temporary:
        sources, _ = extract_reviewed_source_layers(
            archive, [*SCHOOL_LAYERS, "K14_ROAD"], Path(temporary)
        )
        collections = {source.stem: read_vector_dataset(source)[0] for source in sources}

    school_selected = []
    for layer_id in SCHOOL_LAYERS:
        collection = collections[layer_id]
        selected = [
            feature
            for feature in collection["features"]
            if str(feature["properties"].get("TERRAINID")) == "9920103"
        ]
        school_selected.extend(selected)
        assert len(selected) == next(
            layer["selected_feature_count"]
            for layer in record["school"]["layers"]
            if layer["layer_id"] == layer_id
        )
    assert len(school_selected) == 15
    assert all(feature["geometry"]["type"] == "Point" for feature in school_selected)
    assert all(
        _finite_coordinates(feature["geometry"]["coordinates"]) for feature in school_selected
    )
    assert all(feature["properties"].get("MARKID") for feature in school_selected)
    assert all(feature["properties"].get("MARKNAME1") for feature in school_selected)

    road_features = {
        str(feature["properties"].get("ROADSEGID")): feature
        for feature in collections["K14_ROAD"]["features"]
    }
    for expected in record["road"]["authorized_segments"]:
        feature = road_features[expected["segment_id"]]
        geometry = feature["geometry"]
        assert geometry["type"] == "LineString"
        assert _finite_coordinates(geometry["coordinates"])
        assert len(geometry["coordinates"]) == expected["vertex_count"]
        assert canonical_sha256(geometry["coordinates"]) == expected["coordinate_array_sha256"]
        assert canonical_sha256(geometry) == expected["source_geometry_sha256"]
        assert str(feature["properties"]["TERRAINID"]) == "9420400"
        assert feature["properties"]["ROADNUM"] == "縣126"
        assert feature["properties"]["ROADNAME"] == "中山街"

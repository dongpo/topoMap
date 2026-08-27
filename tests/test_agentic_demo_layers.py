import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "nmaAgentDemo.html"
SERVER_PATH = ROOT / "scripts" / "run_nma_agent_server.py"
SPEC = importlib.util.spec_from_file_location("nma_agent_server_a05", SERVER_PATH)
assert SPEC and SPEC.loader
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


def test_a05_bundled_shapefile_has_required_parts_and_full_inspection() -> None:
    result = SERVER.inspect_bundled_dataset("school-points")
    inspection = result["inspection"]
    components = {item["extension"]: item for item in result["components"]}

    assert result["schema"] == "nma.dataset-inspection/1.0"
    assert result["ready"] is True
    assert result["dataset"] == {
        "id": "school-points",
        "label": "Bundled synthetic school points",
        "feature_code": "9920103",
        "synthetic": True,
    }
    assert all(components[extension]["present"] for extension in (".shp", ".shx", ".dbf", ".prj"))
    assert all(len(components[extension]["sha256"]) == 64 for extension in components)
    assert inspection["driver"] == "ESRI Shapefile"
    assert inspection["layer"] == "SCHOOL_POINT"
    assert inspection["feature_count"] == 12
    assert inspection["geometry_type"] == "Point"
    assert inspection["crs"] == "EPSG:3826"
    assert {field["name"] for field in inspection["fields"]} == {
        "MARKID",
        "TERRAINID",
        "MARKNAME1",
    }


def test_a05_exports_browser_safe_geojson_with_provenance() -> None:
    collection = SERVER.export_bundled_geojson("school-points")
    provenance = collection["nma:provenance"]

    assert collection["type"] == "FeatureCollection"
    assert len(collection["features"]) == 12
    assert {feature["properties"]["TERRAINID"] for feature in collection["features"]} == {"9920103"}
    assert all(
        120 < feature["geometry"]["coordinates"][0] < 122
        and 20 < feature["geometry"]["coordinates"][1] < 27
        for feature in collection["features"]
    )
    assert provenance["driver"] == "ESRI Shapefile"
    assert provenance["source_crs"] == "EPSG:3826"
    assert provenance["output_crs"] == "EPSG:4326"
    assert provenance["read_only_source"] is True
    assert provenance["synthetic"] is True
    assert len(provenance["components"]) == 5


@pytest.mark.skipif(
    not SERVER.PRIVATE_SCHOOL_ARCHIVE.is_file(),
    reason="User-provided production archive is intentionally not redistributed",
)
def test_local_private_archive_produces_real_school_layer_without_redistribution() -> None:
    dataset = SERVER.prepare_private_real_school_dataset()
    assert dataset is not None
    assert dataset["synthetic"] is False
    assert dataset["source_archive_sha256"] == SERVER.PRIVATE_SCHOOL_ARCHIVE_SHA256
    assert dataset["source_layers"] == [
        "J01_MARK",
        "J13_MARK",
        "J17_MARK",
        "K01_MARK",
        "K02_MARK",
        "K14_MARK",
    ]
    original = SERVER.BUNDLED_DATASETS["school-points"]
    try:
        SERVER.BUNDLED_DATASETS["school-points"] = dataset
        inspection = SERVER.inspect_bundled_dataset("school-points")
        collection = SERVER.export_bundled_geojson("school-points")
    finally:
        SERVER.BUNDLED_DATASETS["school-points"] = original

    assert inspection["inspection"]["feature_count"] == 15
    assert inspection["inspection"]["crs"] == "EPSG:3826"
    assert len(collection["features"]) == 15
    assert collection["nma:provenance"]["synthetic"] is False
    assert collection["nma:provenance"]["redistributed"] is False
    assert {feature["properties"]["TERRAINID"] for feature in collection["features"]} == {
        "9920103"
    }


def test_a05_server_rejects_unregistered_dataset_paths() -> None:
    with pytest.raises(SERVER.AgentError) as error:
        SERVER.inspect_bundled_dataset("../../private")

    assert error.value.code == "dataset_not_found"
    assert error.value.status == 404


def test_a05_page_shows_inspection_and_proposal_before_execution() -> None:
    html = HTML.read_text(encoding="utf-8")
    prepare_body = html.split("async function prepareLayerProposal()", 1)[1].split(
        "function addApprovedSymbolImage", 1
    )[0]

    assert 'id="layer-workshop"' in html
    assert "Required Shapefile" not in html  # Server owns component enforcement.
    assert "/api/datasets/school-points/inspect" in html
    assert "Inspection complete; no source or layer has been created." in html
    assert "Approve and create layer" in html
    assert "A separate explicit approval is required before execution." in html
    assert "map.addSource" not in prepare_body


def test_a05_requires_explicit_layer_approval_and_preserves_provenance() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "function isExplicitLayerApproval(text)" in html
    assert 'layerProposal?.status==="proposed"&&isExplicitLayerApproval(rawMessage)' in html
    assert 'createApprovedLayer("natural-language-explicit-approval")' in html
    assert "approval_source:approvalSource" in html
    assert "approved_symbol_version:layerProposal.style.version" in html
    assert '"nma:role":"approved-dynamic-symbol"' in html
    assert '"nma:provenance":provenance' in html
    assert "exported feature count mismatch" in html
    assert "exported feature code mismatch" in html
    assert "renderedSymbols===expected" in html
    assert "render_mode:renderMode" in html
    assert '"maplibre-marker-fallback"' in html
    assert (
        "addApprovedMarkers(collection,layerProposal.style,mapping,showLabels,"
        "layerProposal.decision.feature.name)" in html
    )
    assert "marker.getElement().isConnected" in html
    assert '"visibility":showLabels?"visible":"none"' in html
    assert "synthetic_labels_suppressed:!showLabels" in html
    assert "labelMarkup=showLabels&&sourceLabel" in html
    assert "generated test points verify field mapping and symbol rendering" in html
    assert "NMA示範小學A" not in html


def test_a05_uses_official_nlsc_wmts_without_service_worker_caching() -> None:
    html = HTML.read_text(encoding="utf-8")
    worker = (ROOT / "nmaDemoWorker.js").read_text(encoding="utf-8")

    assert (
        'const NLSC_EMAP_TILES="https://wmts.nlsc.gov.tw/wmts/EMAP/default/'
        'GoogleMapsCompatible/{z}/{y}/{x}"' in html
    )
    assert 'id:"nlsc-emap-basemap"' in html
    assert '"nma:cache_policy":"network-only; no bulk caching"' in html
    assert "wmts.nlsc.gov.tw" not in worker


def test_a05_fixture_source_is_explicitly_synthetic() -> None:
    source = json.loads(
        (ROOT / "data/fixtures-source/school-points/school-points.geojson").read_text(
            encoding="utf-8"
        )
    )

    assert source["name"] == "SCHOOL_POINT"
    assert len(source["features"]) == 12
    assert all(
        feature["properties"]["MARKNAME1"].startswith("NMA合成測試點")
        for feature in source["features"]
    )

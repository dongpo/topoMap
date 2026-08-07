import importlib.util
import json
from pathlib import Path
import sys

from nma.demo_contract import check_demo_contract


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "nmaAgentDemo.html"
CATALOG = ROOT / "data/demo/pmtiles-capability-catalog.json"
CONTRACT = ROOT / "data/demo/five-scene-demo.json"
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"
SPEC = importlib.util.spec_from_file_location("nma_agent_server_a06", SERVER_PATH)
assert SPEC and SPEC.loader
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


def test_a06_declares_compliant_nlsc_primary_and_interactive_local_fallback() -> None:
    html = HTML.read_text(encoding="utf-8")
    worker = (ROOT / "nmaDemoWorker.js").read_text(encoding="utf-8")

    assert (
        'const NLSC_EMAP_TILES="https://wmts.nlsc.gov.tw/wmts/EMAP/default/'
        'GoogleMapsCompatible/{z}/{y}/{x}"' in html
    )
    assert "內政部國土測繪中心" in html
    assert '"nma:cache_policy":"network-only; no bulk caching"' in html
    assert (
        'const FORCED_LOCAL_BASEMAP=new URLSearchParams(location.search).get("basemap")==="local"'
        in html
    )
    assert "function activateLocalBasemapFallback(reason)" in html
    assert 'map.setLayoutProperty("nlsc-emap-basemap","visibility","none")' in html
    assert "local PMTiles basemap fallback" in html
    assert "wmts.nlsc.gov.tw" not in worker


def test_a06_school_acceptance_connects_every_supervised_gate_to_real_data() -> None:
    html = HTML.read_text(encoding="utf-8")
    inspection = SERVER.inspect_bundled_dataset("school-points")
    collection = SERVER.export_bundled_geojson("school-points")

    required_steps = {
        "function executeAgentRoute(args,rawMessage)",
        "function renderKnowledgeGraph(decision)",
        "function renderSymbolWorkshop(decision)",
        "function approveStyleRevision()",
        "async function prepareLayerProposal()",
        "async function createApprovedLayer(approvalSource)",
        "Approve and create layer",
        "map.addSource(sourceId",
        "map.addLayer({id:layerId",
    }
    assert required_steps <= {step for step in required_steps if step in html}
    assert inspection["ready"] is True
    assert inspection["inspection"]["feature_count"] == 3
    assert collection["nma:provenance"]["source_crs"] == "EPSG:3826"
    assert collection["nma:provenance"]["output_crs"] == "EPSG:4326"
    assert collection["nma:provenance"]["read_only_source"] is True


def test_a06_non_golden_highway_uses_shared_catalog_and_map_pipeline_without_evidence() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    html = HTML.read_text(encoding="utf-8")
    pilot = next(item for item in catalog["capabilities"] if item["code"] == "9420101")
    golden_codes = {scene["input"]["feature_code"] for scene in contract["scenes"]}

    assert pilot["status"] == "implementation-only"
    assert pilot["evidence_available"] is False
    assert pilot["code"] not in golden_codes
    assert 'const IMPLEMENTATION_PILOT_CODE="9420101"' in html
    assert "function compileImplementationPilotLayers()" in html
    assert "function applyImplementationCapabilityToMap(item)" in html
    assert '"nma:evidence":null' in html
    assert "evidence_used:false" in html
    assert "0 authoritative nodes" in html
    assert "preview-enabled" in html
    assert "Implementation map preview" in html
    assert "It does not reuse the previous supervised Shapefile result" in html


def test_a06_preserves_all_five_golden_scene_controls() -> None:
    result = check_demo_contract(CONTRACT)

    assert result["status"] == "passed"
    assert result["scene_count"] == 5
    assert result["negative_control"] == "passed"

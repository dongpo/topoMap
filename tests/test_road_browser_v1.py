from __future__ import annotations

import json
from pathlib import Path
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "nmaRoadDemoV1.html"
APP = ROOT / "nmaRoadDemoV1.js"
UPLOAD = ROOT / "assets/js/nma-road-upload-v1.js"
PROBE = ROOT / "tests/browser_road_upload_probe.mjs"


def archive(tmp_path: Path, components: tuple[str, ...]) -> Path:
    target = tmp_path / "road-user.zip"
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as output:
        for extension in components:
            output.writestr(f"K14_ROAD{extension}", f"fixture-{extension}".encode())
    return target


def probe(target: Path, mode: str = "direct") -> dict:
    completed = subprocess.run(
        ["node", str(PROBE), str(target), mode],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_road_archive_and_line_observation_accept_user_road_components(tmp_path: Path) -> None:
    result = probe(archive(tmp_path, (".shp", ".shx", ".dbf", ".prj", ".cpg")))
    assert result == {
        "status": "ready",
        "layerName": "k14_road",
        "featureCount": 4,
        "totalVertexCount": 12,
        "vertexCounts": [3, 3, 3, 3],
        "classCounts": {"9420101": 1, "9420400": 1, "9420700": 1, "9420802": 1},
        "mappingStatus": "session-human-confirmed",
        "rawFeatureBytesTransmitted": False,
    }


def test_road_parent_class_and_terrainid_require_explicit_questions(tmp_path: Path) -> None:
    result = probe(archive(tmp_path, (".shp", ".shx", ".dbf", ".prj")), "parent")
    assert result == {
        "status": "clarification-required",
        "clarificationTypes": ["schema-field-mapping", "parent-classification"],
        "parentOptions": ["9420101", "9420102"],
    }


def test_road_archive_stops_without_prj(tmp_path: Path) -> None:
    result = probe(archive(tmp_path, (".shp", ".shx", ".dbf")))
    assert result["status"] == "rejected"
    assert result["code"] == "required-component-missing"
    assert ".prj" in result["message"]


def test_road_adapter_keeps_parent_hierarchy_and_mapping_questions_explicit() -> None:
    upload = UPLOAD.read_text(encoding="utf-8")
    assert "ROADCLASS2" in upload
    assert "TERRAINID" in upload
    assert "schema-field-mapping" in upload
    assert "parent-classification" in upload
    assert '"9420100"' in upload and '"9420101"' in upload and '"9420102"' in upload
    assert '"9420200"' in upload and '"9420201"' in upload and '"9420202"' in upload
    assert '"9420800"' in upload and '"9420801"' in upload and '"9420802"' in upload
    assert "__NMA_ROAD_CLASS" in upload
    assert "rawFeatureBytesTransmitted: false" in upload


def test_road_application_is_staged_and_only_sends_governed_observations() -> None:
    html = HTML.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    for step in ("upload", "evidence", "authorize", "map", "verify"):
        assert f'data-panel="{step}"' in html
        assert f'data-step="{step}"' in html
    assert "mapping 問題" in html
    assert 'type="file"' in html
    assert "download" not in html.lower()
    for endpoint in (
        "road-portrayal/proposals",
        "road-portrayal/authorizations",
        "road-portrayal/compile",
        "road-portrayal/observations",
        "road-portrayal/verify",
    ):
        assert endpoint in app
    assert "state.local.inspection.collection" in app
    assert "raw_feature_bytes_transmitted: false" in app
    assert '"browser-render-verified"' in app
    assert "queryRenderedFeatures" in app
    assert "surveyed-width" in html.lower()
    assert "production activation" in html.lower()
    assert 'new URL(path.replace(/^\\//, ""), apiRoot)' in app
    assert "new URL(fixture, document.baseURI)" in app
    assert '["127.0.0.1", "localhost"].includes(location.hostname)' in app
    assert "qaFixture" not in html

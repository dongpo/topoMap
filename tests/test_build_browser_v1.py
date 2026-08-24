from __future__ import annotations

import json
from pathlib import Path
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "nmaBuildDemoV1.html"
APP = ROOT / "nmaBuildDemoV1.js"
UPLOAD = ROOT / "assets/js/nma-build-upload-v1.js"
PROBE = ROOT / "tests/browser_build_upload_probe.mjs"


def archive(tmp_path: Path, components: tuple[str, ...]) -> Path:
    target = tmp_path / "build-user.zip"
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as output:
        for extension in components:
            output.writestr(f"J13_BUILD{extension}", f"fixture-{extension}".encode())
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


def test_build_archive_and_polygon_observation_accept_reviewed_components(tmp_path: Path) -> None:
    result = probe(archive(tmp_path, (".shp", ".shx", ".dbf", ".prj", ".cpg")))
    assert result == {
        "status": "ready",
        "layerName": "j13_build",
        "featureCount": 4,
        "totalVertexCount": 20,
        "totalRingCount": 4,
        "vertexCounts": [5, 5, 5, 5],
        "zFeatureCount": 4,
        "classCounts": {"9310100": 1, "9310103": 1, "9310200": 1, "9310300": 1},
        "schemaProfile": "multidimensional-build-v4",
        "rawFeatureBytesTransmitted": False,
    }


def test_build_parent_class_requires_question_instead_of_guess(tmp_path: Path) -> None:
    result = probe(archive(tmp_path, (".shp", ".shx", ".dbf", ".prj")), "parent")
    assert result == {
        "status": "clarification-required",
        "clarificationTypes": ["parent-classification"],
        "parentOptions": ["9310100", "9310200", "9310300"],
    }


def test_build_archive_stops_without_prj(tmp_path: Path) -> None:
    result = probe(archive(tmp_path, (".shp", ".shx", ".dbf")))
    assert result["status"] == "rejected"
    assert result["code"] == "required-component-missing"
    assert ".prj" in result["message"]


def test_build_adapter_preserves_official_names_schema_and_z_boundary() -> None:
    upload = UPLOAD.read_text(encoding="utf-8")
    for code, name in (
        ("9310100", "永久性建物"),
        ("9310103", "無牆建物"),
        ("9310200", "建築中建物"),
        ("9310300", "臨時性建物"),
    ):
        assert code in upload and name in upload
    for field in ("BUILD_ID", "TERRAINID", "BUILD_STR", "BUILD_NO", "BUILD_H", "GROUP_ID", "MDATE"):
        assert field in upload
    assert "filename + BUILD_ID" in upload
    assert "sourceDimension" in upload
    assert "self-intersecting-ring" in upload
    assert "rawFeatureBytesTransmitted: false" in upload


def test_build_application_is_staged_and_sends_only_governed_observation() -> None:
    html = HTML.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    for step in ("upload", "evidence", "authorize", "map", "verify"):
        assert f'data-panel="{step}"' in html
        assert f'data-step="{step}"' in html
    assert 'type="file"' in html
    assert "download" not in html.lower()
    for endpoint in (
        "build-portrayal/proposals",
        "build-portrayal/authorizations",
        "build-portrayal/compile",
        "build-portrayal/observations",
        "build-portrayal/verify",
    ):
        assert endpoint in app
    assert "state.local.inspection.collection" in app
    assert "raw_feature_bytes_transmitted: false" in app
    assert '"browser-render-verified"' in app
    assert "nma-build-hatch-diagonal" in app
    assert 'new URL(path.replace(/^\\//, ""), apiRoot)' in app
    assert "new URL(fixture, document.baseURI)" in app
    assert '["127.0.0.1", "localhost"].includes(location.hostname)' in app
    assert "qaFixture" not in html

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "nmaSchoolDemoV1.html"
APP = ROOT / "nmaSchoolDemoV1.js"
UPLOAD = ROOT / "assets/js/nma-school-upload-v1.js"
PROBE = ROOT / "tests/browser_school_upload_probe.mjs"


def archive(tmp_path: Path, components: tuple[str, ...]) -> Path:
    target = tmp_path / "school-user.zip"
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as output:
        for extension in components:
            output.writestr(f"J01_MARK{extension}", f"fixture-{extension}".encode())
    return target


def probe(target: Path) -> dict:
    completed = subprocess.run(
        ["node", str(PROBE), str(target)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_browser_archive_gate_accepts_exact_mark_components_and_all_six_classes(
    tmp_path: Path,
) -> None:
    result = probe(archive(tmp_path, (".shp", ".shx", ".dbf", ".prj", ".cpg")))
    assert result == {
        "status": "pass",
        "layerName": "j01_mark",
        "requiredComponents": 4,
        "optionalComponents": 1,
        "featureCount": 6,
        "observedClassCounts": {
            code: 1
            for code in [
                "9920101",
                "9920102",
                "9920103",
                "9920104",
                "9920105",
                "9920106",
            ]
        },
        "rawFeatureBytesTransmitted": False,
    }


def test_browser_archive_gate_stops_when_any_required_component_is_missing(
    tmp_path: Path,
) -> None:
    result = probe(archive(tmp_path, (".shp", ".shx", ".dbf")))
    assert result["status"] == "rejected"
    assert result["code"] == "required-component-missing"
    assert ".prj" in result["message"]


def test_school_application_is_a_five_stage_user_flow_not_a_workbench() -> None:
    html = HTML.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    upload = UPLOAD.read_text(encoding="utf-8")

    for step in ("upload", "evidence", "authorize", "map", "verify"):
        assert f'data-panel="{step}"' in html
        assert f'data-step="{step}"' in html
    assert 'class="stage-panel is-active"' in html
    assert "Normalized runtime envelope" not in html
    assert 'type="file"' in html
    assert "download" not in html.lower()
    assert "50_000" in upload
    assert "15" not in upload
    assert "9920100" not in upload
    assert "9920101" in upload and "9920106" in upload
    assert "new URL(resource.path, document.baseURI)" in app
    assert 'new URL(path.replace(/^\\//, ""), apiRoot)' in app
    assert '["127.0.0.1", "localhost"].includes(location.hostname)' in app
    assert "qaFixture" not in html


def test_browser_only_sends_observation_and_governed_contracts_to_agent() -> None:
    app = APP.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")

    for endpoint in (
        "school-portrayal/proposals",
        "school-portrayal/authorizations",
        "school-portrayal/compile",
        "school-portrayal/observations",
        "school-portrayal/verify",
    ):
        assert endpoint in app
    assert "state.local.inspection.collection" in app
    assert "raw_feature_bytes_transmitted: false" in app
    assert "rawFeatureBytesTransmitted: false" in UPLOAD.read_text(encoding="utf-8")
    assert "browser-local" in html.lower()
    assert "production activation" in html.lower()
    assert '"browser-render-verified"' in app
    assert "decisionTrace" in app


def test_vendored_shpjs_is_pinned_and_licensed() -> None:
    vendor = ROOT / "assets/vendor/shpjs-6.2.0"
    assert (vendor / "shp.esm.min.js").stat().st_size == 99_731
    license_text = (vendor / "LICENSE.md").read_text(encoding="utf-8")
    assert "MIT License" in license_text

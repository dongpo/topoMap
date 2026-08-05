import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "artifacts/release/nma-v0.2-review-package.zip"
REPORT = ROOT / "artifacts/release/nma-v0.2-review-package-verification.json"
DECK = ROOT / "artifacts/presentation/nma-foss4g-presentation-v0.9.pptx"


def test_review_package_is_manifested_and_excludes_pmtiles() -> None:
    with zipfile.ZipFile(ARCHIVE) as archive:
        package_name = "nma-v0.2-review-package"
        manifest = json.loads(archive.read(f"{package_name}/MANIFEST.json"))
        names = archive.namelist()

    paths = [item["path"] for item in manifest["files"]]
    assert manifest["demo_contract_version"] == "1.0"
    assert manifest["portrayal_profile"] == "tw-nlsc-1000-NLSC112V5.4"
    assert manifest["frozen_scene_count"] == 5
    assert len(paths) == len(set(paths))
    assert all(not Path(path).is_absolute() for path in paths)
    assert all(not path.endswith(".pmtiles") for path in paths)
    assert "artifacts/presentation/nma-foss4g-presentation-v0.9.pptx" in paths
    assert all(not name.endswith(".pmtiles") for name in names)
    assert f"{package_name}/VERIFY.py" in names


def test_review_package_verifier_reproduces_five_scenes(tmp_path: Path) -> None:
    with zipfile.ZipFile(ARCHIVE) as archive:
        archive.extractall(tmp_path)
    package = tmp_path / "nma-v0.2-review-package"
    result = subprocess.run(
        [sys.executable, "VERIFY.py"],
        cwd=package,
        check=True,
        capture_output=True,
        text=True,
    )
    verification = json.loads(result.stdout)

    assert verification["status"] == "passed"
    assert verification["scene_count"] == 5
    assert verification["negative_controls"] == 2
    assert verification["checksum_failures"] == 0
    assert verification["sensitive_matches"] == 0

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert len(report["zip_sha256"]) == 64


def test_presentation_v09_has_twelve_sourced_slides() -> None:
    with zipfile.ZipFile(DECK) as archive:
        slide_names = sorted(
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
        note_names = sorted(
            name
            for name in archive.namelist()
            if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
        )
        note_text = [archive.read(name).decode("utf-8") for name in note_names]

    assert len(slide_names) == 12
    assert len(note_names) == 12
    assert all("[Sources]" in value for value in note_text)

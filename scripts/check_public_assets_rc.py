from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from nma.demo_rc1 import check_demo_rc1  # noqa: E402
from scripts.build_public_site import build_public_site  # noqa: E402


EXPECTED_RELEASE = "nma-public-assets-v0.2-rc1"
EXPECTED_ALLOWED_CHANGES = ["correctness", "clarity", "reliability", "conference-needs"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expect(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def check_presentation(path: Path) -> dict[str, int]:
    with zipfile.ZipFile(path) as archive:
        slides = [
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        ]
        notes = [
            name
            for name in archive.namelist()
            if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
        ]
        sourced = sum("[Sources]" in archive.read(name).decode("utf-8") for name in notes)
    expect(len(slides), 12, "presentation slide count")
    expect(len(notes), 12, "presentation notes count")
    expect(sourced, 12, "sourced presentation notes")
    return {"slides": len(slides), "sourced_notes": sourced}


def check_review_package(path: Path, report_path: Path) -> dict[str, Any]:
    report = load_json(report_path)
    expect(report["status"], "passed", "review package status")
    expect(report["zip_sha256"], sha256(path), "review package report checksum")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if any(name.endswith(".pmtiles") for name in names):
            raise ValueError("review package must not contain PMTiles")
        manifest_name = "nma-v0.2-review-package/MANIFEST.json"
        manifest = json.loads(archive.read(manifest_name))
    expect(manifest["frozen_scene_count"], 5, "review package scene count")
    return {
        "status": report["status"],
        "scene_count": manifest["frozen_scene_count"],
        "file_count": len(manifest["files"]),
    }


def check_clean_install() -> dict[str, Any]:
    temporary_parent = ROOT / "artifacts/tmp"
    temporary_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nma-install-", dir=temporary_parent) as temporary:
        environment = Path(temporary) / "venv"
        subprocess.run(
            [sys.executable, "-m", "venv", "--system-site-packages", str(environment)],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        python = environment / "bin/python"
        nma = environment / "bin/nma"
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--no-build-isolation",
                ".",
            ],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        subprocess.run([str(nma), "--help"], check=True, cwd=ROOT, capture_output=True, text=True)
        scenes = subprocess.run(
            [str(nma), "demo-scenes"],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        scene_result = json.loads(scenes.stdout)
    expect(scene_result["scene_count"], 5, "clean-install scene count")
    return {
        "status": "passed",
        "install_mode": "offline core install with inherited build backend",
        "scene_count": scene_result["scene_count"],
    }


def check_public_assets_rc(manifest_path: Path, *, verify_install: bool = False) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    expect(manifest["release_version"], EXPECTED_RELEASE, "release version")
    expect(manifest["status"], "release-candidate", "release status")
    expect(manifest["source"]["stable_demo_release"], "nma-demo-v0.2-rc1", "stable release")
    expect(manifest["website"]["public_mode"], "evidence-only", "public website mode")
    expect(manifest["website"]["deployment_state"], "deployed", "deployment state")
    deployment = manifest["website"]["deployment_evidence"]
    expect(deployment["run_id"], 31019900015, "Pages deployment run")
    expect(
        deployment["head_sha"],
        "60eb2857b1ff14b0baa51732373ca5c8b697c1c3",
        "Pages deployment commit",
    )
    if not deployment["artifact_digest"].startswith("sha256:"):
        raise ValueError("Pages artifact digest must be SHA-256")
    expect(
        manifest["post_freeze_policy"]["allowed_categories"],
        EXPECTED_ALLOWED_CHANGES,
        "post-freeze categories",
    )

    base_commit = manifest["source"]["base_commit"]
    if len(base_commit) != 40 or any(
        character not in "0123456789abcdef" for character in base_commit
    ):
        raise ValueError("public-assets base commit must be a full lowercase Git SHA")

    paths = [item["path"] for item in manifest["frozen_assets"]]
    if len(paths) != len(set(paths)):
        raise ValueError("public-assets manifest contains duplicate paths")
    for item in manifest["frozen_assets"]:
        path = ROOT / item["path"]
        if not path.is_file():
            raise ValueError(f"missing frozen public asset: {item['path']}")
        expect(sha256(path), item["sha256"], f"{item['path']} SHA-256")

    stable = check_demo_rc1(ROOT / manifest["source"]["stable_demo_manifest"])
    expect(stable["status"], "passed", "Stable Demo RC1 gate")

    quickstart = (ROOT / manifest["install_and_demo_contract"]["quickstart"]).read_text(
        encoding="utf-8"
    )
    commands = manifest["install_and_demo_contract"]["required_commands"]
    missing_commands = [command for command in commands if command not in quickstart]
    if missing_commands:
        raise ValueError(f"quickstart is missing required commands: {missing_commands}")

    presentation_path = ROOT / next(
        item["path"] for item in manifest["frozen_assets"] if item["role"] == "presentation-rc"
    )
    presentation = check_presentation(presentation_path)
    package_path = ROOT / next(
        item["path"]
        for item in manifest["frozen_assets"]
        if item["role"] == "runnable-review-package"
    )
    package_report = ROOT / next(
        item["path"]
        for item in manifest["frozen_assets"]
        if item["role"] == "review-package-verification"
    )
    review_package = check_review_package(package_path, package_report)

    workflow = (ROOT / manifest["website"]["workflow"]).read_text(encoding="utf-8")
    if "python3 scripts/build_public_site.py" not in workflow:
        raise ValueError("Pages workflow does not build the bounded public artifact")
    if "path: 'artifacts/tmp/public-site'" not in workflow or "path: '.'" in workflow:
        raise ValueError("Pages workflow may publish repository-only files")

    temporary_parent = ROOT / "artifacts/tmp"
    temporary_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="nma-public-assets-", dir=temporary_parent
    ) as temporary:
        site = Path(temporary) / "public-site"
        public_site = build_public_site(ROOT, site)
        if (site / "out1120902.pmtiles").exists():
            raise ValueError("bounded public site contains PMTiles")
        release_file_count = len(public_site["files"])
        link_count = sum(item["link_count"] for item in public_site["link_checks"])
        image_count = sum(item["image_count"] for item in public_site["link_checks"])

    blocking = manifest["blocking_defects"]
    resolved = manifest["resolved_defects"]
    deferred = manifest["deferred_defects"]
    if any(item["classification"] != "blocking" for item in blocking):
        raise ValueError("blocking defects must be explicitly classified")
    if any(item["classification"] != "deferred" for item in deferred):
        raise ValueError("deferred defects must be explicitly classified")
    if any(item["classification"] != "resolved" for item in resolved):
        raise ValueError("resolved defects must be explicitly classified")

    install_rehearsal = (
        check_clean_install() if verify_install else {"status": "not-run", "scene_count": None}
    )

    return {
        "release_version": manifest["release_version"],
        "status": "candidate-passed",
        "stable_demo_release": manifest["source"]["stable_demo_release"],
        "frozen_asset_count": len(manifest["frozen_assets"]),
        "public_site_file_count": release_file_count,
        "local_link_count": link_count,
        "local_image_count": image_count,
        "install_command_count": len(commands),
        "install_rehearsal": install_rehearsal,
        "presentation": presentation,
        "review_package": review_package,
        "public_mode": manifest["website"]["public_mode"],
        "public_deployment": manifest["website"]["deployment_state"],
        "blocking_defect_count": len(blocking),
        "resolved_defect_count": len(resolved),
        "deferred_defect_count": len(deferred),
        "post_freeze_categories": manifest["post_freeze_policy"]["allowed_categories"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the NMA D21 public-assets RC")
    parser.add_argument("--manifest", default="data/demo/public-assets-rc1.json")
    parser.add_argument("--output", default="artifacts/release/public-assets-rc1-verification.json")
    parser.add_argument("--verify-install", action="store_true")
    args = parser.parse_args()
    result = check_public_assets_rc(ROOT / args.manifest, verify_install=args.verify_install)
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

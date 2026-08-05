from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


PACKAGE_NAME = "nma-v0.2-review-package"
TEMPLATE_FILES = ("README.md", "DATASET.md", "PAPER-SKELETON.md", "VERIFY.py", "Makefile")
CURATED_FILES = (
    "LICENSE",
    "src/nma/__init__.py",
    "src/nma/knowledge.py",
    "src/nma/portrayal.py",
    "data/demo/five-scene-demo.json",
    "data/extraction/portrayal-records.jsonl",
    "data/knowledge/portrayal-profile.json",
    "data/knowledge/portrayal-graph.json",
    "data/sources/authoritative-sources.json",
    "artifacts/portrayal/maplibre-layers.json",
    "artifacts/presentation/nma-foss4g-presentation-v0.9.pptx",
    "schemas/executable-profile.schema.json",
    "schemas/five-scene-demo.schema.json",
    "docs/BENCHMARK.md",
    "docs/RESEARCH-PROTOCOL.md",
    "docs/FIVE-SCENE-NARRATIVE.md",
    "docs/STABLE-DEMO-RC1.md",
)
CURATED_GLOBS = (
    "assets/symbols/nlsc112v5.4/*",
    "benchmark/portrayal/*.json",
    "benchmark/portrayal/*.jsonl",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_relative(source_root: Path, relative: Path, stage: Path) -> None:
    source = source_root / relative
    if not source.is_file():
        raise FileNotFoundError(f"required review-package asset is missing: {relative}")
    target = stage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def source_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build(root: Path) -> tuple[Path, Path, Path]:
    root = root.resolve()
    release_root = root / "artifacts/release"
    release_root.mkdir(parents=True, exist_ok=True)
    target = release_root / PACKAGE_NAME
    zip_path = release_root / f"{PACKAGE_NAME}.zip"
    verification_path = release_root / f"{PACKAGE_NAME}-verification.json"

    with tempfile.TemporaryDirectory(prefix="nma-review-package-", dir=release_root) as temporary:
        stage = Path(temporary) / PACKAGE_NAME
        stage.mkdir()

        template_root = root / "release/review-package"
        for name in TEMPLATE_FILES:
            copy_relative(template_root, Path(name), stage)
        for name in CURATED_FILES:
            copy_relative(root, Path(name), stage)
        for pattern in CURATED_GLOBS:
            matches = sorted(path for path in root.glob(pattern) if path.is_file())
            if not matches:
                raise FileNotFoundError(f"review-package pattern matched no files: {pattern}")
            for path in matches:
                copy_relative(root, path.relative_to(root), stage)

        payload_files = sorted(path for path in stage.rglob("*") if path.is_file())
        manifest = {
            "package": PACKAGE_NAME,
            "package_version": "0.9",
            "source_base_commit": source_commit(root),
            "demo_contract_version": "1.0",
            "portrayal_profile": "tw-nlsc-1000-NLSC112V5.4",
            "specification_version": "NLSC112V5.4",
            "frozen_scene_count": 5,
            "release_exclusions": [
                "out1120902.pmtiles (redistribution terms pending)",
                "official NLSC portrayal PDF (referenced, not redistributed)",
                "public deployment (separate human-approved release step)",
            ],
            "files": [
                {
                    "path": path.relative_to(stage).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
                for path in payload_files
            ],
        }
        write_json(stage / "MANIFEST.json", manifest)
        (stage / "CHECKSUMS.sha256").write_text(
            "".join(f"{item['sha256']}  {item['path']}\n" for item in manifest["files"]),
            encoding="utf-8",
        )

        verify = subprocess.run(
            [sys.executable, "VERIFY.py"],
            cwd=stage,
            check=True,
            capture_output=True,
            text=True,
            env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        verification = json.loads(verify.stdout)

        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(stage, target)

    with zipfile.ZipFile(
        zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(item for item in target.rglob("*") if item.is_file()):
            relative = Path(PACKAGE_NAME) / path.relative_to(target)
            info = zipfile.ZipInfo(relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())

    report = {
        "package": PACKAGE_NAME,
        "status": verification["status"],
        "source_base_commit": manifest["source_base_commit"],
        "zip_sha256": sha256(zip_path),
        "zip_bytes": zip_path.stat().st_size,
        "release_exclusions": manifest["release_exclusions"],
        "verification": verification,
    }
    write_json(verification_path, report)
    return target, zip_path, verification_path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target, zip_path, verification_path = build(root)
    print(target.relative_to(root))
    print(zip_path.relative_to(root))
    print(verification_path.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

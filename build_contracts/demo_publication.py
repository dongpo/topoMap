from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

from nma.core import canonical_sha256
from scripts.build_public_site import sha256 as file_sha256


PUBLICATION_VERSION = "build-06a/1.0"
PUBLICATION_SCHEMA = "nma.build-demo-safe-publication/1.0"
PUBLICATION_ID = "build-06a-pages-bc636eb1eed7e055"
EXPECTED_PREDECESSOR_SHA = "ac8552066f85e07358751b1f15a6fbc085f7fc67"
EXPECTED_FREEZE_SHA256 = "bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857"
EXPECTED_PUBLICATION_SHA256 = "83c22625ad99dbc0cb26af614d39cf6fd12e6e77b1c863b501656e46f6d105a9"
LIVE_URL = "https://dongpo.github.io/topoMap/build-demo/"

PUBLIC_FILES = {
    "buildDemoV06.html": {
        "target": "index.html",
        "sha256": "de5f6d567810e42af915bdff167fb21e202967b98817e2ef8d2d494d0b47be2d",
    },
    "data/specifications/nma-build-05-golden-execution-package-v1.0.json": {
        "target": ("data/specifications/" "nma-build-05-golden-execution-package-v1.0.json"),
        "sha256": "508e3378a698f869255485c5008fdb80ed670ce174a3b72092aab5160df7431c",
    },
    "data/specifications/nma-build-05-authorization-consumption-v1.0.json": {
        "target": ("data/specifications/" "nma-build-05-authorization-consumption-v1.0.json"),
        "sha256": "715a5445827b77308ec32a67efe74ac8e5ed29b9037ee543285270a4da1c9d47",
    },
}

BOUNDARIES = {
    "dedicated_subdirectory": "build-demo/",
    "published_file_count": 3,
    "private_archive_published": False,
    "raw_geographic_coordinates_published": False,
    "raw_attributes_published": False,
    "source_pdf_published": False,
    "pmtiles_published_by_build06a": False,
    "api_credentials_published": False,
    "external_runtime_dependency": False,
    "production_runtime_wired": False,
    "official_portrayal_claimed": False,
    "demo_only": True,
}

FORBIDDEN_NAMES = {
    "112年多維度SHP成果_0502.zip",
    "out1120902.pmtiles",
    ".env",
    ".env.local",
}

FORBIDDEN_CONTENT = (
    "geometry_wkb_hex",
    '"BUILD_ID"',
    '"BUILD_NO"',
    '"BUILD_STR"',
    "112年多維度SHP成果_0502.zip",
    "sk-proj-",
    "BEGIN PRIVATE KEY",
)


class BuildDemoPublicationError(ValueError):
    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildDemoPublicationError(message, code=code)


def publication_sha256(value: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(value))
    basis.pop("publication_sha256", None)
    return canonical_sha256(basis)


def _safe_target(site: Path, root: Path) -> Path:
    site = site.resolve()
    root = root.resolve()
    target = site / "build-demo"
    if site == root or target == root:
        _fail("BUILD-06A cannot publish into the repository root.", "output_path_invalid")
    if not site.is_dir() or not (site / "index.html").is_file():
        _fail("The bounded base Pages artifact must be built first.", "base_site_invalid")
    if target.is_symlink():
        _fail("The BUILD-06A output cannot be a symlink.", "output_path_invalid")
    return target


def _audit_html(path: Path) -> None:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise BuildDemoPublicationError(
            "The published BUILD-06A HTML is unreadable.", code="publication_invalid"
        ) from error
    required = (
        "DEMO ONLY · 非正式圖式",
        "data/specifications/nma-build-05-golden-execution-package-v1.0.json",
        "data/specifications/nma-build-05-authorization-consumption-v1.0.json",
        "default-src 'self'",
        "10c22339abb8d2eed489ae56a54214948213bad51a135e00f74e309931c98c97",
    )
    if any(token not in source for token in required):
        _fail("The published BUILD-06A HTML contract changed.", "publication_invalid")
    if "http://" in source or "https://" in source:
        _fail("The BUILD-06A DEMO added an external dependency.", "network_detected")


def _audit_payload(target: Path) -> list[dict[str, Any]]:
    files = sorted(path for path in target.rglob("*") if path.is_file())
    actual = {path.relative_to(target).as_posix() for path in files}
    expected = {str(value["target"]) for value in PUBLIC_FILES.values()}
    if actual != expected or len(files) != 3:
        _fail("The BUILD-06A public payload is not exactly three files.", "scope_expanded")
    for path in files:
        if path.name in FORBIDDEN_NAMES:
            _fail("The BUILD-06A payload includes a forbidden file.", "scope_expanded")
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise BuildDemoPublicationError(
                "The BUILD-06A payload contains a binary file.", code="scope_expanded"
            ) from error
        if any(token in content for token in FORBIDDEN_CONTENT):
            _fail("The BUILD-06A payload discloses forbidden content.", "disclosure_detected")
    _audit_html(target / "index.html")
    return [
        {
            "path": path.relative_to(target).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
        for path in files
    ]


def build_build_demo_publication(root: Path, site: Path) -> dict[str, Any]:
    root = root.resolve()
    target = _safe_target(site, root)
    verified_sources: list[tuple[Path, str, str]] = []
    for source_name, specification in PUBLIC_FILES.items():
        source = root / source_name
        expected_sha = str(specification["sha256"])
        if file_sha256(source) != expected_sha:
            _fail(f"The BUILD-06A source changed: {source_name}.", "input_hash_mismatch")
        verified_sources.append((source, str(specification["target"]), expected_sha))
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for source, target_name, _expected_sha in verified_sources:
        destination = target / target_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    files = _audit_payload(target)
    manifest: dict[str, Any] = {
        "publication_version": PUBLICATION_VERSION,
        "schema_version": PUBLICATION_SCHEMA,
        "publication_id": PUBLICATION_ID,
        "status": "bounded-public-demo-ready",
        "prepared_on": "2026-08-20",
        "predecessor": {
            "branch": "build/build-06-demo-verification-freeze",
            "commit_sha": EXPECTED_PREDECESSOR_SHA,
            "freeze_sha256": EXPECTED_FREEZE_SHA256,
        },
        "destination": {
            "provider": "github-pages",
            "repository": "dongpo/topoMap",
            "public_path": "build-demo/",
            "expected_live_url": LIVE_URL,
        },
        "files": files,
        "boundaries": deepcopy(BOUNDARIES),
        "deployment": {
            "workflow": ".github/workflows/build06a-pages.yml",
            "artifact_root": "artifacts/tmp/public-site",
            "base_public_release_preserved": True,
            "deployment_performed": False,
            "live_verification_performed": False,
        },
    }
    manifest["publication_sha256"] = publication_sha256(manifest)
    if (
        EXPECTED_PUBLICATION_SHA256 is not None
        and manifest["publication_sha256"] != EXPECTED_PUBLICATION_SHA256
    ):
        _fail("The BUILD-06A publication is not the frozen candidate.", "publication_mismatch")
    return manifest


def validate_build_demo_publication(
    manifest: Mapping[str, Any], root: Path, site: Path
) -> dict[str, Any]:
    if not isinstance(manifest, Mapping):
        _fail("The BUILD-06A publication manifest must be an object.", "manifest_invalid")
    expected = build_build_demo_publication(root, site)
    if dict(manifest) != expected:
        _fail("The BUILD-06A publication manifest changed.", "manifest_mismatch")
    if manifest.get("publication_sha256") != publication_sha256(manifest):
        _fail("The BUILD-06A publication hash is invalid.", "manifest_hash_mismatch")
    return deepcopy(dict(manifest))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add the exact bounded BUILD-06A DEMO to a sanitized Pages artifact"
    )
    parser.add_argument("--site", default="artifacts/tmp/public-site")
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = build_build_demo_publication(root, root / arguments.site)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "public_path": manifest["destination"]["public_path"],
                "file_count": len(manifest["files"]),
                "publication_sha256": manifest["publication_sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path
import shutil
from typing import Any

from jsonschema import Draft202012Validator, ValidationError
import pytest

import build_contracts.demo_publication as build06a
from build_contracts.demo_publication import (
    BuildDemoPublicationError,
    build_build_demo_publication,
    file_sha256,
    publication_sha256,
    validate_build_demo_publication,
)


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "data/specifications/nma-build-06a-golden-safe-publication-v1.0.json"
SCHEMA_PATH = ROOT / "schemas/build-demo-safe-publication-v1.0.schema.json"
WORKFLOW_PATH = ROOT / ".github/workflows/build06a-pages.yml"


@pytest.fixture()
def golden() -> dict[str, Any]:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def base_site(tmp_path: Path) -> Path:
    site = tmp_path / "public-site"
    site.mkdir()
    (site / "index.html").write_text("<!doctype html><title>base</title>\n", encoding="utf-8")
    return site


def _fails(callable_, code: str) -> BuildDemoPublicationError:
    with pytest.raises(BuildDemoPublicationError) as caught:
        callable_()
    assert caught.value.code == code
    return caught.value


def _copy_public_sources(target_root: Path) -> None:
    for source_name in build06a.PUBLIC_FILES:
        source = ROOT / source_name
        target = target_root / source_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def test_golden_manifest_equals_reproducible_bounded_build(
    golden: dict[str, Any], base_site: Path
) -> None:
    actual = build_build_demo_publication(ROOT, base_site)

    assert actual == golden
    assert validate_build_demo_publication(golden, ROOT, base_site) == golden
    assert actual["publication_sha256"] == (
        "83c22625ad99dbc0cb26af614d39cf6fd12e6e77b1c863b501656e46f6d105a9"
    )


def test_closed_schema_accepts_only_exact_publication(
    golden: dict[str, Any],
) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    validator = Draft202012Validator(schema)
    validator.validate(golden)

    changed = deepcopy(golden)
    changed["private_archive"] = "published"
    with pytest.raises(ValidationError):
        validator.validate(changed)


def test_publication_binds_exact_build06_freeze(golden: dict[str, Any]) -> None:
    assert golden["predecessor"] == {
        "branch": "build/build-06-demo-verification-freeze",
        "commit_sha": "ac8552066f85e07358751b1f15a6fbc085f7fc67",
        "freeze_sha256": ("bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857"),
    }


def test_destination_is_exact_public_github_pages_subdirectory(
    golden: dict[str, Any],
) -> None:
    assert golden["destination"] == {
        "provider": "github-pages",
        "repository": "dongpo/topoMap",
        "public_path": "build-demo/",
        "expected_live_url": "https://dongpo.github.io/topoMap/build-demo/",
    }


def test_build_demo_subdirectory_contains_exactly_three_files(base_site: Path) -> None:
    build_build_demo_publication(ROOT, base_site)
    target = base_site / "build-demo"
    actual = sorted(
        path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()
    )

    assert actual == [
        "data/specifications/nma-build-05-authorization-consumption-v1.0.json",
        "data/specifications/nma-build-05-golden-execution-package-v1.0.json",
        "index.html",
    ]


def test_published_files_are_byte_exact_copies(base_site: Path) -> None:
    build_build_demo_publication(ROOT, base_site)
    target = base_site / "build-demo"

    for source_name, specification in build06a.PUBLIC_FILES.items():
        published = target / str(specification["target"])
        assert published.read_bytes() == (ROOT / source_name).read_bytes()
        assert file_sha256(published) == specification["sha256"]


def test_manifest_file_list_is_sorted_and_exact(golden: dict[str, Any]) -> None:
    paths = [item["path"] for item in golden["files"]]

    assert paths == sorted(paths)
    assert len(paths) == 3
    assert [item["bytes"] for item in golden["files"]] == [737, 6767, 14981]


def test_publication_boundaries_deny_private_or_authority_expansion(
    golden: dict[str, Any],
) -> None:
    boundaries = golden["boundaries"]

    assert boundaries == build06a.BOUNDARIES
    assert boundaries["published_file_count"] == 3
    assert boundaries["demo_only"] is True
    for denied in (
        "private_archive_published",
        "raw_geographic_coordinates_published",
        "raw_attributes_published",
        "source_pdf_published",
        "pmtiles_published_by_build06a",
        "api_credentials_published",
        "external_runtime_dependency",
        "production_runtime_wired",
        "official_portrayal_claimed",
    ):
        assert boundaries[denied] is False


def test_published_html_fetches_only_same_subdirectory_json(base_site: Path) -> None:
    build_build_demo_publication(ROOT, base_site)
    source = (base_site / "build-demo/index.html").read_text(encoding="utf-8")

    assert (
        'const PACKAGE_URL = "data/specifications/'
        'nma-build-05-golden-execution-package-v1.0.json";'
    ) in source
    assert (
        'const LEDGER_URL = "data/specifications/'
        'nma-build-05-authorization-consumption-v1.0.json";'
    ) in source
    assert "http://" not in source
    assert "https://" not in source
    assert "default-src 'self'" in source


def test_payload_contains_no_forbidden_name_content_or_binary(base_site: Path) -> None:
    build_build_demo_publication(ROOT, base_site)
    target = base_site / "build-demo"

    for path in target.rglob("*"):
        if not path.is_file():
            continue
        assert path.name not in build06a.FORBIDDEN_NAMES
        content = path.read_text(encoding="utf-8")
        assert all(token not in content for token in build06a.FORBIDDEN_CONTENT)


def test_rebuild_removes_stale_expanded_subdirectory_content(base_site: Path) -> None:
    target = base_site / "build-demo"
    target.mkdir()
    (target / "private.zip").write_bytes(b"forbidden")

    build_build_demo_publication(ROOT, base_site)

    assert not (target / "private.zip").exists()
    assert len([path for path in target.rglob("*") if path.is_file()]) == 3


def test_repository_root_cannot_be_publication_output() -> None:
    _fails(
        lambda: build_build_demo_publication(ROOT, ROOT),
        "output_path_invalid",
    )


def test_base_public_site_must_exist_before_overlay(tmp_path: Path) -> None:
    _fails(
        lambda: build_build_demo_publication(ROOT, tmp_path / "missing"),
        "base_site_invalid",
    )


def test_build_demo_target_symlink_is_rejected(base_site: Path, tmp_path: Path) -> None:
    external = tmp_path / "external"
    external.mkdir()
    (base_site / "build-demo").symlink_to(external, target_is_directory=True)

    _fails(
        lambda: build_build_demo_publication(ROOT, base_site),
        "output_path_invalid",
    )


@pytest.mark.parametrize("source_name", list(build06a.PUBLIC_FILES))
def test_any_changed_source_hash_fails_before_copy(
    tmp_path: Path, base_site: Path, source_name: str
) -> None:
    source_root = tmp_path / "source"
    _copy_public_sources(source_root)
    changed = source_root / source_name
    changed.write_bytes(changed.read_bytes() + b"changed")

    _fails(
        lambda: build_build_demo_publication(source_root, base_site),
        "input_hash_mismatch",
    )
    assert not (base_site / "build-demo").exists()


def test_external_dependency_is_rejected_even_with_rebased_input_hash(
    tmp_path: Path,
    base_site: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "source"
    _copy_public_sources(source_root)
    html = source_root / "buildDemoV06.html"
    html.write_text(
        html.read_text(encoding="utf-8").replace(
            "</body>", '<script src="https://example.com/runtime.js"></script></body>'
        ),
        encoding="utf-8",
    )
    changed_files = deepcopy(build06a.PUBLIC_FILES)
    changed_files["buildDemoV06.html"]["sha256"] = file_sha256(html)
    monkeypatch.setattr(build06a, "PUBLIC_FILES", changed_files)
    monkeypatch.setattr(build06a, "EXPECTED_PUBLICATION_SHA256", None)

    _fails(
        lambda: build_build_demo_publication(source_root, base_site),
        "network_detected",
    )


def test_private_reference_is_rejected_even_with_rebased_input_hash(
    tmp_path: Path,
    base_site: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "source"
    _copy_public_sources(source_root)
    html = source_root / "buildDemoV06.html"
    html.write_text(
        html.read_text(encoding="utf-8").replace("</body>", "112年多維度SHP成果_0502.zip</body>"),
        encoding="utf-8",
    )
    changed_files = deepcopy(build06a.PUBLIC_FILES)
    changed_files["buildDemoV06.html"]["sha256"] = file_sha256(html)
    monkeypatch.setattr(build06a, "PUBLIC_FILES", changed_files)
    monkeypatch.setattr(build06a, "EXPECTED_PUBLICATION_SHA256", None)

    _fails(
        lambda: build_build_demo_publication(source_root, base_site),
        "disclosure_detected",
    )


def test_binary_payload_is_rejected_after_rebased_scope(
    tmp_path: Path,
    base_site: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "source"
    _copy_public_sources(source_root)
    html = source_root / "buildDemoV06.html"
    html.write_bytes(b"\xff\xfe\x00")
    changed_files = deepcopy(build06a.PUBLIC_FILES)
    changed_files["buildDemoV06.html"]["sha256"] = file_sha256(html)
    monkeypatch.setattr(build06a, "PUBLIC_FILES", changed_files)
    monkeypatch.setattr(build06a, "EXPECTED_PUBLICATION_SHA256", None)

    _fails(
        lambda: build_build_demo_publication(source_root, base_site),
        "scope_expanded",
    )


def test_workflow_builds_base_then_overlay_before_upload() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    base = "python3 scripts/build_public_site.py --output artifacts/tmp/public-site"
    overlay = (
        "PYTHONPATH=src:. python3 -m build_contracts.demo_publication "
        "--site artifacts/tmp/public-site"
    )
    upload = "uses: actions/upload-pages-artifact@v3"

    assert base in workflow
    assert overlay in workflow
    assert upload in workflow
    assert workflow.index(base) < workflow.index(overlay) < workflow.index(upload)


def test_workflow_uploads_only_sanitized_artifact_not_repository_root() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "path: 'artifacts/tmp/public-site'" in workflow
    assert "path: '.'" not in workflow
    assert "pages: write" in workflow
    assert "id-token: write" in workflow


def test_builder_has_no_network_credentials_or_deployment_capability() -> None:
    source = inspect.getsource(build06a)

    assert "requests" not in source
    assert "urllib" not in source
    assert "subprocess" not in source
    assert "gh api" not in source
    assert "GITHUB_TOKEN" not in source
    assert "actions/deploy-pages" not in source


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"extra": True}),
        lambda value: value.pop("boundaries"),
        lambda value: value["boundaries"].update({"private_archive_published": True}),
        lambda value: value["destination"].update({"public_path": "./"}),
        lambda value: value["files"].append(
            {"path": "private.zip", "bytes": 1, "sha256": "0" * 64}
        ),
    ],
)
def test_changed_manifest_cannot_validate(
    golden: dict[str, Any], base_site: Path, mutation
) -> None:
    changed = deepcopy(golden)
    mutation(changed)
    changed["publication_sha256"] = publication_sha256(changed)

    _fails(
        lambda: validate_build_demo_publication(changed, ROOT, base_site),
        "manifest_mismatch",
    )


def test_golden_manifest_is_canonical_json_line(golden: dict[str, Any]) -> None:
    expected = (
        json.dumps(
            golden,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )

    assert GOLDEN_PATH.read_bytes() == expected

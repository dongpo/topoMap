from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from jsonschema import Draft202012Validator, ValidationError
import pytest

import build_contracts.fixture as build_fixture
import nma.core as core
from build_contracts.feature_profile import build_feature_profile
from build_contracts.fixture import (
    BuildFixtureError,
    EXPECTED_ARCHIVE_SHA256,
    fixture_identity,
    load_build_fixture_manifest,
    validate_build_fixture_manifest,
)
from nma.qa_review import diagnose_real_vector_profile
from nma.real_layer import REAL_LAYER_PROFILES, extract_reviewed_source_layers, file_sha256


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data/specifications/nma-build-fixture-manifest-v1.0.json"
SCHEMA_PATH = ROOT / "schemas/build-fixture-manifest-v1.0.schema.json"
SPECIFICATION_PATH = ROOT / "data/specifications/taiwan-temap-build-v0.4.json"
ARCHIVE_PATH = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
PRIVATE_FIXTURE_AVAILABLE = (
    ARCHIVE_PATH.is_file() and shutil.which("ogrinfo") is not None and shutil.which("ogr2ogr") is not None
)


def test_manifest_schema_is_closed_meta_valid_and_accepts_the_frozen_fixture() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(manifest)
    invalid = deepcopy(manifest)
    invalid["execution"] = {"allowed": True}
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(invalid)


def test_manifest_uses_the_exact_frozen_core_identity_provider() -> None:
    manifest = load_build_fixture_manifest()

    assert build_fixture.canonical_sha256 is core.canonical_sha256
    assert build_fixture.validate_sha256 is core.validate_sha256
    assert manifest["fixture_id"] == fixture_identity(manifest)
    assert manifest["core_identity"] == {
        "owner": "nma.core",
        "freeze_tag": "nma-core-v1.0-final",
        "freeze_sha": "5eb138ae7686502431587743ebce9ddf92c5a799",
        "identity_provider": "canonical_sha256",
        "feature_profile_provider": "FeatureProfile",
    }


def test_candidate_comparison_accepts_only_the_smallest_zero_defect_candidate() -> None:
    manifest = load_build_fixture_manifest()
    candidates = manifest["candidates"]
    accepted = [candidate for candidate in candidates if candidate["decision"] == "accepted"]
    zero_defect = [
        candidate
        for candidate in candidates
        if candidate["null_or_blank_build_id"] == 0
        and candidate["duplicate_build_id_groups"] == 0
        and candidate["null_or_empty_geometry"] == 0
        and candidate["invalid_geometry"] == 0
    ]

    assert [candidate["layer_id"] for candidate in accepted] == ["J13_BUILD"]
    assert [candidate["layer_id"] for candidate in zero_defect] == ["J13_BUILD", "K02_BUILD"]
    assert accepted[0]["feature_count"] == min(candidate["feature_count"] for candidate in zero_defect)
    legacy = next(candidate for candidate in candidates if candidate["layer_id"] == "J17_BUILD")
    assert legacy["invalid_geometry"] == 1


def test_build_feature_profile_is_core_owned_read_only_and_non_executing() -> None:
    manifest = load_build_fixture_manifest()
    profile = build_feature_profile()

    assert isinstance(profile, core.FeatureProfile)
    assert profile.geometry_role == "Polygon"
    assert profile.identity_payload == {
        "fixture_id": manifest["fixture_id"],
        "feature_code": "9310100",
    }
    assert profile.source_scope_payload["archive_sha256"] == EXPECTED_ARCHIVE_SHA256
    assert profile.source_scope_payload["layer_id"] == "J13_BUILD"
    assert profile.metadata == {
        "feature_name": "永久性建物(建築區)",
        "purpose": "build-01-entry-readiness-only",
        "execution_authorized": False,
    }
    with pytest.raises(TypeError):
        profile.identity_payload["feature_code"] = "changed"  # type: ignore[index]


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("fixture", "selected_feature_count"), 2961),
        (("selection", "selected_layer_id"), "J17_BUILD"),
        (("boundaries", "execution_authorized"), True),
        (("core_identity", "identity_provider"), "local-sha256"),
    ],
)
def test_rehashed_tampering_still_fails_closed(path: tuple[str, str], value: object) -> None:
    manifest = load_build_fixture_manifest()
    manifest[path[0]][path[1]] = value
    manifest["fixture_id"] = fixture_identity(manifest)

    with pytest.raises(BuildFixtureError):
        validate_build_fixture_manifest(manifest)


def test_identity_is_equal_across_key_order_and_independent_roots(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    reordered = dict(reversed(list(manifest.items())))
    copied = tmp_path / MANIFEST_PATH.name
    copied.write_text(json.dumps(reordered, ensure_ascii=False, indent=4), encoding="utf-8")

    assert fixture_identity(manifest) == fixture_identity(reordered)
    assert load_build_fixture_manifest(copied) == load_build_fixture_manifest(MANIFEST_PATH)


def test_build_fixture_contract_has_no_execution_or_experimental_imports() -> None:
    source = (ROOT / "build_contracts/fixture.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    assert "nma.core" in imports
    assert not imports.intersection(
        {
            "nma.real_layer",
            "nma.qa_review",
            "nma.road_execution",
            "nma.school_hero_execution",
            "subprocess",
            "zipfile",
        }
    )
    lowered = source.lower()
    assert "execute_real_layer" not in lowered
    assert "authorization_id" not in lowered
    assert "idempotency" not in lowered


def test_missing_core_fails_before_fixture_identity_without_fallback(tmp_path: Path) -> None:
    nma_package = tmp_path / "nma"
    nma_package.mkdir()
    (nma_package / "__init__.py").write_text("", encoding="utf-8")
    build_package = tmp_path / "build_contracts"
    build_package.mkdir()
    (build_package / "__init__.py").write_text("", encoding="utf-8")
    shutil.copyfile(ROOT / "build_contracts/fixture.py", build_package / "fixture.py")
    process = subprocess.run(
        [sys.executable, "-c", "import build_contracts.fixture"],
        env={"PYTHONPATH": str(tmp_path), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
    )

    assert process.returncode != 0
    assert "ModuleNotFoundError: No module named 'nma.core'" in process.stderr
    assert not (nma_package / "core").exists()


def test_legacy_v04_building_experiment_remains_unchanged_and_non_authoritative() -> None:
    profile = REAL_LAYER_PROFILES["building-polygon"]

    assert profile["source_layer_ids"] == ["J17_BUILD"]
    assert profile["expected_feature_count"] == 2769
    assert profile["feature_code"] == "9310100"
    assert load_build_fixture_manifest()["boundaries"]["execution_authorized"] is False


@pytest.mark.skipif(not PRIVATE_FIXTURE_AVAILABLE, reason="The private archive and GDAL are required.")
def test_selected_private_fixture_matches_all_frozen_components_and_population(tmp_path: Path) -> None:
    manifest = load_build_fixture_manifest()
    paths, components = extract_reviewed_source_layers(ARCHIVE_PATH, ["J13_BUILD"], tmp_path)
    observed_hashes = {item["extension"]: item["sha256"] for item in components}
    expected_hashes = {
        item["extension"]: item["sha256"] for item in manifest["fixture"]["components"]
    }

    assert file_sha256(ARCHIVE_PATH) == EXPECTED_ARCHIVE_SHA256
    assert observed_hashes == expected_hashes
    completed = subprocess.run(
        [
            "ogrinfo",
            "-json",
            "-ro",
            "-features",
            "-dialect",
            "SQLite",
            "-sql",
            "SELECT TERRAINID, COUNT(*) AS n FROM J13_BUILD GROUP BY TERRAINID ORDER BY TERRAINID",
            str(paths[0]),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    distribution = {
        item["properties"]["TERRAINID"]: item["properties"]["n"]
        for item in payload["layers"][0]["features"]
    }
    assert distribution == manifest["fixture"]["feature_code_distribution"]


@pytest.mark.skipif(not PRIVATE_FIXTURE_AVAILABLE, reason="The private archive and GDAL are required.")
def test_build_qa_profile_is_runnable_and_reports_only_the_documented_boundary() -> None:
    result = diagnose_real_vector_profile(
        profile_id="build-real-polygon",
        archive_path=ARCHIVE_PATH,
        expected_archive_sha256=EXPECTED_ARCHIVE_SHA256,
        project_root=ROOT,
    )

    assert SPECIFICATION_PATH.is_file()
    assert result["summary"] == {
        "source_layers": 1,
        "features": 2839,
        "rules_evaluated": 11,
        "issues": 2,
        "errors": 2,
        "warnings": 0,
        "safe_repairs_available": 0,
    }
    assert {issue.split("|", 1)[0] for issue in result["issue_keys"]} == {
        "J17_BUILD::TW-BUILD-DOC-FIELD-001",
        "J17_BUILD::TW-BUILD-DOC-FIELD-002",
    }
    assert result["source_mutated"] is False
    assert result["repair_proposed"] is False
    assert result["automatic_acceptance"] is False

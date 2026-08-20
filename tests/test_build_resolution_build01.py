from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import shutil

from jsonschema import Draft202012Validator, ValidationError
import pytest

import build_contracts.resolution as build_resolution
import nma.core as core
from build_contracts.fixture import EXPECTED_FIXTURE_ID, load_build_fixture_manifest
from build_contracts.resolution import (
    BuildResolutionError,
    DEFAULT_ARCHIVE_PATH,
    DEFAULT_OBSERVATION_PATH,
    NORMALIZED_INTENT,
    inspect_private_build_source,
    load_build_source_observation,
    observation_identity,
    package_sha256,
    resolve_build_request,
    validate_build_source_observation,
)


ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_SCHEMA_PATH = ROOT / "schemas/build-source-observation-v1.0.schema.json"
PACKAGE_SCHEMA_PATH = ROOT / "schemas/build-resolution-evidence-package-v1.0.schema.json"
GOLDEN_REQUEST = (
    "Resolve the J13 building polygon class 9310100 by the accepted deterministic rule "
    "and prepare its redacted evidence package."
)
PRIVATE_SOURCE_AVAILABLE = DEFAULT_ARCHIVE_PATH.is_file() and shutil.which("ogrinfo") is not None


@pytest.fixture()
def observation() -> dict:
    return load_build_source_observation()


def _error_code(callable_, code: str) -> None:
    with pytest.raises(BuildResolutionError) as caught:
        callable_()
    assert caught.value.code == code


def test_closed_schemas_are_meta_valid_and_accept_the_golden_artifacts() -> None:
    observation_schema = json.loads(OBSERVATION_SCHEMA_PATH.read_text(encoding="utf-8"))
    package_schema = json.loads(PACKAGE_SCHEMA_PATH.read_text(encoding="utf-8"))
    observation = load_build_source_observation()
    package = resolve_build_request(GOLDEN_REQUEST)

    for schema in (observation_schema, package_schema):
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False
    Draft202012Validator(observation_schema).validate(observation)
    Draft202012Validator(package_schema).validate(package)

    changed = deepcopy(package)
    changed["execution"] = {"authorized": True}
    with pytest.raises(ValidationError):
        Draft202012Validator(package_schema).validate(changed)


def test_golden_resolution_binds_exact_source_selection_and_core_identity() -> None:
    package = resolve_build_request(GOLDEN_REQUEST)

    assert package["package_version"] == "build-01/1.0"
    assert package["schema_version"] == "nma.build-resolution-evidence-package/1.0"
    assert package["request"]["normalized_intent"] == NORMALIZED_INTENT
    assert package["source"] == {
        "fixture_id": EXPECTED_FIXTURE_ID,
        "archive_sha256": "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
        "layer_id": "J13_BUILD",
        "feature_code": "9310100",
    }
    assert package["resolution"] == {
        "selection_policy": "largest-valid-2d-area-desc-then-build-id-asc",
        "eligible_feature_count": 2962,
        "selected_rank": 1,
        "largest_area_tie_count": 1,
        "feature_reference": "build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f",
    }
    assert package["identity_evidence"]["provider"] == "nma.core.canonical_sha256"
    assert package["package_sha256"] == package_sha256(package)


def test_polygon_geometry_is_valid_z_preserving_and_not_repaired() -> None:
    geometry = resolve_build_request(GOLDEN_REQUEST)["geometry_evidence"]

    assert geometry == {
        "geometry_commitment_sha256": "23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f",
        "source_geometry_type": "PolygonZ",
        "canonical_geometry_role": "Polygon",
        "area_2d_m2": "1316.686891452159",
        "vertex_count": 65,
        "ring_count": 1,
        "is_valid": True,
        "z_dimension_present": True,
        "repair_required": False,
    }


def test_package_discloses_no_raw_private_feature_data_and_grants_no_authority() -> None:
    package = resolve_build_request(GOLDEN_REQUEST)

    assert package["privacy"] == {
        "raw_feature_id_disclosed": False,
        "raw_attributes_disclosed": False,
        "raw_geometry_disclosed": False,
        "source_redistributed": False,
    }
    assert package["permissions"] == {
        "source_mutation_allowed": False,
        "geometry_repair_allowed": False,
        "z_dimension_drop_authorized": False,
        "execution_authorized": False,
        "runtime_wiring_authorized": False,
        "redistribution_authorized": False,
    }
    tracked_observation = DEFAULT_OBSERVATION_PATH.read_text(encoding="utf-8")
    assert "2BXKP71RBN" not in tracked_observation
    assert "geometry_wkb_hex" not in tracked_observation
    assert "coordinates" not in tracked_observation.casefold()


def test_exact_frozen_core_objects_are_used_without_local_identity_copy() -> None:
    source = (ROOT / "build_contracts/resolution.py").read_text(encoding="utf-8")

    assert build_resolution.canonical_sha256 is core.canonical_sha256
    assert build_resolution.validate_sha256 is core.validate_sha256
    assert "def canonical_json" not in source
    assert "def canonical_sha256" not in source
    package = resolve_build_request(GOLDEN_REQUEST)
    assert package["identity_evidence"]["profile_identity_sha256"] == (
        "5f560c8fde92b7ed590c8f4d1292ae69743e033b2bbf43b837b083b5c611dc09"
    )
    assert package["identity_evidence"]["source_scope_sha256"] == (
        "a4e3eff87f1df770e01c3675fe883335b4416c405922d22b129e85fc4a44065b"
    )


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("source", "layer_id", "J17_BUILD"),
        ("selection", "eligible_feature_count", 2961),
        ("resolved_feature", "geometry_commitment_sha256", "0" * 64),
        ("resolved_feature", "z_dimension_present", False),
        ("core_binding", "identity_provider", "local-sha256"),
        ("privacy", "raw_geometry_disclosed", True),
    ],
)
def test_rehashed_source_evidence_tampering_fails_closed(
    observation: dict, section: str, field: str, value: object
) -> None:
    changed = deepcopy(observation)
    changed[section][field] = value
    changed["observation_id"] = observation_identity(changed)

    _error_code(
        lambda: validate_build_source_observation(changed), "observation_hash_mismatch"
    )


def test_archive_hash_mismatch_fails_closed() -> None:
    _error_code(
        lambda: resolve_build_request(GOLDEN_REQUEST, observed_archive_sha256="0" * 64),
        "archive_hash_mismatch",
    )


def test_inputs_are_not_mutated(observation: dict) -> None:
    before = deepcopy(observation)

    resolve_build_request(GOLDEN_REQUEST, source_observation=observation)

    assert observation == before


def test_equivalent_requests_have_one_deterministic_semantic_hash() -> None:
    variants = [
        GOLDEN_REQUEST,
        "Prepare redacted evidence for J13 BUILD polygon 9310100.",
        "  Resolve J13 建物 9310100 evidence package.  ",
        "J13 建築 9310100: resolve the building evidence.",
    ]
    packages = [resolve_build_request(request) for request in variants]

    assert len({package["package_sha256"] for package in packages}) == 1
    assert len({package["request"]["raw"] for package in packages}) == len(variants)
    assert all(package["package_sha256"] == package_sha256(package) for package in packages)


def test_ambiguous_or_unbound_requests_fail_closed() -> None:
    for request in [
        "Resolve J17 building polygon 9310100.",
        "Resolve J13 or J17 building polygon 9310100.",
        "Resolve J13 building polygon 9310103.",
        "Resolve J13 building polygon 9310100 and 9310103.",
        "Resolve J13 class 9310100.",
    ]:
        _error_code(lambda request=request: resolve_build_request(request), "unsupported_request")


def test_observation_identity_is_key_order_and_root_independent(tmp_path: Path) -> None:
    observation = json.loads(DEFAULT_OBSERVATION_PATH.read_text(encoding="utf-8"))
    reordered = dict(reversed(list(observation.items())))
    copied = tmp_path / DEFAULT_OBSERVATION_PATH.name
    copied.write_text(json.dumps(reordered, ensure_ascii=False, indent=4), encoding="utf-8")

    assert observation_identity(observation) == observation_identity(reordered)
    assert load_build_source_observation(copied) == load_build_source_observation()


def test_resolution_contract_has_no_domain_execution_or_experimental_imports() -> None:
    source = (ROOT / "build_contracts/resolution.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    assert not imports.intersection(
        {
            "nma.real_layer",
            "nma.qa_review",
            "nma.road_execution",
            "nma.school_hero_execution",
        }
    )
    lowered = source.casefold()
    assert "authorization_id" not in lowered
    assert "idempotency" not in lowered
    assert "runtime endpoint" not in lowered


def test_build00a_predecessor_fixture_identity_remains_exact() -> None:
    manifest = load_build_fixture_manifest()

    assert manifest["fixture_id"] == EXPECTED_FIXTURE_ID
    assert manifest["boundaries"]["purpose"] == "build-01-entry-readiness-only"


@pytest.mark.skipif(
    not PRIVATE_SOURCE_AVAILABLE, reason="The private archive and GDAL are required."
)
def test_private_source_reinspection_matches_redacted_observation_without_mutation() -> None:
    before_size = DEFAULT_ARCHIVE_PATH.stat().st_size
    before_mtime = DEFAULT_ARCHIVE_PATH.stat().st_mtime_ns

    inspected = inspect_private_build_source()

    assert inspected == load_build_source_observation()
    assert DEFAULT_ARCHIVE_PATH.stat().st_size == before_size
    assert DEFAULT_ARCHIVE_PATH.stat().st_mtime_ns == before_mtime

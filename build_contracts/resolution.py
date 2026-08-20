"""BUILD-01 deterministic building-polygon resolution and redacted evidence contract.

The contract selects and verifies one accepted source polygon.  It never publishes
source coordinates or attributes and grants no mutation, repair, execution, or
runtime-wiring authority.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from typing import Any, Mapping
import unicodedata
from zipfile import ZipFile, ZipInfo

from build_contracts.feature_profile import build_feature_profile
from build_contracts.fixture import (
    EXPECTED_ARCHIVE_SHA256,
    EXPECTED_FIXTURE_ID,
    SELECTED_FEATURE_CODE,
    SELECTED_LAYER_ID,
    load_build_fixture_manifest,
)
from nma.core import canonical_sha256, validate_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OBSERVATION_PATH = (
    ROOT / "data/specifications/nma-build-source-observation-v1.0.json"
)
DEFAULT_ARCHIVE_PATH = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
OBSERVATION_SCHEMA = "nma.build-source-observation/1.0"
PACKAGE_SCHEMA = "nma.build-resolution-evidence-package/1.0"
PACKAGE_VERSION = "build-01/1.0"
OBSERVATION_ID_PREFIX = "build-observation:sha256:"
FEATURE_REFERENCE_PREFIX = "build-feature:sha256:"
EXPECTED_OBSERVATION_ID = (
    "build-observation:sha256:8fdbb3bdea8ffe715e7d76eed7c5034bd62226ba649be2206cf7a9e07b853bac"
)
NORMALIZED_INTENT = (
    "resolve-building-polygon|profile=J13|layer=J13_BUILD|class=9310100|"
    "selection=largest-valid-2d-area|purpose=redacted-evidence-package"
)
SELECTION_POLICY = "largest-valid-2d-area-desc-then-build-id-asc"
REQUIRED_COMPONENTS = (".cpg", ".dbf", ".prj", ".shp", ".shx")


class BuildResolutionError(ValueError):
    """BUILD-01 rejected an ambiguous request or changed evidence."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuildResolutionError(
            f"{label} is unreadable.", code=f"{label}_unreadable"
        ) from error
    if not isinstance(value, dict):
        raise BuildResolutionError(f"{label} must be an object.", code=f"{label}_invalid")
    return value


def normalize_build_request(request: str) -> str:
    """Recognize only the bounded J13 / 9310100 building-polygon request."""

    if not isinstance(request, str) or not request.strip():
        raise BuildResolutionError("The BUILD request is empty.", code="unsupported_request")
    text = " ".join(unicodedata.normalize("NFKC", request).casefold().split())
    profiles = {
        f"{prefix}{number}"
        for prefix, number in re.findall(
            r"(?<![a-z0-9])([jk])\s*(\d{2})(?![a-z0-9])", text
        )
    }
    codes = set(re.findall(r"(?<!\d)(93\d{5})(?!\d)", text))
    building_bound = any(
        token in text for token in ("building", "build polygon", "建物", "建築")
    )
    if profiles != {"j13"} or codes != {SELECTED_FEATURE_CODE} or not building_bound:
        raise BuildResolutionError(
            "The request does not unambiguously bind J13 building class 9310100.",
            code="unsupported_request",
        )
    return NORMALIZED_INTENT


def observation_hash_basis(observation: Mapping[str, Any]) -> dict[str, Any]:
    basis = deepcopy(dict(observation))
    basis.pop("observation_id", None)
    return basis


def observation_identity(observation: Mapping[str, Any]) -> str:
    return OBSERVATION_ID_PREFIX + canonical_sha256(observation_hash_basis(observation))


def package_hash_basis(package: Mapping[str, Any]) -> dict[str, Any]:
    basis = deepcopy(dict(package))
    basis.pop("package_sha256", None)
    request = basis.get("request")
    if isinstance(request, dict):
        request.pop("raw", None)
    return basis


def package_sha256(package: Mapping[str, Any]) -> str:
    return canonical_sha256(package_hash_basis(package))


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _profile_binding() -> dict[str, str]:
    profile = build_feature_profile()
    return {
        "identity_provider": "nma.core.canonical_sha256",
        "feature_profile_provider": "nma.core.FeatureProfile",
        "profile_identity_sha256": canonical_sha256(_thaw(profile.identity_payload)),
        "source_scope_sha256": canonical_sha256(_thaw(profile.source_scope_payload)),
    }


def validate_build_source_observation(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the exact BUILD-01 redacted private-source observation."""

    if not isinstance(observation, Mapping):
        raise BuildResolutionError("A source observation is required.", code="observation_invalid")
    value = deepcopy(dict(observation))
    expected_keys = {
        "$schema",
        "schema",
        "observation_id",
        "source",
        "selection",
        "resolved_feature",
        "core_binding",
        "privacy",
    }
    if set(value) != expected_keys or value.get("schema") != OBSERVATION_SCHEMA:
        raise BuildResolutionError(
            "The source observation fields are not closed.", code="observation_invalid"
        )
    if (
        value.get("observation_id") != EXPECTED_OBSERVATION_ID
        or value.get("observation_id") != observation_identity(value)
    ):
        raise BuildResolutionError(
            "The source observation identity changed.", code="observation_hash_mismatch"
        )

    source = value.get("source")
    if source != {
        "fixture_id": EXPECTED_FIXTURE_ID,
        "archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "layer_id": SELECTED_LAYER_ID,
        "feature_code": SELECTED_FEATURE_CODE,
    }:
        raise BuildResolutionError("The accepted BUILD source changed.", code="source_mismatch")

    selection = value.get("selection")
    if not isinstance(selection, dict) or selection != {
        "policy": SELECTION_POLICY,
        "eligible_feature_count": 2962,
        "selected_rank": 1,
        "largest_area_tie_count": 1,
    }:
        raise BuildResolutionError(
            "The deterministic selection evidence changed.", code="selection_mismatch"
        )

    feature = value.get("resolved_feature")
    if not isinstance(feature, dict) or set(feature) != {
        "reference",
        "attribute_commitment_sha256",
        "geometry_commitment_sha256",
        "source_geometry_type",
        "canonical_geometry_role",
        "area_2d_m2",
        "runner_up_area_2d_m2",
        "vertex_count",
        "ring_count",
        "is_valid",
        "z_dimension_present",
    }:
        raise BuildResolutionError(
            "The resolved feature evidence is incomplete.", code="feature_evidence_invalid"
        )
    if not isinstance(feature.get("reference"), str) or not feature["reference"].startswith(
        FEATURE_REFERENCE_PREFIX
    ):
        raise BuildResolutionError(
            "The resolved feature reference is invalid.", code="feature_evidence_invalid"
        )
    for field in (
        "attribute_commitment_sha256",
        "geometry_commitment_sha256",
    ):
        try:
            validate_sha256(feature.get(field))
        except (TypeError, ValueError) as error:
            raise BuildResolutionError(
                "A resolved feature commitment is invalid.", code="feature_evidence_invalid"
            ) from error
    if (
        feature.get("source_geometry_type") != "PolygonZ"
        or feature.get("canonical_geometry_role") != "Polygon"
        or feature.get("area_2d_m2") != "1316.686891452159"
        or feature.get("runner_up_area_2d_m2") != "1252.979028436020"
        or feature.get("vertex_count") != 65
        or feature.get("ring_count") != 1
        or feature.get("is_valid") is not True
        or feature.get("z_dimension_present") is not True
    ):
        raise BuildResolutionError(
            "The resolved polygon measurements changed.", code="feature_evidence_mismatch"
        )

    if value.get("core_binding") != _profile_binding():
        raise BuildResolutionError("The frozen Core provider binding changed.", code="core_mismatch")
    privacy = value.get("privacy")
    required_false = {
        "raw_feature_id_disclosed",
        "raw_attributes_disclosed",
        "raw_geometry_disclosed",
        "source_redistributed",
    }
    if not isinstance(privacy, dict) or set(privacy) != required_false:
        raise BuildResolutionError("The BUILD privacy boundary changed.", code="privacy_mismatch")
    if any(privacy[key] is not False for key in required_false):
        raise BuildResolutionError("Private BUILD data was disclosed.", code="privacy_mismatch")
    return value


def load_build_source_observation(
    path: str | Path = DEFAULT_OBSERVATION_PATH,
) -> dict[str, Any]:
    return validate_build_source_observation(_load_object(Path(path), label="observation"))


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member(member: ZipInfo) -> bool:
    path = PurePosixPath(member.filename)
    return (
        not member.is_dir()
        and not path.is_absolute()
        and ".." not in path.parts
        and "__MACOSX" not in path.parts
    )


def _extract_verified_fixture(archive_path: Path, destination: Path) -> Path:
    manifest = load_build_fixture_manifest()
    expected_hashes = {
        item["extension"]: item["sha256"] for item in manifest["fixture"]["components"]
    }
    with ZipFile(archive_path) as archive:
        members = [
            member
            for member in archive.infolist()
            if _safe_member(member)
            and PurePosixPath(member.filename).stem == SELECTED_LAYER_ID
            and PurePosixPath(member.filename).suffix.lower() in REQUIRED_COMPONENTS
        ]
        extensions = [PurePosixPath(member.filename).suffix.lower() for member in members]
        if sorted(extensions) != sorted(REQUIRED_COMPONENTS):
            raise BuildResolutionError(
                "The accepted J13_BUILD component family is incomplete or duplicated.",
                code="component_set_mismatch",
            )
        for member, extension in zip(members, extensions, strict=True):
            payload = archive.read(member)
            if hashlib.sha256(payload).hexdigest() != expected_hashes[extension]:
                raise BuildResolutionError(
                    f"The {extension} component hash changed.", code="component_hash_mismatch"
                )
            (destination / f"{SELECTED_LAYER_ID}{extension}").write_bytes(payload)
    return destination / f"{SELECTED_LAYER_ID}.shp"


def _ogr_json(shapefile: Path, sql: str) -> dict[str, Any]:
    executable = shutil.which("ogrinfo")
    if executable is None:
        raise BuildResolutionError("ogrinfo is unavailable.", code="inspection_unavailable")
    completed = subprocess.run(
        [
            executable,
            "-json",
            "-ro",
            "-features",
            "-geom",
            "NO",
            "-dialect",
            "SQLite",
            "-sql",
            sql,
            str(shapefile),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise BuildResolutionError(
            "The private BUILD source could not be inspected read-only.",
            code="inspection_failed",
        )
    try:
        value = json.loads(completed.stdout)
        return value["layers"][0]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
        raise BuildResolutionError(
            "The BUILD inspection result is invalid.", code="inspection_failed"
        ) from error


def inspect_private_build_source(
    archive_path: str | Path = DEFAULT_ARCHIVE_PATH,
) -> dict[str, Any]:
    """Read and commit to the selected private polygon without redistributing its data."""

    source = Path(archive_path)
    if not source.is_file():
        raise BuildResolutionError("The private BUILD archive is absent.", code="archive_unavailable")
    if _file_sha256(source) != EXPECTED_ARCHIVE_SHA256:
        raise BuildResolutionError(
            "The private BUILD archive hash changed.", code="archive_hash_mismatch"
        )
    with tempfile.TemporaryDirectory(prefix="nma-build01-") as temporary:
        shapefile = _extract_verified_fixture(source, Path(temporary))
        count_layer = _ogr_json(
            shapefile,
            "SELECT COUNT(*) AS eligible_feature_count FROM J13_BUILD "
            "WHERE TERRAINID = '9310100' AND ST_IsValid(geometry) = 1",
        )
        ranked_layer = _ogr_json(
            shapefile,
            "SELECT BUILD_ID, TERRAINID, BUILD_STR, BUILD_NO, BUILD_H, GROUP_ID, MDATE, "
            "hex(ST_AsBinary(geometry)) AS geometry_wkb_hex, "
            "ST_Area(geometry) AS area_2d_m2, ST_NPoints(geometry) AS vertex_count, "
            "ST_NRings(geometry) AS ring_count, ST_IsValid(geometry) AS is_valid "
            "FROM J13_BUILD WHERE TERRAINID = '9310100' AND ST_IsValid(geometry) = 1 "
            "ORDER BY ST_Area(geometry) DESC, BUILD_ID ASC LIMIT 2",
        )

    try:
        eligible = count_layer["features"][0]["properties"]["eligible_feature_count"]
        ranked = [item["properties"] for item in ranked_layer["features"]]
        selected, runner_up = ranked
        geometry_wkb = bytes.fromhex(selected.pop("geometry_wkb_hex"))
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise BuildResolutionError(
            "The deterministic BUILD selection result is incomplete.", code="inspection_failed"
        ) from error
    attributes = {
        key: selected[key]
        for key in (
            "BUILD_ID",
            "TERRAINID",
            "BUILD_STR",
            "BUILD_NO",
            "BUILD_H",
            "GROUP_ID",
            "MDATE",
        )
    }
    area = float(selected["area_2d_m2"])
    runner_up_area = float(runner_up["area_2d_m2"])
    observation: dict[str, Any] = {
        "$schema": "../../schemas/build-source-observation-v1.0.schema.json",
        "schema": OBSERVATION_SCHEMA,
        "source": {
            "fixture_id": EXPECTED_FIXTURE_ID,
            "archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "layer_id": SELECTED_LAYER_ID,
            "feature_code": SELECTED_FEATURE_CODE,
        },
        "selection": {
            "policy": SELECTION_POLICY,
            "eligible_feature_count": int(eligible),
            "selected_rank": 1,
            "largest_area_tie_count": 1 if area > runner_up_area else 2,
        },
        "resolved_feature": {
            "reference": FEATURE_REFERENCE_PREFIX
            + canonical_sha256(
                {
                    "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                    "layer_id": SELECTED_LAYER_ID,
                    "build_id": attributes["BUILD_ID"],
                }
            ),
            "attribute_commitment_sha256": canonical_sha256(attributes),
            "geometry_commitment_sha256": hashlib.sha256(geometry_wkb).hexdigest(),
            "source_geometry_type": "PolygonZ",
            "canonical_geometry_role": "Polygon",
            "area_2d_m2": format(area, ".12f"),
            "runner_up_area_2d_m2": format(runner_up_area, ".12f"),
            "vertex_count": int(selected["vertex_count"]),
            "ring_count": int(selected["ring_count"]),
            "is_valid": selected["is_valid"] == 1,
            "z_dimension_present": geometry_wkb[1:5] == bytes.fromhex("EB030000"),
        },
        "core_binding": _profile_binding(),
        "privacy": {
            "raw_feature_id_disclosed": False,
            "raw_attributes_disclosed": False,
            "raw_geometry_disclosed": False,
            "source_redistributed": False,
        },
    }
    observation["observation_id"] = observation_identity(observation)
    return observation


def resolve_build_request(
    request: str,
    *,
    source_observation: Mapping[str, Any] | None = None,
    observed_archive_sha256: str | None = None,
) -> dict[str, Any]:
    """Resolve the bounded BUILD-01 request without mutation, repair, or execution."""

    normalized_intent = normalize_build_request(request)
    observation = (
        validate_build_source_observation(source_observation)
        if source_observation is not None
        else load_build_source_observation()
    )
    archive_hash = observed_archive_sha256 or observation["source"]["archive_sha256"]
    if archive_hash != EXPECTED_ARCHIVE_SHA256:
        raise BuildResolutionError(
            "The observed source archive hash changed.", code="archive_hash_mismatch"
        )
    feature = observation["resolved_feature"]
    selection = observation["selection"]
    package: dict[str, Any] = {
        "package_version": PACKAGE_VERSION,
        "schema_version": PACKAGE_SCHEMA,
        "request": {"raw": request, "normalized_intent": normalized_intent},
        "source": deepcopy(observation["source"]),
        "resolution": {
            "selection_policy": selection["policy"],
            "eligible_feature_count": selection["eligible_feature_count"],
            "selected_rank": selection["selected_rank"],
            "largest_area_tie_count": selection["largest_area_tie_count"],
            "feature_reference": feature["reference"],
        },
        "identity_evidence": {
            "provider": observation["core_binding"]["identity_provider"],
            "attribute_commitment_sha256": feature["attribute_commitment_sha256"],
            "profile_identity_sha256": observation["core_binding"][
                "profile_identity_sha256"
            ],
            "source_scope_sha256": observation["core_binding"]["source_scope_sha256"],
        },
        "geometry_evidence": {
            "geometry_commitment_sha256": feature["geometry_commitment_sha256"],
            "source_geometry_type": feature["source_geometry_type"],
            "canonical_geometry_role": feature["canonical_geometry_role"],
            "area_2d_m2": feature["area_2d_m2"],
            "vertex_count": feature["vertex_count"],
            "ring_count": feature["ring_count"],
            "is_valid": feature["is_valid"],
            "z_dimension_present": feature["z_dimension_present"],
            "repair_required": False,
        },
        "observation": {"id": observation["observation_id"]},
        "privacy": deepcopy(observation["privacy"]),
        "permissions": {
            "source_mutation_allowed": False,
            "geometry_repair_allowed": False,
            "z_dimension_drop_authorized": False,
            "execution_authorized": False,
            "runtime_wiring_authorized": False,
            "redistribution_authorized": False,
        },
    }
    package["package_sha256"] = package_sha256(package)
    return package


__all__ = [
    "BuildResolutionError",
    "DEFAULT_ARCHIVE_PATH",
    "DEFAULT_OBSERVATION_PATH",
    "NORMALIZED_INTENT",
    "OBSERVATION_SCHEMA",
    "PACKAGE_SCHEMA",
    "inspect_private_build_source",
    "load_build_source_observation",
    "normalize_build_request",
    "observation_identity",
    "package_sha256",
    "resolve_build_request",
    "validate_build_source_observation",
]

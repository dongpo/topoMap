"""BUILD-05 controlled single-consumption building DEMO execution.

The executor validates the frozen BUILD-04 capability, reads one exact private
J13 feature, emits only normalized non-geographic DEMO geometry, and persists a
single immutable package with consumption and receipt records.  It never writes
the source, repairs geometry, removes source Z, or wires production runtime.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Mapping, Sequence

from build_contracts.demo_authorization import (
    AUTHORIZATION_ID,
    plan_build_demo_consumption,
    validate_build_demo_authorization,
)
from build_contracts.resolution import (
    DEFAULT_ARCHIVE_PATH,
    _extract_verified_fixture,
    _file_sha256,
)
from nma.core import canonical_sha256


PACKAGE_SCHEMA = "nma.build-demo-execution-package/1.0"
PACKAGE_VERSION = "build-05/1.0"
ARTIFACT_SCHEMA = "nma.build-derived-maplibre-demo/1.0"
CONSUMPTION_SCHEMA = "nma.build-demo-authorization-consumption/1.0"
RECEIPT_SCHEMA = "nma.build-demo-execution-receipt/1.0"
EXPECTED_AUTHORIZATION_SHA256 = (
    "f609fa99ae0280987e11a3328e04d26484c15a65f72a0266566f2aaa9f650b2d"
)
EXPECTED_RESOLUTION_SHA256 = (
    "a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01"
)
EXPECTED_PLAN_SHA256 = (
    "b8b5ecd54954b190eb8cda398710039f334e8424fd0969816380b4a2b52b0b71"
)
EXPECTED_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
EXPECTED_FIXTURE_ID = (
    "build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a"
)
EXPECTED_FEATURE_REFERENCE = (
    "build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f"
)
EXPECTED_ATTRIBUTE_COMMITMENT = (
    "ddfa112586b9c2bc3a61bdf2638b7994ba1200bfce5d8ad34988f2a24da96078"
)
EXPECTED_GEOMETRY_COMMITMENT = (
    "23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f"
)
EXPECTED_PACKAGE_SHA256 = (
    "10c22339abb8d2eed489ae56a54214948213bad51a135e00f74e309931c98c97"
)
IDEMPOTENCY_KEY = "build04-demo-default-45-v1"
EXECUTION_ID = "build-05-demo-exec-b8b5ecd54954b190eb8cda39"
CONSUMPTION_ID = "build-05-consumption-f609fa99ae0280987e11a332"
RECEIPT_ID = "build-05-receipt-b8b5ecd54954b190eb8cda39"
TARGET = "derived MapLibre web DEMO portrayal candidate"
OPERATION = "render-derived-maplibre-building-demo"
REQUEST_SCHEMA = "nma.build-demo-authorization-request/1.0"
SOURCE_FIELDS = (
    "BUILD_ID",
    "TERRAINID",
    "BUILD_STR",
    "BUILD_NO",
    "BUILD_H",
    "GROUP_ID",
    "MDATE",
)

PACKAGE_BOUNDARIES = {
    "authorization_consumed": True,
    "execution_performed": True,
    "source_read_only": True,
    "source_mutated": False,
    "source_z_preserved": True,
    "derived_view_uses_xy": True,
    "raw_geographic_coordinates_disclosed": False,
    "raw_attributes_disclosed": False,
    "runtime_wired": False,
    "production_activated": False,
    "demo_policy_promoted": False,
}


class BuildDemoExecutionError(ValueError):
    """BUILD-05 rejected an unsafe, replayed, or changed execution."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildDemoExecutionError(message, code=code)


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _record_sha256(value: Mapping[str, Any], hash_field: str) -> str:
    basis = deepcopy(dict(value))
    basis.pop(hash_field, None)
    return canonical_sha256(basis)


def artifact_sha256(artifact: Mapping[str, Any]) -> str:
    return _record_sha256(artifact, "artifact_sha256")


def consumption_sha256(consumption: Mapping[str, Any]) -> str:
    return _record_sha256(consumption, "consumption_sha256")


def receipt_sha256(receipt: Mapping[str, Any]) -> str:
    return _record_sha256(receipt, "receipt_sha256")


def package_sha256(package: Mapping[str, Any]) -> str:
    return _record_sha256(package, "package_sha256")


def _request(authorization: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "request_schema": REQUEST_SCHEMA,
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
        "resolution_sha256": EXPECTED_RESOLUTION_SHA256,
        "fixture_id": EXPECTED_FIXTURE_ID,
        "layer_id": "J13_BUILD",
        "feature_code": "9310100",
        "feature_reference": EXPECTED_FEATURE_REFERENCE,
        "target": TARGET,
        "operation": OPERATION,
        "hatch_angle_degrees": 45.0,
        "idempotency_key": IDEMPOTENCY_KEY,
    }


def _read_private_feature(archive_path: Path) -> dict[str, Any]:
    if not archive_path.is_file():
        _fail("The private BUILD archive is absent.", "archive_unavailable")
    if _file_sha256(archive_path) != EXPECTED_ARCHIVE_SHA256:
        _fail("The private BUILD archive hash changed.", "archive_hash_mismatch")
    executable = shutil.which("ogrinfo")
    if executable is None:
        _fail("OGR is unavailable for the authorized read.", "source_read_unavailable")
    with tempfile.TemporaryDirectory(prefix="nma-build05-") as temporary:
        shapefile = _extract_verified_fixture(archive_path, Path(temporary))
        quoted_code = "'9310100'"
        sql = (
            "SELECT BUILD_ID, TERRAINID, BUILD_STR, BUILD_NO, BUILD_H, GROUP_ID, "
            "MDATE, hex(ST_AsBinary(geometry)) AS geometry_wkb_hex, "
            "ST_NPoints(geometry) AS vertex_count, ST_NRings(geometry) AS ring_count, "
            "geometry FROM J13_BUILD WHERE TERRAINID = "
            f"{quoted_code} AND ST_IsValid(geometry) = 1 "
            "ORDER BY ST_Area(geometry) DESC, BUILD_ID ASC LIMIT 1"
        )
        completed = subprocess.run(
            [
                executable,
                "-json",
                "-ro",
                "-features",
                "-geom",
                "YES",
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
        _fail("The authorized J13 feature read failed.", "source_read_failed")
    try:
        feature = json.loads(completed.stdout)["layers"][0]["features"][0]
        properties = dict(feature["properties"])
        geometry = dict(feature["geometry"])
        geometry_wkb = bytes.fromhex(properties.pop("geometry_wkb_hex"))
        attributes = {field: properties[field] for field in SOURCE_FIELDS}
        vertex_count = int(properties["vertex_count"])
        ring_count = int(properties["ring_count"])
    except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as error:
        raise BuildDemoExecutionError(
            "The authorized J13 feature response is invalid.", code="source_read_failed"
        ) from error
    feature_reference = "build-feature:sha256:" + canonical_sha256(
        {
            "archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "layer_id": "J13_BUILD",
            "build_id": attributes["BUILD_ID"],
        }
    )
    if (
        feature_reference != EXPECTED_FEATURE_REFERENCE
        or canonical_sha256(attributes) != EXPECTED_ATTRIBUTE_COMMITMENT
        or hashlib.sha256(geometry_wkb).hexdigest() != EXPECTED_GEOMETRY_COMMITMENT
        or geometry.get("type") != "Polygon"
        or ring_count != 1
        or vertex_count != 65
    ):
        _fail("The authorized private feature identity changed.", "source_identity_mismatch")
    coordinates = geometry.get("coordinates")
    if (
        not isinstance(coordinates, list)
        or len(coordinates) != 1
        or not isinstance(coordinates[0], list)
        or len(coordinates[0]) != 65
    ):
        _fail("The authorized PolygonZ structure changed.", "source_geometry_mismatch")
    for coordinate in coordinates[0]:
        if (
            not isinstance(coordinate, list)
            or len(coordinate) != 3
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in coordinate
            )
        ):
            _fail("The authorized PolygonZ coordinates are invalid.", "source_geometry_mismatch")
    return {
        "attributes": attributes,
        "coordinates": coordinates,
        "vertex_count": vertex_count,
        "ring_count": ring_count,
    }


def _normalized_xy(coordinates: Sequence[Sequence[Sequence[float]]]) -> list[list[list[float]]]:
    ring = coordinates[0]
    xs = [float(coordinate[0]) for coordinate in ring]
    ys = [float(coordinate[1]) for coordinate in ring]
    min_x = min(xs)
    min_y = min(ys)
    span = max(max(xs) - min_x, max(ys) - min_y)
    if not math.isfinite(span) or span <= 0:
        _fail("The authorized polygon cannot be normalized.", "normalization_failed")
    normalized = [
        [round((x - min_x) / span, 6), round((y - min_y) / span, 6)]
        for x, y in zip(xs, ys, strict=True)
    ]
    if normalized[0] != normalized[-1]:
        _fail("The normalized DEMO ring is not closed.", "normalization_failed")
    return [normalized]


def _demo_artifact(source: Mapping[str, Any]) -> dict[str, Any]:
    attributes = source["attributes"]
    annotation_text = f"{attributes['BUILD_NO']}{attributes['BUILD_STR']}"
    artifact: dict[str, Any] = {
        "artifact_schema": ARTIFACT_SCHEMA,
        "status": "rendered-derived-demo",
        "execution_id": EXECUTION_ID,
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
        "resolution_sha256": EXPECTED_RESOLUTION_SHA256,
        "feature_reference": EXPECTED_FEATURE_REFERENCE,
        "source_commitments": {
            "attribute_commitment_sha256": EXPECTED_ATTRIBUTE_COMMITMENT,
            "geometry_commitment_sha256": EXPECTED_GEOMETRY_COMMITMENT,
            "source_geometry_type": "PolygonZ",
            "source_vertex_count": source["vertex_count"],
            "source_ring_count": source["ring_count"],
        },
        "privacy": {
            "coordinate_space": "normalized-local-demo-not-geographic",
            "raw_geographic_coordinates_included": False,
            "raw_attributes_included": False,
            "annotation_value_included": False,
            "derived_normalized_shape_included": True,
        },
        "maplibre_demo": {
            "source": {
                "type": "geojson",
                "data": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "id": EXPECTED_FEATURE_REFERENCE,
                            "properties": {
                                "feature_code": "9310100",
                                "display_annotation": "樓層＋結構",
                                "annotation_value_sha256": canonical_sha256(
                                    {"annotation": annotation_text}
                                ),
                            },
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": _normalized_xy(source["coordinates"]),
                            },
                        }
                    ],
                },
            },
            "style": {
                "profile_id": "nma-maplibre-web-demo-v1",
                "boundary": {
                    "style": "solid",
                    "width_css_px": 1.0,
                    "color": "#111111",
                    "opacity": 1.0,
                },
                "hatch": {
                    "pattern_id": "nma-building-hatch-demo",
                    "spacing_css_px": "7.559055118110236",
                    "angle_degrees": 45.0,
                    "color": "#111111",
                    "clip_to_feature_geometry": True,
                },
                "annotation": {
                    "anchor_policy": "polygon-pole-of-inaccessibility",
                    "collision_policy": (
                        "suppress-if-no-interior-fit-or-higher-priority-collision"
                    ),
                    "outside_displacement_allowed": False,
                },
            },
            "controls": {
                "hatch_angle_degrees": {
                    "minimum_inclusive": 0.0,
                    "maximum_exclusive": 180.0,
                    "default": 45.0,
                    "step": 1.0,
                    "user_adjustable": True,
                    "demo_only": True,
                }
            },
        },
        "boundaries": {
            "source_accessed_read_only": True,
            "source_mutated": False,
            "source_z_preserved": True,
            "derived_view_uses_xy": True,
            "runtime_wired": False,
            "production_activated": False,
        },
    }
    artifact["artifact_sha256"] = artifact_sha256(artifact)
    return artifact


def _execution_package(plan: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    artifact = _demo_artifact(source)
    consumption: dict[str, Any] = {
        "consumption_schema": CONSUMPTION_SCHEMA,
        "consumption_id": CONSUMPTION_ID,
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
        "execution_id": EXECUTION_ID,
        "plan_sha256": plan["plan_sha256"],
        "idempotency_key_sha256": plan["idempotency_key_sha256"],
        "artifact_sha256": artifact["artifact_sha256"],
        "status": "consumed-once",
        "replay_allowed": False,
    }
    consumption["consumption_sha256"] = consumption_sha256(consumption)
    receipt: dict[str, Any] = {
        "receipt_schema": RECEIPT_SCHEMA,
        "receipt_id": RECEIPT_ID,
        "execution_id": EXECUTION_ID,
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
        "resolution_sha256": EXPECTED_RESOLUTION_SHA256,
        "plan_sha256": plan["plan_sha256"],
        "artifact_sha256": artifact["artifact_sha256"],
        "consumption_sha256": consumption["consumption_sha256"],
        "outcome": "success-derived-demo-only",
        "source_verification": {
            "archive_sha256_before": EXPECTED_ARCHIVE_SHA256,
            "archive_sha256_after": EXPECTED_ARCHIVE_SHA256,
            "attribute_commitment_sha256": EXPECTED_ATTRIBUTE_COMMITMENT,
            "geometry_commitment_sha256": EXPECTED_GEOMETRY_COMMITMENT,
        },
        "boundaries": deepcopy(PACKAGE_BOUNDARIES),
    }
    receipt["receipt_sha256"] = receipt_sha256(receipt)
    package: dict[str, Any] = {
        "package_version": PACKAGE_VERSION,
        "schema_version": PACKAGE_SCHEMA,
        "execution_id": EXECUTION_ID,
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
        "resolution_sha256": EXPECTED_RESOLUTION_SHA256,
        "plan_sha256": plan["plan_sha256"],
        "demo_artifact": artifact,
        "consumption_record": consumption,
        "receipt": receipt,
        "boundaries": deepcopy(PACKAGE_BOUNDARIES),
    }
    package["package_sha256"] = package_sha256(package)
    return package


def validate_build_demo_execution_package(
    package: Mapping[str, Any],
    authorization: Mapping[str, Any],
    resolution: Mapping[str, Any],
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate exact execution identities, internal records, and privacy boundaries."""

    validate_build_demo_authorization(
        authorization, resolution, review, proposal, decision
    )
    if not isinstance(package, Mapping):
        _fail("The BUILD-05 execution package must be an object.", "package_invalid")
    required = {
        "package_version",
        "schema_version",
        "execution_id",
        "authorization_id",
        "authorization_sha256",
        "resolution_sha256",
        "plan_sha256",
        "demo_artifact",
        "consumption_record",
        "receipt",
        "boundaries",
        "package_sha256",
    }
    if set(package) != required:
        _fail("The BUILD-05 package fields are not closed.", "package_invalid")
    exact = {
        "package_version": PACKAGE_VERSION,
        "schema_version": PACKAGE_SCHEMA,
        "execution_id": EXECUTION_ID,
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
        "resolution_sha256": EXPECTED_RESOLUTION_SHA256,
        "plan_sha256": EXPECTED_PLAN_SHA256,
        "boundaries": PACKAGE_BOUNDARIES,
    }
    for field, expected in exact.items():
        if package.get(field) != expected:
            _fail(f"The BUILD-05 {field} changed.", "package_invalid")
    artifact = package.get("demo_artifact")
    consumption = package.get("consumption_record")
    receipt = package.get("receipt")
    if not all(isinstance(item, Mapping) for item in (artifact, consumption, receipt)):
        _fail("The BUILD-05 internal records are invalid.", "package_invalid")
    if artifact.get("artifact_sha256") != artifact_sha256(artifact):
        _fail("The BUILD-05 artifact hash is invalid.", "artifact_hash_mismatch")
    if consumption.get("consumption_sha256") != consumption_sha256(consumption):
        _fail("The BUILD-05 consumption hash is invalid.", "consumption_hash_mismatch")
    if receipt.get("receipt_sha256") != receipt_sha256(receipt):
        _fail("The BUILD-05 receipt hash is invalid.", "receipt_hash_mismatch")
    if (
        consumption.get("artifact_sha256") != artifact.get("artifact_sha256")
        or receipt.get("artifact_sha256") != artifact.get("artifact_sha256")
        or receipt.get("consumption_sha256") != consumption.get("consumption_sha256")
        or consumption.get("status") != "consumed-once"
        or consumption.get("replay_allowed") is not False
    ):
        _fail("The BUILD-05 internal identity chain changed.", "package_invalid")
    computed = package_sha256(package)
    if package.get("package_sha256") != computed:
        _fail("The BUILD-05 package hash is invalid.", "package_hash_mismatch")
    if EXPECTED_PACKAGE_SHA256 is not None and computed != EXPECTED_PACKAGE_SHA256:
        _fail("The BUILD-05 package is not the frozen execution.", "package_hash_mismatch")
    serialized = json.dumps(package, ensure_ascii=False).casefold()
    if (
        IDEMPOTENCY_KEY.casefold() in serialized
        or "geometry_wkb_hex" in serialized
        or package["boundaries"] != PACKAGE_BOUNDARIES
    ):
        _fail("The BUILD-05 privacy boundary changed.", "privacy_boundary_mismatch")
    return deepcopy(dict(package))


def validate_build_demo_consumption_ledger(
    ledger: Mapping[str, Any], package: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate the persistent single-use state against the execution package."""

    if not isinstance(ledger, Mapping) or not isinstance(package, Mapping):
        _fail("The BUILD-05 consumption ledger is invalid.", "ledger_invalid")
    expected = package.get("consumption_record")
    if not isinstance(expected, Mapping) or dict(ledger) != dict(expected):
        _fail("The BUILD-05 consumption ledger changed.", "ledger_invalid")
    if (
        ledger.get("authorization_id") != AUTHORIZATION_ID
        or ledger.get("status") != "consumed-once"
        or ledger.get("replay_allowed") is not False
        or ledger.get("consumption_sha256") != consumption_sha256(ledger)
    ):
        _fail("The BUILD-05 consumption ledger is invalid.", "ledger_invalid")
    return deepcopy(dict(ledger))


def execute_build_demo_once(
    authorization: Mapping[str, Any],
    resolution: Mapping[str, Any],
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
    *,
    output_path: str | Path,
    consumption_ledger_path: str | Path,
    archive_path: str | Path = DEFAULT_ARCHIVE_PATH,
) -> dict[str, Any]:
    """Consume the capability once and atomically persist the redacted DEMO package."""

    output = Path(output_path)
    ledger_path = Path(consumption_ledger_path)
    source_path = Path(archive_path)
    output_identity = output.resolve(strict=False)
    ledger_identity = ledger_path.resolve(strict=False)
    source_identity = source_path.resolve(strict=False)
    if (
        output_identity == source_identity
        or ledger_identity in {output_identity, source_identity}
        or output.is_symlink()
        or ledger_path.is_symlink()
    ):
        _fail("The BUILD-05 output path is unsafe.", "output_path_invalid")
    if ledger_path.exists():
        _fail("The BUILD-04 authorization was already consumed.", "authorization_consumed")
    if output.exists():
        try:
            existing = json.loads(output.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise BuildDemoExecutionError(
                "The BUILD-05 output path already exists.", code="execution_conflict"
            ) from error
        if isinstance(existing, Mapping) and existing.get("authorization_id") == AUTHORIZATION_ID:
            _fail("The BUILD-04 authorization was already consumed.", "authorization_consumed")
        _fail("The BUILD-05 output path already exists.", "execution_conflict")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    claim = {
        "consumption_schema": CONSUMPTION_SCHEMA,
        "authorization_id": AUTHORIZATION_ID,
        "status": "claimed-fail-closed",
    }
    try:
        with ledger_path.open("x", encoding="utf-8") as stream:
            stream.write(_canonical_bytes(claim).decode("utf-8"))
    except FileExistsError as error:
        raise BuildDemoExecutionError(
            "The BUILD-04 authorization was already consumed.",
            code="authorization_consumed",
        ) from error
    request = _request(authorization)
    plan = plan_build_demo_consumption(
        authorization,
        resolution,
        review,
        proposal,
        decision,
        request,
    )
    if plan.get("plan_sha256") != EXPECTED_PLAN_SHA256:
        _fail("The BUILD-04 consumption plan changed.", "plan_hash_mismatch")
    before = _file_sha256(source_path) if source_path.is_file() else None
    source = _read_private_feature(source_path)
    after = _file_sha256(source_path)
    if before != EXPECTED_ARCHIVE_SHA256 or after != EXPECTED_ARCHIVE_SHA256:
        _fail("The private BUILD archive changed during execution.", "source_mutation_detected")
    package = _execution_package(plan, source)
    validate_build_demo_execution_package(
        package, authorization, resolution, review, proposal, decision
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    if temporary.exists() or temporary.is_symlink():
        _fail("The BUILD-05 temporary output path is unsafe.", "output_path_invalid")
    temporary.write_bytes(_canonical_bytes(package))
    temporary.replace(output)
    ledger_temporary = ledger_path.with_name(f".{ledger_path.name}.tmp")
    if ledger_temporary.exists() or ledger_temporary.is_symlink():
        _fail("The BUILD-05 ledger temporary path is unsafe.", "output_path_invalid")
    ledger_temporary.write_bytes(_canonical_bytes(package["consumption_record"]))
    ledger_temporary.replace(ledger_path)
    validate_build_demo_consumption_ledger(
        json.loads(ledger_path.read_text(encoding="utf-8")), package
    )
    if _file_sha256(source_path) != EXPECTED_ARCHIVE_SHA256:
        _fail("The private BUILD archive changed after execution.", "source_mutation_detected")
    return deepcopy(package)


__all__ = [
    "BuildDemoExecutionError",
    "EXPECTED_PACKAGE_SHA256",
    "artifact_sha256",
    "consumption_sha256",
    "execute_build_demo_once",
    "package_sha256",
    "receipt_sha256",
    "validate_build_demo_execution_package",
    "validate_build_demo_consumption_ledger",
]

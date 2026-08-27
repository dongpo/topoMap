"""BUILD-10 controlled Building production implementation.

This production-capable, activation-held executor consumes the frozen BUILD-09F contract while
reusing canonical NMA source, portrayal, MapLibre-record, and Core identity boundaries.
"""

from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Mapping, Sequence

from nma.core import canonical_sha256, validate_sha256
from nma.ogr import inspect_dataset, read_vector_dataset
from nma.real_layer import (
    extract_reviewed_source_layers,
    file_sha256,
    inventory_shapefile_archive,
)

IMPLEMENTATION_SCHEMA = "nma.building-controlled-production-implementation/1.0"
PLAN_SCHEMA = "nma.building-production-execution-plan/1.0"
PROVENANCE_SCHEMA = "nma.building-production-provenance/1.0"
OBSERVATION_SCHEMA = "nma.building-production-observation/1.0"
VERIFICATION_SCHEMA = "nma.building-production-verification/1.0"
RECEIPT_SCHEMA = "nma.building-production-receipt/1.0"

EXPECTED_POLICY_SHA256 = "dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1"
EXPECTED_CONTRACT_SHA256 = "5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88"
EXPECTED_SOURCE_ARCHIVE_SHA256 = (
    "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
)
EXPECTED_SOURCE_ARCHIVE_NAME = "112年多維度SHP成果_0502.zip"
BINDING_POLICY_ID = "build-09f:local-version-package-scoped-production-binding"
DERIVATION_ALGORITHM = "nma.derive-xy-for-portrayal/1.0"
PLACEMENT_ALGORITHM = "nma.deterministic-polygon-interior-point/1.0"
OUTPUT_CRS = "EPSG:4326"
LEGACY_DROP_Z_DISPOSITION = {
    "legacy_module": "nma.real_layer",
    "legacy_profile": "building-polygon",
    "classification": "incompatible-non-authoritative-vs3-path",
    "production_disposition": "bypassed-by-build10-controlled-building-path",
    "execute_real_layer_called": False,
    "dim_xy_requested": False,
    "source_write_target": None,
}

# The official logical definition is copied from the frozen BUILD-09E2 trace.  The delivered OGR
# representation is the exact seven-field schema observed in both authorized package members.
# BUILD_H and GROUP_ID retain both representations; the adapter does not reinterpret either field.
BUILD_SCHEMA: tuple[dict[str, Any], ...] = (
    {
        "name": "BUILD_ID",
        "official_definition": "Text(16)",
        "delivered_type": "String",
        "width": 16,
        "semantic_status": "established-identifier",
    },
    {
        "name": "TERRAINID",
        "official_definition": "Text(8)",
        "delivered_type": "String",
        "width": 8,
        "semantic_status": "established-building-terrain-class",
    },
    {
        "name": "BUILD_STR",
        "official_definition": "Text(3)",
        "delivered_type": "String",
        "width": 3,
        "semantic_status": "established-structure-annotation-component",
    },
    {
        "name": "BUILD_NO",
        "official_definition": "Integer(3)",
        "delivered_type": "Integer",
        "width": 3,
        "semantic_status": "established-floor-count-annotation-component",
    },
    {
        "name": "BUILD_H",
        "official_definition": "Double(6,2)",
        "delivered_type": "Real",
        "width": 7,
        "precision": 2,
        "semantic_status": "intentionally-opaque-for-build-10",
    },
    {
        "name": "GROUP_ID",
        "official_definition": "LongInteger(16)",
        "delivered_type": "String",
        "width": 16,
        "semantic_status": "intentionally-opaque-for-build-10",
    },
    {
        "name": "MDATE",
        "official_definition": "Text(8)",
        "delivered_type": "String",
        "width": 8,
        "semantic_status": "intentionally-opaque-for-build-10",
    },
)


class BuildingProductionError(ValueError):
    """A controlled Building implementation boundary failed closed."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildingProductionError(message, code=code)


def _record(value: Mapping[str, Any], hash_field: str) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result.pop(hash_field, None)
    result[hash_field] = canonical_sha256(result)
    return result


def _verify_record(value: Any, hash_field: str, *, code: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail("A required provenance record is missing.", code)
    result = deepcopy(dict(value))
    supplied = result.pop(hash_field, None)
    if supplied != canonical_sha256(result):
        _fail("A controlled Building provenance identity was tampered.", code)
    result[hash_field] = supplied
    return result


def _load_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuildingProductionError(
            f"The required Building artifact is unavailable: {path.name}.", code=code
        ) from error
    if not isinstance(value, dict):
        _fail("A required Building artifact is not an object.", code)
    return value


def _validate_contract_mapping(contract: Any) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        _fail("The finalized BUILD-09F production contract is missing.", "invalid_contract_identity")
    result = deepcopy(dict(contract))
    supplied = result.pop("finalized_contract_sha256", None)
    if supplied != EXPECTED_CONTRACT_SHA256 or canonical_sha256(result) != supplied:
        _fail("The finalized BUILD-09F production contract identity is invalid.", "invalid_contract_identity")
    result["finalized_contract_sha256"] = supplied
    return result


def _validate_policy_mapping(policy: Any) -> dict[str, Any]:
    if not isinstance(policy, Mapping):
        _fail("The BUILD-09F policy authorization is missing.", "invalid_policy_identity")
    result = deepcopy(dict(policy))
    supplied = result.pop("policy_record_sha256", None)
    if supplied != EXPECTED_POLICY_SHA256 or canonical_sha256(result) != supplied:
        _fail("The BUILD-09F policy authorization identity is invalid.", "invalid_policy_identity")
    result["policy_record_sha256"] = supplied
    return result


def load_frozen_contract(repository_root: str | Path) -> dict[str, Any]:
    """Load and validate only the finalized BUILD-09F contract and its policy identity."""

    root = Path(repository_root)
    policy = _load_json(
        root
        / "data/specifications/nma-build-09f-golden-human-building-production-policy-authorization-v1.0.json",
        code="invalid_policy_identity",
    )
    contract = _load_json(
        root / "data/specifications/nma-build-09f-finalized-building-production-contract-v1.0.json",
        code="invalid_contract_identity",
    )
    policy = _validate_policy_mapping(policy)
    contract = _validate_contract_mapping(contract)
    supplied_policy = policy["policy_record_sha256"]
    if contract.get("bindings", {}).get("build09f_policy_record_sha256") != supplied_policy:
        _fail("The finalized contract is not bound to the authorized policy.", "invalid_policy_identity")
    required_holds = {
        "production_activation_allowed": False,
        "official_portrayal_activation_allowed": False,
        "source_mutation_allowed": False,
        "source_z_drop_allowed": False,
        "unbounded_runtime_wiring_allowed": False,
        "build10_readiness": "READY-FOR-BUILD-10",
        "status": "production-candidate",
    }
    if any(contract.get(key) != expected for key, expected in required_holds.items()):
        _fail("The finalized BUILD-09F safety or readiness boundary changed.", "contract_mismatch")
    authorization = contract.get("implementation_authorization", {})
    if (
        authorization.get("controlled_production_implementation_allowed") is not True
        or authorization.get("production_activation_allowed") is not False
        or authorization.get("official_portrayal_activation_allowed") is not False
        or authorization.get("source_mutation_allowed") is not False
        or authorization.get("source_z_drop_allowed") is not False
    ):
        _fail("BUILD-09F does not authorize this controlled implementation.", "contract_mismatch")
    return {"policy": policy, "contract": contract}


def building_schema_identity() -> str:
    return canonical_sha256(list(BUILD_SCHEMA))


def _normalized_observed_schema(fields: Any) -> list[dict[str, Any]]:
    if not isinstance(fields, list):
        _fail("The Building layer schema is missing.", "schema_mismatch")
    normalized: list[dict[str, Any]] = []
    for field in fields:
        if not isinstance(field, Mapping):
            _fail("The Building layer schema is malformed.", "schema_mismatch")
        item = {key: field.get(key) for key in ("name", "type", "width")}
        if field.get("precision") is not None:
            item["precision"] = field.get("precision")
        normalized.append(item)
    return normalized


def validate_building_schema(fields: Any) -> dict[str, Any]:
    expected = []
    for field in BUILD_SCHEMA:
        item = {
            "name": field["name"],
            "type": field["delivered_type"],
            "width": field["width"],
        }
        if "precision" in field:
            item["precision"] = field["precision"]
        expected.append(item)
    observed = _normalized_observed_schema(fields)
    if observed != expected:
        _fail("The source does not match the frozen seven-field BUILD schema.", "schema_mismatch")
    return {
        "schema_identity": building_schema_identity(),
        "field_count": 7,
        "official_logical_schema": [
            {"name": item["name"], "definition": item["official_definition"]}
            for item in BUILD_SCHEMA
        ],
        "delivered_adapter_schema": observed,
        "opaque_fields": [
            item["name"]
            for item in BUILD_SCHEMA
            if item["semantic_status"] == "intentionally-opaque-for-build-10"
        ],
    }


def _contract_bindings(contract: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    bindings = contract.get("authorized_local_policies", {}).get("j13_j17", {}).get("bindings")
    if not isinstance(bindings, list) or len(bindings) != 2:
        _fail("The package-scoped binding contract is invalid.", "portrayal_contract_mismatch")
    result: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        if not isinstance(binding, Mapping) or not isinstance(binding.get("package_scope"), str):
            _fail("The package-scoped binding contract is invalid.", "portrayal_contract_mismatch")
        scope = binding["package_scope"]
        if scope in result:
            _fail("The contract contains an ambiguous package binding.", "ambiguous_package")
        result[scope] = deepcopy(dict(binding))
    return result


def bind_building_package(
    *,
    contract: Mapping[str, Any],
    package_identities: Sequence[str],
    available_layer_ids: Sequence[str],
    observed_fields: Any,
    source_archive_sha256: str,
    component_sha256: Mapping[str, str],
    geographic_project_scope: str,
) -> dict[str, Any]:
    """Select exactly one authorized package member without cross-prefix fallback."""

    contract = _validate_contract_mapping(contract)
    if isinstance(package_identities, (str, bytes)) or not isinstance(package_identities, Sequence):
        _fail("An exact source package identity is required.", "ambiguous_package")
    if len(package_identities) != 1 or len(set(package_identities)) != 1:
        _fail("The source package identity is ambiguous.", "ambiguous_package")
    package_identity = package_identities[0]
    if not isinstance(package_identity, str) or package_identity.strip() != package_identity:
        _fail("The source package identity is invalid.", "unknown_package")
    bindings = _contract_bindings(contract)
    binding = bindings.get(package_identity)
    if binding is None:
        _fail("The source package is not authorized by BUILD-09F.", "unknown_package")
    prefix = package_identity.split("_", 1)[0]
    if prefix != binding.get("package_prefix"):
        _fail("The source package prefix does not match its binding.", "unknown_package")
    layers = list(available_layer_ids)
    if not layers:
        _fail("The authorized Building layer is absent.", "missing_building_layer")
    if len(layers) != 1:
        _fail("The source contains an ambiguous or unexpected Building layer.", "unexpected_layer")
    selected_layer = layers[0]
    if selected_layer != binding.get("layer_identity"):
        _fail("The package and Building layer do not match.", "package_layer_mismatch")
    if selected_layer.split("_", 1)[0] != prefix:
        _fail("Cross-prefix Building substitution is forbidden.", "package_layer_mismatch")
    try:
        validate_sha256(source_archive_sha256)
    except ValueError as error:
        raise BuildingProductionError(
            "The source archive identity is invalid.", code="unauthorized_source_path"
        ) from error
    if source_archive_sha256 != EXPECTED_SOURCE_ARCHIVE_SHA256:
        _fail("The source archive is not the authorized delivery.", "unauthorized_source_path")
    if not isinstance(component_sha256, Mapping) or set(component_sha256) != {
        ".cpg",
        ".dbf",
        ".prj",
        ".shp",
        ".shx",
    }:
        _fail("The selected Building component identity is incomplete.", "tampered_provenance")
    for digest in component_sha256.values():
        try:
            validate_sha256(digest)
        except ValueError as error:
            raise BuildingProductionError(
                "A selected Building component identity is invalid.", code="tampered_provenance"
            ) from error
    schema = validate_building_schema(observed_fields)
    expected_scope = {
        "J13": "Baoshan urban-plan project area",
        "J17": "Hsinchu Science Park special-plan project area, Baoshan portion",
    }[prefix]
    if geographic_project_scope != expected_scope:
        _fail("The geographic/project scope does not match the source package.", "package_layer_mismatch")
    return {
        "source_package_identity": package_identity,
        "geographic_project_scope": geographic_project_scope,
        "selected_layer": selected_layer,
        "schema_identity": schema["schema_identity"],
        "schema": schema,
        "binding_policy_identity": BINDING_POLICY_ID,
        "binding_policy_authority": "local-nma-production-policy",
        "source_archive_sha256": source_archive_sha256,
        "component_sha256": dict(sorted(component_sha256.items())),
        "cross_prefix_fallback_used": False,
        "global_equivalence_asserted": False,
    }


def validate_authorized_source_path(path: str | Path, *, observed_sha256: str) -> Path:
    source = Path(path)
    try:
        resolved = source.resolve(strict=True)
    except OSError as error:
        raise BuildingProductionError(
            "The authorized source archive path is unavailable.", code="unauthorized_source_path"
        ) from error
    if not resolved.is_file() or source.name != EXPECTED_SOURCE_ARCHIVE_NAME:
        _fail("The source path is not the authorized archive.", "unauthorized_source_path")
    if observed_sha256 != EXPECTED_SOURCE_ARCHIVE_SHA256:
        _fail("The source archive identity changed.", "unauthorized_source_path")
    return resolved


def load_authoritative_package(
    *,
    contract: Mapping[str, Any],
    archive_path: str | Path,
    package_identity: str,
    geographic_project_scope: str,
) -> dict[str, Any]:
    """Read one exact package member and derive a separate reprojected PolygonZ view.

    GDAL reads only a temporary extracted component family.  Its output is captured from stdout;
    neither the authoritative archive nor the extracted source component is an output target.
    Dimensional reduction is deliberately not requested here.
    """

    contract = _validate_contract_mapping(contract)
    archive = Path(archive_path)
    observed_archive_sha256 = file_sha256(archive)
    validate_authorized_source_path(archive, observed_sha256=observed_archive_sha256)
    inventory = inventory_shapefile_archive(
        archive, expected_sha256=EXPECTED_SOURCE_ARCHIVE_SHA256
    )
    bindings = _contract_bindings(contract)
    expected = bindings.get(package_identity)
    if expected is None:
        _fail("The source package is not authorized by BUILD-09F.", "unknown_package")
    expected_group_key = f"{package_identity}/{expected['layer_identity']}"
    matches = [
        item
        for item in inventory["layers"]
        if (
            (item["group_key"] == expected_group_key or item["group_key"].endswith("/" + expected_group_key))
            and item["scope"] == "primary"
        )
    ]
    if not matches:
        _fail("The authorized Building layer is absent.", "missing_building_layer")
    if len(matches) != 1:
        _fail("The authorized package identity is ambiguous.", "ambiguous_package")
    selected = matches[0]
    components = {item["extension"]: item["sha256"] for item in selected["components"]}
    ogr2ogr = shutil.which("ogr2ogr")
    if ogr2ogr is None:
        _fail("GDAL/OGR is required for controlled source derivation.", "conversion_unavailable")
    with tempfile.TemporaryDirectory(prefix="nma-building-derived-view-") as temporary:
        source_paths, extracted_components = extract_reviewed_source_layers(
            archive, [expected["layer_identity"]], Path(temporary)
        )
        if len(source_paths) != 1:
            _fail("The authorized Building layer is ambiguous.", "ambiguous_package")
        source = source_paths[0]
        if {item["extension"]: item["sha256"] for item in extracted_components} != components:
            _fail("Extracted source component provenance changed.", "tampered_provenance")
        inspection = inspect_dataset(source, timeout_seconds=30)
        if not inspection.get("available") or inspection.get("geometry_type") != "PolygonZ":
            _fail("The authorized source is not an inspectable PolygonZ layer.", "source_geometry_mismatch")
        binding = bind_building_package(
            contract=contract,
            package_identities=[package_identity],
            available_layer_ids=[inspection.get("layer")],
            observed_fields=inspection.get("fields"),
            source_archive_sha256=observed_archive_sha256,
            component_sha256=components,
            geographic_project_scope=geographic_project_scope,
        )
        authoritative, read_inspection = read_vector_dataset(source, timeout_seconds=120)
        if read_inspection.get("geometry_type") != "PolygonZ":
            _fail("The authoritative source read lost PolygonZ.", "source_z_missing")
        command = [
            ogr2ogr,
            "-f",
            "GeoJSON",
            "/vsistdout/",
            str(source),
            "-t_srs",
            OUTPUT_CRS,
            "-lco",
            "RFC7946=YES",
        ]
        try:
            process = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            reprojected_polygonz = json.loads(process.stdout)
        except subprocess.TimeoutExpired as error:
            raise BuildingProductionError(
                "Controlled Building reprojection timed out.", code="conversion_failed"
            ) from error
        except (subprocess.CalledProcessError, json.JSONDecodeError) as error:
            raise BuildingProductionError(
                "Controlled Building reprojection failed.", code="conversion_failed"
            ) from error
    return {
        "binding": binding,
        "authoritative_collection": authoritative,
        "portrayal_polygonz_collection": reprojected_polygonz,
        "source_crs": inspection.get("crs") or inspection.get("crs_name"),
        "output_crs": OUTPUT_CRS,
        "external_derivation": {
            "engine": inspection.get("engine"),
            "operation": "reproject-preserve-z-to-separate-stdout-artifact",
            "dimensional_reduction_requested": False,
            "source_write_target": None,
            "derived_writeback_allowed": False,
        },
    }


def bind_annotation_content(properties: Mapping[str, Any]) -> dict[str, Any]:
    """Apply exact ``{BUILD_NO}{BUILD_STR}`` order, suppressing incomplete labels."""

    if "BUILD_NO" not in properties or "BUILD_STR" not in properties:
        _fail("Required annotation fields are missing from a Building feature.", "schema_mismatch")
    floor = properties["BUILD_NO"]
    structure = properties["BUILD_STR"]
    if floor is not None and (isinstance(floor, bool) or not isinstance(floor, int)):
        _fail("BUILD_NO is malformed.", "malformed_annotation_semantics")
    if structure is not None and not isinstance(structure, str):
        _fail("BUILD_STR is malformed.", "malformed_annotation_semantics")
    floor_present = floor is not None
    structure_present = structure is not None and structure != ""
    if not floor_present or not structure_present:
        missing = []
        if not floor_present:
            missing.append("BUILD_NO")
        if not structure_present:
            missing.append("BUILD_STR")
        return {
            "status": "suppressed-incomplete-content",
            "text": None,
            "missing_fields": missing,
            "fallback_used": False,
            "content_rule": "floor count followed by structure",
            "field_binding_rule": "{BUILD_NO}{BUILD_STR}",
        }
    return {
        "status": "bound",
        "text": f"{floor}{structure}",
        "missing_fields": [],
        "fallback_used": False,
        "content_rule": "floor count followed by structure",
        "field_binding_rule": "{BUILD_NO}{BUILD_STR}",
    }


def _finite_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _map_positions(value: Any, transform: Any) -> Any:
    if (
        isinstance(value, list)
        and len(value) >= 2
        and _finite_number(value[0])
        and _finite_number(value[1])
    ):
        return transform(value)
    if not isinstance(value, list) or not value:
        _fail("The PolygonZ coordinates are malformed.", "source_geometry_mismatch")
    return [_map_positions(item, transform) for item in value]


def _xy_geometry(geometry: Mapping[str, Any]) -> dict[str, Any]:
    geometry_type = geometry.get("type")
    if geometry_type not in {"Polygon", "MultiPolygon"}:
        _fail("The authoritative Building geometry is not PolygonZ.", "source_geometry_mismatch")

    def strip(position: list[Any]) -> list[Any]:
        if len(position) < 3 or not _finite_number(position[2]):
            _fail("The authoritative Building geometry does not preserve a Z value.", "source_z_missing")
        return [position[0], position[1]]

    return {"type": geometry_type, "coordinates": _map_positions(geometry.get("coordinates"), strip)}


def _signed_ring_area(ring: list[list[float]]) -> float:
    return sum(
        (ring[index][0] * ring[index + 1][1]) - (ring[index + 1][0] * ring[index][1])
        for index in range(len(ring) - 1)
    ) / 2.0


def _polygon_area(polygon: list[list[list[float]]]) -> float:
    if not polygon:
        return 0.0
    return abs(_signed_ring_area(polygon[0])) - sum(
        abs(_signed_ring_area(hole)) for hole in polygon[1:]
    )


def _point_on_segment(point: tuple[float, float], first: list[float], second: list[float]) -> bool:
    x, y = point
    cross = (x - first[0]) * (second[1] - first[1]) - (y - first[1]) * (
        second[0] - first[0]
    )
    if abs(cross) > 1e-12:
        return False
    return (
        min(first[0], second[0]) <= x <= max(first[0], second[0])
        and min(first[1], second[1]) <= y <= max(first[1], second[1])
    )


def _inside_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    inside = False
    x, y = point
    for index in range(len(ring) - 1):
        first, second = ring[index], ring[index + 1]
        if _point_on_segment(point, first, second):
            return False
        if (first[1] > y) != (second[1] > y):
            crossing = (second[0] - first[0]) * (y - first[1]) / (second[1] - first[1]) + first[0]
            if x < crossing:
                inside = not inside
    return inside


def _inside_polygon(point: tuple[float, float], polygon: list[list[list[float]]]) -> bool:
    return bool(polygon) and _inside_ring(point, polygon[0]) and not any(
        _inside_ring(point, hole) for hole in polygon[1:]
    )


def deterministic_interior_point(geometry: Mapping[str, Any]) -> list[float]:
    """Return a deterministic interior point, never an arbitrary external relocation."""

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    polygons = [coordinates] if geometry_type == "Polygon" else coordinates
    if geometry_type not in {"Polygon", "MultiPolygon"} or not isinstance(polygons, list):
        _fail("Annotation placement requires derived polygon geometry.", "placement_failed")
    candidates = [polygon for polygon in polygons if isinstance(polygon, list) and polygon]
    if not candidates:
        _fail("No polygon is available for annotation placement.", "placement_failed")
    polygon = min(
        candidates,
        key=lambda item: (-_polygon_area(item), canonical_sha256(item)),
    )
    shell = polygon[0]
    if not isinstance(shell, list) or len(shell) < 4 or shell[0] != shell[-1]:
        _fail("The polygon ring is not closed.", "placement_failed")
    xs = [point[0] for point in shell]
    ys = sorted(set(point[1] for point in shell))
    center = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
    if _inside_polygon(center, polygon):
        return [center[0], center[1]]
    scanlines = sorted(
        {center[1]} | {(first + second) / 2.0 for first, second in zip(ys, ys[1:])}
    )
    best: tuple[float, float, float] | None = None
    selected: tuple[float, float] | None = None
    all_rings = polygon
    for y in scanlines:
        intersections: list[float] = []
        for ring in all_rings:
            for index in range(len(ring) - 1):
                first, second = ring[index], ring[index + 1]
                if (first[1] > y) != (second[1] > y):
                    intersections.append(
                        first[0]
                        + (second[0] - first[0]) * (y - first[1]) / (second[1] - first[1])
                    )
        intersections.sort()
        for first, second in zip(intersections[0::2], intersections[1::2]):
            point = ((first + second) / 2.0, y)
            width = second - first
            if width > 0 and _inside_polygon(point, polygon):
                choice = (width, -abs(y - center[1]), -point[0])
                if best is None or choice > best:
                    best = choice
                    selected = point
    if best is None or selected is None:
        _fail("A safe interior annotation point could not be derived.", "placement_failed")
    return [selected[0], selected[1]]


def _validate_feature_properties(properties: Any) -> dict[str, Any]:
    if not isinstance(properties, Mapping) or set(properties) != {
        "BUILD_ID",
        "TERRAINID",
        "BUILD_STR",
        "BUILD_NO",
        "BUILD_H",
        "GROUP_ID",
        "MDATE",
    }:
        _fail("A Building feature does not match the seven-field schema.", "schema_mismatch")
    checked = deepcopy(dict(properties))
    string_fields = {"BUILD_ID": 16, "TERRAINID": 8, "GROUP_ID": 16, "MDATE": 8}
    for name, width in string_fields.items():
        value = checked[name]
        if value is not None and (not isinstance(value, str) or len(value) > width):
            _fail(f"{name} is malformed.", "schema_mismatch")
    structure = checked["BUILD_STR"]
    if structure is not None and (not isinstance(structure, str) or len(structure) > 3):
        _fail("BUILD_STR is malformed.", "malformed_annotation_semantics")
    floor = checked["BUILD_NO"]
    if floor is not None and (isinstance(floor, bool) or not isinstance(floor, int)):
        _fail("BUILD_NO is malformed.", "malformed_annotation_semantics")
    height = checked["BUILD_H"]
    if height is not None and not _finite_number(height):
        _fail("BUILD_H is malformed.", "schema_mismatch")
    if not checked["BUILD_ID"] or not checked["TERRAINID"]:
        _fail("A required Building identity value is absent.", "schema_mismatch")
    return checked


def derive_xy_for_portrayal(
    collection: Mapping[str, Any],
    *,
    binding: Mapping[str, Any],
    source_crs: str,
    output_crs: str,
    portrayal_polygonz_collection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an immutable, non-writing XY portrayal view and annotation point collection."""

    if output_crs != OUTPUT_CRS:
        _fail("The requested output profile/CRS is unsupported.", "unsupported_output_profile")
    if not isinstance(collection, Mapping) or collection.get("type") != "FeatureCollection":
        _fail("The authoritative source is not a FeatureCollection.", "source_geometry_mismatch")
    before = canonical_sha256(collection)
    features = collection.get("features")
    if not isinstance(features, list):
        _fail("The authoritative source features are missing.", "source_geometry_mismatch")
    portrayal_source = portrayal_polygonz_collection or collection
    if not isinstance(portrayal_source, Mapping) or portrayal_source.get("type") != "FeatureCollection":
        _fail("The portrayal PolygonZ derivation is invalid.", "source_geometry_mismatch")
    portrayal_features = portrayal_source.get("features")
    if not isinstance(portrayal_features, list) or len(portrayal_features) != len(features):
        _fail("The portrayal derivation changed the source population.", "tampered_provenance")
    portrayal_by_id: dict[str, Mapping[str, Any]] = {}
    for feature in portrayal_features:
        if not isinstance(feature, Mapping) or not isinstance(feature.get("properties"), Mapping):
            _fail("The portrayal derivation contains a malformed feature.", "tampered_provenance")
        feature_id = feature["properties"].get("BUILD_ID")
        if not isinstance(feature_id, str) or feature_id in portrayal_by_id:
            _fail("The portrayal derivation has an ambiguous feature identity.", "tampered_provenance")
        portrayal_by_id[feature_id] = feature
    derived_features: list[dict[str, Any]] = []
    annotation_features: list[dict[str, Any]] = []
    source_geometry_hashes: list[dict[str, str]] = []
    derived_geometry_hashes: list[dict[str, str]] = []
    suppressed = 0
    placement_suppressed = 0
    for feature in features:
        if not isinstance(feature, Mapping) or feature.get("type") != "Feature":
            _fail("The authoritative source contains a malformed feature.", "source_geometry_mismatch")
        properties = _validate_feature_properties(feature.get("properties"))
        geometry = feature.get("geometry")
        if not isinstance(geometry, Mapping):
            _fail("A Building source geometry is missing.", "source_geometry_mismatch")
        source_geometry_sha256 = canonical_sha256(geometry)
        feature_id = properties["BUILD_ID"]
        portrayal_feature = portrayal_by_id.get(feature_id)
        if portrayal_feature is None:
            _fail("The portrayal derivation lost a source feature.", "tampered_provenance")
        portrayal_properties = _validate_feature_properties(portrayal_feature.get("properties"))
        if portrayal_properties != properties:
            _fail("The portrayal derivation changed source attributes.", "tampered_provenance")
        portrayal_geometry = portrayal_feature.get("geometry")
        if not isinstance(portrayal_geometry, Mapping):
            _fail("The portrayal PolygonZ geometry is missing.", "source_geometry_mismatch")
        xy = _xy_geometry(portrayal_geometry)
        derived_geometry_sha256 = canonical_sha256(xy)
        source_geometry_hashes.append(
            {"source_feature_identity": feature_id, "source_polygonz_sha256": source_geometry_sha256}
        )
        derived_geometry_hashes.append(
            {"source_feature_identity": feature_id, "derived_xy_sha256": derived_geometry_sha256}
        )
        derived_features.append(
            {
                "type": "Feature",
                "id": feature_id,
                "properties": properties,
                "geometry": xy,
            }
        )
        annotation = bind_annotation_content(properties)
        if annotation["status"] != "bound":
            suppressed += 1
            continue
        try:
            point = deterministic_interior_point(xy)
        except BuildingProductionError as error:
            if error.code != "placement_failed":
                raise
            suppressed += 1
            placement_suppressed += 1
            continue
        annotation_features.append(
            {
                "type": "Feature",
                "id": feature_id,
                "properties": {
                    "BUILD_ID": feature_id,
                    "nma:annotation": annotation["text"],
                    "nma:placement_algorithm": PLACEMENT_ALGORITHM,
                },
                "geometry": {"type": "Point", "coordinates": point},
            }
        )
    if canonical_sha256(collection) != before:
        _fail("The authoritative source was mutated during XY derivation.", "attempted_source_write")
    derived = {
        "type": "FeatureCollection",
        "name": f"NMA_{binding['selected_layer']}_DERIVED_XY",
        "features": derived_features,
    }
    annotations = {
        "type": "FeatureCollection",
        "name": f"NMA_{binding['selected_layer']}_ANNOTATIONS",
        "features": annotation_features,
    }
    provenance = _record(
        {
            "schema": PROVENANCE_SCHEMA,
            "production_contract_sha256": EXPECTED_CONTRACT_SHA256,
            "policy_authorization_sha256": EXPECTED_POLICY_SHA256,
            "binding": deepcopy(dict(binding)),
            "source_crs": source_crs,
            "output_crs": output_crs,
            "source_feature_count": len(features),
            "source_collection_sha256": before,
            "source_geometry_identities": source_geometry_hashes,
            "reprojected_polygonz_collection_sha256": canonical_sha256(portrayal_source),
            "reprojection_performed": portrayal_polygonz_collection is not None,
            "reprojection_boundary": (
                "separate-non-writing-polygonz-derived-view"
                if portrayal_polygonz_collection is not None
                else "source-already-in-output-crs"
            ),
            "derived_xy_collection_sha256": canonical_sha256(derived),
            "derived_geometry_identities": derived_geometry_hashes,
            "annotation_collection_sha256": canonical_sha256(annotations),
            "derivation_algorithm": DERIVATION_ALGORITHM,
            "placement_algorithm": PLACEMENT_ALGORITHM,
            "authoritative_source_geometry": "PolygonZ",
            "source_immutable": True,
            "source_z_preserved_and_recoverable": True,
            "source_write_handle_exposed": False,
            "derived_xy_authoritative": False,
            "derived_xy_non_writing": True,
            "derived_xy_purpose": "portrayal-only",
            "geometry_repair_performed": False,
            "materialization": "ephemeral",
            "annotation_bound_count": len(annotation_features),
            "annotation_suppressed_count": suppressed,
            "annotation_placement_suppressed_count": placement_suppressed,
        },
        "provenance_sha256",
    )
    return {"derived_xy": derived, "annotations": annotations, "provenance": provenance}


def _format_number(value: float) -> str:
    return format(value, ".15g")


def procedural_hatch_resource(contract: Mapping[str, Any]) -> dict[str, Any]:
    contract = _validate_contract_mapping(contract)
    policies = contract.get("authorized_local_policies", {})
    hatch = policies.get("hatch", {})
    line = policies.get("line_output_profile", {})
    colour = policies.get("colour", {})
    opacity = policies.get("opacity", {})
    required = {
        "official_diagonal_semantics": True,
        "official_spacing_mm": 2.0,
        "local_angle_degrees": 45,
        "angle_authority": "local-production-policy",
        "hatch_resource_policy": "procedural-canonical",
        "deterministic_procedural_rendering_required": True,
    }
    if any(hatch.get(key) != value for key, value in required.items()):
        _fail("The procedural hatch contract changed.", "portrayal_contract_mismatch")
    if line.get("profile_id") != "nma-screen-96dpi-v1" or line.get("output_dpi") != 96:
        _fail("The Building output profile is unsupported.", "unsupported_output_profile")
    width = line.get("official_physical_width", {}).get("value") * line["output_dpi"] / 25.4
    if not math.isclose(width, line.get("derived_device_width_px"), rel_tol=0, abs_tol=1e-15):
        _fail("The physical line-width conversion changed.", "portrayal_contract_mismatch")
    spacing = hatch["official_spacing_mm"] * line["output_dpi"] / 25.4
    if colour.get("official_rgb_components") != [0, 0, 0]:
        _fail("The official Building RGB semantics changed.", "portrayal_contract_mismatch")
    if colour.get("optional_hex_serialization") != "#000000":
        _fail("The derived device colour serialization changed.", "portrayal_contract_mismatch")
    if opacity != {
        "applies_to": ["building-line", "building-hatch"],
        "authority": "local-output-profile-policy",
        "separate_component_values_require_explicit_contract_binding": True,
        "value": 1.0,
    }:
        _fail("The Building opacity policy changed.", "portrayal_contract_mismatch")
    size = _format_number(spacing)
    stroke = _format_number(width)
    twice = _format_number(spacing * 2)
    negative = _format_number(-spacing)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}"><path d="M 0 {size} L {size} 0 M {negative} '
        f'{size} L 0 0 M {size} {size} L {twice} 0" fill="none" stroke="#000000" '
        f'stroke-width="{stroke}" opacity="1"/></svg>'
    )
    basis = {
        "id": "nma-building-hatch-build09f-v1",
        "kind": "procedural-svg-image",
        "generator": "nma.procedural-building-hatch/1.0",
        "official_diagonal_semantics": True,
        "official_spacing": {"value": 2.0, "unit": "mm"},
        "local_angle": {"value": 45, "unit": "degrees", "authority": "local-production-policy"},
        "output_profile": {
            "id": line["profile_id"],
            "dpi": line["output_dpi"],
            "spacing_device_px_unquantized": spacing,
            "line_width_device_px_unquantized": width,
            "renderer_quantization": None,
        },
        "colour": {
            "official_source": {"representation": "RGB (0,0,0)", "components": [0, 0, 0]},
            "device_serialization": "#000000",
            "device_serialization_authority": "derived-device-serialization",
        },
        "opacity": {"value": 1.0, "authority": "local-output-profile-policy"},
        "svg": svg,
        "static_asset_dependency": None,
        "reproducible": True,
    }
    return {**basis, "resource_sha256": canonical_sha256(basis)}


def compile_maplibre_building(
    *,
    contract: Mapping[str, Any],
    binding: Mapping[str, Any],
    derived_xy: Mapping[str, Any],
    annotations: Mapping[str, Any],
) -> dict[str, Any]:
    line = contract["authorized_local_policies"]["line_output_profile"]
    width = line["official_physical_width"]["value"] * line["output_dpi"] / 25.4
    resource = procedural_hatch_resource(contract)
    source_id = "nma-building-derived-xy"
    annotation_source_id = "nma-building-annotation-points"
    common_metadata = {
        "nma:production-contract-sha256": EXPECTED_CONTRACT_SHA256,
        "nma:policy-authorization-sha256": EXPECTED_POLICY_SHA256,
        "nma:source-package-identity": binding["source_package_identity"],
        "nma:selected-source-layer": binding["selected_layer"],
        "nma:schema-identity": binding["schema_identity"],
        "nma:binding-policy-identity": binding["binding_policy_identity"],
        "nma:derived-xy-authoritative": False,
        "nma:production-activation-allowed": False,
        "nma:official-portrayal-activation-allowed": False,
    }
    layers = [
        {
            "id": "nma-building-hatch",
            "type": "fill",
            "source": source_id,
            "metadata": {**common_metadata, "nma:portrayal-component": "procedural-hatch"},
            "paint": {"fill-pattern": resource["id"], "fill-opacity": 1.0},
        },
        {
            "id": "nma-building-outline",
            "type": "line",
            "source": source_id,
            "metadata": {
                **common_metadata,
                "nma:official-line-width": {"value": 0.2, "unit": "mm"},
                "nma:device-width-formula": "device_px = physical_mm * output_dpi / 25.4",
                "nma:output-dpi": 96,
                "nma:derived-device-width-px": width,
                "nma:official-colour": {"representation": "RGB (0,0,0)", "components": [0, 0, 0]},
                "nma:device-colour-authority": "derived-device-serialization",
            },
            "paint": {"line-color": "#000000", "line-opacity": 1.0, "line-width": width},
        },
        {
            "id": "nma-building-annotation",
            "type": "symbol",
            "source": annotation_source_id,
            "metadata": {
                **common_metadata,
                "nma:content-rule": "floor count followed by structure",
                "nma:field-binding": "{BUILD_NO}{BUILD_STR}",
                "nma:placement-authority": "local-production-policy",
                "nma:placement-algorithm": PLACEMENT_ALGORITHM,
            },
            "layout": {
                "text-field": ["get", "nma:annotation"],
                "text-allow-overlap": False,
                "text-ignore-placement": False,
                "text-optional": True,
            },
            "paint": {"text-color": "#000000", "text-opacity": 1.0},
        },
    ]
    basis = {
        "schema": "nma.maplibre-building-production-candidate/1.0",
        "status": "implementation-ready-activation-hold",
        "sources": {
            source_id: {"type": "geojson", "data": deepcopy(dict(derived_xy))},
            annotation_source_id: {"type": "geojson", "data": deepcopy(dict(annotations))},
        },
        "resources": [resource],
        "layers": layers,
        "production_activation_allowed": False,
        "production_active": False,
        "official_portrayal_activation_allowed": False,
        "official_portrayal_active": False,
        "automatic_action": False,
        "map_mutation_performed": False,
    }
    return {**basis, "bundle_sha256": canonical_sha256(basis)}


def implement_controlled_building(
    *,
    contract_bundle: Mapping[str, Any],
    binding: Mapping[str, Any],
    authoritative_collection: Mapping[str, Any],
    source_crs: str,
    output_crs: str = OUTPUT_CRS,
    portrayal_polygonz_collection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce a deterministic candidate implementation and records; activation remains held."""

    contract = _validate_contract_mapping(contract_bundle.get("contract"))
    policy = _validate_policy_mapping(contract_bundle.get("policy"))
    if not isinstance(binding, Mapping) or not isinstance(binding.get("schema"), Mapping):
        _fail("The Building package binding is invalid.", "tampered_provenance")
    validated_binding = bind_building_package(
        contract=contract,
        package_identities=[binding.get("source_package_identity")],
        available_layer_ids=[binding.get("selected_layer")],
        observed_fields=binding["schema"].get("delivered_adapter_schema"),
        source_archive_sha256=binding.get("source_archive_sha256"),
        component_sha256=binding.get("component_sha256"),
        geographic_project_scope=binding.get("geographic_project_scope"),
    )
    if dict(binding) != validated_binding:
        _fail("The Building package binding provenance was tampered.", "tampered_provenance")
    binding = validated_binding
    if output_crs != OUTPUT_CRS:
        _fail("The output profile is unsupported.", "unsupported_output_profile")
    derivation = derive_xy_for_portrayal(
        authoritative_collection,
        binding=binding,
        source_crs=source_crs,
        output_crs=output_crs,
        portrayal_polygonz_collection=portrayal_polygonz_collection,
    )
    bundle = compile_maplibre_building(
        contract=contract,
        binding=binding,
        derived_xy=derivation["derived_xy"],
        annotations=derivation["annotations"],
    )
    plan = _record(
        {
            "schema": PLAN_SCHEMA,
            "status": "implementation-ready-activation-hold",
            "production_contract_sha256": EXPECTED_CONTRACT_SHA256,
            "policy_authorization_sha256": EXPECTED_POLICY_SHA256,
            "binding": deepcopy(dict(binding)),
            "source_geometry": "PolygonZ",
            "source_crs": source_crs,
            "output_crs": output_crs,
            "output_profile_id": "nma-screen-96dpi-v1",
            "operations": [
                "validate-contract-and-policy-identities",
                "bind-exact-source-package-and-layer",
                "validate-seven-field-build-schema",
                "validate-immutable-polygonz",
                "reproject-to-output-crs-in-separate-polygonz-view",
                "derive-xy-for-portrayal",
                "bind-floor-then-structure-annotation",
                "derive-deterministic-interior-annotation-points",
                "compile-procedural-canonical-hatch",
                "compile-maplibre-production-candidate",
                "verify-activation-hold",
            ],
            "permissions": {
                "source_read_allowed": True,
                "source_write_allowed": False,
                "source_geometry_repair_allowed": False,
                "source_z_removal_allowed": False,
                "production_activation_allowed": False,
                "official_portrayal_activation_allowed": False,
            },
        },
        "execution_plan_sha256",
    )
    observation = _record(
        {
            "schema": OBSERVATION_SCHEMA,
            "status": "controlled-implementation-observed",
            "execution_plan_sha256": plan["execution_plan_sha256"],
            "provenance_sha256": derivation["provenance"]["provenance_sha256"],
            "maplibre_bundle_sha256": bundle["bundle_sha256"],
            "source_feature_count": len(authoritative_collection["features"]),
            "derived_xy_feature_count": len(derivation["derived_xy"]["features"]),
            "annotation_feature_count": len(derivation["annotations"]["features"]),
            "source_mutated": False,
            "source_z_preserved": True,
            "derived_xy_non_authoritative": True,
            "map_mutation_performed": False,
            "production_active": False,
            "official_portrayal_active": False,
        },
        "observation_sha256",
    )
    checks = {
        "contract_identity": contract["finalized_contract_sha256"] == EXPECTED_CONTRACT_SHA256,
        "policy_identity": policy["policy_record_sha256"] == EXPECTED_POLICY_SHA256,
        "package_layer_binding": binding.get("cross_prefix_fallback_used") is False,
        "schema_identity": binding.get("schema_identity") == building_schema_identity(),
        "polygonz_preserved": derivation["provenance"]["source_z_preserved_and_recoverable"] is True,
        "derived_xy_non_writing": derivation["provenance"]["derived_xy_non_writing"] is True,
        "portrayal_contract": bundle["status"] == "implementation-ready-activation-hold",
        "production_activation_hold": bundle["production_activation_allowed"] is False,
        "official_portrayal_activation_hold": bundle["official_portrayal_activation_allowed"] is False,
    }
    if not all(checks.values()):
        _fail("Controlled Building verification failed.", "verification_failed")
    verification = _record(
        {
            "schema": VERIFICATION_SCHEMA,
            "status": "passed-controlled-implementation",
            "checks": checks,
            "execution_plan_sha256": plan["execution_plan_sha256"],
            "provenance_sha256": derivation["provenance"]["provenance_sha256"],
            "observation_sha256": observation["observation_sha256"],
            "maplibre_bundle_sha256": bundle["bundle_sha256"],
        },
        "verification_sha256",
    )
    receipt = _record(
        {
            "schema": RECEIPT_SCHEMA,
            "status": "implementation-complete-activation-hold",
            "execution_plan_sha256": plan["execution_plan_sha256"],
            "provenance_sha256": derivation["provenance"]["provenance_sha256"],
            "observation_sha256": observation["observation_sha256"],
            "verification_sha256": verification["verification_sha256"],
            "maplibre_bundle_sha256": bundle["bundle_sha256"],
            "rollback_cleanup": {
                "required": False,
                "reason": "ephemeral-derived-artifacts-only",
                "authoritative_source_rollback_required": False,
            },
            "implementation_ready": True,
            "production_active": False,
            "official_portrayal_active": False,
            "automatic_activation_performed": False,
        },
        "receipt_sha256",
    )
    record_basis = {
        "schema": IMPLEMENTATION_SCHEMA,
        "status": "implementation-complete-activation-hold",
        "plan": plan,
        "provenance": derivation["provenance"],
        "observation": observation,
        "verification": verification,
        "receipt": receipt,
        "production_activation_allowed": False,
        "official_portrayal_activation_allowed": False,
        "source_mutation_allowed": False,
        "source_z_drop_allowed": False,
    }
    record = {**record_basis, "implementation_record_sha256": canonical_sha256(record_basis)}
    return {
        "record": record,
        "derived_xy": derivation["derived_xy"],
        "annotations": derivation["annotations"],
        "maplibre": bundle,
    }


def verify_implementation_result(result: Any) -> bool:
    """Recompute the complete controlled record chain and reject tampered provenance."""

    if not isinstance(result, Mapping) or not isinstance(result.get("record"), Mapping):
        _fail("The controlled implementation result is invalid.", "tampered_provenance")
    record = deepcopy(dict(result["record"]))
    supplied = record.pop("implementation_record_sha256", None)
    if supplied != canonical_sha256(record):
        _fail("The implementation record identity was tampered.", "tampered_provenance")
    plan = _verify_record(record.get("plan"), "execution_plan_sha256", code="tampered_provenance")
    provenance = _verify_record(
        record.get("provenance"), "provenance_sha256", code="tampered_provenance"
    )
    observation = _verify_record(
        record.get("observation"), "observation_sha256", code="tampered_provenance"
    )
    verification = _verify_record(
        record.get("verification"), "verification_sha256", code="tampered_provenance"
    )
    receipt = _verify_record(record.get("receipt"), "receipt_sha256", code="tampered_provenance")
    maplibre = result.get("maplibre")
    if not isinstance(maplibre, Mapping):
        _fail("The MapLibre candidate is missing.", "tampered_provenance")
    maplibre_basis = deepcopy(dict(maplibre))
    maplibre_sha256 = maplibre_basis.pop("bundle_sha256", None)
    if maplibre_sha256 != canonical_sha256(maplibre_basis):
        _fail("The MapLibre candidate identity was tampered.", "tampered_provenance")
    for resource in maplibre.get("resources", []):
        if not isinstance(resource, Mapping):
            _fail("A procedural resource is malformed.", "tampered_provenance")
        resource_basis = deepcopy(dict(resource))
        resource_sha256 = resource_basis.pop("resource_sha256", None)
        if resource_sha256 != canonical_sha256(resource_basis):
            _fail("A procedural resource identity was tampered.", "tampered_provenance")
    if (
        provenance["derived_xy_collection_sha256"] != canonical_sha256(result.get("derived_xy"))
        or provenance["annotation_collection_sha256"] != canonical_sha256(result.get("annotations"))
        or observation["maplibre_bundle_sha256"] != maplibre_sha256
        or verification["execution_plan_sha256"] != plan["execution_plan_sha256"]
        or receipt["verification_sha256"] != verification["verification_sha256"]
        or any(
            record.get(key) is not False
            for key in (
                "production_activation_allowed",
                "official_portrayal_activation_allowed",
                "source_mutation_allowed",
                "source_z_drop_allowed",
            )
        )
    ):
        _fail("The controlled implementation provenance chain is inconsistent.", "tampered_provenance")
    return True

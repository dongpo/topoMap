from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
from typing import Any
from zipfile import ZipFile, ZipInfo

from nma.ogr import inspect_dataset


REAL_LAYER_PLAN_SCHEMA = "nma.real-layer-plan/0.4"
REAL_LAYER_OBSERVATION_SCHEMA = "nma.real-layer-observation/0.4"
REQUIRED_SHAPEFILE_PARTS = {".shp", ".shx", ".dbf", ".prj"}
OPTIONAL_SHAPEFILE_PARTS = {".cpg"}
SUPPORTED_PARTS = REQUIRED_SHAPEFILE_PARTS | OPTIONAL_SHAPEFILE_PARTS
PLAN_BASIS_KEYS = (
    "schema",
    "profile_id",
    "feature_code",
    "feature_name",
    "geometry_role",
    "product_layer",
    "source_archive_sha256",
    "source_layers",
    "source_filter",
    "field_mapping",
    "operations",
    "expected_feature_count",
    "evidence_node_ids",
    "citation_ids",
    "source_schema_boundary",
)


class RealLayerError(ValueError):
    """A real-data proposal or execution crossed a reviewed VS3 boundary."""


REAL_LAYER_PROFILES: dict[str, dict[str, Any]] = {
    "school-point": {
        "feature_code": "9920103",
        "feature_name": "小學",
        "geometry_role": "Point",
        "product_layer": "MARK",
        "source_layer_ids": [
            "J01_MARK",
            "J13_MARK",
            "J17_MARK",
            "K01_MARK",
            "K02_MARK",
            "K14_MARK",
        ],
        "id_field": "MARKID",
        "feature_code_field": "TERRAINID",
        "label_field": "MARKNAME1",
        "expected_feature_count": 15,
        "evidence_node_ids": [
            "code-value:landmark-type:9920103",
            "portrayal-rule:doc01:9920103",
            "product-layer:MARK",
        ],
        "source_schema_boundary": (
            "The uploaded MARK files use TERRAINID while Document 09 describes MARKTYPE1. "
            "This is a dataset-specific observed binding, not a global schema equivalence."
        ),
    },
    "river-line": {
        "feature_code": "9510101",
        "feature_name": "江、河、溪",
        "geometry_role": "LineString",
        "product_layer": "RIVERL",
        "source_layer_ids": ["J17_RIVERL"],
        "id_field": "RIVERID",
        "feature_code_field": "TERRAINID",
        "label_field": "RIVERLNAME",
        "expected_feature_count": 19,
        "evidence_node_ids": [
            "code-value:river-line-type:9510101",
            "portrayal-rule:doc01:9510101",
            "product-layer:RIVERL",
        ],
        "source_schema_boundary": (
            "The uploaded RIVERL file uses RIVERID and TERRAINID while Document 09 describes "
            "RIVERLID and RIVERLTYPE. This observed mapping remains dataset-specific."
        ),
    },
    "building-polygon": {
        "feature_code": "9310100",
        "feature_name": "永久性建物(建築區)",
        "geometry_role": "Polygon",
        "product_layer": "BUILD",
        "source_layer_ids": ["J17_BUILD"],
        "id_field": "BUILD_ID",
        "feature_code_field": "TERRAINID",
        "label_field": None,
        "expected_feature_count": 2769,
        "evidence_node_ids": [
            "classification:doc01:9310100",
            "portrayal-rule:doc01:9310100",
            "product-layer:BUILD",
        ],
        "source_schema_boundary": (
            "The uploaded BUILD file exposes BUILD_ID, TERRAINID, BUILD_STR, BUILD_NO and "
            "BUILD_H, which differs from Document 09's reduced BUILD field description. The "
            "runtime binding is a reviewed dataset observation, not a global replacement."
        ),
    },
}


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _member_sha256(archive: ZipFile, member: ZipInfo) -> str:
    digest = hashlib.sha256()
    with archive.open(member) as stream:
        for chunk in iter(lambda: stream.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_member_name(name: str) -> str:
    """Repair the archive's UTF-8 bytes that were stored without the ZIP UTF-8 flag."""

    try:
        return name.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def _safe_member(member: ZipInfo) -> bool:
    path = PurePosixPath(member.filename)
    return (
        not member.is_dir()
        and not path.is_absolute()
        and ".." not in path.parts
        and "__MACOSX" not in path.parts
    )


def _scope(display_path: PurePosixPath) -> str:
    return "primary" if len(display_path.parts) >= 2 and display_path.parts[-2] == "SHP" else "auxiliary"


def _archive_groups(archive: ZipFile) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for member in archive.infolist():
        if not _safe_member(member):
            continue
        raw_path = PurePosixPath(member.filename)
        extension = raw_path.suffix.lower()
        if extension not in SUPPORTED_PARTS:
            continue
        display_path = PurePosixPath(_display_member_name(member.filename))
        key = str(display_path.with_suffix(""))
        group = groups.setdefault(
            key,
            {
                "group_key": key,
                "layer_id": display_path.stem,
                "sheet_id": display_path.stem.split("_", 1)[0],
                "product_layer": display_path.stem.split("_", 1)[1]
                if "_" in display_path.stem
                else display_path.stem,
                "scope": _scope(display_path),
                "components": {},
            },
        )
        if extension in group["components"]:
            raise RealLayerError(f"Duplicate {extension} component in {key}.")
        group["components"][extension] = {"member": member, "display_path": str(display_path)}
    return groups


def inventory_shapefile_archive(
    archive_path: str | Path, *, expected_sha256: str | None = None
) -> dict[str, Any]:
    """Inventory every Shapefile family without changing or redistributing the archive."""

    source = Path(archive_path)
    if not source.is_file():
        raise RealLayerError(f"Shapefile archive does not exist: {source}")
    archive_sha256 = file_sha256(source)
    if expected_sha256 and archive_sha256 != expected_sha256:
        raise RealLayerError("The Shapefile archive checksum does not match the reviewed source.")
    layers: list[dict[str, Any]] = []
    with ZipFile(source) as archive:
        groups = _archive_groups(archive)
        for key in sorted(groups):
            group = groups[key]
            component_records = []
            for extension in sorted(group["components"]):
                component = group["components"][extension]
                member = component["member"]
                component_records.append(
                    {
                        "extension": extension,
                        "archive_member": component["display_path"],
                        "size_bytes": member.file_size,
                        "crc32": f"{member.CRC:08x}",
                        "sha256": _member_sha256(archive, member),
                        "required": extension in REQUIRED_SHAPEFILE_PARTS,
                    }
                )
            present = set(group["components"])
            layers.append(
                {
                    "group_key": group["group_key"],
                    "layer_id": group["layer_id"],
                    "sheet_id": group["sheet_id"],
                    "product_layer": group["product_layer"],
                    "scope": group["scope"],
                    "complete": REQUIRED_SHAPEFILE_PARTS.issubset(present),
                    "missing_required_parts": sorted(REQUIRED_SHAPEFILE_PARTS - present),
                    "components": component_records,
                }
            )
    return {
        "schema": "nma.real-shapefile-inventory/0.4",
        "source_archive": source.name,
        "source_archive_sha256": archive_sha256,
        "archive_size_bytes": source.stat().st_size,
        "read_only": True,
        "redistributed": False,
        "summary": {
            "shapefile_families": len(layers),
            "primary_families": sum(item["scope"] == "primary" for item in layers),
            "auxiliary_families": sum(item["scope"] == "auxiliary" for item in layers),
            "complete_families": sum(item["complete"] for item in layers),
            "incomplete_families": sum(not item["complete"] for item in layers),
        },
        "layers": layers,
    }


def _selected_groups(archive: ZipFile, layer_ids: list[str]) -> list[dict[str, Any]]:
    groups = _archive_groups(archive)
    selected = [
        group
        for group in groups.values()
        if group["scope"] == "primary" and group["layer_id"] in layer_ids
    ]
    found = {group["layer_id"] for group in selected}
    missing = sorted(set(layer_ids) - found)
    if missing:
        raise RealLayerError(f"The reviewed source layers are missing: {', '.join(missing)}.")
    if len(selected) != len(layer_ids):
        raise RealLayerError("A reviewed source layer is ambiguous in the archive.")
    for group in selected:
        present = set(group["components"])
        missing_parts = REQUIRED_SHAPEFILE_PARTS - present
        if missing_parts:
            raise RealLayerError(
                f"{group['layer_id']} is missing: {', '.join(sorted(missing_parts))}."
            )
    return sorted(selected, key=lambda group: group["layer_id"])


def extract_reviewed_source_layers(
    archive_path: Path, layer_ids: list[str], destination: Path
) -> tuple[list[Path], list[dict[str, Any]]]:
    source_paths: list[Path] = []
    component_records: list[dict[str, Any]] = []
    with ZipFile(archive_path) as archive:
        for group in _selected_groups(archive, layer_ids):
            for extension, component in sorted(group["components"].items()):
                member = component["member"]
                target = destination / f"{group['layer_id']}{extension}"
                with archive.open(member) as input_stream, target.open("wb") as output_stream:
                    shutil.copyfileobj(input_stream, output_stream)
                component_records.append(
                    {
                        "layer_id": group["layer_id"],
                        "extension": extension,
                        "archive_member": component["display_path"],
                        "sha256": file_sha256(target),
                    }
                )
            source_paths.append(destination / f"{group['layer_id']}.shp")
    return source_paths, component_records


def _geometry_family(geometry_type: str | None) -> str | None:
    if not geometry_type:
        return None
    value = geometry_type.removeprefix("Multi").removesuffix("Z").removesuffix("M")
    return value if value in {"Point", "LineString", "Polygon"} else None


def _profile(profile_id: str) -> dict[str, Any]:
    profile = REAL_LAYER_PROFILES.get(profile_id)
    if not profile:
        raise RealLayerError(f"Unknown reviewed real-layer profile: {profile_id}")
    return deepcopy(profile)


def _validate_evidence(profile: dict[str, Any], evidence_package: Any) -> dict[str, Any]:
    if not isinstance(evidence_package, dict) or evidence_package.get("status") != "retrieved":
        raise RealLayerError("A retrieved canonical GraphRAG evidence package is required.")
    available = {
        item.get("id")
        for item in evidence_package.get("evidence_nodes", [])
        if isinstance(item, dict)
    }
    missing = set(profile["evidence_node_ids"]) - available
    if missing:
        raise RealLayerError(
            "The evidence package is missing reviewed nodes: " + ", ".join(sorted(missing))
        )
    citations = [
        item
        for item in evidence_package.get("citations", [])
        if isinstance(item, dict) and item.get("citation_id")
    ]
    if not citations:
        raise RealLayerError("The real-layer proposal requires source citations.")
    return {"evidence_node_ids": profile["evidence_node_ids"], "citations": citations}


def propose_real_layer(
    *,
    profile_id: str,
    archive_path: str | Path,
    expected_archive_sha256: str,
    evidence_package: dict[str, Any],
) -> dict[str, Any]:
    """Inspect real sources and produce a non-executing, approval-bound layer plan."""

    profile = _profile(profile_id)
    evidence = _validate_evidence(profile, evidence_package)
    archive = Path(archive_path)
    archive_sha256 = file_sha256(archive)
    if archive_sha256 != expected_archive_sha256:
        raise RealLayerError("The real-layer source archive checksum changed.")
    with tempfile.TemporaryDirectory(prefix="nma-real-layer-inspect-") as temporary:
        sources, components = extract_reviewed_source_layers(
            archive, profile["source_layer_ids"], Path(temporary)
        )
        inspections = []
        for source in sources:
            inspection = inspect_dataset(source)
            if not inspection.get("available"):
                raise RealLayerError(f"GDAL could not inspect {source.stem}: {inspection.get('reason')}")
            if _geometry_family(inspection.get("geometry_type")) != profile["geometry_role"]:
                raise RealLayerError(f"{source.stem} has an incompatible geometry type.")
            fields = {field.get("name") for field in inspection.get("fields", [])}
            required_fields = {
                profile["id_field"],
                profile["feature_code_field"],
            }
            if profile["label_field"]:
                required_fields.add(profile["label_field"])
            if missing_fields := required_fields - fields:
                raise RealLayerError(
                    f"{source.stem} is missing reviewed fields: {', '.join(sorted(missing_fields))}."
                )
            inspections.append(inspection)
    plan_basis = {
        "schema": REAL_LAYER_PLAN_SCHEMA,
        "profile_id": profile_id,
        "feature_code": profile["feature_code"],
        "feature_name": profile["feature_name"],
        "geometry_role": profile["geometry_role"],
        "product_layer": profile["product_layer"],
        "source_archive_sha256": archive_sha256,
        "source_layers": profile["source_layer_ids"],
        "source_filter": {
            "field": profile["feature_code_field"],
            "operator": "equals",
            "value": profile["feature_code"],
        },
        "field_mapping": {
            "id": profile["id_field"],
            "feature_code": profile["feature_code_field"],
            "label": profile["label_field"],
        },
        "operations": ["extract-reviewed-components", "filter", "reproject-to-epsg-4326", "drop-z"],
        "expected_feature_count": profile["expected_feature_count"],
        "evidence_node_ids": evidence["evidence_node_ids"],
        "citation_ids": [item["citation_id"] for item in evidence["citations"]],
        "source_schema_boundary": profile["source_schema_boundary"],
    }
    plan_id = _plan_id(plan_basis)
    return {
        **plan_basis,
        "plan_id": plan_id,
        "status": "proposed",
        "source_inspections": inspections,
        "component_checksums": components,
        "approval": {"required": True, "decision": "pending", "plan_id": plan_id},
        "execution_performed": False,
        "automatic_action": False,
    }


def _plan_id(plan: dict[str, Any]) -> str:
    try:
        basis = {key: plan[key] for key in PLAN_BASIS_KEYS}
    except KeyError as error:
        raise RealLayerError(f"The real-layer plan is missing {error.args[0]}.") from error
    return "real-layer-plan:" + hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:20]


def _validate_output_features(collection: dict[str, Any], profile: dict[str, Any]) -> None:
    features = collection.get("features")
    if not isinstance(features, list):
        raise RealLayerError("GDAL did not return a GeoJSON FeatureCollection.")
    if len(features) != profile["expected_feature_count"]:
        raise RealLayerError(
            f"Expected {profile['expected_feature_count']} reviewed real features; found {len(features)}."
        )
    for feature in features:
        properties = feature.get("properties", {})
        if str(properties.get(profile["feature_code_field"])) != profile["feature_code"]:
            raise RealLayerError("A transformed feature escaped the reviewed source filter.")
        geometry = feature.get("geometry") or {}
        if _geometry_family(geometry.get("type")) != profile["geometry_role"]:
            raise RealLayerError("A transformed feature has an incompatible geometry type.")


def execute_real_layer(
    plan: dict[str, Any],
    *,
    approval: dict[str, Any],
    archive_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Execute only an explicitly approved, checksum-bound VS3 plan."""

    if not isinstance(plan, dict) or plan.get("schema") != REAL_LAYER_PLAN_SCHEMA:
        raise RealLayerError("A valid real-layer proposal is required.")
    if plan.get("status") != "proposed" or plan.get("execution_performed") is not False:
        raise RealLayerError("The real-layer plan is not executable.")
    if plan.get("plan_id") != _plan_id(plan):
        raise RealLayerError("The real-layer plan changed after inspection.")
    if not isinstance(approval, dict) or approval != {
        "decision": "approved",
        "plan_id": plan.get("plan_id"),
    }:
        raise RealLayerError("Explicit approval for this exact real-layer plan is required.")
    profile = _profile(plan.get("profile_id", ""))
    archive = Path(archive_path)
    if file_sha256(archive) != plan.get("source_archive_sha256"):
        raise RealLayerError("The approved source archive checksum changed before execution.")
    ogr2ogr = shutil.which("ogr2ogr")
    if not ogr2ogr:
        raise RealLayerError("GDAL/OGR is required for real-layer execution.")
    combined_features: list[dict[str, Any]] = []
    source_observations: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="nma-real-layer-execute-") as temporary:
        sources, components = extract_reviewed_source_layers(
            archive, profile["source_layer_ids"], Path(temporary)
        )
        for source in sources:
            command = [
                ogr2ogr,
                "-f",
                "GeoJSON",
                "/vsistdout/",
                str(source),
                "-where",
                f"{profile['feature_code_field']}='{profile['feature_code']}'",
                "-t_srs",
                "EPSG:4326",
                "-dim",
                "XY",
                "-lco",
                "RFC7946=YES",
            ]
            try:
                process = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                source_collection = json.loads(process.stdout)
            except subprocess.TimeoutExpired as error:
                raise RealLayerError(f"GDAL conversion timed out for {source.stem}.") from error
            except (subprocess.CalledProcessError, json.JSONDecodeError) as error:
                raise RealLayerError(f"GDAL conversion failed for {source.stem}.") from error
            features = source_collection.get("features", [])
            combined_features.extend(features)
            source_observations.append(
                {"layer_id": source.stem, "selected_feature_count": len(features)}
            )
    collection: dict[str, Any] = {
        "type": "FeatureCollection",
        "name": f"NMA_{profile['product_layer']}_{profile['feature_code']}",
        "features": combined_features,
    }
    _validate_output_features(collection, profile)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    target = output_root / f"{plan['profile_id']}.geojson"
    provenance = {
        "schema": "nma.real-layer-provenance/0.4",
        "plan_id": plan["plan_id"],
        "approval": "approved",
        "source_archive": archive.name,
        "source_archive_sha256": plan["source_archive_sha256"],
        "source_layers": source_observations,
        "component_checksums": components,
        "source_filter": plan["source_filter"],
        "field_mapping": plan["field_mapping"],
        "source_crs_resolution": (
            "the source .prj definition is used directly; no EPSG authority code is asserted"
        ),
        "output_crs": "EPSG:4326",
        "feature_count": len(combined_features),
        "synthetic": False,
        "random_coordinates": False,
        "redistributed": False,
    }
    collection["nma:provenance"] = provenance
    target.write_text(json.dumps(collection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "schema": REAL_LAYER_OBSERVATION_SCHEMA,
        "status": "executed-after-approval",
        "plan_id": plan["plan_id"],
        "output_path": str(target),
        "output_sha256": file_sha256(target),
        "feature_count": len(combined_features),
        "geometry_role": profile["geometry_role"],
        "provenance": provenance,
        "map_mutation_performed": False,
    }

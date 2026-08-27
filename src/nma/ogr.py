from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .io import load_json


def _unavailable(reason: str) -> dict[str, Any]:
    return {
        "available": False,
        "engine": "GDAL/OGR",
        "reason": reason,
    }


def inspect_dataset(path: str | Path, timeout_seconds: int = 15) -> dict[str, Any]:
    """Inspect a vector dataset with ogrinfo without making GDAL a Python dependency."""
    executable = shutil.which("ogrinfo")
    if executable is None:
        return _unavailable("ogrinfo executable not found")

    try:
        version_process = subprocess.run(
            [executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        process = subprocess.run(
            [executable, "-ro", "-so", "-json", str(path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        raw = json.loads(process.stdout)
    except subprocess.TimeoutExpired:
        return _unavailable(f"ogrinfo exceeded {timeout_seconds} seconds")
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        return _unavailable(f"ogrinfo failed: {exc}")

    layers = raw.get("layers", [])
    if not layers:
        return _unavailable("ogrinfo returned no layers")
    layer = layers[0]
    geometry_fields = layer.get("geometryFields", [])
    geometry = geometry_fields[0] if geometry_fields else {}
    coordinate_system = geometry.get("coordinateSystem", {})
    projjson = coordinate_system.get("projjson", {})
    crs_id = projjson.get("id", {})
    crs = None
    if crs_id.get("authority") and crs_id.get("code") is not None:
        crs = f"{crs_id['authority']}:{crs_id['code']}"

    return {
        "available": True,
        "engine": version_process.stdout.strip(),
        "driver": raw.get("driverShortName"),
        "layer": layer.get("name"),
        "feature_count": layer.get("featureCount"),
        "geometry_type": geometry.get("type"),
        "extent": geometry.get("extent"),
        "crs": crs,
        "crs_name": projjson.get("name"),
        "crs_wkt": coordinate_system.get("wkt"),
        "fields": [dict(field) for field in layer.get("fields", [])],
        "read_only": True,
    }


def read_vector_dataset(
    path: str | Path, timeout_seconds: int = 60
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read GeoJSON directly or another OGR vector format through read-only ``ogrinfo``.

    The returned feature collection carries the inspected layer schema and CRS as NMA metadata so
    a repaired intermediate GeoJSON can be validated without losing the source contract.
    """

    source = Path(path)
    if source.suffix.lower() in {".json", ".geojson"}:
        collection = load_json(source)
        inspection = inspect_dataset(source, timeout_seconds=min(timeout_seconds, 15))
        if inspection.get("available"):
            fields = inspection.get("fields", [])
            if fields and isinstance(fields[0], str):
                fields = [{"name": name} for name in fields]
            collection.setdefault("nma:fields", fields)
            collection.setdefault("nma:layer", inspection.get("layer"))
            collection.setdefault("nma:crs", inspection.get("crs") or inspection.get("crs_name"))
        return collection, inspection

    executable = shutil.which("ogrinfo")
    if executable is None:
        raise RuntimeError("GDAL/OGR is required to validate non-GeoJSON vector datasets")
    try:
        version_process = subprocess.run(
            [executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        process = subprocess.run(
            [executable, "-ro", "-al", "-json", "-features", str(source)],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        raw = json.loads(process.stdout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"ogrinfo exceeded {timeout_seconds} seconds") from exc
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"ogrinfo could not read {source}: {exc}") from exc

    layers = raw.get("layers", [])
    if len(layers) != 1:
        raise ValueError(f"Expected one vector layer in {source}; found {len(layers)}")
    layer = layers[0]
    geometry_fields = layer.get("geometryFields", [])
    geometry = geometry_fields[0] if geometry_fields else {}
    coordinate_system = geometry.get("coordinateSystem", {})
    projjson = coordinate_system.get("projjson", {})
    crs_id = projjson.get("id", {})
    crs = None
    if crs_id.get("authority") and crs_id.get("code") is not None:
        crs = f"{crs_id['authority']}:{crs_id['code']}"
    crs_name = projjson.get("name")
    fields = [dict(field) for field in layer.get("fields", [])]
    collection: dict[str, Any] = {
        "type": "FeatureCollection",
        "name": layer.get("name"),
        "nma:layer": layer.get("name"),
        "nma:crs": crs or crs_name,
        "nma:fields": fields,
        "features": layer.get("features", []),
    }
    inspection = {
        "available": True,
        "engine": version_process.stdout.strip(),
        "driver": raw.get("driverShortName"),
        "layer": layer.get("name"),
        "feature_count": layer.get("featureCount"),
        "geometry_type": geometry.get("type"),
        "extent": geometry.get("extent"),
        "crs": crs,
        "crs_name": crs_name,
        "crs_wkt": coordinate_system.get("wkt"),
        "fields": fields,
        "read_only": True,
    }
    return collection, inspection

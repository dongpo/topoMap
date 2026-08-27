#!/usr/bin/env python3
"""Rebuild the bounded school Shapefile and public inspection assets from GeoJSON."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SOURCE = ROOT / "data/fixtures-source/school-points/school-points.geojson"
TARGET = ROOT / "data/datasets/authoritative/school-points/SCHOOL_POINT.shp"
PUBLIC_INSPECTION = ROOT / "data/demo/school-points-public-inspection.json"
PUBLIC_GEOJSON = ROOT / "data/demo/school-points-public.geojson"
COMPONENTS = (".shp", ".shx", ".dbf", ".prj", ".cpg")


def _agent_server():
    path = ROOT / "scripts/run_nma_agent_server.py"
    spec = importlib.util.spec_from_file_location("nma_agent_server_fixture_sync", path)
    if not spec or not spec.loader:
        raise RuntimeError("Could not load the bounded agent server")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ogr2ogr = shutil.which("ogr2ogr")
    if not ogr2ogr:
        raise RuntimeError("GDAL/OGR is required to rebuild the school fixture")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    if len(source.get("features", [])) != 12:
        raise ValueError("The bounded school fixture must contain exactly 12 synthetic points")
    if any(
        feature.get("properties", {}).get("TERRAINID") != "9920103"
        for feature in source["features"]
    ):
        raise ValueError("Every school fixture feature must use TERRAINID 9920103")

    environment = {**os.environ, "OGR_CURRENT_DATE": "2026-08-07"}
    with tempfile.TemporaryDirectory(prefix="nma-school-fixture-") as temporary:
        generated = Path(temporary) / "SCHOOL_POINT.shp"
        subprocess.run(
            [
                ogr2ogr,
                "-f",
                "ESRI Shapefile",
                str(generated),
                str(SOURCE),
                "-nln",
                "SCHOOL_POINT",
                "-t_srs",
                "EPSG:3826",
                "-lco",
                "ENCODING=UTF-8",
                "-overwrite",
            ],
            check=True,
            cwd=ROOT,
            env=environment,
        )
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        for extension in COMPONENTS:
            source_component = generated.with_suffix(extension)
            if not source_component.is_file():
                raise RuntimeError(f"GDAL did not create {source_component.name}")
            shutil.copyfile(source_component, TARGET.with_suffix(extension))

    server = _agent_server()
    inspection = server.inspect_bundled_dataset("school-points")
    collection = server.export_bundled_geojson("school-points")
    if inspection["inspection"]["feature_count"] != 12 or len(collection["features"]) != 12:
        raise RuntimeError("Generated school fixture failed the 12-feature integrity check")
    _write_json(PUBLIC_INSPECTION, inspection)
    _write_json(PUBLIC_GEOJSON, collection)
    print(json.dumps({"features": 12, "source_crs": "EPSG:3826", "public_crs": "EPSG:4326"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

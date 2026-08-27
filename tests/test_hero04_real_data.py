import json
from pathlib import Path
import shutil

import pytest

from hero04_support import EXPECTED_ARCHIVE_SHA256, make_authorization, make_engine, private_archive
from nma.real_layer import file_sha256


pytestmark = pytest.mark.skipif(
    not private_archive().is_file() or not shutil.which("ogr2ogr"),
    reason="The private reviewed archive and GDAL are required.",
)


def test_real_mark_execution_is_checksum_bound_filtered_xy_and_deterministic(tmp_path: Path) -> None:
    archive_before = file_sha256(private_archive())
    first = make_engine(tmp_path / "first").execute(make_authorization(), "real-data-key-001")
    second = make_engine(tmp_path / "second").execute(make_authorization(), "real-data-key-001")
    collection = json.loads(
        (tmp_path / "first/executions" / first["execution_id"] / "data/school-point.geojson").read_text(
            encoding="utf-8"
        )
    )
    assert archive_before == EXPECTED_ARCHIVE_SHA256 == file_sha256(private_archive())
    assert collection["type"] == "FeatureCollection"
    assert len(collection["features"]) == 15
    assert all(feature["geometry"]["type"] == "Point" for feature in collection["features"])
    assert all(len(feature["geometry"]["coordinates"]) == 2 for feature in collection["features"])
    assert all(str(feature["properties"]["TERRAINID"]) == "9920103" for feature in collection["features"])
    assert collection["nma:provenance"]["output_crs"] == "EPSG:4326"
    assert collection["nma:provenance"]["synthetic"] is False
    assert first["output"]["geojson_hash"] == second["output"]["geojson_hash"]

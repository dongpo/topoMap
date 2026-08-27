import json
from pathlib import Path
import shutil

import pytest

from nma.graphrag import CanonicalGraphRetriever
from nma.real_layer import (
    RealLayerError,
    execute_real_layer,
    inventory_shapefile_archive,
    propose_real_layer,
)


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
GRAPH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"


pytestmark = pytest.mark.skipif(
    not ARCHIVE.is_file() or not shutil.which("ogrinfo") or not shutil.which("ogr2ogr"),
    reason="The user-provided private archive and GDAL are required for VS3 integration tests.",
)


def evidence(query: str) -> dict:
    return CanonicalGraphRetriever.load(GRAPH).evidence_package(
        query, max_depth=4, max_nodes=100
    )


def proposal(profile_id: str, query: str) -> dict:
    return propose_real_layer(
        profile_id=profile_id,
        archive_path=ARCHIVE,
        expected_archive_sha256=ARCHIVE_SHA256,
        evidence_package=evidence(query),
    )


def test_archive_inventory_is_complete_traceable_and_not_redistributed() -> None:
    result = inventory_shapefile_archive(ARCHIVE, expected_sha256=ARCHIVE_SHA256)

    assert result["schema"] == "nma.real-shapefile-inventory/0.4"
    assert result["read_only"] is True
    assert result["redistributed"] is False
    assert result["summary"] == {
        "shapefile_families": 128,
        "primary_families": 76,
        "auxiliary_families": 52,
        "complete_families": 128,
        "incomplete_families": 0,
    }
    mark = next(item for item in result["layers"] if item["layer_id"] == "J17_MARK" and item["scope"] == "primary")
    assert {part["extension"] for part in mark["components"]} == {
        ".cpg",
        ".dbf",
        ".prj",
        ".shp",
        ".shx",
    }
    assert all(len(part["sha256"]) == 64 for part in mark["components"])
    assert "新竹科學工業園區" in mark["group_key"]


@pytest.mark.parametrize(
    ("profile_id", "query", "geometry", "count", "source_layers"),
    [
        ("school-point", "小學 9920103 MARK 圖層", "Point", 15, 6),
        ("river-line", "江、河、溪 9510101 RIVERL 圖層", "LineString", 19, 1),
        ("building-polygon", "永久性建物 9310100 BUILD 圖層", "Polygon", 2769, 1),
    ],
)
def test_point_line_polygon_proposals_only_inspect_and_require_approval(
    profile_id: str, query: str, geometry: str, count: int, source_layers: int
) -> None:
    plan = proposal(profile_id, query)

    assert plan["schema"] == "nma.real-layer-plan/0.4"
    assert plan["geometry_role"] == geometry
    assert plan["expected_feature_count"] == count
    assert len(plan["source_inspections"]) == source_layers
    assert plan["approval"] == {
        "required": True,
        "decision": "pending",
        "plan_id": plan["plan_id"],
    }
    assert plan["execution_performed"] is False
    assert plan["automatic_action"] is False
    assert all(item["read_only"] for item in plan["source_inspections"])


@pytest.mark.parametrize(
    ("profile_id", "query", "geometry", "count"),
    [
        ("school-point", "小學 9920103 MARK 圖層", "Point", 15),
        ("river-line", "江、河、溪 9510101 RIVERL 圖層", "LineString", 19),
        ("building-polygon", "永久性建物 9310100 BUILD 圖層", "Polygon", 2769),
    ],
)
def test_approved_point_line_polygon_execution_uses_only_real_features(
    tmp_path: Path, profile_id: str, query: str, geometry: str, count: int
) -> None:
    plan = proposal(profile_id, query)
    result = execute_real_layer(
        plan,
        approval={"decision": "approved", "plan_id": plan["plan_id"]},
        archive_path=ARCHIVE,
        output_dir=tmp_path,
    )
    collection = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))

    assert result["status"] == "executed-after-approval"
    assert result["geometry_role"] == geometry
    assert result["feature_count"] == count
    assert result["map_mutation_performed"] is False
    assert len(collection["features"]) == count
    assert collection["nma:provenance"]["synthetic"] is False
    assert collection["nma:provenance"]["random_coordinates"] is False
    assert collection["nma:provenance"]["output_crs"] == "EPSG:4326"


def test_execution_rejects_missing_or_wrong_approval(tmp_path: Path) -> None:
    plan = proposal("school-point", "小學 9920103 MARK 圖層")

    with pytest.raises(RealLayerError, match="Explicit approval"):
        execute_real_layer(
            plan,
            approval={"decision": "approved", "plan_id": "another-plan"},
            archive_path=ARCHIVE,
            output_dir=tmp_path,
        )


def test_proposal_rejects_graph_package_without_product_layer_evidence() -> None:
    package = evidence("小學 9920103 MARK 圖層")
    package["evidence_nodes"] = [
        item for item in package["evidence_nodes"] if item["id"] != "product-layer:MARK"
    ]

    with pytest.raises(RealLayerError, match="product-layer:MARK"):
        propose_real_layer(
            profile_id="school-point",
            archive_path=ARCHIVE,
            expected_archive_sha256=ARCHIVE_SHA256,
            evidence_package=package,
        )

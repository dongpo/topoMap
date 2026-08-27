from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import shutil

from jsonschema import Draft202012Validator
import pytest

from build_contracts.building_production_implementation import (
    BUILD_SCHEMA,
    BuildingProductionError,
    EXPECTED_CONTRACT_SHA256,
    EXPECTED_POLICY_SHA256,
    EXPECTED_SOURCE_ARCHIVE_SHA256,
    LEGACY_DROP_Z_DISPOSITION,
    bind_annotation_content,
    bind_building_package,
    building_schema_identity,
    derive_xy_for_portrayal,
    deterministic_interior_point,
    implement_controlled_building,
    load_authoritative_package,
    load_frozen_contract,
    procedural_hatch_resource,
    validate_building_schema,
    verify_implementation_result,
)
from nma.core import canonical_sha256
from nma.real_layer import REAL_LAYER_PROFILES, file_sha256


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/building-controlled-production-implementation-v1.0.schema.json"
ARCHIVE_PATH = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
REAL_INTEGRATION_AVAILABLE = ARCHIVE_PATH.is_file() and shutil.which("ogrinfo") and shutil.which("ogr2ogr")

PACKAGE = {
    "J13": (
        "J13_寶山都市計畫/SHP",
        "J13_BUILD",
        "Baoshan urban-plan project area",
    ),
    "J17": (
        "J17_新竹科學工業園區特定區計畫(寶山部分)/SHP",
        "J17_BUILD",
        "Hsinchu Science Park special-plan project area, Baoshan portion",
    ),
}


def _fields() -> list[dict]:
    result = []
    for field in BUILD_SCHEMA:
        item = {
            "name": field["name"],
            "type": field["delivered_type"],
            "width": field["width"],
            "nullable": True,
            "uniqueConstraint": False,
        }
        if "precision" in field:
            item["precision"] = field["precision"]
        result.append(item)
    return result


def _components(seed: str = "0") -> dict[str, str]:
    return {extension: seed * 64 for extension in (".cpg", ".dbf", ".prj", ".shp", ".shx")}


def _binding(contract: dict, prefix: str = "J13") -> dict:
    package, layer, scope = PACKAGE[prefix]
    return bind_building_package(
        contract=contract,
        package_identities=[package],
        available_layer_ids=[layer],
        observed_fields=_fields(),
        source_archive_sha256=EXPECTED_SOURCE_ARCHIVE_SHA256,
        component_sha256=_components(),
        geographic_project_scope=scope,
    )


def _properties(
    build_id: str,
    *,
    floor: int | None = 3,
    structure: str | None = "R",
) -> dict:
    return {
        "BUILD_ID": build_id,
        "TERRAINID": "9310100",
        "BUILD_STR": structure,
        "BUILD_NO": floor,
        "BUILD_H": 12.5,
        "GROUP_ID": "G-opaque",
        "MDATE": "1120821",
    }


def _feature(build_id: str, coordinates: list, *, floor=3, structure="R") -> dict:
    return {
        "type": "Feature",
        "properties": _properties(build_id, floor=floor, structure=structure),
        "geometry": {"type": "Polygon", "coordinates": [coordinates]},
    }


def _collection() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            _feature("B001", [[0, 0, 8], [8, 0, 8], [8, 8, 9], [0, 8, 9], [0, 0, 8]]),
            _feature(
                "B002",
                [[10, 0, 3], [14, 0, 3], [14, 4, 4], [10, 4, 4], [10, 0, 3]],
                floor=None,
                structure="S",
            ),
            _feature(
                "B003",
                [[20, 0, 2], [24, 0, 2], [24, 4, 2], [20, 4, 2], [20, 0, 2]],
                floor=2,
                structure=None,
            ),
            _feature(
                "B004",
                [[30, 0, 1], [34, 0, 1], [34, 4, 1], [30, 4, 1], [30, 0, 1]],
                floor=None,
                structure=None,
            ),
        ],
    }


@pytest.fixture()
def frozen() -> dict:
    return load_frozen_contract(ROOT)


def _error_code(callable_) -> str:
    with pytest.raises(BuildingProductionError) as caught:
        callable_()
    return caught.value.code


def test_starting_contract_and_policy_are_consumed_by_exact_identity(frozen: dict) -> None:
    assert frozen["policy"]["policy_record_sha256"] == EXPECTED_POLICY_SHA256
    assert frozen["contract"]["finalized_contract_sha256"] == EXPECTED_CONTRACT_SHA256
    assert frozen["contract"]["production_activation_allowed"] is False
    assert frozen["contract"]["official_portrayal_activation_allowed"] is False

    changed = deepcopy(frozen)
    changed["contract"]["authorized_local_policies"]["hatch"]["local_angle_degrees"] = 30
    assert (
        _error_code(
            lambda: implement_controlled_building(
                contract_bundle=changed,
                binding=_binding(frozen["contract"]),
                authoritative_collection=_collection(),
                source_crs="EPSG:4326",
            )
        )
        == "invalid_contract_identity"
    )


def test_seven_field_schema_is_exact_and_opaque_fields_stay_opaque() -> None:
    result = validate_building_schema(_fields())
    assert result["field_count"] == 7
    assert result["schema_identity"] == building_schema_identity()
    assert result["opaque_fields"] == ["BUILD_H", "GROUP_ID", "MDATE"]
    changed = _fields()
    changed[-1]["name"] = "INVENTED"
    assert _error_code(lambda: validate_building_schema(changed)) == "schema_mismatch"


@pytest.mark.parametrize("prefix", ["J13", "J17"])
def test_package_identity_selects_only_its_exact_building_layer(frozen: dict, prefix: str) -> None:
    result = _binding(frozen["contract"], prefix)
    package, layer, scope = PACKAGE[prefix]
    assert result["source_package_identity"] == package
    assert result["selected_layer"] == layer
    assert result["geographic_project_scope"] == scope
    assert result["cross_prefix_fallback_used"] is False
    assert result["global_equivalence_asserted"] is False


@pytest.mark.parametrize(
    ("packages", "layers", "code"),
    [
        (["K14_unsupported/SHP"], ["K14_BUILD"], "unknown_package"),
        ([PACKAGE["J13"][0], PACKAGE["J17"][0]], ["J13_BUILD"], "ambiguous_package"),
        ([PACKAGE["J13"][0]], ["J17_BUILD"], "package_layer_mismatch"),
        ([PACKAGE["J17"][0]], ["J13_BUILD"], "package_layer_mismatch"),
        ([PACKAGE["J13"][0]], [], "missing_building_layer"),
        ([PACKAGE["J13"][0]], ["J13_BUILD", "J13_BUILD_COPY"], "unexpected_layer"),
    ],
)
def test_package_binding_failures_are_closed(
    frozen: dict, packages: list[str], layers: list[str], code: str
) -> None:
    assert (
        _error_code(
            lambda: bind_building_package(
                contract=frozen["contract"],
                package_identities=packages,
                available_layer_ids=layers,
                observed_fields=_fields(),
                source_archive_sha256=EXPECTED_SOURCE_ARCHIVE_SHA256,
                component_sha256=_components(),
                geographic_project_scope=PACKAGE["J13"][2],
            )
        )
        == code
    )


def test_annotation_content_matrix_has_no_fallback_or_reversal() -> None:
    both = bind_annotation_content(_properties("A", floor=12, structure="RC"))
    floor_absent = bind_annotation_content(_properties("B", floor=None, structure="RC"))
    structure_absent = bind_annotation_content(_properties("C", floor=12, structure=None))
    neither = bind_annotation_content(_properties("D", floor=None, structure=None))

    assert both["text"] == "12RC"
    assert both["field_binding_rule"] == "{BUILD_NO}{BUILD_STR}"
    assert floor_absent["status"] == "suppressed-incomplete-content"
    assert structure_absent["status"] == "suppressed-incomplete-content"
    assert neither["missing_fields"] == ["BUILD_NO", "BUILD_STR"]
    assert all(item["fallback_used"] is False for item in (both, floor_absent, structure_absent, neither))

    malformed = _properties("E")
    malformed["BUILD_NO"] = "three"
    assert _error_code(lambda: bind_annotation_content(malformed)) == "malformed_annotation_semantics"


def test_placement_is_deterministic_and_inside_a_concave_polygon() -> None:
    geometry = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [6, 0], [6, 2], [2, 2], [2, 6], [0, 6], [0, 0]]],
    }
    first = deterministic_interior_point(geometry)
    second = deterministic_interior_point(deepcopy(geometry))
    assert first == second
    assert 0 < first[0] < 6 and 0 < first[1] < 6
    assert not (first[0] > 2 and first[1] > 2)


def test_polygonz_derivation_is_non_mutating_xy_only_and_provenance_bound(frozen: dict) -> None:
    source = _collection()
    source_before = deepcopy(source)
    result = derive_xy_for_portrayal(
        source,
        binding=_binding(frozen["contract"]),
        source_crs="EPSG:4326",
        output_crs="EPSG:4326",
    )
    assert source == source_before
    assert result["provenance"]["source_collection_sha256"] == canonical_sha256(source_before)
    assert result["provenance"]["source_z_preserved_and_recoverable"] is True
    assert result["provenance"]["derived_xy_non_writing"] is True
    assert result["provenance"]["derived_xy_authoritative"] is False
    assert len(result["derived_xy"]["features"][0]["geometry"]["coordinates"][0][0]) == 2
    assert [item["properties"]["nma:annotation"] for item in result["annotations"]["features"]] == ["3R"]
    assert result["provenance"]["annotation_suppressed_count"] == 3


def test_source_without_z_or_with_malformed_annotation_fails_before_output(frozen: dict) -> None:
    no_z = _collection()
    no_z["features"][0]["geometry"]["coordinates"][0][0] = [0, 0]
    assert (
        _error_code(
            lambda: derive_xy_for_portrayal(
                no_z,
                binding=_binding(frozen["contract"]),
                source_crs="EPSG:4326",
                output_crs="EPSG:4326",
            )
        )
        == "source_z_missing"
    )
    malformed = _collection()
    malformed["features"][0]["properties"]["BUILD_STR"] = 7
    assert (
        _error_code(
            lambda: derive_xy_for_portrayal(
                malformed,
                binding=_binding(frozen["contract"]),
                source_crs="EPSG:4326",
                output_crs="EPSG:4326",
            )
        )
        == "malformed_annotation_semantics"
    )


def test_procedural_hatch_and_physical_output_profile_are_exact(frozen: dict) -> None:
    resource = procedural_hatch_resource(frozen["contract"])
    output = resource["output_profile"]
    assert resource["kind"] == "procedural-svg-image"
    assert resource["static_asset_dependency"] is None
    assert resource["official_spacing"] == {"value": 2.0, "unit": "mm"}
    assert resource["local_angle"] == {
        "value": 45,
        "unit": "degrees",
        "authority": "local-production-policy",
    }
    assert math.isclose(output["spacing_device_px_unquantized"], 2 * 96 / 25.4)
    assert output["line_width_device_px_unquantized"] == pytest.approx(0.7559055118110237)
    assert output["renderer_quantization"] is None
    assert resource["colour"]["official_source"] == {
        "representation": "RGB (0,0,0)",
        "components": [0, 0, 0],
    }
    assert resource["colour"]["device_serialization"] == "#000000"
    assert resource["opacity"] == {"value": 1.0, "authority": "local-output-profile-policy"}
    assert "#111111" not in resource["svg"]


def test_controlled_maplibre_result_is_deterministic_schema_valid_and_activation_held(
    frozen: dict,
) -> None:
    kwargs = {
        "contract_bundle": frozen,
        "binding": _binding(frozen["contract"]),
        "authoritative_collection": _collection(),
        "source_crs": "EPSG:4326",
    }
    first = implement_controlled_building(**kwargs)
    second = implement_controlled_building(**kwargs)
    assert first == second
    assert verify_implementation_result(first)
    Draft202012Validator.check_schema(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))).validate(
        first["record"]
    )

    bundle = first["maplibre"]
    assert bundle["status"] == "implementation-ready-activation-hold"
    assert bundle["production_active"] is False
    assert bundle["official_portrayal_active"] is False
    assert bundle["map_mutation_performed"] is False
    assert [layer["id"] for layer in bundle["layers"]] == [
        "nma-building-hatch",
        "nma-building-outline",
        "nma-building-annotation",
    ]
    outline = bundle["layers"][1]
    assert outline["paint"] == {
        "line-color": "#000000",
        "line-opacity": 1.0,
        "line-width": pytest.approx(0.7559055118110237),
    }
    annotation = bundle["layers"][2]
    assert annotation["layout"]["text-allow-overlap"] is False
    assert annotation["layout"]["text-ignore-placement"] is False
    assert annotation["layout"]["text-optional"] is True


def test_tampered_provenance_and_unsupported_output_profile_fail_closed(frozen: dict) -> None:
    result = implement_controlled_building(
        contract_bundle=frozen,
        binding=_binding(frozen["contract"]),
        authoritative_collection=_collection(),
        source_crs="EPSG:4326",
    )
    changed = deepcopy(result)
    changed["derived_xy"]["features"][0]["geometry"]["coordinates"][0][0][0] = 999
    assert _error_code(lambda: verify_implementation_result(changed)) == "tampered_provenance"
    changed = deepcopy(result)
    changed["maplibre"]["layers"][1]["paint"]["line-color"] = "#111111"
    assert _error_code(lambda: verify_implementation_result(changed)) == "tampered_provenance"
    bad_binding = _binding(frozen["contract"])
    bad_binding["selected_layer"] = "J17_BUILD"
    assert (
        _error_code(
            lambda: implement_controlled_building(
                contract_bundle=frozen,
                binding=bad_binding,
                authoritative_collection=_collection(),
                source_crs="EPSG:4326",
            )
        )
        == "package_layer_mismatch"
    )
    assert (
        _error_code(
            lambda: implement_controlled_building(
                contract_bundle=frozen,
                binding=_binding(frozen["contract"]),
                authoritative_collection=_collection(),
                source_crs="EPSG:4326",
                output_crs="EPSG:3857",
            )
        )
        == "unsupported_output_profile"
    )


def test_legacy_global_j17_drop_z_path_is_explicitly_non_authoritative() -> None:
    profile = REAL_LAYER_PROFILES["building-polygon"]
    assert profile["source_layer_ids"] == ["J17_BUILD"]
    assert LEGACY_DROP_Z_DISPOSITION == {
        "legacy_module": "nma.real_layer",
        "legacy_profile": "building-polygon",
        "classification": "incompatible-non-authoritative-vs3-path",
        "production_disposition": "bypassed-by-build10-controlled-building-path",
        "execute_real_layer_called": False,
        "dim_xy_requested": False,
        "source_write_target": None,
    }
    source = (
        ROOT / "build_contracts/building_production_implementation.py"
    ).read_text(encoding="utf-8")
    assert "execute_real_layer(" not in source
    assert '"-dim"' not in source
    assert '"drop-z"' not in source


def test_build10_reuses_frozen_core_identity_without_a_fallback_provider() -> None:
    source = (
        ROOT / "build_contracts/building_production_implementation.py"
    ).read_text(encoding="utf-8")
    assert "from nma.core import canonical_sha256, validate_sha256" in source
    assert "def canonical_sha256" not in source


@pytest.mark.skipif(not REAL_INTEGRATION_AVAILABLE, reason="Authorized private archive and GDAL required")
@pytest.mark.parametrize("prefix", ["J13", "J17"])
def test_controlled_real_package_integration_preserves_source_and_activation_hold(
    frozen: dict, prefix: str
) -> None:
    package, layer, scope = PACKAGE[prefix]
    before = file_sha256(ARCHIVE_PATH)
    loaded = load_authoritative_package(
        contract=frozen["contract"],
        archive_path=ARCHIVE_PATH,
        package_identity=package,
        geographic_project_scope=scope,
    )
    result = implement_controlled_building(
        contract_bundle=frozen,
        binding=loaded["binding"],
        authoritative_collection=loaded["authoritative_collection"],
        portrayal_polygonz_collection=loaded["portrayal_polygonz_collection"],
        source_crs=loaded["source_crs"],
        output_crs=loaded["output_crs"],
    )

    assert loaded["binding"]["selected_layer"] == layer
    assert loaded["external_derivation"] == {
        "engine": loaded["external_derivation"]["engine"],
        "operation": "reproject-preserve-z-to-separate-stdout-artifact",
        "dimensional_reduction_requested": False,
        "source_write_target": None,
        "derived_writeback_allowed": False,
    }
    assert result["record"]["provenance"]["reprojection_performed"] is True
    assert result["record"]["provenance"]["geometry_repair_performed"] is False
    assert result["record"]["receipt"]["production_active"] is False
    assert result["record"]["receipt"]["official_portrayal_active"] is False
    assert verify_implementation_result(result)
    assert file_sha256(ARCHIVE_PATH) == before == EXPECTED_SOURCE_ARCHIVE_SHA256

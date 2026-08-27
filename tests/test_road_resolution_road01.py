from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from nma.road_resolution import (
    DEFAULT_EVIDENCE_PATH,
    DEFAULT_FIXTURE_PATH,
    NORMALIZED_INTENT,
    PACKAGE_SCHEMA,
    RoadResolutionError,
    canonical_sha256,
    fixture_hash_basis,
    package_sha256,
    resolve_road_request,
)


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_REQUEST = (
    "Resolve County Highway 126 / 中山街 in the reviewed K14 road dataset and prepare "
    "the evidence-grounded road portrayal package for the exact contiguous source segment set."
)


@pytest.fixture()
def fixture() -> dict:
    return json.loads(DEFAULT_FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def evidence() -> dict:
    return json.loads(DEFAULT_EVIDENCE_PATH.read_text(encoding="utf-8"))


def _error_code(callable_, code: str) -> None:
    with pytest.raises(RoadResolutionError) as caught:
        callable_()
    assert caught.value.code == code


def test_golden_deterministic_resolution_and_schema_contract(fixture: dict) -> None:
    package = resolve_road_request(GOLDEN_REQUEST)

    assert package["package_version"] == "road-01/1.0"
    assert package["schema_version"] == PACKAGE_SCHEMA
    assert package["request"]["normalized_intent"] == NORMALIZED_INTENT
    assert package["source"] == {
        "profile": "K14",
        "layer": "K14_ROAD",
        "archive_sha256": "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
    }
    assert package["fixture"]["sha256"] == fixture["fixture_sha256"]
    assert package["package_sha256"] == package_sha256(package)

    schema = json.loads(
        (ROOT / "schemas/road-resolution-evidence-package-v1.0.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False


def test_exact_logical_identity_and_ordered_segment_set() -> None:
    package = resolve_road_request(GOLDEN_REQUEST)

    assert package["road_identity"] == {
        "class_code": "9420400",
        "class_name": "County Highway",
        "route_number": "縣126",
        "road_name": "中山街",
        "canonical_identity": "ROADNUM=縣126|ROADNUM1=|ROADNUM2=|ROADNAME=中山街",
        "identity_basis": ["ROADNUM", "ROADNUM1", "ROADNUM2", "ROADNAME"],
    }
    assert package["segment_set"] == {
        "ordered_feature_ids": ["K0000004671", "K0000004913", "K0000005348"],
        "count": 3,
        "geometry_type": "LineString",
        "crs": "TWD97[2020]_TM121",
    }


def test_topology_verification() -> None:
    assert resolve_road_request(GOLDEN_REQUEST)["continuity"] == {
        "connected_components": 1,
        "adjacency": [
            ["K0000004671", "K0000004913"],
            ["K0000004913", "K0000005348"],
        ],
        "branch_count": 0,
        "gap_count": 0,
        "duplicate_segment_count": 0,
        "positive_length_overlap_count": 0,
        "self_intersection_count": 0,
        "repair_required": False,
    }


def test_reviewed_evidence_and_portrayal_binding() -> None:
    package = resolve_road_request(GOLDEN_REQUEST)

    assert package["evidence"] == {
        "record_set": "nma-road-compound-portrayal-reviewed-v0.4",
        "evidence_ids": [
            "BMAP096-P5-TABLE1-GRAPHIC-ELEMENT-CODES",
            "DOC01-P22-P24-ROAD-BOUNDARY-LABEL",
            "DOC01-P34-P35-ROUTE-SHIELDS",
            "DOC02-P45-P46-ANNEX7-CODING-SCHEME",
            "DOC02-P53-P55-ROAD-CODE-BRANCH",
        ],
    }
    assert package["portrayal"] == {
        "road_class": "9420400",
        "road_name": "中山街",
        "route_number": "縣126",
        "shield_code": "9490005",
        "shield_orientation": "road-parallel",
        "graphic_element_roles": [2, 5],
    }


def test_source_archive_hash_mismatch_fails_closed() -> None:
    _error_code(
        lambda: resolve_road_request(GOLDEN_REQUEST, observed_archive_sha256="0" * 64),
        "archive_hash_mismatch",
    )


def test_fixture_hash_mismatch_fails_closed() -> None:
    _error_code(
        lambda: resolve_road_request(GOLDEN_REQUEST, observed_fixture_sha256="0" * 64),
        "fixture_hash_mismatch",
    )


@pytest.mark.parametrize("change", ["missing", "changed", "extra"])
def test_missing_changed_or_extra_segment_fails_closed(fixture: dict, change: str) -> None:
    records = deepcopy(fixture["source_records"])
    if change == "missing":
        records.pop()
    elif change == "changed":
        records[-1]["feature_id"] = "K0000009999"
    else:
        extra = deepcopy(records[-1])
        extra["feature_id"] = "K0000009999"
        extra["endpoint_nodes"] = ["endpoint-4", "endpoint-3"]
        records.append(extra)

    _error_code(
        lambda: resolve_road_request(GOLDEN_REQUEST, source_records=records),
        "segment_set_mismatch",
    )


def test_wrong_class_fails_closed(fixture: dict) -> None:
    records = deepcopy(fixture["source_records"])
    records[0]["class_code"] = "9420300"
    _error_code(
        lambda: resolve_road_request(GOLDEN_REQUEST, source_records=records), "class_mismatch"
    )


@pytest.mark.parametrize(
    ("field", "value"), [("roadnum", "縣127"), ("roadname", "中山路")]
)
def test_wrong_route_or_name_identity_fails_closed(fixture: dict, field: str, value: str) -> None:
    records = deepcopy(fixture["source_records"])
    records[1][field] = value
    _error_code(
        lambda: resolve_road_request(GOLDEN_REQUEST, source_records=records),
        "logical_identity_mismatch",
    )


def test_missing_required_evidence_fails_closed(evidence: dict) -> None:
    changed = deepcopy(evidence)
    changed["sources"][0]["evidence"].pop()
    _error_code(
        lambda: resolve_road_request(GOLDEN_REQUEST, evidence_record_set=changed),
        "missing_evidence",
    )


def test_changed_portrayal_evidence_fails_closed(evidence: dict) -> None:
    changed = deepcopy(evidence)
    recipe = next(
        item for item in changed["compound_road_recipes"] if item["road_code"] == "9420400"
    )
    recipe["shield_code"] = "9490004"
    _error_code(
        lambda: resolve_road_request(GOLDEN_REQUEST, evidence_record_set=changed),
        "evidence_mismatch",
    )


@pytest.mark.parametrize("change", ["gap", "branch", "duplicate", "overlap", "self-intersection"])
def test_topology_change_fails_closed(fixture: dict, change: str) -> None:
    records = deepcopy(fixture["source_records"])
    if change == "gap":
        records[-1]["endpoint_nodes"] = ["gap-a", "gap-b"]
    elif change == "branch":
        records[-1]["endpoint_nodes"] = ["endpoint-1", "endpoint-3"]
    elif change == "duplicate":
        records[-1]["endpoint_nodes"] = deepcopy(records[0]["endpoint_nodes"])
    elif change == "overlap":
        records[0]["positive_length_overlaps"] = [records[1]["feature_id"]]
    else:
        records[1]["is_simple"] = False
    _error_code(
        lambda: resolve_road_request(GOLDEN_REQUEST, source_records=records),
        "topology_mismatch",
    )


def test_inputs_are_not_mutated_and_execution_is_forbidden(fixture: dict, evidence: dict) -> None:
    records = deepcopy(fixture["source_records"])
    before_records = deepcopy(records)
    before_evidence = deepcopy(evidence)

    package = resolve_road_request(
        GOLDEN_REQUEST, source_records=records, evidence_record_set=evidence
    )

    assert records == before_records
    assert evidence == before_evidence
    assert package["permissions"] == {
        "source_mutation_allowed": False,
        "execution_allowed": False,
        "topology_repair_allowed": False,
        "roada_execution_allowed": False,
        "road_edge_derivation_allowed": False,
    }


def test_deterministic_hash_and_equivalent_normalized_requests() -> None:
    variants = [
        GOLDEN_REQUEST,
        "K14 reviewed ROAD: prepare evidence for 中山街 / 縣道 126.",
        "  Prepare K14 evidence package for 中山街 (縣126).  ",
        "Resolve K14 county   highway #126, 中山街.",
    ]
    packages = [resolve_road_request(request) for request in variants]

    assert len({package["package_sha256"] for package in packages}) == 1
    assert len({package["request"]["raw"] for package in packages}) == len(variants)
    assert all(package["package_sha256"] == package_sha256(package) for package in packages)


def test_frozen_fixture_hash_is_recomputed_from_road00_basis(fixture: dict) -> None:
    assert canonical_sha256(fixture_hash_basis(fixture)) == fixture["fixture_sha256"]


def test_ambiguous_or_unbound_request_fails_closed() -> None:
    for request in [
        "Resolve County Highway 126 / 中山街 in K02.",
        "Resolve County Highway 126 / 中山街 in K14 or K02.",
        "Resolve County Highway 126 and County Highway 127 / 中山街 in K14.",
        "Resolve County Highway 126 in K14.",
    ]:
        _error_code(lambda request=request: resolve_road_request(request), "unsupported_request")

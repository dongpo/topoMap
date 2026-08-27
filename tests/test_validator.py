from __future__ import annotations

import json
from pathlib import Path

from nma.io import load_json
from nma.ogr import read_vector_dataset
from nma.repair import apply_safe_repairs
from nma.specification import Specification
from nma.validator import Validator

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_SPEC = ROOT / "data/specifications/tnm-demo-2023.json"
AUTHORITATIVE_SPEC = ROOT / "data/specifications/taiwan-5000-riverl-112.json"


def test_clean_fixture_passes() -> None:
    report = Validator(Specification.load(SYNTHETIC_SPEC)).validate_path(
        ROOT / "data/datasets/river-clean.geojson"
    )
    assert report["status"] == "passed"
    assert report["issues"] == []


def test_defective_fixture_matches_frozen_ground_truth() -> None:
    report = Validator(Specification.load(SYNTHETIC_SPEC)).validate_path(
        ROOT / "data/datasets/river-defective.geojson"
    )
    actual = sorted(issue["issue_key"] for issue in report["issues"])
    assert actual == [
        "NMA-DOMAIN-001|index:1|river_class",
        "NMA-FORMAT-001|R001@index:0|name",
        "NMA-GEOM-001|index:1|-",
        "NMA-SCHEMA-001|index:1|feature_id",
        "NMA-SCHEMA-002|R001@index:2|name",
        "NMA-TOPO-001|R001@index:2|-",
        "NMA-UNIQUE-001|R001@index:0|feature_id",
        "NMA-UNIQUE-001|R001@index:2|feature_id",
    ]
    assert report["summary"] == {
        "features": 3,
        "rules_evaluated": 8,
        "issues": 8,
        "errors": 7,
        "warnings": 1,
        "safe_repairs_available": 1,
    }
    inspection = report["dataset_inspection"]
    assert isinstance(inspection["available"], bool)
    if inspection["available"]:
        assert inspection["driver"] == "GeoJSON"
        assert inspection["feature_count"] == 3
        assert inspection["crs"] == "EPSG:4326"
        assert {field["name"] for field in inspection["fields"]} == {
            "feature_id",
            "name",
            "river_class",
        }


def test_only_explicitly_safe_repairs_are_applied() -> None:
    specification = Specification.load(SYNTHETIC_SPEC)
    validator = Validator(specification)
    collection = load_json(ROOT / "data/datasets/river-defective.geojson")
    before = validator.validate(collection)
    repaired, applied = apply_safe_repairs(collection, before)
    after = validator.validate(repaired)
    assert len(applied) == 1
    assert before["summary"]["warnings"] == 1
    assert after["summary"]["warnings"] == 0
    assert after["summary"]["errors"] == before["summary"]["errors"]


def test_authoritative_shapefile_fixtures_match_frozen_ground_truth() -> None:
    ground_truth = json.loads((ROOT / "benchmark/ground-truth.json").read_text(encoding="utf-8"))
    validator = Validator(Specification.load(AUTHORITATIVE_SPEC))
    for relative_path, expected in ground_truth["datasets"].items():
        report = validator.validate_path(ROOT / relative_path)
        actual = sorted(issue["issue_key"] for issue in report["issues"])
        assert actual == expected
        assert report["dataset_inspection"]["driver"] == "ESRI Shapefile"


def test_authoritative_evidence_has_machine_readable_page_provenance() -> None:
    specification = Specification.load(AUTHORITATIVE_SPEC)
    evidence_by_rule = {rule.rule_id: rule.evidence.as_dict() for rule in specification.rules}
    assert evidence_by_rule["TW-RIVERL-NAME-001"]["page"] == 35
    assert evidence_by_rule["TW-RIVERL-GEOM-001"]["page"] == 35
    assert evidence_by_rule["TW-RIVERL-CRS-001"]["page"] == 34
    assert all(evidence["page"] is not None for evidence in evidence_by_rule.values())
    assert all(
        f"#page={evidence['page']}" in evidence["uri"] for evidence in evidence_by_rule.values()
    )


def test_authoritative_demo_applies_only_the_approved_safe_normalization() -> None:
    specification = Specification.load(AUTHORITATIVE_SPEC)
    validator = Validator(specification)
    collection, _ = read_vector_dataset(
        ROOT / "data/datasets/authoritative/riverl-defective/RIVERL.shp"
    )
    before = validator.validate(collection)
    repaired, applied = apply_safe_repairs(collection, before)
    after = validator.validate(repaired)
    assert len(applied) == 1
    assert applied[0]["operation"] == "trim"
    assert before["summary"]["warnings"] == 1
    assert after["summary"]["warnings"] == 0
    assert after["summary"]["errors"] == before["summary"]["errors"]

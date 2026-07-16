import json
from pathlib import Path

from nma.io import load_json
from nma.report import render_html
from nma.specification import Specification
from nma.validator import Validator

ROOT = Path(__file__).resolve().parents[1]


def test_executable_profile_satisfies_published_required_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas/executable-profile.schema.json").read_text(encoding="utf-8")
    )
    profile = load_json(ROOT / "data/specifications/taiwan-5000-riverl-112.json")
    assert set(schema["required"]) <= set(profile)
    layer_required = set(schema["properties"]["layer"]["required"])
    assert layer_required <= set(profile["layer"])
    rule_schema = schema["properties"]["rules"]["items"]
    assert all(set(rule_schema["required"]) <= set(rule) for rule in profile["rules"])
    evidence_required = set(rule_schema["properties"]["evidence"]["required"])
    assert all(evidence_required <= set(rule["evidence"]) for rule in profile["rules"])


def test_validation_report_satisfies_published_required_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas/validation-report.schema.json").read_text(encoding="utf-8")
    )
    report = Validator(
        Specification.load(ROOT / "data/specifications/tnm-demo-2023.json")
    ).validate_path(ROOT / "data/datasets/river-defective.geojson")

    assert set(schema["required"]) <= set(report)
    issue_required = set(schema["properties"]["issues"]["items"]["required"])
    assert report["issues"]
    assert all(issue_required <= set(issue) for issue in report["issues"])
    evidence_required = set(
        schema["properties"]["issues"]["items"]["properties"]["evidence"]["required"]
    )
    assert all(evidence_required <= set(issue["evidence"]) for issue in report["issues"])


def test_html_report_contains_map_findings_and_escapes_labels(tmp_path: Path) -> None:
    specification = Specification.load(ROOT / "data/specifications/tnm-demo-2023.json")
    collection = load_json(ROOT / "data/datasets/river-defective.geojson")
    report = Validator(specification).validate(collection, dataset="<unsafe-demo>")
    target = render_html(report, collection, tmp_path / "report.html")
    html = target.read_text(encoding="utf-8")

    assert "Spatial findings" in html
    assert "Issues and evidence" in html
    assert "&lt;unsafe-demo&gt;" in html
    assert "<unsafe-demo>" not in html
    assert html.count("<tr>") == len(report["issues"]) + 1

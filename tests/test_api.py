from pathlib import Path

from nma.api import get_payload, post_payload
from nma.io import load_json
from nma.specification import Specification

ROOT = Path(__file__).resolve().parents[1]
SPECIFICATION = Specification.load(ROOT / "data/specifications/tnm-demo-2023.json")


def test_api_read_contracts() -> None:
    status, health = get_payload(SPECIFICATION, "/health")
    assert status == 200
    assert health == {"status": "ok", "version": "0.2.0"}

    status, rules = get_payload(SPECIFICATION, "/v1/rules")
    assert status == 200
    assert len(rules) == 8
    assert all(rule["evidence"]["uri"].startswith("spec://") for rule in rules)

    status, missing = get_payload(SPECIFICATION, "/not-found")
    assert status == 404
    assert missing["error"] == "not_found"


def test_api_validation_is_deterministic_and_read_only() -> None:
    clean = load_json(ROOT / "data/datasets/river-clean.geojson")
    status, report = post_payload(SPECIFICATION, "/v1/validate", clean)
    assert status == 200
    assert report["status"] == "passed"
    assert report["provenance"]["deterministic"] is True

    status, error = post_payload(SPECIFICATION, "/v1/validate", {"type": "Feature"})
    assert status == 400
    assert error["error"] == "invalid_request"

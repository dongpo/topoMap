from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from nma.agents.school_agent.discovery import discover_school_features
from nma.agents.school_agent.evidence import EvidenceItem, evaluate_evidence
from nma.agents.school_agent.proposal import analyze_administrative_area
from nma.agents.school_agent.reasoning import evaluate_spatial_match


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "data" / "samples" / "school-agent"
SERVER_PATH = ROOT / "scripts" / "run_nma_agent_server.py"


def _inventory():
    return discover_school_features(
        "North District",
        nma_dataset=SAMPLE_ROOT / "nma-schools.geojson",
        osm_dataset=SAMPLE_ROOT / "osm-school-pois.geojson",
        official_registry=SAMPLE_ROOT / "official-school-registry.json",
    )


def _load_server():
    spec = importlib.util.spec_from_file_location("nma_school_agent_api_test", SERVER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_feature_discovery_connects_all_three_school_sources() -> None:
    inventory = _inventory()

    assert inventory.administrative_area == "North District"
    assert inventory.feature_count == 8
    assert [feature.feature_id for feature in inventory.nma] == ["school001", "school002"]
    assert {feature.feature_id for feature in inventory.osm} == {
        "osm1001",
        "osm1002",
        "osm1003",
    }
    assert {feature.registry_id for feature in inventory.official_registry} == {
        "REG-001",
        "REG-002",
        "REG-003",
    }


def test_spatial_matching_combines_geometry_admin_semantics_and_attributes() -> None:
    inventory = _inventory()
    official = next(item for item in inventory.official_registry if item.registry_id == "REG-003")
    osm = next(item for item in inventory.osm if item.registry_id == "REG-003")

    assessment = evaluate_spatial_match(official, osm)

    assert assessment.matched is True
    assert assessment.distance_m < 10
    assert assessment.administrative_score == 1.0
    assert assessment.semantic_score == 1.0
    assert assessment.attribute_score == 1.0
    assert assessment.overall_score > 0.98


def test_evidence_completeness_requires_two_distinct_sources() -> None:
    official = EvidenceItem(
        source="OFFICIAL_REGISTRY",
        type="registry",
        feature_id="registry003",
        detail="Reviewed registry record",
        score=0.95,
    )
    osm = EvidenceItem(
        source="OSM",
        type="spatial",
        feature_id="osm1003",
        detail="Nearby school POI",
        score=0.9,
    )

    assert evaluate_evidence((official,)).complete is False
    complete = evaluate_evidence((official, osm))
    assert complete.complete is True
    assert complete.distinct_sources == ("OFFICIAL_REGISTRY", "OSM")
    assert complete.confidence > 0.9


def test_proposal_generation_is_jsonld_compatible_and_matches_example() -> None:
    observed_at = datetime(2026, 8, 14, tzinfo=timezone.utc)
    result = analyze_administrative_area("North District", observed_at=observed_at)
    example = json.loads((SAMPLE_ROOT / "example-output.json").read_text(encoding="utf-8"))

    assert result == example
    assert result["runtime_contract"] == "nma.runtime-baseline/0.32"
    assert result["proposal_count"] == 2
    assert {proposal["proposal"] for proposal in result["proposals"]} == {
        "ADD_FEATURE",
        "UPDATE_ATTRIBUTES",
    }
    for proposal in result["proposals"]:
        assert proposal["@id"].startswith("proposal:")
        assert proposal["feature_id"]
        assert 0.0 <= proposal["confidence"] <= 1.0
        assert len({item["source"] for item in proposal["evidence"]}) >= 2
        assert proposal["reasoning"]
        assert proposal["timestamp"] == "2026-08-14T00:00:00Z"
        assert proposal["human_validation_required"] is True
        assert proposal["automatic_execution"] is False


def test_school_agent_api_contract_is_bounded_to_administrative_area() -> None:
    server = _load_server()

    result = server.analyze_school_agent_request({"administrative_area": "North District"})
    assert result["schema"] == "nma.school-feature-intelligence/0.5"
    assert result["runtime_contract"] == server.RUNTIME_CONTRACT
    assert result["proposal_count"] == 2
    assert result["human_validation_required"] is True
    assert result["automatic_execution"] is False

    with pytest.raises(server.AgentError, match="Expected administrative_area only"):
        server.analyze_school_agent_request(
            {"administrative_area": "North District", "execute": True}
        )

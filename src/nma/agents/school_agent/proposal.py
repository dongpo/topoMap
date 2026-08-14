from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nma.agents.school_agent.discovery import discover_school_features
from nma.agents.school_agent.evidence import evidence_for_finding
from nma.agents.school_agent.reasoning import CandidateFinding, discover_candidate_findings


SCHOOL_AGENT_SCHEMA = "nma.school-feature-intelligence/0.5"
RUNTIME_CONTRACT = "nma.runtime-baseline/0.32"
ROOT = Path(__file__).resolve().parents[4]
SAMPLE_ROOT = ROOT / "data" / "samples" / "school-agent"

JSONLD_CONTEXT = {
    "nma": "https://example.org/nma/",
    "feature_id": "nma:featureIdentifier",
    "proposal": "nma:proposalType",
    "confidence": "nma:confidenceScore",
    "evidence": "nma:evidence",
    "reasoning": "nma:reasoningExplanation",
    "timestamp": "http://purl.org/dc/terms/created",
}


def _timestamp(value: datetime | None) -> str:
    observed = value or datetime.now(timezone.utc)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    return observed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def generate_update_proposal(
    finding: CandidateFinding, *, observed_at: datetime | None = None
) -> dict[str, Any]:
    evaluation = evidence_for_finding(finding)
    proposal_id = f"proposal:{finding.proposal_type.casefold()}:{finding.feature_id}"
    return {
        "@type": "nma:SchoolFeatureUpdateProposal",
        "@id": proposal_id,
        "feature_id": finding.feature_id,
        "proposal": finding.proposal_type,
        "confidence": evaluation.confidence,
        "evidence": [item.to_payload() for item in evaluation.items],
        "reasoning": finding.reasoning,
        "timestamp": _timestamp(observed_at),
        "human_validation_required": True,
        "automatic_execution": False,
    }


def analyze_administrative_area(
    administrative_area: str,
    *,
    nma_dataset: str | Path | None = None,
    osm_dataset: str | Path | None = None,
    official_registry: str | Path | None = None,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    inventory = discover_school_features(
        administrative_area,
        nma_dataset=nma_dataset or SAMPLE_ROOT / "nma-schools.geojson",
        osm_dataset=osm_dataset or SAMPLE_ROOT / "osm-school-pois.geojson",
        official_registry=official_registry or SAMPLE_ROOT / "official-school-registry.json",
    )
    findings = discover_candidate_findings(inventory)
    analysis_time = observed_at or datetime.now(timezone.utc)
    proposals = [
        generate_update_proposal(finding, observed_at=analysis_time) for finding in findings
    ]
    return {
        "@context": JSONLD_CONTEXT,
        "@type": "nma:SchoolFeatureAnalysis",
        "schema": SCHOOL_AGENT_SCHEMA,
        "runtime_contract": RUNTIME_CONTRACT,
        "administrative_area": inventory.administrative_area,
        "source_counts": {
            "NMA": len(inventory.nma),
            "OSM": len(inventory.osm),
            "OFFICIAL_REGISTRY": len(inventory.official_registry),
        },
        "proposal_count": len(proposals),
        "proposals": proposals,
        "human_validation_required": True,
        "automatic_execution": False,
    }

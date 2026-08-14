from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nma.agents.school_agent.discovery import SchoolAgentError, SchoolFeature
from nma.agents.school_agent.reasoning import CandidateFinding


@dataclass(frozen=True)
class EvidenceItem:
    source: str
    type: str
    feature_id: str
    detail: str
    score: float

    def to_payload(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "type": self.type,
            "feature_id": self.feature_id,
            "detail": self.detail,
            "score": self.score,
        }


@dataclass(frozen=True)
class EvidenceEvaluation:
    items: tuple[EvidenceItem, ...]
    complete: bool
    confidence: float
    distinct_sources: tuple[str, ...]


def _source_evidence(feature: SchoolFeature, evidence_type: str, score: float) -> EvidenceItem:
    return EvidenceItem(
        source=feature.source,
        type=evidence_type,
        feature_id=feature.feature_id,
        detail=(
            f"{feature.name} in {feature.administrative_area} at "
            f"({feature.longitude:.6f}, {feature.latitude:.6f})"
        ),
        score=round(score, 4),
    )


def evaluate_evidence(items: tuple[EvidenceItem, ...]) -> EvidenceEvaluation:
    valid = all(
        item.source and item.type and item.feature_id and item.detail and 0.0 <= item.score <= 1.0
        for item in items
    )
    sources = tuple(sorted({item.source for item in items}))
    complete = valid and len(items) >= 2 and len(sources) >= 2
    confidence = 0.0
    if items:
        confidence = min(0.99, (sum(item.score for item in items) / len(items)) * 0.85 + 0.14)
    return EvidenceEvaluation(
        items=items,
        complete=complete,
        confidence=round(confidence, 4),
        distinct_sources=sources,
    )


def evidence_for_finding(finding: CandidateFinding) -> EvidenceEvaluation:
    scores = [match.overall_score for match in finding.supporting_matches]
    match_score = sum(scores) / len(scores) if scores else 0.0
    items: list[EvidenceItem] = [
        _source_evidence(finding.official, "registry", max(0.8, match_score))
    ]
    if finding.osm is not None:
        items.append(_source_evidence(finding.osm, "spatial", match_score))
    if finding.nma is not None:
        items.append(_source_evidence(finding.nma, "baseline", match_score))
    evaluation = evaluate_evidence(tuple(items))
    if not evaluation.complete:
        raise SchoolAgentError("A school proposal requires complete evidence from two sources.")
    return evaluation

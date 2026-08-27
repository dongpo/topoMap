from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
import re
from typing import Literal

from nma.agents.school_agent.discovery import SchoolFeature, SchoolInventory


ProposalType = Literal["ADD_FEATURE", "UPDATE_GEOMETRY", "UPDATE_ATTRIBUTES"]


@dataclass(frozen=True)
class MatchAssessment:
    left: SchoolFeature
    right: SchoolFeature
    distance_m: float
    proximity_score: float
    administrative_score: float
    semantic_score: float
    attribute_score: float
    overall_score: float
    matched: bool


@dataclass(frozen=True)
class CandidateFinding:
    feature_id: str
    proposal_type: ProposalType
    nma: SchoolFeature | None
    osm: SchoolFeature | None
    official: SchoolFeature
    supporting_matches: tuple[MatchAssessment, ...]
    reasoning: str


def geometry_distance_m(left: SchoolFeature, right: SchoolFeature) -> float:
    radius_m = 6_371_008.8
    lat1, lat2 = radians(left.latitude), radians(right.latitude)
    delta_lat = lat2 - lat1
    delta_lon = radians(right.longitude - left.longitude)
    haversine = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return radius_m * 2 * asin(min(1.0, sqrt(haversine)))


def administrative_relationship(left: SchoolFeature, right: SchoolFeature) -> float:
    return float(left.administrative_area.casefold() == right.administrative_area.casefold())


def _tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[^\w]+", value.casefold()) if token}


def semantic_similarity(left: SchoolFeature, right: SchoolFeature) -> float:
    left_tokens = _tokens(left.name)
    right_tokens = _tokens(right.name)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def attribute_matching(left: SchoolFeature, right: SchoolFeature) -> float:
    comparisons: list[float] = [semantic_similarity(left, right)]
    if left.registry_id and right.registry_id:
        comparisons.append(float(left.registry_id.casefold() == right.registry_id.casefold()))
    if left.address and right.address:
        comparisons.append(float(left.address.casefold() == right.address.casefold()))
    return sum(comparisons) / len(comparisons)


def evaluate_spatial_match(
    left: SchoolFeature, right: SchoolFeature, *, maximum_distance_m: float = 250.0
) -> MatchAssessment:
    distance = geometry_distance_m(left, right)
    proximity = max(0.0, 1.0 - distance / maximum_distance_m)
    administrative = administrative_relationship(left, right)
    semantic = semantic_similarity(left, right)
    attributes = attribute_matching(left, right)
    registry_match = bool(
        left.registry_id
        and right.registry_id
        and left.registry_id.casefold() == right.registry_id.casefold()
    )
    matched = administrative == 1.0 and distance <= maximum_distance_m and (
        registry_match or semantic >= 0.5
    )
    overall = (
        0.4 * proximity
        + 0.2 * administrative
        + 0.2 * semantic
        + 0.2 * attributes
    )
    return MatchAssessment(
        left=left,
        right=right,
        distance_m=round(distance, 3),
        proximity_score=round(proximity, 4),
        administrative_score=round(administrative, 4),
        semantic_score=round(semantic, 4),
        attribute_score=round(attributes, 4),
        overall_score=round(overall, 4),
        matched=matched,
    )


def _best_match(
    subject: SchoolFeature, candidates: tuple[SchoolFeature, ...]
) -> tuple[SchoolFeature | None, MatchAssessment | None]:
    assessments = [evaluate_spatial_match(subject, candidate) for candidate in candidates]
    matches = [assessment for assessment in assessments if assessment.matched]
    if not matches:
        return None, None
    best = max(matches, key=lambda item: (item.overall_score, -item.distance_m))
    return best.right, best


def _changed_attributes(nma: SchoolFeature, official: SchoolFeature) -> tuple[str, ...]:
    changed: list[str] = []
    if nma.name.casefold() != official.name.casefold():
        changed.append("name")
    if nma.address and official.address and nma.address.casefold() != official.address.casefold():
        changed.append("address")
    return tuple(changed)


def discover_candidate_findings(inventory: SchoolInventory) -> tuple[CandidateFinding, ...]:
    findings: list[CandidateFinding] = []
    for official in inventory.official_registry:
        osm, official_osm = _best_match(official, inventory.osm)
        nma, official_nma = _best_match(official, inventory.nma)
        if nma is None and osm is not None and official_osm is not None:
            findings.append(
                CandidateFinding(
                    feature_id=official.feature_id,
                    proposal_type="ADD_FEATURE",
                    nma=None,
                    osm=osm,
                    official=official,
                    supporting_matches=(official_osm,),
                    reasoning=(
                        "School exists in OSM and the official registry but has no matching "
                        "feature in the NMA school dataset."
                    ),
                )
            )
            continue
        if nma is None or official_nma is None:
            continue

        supporting = [official_nma]
        if official_osm is not None:
            supporting.append(official_osm)
        changed = _changed_attributes(nma, official)
        if changed:
            findings.append(
                CandidateFinding(
                    feature_id=nma.feature_id,
                    proposal_type="UPDATE_ATTRIBUTES",
                    nma=nma,
                    osm=osm,
                    official=official,
                    supporting_matches=tuple(supporting),
                    reasoning=(
                        f"Official registry differs from the NMA feature for: {', '.join(changed)}."
                    ),
                )
            )

        reference_points = [official, *([osm] if osm is not None else [])]
        consensus_longitude = sum(item.longitude for item in reference_points) / len(reference_points)
        consensus_latitude = sum(item.latitude for item in reference_points) / len(reference_points)
        consensus = SchoolFeature(
            feature_id=f"consensus:{official.feature_id}",
            name=official.name,
            longitude=consensus_longitude,
            latitude=consensus_latitude,
            administrative_area=official.administrative_area,
            source="OFFICIAL_REGISTRY",
            registry_id=official.registry_id,
            address=official.address,
        )
        if geometry_distance_m(nma, consensus) > 75.0:
            findings.append(
                CandidateFinding(
                    feature_id=nma.feature_id,
                    proposal_type="UPDATE_GEOMETRY",
                    nma=nma,
                    osm=osm,
                    official=official,
                    supporting_matches=tuple(supporting),
                    reasoning=(
                        "NMA geometry is more than 75 metres from the OSM and official-registry "
                        "reference location."
                    ),
                )
            )
    return tuple(findings)

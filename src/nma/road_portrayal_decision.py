from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from nma.road_resolution import canonical_sha256, package_sha256


DECISION_SCHEMA = "nma.road-portrayal-decision/1.0"
DECISION_VERSION = "road-02/1.0"
PROPOSAL_SCHEMA = "nma.road-portrayal-proposal/1.0"
PROPOSAL_VERSION = "road-02/1.0"

EXPECTED_UPSTREAM_PACKAGE_SHA256 = (
    "b5df3f57c33843f354371206c937f52d37ddbbd9d047a31ad7c334532ce30e9a"
)
EXPECTED_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
EXPECTED_FIXTURE_SHA256 = "b01e261971f65cbfc127aed4f1ba17b01b194dd89f256d3c024170c1dc7338f0"
EXPECTED_SOURCE_IDS = ("K0000004671", "K0000004913", "K0000005348")
EXPECTED_EVIDENCE_IDS = (
    "BMAP096-P5-TABLE1-GRAPHIC-ELEMENT-CODES",
    "DOC01-P22-P24-ROAD-BOUNDARY-LABEL",
    "DOC01-P34-P35-ROUTE-SHIELDS",
    "DOC02-P45-P46-ANNEX7-CODING-SCHEME",
    "DOC02-P53-P55-ROAD-CODE-BRANCH",
)
EXPECTED_ROUTE_IDENTITY = "ROADNUM=縣126|ROADNUM1=|ROADNUM2=|ROADNAME=中山街"
DERIVED_TARGET = "derived road-centreline portrayal artifact"
ACTION = "prepare derived road-centreline portrayal/annotation"

EXPECTED_BOUNDARIES = {
    "authorization_required": True,
    "execution_allowed": False,
    "source_mutation_allowed": False,
    "topology_repair_allowed": False,
    "roada_execution_allowed": False,
    "road_edge_derivation_allowed": False,
}
EXPECTED_PORTRAYAL = {
    "shield_code": "9490005",
    "shield_orientation": "road-parallel",
    "road_name_annotation": "中山街",
    "graphic_element_roles": [2, 5],
}


class RoadPortrayalDecisionError(ValueError):
    """ROAD-02 rejected an input or artifact instead of broadening its authority."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise RoadPortrayalDecisionError(message, code=code)


def _exact(value: Any, expected: Any, *, label: str, code: str = "binding_mismatch") -> None:
    if value != expected:
        _fail(f"{label} does not match the frozen ROAD-02 binding.", code)


def _semantic_upstream(package: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize only ROAD-01 fields whose contract explicitly defines set semantics."""

    normalized = deepcopy(dict(package))
    evidence = normalized.get("evidence")
    if not isinstance(evidence, dict):
        _fail("The ROAD-01 evidence binding is missing.", "evidence_mismatch")
    evidence_ids = evidence.get("evidence_ids")
    if (
        not isinstance(evidence_ids, list)
        or len(evidence_ids) != len(EXPECTED_EVIDENCE_IDS)
        or not all(isinstance(item, str) for item in evidence_ids)
        or set(evidence_ids) != set(EXPECTED_EVIDENCE_IDS)
    ):
        _fail("The ROAD-01 reviewed evidence set changed.", "evidence_mismatch")
    evidence["evidence_ids"] = list(EXPECTED_EVIDENCE_IDS)
    return normalized


def validate_upstream_package(package: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the complete frozen ROAD-01 semantic and integrity boundary."""

    if not isinstance(package, Mapping):
        _fail("The ROAD-01 input must be an object.", "upstream_invalid")
    normalized = _semantic_upstream(package)

    _exact(
        normalized.get("package_sha256"),
        EXPECTED_UPSTREAM_PACKAGE_SHA256,
        label="Upstream package SHA-256",
        code="upstream_hash_mismatch",
    )
    try:
        computed_package_sha256 = package_sha256(normalized)
    except (TypeError, ValueError):
        _fail("The ROAD-01 package is not canonically serializable.", "upstream_invalid")
    if computed_package_sha256 != EXPECTED_UPSTREAM_PACKAGE_SHA256:
        _fail("The ROAD-01 package content does not match its SHA-256.", "upstream_hash_mismatch")

    _exact(normalized.get("package_version"), "road-01/1.0", label="Package version")
    _exact(
        normalized.get("schema_version"),
        "nma.road-resolution-evidence-package/1.0",
        label="Package schema",
    )
    source = normalized.get("source")
    _exact(
        source,
        {
            "profile": "K14",
            "layer": "K14_ROAD",
            "archive_sha256": EXPECTED_ARCHIVE_SHA256,
        },
        label="Source archive",
        code="source_binding_mismatch",
    )
    _exact(
        normalized.get("fixture"),
        {"sha256": EXPECTED_FIXTURE_SHA256},
        label="Fixture",
        code="fixture_binding_mismatch",
    )
    _exact(
        normalized.get("road_identity"),
        {
            "class_code": "9420400",
            "class_name": "County Highway",
            "route_number": "縣126",
            "road_name": "中山街",
            "canonical_identity": EXPECTED_ROUTE_IDENTITY,
            "identity_basis": ["ROADNUM", "ROADNUM1", "ROADNUM2", "ROADNAME"],
        },
        label="Road identity",
        code="route_identity_mismatch",
    )
    _exact(
        normalized.get("segment_set"),
        {
            "ordered_feature_ids": list(EXPECTED_SOURCE_IDS),
            "count": 3,
            "geometry_type": "LineString",
            "crs": "TWD97[2020]_TM121",
        },
        label="Ordered source scope",
        code="source_scope_mismatch",
    )
    _exact(
        normalized.get("continuity"),
        {
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
        },
        label="Verified topology",
        code="topology_binding_mismatch",
    )
    _exact(
        normalized.get("evidence"),
        {
            "record_set": "nma-road-compound-portrayal-reviewed-v0.4",
            "evidence_ids": list(EXPECTED_EVIDENCE_IDS),
        },
        label="Reviewed evidence",
        code="evidence_mismatch",
    )
    _exact(
        normalized.get("portrayal"),
        {
            "road_class": "9420400",
            "road_name": "中山街",
            "route_number": "縣126",
            "shield_code": "9490005",
            "shield_orientation": "road-parallel",
            "graphic_element_roles": [2, 5],
        },
        label="Reviewed portrayal",
        code="portrayal_mismatch",
    )
    _exact(
        normalized.get("permissions"),
        {
            "source_mutation_allowed": False,
            "execution_allowed": False,
            "topology_repair_allowed": False,
            "roada_execution_allowed": False,
            "road_edge_derivation_allowed": False,
        },
        label="Upstream permissions",
        code="permission_escalation",
    )
    return normalized


def decision_sha256(decision: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(decision))
    basis.pop("decision_sha256", None)
    return canonical_sha256(basis)


def proposal_sha256(proposal: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(proposal))
    basis.pop("proposal_sha256", None)
    return canonical_sha256(basis)


def _bindings() -> dict[str, Any]:
    return {
        "upstream_package_sha256": EXPECTED_UPSTREAM_PACKAGE_SHA256,
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "fixture_sha256": EXPECTED_FIXTURE_SHA256,
        "ordered_source_ids": list(EXPECTED_SOURCE_IDS),
        "route_identity": EXPECTED_ROUTE_IDENTITY,
        "class_code": "9420400",
        "evidence_ids": list(EXPECTED_EVIDENCE_IDS),
    }


def _validate_closed_artifact(
    artifact: Mapping[str, Any], expected: Mapping[str, Any], *, hash_field: str, kind: str
) -> None:
    if not isinstance(artifact, Mapping):
        _fail(f"The ROAD-02 {kind} must be an object.", f"{kind}_invalid")
    missing = set(expected) - set(artifact)
    extra = set(artifact) - set(expected)
    if missing or extra:
        _fail(
            f"The ROAD-02 {kind} fields are not closed (missing={sorted(missing)!r}, "
            f"extra={sorted(extra)!r}).",
            f"{kind}_schema_invalid",
        )
    expected_without_hash = deepcopy(dict(expected))
    expected_hash = expected_without_hash.pop(hash_field)
    for key, value in expected_without_hash.items():
        _exact(artifact.get(key), value, label=f"{kind} field {key}", code=f"{kind}_invalid")
    computed = decision_sha256(artifact) if kind == "decision" else proposal_sha256(artifact)
    if artifact.get(hash_field) != expected_hash or computed != expected_hash:
        _fail(f"The ROAD-02 {kind} hash is invalid.", f"{kind}_hash_mismatch")


def validate_decision(decision: Mapping[str, Any]) -> None:
    expected = _decision_template()
    expected["decision_sha256"] = decision_sha256(expected)
    _validate_closed_artifact(
        decision, expected, hash_field="decision_sha256", kind="decision"
    )


def validate_proposal(proposal: Mapping[str, Any], decision: Mapping[str, Any]) -> None:
    validate_decision(decision)
    expected = _proposal_template(decision["decision_sha256"])
    expected["proposal_sha256"] = proposal_sha256(expected)
    _validate_closed_artifact(
        proposal, expected, hash_field="proposal_sha256", kind="proposal"
    )


def _decision_template() -> dict[str, Any]:
    return {
        "decision_version": DECISION_VERSION,
        "schema_version": DECISION_SCHEMA,
        "bindings": _bindings(),
        "decision": {
            "action": ACTION,
            "execution_target": DERIVED_TARGET,
            "road_class": "9420400",
            "route_number": "縣126",
            "road_name": "中山街",
            "requested_portrayal": deepcopy(EXPECTED_PORTRAYAL),
        },
        "boundaries": deepcopy(EXPECTED_BOUNDARIES),
    }


def _proposal_template(decision_hash: str) -> dict[str, Any]:
    return {
        "proposal_version": PROPOSAL_VERSION,
        "schema_version": PROPOSAL_SCHEMA,
        "bindings": {**_bindings(), "decision_sha256": decision_hash},
        "proposal": {
            "action": ACTION,
            "execution_target": DERIVED_TARGET,
            "requested_changes": deepcopy(EXPECTED_PORTRAYAL),
        },
        "boundaries": deepcopy(EXPECTED_BOUNDARIES),
    }


def prepare_road_portrayal(
    upstream_package: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create deterministic ROAD-02 artifacts; never execute or mutate source/runtime state."""

    validate_upstream_package(upstream_package)
    decision = _decision_template()
    decision["decision_sha256"] = decision_sha256(decision)
    proposal = _proposal_template(decision["decision_sha256"])
    proposal["proposal_sha256"] = proposal_sha256(proposal)
    validate_decision(decision)
    validate_proposal(proposal, decision)
    return decision, proposal

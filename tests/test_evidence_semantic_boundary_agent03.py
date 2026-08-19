from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from agent_contracts.evidence import (
    EVIDENCE_OBJECT_VERSION,
    EVIDENCE_PROPOSAL_VERSION,
    EVIDENCE_REFERENCE_VERSION,
    EvidenceContractError,
    EvidenceReference,
    EvidenceRegistry,
    create_evidence_backed_proposal,
    create_evidence_object,
    evidence_reference,
    validate_evidence_backed_proposal,
    validate_evidence_object,
)
from agent_contracts.intent_planning import plan_request


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_SCHEMA = ROOT / "schemas" / "agent-evidence-v1.0.schema.json"
PROPOSAL_SCHEMA = ROOT / "schemas" / "evidence-backed-proposal-v1.0.schema.json"
PROTECTED_PRODUCTION_HASHES = {
    "nmaAgentDemo.html": "8b6d6310d3ac6b45e71b73102de023869b0f56422dfbf1c74d81a6650ba5a470",
    "scripts/build_public_site.py": "6f9e6e75281f50eb4d6297d9fea7018e165cfdcb0d6ac56873f9940e0a50c55e",
    "data/knowledge/portrayal-graph.json": (
        "0f90dc365805aaac07ab5aaf61323006bcea1ba8a078470c6872ad63a7eeacca"
    ),
    "pyproject.toml": "ccf4d084262633d8806b48645a56ab56c2f6b58566cadcb6fc3c24e6a9592d34",
}


def _schema(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence(payload: object = None):
    evidence_payload = {"feature_code": "9920103", "rule": "school symbol"}
    if payload is not None:
        evidence_payload = payload
    return create_evidence_object(
        source_artifact_id="data/knowledge/portrayal-graph.json",
        source_artifact_version="nma-portrayal-knowledge-v0.1",
        source_artifact_content=(ROOT / "data/knowledge/portrayal-graph.json").read_bytes(),
        evidence_payload=evidence_payload,
        producer="canonical public evidence adapter",
        recorded_at="2026-08-19T00:00:00Z",
        citation_locator="feature:9920103",
        citation_label="NLSC112V5.4 primary school portrayal",
        review_status="reviewed",
        reviewer="tracked portrayal review",
        reproduction_method="deterministic-extraction",
        reproduction_recipe="select node feature:9920103 from the tracked public graph",
        reproduction_inputs=(b"feature:9920103",),
    )


def _proposal_and_registry():
    evidence = _evidence()
    registry = EvidenceRegistry((evidence,))
    proposal = create_evidence_backed_proposal(
        intent_plan=plan_request("What is the primary school symbol rule?"),
        evidence_references=(evidence_reference(evidence),),
        registry=registry,
    )
    return proposal, registry


def test_evidence_and_proposal_schemas_are_closed_and_valid() -> None:
    evidence_schema = _schema(EVIDENCE_SCHEMA)
    proposal_schema = _schema(PROPOSAL_SCHEMA)
    Draft202012Validator.check_schema(evidence_schema)
    Draft202012Validator.check_schema(proposal_schema)
    assert evidence_schema["additionalProperties"] is False
    assert proposal_schema["additionalProperties"] is False
    assert evidence_schema["properties"]["schema"] == {"const": EVIDENCE_OBJECT_VERSION}
    assert proposal_schema["properties"]["schema"] == {"const": EVIDENCE_PROPOSAL_VERSION}


def test_same_evidence_has_stable_identity_and_is_schema_valid() -> None:
    first = _evidence()
    second = _evidence()
    assert first == second
    assert first.evidence_id == second.evidence_id
    assert first.evidence_id.startswith("evidence:sha256:")
    Draft202012Validator(_schema(EVIDENCE_SCHEMA)).validate(first.to_dict())
    validate_evidence_object(first)


def test_changed_evidence_or_source_cannot_preserve_old_identity() -> None:
    original = _evidence()
    changed_payload = _evidence({"feature_code": "9920103", "rule": "changed"})
    assert changed_payload.content_sha256 != original.content_sha256
    assert changed_payload.evidence_id != original.evidence_id

    changed_source = create_evidence_object(
        source_artifact_id=original.source_artifact.artifact_id,
        source_artifact_version=original.source_artifact.version,
        source_artifact_content=b"changed source",
        evidence_payload={"feature_code": "9920103", "rule": "school symbol"},
        producer=original.provenance.producer,
        recorded_at=original.provenance.recorded_at,
        citation_locator=original.citation.locator,
        citation_label=original.citation.label,
        review_status=original.review.status,
        reviewer=original.review.reviewer,
        reproduction_method=original.reproducibility.method,
        reproduction_recipe=original.reproducibility.recipe,
        reproduction_inputs=(b"feature:9920103",),
    )
    assert changed_source.source_artifact.sha256 != original.source_artifact.sha256
    assert changed_source.evidence_id != original.evidence_id

    forged = replace(changed_payload, evidence_id=original.evidence_id)
    with pytest.raises(EvidenceContractError, match="does not match"):
        validate_evidence_object(forged)


def test_evidence_object_is_immutable_and_contains_no_authority_fields() -> None:
    evidence = _evidence()
    with pytest.raises(FrozenInstanceError):
        evidence.evidence_id = "evidence:sha256:" + "0" * 64  # type: ignore[misc]
    serialized = json.dumps(evidence.to_dict(), sort_keys=True)
    forbidden = ("authorization", "approval", "execution", "command", "permission", "mutation")
    assert not any(f'"{term}' in serialized.casefold() for term in forbidden)


def test_missing_evidence_fails_closed_without_generation_or_substitution() -> None:
    missing = EvidenceReference(
        schema=EVIDENCE_REFERENCE_VERSION,
        evidence_id="evidence:sha256:" + "f" * 64,
        purpose="proposal",
    )
    with pytest.raises(EvidenceContractError, match="missing; no fallback"):
        EvidenceRegistry(()).resolve(missing)
    with pytest.raises(EvidenceContractError, match="resolve evidence"):
        create_evidence_backed_proposal(
            intent_plan=plan_request("What is the primary school symbol rule?"),
            evidence_references=(),
            registry=EvidenceRegistry(()),
        )


@pytest.mark.parametrize(
    "reference",
    [
        EvidenceReference(
            schema="nma.agent-evidence-reference/9.9",  # type: ignore[arg-type]
            evidence_id="evidence:sha256:" + "f" * 64,
            purpose="proposal",
        ),
        EvidenceReference(
            schema=EVIDENCE_REFERENCE_VERSION,
            evidence_id="not-an-evidence-identity",
            purpose="proposal",
        ),
        EvidenceReference(
            schema=EVIDENCE_REFERENCE_VERSION,
            evidence_id="evidence:sha256:" + "f" * 64,
            purpose="execute",  # type: ignore[arg-type]
        ),
    ],
)
def test_invalid_evidence_references_are_rejected(reference: EvidenceReference) -> None:
    with pytest.raises(EvidenceContractError):
        EvidenceRegistry((_evidence(),)).resolve(reference)


def test_proposal_binds_canonical_intent_and_resolved_evidence_only() -> None:
    proposal, registry = _proposal_and_registry()
    assert proposal["schema"] == EVIDENCE_PROPOSAL_VERSION
    assert proposal["intent_reference"]["contract"] == "nma.intent-planning/1.0"
    assert proposal["metadata"] == {"boundary": "proposal-only"}
    assert proposal["presentation"] == {
        "display_intent": "evidence_panel",
        "feature_code": "9920103",
    }
    Draft202012Validator(_schema(PROPOSAL_SCHEMA)).validate(proposal)
    assert validate_evidence_backed_proposal(proposal, registry=registry) == proposal


@pytest.mark.parametrize(
    ("location", "field", "value"),
    [
        (None, "authorization_id", "auth-1"),
        (None, "execution_id", "exec-1"),
        ("metadata", "mutation_permissions", ["write"]),
        ("presentation", "shell_command", "touch output"),
        ("presentation", "road_authorization", "substitute"),
        ("presentation", "school_hero_execution", "substitute"),
    ],
)
def test_proposal_cannot_contain_authorization_or_execution_authority(
    location: str | None, field: str, value: object
) -> None:
    proposal, registry = _proposal_and_registry()
    changed = deepcopy(proposal)
    target = changed if location is None else changed[location]
    target[field] = value
    with pytest.raises(EvidenceContractError, match="exact closed field set"):
        validate_evidence_backed_proposal(changed, registry=registry)


def test_abstention_cannot_be_promoted_to_an_evidence_proposal() -> None:
    evidence = _evidence()
    with pytest.raises(EvidenceContractError, match="Only evidence-requiring"):
        create_evidence_backed_proposal(
            intent_plan=plan_request("Deploy the layer"),
            evidence_references=(evidence_reference(evidence),),
            registry=EvidenceRegistry((evidence,)),
        )


def test_production_runtime_dependencies_and_public_graph_are_byte_identical() -> None:
    for relative, expected in PROTECTED_PRODUCTION_HASHES.items():
        assert _sha256(ROOT / relative) == expected
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "dependencies = []" in pyproject
    builder = (ROOT / "scripts/build_public_site.py").read_text(encoding="utf-8")
    for forbidden in ("agent_contracts", "graphrag", "neo4j", "vector_index"):
        assert forbidden not in builder


def test_experimental_semantic_stacks_are_not_imported_by_evidence_contract() -> None:
    source = (ROOT / "agent_contracts" / "evidence.py").read_text(encoding="utf-8")
    forbidden_imports = (
        "nma.graphrag",
        "nma.vector_index",
        "nma.neo4j",
        "nma.retrieval",
        "nma.entity_resolution",
    )
    assert not any(name in source for name in forbidden_imports)

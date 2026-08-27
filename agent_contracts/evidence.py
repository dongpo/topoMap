from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Literal, Mapping, Sequence, cast

from agent_contracts.intent_planning import (
    CONTRACT_VERSION as INTENT_CONTRACT_VERSION,
    validate_intent_plan,
)


EvidenceObjectVersion = Literal["nma.agent-evidence/1.0"]
EvidenceReferenceVersion = Literal["nma.agent-evidence-reference/1.0"]
EvidenceProposalVersion = Literal["nma.evidence-backed-proposal/1.0"]

EVIDENCE_OBJECT_VERSION: EvidenceObjectVersion = "nma.agent-evidence/1.0"
EVIDENCE_REFERENCE_VERSION: EvidenceReferenceVersion = "nma.agent-evidence-reference/1.0"
EVIDENCE_PROPOSAL_VERSION: EvidenceProposalVersion = "nma.evidence-backed-proposal/1.0"

ReviewStatus = Literal["unreviewed", "reviewed", "validated"]
ReproductionMethod = Literal[
    "direct-artifact",
    "deterministic-extraction",
    "deterministic-query",
]
ReferencePurpose = Literal["explanation", "proposal", "verification", "provenance"]

_SHA256 = re.compile(r"[0-9a-f]{64}")
_EVIDENCE_ID = re.compile(r"evidence:sha256:[0-9a-f]{64}")
_INTENT_ID = re.compile(r"intent:sha256:[0-9a-f]{64}")
_REVIEW_STATUSES = frozenset(("unreviewed", "reviewed", "validated"))
_REPRODUCTION_METHODS = frozenset(
    ("direct-artifact", "deterministic-extraction", "deterministic-query")
)
_REFERENCE_PURPOSES = frozenset(("explanation", "proposal", "verification", "provenance"))
_PROPOSAL_FIELDS = frozenset(
    ("schema", "intent_reference", "evidence_references", "presentation", "metadata")
)
_INTENT_REFERENCE_FIELDS = frozenset(("contract", "sha256"))
_PRESENTATION_FIELDS = frozenset(("display_intent", "feature_code"))
_METADATA_FIELDS = frozenset(("boundary",))


class EvidenceContractError(ValueError):
    """Evidence or proposal data violated the closed read-only boundary."""


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise EvidenceContractError("Evidence inputs must be canonical JSON values.") from error


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _bounded_text(value: object, *, field: str, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise EvidenceContractError(f"{field} must be a non-empty bounded string.")
    if any(ord(character) < 32 for character in value):
        raise EvidenceContractError(f"{field} must not contain control characters.")
    return value


def _require_sha256(value: object, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise EvidenceContractError(f"{field} must be a lowercase SHA-256 digest.")
    return value


@dataclass(frozen=True)
class SourceArtifact:
    artifact_id: str
    version: str
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact_id": self.artifact_id,
            "version": self.version,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class Provenance:
    producer: str
    recorded_at: str

    def to_dict(self) -> dict[str, str]:
        return {"producer": self.producer, "recorded_at": self.recorded_at}


@dataclass(frozen=True)
class Citation:
    locator: str
    label: str

    def to_dict(self) -> dict[str, str]:
        return {"locator": self.locator, "label": self.label}


@dataclass(frozen=True)
class Review:
    status: ReviewStatus
    reviewer: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {"status": self.status, "reviewer": self.reviewer}


@dataclass(frozen=True)
class Reproducibility:
    method: ReproductionMethod
    recipe: str
    input_sha256: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "recipe": self.recipe,
            "input_sha256": list(self.input_sha256),
        }


@dataclass(frozen=True)
class EvidenceObject:
    schema: EvidenceObjectVersion
    evidence_id: str
    source_artifact: SourceArtifact
    content_sha256: str
    provenance: Provenance
    citation: Citation
    review: Review
    reproducibility: Reproducibility

    def identity_body(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "source_artifact": self.source_artifact.to_dict(),
            "content_sha256": self.content_sha256,
            "provenance": self.provenance.to_dict(),
            "citation": self.citation.to_dict(),
            "review": self.review.to_dict(),
            "reproducibility": self.reproducibility.to_dict(),
        }

    def to_dict(self) -> dict[str, object]:
        return {"schema": self.schema, "evidence_id": self.evidence_id, **self.identity_body()}


@dataclass(frozen=True)
class EvidenceReference:
    schema: EvidenceReferenceVersion
    evidence_id: str
    purpose: ReferencePurpose

    def to_dict(self) -> dict[str, str]:
        return {
            "schema": self.schema,
            "evidence_id": self.evidence_id,
            "purpose": self.purpose,
        }


@dataclass(frozen=True)
class EvidenceRegistry:
    objects: tuple[EvidenceObject, ...]

    def __post_init__(self) -> None:
        seen: dict[str, EvidenceObject] = {}
        for evidence in self.objects:
            validate_evidence_object(evidence)
            if evidence.evidence_id in seen:
                raise EvidenceContractError("Evidence registry identities must be unique.")
            seen[evidence.evidence_id] = evidence

    def resolve(self, reference: EvidenceReference) -> EvidenceObject:
        validate_evidence_reference(reference)
        for evidence in self.objects:
            if evidence.evidence_id == reference.evidence_id:
                return validate_evidence_object(evidence)
        raise EvidenceContractError("Referenced evidence is missing; no fallback is permitted.")


def create_evidence_object(
    *,
    source_artifact_id: str,
    source_artifact_version: str,
    source_artifact_content: bytes,
    evidence_payload: object,
    producer: str,
    recorded_at: str,
    citation_locator: str,
    citation_label: str,
    review_status: ReviewStatus,
    reviewer: str | None,
    reproduction_method: ReproductionMethod,
    reproduction_recipe: str,
    reproduction_inputs: Sequence[bytes] = (),
) -> EvidenceObject:
    """Create one immutable, content-addressed evidence envelope.

    The envelope records evidence and source identities only. It deliberately has no authority,
    command, permission, endpoint, mutation, executor, or approval-consumption field.
    """

    if not isinstance(source_artifact_content, bytes):
        raise EvidenceContractError("Source artifact content must be bytes.")
    _canonical_json(evidence_payload)
    source = SourceArtifact(
        artifact_id=_bounded_text(source_artifact_id, field="source artifact identity"),
        version=_bounded_text(source_artifact_version, field="source artifact version"),
        sha256=_sha256_bytes(source_artifact_content),
    )
    provenance = Provenance(
        producer=_bounded_text(producer, field="provenance producer"),
        recorded_at=_bounded_text(recorded_at, field="provenance timestamp"),
    )
    citation = Citation(
        locator=_bounded_text(citation_locator, field="citation locator"),
        label=_bounded_text(citation_label, field="citation label"),
    )
    if review_status not in _REVIEW_STATUSES:
        raise EvidenceContractError("Unknown evidence review status.")
    if review_status == "unreviewed" and reviewer is not None:
        raise EvidenceContractError("Unreviewed evidence cannot name a reviewer.")
    if review_status != "unreviewed":
        reviewer = _bounded_text(reviewer, field="reviewer")
    review = Review(status=review_status, reviewer=reviewer)
    if reproduction_method not in _REPRODUCTION_METHODS:
        raise EvidenceContractError("Unknown evidence reproduction method.")
    reproduction = Reproducibility(
        method=reproduction_method,
        recipe=_bounded_text(reproduction_recipe, field="reproduction recipe"),
        input_sha256=tuple(_sha256_bytes(value) for value in reproduction_inputs),
    )
    provisional = EvidenceObject(
        schema=EVIDENCE_OBJECT_VERSION,
        evidence_id="evidence:sha256:" + "0" * 64,
        source_artifact=source,
        content_sha256=_sha256_json(evidence_payload),
        provenance=provenance,
        citation=citation,
        review=review,
        reproducibility=reproduction,
    )
    result = EvidenceObject(
        **{
            **provisional.__dict__,
            "evidence_id": f"evidence:sha256:{_sha256_json(provisional.identity_body())}",
        }
    )
    return validate_evidence_object(result)


def validate_evidence_object(value: EvidenceObject) -> EvidenceObject:
    if not isinstance(value, EvidenceObject):
        raise EvidenceContractError("Evidence must use the immutable EvidenceObject type.")
    if value.schema != EVIDENCE_OBJECT_VERSION:
        raise EvidenceContractError("Unsupported evidence object version.")
    if _EVIDENCE_ID.fullmatch(value.evidence_id) is None:
        raise EvidenceContractError("Evidence identity is malformed.")
    _bounded_text(value.source_artifact.artifact_id, field="source artifact identity")
    _bounded_text(value.source_artifact.version, field="source artifact version")
    _require_sha256(value.source_artifact.sha256, field="source artifact hash")
    _require_sha256(value.content_sha256, field="evidence content hash")
    _bounded_text(value.provenance.producer, field="provenance producer")
    _bounded_text(value.provenance.recorded_at, field="provenance timestamp")
    _bounded_text(value.citation.locator, field="citation locator")
    _bounded_text(value.citation.label, field="citation label")
    if value.review.status not in _REVIEW_STATUSES:
        raise EvidenceContractError("Unknown evidence review status.")
    if value.review.status == "unreviewed" and value.review.reviewer is not None:
        raise EvidenceContractError("Unreviewed evidence cannot name a reviewer.")
    if value.review.status != "unreviewed":
        _bounded_text(value.review.reviewer, field="reviewer")
    if value.reproducibility.method not in _REPRODUCTION_METHODS:
        raise EvidenceContractError("Unknown evidence reproduction method.")
    _bounded_text(value.reproducibility.recipe, field="reproduction recipe")
    for digest in value.reproducibility.input_sha256:
        _require_sha256(digest, field="reproduction input hash")
    expected = f"evidence:sha256:{_sha256_json(value.identity_body())}"
    if value.evidence_id != expected:
        raise EvidenceContractError("Evidence identity does not match its immutable content.")
    return value


def evidence_reference(
    evidence: EvidenceObject, *, purpose: ReferencePurpose = "proposal"
) -> EvidenceReference:
    validate_evidence_object(evidence)
    reference = EvidenceReference(
        schema=EVIDENCE_REFERENCE_VERSION,
        evidence_id=evidence.evidence_id,
        purpose=purpose,
    )
    return validate_evidence_reference(reference)


def validate_evidence_reference(value: EvidenceReference) -> EvidenceReference:
    if not isinstance(value, EvidenceReference):
        raise EvidenceContractError("Evidence references must use the closed immutable type.")
    if value.schema != EVIDENCE_REFERENCE_VERSION:
        raise EvidenceContractError("Unsupported evidence reference version.")
    if _EVIDENCE_ID.fullmatch(value.evidence_id) is None:
        raise EvidenceContractError("Evidence reference identity is malformed.")
    if value.purpose not in _REFERENCE_PURPOSES:
        raise EvidenceContractError("Unknown evidence reference purpose.")
    return value


def intent_reference(intent_plan: Mapping[str, object]) -> dict[str, str]:
    validated = validate_intent_plan(intent_plan)
    return {
        "contract": INTENT_CONTRACT_VERSION,
        "sha256": f"intent:sha256:{_sha256_json(validated)}",
    }


def create_evidence_backed_proposal(
    *,
    intent_plan: Mapping[str, object],
    evidence_references: Sequence[EvidenceReference],
    registry: EvidenceRegistry,
) -> dict[str, object]:
    """Bind resolved evidence to a display proposal without creating authority."""

    validated_intent = validate_intent_plan(intent_plan)
    if validated_intent["disposition"] != "proposal" or validated_intent["evidence_intent"] != (
        "required"
    ):
        raise EvidenceContractError("Only evidence-requiring proposal intents may be bound.")
    references = tuple(evidence_references)
    if not references:
        raise EvidenceContractError("Evidence-requiring proposals must resolve evidence.")
    for reference in references:
        if validate_evidence_reference(reference).purpose != "proposal":
            raise EvidenceContractError("Proposal evidence references must use proposal purpose.")
        registry.resolve(reference)
    proposal = {
        "schema": EVIDENCE_PROPOSAL_VERSION,
        "intent_reference": intent_reference(validated_intent),
        "evidence_references": [reference.to_dict() for reference in references],
        "presentation": {
            "display_intent": validated_intent["display_intent"],
            "feature_code": validated_intent["feature_code"],
        },
        "metadata": {"boundary": "proposal-only"},
    }
    return validate_evidence_backed_proposal(proposal, registry=registry)


def _reference_from_mapping(value: object) -> EvidenceReference:
    if not isinstance(value, Mapping) or set(value) != {"schema", "evidence_id", "purpose"}:
        raise EvidenceContractError("Evidence references must use the exact closed field set.")
    if not all(isinstance(item, str) for item in value.values()):
        raise EvidenceContractError("Evidence reference fields must be strings.")
    return validate_evidence_reference(
        EvidenceReference(
            schema=cast(EvidenceReferenceVersion, value["schema"]),
            evidence_id=cast(str, value["evidence_id"]),
            purpose=cast(ReferencePurpose, value["purpose"]),
        )
    )


def validate_evidence_backed_proposal(
    value: Mapping[str, object], *, registry: EvidenceRegistry
) -> dict[str, object]:
    """Validate one closed proposal envelope and resolve every evidence reference.

    Exact field sets prevent evidence, planning, or callers from smuggling authorization grants,
    execution IDs, commands, mutation parameters, API calls, paths, or domain permissions.
    """

    if not isinstance(value, Mapping) or set(value) != _PROPOSAL_FIELDS:
        raise EvidenceContractError(
            "Evidence-backed proposals must use the exact closed field set."
        )
    if value["schema"] != EVIDENCE_PROPOSAL_VERSION:
        raise EvidenceContractError("Unsupported evidence-backed proposal version.")
    intent = value["intent_reference"]
    if not isinstance(intent, Mapping) or set(intent) != _INTENT_REFERENCE_FIELDS:
        raise EvidenceContractError("Intent references must use the exact closed field set.")
    if intent["contract"] != INTENT_CONTRACT_VERSION:
        raise EvidenceContractError("Proposal intent reference uses an unknown contract.")
    if not isinstance(intent["sha256"], str) or _INTENT_ID.fullmatch(intent["sha256"]) is None:
        raise EvidenceContractError("Proposal intent reference identity is malformed.")
    references = value["evidence_references"]
    if not isinstance(references, list) or not references:
        raise EvidenceContractError("Proposal evidence references must be a non-empty list.")
    for item in references:
        reference = _reference_from_mapping(item)
        if reference.purpose != "proposal":
            raise EvidenceContractError("Proposal evidence references must use proposal purpose.")
        registry.resolve(reference)
    presentation = value["presentation"]
    if not isinstance(presentation, Mapping) or set(presentation) != _PRESENTATION_FIELDS:
        raise EvidenceContractError("Presentation proposals must use the exact closed field set.")
    if presentation["display_intent"] not in {"evidence_panel", "portrayal_preview"}:
        raise EvidenceContractError("Unknown proposal presentation intent.")
    feature_code = presentation["feature_code"]
    if not isinstance(feature_code, str) or re.fullmatch(r"\d{7}", feature_code) is None:
        raise EvidenceContractError("Proposal feature codes must contain seven digits.")
    metadata = value["metadata"]
    if not isinstance(metadata, Mapping) or set(metadata) != _METADATA_FIELDS:
        raise EvidenceContractError("Proposal metadata must use the exact closed field set.")
    if metadata["boundary"] != "proposal-only":
        raise EvidenceContractError("Proposal metadata cannot confer authority.")
    return json.loads(_canonical_json(value))

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
from typing import Literal, Mapping, cast

from agent_contracts.evidence import (
    EVIDENCE_OBJECT_VERSION,
    EVIDENCE_PROPOSAL_VERSION,
    EVIDENCE_REFERENCE_VERSION,
    EvidenceReference,
    EvidenceReferenceVersion,
    EvidenceRegistry,
    ReferencePurpose,
    create_evidence_backed_proposal,
    evidence_reference,
    intent_reference,
    validate_evidence_backed_proposal,
    validate_evidence_reference,
)
from agent_contracts.governance import (
    DECISION_RECORD_VERSION,
    EVALUATION_VERSION,
    proposal_identity,
    request_identity,
    validate_decision_record,
    validate_evaluation_record,
)
from agent_contracts.intent_planning import (
    CONTRACT_VERSION as INTENT_CONTRACT_VERSION,
    plan_request,
    validate_intent_plan,
)


RunRecordVersion = Literal["nma.agent-run-record/1.0"]

RUN_RECORD_VERSION: RunRecordVersion = "nma.agent-run-record/1.0"
PRODUCTION_RUNTIME_VERSION = "nma-public-evidence-runtime/v0.2"

_SHA256 = r"[0-9a-f]{64}"
_RUN_ID = re.compile(rf"agent-run:sha256:{_SHA256}")
_REQUEST_ID = re.compile(rf"request:sha256:{_SHA256}")
_INTENT_ID = re.compile(rf"intent:sha256:{_SHA256}")
_PROPOSAL_ID = re.compile(rf"proposal:sha256:{_SHA256}")
_EVALUATION_ID = re.compile(rf"evaluation:sha256:{_SHA256}")
_DECISION_ID = re.compile(rf"decision-record:sha256:{_SHA256}")
_UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

_RUN_FIELDS = frozenset(
    (
        "schema",
        "run_id",
        "request_identity",
        "intent_reference",
        "evidence_references",
        "proposal_identity",
        "evaluation_reference",
        "decision_record_reference",
        "timestamps",
        "versions",
        "reproducibility",
        "completion",
        "boundary",
        "provenance",
    )
)
_INTENT_REFERENCE_FIELDS = frozenset(("contract", "sha256"))
_EVIDENCE_REFERENCE_FIELDS = frozenset(("schema", "evidence_id", "purpose"))
_TIMESTAMP_FIELDS = frozenset(("started_at", "completed_at"))
_VERSION_FIELDS = frozenset(
    (
        "production_runtime",
        "intent_planning",
        "evidence_object",
        "evidence_reference",
        "proposal",
        "evaluation",
        "decision_record",
        "run_record",
    )
)
_REPRODUCIBILITY_FIELDS = frozenset(
    ("method", "canonicalization", "hidden_state", "execution_access")
)
_COMPLETION_FIELDS = frozenset(("status", "chain_verification"))
_PROVENANCE_FIELDS = frozenset(("recorded_by", "recorded_at"))

_VERSIONS = {
    "production_runtime": PRODUCTION_RUNTIME_VERSION,
    "intent_planning": INTENT_CONTRACT_VERSION,
    "evidence_object": EVIDENCE_OBJECT_VERSION,
    "evidence_reference": EVIDENCE_REFERENCE_VERSION,
    "proposal": EVIDENCE_PROPOSAL_VERSION,
    "evaluation": EVALUATION_VERSION,
    "decision_record": DECISION_RECORD_VERSION,
    "run_record": RUN_RECORD_VERSION,
}
_REPRODUCIBILITY = {
    "method": "deterministic-reference-replay",
    "canonicalization": "json-sort-keys-utf8-sha256",
    "hidden_state": "not-required",
    "execution_access": "not-required",
}
_COMPLETION = {"status": "complete", "chain_verification": "verified"}


class ProvenanceContractError(ValueError):
    """Run provenance violated the closed traceability-only boundary."""


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
        raise ProvenanceContractError(
            "Run provenance must contain canonical JSON values."
        ) from error


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _bounded_text(value: object, *, field: str, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ProvenanceContractError(f"{field} must be a non-empty bounded string.")
    if any(ord(character) < 32 for character in value):
        raise ProvenanceContractError(f"{field} must not contain control characters.")
    return value


def _timestamp(value: object, *, field: str) -> str:
    if not isinstance(value, str) or _UTC_TIMESTAMP.fullmatch(value) is None:
        raise ProvenanceContractError(f"{field} must be an explicit UTC second timestamp.")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProvenanceContractError(f"{field} is not a valid timestamp.") from error
    return value


def _identity(value: object, *, field: str, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ProvenanceContractError(f"{field} is malformed.")
    return value


def _intent_reference(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != _INTENT_REFERENCE_FIELDS:
        raise ProvenanceContractError("Intent references must use the exact closed field set.")
    if value["contract"] != INTENT_CONTRACT_VERSION:
        raise ProvenanceContractError("Run record references an unknown planning contract.")
    identity = _identity(value["sha256"], field="intent identity", pattern=_INTENT_ID)
    return {"contract": INTENT_CONTRACT_VERSION, "sha256": identity}


def _evidence_references(
    value: object, *, registry: EvidenceRegistry
) -> tuple[EvidenceReference, ...]:
    if not isinstance(value, list) or not value:
        raise ProvenanceContractError("Run evidence references must be a non-empty list.")
    references: list[EvidenceReference] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) != _EVIDENCE_REFERENCE_FIELDS:
            raise ProvenanceContractError(
                "Run evidence references must use the exact closed field set."
            )
        if not all(isinstance(field, str) for field in item.values()):
            raise ProvenanceContractError("Run evidence reference fields must be strings.")
        reference = validate_evidence_reference(
            EvidenceReference(
                schema=cast(EvidenceReferenceVersion, item["schema"]),
                evidence_id=cast(str, item["evidence_id"]),
                purpose=cast(ReferencePurpose, item["purpose"]),
            )
        )
        if reference.schema != EVIDENCE_REFERENCE_VERSION or reference.purpose != "proposal":
            raise ProvenanceContractError("Run records preserve proposal evidence only.")
        if reference.evidence_id in seen:
            raise ProvenanceContractError("Run evidence references must be unique.")
        registry.resolve(reference)
        references.append(reference)
        seen.add(reference.evidence_id)
    return tuple(references)


def create_agent_run_record(
    *,
    request: str,
    intent_plan: Mapping[str, object],
    proposal: Mapping[str, object],
    evaluation: Mapping[str, object],
    decision_record: Mapping[str, object],
    registry: EvidenceRegistry,
    started_at: str,
    completed_at: str,
    recorded_by: str,
    recorded_at: str,
) -> dict[str, object]:
    """Create a complete traceability record that grants no authority or execution access."""

    validated_intent = validate_intent_plan(intent_plan)
    if validated_intent != plan_request(request):
        raise ProvenanceContractError("Run intent is not deterministic for the request.")
    expected_intent = intent_reference(validated_intent)
    validated_proposal = validate_evidence_backed_proposal(proposal, registry=registry)
    validated_evaluation = validate_evaluation_record(evaluation, registry=registry)
    validated_decision = validate_decision_record(
        decision_record,
        evaluation=validated_evaluation,
        registry=registry,
    )
    references = _evidence_references(validated_proposal["evidence_references"], registry=registry)
    expected_evidence = [reference.to_dict() for reference in references]
    rebuilt_proposal = create_evidence_backed_proposal(
        intent_plan=validated_intent,
        evidence_references=references,
        registry=registry,
    )
    if rebuilt_proposal != validated_proposal:
        raise ProvenanceContractError("Run proposal is not deterministic for its references.")
    expected_request = request_identity(request)
    expected_proposal = proposal_identity(validated_proposal, registry=registry)
    linked = (
        (validated_evaluation["request_identity"], expected_request, "evaluation request"),
        (validated_decision["request_identity"], expected_request, "decision request"),
        (validated_proposal["intent_reference"], expected_intent, "proposal intent"),
        (validated_evaluation["intent_reference"], expected_intent, "evaluation intent"),
        (validated_decision["intent_reference"], expected_intent, "decision intent"),
        (validated_evaluation["evidence_references"], expected_evidence, "evaluation evidence"),
        (validated_decision["evidence_references"], expected_evidence, "decision evidence"),
        (validated_evaluation["proposal_identity"], expected_proposal, "evaluation proposal"),
        (validated_decision["proposal_identity"], expected_proposal, "decision proposal"),
        (
            validated_decision["evaluation_reference"],
            validated_evaluation["evaluation_id"],
            "decision evaluation",
        ),
    )
    for actual, expected, label in linked:
        if actual != expected:
            raise ProvenanceContractError(f"Run {label} linkage is inconsistent.")

    started = _timestamp(started_at, field="run start")
    completed = _timestamp(completed_at, field="run completion")
    recorded = _timestamp(recorded_at, field="run record timestamp")
    if not (started <= completed <= recorded):
        raise ProvenanceContractError("Run timestamps must be monotonic.")

    body: dict[str, object] = {
        "schema": RUN_RECORD_VERSION,
        "request_identity": expected_request,
        "intent_reference": expected_intent,
        "evidence_references": expected_evidence,
        "proposal_identity": expected_proposal,
        "evaluation_reference": validated_evaluation["evaluation_id"],
        "decision_record_reference": validated_decision["decision_record_id"],
        "timestamps": {"started_at": started, "completed_at": completed},
        "versions": dict(_VERSIONS),
        "reproducibility": dict(_REPRODUCIBILITY),
        "completion": dict(_COMPLETION),
        "boundary": "traceability-audit-replay-only",
        "provenance": {
            "recorded_by": _bounded_text(recorded_by, field="run recorder"),
            "recorded_at": recorded,
        },
    }
    record = {**body, "run_id": f"agent-run:sha256:{_sha256_json(body)}"}
    return validate_agent_run_record(
        record,
        evaluation=validated_evaluation,
        decision_record=validated_decision,
        registry=registry,
    )


def validate_agent_run_record(
    value: Mapping[str, object],
    *,
    evaluation: Mapping[str, object],
    decision_record: Mapping[str, object],
    registry: EvidenceRegistry,
) -> dict[str, object]:
    """Validate one finalized run record and every supplied immutable reference."""

    if not isinstance(value, Mapping) or set(value) != _RUN_FIELDS:
        raise ProvenanceContractError("Run records must use the exact closed field set.")
    if value["schema"] != RUN_RECORD_VERSION:
        raise ProvenanceContractError("Unsupported Agent Run Record version.")
    run_id = _identity(value["run_id"], field="run identity", pattern=_RUN_ID)
    request_id = _identity(value["request_identity"], field="request identity", pattern=_REQUEST_ID)
    intent = _intent_reference(value["intent_reference"])
    references = _evidence_references(value["evidence_references"], registry=registry)
    proposal_id = _identity(
        value["proposal_identity"], field="proposal identity", pattern=_PROPOSAL_ID
    )
    evaluation_id = _identity(
        value["evaluation_reference"], field="evaluation reference", pattern=_EVALUATION_ID
    )
    decision_id = _identity(
        value["decision_record_reference"],
        field="decision record reference",
        pattern=_DECISION_ID,
    )

    validated_evaluation = validate_evaluation_record(evaluation, registry=registry)
    validated_decision = validate_decision_record(
        decision_record,
        evaluation=validated_evaluation,
        registry=registry,
    )
    expected_evidence = [reference.to_dict() for reference in references]
    if evaluation_id != validated_evaluation["evaluation_id"]:
        raise ProvenanceContractError("Run record does not resolve the supplied evaluation.")
    if decision_id != validated_decision["decision_record_id"]:
        raise ProvenanceContractError("Run record does not resolve the supplied decision record.")
    for linked, expected, label in (
        (validated_evaluation["request_identity"], request_id, "evaluation request"),
        (validated_decision["request_identity"], request_id, "decision request"),
        (validated_evaluation["intent_reference"], intent, "evaluation intent"),
        (validated_decision["intent_reference"], intent, "decision intent"),
        (validated_evaluation["evidence_references"], expected_evidence, "evaluation evidence"),
        (validated_decision["evidence_references"], expected_evidence, "decision evidence"),
        (validated_evaluation["proposal_identity"], proposal_id, "evaluation proposal"),
        (validated_decision["proposal_identity"], proposal_id, "decision proposal"),
        (validated_decision["evaluation_reference"], evaluation_id, "decision evaluation"),
    ):
        if linked != expected:
            raise ProvenanceContractError(f"Run record {label} linkage is inconsistent.")

    timestamps = value["timestamps"]
    if not isinstance(timestamps, Mapping) or set(timestamps) != _TIMESTAMP_FIELDS:
        raise ProvenanceContractError("Run timestamps must use the exact closed field set.")
    started = _timestamp(timestamps["started_at"], field="run start")
    completed = _timestamp(timestamps["completed_at"], field="run completion")
    if started > completed:
        raise ProvenanceContractError("Run completion cannot precede run start.")

    versions = value["versions"]
    if not isinstance(versions, Mapping) or set(versions) != _VERSION_FIELDS:
        raise ProvenanceContractError("Run versions must use the exact closed field set.")
    if dict(versions) != _VERSIONS:
        raise ProvenanceContractError("Run record version linkage is not canonical.")
    reproducibility = value["reproducibility"]
    if (
        not isinstance(reproducibility, Mapping)
        or set(reproducibility) != _REPRODUCIBILITY_FIELDS
        or dict(reproducibility) != _REPRODUCIBILITY
    ):
        raise ProvenanceContractError("Run replay metadata is not deterministic and closed.")
    completion = value["completion"]
    if (
        not isinstance(completion, Mapping)
        or set(completion) != _COMPLETION_FIELDS
        or dict(completion) != _COMPLETION
    ):
        raise ProvenanceContractError("Incomplete audit records cannot claim completion.")
    if value["boundary"] != "traceability-audit-replay-only":
        raise ProvenanceContractError("Run provenance cannot confer execution authority.")
    provenance = value["provenance"]
    if not isinstance(provenance, Mapping) or set(provenance) != _PROVENANCE_FIELDS:
        raise ProvenanceContractError("Run provenance must use the exact closed field set.")
    recorder = _bounded_text(provenance["recorded_by"], field="run recorder")
    recorded = _timestamp(provenance["recorded_at"], field="run record timestamp")
    if completed > recorded:
        raise ProvenanceContractError("Run record timestamp cannot precede completion.")

    normalized: dict[str, object] = {
        "schema": RUN_RECORD_VERSION,
        "request_identity": request_id,
        "intent_reference": intent,
        "evidence_references": expected_evidence,
        "proposal_identity": proposal_id,
        "evaluation_reference": evaluation_id,
        "decision_record_reference": decision_id,
        "timestamps": {"started_at": started, "completed_at": completed},
        "versions": dict(_VERSIONS),
        "reproducibility": dict(_REPRODUCIBILITY),
        "completion": dict(_COMPLETION),
        "boundary": "traceability-audit-replay-only",
        "provenance": {"recorded_by": recorder, "recorded_at": recorded},
    }
    expected_id = f"agent-run:sha256:{_sha256_json(normalized)}"
    if run_id != expected_id:
        raise ProvenanceContractError("Run identity does not match its record content.")
    return {**normalized, "run_id": run_id}


def replay_agent_run(
    *,
    run_record: Mapping[str, object],
    request: str,
    intent_plan: Mapping[str, object],
    proposal: Mapping[str, object],
    evaluation: Mapping[str, object],
    decision_record: Mapping[str, object],
    registry: EvidenceRegistry,
) -> dict[str, object]:
    """Deterministically reconstruct the proposal chain without mutation or hidden state."""

    validated_run = validate_agent_run_record(
        run_record,
        evaluation=evaluation,
        decision_record=decision_record,
        registry=registry,
    )
    if request_identity(request) != validated_run["request_identity"]:
        raise ProvenanceContractError("Replay request does not resolve the recorded identity.")
    expected_intent = plan_request(request)
    validated_intent = validate_intent_plan(intent_plan)
    if validated_intent != expected_intent:
        raise ProvenanceContractError("Replay intent is not deterministic for the request.")
    if intent_reference(validated_intent) != validated_run["intent_reference"]:
        raise ProvenanceContractError("Replay intent does not resolve the recorded reference.")

    supplied_proposal = validate_evidence_backed_proposal(proposal, registry=registry)
    references = tuple(
        evidence_reference(registry.resolve(reference))
        for reference in _evidence_references(
            validated_run["evidence_references"], registry=registry
        )
    )
    replayed_proposal = create_evidence_backed_proposal(
        intent_plan=validated_intent,
        evidence_references=references,
        registry=registry,
    )
    if replayed_proposal != supplied_proposal:
        raise ProvenanceContractError("Replay proposal differs from the supplied immutable object.")
    if (
        proposal_identity(replayed_proposal, registry=registry)
        != validated_run["proposal_identity"]
    ):
        raise ProvenanceContractError("Replay proposal does not resolve the recorded identity.")

    return {
        "run_id": validated_run["run_id"],
        "status": "verified",
        "sequence": [
            validated_run["request_identity"],
            validated_run["intent_reference"]["sha256"],
            *[reference.evidence_id for reference in references],
            validated_run["proposal_identity"],
            validated_run["evaluation_reference"],
            validated_run["decision_record_reference"],
        ],
        "method": "deterministic-reference-replay",
        "boundary": "audit-verification-only",
    }

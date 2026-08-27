from __future__ import annotations

import hashlib
import json
import re
from typing import Literal, Mapping, cast

from agent_contracts.evidence import (
    EVIDENCE_REFERENCE_VERSION,
    EvidenceReference,
    EvidenceReferenceVersion,
    EvidenceRegistry,
    ReferencePurpose,
    create_evidence_backed_proposal,
    intent_reference,
    validate_evidence_backed_proposal,
    validate_evidence_reference,
)
from agent_contracts.intent_planning import (
    CONTRACT_VERSION as INTENT_CONTRACT_VERSION,
    plan_request,
    validate_intent_plan,
)


EvaluationVersion = Literal["nma.agent-evaluation/1.0"]
DecisionRecordVersion = Literal["nma.agent-decision-record/1.0"]

EVALUATION_VERSION: EvaluationVersion = "nma.agent-evaluation/1.0"
DECISION_RECORD_VERSION: DecisionRecordVersion = "nma.agent-decision-record/1.0"

DimensionResult = Literal["pass", "fail"]
EvaluationResult = Literal["satisfactory", "rejected"]
DomainReviewStatus = Literal["pending", "accepted", "rejected"]

EVALUATION_DIMENSIONS = (
    "intent_correctness",
    "evidence_completeness",
    "evidence_provenance_validity",
    "proposal_determinism",
    "unsupported_request_handling",
    "fail_closed_behavior",
    "reproducibility",
    "contract_compliance",
)

_SHA256 = r"[0-9a-f]{64}"
_REQUEST_ID = re.compile(rf"request:sha256:{_SHA256}")
_INTENT_ID = re.compile(rf"intent:sha256:{_SHA256}")
_EVIDENCE_ID = re.compile(rf"evidence:sha256:{_SHA256}")
_PROPOSAL_ID = re.compile(rf"proposal:sha256:{_SHA256}")
_EVALUATION_ID = re.compile(rf"evaluation:sha256:{_SHA256}")
_DECISION_RECORD_ID = re.compile(rf"decision-record:sha256:{_SHA256}")
_DOMAIN_DECISION_ID = re.compile(rf"review-decision:sha256:{_SHA256}")

_EVALUATION_FIELDS = frozenset(
    (
        "schema",
        "evaluation_id",
        "request_identity",
        "intent_reference",
        "evidence_references",
        "proposal_identity",
        "dimensions",
        "result",
        "review_requirement",
        "boundary",
        "provenance",
    )
)
_DECISION_RECORD_FIELDS = frozenset(
    (
        "schema",
        "decision_record_id",
        "request_identity",
        "intent_reference",
        "evidence_references",
        "proposal_identity",
        "evaluation_reference",
        "review",
        "boundary",
        "provenance",
    )
)
_INTENT_REFERENCE_FIELDS = frozenset(("contract", "sha256"))
_EVIDENCE_REFERENCE_FIELDS = frozenset(("schema", "evidence_id", "purpose"))
_EVALUATION_PROVENANCE_FIELDS = frozenset(("evaluator", "evaluated_at", "method"))
_DECISION_PROVENANCE_FIELDS = frozenset(("recorded_by", "recorded_at"))
_REVIEW_FIELDS = frozenset(("status", "reviewer", "domain_decision_reference"))
_REVIEW_STATUSES = frozenset(("pending", "accepted", "rejected"))


class GovernanceContractError(ValueError):
    """Evaluation or governance data violated the closed accountability-only boundary."""


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
        raise GovernanceContractError("Governance inputs must be canonical JSON values.") from error


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _bounded_text(value: object, *, field: str, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise GovernanceContractError(f"{field} must be a non-empty bounded string.")
    if any(ord(character) < 32 for character in value):
        raise GovernanceContractError(f"{field} must not contain control characters.")
    return value


def request_identity(request: str) -> str:
    exact_request = _bounded_text(request, field="request", maximum=500)
    return f"request:sha256:{_sha256_json({'request': exact_request})}"


def proposal_identity(proposal: Mapping[str, object], *, registry: EvidenceRegistry) -> str:
    validated = validate_evidence_backed_proposal(proposal, registry=registry)
    return f"proposal:sha256:{_sha256_json(validated)}"


def _evidence_references(
    value: object, *, registry: EvidenceRegistry
) -> tuple[EvidenceReference, ...]:
    if not isinstance(value, list) or not value:
        raise GovernanceContractError("Evidence references must be a non-empty list.")
    references: list[EvidenceReference] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) != _EVIDENCE_REFERENCE_FIELDS:
            raise GovernanceContractError(
                "Evidence references must use the exact closed field set."
            )
        if not all(isinstance(field, str) for field in item.values()):
            raise GovernanceContractError("Evidence reference fields must be strings.")
        reference = validate_evidence_reference(
            EvidenceReference(
                schema=cast(EvidenceReferenceVersion, item["schema"]),
                evidence_id=cast(str, item["evidence_id"]),
                purpose=cast(ReferencePurpose, item["purpose"]),
            )
        )
        if reference.schema != EVIDENCE_REFERENCE_VERSION or reference.purpose != "proposal":
            raise GovernanceContractError("Governance records preserve proposal evidence only.")
        if reference.evidence_id in seen:
            raise GovernanceContractError("Evidence references must be unique.")
        registry.resolve(reference)
        references.append(reference)
        seen.add(reference.evidence_id)
    return tuple(references)


def _intent_reference(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != _INTENT_REFERENCE_FIELDS:
        raise GovernanceContractError("Intent references must use the exact closed field set.")
    if value["contract"] != INTENT_CONTRACT_VERSION:
        raise GovernanceContractError("Unknown intent planning contract reference.")
    identity = value["sha256"]
    if not isinstance(identity, str) or _INTENT_ID.fullmatch(identity) is None:
        raise GovernanceContractError("Intent reference identity is malformed.")
    return {"contract": INTENT_CONTRACT_VERSION, "sha256": identity}


def _validate_review(value: object) -> dict[str, str | None]:
    if not isinstance(value, Mapping) or set(value) != _REVIEW_FIELDS:
        raise GovernanceContractError("Review records must use the exact closed field set.")
    status = value["status"]
    reviewer = value["reviewer"]
    decision_reference = value["domain_decision_reference"]
    if status not in _REVIEW_STATUSES:
        raise GovernanceContractError("Unknown human/domain review status.")
    if status == "pending":
        if reviewer is not None or decision_reference is not None:
            raise GovernanceContractError("Pending review cannot name a reviewer or decision.")
    else:
        reviewer = _bounded_text(reviewer, field="reviewer")
        if (
            not isinstance(decision_reference, str)
            or _DOMAIN_DECISION_ID.fullmatch(decision_reference) is None
        ):
            raise GovernanceContractError("Completed review requires a bounded decision reference.")
    return {
        "status": cast(str, status),
        "reviewer": cast(str | None, reviewer),
        "domain_decision_reference": cast(str | None, decision_reference),
    }


def evaluate_proposal(
    *,
    request: str,
    intent_plan: Mapping[str, object],
    proposal: Mapping[str, object],
    registry: EvidenceRegistry,
    evaluator: str,
    evaluated_at: str,
) -> dict[str, object]:
    """Evaluate proposal quality and return no execution or authorization capability.

    Invalid inputs raise instead of producing a partially successful record. Evidence must already
    be reviewed or validated; that quality gate still cannot replace human/domain review.
    """

    expected_intent = plan_request(_bounded_text(request, field="request", maximum=500))
    validated_intent = validate_intent_plan(intent_plan)
    if validated_intent != expected_intent:
        raise GovernanceContractError(
            "Intent plan is not the deterministic result for the request."
        )
    if validated_intent["disposition"] != "proposal":
        raise GovernanceContractError("Unsupported or abstained requests cannot produce proposals.")

    validated_proposal = validate_evidence_backed_proposal(proposal, registry=registry)
    references = _evidence_references(validated_proposal["evidence_references"], registry=registry)
    for reference in references:
        evidence = registry.resolve(reference)
        if evidence.review.status == "unreviewed":
            raise GovernanceContractError("Unreviewed evidence cannot satisfy proposal evaluation.")

    rebuilt = create_evidence_backed_proposal(
        intent_plan=validated_intent,
        evidence_references=references,
        registry=registry,
    )
    if rebuilt != validated_proposal:
        raise GovernanceContractError("Proposal is not reproducible from its plan and evidence.")

    body: dict[str, object] = {
        "schema": EVALUATION_VERSION,
        "request_identity": request_identity(request),
        "intent_reference": intent_reference(validated_intent),
        "evidence_references": [reference.to_dict() for reference in references],
        "proposal_identity": proposal_identity(validated_proposal, registry=registry),
        "dimensions": {dimension: "pass" for dimension in EVALUATION_DIMENSIONS},
        "result": "satisfactory",
        "review_requirement": "human-domain-review-required",
        "boundary": "proposal-quality-only",
        "provenance": {
            "evaluator": _bounded_text(evaluator, field="evaluator"),
            "evaluated_at": _bounded_text(evaluated_at, field="evaluation timestamp"),
            "method": "deterministic-contract-validation",
        },
    }
    record = {
        **body,
        "evaluation_id": f"evaluation:sha256:{_sha256_json(body)}",
    }
    return validate_evaluation_record(record, registry=registry)


def validate_evaluation_record(
    value: Mapping[str, object], *, registry: EvidenceRegistry
) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != _EVALUATION_FIELDS:
        raise GovernanceContractError("Evaluation records must use the exact closed field set.")
    if value["schema"] != EVALUATION_VERSION:
        raise GovernanceContractError("Unsupported evaluation record version.")
    evaluation_id = value["evaluation_id"]
    if not isinstance(evaluation_id, str) or _EVALUATION_ID.fullmatch(evaluation_id) is None:
        raise GovernanceContractError("Evaluation identity is malformed.")
    request_id = value["request_identity"]
    if not isinstance(request_id, str) or _REQUEST_ID.fullmatch(request_id) is None:
        raise GovernanceContractError("Request identity is malformed.")
    intent = _intent_reference(value["intent_reference"])
    references = _evidence_references(value["evidence_references"], registry=registry)
    proposal_id = value["proposal_identity"]
    if not isinstance(proposal_id, str) or _PROPOSAL_ID.fullmatch(proposal_id) is None:
        raise GovernanceContractError("Proposal identity is malformed.")
    dimensions = value["dimensions"]
    if not isinstance(dimensions, Mapping) or set(dimensions) != set(EVALUATION_DIMENSIONS):
        raise GovernanceContractError("Evaluation dimensions must use the exact closed field set.")
    if any(result not in {"pass", "fail"} for result in dimensions.values()):
        raise GovernanceContractError("Evaluation dimensions must be pass or fail.")
    result = value["result"]
    if result not in {"satisfactory", "rejected"}:
        raise GovernanceContractError("Unknown proposal-quality result.")
    all_pass = all(item == "pass" for item in dimensions.values())
    if (result == "satisfactory") != all_pass:
        raise GovernanceContractError("Evaluation result must agree with every quality dimension.")
    if value["review_requirement"] != "human-domain-review-required":
        raise GovernanceContractError("Evaluation cannot bypass human/domain review.")
    if value["boundary"] != "proposal-quality-only":
        raise GovernanceContractError("Evaluation cannot confer execution authority.")
    provenance = value["provenance"]
    if not isinstance(provenance, Mapping) or set(provenance) != _EVALUATION_PROVENANCE_FIELDS:
        raise GovernanceContractError("Evaluation provenance must use the exact closed field set.")
    _bounded_text(provenance["evaluator"], field="evaluator")
    _bounded_text(provenance["evaluated_at"], field="evaluation timestamp")
    if provenance["method"] != "deterministic-contract-validation":
        raise GovernanceContractError("Unknown evaluation method.")

    normalized: dict[str, object] = {
        "schema": EVALUATION_VERSION,
        "request_identity": request_id,
        "intent_reference": intent,
        "evidence_references": [reference.to_dict() for reference in references],
        "proposal_identity": proposal_id,
        "dimensions": dict(dimensions),
        "result": result,
        "review_requirement": "human-domain-review-required",
        "boundary": "proposal-quality-only",
        "provenance": dict(provenance),
    }
    expected_id = f"evaluation:sha256:{_sha256_json(normalized)}"
    if evaluation_id != expected_id:
        raise GovernanceContractError("Evaluation identity does not match its record content.")
    return {**normalized, "evaluation_id": evaluation_id}


def create_decision_record(
    *,
    request: str,
    intent_plan: Mapping[str, object],
    proposal: Mapping[str, object],
    evaluation: Mapping[str, object],
    registry: EvidenceRegistry,
    review_status: DomainReviewStatus,
    reviewer: str | None,
    domain_decision_reference: str | None,
    recorded_by: str,
    recorded_at: str,
) -> dict[str, object]:
    """Create an accountability record that grants no authorization or mutation capability."""

    validated_intent = validate_intent_plan(intent_plan)
    validated_proposal = validate_evidence_backed_proposal(proposal, registry=registry)
    validated_evaluation = validate_evaluation_record(evaluation, registry=registry)
    references = _evidence_references(validated_proposal["evidence_references"], registry=registry)
    expected_request = request_identity(request)
    expected_intent = intent_reference(validated_intent)
    expected_proposal = proposal_identity(validated_proposal, registry=registry)
    expected_evidence = [reference.to_dict() for reference in references]
    if validated_evaluation["request_identity"] != expected_request:
        raise GovernanceContractError("Evaluation does not reference the decision request.")
    if validated_evaluation["intent_reference"] != expected_intent:
        raise GovernanceContractError("Evaluation does not reference the decision intent plan.")
    if validated_evaluation["proposal_identity"] != expected_proposal:
        raise GovernanceContractError("Evaluation does not reference the decision proposal.")
    if validated_evaluation["evidence_references"] != expected_evidence:
        raise GovernanceContractError("Evaluation does not preserve decision evidence references.")

    review = _validate_review(
        {
            "status": review_status,
            "reviewer": reviewer,
            "domain_decision_reference": domain_decision_reference,
        }
    )
    body: dict[str, object] = {
        "schema": DECISION_RECORD_VERSION,
        "request_identity": expected_request,
        "intent_reference": expected_intent,
        "evidence_references": expected_evidence,
        "proposal_identity": expected_proposal,
        "evaluation_reference": validated_evaluation["evaluation_id"],
        "review": review,
        "boundary": "accountability-only",
        "provenance": {
            "recorded_by": _bounded_text(recorded_by, field="decision recorder"),
            "recorded_at": _bounded_text(recorded_at, field="decision record timestamp"),
        },
    }
    record = {
        **body,
        "decision_record_id": f"decision-record:sha256:{_sha256_json(body)}",
    }
    return validate_decision_record(record, evaluation=evaluation, registry=registry)


def validate_decision_record(
    value: Mapping[str, object],
    *,
    evaluation: Mapping[str, object],
    registry: EvidenceRegistry,
) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != _DECISION_RECORD_FIELDS:
        raise GovernanceContractError("Decision records must use the exact closed field set.")
    if value["schema"] != DECISION_RECORD_VERSION:
        raise GovernanceContractError("Unsupported decision record version.")
    record_id = value["decision_record_id"]
    if not isinstance(record_id, str) or _DECISION_RECORD_ID.fullmatch(record_id) is None:
        raise GovernanceContractError("Decision record identity is malformed.")
    request_id = value["request_identity"]
    if not isinstance(request_id, str) or _REQUEST_ID.fullmatch(request_id) is None:
        raise GovernanceContractError("Decision request identity is malformed.")
    intent = _intent_reference(value["intent_reference"])
    references = _evidence_references(value["evidence_references"], registry=registry)
    proposal_id = value["proposal_identity"]
    if not isinstance(proposal_id, str) or _PROPOSAL_ID.fullmatch(proposal_id) is None:
        raise GovernanceContractError("Decision proposal identity is malformed.")
    evaluation_reference = value["evaluation_reference"]
    if (
        not isinstance(evaluation_reference, str)
        or _EVALUATION_ID.fullmatch(evaluation_reference) is None
    ):
        raise GovernanceContractError("Decision evaluation reference is malformed.")
    validated_evaluation = validate_evaluation_record(evaluation, registry=registry)
    if evaluation_reference != validated_evaluation["evaluation_id"]:
        raise GovernanceContractError("Decision record does not link the supplied evaluation.")
    if request_id != validated_evaluation["request_identity"]:
        raise GovernanceContractError("Decision record request linkage is inconsistent.")
    if intent != validated_evaluation["intent_reference"]:
        raise GovernanceContractError("Decision record intent linkage is inconsistent.")
    if proposal_id != validated_evaluation["proposal_identity"]:
        raise GovernanceContractError("Decision record proposal linkage is inconsistent.")
    evidence = [reference.to_dict() for reference in references]
    if evidence != validated_evaluation["evidence_references"]:
        raise GovernanceContractError("Decision record evidence linkage is inconsistent.")
    review = _validate_review(value["review"])
    if value["boundary"] != "accountability-only":
        raise GovernanceContractError("Decision records cannot confer authority.")
    provenance = value["provenance"]
    if not isinstance(provenance, Mapping) or set(provenance) != _DECISION_PROVENANCE_FIELDS:
        raise GovernanceContractError("Decision provenance must use the exact closed field set.")
    _bounded_text(provenance["recorded_by"], field="decision recorder")
    _bounded_text(provenance["recorded_at"], field="decision record timestamp")

    normalized: dict[str, object] = {
        "schema": DECISION_RECORD_VERSION,
        "request_identity": request_id,
        "intent_reference": intent,
        "evidence_references": evidence,
        "proposal_identity": proposal_id,
        "evaluation_reference": evaluation_reference,
        "review": review,
        "boundary": "accountability-only",
        "provenance": dict(provenance),
    }
    expected_id = f"decision-record:sha256:{_sha256_json(normalized)}"
    if record_id != expected_id:
        raise GovernanceContractError("Decision record identity does not match its content.")
    return {**normalized, "decision_record_id": record_id}


def domain_review_reference(decision_payload: object) -> str:
    """Create a non-authorizing identity for an externally owned review decision."""

    return f"review-decision:sha256:{_sha256_json(decision_payload)}"

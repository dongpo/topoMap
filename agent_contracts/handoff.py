from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
from typing import Mapping

from agent_contracts.evidence import (
    EVIDENCE_PROPOSAL_VERSION,
    EVIDENCE_REFERENCE_VERSION,
    EvidenceRegistry,
    validate_evidence_backed_proposal,
)
from agent_contracts.governance import (
    DECISION_RECORD_VERSION,
    EVALUATION_VERSION,
    proposal_identity,
    validate_decision_record,
    validate_evaluation_record,
)
from agent_contracts.intent_planning import CONTRACT_VERSION as INTENT_CONTRACT_VERSION
from agent_contracts.provenance import (
    PRODUCTION_RUNTIME_VERSION,
    RUN_RECORD_VERSION,
    validate_agent_run_record,
)


HANDOFF_VERSION = "nma.authorization-handoff-request/1.0"

CLOSED_TARGETS = {
    "road": {
        "operation_class": "derived-road-centreline-portrayal",
        "authorization_contract": "nma.road-execution-authorization/1.0",
    },
    "school-hero": {
        "operation_class": "school-symbol-derived-layer-portrayal",
        "authorization_contract": "nma.symbol-edit-authorization/1.0",
    },
}

_HANDOFF_ID = re.compile(r"authorization-handoff:sha256:[0-9a-f]{64}")
_PROPOSAL_ID = re.compile(r"proposal:sha256:[0-9a-f]{64}")
_EVALUATION_ID = re.compile(r"evaluation:sha256:[0-9a-f]{64}")
_DECISION_ID = re.compile(r"decision-record:sha256:[0-9a-f]{64}")
_RUN_ID = re.compile(r"agent-run:sha256:[0-9a-f]{64}")
_REPLAY_ID = re.compile(r"handoff-replay:sha256:[0-9a-f]{64}")
_UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

_HANDOFF_FIELDS = frozenset(
    (
        "schema",
        "handoff_id",
        "target",
        "proposal_reference",
        "evaluation_reference",
        "decision_record_reference",
        "run_record_reference",
        "evidence_references",
        "domain_authorization_reference",
        "replay",
        "versions",
        "boundary",
        "provenance",
    )
)
_TARGET_FIELDS = frozenset(("domain", "operation_class", "authorization_contract"))
_EVIDENCE_REFERENCE_FIELDS = frozenset(("schema", "evidence_id", "purpose"))
_REPLAY_FIELDS = frozenset(("handoff_key", "duplicate_effect", "domain_idempotency"))
_VERSION_FIELDS = frozenset(
    (
        "production_runtime",
        "intent_planning",
        "evidence_reference",
        "proposal",
        "evaluation",
        "decision_record",
        "run_record",
        "handoff",
    )
)
_PROVENANCE_FIELDS = frozenset(("recorded_by", "recorded_at"))

_VERSIONS = {
    "production_runtime": PRODUCTION_RUNTIME_VERSION,
    "intent_planning": INTENT_CONTRACT_VERSION,
    "evidence_reference": EVIDENCE_REFERENCE_VERSION,
    "proposal": EVIDENCE_PROPOSAL_VERSION,
    "evaluation": EVALUATION_VERSION,
    "decision_record": DECISION_RECORD_VERSION,
    "run_record": RUN_RECORD_VERSION,
    "handoff": HANDOFF_VERSION,
}
_REPLAY_CONSTANTS = {
    "duplicate_effect": "same-request-no-new-authority",
    "domain_idempotency": "external-domain-owned",
}


class AuthorizationHandoffError(ValueError):
    """An Agent handoff violated the closed, non-authoritative boundary."""


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
        raise AuthorizationHandoffError(
            "Authorization handoffs must contain canonical JSON values."
        ) from error


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _identity(value: object, *, field: str, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise AuthorizationHandoffError(f"{field} is malformed.")
    return value


def _bounded_text(value: object, *, field: str, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise AuthorizationHandoffError(f"{field} must be a non-empty bounded string.")
    if any(ord(character) < 32 for character in value):
        raise AuthorizationHandoffError(f"{field} must not contain control characters.")
    return value


def _timestamp(value: object, *, field: str) -> str:
    if not isinstance(value, str) or _UTC_TIMESTAMP.fullmatch(value) is None:
        raise AuthorizationHandoffError(f"{field} must be an explicit UTC second timestamp.")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise AuthorizationHandoffError(f"{field} is not a valid timestamp.") from error
    return value


def _target(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != _TARGET_FIELDS:
        raise AuthorizationHandoffError("Handoff targets must use the exact closed field set.")
    domain = value["domain"]
    if not isinstance(domain, str) or domain not in CLOSED_TARGETS:
        raise AuthorizationHandoffError("Unknown authorization handoff target domain.")
    expected = CLOSED_TARGETS[domain]
    if value["operation_class"] != expected["operation_class"]:
        raise AuthorizationHandoffError("Unknown or mismatched authorization operation class.")
    if value["authorization_contract"] != expected["authorization_contract"]:
        raise AuthorizationHandoffError("Target authorization contract linkage is invalid.")
    return {"domain": domain, **expected}


def _evidence_references(value: object, *, registry: EvidenceRegistry) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise AuthorizationHandoffError("Handoff evidence references must be a non-empty list.")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) != _EVIDENCE_REFERENCE_FIELDS:
            raise AuthorizationHandoffError(
                "Handoff evidence references must use the exact closed field set."
            )
        if (
            item["schema"] != EVIDENCE_REFERENCE_VERSION
            or item["purpose"] != "proposal"
            or not isinstance(item["evidence_id"], str)
        ):
            raise AuthorizationHandoffError("Handoff evidence linkage is invalid.")
        evidence_id = item["evidence_id"]
        if evidence_id in seen:
            raise AuthorizationHandoffError("Handoff evidence references must be unique.")
        normalized.append(
            {
                "schema": EVIDENCE_REFERENCE_VERSION,
                "evidence_id": evidence_id,
                "purpose": "proposal",
            }
        )
        seen.add(evidence_id)
    return normalized


def _validated_chain(
    *,
    proposal: Mapping[str, object],
    evaluation: Mapping[str, object],
    decision_record: Mapping[str, object],
    run_record: Mapping[str, object],
    registry: EvidenceRegistry,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    validated_proposal = validate_evidence_backed_proposal(proposal, registry=registry)
    validated_evaluation = validate_evaluation_record(evaluation, registry=registry)
    validated_decision = validate_decision_record(
        decision_record, evaluation=validated_evaluation, registry=registry
    )
    validated_run = validate_agent_run_record(
        run_record,
        evaluation=validated_evaluation,
        decision_record=validated_decision,
        registry=registry,
    )
    expected_proposal = proposal_identity(validated_proposal, registry=registry)
    expected_evidence = validated_proposal["evidence_references"]
    for actual, expected, label in (
        (validated_evaluation["proposal_identity"], expected_proposal, "evaluation proposal"),
        (validated_decision["proposal_identity"], expected_proposal, "decision proposal"),
        (validated_run["proposal_identity"], expected_proposal, "run proposal"),
        (validated_evaluation["evidence_references"], expected_evidence, "evaluation evidence"),
        (validated_decision["evidence_references"], expected_evidence, "decision evidence"),
        (validated_run["evidence_references"], expected_evidence, "run evidence"),
    ):
        if actual != expected:
            raise AuthorizationHandoffError(f"Handoff {label} linkage is stale or mismatched.")
    if validated_evaluation["result"] != "satisfactory":
        raise AuthorizationHandoffError("Rejected proposal quality cannot enter handoff.")
    review = validated_decision["review"]
    if not isinstance(review, Mapping) or review["status"] != "accepted":
        raise AuthorizationHandoffError(
            "Only an accepted accountability decision may be handed off."
        )
    return validated_proposal, validated_evaluation, validated_decision, validated_run


def _replay_key(
    *,
    target: Mapping[str, str],
    proposal_reference: str,
    evaluation_reference: str,
    decision_record_reference: str,
    run_record_reference: str,
    evidence_references: list[dict[str, str]],
) -> str:
    basis = {
        "schema": HANDOFF_VERSION,
        "target": dict(target),
        "proposal_reference": proposal_reference,
        "evaluation_reference": evaluation_reference,
        "decision_record_reference": decision_record_reference,
        "run_record_reference": run_record_reference,
        "evidence_references": evidence_references,
    }
    return f"handoff-replay:sha256:{_sha256_json(basis)}"


def create_authorization_handoff_request(
    *,
    target_domain: str,
    operation_class: str,
    proposal: Mapping[str, object],
    evaluation: Mapping[str, object],
    decision_record: Mapping[str, object],
    run_record: Mapping[str, object],
    registry: EvidenceRegistry,
    recorded_by: str,
    recorded_at: str,
) -> dict[str, object]:
    """Create a validation request that is incapable of carrying domain authorization."""

    target = _target(
        {
            "domain": target_domain,
            "operation_class": operation_class,
            "authorization_contract": CLOSED_TARGETS.get(target_domain, {}).get(
                "authorization_contract"
            ),
        }
    )
    validated_proposal, validated_evaluation, validated_decision, validated_run = _validated_chain(
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision_record,
        run_record=run_record,
        registry=registry,
    )
    references = _evidence_references(validated_proposal["evidence_references"], registry=registry)
    proposal_reference = proposal_identity(validated_proposal, registry=registry)
    evaluation_reference = str(validated_evaluation["evaluation_id"])
    decision_reference = str(validated_decision["decision_record_id"])
    run_reference = str(validated_run["run_id"])
    replay = {
        "handoff_key": _replay_key(
            target=target,
            proposal_reference=proposal_reference,
            evaluation_reference=evaluation_reference,
            decision_record_reference=decision_reference,
            run_record_reference=run_reference,
            evidence_references=references,
        ),
        **_REPLAY_CONSTANTS,
    }
    timestamp = _timestamp(recorded_at, field="handoff record timestamp")
    run_recorded_at = validated_run["provenance"]["recorded_at"]
    if timestamp < run_recorded_at:
        raise AuthorizationHandoffError("Handoff cannot precede the linked run record.")
    body: dict[str, object] = {
        "schema": HANDOFF_VERSION,
        "target": target,
        "proposal_reference": proposal_reference,
        "evaluation_reference": evaluation_reference,
        "decision_record_reference": decision_reference,
        "run_record_reference": run_reference,
        "evidence_references": references,
        "domain_authorization_reference": None,
        "replay": replay,
        "versions": dict(_VERSIONS),
        "boundary": "domain-validation-request-only",
        "provenance": {
            "recorded_by": _bounded_text(recorded_by, field="handoff recorder"),
            "recorded_at": timestamp,
        },
    }
    request = {
        **body,
        "handoff_id": f"authorization-handoff:sha256:{_sha256_json(body)}",
    }
    return validate_authorization_handoff_request(
        request,
        proposal=validated_proposal,
        evaluation=validated_evaluation,
        decision_record=validated_decision,
        run_record=validated_run,
        registry=registry,
    )


def validate_authorization_handoff_request(
    value: Mapping[str, object],
    *,
    proposal: Mapping[str, object],
    evaluation: Mapping[str, object],
    decision_record: Mapping[str, object],
    run_record: Mapping[str, object],
    registry: EvidenceRegistry,
) -> dict[str, object]:
    """Validate governance linkage; never validate, consume, or execute domain authority."""

    if not isinstance(value, Mapping) or set(value) != _HANDOFF_FIELDS:
        raise AuthorizationHandoffError("Handoff requests must use the exact closed field set.")
    if value["schema"] != HANDOFF_VERSION:
        raise AuthorizationHandoffError("Unsupported authorization handoff version.")
    handoff_id = _identity(value["handoff_id"], field="handoff identity", pattern=_HANDOFF_ID)
    target = _target(value["target"])
    validated_proposal, validated_evaluation, validated_decision, validated_run = _validated_chain(
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision_record,
        run_record=run_record,
        registry=registry,
    )
    proposal_reference = _identity(
        value["proposal_reference"], field="proposal reference", pattern=_PROPOSAL_ID
    )
    evaluation_reference = _identity(
        value["evaluation_reference"], field="evaluation reference", pattern=_EVALUATION_ID
    )
    decision_reference = _identity(
        value["decision_record_reference"],
        field="decision record reference",
        pattern=_DECISION_ID,
    )
    run_reference = _identity(
        value["run_record_reference"], field="run record reference", pattern=_RUN_ID
    )
    references = _evidence_references(value["evidence_references"], registry=registry)
    expected_links = (
        (
            proposal_reference,
            proposal_identity(validated_proposal, registry=registry),
            "proposal",
        ),
        (evaluation_reference, validated_evaluation["evaluation_id"], "evaluation"),
        (decision_reference, validated_decision["decision_record_id"], "decision record"),
        (run_reference, validated_run["run_id"], "run record"),
        (references, validated_proposal["evidence_references"], "evidence set"),
    )
    for actual, expected, label in expected_links:
        if actual != expected:
            raise AuthorizationHandoffError(f"Handoff {label} linkage is stale or mismatched.")

    if value["domain_authorization_reference"] is not None:
        raise AuthorizationHandoffError(
            "Agent handoffs cannot carry or mint a domain authorization reference."
        )
    replay = value["replay"]
    if not isinstance(replay, Mapping) or set(replay) != _REPLAY_FIELDS:
        raise AuthorizationHandoffError("Handoff replay metadata must use the closed field set.")
    handoff_key = _identity(replay["handoff_key"], field="handoff replay key", pattern=_REPLAY_ID)
    expected_key = _replay_key(
        target=target,
        proposal_reference=proposal_reference,
        evaluation_reference=evaluation_reference,
        decision_record_reference=decision_reference,
        run_record_reference=run_reference,
        evidence_references=references,
    )
    if handoff_key != expected_key or any(
        replay[field] != expected for field, expected in _REPLAY_CONSTANTS.items()
    ):
        raise AuthorizationHandoffError("Handoff replay or idempotency linkage is invalid.")
    versions = value["versions"]
    if (
        not isinstance(versions, Mapping)
        or set(versions) != _VERSION_FIELDS
        or dict(versions) != _VERSIONS
    ):
        raise AuthorizationHandoffError("Handoff version linkage is not canonical.")
    if value["boundary"] != "domain-validation-request-only":
        raise AuthorizationHandoffError("Handoff requests cannot confer execution authority.")
    provenance = value["provenance"]
    if not isinstance(provenance, Mapping) or set(provenance) != _PROVENANCE_FIELDS:
        raise AuthorizationHandoffError("Handoff provenance must use the exact closed field set.")
    recorder = _bounded_text(provenance["recorded_by"], field="handoff recorder")
    recorded_at = _timestamp(provenance["recorded_at"], field="handoff record timestamp")
    if recorded_at < validated_run["provenance"]["recorded_at"]:
        raise AuthorizationHandoffError("Handoff cannot precede the linked run record.")

    normalized: dict[str, object] = {
        "schema": HANDOFF_VERSION,
        "target": target,
        "proposal_reference": proposal_reference,
        "evaluation_reference": evaluation_reference,
        "decision_record_reference": decision_reference,
        "run_record_reference": run_reference,
        "evidence_references": references,
        "domain_authorization_reference": None,
        "replay": {"handoff_key": handoff_key, **_REPLAY_CONSTANTS},
        "versions": dict(_VERSIONS),
        "boundary": "domain-validation-request-only",
        "provenance": {"recorded_by": recorder, "recorded_at": recorded_at},
    }
    expected_id = f"authorization-handoff:sha256:{_sha256_json(normalized)}"
    if handoff_id != expected_id:
        raise AuthorizationHandoffError("Handoff identity does not match its content.")
    return {**normalized, "handoff_id": handoff_id}


def handoff_boundary_state(
    value: Mapping[str, object],
    *,
    proposal: Mapping[str, object],
    evaluation: Mapping[str, object],
    decision_record: Mapping[str, object],
    run_record: Mapping[str, object],
    registry: EvidenceRegistry,
) -> dict[str, object]:
    """Return the only AGENT-06 outcome: validated request, still ineligible to execute."""

    validated = validate_authorization_handoff_request(
        value,
        proposal=proposal,
        evaluation=evaluation,
        decision_record=decision_record,
        run_record=run_record,
        registry=registry,
    )
    return {
        "handoff_id": validated["handoff_id"],
        "state": "requires-domain-authorization-validation",
        "execution_eligible": False,
        "authority_source": "external-domain-owned",
        "boundary": "non-executing",
    }

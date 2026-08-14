from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal, TypedDict


SchemaVersion = Literal["nma.intent-plan/0.5"]
INTENT_PLAN_SCHEMA: SchemaVersion = "nma.intent-plan/0.5"

IntentKind = Literal[
    "retrieve_information",
    "modify_portrayal",
    "unsupported_request",
]
OperationKind = Literal[
    "retrieve_rule",
    "change_color",
    "modify_portrayal",
    "create_official_feature",
    "unsupported",
]
TargetKind = Literal["official_portrayal", "derived_symbol", "unspecified"]


class FeaturePayload(TypedDict):
    code: str | None


class OperationPayload(TypedDict):
    type: OperationKind


class IntentPlanPayload(TypedDict):
    schema: SchemaVersion
    intent: IntentKind
    feature: FeaturePayload
    operation: OperationPayload
    target: TargetKind
    constraints: list[str]
    evidence_required: Literal[True]
    approval_required: bool
    immutable: Literal[True]


INTENT_PLAN_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "schema": {"type": "string", "const": INTENT_PLAN_SCHEMA},
        "intent": {
            "type": "string",
            "enum": [
                "retrieve_information",
                "modify_portrayal",
                "unsupported_request",
            ],
        },
        "feature": {
            "type": "object",
            "properties": {"code": {"type": ["string", "null"]}},
            "required": ["code"],
            "additionalProperties": False,
        },
        "operation": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [
                        "retrieve_rule",
                        "change_color",
                        "modify_portrayal",
                        "create_official_feature",
                        "unsupported",
                    ],
                }
            },
            "required": ["type"],
            "additionalProperties": False,
        },
        "target": {
            "type": "string",
            "enum": ["official_portrayal", "derived_symbol", "unspecified"],
        },
        "constraints": {"type": "array", "items": {"type": "string"}},
        "evidence_required": {"type": "boolean", "const": True},
        "approval_required": {"type": "boolean"},
        "immutable": {"type": "boolean", "const": True},
    },
    "required": [
        "schema",
        "intent",
        "feature",
        "operation",
        "target",
        "constraints",
        "evidence_required",
        "approval_required",
        "immutable",
    ],
    "additionalProperties": False,
}


class IntentPlanningError(ValueError):
    """The request or plan violated the bounded HERO-01 planning contract."""


@dataclass(frozen=True)
class FeatureReference:
    code: str | None

    def to_payload(self) -> FeaturePayload:
        return {"code": self.code}


@dataclass(frozen=True)
class PlannedOperation:
    type: OperationKind

    def to_payload(self) -> OperationPayload:
        return {"type": self.type}


@dataclass(frozen=True)
class IntentPlan:
    intent: IntentKind
    feature: FeatureReference
    operation: PlannedOperation
    target: TargetKind
    constraints: tuple[str, ...]
    evidence_required: Literal[True] = True
    approval_required: bool = False
    immutable: Literal[True] = True
    schema: SchemaVersion = INTENT_PLAN_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != INTENT_PLAN_SCHEMA:
            raise IntentPlanningError("Unsupported intent-plan schema version.")
        if not self.evidence_required:
            raise IntentPlanningError("Every intent decision requires evidence.")
        if not self.immutable:
            raise IntentPlanningError("Official portrayal must remain immutable.")
        if self.intent == "modify_portrayal" and not self.approval_required:
            raise IntentPlanningError("Portrayal modification requires approval.")
        if self.intent == "modify_portrayal" and self.target != "derived_symbol":
            raise IntentPlanningError("Portrayal modification may target only a derived symbol.")
        if "no_execution" not in self.constraints:
            raise IntentPlanningError("Every HERO-01 plan must prohibit execution.")

    def to_payload(self) -> IntentPlanPayload:
        return {
            "schema": self.schema,
            "intent": self.intent,
            "feature": self.feature.to_payload(),
            "operation": self.operation.to_payload(),
            "target": self.target,
            "constraints": list(self.constraints),
            "evidence_required": self.evidence_required,
            "approval_required": self.approval_required,
            "immutable": self.immutable,
        }


_FEATURE_CODE = re.compile(r"(?<!\d)(\d{7})(?!\d)")
_MODIFICATION_TERMS = ("change", "modify", "update", "recolor", "recolour", "set color")
_INFORMATION_TERMS = ("what is", "where is", "show", "find", "explain", "which")
_OFFICIAL_CREATION_TERMS = ("create", "add", "invent", "define")


def _feature_reference(normalized_request: str) -> FeatureReference:
    match = _FEATURE_CODE.search(normalized_request)
    if match:
        return FeatureReference(code=match.group(1))
    if "school" in normalized_request:
        return FeatureReference(code="9920103")
    return FeatureReference(code=None)


def _is_official_creation(normalized_request: str) -> bool:
    creates = any(term in normalized_request for term in _OFFICIAL_CREATION_TERMS)
    official_target = "official" in normalized_request and any(
        term in normalized_request for term in ("feature", "symbol", "portrayal")
    )
    return creates and official_target


def _is_modification(normalized_request: str) -> bool:
    return any(term in normalized_request for term in _MODIFICATION_TERMS) and any(
        term in normalized_request for term in ("symbol", "portrayal", "color", "colour")
    )


def _is_information_request(normalized_request: str) -> bool:
    asks = normalized_request.endswith("?") or any(
        term in normalized_request for term in _INFORMATION_TERMS
    )
    subject = any(
        term in normalized_request for term in ("rule", "symbol", "portrayal", "feature")
    )
    return asks and subject


def plan_intent(request: str) -> IntentPlanPayload:
    """Classify one request and return a validated, non-executing action plan."""

    if not isinstance(request, str) or not request.strip():
        raise IntentPlanningError("Intent planning requires a non-empty request.")
    if len(request) > 500:
        raise IntentPlanningError("Intent planning requests are limited to 500 characters.")

    normalized = " ".join(request.casefold().split())
    feature = _feature_reference(normalized)

    if _is_official_creation(normalized):
        plan = IntentPlan(
            intent="unsupported_request",
            feature=feature,
            operation=PlannedOperation(type="create_official_feature"),
            target="official_portrayal",
            constraints=(
                "unsupported_operation",
                "official_portrayal_immutable",
                "no_execution",
            ),
            approval_required=True,
        )
    elif _is_modification(normalized):
        operation: OperationKind = (
            "change_color"
            if "color" in normalized or "colour" in normalized
            else "modify_portrayal"
        )
        plan = IntentPlan(
            intent="modify_portrayal",
            feature=feature,
            operation=PlannedOperation(type=operation),
            target="derived_symbol",
            constraints=(
                "derived_artifact_only",
                "official_portrayal_immutable",
                "no_execution",
            ),
            approval_required=True,
        )
    elif _is_information_request(normalized):
        plan = IntentPlan(
            intent="retrieve_information",
            feature=feature,
            operation=PlannedOperation(type="retrieve_rule"),
            target="official_portrayal",
            constraints=("read_only", "official_portrayal_immutable", "no_execution"),
        )
    else:
        plan = IntentPlan(
            intent="unsupported_request",
            feature=feature,
            operation=PlannedOperation(type="unsupported"),
            target="unspecified",
            constraints=(
                "unsupported_operation",
                "official_portrayal_immutable",
                "no_execution",
            ),
        )

    return plan.to_payload()

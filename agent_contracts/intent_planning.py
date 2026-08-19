from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal, Mapping, TypedDict, cast


ContractVersion = Literal["nma.intent-planning/1.0"]
CONTRACT_VERSION: ContractVersion = "nma.intent-planning/1.0"

# AGENT-02 disposition registry.  The historical module stays byte-identical because frozen
# HERO-05 lineage records consume its nma.intent-plan/0.5 payload.  It is not a shared planner.
V05_PLANNER_DISPOSITION = "deprecated"
V05_REPLACEMENT_CONTRACT = CONTRACT_VERSION
V05_REPLACEMENT_OWNER = "agent_contracts.intent_planning.plan_request"

Boundary = Literal["canonical-production", "retained-demo"]
RouteKind = Literal["present_evidence", "propose_portrayal_preview", "abstain"]
Disposition = Literal["proposal", "abstention"]
DisplayIntent = Literal["evidence_panel", "portrayal_preview", "none"]
EvidenceIntent = Literal["required", "none"]
ReasonCode = Literal[
    "supported_evidence_request",
    "supported_portrayal_request",
    "unsupported_request",
    "ambiguous_request",
    "missing_feature_context",
    "downstream_state_transition",
]

PRODUCTION_ROUTE_KINDS: tuple[RouteKind, ...] = (
    "present_evidence",
    "propose_portrayal_preview",
    "abstain",
)
RETAINED_DEMO_ROUTE_KINDS = (
    "inspect_feature",
    "propose_style_revision",
    "approve_revision",
    "discard_revision",
    "finish_revisions",
    "request_layer_confirmation",
    "reset_session",
    "abstain",
)


class IntentPlanPayload(TypedDict):
    schema: ContractVersion
    boundary: Boundary
    route_kind: RouteKind
    disposition: Disposition
    feature_code: str | None
    display_intent: DisplayIntent
    evidence_intent: EvidenceIntent
    reason_code: ReasonCode


class IntentPlanningError(ValueError):
    """An input or output violated the closed intent/planning contract."""


@dataclass(frozen=True)
class FeatureVocabulary:
    code: str
    terms: tuple[str, ...]

    def __post_init__(self) -> None:
        if not re.fullmatch(r"\d{7}", self.code):
            raise IntentPlanningError("Feature codes must contain exactly seven digits.")
        if not self.terms or any(not term.strip() for term in self.terms):
            raise IntentPlanningError("Feature vocabularies require non-empty terms.")


# This is the reviewed feature vocabulary in the v0.2 public portrayal graph.  It is deliberately
# finite: adding a feature is a contract change and cannot occur through request text.
PRODUCTION_FEATURES: tuple[FeatureVocabulary, ...] = (
    FeatureVocabulary("9350906", ("9350906", "fire hydrant", "hydrant", "消防栓")),
    FeatureVocabulary("9740100", ("9740100", "aquaculture pond", "fish pond", "養殖池")),
    FeatureVocabulary(
        "9910603",
        (
            "9910603",
            "police office",
            "police station",
            "police substation",
            "警察局",
            "分駐所",
            "派出所",
        ),
    ),
    FeatureVocabulary("9920101", ("9920101", "college", "university", "大專院校")),
    FeatureVocabulary("9920102", ("9920102", "secondary school", "中學")),
    FeatureVocabulary("9920103", ("9920103", "elementary school", "primary school", "小學")),
    FeatureVocabulary(
        "9920104",
        ("9920104", "vocational training center", "vocational training centre", "職訓中心"),
    ),
    FeatureVocabulary("9920105", ("9920105", "kindergarten", "幼兒園")),
    FeatureVocabulary("9920106", ("9920106", "special school", "特殊學校")),
    FeatureVocabulary("9950201", ("9950201", "post office", "郵局")),
)

_OUTPUT_FIELDS = frozenset(IntentPlanPayload.__required_keys__)
_BOUNDARIES = frozenset(("canonical-production", "retained-demo"))
_ROUTES = frozenset(PRODUCTION_ROUTE_KINDS)
_DISPOSITIONS = frozenset(("proposal", "abstention"))
_DISPLAY_INTENTS = frozenset(("evidence_panel", "portrayal_preview", "none"))
_EVIDENCE_INTENTS = frozenset(("required", "none"))
_REASON_CODES = frozenset(
    (
        "supported_evidence_request",
        "supported_portrayal_request",
        "unsupported_request",
        "ambiguous_request",
        "missing_feature_context",
        "downstream_state_transition",
    )
)
_INFORMATION_TERMS = (
    "what is",
    "where is",
    "show",
    "find",
    "explain",
    "which",
    "rule",
    "symbol",
    "portrayal",
    "圖式",
    "符號",
    "規則",
    "如何呈現",
)
_PORTRAYAL_TERMS = (
    "change",
    "modify",
    "update",
    "recolor",
    "recolour",
    "set color",
    "style",
    "改成",
    "修改",
    "調整",
    "變更",
    "顏色",
    "放大",
    "縮小",
    "旋轉",
)
_UNSUPPORTED_TERMS = (
    "create official",
    "delete",
    "remove official",
    "overwrite",
    "write file",
    "filesystem",
    "shell",
    "command",
    "endpoint",
    "deploy",
    "execute",
    "authorization",
    "authorisation",
    "刪除",
    "覆寫",
    "部署",
    "執行指令",
    "授權",
)
_GENERIC_SCHOOL_TERMS = ("school", "學校")


def _normalize(request: str) -> str:
    if not isinstance(request, str) or not request.strip():
        raise IntentPlanningError("Intent planning requires a non-empty request.")
    if len(request) > 500:
        raise IntentPlanningError("Intent planning requests are limited to 500 characters.")
    return " ".join(request.casefold().split())


def _matched_feature_codes(normalized: str) -> set[str]:
    matches = {
        feature.code
        for feature in PRODUCTION_FEATURES
        if any(term.casefold() in normalized for term in feature.terms)
    }
    school_codes = {
        feature.code for feature in PRODUCTION_FEATURES if feature.code.startswith("99201")
    }
    if not (matches & school_codes) and any(term in normalized for term in _GENERIC_SCHOOL_TERMS):
        matches.update(school_codes)
    return matches


def _plan(
    *,
    boundary: Boundary,
    route_kind: RouteKind,
    feature_code: str | None,
    reason_code: ReasonCode,
) -> IntentPlanPayload:
    if route_kind == "present_evidence":
        display_intent: DisplayIntent = "evidence_panel"
        evidence_intent: EvidenceIntent = "required"
        disposition: Disposition = "proposal"
    elif route_kind == "propose_portrayal_preview":
        display_intent = "portrayal_preview"
        evidence_intent = "required"
        disposition = "proposal"
    else:
        display_intent = "none"
        evidence_intent = "none"
        disposition = "abstention"
        feature_code = None
    result: IntentPlanPayload = {
        "schema": CONTRACT_VERSION,
        "boundary": boundary,
        "route_kind": route_kind,
        "disposition": disposition,
        "feature_code": feature_code,
        "display_intent": display_intent,
        "evidence_intent": evidence_intent,
        "reason_code": reason_code,
    }
    return validate_intent_plan(result)


def plan_request(request: str, *, active_feature_code: str | None = None) -> IntentPlanPayload:
    """Return one deterministic production proposal or a closed abstention.

    The output describes only evidence/display intent.  It cannot grant authorization, request
    execution, or carry mutation parameters.  State gates and effects remain downstream.
    """

    normalized = _normalize(request)
    known_codes = {feature.code for feature in PRODUCTION_FEATURES}
    if active_feature_code is not None and active_feature_code not in known_codes:
        raise IntentPlanningError("Active feature context is outside the production vocabulary.")

    if any(term in normalized for term in _UNSUPPORTED_TERMS):
        return _plan(
            boundary="canonical-production",
            route_kind="abstain",
            feature_code=None,
            reason_code="unsupported_request",
        )

    matches = _matched_feature_codes(normalized)
    if len(matches) > 1:
        return _plan(
            boundary="canonical-production",
            route_kind="abstain",
            feature_code=None,
            reason_code="ambiguous_request",
        )

    mentioned_code = next(iter(matches), None)
    portrayal_requested = any(term in normalized for term in _PORTRAYAL_TERMS)
    information_requested = normalized.endswith(("?", "？")) or any(
        term in normalized for term in _INFORMATION_TERMS
    )
    if portrayal_requested and information_requested:
        return _plan(
            boundary="canonical-production",
            route_kind="abstain",
            feature_code=None,
            reason_code="ambiguous_request",
        )

    if portrayal_requested:
        if mentioned_code and active_feature_code and mentioned_code != active_feature_code:
            return _plan(
                boundary="canonical-production",
                route_kind="abstain",
                feature_code=None,
                reason_code="ambiguous_request",
            )
        feature_code = mentioned_code or active_feature_code
        if feature_code is None:
            return _plan(
                boundary="canonical-production",
                route_kind="abstain",
                feature_code=None,
                reason_code="missing_feature_context",
            )
        return _plan(
            boundary="canonical-production",
            route_kind="propose_portrayal_preview",
            feature_code=feature_code,
            reason_code="supported_portrayal_request",
        )

    if mentioned_code:
        return _plan(
            boundary="canonical-production",
            route_kind="present_evidence",
            feature_code=mentioned_code,
            reason_code="supported_evidence_request",
        )

    return _plan(
        boundary="canonical-production",
        route_kind="abstain",
        feature_code=None,
        reason_code=("missing_feature_context" if information_requested else "unsupported_request"),
    )


def adapt_public_runtime_route(route: Mapping[str, object]) -> IntentPlanPayload:
    """Project the unchanged v0.2 browser route into the canonical production subset."""

    return _adapt_legacy_browser_route(route, boundary="canonical-production")


def adapt_retained_demo_route(route: Mapping[str, object]) -> IntentPlanPayload:
    """Project a V04/V031/V032 route into the retained demo subset."""

    return _adapt_legacy_browser_route(route, boundary="retained-demo")


def _adapt_legacy_browser_route(
    route: Mapping[str, object], *, boundary: Boundary
) -> IntentPlanPayload:
    """Project an existing browser route into the shared proposal-only vocabulary.

    Legacy approval, discard, finish, layer-confirmation, and reset route names are downstream
    state transitions.  They deliberately collapse to abstention instead of entering this contract.
    """

    if not isinstance(route, Mapping):
        raise IntentPlanningError("A retained demo route must be an object.")
    expected = {
        "intent",
        "feature_query",
        "feature_code",
        "style_request",
        "style_plan",
        "reply",
    }
    if set(route) != expected:
        raise IntentPlanningError("Retained demo routes must use the exact legacy field set.")
    intent = route["intent"]
    if not isinstance(intent, str) or intent not in RETAINED_DEMO_ROUTE_KINDS:
        raise IntentPlanningError("Unknown retained demo route kind.")

    code = route["feature_code"]
    if code is not None and (not isinstance(code, str) or not re.fullmatch(r"\d{7}", code)):
        raise IntentPlanningError("Retained demo feature codes must contain seven digits.")
    production_codes = {feature.code for feature in PRODUCTION_FEATURES}
    if boundary == "canonical-production" and code is not None and code not in production_codes:
        return _plan(
            boundary=boundary,
            route_kind="abstain",
            feature_code=None,
            reason_code="unsupported_request",
        )

    if intent == "inspect_feature":
        if code is None:
            query = route["feature_query"]
            if not isinstance(query, str):
                raise IntentPlanningError("Evidence routes require a feature code or query.")
            projected = plan_request(query)
            if projected["route_kind"] != "present_evidence":
                return _plan(
                    boundary=boundary,
                    route_kind="abstain",
                    feature_code=None,
                    reason_code=projected["reason_code"],
                )
            code = projected["feature_code"]
        return _plan(
            boundary=boundary,
            route_kind="present_evidence",
            feature_code=cast(str, code),
            reason_code="supported_evidence_request",
        )
    if intent == "propose_style_revision":
        if code is None:
            return _plan(
                boundary=boundary,
                route_kind="abstain",
                feature_code=None,
                reason_code="missing_feature_context",
            )
        return _plan(
            boundary=boundary,
            route_kind="propose_portrayal_preview",
            feature_code=code,
            reason_code="supported_portrayal_request",
        )
    if intent == "abstain":
        return _plan(
            boundary=boundary,
            route_kind="abstain",
            feature_code=None,
            reason_code="unsupported_request",
        )
    return _plan(
        boundary=boundary,
        route_kind="abstain",
        feature_code=None,
        reason_code="downstream_state_transition",
    )


def validate_intent_plan(value: Mapping[str, object]) -> IntentPlanPayload:
    """Validate the exact contract without adding a production dependency on jsonschema."""

    if not isinstance(value, Mapping) or set(value) != _OUTPUT_FIELDS:
        raise IntentPlanningError("Intent plans must use the exact closed field set.")
    if value["schema"] != CONTRACT_VERSION:
        raise IntentPlanningError("Unsupported intent/planning contract version.")
    if value["boundary"] not in _BOUNDARIES:
        raise IntentPlanningError("Unknown planning boundary.")
    if value["route_kind"] not in _ROUTES:
        raise IntentPlanningError("Unknown route kind.")
    if value["disposition"] not in _DISPOSITIONS:
        raise IntentPlanningError("Unknown planning disposition.")
    if value["display_intent"] not in _DISPLAY_INTENTS:
        raise IntentPlanningError("Unknown display intent.")
    if value["evidence_intent"] not in _EVIDENCE_INTENTS:
        raise IntentPlanningError("Unknown evidence intent.")
    if value["reason_code"] not in _REASON_CODES:
        raise IntentPlanningError("Unknown planning reason.")
    feature_code = value["feature_code"]
    if feature_code is not None and (
        not isinstance(feature_code, str) or not re.fullmatch(r"\d{7}", feature_code)
    ):
        raise IntentPlanningError("Feature codes must contain exactly seven digits.")

    route_kind = value["route_kind"]
    expected = {
        "present_evidence": ("proposal", "evidence_panel", "required", True),
        "propose_portrayal_preview": ("proposal", "portrayal_preview", "required", True),
        "abstain": ("abstention", "none", "none", False),
    }[cast(RouteKind, route_kind)]
    observed = (
        value["disposition"],
        value["display_intent"],
        value["evidence_intent"],
        feature_code is not None,
    )
    if observed != expected:
        raise IntentPlanningError("Route fields do not form a valid proposal-only combination.")
    return cast(IntentPlanPayload, dict(value))

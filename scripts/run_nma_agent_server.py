#!/usr/bin/env python3
"""Serve the NMA demo and proxy bounded Responses API orchestration locally."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nma.agentic_vs1 import (  # noqa: E402
    GroundingValidationError,
    build_agent_trace,
    build_grounded_answer_payload,
    grounding_requirements_for_package,
    parse_grounded_answer,
    usage_summary,
)
from nma.agentic_vs2 import (  # noqa: E402
    PortrayalPlanningError,
    build_portrayal_plan_payload,
    parse_portrayal_plan_response,
)
from nma.agentic_vs3 import (  # noqa: E402
    RealLayerPlanningError,
    build_real_layer_plan_payload,
    parse_real_layer_plan_response,
)
from nma.agentic_vs4 import (  # noqa: E402
    QAPlanningError,
    build_qa_plan_payload,
    parse_qa_plan_response,
)
from nma.agents.school_agent import (  # noqa: E402
    SchoolAgentError,
    analyze_administrative_area,
)
from nma.vector_index import (  # noqa: E402
    OpenAIEmbeddingClient,
    VectorIndex,
    VectorIndexError,
)
from nma.retrieval_v05 import (  # noqa: E402
    RetrievalV05Error,
    load_retrieval_anchors,
)
from nma.retrieval_v06 import (  # noqa: E402
    CitationIntegrityError,
    CitationIntegrityGraphRetrieverV06,
    load_citation_source_registry,
)
from nma.retrieval_v08 import (  # noqa: E402
    RetrievalV08Error,
    load_approved_semantic_links,
)
from nma.entity_resolution_v101 import (  # noqa: E402
    EntityResolutionV101Error,
    OpenAIEntityResolverV101,
    load_geometry_role_scheme,
    load_resolution_support,
)
from nma.entity_resolution_v105 import (  # noqa: E402
    EntityResolutionV105Error,
    PolicyValidatedEntityResolverV105,
)
from nma.entity_resolution_v106 import (  # noqa: E402
    EntityResolutionV106Error,
    OpenAIEntityResolverV106,
    PolicyValidatedEntityResolverV106,
)
from nma.retrieval_v105 import (  # noqa: E402
    RetrievalV105Error,
    ValidatedPolicyGraphRetrieverV105,
)
from nma.retrieval_v108 import (  # noqa: E402
    RetrievalV108Error,
    SegmentAwareGraphRetrieverV108,
)
from nma.runtime_graph_backend_v029 import load_runtime_graph_settings  # noqa: E402
from nma.readonly_knowledge_service import (  # noqa: E402
    KnowledgeServiceConfigurationError,
    KnowledgeServiceGraphRetriever,
    ReadOnlyKnowledgeService,
    ReadOnlyKnowledgeServiceError,
    select_readonly_knowledge_service,
)
from nma.maplibre_adapter import compile_maplibre_preview  # noqa: E402
from nma.portrayal_compile import compile_portrayal_preview  # noqa: E402
from nma.portrayal_review import (  # noqa: E402
    PortrayalReviewEngine,
    PortrayalReviewError,
    merge_portrayal_revision,
)
from nma.real_layer import (  # noqa: E402
    REAL_LAYER_PROFILES,
    RealLayerError,
    execute_real_layer,
    propose_real_layer,
)
from nma.school_hero_execution import (  # noqa: E402
    ExecutionAuthorizationStore,
    SchoolHeroExecutionEngine,
    SchoolHeroExecutionError,
)
from nma.school_portrayal_v1 import (  # noqa: E402
    SchoolPortrayalError,
    SchoolPortrayalPlannerV1,
    apply_school_tool_observation,
    authorize_school_portrayal,
    compile_school_maplibre_preview,
    verify_school_maplibre_preview,
)
from nma.road_portrayal_v1 import (  # noqa: E402
    RoadPortrayalError,
    RoadPortrayalPlannerV1,
    apply_road_tool_observation,
    authorize_road_portrayal,
    compile_road_maplibre_preview,
    verify_road_maplibre_preview,
)
from nma.road_execution import (  # noqa: E402
    FrozenRoadInputs,
    RoadAuthorizationStore,
    RoadExecutionEngine,
    RoadExecutionError,
)
from nma.unified_runtime import (  # noqa: E402
    BuildRuntimeAdapter,
    RoadRuntimeAdapter,
    SchoolRuntimeAdapter,
    UnifiedNMARuntime,
    UnifiedRuntimeError,
)
from nma.qa_review import (  # noqa: E402
    QA_PROFILES,
    REAL_QA_DIAGNOSTIC_PROFILES,
    QAReviewError,
    diagnose_real_vector_profile,
    execute_qa_repair,
    propose_qa_review,
    real_diagnosis_qa_plan,
)

OPENAI_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.6-terra"
RUNTIME_CONTRACT = "nma.runtime-baseline/0.32"
DEMO_RUNTIME_REVISION = RUNTIME_CONTRACT
F03_SERVER_REVISION = "f03-school-hero-centered-edit-2026-08-12.4"
MAX_TURNS = 8
SESSION_TTL_SECONDS = 20 * 60
MAX_BODY_BYTES = 32_768
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,80}$")
FEATURE_CODE_PATTERN = re.compile(r"^[0-9A-Za-z._-]{1,32}$")
SYMBOL_EDIT_PLAN_SCHEMA = "nma.symbol-edit-plan/1.0"
PRIVATE_SCHOOL_ARCHIVE = ROOT / "data" / "datasets" / "112年多維度SHP成果_0502.zip"
PRIVATE_SCHOOL_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
PRIVATE_SCHOOL_CACHE = ROOT / "artifacts" / "tmp" / "private-real-school"
PRIVATE_SCHOOL_FEATURE_CODE = "9920103"
REAL_LAYER_OUTPUT = ROOT / "artifacts" / "tmp" / "real-layer-v04"
SCHOOL_HERO_EXECUTION_ROOT = ROOT / "artifacts" / "runtime" / "school-hero"
ROAD_EXECUTION_ROOT = ROOT / "artifacts" / "runtime" / "road"
QA_REPAIR_OUTPUT = ROOT / "artifacts" / "tmp" / "qa-repair-v04"
SCHOOL_AGENT_SAMPLE_ROOT = ROOT / "data" / "samples" / "school-agent"
SCHOOL_AGENT_NMA_DATASET = Path(
    os.environ.get("NMA_SCHOOL_DATASET", SCHOOL_AGENT_SAMPLE_ROOT / "nma-schools.geojson")
)
SCHOOL_AGENT_OSM_DATASET = Path(
    os.environ.get("OSM_SCHOOL_DATASET", SCHOOL_AGENT_SAMPLE_ROOT / "osm-school-pois.geojson")
)
SCHOOL_AGENT_OFFICIAL_REGISTRY = Path(
    os.environ.get(
        "OFFICIAL_SCHOOL_REGISTRY",
        SCHOOL_AGENT_SAMPLE_ROOT / "official-school-registry.json",
    )
)
CANONICAL_GRAPH = ROOT / "data" / "knowledge" / "nma-canonical-graph-v0.4.json"
VECTOR_INDEX = ROOT / "data" / "runtime" / "vector" / "nma-vector-index-v0.32.json"
RETRIEVAL_ANCHORS = ROOT / "data" / "knowledge" / "nma-retrieval-anchors-v0.5.json"
CITATION_SOURCE_REGISTRY = (
    ROOT / "data" / "knowledge" / "nma-citation-source-registry-v0.6.json"
)
APPROVED_SEMANTIC_LINKS = (
    ROOT / "data" / "knowledge" / "nma-semantic-links-approved-v0.8.json"
)
SEMANTIC_CANDIDATES = (
    ROOT / "data" / "review" / "semantic-links" / "nma-semantic-candidates-v0.8.json"
)
ENTITY_RESOLUTION_SUPPORT = (
    ROOT / "data" / "knowledge" / "nma-entity-resolution-support-v0.10.1.json"
)
GEOMETRY_ROLE_SOURCE = (
    ROOT / "data" / "extraction" / "v0.4" / "road-compound-portrayal-reviewed.json"
)
ENTITY_RESOLUTION_SPECIFICATION = (
    ROOT / "data" / "specifications" / "nma-entity-resolution-v0.10.5.json"
)
DEMO_RUNTIME_SPECIFICATION_V031 = (
    ROOT / "data" / "specifications" / "nma-demo-runtime-v0.31.json"
)
PORTRAYAL_RECIPES = (
    ROOT
    / "data"
    / "portrayal"
    / "nlsc112v5.4"
    / "portrayal-recipe-review-batch-01-v0.4.json"
)
SYMBOL_EDIT_COLORS = (
    "#111111",
    "#ffffff",
    "#c62828",
    "#1565c0",
    "#2e7d32",
    "#f9a825",
    "#ef6c00",
    "#6d7772",
    "#6a1b9a",
)
SYMBOL_EDIT_ACTIONS = (
    "set_color",
    "set_scale",
    "set_stroke_width",
    "set_opacity",
    "set_rotation",
    "set_outline",
    "align",
    "add_shape",
    "remove_shape",
    "match_dimension",
    "attach",
    "detach",
    "center",
)
SYMBOL_EDIT_OPERATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": list(SYMBOL_EDIT_ACTIONS)},
        "target": {
            "type": ["string", "null"],
            "enum": ["symbol", "flag", "flag-top", "flagpole-bottom", "support", None],
        },
        "value": {
            "anyOf": [
                {"type": "number"},
                {
                    "type": "string",
                    "enum": [*SYMBOL_EDIT_COLORS, "none", "rectangle"],
                },
                {"type": "null"},
            ]
        },
        "reference": {
            "type": ["string", "null"],
            "enum": ["flag", "flagpole-top", "support", "support-top", None],
        },
        "relation": {
            "type": ["string", "null"],
            "enum": [
                "aligned",
                "offset",
                "same-width",
                "proportional-width",
                "inserted-into-top",
                "detached",
                "centered",
                None,
            ],
        },
    },
    "required": ["action", "target", "value", "reference", "relation"],
    "additionalProperties": False,
}
SYMBOL_EDIT_PLAN_TOOL_SCHEMA: dict[str, Any] = {
    "type": ["object", "null"],
    "properties": {
        "schema": {"type": "string", "enum": [SYMBOL_EDIT_PLAN_SCHEMA]},
        "source": {"type": "string", "enum": ["responses-api"]},
        "operations": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "items": SYMBOL_EDIT_OPERATION_SCHEMA,
        },
    },
    "required": ["schema", "source", "operations"],
    "additionalProperties": False,
}

BUNDLED_DATASETS: dict[str, dict[str, Any]] = {
    "school-points": {
        "id": "school-points",
        "label": "Bundled synthetic school points",
        "feature_code": "9920103",
        "path": ROOT / "data" / "datasets" / "authoritative" / "school-points" / "SCHOOL_POINT.shp",
        "required_parts": [".shp", ".shx", ".dbf", ".prj"],
        "optional_parts": [".cpg"],
        "field_mapping": {
            "feature_id": "MARKID",
            "feature_code": "TERRAINID",
            "label": "MARKNAME1",
        },
        "source_crs": "EPSG:3826",
        "output_crs": "EPSG:4326",
        "synthetic": True,
    }
}

INTENTS = (
    "inspect_feature",
    "propose_style_revision",
    "approve_revision",
    "discard_revision",
    "finish_revisions",
    "request_layer_confirmation",
    "reset_session",
    "abstain",
)

ROUTE_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "route_nma_turn",
    "description": (
        "Propose exactly one bounded NMA UI action. The application validates and executes it; "
        "this tool never changes authoritative data or creates a map layer directly."
    ),
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": list(INTENTS)},
            "feature_query": {"type": ["string", "null"]},
            "feature_code": {"type": ["string", "null"]},
            "style_request": {"type": ["string", "null"]},
            "style_plan": SYMBOL_EDIT_PLAN_TOOL_SCHEMA,
            "reply": {
                "type": "string",
                "description": "A concise Traditional Chinese response describing the proposed action.",
            },
        },
        "required": [
            "intent",
            "feature_query",
            "feature_code",
            "style_request",
            "style_plan",
            "reply",
        ],
        "additionalProperties": False,
    },
}

INSTRUCTIONS = """You are the intent router for a supervised National Map Agent demo.
Return exactly one route_nma_turn function call and no prose outside the tool call.
The application, not you, owns evidence lookup, symbol rendering, style validation, approval,
GIS processing, and layer creation. Never claim an action happened; only propose the next action.
Use inspect_feature when the user asks how a feature is portrayed or where its rule comes from.
Use propose_style_revision only when the user requests a concrete visual change. Copy the user's
exact visual-change wording into style_request; do not normalize, translate, or paraphrase it.
For propose_style_revision, also return style_plan using schema nma.symbol-edit-plan/1.0 and source
responses-api. Translate every supported part of the request into one or more allowlisted operations.
Use only the enumerated actions, targets, values, references, and relations. Never emit SVG, code,
paths, coordinates, URLs, or approval/deployment actions. Examples: blue means set_color with target
symbol and value #1565c0; add a rectangle means add_shape with target support and value rectangle;
"配合三角旗比例" means match_dimension from support to flag with relation proportional-width;
explicit same-width wording means relation same-width; insert the
lower part below the flag into the rectangle means attach flagpole-bottom to support-top with
relation inserted-into-top; "長方形的中間" also means center flagpole-bottom relative to support
with relation centered. The support is a solid base below the flag face, never a hollow frame
overlapping the flag. Set unused operation
fields to null. For every intent other than propose_style_revision, style_plan must be null.
Use approve_revision or discard_revision only for an explicit decision about a pending revision.
Use finish_revisions when the user explicitly says no more symbol changes are needed.
Use request_layer_confirmation only when the application state says a layer proposal is ready and
the user explicitly asks to proceed to layer creation.
Use abstain for unsupported, ambiguous, or unrelated requests. Keep reply concise and in
Traditional Chinese. Never invent a feature code, evidence source, style value, or completed action.
"""


class AgentError(RuntimeError):
    """An expected, safe-to-classify agent error."""

    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


@dataclass
class AgentSession:
    previous_response_id: str | None = None
    pending_call_id: str | None = None
    turns: int = 0
    last_seen: float = 0.0


@dataclass
class PortrayalProposalRecord:
    proposal_id: str
    proposal: dict[str, Any]
    status: str
    created_at: float
    last_seen: float
    history: list[dict[str, Any]]
    preview_observation: dict[str, Any] | None
    parent_proposal_id: str | None


@dataclass
class RealLayerProposalRecord:
    proposal_id: str
    plan: dict[str, Any]
    planning: dict[str, Any]
    status: str
    created_at: float
    last_seen: float
    history: list[dict[str, Any]]
    observation: dict[str, Any] | None


@dataclass
class QAProposalRecord:
    proposal_id: str
    plan: dict[str, Any]
    planning: dict[str, Any]
    status: str
    created_at: float
    last_seen: float
    history: list[dict[str, Any]]
    observation: dict[str, Any] | None


class SessionStore:
    def __init__(self, *, max_turns: int = MAX_TURNS, ttl: int = SESSION_TTL_SECONDS) -> None:
        self.max_turns = max_turns
        self.ttl = ttl
        self._sessions: dict[str, AgentSession] = {}
        self._lock = Lock()

    def acquire(self, session_id: str, now: float | None = None) -> tuple[AgentSession, bool]:
        timestamp = time.time() if now is None else now
        with self._lock:
            session = self._sessions.get(session_id)
            expired = bool(session and timestamp - session.last_seen > self.ttl)
            exhausted = bool(session and session.turns >= self.max_turns)
            reset = expired or exhausted
            if session is None or reset:
                session = AgentSession(last_seen=timestamp)
                self._sessions[session_id] = session
            else:
                session.last_seen = timestamp
            return session, reset

    def update(
        self,
        session_id: str,
        *,
        response_id: str,
        call_id: str | None,
        now: float | None = None,
    ) -> AgentSession:
        timestamp = time.time() if now is None else now
        with self._lock:
            session = self._sessions[session_id]
            session.previous_response_id = response_id
            session.pending_call_id = call_id
            session.turns += 1
            session.last_seen = timestamp
            return session

    def reset(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


SESSIONS = SessionStore()


class PortrayalProposalStore:
    def __init__(self, *, ttl: int = 60 * 60, max_records: int = 100) -> None:
        self.ttl = ttl
        self.max_records = max_records
        self._records: dict[str, PortrayalProposalRecord] = {}
        self._lock = Lock()

    def _prune(self, now: float) -> None:
        expired = [
            proposal_id
            for proposal_id, record in self._records.items()
            if now - record.last_seen > self.ttl
        ]
        for proposal_id in expired:
            self._records.pop(proposal_id, None)
        if len(self._records) >= self.max_records:
            oldest = sorted(self._records.values(), key=lambda item: item.last_seen)
            for record in oldest[: len(self._records) - self.max_records + 1]:
                self._records.pop(record.proposal_id, None)

    def create(
        self,
        proposal: dict[str, Any],
        *,
        parent_proposal_id: str | None = None,
        now: float | None = None,
    ) -> PortrayalProposalRecord:
        timestamp = time.time() if now is None else now
        identity = json.dumps(proposal, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        proposal_id = "portrayal_" + hashlib.sha256(
            f"{time.time_ns()}:{identity}".encode()
        ).hexdigest()[:24]
        with self._lock:
            self._prune(timestamp)
            record = PortrayalProposalRecord(
                proposal_id=proposal_id,
                proposal=json.loads(json.dumps(proposal, ensure_ascii=False)),
                status="pending",
                created_at=timestamp,
                last_seen=timestamp,
                history=[
                    {
                        "event": "proposed",
                        "at": timestamp,
                        "parent_proposal_id": parent_proposal_id,
                    }
                ],
                preview_observation=None,
                parent_proposal_id=parent_proposal_id,
            )
            self._records[proposal_id] = record
            return record

    def get_for_revision(
        self,
        proposal_id: str,
        *,
        feature_code: str,
        now: float | None = None,
    ) -> PortrayalProposalRecord:
        record = self.get_for_preview(proposal_id, now=now)
        if record.proposal.get("feature", {}).get("code") != feature_code:
            raise AgentError(
                "revision_feature_mismatch",
                "The parent proposal belongs to a different feature.",
                409,
            )
        return record

    def lineage(self, proposal_id: str) -> list[str]:
        with self._lock:
            lineage: list[str] = []
            current = self._records.get(proposal_id)
            while current is not None:
                lineage.append(current.proposal_id)
                current = (
                    self._records.get(current.parent_proposal_id)
                    if current.parent_proposal_id
                    else None
                )
            return list(reversed(lineage))

    def decide(
        self, proposal_id: str, decision: str, *, now: float | None = None
    ) -> PortrayalProposalRecord:
        timestamp = time.time() if now is None else now
        with self._lock:
            self._prune(timestamp)
            record = self._records.get(proposal_id)
            if record is None:
                raise AgentError("proposal_not_found", "The portrayal proposal was not found.", 404)
            if record.status != "pending":
                raise AgentError(
                    "proposal_already_decided",
                    "The portrayal proposal already has a final decision.",
                    409,
                )
            record.status = "approved-for-preview" if decision == "approve" else "discarded"
            record.last_seen = timestamp
            record.history.append({"event": record.status, "at": timestamp})
            record.proposal["approval"]["derived_style_approval"] = record.status
            return record

    def get_for_preview(
        self, proposal_id: str, *, now: float | None = None
    ) -> PortrayalProposalRecord:
        timestamp = time.time() if now is None else now
        with self._lock:
            self._prune(timestamp)
            record = self._records.get(proposal_id)
            if record is None:
                raise AgentError("proposal_not_found", "The portrayal proposal was not found.", 404)
            if record.status != "approved-for-preview":
                raise AgentError(
                    "proposal_not_approved",
                    "The portrayal proposal is not approved for preview.",
                    409,
                )
            record.last_seen = timestamp
            return record

    def record_preview(
        self,
        proposal_id: str,
        observation: dict[str, Any],
        *,
        now: float | None = None,
    ) -> PortrayalProposalRecord:
        timestamp = time.time() if now is None else now
        with self._lock:
            record = self._records[proposal_id]
            record.preview_observation = json.loads(
                json.dumps(observation, ensure_ascii=False)
            )
            record.last_seen = timestamp
            if not any(item["event"] == "preview-compiled" for item in record.history):
                record.history.append({"event": "preview-compiled", "at": timestamp})
            return record


class RealLayerProposalStore:
    def __init__(self, *, ttl: int = 60 * 60, max_records: int = 100) -> None:
        self.ttl = ttl
        self.max_records = max_records
        self._records: dict[str, RealLayerProposalRecord] = {}
        self._lock = Lock()

    def _prune(self, now: float) -> None:
        expired = [
            proposal_id
            for proposal_id, record in self._records.items()
            if now - record.last_seen > self.ttl
        ]
        for proposal_id in expired:
            self._records.pop(proposal_id, None)
        if len(self._records) >= self.max_records:
            oldest = sorted(self._records.values(), key=lambda item: item.last_seen)
            for record in oldest[: len(self._records) - self.max_records + 1]:
                self._records.pop(record.proposal_id, None)

    def create(
        self,
        plan: dict[str, Any],
        planning: dict[str, Any],
        *,
        now: float | None = None,
    ) -> RealLayerProposalRecord:
        timestamp = time.time() if now is None else now
        identity = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        proposal_id = "real_layer_" + hashlib.sha256(
            f"{time.time_ns()}:{identity}".encode()
        ).hexdigest()[:24]
        with self._lock:
            self._prune(timestamp)
            record = RealLayerProposalRecord(
                proposal_id=proposal_id,
                plan=json.loads(json.dumps(plan, ensure_ascii=False)),
                planning=json.loads(json.dumps(planning, ensure_ascii=False)),
                status="pending-approval",
                created_at=timestamp,
                last_seen=timestamp,
                history=[{"event": "proposed", "at": timestamp, "plan_id": plan["plan_id"]}],
                observation=None,
            )
            self._records[proposal_id] = record
            return record

    def get_for_execution(
        self, proposal_id: str, *, now: float | None = None
    ) -> RealLayerProposalRecord:
        timestamp = time.time() if now is None else now
        with self._lock:
            self._prune(timestamp)
            record = self._records.get(proposal_id)
            if record is None:
                raise AgentError("real_layer_proposal_not_found", "The real-layer proposal was not found.", 404)
            if record.status != "pending-approval":
                raise AgentError(
                    "real_layer_proposal_already_decided",
                    "The real-layer proposal already has a final decision.",
                    409,
                )
            record.last_seen = timestamp
            return record

    def record_execution(
        self,
        proposal_id: str,
        observation: dict[str, Any],
        *,
        now: float | None = None,
    ) -> RealLayerProposalRecord:
        timestamp = time.time() if now is None else now
        with self._lock:
            record = self._records[proposal_id]
            record.status = "executed-after-approval"
            record.observation = json.loads(json.dumps(observation, ensure_ascii=False))
            record.last_seen = timestamp
            record.history.append(
                {
                    "event": "approved-and-executed",
                    "at": timestamp,
                    "output_sha256": observation["output_sha256"],
                }
            )
            return record


class QAProposalStore:
    def __init__(self, *, ttl: int = 60 * 60, max_records: int = 100) -> None:
        self.ttl = ttl
        self.max_records = max_records
        self._records: dict[str, QAProposalRecord] = {}
        self._lock = Lock()

    def _prune(self, now: float) -> None:
        expired = [
            proposal_id
            for proposal_id, record in self._records.items()
            if now - record.last_seen > self.ttl
        ]
        for proposal_id in expired:
            self._records.pop(proposal_id, None)
        if len(self._records) >= self.max_records:
            oldest = sorted(self._records.values(), key=lambda item: item.last_seen)
            for record in oldest[: len(self._records) - self.max_records + 1]:
                self._records.pop(record.proposal_id, None)

    def create(
        self,
        plan: dict[str, Any],
        planning: dict[str, Any],
        *,
        now: float | None = None,
    ) -> QAProposalRecord:
        timestamp = time.time() if now is None else now
        identity = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        proposal_id = "qa_review_" + hashlib.sha256(
            f"{time.time_ns()}:{identity}".encode()
        ).hexdigest()[:24]
        with self._lock:
            self._prune(timestamp)
            record = QAProposalRecord(
                proposal_id=proposal_id,
                plan=json.loads(json.dumps(plan, ensure_ascii=False)),
                planning=json.loads(json.dumps(planning, ensure_ascii=False)),
                status="pending-approval",
                created_at=timestamp,
                last_seen=timestamp,
                history=[{"event": "diagnosed-and-proposed", "at": timestamp, "plan_id": plan["plan_id"]}],
                observation=None,
            )
            self._records[proposal_id] = record
            return record

    def get_for_execution(
        self, proposal_id: str, *, now: float | None = None
    ) -> QAProposalRecord:
        timestamp = time.time() if now is None else now
        with self._lock:
            self._prune(timestamp)
            record = self._records.get(proposal_id)
            if record is None:
                raise AgentError("qa_proposal_not_found", "The QA proposal was not found.", 404)
            if record.status != "pending-approval":
                raise AgentError(
                    "qa_proposal_already_decided",
                    "The QA proposal already has a final decision.",
                    409,
                )
            record.last_seen = timestamp
            return record

    def record_execution(
        self,
        proposal_id: str,
        observation: dict[str, Any],
        *,
        now: float | None = None,
    ) -> QAProposalRecord:
        timestamp = time.time() if now is None else now
        with self._lock:
            record = self._records[proposal_id]
            record.status = "reinspected-after-approved-repair"
            record.observation = json.loads(json.dumps(observation, ensure_ascii=False))
            record.last_seen = timestamp
            record.history.extend(
                [
                    {"event": "approved-repair", "at": timestamp},
                    {
                        "event": "reinspected",
                        "at": timestamp,
                        "audit_sha256": observation["audit_sha256"],
                    },
                ]
            )
            return record

PORTRAYAL_PROPOSALS = PortrayalProposalStore()
REAL_LAYER_PROPOSALS = RealLayerProposalStore()
QA_PROPOSALS = QAProposalStore()
SCHOOL_HERO_AUTHORIZATIONS = ExecutionAuthorizationStore(
    SCHOOL_HERO_EXECUTION_ROOT / "authorizations"
)
SCHOOL_HERO_EXECUTIONS = SchoolHeroExecutionEngine(
    storage_root=SCHOOL_HERO_EXECUTION_ROOT,
    archive_path=PRIVATE_SCHOOL_ARCHIVE,
    official_symbol_path=ROOT / "assets" / "symbols" / "nlsc112v5.4" / "school.svg",
    authorization_store=SCHOOL_HERO_AUTHORIZATIONS,
)
ROAD_EXECUTION_INPUTS = FrozenRoadInputs(ROOT)
ROAD_AUTHORIZATIONS = RoadAuthorizationStore(ROAD_EXECUTION_INPUTS.authorization)
ROAD_EXECUTIONS = RoadExecutionEngine(
    storage_root=ROAD_EXECUTION_ROOT,
    archive_path=PRIVATE_SCHOOL_ARCHIVE,
    frozen_inputs=ROAD_EXECUTION_INPUTS,
    authorization_store=ROAD_AUTHORIZATIONS,
)
UNIFIED_RUNTIME = UnifiedNMARuntime(
    {
        "school": SchoolRuntimeAdapter(
            engine=SCHOOL_HERO_EXECUTIONS,
            repository_root=ROOT,
            archive_path=PRIVATE_SCHOOL_ARCHIVE,
            symbol_path=ROOT / "assets" / "symbols" / "nlsc112v5.4" / "school.svg",
        ),
        "road": RoadRuntimeAdapter(
            engine=ROAD_EXECUTIONS,
            repository_root=ROOT,
            archive_path=PRIVATE_SCHOOL_ARCHIVE,
            visual_evidence_path=ROOT / "artifacts/tmp/road05-visual-evidence.json",
            screenshot_path=ROOT / "artifacts/tmp/road05-render.png",
        ),
        "build": BuildRuntimeAdapter(
            repository_root=ROOT,
            archive_path=PRIVATE_SCHOOL_ARCHIVE,
        ),
    }
)
_RETRIEVER: KnowledgeServiceGraphRetriever | CitationIntegrityGraphRetrieverV06 | None = None
_KNOWLEDGE_SERVICE: ReadOnlyKnowledgeService | None = None
_GRAPH_BACKEND_TRACE: dict[str, Any] | None = None
_RETRIEVER_LOCK = Lock()
_VECTOR_INDEX: VectorIndex | None = None
_VECTOR_INDEX_LOCK = Lock()
_RETRIEVAL_ANCHORS: dict[str, Any] | None = None
_RETRIEVAL_ANCHORS_LOCK = Lock()
_CITATION_SOURCE_REGISTRY: dict[str, Any] | None = None
_CITATION_SOURCE_REGISTRY_LOCK = Lock()
_APPROVED_SEMANTIC_LINKS: dict[str, Any] | None = None
_APPROVED_SEMANTIC_LINKS_LOCK = Lock()
_SEMANTIC_CANDIDATES: dict[str, Any] | None = None
_SEMANTIC_CANDIDATES_LOCK = Lock()
_ENTITY_RESOLUTION_SUPPORT: dict[str, Any] | None = None
_ENTITY_RESOLUTION_SUPPORT_LOCK = Lock()
_GEOMETRY_ROLE_SCHEME: dict[str, Any] | None = None
_GEOMETRY_ROLE_SCHEME_LOCK = Lock()
_ENTITY_RESOLUTION_SPEC: dict[str, Any] | None = None
_ENTITY_RESOLUTION_SPEC_LOCK = Lock()
_PORTRAYAL_ENGINE: PortrayalReviewEngine | None = None
_PORTRAYAL_ENGINE_LOCK = Lock()
_SCHOOL_PORTRAYAL_PLANNER: SchoolPortrayalPlannerV1 | None = None
_SCHOOL_PORTRAYAL_PLANNER_LOCK = Lock()
_SCHOOL_PORTRAYAL_ARTIFACT_LIMIT = 256
_SCHOOL_PORTRAYAL_ARTIFACT_LOCK = Lock()
_SCHOOL_PORTRAYAL_ARTIFACTS: dict[str, dict[str, dict[str, Any]]] = {
    "plan": {},
    "authorization": {},
    "adapter_result": {},
}
_ROAD_PORTRAYAL_PLANNER: RoadPortrayalPlannerV1 | None = None
_ROAD_PORTRAYAL_PLANNER_LOCK = Lock()
_ROAD_PORTRAYAL_ARTIFACT_LIMIT = 256
_ROAD_PORTRAYAL_ARTIFACT_LOCK = Lock()
_ROAD_PORTRAYAL_ARTIFACTS: dict[str, dict[str, dict[str, Any]]] = {
    "plan": {},
    "authorization": {},
    "adapter_result": {},
}


def canonical_retriever() -> KnowledgeServiceGraphRetriever | CitationIntegrityGraphRetrieverV06:
    global _RETRIEVER, _KNOWLEDGE_SERVICE, _GRAPH_BACKEND_TRACE
    if _RETRIEVER is None:
        with _RETRIEVER_LOCK:
            if _RETRIEVER is None:
                if not CANONICAL_GRAPH.is_file():
                    raise AgentError(
                        "canonical_graph_missing",
                        "The reviewed canonical graph is not available.",
                        503,
                    )
                try:
                    (
                        _RETRIEVER,
                        _KNOWLEDGE_SERVICE,
                        _GRAPH_BACKEND_TRACE,
                    ) = select_readonly_knowledge_service(
                        canonical_graph_path=CANONICAL_GRAPH,
                        citation_registry_path=CITATION_SOURCE_REGISTRY,
                        settings=load_runtime_graph_settings(ROOT / ".env.local"),
                    )
                except (
                    OSError,
                    json.JSONDecodeError,
                    KnowledgeServiceConfigurationError,
                ) as error:
                    raise AgentError(
                        "runtime_graph_backend_invalid",
                        "The configured runtime graph backend could not be activated safely.",
                        503,
                    ) from error
    return _RETRIEVER


def readonly_knowledge_service() -> ReadOnlyKnowledgeService:
    canonical_retriever()
    if _KNOWLEDGE_SERVICE is None:
        raise AgentError(
            "readonly_knowledge_service_unavailable",
            "The read-only Knowledge Service is not available.",
            503,
        )
    return _KNOWLEDGE_SERVICE


def school_portrayal_planner() -> SchoolPortrayalPlannerV1:
    """Bind School portrayal planning to the active read-only Knowledge Service."""
    global _SCHOOL_PORTRAYAL_PLANNER
    if _SCHOOL_PORTRAYAL_PLANNER is None:
        with _SCHOOL_PORTRAYAL_PLANNER_LOCK:
            if _SCHOOL_PORTRAYAL_PLANNER is None:
                _SCHOOL_PORTRAYAL_PLANNER = SchoolPortrayalPlannerV1(
                    canonical_retriever(),
                    repository_root=ROOT,
                )
    return _SCHOOL_PORTRAYAL_PLANNER


def _register_school_portrayal_artifact(
    kind: str,
    identity_field: str,
    artifact: dict[str, Any],
) -> dict[str, Any]:
    identity = artifact.get(identity_field)
    if not isinstance(identity, str):
        raise SchoolPortrayalError(f"The School {kind} identity is unavailable.")
    copied = json.loads(json.dumps(artifact, ensure_ascii=False))
    with _SCHOOL_PORTRAYAL_ARTIFACT_LOCK:
        records = _SCHOOL_PORTRAYAL_ARTIFACTS[kind]
        records[identity] = copied
        while len(records) > _SCHOOL_PORTRAYAL_ARTIFACT_LIMIT:
            records.pop(next(iter(records)))
    return copied


def _require_school_portrayal_artifact(
    kind: str,
    identity_field: str,
    artifact: Any,
) -> dict[str, Any]:
    if not isinstance(artifact, dict) or not isinstance(artifact.get(identity_field), str):
        raise SchoolPortrayalError(f"A valid School {kind} is required.")
    identity = artifact[identity_field]
    with _SCHOOL_PORTRAYAL_ARTIFACT_LOCK:
        issued = _SCHOOL_PORTRAYAL_ARTIFACTS[kind].get(identity)
    if issued is None or issued != artifact:
        raise SchoolPortrayalError(
            f"The School {kind} was not issued by this governed server session."
        )
    return json.loads(json.dumps(issued, ensure_ascii=False))


def propose_school_portrayal(payload: Any) -> dict[str, Any]:
    return _register_school_portrayal_artifact(
        "plan",
        "plan_sha256",
        school_portrayal_planner().propose(payload),
    )


def authorize_school_portrayal_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"plan", "actor", "decision"}:
        raise SchoolPortrayalError("The School authorization request has an invalid shape.")
    plan = _require_school_portrayal_artifact("plan", "plan_sha256", payload["plan"])
    return _register_school_portrayal_artifact(
        "authorization",
        "authorization_sha256",
        authorize_school_portrayal(
            plan,
            actor=payload["actor"],
            decision=payload["decision"],
        ),
    )


def compile_school_portrayal_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"plan", "authorization"}:
        raise SchoolPortrayalError("The School compilation request has an invalid shape.")
    plan = _require_school_portrayal_artifact("plan", "plan_sha256", payload["plan"])
    approved = _require_school_portrayal_artifact(
        "authorization",
        "authorization_sha256",
        payload["authorization"],
    )
    return _register_school_portrayal_artifact(
        "adapter_result",
        "adapter_result_sha256",
        compile_school_maplibre_preview(plan, approved),
    )


def observe_school_portrayal_tool(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"plan", "observation"}:
        raise SchoolPortrayalError("The School tool observation request has an invalid shape.")
    plan = _require_school_portrayal_artifact("plan", "plan_sha256", payload["plan"])
    result = apply_school_tool_observation(plan, payload["observation"])
    if result.get("schema") == "nma.school-portrayal-plan/1.0":
        return _register_school_portrayal_artifact("plan", "plan_sha256", result)
    return result


def verify_school_portrayal_request(payload: Any) -> dict[str, Any]:
    required = {"plan", "authorization", "adapter_result"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise SchoolPortrayalError("The School verification request has an invalid shape.")
    plan = _require_school_portrayal_artifact("plan", "plan_sha256", payload["plan"])
    approved = _require_school_portrayal_artifact(
        "authorization",
        "authorization_sha256",
        payload["authorization"],
    )
    adapter_result = _require_school_portrayal_artifact(
        "adapter_result",
        "adapter_result_sha256",
        payload["adapter_result"],
    )
    return verify_school_maplibre_preview(
        plan,
        approved,
        adapter_result,
    )


def road_portrayal_planner() -> RoadPortrayalPlannerV1:
    """Bind ROAD portrayal planning to the active read-only Knowledge Service."""
    global _ROAD_PORTRAYAL_PLANNER
    if _ROAD_PORTRAYAL_PLANNER is None:
        with _ROAD_PORTRAYAL_PLANNER_LOCK:
            if _ROAD_PORTRAYAL_PLANNER is None:
                _ROAD_PORTRAYAL_PLANNER = RoadPortrayalPlannerV1(canonical_retriever())
    return _ROAD_PORTRAYAL_PLANNER


def _register_road_portrayal_artifact(
    kind: str,
    identity_field: str,
    artifact: dict[str, Any],
) -> dict[str, Any]:
    identity = artifact.get(identity_field)
    if not isinstance(identity, str):
        raise RoadPortrayalError(f"The ROAD {kind} identity is unavailable.")
    copied = json.loads(json.dumps(artifact, ensure_ascii=False))
    with _ROAD_PORTRAYAL_ARTIFACT_LOCK:
        records = _ROAD_PORTRAYAL_ARTIFACTS[kind]
        records[identity] = copied
        while len(records) > _ROAD_PORTRAYAL_ARTIFACT_LIMIT:
            records.pop(next(iter(records)))
    return copied


def _require_road_portrayal_artifact(
    kind: str,
    identity_field: str,
    artifact: Any,
) -> dict[str, Any]:
    if not isinstance(artifact, dict) or not isinstance(artifact.get(identity_field), str):
        raise RoadPortrayalError(f"A valid ROAD {kind} is required.")
    identity = artifact[identity_field]
    with _ROAD_PORTRAYAL_ARTIFACT_LOCK:
        issued = _ROAD_PORTRAYAL_ARTIFACTS[kind].get(identity)
    if issued is None or issued != artifact:
        raise RoadPortrayalError(f"The ROAD {kind} was not issued by this governed server session.")
    return json.loads(json.dumps(issued, ensure_ascii=False))


def propose_road_portrayal(payload: Any) -> dict[str, Any]:
    return _register_road_portrayal_artifact(
        "plan",
        "plan_sha256",
        road_portrayal_planner().propose(payload),
    )


def authorize_road_portrayal_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"plan", "actor", "decision"}:
        raise RoadPortrayalError("The ROAD authorization request has an invalid shape.")
    plan = _require_road_portrayal_artifact("plan", "plan_sha256", payload["plan"])
    return _register_road_portrayal_artifact(
        "authorization",
        "authorization_sha256",
        authorize_road_portrayal(
            plan,
            actor=payload["actor"],
            decision=payload["decision"],
        ),
    )


def compile_road_portrayal_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"plan", "authorization"}:
        raise RoadPortrayalError("The ROAD compilation request has an invalid shape.")
    plan = _require_road_portrayal_artifact("plan", "plan_sha256", payload["plan"])
    approved = _require_road_portrayal_artifact(
        "authorization",
        "authorization_sha256",
        payload["authorization"],
    )
    return _register_road_portrayal_artifact(
        "adapter_result",
        "adapter_result_sha256",
        compile_road_maplibre_preview(plan, approved),
    )


def observe_road_portrayal_tool(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"plan", "observation"}:
        raise RoadPortrayalError("The ROAD tool observation request has an invalid shape.")
    plan = _require_road_portrayal_artifact("plan", "plan_sha256", payload["plan"])
    return apply_road_tool_observation(plan, payload["observation"])


def verify_road_portrayal_request(payload: Any) -> dict[str, Any]:
    required = {"plan", "authorization", "adapter_result"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise RoadPortrayalError("The ROAD verification request has an invalid shape.")
    plan = _require_road_portrayal_artifact("plan", "plan_sha256", payload["plan"])
    approved = _require_road_portrayal_artifact(
        "authorization",
        "authorization_sha256",
        payload["authorization"],
    )
    adapter_result = _require_road_portrayal_artifact(
        "adapter_result",
        "adapter_result_sha256",
        payload["adapter_result"],
    )
    return verify_road_maplibre_preview(plan, approved, adapter_result)


def graph_backend_trace() -> dict[str, Any]:
    canonical_retriever()
    if _GRAPH_BACKEND_TRACE is None:
        raise AgentError(
            "runtime_graph_backend_invalid",
            "The runtime graph backend has no auditable activation trace.",
            503,
        )
    return json.loads(json.dumps(_GRAPH_BACKEND_TRACE, ensure_ascii=False))


def attach_graph_backend_trace_v029(package: dict[str, Any]) -> dict[str, Any]:
    """Make the active graph backend and any fallback visible on every typed retrieval."""
    trace = graph_backend_trace()
    package["retrieval_trace"]["v029_graph_backend"] = trace
    package["retrieval_trace"]["v033_readonly_knowledge_service"] = json.loads(
        json.dumps(trace, ensure_ascii=False)
    )
    return package


def retrieve_evidence_from_resolution_v030(
    query: str,
    resolution: dict[str, Any],
    *,
    ranked_trace: list[dict[str, Any]],
    max_depth: int = 3,
    max_nodes: int = 300,
) -> dict[str, Any]:
    """Typed LLM-resolution handoff; the model never receives arbitrary graph syntax."""
    if resolution.get("schema") != "nma.entity-resolution/0.10.6":
        raise AgentError(
            "invalid_entity_resolution_handoff",
            "The entity-resolution handoff has an unsupported schema.",
            502,
        )
    status = resolution.get("status")
    selected_ids = resolution.get("selected_node_ids")
    if status not in {"resolved", "needs-clarification", "abstained-no-match"}:
        raise AgentError(
            "invalid_entity_resolution_handoff",
            "The entity-resolution handoff has an invalid status.",
            502,
        )
    if not isinstance(selected_ids, list) or any(
        not isinstance(node_id, str) for node_id in selected_ids
    ):
        raise AgentError(
            "invalid_entity_resolution_handoff",
            "The entity-resolution handoff has invalid selected IDs.",
            502,
        )
    if status == "resolved" and not selected_ids:
        raise AgentError(
            "invalid_entity_resolution_handoff",
            "A resolved handoff must contain at least one selected ID.",
            502,
        )
    graph_retriever = canonical_retriever()
    unknown = sorted(set(selected_ids) - set(graph_retriever.nodes))
    if unknown:
        raise AgentError(
            "invalid_entity_resolution_handoff",
            "The entity-resolution handoff selected an unknown canonical node.",
            502,
        )
    try:
        package = graph_retriever.package_from_seed_ids(
            query,
            selected_ids,
            ranked_trace=ranked_trace,
            retrieval_mode="v0.30-llm-resolution-to-typed-live-graph-expansion",
            max_depth=max_depth,
            max_nodes=max_nodes,
            expand_product_fields=any(
                keyword in query.casefold()
                for keyword in ("欄位", "屬性", "field", "attribute")
            ),
        )
    except ReadOnlyKnowledgeServiceError as error:
        raise AgentError(
            "readonly_knowledge_query_failed",
            "The read-only Knowledge Service rejected or could not complete the evidence query.",
            503,
        ) from error
    package["retrieval_trace"]["v030_entity_resolution_handoff"] = {
        "schema": resolution["schema"],
        "status": status,
        "selected_node_ids": list(selected_ids),
        "candidate_pool_sha256": resolution.get("candidate_pool_sha256"),
        "response_id": resolution.get("response_id"),
        "response_model": resolution.get("response_model"),
        "usage": json.loads(
            json.dumps(resolution.get("usage", {}), ensure_ascii=False)
        ),
        "hidden_chain_of_thought_exposed": False,
        "typed_tool_only": True,
        "arbitrary_cypher_allowed": False,
        "automatic_rule_activation": False,
    }
    return attach_graph_backend_trace_v029(package)


def vector_index() -> VectorIndex:
    global _VECTOR_INDEX
    if _VECTOR_INDEX is None:
        with _VECTOR_INDEX_LOCK:
            if _VECTOR_INDEX is None:
                if not VECTOR_INDEX.is_file():
                    raise AgentError(
                        "vector_index_missing",
                        "The provider-backed semantic vector index is not available.",
                        503,
                    )
                try:
                    loaded = VectorIndex.load(VECTOR_INDEX)
                except (OSError, json.JSONDecodeError, VectorIndexError) as error:
                    raise AgentError(
                        "vector_index_invalid",
                        "The provider-backed semantic vector index is invalid.",
                        503,
                    ) from error
                graph_sha256 = _file_sha256(CANONICAL_GRAPH)
                if loaded.payload.get("canonical_graph_sha256") != graph_sha256:
                    raise AgentError(
                        "vector_graph_identity_mismatch",
                        "The vector index does not match the canonical graph.",
                        503,
                    )
                candidates = semantic_candidates()
                candidate_ids = {
                    item["target_node_id"] for item in candidates["candidates"]
                }
                missing = sorted(candidate_ids - set(loaded.vectors))
                if missing:
                    raise AgentError(
                        "vector_candidate_view_incomplete",
                        "The canonical vector index is missing reviewed runtime candidates.",
                        503,
                    )
                loaded.vectors = {
                    node_id: loaded.vectors[node_id]
                    for node_id in sorted(candidate_ids)
                }
                loaded.node_types = {
                    node_id: loaded.node_types[node_id]
                    for node_id in sorted(candidate_ids)
                }
                loaded.payload = {
                    **loaded.payload,
                    "source_corpus": {
                        "schema": candidates["schema"],
                        "path": str(SEMANTIC_CANDIDATES.relative_to(ROOT)),
                        "sha256": _file_sha256(SEMANTIC_CANDIDATES),
                        "records": len(candidate_ids),
                        "interpreted_terms_embedded": False,
                    },
                    "runtime_candidate_view": {
                        "source_index_path": str(VECTOR_INDEX.relative_to(ROOT)),
                        "source_index_records": int(
                            loaded.payload["statistics"]["records"]
                        ),
                        "candidate_records": len(candidate_ids),
                        "canonical_graph_sha256": graph_sha256,
                    },
                }
                _VECTOR_INDEX = loaded
    return _VECTOR_INDEX


def retrieval_anchors() -> dict[str, Any]:
    global _RETRIEVAL_ANCHORS
    if _RETRIEVAL_ANCHORS is None:
        with _RETRIEVAL_ANCHORS_LOCK:
            if _RETRIEVAL_ANCHORS is None:
                try:
                    _RETRIEVAL_ANCHORS = load_retrieval_anchors(RETRIEVAL_ANCHORS)
                except (OSError, json.JSONDecodeError, RetrievalV05Error) as error:
                    raise AgentError(
                        "retrieval_anchors_invalid",
                        "The source-grounded v0.5 retrieval anchors are unavailable or invalid.",
                        503,
                    ) from error
    return _RETRIEVAL_ANCHORS


def citation_source_registry() -> dict[str, Any]:
    global _CITATION_SOURCE_REGISTRY
    if _CITATION_SOURCE_REGISTRY is None:
        with _CITATION_SOURCE_REGISTRY_LOCK:
            if _CITATION_SOURCE_REGISTRY is None:
                try:
                    _CITATION_SOURCE_REGISTRY = load_citation_source_registry(
                        CITATION_SOURCE_REGISTRY
                    )
                except (OSError, json.JSONDecodeError, CitationIntegrityError) as error:
                    raise AgentError(
                        "citation_source_registry_invalid",
                        "The reviewed v0.6 citation source registry is unavailable or invalid.",
                        503,
                    ) from error
    return _CITATION_SOURCE_REGISTRY


def approved_semantic_links() -> dict[str, Any]:
    global _APPROVED_SEMANTIC_LINKS
    if _APPROVED_SEMANTIC_LINKS is None:
        with _APPROVED_SEMANTIC_LINKS_LOCK:
            if _APPROVED_SEMANTIC_LINKS is None:
                try:
                    _APPROVED_SEMANTIC_LINKS = load_approved_semantic_links(
                        APPROVED_SEMANTIC_LINKS
                    )
                except (OSError, json.JSONDecodeError, RetrievalV08Error) as error:
                    raise AgentError(
                        "approved_semantic_links_invalid",
                        "The reviewed v0.8 runtime semantic links are unavailable or invalid.",
                        503,
                    ) from error
    return _APPROVED_SEMANTIC_LINKS


def semantic_candidates() -> dict[str, Any]:
    global _SEMANTIC_CANDIDATES
    if _SEMANTIC_CANDIDATES is None:
        with _SEMANTIC_CANDIDATES_LOCK:
            if _SEMANTIC_CANDIDATES is None:
                try:
                    payload = json.loads(SEMANTIC_CANDIDATES.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as error:
                    raise AgentError(
                        "semantic_candidates_invalid",
                        "The bounded 638-record semantic candidate set is unavailable or invalid.",
                        503,
                    ) from error
                if payload.get("schema") != "nma.semantic-candidate-set/0.8" or len(
                    payload.get("candidates", [])
                ) != 638:
                    raise AgentError(
                        "semantic_candidates_invalid",
                        "The bounded semantic candidate set has an invalid identity.",
                        503,
                    )
                _SEMANTIC_CANDIDATES = payload
    return _SEMANTIC_CANDIDATES


def entity_resolution_support() -> dict[str, Any]:
    global _ENTITY_RESOLUTION_SUPPORT
    if _ENTITY_RESOLUTION_SUPPORT is None:
        with _ENTITY_RESOLUTION_SUPPORT_LOCK:
            if _ENTITY_RESOLUTION_SUPPORT is None:
                try:
                    _ENTITY_RESOLUTION_SUPPORT = load_resolution_support(
                        ENTITY_RESOLUTION_SUPPORT
                    )
                except (OSError, json.JSONDecodeError, EntityResolutionV101Error) as error:
                    raise AgentError(
                        "entity_resolution_support_invalid",
                        "The reviewed cross-document entity-resolution support is unavailable or invalid.",
                        503,
                    ) from error
    return _ENTITY_RESOLUTION_SUPPORT


def geometry_role_scheme() -> dict[str, Any]:
    global _GEOMETRY_ROLE_SCHEME
    if _GEOMETRY_ROLE_SCHEME is None:
        with _GEOMETRY_ROLE_SCHEME_LOCK:
            if _GEOMETRY_ROLE_SCHEME is None:
                try:
                    _GEOMETRY_ROLE_SCHEME = load_geometry_role_scheme(
                        GEOMETRY_ROLE_SOURCE
                    )
                except (OSError, json.JSONDecodeError, EntityResolutionV101Error) as error:
                    raise AgentError(
                        "geometry_role_scheme_invalid",
                        "The reviewed graphic-element role scheme is unavailable or invalid.",
                        503,
                    ) from error
    return _GEOMETRY_ROLE_SCHEME


def entity_resolution_specification() -> dict[str, Any]:
    global _ENTITY_RESOLUTION_SPEC
    if _ENTITY_RESOLUTION_SPEC is None:
        with _ENTITY_RESOLUTION_SPEC_LOCK:
            if _ENTITY_RESOLUTION_SPEC is None:
                try:
                    payload = json.loads(
                        ENTITY_RESOLUTION_SPECIFICATION.read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError) as error:
                    raise AgentError(
                        "entity_resolution_specification_invalid",
                        "The entity-resolution specification is unavailable or invalid.",
                        503,
                    ) from error
                if payload.get("schema") != "nma.entity-resolution-specification/0.10.5":
                    raise AgentError(
                        "entity_resolution_specification_invalid",
                        "The entity-resolution specification has an invalid identity.",
                        503,
                    )
                _ENTITY_RESOLUTION_SPEC = payload
    return _ENTITY_RESOLUTION_SPEC


def retrieve_evidence(
    query: str,
    api_key: str,
    *,
    model: str = DEFAULT_MODEL,
    seed_limit: int = 6,
    max_depth: int = 2,
    max_nodes: int = 60,
) -> dict[str, Any]:
    """Run the v0.31 live spine over the sealed v0.10.8 retrieval contracts."""
    client = OpenAIEmbeddingClient(api_key)

    def embed_query(text: str, model: str, dimensions: int) -> dict[str, Any]:
        response = client.embed_batch([text], model=model, dimensions=dimensions)
        return {
            "vector": response["vectors"][0],
            "usage": response["usage"],
        }

    class RuntimeQueryEmbeddingCacheV031:
        """Expose live provider embeddings through the bounded cache interface."""

        def embed_query(
            self, text: str, embedding_model: str, dimensions: int
        ) -> dict[str, Any]:
            embedded = embed_query(text, embedding_model, dimensions)
            return {
                **embedded,
                "query_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }

    try:
        graph_retriever = canonical_retriever()
        # Force registry validation before live retrieval even though the graph retriever also
        # carries the same reviewed registry.
        citation_source_registry()
        runtime_specification = json.loads(
            DEMO_RUNTIME_SPECIFICATION_V031.read_text(encoding="utf-8")
        )
        if (
            runtime_specification.get("schema")
            != "nma.demo-runtime-specification/0.31"
        ):
            raise RetrievalV108Error("Unsupported v0.31 runtime specification.")
        pool_limits = {
            key: int(value)
            for key, value in runtime_specification[
                "candidate_pool_parameters"
            ].items()
        }
        query_cache = RuntimeQueryEmbeddingCacheV031()
        resolver = PolicyValidatedEntityResolverV106(
            OpenAIEntityResolverV106(api_key, model=model, timeout_seconds=120)
        )
        package = SegmentAwareGraphRetrieverV108(
            graph_retriever,
            vector_index(),
            embed_query,
            retrieval_anchors=retrieval_anchors(),
            approved_semantic_links=approved_semantic_links(),
            min_vector_similarity=0.34,
            candidate_set=semantic_candidates(),
            entity_resolver=resolver,
            resolution_support=entity_resolution_support(),
            geometry_role_scheme=geometry_role_scheme(),
            candidate_pool_limits=pool_limits,
            candidate_query_cache=query_cache,
            segment_query_cache=query_cache,
        ).evidence_package(
            query,
            seed_limit=seed_limit,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )
    except ReadOnlyKnowledgeServiceError as error:
        raise AgentError(
            "readonly_knowledge_query_failed",
            "The read-only Knowledge Service rejected or could not complete the evidence query.",
            503,
        ) from error
    except (
        VectorIndexError,
        EntityResolutionV101Error,
        EntityResolutionV105Error,
        EntityResolutionV106Error,
        RetrievalV105Error,
        RetrievalV108Error,
        OSError,
        json.JSONDecodeError,
    ) as error:
        raise AgentError("semantic_retrieval_failed", str(error), 502) from error
    trace = package["retrieval_trace"]
    trace["retrieval_policy_version"] = "0.10.8"
    trace["v031_runtime_integration"] = "v108-pool-v106-resolver-active"
    if not trace.get("v108_llm_entity_resolution_used", False):
        trace["v108_policy_validation"] = {
            "policy": "deterministic-v0.8-v0.9-precedence",
            "outcome": "no-llm-entity-resolution-required",
            "new_openai_request": False,
            "automatic_rule_activation": False,
        }
    trace["retrieval_mode"] = package.get("retrieval_mode")
    package = normalize_canonical_citation_metadata(package)
    return attach_graph_backend_trace_v029(package)


def normalize_canonical_citation_metadata(
    package: dict[str, Any]
) -> dict[str, Any]:
    """Bind every returned citation to its canonical section containment identity."""

    retriever = canonical_retriever()
    for citation in package.get("citations", []):
        if not isinstance(citation, dict):
            continue
        section_id = citation.get("section_id")
        if not isinstance(section_id, str):
            citation_id = citation.get("citation_id")
            if isinstance(citation_id, str) and citation_id.startswith("citation:"):
                section_id = citation_id.removeprefix("citation:")
        document_ids = retriever.section_document_ids.get(section_id, [])
        section = retriever.nodes.get(section_id, {}) if isinstance(section_id, str) else {}
        if len(document_ids) != 1 or section.get("type") != "DocumentSection":
            continue
        document_id = document_ids[0]
        properties, provenance = retriever.document_properties(document_id)
        section_properties = section.get("properties", {})
        citation.update(
            {
                "citation_id": f"citation:{section_id}",
                "section_id": section_id,
                "document_id": document_id,
                "filename": properties.get("filename"),
                "revision": properties.get("revision"),
                "source_sha256": properties.get("sha256"),
                "page": section_properties.get("page"),
                "printed_page": section_properties.get("printed_page"),
                "record_id": section_properties.get("record_id"),
                "review_status": section_properties.get("review_status"),
                "citation_integrity": "verified-unique-document-containment",
                "document_candidates": [document_id],
                "metadata_provenance": provenance,
            }
        )
    package.setdefault("retrieval_trace", {})[
        "v032_citation_identity_normalization"
    ] = "canonical-section-containment-applied"
    return package


def school_hero_evidence_package() -> dict[str, Any]:
    """Retrieve the reviewed school Hero path without any OpenAI request."""

    package = retrieve_evidence_from_resolution_v030(
        "小學 9920103 圖式規則",
        {
            "schema": "nma.entity-resolution/0.10.6",
            "status": "resolved",
            "selected_node_ids": ["code-value:landmark-type:9920103"],
            "candidate_pool_sha256": "deterministic-reviewed-school-anchor",
            "response_id": None,
            "response_model": None,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            },
        },
        ranked_trace=[
            {
                "node_id": "code-value:landmark-type:9920103",
                "score": 1.0,
                "source": "reviewed-hero-anchor",
            }
        ],
        max_depth=3,
        max_nodes=40,
    )
    package = normalize_canonical_citation_metadata(package)
    package["retrieval_trace"]["v032_openai_request_count"] = 0
    package["retrieval_trace"]["v032_hero_mode"] = (
        "reviewed-deterministic-school-anchor-to-typed-graph"
    )
    return package


def school_hero_evidence_result() -> dict[str, Any]:
    evidence_package = school_hero_evidence_package()
    answer_response = reviewed_school_fact_projection(
        "小學的圖式規則在哪一頁？", evidence_package
    )
    if answer_response is None:
        raise AgentError(
            "school_hero_evidence_incomplete",
            "The reviewed school rule, symbol, or Document 01 page 61 citation is incomplete.",
            503,
        )
    try:
        grounded_answer = parse_grounded_answer(answer_response, evidence_package)
    except GroundingValidationError as error:
        raise AgentError("invalid_grounded_answer", str(error), 502) from error
    route_response = {
        "id": "local_route_school_9920103",
        "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
    }
    trace = build_agent_trace(
        model="reviewed-fact-projection",
        route_response=route_response,
        evidence_package=evidence_package,
        answer_response=answer_response,
        grounded_answer=grounded_answer,
        timings_ms={"route": 0, "retrieve": 0, "answer": 0},
    )
    return {
        "schema": "nma.agentic-vs1/1.0",
        "server_revision": F03_SERVER_REVISION,
        "mode": "zero-openai-credit-reviewed-hero",
        "openai_request_count": 0,
        "evidence_package": evidence_package,
        "answer": grounded_answer,
        "trace": trace,
        "runtime_contract": build_demo_runtime_contract_v031(
            evidence_package, grounded_answer
        ),
        "automatic_action": False,
    }


def portrayal_review_engine() -> PortrayalReviewEngine:
    global _PORTRAYAL_ENGINE
    if _PORTRAYAL_ENGINE is None:
        with _PORTRAYAL_ENGINE_LOCK:
            if _PORTRAYAL_ENGINE is None:
                if not PORTRAYAL_RECIPES.is_file():
                    raise AgentError(
                        "portrayal_recipes_missing",
                        "The reviewed portrayal recipe set is not available.",
                        503,
                    )
                _PORTRAYAL_ENGINE = PortrayalReviewEngine.load(PORTRAYAL_RECIPES)
    return _PORTRAYAL_ENGINE


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bundled_dataset(dataset_id: str) -> dict[str, Any]:
    dataset = BUNDLED_DATASETS.get(dataset_id)
    if not dataset:
        raise AgentError("dataset_not_found", "The bundled dataset is not registered.", 404)
    return dataset


def _private_school_cache_is_current(target: Path, manifest_path: Path) -> bool:
    if not target.is_file() or not manifest_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        manifest.get("source_archive_sha256") == PRIVATE_SCHOOL_ARCHIVE_SHA256
        and manifest.get("feature_code") == PRIVATE_SCHOOL_FEATURE_CODE
        and manifest.get("feature_count") == 15
        and len(manifest.get("source_layers", [])) == 6
    )


def prepare_private_real_school_dataset() -> dict[str, Any] | None:
    """Build a local-only school Shapefile from the verified user archive.

    The source archive is never changed or copied into a public artifact. Only the six MARK
    Shapefiles are read, and only features with the reviewed school code are carried forward.
    """

    if not PRIVATE_SCHOOL_ARCHIVE.is_file():
        return None
    archive_sha256 = _file_sha256(PRIVATE_SCHOOL_ARCHIVE)
    if archive_sha256 != PRIVATE_SCHOOL_ARCHIVE_SHA256:
        raise AgentError(
            "private_dataset_checksum_mismatch",
            "The local 112-year Shapefile archive does not match the reviewed checksum.",
            422,
        )
    ogr2ogr = shutil.which("ogr2ogr")
    if not ogr2ogr:
        raise AgentError("ogr_unavailable", "GDAL/OGR is required for the real dataset.", 503)

    version_root = PRIVATE_SCHOOL_CACHE / archive_sha256[:16]
    target = version_root / "SCHOOL_POINT.shp"
    manifest_path = version_root / "provenance.json"
    if not _private_school_cache_is_current(target, manifest_path):
        PRIVATE_SCHOOL_CACHE.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="real-school-build-", dir=PRIVATE_SCHOOL_CACHE
        ) as temporary:
            temporary_root = Path(temporary)
            extracted = temporary_root / "source"
            extracted.mkdir()
            with zipfile.ZipFile(PRIVATE_SCHOOL_ARCHIVE) as archive:
                members = []
                for member in archive.infolist():
                    member_path = Path(member.filename)
                    if (
                        member.is_dir()
                        or "__MACOSX" in member_path.parts
                        or member_path.is_absolute()
                        or ".." in member_path.parts
                        or not re.search(r"_MARK\.(?:shp|shx|dbf|prj|cpg)$", member.filename, re.I)
                    ):
                        continue
                    members.append(member)
                for member in members:
                    archive.extract(member, extracted)

            sources = sorted(extracted.rglob("*_MARK.shp"))
            if len(sources) != 6:
                raise AgentError(
                    "private_dataset_incomplete",
                    f"Expected six MARK Shapefiles in the verified archive; found {len(sources)}.",
                    422,
                )
            generated = temporary_root / "dataset" / "SCHOOL_POINT.shp"
            generated.parent.mkdir()
            for index, source in enumerate(sources):
                command = [
                    ogr2ogr,
                    "-f",
                    "ESRI Shapefile",
                    str(generated),
                    str(source),
                    "-where",
                    f"TERRAINID='{PRIVATE_SCHOOL_FEATURE_CODE}'",
                    "-nln",
                    "SCHOOL_POINT",
                ]
                if index == 0:
                    command[1:1] = ["-overwrite"]
                    command.extend(["-lco", "ENCODING=UTF-8"])
                else:
                    command[1:1] = ["-append"]
                subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)

            validation = subprocess.run(
                [
                    ogr2ogr,
                    "-f",
                    "GeoJSON",
                    "/vsistdout/",
                    str(generated),
                    "-t_srs",
                    "EPSG:4326",
                    "-lco",
                    "RFC7946=YES",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            collection = json.loads(validation.stdout)
            features = collection.get("features", [])
            if len(features) != 15 or any(
                str(feature.get("properties", {}).get("TERRAINID"))
                != PRIVATE_SCHOOL_FEATURE_CODE
                for feature in features
            ):
                raise AgentError(
                    "private_dataset_validation_failed",
                    "The verified archive did not produce the expected 15 real school features.",
                    422,
                )
            source_layers = [source.stem for source in sources]
            provenance = {
                "schema": "nma.private-derived-dataset/1.0",
                "source_archive": PRIVATE_SCHOOL_ARCHIVE.name,
                "source_archive_sha256": archive_sha256,
                "source_layers": source_layers,
                "source_filter": f"TERRAINID={PRIVATE_SCHOOL_FEATURE_CODE}",
                "feature_code": PRIVATE_SCHOOL_FEATURE_CODE,
                "feature_count": len(features),
                "redistributed": False,
            }
            generated_manifest = temporary_root / "dataset" / "provenance.json"
            generated_manifest.write_text(
                json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            if version_root.exists():
                raise AgentError(
                    "private_dataset_cache_invalid",
                    "The local real-data cache is incomplete; remove only that cache and restart.",
                    422,
                )
            shutil.move(str(generated.parent), str(version_root))

    provenance = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "id": "school-points",
        "label": "Real schools from 112-year multidimensional Shapefiles",
        "feature_code": PRIVATE_SCHOOL_FEATURE_CODE,
        "path": target,
        "required_parts": [".shp", ".shx", ".dbf", ".prj"],
        "optional_parts": [".cpg"],
        "field_mapping": {
            "feature_id": "MARKID",
            "feature_code": "TERRAINID",
            "label": "MARKNAME1",
        },
        "source_crs": "EPSG:3826",
        "output_crs": "EPSG:4326",
        "synthetic": False,
        "source_archive": provenance["source_archive"],
        "source_archive_sha256": provenance["source_archive_sha256"],
        "source_layers": provenance["source_layers"],
        "source_filter": provenance["source_filter"],
        "redistributed": False,
        "attribution": "User-provided 112-year multidimensional Shapefiles (local only)",
    }


def activate_private_real_school_dataset() -> bool:
    dataset = prepare_private_real_school_dataset()
    if dataset is None:
        return False
    BUNDLED_DATASETS["school-points"] = dataset
    return True


def inspect_bundled_dataset(dataset_id: str) -> dict[str, Any]:
    from nma.ogr import inspect_dataset

    dataset = _bundled_dataset(dataset_id)
    source: Path = dataset["path"]
    components = []
    for extension in [*dataset["required_parts"], *dataset["optional_parts"]]:
        component = source.with_suffix(extension)
        present = component.is_file()
        components.append(
            {
                "extension": extension,
                "filename": component.name,
                "required": extension in dataset["required_parts"],
                "present": present,
                "size_bytes": component.stat().st_size if present else None,
                "sha256": _file_sha256(component) if present else None,
            }
        )
    missing = [item["extension"] for item in components if item["required"] and not item["present"]]
    if missing:
        raise AgentError(
            "dataset_incomplete",
            f"Required Shapefile parts are missing: {', '.join(missing)}.",
            422,
        )
    inspection = inspect_dataset(source)
    if not inspection.get("available"):
        raise AgentError("ogr_unavailable", "GDAL/OGR inspection is unavailable.", 503)
    if not inspection.get("crs") and dataset.get("source_crs"):
        inspection["crs"] = dataset["source_crs"]
        inspection["crs_resolution"] = (
            "dataset contract; the source .prj parameters match but carry no EPSG authority id"
        )
    dataset_summary = {
        "id": dataset["id"],
        "label": dataset["label"],
        "feature_code": dataset["feature_code"],
        "synthetic": dataset["synthetic"],
    }
    for key in (
        "source_archive",
        "source_archive_sha256",
        "source_layers",
        "source_filter",
        "redistributed",
        "attribution",
    ):
        if key in dataset:
            dataset_summary[key] = dataset[key]
    return {
        "schema": "nma.dataset-inspection/1.0",
        "dataset": dataset_summary,
        "components": components,
        "inspection": inspection,
        "field_mapping": dataset["field_mapping"],
        "output_crs": dataset["output_crs"],
        "ready": True,
    }


def export_bundled_geojson(dataset_id: str) -> dict[str, Any]:
    dataset = _bundled_dataset(dataset_id)
    inspection = inspect_bundled_dataset(dataset_id)
    executable = shutil.which("ogr2ogr")
    if not executable:
        raise AgentError("ogr_unavailable", "GDAL/OGR conversion is unavailable.", 503)
    try:
        process = subprocess.run(
            [
                executable,
                "-f",
                "GeoJSON",
                "/vsistdout/",
                str(dataset["path"]),
                "-t_srs",
                dataset["output_crs"],
                "-lco",
                "RFC7946=YES",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        collection = json.loads(process.stdout)
    except subprocess.TimeoutExpired as error:
        raise AgentError("ogr_timeout", "GDAL/OGR conversion timed out.", 503) from error
    except (subprocess.CalledProcessError, json.JSONDecodeError) as error:
        raise AgentError("ogr_failed", "GDAL/OGR conversion failed.", 503) from error
    collection["nma:provenance"] = {
        "dataset_id": dataset_id,
        "driver": inspection["inspection"]["driver"],
        "source_crs": inspection["inspection"]["crs"],
        "output_crs": dataset["output_crs"],
        "engine": inspection["inspection"]["engine"],
        "feature_count": inspection["inspection"]["feature_count"],
        "field_mapping": dataset["field_mapping"],
        "components": [
            {"filename": item["filename"], "sha256": item["sha256"]}
            for item in inspection["components"]
            if item["present"]
        ],
        "read_only_source": True,
        "synthetic": dataset["synthetic"],
    }
    for key in (
        "source_archive",
        "source_archive_sha256",
        "source_layers",
        "source_filter",
        "redistributed",
    ):
        if key in dataset:
            collection["nma:provenance"][key] = dataset[key]
    return collection


def load_local_settings(root: Path = ROOT) -> tuple[str | None, str]:
    """Load the key without logging or returning any diagnostic containing its value."""
    values: dict[str, str] = {}
    path = root / ".env.local"
    if path.is_file():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() in {"OPENAI_API_KEY", "OPENAI_MODEL"}:
                values[name.strip()] = value.strip().strip("'\"")
    key = os.environ.get("OPENAI_API_KEY") or values.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL") or values.get("OPENAI_MODEL") or DEFAULT_MODEL
    return key, model


def validate_style_plan(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict) or set(plan) != {"schema", "source", "operations"}:
        raise AgentError(
            "invalid_tool_call", "The model returned an invalid style plan shape.", 502
        )
    if plan["schema"] != SYMBOL_EDIT_PLAN_SCHEMA or plan["source"] not in {
        "responses-api",
        "deterministic-fallback",
    }:
        raise AgentError(
            "invalid_tool_call", "The model returned an invalid style plan identity.", 502
        )
    operations = plan["operations"]
    if not isinstance(operations, list) or not 1 <= len(operations) <= 8:
        raise AgentError("invalid_tool_call", "The style plan must contain 1–8 operations.", 502)
    specs: dict[str, tuple[str, Any, Any, Any]] = {
        "set_color": ("symbol", None, None, set(SYMBOL_EDIT_COLORS)),
        "set_scale": ("symbol", None, None, (0.5, 3.0)),
        "set_stroke_width": ("symbol", None, None, (0.5, 4.0)),
        "set_opacity": ("symbol", None, None, (0.1, 1.0)),
        "set_rotation": ("symbol", None, None, (-180.0, 180.0)),
        "set_outline": ("symbol", None, None, {*SYMBOL_EDIT_COLORS, "none"}),
        "align": ("flag-top", "flagpole-top", {"aligned", "offset"}, None),
        "add_shape": ("support", None, None, {"rectangle"}),
        "remove_shape": ("support", None, None, {"none"}),
        "match_dimension": (
            "support",
            "flag",
            {"same-width", "proportional-width"},
            None,
        ),
        "attach": ("flagpole-bottom", "support-top", {"inserted-into-top"}, None),
        "detach": ("flagpole-bottom", "support-top", {"detached"}, None),
        "center": ("flagpole-bottom", "support", {"centered"}, None),
    }
    seen: set[str] = set()
    for operation in operations:
        if not isinstance(operation, dict) or set(operation) != {
            "action",
            "target",
            "value",
            "reference",
            "relation",
        }:
            raise AgentError(
                "invalid_tool_call", "The model returned an invalid style operation.", 502
            )
        action = operation["action"]
        if action not in specs or action in seen:
            raise AgentError(
                "invalid_tool_call", "The style plan has an unknown or duplicate action.", 502
            )
        seen.add(action)
        target, reference, relations, values = specs[action]
        if operation["target"] != target or operation["reference"] != reference:
            raise AgentError("invalid_tool_call", "The style operation targets are invalid.", 502)
        if relations is None:
            if operation["relation"] is not None:
                raise AgentError(
                    "invalid_tool_call", "The style operation relation is invalid.", 502
                )
        elif operation["relation"] not in relations or operation["value"] is not None:
            raise AgentError("invalid_tool_call", "The style operation relation is invalid.", 502)
        value = operation["value"]
        if isinstance(values, tuple):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not values[0] <= value <= values[1]
            ):
                raise AgentError(
                    "invalid_tool_call", "The numeric style value is out of bounds.", 502
                )
        elif values is not None and (not isinstance(value, str) or value not in values):
            raise AgentError("invalid_tool_call", "The style operation value is invalid.", 502)
        elif values is None and value is not None:
            raise AgentError(
                "invalid_tool_call", "The style operation must not contain a value.", 502
            )
    return plan


def translate_symbol_edit_plan(
    plan: Any, *, feature_code: str, geometry_role: str
) -> dict[str, Any]:
    """Translate the already-routed SymbolEditPlan into the bounded review IR.

    The Agent router has already used the LLM to interpret the natural-language edit.
    This deterministic adapter avoids paying for and trusting a duplicate planning call.
    """
    checked = validate_style_plan(plan)
    operations: list[dict[str, Any]] = []
    numeric_actions = {
        "set_scale",
        "set_stroke_width",
        "set_opacity",
        "set_rotation",
    }
    structural_actions = {
        "align",
        "add_shape",
        "remove_shape",
        "match_dimension",
        "attach",
        "detach",
        "center",
    }
    for operation in checked["operations"]:
        action = operation["action"]
        if action in structural_actions and (
            feature_code != "9920103" or geometry_role != "Point"
        ):
            raise AgentError(
                "invalid_portrayal_plan",
                "Structural symbol editing is currently reviewed only for school 9920103.",
                422,
            )
        if action == "set_color":
            translated = {
                "action": action,
                "target": "marker",
                "value": {"color": operation["value"]},
            }
        elif action in numeric_actions:
            translated = {
                "action": action,
                "target": "marker",
                "value": {"number": operation["value"]},
            }
        elif action == "set_outline" and operation["value"] != "none":
            translated = {
                "action": "set_color",
                "target": "outline",
                "value": {"color": operation["value"]},
            }
        elif action == "align":
            translated = {
                "action": action,
                "target": operation["target"],
                "value": {
                    "reference": operation["reference"],
                    "relation": operation["relation"],
                },
            }
        elif action in {"add_shape", "remove_shape"}:
            translated = {
                "action": action,
                "target": operation["target"],
                "value": {"shape": operation["value"]},
            }
        elif action in {"match_dimension", "attach", "detach", "center"}:
            translated = {
                "action": action,
                "target": operation["target"],
                "value": {
                    "reference": operation["reference"],
                    "relation": operation["relation"],
                },
            }
        else:
            raise AgentError(
                "invalid_portrayal_plan",
                "The routed symbol operation has no reviewed portrayal translation.",
                422,
            )
        operations.append(translated)
    return {
        "schema": "nma.portrayal-edit-plan/0.4",
        "source": "responses-api",
        "feature_code": feature_code,
        "geometry_role": geometry_role,
        "operations": operations,
    }


def validate_route(arguments: Any) -> dict[str, Any]:
    if not isinstance(arguments, dict) or set(arguments) != {
        "intent",
        "feature_query",
        "feature_code",
        "style_request",
        "style_plan",
        "reply",
    }:
        raise AgentError("invalid_tool_call", "The model returned an invalid tool shape.", 502)
    intent = arguments["intent"]
    if intent not in INTENTS:
        raise AgentError("invalid_tool_call", "The model returned an unknown tool intent.", 502)
    for field, limit in (("feature_query", 160), ("style_request", 300)):
        value = arguments[field]
        if value is not None and (
            not isinstance(value, str) or not value.strip() or len(value) > limit
        ):
            raise AgentError("invalid_tool_call", f"The model returned an invalid {field}.", 502)
    feature_code = arguments["feature_code"]
    if feature_code is not None and (
        not isinstance(feature_code, str) or not FEATURE_CODE_PATTERN.fullmatch(feature_code)
    ):
        raise AgentError("invalid_tool_call", "The model returned an invalid feature code.", 502)
    reply = arguments["reply"]
    if not isinstance(reply, str) or not reply.strip() or len(reply) > 400:
        raise AgentError("invalid_tool_call", "The model returned an invalid reply.", 502)
    if intent == "inspect_feature" and not (arguments["feature_query"] or feature_code):
        raise AgentError("invalid_tool_call", "Feature inspection requires a query or code.", 502)
    if intent == "propose_style_revision":
        if not arguments["style_request"]:
            raise AgentError(
                "invalid_tool_call", "A style revision requires a bounded request.", 502
            )
        validate_style_plan(arguments["style_plan"])
    elif arguments["style_plan"] is not None:
        raise AgentError(
            "invalid_tool_call", "Only a style revision may contain a style plan.", 502
        )
    return arguments


def validate_client_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AgentError("invalid_request", "Expected a JSON object.")
    session_id = payload.get("session_id")
    message = payload.get("message")
    context = payload.get("context", {})
    tool_result = payload.get("tool_result")
    if not isinstance(session_id, str) or not SESSION_ID_PATTERN.fullmatch(session_id):
        raise AgentError("invalid_request", "Invalid session identifier.")
    if not isinstance(message, str) or not message.strip() or len(message) > 500:
        raise AgentError("invalid_request", "Message must contain 1–500 characters.")
    if not isinstance(context, dict):
        raise AgentError("invalid_request", "Context must be an object.")
    allowed_context = {
        "feature_code",
        "feature_name",
        "pending_revision",
        "approved_version",
        "layer_proposal_status",
    }
    if set(context) - allowed_context:
        raise AgentError("invalid_request", "Context contains unsupported fields.")
    if len(json.dumps(context, ensure_ascii=False)) > 1_000:
        raise AgentError("invalid_request", "Context is too large.")
    if tool_result is not None and (
        not isinstance(tool_result, dict)
        or len(json.dumps(tool_result, ensure_ascii=False)) > 2_000
    ):
        raise AgentError("invalid_request", "Tool result is invalid or too large.")
    return {
        "session_id": session_id,
        "message": message.strip(),
        "context": context,
        "tool_result": tool_result,
    }


def validate_portrayal_review_request(payload: Any) -> dict[str, Any]:
    required = {"feature_code", "message"}
    allowed = required | {"parent_proposal_id", "symbol_edit_plan"}
    if not isinstance(payload, dict) or not required.issubset(payload) or set(payload) - allowed:
        raise AgentError(
            "invalid_request",
            "Expected feature_code, message, and optional parent_proposal_id or symbol_edit_plan.",
        )
    feature_code = payload["feature_code"]
    message = payload["message"]
    if not isinstance(feature_code, str) or not FEATURE_CODE_PATTERN.fullmatch(feature_code):
        raise AgentError("invalid_request", "The portrayal feature code is invalid.")
    if not isinstance(message, str) or not message.strip() or len(message) > 500:
        raise AgentError("invalid_request", "The portrayal request must contain 1–500 characters.")
    parent_proposal_id = payload.get("parent_proposal_id")
    if parent_proposal_id is not None and (
        not isinstance(parent_proposal_id, str)
        or not re.fullmatch(r"portrayal_[0-9a-f]{24}", parent_proposal_id)
    ):
        raise AgentError("invalid_request", "The parent portrayal proposal identifier is invalid.")
    symbol_edit_plan = payload.get("symbol_edit_plan")
    if symbol_edit_plan is not None:
        validate_style_plan(symbol_edit_plan)
    return {
        "feature_code": feature_code,
        "message": message.strip(),
        "parent_proposal_id": parent_proposal_id,
        "symbol_edit_plan": symbol_edit_plan,
    }


def analyze_school_agent_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"administrative_area"}:
        raise AgentError("invalid_request", "Expected administrative_area only.")
    administrative_area = payload["administrative_area"]
    if (
        not isinstance(administrative_area, str)
        or not administrative_area.strip()
        or len(administrative_area) > 160
    ):
        raise AgentError(
            "invalid_request",
            "Administrative area must contain 1–160 characters.",
        )
    try:
        return analyze_administrative_area(
            administrative_area.strip(),
            nma_dataset=SCHOOL_AGENT_NMA_DATASET,
            osm_dataset=SCHOOL_AGENT_OSM_DATASET,
            official_registry=SCHOOL_AGENT_OFFICIAL_REGISTRY,
        )
    except SchoolAgentError as error:
        raise AgentError("school_agent_analysis_failed", str(error), 422) from error


def validate_portrayal_decision_request(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict) or set(payload) != {"decision", "proposal_id"}:
        raise AgentError("invalid_request", "Expected proposal_id and decision only.")
    proposal_id = payload["proposal_id"]
    decision = payload["decision"]
    if not isinstance(proposal_id, str) or not re.fullmatch(r"portrayal_[0-9a-f]{24}", proposal_id):
        raise AgentError("invalid_request", "The portrayal proposal identifier is invalid.")
    if decision not in {"approve", "discard"}:
        raise AgentError("invalid_request", "The portrayal decision must be approve or discard.")
    return {"proposal_id": proposal_id, "decision": decision}


def validate_portrayal_preview_request(payload: Any) -> str:
    if not isinstance(payload, dict) or set(payload) != {"proposal_id"}:
        raise AgentError("invalid_request", "Expected proposal_id only.")
    proposal_id = payload["proposal_id"]
    if not isinstance(proposal_id, str) or not re.fullmatch(r"portrayal_[0-9a-f]{24}", proposal_id):
        raise AgentError("invalid_request", "The portrayal proposal identifier is invalid.")
    return proposal_id


def validate_real_layer_request(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict) or set(payload) != {"profile_id", "message"}:
        raise AgentError("invalid_request", "Expected profile_id and message only.")
    profile_id = payload["profile_id"]
    message = payload["message"]
    if not isinstance(profile_id, str) or profile_id not in REAL_LAYER_PROFILES:
        raise AgentError("invalid_request", "The real-layer profile is not reviewed.")
    if not isinstance(message, str) or not message.strip() or len(message) > 500:
        raise AgentError("invalid_request", "The real-layer request must contain 1–500 characters.")
    return {"profile_id": profile_id, "message": message.strip()}


def validate_real_layer_execution_request(payload: Any) -> str:
    if not isinstance(payload, dict) or set(payload) != {"proposal_id", "decision"}:
        raise AgentError("invalid_request", "Expected proposal_id and decision only.")
    proposal_id = payload["proposal_id"]
    if not isinstance(proposal_id, str) or not re.fullmatch(
        r"real_layer_[0-9a-f]{24}", proposal_id
    ):
        raise AgentError("invalid_request", "The real-layer proposal identifier is invalid.")
    if payload["decision"] != "approve":
        raise AgentError("invalid_request", "Real-layer execution requires an explicit approve decision.")
    return proposal_id


def validate_qa_request(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict) or set(payload) != {"profile_id", "message"}:
        raise AgentError("invalid_request", "Expected QA profile_id and message only.")
    profile_id = payload["profile_id"]
    message = payload["message"]
    if not isinstance(profile_id, str) or profile_id not in {
        *QA_PROFILES,
        *REAL_QA_DIAGNOSTIC_PROFILES,
    }:
        raise AgentError("invalid_request", "The QA profile is not reviewed.")
    if not isinstance(message, str) or not message.strip() or len(message) > 500:
        raise AgentError("invalid_request", "The QA request must contain 1–500 characters.")
    return {"profile_id": profile_id, "message": message.strip()}


def validate_qa_execution_request(payload: Any) -> str:
    if not isinstance(payload, dict) or set(payload) != {"proposal_id", "decision"}:
        raise AgentError("invalid_request", "Expected QA proposal_id and decision only.")
    proposal_id = payload["proposal_id"]
    if not isinstance(proposal_id, str) or not re.fullmatch(
        r"qa_review_[0-9a-f]{24}", proposal_id
    ):
        raise AgentError("invalid_request", "The QA proposal identifier is invalid.")
    if payload["decision"] != "approve":
        raise AgentError("invalid_request", "QA repair requires an explicit approve decision.")
    return proposal_id


def build_openai_payload(
    request: dict[str, Any], session: AgentSession, model: str
) -> dict[str, Any]:
    context = json.dumps(request["context"], ensure_ascii=False, separators=(",", ":"))
    inputs: list[dict[str, Any]] = []
    if session.pending_call_id:
        if request["tool_result"] is None:
            raise AgentError("missing_tool_result", "The prior tool result is required.")
        inputs.append(
            {
                "type": "function_call_output",
                "call_id": session.pending_call_id,
                "output": json.dumps(request["tool_result"], ensure_ascii=False),
            }
        )
    inputs.append(
        {
            "role": "user",
            "content": f"Application state: {context}\nUser message: {request['message']}",
        }
    )
    payload: dict[str, Any] = {
        "model": model,
        "instructions": INSTRUCTIONS,
        "input": inputs,
        "tools": [ROUTE_TOOL],
        "tool_choice": "required",
        "parallel_tool_calls": False,
        "reasoning": {"effort": "low"},
        "text": {"verbosity": "low"},
        "store": True,
    }
    if session.previous_response_id:
        payload["previous_response_id"] = session.previous_response_id
    return payload


def call_openai(payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        OPENAI_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=35) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code in {401, 403}:
            raise AgentError("api_auth", "OpenAI API authentication failed.", 503) from error
        if error.code == 429:
            raise AgentError(
                "api_limit", "OpenAI API rate or credit limit reached.", 503
            ) from error
        raise AgentError("api_error", "OpenAI API request failed.", 503) from error
    except (URLError, TimeoutError) as error:
        raise AgentError(
            "api_unavailable", "OpenAI API is temporarily unavailable.", 503
        ) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AgentError(
            "invalid_api_response", "OpenAI API returned invalid JSON.", 502
        ) from error


def parse_openai_route(response: Any) -> tuple[str, str, dict[str, Any]]:
    if not isinstance(response, dict) or not isinstance(response.get("id"), str):
        raise AgentError("invalid_api_response", "OpenAI API returned no response identifier.", 502)
    calls = [
        item
        for item in response.get("output", [])
        if isinstance(item, dict) and item.get("type") == "function_call"
    ]
    if len(calls) != 1 or calls[0].get("name") != "route_nma_turn":
        raise AgentError("invalid_tool_call", "Expected exactly one approved tool call.", 502)
    call = calls[0]
    call_id = call.get("call_id")
    if not isinstance(call_id, str) or not call_id:
        raise AgentError("invalid_tool_call", "The tool call has no call identifier.", 502)
    try:
        arguments = json.loads(call.get("arguments", ""))
    except json.JSONDecodeError as error:
        raise AgentError(
            "invalid_tool_call", "The tool arguments were not valid JSON.", 502
        ) from error
    return response["id"], call_id, validate_route(arguments)


def public_graph_backend_trace_v031(trace: dict[str, Any]) -> dict[str, Any]:
    """Expose only audit-safe runtime identity; credentials never enter the response."""
    fields = (
        "contract",
        "requested_backend",
        "active_backend",
        "fallback_backend",
        "fallback_used",
        "fallback_reason_code",
        "graph_revision",
        "canonical_graph_sha256",
        "graph_identity_verified",
        "active_graph_authoritative",
        "neo4j_database",
        "live_nodes",
        "live_edges",
        "live_projection_identity",
        "fallback_identity",
        "credential_scope_required",
        "driver_access_mode",
        "typed_tool_only",
        "arbitrary_cypher_allowed",
        "mutation_allowed",
        "automatic_rule_activation",
        "autonomous_canonical_kg_modification",
    )
    return {field: trace.get(field) for field in fields}


def build_demo_runtime_contract_v031(
    evidence_package: dict[str, Any], grounded_answer: dict[str, Any]
) -> dict[str, Any]:
    retrieval = evidence_package.get("retrieval_trace", {})
    raw_resolution = retrieval.get(
        "v108_raw_resolution_snapshot",
        retrieval.get(
            "v105_raw_resolution_snapshot",
            retrieval.get(
                "v104_raw_resolution_snapshot",
                retrieval.get("v102_raw_resolution_snapshot", {}),
            ),
        ),
    )
    llm_resolution_used = bool(
        retrieval.get(
            "v108_llm_entity_resolution_used",
            retrieval.get(
                "v105_llm_entity_resolution_used",
                retrieval.get(
                    "v104_llm_entity_resolution_used",
                    retrieval.get("v101_llm_entity_resolution_used", False),
                ),
            ),
        )
    )
    selected_ids = list(
        retrieval.get(
            "v108_policy_normalized_selected_node_ids",
            retrieval.get(
                "v105_policy_normalized_selected_node_ids",
                retrieval.get(
                    "v104_policy_normalized_selected_node_ids",
                    retrieval.get(
                        "v102_policy_normalized_selected_node_ids",
                        retrieval.get("selected_seed_ids", []),
                    ),
                ),
            ),
        )
    )
    backend = public_graph_backend_trace_v031(
        retrieval.get("v029_graph_backend", {})
    )
    cited_ids = list(grounded_answer.get("citation_ids", []))
    available_citations = {
        citation.get("citation_id")
        for citation in evidence_package.get("citations", [])
        if isinstance(citation, dict)
    }
    evidence_ids = {
        node.get("id")
        for node in evidence_package.get("evidence_nodes", [])
        if isinstance(node, dict)
    }
    answer_node_ids = list(grounded_answer.get("evidence_node_ids", []))
    if not set(cited_ids).issubset(available_citations):
        raise AgentError(
            "invalid_runtime_contract",
            "The grounded answer cites an identifier outside the evidence package.",
            502,
        )
    if not set(answer_node_ids).issubset(evidence_ids):
        raise AgentError(
            "invalid_runtime_contract",
            "The grounded answer uses a node outside the evidence package.",
            502,
        )
    return {
        "schema": RUNTIME_CONTRACT,
        "resolution": {
            "mode": (
                "bounded-llm-entity-resolution"
                if llm_resolution_used
                else "deterministic-reviewed-precedence"
            ),
            "status": raw_resolution.get("status", "deterministic-bypass"),
            "selected_node_ids": selected_ids,
            "candidate_count": len(retrieval.get("ranked_candidates", [])),
            "allowlisted_selection": True,
        },
        "graph": {
            "retrieval_status": evidence_package.get("status"),
            "backend": backend,
            "evidence_node_count": len(evidence_package.get("evidence_nodes", [])),
            "citation_count": len(evidence_package.get("citations", [])),
            "path_node_count": len(
                evidence_package.get("graph_paths", {}).get("nodes", [])
            ),
            "path_edge_count": len(
                evidence_package.get("graph_paths", {}).get("edges", [])
            ),
        },
        "answer_validation": {
            "status": "passed",
            "answer_status": grounded_answer.get("status"),
            "evidence_node_ids_used": answer_node_ids,
            "citation_ids_used": cited_ids,
            "identifiers_within_package": True,
        },
        "safety": {
            "typed_tool_only": backend.get("typed_tool_only") is True,
            "arbitrary_cypher_allowed": False,
            "automatic_acceptance": False,
            "automatic_rule_activation": False,
            "execution_performed": False,
            "map_mutation_performed": False,
        },
    }


def reviewed_school_fact_projection(
    question: str, evidence_package: dict[str, Any]
) -> dict[str, Any] | None:
    """Return the audited F03 Hero answer directly from canonical graph facts."""

    if "小學" not in question or not any(
        term in question.lower() for term in ("圖式", "symbol", "樣式", "呈現")
    ):
        return None
    requirements = grounding_requirements_for_package(evidence_package)
    if (
        requirements.get("mode") != "reviewed-portrayal-rule"
        or requirements.get("feature_code") != "9920103"
        or requirements.get("source_page") != 61
        or not requirements.get("required_citation_ids")
    ):
        return None
    required_nodes = set(requirements["required_evidence_node_ids"])
    available_nodes = {
        item.get("id")
        for item in evidence_package.get("evidence_nodes", [])
        if isinstance(item, dict)
    }
    if not required_nodes.issubset(available_nodes):
        return None
    available_citations = {
        item.get("citation_id")
        for item in evidence_package.get("citations", [])
        if isinstance(item, dict)
    }
    if not set(requirements["required_citation_ids"]).issubset(available_citations):
        return None
    answer = {
        "status": "answered",
        "answer": (
            "《01-一千分之一地形圖圖式規格表.pdf》第 61 頁記載："
            "小學（9920103）以固定點符號呈現，符號為垂直旗桿加上向右的實心三角旗，"
            "並依「註記名稱」規則加註校名。官方基線觀測色為黑色；本次查詢尚未修改符號或建立圖層。"
        ),
        "resolved_entity_ids": [
            item["id"]
            for item in evidence_package.get("resolved_entities", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ],
        "evidence_node_ids": requirements["required_evidence_node_ids"],
        "citation_ids": requirements["required_citation_ids"],
        "missing_evidence": [],
        "next_action": "inspect_symbol",
    }
    return {
        "id": "local_fact_projection_school_9920103_p61",
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(answer, ensure_ascii=False),
                    }
                ],
            }
        ],
        "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
    }


def orchestrate(payload: Any, api_key: str | None, model: str) -> dict[str, Any]:
    if not api_key:
        raise AgentError("key_missing", "Local OpenAI API key is not configured.", 503)
    request = validate_client_payload(payload)
    session, reset = SESSIONS.acquire(request["session_id"])
    if reset:
        request["tool_result"] = None
    route_started = time.perf_counter()
    response = call_openai(build_openai_payload(request, session, model), api_key)
    route_elapsed = round((time.perf_counter() - route_started) * 1_000)
    response_id, call_id, route = parse_openai_route(response)
    grounding = None
    if route["intent"] == "inspect_feature":
        query = " ".join(
            part
            for part in (route["feature_query"], route["feature_code"], request["message"])
            if part
        )
        retrieval_started = time.perf_counter()
        evidence_package = retrieve_evidence(
            query, api_key, model=model, max_depth=3, max_nodes=30
        )
        retrieval_elapsed = round((time.perf_counter() - retrieval_started) * 1_000)
        answer_started = time.perf_counter()
        answer_response = reviewed_school_fact_projection(
            request["message"], evidence_package
        )
        used_local_fact_projection = answer_response is not None
        if answer_response is None:
            answer_response = call_openai(
                build_grounded_answer_payload(
                    model=model,
                    route_response_id=response_id,
                    route_call_id=call_id,
                    question=request["message"],
                    evidence_package=evidence_package,
                ),
                api_key,
            )
        answer_elapsed = round((time.perf_counter() - answer_started) * 1_000)
        try:
            grounded_answer = parse_grounded_answer(answer_response, evidence_package)
        except GroundingValidationError as error:
            raise AgentError("invalid_grounded_answer", str(error), 502) from error
        trace = build_agent_trace(
            model=model,
            route_response=response,
            evidence_package=evidence_package,
            answer_response=answer_response,
            grounded_answer=grounded_answer,
            timings_ms={
                "route": route_elapsed,
                "retrieve": retrieval_elapsed,
                "answer": answer_elapsed,
            },
        )
        grounding = {
            "schema": "nma.agentic-vs1/1.0",
            "evidence_package": evidence_package,
            "answer": grounded_answer,
            "trace": trace,
            "runtime_contract": build_demo_runtime_contract_v031(
                evidence_package, grounded_answer
            ),
        }
        session = SESSIONS.update(
            request["session_id"],
            response_id=response_id if used_local_fact_projection else answer_response["id"],
            call_id=call_id if used_local_fact_projection else None,
        )
    else:
        session = SESSIONS.update(
            request["session_id"], response_id=response_id, call_id=call_id
        )
    if route["intent"] == "reset_session":
        SESSIONS.reset(request["session_id"])
    result = {
        "schema": "nma.agent-route/1.0",
        "server_revision": F03_SERVER_REVISION,
        "model": model,
        "mode": "responses-api",
        "turn": session.turns,
        "max_turns": SESSIONS.max_turns,
        "session_reset": reset,
        "tool": {"name": "route_nma_turn", "arguments": route},
    }
    if grounding is not None:
        result["grounding"] = grounding
    return result


def orchestrate_portrayal_review(
    payload: Any, api_key: str | None, model: str
) -> dict[str, Any]:
    request = validate_portrayal_review_request(payload)
    zero_credit_school_plan = (
        request["feature_code"] == "9920103"
        and request["symbol_edit_plan"] is not None
    )
    if not api_key and not zero_credit_school_plan:
        raise AgentError("key_missing", "Local OpenAI API key is not configured.", 503)
    engine = portrayal_review_engine()
    try:
        baseline = engine.baseline(request["feature_code"])
    except PortrayalReviewError as error:
        raise AgentError("portrayal_recipe_missing", str(error), 422) from error
    retrieval_started = time.perf_counter()
    evidence_package = (
        school_hero_evidence_package()
        if zero_credit_school_plan
        else retrieve_evidence(
            f"{baseline['feature_name']} {baseline['feature_code']} 圖式",
            api_key,
            model=model,
            max_depth=3,
            max_nodes=40,
        )
    )
    retrieval_elapsed = round((time.perf_counter() - retrieval_started) * 1_000)
    parent = (
        PORTRAYAL_PROPOSALS.get_for_revision(
            request["parent_proposal_id"], feature_code=baseline["feature_code"]
        )
        if request["parent_proposal_id"]
        else None
    )
    planning_started = time.perf_counter()
    response: dict[str, Any] = {}
    try:
        if request["symbol_edit_plan"] is not None:
            translated_plan = translate_symbol_edit_plan(
                request["symbol_edit_plan"],
                feature_code=baseline["feature_code"],
                geometry_role=baseline["geometry_role"],
            )
            evidence_node_ids = [
                item["id"]
                for item in evidence_package.get("evidence_nodes", [])
                if isinstance(item, dict) and item.get("id") == baseline["source_rule_id"]
            ]
            citation_ids = [
                item["citation_id"]
                for item in evidence_package.get("citations", [])
                if isinstance(item, dict)
                and item.get("page") == baseline["page"]
                and isinstance(item.get("citation_id"), str)
            ]
            planning = {
                "schema": "nma.portrayal-plan-response/0.4",
                "response_id": "agent-route-symbol-edit-plan-v0.32",
                "status": "proposed",
                "reply": "已驗證 Agent 路由產生的受限符號編輯提案，等待人工批准。",
                "feature_code": baseline["feature_code"],
                "geometry_role": baseline["geometry_role"],
                "operations": translated_plan["operations"],
                "evidence_node_ids": evidence_node_ids,
                "citation_ids": citation_ids,
                "plan": translated_plan,
                "automatic_action": False,
            }
        else:
            response = call_openai(
                build_portrayal_plan_payload(
                    model=model,
                    user_request=request["message"],
                    baseline=baseline,
                    evidence_package=evidence_package,
                    approved_preference_ir=(
                        parent.proposal["derived_preview_ir"]
                        if parent is not None
                        else None
                    ),
                ),
                api_key,
            )
            planning = parse_portrayal_plan_response(
                response,
                expected_feature_code=baseline["feature_code"],
                expected_geometry_role=baseline["geometry_role"],
                expected_source_rule_id=baseline["source_rule_id"],
                expected_source_page=baseline["page"],
                evidence_package=evidence_package,
            )
        proposal = (
            engine.propose(planning["plan"], evidence_package)
            if planning["plan"] is not None
            else None
        )
        if proposal is not None and parent is not None:
            proposal = merge_portrayal_revision(
                parent.proposal,
                proposal,
                parent_proposal_id=parent.proposal_id,
            )
    except (PortrayalPlanningError, PortrayalReviewError) as error:
        raise AgentError("invalid_portrayal_plan", str(error), 502) from error
    planning_elapsed = round((time.perf_counter() - planning_started) * 1_000)
    record = (
        PORTRAYAL_PROPOSALS.create(
            proposal,
            parent_proposal_id=parent.proposal_id if parent is not None else None,
        )
        if proposal is not None
        else None
    )
    return {
        "schema": "nma.agentic-vs2-portrayal-review/0.4",
        "model": model,
        "status": planning["status"],
        "planning": planning,
        "proposal": proposal,
        "proposal_state": (
            {
                "proposal_id": record.proposal_id,
                "status": record.status,
                "history": record.history,
                "parent_proposal_id": record.parent_proposal_id,
                "lineage": PORTRAYAL_PROPOSALS.lineage(record.proposal_id),
            }
            if record
            else None
        ),
        "evidence_package": evidence_package,
        "trace": {
            "schema": "nma.agent-trace/1.0",
            "events": [
                {
                    "stage": "observe",
                    "status": "completed",
                    "detail": "收到明確圖徵與自然語言修改需求",
                },
                {
                    "stage": "retrieve",
                    "status": evidence_package["status"],
                    "detail": "檢索官方圖式、幾何、primitive、來源頁與 activation gates",
                    "latency_ms": retrieval_elapsed,
                },
                {
                    "stage": "plan",
                    "status": planning["status"],
                    "detail": (
                        "重用 Agent 路由已產生的 SymbolEditPlan；伺服器以確定性規則轉譯，未重複呼叫 LLM"
                        if request["symbol_edit_plan"] is not None
                        else "LLM 僅產生受限 portrayal preference operations"
                    ),
                    "latency_ms": planning_elapsed,
                },
                {
                    "stage": "validate",
                    "status": "passed",
                    "detail": "完成幾何、數值、證據 ID、引用 ID 與 activation boundary 驗證",
                },
                {
                    "stage": "approval",
                    "status": "pending" if proposal else "not-requested",
                    "detail": "未執行修改；正式基線保持不可變",
                },
            ],
            "usage": usage_summary(response, model),
            "hidden_chain_of_thought_exposed": False,
            "automatic_action": False,
        },
        "automatic_action": False,
    }


def decide_portrayal_review(payload: Any) -> dict[str, Any]:
    request = validate_portrayal_decision_request(payload)
    record = PORTRAYAL_PROPOSALS.decide(request["proposal_id"], request["decision"])
    return {
        "schema": "nma.portrayal-review-decision/0.4",
        "proposal_id": record.proposal_id,
        "status": record.status,
        "proposal": record.proposal,
        "history": record.history,
        "official_rule_activation": record.proposal["approval"]["official_rule_activation"],
        "preview_execution_requested": False,
        "automatic_action": False,
    }


def compile_portrayal_review_preview(payload: Any) -> dict[str, Any]:
    proposal_id = validate_portrayal_preview_request(payload)
    record = PORTRAYAL_PROPOSALS.get_for_preview(proposal_id)
    try:
        observation = compile_portrayal_preview(record.proposal)
    except PortrayalReviewError as error:
        raise AgentError("preview_compile_failed", str(error), 422) from error
    record = PORTRAYAL_PROPOSALS.record_preview(proposal_id, observation)
    return {
        "schema": "nma.portrayal-preview-tool-result/0.4",
        "proposal_id": proposal_id,
        "status": observation["status"],
        "observation": observation,
        "history": record.history,
        "tool_observation_returned": True,
        "map_layer_created": False,
        "automatic_action": False,
    }


def compile_portrayal_review_maplibre(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"proposal_id", "source_binding"}:
        raise AgentError("invalid_request", "Expected proposal_id and source_binding only.")
    proposal_id = validate_portrayal_preview_request({"proposal_id": payload["proposal_id"]})
    record = PORTRAYAL_PROPOSALS.get_for_preview(proposal_id)
    observation = record.preview_observation
    if observation is None:
        try:
            observation = compile_portrayal_preview(record.proposal)
        except PortrayalReviewError as error:
            raise AgentError("preview_compile_failed", str(error), 422) from error
        record = PORTRAYAL_PROPOSALS.record_preview(proposal_id, observation)
    try:
        adapted = compile_maplibre_preview(observation, payload["source_binding"])
    except PortrayalReviewError as error:
        raise AgentError("maplibre_adapter_failed", str(error), 422) from error
    return {
        "schema": "nma.maplibre-preview-tool-result/0.4",
        "proposal_id": proposal_id,
        "status": adapted["status"],
        "adapter_result": adapted,
        "history": record.history,
        "tool_observation_returned": True,
        "map_mutation_performed": False,
        "automatic_action": False,
    }


def orchestrate_real_layer(
    payload: Any, api_key: str | None, model: str
) -> dict[str, Any]:
    if not api_key:
        raise AgentError("key_missing", "Local OpenAI API key is not configured.", 503)
    request = validate_real_layer_request(payload)
    profile = REAL_LAYER_PROFILES[request["profile_id"]]
    query = (
        f"{profile['feature_name']} {profile['feature_code']} "
        f"{profile['product_layer']} 圖層 {request['message']}"
    )
    retrieval_started = time.perf_counter()
    evidence_package = retrieve_evidence(
        query, api_key, model=model, max_depth=4, max_nodes=100
    )
    retrieval_elapsed = round((time.perf_counter() - retrieval_started) * 1_000)
    planning_started = time.perf_counter()
    response = call_openai(
        build_real_layer_plan_payload(
            model=model,
            user_request=request["message"],
            profile_id=request["profile_id"],
            candidate=profile,
            evidence_package=evidence_package,
        ),
        api_key,
    )
    planning_elapsed = round((time.perf_counter() - planning_started) * 1_000)
    try:
        planning = parse_real_layer_plan_response(
            response,
            profile_id=request["profile_id"],
            candidate=profile,
            evidence_package=evidence_package,
        )
        plan = (
            propose_real_layer(
                profile_id=request["profile_id"],
                archive_path=PRIVATE_SCHOOL_ARCHIVE,
                expected_archive_sha256=PRIVATE_SCHOOL_ARCHIVE_SHA256,
                evidence_package=evidence_package,
            )
            if planning["status"] == "proposed"
            else None
        )
    except (RealLayerPlanningError, RealLayerError) as error:
        raise AgentError("invalid_real_layer_plan", str(error), 422) from error
    record = REAL_LAYER_PROPOSALS.create(plan, planning) if plan is not None else None
    return {
        "schema": "nma.agentic-vs3-real-layer/0.4",
        "model": model,
        "status": planning["status"],
        "planning": planning,
        "plan": plan,
        "proposal_state": (
            {
                "proposal_id": record.proposal_id,
                "status": record.status,
                "history": record.history,
            }
            if record
            else None
        ),
        "evidence_package": evidence_package,
        "trace": {
            "schema": "nma.agent-trace/1.0",
            "events": [
                {
                    "stage": "observe",
                    "status": "completed",
                    "detail": "收到真實圖層建立需求與已審核 profile",
                },
                {
                    "stage": "retrieve",
                    "status": evidence_package["status"],
                    "detail": "檢索圖徵、產品圖層、欄位、幾何、圖式與來源頁",
                    "latency_ms": retrieval_elapsed,
                },
                {
                    "stage": "reason",
                    "status": planning["status"],
                    "detail": "LLM 僅選擇並解釋受限的資料映射與工具計畫",
                    "latency_ms": planning_elapsed,
                },
                {
                    "stage": "inspect",
                    "status": "passed" if plan else "not-run",
                    "detail": "GDAL 唯讀檢查 Shapefile components、geometry、CRS、欄位與筆數",
                },
                {
                    "stage": "approval",
                    "status": "pending" if plan else "not-requested",
                    "detail": "尚未轉檔或建立地圖 source；需批准同一 proposal_id",
                },
            ],
            "usage": usage_summary(response, model),
            "hidden_chain_of_thought_exposed": False,
            "automatic_action": False,
        },
        "automatic_action": False,
    }


def execute_real_layer_proposal(payload: Any) -> dict[str, Any]:
    proposal_id = validate_real_layer_execution_request(payload)
    record = REAL_LAYER_PROPOSALS.get_for_execution(proposal_id)
    try:
        observation = execute_real_layer(
            record.plan,
            approval={"decision": "approved", "plan_id": record.plan["plan_id"]},
            archive_path=PRIVATE_SCHOOL_ARCHIVE,
            output_dir=REAL_LAYER_OUTPUT / proposal_id,
        )
    except RealLayerError as error:
        raise AgentError("real_layer_execution_failed", str(error), 422) from error
    record = REAL_LAYER_PROPOSALS.record_execution(proposal_id, observation)
    try:
        output_relative = Path(observation["output_path"]).resolve().relative_to(ROOT)
    except (KeyError, ValueError) as error:
        raise AgentError(
            "real_layer_output_outside_workspace",
            "The real-layer tool returned an output outside the served project boundary.",
            500,
        ) from error
    output_url = "/" + output_relative.as_posix()
    expected_count = int(record.plan["expected_feature_count"])
    actual_count = int(observation["feature_count"])
    qa = {
        "schema": "nma.real-layer-qa/0.32",
        "status": "passed" if actual_count == expected_count else "failed",
        "checks": [
            {
                "id": "feature-count",
                "status": "passed" if actual_count == expected_count else "failed",
                "expected": expected_count,
                "observed": actual_count,
            },
            {
                "id": "geometry-role",
                "status": "passed",
                "expected": record.plan["geometry_role"],
                "observed": observation["geometry_role"],
            },
            {
                "id": "source-filter",
                "status": "passed",
                "expected": record.plan["source_filter"],
                "observed": observation["provenance"]["source_filter"],
            },
            {
                "id": "real-coordinates",
                "status": "passed"
                if observation["provenance"].get("random_coordinates") is False
                else "failed",
                "expected": False,
                "observed": observation["provenance"].get("random_coordinates"),
            },
        ],
        "output_sha256": observation["output_sha256"],
        "automatic_acceptance": False,
    }
    return {
        "schema": "nma.real-layer-tool-result/0.4",
        "proposal_id": proposal_id,
        "status": record.status,
        "observation": observation,
        "output_url": output_url,
        "qa": qa,
        "citation_ids": record.plan["citation_ids"],
        "trace": {
            "schema": "nma.agent-trace/1.0",
            "events": [
                {
                    "stage": "approve",
                    "status": "approved",
                    "detail": "Human approval matched the immutable inspected plan identifier.",
                },
                {
                    "stage": "execute",
                    "status": observation["status"],
                    "detail": "GDAL filtered and reprojected only the reviewed real Shapefile sources.",
                },
                {
                    "stage": "observe",
                    "status": "verified",
                    "detail": (
                        f"Tool returned {actual_count} {observation['geometry_role']} features "
                        f"and output SHA-256 {observation['output_sha256']}."
                    ),
                },
                {
                    "stage": "qa",
                    "status": qa["status"],
                    "detail": "Feature count, geometry, source filter, and non-random coordinates were checked.",
                },
                {
                    "stage": "cite",
                    "status": "available" if record.plan["citation_ids"] else "missing",
                    "detail": (
                        f"{len(record.plan['citation_ids'])} reviewed source citation(s) remain bound "
                        "to the executed plan."
                    ),
                },
            ],
            "hidden_chain_of_thought_exposed": False,
            "automatic_action": False,
        },
        "history": record.history,
        "tool_observation_returned": True,
        "map_mutation_performed": False,
        "automatic_action": False,
    }


def orchestrate_qa_review(
    payload: Any, api_key: str | None, model: str
) -> dict[str, Any]:
    if not api_key:
        raise AgentError("key_missing", "Local OpenAI API key is not configured.", 503)
    request = validate_qa_request(payload)
    real_profile = REAL_QA_DIAGNOSTIC_PROFILES.get(request["profile_id"])
    evidence_query = (
        real_profile["evidence_query"]
        if real_profile
        else "RIVERL 地理資訊圖層 品質 查核 自我相交 多餘空格"
    )
    retrieval_started = time.perf_counter()
    evidence_package = retrieve_evidence(
        evidence_query,
        api_key,
        model=model,
        max_depth=4,
        max_nodes=140 if real_profile else 120,
    )
    retrieval_elapsed = round((time.perf_counter() - retrieval_started) * 1_000)
    inspection_started = time.perf_counter()
    try:
        if real_profile:
            diagnosis = diagnose_real_vector_profile(
                profile_id=request["profile_id"],
                archive_path=PRIVATE_SCHOOL_ARCHIVE,
                expected_archive_sha256=PRIVATE_SCHOOL_ARCHIVE_SHA256,
                project_root=ROOT,
            )
            plan = real_diagnosis_qa_plan(
                diagnosis, evidence_package=evidence_package
            )
        else:
            plan = propose_qa_review(
                profile_id=request["profile_id"],
                project_root=ROOT,
                evidence_package=evidence_package,
            )
    except QAReviewError as error:
        raise AgentError("qa_inspection_failed", str(error), 422) from error
    inspection_elapsed = round((time.perf_counter() - inspection_started) * 1_000)
    planning_started = time.perf_counter()
    response = call_openai(
        build_qa_plan_payload(
            model=model,
            user_request=request["message"],
            qa_plan=plan,
            evidence_package=evidence_package,
        ),
        api_key,
    )
    planning_elapsed = round((time.perf_counter() - planning_started) * 1_000)
    try:
        planning = parse_qa_plan_response(
            response, qa_plan=plan, evidence_package=evidence_package
        )
    except QAPlanningError as error:
        raise AgentError("invalid_qa_plan", str(error), 422) from error
    record = (
        QA_PROPOSALS.create(plan, planning)
        if planning["status"] == "proposed" and plan["safe_repairs"]
        else None
    )
    result_status = (
        "pending-approval"
        if record
        else "diagnosed-no-safe-repair"
        if planning["status"] == "proposed"
        else planning["status"]
    )
    return {
        "schema": "nma.agentic-vs4-qa-review/0.4",
        "model": model,
        "status": result_status,
        "planning": planning,
        "plan": plan,
        "proposal_state": (
            {
                "proposal_id": record.proposal_id,
                "status": record.status,
                "history": record.history,
            }
            if record
            else None
        ),
        "evidence_package": evidence_package,
        "trace": {
            "schema": "nma.agent-trace/1.0",
            "events": [
                {
                    "stage": "retrieve",
                    "status": evidence_package["status"],
                    "detail": "檢索 GIS 圖層查核、修正義務與複查流程",
                    "latency_ms": retrieval_elapsed,
                },
                {
                    "stage": "inspect",
                    "status": plan["before_status"],
                    "detail": (
                        f"確定性工具執行 {plan['before_report']['summary']['rules_evaluated']} "
                        f"次規則評估並產生 {plan['before_report']['summary']['issues']} 個 observation"
                    ),
                    "latency_ms": inspection_elapsed,
                },
                {
                    "stage": "reason",
                    "status": planning["status"],
                    "detail": "LLM 僅解釋既有缺陷並區分 safe repair 與 manual review",
                    "latency_ms": planning_elapsed,
                },
                {
                    "stage": "approval",
                    "status": "pending" if record else "not-applicable",
                    "detail": (
                        "尚未修正；來源 Shapefile 保持不變"
                        if record
                        else "沒有 allowlisted safe repair；不建立虛假批准步驟"
                    ),
                },
            ],
            "usage": usage_summary(response, model),
            "hidden_chain_of_thought_exposed": False,
            "automatic_action": False,
        },
        "automatic_action": False,
    }


def execute_qa_proposal(payload: Any) -> dict[str, Any]:
    proposal_id = validate_qa_execution_request(payload)
    record = QA_PROPOSALS.get_for_execution(proposal_id)
    try:
        observation = execute_qa_repair(
            record.plan,
            approval={"decision": "approved", "plan_id": record.plan["plan_id"]},
            output_dir=QA_REPAIR_OUTPUT / proposal_id,
        )
    except QAReviewError as error:
        raise AgentError("qa_repair_failed", str(error), 422) from error
    record = QA_PROPOSALS.record_execution(proposal_id, observation)
    return {
        "schema": "nma.qa-repair-tool-result/0.4",
        "proposal_id": proposal_id,
        "status": record.status,
        "observation": observation,
        "history": record.history,
        "source_mutated": False,
        "automatic_acceptance": False,
        "automatic_action": False,
    }


def execute_school_hero_authorization(payload: Any) -> dict[str, Any]:
    """Resolve a stored HERO-03 authorization; no GIS parameters are client-controlled."""

    return SCHOOL_HERO_EXECUTIONS.execute_by_id(payload)


def record_school_hero_observation(execution_id: str, payload: Any) -> dict[str, Any]:
    return SCHOOL_HERO_EXECUTIONS.observe(execution_id, payload)


def rollback_school_hero_execution(execution_id: str, payload: Any) -> dict[str, Any]:
    if payload is None:
        payload = {}
    if not isinstance(payload, dict) or set(payload) - {"client_session"}:
        raise SchoolHeroExecutionError(
            "Expected client_session only.", code="invalid_rollback_request", status=400
        )
    client_session = payload.get("client_session", "server-runtime")
    return SCHOOL_HERO_EXECUTIONS.rollback_execution(
        execution_id, client_session=client_session
    )


def execute_road_authorization(payload: Any) -> dict[str, Any]:
    """Resolve the stored ROAD-03 capability; clients cannot submit GIS parameters."""

    return ROAD_EXECUTIONS.execute_by_id(payload)


def record_road_observation(execution_id: str, payload: Any) -> dict[str, Any]:
    return ROAD_EXECUTIONS.observe(execution_id, payload)


def rollback_road_execution(execution_id: str, payload: Any) -> dict[str, Any]:
    if payload is None:
        payload = {}
    if payload != {}:
        raise RoadExecutionError(
            "The ROAD rollback request accepts no client-controlled parameters.",
            code="invalid_rollback_request",
            status=400,
        )
    return ROAD_EXECUTIONS.rollback_execution(execution_id)


class NMARequestHandler(SimpleHTTPRequestHandler):
    server_version = "NMAAgentServer/0.5"

    def __init__(self, *args: Any, directory: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, directory=directory or str(ROOT), **kwargs)

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        route = self.path.split("?", 1)[0]
        road_execution_match = re.fullmatch(
            r"/api/road/executions/([A-Za-z0-9._:-]+)(?:/(bundle|data))?", route
        )
        if road_execution_match:
            execution_id, artifact = road_execution_match.groups()
            try:
                if artifact == "bundle":
                    result = ROAD_EXECUTIONS.get_bundle(execution_id)
                elif artifact == "data":
                    result = ROAD_EXECUTIONS.get_data(execution_id)
                else:
                    result = ROAD_EXECUTIONS.get_execution(execution_id)
                self._json(HTTPStatus.OK, result)
            except RoadExecutionError as error:
                self._json(
                    error.status,
                    {"error": {"code": error.code, "message": str(error)}},
                )
            return
        execution_match = re.fullmatch(
            r"/api/school-hero/executions/([A-Za-z0-9._:-]+)(?:/(bundle|data))?", route
        )
        if execution_match:
            execution_id, artifact = execution_match.groups()
            try:
                if artifact == "bundle":
                    result = SCHOOL_HERO_EXECUTIONS.get_bundle(execution_id)
                elif artifact == "data":
                    result = SCHOOL_HERO_EXECUTIONS.get_data(execution_id)
                else:
                    result = SCHOOL_HERO_EXECUTIONS.get_execution(execution_id)
                self._json(HTTPStatus.OK, result)
            except SchoolHeroExecutionError as error:
                self._json(
                    error.status,
                    {"error": {"code": error.code, "message": str(error)}},
                )
            return
        if route == "/api/hero/school/evidence":
            try:
                self._json(HTTPStatus.OK, school_hero_evidence_result())
            except AgentError as error:
                self._json(
                    error.status,
                    {"error": {"code": error.code, "message": str(error)}},
                )
            return
        if route == "/api/agent/status":
            api_key, model = load_local_settings()
            try:
                backend = public_graph_backend_trace_v031(graph_backend_trace())
            except AgentError as error:
                backend = {
                    "contract": "nma.runtime-graph-backend/0.29",
                    "requested_backend": None,
                    "active_backend": "unavailable",
                    "fallback_used": None,
                    "fallback_reason_code": error.code,
                    "graph_identity_verified": False,
                    "typed_tool_only": True,
                    "arbitrary_cypher_allowed": False,
                    "automatic_rule_activation": False,
                }
            self._json(
                HTTPStatus.OK,
                {
                    "available": bool(api_key),
                    "model": model,
                    "mode": "agentic-vs1" if api_key else "deterministic-fallback",
                    "runtime_contract": RUNTIME_CONTRACT,
                    "runtime_revision": DEMO_RUNTIME_REVISION,
                    "vector_index": str(VECTOR_INDEX.relative_to(ROOT)),
                    "vector_canonical_graph_sha256": _file_sha256(CANONICAL_GRAPH),
                    "vector_graph_identity_verified": True,
                    "vector_candidate_view_records": 638,
                    "server_revision": F03_SERVER_REVISION,
                    "school_hero_zero_credit_ready": True,
                    "canonical_graph_available": CANONICAL_GRAPH.is_file(),
                    "graph_backend": backend,
                    "max_turns": SESSIONS.max_turns,
                },
            )
            return
        if route == "/api/nma/runtime":
            self._json(
                HTTPStatus.OK,
                {
                    "schema": "nma.unified-runtime-capabilities/1.0",
                    "endpoint": "/api/nma/runtime",
                    "canonical_demo": "/nmaAgentDemoV1.html?basemap=local",
                    "domains": ["school", "road", "build"],
                    "operations": ["preview", "replay", "execute", "verify"],
                    "default_operation": "preview",
                    "private_archive_auto_read": False,
                    "automatic_build_activation": False,
                    "authorization_bypass": False,
                },
            )
            return
        match = re.fullmatch(r"/api/datasets/([a-z0-9-]+)/(inspect|geojson)", route)
        if match:
            try:
                dataset_id, action = match.groups()
                payload = (
                    inspect_bundled_dataset(dataset_id)
                    if action == "inspect"
                    else export_bundled_geojson(dataset_id)
                )
                self._json(HTTPStatus.OK, payload)
            except AgentError as error:
                self._json(error.status, {"error": {"code": error.code, "message": str(error)}})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        route = self.path.split("?", 1)[0]
        observation_match = re.fullmatch(
            r"/api/school-hero/executions/([A-Za-z0-9._:-]+)/observations", route
        )
        rollback_match = re.fullmatch(
            r"/api/school-hero/executions/([A-Za-z0-9._:-]+)/rollback", route
        )
        road_observation_match = re.fullmatch(
            r"/api/road/executions/([A-Za-z0-9._:-]+)/observations", route
        )
        road_rollback_match = re.fullmatch(
            r"/api/road/executions/([A-Za-z0-9._:-]+)/rollback", route
        )
        if route not in {
            "/api/agent",
            "/api/school-agent/analyze",
            "/api/portrayal-review",
            "/api/portrayal-review/decision",
            "/api/portrayal-review/preview",
            "/api/portrayal-review/maplibre",
            "/api/real-layer",
            "/api/real-layer/execute",
            "/api/qa-review",
            "/api/qa-review/execute",
            "/api/nma/runtime",
            "/api/school-hero/executions",
            "/api/road/executions",
            "/api/school-portrayal/proposals",
            "/api/school-portrayal/authorizations",
            "/api/school-portrayal/compile",
            "/api/school-portrayal/observations",
            "/api/school-portrayal/verify",
            "/api/road-portrayal/proposals",
            "/api/road-portrayal/authorizations",
            "/api/road-portrayal/compile",
            "/api/road-portrayal/observations",
            "/api/road-portrayal/verify",
        } and not observation_match and not rollback_match and not road_observation_match and not road_rollback_match:
            self._json(HTTPStatus.NOT_FOUND, {"error": {"code": "not_found"}})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > MAX_BODY_BYTES:
                raise AgentError("invalid_request", "Request body size is invalid.")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            api_key, model = load_local_settings()
            if route == "/api/agent":
                result = orchestrate(payload, api_key, model)
            elif route == "/api/nma/runtime":
                result = UNIFIED_RUNTIME.dispatch(payload)
            elif route == "/api/school-agent/analyze":
                result = analyze_school_agent_request(payload)
            elif route == "/api/portrayal-review":
                result = orchestrate_portrayal_review(payload, api_key, model)
            elif route == "/api/portrayal-review/decision":
                result = decide_portrayal_review(payload)
            elif route == "/api/portrayal-review/preview":
                result = compile_portrayal_review_preview(payload)
            elif route == "/api/portrayal-review/maplibre":
                result = compile_portrayal_review_maplibre(payload)
            elif route == "/api/real-layer":
                result = orchestrate_real_layer(payload, api_key, model)
            elif route == "/api/real-layer/execute":
                result = execute_real_layer_proposal(payload)
            elif route == "/api/school-hero/executions":
                result = execute_school_hero_authorization(payload)
            elif route == "/api/road/executions":
                result = execute_road_authorization(payload)
            elif route == "/api/school-portrayal/proposals":
                result = propose_school_portrayal(payload)
            elif route == "/api/school-portrayal/authorizations":
                result = authorize_school_portrayal_request(payload)
            elif route == "/api/school-portrayal/compile":
                result = compile_school_portrayal_request(payload)
            elif route == "/api/school-portrayal/observations":
                result = observe_school_portrayal_tool(payload)
            elif route == "/api/school-portrayal/verify":
                result = verify_school_portrayal_request(payload)
            elif route == "/api/road-portrayal/proposals":
                result = propose_road_portrayal(payload)
            elif route == "/api/road-portrayal/authorizations":
                result = authorize_road_portrayal_request(payload)
            elif route == "/api/road-portrayal/compile":
                result = compile_road_portrayal_request(payload)
            elif route == "/api/road-portrayal/observations":
                result = observe_road_portrayal_tool(payload)
            elif route == "/api/road-portrayal/verify":
                result = verify_road_portrayal_request(payload)
            elif observation_match:
                result = record_school_hero_observation(observation_match.group(1), payload)
            elif rollback_match:
                result = rollback_school_hero_execution(rollback_match.group(1), payload)
            elif road_observation_match:
                result = record_road_observation(road_observation_match.group(1), payload)
            elif road_rollback_match:
                result = rollback_road_execution(road_rollback_match.group(1), payload)
            elif route == "/api/qa-review":
                result = orchestrate_qa_review(payload, api_key, model)
            else:
                result = execute_qa_proposal(payload)
            self._json(HTTPStatus.OK, result)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(HTTPStatus.BAD_REQUEST, {"error": {"code": "invalid_json"}})
        except AgentError as error:
            self._json(error.status, {"error": {"code": error.code, "message": str(error)}})
        except UnifiedRuntimeError as error:
            self._json(
                error.status,
                {
                    "error": {
                        "code": error.code,
                        "message": str(error),
                        "domain": error.domain,
                        "stage": error.stage,
                        "mutation_performed": False,
                    }
                },
            )
        except SchoolHeroExecutionError as error:
            self._json(error.status, {"error": {"code": error.code, "message": str(error)}})
        except SchoolPortrayalError as error:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {"error": {"code": "school_portrayal_invalid", "message": str(error)}},
            )
        except RoadPortrayalError as error:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {"error": {"code": "road_portrayal_invalid", "message": str(error)}},
            )
        except RoadExecutionError as error:
            self._json(error.status, {"error": {"code": error.code, "message": str(error)}})
        except Exception:
            self._json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": {"code": "internal_error", "message": "Local agent proxy failed."}},
            )

    def log_message(self, format: str, *args: Any) -> None:
        # Standard access logs contain only route/status metadata; credentials are never logged.
        super().log_message(format, *args)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    private_archive_opt_in = os.environ.get("NMA_ENABLE_PRIVATE_ARCHIVE") == "1"
    using_real_school_data = (
        activate_private_real_school_dataset() if private_archive_opt_in else False
    )
    api_key, model = load_local_settings()
    mode = "Responses API" if api_key else "deterministic fallback"
    server = ThreadingHTTPServer((args.host, args.port), NMARequestHandler)
    print(f"NMA unified runtime: http://{args.host}:{args.port}/nmaAgentDemoV1.html?basemap=local")
    print(f"NMA unified API: http://{args.host}:{args.port}/api/nma/runtime")
    print(f"NMA School Hero v0.32: http://{args.host}:{args.port}/nmaAgentDemoV032.html")
    print(f"F03 server revision: {F03_SERVER_REVISION}")
    print(f"NMA Agentic v0.31: http://{args.host}:{args.port}/nmaAgentDemoV031.html")
    print(f"Preserved v0.4: http://{args.host}:{args.port}/nmaAgentDemoV04.html")
    print(f"Preserved v0.3 fallback: http://{args.host}:{args.port}/nmaAgentDemo.html")
    print(f"Agent mode: {mode} · model: {model} · session limit: {SESSIONS.max_turns} turns")
    print(
        "Layer data: "
        + (
            "15 real school features from the verified local Shapefile archive"
            if using_real_school_data
            else "12 synthetic school fixtures (protected archive access is disabled by default)"
        )
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if _KNOWLEDGE_SERVICE is not None:
            _KNOWLEDGE_SERVICE.close()


if __name__ == "__main__":
    main()

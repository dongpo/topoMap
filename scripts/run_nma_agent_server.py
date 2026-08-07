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
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OPENAI_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.6-terra"
MAX_TURNS = 8
SESSION_TTL_SECONDS = 20 * 60
MAX_BODY_BYTES = 32_768
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,80}$")
FEATURE_CODE_PATTERN = re.compile(r"^[0-9A-Za-z._-]{1,32}$")
SYMBOL_EDIT_PLAN_SCHEMA = "nma.symbol-edit-plan/1.0"
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
)
SYMBOL_EDIT_OPERATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": list(SYMBOL_EDIT_ACTIONS)},
        "target": {
            "type": ["string", "null"],
            "enum": ["symbol", "flag", "flag-top", "support", None],
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
            "enum": ["flag", "flagpole-top", "support", None],
        },
        "relation": {
            "type": ["string", "null"],
            "enum": ["aligned", "offset", "same-width", "inserted", "detached", None],
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
match the flag width means match_dimension from support to flag with relation same-width; insert the
flag into the rectangle means attach flag to support with relation inserted. Set unused operation
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
        self, session_id: str, *, response_id: str, call_id: str, now: float | None = None
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
    return {
        "schema": "nma.dataset-inspection/1.0",
        "dataset": {
            "id": dataset["id"],
            "label": dataset["label"],
            "feature_code": dataset["feature_code"],
            "synthetic": dataset["synthetic"],
        },
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
    if plan["schema"] != SYMBOL_EDIT_PLAN_SCHEMA or plan["source"] != "responses-api":
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
        "match_dimension": ("support", "flag", {"same-width"}, None),
        "attach": ("flag", "support", {"inserted"}, None),
        "detach": ("flag", "support", {"detached"}, None),
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


def orchestrate(payload: Any, api_key: str | None, model: str) -> dict[str, Any]:
    if not api_key:
        raise AgentError("key_missing", "Local OpenAI API key is not configured.", 503)
    request = validate_client_payload(payload)
    session, reset = SESSIONS.acquire(request["session_id"])
    if reset:
        request["tool_result"] = None
    response = call_openai(build_openai_payload(request, session, model), api_key)
    response_id, call_id, route = parse_openai_route(response)
    session = SESSIONS.update(request["session_id"], response_id=response_id, call_id=call_id)
    if route["intent"] == "reset_session":
        SESSIONS.reset(request["session_id"])
    return {
        "schema": "nma.agent-route/1.0",
        "model": model,
        "mode": "responses-api",
        "turn": session.turns,
        "max_turns": SESSIONS.max_turns,
        "session_reset": reset,
        "tool": {"name": "route_nma_turn", "arguments": route},
    }


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
        if route == "/api/agent/status":
            api_key, model = load_local_settings()
            self._json(
                HTTPStatus.OK,
                {
                    "available": bool(api_key),
                    "model": model,
                    "mode": "responses-api" if api_key else "deterministic-fallback",
                    "max_turns": SESSIONS.max_turns,
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
        if self.path.split("?", 1)[0] != "/api/agent":
            self._json(HTTPStatus.NOT_FOUND, {"error": {"code": "not_found"}})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > MAX_BODY_BYTES:
                raise AgentError("invalid_request", "Request body size is invalid.")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            api_key, model = load_local_settings()
            self._json(HTTPStatus.OK, orchestrate(payload, api_key, model))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(HTTPStatus.BAD_REQUEST, {"error": {"code": "invalid_json"}})
        except AgentError as error:
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
    api_key, model = load_local_settings()
    mode = "Responses API" if api_key else "deterministic fallback"
    server = ThreadingHTTPServer((args.host, args.port), NMARequestHandler)
    print(f"NMA demo: http://{args.host}:{args.port}/nmaAgentDemo.html")
    print(f"Agent mode: {mode} · model: {model} · session limit: {SESSIONS.max_turns} turns")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

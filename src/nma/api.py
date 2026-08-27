from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .specification import Specification
from .validator import Validator
from .knowledge import PortrayalGraph
from .portrayal import PortrayalAgent, compile_maplibre_layers


def get_payload(
    specification: Specification, path: str, portrayal_graph: PortrayalGraph | None = None
) -> tuple[int, Any]:
    if path == "/health":
        return 200, {"status": "ok", "version": "0.2.0"}
    if path == "/v1/specification":
        return 200, specification.raw
    if path == "/v1/rules":
        return 200, [rule.as_dict() for rule in specification.rules]
    if path == "/v1/knowledge/portrayal" and portrayal_graph:
        return 200, portrayal_graph.graph
    if path == "/v1/maplibre/portrayal-layers" and portrayal_graph:
        return 200, {"version": 8, "layers": compile_maplibre_layers(portrayal_graph)}
    return 404, {"error": "not_found"}


def post_payload(
    specification: Specification,
    path: str,
    payload: Any,
    portrayal_graph: PortrayalGraph | None = None,
) -> tuple[int, dict[str, Any]]:
    try:
        if not isinstance(payload, dict):
            raise ValueError("JSON request body must be an object")
        if path == "/v1/agent/ask" and portrayal_graph:
            question = payload.get("question")
            if not isinstance(question, str) or not question.strip():
                raise ValueError("question must be a non-empty string")
            return 200, PortrayalAgent(portrayal_graph).answer(question)
        if path == "/v1/agent/portray" and portrayal_graph:
            code = payload.get("feature_code")
            if not isinstance(code, str):
                raise ValueError("feature_code must be a string")
            decision = PortrayalAgent(portrayal_graph).select_symbol(
                code,
                scale_denominator=int(payload.get("scale_denominator", 1000)),
                profile_id=payload.get("profile_id"),
                attributes=payload.get("attributes"),
            )
            return 200, decision.as_dict()
        if path != "/v1/validate":
            return 404, {"error": "not_found"}
        report = Validator(specification).validate(payload, dataset="api-request")
    except (ValueError, KeyError, TypeError) as exc:
        return 400, {"error": "invalid_request", "detail": str(exc)}
    return 200, report


def make_handler(specification: Specification, portrayal_graph: PortrayalGraph | None = None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "NMA/0.2"

        def _send(self, status: int, value: Any) -> None:
            payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802
            status, payload = get_payload(specification, self.path, portrayal_graph)
            self._send(status, payload)

        def do_POST(self) -> None:  # noqa: N802
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length))
            except (ValueError, json.JSONDecodeError) as exc:
                self._send(400, {"error": "invalid_request", "detail": str(exc)})
                return
            status, response = post_payload(specification, self.path, payload, portrayal_graph)
            self._send(status, response)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def serve(
    specification: Specification,
    host: str = "127.0.0.1",
    port: int = 8000,
    portrayal_graph: PortrayalGraph | None = None,
) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(specification, portrayal_graph))
    print(f"NMA API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

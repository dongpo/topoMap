from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .specification import Specification
from .validator import Validator


def get_payload(specification: Specification, path: str) -> tuple[int, Any]:
    if path == "/health":
        return 200, {"status": "ok", "version": "0.2.0"}
    if path == "/v1/specification":
        return 200, specification.raw
    if path == "/v1/rules":
        return 200, [rule.as_dict() for rule in specification.rules]
    return 404, {"error": "not_found"}


def post_payload(
    specification: Specification, path: str, payload: Any
) -> tuple[int, dict[str, Any]]:
    if path != "/v1/validate":
        return 404, {"error": "not_found"}
    try:
        if not isinstance(payload, dict):
            raise ValueError("JSON request body must be an object")
        report = Validator(specification).validate(payload, dataset="api-request")
    except (ValueError, KeyError, TypeError) as exc:
        return 400, {"error": "invalid_request", "detail": str(exc)}
    return 200, report


def make_handler(specification: Specification):
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
            status, payload = get_payload(specification, self.path)
            self._send(status, payload)

        def do_POST(self) -> None:  # noqa: N802
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length))
            except (ValueError, json.JSONDecodeError) as exc:
                self._send(400, {"error": "invalid_request", "detail": str(exc)})
                return
            status, response = post_payload(specification, self.path, payload)
            self._send(status, response)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def serve(specification: Specification, host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(specification))
    print(f"NMA API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

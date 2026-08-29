"""Dependency-free localhost HTTP API and static server for AMA-LIVE-01."""

from __future__ import annotations

import argparse
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from threading import Lock, Thread
import time
from urllib.parse import parse_qs, urlparse

from nma.ama_demo import AMADemoPresentation
from nma.ama_live import AMALiveError, AMALiveService, CANONICAL_INTENT


class AMAHandler(BaseHTTPRequestHandler):
    service: AMALiveService
    demo: AMADemoPresentation | None = None
    static_root: Path
    asset_root: Path
    symbol_root: Path
    cors_origin: str = ""
    deployment_label: str = "LOCAL"
    _run_state_lock = Lock()
    _run_active = False
    _run_starts: deque[float] = deque()
    _runs_per_minute = 6

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(15)

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        origin = self.headers.get("Origin", "")
        if self.cors_origin and origin == self.cors_origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def _demo(self) -> AMADemoPresentation:
        handler_type = type(self)
        if handler_type.demo is None:
            handler_type.demo = AMADemoPresentation(
                self.service.repository_root, self.service.storage_root
            )
        return handler_type.demo

    def _log(self, event: str, **detail: object) -> None:
        value = {
            "event": event,
            "method": self.command,
            "path": urlparse(self.path).path,
            "deployment": self.deployment_label,
            **detail,
        }
        print(json.dumps(value, ensure_ascii=False, sort_keys=True), flush=True)

    def _json(self, value: object, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _file(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=300")
        self._security_headers()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin", "")
        if not self.cors_origin or origin != self.cors_origin:
            return self._json({"error": "origin not allowed"}, 403)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self._security_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/":
                return self._file(self.static_root / "index.html", "text/html; charset=utf-8")
            if path == "/app.js":
                return self._file(self.static_root / "app.js", "text/javascript; charset=utf-8")
            if path == "/app.css":
                return self._file(self.static_root / "app.css", "text/css; charset=utf-8")
            if path in {"/research.css", "/components.css"}:
                return self._file(
                    self.static_root / path.removeprefix("/"), "text/css; charset=utf-8"
                )
            if path.startswith("/assets/"):
                name = path.removeprefix("/assets/")
                if "/" in name or ".." in name:
                    return self.send_error(404)
                types = {".js": "text/javascript", ".css": "text/css"}
                return self._file(
                    self.asset_root / name, types.get(Path(name).suffix, "application/octet-stream")
                )
            if path.startswith("/symbols/"):
                name = path.removeprefix("/symbols/")
                if "/" in name or ".." in name or Path(name).suffix != ".svg":
                    return self.send_error(404)
                return self._file(self.symbol_root / name, "image/svg+xml")
            if path == "/ama/features":
                query = parse_qs(parsed.query).get("query", [""])[0]
                limit_raw = parse_qs(parsed.query).get("limit", ["20"])[0]
                try:
                    limit = int(limit_raw)
                except ValueError:
                    return self._json({"error": "limit must be an integer"}, 400)
                return self._json(self.service.search_features(query, limit=limit))
            if path.startswith("/ama/features/"):
                code = path.removeprefix("/ama/features/")
                if not (len(code) == 7 and code.isdigit()):
                    return self._json({"error": "TerrainID must contain exactly seven digits"}, 400)
                return self._json(self.service.feature_detail(code))
            if path == "/ama/config":
                live_cloud = self.deployment_label == "LIVE CLOUD RUN"
                return self._json(
                    {
                        "mode": "LIVE" if live_cloud else "LOCAL/TEST",
                        "deployment": self.deployment_label,
                        "canonical_intent": CANONICAL_INTENT,
                        "normalized_intent": CANONICAL_INTENT,
                        "planner_input": CANONICAL_INTENT,
                        "queryable_terrainid_count": self.service.feature_catalog.count,
                        "feature_search_endpoint": "/ama/features?query=",
                        "live_execution_fixture_codes": ["9350906"],
                        "research_example_codes": ["9920103", "9420400", "9310100"],
                        "live_capable": live_cloud,
                        "replay_capable": True,
                        "allowed_public_modes": ["LIVE", "REPLAY"],
                    }
                )
            if path == "/health":
                try:
                    return self._json(self.service.startup_check())
                except Exception as error:
                    self._log("health_failed", error_type=type(error).__name__)
                    return self._json({"status": "FAIL", "error": str(error)}, 503)
            if path == "/ama/context":
                return self._json(self._demo().domain_graph())
            if path == "/ama/rq1-comparison":
                return self._json(self._demo().rq1_comparison())
            if path == "/ama/demo/domain-kg":
                return self._json(self._demo().domain_graph())
            if path == "/ama/demo/rq1-comparison":
                return self._json(self._demo().rq1_comparison())
            if path == "/ama/demo/replay":
                return self._json(self._demo().replay_record())
            if path == "/ama/demo/replay/manifest":
                return self._json(self._demo().replay_manifest())
            if path == "/ama/demo/replay/result":
                return self._json(self._demo().replay_result())
            if path == "/ama/demo/replay/views":
                replay = self._demo().replay_record()
                return self._json(self._demo().views_for(replay, mode="REPLAY"))
            if path == "/ama/source":
                return self._json(self.service.source_geojson())
            parts = path.strip("/").split("/")
            if len(parts) >= 3 and parts[:2] == ["ama", "run"]:
                run_id = parts[2]
                record = self.service.get(run_id)
                if len(parts) == 3:
                    return self._json(record)
                view = parts[3]
                views = {
                    "evidence": record.get("evidence"),
                    "proposal": {
                        "proposal": record.get("proposal"),
                        "validation": record.get("proposal_validation"),
                    },
                    "verification": record.get("verification"),
                    "provenance": record.get("provenance"),
                    "demo-views": self._demo().views_for(record, mode=record.get("mode", "LIVE")),
                }
                if view == "result":
                    return self._json(self.service.result_geojson(run_id))
                if view in views:
                    return self._json(views[view])
            self.send_error(404)
        except KeyError:
            self._json({"error": "run not found"}, 404)

    def do_HEAD(self) -> None:
        """Return GET-equivalent headers without a body for link and uptime probes."""

        self.do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
            if content_type != "application/json":
                return self._json({"error": "Content-Type must be application/json"}, 415)
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 4096:
                return self._json({"error": "request too large"}, 413)
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                return self._json({"error": "request body must be a JSON object"}, 400)
            if path == "/ama/run":
                now = time.monotonic()
                handler_type = type(self)
                with self._run_state_lock:
                    while self._run_starts and now - self._run_starts[0] >= 60:
                        self._run_starts.popleft()
                    if handler_type._run_active:
                        return self._json({"error": "a live AMA run is already active"}, 409)
                    if len(self._run_starts) >= self._runs_per_minute:
                        return self._json({"error": "live AMA run rate limit exceeded"}, 429)
                    handler_type._run_active = True
                    self._run_starts.append(now)
                try:
                    record = self.service.new_record(body.get("intent", ""))
                except Exception:
                    with self._run_state_lock:
                        handler_type._run_active = False
                    raise

                def execute() -> None:
                    try:
                        completed = self.service.run(record["run_id"])
                        self._log(
                            "run_complete",
                            run_id=record["run_id"],
                            status=completed["status"],
                        )
                    except Exception as error:
                        self._log(
                            "run_complete",
                            run_id=record["run_id"],
                            status="FAILED",
                            error_type=type(error).__name__,
                        )
                    finally:
                        with self._run_state_lock:
                            handler_type._run_active = False

                Thread(target=execute, daemon=True).start()
                self._log("run_accepted", run_id=record["run_id"])
                return self._json(record, HTTPStatus.ACCEPTED)
            if path == "/ama/reset":
                handler_type = type(self)
                with self._run_state_lock:
                    if handler_type._run_active:
                        return self._json({"error": "cannot reset while a live run is active"}, 409)
                    result = self._demo().reset()
                    self.service.forget_records(result["removed_run_ids"])
                    handler_type._run_starts.clear()
                return self._json(result)
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["ama", "run"] and parts[3] == "tamper-test":
                return self._json(self.service.tamper_test(parts[2]))
            self.send_error(404)
        except (AMALiveError, ValueError, json.JSONDecodeError) as error:
            self._json({"error": str(error)}, 400)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8086)
    parser.add_argument("--storage-root", default="artifacts/ama-live/runtime")
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()
    service = AMALiveService(repository_root=root, storage_root=root / args.storage_root)
    readiness = service.startup_check()
    handler = type(
        "BoundAMAHandler",
        (AMAHandler,),
        {
            "service": service,
            "demo": AMADemoPresentation(root, root / args.storage_root),
            "static_root": root / "public/ama-live",
            "asset_root": root / "public/gh-pages/assets",
            "symbol_root": root / "assets/symbols/nlsc112v5.4",
            "cors_origin": os.environ.get("AMA_CORS_ORIGIN", ""),
            "deployment_label": os.environ.get("AMA_DEPLOYMENT_LABEL", "LOCAL"),
            "_runs_per_minute": int(os.environ.get("AMA_RUNS_PER_MINUTE", "6")),
        },
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(
        json.dumps(
            {
                "event": "startup_ready",
                "listen": f"http://{args.host}:{args.port}",
                "readiness": readiness,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

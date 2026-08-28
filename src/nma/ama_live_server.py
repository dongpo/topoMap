"""Dependency-free localhost HTTP API and static server for AMA-LIVE-01."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

from nma.ama_live import AMALiveError, AMALiveService, CANONICAL_INTENT


class AMAHandler(BaseHTTPRequestHandler):
    service: AMALiveService
    static_root: Path
    asset_root: Path

    def _json(self, value: object, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/":
                return self._file(self.static_root / "index.html", "text/html; charset=utf-8")
            if path == "/app.js":
                return self._file(self.static_root / "app.js", "text/javascript; charset=utf-8")
            if path == "/app.css":
                return self._file(self.static_root / "app.css", "text/css; charset=utf-8")
            if path.startswith("/assets/"):
                name = path.removeprefix("/assets/")
                if "/" in name or ".." in name:
                    return self.send_error(404)
                types = {".js": "text/javascript", ".css": "text/css"}
                return self._file(
                    self.asset_root / name, types.get(Path(name).suffix, "application/octet-stream")
                )
            if path == "/ama/config":
                return self._json({"mode": "LIVE", "canonical_intent": CANONICAL_INTENT})
            if path == "/ama/context":
                return self._json(self.service.domain_context())
            if path == "/ama/rq1-comparison":
                return self._json(self.service.rq1_comparison())
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
                }
                if view == "result":
                    return self._json(self.service.result_geojson(run_id))
                if view in views:
                    return self._json(views[view])
            self.send_error(404)
        except KeyError:
            self._json({"error": "run not found"}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 4096:
                return self._json({"error": "request too large"}, 413)
            body = json.loads(self.rfile.read(length) or b"{}")
            if path == "/ama/run":
                record = self.service.new_record(body.get("intent", ""))

                def execute() -> None:
                    try:
                        self.service.run(record["run_id"])
                    except Exception:
                        pass

                Thread(target=execute, daemon=True).start()
                return self._json(record, HTTPStatus.ACCEPTED)
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
    handler = type(
        "BoundAMAHandler",
        (AMAHandler,),
        {
            "service": service,
            "static_root": root / "public/ama-live",
            "asset_root": root / "public/gh-pages/assets",
        },
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"AMA-LIVE-01 http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

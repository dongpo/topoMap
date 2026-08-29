from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from nma.ama_live import AMALiveService, CANONICAL_INTENT
from nma.ama_live_server import AMAHandler
from nma.llm import LLMAdapter, LLMResult
from nma.llm.base import canonical_json
from nma.rq2_demo import sha256_file


ROOT = Path(__file__).resolve().parents[1]


class BoundedPlanner(LLMAdapter):
    def __init__(self, draft: dict[str, Any], delay: float = 0) -> None:
        self.draft = deepcopy(draft)
        self.delay = delay

    def generate_structured(
        self,
        *,
        task: str,
        instructions: str,
        context: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> LLMResult:
        time.sleep(self.delay)
        return LLMResult(
            model_id="qwen2.5:latest-test-double",
            provider="recorded-local-test",
            output=deepcopy(self.draft),
            latency_ms=round(self.delay * 1000),
            usage={"input_tokens": 1, "output_tokens": 1},
            raw_response_hash=hashlib.sha256(canonical_json(self.draft)).hexdigest(),
        )


def request(
    base: str,
    path: str,
    *,
    method: str = "GET",
    body: object | None = None,
    content_type: str = "application/json",
    origin: str | None = None,
) -> tuple[int, dict[str, Any], dict[str, str]]:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": content_type} if data is not None else {}
    if origin:
        headers["Origin"] = origin
    req = Request(base + path, data=data, method=method, headers=headers)
    try:
        with urlopen(req, timeout=10) as response:
            raw = response.read()
            status = response.status
            response_headers = dict(response.headers.items())
    except HTTPError as error:
        raw = error.read()
        status = error.code
        response_headers = dict(error.headers.items())
    return status, json.loads(raw or b"{}"), response_headers


def start_server(tmp_path: Path, *, delay: float = 0) -> tuple[ThreadingHTTPServer, str]:
    draft = json.loads((ROOT / "artifacts/rq2/rq2-demo-01-constrained-result.json").read_text())[
        "raw_planner_draft"
    ]
    service = AMALiveService(
        repository_root=ROOT,
        storage_root=tmp_path / "runtime",
        adapter_factory=lambda: BoundedPlanner(draft, delay),
    )
    handler = type(
        "CloudTestHandler",
        (AMAHandler,),
        {
            "service": service,
            "static_root": ROOT / "public/ama-live",
            "asset_root": ROOT / "public/gh-pages/assets",
            "cors_origin": "https://demo.example",
            "deployment_label": "LIVE CLOUD RUN",
            "_run_active": False,
            "_run_starts": deque(),
            "_runs_per_minute": 6,
        },
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def test_cloud_health_frontend_and_security_headers(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("AMA_DEPLOYMENT_LABEL", "LIVE CLOUD RUN")
    server, base = start_server(tmp_path)
    try:
        status, health, headers = request(base, "/health")
        assert status == 200
        assert health["status"] == "PASS"
        assert health["model_ready"] is True
        assert health["deployment"] == "LIVE CLOUD RUN"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        status, config, _ = request(base, "/ama/config")
        assert status == 200
        assert config["deployment"] == "LIVE CLOUD RUN"
        status, _, cors_headers = request(
            base,
            "/ama/config",
            origin="https://demo.example",
        )
        assert status == 200
        assert cors_headers["Access-Control-Allow-Origin"] == "https://demo.example"
        status, _, denied_headers = request(
            base,
            "/ama/config",
            origin="https://attacker.example",
        )
        assert status == 200
        assert "Access-Control-Allow-Origin" not in denied_headers
    finally:
        server.shutdown()
        server.server_close()


def test_cloud_frontend_supports_head_link_preflight(tmp_path: Path) -> None:
    server, base = start_server(tmp_path)
    try:
        status, body, headers = request(base, "/", method="HEAD")
        assert status == 200
        assert body == {}
        assert headers["Content-Type"] == "text/html; charset=utf-8"
        assert int(headers["Content-Length"]) > 0
        assert headers["X-Content-Type-Options"] == "nosniff"

        status, body, headers = request(base, "/health", method="HEAD")
        assert status == 200
        assert body == {}
        assert headers["Content-Type"] == "application/json; charset=utf-8"
        assert int(headers["Content-Length"]) > 0
    finally:
        server.shutdown()
        server.server_close()


def test_failed_requests_do_not_create_runs_or_mutate_fixture(tmp_path: Path) -> None:
    server, base = start_server(tmp_path)
    fixture = ROOT / "data/rq2/rq2-demo-01-fire-hydrant.geojson"
    before = sha256_file(fixture)
    try:
        status, _, _ = request(
            base,
            "/ama/run",
            method="POST",
            body={"intent": "arbitrary unsupported mutation"},
        )
        assert status == 400
        status, _, _ = request(
            base,
            "/ama/run",
            method="POST",
            body={"intent": CANONICAL_INTENT},
            content_type="text/plain",
        )
        assert status == 415
        assert sha256_file(fixture) == before
        assert not list((tmp_path / "runtime").glob("ama-live-run:*"))
    finally:
        server.shutdown()
        server.server_close()


def test_cloud_boundary_allows_only_one_live_run_at_a_time(tmp_path: Path) -> None:
    server, base = start_server(tmp_path, delay=0.3)
    try:
        first_status, first, _ = request(
            base,
            "/ama/run",
            method="POST",
            body={"intent": CANONICAL_INTENT},
        )
        assert first_status == 202
        second_status, second, _ = request(
            base,
            "/ama/run",
            method="POST",
            body={"intent": CANONICAL_INTENT},
        )
        assert second_status == 409
        assert "already active" in second["error"]
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            _, record, _ = request(base, f"/ama/run/{first['run_id']}")
            if record["status"] == "PASS":
                break
            time.sleep(0.05)
        assert record["status"] == "PASS"
    finally:
        server.shutdown()
        server.server_close()


def test_container_and_deployment_preserve_frozen_runtime_identity() -> None:
    dockerfile = (ROOT / "deploy/ama-cloud/Dockerfile").read_text()
    entrypoint = (ROOT / "scripts/ama_cloud_entrypoint.sh").read_text()
    deploy = (ROOT / "scripts/deploy_ama_cloud_run.sh").read_text()
    digest = "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"
    assert "OLLAMA_VERSION=0.32.15" in dockerfile
    assert "FROZEN_MODEL=qwen2.5:latest" in dockerfile
    assert digest in dockerfile
    assert digest in entrypoint
    assert "--gpu-type nvidia-l4" in deploy
    assert "--concurrency 1" in deploy
    assert "--max 1" in deploy
    assert "--no-cpu-throttling" in deploy
    assert "AMA_REQUIRE_GPU=1" in dockerfile
    assert '"size_vram"' in entrypoint
    assert "OPENAI_API_KEY" not in dockerfile + entrypoint + deploy


def test_research_semantic_artifacts_remain_byte_frozen() -> None:
    manifest = json.loads(
        (ROOT / "artifacts/demo-public/demo-public-00-evidence-manifest.json").read_text()
    )
    protected = [
        manifest["rq_final_manifest"],
        *manifest["research_closure"],
        *manifest["rq2_evidence"],
    ]
    for item in protected:
        assert sha256_file(ROOT / item["path"]) == item["sha256"]

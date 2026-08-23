"""Default-deny public adapter for the frozen NMA v1.0 research demo.

This module deliberately owns only deployment-boundary concerns: startup identity checks,
closed scenario selection, public-safe projections, anonymous run/session state, request limits,
and a Unix-socket HTTP surface.  It does not change or generalize any domain semantics.
"""

from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import logging
import mimetypes
import os
from pathlib import Path
import re
import secrets
import socketserver
from threading import Lock, Semaphore
import time
from typing import Any, Mapping
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlsplit
import zipfile

from build_contracts.demo_execution import validate_build_demo_execution_package
from nma.core import canonical_sha256
from nma.school_hero_execution import (
    ExecutionAuthorizationStore,
    SchoolHeroExecutionEngine,
    authorization_sha256,
)
from nma.school_hero_verification import SchoolHeroVerifier


RELEASE_COMMIT = "eb87bde775333811529efb6f651573ea21cf456b"
RELEASE_MANIFEST_SHA256 = "623860a18e82ad268ab389b417f3e9edc29c6c398b5dd923b37dbba3b2ba3bb4"
ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
ARCHIVE_SIZE = 12_822_898
GRAPH_SHA256 = "4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4"
SCHOOL_FIXTURE_SHA256 = "77802b44b97c6687bc626d257e14b57c3d7427949a65942fa721d05bb79fc12d"
ROAD_FIXTURE_SHA256 = "dc82db8bfc96dd6ab16b3206866e000459b9fd59a8f6d44602fcf06586b1ae79"
SCHOOL_AUTHORIZATION_ID = "authorization-school-demo-b4ecdbfc35ecaf73293ed497"
SCHOOL_AUTHORIZATION_SHA256 = "d5546bd1b2176a4ad287acb1c78740ce79a90db76d05739dc871267d901dac67"
SCHOOL_IDEMPOTENCY_KEY = "demo-02-retry-school-controlled-e2e"
SCHOOL_EXECUTION_ID = "exec-8d174b62fb63189987eafdb6"
ROAD_EXECUTION_ID = "road-exec-33766f336d9cc18eb2ac159e"
BUILD_EXECUTION_ID = "build-05-demo-exec-b8b5ecd54954b190eb8cda39"
PUBLIC_PREFIX = "/nma/"
MAX_JSON_BYTES = 2_048
MAX_TEXT_LENGTH = 500
RUN_TTL_SECONDS_DEFAULT = 1_800
ALLOWED_ENV = {
    "NMA_DEMO_RELEASE_COMMIT",
    "NMA_DEMO_RELEASE_MANIFEST",
    "NMA_DEMO_FIXTURE_ARCHIVE",
    "NMA_DEMO_GRAPH_ROOT",
    "NMA_DEMO_AUTHORITY_ROOT",
    "NMA_DEMO_STATE_ROOT",
    "NMA_DEMO_SOCKET",
    "NMA_DEMO_PUBLIC_ORIGIN",
    "NMA_DEMO_PUBLIC_PREFIX",
    "NMA_DEMO_MAX_ACTIVE_RUNS",
    "NMA_DEMO_RUN_TTL_SECONDS",
    "NMA_DEMO_LLM_MODE",
    "NMA_DEMO_BUILD_ACTIVATION",
}
FORBIDDEN_ENV_TERMS = ("OPENAI", "NEO4J", "PRODUCTION", "ACTIVATION", "WRITEBACK", "UPLOAD")
PUBLIC_ERROR_MESSAGES = {
    "invalid_request": "The request is malformed or outside the controlled demo schema.",
    "unsupported_request": "Choose one supported School, ROAD, or BUILD scenario.",
    "not_found": "The requested public resource does not exist.",
    "method_not_allowed": "That method is not allowed for this public resource.",
    "origin_rejected": "The request origin is not allowed.",
    "rate_limited": "The research demo rate limit was reached. Please retry later.",
    "service_busy": "The controlled demo is busy. Please retry shortly.",
    "not_ready": "The controlled demo is not ready.",
}


class PublicDemoError(ValueError):
    def __init__(self, code: str, status: int = 400):
        super().__init__(PUBLIC_ERROR_MESSAGES.get(code, "The controlled request failed."))
        self.code = code
        self.status = status


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


@dataclass(frozen=True)
class PublicDemoConfig:
    release_root: Path
    release_manifest: Path
    fixture_archive: Path
    graph_root: Path
    authority_root: Path
    state_root: Path
    socket_path: Path
    public_origin: str = "https://demo.geomni.tw"
    public_prefix: str = PUBLIC_PREFIX
    max_active_runs: int = 4
    run_ttl_seconds: int = RUN_TTL_SECONDS_DEFAULT
    llm_mode: str = "disabled"
    build_activation: str = "not-mounted"

    @classmethod
    def from_environment(cls, release_root: Path | None = None) -> "PublicDemoConfig":
        root = (release_root or Path.cwd()).resolve()
        unknown = sorted(
            key for key in os.environ if key.startswith("NMA_DEMO_") and key not in ALLOWED_ENV
        )
        if unknown:
            raise ValueError("unknown NMA demo configuration variables")
        suspicious = [
            key
            for key in os.environ
            if any(term in key.upper() for term in FORBIDDEN_ENV_TERMS)
            and key not in {"NMA_DEMO_BUILD_ACTIVATION"}
        ]
        if suspicious:
            raise ValueError("forbidden external/production configuration is present")

        def configured(name: str, fallback: Path) -> Path:
            return Path(os.environ.get(name, str(fallback))).resolve()

        return cls(
            release_root=root,
            release_manifest=configured(
                "NMA_DEMO_RELEASE_MANIFEST",
                root / "data/specifications/nma-v1.0-final-release-manifest.json",
            ),
            fixture_archive=configured(
                "NMA_DEMO_FIXTURE_ARCHIVE", root / "data/datasets/112年多維度SHP成果_0502.zip"
            ),
            graph_root=configured("NMA_DEMO_GRAPH_ROOT", root / "data/knowledge"),
            authority_root=configured(
                "NMA_DEMO_AUTHORITY_ROOT", root / "artifacts/runtime/school-hero/authorizations"
            ),
            state_root=configured("NMA_DEMO_STATE_ROOT", root / "artifacts/public-demo-state"),
            socket_path=configured("NMA_DEMO_SOCKET", Path("/tmp/nma-demo.sock")),
            public_origin=os.environ.get("NMA_DEMO_PUBLIC_ORIGIN", "https://demo.geomni.tw").rstrip(
                "/"
            ),
            public_prefix=os.environ.get("NMA_DEMO_PUBLIC_PREFIX", PUBLIC_PREFIX),
            max_active_runs=int(os.environ.get("NMA_DEMO_MAX_ACTIVE_RUNS", "4")),
            run_ttl_seconds=int(os.environ.get("NMA_DEMO_RUN_TTL_SECONDS", "1800")),
            llm_mode=os.environ.get("NMA_DEMO_LLM_MODE", "disabled"),
            build_activation=os.environ.get("NMA_DEMO_BUILD_ACTIVATION", "not-mounted"),
        )


class StartupIntegrityValidator:
    """Validate all critical controlled assets without mutating them."""

    def __init__(self, config: PublicDemoConfig):
        self.config = config

    def _authority_path(self) -> Path:
        candidates = (
            self.config.authority_root / f"{SCHOOL_AUTHORIZATION_ID}.json",
            self.config.release_root
            / "artifacts/runtime/school-hero/authorizations"
            / f"{SCHOOL_AUTHORIZATION_ID}.json",
        )
        return next((path for path in candidates if path.is_file()), candidates[0])

    def validate(self) -> dict[str, Any]:
        cfg = self.config
        if os.environ.get("NMA_DEMO_RELEASE_COMMIT", RELEASE_COMMIT) != RELEASE_COMMIT:
            raise ValueError("release commit mismatch")
        if cfg.public_prefix != PUBLIC_PREFIX or cfg.llm_mode != "disabled":
            raise ValueError("unsafe public prefix or LLM mode")
        if cfg.build_activation != "not-mounted":
            raise ValueError("BUILD activation capability must be not-mounted")
        local_test_origin = re.fullmatch(
            r"http://(?:127\.0\.0\.1|localhost)(?::[0-9]{1,5})?", cfg.public_origin
        )
        if (
            not cfg.public_origin.startswith("https://") and local_test_origin is None
        ) or "*" in cfg.public_origin:
            raise ValueError("public origin must be explicit HTTPS or loopback-only test origin")
        manifest = _load(cfg.release_manifest)
        supplied = manifest.pop("canonical_manifest_sha256", None)
        if supplied != RELEASE_MANIFEST_SHA256 or canonical_sha256(manifest) != supplied:
            raise ValueError("release manifest identity mismatch")
        archive = cfg.fixture_archive
        if archive.stat().st_size != ARCHIVE_SIZE or _sha256(archive) != ARCHIVE_SHA256:
            raise ValueError("controlled archive identity mismatch")
        fixture = _load(
            cfg.release_root / "data/specifications/nma-demo-controlled-fixture-baseline-v1.0.json"
        )
        if fixture["school"]["aggregate_sha256"] != SCHOOL_FIXTURE_SHA256:
            raise ValueError("School fixture commitment mismatch")
        if fixture["road"]["aggregate_sha256"] != ROAD_FIXTURE_SHA256:
            raise ValueError("ROAD fixture commitment mismatch")
        expected_components: list[dict[str, Any]] = []
        for layer in fixture["school"]["layers"]:
            for component in layer["components"]:
                expected_components.append(
                    {**component, "suffix": f"/SHP/{layer['layer_id']}{component['extension']}"}
                )
        for component in fixture["road"]["layer"]["components"]:
            expected_components.append(
                {**component, "suffix": f"/SHP/K14_ROAD{component['extension']}"}
            )
        with zipfile.ZipFile(archive) as package:
            names = package.namelist()
            if any(name.startswith("/") or ".." in Path(name).parts for name in names):
                raise ValueError("unsafe controlled archive member")
            for expected in expected_components:
                suffix = expected["suffix"].casefold()
                matches = [name for name in names if name.casefold().endswith(suffix)]
                if len(matches) != 1:
                    raise ValueError("controlled component missing or ambiguous")
                payload = package.read(matches[0])
                if (
                    len(payload) != expected["size_bytes"]
                    or hashlib.sha256(payload).hexdigest() != expected["sha256"]
                ):
                    raise ValueError("controlled component identity mismatch")
        graph_path = cfg.graph_root / "nma-canonical-graph-v0.4.json"
        if _sha256(graph_path) != GRAPH_SHA256:
            raise ValueError("GraphRAG asset identity mismatch")
        graph = _load(graph_path)
        graph_ids = {node.get("id") for node in graph.get("nodes", [])}
        for domain in ("school", "road"):
            required = fixture[domain]["graphrag"]["required_nodes"]
            if not set(required).issubset(graph_ids):
                raise ValueError(f"{domain} GraphRAG evidence is incomplete")
        authorization_path = self._authority_path()
        authorization = _load(authorization_path)
        if (
            authorization.get("authorization_id") != SCHOOL_AUTHORIZATION_ID
            or authorization.get("authorization_hash") != SCHOOL_AUTHORIZATION_SHA256
            or authorization_sha256(authorization) != SCHOOL_AUTHORIZATION_SHA256
        ):
            raise ValueError("School demo authorization identity mismatch")
        build_package = _load(
            cfg.release_root / "data/specifications/nma-build-05-golden-execution-package-v1.0.json"
        )
        validate_build_demo_execution_package(build_package, *self._build_frozen_inputs())
        if build_package["boundaries"]["production_activated"] is not False:
            raise ValueError("BUILD production activation invariant failed")
        asset_manifest = _load(cfg.release_root / "public/nma/assets/manifest.json")
        for item in asset_manifest.get("assets", []):
            path = cfg.release_root / "public/nma" / item["path"]
            if _sha256(path) != item["sha256"]:
                raise ValueError("public asset identity mismatch")
        data_authority = _load(
            cfg.release_root / "data/demo/public-demo-data-authority-matrix-v1.0.json"
        )
        if (
            data_authority.get("accepted_public_demo_fixtures") != []
            or data_authority.get("demo_authorizations") != []
            or data_authority.get("verdict", {}).get("status") != "fail-closed"
        ):
            raise ValueError("unexpected public data authority matrix state")
        raise ValueError(
            "public School/ROAD data authority and frozen contract compatibility are not closed"
        )

    def _build_frozen_inputs(self) -> tuple[dict[str, Any], ...]:
        spec = self.config.release_root / "data/specifications"
        return tuple(
            _load(spec / name)
            for name in (
                "nma-build-04-golden-demo-authorization-v1.0.json",
                "nma-build-03a-golden-gate-resolution-v1.0.json",
                "nma-build-03-golden-gate-review-v1.0.json",
                "nma-build-02-golden-proposal-v1.0.json",
                "nma-build-02-golden-decision-v1.0.json",
            )
        )


SCENARIOS = {
    "school-v1": {
        "domain": "School",
        "title": "School — official blue symbol",
        "mode": "controlled execution",
    },
    "road-v1": {"domain": "ROAD", "title": "ROAD — 中山街", "mode": "validated accepted replay"},
    "build-v1": {"domain": "BUILD", "title": "BUILD — boundary and hatch", "mode": "replay only"},
}
LANGUAGE_TERMS = {
    "school-v1": ("school", "小學", "學校", "9920103"),
    "road-v1": ("road", "道路", "中山街", "9420400", "縣126"),
    "build-v1": ("build", "building", "建物", "建築", "9310100"),
}
BLOCKED_TEXT = re.compile(
    r"(?:/|\\|https?://|file:|upload|path|secret|token|password|cypher|neo4j|openai|activate|production|writeback|shell|subprocess)",
    re.IGNORECASE,
)


class PublicDemoGateway:
    def __init__(self, config: PublicDemoConfig, *, validate: bool = True):
        self.config = config
        self.integrity = StartupIntegrityValidator(config)
        self.readiness = self.integrity.validate() if validate else {"release": RELEASE_COMMIT}
        self.ready = bool(validate)
        self.started_at = time.time()
        self._runs: dict[str, dict[str, Any]] = {}
        self._lock = Lock()
        self._global = Semaphore(config.max_active_runs)
        self._active_ips: set[str] = set()
        self._limits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._session_limits: dict[str, deque[float]] = defaultdict(deque)
        self._fixture = _load(
            config.release_root
            / "data/specifications/nma-demo-controlled-fixture-baseline-v1.0.json"
        )
        self._graph = _load(config.graph_root / "nma-canonical-graph-v0.4.json")
        self._graph_nodes = {node["id"]: node for node in self._graph["nodes"]}
        self._asset_manifest = _load(config.release_root / "public/nma/assets/manifest.json")
        self.asset_paths = {
            item.get("public_name", item["path"].removeprefix("assets/")): item["path"]
            for item in self._asset_manifest["assets"]
        }
        self._school_engine: SchoolHeroExecutionEngine | None = None

    def scenarios(self) -> dict[str, Any]:
        return {
            "release": RELEASE_COMMIT,
            "baseline": {
                "llm": "disabled",
                "neo4j": "not-required",
                "production_credentials": "absent",
            },
            "scenarios": [{"scenario_id": key, **value} for key, value in SCENARIOS.items()],
        }

    def select_scenario(self, payload: Any) -> tuple[str, str]:
        if not isinstance(payload, Mapping):
            raise PublicDemoError("invalid_request")
        keys = set(payload)
        input_type = payload.get("input_type")
        if input_type == "guided" and keys == {"scenario_id", "input_type"}:
            scenario = payload.get("scenario_id")
            if scenario not in SCENARIOS:
                raise PublicDemoError("unsupported_request")
            return str(scenario), "guided"
        if input_type == "bounded-natural-language" and keys == {"request", "input_type"}:
            request = payload.get("request")
            if (
                not isinstance(request, str)
                or not request.strip()
                or len(request) > MAX_TEXT_LENGTH
            ):
                raise PublicDemoError("invalid_request")
            normalized = " ".join(request.casefold().split())
            if BLOCKED_TEXT.search(normalized):
                raise PublicDemoError("unsupported_request")
            matches = [
                key
                for key, terms in LANGUAGE_TERMS.items()
                if any(term in normalized for term in terms)
            ]
            if len(matches) != 1:
                raise PublicDemoError("unsupported_request")
            return matches[0], "bounded-natural-language"
        raise PublicDemoError("invalid_request")

    def check_rate(self, client: str, category: str, *, limit: int, window: int) -> None:
        now = time.monotonic()
        bucket = self._limits[(client, category)]
        while bucket and bucket[0] <= now - window:
            bucket.popleft()
        if len(bucket) >= limit:
            raise PublicDemoError("rate_limited", 429)
        bucket.append(now)

    def run(self, payload: Any, client: str, session: str) -> dict[str, Any]:
        if not self.ready:
            raise PublicDemoError("not_ready", 503)
        self.check_rate(client, "run", limit=5, window=60)
        now = time.monotonic()
        session_bucket = self._session_limits[session]
        while session_bucket and session_bucket[0] <= now - 3600:
            session_bucket.popleft()
        if len(session_bucket) >= 20:
            raise PublicDemoError("rate_limited", 429)
        scenario_id, input_type = self.select_scenario(payload)
        with self._lock:
            if client in self._active_ips:
                raise PublicDemoError("rate_limited", 429)
            self._active_ips.add(client)
        if not self._global.acquire(timeout=2):
            with self._lock:
                self._active_ips.discard(client)
            raise PublicDemoError("service_busy", 503)
        started = time.monotonic()
        try:
            projection, evidence, map_result = self._execute(scenario_id)
            run_id = secrets.token_hex(16)
            record = {
                "run_id": run_id,
                "session": session,
                "created_at": time.time(),
                "scenario_id": scenario_id,
                "input_type": input_type,
                "projection": projection,
                "evidence": evidence,
                "map": map_result,
            }
            with self._lock:
                self._prune()
                self._runs[run_id] = record
            session_bucket.append(now)
            logging.info(
                json.dumps(
                    {
                        "event": "controlled_run",
                        "scenario": scenario_id,
                        "domain": SCENARIOS[scenario_id]["domain"],
                        "input_type": input_type,
                        "status": "passed",
                        "verification": projection["verification"]["status"],
                        "latency_ms": round((time.monotonic() - started) * 1000),
                    },
                    separators=(",", ":"),
                )
            )
            return {
                "run_id": run_id,
                "status": "complete",
                "result_url": f"{PUBLIC_PREFIX}api/v1/runs/{run_id}",
            }
        finally:
            self._global.release()
            with self._lock:
                self._active_ips.discard(client)

    def _prune(self) -> None:
        cutoff = time.time() - self.config.run_ttl_seconds
        for run_id in [key for key, value in self._runs.items() if value["created_at"] < cutoff]:
            del self._runs[run_id]

    def get_run(self, run_id: str, session: str, part: str) -> dict[str, Any]:
        if not re.fullmatch(r"[0-9a-f]{32}", run_id):
            raise PublicDemoError("not_found", 404)
        with self._lock:
            self._prune()
            record = self._runs.get(run_id)
        if record is None or not secrets.compare_digest(record["session"], session):
            raise PublicDemoError("not_found", 404)
        if part == "projection":
            return {
                "run_id": run_id,
                "scenario_id": record["scenario_id"],
                **deepcopy(record["projection"]),
            }
        return deepcopy(record[part])

    def _graph_evidence(self, domain: str) -> dict[str, Any]:
        ids = self._fixture[domain]["graphrag"]["required_nodes"]
        allowed = {
            "feature_code",
            "feature_name",
            "label",
            "code",
            "page",
            "geometry_role",
            "instruction",
            "representation_kind",
        }
        nodes = []
        for identity in ids:
            node = self._graph_nodes[identity]
            nodes.append(
                {
                    "id": identity,
                    "type": node["type"],
                    "summary": {
                        key: value
                        for key, value in node.get("properties", {}).items()
                        if key in allowed
                    },
                }
            )
        edges = [
            {"source": edge["source"], "relationship": edge["type"], "target": edge["target"]}
            for edge in self._graph["edges"]
            if edge["source"] in ids and edge["target"] in ids
        ][:12]
        return {
            "mode": "deterministic accepted-scenario GraphRAG path",
            "graph_identity": GRAPH_SHA256,
            "nodes": nodes,
            "relationships": edges,
            "boundary": self._fixture[domain]["graphrag"]["boundary"],
        }

    def _execute(self, scenario_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        if scenario_id == "school-v1":
            return self._execute_school()
        if scenario_id == "road-v1":
            return self._replay_road()
        return self._replay_build()

    def _school_authorization_path(self) -> Path:
        mounted = self.config.authority_root / f"{SCHOOL_AUTHORIZATION_ID}.json"
        if mounted.is_file():
            return mounted
        return (
            self.config.release_root / "artifacts/runtime/school-hero/authorizations" / mounted.name
        )

    def _execute_school(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        if self._school_engine is None:
            school_root = self.config.state_root / "school"
            store = ExecutionAuthorizationStore(school_root / "authorizations")
            store.save(_load(self._school_authorization_path()))
            self._school_engine = SchoolHeroExecutionEngine(
                storage_root=school_root,
                archive_path=self.config.fixture_archive,
                official_symbol_path=self.config.release_root
                / "assets/symbols/nlsc112v5.4/school.svg",
                authorization_store=store,
            )
        receipt = self._school_engine.execute_by_id(
            {
                "authorization_id": SCHOOL_AUTHORIZATION_ID,
                "idempotency_key": SCHOOL_IDEMPOTENCY_KEY,
            }
        )
        if receipt["execution_id"] != SCHOOL_EXECUTION_ID:
            raise ValueError("School execution identity drift")
        verified = SchoolHeroVerifier(
            storage_root=self._school_engine.storage_root,
            archive_path=self.config.fixture_archive,
            official_symbol_path=self.config.release_root / "assets/symbols/nlsc112v5.4/school.svg",
            repository_root=self.config.release_root,
        ).verify(SCHOOL_EXECUTION_ID, persist=True)
        data = self._school_engine.get_data(SCHOOL_EXECUTION_ID)
        projection = {
            "domain": "School",
            "intent": "Produce the controlled School 9920103 rule-aligned map.",
            "plan": {
                "status": "accepted",
                "identity": receipt["execution_plan_id"],
                "action": "filter 9920103; derive EPSG:4326; apply approved blue School portrayal",
            },
            "authorization": {
                "status": "consumed-idempotently",
                "identity": SCHOOL_AUTHORIZATION_ID,
                "sha256": SCHOOL_AUTHORIZATION_SHA256,
                "scope": "controlled 15-point School derivative only",
                "demo_only": True,
                "production_authority": "absent",
            },
            "execution": {
                "status": "completed",
                "identity": SCHOOL_EXECUTION_ID,
                "feature_count": 15,
            },
            "verification": {"status": verified["status"], "identity": verified["qa"]["qa_sha256"]},
            "receipt": {"identity": receipt["receipt_sha256"]},
            "provenance": {
                "status": verified["provenance"]["status"],
                "identity": verified["provenance"]["provenance_sha256"],
                "fixture": SCHOOL_FIXTURE_SHA256,
            },
            "production_activation": "unavailable",
        }
        evidence = {
            "graphrag": self._graph_evidence("school"),
            "plan_link": {
                "plan_id": receipt["execution_plan_id"],
                "uses_rule_ids": self._fixture["school"]["graphrag"]["required_nodes"],
            },
            "qa": projection["verification"],
            "receipt": projection["receipt"],
            "provenance": projection["provenance"],
        }
        return (
            projection,
            evidence,
            {
                "type": "school",
                "geojson": data,
                "expected_feature_count": 15,
                "image": f"{PUBLIC_PREFIX}assets/school-blue.svg",
            },
        )

    def _replay_road(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        root = self.config.release_root
        execution = root / f"artifacts/runtime/road/executions/{ROAD_EXECUTION_ID}"
        data = _load(execution / "data/road-centreline-runtime.geojson")
        plan = _load(execution / "plan.json")
        receipt = _load(execution / "receipt.json")
        qa = _load(execution / "qa.json")
        provenance = _load(execution / "provenance.json")
        if [len(f["geometry"]["coordinates"]) for f in data["features"]] != [4, 3, 4]:
            raise ValueError("ROAD geometry drift")
        projection = {
            "domain": "ROAD",
            "intent": "Replay accepted K14_ROAD 9420400 中山街 portrayal.",
            "plan": {
                "status": "frozen-validated-replay",
                "identity": plan["execution_plan_id"],
                "sha256": plan["execution_plan_sha256"],
                "action": "render exact ordered 4/3/4 LineStrings with line-following 中山街",
            },
            "authorization": {
                "status": "frozen-consumed-evidence",
                "identity": receipt["authorization"]["id"],
                "sha256": receipt["authorization"]["sha256"],
                "scope": "exact K14_ROAD three-segment derivative",
                "demo_only": True,
                "production_authority": "absent",
            },
            "execution": {
                "status": "accepted-replay",
                "identity": ROAD_EXECUTION_ID,
                "feature_count": 3,
            },
            "verification": {"status": qa["status"], "identity": qa["qa_sha256"]},
            "receipt": {"identity": receipt["receipt_id"], "sha256": receipt["receipt_sha256"]},
            "provenance": {
                "status": provenance["status"],
                "identity": provenance["provenance_sha256"],
                "fixture": ROAD_FIXTURE_SHA256,
            },
            "production_activation": "unavailable",
        }
        evidence = {
            "graphrag": self._graph_evidence("road"),
            "plan_link": {
                "plan_id": plan["execution_plan_id"],
                "uses_rule_ids": self._fixture["road"]["graphrag"]["required_nodes"],
            },
            "qa": projection["verification"],
            "receipt": projection["receipt"],
            "provenance": projection["provenance"],
        }
        return (
            projection,
            evidence,
            {
                "type": "road",
                "geojson": data,
                "expected_feature_count": 3,
                "label": "中山街",
                "vertex_counts": [4, 3, 4],
            },
        )

    def _replay_build(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        package = _load(
            self.config.release_root
            / "data/specifications/nma-build-05-golden-execution-package-v1.0.json"
        )
        validate_build_demo_execution_package(package, *self.integrity._build_frozen_inputs())
        artifact = package["demo_artifact"]
        projection = {
            "domain": "BUILD",
            "intent": "Replay the accepted BUILD 9310100 derived demonstration.",
            "plan": {
                "status": "frozen-validated-replay",
                "identity": package["plan_sha256"],
                "action": "render accepted normalized boundary and diagonal hatch",
            },
            "authorization": {
                "status": "frozen-consumed-evidence",
                "identity": package["authorization_id"],
                "sha256": package["authorization_sha256"],
                "scope": "derived demo replay only",
                "demo_only": True,
                "production_authority": "absent",
            },
            "execution": {"status": "accepted-replay", "identity": BUILD_EXECUTION_ID},
            "verification": {
                "status": "passed-frozen-package-validation",
                "identity": package["package_sha256"],
            },
            "receipt": {
                "identity": package["receipt"]["receipt_id"],
                "sha256": package["receipt"]["receipt_sha256"],
            },
            "provenance": {
                "status": "source-commitments-verified",
                "identity": artifact["artifact_sha256"],
                "source_commitments": artifact["source_commitments"],
            },
            "production_activation": "disabled/unavailable — capability not mounted",
        }
        evidence = {
            "graphrag": {
                "mode": "not-applicable in accepted BUILD evaluation",
                "nodes": [],
                "relationships": [],
                "boundary": "BUILD exposes frozen mapping-rule evidence; it does not fabricate a GraphRAG claim.",
            },
            "mapping_rules": {
                "feature_code": "9310100",
                "portrayal": "solid boundary plus 45° diagonal hatch",
                "resolution_sha256": package["resolution_sha256"],
            },
            "plan_link": {
                "plan_id": package["plan_sha256"],
                "uses_rule_ids": ["build-resolution:" + package["resolution_sha256"]],
            },
            "qa": projection["verification"],
            "receipt": projection["receipt"],
            "provenance": projection["provenance"],
        }
        return (
            projection,
            evidence,
            {
                "type": "build",
                "geojson": artifact["maplibre_demo"]["source"]["data"],
                "style": artifact["maplibre_demo"]["style"],
                "coordinate_space": "normalized-local-demo-not-geographic",
                "activation_capability": "not-mounted",
            },
        )


class _ThreadingUnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    allow_reuse_address = True


class PublicDemoRequestHandler(BaseHTTPRequestHandler):
    server_version = "NMA-Public-Demo"
    sys_version = ""

    @property
    def gateway(self) -> PublicDemoGateway:
        return self.server.gateway  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:
        logging.info(
            json.dumps(
                {"event": "http", "status": args[1] if len(args) > 1 else None},
                separators=(",", ":"),
            )
        )

    def _headers(
        self,
        status: int,
        content_type: str,
        length: int,
        *,
        cookie: str | None = None,
        immutable: bool = False,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header(
            "Cache-Control", "public, max-age=31536000, immutable" if immutable else "no-store"
        )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; manifest-src 'self'; upgrade-insecure-requests",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        if cookie:
            self.send_header(
                "Set-Cookie",
                f"nma_session={cookie}; Path=/nma/; Max-Age=1800; Secure; HttpOnly; SameSite=Strict",
            )
        self.end_headers()

    def _json(self, status: int, value: Any, *, cookie: str | None = None) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(payload), cookie=cookie)
        self.wfile.write(payload)

    def _error(self, error: PublicDemoError) -> None:
        headers = {"error": {"code": error.code, "message": str(error)}}
        if error.status == 429:
            payload = json.dumps(headers, ensure_ascii=False, separators=(",", ":")).encode()
            self.send_response(429)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Retry-After", "60")
            self.end_headers()
            self.wfile.write(payload)
            return
        self._json(error.status, headers)

    def _session(self, *, create: bool = False) -> tuple[str | None, bool]:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        value = cookie.get("nma_session")
        if value and re.fullmatch(r"[0-9a-f]{32}", value.value):
            return value.value, False
        return (secrets.token_hex(16), True) if create else (None, False)

    def _client(self) -> str:
        forwarded = self.headers.get("X-Real-IP", "unix")
        return forwarded[:64] if re.fullmatch(r"[0-9A-Fa-f:.]{1,64}", forwarded) else "unix"

    def do_GET(self) -> None:
        try:
            path = urlsplit(self.path).path
            if path == "/nma/":
                return self._file(
                    self.gateway.config.release_root / "public/nma/index.html",
                    "text/html; charset=utf-8",
                )
            if path == "/nma/api/v1/health/live":
                return self._json(200, {"status": "ok", "release": RELEASE_COMMIT})
            if path == "/nma/api/v1/health/ready":
                status = 200 if self.gateway.ready else 503
                return self._json(
                    status,
                    {
                        "status": "ready" if self.gateway.ready else "not-ready",
                        "release": RELEASE_COMMIT,
                        "fixtures": "verified" if self.gateway.ready else "unavailable",
                        "runtime": "ready" if self.gateway.ready else "unavailable",
                        "production_activation_capability": "not-mounted",
                    },
                )
            if path == "/nma/api/v1/scenarios":
                return self._json(200, self.gateway.scenarios())
            if path.startswith("/nma/assets/"):
                name = path.removeprefix("/nma/assets/")
                if name not in self.gateway.asset_paths or "/" in name or ".." in name:
                    raise PublicDemoError("not_found", 404)
                content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
                relative = self.gateway.asset_paths[name]
                return self._file(
                    self.gateway.config.release_root / "public/nma" / relative,
                    content_type,
                    immutable=True,
                )
            matched = re.fullmatch(r"/nma/api/v1/runs/([0-9a-f]{32})(?:/(evidence|map))?", path)
            if matched:
                session, _ = self._session()
                if session is None:
                    raise PublicDemoError("not_found", 404)
                self.gateway.check_rate(self._client(), "result", limit=30, window=60)
                part = matched.group(2) or "projection"
                return self._json(200, self.gateway.get_run(matched.group(1), session, part))
            raise PublicDemoError("not_found", 404)
        except PublicDemoError as error:
            self._error(error)
        except Exception:
            logging.exception("public GET failed")
            self._error(PublicDemoError("not_ready", 503))

    def _file(self, path: Path, content_type: str, immutable: bool = False) -> None:
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise PublicDemoError("not_found", 404) from error
        self._headers(200, content_type, len(payload), immutable=immutable)
        self.wfile.write(payload)

    def do_POST(self) -> None:
        try:
            if urlsplit(self.path).path != "/nma/api/v1/runs":
                raise PublicDemoError("not_found", 404)
            if self.headers.get("Origin") != self.gateway.config.public_origin:
                raise PublicDemoError("origin_rejected", 403)
            if (
                self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                != "application/json"
            ):
                raise PublicDemoError("invalid_request", 415)
            if self.headers.get("Transfer-Encoding"):
                raise PublicDemoError("invalid_request", 400)
            try:
                length = int(self.headers.get("Content-Length", "-1"))
            except ValueError as error:
                raise PublicDemoError("invalid_request", 400) from error
            if length < 2 or length > MAX_JSON_BYTES:
                raise PublicDemoError("invalid_request", 413)
            try:
                payload = json.loads(self.rfile.read(length))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise PublicDemoError("invalid_request", 400) from error
            session, created = self._session(create=True)
            assert session is not None
            result = self.gateway.run(payload, self._client(), session)
            self._json(201, result, cookie=session if created else None)
        except PublicDemoError as error:
            self._error(error)
        except Exception:
            logging.exception("public POST failed")
            self._error(PublicDemoError("not_ready", 503))

    def do_OPTIONS(self) -> None:
        self._error(PublicDemoError("method_not_allowed", 405))

    def __getattr__(self, name: str) -> Any:
        if name.startswith("do_"):
            return lambda: self._error(PublicDemoError("method_not_allowed", 405))
        raise AttributeError(name)


def serve_unix(config: PublicDemoConfig) -> None:
    gateway = PublicDemoGateway(config)
    config.socket_path.parent.mkdir(parents=True, exist_ok=True)
    if config.socket_path.exists():
        config.socket_path.unlink()
    server = _ThreadingUnixServer(str(config.socket_path), PublicDemoRequestHandler)
    server.gateway = gateway  # type: ignore[attr-defined]
    os.chmod(config.socket_path, 0o660)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
        if config.socket_path.exists():
            config.socket_path.unlink()

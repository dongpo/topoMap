from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from nma.unified_runtime import (
    BuildRuntimeAdapter,
    RoadRuntimeAdapter,
    SchoolRuntimeAdapter,
    UnifiedNMARuntime,
    UnifiedRuntimeError,
    select_domain,
)


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
SYMBOL = ROOT / "assets/symbols/nlsc112v5.4/school.svg"
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"
DEMO_PATH = ROOT / "nmaAgentDemoV1.html"


class UnusedEngine:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root

    def execute_by_id(self, request):  # pragma: no cover - a safety tripwire
        raise AssertionError(f"Execution unexpectedly invoked: {request}")


@pytest.fixture()
def runtime(tmp_path: Path) -> UnifiedNMARuntime:
    return UnifiedNMARuntime(
        {
            "school": SchoolRuntimeAdapter(
                engine=UnusedEngine(tmp_path / "school"),
                repository_root=ROOT,
                archive_path=ARCHIVE,
                symbol_path=SYMBOL,
            ),
            "road": RoadRuntimeAdapter(
                engine=UnusedEngine(tmp_path / "road"),
                repository_root=ROOT,
                archive_path=ARCHIVE,
            ),
            "build": BuildRuntimeAdapter(
                repository_root=ROOT,
                archive_path=ARCHIVE,
            ),
        }
    )


def test_deterministic_domain_selection_and_fail_closed_ambiguity() -> None:
    assert select_domain("school-hero", "ignored") == "school"
    assert select_domain(None, "Show County Highway 126 ROAD") == "road"
    assert select_domain(None, "請顯示建物 9310100") == "build"
    with pytest.raises(UnifiedRuntimeError, match="exactly one") as absent:
        select_domain(None, "Show a feature")
    assert absent.value.code == "ambiguous_domain"
    with pytest.raises(UnifiedRuntimeError, match="exactly one"):
        select_domain(None, "Show a broad overview before rebuilding")
    with pytest.raises(UnifiedRuntimeError, match="more than one") as multiple:
        select_domain(None, "Show the school and road")
    assert multiple.value.code == "ambiguous_domain"
    with pytest.raises(UnifiedRuntimeError) as unsupported:
        select_domain("riverl", "Inspect the river")
    assert unsupported.value.code == "unsupported_domain"


def test_school_routes_to_frozen_capability_without_execution(runtime: UnifiedNMARuntime) -> None:
    result = runtime.dispatch(
        {"domain": "school", "request": "Show School Hero capability", "operation": "preview"}
    )
    assert result["selected_domain"] == "school"
    assert result["plan"]["contract"] == "nma.school-hero-execution-plan/1.0"
    assert result["plan"]["capability"]["identity"]["feature_code"] == "9920103"
    assert result["authorization"] == {
        "required": True,
        "status": "not-presented",
        "identity": None,
    }
    assert result["execution"]["canonical_boundary"].endswith("SchoolHeroExecutionEngine")
    assert not any(result["mutation"].values())


def test_road_replay_validates_frozen_plan_receipt_and_bundle(runtime: UnifiedNMARuntime) -> None:
    result = runtime.dispatch({"request": "Show County Highway 126 ROAD", "operation": "replay"})
    assert result["selected_domain"] == "road"
    assert result["plan"]["identity"] == "road-plan-cd434d50bd5b49a012bd1e10"
    assert result["authorization"]["status"] == "frozen-consumed-evidence"
    assert result["execution"]["identity"] == "road-exec-33766f336d9cc18eb2ac159e"
    assert result["verification"]["status"] == "passed-frozen-identity-and-linkage"
    assert result["visualization"]["status"] == "artifact-reference-only"
    assert "not a new ROAD execution" in result["warnings"][0]


def test_build_replay_uses_frozen_validator_and_never_activates(runtime: UnifiedNMARuntime) -> None:
    result = runtime.dispatch(
        {"domain": "build", "request": "Show the frozen BUILD result", "operation": "replay"}
    )
    assert result["selected_domain"] == "build"
    assert result["plan"]["identity"] == (
        "b8b5ecd54954b190eb8cda398710039f334e8424fd0969816380b4a2b52b0b71"
    )
    assert result["execution"]["activation_status"] == "held-not-requested"
    assert result["verification"]["status"] == "passed-frozen-package-validation"
    assert result["receipt"]["identity"] == "build-05-receipt-b8b5ecd54954b190eb8cda39"
    assert result["visualization"]["status"] == "available"
    assert result["mutation"]["automatic_build_activation"] is False


@pytest.mark.parametrize("domain", ["school", "road", "build"])
def test_missing_or_invalid_authorization_never_reaches_execution(
    runtime: UnifiedNMARuntime, domain: str
) -> None:
    with pytest.raises(UnifiedRuntimeError) as missing:
        runtime.dispatch({"domain": domain, "request": f"Execute {domain}", "operation": "execute"})
    assert missing.value.code == "authorization_failure"
    assert missing.value.stage == "authorization"

    with pytest.raises(UnifiedRuntimeError) as invalid:
        runtime.dispatch(
            {
                "domain": domain,
                "request": f"Execute {domain}",
                "operation": "execute",
                "authorization": {"authorization_id": "not-canonical"},
            }
        )
    assert invalid.value.code == "authorization_failure"


@pytest.mark.parametrize("domain", ["school", "road"])
def test_verification_rejects_client_controlled_file_paths(
    runtime: UnifiedNMARuntime, domain: str
) -> None:
    with pytest.raises(UnifiedRuntimeError) as caught:
        runtime.dispatch(
            {
                "domain": domain,
                "request": f"Verify {domain}",
                "operation": "verify",
                "parameters": {
                    "execution_id": "existing-execution",
                    "screenshot_path": "/etc/passwd",
                },
            }
        )
    assert caught.value.code == "invalid_request"
    assert caught.value.stage == "verification"

    with pytest.raises(UnifiedRuntimeError) as traversal:
        runtime.dispatch(
            {
                "domain": domain,
                "request": f"Verify {domain}",
                "operation": "verify",
                "parameters": {"execution_id": "../../outside"},
            }
        )
    assert traversal.value.code == "invalid_request"
    assert traversal.value.stage == "verification"


class ExecutingSpy:
    def __init__(self, storage_root: Path, domain: str):
        self.storage_root = storage_root
        self.domain = domain
        self.calls: list[dict] = []

    def execute_by_id(self, request: dict) -> dict:
        self.calls.append(request)
        execution_id = "exec-school-canonical" if self.domain == "school" else "road-exec-canonical"
        target = self.storage_root / "executions" / execution_id
        target.mkdir(parents=True)
        if self.domain == "school":
            plan = {
                "schema": "nma.school-hero-execution-plan/1.0",
                "execution_plan_id": "school-plan-canonical",
                "plan_sha256": "a" * 64,
            }
            receipt = {
                "schema": "nma.school-hero-execution-receipt/1.0",
                "execution_id": execution_id,
                "authorization": {
                    "authorization_id": request["authorization_id"],
                    "authorization_hash": "b" * 64,
                },
                "receipt_sha256": "c" * 64,
            }
        else:
            plan = {
                "schema": "nma.road-execution-plan/1.0",
                "execution_plan_id": "road-plan-canonical",
                "execution_plan_sha256": "d" * 64,
            }
            receipt = {
                "schema": "nma.road-execution-receipt/1.0",
                "execution_id": execution_id,
                "authorization": {"id": request["authorization_id"], "sha256": "e" * 64},
                "receipt_id": "road-receipt-canonical",
                "receipt_sha256": "f" * 64,
                "frozen_identities": {"road03_authorization_sha256": "e" * 64},
            }
        (target / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        return receipt

    def get_bundle(self, execution_id: str) -> dict:
        return {
            "schema": f"nma.{self.domain}-runtime-bundle/1.0",
            "source": {"id": f"{self.domain}-source", "data": "/data"},
            "layers": [],
        }


@pytest.mark.parametrize("domain", ["school", "road"])
def test_execute_dispatch_calls_existing_domain_engine_not_demo_stub(
    tmp_path: Path, domain: str
) -> None:
    engine = ExecutingSpy(tmp_path / domain, domain)
    adapter = (
        SchoolRuntimeAdapter(
            engine=engine,
            repository_root=ROOT,
            archive_path=ARCHIVE,
            symbol_path=SYMBOL,
        )
        if domain == "school"
        else RoadRuntimeAdapter(engine=engine, repository_root=ROOT, archive_path=ARCHIVE)
    )
    request = {
        "domain": domain,
        "request": f"Execute canonical {domain}",
        "operation": "execute",
        "authorization": {
            "authorization_id": "canonical-authorization",
            "idempotency_key": "canonical-idempotency-key",
        },
    }
    checked = {
        "school": SchoolRuntimeAdapter(
            engine=ExecutingSpy(tmp_path / "unused-school", "school"),
            repository_root=ROOT,
            archive_path=ARCHIVE,
            symbol_path=SYMBOL,
        ),
        "road": RoadRuntimeAdapter(
            engine=ExecutingSpy(tmp_path / "unused-road", "road"),
            repository_root=ROOT,
            archive_path=ARCHIVE,
        ),
        "build": BuildRuntimeAdapter(
            repository_root=ROOT,
            archive_path=ARCHIVE,
        ),
    }
    checked[domain] = adapter
    result = UnifiedNMARuntime(checked).dispatch(request)
    assert engine.calls == [request["authorization"]]
    assert result["execution"]["status"] == "completed-verification-pending"
    assert result["visualization"]["status"] == "available"


def test_build_execute_calls_controlled_build_final_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    policy_sha = "d" * 64

    def load_contract(root):
        calls.append("load_frozen_contract")
        assert root == ROOT
        return {"policy": {"policy_record_sha256": policy_sha}, "contract": {"frozen": True}}

    def load_package(**kwargs):
        calls.append("load_authoritative_package")
        assert kwargs["package_identity"] == "J13_寶山都市計畫/SHP"
        return {
            "binding": {"selected_layer": "J13_BUILD"},
            "authoritative_collection": {"type": "FeatureCollection", "features": []},
            "portrayal_polygonz_collection": {"type": "FeatureCollection", "features": []},
            "source_crs": "EPSG:3826",
            "output_crs": "EPSG:4326",
        }

    def implement(**kwargs):
        calls.append("implement_controlled_building")
        assert kwargs["contract_bundle"]["policy"]["policy_record_sha256"] == policy_sha
        return {
            "record": {
                "schema": "nma.building-controlled-production-implementation/1.0",
                "status": "implementation-complete-activation-hold",
                "implementation_record_sha256": "1" * 64,
                "plan": {
                    "schema": "nma.building-production-execution-plan/1.0",
                    "status": "implementation-ready-activation-hold",
                    "execution_plan_sha256": "2" * 64,
                    "policy_authorization_sha256": policy_sha,
                },
                "observation": {
                    "status": "controlled-implementation-observed",
                    "observation_sha256": "3" * 64,
                },
                "verification": {
                    "status": "passed-controlled-implementation",
                    "verification_sha256": "4" * 64,
                },
                "receipt": {
                    "receipt_sha256": "5" * 64,
                    "production_active": False,
                    "official_portrayal_active": False,
                    "automatic_activation_performed": False,
                },
                "provenance": {
                    "provenance_sha256": "6" * 64,
                    "source_collection_sha256": "7" * 64,
                },
            },
            "maplibre": {"sources": {}, "resources": [], "layers": []},
        }

    def verify(value):
        calls.append("verify_implementation_result")
        assert value["record"]["receipt"]["production_active"] is False
        return True

    monkeypatch.setattr("nma.unified_runtime.load_frozen_contract", load_contract)
    monkeypatch.setattr("nma.unified_runtime.load_authoritative_package", load_package)
    monkeypatch.setattr("nma.unified_runtime.implement_controlled_building", implement)
    monkeypatch.setattr("nma.unified_runtime.verify_implementation_result", verify)
    adapter = BuildRuntimeAdapter(
        repository_root=ROOT,
        archive_path=ARCHIVE,
    )
    result = adapter.dispatch(
        {
            "request": "Execute controlled BUILD",
            "operation": "execute",
            "authorization": {"policy_record_sha256": policy_sha},
            "parameters": {
                "source_package_identity": "J13_寶山都市計畫/SHP",
                "geographic_project_scope": "Baoshan urban-plan project area",
            },
        }
    )
    assert calls == [
        "load_frozen_contract",
        "load_authoritative_package",
        "implement_controlled_building",
        "verify_implementation_result",
    ]
    assert result["execution"]["status"] == "implementation-complete-activation-hold"
    assert result["execution"]["activation_status"] == "held-not-requested"
    assert result["mutation"]["automatic_build_activation"] is False


def test_validation_and_replay_produce_no_filesystem_mutation(
    runtime: UnifiedNMARuntime, tmp_path: Path
) -> None:
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    runtime.dispatch({"domain": "school", "request": "School preview"})
    runtime.dispatch({"domain": "road", "request": "ROAD replay", "operation": "replay"})
    runtime.dispatch({"domain": "build", "request": "BUILD replay", "operation": "replay"})
    with pytest.raises(UnifiedRuntimeError):
        runtime.dispatch({"request": "school road", "operation": "execute"})
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert after == before


def _server_module():
    specification = importlib.util.spec_from_file_location("demo01_server", SERVER_PATH)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def test_server_registers_unified_endpoint_and_preserves_demo_pages() -> None:
    source = SERVER_PATH.read_text(encoding="utf-8")
    page = DEMO_PATH.read_text(encoding="utf-8")
    assert 'route == "/api/nma/runtime"' in source
    assert "UNIFIED_RUNTIME.dispatch(payload)" in source
    assert "NMA_ENABLE_PRIVATE_ARCHIVE" in source
    assert "nmaAgentDemoV1.html" in source
    assert (ROOT / "nmaAgentDemoV032.html").is_file()
    assert "MapLibre" in page
    assert 'endpoint="/api/nma/runtime"' in page
    assert "automatic BUILD activation" in page


def test_live_server_capabilities_page_and_build_request() -> None:
    server_module = _server_module()
    try:
        server = server_module.ThreadingHTTPServer(
            ("127.0.0.1", 0), server_module.NMARequestHandler
        )
    except PermissionError:
        pytest.skip("The active sandbox prohibits loopback socket binding.")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base + "/api/nma/runtime", timeout=5) as response:
            capabilities = json.load(response)
        assert capabilities["domains"] == ["school", "road", "build"]
        assert capabilities["automatic_build_activation"] is False
        with urlopen(base + "/nmaAgentDemoV1.html?basemap=local", timeout=5) as response:
            assert response.status == 200
            assert b"Unified frozen-domain runtime" in response.read()
        request = Request(
            base + "/api/nma/runtime",
            data=json.dumps(
                {
                    "domain": "build",
                    "request": "Show frozen BUILD result",
                    "operation": "replay",
                }
            ).encode(),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            result = json.load(response)
        assert result["selected_domain"] == "build"
        assert result["verification"]["status"] == "passed-frozen-package-validation"

        ambiguous = Request(
            base + "/api/nma/runtime",
            data=json.dumps({"request": "Show school and road"}).encode(),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with pytest.raises(HTTPError) as caught:
            urlopen(ambiguous, timeout=5)
        assert caught.value.code == 400
        error = json.loads(caught.value.read())
        assert error["error"]["code"] == "ambiguous_domain"
        assert error["error"]["mutation_performed"] is False
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

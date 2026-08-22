from __future__ import annotations

from pathlib import Path

import pytest

from nma.unified_runtime import (
    BuildRuntimeAdapter,
    RoadRuntimeAdapter,
    SchoolRuntimeAdapter,
    UnifiedNMARuntime,
    UnifiedRuntimeError,
)


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
SYMBOL = ROOT / "assets/symbols/nlsc112v5.4/school.svg"


class ExecutionTripwire:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root
        self.calls = 0

    def execute_by_id(self, request):  # pragma: no cover - fail-closed tripwire
        self.calls += 1
        raise AssertionError(f"Execution unexpectedly invoked: {request}")


@pytest.fixture()
def runtime(tmp_path: Path) -> tuple[UnifiedNMARuntime, dict[str, ExecutionTripwire]]:
    engines = {
        "school": ExecutionTripwire(tmp_path / "school"),
        "road": ExecutionTripwire(tmp_path / "road"),
    }
    return (
        UnifiedNMARuntime(
            {
                "school": SchoolRuntimeAdapter(
                    engine=engines["school"],
                    repository_root=ROOT,
                    archive_path=ARCHIVE,
                    symbol_path=SYMBOL,
                ),
                "road": RoadRuntimeAdapter(
                    engine=engines["road"],
                    repository_root=ROOT,
                    archive_path=ARCHIVE,
                ),
                "build": BuildRuntimeAdapter(repository_root=ROOT, archive_path=ARCHIVE),
            }
        ),
        engines,
    )


@pytest.mark.parametrize(
    ("payload", "domain"),
    [
        ({"domain": "school", "request": "Inspect School Hero 9920103"}, "school"),
        ({"domain": "road", "request": "Inspect ROAD 9420400"}, "road"),
        ({"domain": "build", "request": "Inspect BUILD 9310100"}, "build"),
        ({"request": "Inspect School Hero 9920103"}, "school"),
        ({"request": "Replay County Highway 126 ROAD", "operation": "replay"}, "road"),
        ({"request": "Replay BUILD 9310100", "operation": "replay"}, "build"),
    ],
)
def test_explicit_and_natural_language_routes_are_deterministic(
    runtime: tuple[UnifiedNMARuntime, dict[str, ExecutionTripwire]],
    payload: dict,
    domain: str,
) -> None:
    result = runtime[0].dispatch(payload)
    assert result["selected_domain"] == domain
    assert result["request_id"].startswith("nma-runtime-request:sha256:")
    assert not any(result["mutation"].values())


def test_school_public_boundary_reports_absent_lifecycle_without_fabrication(
    runtime: tuple[UnifiedNMARuntime, dict[str, ExecutionTripwire]],
) -> None:
    result = runtime[0].dispatch(
        {"domain": "school", "request": "Inspect School Hero 9920103", "operation": "preview"}
    )
    assert result["plan"]["identity"] is None
    assert result["authorization"]["status"] == "not-presented"
    assert result["execution"]["status"] == "not-requested"
    assert result["observation"] is None
    assert result["verification"] is None
    assert result["receipt"] is None
    assert result["provenance"] is None
    assert result["visualization"]["status"] == "unavailable"


def test_road_public_replay_reconstructs_frozen_lineage_but_not_geometry(
    runtime: tuple[UnifiedNMARuntime, dict[str, ExecutionTripwire]],
) -> None:
    result = runtime[0].dispatch(
        {"domain": "road", "request": "Replay County Highway 126 ROAD", "operation": "replay"}
    )
    assert result["plan"]["identity"] == "road-plan-cd434d50bd5b49a012bd1e10"
    assert result["authorization"]["identity"] == "road-03-authorization-f68220ecef989e589dd6e28c"
    assert result["execution"]["identity"] == "road-exec-33766f336d9cc18eb2ac159e"
    assert result["verification"]["status"] == "passed-frozen-identity-and-linkage"
    assert result["receipt"]["sha256"] == (
        "0ab5964fcc2e1f47d43fd328dbc3771a7e624bf4a3707f91236a1485f5610720"
    )
    assert result["provenance"]["status"] == "frozen-content-addressed-lineage"
    assert result["observation"] is None
    assert result["visualization"]["status"] == "artifact-reference-only"


def test_build_public_replay_has_verified_polygon_lineage_and_activation_hold(
    runtime: tuple[UnifiedNMARuntime, dict[str, ExecutionTripwire]],
) -> None:
    result = runtime[0].dispatch(
        {"domain": "build", "request": "Replay BUILD 9310100", "operation": "replay"}
    )
    feature = result["visualization"]["maplibre"]["source"]["data"]["features"][0]
    assert result["plan"]["identity"]
    assert result["authorization"]["identity"]
    assert result["execution"]["identity"]
    assert result["observation"]["identity"]
    assert result["verification"]["status"] == "passed-frozen-package-validation"
    assert result["receipt"]["identity"]
    assert result["provenance"]["identity"]
    assert feature["id"] == (
        "build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f"
    )
    assert feature["geometry"]["type"] == "Polygon"
    assert result["execution"]["activation_status"] == "held-not-requested"
    assert result["mutation"]["automatic_build_activation"] is False


@pytest.mark.parametrize(
    ("payload", "code", "stage"),
    [
        (
            {"domain": "riverl", "request": "Inspect river", "operation": "preview"},
            "unsupported_domain",
            "request",
        ),
        (
            {"request": "Show the school and road", "operation": "preview"},
            "ambiguous_domain",
            "request",
        ),
        (
            {"domain": "school", "request": "", "operation": "preview"},
            "invalid_request",
            "request",
        ),
        (
            {"domain": "school", "request": "Execute school", "operation": "execute"},
            "authorization_failure",
            "authorization",
        ),
        (
            {
                "domain": "build",
                "request": "Execute BUILD",
                "operation": "execute",
                "authorization": {"policy_record_sha256": "0" * 64},
                "parameters": {
                    "source_package_identity": "J13_寶山都市計畫/SHP",
                    "geographic_project_scope": "Baoshan urban-plan project area",
                },
            },
            "authorization_failure",
            "authorization",
        ),
        (
            {
                "domain": "build",
                "request": "Verify BUILD",
                "operation": "verify",
                "parameters": {"execution_id": "malformed"},
            },
            "invalid_request",
            "verification",
        ),
        (
            {"domain": "build", "request": "Activate BUILD production", "operation": "activate"},
            "invalid_request",
            "request",
        ),
        (
            {
                "domain": "school",
                "request": "Show School feature 9999999",
                "operation": "preview",
            },
            "unsupported_capability",
            "routing",
        ),
    ],
)
def test_negative_flows_fail_before_domain_execution(
    runtime: tuple[UnifiedNMARuntime, dict[str, ExecutionTripwire]],
    payload: dict,
    code: str,
    stage: str,
) -> None:
    with pytest.raises(UnifiedRuntimeError) as caught:
        runtime[0].dispatch(payload)
    assert caught.value.code == code
    assert caught.value.stage == stage
    assert runtime[1]["school"].calls == 0
    assert runtime[1]["road"].calls == 0


def test_missing_public_dependency_fails_closed_without_fallback(tmp_path: Path) -> None:
    adapter = BuildRuntimeAdapter(repository_root=tmp_path, archive_path=tmp_path / "absent.zip")
    with pytest.raises(UnifiedRuntimeError) as caught:
        adapter.dispatch(
            {
                "request": "Replay BUILD 9310100",
                "operation": "replay",
                "authorization": None,
                "parameters": {},
            }
        )
    assert caught.value.code == "missing_dependency"
    assert caught.value.stage == "dependency"
    assert list(tmp_path.iterdir()) == []


def test_production_demo_path_has_no_stub_executor() -> None:
    source = (ROOT / "src/nma/unified_runtime.py").read_text(encoding="utf-8")
    assert "self.engine.execute_by_id(authorization)" in source
    assert "implement_controlled_building(" in source
    assert "class DemoStub" not in source
    assert "authorized = True" not in source


def test_browser_surface_exposes_runtime_state_lineage_and_errors() -> None:
    page = (ROOT / "nmaAgentDemoV1.html").read_text(encoding="utf-8")
    for required in (
        'endpoint="/api/nma/runtime"',
        'id="domain"',
        'id="request"',
        'id="status"',
        'id="routing"',
        'id="lifecycle"',
        'id="provenance"',
        'id="map"',
        "body.error?.code",
    ):
        assert required in page

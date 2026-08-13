from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"
SPEC_PATH = ROOT / "data/specifications/nma-runtime-graph-backend-v0.29.json"


def load_server():
    spec = importlib.util.spec_from_file_location("nma_agent_server_v029_test", SERVER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v029_runtime_cases_are_fixed_and_cover_point_line_polygon_and_conflict() -> None:
    specification = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert specification["status"] == (
        "prospective-fixed-runtime-wiring-cases-before-live-run"
    )
    assert len(specification["cases"]) == 4
    assert {item["geometry"] for item in specification["cases"]} >= {
        "Point",
        "LineString",
        "Polygon",
    }
    assert any(item["expected_status"] == "retrieved-with-conflict" for item in specification["cases"])


def test_v029_every_typed_package_receives_visible_backend_trace(monkeypatch) -> None:
    server = load_server()
    trace = {
        "contract": "nma.runtime-graph-backend/0.29",
        "requested_backend": "neo4j",
        "active_backend": "live-neo4j",
        "fallback_used": False,
        "typed_tool_only": True,
        "arbitrary_cypher_allowed": False,
    }
    monkeypatch.setattr(server, "_GRAPH_BACKEND_TRACE", trace)
    monkeypatch.setattr(server, "_RETRIEVER", object())
    package = {"retrieval_trace": {}, "automatic_rule_activation": False}
    actual = server.attach_graph_backend_trace_v029(package)
    assert actual["retrieval_trace"]["v029_graph_backend"] == trace
    assert actual["retrieval_trace"]["v029_graph_backend"] is not trace

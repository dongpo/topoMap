from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "data/runtime/nma-runtime-baseline-v0.32.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v032_offline_baseline_binds_current_graph_and_projection() -> None:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    graph = ROOT / payload["canonical_graph"]["path"]
    projection = ROOT / payload["neo4j_projection"]["path"]
    round_trip = ROOT / payload["neo4j_offline_round_trip"]["path"]

    assert payload["schema"] == "nma.runtime-baseline/0.32"
    assert payload["runtime_release"] == "v0.2.1"
    assert sha256(graph) == payload["canonical_graph"]["sha256"]
    assert sha256(projection) == payload["neo4j_projection"]["sha256"]
    assert sha256(round_trip) == payload["neo4j_offline_round_trip"]["sha256"]

    graph_payload = json.loads(graph.read_text(encoding="utf-8"))
    projection_payload = json.loads(projection.read_text(encoding="utf-8"))
    round_trip_payload = json.loads(round_trip.read_text(encoding="utf-8"))
    graph_sha = payload["canonical_graph"]["sha256"]

    assert graph_payload["statistics"]["nodes"] == 4293
    assert graph_payload["statistics"]["edges"] == 11244
    assert projection_payload["canonical_graph_sha256"] == graph_sha
    assert round_trip_payload["canonical_graph_sha256"] == graph_sha
    assert round_trip_payload["canonical_reconstruction_lossless"] is True
    assert payload["canonical_graph"]["authority"] == "consolidated-runtime-artifact"
    assert payload["canonical_graph"]["component_paths_role"] == "provenance-metadata-only"
    assert (ROOT / payload["canonical_graph"]["provenance_policy"]).is_file()


def test_v032_baseline_records_verified_external_runtime_without_overclaiming_http() -> None:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))

    vector = ROOT / payload["vector_index"]["required_path"]
    live_round_trip = ROOT / payload["neo4j_live_round_trip"]["path"]
    parity = ROOT / payload["neo4j_retrieval_parity"]["path"]
    backend = ROOT / payload["agent_server"]["runtime_backend_evidence"]

    assert sha256(vector) == payload["vector_index"]["sha256"]
    assert payload["vector_index"]["records"] == 4293
    vector_payload = json.loads(vector.read_text(encoding="utf-8"))
    assert vector_payload["canonical_graph_sha256"] == payload["canonical_graph"]["sha256"]
    assert sha256(live_round_trip) == payload["neo4j_live_round_trip"]["sha256"]
    assert payload["neo4j_live_round_trip"]["live_round_trip_verified"] is True
    assert sha256(parity) == payload["neo4j_retrieval_parity"]["sha256"]
    assert payload["neo4j_retrieval_parity"]["retrieval_parity_verified"] is True
    assert sha256(backend) == payload["agent_server"]["runtime_backend_evidence_sha256"]
    assert payload["agent_server"]["graph_identity_verified"] is True
    assert payload["agent_server"]["runtime_contract"] == payload["schema"]
    assert payload["agent_server"]["runtime_revision"] == payload["schema"]
    assert payload["agent_server"]["vector_index"] == payload["vector_index"]["required_path"]
    assert payload["agent_server"]["vector_canonical_graph_sha256"] == payload["canonical_graph"]["sha256"]
    assert "deferred-to-F07" in payload["agent_server"]["http_socket_smoke_test"]
    assert payload["verification"]["historical_artifacts_overwritten"] is False
    assert len(payload["remaining_gates"]) == 1

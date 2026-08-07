from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from .demo_contract import check_demo_contract
from .demo_offline import check_offline_runtime
from .historical_release import verify_manifest_snapshot
from .paths import resolve_asset


EXPECTED_FREEZE = "nma-agentic-v0.3-rc1"
EXPECTED_STATUS = "candidate-frozen"
EXPECTED_INCREMENT_IDS = {"A01", "A02", "A03", "A04", "A05", "A06"}
EXPECTED_CATALOG_COUNTS = {
    "implementation-only": 28,
    "style-variant": 5,
    "evidence-backed": 5,
    "conflicted": 4,
}
EXPECTED_INTENTS = {
    "inspect_feature",
    "propose_style_revision",
    "approve_revision",
    "discard_revision",
    "finish_revisions",
    "request_layer_confirmation",
    "reset_session",
    "abstain",
}


def _expect(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_agent_server(path: Path):
    module_name = "_nma_agentic_v03_freeze_server"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise ValueError(f"could not load agent server: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_agentic_freeze(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_asset(path).read_text(encoding="utf-8"))


def check_agentic_freeze(
    path: str | Path = "data/demo/agentic-v0.3-freeze.json",
) -> dict[str, Any]:
    manifest = load_agentic_freeze(path)
    _expect(manifest["freeze_version"], EXPECTED_FREEZE, "freeze version")
    _expect(manifest["status"], EXPECTED_STATUS, "freeze status")
    _expect(
        {item["id"] for item in manifest["approved_increments"]},
        EXPECTED_INCREMENT_IDS,
        "approved increment set",
    )
    _expect(manifest["source"]["public_deployment"], "not-deployed", "public deployment")
    _expect(
        manifest["source"]["prior_public_release"],
        "nma-demo-v0.2-rc1",
        "prior public release",
    )
    if manifest["blocking_defects"]:
        raise ValueError("Agentic v0.3 freeze cannot contain an unresolved blocking defect")

    approved_commit = manifest["source"]["approved_through_commit"]
    if len(approved_commit) != 40 or any(
        character not in "0123456789abcdef" for character in approved_commit
    ):
        raise ValueError("approved-through commit must be a full lowercase Git SHA")

    artifact_paths = [artifact["path"] for artifact in manifest["artifacts"]]
    if len(artifact_paths) != len(set(artifact_paths)):
        raise ValueError("Agentic v0.3 freeze contains duplicate artifact paths")
    if any(path.endswith((".pptx", ".pdf")) for path in artifact_paths):
        raise ValueError("owner-controlled presentation or PDF cannot enter the Agentic freeze")

    artifact_results = []
    for artifact in manifest["artifacts"]:
        asset = resolve_asset(artifact["path"])
        if not asset.is_file():
            raise ValueError(f"missing Agentic v0.3 artifact: {artifact['path']}")
        actual_size = asset.stat().st_size
        actual_sha = _sha256(asset)
        _expect(actual_size, artifact["size_bytes"], f"{artifact['path']} size")
        _expect(actual_sha, artifact["sha256"], f"{artifact['path']} SHA-256")
        artifact_results.append(
            {
                "path": artifact["path"],
                "role": artifact["role"],
                "size_bytes": actual_size,
                "sha256": actual_sha,
            }
        )

    contract = check_demo_contract(manifest["acceptance"]["five_scene_contract"])
    offline = check_offline_runtime(manifest["acceptance"]["offline_runtime"])
    _expect(contract["scene_count"], 5, "five-scene contract count")
    _expect(offline["runtime_version"], "nma-agentic-v0.3-a06", "offline runtime version")

    catalog = json.loads(
        resolve_asset(manifest["acceptance"]["capability_catalog"]).read_text(encoding="utf-8")
    )
    _expect(catalog["count"], 42, "capability count")
    _expect(catalog["status_counts"], EXPECTED_CATALOG_COUNTS, "capability status counts")
    evidence_linked = sum(
        catalog["status_counts"][status] for status in ("evidence-backed", "conflicted")
    )
    _expect(evidence_linked, 9, "graph-evidence-linked capability count")

    graph = json.loads(
        resolve_asset(manifest["acceptance"]["portrayal_graph"]).read_text(encoding="utf-8")
    )
    _expect(len(graph["nodes"]), 44, "portrayal graph node count")
    _expect(len(graph["edges"]), 85, "portrayal graph edge count")

    server = _load_agent_server(resolve_asset(manifest["acceptance"]["agent_server"]))
    _expect(server.DEFAULT_MODEL, "gpt-5.6-terra", "default language model")
    _expect(set(server.INTENTS), EXPECTED_INTENTS, "bounded intent set")
    _expect(
        server.SYMBOL_EDIT_PLAN_SCHEMA,
        "nma.symbol-edit-plan/1.0",
        "symbol edit plan schema",
    )
    inspection = server.inspect_bundled_dataset("school-points")
    collection = server.export_bundled_geojson("school-points")
    _expect(inspection["ready"], True, "school Shapefile readiness")
    _expect(inspection["inspection"]["feature_count"], 12, "school feature count")
    _expect(collection["nma:provenance"]["source_crs"], "EPSG:3826", "school source CRS")
    _expect(collection["nma:provenance"]["output_crs"], "EPSG:4326", "school output CRS")
    _expect(collection["nma:provenance"]["read_only_source"], True, "school source read mode")

    html = resolve_asset("nmaAgentDemo.html").read_text(encoding="utf-8")
    required_markers = {
        "Agentic Demo v0.3",
        "function renderKnowledgeGraph(decision)",
        "function renderSymbolWorkshop(decision)",
        "function approveStyleRevision()",
        "function validateSymbolEditPlan(plan,supported)",
        "Agent interpretation · SymbolEditPlan",
        "async function prepareLayerProposal()",
        "async function createApprovedLayer(approvalSource)",
        "function deterministicRoute(message)",
        "local PMTiles basemap fallback",
    }
    missing_markers = sorted(marker for marker in required_markers if marker not in html)
    if missing_markers:
        raise ValueError(f"Agentic demo is missing required runtime markers: {missing_markers}")

    historical_results = []
    for baseline in manifest["historical_baselines"]:
        historical_results.append(
            verify_manifest_snapshot(
                baseline["manifest"],
                baseline["snapshot_commit"],
                artifact_key=baseline["artifact_key"],
            )
        )

    return {
        "freeze_version": manifest["freeze_version"],
        "status": "passed",
        "approved_through_commit": approved_commit,
        "approved_increment_count": len(manifest["approved_increments"]),
        "artifact_count": len(artifact_results),
        "scene_count": contract["scene_count"],
        "capability_count": catalog["count"],
        "evidence_linked_capability_count": evidence_linked,
        "graph_nodes": len(graph["nodes"]),
        "graph_edges": len(graph["edges"]),
        "school_fixture_features": inspection["inspection"]["feature_count"],
        "offline_runtime": offline["runtime_version"],
        "historical_baseline_count": len(historical_results),
        "public_deployment": manifest["source"]["public_deployment"],
        "blocking_defect_count": len(manifest["blocking_defects"]),
    }

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"
BUILDER_PATH = ROOT / "scripts/build_nma_agentic_v031_demo.py"
SOURCE = ROOT / "nmaAgentDemoV04.html"
TARGET = ROOT / "nmaAgentDemoV031.html"
WORKER_SOURCE = ROOT / "nmaDemoWorkerV04.js"
WORKER_TARGET = ROOT / "nmaDemoWorkerV031.js"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def evidence_package() -> dict:
    return {
        "status": "retrieved",
        "resolved_entities": [
            {"id": "portrayal-rule:doc01:9120200", "type": "PortrayalRule"}
        ],
        "evidence_nodes": [
            {"id": "portrayal-rule:doc01:9120200", "type": "PortrayalRule"},
            {"id": "section:doc01-portrayal:p2", "type": "DocumentSection"},
        ],
        "citations": [
            {
                "citation_id": "citation:section:doc01-portrayal:p2",
                "filename": "01-一千分之一地形圖圖式規格表.pdf",
                "page": 2,
            }
        ],
        "graph_paths": {
            "nodes": [
                "portrayal-rule:doc01:9120200",
                "section:doc01-portrayal:p2",
            ],
            "edges": [
                {
                    "source": "portrayal-rule:doc01:9120200",
                    "type": "EVIDENCED_ON",
                    "target": "section:doc01-portrayal:p2",
                }
            ],
        },
        "retrieval_trace": {
            "selected_seed_ids": ["portrayal-rule:doc01:9120200"],
            "ranked_candidates": [{"id": "portrayal-rule:doc01:9120200"}],
            "v108_llm_entity_resolution_used": True,
            "v108_raw_resolution_snapshot": {"status": "resolved"},
            "v108_policy_normalized_selected_node_ids": [
                "portrayal-rule:doc01:9120200"
            ],
            "v029_graph_backend": {
                "contract": "nma.runtime-graph-backend/0.29",
                "requested_backend": "neo4j",
                "active_backend": "live-neo4j",
                "fallback_backend": "canonical-json",
                "fallback_used": False,
                "fallback_reason_code": None,
                "graph_revision": "nma-canonical-graph-v0.4",
                "graph_identity_verified": True,
                "active_graph_authoritative": True,
                "neo4j_database": "mapfeatures",
                "live_nodes": 2327,
                "live_edges": 7012,
                "typed_tool_only": True,
                "arbitrary_cypher_allowed": False,
                "automatic_rule_activation": False,
            },
        },
    }


def grounded_answer() -> dict:
    return {
        "status": "answered",
        "answer": "應選三角點 9120200。",
        "resolved_entity_ids": ["portrayal-rule:doc01:9120200"],
        "evidence_node_ids": ["portrayal-rule:doc01:9120200"],
        "citation_ids": ["citation:section:doc01-portrayal:p2"],
        "missing_evidence": [],
        "next_action": "inspect_symbol",
        "automatic_action": False,
    }


def test_v031_runtime_contract_exposes_live_backend_and_validated_identifiers() -> None:
    server = load_module(SERVER_PATH, "nma_agent_server_v031_contract")
    contract = server.build_demo_runtime_contract_v031(
        evidence_package(), grounded_answer()
    )

    assert contract["schema"] == "nma.demo-runtime/0.31"
    assert contract["resolution"] == {
        "mode": "bounded-llm-entity-resolution",
        "status": "resolved",
        "selected_node_ids": ["portrayal-rule:doc01:9120200"],
        "candidate_count": 1,
        "allowlisted_selection": True,
    }
    backend = contract["graph"]["backend"]
    assert backend["active_backend"] == "live-neo4j"
    assert backend["fallback_used"] is False
    assert backend["graph_identity_verified"] is True
    assert backend["neo4j_database"] == "mapfeatures"
    assert contract["answer_validation"]["citation_ids_used"] == [
        "citation:section:doc01-portrayal:p2"
    ]
    assert contract["safety"]["execution_performed"] is False
    assert contract["safety"]["map_mutation_performed"] is False
    assert "usage" not in contract
    assert "estimated_cost_usd" not in str(contract)


def test_v031_runtime_contract_rejects_an_identifier_outside_the_package() -> None:
    server = load_module(SERVER_PATH, "nma_agent_server_v031_reject")
    answer = grounded_answer()
    answer["citation_ids"] = ["citation:invented"]

    with pytest.raises(server.AgentError, match="outside the evidence package"):
        server.build_demo_runtime_contract_v031(evidence_package(), answer)


def test_v031_demo_is_reproducible_and_preserves_v04() -> None:
    builder = load_module(BUILDER_PATH, "nma_agentic_v031_demo_builder")
    source = SOURCE.read_text(encoding="utf-8")
    target = TARGET.read_text(encoding="utf-8")

    assert target == builder.build(source)
    assert "Agentic Demo v0.4" in source
    assert "Agentic Demo v0.31" in target
    assert WORKER_TARGET.read_text(encoding="utf-8") == builder.build_worker(
        WORKER_SOURCE.read_text(encoding="utf-8")
    )


def test_v031_demo_shows_runtime_spine_without_cost_or_automatic_execution() -> None:
    html = TARGET.read_text(encoding="utf-8")

    assert 'runtime.schema!=="nma.demo-runtime/0.31"' in html
    assert "Verified Agent runtime spine" in html
    assert "live Neo4j verified" in html
    assert "graph identity verified" in html
    assert "Typed graph relations" in html
    assert "used by answer" in html
    assert "arbitrary Cypher disabled" in html
    assert "no automatic acceptance, execution, or map mutation" in html
    assert "Agent runtime failed closed" in html
    assert "No GraphRAG answer, tool execution, or map mutation was accepted." in html
    assert "failed closed · ${code}" in html
    assert "function renderAgenticEvidenceSummary(grounding)" in html
    assert 'outcome:answerStatus==="answered"?"answered-non-executable":answerStatus' in html
    assert "informational GraphRAG answers do not create symbols, layers, or map mutations" in html
    assert "token usage" not in html
    assert "estimated total US$" not in html
    assert 'register("nmaDemoWorkerV031.js"' in html
    assert 'const CACHE_NAME = "nma-agentic-v0.31.2-grounding-panels";' in (
        WORKER_TARGET.read_text(encoding="utf-8")
    )


def test_v031_server_uses_the_validated_runtime_components() -> None:
    source = SERVER_PATH.read_text(encoding="utf-8")
    specification = (
        ROOT / "data/specifications/nma-demo-runtime-v0.31.json"
    ).read_text(encoding="utf-8")

    assert "SegmentAwareGraphRetrieverV108(" in source
    assert "PolicyValidatedEntityResolverV106(" in source
    assert 'trace["retrieval_policy_version"] = "0.10.8"' in source
    assert 'DEMO_RUNTIME_REVISION = "v0.31.1-dynamic-answer-identifier-allowlist"' in source
    assert '"candidate_pool_contract": "nma.entity-candidate-pool/0.10.8"' in specification
    assert '"entity_resolution_contract": "nma.entity-resolution/0.10.6"' in specification
    assert '"answer_keys_used": false' in specification

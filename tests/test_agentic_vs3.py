import json
import importlib.util
from pathlib import Path
import shutil
import sys

import pytest

from nma.agentic_vs3 import (
    RealLayerPlanningError,
    build_real_layer_plan_payload,
    parse_real_layer_plan_response,
)
from nma.graphrag import CanonicalGraphRetriever
from nma.real_layer import REAL_LAYER_PROFILES


ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"


def package(query: str) -> dict:
    return CanonicalGraphRetriever.load(GRAPH).evidence_package(
        query, max_depth=4, max_nodes=100
    )


def response(profile_id: str, evidence: dict, *, change: dict | None = None) -> dict:
    candidate = REAL_LAYER_PROFILES[profile_id]
    body = {
        "status": "proposed",
        "reply": "已依正式圖譜與實際資料欄位提出轉檔計畫，尚未執行。",
        "profile_id": profile_id,
        "feature_code": candidate["feature_code"],
        "feature_name": candidate["feature_name"],
        "geometry_role": candidate["geometry_role"],
        "product_layer": candidate["product_layer"],
        "source_layers": candidate["source_layer_ids"],
        "source_filter": {
            "field": candidate["feature_code_field"],
            "operator": "equals",
            "value": candidate["feature_code"],
        },
        "field_mapping": {
            "id": candidate["id_field"],
            "feature_code": candidate["feature_code_field"],
            "label": candidate["label_field"],
        },
        "operations": [
            "extract-reviewed-components",
            "filter",
            "reproject-to-epsg-4326",
            "drop-z",
        ],
        "evidence_node_ids": candidate["evidence_node_ids"],
        "citation_ids": [evidence["citations"][0]["citation_id"]],
    }
    body.update(change or {})
    return {
        "id": "resp_vs3",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(body)}],
            }
        ],
        "usage": {"input_tokens": 900, "output_tokens": 110, "total_tokens": 1010},
    }


@pytest.mark.parametrize(
    ("profile_id", "query"),
    [
        ("school-point", "小學 9920103 MARK 圖層"),
        ("river-line", "江、河、溪 9510101 RIVERL 圖層"),
        ("building-polygon", "永久性建物 9310100 BUILD 圖層"),
    ],
)
def test_vs3_payload_and_parser_preserve_reviewed_mapping(profile_id: str, query: str) -> None:
    candidate = REAL_LAYER_PROFILES[profile_id]
    evidence = package(query)
    payload = build_real_layer_plan_payload(
        model="gpt-5.6-terra",
        user_request="請用真實 Shapefile 建立圖層",
        profile_id=profile_id,
        candidate=candidate,
        evidence_package=evidence,
    )
    supplied = json.loads(payload["input"][0]["content"])
    parsed = parse_real_layer_plan_response(
        response(profile_id, evidence),
        profile_id=profile_id,
        candidate=candidate,
        evidence_package=evidence,
    )

    assert payload["text"]["format"]["strict"] is True
    assert supplied["reviewed_candidate"]["source_layer_ids"] == candidate["source_layer_ids"]
    assert supplied["evidence"]["automatic_rule_activation"] is False
    assert parsed["profile_id"] == profile_id
    assert parsed["geometry_role"] == candidate["geometry_role"]
    assert parsed["approval_granted"] is False
    assert parsed["execution_performed"] is False
    assert parsed["automatic_action"] is False


def test_vs3_rejects_changed_field_or_invented_citation() -> None:
    profile_id = "school-point"
    candidate = REAL_LAYER_PROFILES[profile_id]
    evidence = package("小學 9920103 MARK 圖層")
    changed = response(
        profile_id,
        evidence,
        change={
            "field_mapping": {
                "id": "MARKID",
                "feature_code": "MARKTYPE1",
                "label": "MARKNAME1",
            }
        },
    )
    with pytest.raises(RealLayerPlanningError, match="field_mapping"):
        parse_real_layer_plan_response(
            changed,
            profile_id=profile_id,
            candidate=candidate,
            evidence_package=evidence,
        )

    invented = response(profile_id, evidence, change={"citation_ids": ["invented"]})
    with pytest.raises(RealLayerPlanningError, match="citations"):
        parse_real_layer_plan_response(
            invented,
            profile_id=profile_id,
            candidate=candidate,
            evidence_package=evidence,
        )


@pytest.mark.skipif(
    not (ROOT / "data/datasets/112年多維度SHP成果_0502.zip").is_file()
    or not shutil.which("ogrinfo")
    or not shutil.which("ogr2ogr"),
    reason="The private real source archive and GDAL are required.",
)
def test_vs3_server_requires_approval_then_executes_real_geometry(monkeypatch) -> None:
    spec = importlib.util.spec_from_file_location("nma_agent_server_vs3", SERVER_PATH)
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = server
    spec.loader.exec_module(server)

    def fake_call(payload, api_key):
        supplied = json.loads(payload["input"][0]["content"])
        return response("school-point", supplied["evidence"])

    monkeypatch.setattr(server, "call_openai", fake_call)
    monkeypatch.setattr(server, "REAL_LAYER_PROPOSALS", server.RealLayerProposalStore())
    monkeypatch.setattr(
        server,
        "retrieve_evidence",
        lambda query, api_key, **kwargs: server.canonical_retriever().evidence_package(
            query, **{key: value for key, value in kwargs.items() if key != "model"}
        ),
    )
    result = server.orchestrate_real_layer(
        {"profile_id": "school-point", "message": "以真實 Shapefile 建立小學圖層"},
        "sk-proj-placeholder",
        "gpt-5.6-terra",
    )

    assert result["schema"] == "nma.agentic-vs3-real-layer/0.4"
    assert result["plan"]["execution_performed"] is False
    assert result["proposal_state"]["status"] == "pending-approval"
    assert result["trace"]["events"][-1]["status"] == "pending"
    proposal_id = result["proposal_state"]["proposal_id"]
    executed = server.execute_real_layer_proposal(
        {"proposal_id": proposal_id, "decision": "approve"}
    )

    assert executed["status"] == "executed-after-approval"
    assert executed["observation"]["feature_count"] == 15
    assert executed["observation"]["provenance"]["synthetic"] is False
    assert executed["output_url"].startswith("/artifacts/tmp/real-layer-v04/")
    assert executed["output_url"].endswith("/school-point.geojson")
    assert executed["qa"]["status"] == "passed"
    assert {item["id"] for item in executed["qa"]["checks"]} == {
        "feature-count",
        "geometry-role",
        "source-filter",
        "real-coordinates",
    }
    assert executed["citation_ids"]
    assert [event["stage"] for event in executed["trace"]["events"]] == [
        "approve",
        "execute",
        "observe",
        "qa",
        "cite",
    ]
    assert executed["trace"]["events"][3]["status"] == "passed"
    assert executed["map_mutation_performed"] is False
    with pytest.raises(server.AgentError, match="already has a final decision"):
        server.execute_real_layer_proposal(
            {"proposal_id": proposal_id, "decision": "approve"}
        )

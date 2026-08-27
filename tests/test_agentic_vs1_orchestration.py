import importlib.util
import json
from pathlib import Path
import sys

from nma.vector_index import QueryEmbeddingCache


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "scripts" / "run_nma_agent_server.py"
SPEC = importlib.util.spec_from_file_location("nma_agent_server_vs1", SERVER_PATH)
assert SPEC and SPEC.loader
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)


def route_response(query: str, code: str | None) -> dict:
    route = {
        "intent": "inspect_feature",
        "feature_query": query,
        "feature_code": code,
        "style_request": None,
        "style_plan": None,
        "reply": "將檢索正式文件與圖譜證據。",
    }
    return {
        "id": "resp_route",
        "output": [
            {
                "type": "function_call",
                "name": "route_nma_turn",
                "call_id": "call_route",
                "arguments": json.dumps(route, ensure_ascii=False),
            }
        ],
        "usage": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
    }


def answer_from_payload(payload: dict) -> dict:
    package = json.loads(payload["input"][0]["output"])
    retrieved = package["status"] == "retrieved"
    citations = package["citations"]
    answer = {
        "status": "answered" if retrieved else "abstained",
        "answer": (
            "小學圖式規則見正式規格表第 61 頁。"
            if retrieved
            else "目前的已審核圖譜沒有這個圖徵，因此停止回答。"
        ),
        "resolved_entity_ids": (
            [item["id"] for item in package["resolved_entities"]]
            if retrieved
            else []
        ),
        "evidence_node_ids": (
            [
                next(
                    node["id"]
                    for node in package["evidence_nodes"]
                    if node["id"] == "portrayal-rule:doc01:9920103"
                )
            ]
            if retrieved
            else []
        ),
        "citation_ids": (
            [next(item["citation_id"] for item in citations if item.get("page") == 61)]
            if retrieved
            else []
        ),
        "missing_evidence": [] if retrieved else package["missing_evidence"],
        "next_action": "inspect_symbol" if retrieved else "clarify",
    }
    return {
        "id": "resp_answer",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(answer)}],
            }
        ],
        "usage": {"input_tokens": 1_000, "output_tokens": 60, "total_tokens": 1_060},
    }


def client_payload(message: str) -> dict:
    return {
        "session_id": "session_vs1_test",
        "message": message,
        "context": {},
        "tool_result": None,
    }


def raw_resolution(
    *, status: str, selected_node_ids: list[str], summary: str, question: str = ""
) -> dict:
    return {
        "schema": "nma.entity-resolution/0.10.1",
        "status": status,
        "resolved_entities": [
            {
                "query_segment": summary,
                "selected_node_id": node_id,
                "confidence": "high",
                "evidence_basis": ["official-name", "hierarchy-context"],
            }
            for node_id in selected_node_ids
        ],
        "clarification_question": question,
        "decision_summary": summary,
        "selected_node_ids": selected_node_ids,
        "candidate_pool_sha256": "set-by-test-resolver",
        "response_id": "resp_entity_resolution_test",
        "response_model": "gpt-5.6-terra",
        "usage": {"input_tokens": 700, "output_tokens": 80, "total_tokens": 780},
        "hidden_chain_of_thought_exposed": False,
        "automatic_rule_activation": False,
    }


def canonical_evidence_without_model(query: str, **kwargs) -> dict:
    kwargs.pop("model", None)
    return SERVER.canonical_retriever().evidence_package(query, **kwargs)


def test_live_server_retrieval_path_uses_provider_query_embedding_and_hybrid_graph(
    monkeypatch,
) -> None:
    query = "道路旁可接消防水帶、提供滅火用水的柱狀設施，地圖上如何表示？"
    cache = QueryEmbeddingCache.load(
        ROOT / "data/runtime/vector/nma-semantic-dev-query-vectors-v0.4.json"
    )

    def fake_embed_batch(self, texts, *, model, dimensions):
        assert texts == [query]
        cached = cache.embed_query(query, model, dimensions)
        return {
            "vectors": [cached["vector"]],
            "response_model": model,
            "usage": {"prompt_tokens": 19, "total_tokens": 19},
        }

    monkeypatch.setattr(SERVER.OpenAIEmbeddingClient, "embed_batch", fake_embed_batch)
    monkeypatch.setattr(
        SERVER.OpenAIEntityResolverV106,
        "resolve",
        lambda self, pool: raw_resolution(
            status="resolved",
            selected_node_ids=["portrayal-rule:doc01:9350906"],
            summary="消防栓",
        ),
    )
    monkeypatch.setattr(SERVER, "_RETRIEVER", None)
    monkeypatch.setattr(SERVER, "_VECTOR_INDEX", None)
    monkeypatch.setattr(SERVER, "_RETRIEVAL_ANCHORS", None)
    monkeypatch.setattr(SERVER, "_CITATION_SOURCE_REGISTRY", None)
    monkeypatch.setattr(SERVER, "_APPROVED_SEMANTIC_LINKS", None)
    package = SERVER.retrieve_evidence(
        query,
        "sk-proj-placeholder",
        max_depth=3,
        max_nodes=100,
    )

    assert package["status"] == "retrieved"
    assert package["retrieval_trace"]["retrieval_policy_version"] == "0.10.8"
    assert package["retrieval_trace"]["v031_runtime_integration"] == (
        "v108-pool-v106-resolver-active"
    )
    assert package["retrieval_trace"]["v108_policy_validation"]["outcome"] == (
        "not-applicable"
    )
    assert package["retrieval_trace"]["v06_citation_integrity"] == "passed"
    assert package["retrieval_trace"]["v108_query_embedding_usage"] == {
        "prompt_tokens": 19,
        "total_tokens": 19,
    }
    assert package["retrieval_trace"]["selected_seed_ids"][0] == (
        "portrayal-rule:doc01:9350906"
    )


def test_live_server_policy_validator_anchors_unique_hierarchy_without_new_call(
    monkeypatch,
) -> None:
    query = "只知道它是一片地表水域，尚未辨識為湖、庫、池或濕地；應直接套用哪個圖式？"
    cache = QueryEmbeddingCache.load(
        ROOT / "data/runtime/vector/nma-v09-query-vectors.json"
    )

    def fake_embed_batch(self, texts, *, model, dimensions):
        cached = cache.embed_query(texts[0], model, dimensions)
        return {
            "vectors": [cached["vector"]],
            "response_model": model,
            "usage": {"prompt_tokens": 21, "total_tokens": 21},
        }

    monkeypatch.setattr(SERVER.OpenAIEmbeddingClient, "embed_batch", fake_embed_batch)
    monkeypatch.setattr(
        SERVER.OpenAIEntityResolverV106,
        "resolve",
        lambda self, pool: raw_resolution(
            status="needs-clarification",
            selected_node_ids=[],
            summary="「面狀水域」是分類階層，必須確認具體水域類型。",
            question="請確認湖泊、水庫、池塘或濕地。",
        ),
    )
    package = SERVER.retrieve_evidence(
        query, "sk-proj-placeholder", max_depth=3, max_nodes=100
    )

    trace = package["retrieval_trace"]
    assert package["status"] == "needs-clarification"
    assert trace["selected_seed_ids"] == ["classification-hierarchy:doc01:9520000"]
    assert trace["v108_raw_resolution_snapshot"]["selected_node_ids"] == []
    assert trace["v108_policy_validation"]["outcome"] == (
        "unique-exact-hierarchy-anchor-added"
    )
    assert trace["v108_new_openai_request_for_validation"] is False
    assert any(item["page"] == 39 for item in package["citations"])


def test_live_server_v108_anchors_unique_explicit_hierarchy_code(monkeypatch) -> None:
    query = "目前只知道對象屬於交通系統，尚未辨認是鐵路、道路、捷運、機場或港灣；能直接決定單一圖式嗎？"
    cache = QueryEmbeddingCache.load(
        ROOT / "data/runtime/vector/nma-v011-query-vectors.json"
    )

    def fake_embed_batch(self, texts, *, model, dimensions):
        cached = cache.embed_query(texts[0], model, dimensions)
        return {
            "vectors": [cached["vector"]],
            "response_model": model,
            "usage": {"prompt_tokens": 22, "total_tokens": 22},
        }

    monkeypatch.setattr(SERVER.OpenAIEmbeddingClient, "embed_batch", fake_embed_batch)
    monkeypatch.setattr(
        SERVER.OpenAIEntityResolverV106,
        "resolve",
        lambda self, pool: raw_resolution(
            status="needs-clarification",
            selected_node_ids=[],
            summary="交通系統 9400000 是廣義分類；鐵路、道路、捷運、機場或港灣仍須確認。",
            question="請確認具體交通子類。",
        ),
    )
    package = SERVER.retrieve_evidence(
        query, "sk-proj-placeholder", max_depth=3, max_nodes=100
    )

    trace = package["retrieval_trace"]
    assert package["status"] == "needs-clarification"
    assert trace["selected_seed_ids"] == ["classification-hierarchy:doc01:9400000"]
    assert trace["v108_policy_validation"]["outcome"] == (
        "unique-explicit-official-hierarchy-code-anchor-added"
    )
    assert trace["v108_new_openai_request_for_validation"] is False


def test_inspection_runs_route_retrieval_grounded_answer_and_validation(monkeypatch) -> None:
    calls = []
    first = route_response("小學的圖式規則在哪一頁？", "9920103")

    def fake_call(payload, api_key):
        calls.append(payload)
        return first if len(calls) == 1 else answer_from_payload(payload)

    monkeypatch.setattr(SERVER, "call_openai", fake_call)
    monkeypatch.setattr(SERVER, "SESSIONS", SERVER.SessionStore())
    monkeypatch.setattr(SERVER, "_RETRIEVER", None)
    monkeypatch.setattr(
        SERVER,
        "retrieve_evidence",
        lambda query, api_key, **kwargs: canonical_evidence_without_model(
            query, **kwargs
        ),
    )
    result = SERVER.orchestrate(
        client_payload("小學的圖式規則在哪一頁？"), "sk-proj-placeholder", "gpt-5.6-terra"
    )

    assert len(calls) == 1
    assert result["grounding"]["schema"] == "nma.agentic-vs1/1.0"
    assert result["server_revision"] == "f03-school-hero-centered-edit-2026-08-12.4"
    assert result["grounding"]["answer"]["status"] == "answered"
    assert result["grounding"]["answer"]["answer"].startswith(
        "《01-一千分之一地形圖圖式規格表.pdf》第 61 頁"
    )
    assert result["grounding"]["answer"]["citation_ids"] == [
        "citation:section:doc01-portrayal:p61"
    ]
    assert any(
        citation.get("page") == 61
        for citation in result["grounding"]["evidence_package"]["citations"]
    )
    session, _ = SERVER.SESSIONS.acquire("session_vs1_test")
    assert session.previous_response_id == "resp_route"
    assert session.pending_call_id == "call_route"


def test_citation_metadata_is_rebound_to_canonical_section_containment() -> None:
    package = canonical_evidence_without_model(
        "小學 9920103 圖式規則", max_depth=3, max_nodes=30
    )
    citation = next(
        item
        for item in package["citations"]
        if item["citation_id"] == "citation:section:doc01-portrayal:p61"
    )
    citation.update(
        {
            "document_id": "document:doc02-1000-production",
            "filename": "02-一千分之一數值航測地形圖測製作業規定.pdf",
            "page": 65,
        }
    )

    normalized = SERVER.normalize_canonical_citation_metadata(package)
    repaired = next(
        item
        for item in normalized["citations"]
        if item["citation_id"] == "citation:section:doc01-portrayal:p61"
    )

    assert repaired["document_id"] == "document:doc01-portrayal"
    assert repaired["filename"] == "01-一千分之一地形圖圖式規格表.pdf"
    assert repaired["page"] == 61
    assert repaired["citation_integrity"] == "verified-unique-document-containment"


def test_unknown_feature_completes_with_visible_evidence_abstention(monkeypatch) -> None:
    calls = []
    first = route_response("不存在於官方語料的虛構星際傳送門圖徵", None)

    def fake_call(payload, api_key):
        calls.append(payload)
        return first if len(calls) == 1 else answer_from_payload(payload)

    monkeypatch.setattr(SERVER, "call_openai", fake_call)
    monkeypatch.setattr(SERVER, "SESSIONS", SERVER.SessionStore())
    monkeypatch.setattr(
        SERVER,
        "retrieve_evidence",
        lambda query, api_key, **kwargs: canonical_evidence_without_model(
            query, **kwargs
        ),
    )
    result = SERVER.orchestrate(
        client_payload("不存在於官方語料的虛構星際傳送門圖徵"),
        "sk-proj-placeholder",
        "gpt-5.6-terra",
    )

    grounding = result["grounding"]
    assert grounding["evidence_package"]["status"] == "abstained-no-match"
    assert grounding["evidence_package"]["citations"] == []
    assert grounding["answer"]["status"] == "abstained"
    assert grounding["answer"]["automatic_action"] is False

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from nma.ama_demo import AMADemoPresentation, build_evidence_action_trace
from nma.ama_live import AMALiveService, CANONICAL_INTENT
from nma.llm import LLMAdapter, LLMResult
from nma.llm.base import canonical_json
from nma.rq2_demo import proposal_hash


ROOT = Path(__file__).resolve().parents[1]


class ScriptedPlanner(LLMAdapter):
    def __init__(self, output: dict[str, Any]) -> None:
        self.output = deepcopy(output)

    def generate_structured(
        self,
        *,
        task: str,
        instructions: str,
        context: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> LLMResult:
        return LLMResult(
            model_id="qwen2.5:latest-test-double",
            provider="recorded-local-test",
            output=deepcopy(self.output),
            latency_ms=1,
            usage={"input_tokens": 1, "output_tokens": 1},
            raw_response_hash=hashlib.sha256(canonical_json(self.output)).hexdigest(),
        )


@pytest.fixture()
def service(tmp_path: Path) -> AMALiveService:
    draft = json.loads((ROOT / "artifacts/rq2/rq2-demo-01-constrained-result.json").read_text())[
        "raw_planner_draft"
    ]
    return AMALiveService(
        repository_root=ROOT,
        storage_root=tmp_path / "runtime",
        adapter_factory=lambda: ScriptedPlanner(draft),
    )


def live(service: AMALiveService) -> dict[str, Any]:
    record = service.new_record(CANONICAL_INTENT)
    return service.run(record["run_id"])


def presentation(service: AMALiveService) -> AMADemoPresentation:
    return AMADemoPresentation(ROOT, service.storage_root)


def test_live_mode_is_explicit(service: AMALiveService) -> None:
    assert service.new_record(CANONICAL_INTENT)["mode"] == "LIVE"
    assert "LIVE CLOUD RUN" in (ROOT / "public/ama-live/app.js").read_text()


def test_replay_mode_is_explicit(service: AMALiveService) -> None:
    replay = presentation(service).replay_record()
    assert replay["mode"] == "REPLAY"
    assert replay["replay_identity"].startswith("ama-demo-02-replay:")


def test_replay_never_claims_live(service: AMALiveService) -> None:
    replay = presentation(service).replay_record()
    assert replay["mode"] == "REPLAY"
    assert "no new inference or execution" in replay["replay_notice"]
    assert presentation(service).replay_manifest()["source_mode"] == "LIVE"


def test_same_rq1_question_across_three_architectures(service: AMALiveService) -> None:
    comparison = presentation(service).rq1_comparison()
    assert comparison["same_question"] is True
    assert len({row["question_identity"] for row in comparison["rows"]}) == 1


def test_rq1_comparison_records_model_identity(service: AMALiveService) -> None:
    rows = presentation(service).rq1_comparison()["rows"]
    assert {row["model_identity"]["digest"] for row in rows} == {"845dbda0ea48"}
    assert all(row["prompt_contract_hash"] for row in rows)
    assert all(row["temperature"] == 0 and row["context_window"] == 8192 for row in rows)


def test_graphrag_retrieval_trace_present(service: AMALiveService) -> None:
    row = presentation(service).rq1_comparison()["rows"][2]
    assert row["architecture"] == "graphrag"
    assert row["retrieved_item_count"] == 46
    assert row["projected_evidence_count"] == 9
    assert row["retrieval_context_summary"]["projected_evidence_ids"]


def test_graphrag_public_answer_uses_traditional_chinese_without_changing_frozen_source(
    service: AMALiveService,
) -> None:
    row = presentation(service).rq1_comparison()["rows"][2]
    frozen = json.loads((ROOT / "rq1-compare-01-results.json").read_text(encoding="utf-8"))
    frozen_answer = next(
        item["answer"]
        for item in frozen["raw_runs"]
        if item["architecture"] == "graphrag"
        and item["question_id"] == "canonical"
        and item["phase"] == "primary"
    )
    rendered = json.dumps(row, ensure_ascii=False)

    assert row["answer_presentation"]["display_language"] == "zh-Hant-TW"
    assert row["answer_presentation"]["mode"] == "PRESENTATION_TRANSLATION_FROM_FROZEN_RAW"
    assert row["answer_presentation"]["manual_research_answer_editing"] is False
    assert "分類代碼" in row["answer"] and "產品圖層欄位" in row["answer"]
    assert not any(
        term in rendered
        for term in ("分类", "规则", "图层", "字段", "颜色", "线型", "线号", "第11页")
    )
    assert "分类代码" in frozen_answer
    assert (
        row["answer_presentation"]["frozen_answer_sha256"]
        == hashlib.sha256(frozen_answer.encode("utf-8")).hexdigest()
    )


def test_domain_kg_view_present(service: AMALiveService) -> None:
    graph = presentation(service).domain_graph()
    assert graph["label"] == "DOMAIN KNOWLEDGE GRAPH"
    assert graph["nodes"] and graph["edges"]


def test_graph_relations_are_visible_and_directed() -> None:
    html = (ROOT / "public/ama-live/index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "public/ama-live/app.js").read_text(encoding="utf-8")
    css = (ROOT / "public/ama-live/app.css").read_text(encoding="utf-8")

    assert all(f'id="{name}-relations"' in html for name in ("domain", "retrieved", "action"))
    assert "renderRelationLegend" in javascript
    assert 'marker-end="url(#' in javascript
    assert "DIRECTED RELATIONS" in javascript
    assert ".graph .relation-edge line" in css
    assert ".graph .edge-label" in css


def test_retrieved_subgraph_view_present(service: AMALiveService) -> None:
    record = live(service)
    graph = presentation(service).views_for(record, mode="LIVE")["retrieved_subgraph"]
    assert graph["label"] == "RETRIEVED SUBGRAPH FOR THIS QUERY"
    assert graph["run_id"] == record["run_id"]
    assert any(item["display_state"] == "PROJECTED_EVIDENCE" for item in graph["nodes"])


def test_evidence_action_trace_present(service: AMALiveService) -> None:
    record = live(service)
    trace = build_evidence_action_trace(record, mode="LIVE")
    assert trace["label"] == "KNOWLEDGE → CONSTRAINT → ACTION TRACE"
    assert trace["identity_invariant"]["status"] == "PASS"
    assert {"Proposal", "Authorization", "GISOperation", "Verification", "Provenance"} <= {
        item["type"] for item in trace["nodes"]
    }


def test_unresolved_constraints_preserved(service: AMALiveService) -> None:
    record = live(service)
    unresolved = [item for item in record["constraints"] if item["status"] == "BOUNDED_UNRESOLVED"]
    assert len(unresolved) == 4
    assert any(
        item["constraint_id"] == "constraint:relationship.product_layer" for item in unresolved
    )
    assert all(item["resolved_value"] is None for item in unresolved)


def test_displayed_proposal_matches_canonical(service: AMALiveService) -> None:
    record = live(service)
    ui = (ROOT / "public/ama-live/app.js").read_text()
    assert record["proposal"]["proposal_hash"] == proposal_hash(record["proposal"])
    assert "JSON.stringify(proposal,null,2)" in ui
    assert "proposal.proposal_hash" in ui


def test_authorized_hash_matches_executed_hash(service: AMALiveService) -> None:
    record = live(service)
    assert (
        record["proposal"]["proposal_hash"]
        == record["authorization"]["proposal_hash"]
        == record["provenance"]["executed_proposal_hash"]
    )


def test_tampered_proposal_denied(service: AMALiveService) -> None:
    record = live(service)
    tamper = service.tamper_test(record["run_id"])
    assert tamper["authorization"] == "DENIED"
    assert tamper["execution_attempted"] is tamper["mutation_started"] is False


def test_verification_result_present(service: AMALiveService) -> None:
    verification = live(service)["verification"]
    assert verification["status"] == "PASS"
    assert all({"expected", "observed", "status"} <= set(item) for item in verification["checks"])


def test_provenance_complete(service: AMALiveService) -> None:
    provenance = live(service)["provenance"]
    required = {
        "proposal_id",
        "proposal_hash",
        "authorization_id",
        "execution_id",
        "verification_id",
        "receipt_id",
        "evidence_ids",
        "timestamp",
        "run_id",
    }
    assert required <= set(provenance)


def test_reset_removes_stale_run_state(service: AMALiveService) -> None:
    record = live(service)
    result = presentation(service).reset()
    service.forget_records(result["removed_run_ids"])
    assert record["run_id"] in result["removed_run_ids"]
    with pytest.raises(KeyError):
        service.get(record["run_id"])


def test_sequential_live_runs_generate_fresh_identity(service: AMALiveService) -> None:
    first, second = live(service), live(service)
    assert first["run_id"] != second["run_id"]
    assert first["proposal"]["proposal_hash"] != second["proposal"]["proposal_hash"]
    assert first["authorization"]["authorization_id"] != second["authorization"]["authorization_id"]


def test_cloud_failure_can_fallback_to_replay(service: AMALiveService) -> None:
    ui = (ROOT / "public/ama-live/app.js").read_text()
    assert "showFailure" in ui and "'/ama/demo/replay'" in ui
    assert presentation(service).replay_record()["status"] == "PASS"


def test_fallback_is_visibly_marked_replay() -> None:
    html = (ROOT / "public/ama-live/index.html").read_text()
    javascript = (ROOT / "public/ama-live/app.js").read_text()
    assert "Live execution unavailable." in html
    assert "VERIFIED REPLAY" in javascript
    assert "No replay has been selected." in javascript


def test_browser_flow_reaches_final_map(service: AMALiveService) -> None:
    html = (ROOT / "public/ama-live/index.html").read_text()
    result = presentation(service).replay_result()
    assert all(value in html for value in ('id="map"', 'id="verification"', 'id="provenance"'))
    assert (
        result["features"][0]["properties"]["proposal_hash"]
        == (presentation(service).replay_record()["proposal"]["proposal_hash"])
    )


def test_map_renders_a_visible_but_non_authoritative_hydrant_preview(
    service: AMALiveService,
) -> None:
    html = (ROOT / "public/ama-live/index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "public/ama-live/app.js").read_text(encoding="utf-8")
    css = (ROOT / "public/ama-live/app.css").read_text(encoding="utf-8")
    feature = presentation(service).replay_result()["features"][0]

    assert feature["properties"]["authoritative_render"] is False
    assert 'id="map-symbol-notice"' in html
    assert "symbolic hydrant preview" in html
    assert "hydrantPreviewMarker" in javascript
    assert "new maplibregl.Marker" in javascript
    assert "NON-AUTHORITATIVE SYMBOLIC PREVIEW" in javascript
    assert ".hydrant-preview-marker" in css


def test_replay_manifest_hashes_every_included_artifact(service: AMALiveService) -> None:
    demo = presentation(service)
    manifest = demo.replay_manifest()
    for name, identity in manifest["artifacts"].items():
        path = demo.replay_root / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == identity["sha256"]


def test_cloud_image_includes_canonical_replay_package() -> None:
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert "!artifacts/ama-demo/replay/canonical-run/**" in dockerignore
    assert (ROOT / "artifacts/ama-demo/replay/canonical-run/manifest.json").is_file()


def test_live_identity_content_cannot_expand_main_grid() -> None:
    css = (ROOT / "public/ama-live/app.css").read_text(encoding="utf-8")
    assert "main>*{width:100%;min-width:0}" in css
    assert ".identity-chain code{overflow-wrap:anywhere}" in css


def test_cloud_acceptance_runner_uses_demo02_frontend_markers() -> None:
    runner = (ROOT / "scripts/run_ama_cloud_acceptance.py").read_text(encoding="utf-8")
    assert 'marker in root_html for marker in ("AMA-DEMO-02", \'id="mode-run"\')' in runner


def test_research_semantic_files_unchanged_from_predecessor() -> None:
    protected = [
        "src/nma/graphrag.py",
        "src/nma/research_answer_validation.py",
        "src/nma/rq2_demo.py",
        "src/nma/rq3_demo.py",
        "src/nma/school_hero_execution.py",
        "src/nma/road_execution.py",
        "data/knowledge/nma-canonical-graph-v0.4.json",
    ]
    import subprocess

    changed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "0ebe7193951a8d4f5c5c6d10f3e5de4c71698284",
            "--",
            *protected,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert changed == ""

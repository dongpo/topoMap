from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

from nma.api import get_payload, post_payload
from nma.extraction import extract_code_anchored_candidates
from nma.knowledge import PortrayalGraph, compile_portrayal_graph
from nma.portrayal import PortrayalAgent, compile_maplibre_layers
from nma.portrayal_bench import run_portrayal_benchmark
from nma.specification import Specification


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data/knowledge/portrayal-graph.json"


def test_pdf_candidate_extraction_preserves_page_and_requires_review() -> None:
    text = "header\n消防栓 9350906 地形測繪 1 2 7 實測\nfooter\f養殖池 9740100"
    records = extract_code_anchored_candidates(text, context_lines=0)
    assert records == [
        {
            "feature_code": "9350906",
            "page": 1,
            "context": "消防栓 9350906 地形測繪 1 2 7 實測",
            "review_status": "candidate-not-executable",
        },
        {
            "feature_code": "9740100",
            "page": 2,
            "context": "養殖池 9740100",
            "review_status": "candidate-not-executable",
        },
    ]


def test_checked_in_graph_is_reproducibly_compiled_from_review_records() -> None:
    compiled = compile_portrayal_graph(
        ROOT / "data/extraction/portrayal-records.jsonl",
        ROOT / "data/knowledge/portrayal-profile.json",
    )
    checked_in = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    assert compiled == checked_in
    assert compiled["statistics"] == {"nodes": 44, "edges": 85, "observations": 10}
    conflict = next(node for node in compiled["nodes"] if node["type"] == "ProfileConflict")
    assert conflict["properties"]["authoritative_profile"]["9920103"] == "小學"


def test_graphrag_answers_human_question_and_returns_governance_path() -> None:
    answer = PortrayalAgent(PortrayalGraph.load(GRAPH_PATH)).answer(
        "依 NLSC112V5.4，小學的代碼是什麼？"
    )
    assert answer["feature_codes"] == ["9920103"]
    assert answer["evidence"][0]["page"] == 61
    assert [edge["type"] for edge in answer["graph_paths"][0]["edges"]] == [
        "PORTRAYED_BY",
        "USES_SYMBOL",
        "SUPPORTED_BY",
        "EVIDENCED_ON",
    ]


def test_five_scene_golden_queries_return_grounded_graph_evidence() -> None:
    agent = PortrayalAgent(PortrayalGraph.load(GRAPH_PATH))
    cases = [
        ("消防栓的地形代碼是什麼？", ["9350906"], [11]),
        ("養殖池的圖式規則在 PDF 哪一頁？", ["9740100"], [50]),
        ("警察局、分駐所、派出所的代碼是什麼？", ["9910603"], [60]),
        ("依 NLSC112V5.4，小學的代碼是什麼？", ["9920103"], [61]),
        ("大型獨幢郵局有什麼圖式例外？", ["9950201"], [69]),
    ]
    required_edges = {"PORTRAYED_BY", "USES_SYMBOL", "SUPPORTED_BY", "EVIDENCED_ON"}

    for question, codes, pages in cases:
        answer = agent.answer(question)
        assert answer["status"] == "answered"
        assert answer["feature_codes"] == codes
        assert [evidence["page"] for evidence in answer["evidence"]] == pages
        for evidence in answer["evidence"]:
            assert evidence["uri"]
            assert evidence["source_sha256"]
            assert evidence["review_status"] == "human-review-required"
        for path in answer["graph_paths"]:
            assert all(
                node.startswith(("feature:", "rule:", "symbol:", "observation:", "section:"))
                for node in path["nodes"]
            )
            assert required_edges <= {edge["type"] for edge in path["edges"]}


def test_graphrag_abstains_without_evidence_when_no_feature_matches() -> None:
    answer = PortrayalAgent(PortrayalGraph.load(GRAPH_PATH)).answer("火車站應使用哪一個符號？")
    assert answer == {
        "status": "abstain",
        "answer": "The loaded portrayal knowledge does not contain a matching feature.",
        "feature_codes": [],
        "evidence": [],
        "graph_paths": [],
    }


def test_agent_applies_post_office_exception_and_abstains_on_wrong_scale() -> None:
    agent = PortrayalAgent(PortrayalGraph.load(GRAPH_PATH))
    exception = agent.select_symbol("9950201", attributes={"large_detached_building": True})
    assert exception.symbol["selected_action"] == "text_only"
    assert exception.evidence["page"] == 69
    assert agent.select_symbol("9950201", scale_denominator=5000).status == "abstain"


def test_five_scene_rules_expose_explicit_outputs_and_evidence() -> None:
    agent = PortrayalAgent(PortrayalGraph.load(GRAPH_PATH))
    expected = {
        "9350906": ("消防栓", "fire-hydrant", "symbol", 11),
        "9740100": ("養殖池", "fish-pond", "fill", 50),
        "9910603": ("警察局、分駐所、派出所", "police", "symbol", 60),
        "9920103": ("小學", "school", "symbol", 61),
        "9950201": ("郵局", "post", "symbol", 69),
    }

    for code, (name, symbol_id, maplibre_type, page) in expected.items():
        decision = agent.select_symbol(code)
        assert decision.status == "selected"
        assert decision.feature_code == code
        assert decision.feature_name == name
        assert decision.symbol["symbol_id"] == symbol_id
        assert decision.symbol["maplibre_type"] == maplibre_type
        assert decision.symbol["selected_action"] == "draw_symbol"
        assert decision.rule["scale_denominator"] == 1000
        assert decision.rule["source_layers"]
        assert decision.evidence["page"] == page
        assert decision.evidence["source_sha256"]
        assert decision.evidence["review_status"] == "human-review-required"
        assert decision.graph_path["nodes"]
        assert decision.graph_path["edges"]
        assert decision.reason


def test_unsupported_portrayal_contexts_fail_explicitly_without_partial_outputs() -> None:
    agent = PortrayalAgent(PortrayalGraph.load(GRAPH_PATH))
    cases = [
        (
            agent.select_symbol("9950201", profile_id="unknown-profile"),
            "abstain",
            "not loaded",
        ),
        (agent.select_symbol("9950201", scale_denominator=5000), "abstain", "No reviewed"),
        (agent.select_symbol("9999999"), "not_found", "No feature"),
    ]

    for decision, status, reason_fragment in cases:
        assert decision.status == status
        assert decision.symbol is None
        assert decision.rule is None
        assert decision.evidence is None
        assert decision.graph_path is None
        assert reason_fragment in decision.reason


def test_maplibre_layers_carry_rule_and_pdf_evidence() -> None:
    layers = compile_maplibre_layers(PortrayalGraph.load(GRAPH_PATH))
    pond = next(
        layer
        for layer in layers
        if layer["source-layer"] == "J01_WATERA"
        and layer["metadata"].get("nma:featureCode") == "9740100"
        and layer["metadata"].get("nma:role") == "portrayal-icon"
    )
    assert pond["layout"]["icon-image"] == "waterFishIcon"
    assert pond["metadata"]["nma:evidence"]["page"] == 50
    assert pond["metadata"]["nma:ruleId"].endswith(":9740100")


def test_official_symbol_assets_are_source_hashed_and_valid_svg() -> None:
    directory = ROOT / "assets/symbols/nlsc112v5.4"
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_sha256"] == (
        "1f9c4457d7ced86f2b7681e21be9ad3b7b7ae364981ab995ef27b468e0fa2620"
    )
    assert manifest["symbols"]["9910603"]["shape"] == "circle crossed by two diagonals"
    assert manifest["symbols"]["9350906"]["shape"] == "boxed Chinese character 火"
    for svg in sorted(directory.glob("*.svg")):
        assert ET.parse(svg).getroot().tag.endswith("svg")


def test_human_question_portrayal_benchmark_is_answer_key_isolated() -> None:
    tasks = (ROOT / "benchmark/portrayal/tasks.jsonl").read_text(encoding="utf-8")
    assert '"expected"' not in tasks
    report = run_portrayal_benchmark(ROOT)
    assert report["task_count"] == 21
    assert report["systems"]["full_nma"]["accuracy"] == 1.0
    assert report["systems"]["full_nma"]["evidence_accuracy"] == 1.0
    assert report["systems"]["full_nma"]["graph_grounding"] == 1.0
    assert report["systems"]["pdf_search"]["by_task_type"]["symbol_decision"] == 0.0


def test_portrayal_agent_api_endpoints() -> None:
    specification = Specification.load(ROOT / "data/specifications/taiwan-5000-riverl-112.json")
    graph = PortrayalGraph.load(GRAPH_PATH)
    status, answer = post_payload(
        specification, "/v1/agent/ask", {"question": "消防栓的代碼？"}, graph
    )
    assert status == 200
    assert answer["feature_codes"] == ["9350906"]
    status, layers = get_payload(specification, "/v1/maplibre/portrayal-layers", graph)
    assert status == 200
    assert len(layers["layers"]) == 133

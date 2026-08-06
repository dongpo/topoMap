import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "nmaAgentDemo.html"
GRAPH = ROOT / "data/knowledge/portrayal-graph.json"
WORKER = ROOT / "nmaDemoWorker.js"


def test_a02_renders_canonical_interactive_evidence_path() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "function buildEvidencePath(decision)" in html
    assert '["CONTAINS","YIELDS","DESCRIBES","PORTRAYED_BY","USES_SYMBOL"]' in html
    assert "function renderGraphNodeDetails(nodeId)" in html
    assert 'data-graph-node="${node.id}"' in html
    assert 'aria-label="Selected authoritative evidence path"' in html
    assert "6-node selected evidence path" not in html  # count is generated from the path
    assert "${path.length}-node selected evidence path" in html


def test_a02_exposes_source_review_and_profile_conflict_details() -> None:
    html = HTML.read_text(encoding="utf-8")
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))

    assert "Source text" in html
    assert "Review status" in html
    assert "Extraction" in html
    assert "Implementation status" in html
    assert "Profile conflict requires review." in html
    assert "authoritative_label" in html
    assert "observed_label" in html

    conflict = next(node for node in graph["nodes"] if node["type"] == "ProfileConflict")
    assert conflict["properties"]["authoritative_profile"]["9920103"] == "小學"
    assert conflict["properties"]["observed_implementation"]["9920103"] == "高中"


def test_a02_keeps_non_authoritative_and_abstained_paths_empty() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "0 authoritative nodes" in html
    assert "empty evidence path" in html
    assert "evidence not compiled" in html
    assert "not authoritative" in html
    assert "No graph evidence was used. The Agent stopped before selecting a portrayal rule." in html


def test_a02_updates_local_shell_without_losing_offline_fallback() -> None:
    worker = WORKER.read_text(encoding="utf-8")

    assert 'const CACHE_NAME = "nma-agentic-v0.3-a' in worker
    assert '"./data/demo/pmtiles-capability-catalog.json"' in worker
    assert '"./assets/symbols/nlsc112v5.4/school.svg"' in worker
    assert "const response = await fetch(event.request)" in worker
    assert 'cache.match(event.request, {ignoreSearch: true})' in worker

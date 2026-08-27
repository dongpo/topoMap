import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/demo/pmtiles-capability-catalog.json"


def test_pmtiles_capability_catalog_is_reproducible(tmp_path: Path) -> None:
    generated = tmp_path / "catalog.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/build_pmtiles_capability_catalog.py",
            "--output",
            str(generated),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(generated.read_text(encoding="utf-8")) == json.loads(
        CATALOG.read_text(encoding="utf-8")
    )


def test_catalog_covers_all_pmtiles_entries_and_governance_states() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    items = catalog["capabilities"]

    assert catalog["schema"] == "nma.pmtiles-capability-catalog/1.0"
    assert catalog["count"] == 42
    assert len({item["code"] for item in items}) == 42
    assert catalog["status_counts"] == {
        "implementation-only": 28,
        "evidence-backed": 5,
        "conflicted": 4,
        "style-variant": 5,
    }
    school = next(item for item in items if item["code"] == "9920103")
    assert school["label"] == "高中"
    assert school["authoritative_name"] == "小學"
    assert school["status"] == "conflicted"
    assert school["evidence_available"] is True
    parking_variant = next(item for item in items if item["code"] == "9960204b")
    assert parking_variant["status"] == "style-variant"
    assert parking_variant["base_code"] == "9960204"


def test_agentic_demo_shell_loads_catalog_graph_and_symbol_results() -> None:
    html = (ROOT / "nmaAgentDemo.html").read_text(encoding="utf-8")

    assert "data/demo/pmtiles-capability-catalog.json" in html
    assert 'id="capability-search"' in html
    assert 'id="symbol-workshop"' in html
    assert 'id="knowledge-graph"' in html
    assert "function renderCapabilityCatalog" in html
    assert "function renderSymbolWorkshop" in html
    assert "function renderKnowledgeGraph" in html

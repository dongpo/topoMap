import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_agentic_v03_pages import check_agentic_v03_pages  # noqa: E402


MANIFEST = ROOT / "data/demo/agentic-v0.3-pages.json"


def test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate() -> None:
    result = check_agentic_v03_pages(MANIFEST)

    assert result["status"] == "candidate-passed-not-deployed"
    assert result["stable_root_release"] == "nma-public-assets-v0.2-rc1"
    assert result["candidate_path"] == "agentic-v0.3"
    assert result["stable_file_count"] == 9
    assert result["candidate_file_count"] == 12
    assert result["dataset"] == {
        "feature_count": 12,
        "source_crs": "EPSG:3826",
        "output_crs": "EPSG:4326",
        "component_count": 5,
    }
    assert result["pmtiles_included"] is False
    assert result["deployment_state"] == "not-deployed"
    assert result["owner_approval_required"] is True
    assert result["blocking_defect_count"] == 0


def test_agentic_v03_pages_manifest_keeps_publication_boundaries_explicit() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["release_version"] == "nma-agentic-v0.3-pages-rc1"
    assert manifest["website"] == {
        "stable_root_release": "nma-public-assets-v0.2-rc1",
        "stable_root_snapshot": "60eb2857b1ff14b0baa51732373ca5c8b697c1c3",
        "candidate_path": "agentic-v0.3",
        "planned_url": "https://dongpo.github.io/topoMap/agentic-v0.3/",
        "deployment_state": "not-deployed",
    }
    assert "out1120902.pmtiles" in manifest["exclusions"]
    assert "nmaDemoWorker.js" in manifest["exclusions"]
    assert manifest["approval"]["public_deployment"] == (
        "separate explicit owner approval required"
    )
    assert manifest["approval"]["pull_request_merge"] == "not authorized"
    assert manifest["blocking_defects"] == []

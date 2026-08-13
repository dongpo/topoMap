from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_nma_agentic_v032_demo.py"
SOURCE = ROOT / "nmaAgentDemoV031.html"
TARGET = ROOT / "nmaAgentDemoV032.html"
WORKER_SOURCE = ROOT / "nmaDemoWorkerV031.js"
WORKER_TARGET = ROOT / "nmaDemoWorkerV032.js"


def load_builder():
    spec = importlib.util.spec_from_file_location("nma_v032_builder", BUILDER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v032_is_reproducible_and_preserves_v031() -> None:
    builder = load_builder()
    source = SOURCE.read_text(encoding="utf-8")
    target = TARGET.read_text(encoding="utf-8")

    assert target == builder.build(source)
    assert "Agentic Demo v0.31" in source
    assert "Agentic Demo v0.32" in target
    assert WORKER_TARGET.read_text(encoding="utf-8") == builder.build_worker(
        WORKER_SOURCE.read_text(encoding="utf-8")
    )


def test_v032_school_hero_uses_server_proposals_and_two_approval_gates() -> None:
    html = TARGET.read_text(encoding="utf-8")

    assert 'PORTRAYAL_API="/api/portrayal-review"' in html
    assert 'PORTRAYAL_DECISION_API="/api/portrayal-review/decision"' in html
    assert 'PORTRAYAL_PREVIEW_API="/api/portrayal-review/preview"' in html
    assert 'REAL_LAYER_API="/api/real-layer"' in html
    assert 'REAL_LAYER_EXECUTE_API="/api/real-layer/execute"' in html
    assert "proposal-pending-approval" in html
    assert "approved-preview-observed" in html
    assert "real-layer-proposal-pending" in html
    assert "verified-real-layer-on-map" in html
    assert 'decision:"approve"' in html
    assert "symbol_edit_plan:symbolEditPlan" in html
    assert "args.style_plan" in html


def test_v032_requires_verified_real_output_before_map_mutation() -> None:
    html = TARGET.read_text(encoding="utf-8")

    assert 'result.qa?.status!=="passed"' in html
    assert 'result.observation?.provenance?.random_coordinates!==false' in html
    assert "result.output_url" in html
    assert "collection.features?.length!==15" in html
    assert 'source:"nma-v032-school-real"' in html
    assert '"text-field":["get","MARKNAME1"]' in html
    assert "flagpole_attachment" in html
    assert "proportional-width" in html
    assert '<rect x="${supportX}"' in html


def test_v032_shows_complete_ordered_agent_spine_and_authority_boundary() -> None:
    html = TARGET.read_text(encoding="utf-8")

    assert 'HERO_STAGE_ORDER=["resolve","retrieve","explain","propose","validate","approve","execute","observe","qa","cite"]' in html
    assert "V0 remains immutable" in html
    assert "Document 01" in html
    assert "No random geometry" in html
    assert "Output SHA-256" in html
    assert "reviewed citation(s) remain bound" in html


def test_v032_shows_only_used_citations_and_never_leaves_ask_disabled_on_tool_failure() -> None:
    html = TARGET.read_text(encoding="utf-8")

    assert "filter(citation=>usedCitationIds.has(citation.citation_id))" in html
    assert "<h3>Cited source</h3>" in html
    assert 'button.textContent="Working…"' in html
    assert "finally{button.disabled=false;button.textContent=originalLabel" in html
    assert "No unverified answer, symbol, or map mutation was accepted." in html
    assert 'REQUIRED_F03_SERVER_REVISION="f03-school-hero-centered-edit-2026-08-12.4"' in html
    assert 'runtime.schema!=="nma.runtime-baseline/0.32"' in html
    assert "incompatible F03 agent server revision" in html
    assert 'SCHOOL_HERO_EVIDENCE_API="/api/hero/school/evidence"' in html
    assert "requestSchoolHeroEvidence()" in html
    assert 'localPlan.intent==="propose_style_revision"' in html
    assert 'action:"center",target:"flagpole-bottom"' in html
    assert 'poleX=support&&state.flagpole_horizontal_alignment==="centered"?supportX+supportWidth/2:14' in html
    assert 'reference:"support",relations:new Set(["centered"])' in html

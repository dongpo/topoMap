import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "nmaAgentDemo.html"


def test_a03_keeps_v0_immutable_and_renders_side_by_side_previews() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "function baselineStyleFor(decision)" in html
    assert "Object.freeze" in html
    assert 'class="symbol-compare"' in html
    assert "Specification baseline" in html
    assert "Derived preview" in html
    assert "V0 · immutable" in html
    assert "authoritative V0 is never overwritten" in html


def test_a03_supports_bounded_natural_language_style_patches() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "function parseStylePatch(text,supported)" in html
    assert "function symbolEditPlanFromText(text,supported)" in html
    assert "function compileSymbolEditPlan(plan,supported)" in html
    assert 'typeof op.value==="number"?Math.round' in html
    assert 'setBounded("scale"' in html
    assert 'setBounded("stroke_width"' in html
    assert 'setBounded("opacity"' in html
    assert 'setBounded("rotation"' in html
    assert 'setValue("outline","none","Outline")' in html
    assert "STYLE_COLORS" in html
    assert 'id="style-request"' in html
    assert 'id="preview-revision"' in html
    assert ">Edit symbol</button>" in html
    assert ">Preview change</button>" not in html


def test_a05_supports_bounded_school_geometry_edits() -> None:
    html = HTML.read_text(encoding="utf-8")
    catalog = json.loads(
        (ROOT / "data/demo/pmtiles-capability-catalog.json").read_text(encoding="utf-8")
    )
    school = next(item for item in catalog["capabilities"] if item["code"] == "9920103")

    assert {
        "flag_top_alignment",
        "support_shape",
        "support_proportion",
        "flag_attachment",
    }.issubset(school["editable_parameters"])
    assert 'setValue("flag_top_alignment","aligned","Flag top alignment")' in html
    assert 'setValue("support_shape","rectangle","Support shape")' in html
    assert 'setValue("support_proportion","match_flag","Support proportion")' in html
    assert 'setValue("flag_attachment","inserted","Flag attachment")' in html
    assert 'action:value==="rectangle"?"add_shape":"remove_shape"' in html
    assert 'action:"match_dimension"' in html
    assert 'target:"flagpole-bottom"' in html
    assert 'reference:"support-top"' in html
    assert '"inserted-into-top"' in html
    assert '"proportional-width"' in html
    assert "三角(?:形)?(?:上方)?頂部" in html
    assert 'style.flag_top_alignment==="aligned"' in html
    assert 'flag_top_alignment:"offset"' in html
    assert 'support_shape:"none"' in html
    assert "function schoolSymbolGeometry(style)" in html
    assert "function schoolSymbolSvg(style" in html
    assert "proportional=style.support_proportion" in html
    assert "y:36,width:proportional?30:sameWidth?22:24,height:17" in html
    assert 'fill="${style.color}" stroke="${outline}"' in html
    assert 'fill-opacity=".18"' not in html
    assert "g.globalAlpha=style.opacity*.18" not in html
    assert "g.fillRect(shape.rectangle.x" in html
    assert "Flag top alignment" in html


def test_a07_places_layer_creation_between_symbol_and_knowledge_graph() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert html.index('id="symbol-workshop"') < html.index('id="layer-workshop"')
    assert html.index('id="layer-workshop"') < html.index('id="knowledge-graph"')


def test_a07_exposes_bounded_portable_graph_query() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "function queryPortableGraph(rawQuery)" in html
    assert 'id="graph-query"' in html
    assert 'id="run-graph-query"' in html
    assert "Neo4j adapter is not connected" in html


def test_a03_versions_diffs_and_requires_explicit_approval() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "function revisionDiffTable(revision)" in html
    assert "function revisionHistory(state)" in html
    assert "function proposeStyleRevision(planOverride=null)" in html
    assert "function stylePlanAudit(plan)" in html
    assert "Agent interpretation · SymbolEditPlan" in html
    assert "function approveStyleRevision()" in html
    assert "function discardStyleRevision()" in html
    assert "function approvedStyleFor(featureCode)" in html
    assert 'status:"pending"' in html
    assert 'status="approved"' in html
    assert 'status="discarded"' in html
    assert "only explicit approval advances the selected symbol" in html


def test_a05_keeps_the_next_supervised_action_in_the_symbol_panel() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "function finishSymbolEditingFromPanel()" in html
    assert 'id="finish-symbol-editing"' in html
    assert "Finish Symbol editing &amp; prepare layer" in html
    assert "You do not need to return to the conversation." in html
    assert 'appendAgentMessage("user","完成 Symbol 編輯，準備圖層")' in html
    assert "Panel action · finish_revisions" in html
    assert 'document.querySelector("#layer-workshop")?.scrollIntoView' in html

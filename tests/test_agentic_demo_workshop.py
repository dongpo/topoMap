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
    assert "the authoritative V0 asset is never overwritten" in html


def test_a03_supports_bounded_natural_language_style_patches() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "function parseStylePatch(text,supported)" in html
    assert 'setBounded("scale"' in html
    assert 'setBounded("stroke_width"' in html
    assert 'setBounded("opacity"' in html
    assert 'setBounded("rotation"' in html
    assert 'patch.outline="none"' in html
    assert "STYLE_COLORS" in html
    assert 'id="style-request"' in html
    assert 'id="preview-revision"' in html


def test_a03_versions_diffs_and_requires_explicit_approval() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "function revisionDiffTable(revision)" in html
    assert "function revisionHistory(state)" in html
    assert "function proposeStyleRevision()" in html
    assert "function approveStyleRevision()" in html
    assert "function discardStyleRevision()" in html
    assert "function approvedStyleFor(featureCode)" in html
    assert 'status:"pending"' in html
    assert 'status="approved"' in html
    assert 'status="discarded"' in html
    assert "Only explicit approval advances the selected style" in html

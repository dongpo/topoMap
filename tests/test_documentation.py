import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class _LandingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[tuple[str, str | None]] = []
        self.image_sources: list[str] = []
        self.has_viewport = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.hrefs.append((values["href"] or "", values.get("data-public-link")))
        if tag == "img" and values.get("src"):
            self.image_sources.append(values["src"] or "")
        if tag == "meta" and values.get("name") == "viewport":
            self.has_viewport = True


def test_local_markdown_links_resolve() -> None:
    markdown_files = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    missing: list[str] = []
    for source in markdown_files:
        text = source.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]*\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0]
            if path and not (source.parent / path).resolve().exists():
                missing.append(f"{source.relative_to(ROOT)} -> {target}")
    assert not missing, "Missing local documentation links:\n" + "\n".join(missing)


def test_d19_readme_exposes_reproducible_public_entry_point() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in (
        "## Five scenes, five agent capabilities",
        "## Quickstart",
        "## Public entry points",
        "## Known limitations",
    ):
        assert heading in text
    for command in ("git switch codex/nma-v0.2-authoritative", "make demo-reset", "make demo-rc1"):
        assert command in text
    assert "Public RC1" in text
    assert "evidence-only mode" in text


def test_d19_landing_links_and_assets_resolve() -> None:
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = _LandingParser()
    parser.feed(source)

    missing: list[str] = []
    for target, _role in parser.hrefs:
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path = target.split("#", 1)[0]
        if path and not (ROOT / path).resolve().exists():
            missing.append(target)
    for target in parser.image_sources:
        if not (ROOT / target).resolve().exists():
            missing.append(target)
    assert not missing, "Missing local landing-page links/assets:\n" + "\n".join(missing)

    public_roles = {role for _href, role in parser.hrefs if role}
    assert public_roles == {"demo", "repository", "documentation", "publication"}
    assert parser.has_viewport
    assert "@media(max-width:780px)" in source


def test_d19_landing_claims_match_frozen_five_scene_contract() -> None:
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    expected = {
        "9920103": "PDF 61",
        "9350906": "PDF 11",
        "9910603": "PDF 60",
        "9740100": "PDF 50",
        "9950201": "PDF 69",
    }
    for code, page_label in expected.items():
        assert code in source
        assert page_label in source
    assert "20/20; 0 defects" in source
    assert "10/10; 0 console errors" in source
    assert "Repository readiness is not deployment completion" in source

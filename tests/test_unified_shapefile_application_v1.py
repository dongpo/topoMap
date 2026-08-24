from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "nmaApplicationV1.html"
APP = ROOT / "nmaApplicationV1.js"
DOMAIN_PAGES = {
    "school": ROOT / "nmaSchoolDemoV1.html",
    "road": ROOT / "nmaRoadDemoV1.html",
    "build": ROOT / "nmaBuildDemoV1.html",
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.hrefs.append(values["href"] or "")
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"] or "")
        if tag == "link" and values.get("rel") == "stylesheet" and values.get("href"):
            self.stylesheets.append(values["href"] or "")


def test_landing_routes_each_geometry_to_a_separate_user_shapefile_workflow() -> None:
    source = LANDING.read_text(encoding="utf-8")
    for page in ("nmaSchoolDemoV1.html", "nmaRoadDemoV1.html", "nmaBuildDemoV1.html"):
        assert source.count(f'href="{page}"') == 1
    for value in ("POINT · MARK", "LINE · ROAD", "POLYGON / POLYGONZ · BUILD"):
        assert value in source
    assert "type=\"file\"" not in source
    assert "iframe" not in source.lower()
    assert "RQ1" not in source and "research workbench" not in source.lower()


def test_landing_states_the_governed_agent_loop_and_application_boundaries() -> None:
    source = LANDING.read_text(encoding="utf-8")
    for label in ("資料檢查", "查找規範證據", "人工授權", "MapLibre 繪圖", "觀察與決策"):
        assert label in source
    for decision in ("replan", "abstain", "request human", "stop"):
        assert decision in source
    for boundary in ("Fail closed", "Read-only knowledge", "No data export", "production activation"):
        assert boundary in source
    assert "Shapefile 與逐點 geometry 留在瀏覽器" in source


def test_runtime_capability_check_is_path_prefix_safe_and_requires_all_domains() -> None:
    source = APP.read_text(encoding="utf-8")
    assert 'new URL(document.querySelector' in source
    assert 'new URL("nma/runtime", apiRoot)' in source
    assert 'const expected = ["school", "road", "build"]' in source
    assert 'nma.unified-runtime-capabilities/1.0' in source
    assert "未連線本機 Runtime · 操作頁會明確停止" in source


def test_domain_pages_return_to_landing_and_keep_only_one_current_domain() -> None:
    expected = {
        "school": "目前：School",
        "road": "目前：ROAD",
        "build": "目前：BUILD",
    }
    for domain, path in DOMAIN_PAGES.items():
        source = path.read_text(encoding="utf-8")
        assert source.count('href="nmaApplicationV1.html"') == 2
        assert source.count("目前：") == 1
        assert expected[domain] in source
        assert 'assets/css/nma-domain-navigation-v1.css' in source
        assert 'aria-label="資料工作"' in source


def test_every_landing_local_link_and_asset_exists() -> None:
    parser = LinkParser()
    parser.feed(LANDING.read_text(encoding="utf-8"))
    local_targets = [*parser.hrefs, *parser.scripts, *parser.stylesheets]
    assert local_targets
    for target in local_targets:
        if target.startswith("#"):
            assert f'id="{target[1:]}"' in LANDING.read_text(encoding="utf-8")
            continue
        assert not target.startswith("/")
        assert (ROOT / target).is_file(), target

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public/gh-pages"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.local: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for name in ("href", "src"):
            value = values.get(name)
            if value and not value.startswith(("https://", "mailto:", "#")):
                self.local.append(value)


class StaticPagesDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = (OUTPUT / "index.html").read_text(encoding="utf-8")
        cls.run_page = (OUTPUT / "run.html").read_text(encoding="utf-8")
        cls.app = (OUTPUT / "app.js").read_text(encoding="utf-8")
        cls.landing = (OUTPUT / "landing.js").read_text(encoding="utf-8")
        cls.knowledge = json.loads(
            (OUTPUT / "data/nma-runtime-knowledge-v0.4.json").read_text(encoding="utf-8")
        )
        cls.release = json.loads((OUTPUT / "release.json").read_text(encoding="utf-8"))

    def test_runtime_is_derived_from_frozen_canonical_graph(self) -> None:
        self.assertEqual(self.knowledge["source"]["commit"], "eb87bde775333811529efb6f651573ea21cf456b")
        self.assertEqual(self.knowledge["source"]["graph_id"], "nma-canonical-graph-v0.4")
        self.assertGreaterEqual(self.knowledge["statistics"]["nodes"], 800)
        self.assertIn('const KNOWLEDGE_URL = "data/nma-runtime-knowledge-v0.4.json"', self.app)
        self.assertIn("fetch(asset(KNOWLEDGE_URL)", self.app)
        self.assertNotIn("const PROFILES =", self.app)

    def test_document_09_layers_and_fields_are_in_projection(self) -> None:
        ids = {node["id"] for node in self.knowledge["nodes"]}
        for node_id in (
            "document:doc09-temap-layers",
            "product-layer:MARK",
            "product-layer:ROAD",
            "product-layer:BUILD",
            "field:MARK:MARKID",
            "field:ROAD:ROADSEGID",
            "field:ROAD:ROADCLASS2",
        ):
            self.assertIn(node_id, ids)

    def test_classification_labels_come_from_graph_including_build(self) -> None:
        by_id = {node["id"]: node for node in self.knowledge["nodes"]}
        self.assertEqual(by_id["terrain-classification:doc02:9920100"]["properties"]["name_zh"], "學校及訓練機構")
        self.assertEqual(by_id["terrain-classification:doc02:9920106"]["properties"]["name_zh"], "特殊學校")
        self.assertEqual(by_id["classification:doc01:9310103"]["properties"]["label"], "無牆建物")
        self.assertEqual(by_id["classification:doc01:9310200"]["properties"]["label"], "建築中建物")
        self.assertIn("if (n.id.includes(\"doc01\") && p.label) current.label = p.label", self.app)

    def test_unknown_mapping_enters_bounded_question_and_replan(self) -> None:
        for marker in (
            'unknown_mapping_action": "ask-user"',
            'id="clarification-panel"',
            'id="confirm-mapping"',
            'id="reject-mapping"',
            "NEEDS CLARIFICATION",
            "current-browser-run-only",
            "回答已改變 decision；Agent 重新規劃完成",
            "APPROVED_MAPPING_TO",
        ):
            self.assertIn(marker, json.dumps(self.knowledge, ensure_ascii=False) + self.run_page + self.app)
        self.assertFalse(self.knowledge["governance"]["session_mapping_reuse"])

    def test_intake_is_strict_and_uses_actual_archive_envelope(self) -> None:
        for marker in (
            "const MAX_ARCHIVE_BYTES = 16 * 1024 * 1024",
            "const MAX_UNCOMPRESSED_BYTES = 64 * 1024 * 1024",
            "const MAX_ENTRIES = 1500",
            'const SIDECARS = ["shp", "shx", "dbf", "prj"]',
            "缺少必要欄位 TERRAINID",
            "TERRAINID 未通過 KG code validation",
            ".prj 為空",
        ):
            self.assertIn(marker, self.app)

    def test_identity_is_filename_plus_source_id_not_global_unique_id(self) -> None:
        self.assertEqual(
            self.knowledge["governance"]["source_identity"],
            "normalized-zip-relative-filename + source-id",
        )
        self.assertIn("const identity = `${filename}::${sourceId}`", self.app)
        self.assertIn("logical identity 不變；renderer key 才加 index", self.app)
        self.assertNotIn("uniqueCompositeIds.size === compositeIds.length", self.app)

    def test_no_fixed_acceptance_fixture_gate(self) -> None:
        for forbidden in ("expectedCount", "expectedVertices", 'codeValue: "9920103"', 'layerExact: "K14_ROAD"', 'nameValue: "中山街"'):
            self.assertNotIn(forbidden, self.app)
        self.assertIn("沒有固定 15-point 或其他 acceptance count", self.app)

    def test_symbolic_agent_loop_and_authorization_are_observable(self) -> None:
        for label in ("Goal", "Observe", "Retrieve KG", "Clarify", "Replan", "Authorize", "Act", "Verify / stop"):
            self.assertIn(f'"{label}"', self.app)
        self.assertIn("Agenticity", self.app)
        self.assertIn("EXERCISED · SYMBOLIC", self.app)
        self.assertIn("if (!state.proposal) return", self.app)

    def test_maplibre_handles_point_line_polygon_without_export(self) -> None:
        for marker in ('type: "circle"', 'type: "line"', 'type: "fill"', '"fill-pattern": "hatch"', "new maplibregl.Map"):
            self.assertIn(marker, self.app)
        self.assertIn("不輸出資料", self.run_page + self.app)
        self.assertIn("production activation：HELD / DISABLED", self.app)

    def test_local_links_are_path_prefix_safe_and_exist(self) -> None:
        for page in (self.index, self.run_page):
            parser = LinkParser()
            parser.feed(page)
            for value in parser.local:
                self.assertFalse(value.startswith("/"), value)
                target = value.split("?", 1)[0]
                if target in {".", "./"}:
                    target = "index.html"
                self.assertTrue((OUTPUT / target).is_file(), value)
        self.assertNotRegex(self.app, re.compile(r'["\']/[^"\']+'))

    def test_landing_routes_to_three_separate_domain_runs(self) -> None:
        self.assertNotIn('id="shp-file"', self.index)
        self.assertNotIn("scenario-tabs", self.index)
        for domain, geometry in (("school", "POINT"), ("road", "LINE"), ("build", "POLYGON")):
            self.assertEqual(self.index.count(f'run.html?domain={domain}'), 1)
            self.assertIn(geometry, self.index)
        self.assertIn('new URL("data/nma-runtime-knowledge-v0.4.json", document.baseURI)', self.landing)

    def test_run_page_locks_domain_from_path_prefix_safe_query(self) -> None:
        self.assertNotIn("scenario-tabs", self.run_page)
        self.assertNotIn("scenario-tab", self.run_page)
        for domain in ("school", "road", "build"):
            self.assertIn(f'data-domain-link="{domain}"', self.run_page)
        self.assertIn('new URLSearchParams(location.search).get("domain")', self.app)
        self.assertIn('const initialDomain = Object.hasOwn(UI, requestedDomain)', self.app)
        self.assertNotIn('document.querySelectorAll(".scenario-tab")', self.app)

    def test_public_release_has_no_fixture_bytes_or_credentials(self) -> None:
        paths = [item["path"].lower() for item in self.release["files"]]
        self.assertFalse(any(path.endswith((".zip", ".shp", ".shx", ".dbf", ".pmtiles")) for path in paths))
        self.assertFalse(self.release["private_fixture_bytes_included"])
        self.assertFalse(self.release["production_credentials_included"])
        self.assertFalse(self.release["production_activation"])
        corpus = self.index + self.run_page + self.app + self.landing + json.dumps(self.knowledge)
        for secret in ("OPENAI_API_KEY", "NEO4J_PASSWORD", "sk-proj-"):
            self.assertNotIn(secret, corpus)

    def test_manifest_lists_exact_artifact(self) -> None:
        expected = {path.relative_to(OUTPUT).as_posix() for path in OUTPUT.rglob("*") if path.is_file() and path.name != "release.json"}
        self.assertEqual({item["path"] for item in self.release["files"]}, expected)
        self.assertTrue(self.release["user_file_required"])
        self.assertFalse(self.release["user_file_transmission"])
        self.assertFalse(self.release["preloaded_result_geometry"])
        self.assertEqual(self.release["schema"], "nma.github-pages-static-release/2.1")
        self.assertEqual(self.release["interface"], "task-landing-plus-domain-locked-run")
        self.assertEqual(
            self.release["domain_routes"],
            {
                "school": "run.html?domain=school",
                "road": "run.html?domain=road",
                "build": "run.html?domain=build",
            },
        )


if __name__ == "__main__":
    unittest.main()

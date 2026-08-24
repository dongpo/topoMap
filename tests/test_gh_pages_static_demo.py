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
        cls.app = (OUTPUT / "app.js").read_text(encoding="utf-8")
        cls.release = json.loads((OUTPUT / "release.json").read_text(encoding="utf-8"))

    def test_demo_requires_user_shapefile_before_any_result(self) -> None:
        self.assertIn('type="file"', self.index)
        self.assertIn('accept=".zip,application/zip"', self.index)
        self.assertIn("USER SHP REQUIRED", self.index)
        self.assertIn("尚未執行；沒有預製 geometry", self.index)
        self.assertNotIn("data/scenarios.json", self.index + self.app)
        self.assertFalse((OUTPUT / "data/scenarios.json").exists())

    def test_school_road_build_are_user_data_profiles(self) -> None:
        for profile in ("school", "road", "build"):
            self.assertIn(f'data-profile="{profile}"', self.index)
            self.assertRegex(self.app, rf"{profile}: \{{")
        self.assertIn('layerSuffix: "_MARK"', self.app)
        self.assertIn('codeValue: "9920103"', self.app)
        self.assertIn('expectedCount: 15', self.app)
        self.assertIn('layerExact: "K14_ROAD"', self.app)
        self.assertIn('nameValue: "中山街"', self.app)
        self.assertIn('expectedVertices: [4, 3, 4]', self.app)
        self.assertIn('layerExact: "J17_BUILD"', self.app)
        self.assertIn('codeValue: "9310100"', self.app)
        self.assertIn('baseName(layer.name).toLocaleUpperCase() === profile.layerExact', self.app)

    def test_intake_has_component_crs_identity_and_geometry_gates(self) -> None:
        for marker in (
            'const SIDECARS = ["shp", "shx", "dbf", "prj"]',
            "safeEntryName",
            "MAX_UNCOMPRESSED_BYTES",
            "missingSidecars",
            "crsSummary",
            "geometryMismatch",
            "uniqueIds",
            "selectedComponentHashes",
            "crypto.subtle.digest",
        ):
            self.assertIn(marker, self.app)

    def test_eight_stage_controlled_lifecycle_is_visible(self) -> None:
        for label in (
            "Request",
            "Agent interpretation",
            "GraphRAG / rules",
            "Plan",
            "Authorization",
            "Execution",
            "QA / verification",
            "Provenance",
        ):
            self.assertIn(f'"{label}"', self.app)
        self.assertIn("AUTHORIZATION REQUIRED", self.index + self.app)
        self.assertIn("if (!proposal || !proposal.hardGate) return", self.app)

    def test_verification_does_not_fake_unsupported_operations(self) -> None:
        self.assertIn("Hausdorff distance：未執行", self.app)
        self.assertIn("PMTiles / Hausdorff / OSM comparison", self.index)
        self.assertIn("沒有外部資料 substitution", self.app)
        self.assertIn("production activation：HELD / DISABLED", self.app)
        self.assertIn('production_activation: false', self.app)

    def test_browser_parsers_and_maplibre_are_pinned_and_vendored(self) -> None:
        expected = (
            "assets/maplibre-gl-4.7.0.js",
            "assets/maplibre-gl-4.7.0.css",
            "assets/shpjs-6.2.0.min.js",
            "assets/shpjs-6.2.0-LICENSE.txt",
            "assets/fflate-0.8.3.min.js",
            "assets/fflate-0.8.3-LICENSE.txt",
        )
        for path in expected:
            self.assertTrue((OUTPUT / path).is_file(), path)
            self.assertIn(path, self.index if path.endswith((".js", ".css")) else json.dumps(self.release))
        self.assertIn("window.shp(buffer)", self.app)
        self.assertIn("window.fflate.unzipSync", self.app)
        self.assertIn("new maplibregl.Map", self.app)

    def test_all_local_links_are_path_prefix_safe_and_exist(self) -> None:
        parser = LinkParser()
        parser.feed(self.index)
        self.assertTrue(parser.local)
        for value in parser.local:
            self.assertFalse(value.startswith("/"), value)
            target = value.split("?", 1)[0]
            if target in {".", "./"}:
                target = "index.html"
            self.assertTrue((OUTPUT / target).is_file(), value)
        self.assertNotRegex(self.app, re.compile(r'["\']/[^"\']+'))

    def test_release_has_no_user_fixture_or_credentials(self) -> None:
        paths = [item["path"].lower() for item in self.release["files"]]
        forbidden_suffixes = (".zip", ".shp", ".dbf", ".shx", ".pmtiles")
        self.assertFalse(any(path.endswith(forbidden_suffixes) for path in paths))
        self.assertFalse(self.release["private_fixture_bytes_included"])
        self.assertFalse(self.release["production_credentials_included"])
        self.assertFalse(self.release["production_activation"])
        corpus = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in OUTPUT.rglob("*")
            if path.is_file() and path.suffix in {".html", ".js", ".css", ".json"}
        )
        for marker in ("OPENAI_API_KEY", "NEO4J_PASSWORD", "sk-proj-", "/api/v1/runs"):
            self.assertNotIn(marker, corpus)

    def test_release_manifest_lists_exact_public_artifact(self) -> None:
        expected = {
            path.relative_to(OUTPUT).as_posix()
            for path in OUTPUT.rglob("*")
            if path.is_file() and path.name != "release.json"
        }
        listed = {item["path"] for item in self.release["files"]}
        self.assertEqual(listed, expected)
        self.assertTrue(self.release["user_file_required"])
        self.assertFalse(self.release["user_file_transmission"])
        self.assertFalse(self.release["preloaded_result_geometry"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
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
        cls.payload = json.loads(
            (OUTPUT / "data/scenarios.json").read_text(encoding="utf-8")
        )
        cls.release = json.loads((OUTPUT / "release.json").read_text(encoding="utf-8"))
        cls.scenarios = {item["id"]: item for item in cls.payload["scenarios"]}

    def test_three_required_scenarios_and_replay_boundary(self) -> None:
        self.assertEqual(set(self.scenarios), {"school", "road", "build"})
        self.assertEqual(self.payload["release"]["mode"], "accepted execution replay")
        self.assertFalse(self.payload["release"]["live_agent"])
        self.assertFalse(self.payload["release"]["production_credentials"])
        self.assertIn("REPLAY · NOT LIVE", self.index)

    def test_school_is_accepted_fifteen_point_public_safe_replay(self) -> None:
        school = self.scenarios["school"]
        self.assertEqual(school["execution"]["feature_count"], 15)
        self.assertEqual(len(school["map"]["geojson"]["features"]), 15)
        self.assertIn("accepted", school["authorization"]["status"])
        self.assertEqual(
            school["map"]["coordinate_policy"],
            "normalized-public-replay-not-source-geography",
        )
        self.assertTrue(
            all(
                feature["id"].startswith("public-replay-")
                for feature in school["map"]["geojson"]["features"]
            )
        )

    def test_road_preserves_accepted_identity_counts_and_label(self) -> None:
        road = self.scenarios["road"]
        features = road["map"]["geojson"]["features"]
        self.assertEqual(
            [len(item["geometry"]["coordinates"]) for item in features], [4, 3, 4]
        )
        self.assertEqual(
            [item["properties"]["ROADNAME"] for item in features], ["中山街"] * 3
        )
        self.assertIn("K14_ROAD", road["title"])
        self.assertIn("line-following 中山街", road["subtitle"])

    def test_build_is_normalized_hatched_replay_with_activation_disabled(self) -> None:
        build = self.scenarios["build"]
        self.assertFalse(build["production_activation"])
        self.assertEqual(build["execution"]["feature_count"], 1)
        self.assertEqual(
            build["map"]["geojson"]["features"][0]["geometry"]["type"], "Polygon"
        )
        self.assertIn("45° diagonal hatch", build["knowledge"]["mapping_rule"])
        self.assertIn("fill-pattern", self.app)

    def test_eight_stage_evidence_chain_is_visible(self) -> None:
        for label in (
            "Request",
            "Agent interpretation",
            "GraphRAG / rules",
            "Plan",
            "Authorization",
            "Execution replay",
            "QA / verification",
            "Provenance",
        ):
            self.assertIn(f'"{label}"', self.app)

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
        self.assertNotIn('const BASE = "/', self.app)

    def test_release_excludes_private_archives_credentials_and_live_api(self) -> None:
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

    def test_maplibre_is_vendored_and_manifest_is_complete(self) -> None:
        self.assertTrue((OUTPUT / "assets/maplibre-gl-4.7.0.js").is_file())
        self.assertIn("maplibregl.Map", self.app)
        listed = {item["path"] for item in self.release["files"]}
        self.assertIn("index.html", listed)
        self.assertIn("data/scenarios.json", listed)
        self.assertIn("assets/maplibre-gl-4.7.0.js", listed)


if __name__ == "__main__":
    unittest.main()

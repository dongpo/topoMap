from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


PUBLIC_FILES = {
    "data/knowledge/portrayal-graph.json": "data/knowledge/portrayal-graph.json",
    "data/demo/five-scene-demo.json": "data/demo/five-scene-demo.json",
    "data/demo/pmtiles-capability-catalog.json": "data/demo/pmtiles-capability-catalog.json",
    "assets/symbols/nlsc112v5.4/school.svg": "assets/symbols/nlsc112v5.4/school.svg",
    "assets/symbols/nlsc112v5.4/fire-hydrant.svg": ("assets/symbols/nlsc112v5.4/fire-hydrant.svg"),
    "assets/symbols/nlsc112v5.4/police.svg": "assets/symbols/nlsc112v5.4/police.svg",
    "assets/symbols/nlsc112v5.4/fish-pond.svg": "assets/symbols/nlsc112v5.4/fish-pond.svg",
    "assets/symbols/nlsc112v5.4/post.svg": "assets/symbols/nlsc112v5.4/post.svg",
    "artifacts/presentation/d18/architecture.png": "artifacts/presentation/d18/architecture.png",
    "artifacts/presentation/nma-foss4g-presentation-v0.9.pptx": (
        "artifacts/presentation/nma-foss4g-presentation-v0.9.pptx"
    ),
    "artifacts/release/nma-v0.2-review-package.zip": (
        "artifacts/release/nma-v0.2-review-package.zip"
    ),
    "artifacts/release/nma-v0.2-review-package-verification.json": (
        "artifacts/release/nma-v0.2-review-package-verification.json"
    ),
}


class PublicPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.images: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "a" and values.get("href"):
            self.hrefs.append(values["href"] or "")
        if tag == "img" and values.get("src"):
            self.images.append(values["src"] or "")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def public_index(source: str) -> str:
    source = source.replace(
        '<a class="button" href="nmaAgentDemo.html" data-public-link="demo">Open five-scene demo</a>',
        '<a class="button" href="nmaAgentDemo.html?mode=degraded" '
        'data-public-link="demo">Open evidence-only demo</a>',
    )
    source = source.replace(
        '<p class="notice"><strong>Release status:</strong> the executable candidate is verified. The\n'
        "      GitHub Pages URL remains unavailable until PR #1 is merged or a separate deployment is\n"
        "      explicitly approved. Repository readiness is not deployment completion.</p>",
        '<p class="notice"><strong>Public release mode:</strong> this site publishes the reviewed '
        "evidence-only demonstration and excludes the PMTiles archive. The full live-map RC1 remains "
        "available for local rehearsal after licence review.</p>",
    )
    source = source.replace(
        "<li>First load must be online to prime the pinned cache; evidence-only mode and the D16 "
        "recording are the supported offline fallbacks.</li>",
        "<li>This public artifact intentionally runs in evidence-only mode. The full live-map RC1 "
        "requires the local rehearsal setup and its online preflight.</li>",
    )
    marker = (
        '        <a class="button secondary" href="https://github.com/dongpo/topoMap/blob/'
        'codex/nma-v0.2-authoritative/docs/QUICKSTART.md" data-public-link="documentation">'
        "Read quickstart</a>\n"
    )
    additions = (
        marker + '        <a class="button secondary" href="artifacts/presentation/'
        'nma-foss4g-presentation-v0.9.pptx">Download presentation RC</a>\n'
        + '        <a class="button secondary" href="artifacts/release/'
        'nma-v0.2-review-package.zip">Download review package</a>\n'
    )
    if marker not in source:
        raise ValueError("public landing-page insertion point is missing")
    return source.replace(marker, additions)


def public_demo(source: str) -> str:
    marker = 'const DEGRADED_MODE=new URLSearchParams(location.search).get("mode")==="degraded";'
    replacement = (
        "const PUBLIC_EVIDENCE_ONLY=true;"
        "const DEGRADED_MODE=PUBLIC_EVIDENCE_ONLY||"
        'new URLSearchParams(location.search).get("mode")==="degraded";'
    )
    if marker not in source:
        raise ValueError("public demo mode marker is missing")
    return source.replace(marker, replacement)


def local_target(value: str) -> str:
    return value.split("#", 1)[0].split("?", 1)[0]


def check_page_links(site: Path, page: str) -> dict[str, Any]:
    source = (site / page).read_text(encoding="utf-8")
    parser = PublicPageParser()
    parser.feed(source)
    missing = []
    for value in [*parser.hrefs, *parser.images]:
        if value.startswith(("http://", "https://", "mailto:")):
            continue
        if value.startswith("#"):
            if value[1:] not in parser.ids:
                missing.append(value)
            continue
        target = local_target(value)
        if target and not (site / target).is_file():
            missing.append(value)
    return {
        "page": page,
        "link_count": len(parser.hrefs),
        "image_count": len(parser.images),
        "missing": missing,
    }


def build_public_site(root: Path, output: Path) -> dict[str, Any]:
    root = root.resolve()
    output = output.resolve()
    if output == root or root not in output.parents:
        raise ValueError("public-site output must be a dedicated directory inside the repository")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    (output / "index.html").write_text(
        public_index((root / "index.html").read_text(encoding="utf-8")), encoding="utf-8"
    )
    (output / "nmaAgentDemo.html").write_text(
        public_demo((root / "nmaAgentDemo.html").read_text(encoding="utf-8")), encoding="utf-8"
    )
    (output / ".nojekyll").write_text("", encoding="utf-8")

    for source_name, target_name in PUBLIC_FILES.items():
        source = root / source_name
        if not source.is_file():
            raise FileNotFoundError(f"missing public release asset: {source_name}")
        target = output / target_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    link_checks = [check_page_links(output, "index.html")]
    missing = [item for result in link_checks for item in result["missing"]]
    if missing:
        raise ValueError(f"public website has missing local links/assets: {missing}")

    if any(path.suffix == ".pmtiles" for path in output.rglob("*")):
        raise ValueError("public site must not contain a PMTiles archive")
    if "PUBLIC_EVIDENCE_ONLY=true" not in (output / "nmaAgentDemo.html").read_text(
        encoding="utf-8"
    ):
        raise ValueError("public demo must be frozen in evidence-only mode")
    demo_source = (output / "nmaAgentDemo.html").read_text(encoding="utf-8")
    for required_fetch in (
        'fetch("data/knowledge/portrayal-graph.json")',
        'fetch("data/demo/five-scene-demo.json")',
        'fetch("data/demo/pmtiles-capability-catalog.json")',
    ):
        if required_fetch not in demo_source:
            raise ValueError(f"public demo is missing required data load: {required_fetch}")

    payload = sorted(path for path in output.rglob("*") if path.is_file())
    release = {
        "release_version": "nma-public-assets-v0.2-rc1",
        "stable_demo_release": "nma-demo-v0.2-rc1",
        "public_mode": "evidence-only",
        "pmtiles_included": False,
        "files": [
            {
                "path": path.relative_to(output).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in payload
        ],
        "link_checks": link_checks,
    }
    write_json(output / "release.json", release)
    return release


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the bounded NMA public website artifact")
    parser.add_argument("--output", default="artifacts/tmp/public-site")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / args.output
    release = build_public_site(root, output)
    print(
        json.dumps(
            {
                "output": output.relative_to(root).as_posix(),
                "file_count": len(release["files"]),
                "public_mode": release["public_mode"],
                "pmtiles_included": release["pmtiles_included"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

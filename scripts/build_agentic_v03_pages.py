from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STABLE_ROOT_COMMIT = "60eb2857b1ff14b0baa51732373ca5c8b697c1c3"
MANIFEST = ROOT / "data/demo/agentic-v0.3-pages.json"
STABLE_SOURCE_FILES = (
    "scripts/build_public_site.py",
    "index.html",
    "nmaAgentDemo.html",
    "data/knowledge/portrayal-graph.json",
    "data/demo/five-scene-demo.json",
    "artifacts/presentation/d18/architecture.png",
    "artifacts/presentation/nma-foss4g-presentation-v0.9.pptx",
    "artifacts/release/nma-v0.2-review-package.zip",
    "artifacts/release/nma-v0.2-review-package-verification.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_bytes(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        raise FileNotFoundError(f"{path} is unavailable in stable snapshot {commit}")
    return result.stdout


def materialize_stable_source(target: Path) -> None:
    for relative in STABLE_SOURCE_FILES:
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(git_bytes(STABLE_ROOT_COMMIT, relative))


def build_stable_root(target: Path) -> dict[str, Any]:
    materialize_stable_source(target)
    result = subprocess.run(
        [
            sys.executable,
            str(target / "scripts/build_public_site.py"),
            "--output",
            "artifacts/tmp/public-site",
        ],
        cwd=target,
        check=True,
        capture_output=True,
        text=True,
    )
    site = target / "artifacts/tmp/public-site"
    release = json.loads((site / "release.json").read_text(encoding="utf-8"))
    if release["release_version"] != "nma-public-assets-v0.2-rc1":
        raise ValueError("stable root release identity changed")
    if release["stable_demo_release"] != "nma-demo-v0.2-rc1":
        raise ValueError("stable root demo identity changed")
    if release["pmtiles_included"] is not False:
        raise ValueError("stable public root unexpectedly contains PMTiles")
    return {"site": site, "release": release, "builder_output": result.stdout.strip()}


def candidate_demo(source: str) -> str:
    replacements = {
        'const DEGRADED_MODE=new URLSearchParams(location.search).get("mode")==="degraded";': (
            "const PUBLIC_AGENTIC_CANDIDATE=true;const DEGRADED_MODE=false;"
        ),
        'fetch("/api/datasets/school-points/inspect",{cache:"no-store"})': (
            'fetch("data/demo/school-points-public-inspection.json",{cache:"no-store"})'
        ),
        'fetch(`/api/datasets/${layerProposal.dataset_id}/geojson`,{cache:"no-store"})': (
            'fetch("data/demo/school-points-public.geojson",{cache:"no-store"})'
        ),
        "async function loadMapRuntime(){await registerOfflineCache();await Promise.all([loadStylesheet(MAPLIBRE_CSS),loadScript(MAPLIBRE_JS,()=>Boolean(globalThis.maplibregl)),loadScript(PMTILES_JS,()=>Boolean(globalThis.pmtiles))])}": (
            "async function loadMapRuntime(){await Promise.all([loadStylesheet(MAPLIBRE_CSS),"
            "loadScript(MAPLIBRE_JS,()=>Boolean(globalThis.maplibregl))])}"
        ),
        'function mapRuntimeStatus(){return basemapMode==="nlsc-online"?"Map ready · NLSC EMAP online · local PMTiles data · supervised dynamic layers":"Map ready · local PMTiles basemap fallback · NLSC EMAP unavailable or bypassed"}': (
            'function mapRuntimeStatus(){return basemapMode==="nlsc-online"?'
            '"Map ready · NLSC EMAP online · bounded public data · supervised dynamic layers":'
            '"Map ready · bounded public background fallback · NLSC EMAP unavailable or bypassed"}'
        ),
        'function activateLocalBasemapFallback(reason){basemapMode="local-pmtiles-fallback";if(map?.getLayer("nlsc-emap-basemap"))map.setLayoutProperty("nlsc-emap-basemap","visibility","none");setRuntimeStatus(`${mapRuntimeStatus()} · ${reason}`,true)}': (
            'function activateLocalBasemapFallback(reason){basemapMode="bounded-public-fallback";'
            'if(map?.getLayer("nlsc-emap-basemap"))map.setLayoutProperty('
            '"nlsc-emap-basemap","visibility","none");'
            "setRuntimeStatus(`${mapRuntimeStatus()} · ${reason}`,true)}"
        ),
        "  const protocol=new pmtiles.Protocol({metadata:true});\n"
        '  maplibregl.addProtocol("pmtiles",protocol.tile);\n'
        '  map=new maplibregl.Map({container:"map",center:[121.0236,24.7745],zoom:14,style:{version:8,glyphs:GLYPHS_URL,sources:{data:{type:"vector",url:`pmtiles://${PMT_URL}`}},layers:[{id:"background",type:"background",paint:{"background-color":"#f7faf8"}}]}});': (
            '  map=new maplibregl.Map({container:"map",center:[121.0236,24.7745],zoom:14,'
            'style:{version:8,glyphs:GLYPHS_URL,sources:{},layers:[{id:"background",'
            'type:"background",paint:{"background-color":"#f7faf8"}}]}});'
        ),
        "    generatedLayers.forEach(layer=>map.addLayer(layer));": (
            "    // The public candidate excludes the repository-only PMTiles source and its layers."
        ),
        "    implementationLayers.forEach(layer=>map.addLayer(layer));": (
            "    // Implementation-only catalog entries remain inspectable but are not mapped publicly."
        ),
    }
    for marker, replacement in replacements.items():
        if marker not in source:
            raise ValueError(f"Agentic public transform marker is missing: {marker[:80]}")
        source = source.replace(marker, replacement, 1)
    return source


def candidate_index() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>National Map Agent · Agentic Demo v0.3 Candidate</title>
  <style>
    :root{font-family:Inter,system-ui,sans-serif;color:#10251f;background:#eef3ef}
    body{margin:0;display:grid;min-height:100vh;place-items:center}
    main{max-width:760px;margin:24px;padding:44px;border:1px solid #c7d5cc;border-radius:20px;background:#fff;box-shadow:0 18px 50px #143c2b18}
    .badge{display:inline-block;padding:6px 10px;border-radius:999px;background:#fff0c2;color:#6b4d00;font-weight:700}
    h1{font-size:clamp(2rem,6vw,4rem);line-height:1;margin:.4em 0}
    p{font-size:1.08rem;line-height:1.65;color:#40534b}
    a.button{display:inline-block;margin:.5rem .6rem .2rem 0;padding:12px 18px;border-radius:10px;background:#11633f;color:#fff;text-decoration:none;font-weight:700}
    a.secondary{background:#e8f2eb;color:#164d35}
    code{background:#edf2ee;padding:.15rem .35rem;border-radius:5px}
  </style>
</head>
<body><main>
  <span class="badge">candidate · not deployed as stable</span>
  <h1>Agentic Demo v0.3</h1>
  <p>This bounded candidate demonstrates supervised conversation, evidence-graph inspection, symbol revision, static Shapefile inspection evidence, explicit layer approval, and an NLSC EMAP context map.</p>
  <p>The repository-only PMTiles archive, API keys, official source PDFs, tests, and development files are excluded. GPT routing falls back deterministically because no server credential is shipped to Pages.</p>
  <a class="button" href="nmaAgentDemo.html">Open Agentic v0.3 candidate</a>
  <a class="button secondary" href="../">Return to stable v0.2</a>
  <p><small>Release identity: <code>nma-agentic-v0.3-pages-rc1</code></small></p>
</main></body></html>
"""


def verify_source_assets(manifest: dict[str, Any]) -> None:
    for item in manifest["source_assets"]:
        path = ROOT / item["path"]
        if not path.is_file():
            raise FileNotFoundError(f"missing Agentic Pages source asset: {item['path']}")
        if path.stat().st_size != item["size_bytes"]:
            raise ValueError(f"{item['path']} size differs from the candidate manifest")
        if sha256(path) != item["sha256"]:
            raise ValueError(f"{item['path']} SHA-256 differs from the candidate manifest")


def build_candidate_subtree(manifest: dict[str, Any], target: Path) -> dict[str, Any]:
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(candidate_index(), encoding="utf-8")
    (target / "nmaAgentDemo.html").write_text(
        candidate_demo((ROOT / "nmaAgentDemo.html").read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    for item in manifest["candidate_assets"]:
        source = ROOT / item["source"]
        destination = target / item["target"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    if any(path.suffix == ".pmtiles" for path in target.rglob("*")):
        raise ValueError("Agentic v0.3 public candidate must not contain PMTiles")
    forbidden_names = {".env", ".env.local", "OPENAI_API_KEY"}
    if any(path.name in forbidden_names for path in target.rglob("*")):
        raise ValueError("Agentic v0.3 public candidate contains a credential file")
    demo = (target / "nmaAgentDemo.html").read_text(encoding="utf-8")
    required_markers = (
        "PUBLIC_AGENTIC_CANDIDATE=true",
        'fetch("data/demo/school-points-public-inspection.json"',
        'fetch("data/demo/school-points-public.geojson"',
        "NLSC_EMAP_TILES",
        "bounded public background fallback",
        "function renderKnowledgeGraph(decision)",
        "function renderSymbolWorkshop(decision)",
        "async function createApprovedLayer(approvalSource)",
    )
    missing = [marker for marker in required_markers if marker not in demo]
    if missing:
        raise ValueError(f"Agentic candidate runtime markers are missing: {missing}")

    payload = sorted(path for path in target.rglob("*") if path.is_file())
    release = {
        "release_version": manifest["release_version"],
        "status": "candidate-built-not-deployed",
        "source_commit": manifest["source"]["agentic_freeze_commit"],
        "candidate_path": manifest["website"]["candidate_path"],
        "stable_root_release": manifest["website"]["stable_root_release"],
        "public_mode": "bounded-static-agentic",
        "model_mode": "deterministic-fallback; no API credential shipped",
        "nlsc_cache_policy": "network-only; no bulk caching",
        "pmtiles_included": False,
        "files": [
            {
                "path": path.relative_to(target).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in payload
        ],
    }
    write_json(target / "release.json", release)
    return release


def build_pages_candidate(root: Path, output: Path) -> dict[str, Any]:
    root = root.resolve()
    output = output.resolve()
    if output == root:
        raise ValueError("Pages candidate output cannot replace the repository root")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    verify_source_assets(manifest)
    if output.exists():
        shutil.rmtree(output)

    temporary_parent = ROOT / "artifacts/tmp"
    temporary_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nma-stable-root-", dir=temporary_parent) as temp:
        stable = build_stable_root(Path(temp) / "stable-source")
        shutil.copytree(stable["site"], output)

    candidate = build_candidate_subtree(manifest, output / manifest["website"]["candidate_path"])
    combined = {
        "schema": "nma.agentic-v0.3-pages-candidate/1.0",
        "status": "candidate-built-not-deployed",
        "stable_root": {
            "release_version": stable["release"]["release_version"],
            "source_commit": STABLE_ROOT_COMMIT,
            "release_sha256": sha256(output / "release.json"),
        },
        "agentic_candidate": {
            "release_version": candidate["release_version"],
            "path": manifest["website"]["candidate_path"],
            "release_sha256": sha256(
                output / manifest["website"]["candidate_path"] / "release.json"
            ),
        },
        "deployment_state": "not-deployed",
        "owner_approval_required": True,
    }
    write_json(output / "pages-candidate.json", combined)
    return combined


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build stable v0.2 root plus bounded Agentic v0.3 Pages candidate"
    )
    parser.add_argument("--output", default="artifacts/tmp/agentic-v0.3-pages")
    args = parser.parse_args()
    output = ROOT / args.output
    result = build_pages_candidate(ROOT, output)
    print(
        json.dumps(
            {
                "output": output.relative_to(ROOT).as_posix(),
                **result,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import resolve_asset


def load_offline_runtime(path: str | Path) -> dict[str, Any]:
    with resolve_asset(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def check_offline_runtime(
    path: str | Path = "data/demo/offline-runtime.json",
) -> dict[str, Any]:
    runtime = load_offline_runtime(path)
    missing = [asset for asset in runtime["local_assets"] if not resolve_asset(asset).is_file()]
    if missing:
        raise ValueError(f"missing offline runtime assets: {', '.join(missing)}")

    html = resolve_asset("nmaAgentDemo.html").read_text(encoding="utf-8")
    worker = resolve_asset(runtime["cache"]["worker"]).read_text(encoding="utf-8")
    if 'const PMT_URL="out1120902.pmtiles"' not in html:
        raise ValueError("demo does not use the locally packaged PMTiles archive")
    if 'get("mode")==="degraded"' not in html or "activateEvidenceFallback" not in html:
        raise ValueError("demo does not expose the deterministic evidence-only fallback")
    if runtime["cache"]["name"] not in worker:
        raise ValueError("service-worker cache name does not match the runtime manifest")
    for asset in runtime["cache"]["pinned_runtime_assets"]:
        if asset not in worker or asset not in html:
            raise ValueError(f"runtime dependency is not pinned consistently: {asset}")
    if runtime["cache"]["glyph_prefix"] not in worker:
        raise ValueError("glyph cache route is missing")
    if runtime["pmtiles_range_strategy"] != "service-worker-local-range-adapter":
        raise ValueError("local PMTiles range strategy is not declared")
    if "pmtilesRangeResponse" not in worker or '"Content-Range"' not in worker:
        raise ValueError("local PMTiles byte-range adapter is missing")
    verification = runtime["verification"]
    if verification["normal_mode"]["status"] != "passed":
        raise ValueError("normal offline-ready browser mode is not verified")
    if verification["degraded_mode"]["status"] != "passed":
        raise ValueError("evidence-only browser mode is not verified")
    if verification["degraded_mode"]["passed_scenes"] != 5:
        raise ValueError("degraded browser verification must cover all five scenes")
    for mode in (verification["normal_mode"], verification["degraded_mode"]):
        if mode["console_errors"] or mode["console_warnings"]:
            raise ValueError("browser verification contains console errors or warnings")
    if not runtime["deferred"]:
        raise ValueError("non-blocking offline limitations must be explicitly deferred")
    if any(item["classification"] != "non-blocking" for item in runtime["deferred"]):
        raise ValueError("blocking offline limitations cannot be deferred")
    if any(not item["owner"] or not item["next_action"] for item in runtime["deferred"]):
        raise ValueError("every deferred limitation needs an owner and next action")

    return {
        "runtime_version": runtime["runtime_version"],
        "status": "passed",
        "local_asset_count": len(runtime["local_assets"]),
        "pinned_runtime_asset_count": len(runtime["cache"]["pinned_runtime_assets"]),
        "fallback_mode": runtime["fallback"]["mode"],
        "browser_modes_verified": 2,
        "deferred_count": len(runtime["deferred"]),
    }

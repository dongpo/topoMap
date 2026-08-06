import json
from pathlib import Path

from nma.demo_offline import check_offline_runtime


ROOT = Path(__file__).resolve().parents[1]


def test_offline_runtime_packages_local_data_and_a_degraded_fallback() -> None:
    result = check_offline_runtime()

    assert result == {
        "runtime_version": "nma-agentic-v0.3-a02",
        "status": "passed",
        "local_asset_count": 11,
        "pinned_runtime_asset_count": 3,
        "fallback_mode": "evidence-only",
        "browser_modes_verified": 2,
        "deferred_count": 2,
    }


def test_offline_manifest_keeps_deferrals_owned_and_non_blocking() -> None:
    runtime = json.loads((ROOT / "data/demo/offline-runtime.json").read_text())

    assert runtime["local_pmtiles_url"] == "out1120902.pmtiles"
    assert runtime["pmtiles_range_strategy"] == "service-worker-local-range-adapter"
    assert runtime["cache"]["glyph_strategy"] == "cache-on-use"
    assert runtime["cache"]["local_shell_strategy"] == "network-first-with-cache-fallback"
    assert runtime["verification"]["normal_mode"]["local_pmtiles_range_adapter"] == "passed"
    assert runtime["verification"]["degraded_mode"]["passed_scenes"] == 5
    assert all(item["classification"] == "non-blocking" for item in runtime["deferred"])
    assert all(item["owner"] and item["next_action"] for item in runtime["deferred"])

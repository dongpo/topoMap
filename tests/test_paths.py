from nma.paths import distribution_root, resolve_asset


def test_project_assets_are_discoverable() -> None:
    root = distribution_root()
    assert (root / "benchmark/manifest.json").exists()
    assert resolve_asset("data/specifications/taiwan-5000-riverl-112.json").exists()
    assert resolve_asset("data/datasets/authoritative/riverl-defective/RIVERL.shp").exists()

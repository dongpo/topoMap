from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public/nma"


def test_ui_is_prefix_safe_self_hosted_and_has_no_inline_code() -> None:
    html = (PUBLIC / "index.html").read_text(encoding="utf-8")
    assert 'src="assets/maplibre-gl-4.7.0.js"' in html
    assert 'src="assets/nma-demo.js"' in html
    assert 'href="assets/maplibre-gl-4.7.0.css"' in html
    assert "http://" not in html and "https://" not in html
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html)
    assert "<style" not in html


def test_ui_uses_dom_safe_text_and_live_maplibre_layers() -> None:
    script = (PUBLIC / "nma-demo.js").read_text(encoding="utf-8")
    assert "innerHTML" not in script
    assert ".textContent" in script
    assert "new maplibregl.Map" in script
    assert '"symbol-placement": "line"' in script
    assert "school-symbol" in script
    assert "build-hatch" in script
    assert "fetch(" in script and 'const BASE = "/nma/"' in script


def test_public_asset_allowlist_hashes_every_served_asset() -> None:
    manifest = json.loads((PUBLIC / "assets/manifest.json").read_text(encoding="utf-8"))
    assert manifest["runtime_network_dependencies"] == 0
    assert manifest["maplibre_version"] == "4.7.0"
    names = set()
    for item in manifest["assets"]:
        path = PUBLIC / item["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        names.add(item.get("public_name", Path(item["path"]).name))
    assert {"nma-demo.js", "nma-demo.css", "maplibre-gl-4.7.0.js", "school-blue.svg"}.issubset(
        names
    )


def test_nginx_policy_is_default_deny_with_bounds_headers_and_exact_routes() -> None:
    nginx = (ROOT / "deploy/nma-demo/nginx-nma-demo.conf").read_text(encoding="utf-8")
    assert "client_max_body_size 16k" in nginx
    assert "zone=nma_runs" in nginx and "rate=5r/m" in nginx
    assert "Content-Security-Policy" in nginx
    assert "Access-Control-Allow-Origin" not in nginx
    assert "location / { return 404; }" in nginx
    assert "proxy_pass everything" not in nginx
    assert "/nma/api/v1/runs/[0-9a-f]{32}" in nginx


def test_systemd_unit_is_unix_only_least_privilege_and_production_absent() -> None:
    unit = (ROOT / "deploy/nma-demo/nma-demo.service").read_text(encoding="utf-8")
    assert "User=nma-demo" in unit and "Group=nma-demo" in unit
    assert "RestrictAddressFamilies=AF_UNIX" in unit
    assert "IPAddressDeny=any" in unit
    assert "NoNewPrivileges=true" in unit
    assert "ProtectSystem=strict" in unit
    assert "ExecStartPre=" in unit
    environment = (ROOT / "deploy/nma-demo/nma-demo.env.example").read_text(encoding="utf-8")
    assert "NMA_DEMO_LLM_MODE=disabled" in environment
    assert "NMA_DEMO_BUILD_ACTIVATION=not-mounted" in environment
    assert "OPENAI_API_KEY" not in environment and "NEO4J" not in environment

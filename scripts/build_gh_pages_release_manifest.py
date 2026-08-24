from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "gh-pages"
MANIFEST = OUTPUT / "release.json"


def main() -> None:
    files = []
    for path in sorted(OUTPUT.rglob("*")):
        if not path.is_file() or path == MANIFEST:
            continue
        payload = path.read_bytes()
        files.append(
            {
                "path": path.relative_to(OUTPUT).as_posix(),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    release = {
        "schema": "nma.github-pages-static-release/2.1",
        "source_branch": "main",
        "authority_commit": "eb87bde775333811529efb6f651573ea21cf456b",
        "mode": "browser-local-user-shapefile-controlled-execution",
        "interface": "task-landing-plus-domain-locked-run",
        "domain_routes": {
            "school": "run.html?domain=school",
            "road": "run.html?domain=road",
            "build": "run.html?domain=build",
        },
        "user_file_required": True,
        "user_file_transmission": False,
        "preloaded_result_geometry": False,
        "live_agent": False,
        "private_fixture_bytes_included": False,
        "production_credentials_included": False,
        "production_activation": False,
        "files": files,
    }
    MANIFEST.write_text(
        json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

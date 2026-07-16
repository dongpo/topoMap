from __future__ import annotations

import os
import sys
from pathlib import Path


def distribution_root() -> Path:
    candidates = []
    if os.environ.get("NMA_ROOT"):
        candidates.append(Path(os.environ["NMA_ROOT"]))
    candidates.extend(
        [
            Path.cwd(),
            Path(__file__).resolve().parents[2],
            Path(sys.prefix) / "share/nma",
        ]
    )
    for candidate in candidates:
        if (candidate / "data/specifications/taiwan-5000-riverl-112.json").exists() and (
            candidate / "benchmark/manifest.json"
        ).exists():
            return candidate
    raise FileNotFoundError(
        "NMA fixtures were not found; run from the repository, install the complete wheel, "
        "or set NMA_ROOT"
    )


def resolve_asset(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute() or candidate.exists():
        return candidate
    rooted = distribution_root() / candidate
    return rooted if rooted.exists() else candidate

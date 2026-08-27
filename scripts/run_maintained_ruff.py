#!/usr/bin/env python3
"""Run Ruff on maintained Python while enforcing the immutable legacy-debt baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "config/ruff-legacy-baseline.json"
PYTHON_ROOTS = (
    "agent_contracts",
    "benchmark/adapters",
    "build_contracts",
    "scripts",
    "src",
    "tests",
)


def _digest(paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update((ROOT / relative).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_baseline() -> dict:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    format_paths = baseline["format"]["paths"]
    missing = [path for path in format_paths if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit(f"Legacy format baseline paths are missing: {missing}")
    actual_digest = _digest(format_paths)
    if actual_digest != baseline["format"]["aggregate_sha256"]:
        raise SystemExit(
            "Legacy format baseline changed. Format the touched file and remove it from the "
            "baseline; do not refresh the debt digest."
        )
    for relative, record in baseline["lint"].items():
        path = ROOT / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise SystemExit(
                f"Legacy lint baseline changed for {relative}. Resolve its recorded lint debt."
            )
    return baseline


def _python_files() -> list[str]:
    return sorted(
        path.relative_to(ROOT).as_posix()
        for root in PYTHON_ROOTS
        for path in (ROOT / root).rglob("*.py")
        if "__pycache__" not in path.parts
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "format", "baseline"))
    args = parser.parse_args()
    baseline = _load_baseline()
    if args.mode == "baseline":
        print(
            json.dumps(
                {
                    "status": "passed",
                    "format_debt_files": len(baseline["format"]["paths"]),
                    "lint_debt_files": len(baseline["lint"]),
                }
            )
        )
        return 0

    excluded = set(baseline["lint"] if args.mode == "check" else baseline["format"]["paths"])
    files = [path for path in _python_files() if path not in excluded]
    ruff = shutil.which("ruff")
    if not ruff:
        raise SystemExit("ruff is not installed")
    command = [ruff, "check"] if args.mode == "check" else [ruff, "format", "--check"]
    return subprocess.run([*command, *files], cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nma.school_hero_verification import (  # noqa: E402
    SchoolHeroVerificationError,
    SchoolHeroVerifier,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministically verify one persisted HERO-04 School Hero execution."
    )
    parser.add_argument("execution_id")
    parser.add_argument("--storage-root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument(
        "--official-symbol",
        type=Path,
        default=ROOT / "assets/symbols/nlsc112v5.4/school.svg",
    )
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--no-persist", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verifier = SchoolHeroVerifier(
        storage_root=args.storage_root,
        archive_path=args.archive,
        official_symbol_path=args.official_symbol,
        repository_root=args.repository_root,
    )
    try:
        result = verifier.verify(args.execution_id, persist=not args.no_persist)
    except SchoolHeroVerificationError as error:
        print(json.dumps({"status": "failed", "error": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())

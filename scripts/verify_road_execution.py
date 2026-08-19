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

from nma.road_verification import (  # noqa: E402
    EXECUTION_ID,
    RoadExecutionVerifier,
    RoadVerificationError,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Independently verify the persisted ROAD-04 execution and provenance."
    )
    parser.add_argument("execution_id", nargs="?", default=EXECUTION_ID)
    parser.add_argument("--storage-root", type=Path, default=ROOT / "artifacts/runtime/road")
    parser.add_argument(
        "--archive",
        type=Path,
        default=ROOT / "data/datasets/112年多維度SHP成果_0502.zip",
    )
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--visual-evidence", type=Path)
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--no-persist", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verifier = RoadExecutionVerifier(
        storage_root=args.storage_root,
        archive_path=args.archive,
        repository_root=args.repository_root,
        visual_evidence_path=args.visual_evidence,
        screenshot_path=args.screenshot,
    )
    try:
        result = verifier.verify(args.execution_id, persist=not args.no_persist)
    except RoadVerificationError as error:
        print(json.dumps({"status": "blocked", "error": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())

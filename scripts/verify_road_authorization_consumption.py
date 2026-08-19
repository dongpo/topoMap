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

from nma.road_authorization_consumption import (  # noqa: E402
    authorization_consumption_file_sha256,
    load_authorization_consumption_fixture,
)


DEFAULT_FIXTURE = (
    ROOT / "data/specifications/nma-road-hero-road-04-authorization-consumption-fixture-v1.0.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce the frozen ROAD authorization-consumption identity."
    )
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        fixture, consumption = load_authorization_consumption_fixture(args.fixture)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(
            json.dumps(
                {"status": "failed", "error": type(error).__name__, "message": str(error)},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": "verified",
                "contract_version": fixture["contract_version"],
                "fixture_sha256": fixture["fixture_sha256"],
                "idempotency_key_sha256": consumption["idempotency_key_sha256"],
                "consumption_file_sha256": authorization_consumption_file_sha256(consumption),
                "consumption": consumption,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

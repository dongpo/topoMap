#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json

from nma.agentic_freeze import check_agentic_freeze


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Agentic v0.3 candidate freeze")
    parser.add_argument(
        "--manifest",
        default="data/demo/agentic-v0.3-freeze.json",
        help="Agentic freeze manifest path",
    )
    args = parser.parse_args()
    print(json.dumps(check_agentic_freeze(args.manifest), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

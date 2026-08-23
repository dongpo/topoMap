#!/usr/bin/env python3
"""Fail-closed offline integrity gate used by nma-demo.service."""

from __future__ import annotations

import json

from nma.public_demo_gateway import PublicDemoConfig, StartupIntegrityValidator


def main() -> int:
    result = StartupIntegrityValidator(PublicDemoConfig.from_environment()).validate()
    print(json.dumps({"status": "ready", **result}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

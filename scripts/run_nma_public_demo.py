#!/usr/bin/env python3
"""Run the default-deny NMA public demo on its configured Unix socket."""

from __future__ import annotations

import logging

from nma.public_demo_gateway import PublicDemoConfig, serve_unix


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    serve_unix(PublicDemoConfig.from_environment())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify immutable NMA annotated-tag objects and their peeled commit targets."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TAGS = {
    "nma-build-v1.0-final": (
        "1b55ff67fd670a482da74975ce41fa86df5dd71f",
        "95de5fa3657a2c8ac7847f1ee1010c48ea984cd7",
    ),
    "nma-core-v0.1-baseline": (
        "d86b77392c1dc9c9edc1d4adc370fc73e7e14f75",
        "ce6e90c993cb36782da29d7e24369882eb303476",
    ),
    "nma-core-v1.0-final": (
        "5729f2db0fc441b3eb0a22c1f76b0f6af3f368ea",
        "5eb138ae7686502431587743ebce9ddf92c5a799",
    ),
    "nma-demo-v0.2-rc1": (
        "19b234164f489497e08b3d64d0ea07987b11e91c",
        "2e72262a3181e9335915026d90d9b9890d2984a0",
    ),
    "nma-demo-v1.0-final": (
        "794a71ab8fdf56c4504f85521f7a063a9acb63f9",
        "05af154a14e781f20b5cf2d3996eac8191875b0f",
    ),
    "nma-generalization-v1.0-final": (
        "9ba26ff032e23f0ba5de80d809f08eb6e973bb4f",
        "380cc6ea2a4498ce83690521c933accfd918818e",
    ),
    "nma-road-v1.0-final": (
        "d60fffa873428d1ba8b308ea0d4d2028ac8431fd",
        "325c70d5335f57c43a8af85822db25032aa225c3",
    ),
    "nma-v0.2.1-baseline": (
        "ecfd8e9e13c12c30d65a29aedb329c23d08c176c",
        "6c7eef1259bfc3001afae761a7ae47321612a709",
    ),
    "nma-v1.0-final": (
        "f710da4828cd9ebf170fb60bd6af8f81e4e7abff",
        "eb87bde775333811529efb6f651573ea21cf456b",
    ),
}


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _remote_tags(remote: str) -> dict[str, str]:
    output = _git("ls-remote", "--tags", remote)
    return {
        ref.removeprefix("refs/tags/"): object_id
        for line in output.splitlines()
        for object_id, ref in [line.split()]
    }


def verify_tags(remote: str | None = None) -> dict[str, object]:
    remote_refs = _remote_tags(remote) if remote else {}
    records = []
    for name, (expected_object, expected_target) in EXPECTED_TAGS.items():
        ref = f"refs/tags/{name}"
        actual_type = _git("cat-file", "-t", ref)
        actual_object = _git("rev-parse", ref)
        actual_target = _git("rev-parse", f"{ref}^{{}}")
        checks = {
            "annotated_tag": actual_type == "tag",
            "object_exact": actual_object == expected_object,
            "peeled_target_exact": actual_target == expected_target,
        }
        if remote:
            checks.update(
                {
                    "remote_object_exact": remote_refs.get(name) == expected_object,
                    "remote_peeled_target_exact": remote_refs.get(f"{name}^{{}}")
                    == expected_target,
                }
            )
        records.append(
            {
                "tag": name,
                "expected_object": expected_object,
                "actual_object": actual_object,
                "expected_peeled_target": expected_target,
                "actual_peeled_target": actual_target,
                "checks": checks,
                "status": "passed" if all(checks.values()) else "failed",
            }
        )
    return {
        "schema": "ama.historical-tag-integrity/1.0",
        "tag_count": len(records),
        "remote": remote,
        "status": "passed" if all(item["status"] == "passed" for item in records) else "failed",
        "tags": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remote", help="also compare tag objects and peeled targets with a remote"
    )
    args = parser.parse_args()
    result = verify_tags(args.remote)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

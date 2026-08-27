#!/usr/bin/env python3
"""NMA-Bench adapter for a local OpenAI-compatible chat-completions server."""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib import error, request


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=120)
    return parser


def _content_json(content: str) -> dict:
    value = content.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        value = "\n".join(lines[1:-1])
    parsed = json.loads(value)
    if not isinstance(parsed, dict) or "value" not in parsed:
        raise ValueError("model output must contain a value field")
    parsed.setdefault("evidence", [])
    return parsed


def main() -> int:
    args = _parser().parse_args()
    protocol_request = json.load(sys.stdin)
    if protocol_request.get("protocol") != "nma-bench-adapter/1.0":
        raise ValueError("unsupported adapter protocol")

    system_prompt = (
        "You are an evaluated national-mapping assistant. Return exactly one JSON object with "
        "keys value and evidence. The value must directly answer the task in the requested shape. "
        "Evidence is an array of source records actually supporting the answer. Use no markdown. "
        "If the supplied information is insufficient, use null for value and an empty evidence array."
    )
    user_payload = {
        "task": protocol_request["task"],
        "context_mode": protocol_request["context_mode"],
        "context": protocol_request.get("context"),
    }
    body = json.dumps(
        {
            "model": args.model,
            "temperature": args.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("NMA_MODEL_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    endpoint = args.base_url.rstrip("/") + "/chat/completions"
    try:
        with request.urlopen(
            request.Request(endpoint, data=body, headers=headers, method="POST"),
            timeout=args.timeout,
        ) as response:
            result = json.load(response)
    except error.URLError as exc:
        print(f"model endpoint failed: {exc}", file=sys.stderr)
        return 2
    output = _content_json(result["choices"][0]["message"]["content"])
    output["metadata"] = {"model": args.model, "adapter": "openai-compatible/1.0"}
    json.dump(output, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import hashlib
import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from nma.llm.base import (
    LLMAdapter,
    LLMAdapterError,
    LLMResult,
    canonical_json,
)


class OllamaAdapter(LLMAdapter):
    """Local Ollama structured-chat adapter with no cloud or credential fallback."""

    def __init__(self, *, base_url: str, model: str, timeout_seconds: float = 120.0) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username:
            raise LLMAdapterError(
                "AMA_LLM_BASE_URL must be an HTTP(S) endpoint without credentials."
            )
        if not model.strip():
            raise LLMAdapterError("AMA_LLM_MODEL must name a configured local model.")
        if timeout_seconds <= 0:
            raise LLMAdapterError("The model timeout must be positive.")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_structured(
        self,
        *,
        task: str,
        instructions: str,
        context: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> LLMResult:
        if not task.strip() or not instructions.strip():
            raise LLMAdapterError("Structured generation requires a task and instructions.")
        request_body = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a bounded mapping research proposal generator. "
                        "Return only JSON matching the supplied schema. Evidence and reviewed "
                        "candidate values are authoritative; never invent identities."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "task": task,
                            "instructions": instructions,
                            "context": context,
                            "output_schema": output_schema,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                },
            ],
        }
        request = Request(
            f"{self.base_url}/api/chat",
            data=canonical_json(request_body),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.monotonic()
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as error:
            detail = error.read(500).decode("utf-8", errors="replace")
            raise LLMAdapterError(
                f"Local Ollama rejected model {self.model!r} with HTTP {error.code}: {detail}"
            ) from error
        except (URLError, TimeoutError, OSError) as error:
            raise LLMAdapterError(
                f"Local Ollama model {self.model!r} is unavailable at {self.base_url}."
            ) from error
        latency_ms = round((time.monotonic() - started) * 1000)
        try:
            envelope = json.loads(raw)
            content = envelope["message"]["content"]
            output = json.loads(content)
        except (KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as error:
            raise LLMAdapterError(
                "Local Ollama returned an invalid structured response."
            ) from error
        if not isinstance(output, dict):
            raise LLMAdapterError("Structured model output must be a JSON object.")
        usage_values = {
            "input_tokens": envelope.get("prompt_eval_count"),
            "output_tokens": envelope.get("eval_count"),
        }
        usage = {
            key: value for key, value in usage_values.items() if isinstance(value, int)
        } or None
        return LLMResult(
            model_id=self.model,
            provider="ollama",
            output=output,
            latency_ms=latency_ms,
            usage=usage,
            raw_response_hash=hashlib.sha256(raw).hexdigest(),
        )

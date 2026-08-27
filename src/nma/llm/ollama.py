from __future__ import annotations

import hashlib
import json
import math
import time
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from nma.llm.base import (
    LLMAdapter,
    LLMAdapterError,
    LLMResult,
    canonical_json,
)


DEFAULT_CONTEXT_WINDOW = 8_192
DEFAULT_OUTPUT_TOKEN_RESERVE = 2_048
DEFAULT_TIMEOUT_SECONDS = 600.0
CHAT_TEMPLATE_TOKEN_ALLOWANCE = 256
TOKEN_ESTIMATE_SAFETY_FACTOR = 1.2


def estimate_ollama_prompt_tokens(messages: list[dict[str, str]]) -> int:
    """Estimate Qwen chat input with an explicit safety margin.

    The local Ollama API does not expose a tokenize-only endpoint. TRACE-01 and PROMPT-01 probes
    both measured approximately three UTF-8 bytes per qwen2.5 prompt token. The estimate adds a
    fixed chat-template allowance and a 20% safety factor; observed provider usage remains traced.
    """

    rendered_values = [f"{item['role']}\n{item['content']}\n" for item in messages]
    byte_count = len("".join(rendered_values).encode("utf-8"))
    base_estimate = math.ceil(byte_count / 3) + CHAT_TEMPLATE_TOKEN_ALLOWANCE
    return math.ceil(base_estimate * TOKEN_ESTIMATE_SAFETY_FACTOR)


class OllamaAdapter(LLMAdapter):
    """Local Ollama structured-chat adapter with no cloud or credential fallback."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        output_token_reserve: int = DEFAULT_OUTPUT_TOKEN_RESERVE,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username:
            raise LLMAdapterError(
                "AMA_LLM_BASE_URL must be an HTTP(S) endpoint without credentials."
            )
        if not model.strip():
            raise LLMAdapterError("AMA_LLM_MODEL must name a configured local model.")
        if timeout_seconds <= 0:
            raise LLMAdapterError("The model timeout must be positive.")
        if context_window <= 0 or output_token_reserve <= 0:
            raise LLMAdapterError("Context window and output reserve must be positive integers.")
        if output_token_reserve >= context_window:
            raise LLMAdapterError("The output reserve must be smaller than the context window.")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.context_window = context_window
        self.output_token_reserve = output_token_reserve
        self._trace_hook: Callable[[str, Mapping[str, Any]], None] | None = None

    def set_trace_hook(self, hook: Callable[[str, Mapping[str, Any]], None] | None) -> None:
        """Observe provider wire values without changing the generated request or response."""

        self._trace_hook = hook

    def _emit_trace(self, event: str, payload: Mapping[str, Any]) -> None:
        if self._trace_hook is not None:
            self._trace_hook(event, payload)

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
        messages = [
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
        ]
        prompt_token_estimate = estimate_ollama_prompt_tokens(messages)
        available_input_tokens = self.context_window - self.output_token_reserve
        fits = prompt_token_estimate <= available_input_tokens
        context_budget: dict[str, Any] = {
            "context_window": self.context_window,
            "prompt_token_estimate": prompt_token_estimate,
            "reserved_output_tokens": self.output_token_reserve,
            "available_input_tokens": available_input_tokens,
            "remaining_input_margin": available_input_tokens - prompt_token_estimate,
            "budget_status": "PASS" if fits else "FAIL",
            "fits": fits,
            "truncation_expected": not fits,
            "silent_truncation": False,
            "estimator": "qwen-utf8-byte-estimate-plus-20pct-safety/1.0",
        }
        self._emit_trace("context_budget", context_budget)
        if not fits:
            raise LLMAdapterError(
                "Ollama request exceeds the configured input budget before invocation: "
                f"estimated {prompt_token_estimate} tokens, available {available_input_tokens}."
            )
        request_body = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
                "num_ctx": self.context_window,
                "num_predict": self.output_token_reserve,
            },
            "messages": messages,
        }
        request_url = f"{self.base_url}/api/chat"
        request_bytes = canonical_json(request_body)
        request_headers = {"Content-Type": "application/json"}
        self._emit_trace(
            "request",
            {
                "url": request_url,
                "method": "POST",
                "headers": request_headers,
                "timeout_seconds": self.timeout_seconds,
                "body": request_body,
                "serialized_body_utf8": request_bytes.decode("utf-8"),
            },
        )
        request = Request(
            request_url,
            data=request_bytes,
            headers=request_headers,
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
        self._emit_trace(
            "raw_response",
            {
                "capture_stage": "immediately after response.read(), before JSON parsing",
                "raw_response_utf8": raw.decode("utf-8", errors="replace"),
                "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
                "latency_ms": latency_ms,
            },
        )
        try:
            envelope = json.loads(raw)
            self._emit_trace("response_envelope", envelope)
            observed_prompt_tokens = envelope.get("prompt_eval_count")
            if isinstance(observed_prompt_tokens, int):
                context_budget.update(
                    {
                        "observed_prompt_tokens": observed_prompt_tokens,
                        "observed_input_margin": available_input_tokens - observed_prompt_tokens,
                        "observed_within_input_budget": (
                            observed_prompt_tokens <= available_input_tokens
                        ),
                    }
                )
            self._emit_trace("context_budget_result", context_budget)
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
            context_budget=context_budget,
        )

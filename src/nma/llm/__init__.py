from __future__ import annotations

import os
from typing import Mapping

from nma.llm.base import LLMAdapter, LLMAdapterError, LLMResult
from nma.llm.ollama import (
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_OUTPUT_TOKEN_RESERVE,
    OllamaAdapter,
)


def _positive_integer_setting(values: Mapping[str, str], name: str, default: int) -> int:
    raw = values.get(name, "").strip()
    if not raw:
        return default
    try:
        parsed = int(raw)
    except ValueError as error:
        raise LLMAdapterError(f"{name} must be a positive integer.") from error
    if parsed <= 0:
        raise LLMAdapterError(f"{name} must be a positive integer.")
    return parsed


def adapter_from_environment(*, environ: dict[str, str] | None = None) -> LLMAdapter:
    values = os.environ if environ is None else environ
    provider = values.get("AMA_LLM_PROVIDER", "").strip().casefold()
    base_url = values.get("AMA_LLM_BASE_URL", "").strip()
    model = values.get("AMA_LLM_MODEL", "").strip()
    missing = [
        name
        for name, value in (
            ("AMA_LLM_PROVIDER", provider),
            ("AMA_LLM_BASE_URL", base_url),
            ("AMA_LLM_MODEL", model),
        )
        if not value
    ]
    if missing:
        raise LLMAdapterError("Missing local model configuration: " + ", ".join(missing))
    if provider == "ollama":
        return OllamaAdapter(
            base_url=base_url,
            model=model,
            context_window=_positive_integer_setting(
                values, "AMA_LLM_CONTEXT_WINDOW", DEFAULT_CONTEXT_WINDOW
            ),
            output_token_reserve=_positive_integer_setting(
                values, "AMA_LLM_OUTPUT_TOKEN_RESERVE", DEFAULT_OUTPUT_TOKEN_RESERVE
            ),
        )
    raise LLMAdapterError(f"Unsupported AMA_LLM_PROVIDER: {provider!r}; no fallback is allowed.")


__all__ = [
    "LLMAdapter",
    "LLMAdapterError",
    "LLMResult",
    "OllamaAdapter",
    "adapter_from_environment",
]

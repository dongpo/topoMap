from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping


_SHA256 = re.compile(r"[0-9a-f]{64}")


class LLMAdapterError(RuntimeError):
    """A provider-neutral model request or response failed closed."""


def canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise LLMAdapterError("The model contract requires canonical JSON values.") from error


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


@dataclass(frozen=True)
class LLMResult:
    """Only provider-neutral, observable model result fields owned by AMA."""

    model_id: str
    provider: str
    output: dict[str, Any]
    latency_ms: int
    usage: dict[str, int] | None
    raw_response_hash: str
    context_budget: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.model_id.strip() or not self.provider.strip():
            raise LLMAdapterError("Model results require provider and model identities.")
        if self.latency_ms < 0:
            raise LLMAdapterError("Model latency cannot be negative.")
        if self.usage is not None and any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in self.usage.values()
        ):
            raise LLMAdapterError("Model usage values must be non-negative integers.")
        if _SHA256.fullmatch(self.raw_response_hash) is None:
            raise LLMAdapterError("The raw model response hash is malformed.")
        if self.context_budget is not None and not isinstance(self.context_budget, dict):
            raise LLMAdapterError("Model context budget metadata must be a dictionary.")

    def to_trace(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model_id": self.model_id,
            "latency_ms": self.latency_ms,
            "usage": self.usage,
            "raw_response_hash": self.raw_response_hash,
            "context_budget": self.context_budget,
        }


class LLMAdapter(ABC):
    """Replaceable structured-generation boundary for the AMA research runtime.

    Implementations may translate this request into provider-specific wire messages, but no
    response, tool-call, session, or continuation identity crosses this interface.
    """

    @abstractmethod
    def generate_structured(
        self,
        *,
        task: str,
        instructions: str,
        context: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> LLMResult:
        raise NotImplementedError


def validate_json_schema_subset(
    value: object, schema: Mapping[str, Any], *, path: str = "$"
) -> None:
    """Validate the closed JSON-schema subset used at the model trust boundary.

    The runtime deliberately has no mandatory third-party dependency. Unsupported schema
    keywords fail closed instead of being silently ignored.
    """

    supported = {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "enum",
        "const",
        "minItems",
        "maxItems",
        "minLength",
        "maxLength",
    }
    unknown = set(schema) - supported
    if unknown:
        raise LLMAdapterError(f"Unsupported output-schema keywords at {path}: {sorted(unknown)}")
    if "const" in schema and value != schema["const"]:
        raise LLMAdapterError(f"Model output at {path} does not match the required constant.")
    if "enum" in schema and value not in schema["enum"]:
        raise LLMAdapterError(f"Model output at {path} is outside the allowed values.")

    expected = schema.get("type")
    if expected is not None:
        allowed = [expected] if isinstance(expected, str) else list(expected)
        observed = (
            "null"
            if value is None
            else "boolean"
            if isinstance(value, bool)
            else "integer"
            if isinstance(value, int)
            else "number"
            if isinstance(value, float)
            else "string"
            if isinstance(value, str)
            else "array"
            if isinstance(value, list)
            else "object"
            if isinstance(value, Mapping)
            else "unsupported"
        )
        compatible = observed in allowed or (observed == "integer" and "number" in allowed)
        if not compatible:
            raise LLMAdapterError(
                f"Model output at {path} has type {observed}; expected {allowed}."
            )

    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        missing = required - set(value)
        if missing:
            raise LLMAdapterError(f"Model output at {path} is missing fields: {sorted(missing)}")
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise LLMAdapterError(
                    f"Model output at {path} contains unsupported fields: {sorted(extra)}"
                )
        for key, item in value.items():
            if key in properties:
                validate_json_schema_subset(item, properties[key], path=f"{path}.{key}")
    elif isinstance(value, list):
        minimum = schema.get("minItems")
        maximum = schema.get("maxItems")
        if minimum is not None and len(value) < minimum:
            raise LLMAdapterError(f"Model output at {path} has too few items.")
        if maximum is not None and len(value) > maximum:
            raise LLMAdapterError(f"Model output at {path} has too many items.")
        if "items" in schema:
            for index, item in enumerate(value):
                validate_json_schema_subset(item, schema["items"], path=f"{path}[{index}]")
    elif isinstance(value, str):
        minimum = schema.get("minLength")
        maximum = schema.get("maxLength")
        if minimum is not None and len(value) < minimum:
            raise LLMAdapterError(f"Model output at {path} is too short.")
        if maximum is not None and len(value) > maximum:
            raise LLMAdapterError(f"Model output at {path} is too long.")

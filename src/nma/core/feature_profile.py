"""Thin, domain-neutral feature-profile contract."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping


def _freeze_json(value: Any, *, location: str) -> Any:
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{location} keys must be strings")
            frozen[key] = _freeze_json(item, location=f"{location}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_json(item, location=f"{location}[{index}]") for index, item in enumerate(value)
        )
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{location} must not contain non-finite numbers")
        return value
    raise TypeError(f"{location} contains a non-JSON-compatible value")


def _freeze_payload(value: Mapping[str, Any], *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    return _freeze_json(value, location=field_name)


@dataclass(frozen=True, slots=True)
class FeatureProfile:
    """An immutable compatibility view over a feature implementation.

    Payload meanings belong to each feature adapter. Core only guarantees a geometry
    role/type and recursively immutable, JSON-compatible payloads.
    """

    geometry_role: str
    identity_payload: Mapping[str, Any]
    source_scope_payload: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.geometry_role, str) or not self.geometry_role.strip():
            raise ValueError("geometry_role must be a non-empty string")
        if not self.identity_payload:
            raise ValueError("identity_payload must not be empty")
        if not self.source_scope_payload:
            raise ValueError("source_scope_payload must not be empty")
        object.__setattr__(
            self,
            "identity_payload",
            _freeze_payload(self.identity_payload, field_name="identity_payload"),
        )
        object.__setattr__(
            self,
            "source_scope_payload",
            _freeze_payload(self.source_scope_payload, field_name="source_scope_payload"),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze_payload(self.metadata, field_name="metadata"),
        )

"""Minimal deterministic identity primitives for NMA contracts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def canonical_json(value: Any) -> bytes:
    """Serialize a JSON-compatible value to canonical, Unicode-preserving UTF-8 bytes."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the lowercase SHA-256 digest of a value's canonical JSON bytes."""

    return hashlib.sha256(canonical_json(value)).hexdigest()


def validate_sha256(value: str) -> str:
    """Return a strict lowercase SHA-256 digest or reject it."""

    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError("sha256 must contain exactly 64 lowercase hexadecimal characters")
    return value


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """An immutable, domain-neutral reference to a content-addressed artifact."""

    id: str
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("id must be a non-empty string")
        validate_sha256(self.sha256)

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from nma.road_resolution import canonical_json, canonical_sha256


FIXTURE_SCHEMA = "nma.road-authorization-consumption-fixture/1.0"
CONTRACT_VERSION = "road-05a-authorization-consumption/1.0"
CONSUMPTION_SCHEMA = "nma.road-authorization-consumption/1.0"
CANONICAL_SERIALIZATION = {
    "idempotency_key": "exact UTF-8 bytes; no Unicode normalization or line terminator",
    "consumption_record": (
        "UTF-8 JSON; keys sorted lexicographically; separators ',' and ':'; "
        "ensure_ascii=false; one trailing LF"
    ),
}
HASHING = {
    "algorithm": "SHA-256",
    "idempotency_input": "inputs.idempotency_key exact UTF-8 bytes",
    "consumption_input": "canonical persisted consumption_record bytes",
}
INPUT_FIELDS = {
    "authorization_id",
    "authorization_sha256",
    "execution_id",
    "idempotency_key",
    "receipt_id",
    "receipt_sha256",
}


def _require_exact_fields(value: Mapping[str, Any], expected: set[str], name: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{name} fields do not match the {CONTRACT_VERSION} contract.")


def authorization_consumption_fixture_sha256(fixture: Mapping[str, Any]) -> str:
    """Return the canonical identity of a fixture, excluding its self-hash field."""

    basis = dict(fixture)
    basis.pop("fixture_sha256", None)
    return canonical_sha256(basis)


def authorization_consumption_file_sha256(consumption: Mapping[str, Any]) -> str:
    """Return the SHA-256 identity of canonical persisted consumption bytes."""

    return hashlib.sha256(canonical_json(consumption) + b"\n").hexdigest()


def authorization_consumption_from_fixture(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct and validate the frozen consumption record from tracked inputs only."""

    _require_exact_fields(
        fixture,
        {
            "schema",
            "contract_version",
            "consumption_schema",
            "inputs",
            "canonical_serialization",
            "hashing",
            "expected_idempotency_key_sha256",
            "expected_consumption_file_sha256",
            "fixture_sha256",
        },
        "fixture",
    )
    if (
        fixture["schema"] != FIXTURE_SCHEMA
        or fixture["contract_version"] != CONTRACT_VERSION
        or fixture["consumption_schema"] != CONSUMPTION_SCHEMA
        or fixture["canonical_serialization"] != CANONICAL_SERIALIZATION
        or fixture["hashing"] != HASHING
    ):
        raise ValueError("Authorization-consumption fixture contract metadata is invalid.")

    inputs = fixture["inputs"]
    if not isinstance(inputs, Mapping):
        raise ValueError("Authorization-consumption fixture inputs must be an object.")
    _require_exact_fields(inputs, INPUT_FIELDS, "inputs")
    idempotency_key = inputs["idempotency_key"]
    if not isinstance(idempotency_key, str) or not 8 <= len(idempotency_key) <= 160:
        raise ValueError("The canonical idempotency key is invalid.")

    idempotency_key_sha256 = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
    consumption = {
        "schema": CONSUMPTION_SCHEMA,
        "authorization_id": inputs["authorization_id"],
        "authorization_sha256": inputs["authorization_sha256"],
        "execution_id": inputs["execution_id"],
        "idempotency_key_sha256": idempotency_key_sha256,
        "receipt_id": inputs["receipt_id"],
        "receipt_sha256": inputs["receipt_sha256"],
    }
    consumption_file_sha256 = authorization_consumption_file_sha256(consumption)
    if idempotency_key_sha256 != fixture["expected_idempotency_key_sha256"]:
        raise ValueError("The canonical idempotency-key identity does not match the fixture.")
    if consumption_file_sha256 != fixture["expected_consumption_file_sha256"]:
        raise ValueError("The canonical consumption-file identity does not match the fixture.")
    if fixture["fixture_sha256"] != authorization_consumption_fixture_sha256(fixture):
        raise ValueError("The authorization-consumption fixture identity is invalid.")
    return consumption


def load_authorization_consumption_fixture(
    path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load a canonical fixture and return it with its reconstructed consumption record."""

    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(fixture, dict):
        raise ValueError("Authorization-consumption fixture must be a JSON object.")
    return fixture, authorization_consumption_from_fixture(fixture)

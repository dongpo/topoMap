from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from nma.core.identity import ArtifactReference, canonical_json, canonical_sha256
from nma.road_resolution import canonical_json as road_canonical_json
from nma.road_resolution import canonical_sha256 as road_canonical_sha256
from nma.school_hero_execution import canonical_json as school_canonical_json
from nma.school_hero_execution import canonical_sha256 as school_canonical_sha256


@pytest.mark.parametrize(
    "payload",
    [
        {"中文": "中山街", "ascii": "school"},
        {"z": [True, False, None], "a": {"integer": 7, "float": 2.5}},
        {"nested": [{"b": 2, "a": 1}], "array": [3, 2, 1]},
    ],
)
def test_canonical_serialization_and_hash_parity(payload: object) -> None:
    expected_bytes = school_canonical_json(payload)

    assert canonical_json(payload) == expected_bytes
    assert road_canonical_json(payload) == expected_bytes
    assert canonical_sha256(payload) == school_canonical_sha256(payload)
    assert canonical_sha256(payload) == road_canonical_sha256(payload)


def test_canonical_json_uses_sorted_keys_compact_separators_and_utf8() -> None:
    assert canonical_json({"b": 2, "中": "文", "a": 1}) == (
        b'{"a":1,"b":2,"\xe4\xb8\xad":"\xe6\x96\x87"}'
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_values_fail_consistently(value: float) -> None:
    payload = {"value": value}

    with pytest.raises(ValueError):
        canonical_json(payload)
    with pytest.raises(ValueError):
        school_canonical_json(payload)
    with pytest.raises(ValueError):
        road_canonical_json(payload)


def test_artifact_reference_accepts_strict_sha256_and_is_immutable() -> None:
    reference = ArtifactReference(id="artifact-1", sha256="a" * 64)

    assert reference.id == "artifact-1"
    assert reference.sha256 == "a" * 64
    with pytest.raises(FrozenInstanceError):
        reference.id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "digest",
    [
        "A" * 64,
        "a" * 63,
        "g" * 64,
    ],
)
def test_artifact_reference_rejects_invalid_sha256(digest: str) -> None:
    with pytest.raises(ValueError):
        ArtifactReference(id="artifact-1", sha256=digest)


def test_artifact_reference_rejects_empty_id() -> None:
    with pytest.raises(ValueError):
        ArtifactReference(id="", sha256="a" * 64)

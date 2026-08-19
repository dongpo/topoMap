from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

import nma.core as core
import nma.road_approval as road03
import nma.road_execution as road04
import nma.road_portrayal_decision as road02
import nma.road_resolution as road01


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "nma-core-v0.1-baseline"
GOLDEN_REQUEST = (
    "Resolve County Highway 126 / 中山街 in the reviewed K14 road dataset and prepare "
    "the evidence-grounded road portrayal package for the exact contiguous source segment set."
)
CORE_IMMUTABLE_PATHS = (
    "src/nma/core/__init__.py",
    "src/nma/core/identity.py",
    "src/nma/core/feature_profile.py",
    "src/nma/feature_profile_adapters.py",
)


def _load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_road_provider_exports_are_exact_core_functions() -> None:
    assert road01.canonical_json is core.canonical_json
    assert road01.canonical_sha256 is core.canonical_sha256


def test_downstream_road_hash_consumers_adopt_core_transitively() -> None:
    assert road02.canonical_sha256 is core.canonical_sha256
    assert road03.canonical_sha256 is core.canonical_sha256
    assert road04.canonical_sha256 is core.canonical_sha256


def test_unicode_nested_payload_keeps_exact_canonical_bytes_and_hash() -> None:
    payload = {
        "unicode": "中山街",
        "nested": {"z": [True, False, None], "a": {"integer": 7, "float": 2.5}},
        "array": [3, {"b": 2, "a": 1}],
    }
    reordered = {
        "array": [3, {"a": 1, "b": 2}],
        "nested": {"a": {"float": 2.5, "integer": 7}, "z": [True, False, None]},
        "unicode": "中山街",
    }
    expected = (
        b'{"array":[3,{"a":1,"b":2}],"nested":{"a":{"float":2.5,"integer":7},'
        b'"z":[true,false,null]},"unicode":"\xe4\xb8\xad\xe5\xb1\xb1\xe8\xa1\x97"}'
    )

    assert road01.canonical_json(payload) == expected
    assert road01.canonical_json(reordered) == expected
    assert road01.canonical_sha256(payload) == core.canonical_sha256(reordered)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_values_still_fail_closed(value: float) -> None:
    with pytest.raises(ValueError):
        road01.canonical_json({"value": value})


def test_frozen_road01_through_road03_identities_remain_exact() -> None:
    package = road01.resolve_road_request(GOLDEN_REQUEST)
    proposal = _load("data/specifications/nma-road-hero-road-02-golden-proposal-v1.0.json")
    decision = _load("data/specifications/nma-road-hero-road-02-golden-decision-v1.0.json")
    approval = _load("data/specifications/nma-road-hero-road-03-golden-approval-v1.0.json")
    authorization = _load(
        "data/specifications/nma-road-hero-road-03-golden-authorization-v1.0.json"
    )

    assert road01.package_sha256(package) == (
        "b5df3f57c33843f354371206c937f52d37ddbbd9d047a31ad7c334532ce30e9a"
    )
    assert road02.proposal_sha256(proposal) == (
        "3d45d1ed039c2af1aa7f050fa1e3c22158c891390c001285054b05a02959ce06"
    )
    assert road02.decision_sha256(decision) == (
        "0d671b1fed3f4b19e4204e745bdcb13f872f3a00dcb4ef5050a091a14065e090"
    )
    assert road03.approval_sha256(approval) == (
        "f333defee511e0ae82702444d18befe2f9e115d75608ab61a5c20f91c52f2f07"
    )
    assert road03.authorization_sha256(authorization) == (
        "f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38"
    )


@pytest.mark.parametrize("relative_path", CORE_IMMUTABLE_PATHS)
def test_core_source_is_byte_identical_to_baseline(relative_path: str) -> None:
    baseline_bytes = subprocess.check_output(
        ["git", "show", f"{BASELINE}:{relative_path}"], cwd=ROOT
    )

    assert (ROOT / relative_path).read_bytes() == baseline_bytes

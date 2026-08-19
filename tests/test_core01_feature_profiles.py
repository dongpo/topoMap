from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from nma.core.feature_profile import FeatureProfile
from nma.feature_profile_adapters import road_feature_profile, school_feature_profile
from nma.road_resolution import EXPECTED_FEATURE_IDS, EXPECTED_IDENTITY
from nma.school_hero_execution import (
    REAL_LAYER_PROFILES,
    SCHOOL_FEATURE_CODE,
    SCHOOL_GEOMETRY,
    SCHOOL_PROFILE_ID,
)


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_CORE_LITERALS = {
    "school-point",
    "9920103",
    "中山街",
    "9420400",
    "K0000004671",
    "K0000004913",
    "K0000005348",
}


def test_school_adapter_preserves_frozen_identity_and_scope() -> None:
    profile = school_feature_profile()
    frozen = REAL_LAYER_PROFILES[SCHOOL_PROFILE_ID]

    assert profile.geometry_role == SCHOOL_GEOMETRY == "Point"
    assert profile.identity_payload == {
        "profile_id": SCHOOL_PROFILE_ID,
        "feature_code": SCHOOL_FEATURE_CODE,
    }
    assert profile.identity_payload["profile_id"] == "school-point"
    assert profile.identity_payload["feature_code"] == "9920103"
    assert profile.source_scope_payload == {
        "product_layer": frozen["product_layer"],
        "source_layer_ids": tuple(frozen["source_layer_ids"]),
    }


def test_road_adapter_preserves_frozen_identity_scope_and_order() -> None:
    profile = road_feature_profile()

    assert profile.geometry_role == "LineString"
    assert profile.identity_payload == {
        "class_code": EXPECTED_IDENTITY["class_code"],
        "canonical_route_identity": EXPECTED_IDENTITY["canonical_identity"],
    }
    assert profile.identity_payload["class_code"] == "9420400"
    assert profile.identity_payload["canonical_route_identity"] == (
        "ROADNUM=縣126|ROADNUM1=|ROADNUM2=|ROADNAME=中山街"
    )
    assert profile.metadata["road_name"] == "中山街"
    assert profile.source_scope_payload["ordered_segment_ids"] == EXPECTED_FEATURE_IDS
    assert profile.source_scope_payload["ordered_segment_ids"] == (
        "K0000004671",
        "K0000004913",
        "K0000005348",
    )


def test_profile_payloads_are_defensively_and_recursively_immutable() -> None:
    identity = {"kind": "example", "nested": {"revision": 1}}
    source_scope = {"sources": [{"id": "source-1"}]}
    profile = FeatureProfile(
        geometry_role="ExampleGeometry",
        identity_payload=identity,
        source_scope_payload=source_scope,
    )

    identity["nested"]["revision"] = 2  # type: ignore[index]
    source_scope["sources"][0]["id"] = "changed"  # type: ignore[index]
    assert profile.identity_payload["nested"]["revision"] == 1
    assert profile.source_scope_payload["sources"][0]["id"] == "source-1"

    with pytest.raises(TypeError):
        profile.identity_payload["kind"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        profile.identity_payload["nested"]["revision"] = 3  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        profile.geometry_role = "Changed"  # type: ignore[misc]


def test_core_contains_no_frozen_domain_literals_or_implementation_imports() -> None:
    core_root = ROOT / "src/nma/core"
    sources = {path: path.read_text(encoding="utf-8") for path in core_root.glob("*.py")}
    combined = "\n".join(sources.values())

    assert not [literal for literal in FORBIDDEN_CORE_LITERALS if literal in combined]

    imported_names: set[str] = set()
    for source in sources.values():
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names.add(node.module)
                imported_names.update(f"{node.module}.{alias.name}" for alias in node.names)
    assert not [
        name
        for name in imported_names
        if name == "nma.school_hero_execution" or name.startswith("nma.road_")
    ]


def test_contract_accepts_future_domain_payloads_without_core_changes() -> None:
    profile = FeatureProfile(
        geometry_role="FutureGeometry",
        identity_payload={"provider_key": "future-1"},
        source_scope_payload={"catalog": {"namespace": "future"}},
        metadata={"capabilities": ["opaque-capability"]},
    )

    assert profile.identity_payload["provider_key"] == "future-1"
    assert profile.metadata["capabilities"] == ("opaque-capability",)

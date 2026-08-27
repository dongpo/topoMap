"""BUILD-owned Core FeatureProfile adapter for the accepted entry fixture."""

from __future__ import annotations

from build_contracts.fixture import load_build_fixture_manifest
from nma.core import FeatureProfile


def build_feature_profile() -> FeatureProfile:
    """Expose BUILD fixture identity and scope without granting execution authority."""

    manifest = load_build_fixture_manifest()
    fixture = manifest["fixture"]
    selection = manifest["selection"]
    source = manifest["source"]
    return FeatureProfile(
        geometry_role=fixture["canonical_geometry_role"],
        identity_payload={
            "fixture_id": manifest["fixture_id"],
            "feature_code": selection["feature_code"],
        },
        source_scope_payload={
            "archive_sha256": source["archive_sha256"],
            "layer_id": fixture["layer_id"],
            "component_sha256": {
                item["extension"]: item["sha256"] for item in fixture["components"]
            },
        },
        metadata={
            "feature_name": selection["feature_name"],
            "purpose": manifest["boundaries"]["purpose"],
            "execution_authorized": False,
        },
    )


__all__ = ["build_feature_profile"]

"""Read-only compatibility views over the frozen School and Road Heroes."""

from __future__ import annotations

from nma.core.feature_profile import FeatureProfile
from nma import road_resolution
from nma import school_hero_execution


def school_feature_profile() -> FeatureProfile:
    """Expose the frozen School Hero identity and source scope without changing execution."""

    profile = school_hero_execution.REAL_LAYER_PROFILES[school_hero_execution.SCHOOL_PROFILE_ID]
    return FeatureProfile(
        geometry_role=school_hero_execution.SCHOOL_GEOMETRY,
        identity_payload={
            "profile_id": school_hero_execution.SCHOOL_PROFILE_ID,
            "feature_code": school_hero_execution.SCHOOL_FEATURE_CODE,
        },
        source_scope_payload={
            "product_layer": profile["product_layer"],
            "source_layer_ids": profile["source_layer_ids"],
        },
        metadata={"feature_name": profile["feature_name"]},
    )


def road_feature_profile() -> FeatureProfile:
    """Expose the frozen Road Hero identity and ordered source scope without execution."""

    identity = road_resolution.EXPECTED_IDENTITY
    return FeatureProfile(
        geometry_role="LineString",
        identity_payload={
            "class_code": identity["class_code"],
            "canonical_route_identity": identity["canonical_identity"],
        },
        source_scope_payload={
            "profile": "K14",
            "layer": "K14_ROAD",
            "ordered_segment_ids": road_resolution.EXPECTED_FEATURE_IDS,
        },
        metadata={
            "class_name": identity["class_name"],
            "route_number": identity["route_number"],
            "road_name": identity["road_name"],
        },
    )


__all__ = ["road_feature_profile", "school_feature_profile"]

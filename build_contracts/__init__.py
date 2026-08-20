"""BUILD-owned, non-executing entry contracts."""

from build_contracts.feature_profile import build_feature_profile
from build_contracts.fixture import (
    BuildFixtureError,
    fixture_identity,
    load_build_fixture_manifest,
    validate_build_fixture_manifest,
)

__all__ = [
    "BuildFixtureError",
    "build_feature_profile",
    "fixture_identity",
    "load_build_fixture_manifest",
    "validate_build_fixture_manifest",
]

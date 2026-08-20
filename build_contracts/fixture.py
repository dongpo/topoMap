"""BUILD fixture contract for the BUILD-01 entry boundary.

This module validates fixture identity and scope only. It intentionally exposes no
authorization, execution, mutation, repair, or runtime-wiring capability.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from nma.core import canonical_sha256, validate_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = ROOT / "data/specifications/nma-build-fixture-manifest-v1.0.json"
MANIFEST_SCHEMA = "nma.build-fixture-manifest/1.0"
FIXTURE_ID_PREFIX = "build-fixture:sha256:"
CORE_FREEZE_SHA = "5eb138ae7686502431587743ebce9ddf92c5a799"
CORE_FREEZE_TAG = "nma-core-v1.0-final"
EXPECTED_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
EXPECTED_FIXTURE_ID = (
    "build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a"
)
EXPECTED_CANDIDATES = (
    "J01_BUILD",
    "J13_BUILD",
    "J17_BUILD",
    "K01_BUILD",
    "K02_BUILD",
    "K14_BUILD",
)
SELECTED_LAYER_ID = "J13_BUILD"
SELECTED_FEATURE_CODE = "9310100"
REQUIRED_COMPONENTS = (".cpg", ".dbf", ".prj", ".shp", ".shx")


class BuildFixtureError(ValueError):
    """The BUILD fixture crossed its accepted read-only boundary."""


def fixture_identity(manifest: Mapping[str, Any]) -> str:
    """Return the full Core-owned content identity, excluding only the self-identity."""

    if not isinstance(manifest, Mapping):
        raise TypeError("BUILD fixture manifest must be a mapping")
    basis = {key: value for key, value in manifest.items() if key != "fixture_id"}
    return FIXTURE_ID_PREFIX + canonical_sha256(basis)


def validate_build_fixture_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the closed fixture identity, selection, Core link, and non-execution boundary."""

    if not isinstance(manifest, Mapping):
        raise BuildFixtureError("A BUILD fixture manifest object is required.")
    value = deepcopy(dict(manifest))
    expected_keys = {
        "$schema",
        "schema",
        "fixture_id",
        "status",
        "source",
        "selection",
        "candidates",
        "fixture",
        "core_identity",
        "boundaries",
    }
    if set(value) != expected_keys:
        raise BuildFixtureError("The BUILD fixture manifest fields are not closed.")
    if value.get("schema") != MANIFEST_SCHEMA:
        raise BuildFixtureError("The BUILD fixture manifest schema is unsupported.")
    if value.get("status") != "accepted-build-01-entry-fixture":
        raise BuildFixtureError("The BUILD fixture is not accepted for the BUILD-01 entry gate.")
    if (
        value.get("fixture_id") != EXPECTED_FIXTURE_ID
        or value.get("fixture_id") != fixture_identity(value)
    ):
        raise BuildFixtureError("The BUILD fixture content identity does not match Core identity.")

    source = value.get("source")
    if not isinstance(source, dict) or source.get("archive_sha256") != EXPECTED_ARCHIVE_SHA256:
        raise BuildFixtureError("The BUILD source archive is not the accepted private archive.")
    validate_sha256(source["archive_sha256"])
    if source.get("redistributed") is not False or source.get("tracked") is not False:
        raise BuildFixtureError("The private BUILD source must remain untracked and unredistributed.")

    selection = value.get("selection")
    if not isinstance(selection, dict) or selection.get("selected_layer_id") != SELECTED_LAYER_ID:
        raise BuildFixtureError("The canonical BUILD source layer changed.")
    if selection.get("feature_code") != SELECTED_FEATURE_CODE:
        raise BuildFixtureError("The canonical BUILD feature code changed.")

    candidates = value.get("candidates")
    if not isinstance(candidates, list):
        raise BuildFixtureError("The BUILD candidate comparison is required.")
    candidate_ids = tuple(item.get("layer_id") for item in candidates if isinstance(item, dict))
    if candidate_ids != EXPECTED_CANDIDATES:
        raise BuildFixtureError("The BUILD candidate comparison changed or is incomplete.")
    accepted = [item for item in candidates if item.get("decision") == "accepted"]
    if len(accepted) != 1 or accepted[0].get("layer_id") != SELECTED_LAYER_ID:
        raise BuildFixtureError("Exactly J13_BUILD must be the accepted fixture candidate.")

    fixture = value.get("fixture")
    if not isinstance(fixture, dict) or fixture.get("layer_id") != SELECTED_LAYER_ID:
        raise BuildFixtureError("The BUILD fixture scope changed.")
    if fixture.get("source_geometry_type") != "PolygonZ":
        raise BuildFixtureError("The accepted source geometry must remain PolygonZ.")
    if fixture.get("canonical_geometry_role") != "Polygon":
        raise BuildFixtureError("The BUILD Core geometry role must remain Polygon.")
    if fixture.get("feature_count") != 2968 or fixture.get("selected_feature_count") != 2962:
        raise BuildFixtureError("The BUILD fixture population changed.")
    components = fixture.get("components")
    if not isinstance(components, list):
        raise BuildFixtureError("The BUILD fixture component hashes are required.")
    extensions = tuple(item.get("extension") for item in components if isinstance(item, dict))
    if extensions != REQUIRED_COMPONENTS:
        raise BuildFixtureError("The BUILD fixture component inventory changed.")
    for component in components:
        validate_sha256(component.get("sha256"))

    core = value.get("core_identity")
    if core != {
        "owner": "nma.core",
        "freeze_tag": CORE_FREEZE_TAG,
        "freeze_sha": CORE_FREEZE_SHA,
        "identity_provider": "canonical_sha256",
        "feature_profile_provider": "FeatureProfile",
    }:
        raise BuildFixtureError("The frozen Core identity/provider binding changed.")

    boundaries = value.get("boundaries")
    required_false = {
        "source_mutation_allowed",
        "geometry_repair_allowed",
        "z_dimension_drop_authorized",
        "execution_authorized",
        "runtime_wiring_authorized",
        "redistribution_authorized",
    }
    if not isinstance(boundaries, dict) or any(boundaries.get(key) is not False for key in required_false):
        raise BuildFixtureError("The BUILD fixture cannot grant mutation, execution, or publication.")
    if boundaries.get("purpose") != "build-01-entry-readiness-only":
        raise BuildFixtureError("The BUILD fixture purpose changed.")
    return value


def load_build_fixture_manifest(path: str | Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    source = Path(path)
    value = json.loads(source.read_text(encoding="utf-8"))
    return validate_build_fixture_manifest(value)


__all__ = [
    "BuildFixtureError",
    "DEFAULT_MANIFEST_PATH",
    "EXPECTED_ARCHIVE_SHA256",
    "SELECTED_FEATURE_CODE",
    "SELECTED_LAYER_ID",
    "fixture_identity",
    "load_build_fixture_manifest",
    "validate_build_fixture_manifest",
]

"""BUILD-06 independent verification and DEMO-only freeze.

This module reads only the redacted BUILD-05 package, its independent
consumption ledger, and the static BUILD-06 presentation.  It has no private
archive path, source reader, execution function, or production runtime hook.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

from nma.core import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_PATH = (
    ROOT / "data/specifications/nma-build-05-golden-execution-package-v1.0.json"
)
DEFAULT_LEDGER_PATH = (
    ROOT / "data/specifications/nma-build-05-authorization-consumption-v1.0.json"
)
DEFAULT_PRESENTATION_PATH = ROOT / "buildDemoV06.html"
VERIFICATION_SCHEMA = "nma.build-demo-verification-freeze/1.0"
VERIFICATION_VERSION = "build-06/1.0"
VERIFICATION_ID = "build-06-verification-10c22339abb8d2ee"
EXPECTED_PREDECESSOR_SHA = "290625111ab7a4ecb8af41be168ca186d55d949c"
EXPECTED_PACKAGE_FILE_SHA256 = (
    "508e3378a698f869255485c5008fdb80ed670ce174a3b72092aab5160df7431c"
)
EXPECTED_LEDGER_FILE_SHA256 = (
    "715a5445827b77308ec32a67efe74ac8e5ed29b9037ee543285270a4da1c9d47"
)
EXPECTED_PRESENTATION_FILE_SHA256 = (
    "de5f6d567810e42af915bdff167fb21e202967b98817e2ef8d2d494d0b47be2d"
)
EXPECTED_PACKAGE_SHA256 = (
    "10c22339abb8d2eed489ae56a54214948213bad51a135e00f74e309931c98c97"
)
EXPECTED_ARTIFACT_SHA256 = (
    "9131df533365e2f42e01edb8988804b850b65e69b932c55b672e0addd3400d84"
)
EXPECTED_CONSUMPTION_SHA256 = (
    "44ab99947d9cb196de6a4f5a5238b4af33eb306a911a104224774425c7ebb108"
)
EXPECTED_RECEIPT_SHA256 = (
    "c4ff4017c01aa3ef861530a91204fcd8357387a8400f4a47fcd637033f445573"
)
EXPECTED_VERIFICATION_SHA256 = (
    "bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857"
)

BOUNDARIES = {
    "build05_authorization_reconsumed": False,
    "build05_execution_repeated": False,
    "private_source_accessed": False,
    "private_source_required": False,
    "normalized_artifact_only": True,
    "raw_geographic_coordinates_disclosed": False,
    "raw_attributes_disclosed": False,
    "network_dependency_added": False,
    "production_runtime_wired": False,
    "production_activated": False,
    "demo_policy_promoted": False,
}

KNOWN_BASELINE_FAILURES = [
    "tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible",
    "tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries",
    "tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate",
]


class BuildDemoFreezeError(ValueError):
    """BUILD-06 rejected drift, disclosure, replay, or authority expansion."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildDemoFreezeError(message, code=code)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise BuildDemoFreezeError(
            f"The BUILD-06 input is unavailable: {path.name}.", code="input_unavailable"
        ) from error
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BuildDemoFreezeError(
            f"The BUILD-06 JSON input is invalid: {path.name}.", code="input_invalid"
        ) from error
    if not isinstance(value, dict):
        _fail("The BUILD-06 JSON input must be an object.", "input_invalid")
    return value


def _record_sha256(value: Mapping[str, Any], field: str) -> str:
    basis = deepcopy(dict(value))
    basis.pop(field, None)
    return canonical_sha256(basis)


def verification_sha256(value: Mapping[str, Any]) -> str:
    return _record_sha256(value, "verification_sha256")


def _require_exact_fields(
    value: Mapping[str, Any], expected: set[str], label: str
) -> None:
    if set(value) != expected:
        _fail(f"The BUILD-06 {label} fields changed.", "input_invalid")


def _validate_coordinates(coordinates: Any) -> list[list[float]]:
    if (
        not isinstance(coordinates, list)
        or len(coordinates) != 1
        or not isinstance(coordinates[0], list)
        or len(coordinates[0]) != 65
    ):
        _fail("The normalized DEMO polygon structure changed.", "privacy_boundary_mismatch")
    ring = coordinates[0]
    for coordinate in ring:
        if (
            not isinstance(coordinate, list)
            or len(coordinate) != 2
            or any(
                isinstance(number, bool)
                or not isinstance(number, (int, float))
                or not math.isfinite(number)
                or not 0.0 <= number <= 1.0
                for number in coordinate
            )
        ):
            _fail("The normalized DEMO coordinates changed.", "privacy_boundary_mismatch")
    if ring[0] != ring[-1]:
        _fail("The normalized DEMO ring is not closed.", "privacy_boundary_mismatch")
    return deepcopy(ring)


def _verify_package(package: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_fields(
        package,
        {
            "package_version",
            "schema_version",
            "execution_id",
            "authorization_id",
            "authorization_sha256",
            "resolution_sha256",
            "plan_sha256",
            "demo_artifact",
            "consumption_record",
            "receipt",
            "boundaries",
            "package_sha256",
        },
        "package",
    )
    if (
        package.get("package_version") != "build-05/1.0"
        or package.get("schema_version") != "nma.build-demo-execution-package/1.0"
        or package.get("package_sha256") != EXPECTED_PACKAGE_SHA256
        or _record_sha256(package, "package_sha256") != EXPECTED_PACKAGE_SHA256
    ):
        _fail("The BUILD-05 package identity changed.", "package_identity_mismatch")
    artifact = package.get("demo_artifact")
    consumption = package.get("consumption_record")
    receipt = package.get("receipt")
    if not all(isinstance(value, Mapping) for value in (artifact, consumption, receipt)):
        _fail("The BUILD-05 internal records are invalid.", "input_invalid")
    if (
        artifact.get("artifact_sha256") != EXPECTED_ARTIFACT_SHA256
        or _record_sha256(artifact, "artifact_sha256") != EXPECTED_ARTIFACT_SHA256
        or consumption.get("consumption_sha256") != EXPECTED_CONSUMPTION_SHA256
        or _record_sha256(consumption, "consumption_sha256")
        != EXPECTED_CONSUMPTION_SHA256
        or receipt.get("receipt_sha256") != EXPECTED_RECEIPT_SHA256
        or _record_sha256(receipt, "receipt_sha256") != EXPECTED_RECEIPT_SHA256
    ):
        _fail("The BUILD-05 internal identity chain changed.", "record_identity_mismatch")
    if (
        consumption.get("status") != "consumed-once"
        or consumption.get("replay_allowed") is not False
        or consumption.get("artifact_sha256") != EXPECTED_ARTIFACT_SHA256
        or receipt.get("artifact_sha256") != EXPECTED_ARTIFACT_SHA256
        or receipt.get("consumption_sha256") != EXPECTED_CONSUMPTION_SHA256
    ):
        _fail("The BUILD-05 consumption chain changed.", "consumption_mismatch")
    privacy = artifact.get("privacy")
    if privacy != {
        "coordinate_space": "normalized-local-demo-not-geographic",
        "raw_geographic_coordinates_included": False,
        "raw_attributes_included": False,
        "annotation_value_included": False,
        "derived_normalized_shape_included": True,
    }:
        _fail("The BUILD-05 privacy boundary changed.", "privacy_boundary_mismatch")
    try:
        feature = artifact["maplibre_demo"]["source"]["data"]["features"][0]
        controls = artifact["maplibre_demo"]["controls"]
        source_commitments = artifact["source_commitments"]
    except (KeyError, IndexError, TypeError) as error:
        raise BuildDemoFreezeError(
            "The BUILD-05 DEMO artifact structure changed.",
            code="input_invalid",
        ) from error
    ring = _validate_coordinates(feature.get("geometry", {}).get("coordinates"))
    if (
        feature.get("properties")
        != {
            "feature_code": "9310100",
            "display_annotation": "樓層＋結構",
            "annotation_value_sha256": (
                "17460f383142153fa58b587a2d3902b6cdbbcddb663d151cf28ce86bc6149a52"
            ),
        }
        or source_commitments.get("source_geometry_type") != "PolygonZ"
        or source_commitments.get("source_vertex_count") != 65
        or controls
        != {
            "hatch_angle_degrees": {
                "minimum_inclusive": 0.0,
                "maximum_exclusive": 180.0,
                "default": 45.0,
                "step": 1.0,
                "user_adjustable": True,
                "demo_only": True,
            }
        }
    ):
        _fail("The BUILD-05 DEMO semantics changed.", "semantic_mismatch")
    serialized = json.dumps(package, ensure_ascii=False).casefold()
    forbidden = (
        "geometry_wkb_hex",
        '"build_id"',
        '"build_no"',
        '"build_str"',
        "build04-demo-default-45-v1",
    )
    if any(token in serialized for token in forbidden):
        _fail("The BUILD-05 package discloses a forbidden source value.", "disclosure_detected")
    return {
        "ring_count": 1,
        "vertex_count": len(ring),
        "coordinate_dimensions": 2,
        "coordinate_space": privacy["coordinate_space"],
        "source_geometry_commitment": source_commitments[
            "geometry_commitment_sha256"
        ],
        "source_attribute_commitment": source_commitments[
            "attribute_commitment_sha256"
        ],
    }


def _verify_presentation(path: Path) -> dict[str, Any]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise BuildDemoFreezeError(
            "The BUILD-06 DEMO presentation is unavailable.", code="input_unavailable"
        ) from error
    required = (
        "DEMO ONLY · 非正式圖式",
        "type=\"range\" min=\"0\" max=\"179\" step=\"1\" value=\"45\"",
        "normalized-local-demo-not-geographic",
        EXPECTED_PACKAGE_FILE_SHA256,
        EXPECTED_LEDGER_FILE_SHA256,
        EXPECTED_PACKAGE_SHA256,
        EXPECTED_CONSUMPTION_SHA256,
        "default-src 'self'",
    )
    if any(token not in source for token in required):
        _fail("The BUILD-06 DEMO presentation contract changed.", "presentation_mismatch")
    if "http://" in source or "https://" in source:
        _fail("The BUILD-06 DEMO added a network dependency.", "network_dependency_detected")
    forbidden = (
        "geometry_wkb_hex",
        '"BUILD_ID"',
        '"BUILD_NO"',
        '"BUILD_STR"',
        "112年多維度SHP成果_0502.zip",
    )
    if any(token in source for token in forbidden):
        _fail("The BUILD-06 DEMO references private source data.", "disclosure_detected")
    return {
        "mode": "offline-static-svg-presentation",
        "clearly_labeled_demo_only": True,
        "external_network_dependencies": 0,
        "private_source_dependencies": 0,
        "default_hatch_angle_degrees": 45.0,
        "user_adjustable_hatch_angle": True,
        "angle_range": {
            "minimum_inclusive": 0.0,
            "maximum_exclusive": 180.0,
            "step": 1.0,
        },
    }


def build_build_demo_verification_freeze(
    *,
    package_path: str | Path = DEFAULT_PACKAGE_PATH,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
    presentation_path: str | Path = DEFAULT_PRESENTATION_PATH,
) -> dict[str, Any]:
    """Independently verify and freeze existing redacted BUILD-05 artifacts."""

    package_file = Path(package_path)
    ledger_file = Path(ledger_path)
    presentation_file = Path(presentation_path)
    package_file_sha = _file_sha256(package_file)
    ledger_file_sha = _file_sha256(ledger_file)
    presentation_file_sha = _file_sha256(presentation_file)
    if package_file_sha != EXPECTED_PACKAGE_FILE_SHA256:
        _fail("The BUILD-05 package file changed.", "package_file_mismatch")
    if ledger_file_sha != EXPECTED_LEDGER_FILE_SHA256:
        _fail("The BUILD-05 ledger file changed.", "ledger_file_mismatch")
    if presentation_file_sha != EXPECTED_PRESENTATION_FILE_SHA256:
        _fail("The BUILD-06 presentation file changed.", "presentation_file_mismatch")
    package = _load_json(package_file)
    ledger = _load_json(ledger_file)
    artifact_evidence = _verify_package(package)
    if ledger != package["consumption_record"]:
        _fail("The independent consumption ledger changed.", "ledger_mismatch")
    if (
        ledger.get("consumption_sha256") != EXPECTED_CONSUMPTION_SHA256
        or _record_sha256(ledger, "consumption_sha256")
        != EXPECTED_CONSUMPTION_SHA256
        or ledger.get("status") != "consumed-once"
        or ledger.get("replay_allowed") is not False
    ):
        _fail("The BUILD-04 authorization is not frozen as consumed.", "ledger_mismatch")
    presentation = _verify_presentation(presentation_file)
    manifest: dict[str, Any] = {
        "verification_version": VERIFICATION_VERSION,
        "schema_version": VERIFICATION_SCHEMA,
        "verification_id": VERIFICATION_ID,
        "status": "accepted-frozen-demo-only",
        "verified_on": "2026-08-20",
        "predecessor": {
            "branch": "build/build-05-controlled-demo-execution",
            "commit_sha": EXPECTED_PREDECESSOR_SHA,
            "package_sha256": EXPECTED_PACKAGE_SHA256,
        },
        "inputs": {
            "execution_package": {
                "path": (
                    "data/specifications/"
                    "nma-build-05-golden-execution-package-v1.0.json"
                ),
                "file_sha256": package_file_sha,
                "record_sha256": EXPECTED_PACKAGE_SHA256,
            },
            "consumption_ledger": {
                "path": (
                    "data/specifications/"
                    "nma-build-05-authorization-consumption-v1.0.json"
                ),
                "file_sha256": ledger_file_sha,
                "record_sha256": EXPECTED_CONSUMPTION_SHA256,
            },
            "presentation": {
                "path": "buildDemoV06.html",
                "file_sha256": presentation_file_sha,
            },
        },
        "independent_verification": {
            "execution_package_identity": "PASS",
            "artifact_identity": "PASS",
            "consumption_identity": "PASS",
            "receipt_identity": "PASS",
            "ledger_equality": "PASS",
            "replay_blocked": "PASS",
            "normalized_geometry": "PASS",
            "privacy_boundary": "PASS",
            "source_commitments_retained": "PASS",
            "presentation_contract": "PASS",
            "artifact_evidence": artifact_evidence,
        },
        "presentation": presentation,
        "boundaries": deepcopy(BOUNDARIES),
        "known_pre_existing_failures": deepcopy(KNOWN_BASELINE_FAILURES),
        "freeze_policy": {
            "immutable": True,
            "authorization_reuse_allowed": False,
            "source_reexecution_allowed": False,
            "production_activation_allowed": False,
            "demo_policy_promotion_allowed": False,
            "allowed_follow_up": (
                "verify or present this exact normalized DEMO artifact without source access"
            ),
            "change_requires_new_human_gate": True,
        },
    }
    manifest["verification_sha256"] = verification_sha256(manifest)
    return manifest


def validate_build_demo_verification_freeze(
    manifest: Mapping[str, Any],
    *,
    package_path: str | Path = DEFAULT_PACKAGE_PATH,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
    presentation_path: str | Path = DEFAULT_PRESENTATION_PATH,
) -> dict[str, Any]:
    """Validate an exact BUILD-06 freeze against independently rechecked inputs."""

    if not isinstance(manifest, Mapping):
        _fail("The BUILD-06 freeze must be an object.", "freeze_invalid")
    expected = build_build_demo_verification_freeze(
        package_path=package_path,
        ledger_path=ledger_path,
        presentation_path=presentation_path,
    )
    if dict(manifest) != expected:
        _fail("The BUILD-06 freeze differs from independent verification.", "freeze_mismatch")
    actual_sha = verification_sha256(manifest)
    if manifest.get("verification_sha256") != actual_sha:
        _fail("The BUILD-06 freeze hash is invalid.", "freeze_hash_mismatch")
    if EXPECTED_VERIFICATION_SHA256 is not None and actual_sha != EXPECTED_VERIFICATION_SHA256:
        _fail("The BUILD-06 freeze is not the accepted exact record.", "freeze_hash_mismatch")
    return deepcopy(dict(manifest))


__all__ = [
    "BuildDemoFreezeError",
    "EXPECTED_VERIFICATION_SHA256",
    "build_build_demo_verification_freeze",
    "validate_build_demo_verification_freeze",
    "verification_sha256",
]

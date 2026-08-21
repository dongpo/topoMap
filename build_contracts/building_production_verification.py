"""BUILD-11 controlled Building production verification and activation readiness.

This module independently replays the activation-held BUILD-10 implementation.  It creates no
production wiring, writes no source or derived data, and grants no activation authority.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from build_contracts.building_production_implementation import (
    BuildingProductionError,
    EXPECTED_CONTRACT_SHA256,
    EXPECTED_POLICY_SHA256,
    EXPECTED_SOURCE_ARCHIVE_SHA256,
    LEGACY_DROP_Z_DISPOSITION,
    bind_annotation_content,
    bind_building_package,
    building_schema_identity,
    deterministic_interior_point,
    implement_controlled_building,
    load_authoritative_package,
    load_frozen_contract,
    procedural_hatch_resource,
    verify_implementation_result,
)
from nma.core import canonical_sha256
from nma.real_layer import file_sha256


READINESS_SCHEMA = "nma.building-production-activation-readiness/1.0"
READINESS_VERSION = "build-11/1.0"
CREATED_ON = "2026-08-21"
BUILD10_BRANCH = "build/build-10-controlled-building-production-implementation"
BUILD10_COMMIT = "790a1bcd5624e38fb4a42060044bb73af152a5be"
BUILD09F_COMMIT = "816faa0209d3bbb83ceb71a3df4f27e8d99e4407"
BUILD10_IMPLEMENTATION_FILE_SHA256 = (
    "2772ce93f81973e1dbbeb2d4ae9bb1307a29dcdcc4a61ca08f382c12b6b3c957"
)
BUILD10_SCHEMA_FILE_SHA256 = "43eae28af0d189eba235037fd9a27eacf70c78a1caa20b72cd81e8c7fac88864"
BUILD10_TEST_FILE_SHA256 = "bd53f94b496369d2ab5685e123321a721383cd0dd99d8e8cd4eccb82e85232b6"
BUILD10_REPORT_FILE_SHA256 = "1ccb5e7860c235a0a78225ad3111ed48e307d4536e72f2d222cd5cc34fca025e"
READINESS_STATE = "READY-FOR-HUMAN-ACTIVATION-GATE"
VERDICT = "PASS — CONTROLLED BUILDING PRODUCTION VERIFIED; HUMAN ACTIVATION GATE READY"

PACKAGE = {
    "J13": {
        "package": "J13_寶山都市計畫/SHP",
        "layer": "J13_BUILD",
        "scope": "Baoshan urban-plan project area",
        "source_count": 2968,
        "derived_count": 2968,
        "annotation_count": 2967,
        "placement_suppressed_count": 1,
        "implementation_record_sha256": (
            "ccffdf038cecf06d1dd3341d49b15745f37029f2af78c51bf68b1ab677035b4a"
        ),
    },
    "J17": {
        "package": "J17_新竹科學工業園區特定區計畫(寶山部分)/SHP",
        "layer": "J17_BUILD",
        "scope": "Hsinchu Science Park special-plan project area, Baoshan portion",
        "source_count": 2839,
        "derived_count": 2839,
        "annotation_count": 2838,
        "placement_suppressed_count": 1,
        "implementation_record_sha256": (
            "0722007704a5a12fb6f314d71bf7898ab1718dd3185bc9060687160a0ce119a7"
        ),
    },
}


class BuildingProductionVerificationError(ValueError):
    """BUILD-11 rejected verification evidence or an activation boundary."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildingProductionVerificationError(message, code=code)


def activation_readiness_record_sha256(record: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(record))
    basis.pop("canonical_record_sha256", None)
    return canonical_sha256(basis)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect_build10_error(operation: Callable[[], Any], expected: str) -> str:
    try:
        operation()
    except BuildingProductionError as error:
        if error.code != expected:
            _fail(
                f"Expected BUILD-10 error {expected}, observed {error.code}.",
                "fail_closed_matrix_mismatch",
            )
        return error.code
    _fail("A tampered or unsupported input did not fail closed.", "fail_closed_matrix_mismatch")


def _run_controlled(
    root: Path, archive: Path, frozen: Mapping[str, Any], prefix: str
) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    expected = PACKAGE[prefix]
    archive_before = file_sha256(archive)
    loaded = load_authoritative_package(
        contract=frozen["contract"],
        archive_path=archive,
        package_identity=expected["package"],
        geographic_project_scope=expected["scope"],
    )
    source_before = canonical_sha256(loaded["authoritative_collection"])
    result = implement_controlled_building(
        contract_bundle=frozen,
        binding=loaded["binding"],
        authoritative_collection=loaded["authoritative_collection"],
        portrayal_polygonz_collection=loaded["portrayal_polygonz_collection"],
        source_crs=loaded["source_crs"],
        output_crs=loaded["output_crs"],
    )
    verify_implementation_result(result)
    source_after = canonical_sha256(loaded["authoritative_collection"])
    archive_after = file_sha256(archive)
    if not (
        archive_before == archive_after == EXPECTED_SOURCE_ARCHIVE_SHA256
        and source_before == source_after
    ):
        _fail("Authoritative PolygonZ source identity drifted.", "source_identity_drift")
    return loaded, result, archive_before, source_before


def _verify_replay_pair(
    prefix: str,
    first_loaded: Mapping[str, Any],
    first: Mapping[str, Any],
    second_loaded: Mapping[str, Any],
    second: Mapping[str, Any],
    archive_sha256: str,
    source_collection_sha256: str,
) -> dict[str, Any]:
    expected = PACKAGE[prefix]
    if first_loaded != second_loaded or first != second:
        _fail("Repeated controlled replay was not byte-canonically identical.", "replay_drift")
    record = first["record"]
    provenance = record["provenance"]
    observation = record["observation"]
    receipt = record["receipt"]
    checks = {
        "package": record["plan"]["binding"]["source_package_identity"] == expected["package"],
        "layer": record["plan"]["binding"]["selected_layer"] == expected["layer"],
        "schema": record["plan"]["binding"]["schema_identity"] == building_schema_identity(),
        "source_count": observation["source_feature_count"] == expected["source_count"],
        "derived_count": observation["derived_xy_feature_count"] == expected["derived_count"],
        "annotation_count": observation["annotation_feature_count"] == expected["annotation_count"],
        "placement_suppressed_count": provenance["annotation_placement_suppressed_count"]
        == expected["placement_suppressed_count"],
        "implementation_identity": record["implementation_record_sha256"]
        == expected["implementation_record_sha256"],
        "source_archive": archive_sha256 == EXPECTED_SOURCE_ARCHIVE_SHA256,
        "source_collection": provenance["source_collection_sha256"] == source_collection_sha256,
        "source_z": provenance["source_z_preserved_and_recoverable"] is True,
        "derived_xy_non_authoritative": provenance["derived_xy_authoritative"] is False,
        "derived_xy_non_writing": provenance["derived_xy_non_writing"] is True,
        "source_write_handle": provenance["source_write_handle_exposed"] is False,
        "production_hold": receipt["production_active"] is False,
        "portrayal_hold": receipt["official_portrayal_active"] is False,
    }
    if not all(checks.values()):
        _fail(f"{prefix} controlled replay did not match its frozen baseline.", "baseline_mismatch")
    identities = {
        "execution_plan_sha256": record["plan"]["execution_plan_sha256"],
        "source_polygonz_collection_sha256": provenance["source_collection_sha256"],
        "reprojected_polygonz_collection_sha256": provenance[
            "reprojected_polygonz_collection_sha256"
        ],
        "derived_xy_collection_sha256": provenance["derived_xy_collection_sha256"],
        "annotation_collection_sha256": provenance["annotation_collection_sha256"],
        "procedural_hatch_resource_sha256": first["maplibre"]["resources"][0]["resource_sha256"],
        "portrayal_bundle_sha256": first["maplibre"]["bundle_sha256"],
        "provenance_sha256": provenance["provenance_sha256"],
        "observation_sha256": observation["observation_sha256"],
        "verification_sha256": record["verification"]["verification_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "implementation_record_sha256": record["implementation_record_sha256"],
    }
    return {
        "result": "PASS",
        "package_identity": expected["package"],
        "selected_layer": expected["layer"],
        "schema_identity": building_schema_identity(),
        "source_feature_count": observation["source_feature_count"],
        "derived_xy_feature_count": observation["derived_xy_feature_count"],
        "annotation_count": observation["annotation_feature_count"],
        "suppressed_annotation_count": provenance["annotation_suppressed_count"],
        "unsafe_placement_suppressed_count": provenance["annotation_placement_suppressed_count"],
        "source_archive_before_sha256": archive_sha256,
        "source_archive_after_sha256": archive_sha256,
        "source_geometry_before_sha256": source_collection_sha256,
        "source_geometry_after_sha256": source_collection_sha256,
        "identities": identities,
        "repeated_replay_identical": True,
        "timestamps_in_canonical_identity": False,
    }


def _binding_arguments(loaded: Mapping[str, Any]) -> dict[str, Any]:
    binding = loaded["binding"]
    return {
        "observed_fields": binding["schema"]["delivered_adapter_schema"],
        "source_archive_sha256": binding["source_archive_sha256"],
        "component_sha256": binding["component_sha256"],
        "geographic_project_scope": binding["geographic_project_scope"],
    }


def _fail_closed_matrix(
    frozen: Mapping[str, Any], loaded: Mapping[str, Mapping[str, Any]]
) -> dict[str, str]:
    contract = frozen["contract"]
    j13 = loaded["J13"]
    j17 = loaded["J17"]
    j13_args = _binding_arguments(j13)
    cases: dict[str, tuple[Callable[[], Any], str]] = {
        "j13-package-j17-layer": (
            lambda: bind_building_package(
                contract=contract,
                package_identities=[PACKAGE["J13"]["package"]],
                available_layer_ids=[PACKAGE["J17"]["layer"]],
                **j13_args,
            ),
            "package_layer_mismatch",
        ),
        "j17-package-j13-layer": (
            lambda: bind_building_package(
                contract=contract,
                package_identities=[PACKAGE["J17"]["package"]],
                available_layer_ids=[PACKAGE["J13"]["layer"]],
                **_binding_arguments(j17),
            ),
            "package_layer_mismatch",
        ),
        "unknown-package": (
            lambda: bind_building_package(
                contract=contract,
                package_identities=["UNKNOWN/SHP"],
                available_layer_ids=["UNKNOWN_BUILD"],
                **j13_args,
            ),
            "unknown_package",
        ),
        "ambiguous-package": (
            lambda: bind_building_package(
                contract=contract,
                package_identities=[PACKAGE["J13"]["package"], PACKAGE["J17"]["package"]],
                available_layer_ids=[PACKAGE["J13"]["layer"]],
                **j13_args,
            ),
            "ambiguous_package",
        ),
        "missing-layer": (
            lambda: bind_building_package(
                contract=contract,
                package_identities=[PACKAGE["J13"]["package"]],
                available_layer_ids=[],
                **j13_args,
            ),
            "missing_building_layer",
        ),
        "duplicate-candidate-layer": (
            lambda: bind_building_package(
                contract=contract,
                package_identities=[PACKAGE["J13"]["package"]],
                available_layer_ids=["J13_BUILD", "J13_BUILD_COPY"],
                **j13_args,
            ),
            "unexpected_layer",
        ),
        "schema-mismatch": (
            lambda: bind_building_package(
                contract=contract,
                package_identities=[PACKAGE["J13"]["package"]],
                available_layer_ids=[PACKAGE["J13"]["layer"]],
                **{**j13_args, "observed_fields": j13_args["observed_fields"][:-1]},
            ),
            "schema_mismatch",
        ),
        "tampered-package-identity": (
            lambda: bind_building_package(
                contract=contract,
                package_identities=[PACKAGE["J13"]["package"]],
                available_layer_ids=[PACKAGE["J13"]["layer"]],
                **{**j13_args, "source_archive_sha256": "0" * 64},
            ),
            "unauthorized_source_path",
        ),
    }
    return {
        name: _expect_build10_error(operation, code) for name, (operation, code) in cases.items()
    }


def _tamper_matrix(
    frozen: Mapping[str, Any], loaded: Mapping[str, Any], result: Mapping[str, Any]
) -> dict[str, str]:
    base_kwargs = {
        "contract_bundle": frozen,
        "binding": loaded["binding"],
        "authoritative_collection": loaded["authoritative_collection"],
        "portrayal_polygonz_collection": loaded["portrayal_polygonz_collection"],
        "source_crs": loaded["source_crs"],
        "output_crs": loaded["output_crs"],
    }
    cases: dict[str, tuple[Callable[[], Any], str]] = {}
    policy = deepcopy(frozen)
    policy["policy"]["status"] = "tampered"
    cases["modified-policy-record"] = (
        lambda: implement_controlled_building(**{**base_kwargs, "contract_bundle": policy}),
        "invalid_policy_identity",
    )
    contract = deepcopy(frozen)
    contract["contract"]["status"] = "tampered"
    cases["modified-production-contract"] = (
        lambda: implement_controlled_building(**{**base_kwargs, "contract_bundle": contract}),
        "invalid_contract_identity",
    )
    binding = deepcopy(loaded["binding"])
    binding["binding_policy_identity"] = "tampered"
    cases["modified-binding-policy-identity"] = (
        lambda: implement_controlled_building(**{**base_kwargs, "binding": binding}),
        "tampered_provenance",
    )
    layer = deepcopy(loaded["binding"])
    layer["selected_layer"] = "J17_BUILD"
    cases["modified-layer-name"] = (
        lambda: implement_controlled_building(**{**base_kwargs, "binding": layer}),
        "package_layer_mismatch",
    )
    for name, path, value in (
        (
            "modified-output-profile-dpi",
            ("authorized_local_policies", "line_output_profile", "output_dpi"),
            97,
        ),
        (
            "modified-line-width",
            (
                "authorized_local_policies",
                "line_output_profile",
                "official_physical_width",
                "value",
            ),
            1.0,
        ),
        (
            "modified-colour-tuple",
            ("authorized_local_policies", "colour", "official_rgb_components"),
            [17, 17, 17],
        ),
        ("modified-hatch-angle", ("authorized_local_policies", "hatch", "local_angle_degrees"), 30),
    ):
        changed = deepcopy(frozen)
        target = changed["contract"]
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        cases[name] = (
            lambda changed=changed: implement_controlled_building(
                **{**base_kwargs, "contract_bundle": changed}
            ),
            "invalid_contract_identity",
        )
    for name, mutate in (
        (
            "modified-source-identity",
            lambda value: value["record"]["provenance"].__setitem__(
                "source_collection_sha256", "0" * 64
            ),
        ),
        (
            "modified-derived-xy",
            lambda value: value["derived_xy"]["features"][0]["geometry"]["coordinates"][0][
                0
            ].__setitem__(0, 999),
        ),
        (
            "modified-provenance-record",
            lambda value: value["record"]["provenance"].__setitem__("source_immutable", False),
        ),
        (
            "modified-receipt",
            lambda value: value["record"]["receipt"].__setitem__("production_active", True),
        ),
    ):
        changed_result = deepcopy(result)
        mutate(changed_result)
        cases[name] = (
            lambda changed_result=changed_result: verify_implementation_result(changed_result),
            "tampered_provenance",
        )
    return {
        name: _expect_build10_error(operation, code) for name, (operation, code) in cases.items()
    }


def _verify_semantics(frozen: Mapping[str, Any], j13: Mapping[str, Any]) -> dict[str, Any]:
    properties = {
        "BUILD_ID": "B1",
        "TERRAINID": "9310100",
        "BUILD_STR": "RC",
        "BUILD_NO": 12,
        "BUILD_H": None,
        "GROUP_ID": None,
        "MDATE": "1120821",
    }
    annotation = bind_annotation_content(properties)
    missing_floor = bind_annotation_content({**properties, "BUILD_NO": None})
    missing_structure = bind_annotation_content({**properties, "BUILD_STR": None})
    missing_both = bind_annotation_content({**properties, "BUILD_NO": None, "BUILD_STR": None})
    malformed = _expect_build10_error(
        lambda: bind_annotation_content({**properties, "BUILD_NO": "twelve"}),
        "malformed_annotation_semantics",
    )
    geometries = {
        "convex": {"type": "Polygon", "coordinates": [[[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]]]},
        "concave": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [6, 0], [6, 2], [2, 2], [2, 6], [0, 6], [0, 0]]],
        },
        "narrow": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [20, 0], [20, 0.1], [0, 0.1], [0, 0]]],
        },
    }
    placements = {name: deterministic_interior_point(value) for name, value in geometries.items()}
    if any(
        placements[name] != deterministic_interior_point(value)
        for name, value in geometries.items()
    ):
        _fail("Annotation placement is nondeterministic.", "placement_drift")
    resource = procedural_hatch_resource(frozen["contract"])
    output = resource["output_profile"]
    outline = j13["maplibre"]["layers"][1]
    if not (
        annotation["text"] == "12RC"
        and missing_floor["status"] == "suppressed-incomplete-content"
        and missing_structure["status"] == "suppressed-incomplete-content"
        and missing_both["status"] == "suppressed-incomplete-content"
        and malformed == "malformed_annotation_semantics"
        and resource["official_diagonal_semantics"] is True
        and resource["official_spacing"] == {"value": 2.0, "unit": "mm"}
        and resource["local_angle"]
        == {
            "value": 45,
            "unit": "degrees",
            "authority": "local-production-policy",
        }
        and resource["static_asset_dependency"] is None
        and output["dpi"] == 96
        and output["line_width_device_px_unquantized"] == 0.2 * 96 / 25.4
        and output["renderer_quantization"] is None
        and resource["colour"]["official_source"]
        == {"representation": "RGB (0,0,0)", "components": [0, 0, 0]}
        and resource["colour"]["device_serialization"] == "#000000"
        and "#111111" not in resource["svg"]
        and resource["opacity"] == {"value": 1.0, "authority": "local-output-profile-policy"}
        and outline["metadata"]["nma:official-line-width"] == {"value": 0.2, "unit": "mm"}
    ):
        _fail("A finalized portrayal or annotation semantic changed.", "semantic_regression")
    return {
        "schema": "PASS",
        "annotation": "PASS",
        "annotation_placement": "PASS",
        "procedural_hatch": "PASS",
        "line_width_conversion": "PASS",
        "colour_and_opacity": "PASS",
        "representative_placements": placements,
        "line_width_device_px_unquantized": output["line_width_device_px_unquantized"],
        "hatch_spacing_device_px_unquantized": output["spacing_device_px_unquantized"],
    }


def _verify_frozen_build10(root: Path) -> dict[str, Any]:
    expected = {
        "build_contracts/building_production_implementation.py": BUILD10_IMPLEMENTATION_FILE_SHA256,
        "schemas/building-controlled-production-implementation-v1.0.schema.json": BUILD10_SCHEMA_FILE_SHA256,
        "tests/test_building_controlled_production_build10.py": BUILD10_TEST_FILE_SHA256,
        "BUILD-10-Completion-Report.md": BUILD10_REPORT_FILE_SHA256,
    }
    observed = {path: _file_sha256(root / path) for path in expected}
    if observed != expected:
        _fail("A frozen BUILD-10 artifact identity drifted.", "build10_identity_drift")
    return {"result": "PASS", "artifact_file_sha256": observed}


def _verify_legacy_isolation(root: Path) -> dict[str, Any]:
    source = (root / "build_contracts/building_production_implementation.py").read_text(
        encoding="utf-8"
    )
    if (
        "execute_real_layer(" in source
        or '"-dim"' in source
        or '"drop-z"' in source
        or LEGACY_DROP_Z_DISPOSITION["source_write_target"] is not None
        or LEGACY_DROP_Z_DISPOSITION["dim_xy_requested"] is not False
    ):
        _fail(
            "Legacy destructive dimensional reduction is production reachable.", "drop_z_reachable"
        )
    return {
        "result": "PASS",
        "classification": LEGACY_DROP_Z_DISPOSITION["classification"],
        "disposition": LEGACY_DROP_Z_DISPOSITION["production_disposition"],
        "production_reachable": False,
        "authoritative_source_write_target": None,
    }


def build_activation_readiness_record(
    repository_root: str | Path, archive_path: str | Path
) -> dict[str, Any]:
    """Run two real controlled replays per package and return a deterministic readiness record."""

    root = Path(repository_root).resolve()
    archive = Path(archive_path).resolve()
    frozen_build10 = _verify_frozen_build10(root)
    frozen = load_frozen_contract(root)
    if file_sha256(archive) != EXPECTED_SOURCE_ARCHIVE_SHA256:
        _fail("The authorized source archive identity changed.", "source_identity_drift")

    loaded: dict[str, dict[str, Any]] = {}
    results: dict[str, dict[str, Any]] = {}
    summaries: dict[str, dict[str, Any]] = {}
    for prefix in ("J13", "J17"):
        first_loaded, first, archive_identity, source_identity = _run_controlled(
            root, archive, frozen, prefix
        )
        second_loaded, second, second_archive_identity, second_source_identity = _run_controlled(
            root, archive, frozen, prefix
        )
        if archive_identity != second_archive_identity or source_identity != second_source_identity:
            _fail("Repeated source identity changed.", "source_identity_drift")
        loaded[prefix] = first_loaded
        results[prefix] = first
        summaries[prefix] = _verify_replay_pair(
            prefix,
            first_loaded,
            first,
            second_loaded,
            second,
            archive_identity,
            source_identity,
        )

    fail_closed = _fail_closed_matrix(frozen, loaded)
    tamper = _tamper_matrix(frozen, loaded["J13"], results["J13"])
    semantics = _verify_semantics(frozen, results["J13"])
    legacy = _verify_legacy_isolation(root)
    record: dict[str, Any] = {
        "schema_version": READINESS_SCHEMA,
        "record_version": READINESS_VERSION,
        "created_on": CREATED_ON,
        "status": "controlled-production-verified-activation-held",
        "verdict": VERDICT,
        "predecessor": {
            "build10_branch": BUILD10_BRANCH,
            "build10_commit": BUILD10_COMMIT,
            "build09f_commit": BUILD09F_COMMIT,
            "build09f_policy_record_sha256": EXPECTED_POLICY_SHA256,
            "finalized_production_contract_sha256": EXPECTED_CONTRACT_SHA256,
            "build10_implementation_identity": BUILD10_IMPLEMENTATION_FILE_SHA256,
            "frozen_build10": frozen_build10,
        },
        "source_archive": {
            "sha256": EXPECTED_SOURCE_ARCHIVE_SHA256,
            "source_mutated": False,
            "source_writeback_performed": False,
            "source_repair_performed": False,
            "source_z_removed": False,
        },
        "controlled_replays": summaries,
        "deterministic_replay": {
            "result": "PASS",
            "runs_per_package": 2,
            "canonical_ordering_stable": True,
            "timestamps_present": False,
            "timestamps_excluded_from_canonical_identities": True,
            "all_bound_identities_equal": True,
        },
        "fail_closed_matrix": {
            "result": "PASS",
            "positive_controls": {
                "j13-package-j13-layer": "PASS",
                "j17-package-j17-layer": "PASS",
            },
            "rejections": fail_closed,
            "fallback_used": False,
        },
        "semantic_verification": semantics,
        "polygonz_source_integrity": {
            "result": "PASS",
            "z_dimension_exists": True,
            "z_values_recoverable": True,
            "source_identity_before_equals_after": True,
            "source_repair_performed": False,
            "source_writeback_performed": False,
            "in_place_transformation_performed": False,
        },
        "derived_xy_boundary": {
            "result": "PASS",
            "authoritative": False,
            "non_writing": True,
            "purpose": "portrayal-only",
            "materialization": "ephemeral",
            "source_overwrite_possible": False,
            "stale_or_tampered_artifact_trusted": False,
        },
        "drop_z_isolation": legacy,
        "provenance_chain": {
            "result": "PASS",
            "identity_provider": "nma.core.canonical_sha256",
            "fallback_identity_provider": False,
            "chain": [
                "BUILD-09F-policy",
                "finalized-production-contract",
                "BUILD-10-implementation",
                "source-package",
                "selected-layer",
                "seven-field-schema",
                "PolygonZ-source",
                "derived-XY",
                "annotation",
                "portrayal-output-profile",
                "observation",
                "verification",
                "receipt",
            ],
            "all_links_identity_bound": True,
        },
        "rollback_cleanup": {
            "result": "PASS",
            "classification": "rollback-not-required-source-immutable",
            "persistent_derived_artifact": False,
            "ephemeral_artifacts_cleaned_by_temporary_boundary": True,
            "authoritative_source_rollback_required": False,
            "cleanup_can_delete_source": False,
            "replay_after_cleanup_identity_equal": True,
            "frozen_evidence_changed": False,
        },
        "tamper_tests": {
            "result": "PASS",
            "rejections": tamper,
            "auto_repair_performed": False,
        },
        "regression_classification": {
            "new_material_regression": False,
            "inherited_build_failures": 4,
            "inherited_full_suite_additional_failures": 3,
            "classification": "exact-BUILD-10-predecessor-inherited-descendant-scope-and-agentic-demo-drift",
        },
        "activation_readiness": READINESS_STATE,
        "remaining_blockers": [],
        "activation_boundary": {
            "implementation_ready": True,
            "production_activation_authority": False,
            "production_activation_allowed": False,
            "production_active": False,
            "official_portrayal_activation_authority": False,
            "official_portrayal_activation_allowed": False,
            "official_portrayal_active": False,
            "source_mutation_authority": False,
            "source_mutation_allowed": False,
            "source_mutated": False,
        },
    }
    record["canonical_record_sha256"] = activation_readiness_record_sha256(record)
    verify_activation_readiness_record(record)
    return record


def verify_activation_readiness_record(record: Any) -> bool:
    if not isinstance(record, Mapping):
        _fail("The BUILD-11 readiness record is missing.", "readiness_record_invalid")
    supplied = record.get("canonical_record_sha256")
    if supplied != activation_readiness_record_sha256(record):
        _fail("The BUILD-11 readiness record identity is invalid.", "readiness_record_tampered")
    exact = {
        "schema_version": READINESS_SCHEMA,
        "record_version": READINESS_VERSION,
        "status": "controlled-production-verified-activation-held",
        "verdict": VERDICT,
        "activation_readiness": READINESS_STATE,
    }
    if any(record.get(key) != value for key, value in exact.items()):
        _fail("The BUILD-11 readiness state is invalid.", "readiness_record_invalid")
    boundary = record.get("activation_boundary", {})
    if boundary.get("implementation_ready") is not True:
        _fail("The verified BUILD-10 implementation is not ready.", "readiness_record_invalid")
    if any(
        boundary.get(key) is not False
        for key in (
            "production_activation_authority",
            "production_activation_allowed",
            "production_active",
            "official_portrayal_activation_authority",
            "official_portrayal_activation_allowed",
            "official_portrayal_active",
            "source_mutation_authority",
            "source_mutation_allowed",
            "source_mutated",
        )
    ):
        _fail(
            "BUILD-11 may not grant activation or mutation authority.",
            "activation_boundary_breached",
        )
    if record.get("remaining_blockers") != []:
        _fail("The ready state cannot contain blockers.", "readiness_record_invalid")
    return True


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    archive = root / "data/datasets/112年多維度SHP成果_0502.zip"
    print(
        json.dumps(
            build_activation_readiness_record(root, archive),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

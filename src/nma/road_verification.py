from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
from typing import Any, Mapping, Sequence

from nma.ogr import inspect_dataset, read_vector_dataset
from nma.real_layer import extract_reviewed_source_layers, file_sha256
from nma.road_approval import approval_sha256, authorization_sha256, validate_authorization
from nma.road_portrayal_decision import (
    decision_sha256,
    proposal_sha256,
    validate_proposal,
)
from nma.road_resolution import canonical_json, canonical_sha256, resolve_road_request


QA_SCHEMA = "nma.road-qa/1.0"
PROVENANCE_SCHEMA = "nma.road-provenance/1.0"
VISUAL_EVIDENCE_SCHEMA = "nma.road-visual-evidence/1.0"

EXECUTION_ID = "road-exec-33766f336d9cc18eb2ac159e"
PLAN_ID = "road-plan-cd434d50bd5b49a012bd1e10"
PLAN_SHA256 = "e51e42b955ade0d3ff5c6b8fbe00919aac4d9b9f90fe59bd548e14b7a9bf04a0"
DERIVED_ID = "road-derived-092adadc29954c5151ae43a7"
DERIVED_SHA256 = "fb8762642e4e3e633912028b18ca6aa11545117e15572839896770537a5971b6"
BUNDLE_ID = "road-bundle-road-exec-33766f336d9cc18eb2ac159e"
BUNDLE_SHA256 = "33aa7c6b0d557fa9a72e2fa4e0106493d8dfe10ec9201bd7762e204bb14a286d"
OBSERVATION_ID = "road-observation-4c88e2e424168c1c712145c1"
OBSERVATION_SHA256 = "e5263aa67dbb400e0c3a63b7cd1457d9d95428a8d519aef34b3c9b4396ce1d9a"
RECEIPT_ID = "road-receipt-road-exec-33766f336d9cc18eb2ac159e"
RECEIPT_SHA256 = "0ab5964fcc2e1f47d43fd328dbc3771a7e624bf4a3707f91236a1485f5610720"
ROLLBACK_ID = "road-rollback-road-exec-33766f336d9cc18eb2ac159e"
ROLLBACK_SHA256 = "03bc4f84d27b9b55baa7403d4ff4abc758ff223d0ffe7b7aaaa11233da162ae2"

ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
ROAD01_PACKAGE_SHA256 = "b5df3f57c33843f354371206c937f52d37ddbbd9d047a31ad7c334532ce30e9a"
FIXTURE_SHA256 = "b01e261971f65cbfc127aed4f1ba17b01b194dd89f256d3c024170c1dc7338f0"
PROPOSAL_SHA256 = "3d45d1ed039c2af1aa7f050fa1e3c22158c891390c001285054b05a02959ce06"
DECISION_SHA256 = "0d671b1fed3f4b19e4204e745bdcb13f872f3a00dcb4ef5050a091a14065e090"
APPROVAL_SHA256 = "f333defee511e0ae82702444d18befe2f9e115d75608ab61a5c20f91c52f2f07"
AUTHORIZATION_SHA256 = "f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38"
AUTHORIZATION_ID = "road-03-authorization-" + AUTHORIZATION_SHA256[:24]

ROUTE_IDENTITY = "ROADNUM=縣126|ROADNUM1=|ROADNUM2=|ROADNAME=中山街"
CLASS_CODE = "9420400"
SOURCE_LAYER = "K14_ROAD"
SOURCE_CRS = "TWD97[2020]_TM121"
RUNTIME_CRS = "EPSG:4326"
SEGMENT_IDS = ("K0000004671", "K0000004913", "K0000005348")
VERTEX_COUNTS = (4, 3, 4)
PORTRAYAL = {
    "shield_code": "9490005",
    "shield_orientation": "road-parallel",
    "road_name_annotation": "中山街",
    "graphic_element_roles": [2, 5],
}
FROZEN_IDENTITIES = {
    "road01_package_sha256": ROAD01_PACKAGE_SHA256,
    "road01_fixture_sha256": FIXTURE_SHA256,
    "road02_proposal_sha256": PROPOSAL_SHA256,
    "road02_decision_sha256": DECISION_SHA256,
    "road03_approval_sha256": APPROVAL_SHA256,
    "road03_authorization_sha256": AUTHORIZATION_SHA256,
}

CORE_ARTIFACTS = (
    "authorization.json",
    "plan.json",
    "derived-portrayal.json",
    "bundle.json",
    "receipt.json",
    "rollback-manifest.json",
    "consumption.json",
    "data/road-centreline-source.geojson",
    "data/road-centreline-runtime.geojson",
    f"observations/{OBSERVATION_ID}.json",
)
GENERATED_ARTIFACTS = {"qa.json", "provenance.json"}
GOLDENS = {
    "plan": "nma-road-hero-road-04-golden-plan-v1.0.json",
    "derived": "nma-road-hero-road-04-golden-derived-portrayal-v1.0.json",
    "bundle": "nma-road-hero-road-04-golden-runtime-bundle-v1.0.json",
    "receipt": "nma-road-hero-road-04-golden-receipt-v1.0.json",
    "rollback": "nma-road-hero-road-04-golden-rollback-manifest-v1.0.json",
    "observation": "nma-road-hero-road-04-golden-observation-v1.0.json",
}


class RoadVerificationError(ValueError):
    """ROAD-05 cannot inspect the requested persisted execution safely."""


def _canonical_file_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value) + b"\n").hexdigest()


def _without(value: Mapping[str, Any], *fields: str) -> dict[str, Any]:
    result = deepcopy(dict(value))
    for field in fields:
        result.pop(field, None)
    return result


def _record_hash(value: Mapping[str, Any], field: str, *ignored: str) -> str:
    return canonical_sha256(_without(value, field, *ignored))


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RoadVerificationError(f"Unreadable JSON artifact: {path}") from error
    if not isinstance(value, dict):
        raise RoadVerificationError(f"JSON artifact is not an object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_bytes(canonical_json(value) + b"\n")


def _check(
    checks: list[dict[str, Any]],
    identifier: str,
    passed: bool,
    *,
    expected: Any,
    observed: Any,
) -> bool:
    checks.append(
        {
            "id": identifier,
            "status": "passed" if passed else "failed",
            "expected": expected,
            "observed": observed,
        }
    )
    return passed


def _safe_json(path: Path, checks: list[dict[str, Any]], identifier: str) -> dict[str, Any]:
    try:
        value = _load_json(path)
    except RoadVerificationError as error:
        _check(checks, identifier, False, expected="readable JSON object", observed=str(error))
        return {}
    _check(checks, identifier, True, expected="readable JSON object", observed="readable")
    return value


def _finite_coordinates(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value) and all(_finite_coordinates(item) for item in value)
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _route_identity(properties: Mapping[str, Any]) -> str:
    def text(name: str) -> str:
        value = properties.get(name)
        return "" if value is None else str(value)

    return (
        f"ROADNUM={text('ROADNUM')}|ROADNUM1={text('ROADNUM1')}|"
        f"ROADNUM2={text('ROADNUM2')}|ROADNAME={text('ROADNAME')}"
    )


def _normalize_feature(feature: Mapping[str, Any], *, runtime: bool) -> dict[str, Any]:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, Mapping) or not isinstance(geometry, Mapping):
        raise RoadVerificationError("Invalid ROAD feature object.")
    identifier = str(properties.get("ROADSEGID", ""))
    if geometry.get("type") != "LineString" or not _finite_coordinates(geometry.get("coordinates")):
        raise RoadVerificationError("Invalid ROAD LineString geometry.")
    return {
        "type": "Feature",
        "id": identifier,
        "properties": {
            "ROADSEGID": identifier,
            "TERRAINID": ""
            if properties.get("TERRAINID") is None
            else str(properties["TERRAINID"]),
            "ROADNUM": "" if properties.get("ROADNUM") is None else str(properties["ROADNUM"]),
            "ROADNUM1": "" if properties.get("ROADNUM1") is None else str(properties["ROADNUM1"]),
            "ROADNUM2": "" if properties.get("ROADNUM2") is None else str(properties["ROADNUM2"]),
            "ROADNAME": "" if properties.get("ROADNAME") is None else str(properties["ROADNAME"]),
            "nma_runtime_derivative": runtime,
        },
        "geometry": deepcopy(dict(geometry)),
    }


def _ordered_features(collection: Mapping[str, Any], *, runtime: bool) -> list[dict[str, Any]]:
    features = collection.get("features")
    if not isinstance(features, list):
        raise RoadVerificationError("K14_ROAD feature collection is invalid.")
    selected: dict[str, Mapping[str, Any]] = {}
    for feature in features:
        if not isinstance(feature, Mapping) or not isinstance(feature.get("properties"), Mapping):
            continue
        identifier = str(feature["properties"].get("ROADSEGID", ""))
        if identifier in SEGMENT_IDS:
            if identifier in selected:
                raise RoadVerificationError("An authorized ROAD segment is duplicated.")
            selected[identifier] = feature
    if set(selected) != set(SEGMENT_IDS):
        raise RoadVerificationError("The archive is missing an authorized ROAD segment.")
    ordered = [_normalize_feature(selected[item], runtime=runtime) for item in SEGMENT_IDS]
    for feature in ordered:
        properties = feature["properties"]
        if properties["TERRAINID"] != CLASS_CODE or _route_identity(properties) != ROUTE_IDENTITY:
            raise RoadVerificationError("The archive ROAD semantics differ from authorization.")
    return ordered


def _geometry_records(
    source_features: Sequence[Mapping[str, Any]], runtime_features: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source, runtime in zip(source_features, runtime_features, strict=True):
        source_geometry = source["geometry"]
        runtime_geometry = runtime["geometry"]
        source_coordinates = source_geometry["coordinates"]
        runtime_coordinates = runtime_geometry["coordinates"]
        if len(source_coordinates) != len(runtime_coordinates):
            raise RoadVerificationError("Runtime projection changed ROAD vertex count.")
        records.append(
            {
                "segment_id": source["id"],
                "source_geometry_type": "LineString",
                "source_crs": SOURCE_CRS,
                "source_geometry_sha256": canonical_sha256(source_geometry),
                "source_vertex_count": len(source_coordinates),
                "source_endpoint_sha256": [
                    canonical_sha256(source_coordinates[0]),
                    canonical_sha256(source_coordinates[-1]),
                ],
                "runtime_crs": RUNTIME_CRS,
                "transformation_method": (
                    "GDAL/OGR coordinate transformation; XY vertices preserved"
                ),
                "runtime_geometry_sha256": canonical_sha256(runtime_geometry),
                "runtime_vertex_count": len(runtime_coordinates),
            }
        )
    endpoints = [set(record["source_endpoint_sha256"]) for record in records]
    if (
        len(endpoints[0] & endpoints[1]) != 1
        or len(endpoints[1] & endpoints[2]) != 1
        or endpoints[0] & endpoints[2]
    ):
        raise RoadVerificationError("The frozen source endpoint continuity changed.")
    return records


def _collections(
    source_features: list[dict[str, Any]], runtime_features: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = {
        "type": "FeatureCollection",
        "nma:provenance": {
            "archive_sha256": ARCHIVE_SHA256,
            "source_layer": SOURCE_LAYER,
            "source_crs": SOURCE_CRS,
            "geometry_operation": "selection-only; native coordinates unchanged",
            "ordered_segment_ids": list(SEGMENT_IDS),
        },
        "features": source_features,
    }
    runtime = {
        "type": "FeatureCollection",
        "nma:provenance": {
            "archive_sha256": ARCHIVE_SHA256,
            "source_layer": SOURCE_LAYER,
            "source_crs": SOURCE_CRS,
            "runtime_crs": RUNTIME_CRS,
            "transformation_method": "GDAL/OGR coordinate transformation; XY vertices preserved",
            "ordered_segment_ids": list(SEGMENT_IDS),
        },
        "features": runtime_features,
    }
    return source, runtime


def _reconstruct_geometry(archive_path: Path) -> dict[str, Any]:
    if not archive_path.is_file() or file_sha256(archive_path) != ARCHIVE_SHA256:
        raise RoadVerificationError("Private archive is missing or hash-mismatched.")
    ogr2ogr = shutil.which("ogr2ogr")
    if ogr2ogr is None:
        raise RoadVerificationError("GDAL/OGR is unavailable for independent reconstruction.")
    with tempfile.TemporaryDirectory(prefix="nma-road05-independent-") as temporary:
        root = Path(temporary)
        components = root / "source-components"
        components.mkdir()
        sources, _ = extract_reviewed_source_layers(archive_path, [SOURCE_LAYER], components)
        if len(sources) != 1:
            raise RoadVerificationError("K14_ROAD source is missing or ambiguous.")
        inspection = inspect_dataset(sources[0])
        required_fields = {"ROADSEGID", "TERRAINID", "ROADNUM", "ROADNUM1", "ROADNUM2", "ROADNAME"}
        observed_fields = {
            item.get("name") for item in inspection.get("fields", []) if isinstance(item, Mapping)
        }
        if (
            not inspection.get("available")
            or inspection.get("layer") != SOURCE_LAYER
            or inspection.get("geometry_type") != "LineString"
            or inspection.get("crs_name") != SOURCE_CRS
            or inspection.get("feature_count") != 196
            or not required_fields.issubset(observed_fields)
        ):
            raise RoadVerificationError("K14_ROAD does not match the source contract.")
        source_collection, _ = read_vector_dataset(sources[0])
        source_features = _ordered_features(source_collection, runtime=False)
        runtime_raw = root / "runtime.geojson"
        where = "ROADSEGID IN ('" + "','".join(SEGMENT_IDS) + "')"
        try:
            subprocess.run(
                [
                    ogr2ogr,
                    "-f",
                    "GeoJSON",
                    str(runtime_raw),
                    str(sources[0]),
                    "-where",
                    where,
                    "-t_srs",
                    RUNTIME_CRS,
                    "-dim",
                    "XY",
                    "-lco",
                    "RFC7946=YES",
                    "-lco",
                    "WRITE_BBOX=NO",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            raise RoadVerificationError("Independent EPSG:4326 projection failed.") from error
        runtime_features = _ordered_features(_load_json(runtime_raw), runtime=True)
        records = _geometry_records(source_features, runtime_features)
        source, runtime = _collections(source_features, runtime_features)
        return {"source": source, "runtime": runtime, "geometry": records}


def _frozen_paths(repository_root: Path) -> dict[str, Path]:
    specifications = repository_root / "data/specifications"
    return {
        "fixture": specifications / "nma-road-hero-road-01-v1.0.json",
        "evidence": repository_root / "data/extraction/v0.4/road-compound-portrayal-reviewed.json",
        "proposal": specifications / "nma-road-hero-road-02-golden-proposal-v1.0.json",
        "decision": specifications / "nma-road-hero-road-02-golden-decision-v1.0.json",
        "approval": specifications / "nma-road-hero-road-03-golden-approval-v1.0.json",
        "authorization": specifications / "nma-road-hero-road-03-golden-authorization-v1.0.json",
    }


def _verify_frozen_lineage(repository_root: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    paths = _frozen_paths(repository_root)
    records = {
        name: _safe_json(path, checks, f"read_frozen_{name}") for name, path in paths.items()
    }
    identities: dict[str, Any] = {}
    try:
        package = resolve_road_request(
            "Resolve K14 County Highway 126 中山街",
            observed_archive_sha256=ARCHIVE_SHA256,
            observed_fixture_sha256=records["fixture"].get("fixture_sha256"),
            fixture=records["fixture"],
            evidence_record_set=records["evidence"],
        )
        validate_proposal(records["proposal"], records["decision"])
        validate_authorization(
            records["authorization"],
            records["approval"],
            records["proposal"],
            records["decision"],
        )
        identities = {
            "road01_package_sha256": package.get("package_sha256"),
            "road01_fixture_sha256": records["fixture"].get("fixture_sha256"),
            "road02_proposal_sha256": proposal_sha256(records["proposal"]),
            "road02_decision_sha256": decision_sha256(records["decision"]),
            "road03_approval_sha256": approval_sha256(records["approval"]),
            "road03_authorization_sha256": authorization_sha256(records["authorization"]),
        }
        valid = identities == FROZEN_IDENTITIES
        observed: Any = identities
    except (TypeError, ValueError) as error:
        valid = False
        observed = {"error": type(error).__name__, "message": str(error)}
    _check(
        checks,
        "frozen_upstream_lineage",
        valid,
        expected=FROZEN_IDENTITIES,
        observed=observed,
    )
    records["identities"] = identities
    return records


def _git_archive_status(repository_root: Path, archive_path: Path) -> dict[str, Any]:
    try:
        relative = archive_path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError:
        return {"relative_path": None, "ignored": False, "tracked": True, "staged": True}

    def run(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=repository_root,
            capture_output=True,
            text=True,
            check=False,
        )

    ignored = run("check-ignore", "-q", "--", relative).returncode == 0
    tracked = bool(run("ls-files", "--", relative).stdout.strip())
    staged = relative in run("diff", "--cached", "--name-only", "--", relative).stdout.splitlines()
    return {
        "relative_path": relative,
        "ignored": ignored,
        "tracked": tracked,
        "staged": staged,
    }


def _visual_qa(
    visual_evidence_path: Path | None,
    screenshot_path: Path | None,
    bundle: Mapping[str, Any],
    runtime_file_sha256: str | None,
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    layer = bundle.get("layers", [None])
    layer = layer[0] if isinstance(layer, list) and len(layer) == 1 else None
    semantic_label = (
        isinstance(layer, Mapping)
        and layer.get("type") == "symbol"
        and layer.get("layout") == {"symbol-placement": "line", "text-field": ["literal", "中山街"]}
        and "paint" not in layer
        and not any(
            key in layer.get("layout", {})
            for key in (
                "text-offset",
                "text-font",
                "text-allow-overlap",
                "text-ignore-placement",
                "symbol-spacing",
                "icon-image",
            )
        )
    )
    _check(
        checks,
        "label_semantic_contract",
        semantic_label,
        expected="single line-following literal 中山街 layer with no added styling",
        observed=deepcopy(layer),
    )
    shield = bundle.get("shield_binding")
    shield_valid = (
        shield
        == {
            "shield_code": "9490005",
            "shield_orientation": "road-parallel",
            "status": "semantic_binding_only",
            "resolver_identity": None,
            "resolved_artifact_sha256": None,
        }
        and "icon" not in json.dumps(bundle, ensure_ascii=False).casefold()
    )
    _check(
        checks,
        "shield_semantic_binding",
        shield_valid,
        expected="9490005 road-parallel semantic_binding_only without graphic",
        observed=shield,
    )

    if visual_evidence_path is None or not visual_evidence_path.is_file():
        _check(
            checks,
            "actual_render_observation",
            False,
            expected="hash-bound actual candidate render evidence",
            observed="missing",
        )
        return {
            "rendering_mechanism": "not_observed",
            "render_environment": None,
            "annotation_result": "verification_blocked_no_render_evidence",
            "collision_placement_result": "verification_blocked_no_render_evidence",
            "shield_result": (
                "semantic_binding_only_no_fabricated_graphic" if shield_valid else "incorrect"
            ),
            "pixel_evidence_sha256": None,
            "independent_visual_oracle": "absent",
            "pixel_correctness_status": "not_evaluated_no_render_evidence",
        }

    try:
        evidence = _load_json(visual_evidence_path)
    except RoadVerificationError as error:
        _check(
            checks,
            "actual_render_observation",
            False,
            expected="readable visual evidence",
            observed=str(error),
        )
        return {
            "rendering_mechanism": "invalid_evidence",
            "render_environment": None,
            "annotation_result": "verification_blocked_invalid_render_evidence",
            "collision_placement_result": "verification_blocked_invalid_render_evidence",
            "shield_result": "incorrect" if not shield_valid else "semantic_binding_only",
            "pixel_evidence_sha256": None,
            "independent_visual_oracle": "absent",
            "pixel_correctness_status": "not_evaluated_invalid_render_evidence",
        }
    supplied_hash = evidence.get("evidence_sha256")
    evidence_hash_valid = supplied_hash == _record_hash(evidence, "evidence_sha256")
    screenshot_actual = (
        file_sha256(screenshot_path)
        if screenshot_path is not None and screenshot_path.is_file()
        else None
    )
    observation = evidence.get("render_observation", {})
    rendered_texts = (
        observation.get("rendered_label_texts") if isinstance(observation, Mapping) else None
    )
    label_count = (
        observation.get("rendered_label_feature_count")
        if isinstance(observation, Mapping)
        else None
    )
    valid = (
        evidence.get("schema") == VISUAL_EVIDENCE_SCHEMA
        and evidence.get("execution_id") == EXECUTION_ID
        and evidence.get("bundle_sha256") == BUNDLE_SHA256
        and evidence.get("runtime_geojson_sha256") == runtime_file_sha256
        and evidence_hash_valid
        and screenshot_actual == observation.get("screenshot_sha256")
        and observation.get("map_loaded") is True
        and rendered_texts == ["中山街"]
        and isinstance(label_count, int)
        and label_count >= 1
        and observation.get("unrelated_feature_count") == 0
        and observation.get("shield_graphic_count") == 0
        and observation.get("unexpected_layer_ids") == []
        and observation.get("unexpected_source_ids") == []
        and evidence.get("oracle") == {"status": "absent", "identity": None}
        and evidence.get("pixel_correctness_status")
        == "evidence_generated_but_no_independent_visual_oracle"
    )
    _check(
        checks,
        "actual_render_observation",
        valid,
        expected={
            "execution_id": EXECUTION_ID,
            "bundle_sha256": BUNDLE_SHA256,
            "label": "中山街",
            "minimum_visible_label_features": 1,
            "shield_graphic_count": 0,
            "oracle": "absent",
        },
        observed={
            "execution_id": evidence.get("execution_id"),
            "bundle_sha256": evidence.get("bundle_sha256"),
            "rendered_label_texts": rendered_texts,
            "rendered_label_feature_count": label_count,
            "shield_graphic_count": observation.get("shield_graphic_count"),
            "screenshot_sha256": screenshot_actual,
            "evidence_hash_valid": evidence_hash_valid,
        },
    )
    return {
        "rendering_mechanism": evidence.get("rendering_mechanism"),
        "render_environment": deepcopy(evidence.get("render_environment")),
        "annotation_result": "present" if valid else "incorrect_or_unverified",
        "collision_placement_result": (
            "rendered_without_duplicate_text_values_or_unrelated_features"
            if valid
            else "incorrect_or_unverified"
        ),
        "shield_result": (
            "semantic_binding_only_no_fabricated_graphic"
            if valid and shield_valid
            else "incorrect_or_unverified"
        ),
        "pixel_evidence_sha256": screenshot_actual,
        "visual_evidence_sha256": supplied_hash,
        "independent_visual_oracle": "absent",
        "pixel_correctness_status": evidence.get("pixel_correctness_status"),
    }


def _chain_node(
    kind: str,
    sha256: str | None,
    *,
    record_id: str | None,
    parents: Sequence[str] = (),
    byte_sha256: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "record_id": record_id,
        "sha256": sha256,
        "byte_sha256": byte_sha256,
        "parent_sha256": list(parents),
    }


class RoadExecutionVerifier:
    """Independently reconstruct and verify one persisted ROAD-04 execution."""

    def __init__(
        self,
        *,
        storage_root: str | Path,
        archive_path: str | Path,
        repository_root: str | Path,
        visual_evidence_path: str | Path | None = None,
        screenshot_path: str | Path | None = None,
    ) -> None:
        self.storage_root = Path(storage_root)
        self.archive_path = Path(archive_path)
        self.repository_root = Path(repository_root)
        self.visual_evidence_path = (
            Path(visual_evidence_path) if visual_evidence_path is not None else None
        )
        self.screenshot_path = Path(screenshot_path) if screenshot_path is not None else None

    def _execution_root(self, execution_id: str) -> Path:
        if execution_id != EXECUTION_ID:
            raise RoadVerificationError(f"Unexpected ROAD-04 execution identity: {execution_id}")
        root = self.storage_root / "executions" / execution_id
        if not root.is_dir():
            raise RoadVerificationError(f"Execution not found: {execution_id}")
        return root

    def verify(self, execution_id: str = EXECUTION_ID, *, persist: bool = True) -> dict[str, Any]:
        root = self._execution_root(execution_id)
        qa_checks: list[dict[str, Any]] = []
        provenance_checks: list[dict[str, Any]] = []

        archive_actual = file_sha256(self.archive_path) if self.archive_path.is_file() else None
        archive_status = _git_archive_status(self.repository_root, self.archive_path)
        _check(
            qa_checks,
            "private_archive_identity",
            archive_actual == ARCHIVE_SHA256,
            expected=ARCHIVE_SHA256,
            observed=archive_actual,
        )
        _check(
            qa_checks,
            "private_archive_git_boundary",
            archive_status["ignored"]
            and not archive_status["tracked"]
            and not archive_status["staged"],
            expected={"ignored": True, "tracked": False, "staged": False},
            observed={key: archive_status[key] for key in ("ignored", "tracked", "staged")},
        )

        frozen = _verify_frozen_lineage(self.repository_root, provenance_checks)
        actual = {
            "authorization": _safe_json(
                root / "authorization.json", qa_checks, "read_authorization"
            ),
            "plan": _safe_json(root / "plan.json", qa_checks, "read_plan"),
            "derived": _safe_json(root / "derived-portrayal.json", qa_checks, "read_derived"),
            "bundle": _safe_json(root / "bundle.json", qa_checks, "read_bundle"),
            "receipt": _safe_json(root / "receipt.json", qa_checks, "read_receipt"),
            "rollback": _safe_json(root / "rollback-manifest.json", qa_checks, "read_rollback"),
            "consumption": _safe_json(root / "consumption.json", qa_checks, "read_consumption"),
            "source": _safe_json(
                root / "data/road-centreline-source.geojson", qa_checks, "read_source_geometry"
            ),
            "runtime": _safe_json(
                root / "data/road-centreline-runtime.geojson", qa_checks, "read_runtime_geometry"
            ),
            "observation": _safe_json(
                root / f"observations/{OBSERVATION_ID}.json", qa_checks, "read_observation"
            ),
        }

        expected_goldens: dict[str, dict[str, Any]] = {}
        for kind, name in GOLDENS.items():
            expected_goldens[kind] = _safe_json(
                self.repository_root / "data/specifications" / name,
                provenance_checks,
                f"read_road04_golden_{kind}",
            )

        hash_contracts = {
            "plan": ("execution_plan_sha256", PLAN_SHA256, ()),
            "derived": ("artifact_sha256", DERIVED_SHA256, ()),
            "bundle": ("bundle_sha256", BUNDLE_SHA256, ()),
            "receipt": ("receipt_sha256", RECEIPT_SHA256, ("completed_at",)),
            "rollback": ("rollback_manifest_sha256", ROLLBACK_SHA256, ()),
            "observation": ("observation_sha256", OBSERVATION_SHA256, ("timestamp",)),
        }
        for kind, (field, identity, ignored) in hash_contracts.items():
            value = actual[kind]
            computed = _record_hash(value, field, *ignored) if value else None
            _check(
                qa_checks,
                f"{kind}_canonical_identity",
                value.get(field) == identity == computed,
                expected=identity,
                observed={"declared": value.get(field), "computed": computed},
            )
            golden = expected_goldens[kind]
            golden_computed = _record_hash(golden, field, *ignored) if golden else None
            _check(
                provenance_checks,
                f"road04_golden_{kind}_identity",
                golden.get(field) == identity == golden_computed,
                expected=identity,
                observed={"declared": golden.get(field), "computed": golden_computed},
            )

        persisted_authorization = actual["authorization"]
        expected_persisted_authorization = {
            "authorization_id": AUTHORIZATION_ID,
            "authorization_sha256": AUTHORIZATION_SHA256,
            "frozen_identities": FROZEN_IDENTITIES,
            "bindings": deepcopy(frozen.get("authorization", {}).get("bindings")),
            "capability": deepcopy(frozen.get("authorization", {}).get("capability")),
            "permissions": deepcopy(frozen.get("authorization", {}).get("permissions")),
        }
        _check(
            provenance_checks,
            "persisted_authorization_binding",
            persisted_authorization == expected_persisted_authorization,
            expected=expected_persisted_authorization,
            observed=persisted_authorization,
        )

        reconstructed: dict[str, Any] | None = None
        try:
            reconstructed = _reconstruct_geometry(self.archive_path)
            reconstruction_observed: Any = "derived independently"
        except (OSError, RuntimeError, ValueError) as error:
            reconstruction_observed = {"error": type(error).__name__, "message": str(error)}
        _check(
            qa_checks,
            "independent_expected_state_reconstruction",
            reconstructed is not None,
            expected="archive-derived K14_ROAD source and EPSG:4326 runtime state",
            observed=reconstruction_observed,
        )
        if reconstructed is not None:
            _check(
                qa_checks,
                "source_geometry_exact",
                actual["source"] == reconstructed["source"],
                expected={
                    "sha256": _canonical_file_sha256(reconstructed["source"]),
                    "segments": list(SEGMENT_IDS),
                    "vertex_counts": list(VERTEX_COUNTS),
                },
                observed={
                    "sha256": (
                        file_sha256(root / "data/road-centreline-source.geojson")
                        if (root / "data/road-centreline-source.geojson").is_file()
                        else None
                    ),
                    "segments": [
                        feature.get("id") for feature in actual["source"].get("features", [])
                    ],
                    "vertex_counts": [
                        len(feature.get("geometry", {}).get("coordinates", []))
                        for feature in actual["source"].get("features", [])
                    ],
                },
            )
            _check(
                qa_checks,
                "runtime_derivative_exact",
                actual["runtime"] == reconstructed["runtime"],
                expected={
                    "sha256": _canonical_file_sha256(reconstructed["runtime"]),
                    "crs": RUNTIME_CRS,
                    "vertex_counts": list(VERTEX_COUNTS),
                },
                observed={
                    "sha256": (
                        file_sha256(root / "data/road-centreline-runtime.geojson")
                        if (root / "data/road-centreline-runtime.geojson").is_file()
                        else None
                    ),
                    "crs": actual["runtime"].get("nma:provenance", {}).get("runtime_crs"),
                    "vertex_counts": [
                        len(feature.get("geometry", {}).get("coordinates", []))
                        for feature in actual["runtime"].get("features", [])
                    ],
                },
            )
            expected_geometry = reconstructed["geometry"]
        else:
            expected_geometry = []

        plan_geometry = actual["plan"].get("source", {}).get("geometry")
        _check(
            qa_checks,
            "geometry_provenance_contract",
            bool(expected_geometry)
            and plan_geometry == expected_geometry
            and actual["derived"].get("geometry_provenance") == expected_geometry
            and [item.get("source_vertex_count") for item in expected_geometry]
            == list(VERTEX_COUNTS)
            and [item.get("runtime_vertex_count") for item in expected_geometry]
            == list(VERTEX_COUNTS),
            expected=expected_geometry,
            observed=plan_geometry,
        )

        for kind in ("plan", "derived", "bundle", "receipt", "rollback", "observation"):
            golden = expected_goldens[kind]
            observed = actual[kind]
            if kind in {"receipt", "observation"}:
                ignored = "completed_at" if kind == "receipt" else "timestamp"
                matches = _without(observed, ignored) == _without(golden, ignored)
            else:
                matches = observed == golden
            _check(
                qa_checks,
                f"{kind}_expected_state",
                matches,
                expected={"canonical_sha256": hash_contracts[kind][1]},
                observed={"canonical_sha256": observed.get(hash_contracts[kind][0])},
            )

        source_file_hash = (
            file_sha256(root / "data/road-centreline-source.geojson")
            if (root / "data/road-centreline-source.geojson").is_file()
            else None
        )
        runtime_file_hash = (
            file_sha256(root / "data/road-centreline-runtime.geojson")
            if (root / "data/road-centreline-runtime.geojson").is_file()
            else None
        )
        output_bindings = actual["derived"].get("outputs", {})
        rollback_artifacts = actual["rollback"].get("artifacts", [])
        rollback_by_path = {
            item.get("path"): item.get("sha256")
            for item in rollback_artifacts
            if isinstance(item, Mapping)
        }
        artifact_hash_binding = (
            output_bindings.get("source_geometry", {}).get("sha256") == source_file_hash
            and output_bindings.get("runtime_geometry", {}).get("sha256") == runtime_file_hash
            and rollback_by_path.get("data/road-centreline-source.geojson") == source_file_hash
            and rollback_by_path.get("data/road-centreline-runtime.geojson") == runtime_file_hash
            and rollback_by_path.get("bundle.json")
            == (file_sha256(root / "bundle.json") if (root / "bundle.json").is_file() else None)
            and rollback_by_path.get("derived-portrayal.json")
            == (
                file_sha256(root / "derived-portrayal.json")
                if (root / "derived-portrayal.json").is_file()
                else None
            )
        )
        _check(
            provenance_checks,
            "persisted_artifact_hash_bindings",
            artifact_hash_binding,
            expected="all derived/rollback file hashes bind actual bytes",
            observed={
                "source": source_file_hash,
                "runtime": runtime_file_hash,
                "rollback": rollback_by_path,
            },
        )

        expected_consumption = {
            "schema": "nma.road-authorization-consumption/1.0",
            "authorization_id": AUTHORIZATION_ID,
            "authorization_sha256": AUTHORIZATION_SHA256,
            "execution_id": EXECUTION_ID,
            "idempotency_key_sha256": "d4645499a8a897194ed49d7cd19edb6acd96bda5db0611fd82a701a875f343cb",
            "receipt_id": RECEIPT_ID,
            "receipt_sha256": RECEIPT_SHA256,
        }
        ledger_path = self.storage_root / "ledger" / f"{AUTHORIZATION_SHA256}.json"
        ledger = _safe_json(ledger_path, provenance_checks, "read_authorization_ledger")
        _check(
            provenance_checks,
            "authorization_consumption_binding",
            actual["consumption"] == expected_consumption == ledger,
            expected=expected_consumption,
            observed={"execution": actual["consumption"], "ledger": ledger},
        )

        actual_files = sorted(
            path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
        )
        expected_files = sorted(
            [*CORE_ARTIFACTS, *[item for item in GENERATED_ARTIFACTS if (root / item).is_file()]]
        )
        unexpected_files = sorted(set(actual_files) - set(expected_files))
        missing_files = sorted(set(CORE_ARTIFACTS) - set(actual_files))
        _check(
            qa_checks,
            "exact_persisted_artifact_set",
            not unexpected_files and not missing_files,
            expected={
                "required": list(CORE_ARTIFACTS),
                "generated_allowed": sorted(GENERATED_ARTIFACTS),
            },
            observed={"missing": missing_files, "unexpected": unexpected_files},
        )

        forbidden_operations = (
            "snap",
            "simplify",
            "smooth",
            "densify",
            "buffer",
            "offset",
            "topology repair",
            "merge",
            "split",
            "polygon",
            "roada",
            "road edge",
        )
        translation_text = json.dumps(
            actual["plan"].get("runtime_translation", {}), ensure_ascii=False
        ).casefold()
        governance = actual["derived"].get("governance")
        semantics_valid = (
            actual["plan"].get("portrayal") == PORTRAYAL
            and actual["derived"].get("portrayal") == PORTRAYAL
            and actual["plan"].get("source", {}).get("ordered_segment_ids") == list(SEGMENT_IDS)
            and actual["bundle"].get("scope", {}).get("ordered_segment_ids") == list(SEGMENT_IDS)
            and actual["bundle"].get("scope", {}).get("route_identity") == ROUTE_IDENTITY
            and actual["bundle"].get("scope", {}).get("class_code") == CLASS_CODE
            and governance
            == {
                "source_mutation_performed": False,
                "topology_repair_performed": False,
                "roada_execution_performed": False,
                "road_edge_derivation_performed": False,
            }
            and not any(item in translation_text for item in forbidden_operations)
        )
        _check(
            qa_checks,
            "authorized_road_portrayal_only",
            semantics_valid,
            expected={"portrayal": PORTRAYAL, "segments": list(SEGMENT_IDS)},
            observed={
                "portrayal": actual["plan"].get("portrayal"),
                "segments": actual["plan"].get("source", {}).get("ordered_segment_ids"),
                "governance": governance,
            },
        )

        visual = _visual_qa(
            self.visual_evidence_path,
            self.screenshot_path,
            actual["bundle"],
            runtime_file_hash,
            qa_checks,
        )

        core_hashes = {
            relative: file_sha256(root / relative)
            for relative in CORE_ARTIFACTS
            if (root / relative).is_file()
        }
        artifact_set_sha256 = canonical_sha256(core_hashes)
        expected_transition = {
            "authorization_sha256": AUTHORIZATION_SHA256,
            "archive_sha256": ARCHIVE_SHA256,
            "execution_id": EXECUTION_ID,
            "plan": {"id": PLAN_ID, "sha256": PLAN_SHA256},
            "derived": {"id": DERIVED_ID, "sha256": DERIVED_SHA256},
            "bundle": {"id": BUNDLE_ID, "sha256": BUNDLE_SHA256},
            "observation": {"id": OBSERVATION_ID, "sha256": OBSERVATION_SHA256},
            "receipt": {"id": RECEIPT_ID, "sha256": RECEIPT_SHA256},
            "rollback": {"id": ROLLBACK_ID, "sha256": ROLLBACK_SHA256},
            "scope": {
                "route_identity": ROUTE_IDENTITY,
                "class_code": CLASS_CODE,
                "ordered_segment_ids": list(SEGMENT_IDS),
                "vertex_counts": list(VERTEX_COUNTS),
                "portrayal": PORTRAYAL,
            },
        }
        observed_transition = {
            "artifact_set_sha256": artifact_set_sha256,
            "artifacts": core_hashes,
            "archive_git_boundary": {
                key: archive_status[key] for key in ("ignored", "tracked", "staged")
            },
        }

        qa_failed = [check["id"] for check in qa_checks if check["status"] == "failed"]
        provenance_failed = [
            check["id"] for check in provenance_checks if check["status"] == "failed"
        ]
        if "exact_persisted_artifact_set" in qa_failed and unexpected_files:
            classification = "unexpected-additional-change"
        elif missing_files:
            classification = "expected-change-missing"
        elif (
            "independent_expected_state_reconstruction" in qa_failed
            or "actual_render_observation" in qa_failed
        ):
            classification = "verification-blocked"
        elif qa_failed or provenance_failed:
            classification = "incorrect-change"
        else:
            classification = "expected-change-verified"
        qa_passed = not qa_failed and not provenance_failed
        qa_base = {
            "schema": QA_SCHEMA,
            "qa_id": "road-qa-"
            + canonical_sha256(
                {
                    "execution_id": EXECUTION_ID,
                    "artifact_set_sha256": artifact_set_sha256,
                    "visual_evidence_sha256": visual.get("visual_evidence_sha256"),
                }
            )[:24],
            "execution_id": EXECUTION_ID,
            "status": "passed" if qa_passed else "failed",
            "classification": classification,
            "expected_transition": expected_transition,
            "observed_transition": observed_transition,
            "visual_qa": visual,
            "checks": qa_checks,
        }
        qa = {**qa_base, "qa_sha256": canonical_sha256(qa_base)}

        evidence_id = frozen.get("evidence", {}).get("record_set_id")
        chain = [
            _chain_node("private-source-archive", ARCHIVE_SHA256, record_id=None),
            _chain_node(
                "road-01-evidence",
                canonical_sha256(frozen.get("evidence", {})),
                record_id=evidence_id if isinstance(evidence_id, str) else None,
                parents=(ARCHIVE_SHA256,),
                byte_sha256=(
                    file_sha256(_frozen_paths(self.repository_root)["evidence"])
                    if _frozen_paths(self.repository_root)["evidence"].is_file()
                    else None
                ),
            ),
            _chain_node(
                "road-01-fixture",
                FIXTURE_SHA256,
                record_id=None,
                parents=(ARCHIVE_SHA256,),
                byte_sha256=(
                    file_sha256(_frozen_paths(self.repository_root)["fixture"])
                    if _frozen_paths(self.repository_root)["fixture"].is_file()
                    else None
                ),
            ),
            _chain_node(
                "road-01-package",
                ROAD01_PACKAGE_SHA256,
                record_id=None,
                parents=(ARCHIVE_SHA256, FIXTURE_SHA256),
            ),
            _chain_node(
                "road-02-proposal",
                PROPOSAL_SHA256,
                record_id=None,
                parents=(ROAD01_PACKAGE_SHA256, DECISION_SHA256),
            ),
            _chain_node(
                "road-02-decision",
                DECISION_SHA256,
                record_id=None,
                parents=(ROAD01_PACKAGE_SHA256,),
            ),
            _chain_node(
                "road-03-approval",
                APPROVAL_SHA256,
                record_id=None,
                parents=(PROPOSAL_SHA256, DECISION_SHA256),
            ),
            _chain_node(
                "road-03-authorization",
                AUTHORIZATION_SHA256,
                record_id=AUTHORIZATION_ID,
                parents=(APPROVAL_SHA256, PROPOSAL_SHA256, DECISION_SHA256),
            ),
            _chain_node(
                "road-04-execution",
                RECEIPT_SHA256,
                record_id=EXECUTION_ID,
                parents=(AUTHORIZATION_SHA256,),
            ),
            _chain_node(
                "execution-plan", PLAN_SHA256, record_id=PLAN_ID, parents=(AUTHORIZATION_SHA256,)
            ),
            _chain_node(
                "derived-portrayal",
                DERIVED_SHA256,
                record_id=DERIVED_ID,
                parents=(PLAN_SHA256, AUTHORIZATION_SHA256),
            ),
            _chain_node(
                "runtime-bundle", BUNDLE_SHA256, record_id=BUNDLE_ID, parents=(DERIVED_SHA256,)
            ),
            _chain_node(
                "runtime-observation",
                OBSERVATION_SHA256,
                record_id=OBSERVATION_ID,
                parents=(BUNDLE_SHA256,),
            ),
            _chain_node(
                "execution-receipt",
                RECEIPT_SHA256,
                record_id=RECEIPT_ID,
                parents=(PLAN_SHA256, DERIVED_SHA256, BUNDLE_SHA256),
            ),
            _chain_node(
                "rollback-manifest",
                ROLLBACK_SHA256,
                record_id=ROLLBACK_ID,
                parents=(RECEIPT_SHA256, BUNDLE_SHA256),
            ),
            _chain_node(
                "road-05-qa",
                qa["qa_sha256"],
                record_id=qa["qa_id"],
                parents=(RECEIPT_SHA256, OBSERVATION_SHA256),
            ),
            _chain_node(
                "verified-artifacts",
                artifact_set_sha256,
                record_id=None,
                parents=(qa["qa_sha256"],),
            ),
        ]
        chain_complete = all(node["sha256"] for node in chain) and not provenance_failed
        _check(
            provenance_checks,
            "complete_content_addressed_chain",
            bool(chain_complete),
            expected="complete ROAD-01 through ROAD-05 content-addressed lineage",
            observed=[{"kind": node["kind"], "sha256": node["sha256"]} for node in chain],
        )
        provenance_passed = (
            all(check["status"] == "passed" for check in provenance_checks)
            and qa["status"] == "passed"
        )
        provenance_base = {
            "schema": PROVENANCE_SCHEMA,
            "provenance_id": "road-provenance-"
            + canonical_sha256(
                {
                    "execution_id": EXECUTION_ID,
                    "qa_sha256": qa["qa_sha256"],
                    "artifact_set_sha256": artifact_set_sha256,
                }
            )[:24],
            "execution_id": EXECUTION_ID,
            "status": "verified" if provenance_passed else "failed",
            "lineage_completeness": "complete" if chain_complete else "incomplete",
            "chain": chain,
            "input_artifact_identity": {
                "private_archive_sha256": archive_actual,
                "frozen_identities": frozen.get("identities", {}),
            },
            "output_artifact_identity": {
                "artifact_set_sha256": artifact_set_sha256,
                "artifacts": core_hashes,
            },
            "qa_parent": {"id": qa["qa_id"], "sha256": qa["qa_sha256"]},
            "checks": provenance_checks,
        }
        provenance = {
            **provenance_base,
            "provenance_sha256": canonical_sha256(provenance_base),
        }
        result = {
            "status": "verified" if qa_passed and provenance_passed else "failed",
            "qa": qa,
            "provenance": provenance,
        }
        if persist:
            _write_json(root / "qa.json", qa)
            _write_json(root / "provenance.json", provenance)
        return result


def safe_relative_path(value: str) -> bool:
    """Expose the rollback-path safety predicate for focused tamper tests."""

    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def validate_emitted_records(qa: Mapping[str, Any], provenance: Mapping[str, Any]) -> bool:
    """Validate emitted ROAD-05 identities and the provenance-to-QA parent binding."""

    if (
        qa.get("schema") != QA_SCHEMA
        or provenance.get("schema") != PROVENANCE_SCHEMA
        or qa.get("qa_sha256") != _record_hash(qa, "qa_sha256")
        or provenance.get("provenance_sha256") != _record_hash(provenance, "provenance_sha256")
        or provenance.get("qa_parent") != {"id": qa.get("qa_id"), "sha256": qa.get("qa_sha256")}
    ):
        return False
    chain = provenance.get("chain")
    if not isinstance(chain, list):
        return False
    qa_nodes = [
        node for node in chain if isinstance(node, Mapping) and node.get("kind") == "road-05-qa"
    ]
    artifact_nodes = [
        node
        for node in chain
        if isinstance(node, Mapping) and node.get("kind") == "verified-artifacts"
    ]
    return (
        len(qa_nodes) == 1
        and qa_nodes[0].get("record_id") == qa.get("qa_id")
        and qa_nodes[0].get("sha256") == qa.get("qa_sha256")
        and len(artifact_nodes) == 1
        and artifact_nodes[0].get("parent_sha256") == [qa.get("qa_sha256")]
    )

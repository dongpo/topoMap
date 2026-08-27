from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
from threading import Lock
from typing import Any, Callable, Iterator, Mapping, Sequence

from nma.ogr import inspect_dataset, read_vector_dataset
from nma.real_layer import RealLayerError, extract_reviewed_source_layers, file_sha256
from nma.road_approval import (
    approval_sha256,
    authorization_sha256,
    validate_authorization,
)
from nma.road_portrayal_decision import decision_sha256, proposal_sha256
from nma.road_resolution import canonical_sha256, resolve_road_request


EXECUTION_CONTRACT_VERSION = "road-04/1.0"
EXECUTION_PLAN_SCHEMA = "nma.road-execution-plan/1.0"
DERIVED_PORTRAYAL_SCHEMA = "nma.road-derived-portrayal/1.0"
RUNTIME_BUNDLE_SCHEMA = "nma.road-runtime-bundle/1.0"
RUNTIME_OBSERVATION_SCHEMA = "nma.road-runtime-observation/1.0"
EXECUTION_RECEIPT_SCHEMA = "nma.road-execution-receipt/1.0"
ROLLBACK_MANIFEST_SCHEMA = "nma.road-rollback-manifest/1.0"

EXPECTED_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
EXPECTED_ROAD01_PACKAGE_SHA256 = "b5df3f57c33843f354371206c937f52d37ddbbd9d047a31ad7c334532ce30e9a"
EXPECTED_FIXTURE_SHA256 = "b01e261971f65cbfc127aed4f1ba17b01b194dd89f256d3c024170c1dc7338f0"
EXPECTED_PROPOSAL_SHA256 = "3d45d1ed039c2af1aa7f050fa1e3c22158c891390c001285054b05a02959ce06"
EXPECTED_DECISION_SHA256 = "0d671b1fed3f4b19e4204e745bdcb13f872f3a00dcb4ef5050a091a14065e090"
EXPECTED_APPROVAL_SHA256 = "f333defee511e0ae82702444d18befe2f9e115d75608ab61a5c20f91c52f2f07"
EXPECTED_AUTHORIZATION_SHA256 = "f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38"
EXPECTED_ROUTE_IDENTITY = "ROADNUM=縣126|ROADNUM1=|ROADNUM2=|ROADNAME=中山街"
EXPECTED_CLASS_CODE = "9420400"
EXPECTED_SOURCE_LAYER = "K14_ROAD"
EXPECTED_SOURCE_CRS = "TWD97[2020]_TM121"
RUNTIME_CRS = "EPSG:4326"
EXPECTED_SEGMENT_IDS = ("K0000004671", "K0000004913", "K0000005348")
EXPECTED_PORTRAYAL = {
    "shield_code": "9490005",
    "shield_orientation": "road-parallel",
    "road_name_annotation": "中山街",
    "graphic_element_roles": [2, 5],
}
EXPECTED_TARGET = "derived road-centreline portrayal artifact"
EXPECTED_PERMISSIONS = {
    "execution_allowed": True,
    "source_mutation_allowed": False,
    "topology_repair_allowed": False,
    "roada_execution_allowed": False,
    "road_edge_derivation_allowed": False,
}
AUTHORIZATION_ID = "road-03-authorization-" + EXPECTED_AUTHORIZATION_SHA256[:24]
SHA256 = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,180}$")


class RoadExecutionError(ValueError):
    """ROAD-04 rejected an invalid capability or unsafe execution."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "road04_execution_failed",
        status: int = 422,
    ):
        super().__init__(message)
        self.code = code
        self.status = status


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value) + b"\n")


def _read_json(path: Path, *, code: str = "frozen_identity_mismatch") -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RoadExecutionError(
            f"The required JSON artifact is unreadable: {path.name}.", code=code
        ) from error
    if not isinstance(value, dict):
        raise RoadExecutionError(
            f"The required JSON artifact is not an object: {path.name}.", code=code
        )
    return value


def _hash_record(
    value: Mapping[str, Any], hash_field: str, *, ignored_identity_fields: Sequence[str] = ()
) -> dict[str, Any]:
    record = deepcopy(dict(value))
    basis = deepcopy(record)
    basis.pop(hash_field, None)
    for field in ignored_identity_fields:
        basis.pop(field, None)
    record[hash_field] = canonical_sha256(basis)
    return record


def _require_identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise RoadExecutionError(f"{label} is invalid.", code="execution_scope_mismatch")
    return value


def _now_timestamp(now: Callable[[], datetime]) -> str:
    return now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _road_identity(properties: Mapping[str, Any]) -> str:
    def text(name: str) -> str:
        value = properties.get(name)
        return "" if value is None else str(value)

    return (
        f"ROADNUM={text('ROADNUM')}|ROADNUM1={text('ROADNUM1')}|"
        f"ROADNUM2={text('ROADNUM2')}|ROADNAME={text('ROADNAME')}"
    )


def _finite_coordinates(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value) and all(_finite_coordinates(item) for item in value)
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _geometry_identity(geometry: Mapping[str, Any]) -> str:
    return canonical_sha256(dict(geometry))


def _endpoint_identity(coordinate: Sequence[Any]) -> str:
    return canonical_sha256(list(coordinate))


class FrozenRoadInputs:
    """Paths for the immutable ROAD-01/02/03 handoff inside one repository checkout."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        specifications = self.root / "data/specifications"
        self.fixture = specifications / "nma-road-hero-road-01-v1.0.json"
        self.evidence = self.root / "data/extraction/v0.4/road-compound-portrayal-reviewed.json"
        self.proposal = specifications / "nma-road-hero-road-02-golden-proposal-v1.0.json"
        self.decision = specifications / "nma-road-hero-road-02-golden-decision-v1.0.json"
        self.approval = specifications / "nma-road-hero-road-03-golden-approval-v1.0.json"
        self.authorization = specifications / "nma-road-hero-road-03-golden-authorization-v1.0.json"


class RoadAuthorizationStore:
    """Read-only store for the single frozen ROAD-03 capability."""

    def __init__(self, authorization_path: str | Path):
        self.authorization_path = Path(authorization_path)

    def load(self, authorization_id: str) -> dict[str, Any]:
        if authorization_id != AUTHORIZATION_ID:
            raise RoadExecutionError(
                "The ROAD-03 execution authorization was not found.",
                code="authorization_not_found",
                status=404,
            )
        if not self.authorization_path.is_file():
            raise RoadExecutionError(
                "The frozen ROAD-03 execution authorization was not found.",
                code="authorization_not_found",
                status=404,
            )
        return _read_json(self.authorization_path, code="authorization_not_found")


class FrozenRoadAuthorizationVerifier:
    """Verify the complete immutable ROAD-01/02/03 chain before execution."""

    def __init__(self, inputs: FrozenRoadInputs):
        self.inputs = inputs

    def verify(self, authorization: Any, *, observed_archive_sha256: str) -> dict[str, Any]:
        if not isinstance(authorization, Mapping):
            raise RoadExecutionError(
                "A complete frozen ROAD-03 authorization is required.",
                code="authorization_not_executable",
            )
        supplied = authorization.get("authorization_sha256")
        if supplied != authorization_sha256(authorization):
            raise RoadExecutionError(
                "The ROAD-03 authorization hash does not match its content.",
                code="authorization_hash_mismatch",
            )

        capability = authorization.get("capability")
        permissions = authorization.get("permissions")
        bindings = authorization.get("bindings")
        if not isinstance(capability, Mapping) or capability.get("execution_allowed") is not True:
            raise RoadExecutionError(
                "The ROAD-03 capability is not executable.", code="authorization_not_executable"
            )
        unsafe_codes = {
            "source_mutation_allowed": "unsafe_source_mutation",
            "topology_repair_allowed": "unsafe_topology_operation",
            "roada_execution_allowed": "unsafe_roada_operation",
            "road_edge_derivation_allowed": "unsafe_road_edge_derivation",
        }
        for key, code in unsafe_codes.items():
            if isinstance(permissions, Mapping) and permissions.get(key) is True:
                raise RoadExecutionError(f"Unsafe permission enabled: {key}.", code=code)
        restricted_permissions = {
            key: value for key, value in EXPECTED_PERMISSIONS.items() if key != "execution_allowed"
        }
        if permissions != restricted_permissions:
            raise RoadExecutionError(
                "The authorization permission boundary changed.", code="execution_scope_mismatch"
            )
        if (
            capability.get("execution_target") != EXPECTED_TARGET
            or not isinstance(bindings, Mapping)
            or bindings.get("execution_target") != EXPECTED_TARGET
            or bindings.get("route_identity") != EXPECTED_ROUTE_IDENTITY
            or bindings.get("class_code") != EXPECTED_CLASS_CODE
            or bindings.get("ordered_source_ids") != list(EXPECTED_SEGMENT_IDS)
            or bindings.get("source_archive_sha256") != EXPECTED_ARCHIVE_SHA256
        ):
            raise RoadExecutionError(
                "The authorization execution scope changed.", code="execution_scope_mismatch"
            )
        if (
            capability.get("allowed_changes") != EXPECTED_PORTRAYAL
            or bindings.get("requested_portrayal") != EXPECTED_PORTRAYAL
        ):
            raise RoadExecutionError(
                "The authorization portrayal scope changed.", code="portrayal_scope_mismatch"
            )
        if supplied != EXPECTED_AUTHORIZATION_SHA256:
            raise RoadExecutionError(
                "The ROAD-03 authorization identity is not the frozen identity.",
                code="frozen_identity_mismatch",
            )

        fixture = _read_json(self.inputs.fixture)
        evidence = _read_json(self.inputs.evidence)
        proposal = _read_json(self.inputs.proposal)
        decision = _read_json(self.inputs.decision)
        approval = _read_json(self.inputs.approval)
        try:
            package = resolve_road_request(
                "Resolve K14 County Highway 126 中山街",
                observed_archive_sha256=observed_archive_sha256,
                observed_fixture_sha256=fixture.get("fixture_sha256"),
                fixture=fixture,
                evidence_record_set=evidence,
            )
            validate_authorization(authorization, approval, proposal, decision)
        except ValueError as error:
            raise RoadExecutionError(
                "A frozen ROAD-01/02/03 identity or authorization binding changed.",
                code="frozen_identity_mismatch",
            ) from error

        identities = {
            "road01_package_sha256": package.get("package_sha256"),
            "road01_fixture_sha256": fixture.get("fixture_sha256"),
            "road02_proposal_sha256": proposal_sha256(proposal),
            "road02_decision_sha256": decision_sha256(decision),
            "road03_approval_sha256": approval_sha256(approval),
            "road03_authorization_sha256": authorization_sha256(authorization),
        }
        expected = {
            "road01_package_sha256": EXPECTED_ROAD01_PACKAGE_SHA256,
            "road01_fixture_sha256": EXPECTED_FIXTURE_SHA256,
            "road02_proposal_sha256": EXPECTED_PROPOSAL_SHA256,
            "road02_decision_sha256": EXPECTED_DECISION_SHA256,
            "road03_approval_sha256": EXPECTED_APPROVAL_SHA256,
            "road03_authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
        }
        if identities != expected:
            raise RoadExecutionError(
                "A frozen ROAD-01/02/03 canonical identity changed.",
                code="frozen_identity_mismatch",
            )

        return {
            "authorization_id": AUTHORIZATION_ID,
            "authorization_sha256": EXPECTED_AUTHORIZATION_SHA256,
            "frozen_identities": identities,
            "bindings": deepcopy(dict(bindings)),
            "capability": deepcopy(dict(capability)),
            "permissions": deepcopy(dict(permissions)),
        }


def _normalized_feature(feature: Mapping[str, Any], *, runtime: bool) -> dict[str, Any]:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, Mapping) or not isinstance(geometry, Mapping):
        raise RoadExecutionError(
            "A source ROAD feature is invalid.", code="authorized_segment_missing"
        )
    segment_id = str(properties.get("ROADSEGID", ""))
    if geometry.get("type") != "LineString" or not _finite_coordinates(geometry.get("coordinates")):
        raise RoadExecutionError(
            "A source ROAD geometry is not a finite LineString.", code="execution_scope_mismatch"
        )
    return {
        "type": "Feature",
        "id": segment_id,
        "properties": {
            "ROADSEGID": segment_id,
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
        raise RoadExecutionError("The K14_ROAD source is unreadable.", code="source_layer_missing")
    by_id: dict[str, Mapping[str, Any]] = {}
    for feature in features:
        if not isinstance(feature, Mapping) or not isinstance(feature.get("properties"), Mapping):
            continue
        segment_id = str(feature["properties"].get("ROADSEGID", ""))
        if segment_id in EXPECTED_SEGMENT_IDS:
            if segment_id in by_id:
                raise RoadExecutionError(
                    "An authorized segment is duplicated.", code="execution_conflict"
                )
            by_id[segment_id] = feature
    if set(by_id) != set(EXPECTED_SEGMENT_IDS):
        raise RoadExecutionError(
            "An authorized K14_ROAD source segment is missing.", code="authorized_segment_missing"
        )
    ordered = [
        _normalized_feature(by_id[segment_id], runtime=runtime)
        for segment_id in EXPECTED_SEGMENT_IDS
    ]
    for feature in ordered:
        properties = feature["properties"]
        if properties["TERRAINID"] != EXPECTED_CLASS_CODE:
            raise RoadExecutionError(
                "The authorized ROAD class changed.", code="execution_scope_mismatch"
            )
        if _road_identity(properties) != EXPECTED_ROUTE_IDENTITY:
            raise RoadExecutionError(
                "The authorized ROAD route changed.", code="execution_scope_mismatch"
            )
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
            raise RoadExecutionError(
                "Runtime projection changed the ROAD vertex count.",
                code="runtime_translation_failed",
            )
        records.append(
            {
                "segment_id": source["id"],
                "source_geometry_type": "LineString",
                "source_crs": EXPECTED_SOURCE_CRS,
                "source_geometry_sha256": _geometry_identity(source_geometry),
                "source_vertex_count": len(source_coordinates),
                "source_endpoint_sha256": [
                    _endpoint_identity(source_coordinates[0]),
                    _endpoint_identity(source_coordinates[-1]),
                ],
                "runtime_crs": RUNTIME_CRS,
                "transformation_method": "GDAL/OGR coordinate transformation; XY vertices preserved",
                "runtime_geometry_sha256": _geometry_identity(runtime_geometry),
                "runtime_vertex_count": len(runtime_coordinates),
            }
        )
    return records


def _verify_continuity(records: Sequence[Mapping[str, Any]]) -> None:
    endpoints = [set(record["source_endpoint_sha256"]) for record in records]
    if (
        len(endpoints[0] & endpoints[1]) != 1
        or len(endpoints[1] & endpoints[2]) != 1
        or endpoints[0] & endpoints[2]
    ):
        raise RoadExecutionError(
            "The source ROAD endpoint topology differs from the frozen scope.",
            code="execution_scope_mismatch",
        )


class RoadExecutionEngine:
    """Atomically materialize one frozen ROAD-03 capability without source/runtime mutation."""

    def __init__(
        self,
        *,
        storage_root: str | Path,
        archive_path: str | Path,
        frozen_inputs: FrozenRoadInputs,
        authorization_store: RoadAuthorizationStore | None = None,
        verifier: FrozenRoadAuthorizationVerifier | None = None,
        now: Callable[[], datetime] | None = None,
    ):
        self.storage_root = Path(storage_root)
        self.archive_path = Path(archive_path)
        self.frozen_inputs = frozen_inputs
        self.authorization_store = authorization_store or RoadAuthorizationStore(
            frozen_inputs.authorization
        )
        self.verifier = verifier or FrozenRoadAuthorizationVerifier(frozen_inputs)
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._thread_lock = Lock()

    @property
    def staging_root(self) -> Path:
        return self.storage_root / ".staging"

    @property
    def executions_root(self) -> Path:
        return self.storage_root / "executions"

    @property
    def ledger_root(self) -> Path:
        return self.storage_root / "ledger"

    @contextmanager
    def _execution_lock(self) -> Iterator[None]:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        with self._thread_lock:
            descriptor = os.open(self.storage_root / ".road04.lock", os.O_CREAT | os.O_RDWR, 0o600)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)

    def _verify_source(self) -> str:
        if not self.archive_path.is_file():
            raise RoadExecutionError(
                "The private ROAD source archive is missing.",
                code="source_archive_missing",
                status=503,
            )
        observed = file_sha256(self.archive_path)
        if observed != EXPECTED_ARCHIVE_SHA256:
            raise RoadExecutionError(
                "The private ROAD source archive hash changed.",
                code="source_archive_hash_mismatch",
            )
        return observed

    def execute_by_id(self, request: Any) -> dict[str, Any]:
        if not isinstance(request, dict) or set(request) != {"authorization_id", "idempotency_key"}:
            raise RoadExecutionError(
                "Expected authorization_id and idempotency_key only.",
                code="invalid_execution_request",
                status=400,
            )
        return self.execute(
            self.authorization_store.load(request["authorization_id"]), request["idempotency_key"]
        )

    def execute(self, authorization: Any, idempotency_key: str) -> dict[str, Any]:
        if not isinstance(idempotency_key, str) or not 8 <= len(idempotency_key) <= 160:
            raise RoadExecutionError(
                "The idempotency key is invalid.", code="invalid_idempotency_key", status=400
            )
        key_hash = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
        with self._execution_lock():
            archive_hash = self._verify_source()
            checked = self.verifier.verify(authorization, observed_archive_sha256=archive_hash)
            execution_id = (
                "road-exec-"
                + canonical_sha256(
                    {
                        "authorization_sha256": checked["authorization_sha256"],
                        "execution_contract_version": EXECUTION_CONTRACT_VERSION,
                    }
                )[:24]
            )
            replay = self._existing_execution(execution_id, checked, key_hash)
            if replay is not None:
                return replay
            receipt = self._execute_atomic(checked, execution_id, key_hash)
            self._write_ledger_from_execution(execution_id)
            return receipt

    def _ledger_path(self) -> Path:
        return self.ledger_root / f"{EXPECTED_AUTHORIZATION_SHA256}.json"

    def _existing_execution(
        self, execution_id: str, authorization: Mapping[str, Any], key_hash: str
    ) -> dict[str, Any] | None:
        target = self.executions_root / execution_id
        ledger_path = self._ledger_path()
        record_path = target / "consumption.json"
        if ledger_path.is_file():
            ledger = _read_json(ledger_path, code="execution_conflict")
            if ledger.get("execution_id") != execution_id:
                raise RoadExecutionError(
                    "The authorization ledger conflicts.", code="execution_conflict"
                )
        if not target.exists() and not ledger_path.exists():
            return None
        if not target.is_dir() or not record_path.is_file():
            raise RoadExecutionError(
                "The authorization consumption state conflicts.", code="execution_conflict"
            )
        consumption = _read_json(record_path, code="execution_conflict")
        if (
            consumption.get("authorization_sha256") != authorization["authorization_sha256"]
            or consumption.get("execution_id") != execution_id
        ):
            raise RoadExecutionError(
                "The authorization consumption record conflicts.", code="execution_conflict"
            )
        if consumption.get("idempotency_key_sha256") != key_hash:
            raise RoadExecutionError(
                "The frozen authorization was already consumed with another idempotency key.",
                code="authorization_already_consumed",
                status=409,
            )
        receipt = self.get_execution(execution_id)
        if receipt.get("receipt_sha256") != consumption.get("receipt_sha256"):
            raise RoadExecutionError(
                "The immutable execution receipt conflicts.", code="execution_conflict"
            )
        if not ledger_path.is_file():
            self._write_ledger_from_execution(execution_id)
        return receipt

    def _write_ledger_from_execution(self, execution_id: str) -> None:
        consumption = _read_json(
            self.executions_root / execution_id / "consumption.json", code="execution_conflict"
        )
        self.ledger_root.mkdir(parents=True, exist_ok=True)
        temporary = self._ledger_path().with_suffix(".json.tmp")
        _write_json(temporary, consumption)
        os.replace(temporary, self._ledger_path())

    def _extract_geometry(
        self, stage: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        component_root = stage / "source-components"
        component_root.mkdir(parents=True, exist_ok=False)
        try:
            sources, _ = extract_reviewed_source_layers(
                self.archive_path, [EXPECTED_SOURCE_LAYER], component_root
            )
        except (OSError, RealLayerError) as error:
            raise RoadExecutionError(
                "K14_ROAD is missing or incomplete.", code="source_layer_missing"
            ) from error
        if len(sources) != 1:
            raise RoadExecutionError(
                "K14_ROAD is missing or ambiguous.", code="source_layer_missing"
            )
        source_path = sources[0]
        inspection = inspect_dataset(source_path)
        required_fields = {"ROADSEGID", "TERRAINID", "ROADNUM", "ROADNUM1", "ROADNUM2", "ROADNAME"}
        fields = {
            item.get("name") for item in inspection.get("fields", []) if isinstance(item, Mapping)
        }
        if (
            not inspection.get("available")
            or inspection.get("layer") != EXPECTED_SOURCE_LAYER
            or inspection.get("geometry_type") != "LineString"
            or inspection.get("crs_name") != EXPECTED_SOURCE_CRS
            or inspection.get("feature_count") != 196
            or not required_fields.issubset(fields)
        ):
            raise RoadExecutionError(
                "K14_ROAD does not match the reviewed source contract.", code="source_layer_missing"
            )
        try:
            source_collection, _ = read_vector_dataset(source_path)
        except (OSError, RuntimeError, ValueError) as error:
            raise RoadExecutionError(
                "K14_ROAD could not be read.", code="source_layer_missing"
            ) from error
        source_features = _ordered_features(source_collection, runtime=False)

        ogr2ogr = shutil.which("ogr2ogr")
        if ogr2ogr is None:
            raise RoadExecutionError(
                "GDAL/OGR is required for the explicit runtime projection.",
                code="runtime_translation_failed",
                status=503,
            )
        runtime_raw = stage / "runtime-raw.geojson"
        where = "ROADSEGID IN ('" + "','".join(EXPECTED_SEGMENT_IDS) + "')"
        try:
            subprocess.run(
                [
                    ogr2ogr,
                    "-f",
                    "GeoJSON",
                    str(runtime_raw),
                    str(source_path),
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
            runtime_collection = _read_json(runtime_raw, code="runtime_translation_failed")
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            raise RoadExecutionError(
                "The explicit ROAD runtime projection failed.", code="runtime_translation_failed"
            ) from error
        runtime_features = _ordered_features(runtime_collection, runtime=True)
        records = _geometry_records(source_features, runtime_features)
        _verify_continuity(records)
        return source_features, runtime_features, records

    def _collections(
        self,
        source_features: list[dict[str, Any]],
        runtime_features: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        source = {
            "type": "FeatureCollection",
            "nma:provenance": {
                "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                "source_layer": EXPECTED_SOURCE_LAYER,
                "source_crs": EXPECTED_SOURCE_CRS,
                "geometry_operation": "selection-only; native coordinates unchanged",
                "ordered_segment_ids": list(EXPECTED_SEGMENT_IDS),
            },
            "features": source_features,
        }
        runtime = {
            "type": "FeatureCollection",
            "nma:provenance": {
                "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                "source_layer": EXPECTED_SOURCE_LAYER,
                "source_crs": EXPECTED_SOURCE_CRS,
                "runtime_crs": RUNTIME_CRS,
                "transformation_method": "GDAL/OGR coordinate transformation; XY vertices preserved",
                "ordered_segment_ids": list(EXPECTED_SEGMENT_IDS),
            },
            "features": runtime_features,
        }
        return source, runtime

    def build_plan(
        self,
        authorization: Mapping[str, Any],
        execution_id: str,
        geometry_records: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        base = {
            "schema": EXECUTION_PLAN_SCHEMA,
            "execution_contract_version": EXECUTION_CONTRACT_VERSION,
            "execution_id": execution_id,
            "authorization": {
                "authorization_id": authorization["authorization_id"],
                "authorization_sha256": authorization["authorization_sha256"],
            },
            "frozen_identities": deepcopy(authorization["frozen_identities"]),
            "source": {
                "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                "layer": EXPECTED_SOURCE_LAYER,
                "source_crs": EXPECTED_SOURCE_CRS,
                "runtime_crs": RUNTIME_CRS,
                "ordered_segment_ids": list(EXPECTED_SEGMENT_IDS),
                "geometry": deepcopy(list(geometry_records)),
            },
            "scope": {
                "route_identity": EXPECTED_ROUTE_IDENTITY,
                "class_code": EXPECTED_CLASS_CODE,
                "feature_count": 3,
            },
            "portrayal": deepcopy(EXPECTED_PORTRAYAL),
            "runtime_translation": {
                "geometry": "explicit EPSG:4326 derivative with unchanged vertex count",
                "road_name": "MapLibre symbol-placement=line with literal authorized annotation",
                "shield_resolution_mode": "semantic_binding_only",
                "shield_renderer": None,
            },
            "targets": {
                "derived_portrayal": "derived-portrayal.json",
                "source_geometry": "data/road-centreline-source.geojson",
                "runtime_geometry": "data/road-centreline-runtime.geojson",
                "candidate_runtime": "bundle.json",
                "receipt": "receipt.json",
                "rollback_manifest": "rollback-manifest.json",
            },
            "permissions": deepcopy(EXPECTED_PERMISSIONS),
        }
        identity = canonical_sha256(base)
        base["execution_plan_id"] = "road-plan-" + identity[:24]
        return _hash_record(base, "execution_plan_sha256")

    def _build_derived(
        self,
        authorization: Mapping[str, Any],
        execution_id: str,
        plan: Mapping[str, Any],
        geometry_records: Sequence[Mapping[str, Any]],
        source_file_sha256: str,
        runtime_file_sha256: str,
    ) -> dict[str, Any]:
        base = {
            "schema": DERIVED_PORTRAYAL_SCHEMA,
            "execution_id": execution_id,
            "execution_plan": {
                "id": plan["execution_plan_id"],
                "sha256": plan["execution_plan_sha256"],
            },
            "authorization": {
                "id": authorization["authorization_id"],
                "sha256": authorization["authorization_sha256"],
            },
            "frozen_identities": deepcopy(authorization["frozen_identities"]),
            "source": {
                "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                "layer": EXPECTED_SOURCE_LAYER,
                "route_identity": EXPECTED_ROUTE_IDENTITY,
                "class_code": EXPECTED_CLASS_CODE,
                "ordered_segment_ids": list(EXPECTED_SEGMENT_IDS),
            },
            "geometry_provenance": deepcopy(list(geometry_records)),
            "portrayal": deepcopy(EXPECTED_PORTRAYAL),
            "runtime_translation": deepcopy(plan["runtime_translation"]),
            "outputs": {
                "source_geometry": {
                    "path": "data/road-centreline-source.geojson",
                    "sha256": source_file_sha256,
                },
                "runtime_geometry": {
                    "path": "data/road-centreline-runtime.geojson",
                    "sha256": runtime_file_sha256,
                },
            },
            "governance": {
                "source_mutation_performed": False,
                "topology_repair_performed": False,
                "roada_execution_performed": False,
                "road_edge_derivation_performed": False,
            },
        }
        identity = canonical_sha256(base)
        base["artifact_id"] = "road-derived-" + identity[:24]
        return _hash_record(base, "artifact_sha256")

    def _build_bundle(self, execution_id: str, derived: Mapping[str, Any]) -> dict[str, Any]:
        source_id = f"nma-road-source-{execution_id}"
        label_id = f"nma-road-label-{execution_id}"
        base = {
            "schema": RUNTIME_BUNDLE_SCHEMA,
            "bundle_id": f"road-bundle-{execution_id}",
            "execution_id": execution_id,
            "derived_portrayal": {
                "id": derived["artifact_id"],
                "sha256": derived["artifact_sha256"],
            },
            "source": {
                "id": source_id,
                "type": "geojson",
                "data": f"/api/road/executions/{execution_id}/data",
                "crs": RUNTIME_CRS,
                "expected_feature_count": 3,
            },
            "layers": [
                {
                    "id": label_id,
                    "type": "symbol",
                    "source": source_id,
                    "layout": {
                        "symbol-placement": "line",
                        "text-field": ["literal", "中山街"],
                    },
                    "semantic_role": "authorized-road-name-annotation",
                }
            ],
            "shield_binding": {
                "shield_code": "9490005",
                "shield_orientation": "road-parallel",
                "status": "semantic_binding_only",
                "resolver_identity": None,
                "resolved_artifact_sha256": None,
            },
            "scope": {
                "route_identity": EXPECTED_ROUTE_IDENTITY,
                "class_code": EXPECTED_CLASS_CODE,
                "ordered_segment_ids": list(EXPECTED_SEGMENT_IDS),
                "graphic_element_roles": [2, 5],
            },
            "canonical_runtime_mutation_performed": False,
        }
        return _hash_record(base, "bundle_sha256")

    def _build_receipt(
        self,
        authorization: Mapping[str, Any],
        execution_id: str,
        plan: Mapping[str, Any],
        derived: Mapping[str, Any],
        bundle: Mapping[str, Any],
        geometry_records: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        base = {
            "schema": EXECUTION_RECEIPT_SCHEMA,
            "receipt_id": f"road-receipt-{execution_id}",
            "execution_id": execution_id,
            "completed_at": _now_timestamp(self._now),
            "execution_plan": {
                "id": plan["execution_plan_id"],
                "sha256": plan["execution_plan_sha256"],
            },
            "authorization": {
                "id": authorization["authorization_id"],
                "sha256": authorization["authorization_sha256"],
            },
            "frozen_identities": deepcopy(authorization["frozen_identities"]),
            "source": {
                "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                "layer": EXPECTED_SOURCE_LAYER,
            },
            "scope": {
                "route_identity": EXPECTED_ROUTE_IDENTITY,
                "class_code": EXPECTED_CLASS_CODE,
                "ordered_segment_ids": list(EXPECTED_SEGMENT_IDS),
            },
            "source_geometry_sha256": [
                record["source_geometry_sha256"] for record in geometry_records
            ],
            "derived_portrayal": {
                "id": derived["artifact_id"],
                "sha256": derived["artifact_sha256"],
            },
            "runtime_bundle": {
                "id": bundle["bundle_id"],
                "sha256": bundle["bundle_sha256"],
            },
            "shield_runtime_status": "semantic_binding_only",
            "rollback_manifest_target": "rollback-manifest.json",
            "governance": {
                "data_execution_performed": True,
                "authoritative_source_mutation_performed": False,
                "topology_repair_performed": False,
                "roada_execution_performed": False,
                "road_edge_derivation_performed": False,
                "canonical_runtime_mutation_performed": False,
            },
        }
        return _hash_record(base, "receipt_sha256", ignored_identity_fields=("completed_at",))

    def _build_rollback_manifest(
        self,
        execution_id: str,
        receipt: Mapping[str, Any],
        bundle: Mapping[str, Any],
        removable: Sequence[tuple[str, str, str]],
    ) -> dict[str, Any]:
        base = {
            "schema": ROLLBACK_MANIFEST_SCHEMA,
            "rollback_manifest_id": f"road-rollback-{execution_id}",
            "execution_id": execution_id,
            "receipt": {"id": receipt["receipt_id"], "sha256": receipt["receipt_sha256"]},
            "bundle": {"id": bundle["bundle_id"], "sha256": bundle["bundle_sha256"]},
            "rollback_root": ".",
            "artifacts": [
                {"path": path, "sha256": sha256, "role": role} for path, sha256, role in removable
            ],
            "runtime_ids": {
                "source_ids": [bundle["source"]["id"]],
                "layer_ids": [layer["id"] for layer in bundle["layers"]],
            },
            "allowed_removal_operations": ["remove-file"],
            "preserve_paths": [
                "authorization.json",
                "plan.json",
                "receipt.json",
                "rollback-manifest.json",
                "consumption.json",
                "observations",
            ],
            "status": "ready",
        }
        return _hash_record(base, "rollback_manifest_sha256")

    def _execute_atomic(
        self, authorization: Mapping[str, Any], execution_id: str, key_hash: str
    ) -> dict[str, Any]:
        stage = self.staging_root / execution_id
        target = self.executions_root / execution_id
        if stage.exists():
            shutil.rmtree(stage)
        if target.exists():
            raise RoadExecutionError(
                "The ROAD execution target already exists.", code="execution_conflict"
            )
        stage.mkdir(parents=True, exist_ok=False)
        try:
            _write_json(stage / "authorization.json", authorization)
            source_features, runtime_features, geometry_records = self._extract_geometry(stage)
            source_collection, runtime_collection = self._collections(
                source_features, runtime_features
            )
            source_path = stage / "data/road-centreline-source.geojson"
            runtime_path = stage / "data/road-centreline-runtime.geojson"
            _write_json(source_path, source_collection)
            _write_json(runtime_path, runtime_collection)
            plan = self.build_plan(authorization, execution_id, geometry_records)
            _write_json(stage / "plan.json", plan)
            derived = self._build_derived(
                authorization,
                execution_id,
                plan,
                geometry_records,
                file_sha256(source_path),
                file_sha256(runtime_path),
            )
            _write_json(stage / "derived-portrayal.json", derived)
            bundle = self._build_bundle(execution_id, derived)
            _write_json(stage / "bundle.json", bundle)
            receipt = self._build_receipt(
                authorization, execution_id, plan, derived, bundle, geometry_records
            )
            _write_json(stage / "receipt.json", receipt)
            removable = [
                ("bundle.json", file_sha256(stage / "bundle.json"), "candidate-runtime-bundle"),
                (
                    "derived-portrayal.json",
                    file_sha256(stage / "derived-portrayal.json"),
                    "derived-portrayal",
                ),
                (
                    "data/road-centreline-source.geojson",
                    file_sha256(source_path),
                    "selected-native-geometry",
                ),
                (
                    "data/road-centreline-runtime.geojson",
                    file_sha256(runtime_path),
                    "candidate-runtime-geometry",
                ),
            ]
            manifest = self._build_rollback_manifest(execution_id, receipt, bundle, removable)
            _write_json(stage / "rollback-manifest.json", manifest)
            consumption = {
                "schema": "nma.road-authorization-consumption/1.0",
                "authorization_id": authorization["authorization_id"],
                "authorization_sha256": authorization["authorization_sha256"],
                "execution_id": execution_id,
                "idempotency_key_sha256": key_hash,
                "receipt_id": receipt["receipt_id"],
                "receipt_sha256": receipt["receipt_sha256"],
            }
            _write_json(stage / "consumption.json", consumption)
            if file_sha256(self.archive_path) != EXPECTED_ARCHIVE_SHA256:
                raise RoadExecutionError(
                    "The private source changed during execution.",
                    code="source_archive_hash_mismatch",
                )
            shutil.rmtree(stage / "source-components")
            runtime_raw = stage / "runtime-raw.geojson"
            if runtime_raw.exists():
                runtime_raw.unlink()
            self.executions_root.mkdir(parents=True, exist_ok=True)
            os.replace(stage, target)
            return receipt
        except RoadExecutionError:
            shutil.rmtree(stage, ignore_errors=True)
            raise
        except Exception as error:
            shutil.rmtree(stage, ignore_errors=True)
            raise RoadExecutionError(
                "ROAD-04 atomic execution failed.", code="road04_execution_failed"
            ) from error

    def _execution_path(self, execution_id: str) -> Path:
        _require_identifier(execution_id, "execution_id")
        path = self.executions_root / execution_id
        if not path.is_dir():
            raise RoadExecutionError(
                "The ROAD-04 execution was not found.", code="execution_not_found", status=404
            )
        return path

    def _read_execution_json(self, execution_id: str, name: str) -> dict[str, Any]:
        return _read_json(self._execution_path(execution_id) / name, code="execution_conflict")

    def get_execution(self, execution_id: str) -> dict[str, Any]:
        return self._read_execution_json(execution_id, "receipt.json")

    def get_bundle(self, execution_id: str) -> dict[str, Any]:
        return self._read_execution_json(execution_id, "bundle.json")

    def get_data(self, execution_id: str) -> dict[str, Any]:
        return self._read_execution_json(execution_id, "data/road-centreline-runtime.geojson")

    def observe(self, execution_id: str, payload: Any) -> dict[str, Any]:
        required = {
            "state",
            "client_session",
            "source_ids",
            "layer_ids",
            "observed_feature_count",
            "runtime_version",
            "status",
        }
        if not isinstance(payload, dict) or set(payload) != required:
            raise RoadExecutionError(
                "The ROAD runtime observation has an invalid shape.",
                code="invalid_observation",
                status=400,
            )
        bundle = self.get_bundle(execution_id)
        expected_sources = [bundle["source"]["id"]]
        expected_layers = [layer["id"] for layer in bundle["layers"]]
        if payload["state"] not in {"activate", "verify", "rollback"}:
            raise RoadExecutionError(
                "The ROAD runtime observation state is invalid.", code="invalid_observation"
            )
        if payload["source_ids"] != expected_sources or payload["layer_ids"] != expected_layers:
            raise RoadExecutionError(
                "The ROAD runtime identifiers do not match.", code="invalid_observation"
            )
        if payload["observed_feature_count"] != 3:
            raise RoadExecutionError(
                "The ROAD runtime feature count does not match.", code="invalid_observation"
            )
        client_session = _require_identifier(payload["client_session"], "client_session")
        runtime_version = payload["runtime_version"]
        if not isinstance(runtime_version, str) or not runtime_version or len(runtime_version) > 80:
            raise RoadExecutionError(
                "The ROAD runtime version is invalid.", code="invalid_observation"
            )
        if payload["status"] not in {"observed", "verified", "removed", "failed"}:
            raise RoadExecutionError(
                "The ROAD runtime status is invalid.", code="invalid_observation"
            )
        identity_basis = {
            "execution_id": execution_id,
            "bundle_sha256": bundle["bundle_sha256"],
            "payload": payload,
        }
        base = {
            "schema": RUNTIME_OBSERVATION_SCHEMA,
            "observation_id": "road-observation-" + canonical_sha256(identity_basis)[:24],
            "execution_id": execution_id,
            "bundle_sha256": bundle["bundle_sha256"],
            "client_session": client_session,
            "state": payload["state"],
            "source_ids": expected_sources,
            "layer_ids": expected_layers,
            "observed_feature_count": 3,
            "runtime_version": runtime_version,
            "timestamp": _now_timestamp(self._now),
            "status": payload["status"],
            "loaded_candidate_representation": payload["status"] in {"observed", "verified"},
            "final_qa": False,
        }
        observation = _hash_record(
            base, "observation_sha256", ignored_identity_fields=("timestamp",)
        )
        path = (
            self._execution_path(execution_id)
            / "observations"
            / (observation["observation_id"] + ".json")
        )
        _write_json(path, observation)
        return observation

    def rollback_execution(self, execution_id: str) -> dict[str, Any]:
        with self._execution_lock():
            root = self._execution_path(execution_id)
            result_path = root / "rollback-result.json"
            if result_path.is_file():
                return _read_json(result_path, code="rollback_precondition_failed")
            manifest = self._read_execution_json(execution_id, "rollback-manifest.json")
            supplied = manifest.get("rollback_manifest_sha256")
            basis = deepcopy(manifest)
            basis.pop("rollback_manifest_sha256", None)
            if supplied != canonical_sha256(basis):
                raise RoadExecutionError(
                    "The ROAD rollback manifest hash changed.",
                    code="rollback_precondition_failed",
                )
            artifacts = manifest.get("artifacts")
            if not isinstance(artifacts, list):
                raise RoadExecutionError(
                    "The ROAD rollback manifest is invalid.", code="rollback_precondition_failed"
                )
            verified: list[Path] = []
            for item in artifacts:
                if not isinstance(item, Mapping) or set(item) != {"path", "sha256", "role"}:
                    raise RoadExecutionError(
                        "The ROAD rollback entry is invalid.", code="rollback_precondition_failed"
                    )
                relative = PurePosixPath(str(item["path"]))
                if relative.is_absolute() or ".." in relative.parts:
                    raise RoadExecutionError(
                        "The ROAD rollback path is unsafe.", code="rollback_precondition_failed"
                    )
                path = root.joinpath(*relative.parts)
                if not path.is_file() or file_sha256(path) != item["sha256"]:
                    raise RoadExecutionError(
                        "A ROAD candidate artifact changed; rollback stopped before removal.",
                        code="rollback_precondition_failed",
                    )
                verified.append(path)
            for path in verified:
                path.unlink()
            data_root = root / "data"
            if data_root.is_dir() and not any(data_root.iterdir()):
                data_root.rmdir()
            result_base = {
                "schema": "nma.road-rollback-result/1.0",
                "rollback_id": f"road-rollback-result-{execution_id}",
                "execution_id": execution_id,
                "rollback_manifest_sha256": supplied,
                "status": "rolled_back",
                "removed_paths": [item["path"] for item in artifacts],
                "receipt_preserved": True,
                "receipt_sha256": manifest["receipt"]["sha256"],
            }
            result = _hash_record(result_base, "rollback_result_sha256")
            _write_json(result_path, result)
            receipt = self.get_execution(execution_id)
            if receipt.get("receipt_sha256") != manifest["receipt"]["sha256"]:
                raise RoadExecutionError(
                    "Rollback did not preserve the ROAD receipt.",
                    code="rollback_precondition_failed",
                )
            return result


def rollback_execution(engine: RoadExecutionEngine, execution_id: str) -> dict[str, Any]:
    return engine.rollback_execution(execution_id)

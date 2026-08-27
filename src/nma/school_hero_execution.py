from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
from threading import Lock
from typing import Any, Callable

from nma.core import canonical_json, canonical_sha256
from nma.real_layer import (
    REAL_LAYER_PLAN_SCHEMA,
    REAL_LAYER_PROFILES,
    RealLayerError,
    execute_real_layer,
    file_sha256,
)


AUTHORIZATION_SCHEMA = "nma.symbol-edit-authorization/1.0"
EXECUTION_PLAN_SCHEMA = "nma.school-hero-execution-plan/1.0"
RUNTIME_BUNDLE_SCHEMA = "nma.maplibre-runtime-bundle/1.0"
EXECUTION_RECEIPT_SCHEMA = "nma.school-hero-execution-receipt/1.0"
RUNTIME_OBSERVATION_SCHEMA = "nma.runtime-layer-observation/1.0"
ROLLBACK_MANIFEST_SCHEMA = "nma.rollback-manifest/1.0"
RUNTIME_CONTRACT = "nma.runtime-baseline/0.32"
SCHOOL_PROFILE_ID = "school-point"
SCHOOL_FEATURE_CODE = "9920103"
SCHOOL_GEOMETRY = "Point"
REQUIRED_SCOPE = {
    "derived-real-layer",
    "derived-portrayal",
    "candidate-maplibre-layer",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
SAFE_SYMBOL_PATH = "assets/symbols/nlsc112v5.4/school.svg"


class SchoolHeroExecutionError(ValueError):
    """HERO-04 rejected an invalid authorization or unsafe execution."""

    def __init__(self, message: str, *, code: str = "hero04_execution_failed", status: int = 422):
        super().__init__(message)
        self.code = code
        self.status = status


def authorization_sha256(authorization: dict[str, Any]) -> str:
    basis = deepcopy(authorization)
    basis.pop("authorization_hash", None)
    return canonical_sha256(basis)


def _require_identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise SchoolHeroExecutionError(f"The authorization {label} is invalid.")
    return value


def _parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise SchoolHeroExecutionError(f"The authorization {label} is invalid.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SchoolHeroExecutionError(f"The authorization {label} is invalid.") from error
    if parsed.tzinfo is None:
        raise SchoolHeroExecutionError(f"The authorization {label} must include a timezone.")
    return parsed.astimezone(timezone.utc)


def _identity(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"code", "geometry_role"}:
        raise SchoolHeroExecutionError(f"The authorization {label} is invalid.")
    if value["code"] != SCHOOL_FEATURE_CODE or value["geometry_role"] != SCHOOL_GEOMETRY:
        raise SchoolHeroExecutionError(
            "The authorization feature identity is outside HERO-04 scope."
        )
    return {"code": value["code"], "geometry_role": value["geometry_role"]}


def _baseline(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"id", "sha256"}:
        raise SchoolHeroExecutionError(f"The authorization {label} is invalid.")
    _require_identifier(value["id"], f"{label}.id")
    if not isinstance(value["sha256"], str) or not SHA256.fullmatch(value["sha256"]):
        raise SchoolHeroExecutionError(f"The authorization {label}.sha256 is invalid.")
    return {"id": value["id"], "sha256": value["sha256"]}


def _approved_operations(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not 1 <= len(value) <= 12:
        raise SchoolHeroExecutionError("The authorization must contain 1–12 approved operations.")
    checked: list[dict[str, Any]] = []
    for operation in value:
        if not isinstance(operation, dict) or set(operation) != {"action", "target", "value"}:
            raise SchoolHeroExecutionError("An approved portrayal operation has an invalid shape.")
        action = operation["action"]
        target = operation["target"]
        detail = operation["value"]
        if action == "set_color":
            if target not in {"symbol", "marker", "portrayal"}:
                raise SchoolHeroExecutionError("The approved colour target is unsupported.")
            if not isinstance(detail, dict) or set(detail) != {"color"}:
                raise SchoolHeroExecutionError("The approved colour value is invalid.")
            if not isinstance(detail["color"], str) or not COLOR.fullmatch(detail["color"]):
                raise SchoolHeroExecutionError("The approved colour is invalid.")
        elif action in {"set_opacity", "set_scale", "set_rotation"}:
            if target not in {"symbol", "marker", "portrayal"}:
                raise SchoolHeroExecutionError("The approved portrayal target is unsupported.")
            if not isinstance(detail, dict) or set(detail) != {"number"}:
                raise SchoolHeroExecutionError("The approved numeric value is invalid.")
            number = detail["number"]
            if (
                isinstance(number, bool)
                or not isinstance(number, (int, float))
                or not math.isfinite(number)
            ):
                raise SchoolHeroExecutionError("The approved numeric value is invalid.")
            bounds = {
                "set_opacity": (0.1, 1.0),
                "set_scale": (0.5, 3.0),
                "set_rotation": (-180.0, 180.0),
            }[action]
            if not bounds[0] <= number <= bounds[1]:
                raise SchoolHeroExecutionError("The approved numeric value is out of bounds.")
        else:
            raise SchoolHeroExecutionError("The approved portrayal operation is unsupported.")
        checked.append(deepcopy(operation))
    return checked


class ExecutionAuthorizationVerifier:
    """Verify the complete HERO-03 handoff; a bare approval can never pass."""

    required_fields = {
        "schema",
        "authorization_id",
        "authorization_hash",
        "status",
        "execution_performed",
        "proposal_id",
        "proposal_revision",
        "proposal_payload",
        "proposal_payload_sha256",
        "feature_identity",
        "baseline_identity",
        "validation_result",
        "human_approval",
        "approved_operations",
        "portrayal_reference",
        "source_archive_sha256",
        "execution_scope",
        "expires_at",
        "invalidation_status",
    }

    def __init__(self, *, now: Callable[[], datetime] | None = None):
        self._now = now or (lambda: datetime.now(timezone.utc))

    def verify(self, authorization: Any) -> dict[str, Any]:
        if not isinstance(authorization, dict) or not self.required_fields.issubset(authorization):
            raise SchoolHeroExecutionError("A complete HERO-03 ExecutionAuthorization is required.")
        if authorization["schema"] != AUTHORIZATION_SCHEMA:
            raise SchoolHeroExecutionError("The execution authorization schema is unsupported.")
        authorization_id = _require_identifier(
            authorization["authorization_id"], "authorization_id"
        )
        supplied_hash = authorization["authorization_hash"]
        if not isinstance(supplied_hash, str) or not SHA256.fullmatch(supplied_hash):
            raise SchoolHeroExecutionError("The authorization hash is invalid.")
        if supplied_hash != authorization_sha256(authorization):
            raise SchoolHeroExecutionError("The authorization hash does not match its payload.")
        if authorization["status"] != "ready_for_execution":
            raise SchoolHeroExecutionError("The authorization is not ready for execution.")
        if authorization["execution_performed"] is not False:
            raise SchoolHeroExecutionError("The authorization has already been executed.")

        proposal_id = _require_identifier(authorization["proposal_id"], "proposal_id")
        revision = authorization["proposal_revision"]
        if isinstance(revision, bool) or not isinstance(revision, (str, int)) or revision == "":
            raise SchoolHeroExecutionError("The proposal revision is invalid.")
        payload = authorization["proposal_payload"]
        if not isinstance(payload, dict):
            raise SchoolHeroExecutionError("The authorized proposal payload is missing.")
        proposal_hash = authorization["proposal_payload_sha256"]
        if not isinstance(proposal_hash, str) or not SHA256.fullmatch(proposal_hash):
            raise SchoolHeroExecutionError("The proposal hash is invalid.")
        if canonical_sha256(payload) != proposal_hash:
            raise SchoolHeroExecutionError("The proposal hash does not match its payload.")

        feature = _identity(authorization["feature_identity"], "feature_identity")
        baseline = _baseline(authorization["baseline_identity"], "baseline_identity")
        operations = _approved_operations(authorization["approved_operations"])
        if payload.get("proposal_id") != proposal_id or payload.get("revision") != revision:
            raise SchoolHeroExecutionError(
                "The proposal identity does not match the authorization."
            )
        if (
            payload.get("feature_identity") != feature
            or payload.get("baseline_identity") != baseline
        ):
            raise SchoolHeroExecutionError("The proposal feature or baseline identity changed.")
        if payload.get("operations") != operations:
            raise SchoolHeroExecutionError("The approved operations do not match the proposal.")

        identity = {
            "proposal_id": proposal_id,
            "proposal_revision": revision,
            "proposal_payload_sha256": proposal_hash,
            "feature_identity": feature,
            "baseline_identity": baseline,
        }
        validation = authorization["validation_result"]
        if not isinstance(validation, dict) or validation.get("status") != "passed":
            raise SchoolHeroExecutionError("The proposal validation result is not passed.")
        if any(validation.get(key) != value for key, value in identity.items()):
            raise SchoolHeroExecutionError("The validation identity does not match the proposal.")
        approval = authorization["human_approval"]
        if not isinstance(approval, dict) or approval.get("decision") != "approved":
            raise SchoolHeroExecutionError("Explicit human approval is required.")
        if approval.get("actor_type") != "human":
            raise SchoolHeroExecutionError("The approval actor must be human.")
        if any(approval.get(key) != value for key, value in identity.items()):
            raise SchoolHeroExecutionError(
                "The human approval identity does not match the proposal."
            )
        if approval.get("approved_operations_sha256") != canonical_sha256(operations):
            raise SchoolHeroExecutionError("The approved operation hash does not match.")

        source_hash = authorization["source_archive_sha256"]
        if not isinstance(source_hash, str) or not SHA256.fullmatch(source_hash):
            raise SchoolHeroExecutionError("The approved source archive hash is invalid.")
        portrayal = authorization["portrayal_reference"]
        if not isinstance(portrayal, dict) or portrayal.get("asset_path") != SAFE_SYMBOL_PATH:
            raise SchoolHeroExecutionError(
                "The portrayal reference is outside the reviewed baseline."
            )
        if portrayal.get("baseline_identity") != baseline:
            raise SchoolHeroExecutionError("The portrayal baseline identity changed.")
        if portrayal.get("approved_operations_sha256") != canonical_sha256(operations):
            raise SchoolHeroExecutionError("The portrayal operation reference changed.")

        scope = authorization["execution_scope"]
        if not isinstance(scope, list) or any(not isinstance(item, str) for item in scope):
            raise SchoolHeroExecutionError("The authorization execution scope is invalid.")
        if not REQUIRED_SCOPE.issubset(scope):
            raise SchoolHeroExecutionError("The authorization execution scope is incomplete.")
        if authorization["invalidation_status"] != "valid":
            raise SchoolHeroExecutionError("The authorization was invalidated.")
        now = self._now().astimezone(timezone.utc)
        if _parse_timestamp(authorization["expires_at"], "expires_at") <= now:
            raise SchoolHeroExecutionError("The authorization expired.")
        if (
            "issued_at" in authorization
            and _parse_timestamp(authorization["issued_at"], "issued_at") > now
        ):
            raise SchoolHeroExecutionError("The authorization issue time is in the future.")

        checked = deepcopy(authorization)
        checked["authorization_id"] = authorization_id
        checked["approved_operations"] = operations
        return checked


class ExecutionAuthorizationStore:
    """Filesystem handoff from HERO-03; clients submit only an authorization id."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def path_for(self, authorization_id: str) -> Path:
        _require_identifier(authorization_id, "authorization_id")
        return self.root / f"{authorization_id}.json"

    def load(self, authorization_id: str) -> dict[str, Any]:
        path = self.path_for(authorization_id)
        if not path.is_file():
            raise SchoolHeroExecutionError(
                "The execution authorization was not found.",
                code="authorization_not_found",
                status=404,
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SchoolHeroExecutionError("The stored authorization is unreadable.") from error
        if payload.get("authorization_id") != authorization_id:
            raise SchoolHeroExecutionError("The stored authorization identity does not match.")
        return payload

    def save(self, authorization: dict[str, Any]) -> Path:
        authorization_id = _require_identifier(
            authorization.get("authorization_id"), "authorization_id"
        )
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.path_for(authorization_id)
        temporary = target.with_suffix(".json.tmp")
        temporary.write_bytes(canonical_json(authorization) + b"\n")
        os.replace(temporary, target)
        return target


def _utc_timestamp(now: Callable[[], datetime]) -> str:
    return now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value) + b"\n")


def _hash_record(value: dict[str, Any], hash_field: str) -> dict[str, Any]:
    record = deepcopy(value)
    record[hash_field] = canonical_sha256(record)
    return record


def _real_layer_plan(execution_plan: dict[str, Any]) -> dict[str, Any]:
    profile = REAL_LAYER_PROFILES[SCHOOL_PROFILE_ID]
    basis = {
        "schema": REAL_LAYER_PLAN_SCHEMA,
        "profile_id": SCHOOL_PROFILE_ID,
        "feature_code": SCHOOL_FEATURE_CODE,
        "feature_name": profile["feature_name"],
        "geometry_role": SCHOOL_GEOMETRY,
        "product_layer": profile["product_layer"],
        "source_archive_sha256": execution_plan["source_archive_sha256"],
        "source_layers": profile["source_layer_ids"],
        "source_filter": execution_plan["source_filter"],
        "field_mapping": execution_plan["field_mapping"],
        "operations": [
            "extract-reviewed-components",
            "filter",
            "reproject-to-epsg-4326",
            "drop-z",
        ],
        "expected_feature_count": profile["expected_feature_count"],
        "evidence_node_ids": profile["evidence_node_ids"],
        "citation_ids": ["hero03-authorization:" + execution_plan["authorization_id"]],
        "source_schema_boundary": profile["source_schema_boundary"],
    }
    plan_id = "real-layer-plan:" + canonical_sha256(basis)[:20]
    return {
        **basis,
        "plan_id": plan_id,
        "status": "proposed",
        "execution_performed": False,
    }


def _coordinate_is_xy(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(
            not isinstance(item, bool) and isinstance(item, (int, float)) and math.isfinite(item)
            for item in value
        )
    )


def _validate_school_geojson(path: Path) -> dict[str, Any]:
    try:
        collection = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SchoolHeroExecutionError("The materialized GeoJSON is unreadable.") from error
    if collection.get("type") != "FeatureCollection":
        raise SchoolHeroExecutionError("The materialized output is not a FeatureCollection.")
    features = collection.get("features")
    if not isinstance(features, list) or len(features) != 15:
        raise SchoolHeroExecutionError("The materialized output must contain 15 features.")
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise SchoolHeroExecutionError("The materialized output contains an invalid feature.")
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") != "Point":
            raise SchoolHeroExecutionError("The materialized output must contain Point geometry.")
        if not _coordinate_is_xy(geometry.get("coordinates")):
            raise SchoolHeroExecutionError(
                "The materialized output must contain finite XY coordinates."
            )
        properties = feature.get("properties")
        if (
            not isinstance(properties, dict)
            or str(properties.get("TERRAINID")) != SCHOOL_FEATURE_CODE
        ):
            raise SchoolHeroExecutionError("A feature escaped the authorized TERRAINID filter.")
    provenance = collection.get("nma:provenance")
    if not isinstance(provenance, dict) or provenance.get("output_crs") != "EPSG:4326":
        raise SchoolHeroExecutionError("The materialized output CRS is not EPSG:4326.")
    if (
        provenance.get("synthetic") is not False
        or provenance.get("random_coordinates") is not False
    ):
        raise SchoolHeroExecutionError("Synthetic or random geometry is forbidden.")
    return collection


def _portrayal_values(operations: list[dict[str, Any]]) -> dict[str, Any]:
    values = {"color": "#111111", "opacity": 1.0, "scale": 1.0, "rotation": 0.0}
    for operation in operations:
        if operation["action"] == "set_color":
            values["color"] = operation["value"]["color"].lower()
        elif operation["action"] == "set_opacity":
            values["opacity"] = operation["value"]["number"]
        elif operation["action"] == "set_scale":
            values["scale"] = operation["value"]["number"]
        elif operation["action"] == "set_rotation":
            values["rotation"] = operation["value"]["number"]
    return values


def _materialize_asset(
    official_symbol_path: Path, destination: Path, operations: list[dict[str, Any]]
) -> dict[str, Any]:
    if not official_symbol_path.is_file():
        raise SchoolHeroExecutionError("The reviewed official symbol asset is unavailable.")
    original_hash = file_sha256(official_symbol_path)
    text = official_symbol_path.read_text(encoding="utf-8")
    values = _portrayal_values(operations)
    derived = re.sub(r'fill="#[0-9a-fA-F]{3,6}"', f'fill="{values["color"]}"', text)
    if values["color"] != "#111111" and derived == text:
        raise SchoolHeroExecutionError("The approved colour could not be materialized safely.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(derived, encoding="utf-8")
    if file_sha256(official_symbol_path) != original_hash:
        raise SchoolHeroExecutionError("The official symbol asset changed during execution.")
    return {
        "asset_path": "assets/school.svg",
        "asset_sha256": file_sha256(destination),
        "official_asset_sha256": original_hash,
        "approved_operations_sha256": canonical_sha256(operations),
        "values": values,
    }


class SchoolHeroExecutionEngine:
    """Atomically execute one hash-bound HERO-03 authorization on reviewed school data."""

    def __init__(
        self,
        *,
        storage_root: str | Path,
        archive_path: str | Path,
        official_symbol_path: str | Path,
        authorization_store: ExecutionAuthorizationStore | None = None,
        verifier: ExecutionAuthorizationVerifier | None = None,
        now: Callable[[], datetime] | None = None,
    ):
        self.storage_root = Path(storage_root)
        self.archive_path = Path(archive_path)
        self.official_symbol_path = Path(official_symbol_path)
        self.authorization_store = authorization_store or ExecutionAuthorizationStore(
            self.storage_root / "authorizations"
        )
        self.verifier = verifier or ExecutionAuthorizationVerifier(now=now)
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._lock = Lock()

    @property
    def staging_root(self) -> Path:
        return self.storage_root / ".staging"

    @property
    def executions_root(self) -> Path:
        return self.storage_root / "executions"

    def _index_path(self) -> Path:
        return self.storage_root / "idempotency-index.json"

    def _load_index(self) -> dict[str, Any]:
        path = self._index_path()
        if not path.is_file():
            return {"schema": "nma.school-hero-idempotency-index/1.0", "entries": []}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SchoolHeroExecutionError(
                "The execution idempotency index is unreadable."
            ) from error
        if value.get("schema") != "nma.school-hero-idempotency-index/1.0" or not isinstance(
            value.get("entries"), list
        ):
            raise SchoolHeroExecutionError("The execution idempotency index is invalid.")
        return value

    def _save_index(self, value: dict[str, Any]) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        temporary = self._index_path().with_suffix(".json.tmp")
        _write_json(temporary, value)
        os.replace(temporary, self._index_path())

    def execute_by_id(self, request: Any) -> dict[str, Any]:
        if not isinstance(request, dict) or set(request) != {"authorization_id", "idempotency_key"}:
            raise SchoolHeroExecutionError(
                "Expected authorization_id and idempotency_key only.",
                code="invalid_execution_request",
                status=400,
            )
        authorization_id = _require_identifier(request["authorization_id"], "authorization_id")
        idempotency_key = request["idempotency_key"]
        if not isinstance(idempotency_key, str) or not 8 <= len(idempotency_key) <= 160:
            raise SchoolHeroExecutionError(
                "The idempotency key is invalid.", code="invalid_idempotency_key", status=400
            )
        return self.execute(self.authorization_store.load(authorization_id), idempotency_key)

    def execute(self, authorization: Any, idempotency_key: str) -> dict[str, Any]:
        if not isinstance(idempotency_key, str) or not 8 <= len(idempotency_key) <= 160:
            raise SchoolHeroExecutionError("The idempotency key is invalid.")
        checked = self.verifier.verify(authorization)
        authorization_id = checked["authorization_id"]
        key_hash = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
        with self._lock:
            index = self._load_index()
            prior = [
                item
                for item in index["entries"]
                if item.get("authorization_id") == authorization_id
            ]
            for item in prior:
                if (
                    item.get("authorization_hash") == checked["authorization_hash"]
                    and item.get("idempotency_key_sha256") == key_hash
                ):
                    return self.get_execution(item["execution_id"])
            if prior:
                raise SchoolHeroExecutionError(
                    "This authorization was already executed with another idempotency key.",
                    code="authorization_already_executed",
                    status=409,
                )
            execution_id = (
                "exec-"
                + canonical_sha256(
                    {
                        "authorization_id": authorization_id,
                        "authorization_hash": checked["authorization_hash"],
                        "idempotency_key_sha256": key_hash,
                    }
                )[:24]
            )
            receipt = self._execute_atomic(checked, execution_id)
            index["entries"].append(
                {
                    "authorization_id": authorization_id,
                    "authorization_hash": checked["authorization_hash"],
                    "idempotency_key_sha256": key_hash,
                    "execution_id": execution_id,
                }
            )
            index["entries"].sort(key=lambda item: item["authorization_id"])
            self._save_index(index)
            return receipt

    def build_plan(self, authorization: dict[str, Any], execution_id: str) -> dict[str, Any]:
        profile = REAL_LAYER_PROFILES[SCHOOL_PROFILE_ID]
        base = {
            "schema": EXECUTION_PLAN_SCHEMA,
            "execution_plan_id": "plan-" + execution_id.removeprefix("exec-"),
            "execution_id": execution_id,
            "authorization_id": authorization["authorization_id"],
            "authorization_hash": authorization["authorization_hash"],
            "proposal_id": authorization["proposal_id"],
            "proposal_revision": authorization["proposal_revision"],
            "proposal_payload_sha256": authorization["proposal_payload_sha256"],
            "profile_id": SCHOOL_PROFILE_ID,
            "feature_code": SCHOOL_FEATURE_CODE,
            "geometry_role": SCHOOL_GEOMETRY,
            "source_archive_sha256": authorization["source_archive_sha256"],
            "source_layers": deepcopy(profile["source_layer_ids"]),
            "source_filter": {
                "field": profile["feature_code_field"],
                "operator": "equals",
                "value": SCHOOL_FEATURE_CODE,
            },
            "field_mapping": {
                "id": profile["id_field"],
                "feature_code": profile["feature_code_field"],
                "label": profile["label_field"],
            },
            "transformation_steps": [
                "extract-reviewed-components",
                "filter-terrainid-9920103",
                "reproject-epsg-4326",
                "force-xy",
                "materialize-deterministic-geojson",
            ],
            "expected_feature_count": profile["expected_feature_count"],
            "portrayal_reference": {
                "baseline_identity": deepcopy(authorization["baseline_identity"]),
                "approved_operations_sha256": canonical_sha256(
                    authorization["approved_operations"]
                ),
                "asset_output": "assets/school.svg",
            },
            "maplibre_output_reference": "bundle.json",
        }
        return _hash_record(base, "plan_sha256")

    def _execute_atomic(self, authorization: dict[str, Any], execution_id: str) -> dict[str, Any]:
        if not self.archive_path.is_file():
            raise SchoolHeroExecutionError(
                "The private reviewed source archive is unavailable.",
                code="source_archive_unavailable",
                status=503,
            )
        if file_sha256(self.archive_path) != authorization["source_archive_sha256"]:
            raise SchoolHeroExecutionError("The private source archive checksum changed.")
        if (
            not self.official_symbol_path.is_file()
            or file_sha256(self.official_symbol_path)
            != authorization["baseline_identity"]["sha256"]
        ):
            raise SchoolHeroExecutionError("The approved portrayal baseline checksum changed.")
        stage = self.staging_root / execution_id
        target = self.executions_root / execution_id
        if stage.exists():
            shutil.rmtree(stage)
        if target.exists():
            raise SchoolHeroExecutionError("The execution target already exists.")
        stage.mkdir(parents=True, exist_ok=False)
        try:
            _write_json(stage / "authorization.json", authorization)
            plan = self.build_plan(authorization, execution_id)
            _write_json(stage / "plan.json", plan)
            try:
                observation = execute_real_layer(
                    _real_layer_plan(plan),
                    approval={
                        "decision": "approved",
                        "plan_id": _real_layer_plan(plan)["plan_id"],
                    },
                    archive_path=self.archive_path,
                    output_dir=stage / "data",
                )
            except RealLayerError as error:
                raise SchoolHeroExecutionError(str(error)) from error
            data_path = Path(observation["output_path"])
            _validate_school_geojson(data_path)
            asset = _materialize_asset(
                self.official_symbol_path,
                stage / "assets" / "school.svg",
                authorization["approved_operations"],
            )
            bundle = self._build_bundle(execution_id, plan, asset)
            _write_json(stage / "bundle.json", bundle)
            receipt = self._build_receipt(
                authorization, execution_id, plan, observation, asset, bundle
            )
            _write_json(stage / "receipt.json", receipt)
            self.executions_root.mkdir(parents=True, exist_ok=True)
            os.replace(stage, target)
            return receipt
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            raise

    def _build_bundle(
        self,
        execution_id: str,
        plan: dict[str, Any],
        asset: dict[str, Any],
    ) -> dict[str, Any]:
        source_id = f"nma-school-source-{execution_id}"
        layer_id = f"nma-school-layer-{execution_id}"
        image_id = f"nma-school-image-{execution_id}"
        values = asset["values"]
        base = {
            "schema": RUNTIME_BUNDLE_SCHEMA,
            "bundle_id": f"bundle-{execution_id}",
            "execution_id": execution_id,
            "source": {
                "id": source_id,
                "type": "geojson",
                "data": f"/api/school-hero/executions/{execution_id}/data",
            },
            "layer": {
                "id": layer_id,
                "type": "symbol",
                "source": source_id,
                "layout": {
                    "icon-image": image_id,
                    "icon-size": values["scale"],
                    "icon-rotate": values["rotation"],
                    "icon-allow-overlap": False,
                    "text-field": ["to-string", ["get", "MARKNAME1"]],
                    "text-offset": [0, 1.4],
                    "text-optional": True,
                },
                "paint": {
                    "icon-color": values["color"],
                    "icon-opacity": values["opacity"],
                    "text-color": values["color"],
                },
            },
            "image_resources": [
                {
                    "id": image_id,
                    "path": (
                        f"/artifacts/runtime/school-hero/executions/{execution_id}/assets/school.svg"
                    ),
                    "sha256": asset["asset_sha256"],
                    "sdf": True,
                }
            ],
            "expected_feature_count": 15,
            "portrayal_reference": deepcopy(plan["portrayal_reference"]),
        }
        return _hash_record(base, "bundle_sha256")

    def _build_receipt(
        self,
        authorization: dict[str, Any],
        execution_id: str,
        plan: dict[str, Any],
        observation: dict[str, Any],
        asset: dict[str, Any],
        bundle: dict[str, Any],
    ) -> dict[str, Any]:
        base = {
            "schema": EXECUTION_RECEIPT_SCHEMA,
            "execution_id": execution_id,
            "execution_plan_id": plan["execution_plan_id"],
            "completed_at": _utc_timestamp(self._now),
            "authorization": {
                "authorization_id": authorization["authorization_id"],
                "authorization_hash": authorization["authorization_hash"],
            },
            "proposal": {
                "proposal_id": authorization["proposal_id"],
                "revision": authorization["proposal_revision"],
                "proposal_hash": authorization["proposal_payload_sha256"],
            },
            "source": {
                "archive_hash": authorization["source_archive_sha256"],
                "profile_id": SCHOOL_PROFILE_ID,
                "source_layers": deepcopy(plan["source_layers"]),
            },
            "output": {
                "geojson_hash": observation["output_sha256"],
                "feature_count": observation["feature_count"],
                "crs": "EPSG:4326",
                "geometry_type": SCHOOL_GEOMETRY,
            },
            "portrayal": {
                "approved_operation_hash": asset["approved_operations_sha256"],
                "asset_hash": asset["asset_sha256"],
            },
            "map": {
                "bundle_id": bundle["bundle_id"],
                "bundle_hash": bundle["bundle_sha256"],
            },
            "governance": {
                "data_execution_performed": True,
                "authoritative_source_mutation_performed": False,
                "official_portrayal_activation_performed": False,
                "pmtiles_rebuild_performed": False,
                "publication_performed": False,
            },
        }
        return _hash_record(base, "receipt_sha256")

    def _execution_path(self, execution_id: str) -> Path:
        _require_identifier(execution_id, "execution_id")
        path = self.executions_root / execution_id
        if not path.is_dir():
            raise SchoolHeroExecutionError(
                "The HERO-04 execution was not found.", code="execution_not_found", status=404
            )
        return path

    def _read_execution_json(self, execution_id: str, name: str) -> dict[str, Any]:
        path = self._execution_path(execution_id) / name
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SchoolHeroExecutionError("The execution artifact is unreadable.") from error
        return value

    def get_execution(self, execution_id: str) -> dict[str, Any]:
        return self._read_execution_json(execution_id, "receipt.json")

    def get_bundle(self, execution_id: str) -> dict[str, Any]:
        return self._read_execution_json(execution_id, "bundle.json")

    def get_data(self, execution_id: str) -> dict[str, Any]:
        return self._read_execution_json(execution_id, "data/school-point.geojson")

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
            raise SchoolHeroExecutionError(
                "The runtime observation has an invalid shape.",
                code="invalid_observation",
                status=400,
            )
        if payload["state"] not in {"activate", "verify", "rollback"}:
            raise SchoolHeroExecutionError("The runtime observation state is invalid.")
        _require_identifier(payload["client_session"], "client_session")
        bundle = self.get_bundle(execution_id)
        expected_sources = [bundle["source"]["id"]]
        expected_layers = [bundle["layer"]["id"]]
        if payload["source_ids"] != expected_sources or payload["layer_ids"] != expected_layers:
            raise SchoolHeroExecutionError(
                "The observed runtime identifiers do not match the bundle."
            )
        if payload["observed_feature_count"] != bundle["expected_feature_count"]:
            raise SchoolHeroExecutionError("The observed feature count does not match the bundle.")
        if not isinstance(payload["runtime_version"], str) or not payload["runtime_version"]:
            raise SchoolHeroExecutionError("The runtime version is invalid.")
        if payload["status"] not in {"observed", "verified", "removed", "failed"}:
            raise SchoolHeroExecutionError("The runtime observation status is invalid.")
        base = {
            "schema": RUNTIME_OBSERVATION_SCHEMA,
            "observation_id": "observation-"
            + canonical_sha256({"execution_id": execution_id, "payload": payload})[:24],
            "execution_id": execution_id,
            "bundle_hash": bundle["bundle_sha256"],
            "client_session": payload["client_session"],
            "state": payload["state"],
            "source_ids": expected_sources,
            "layer_ids": expected_layers,
            "observed_feature_count": payload["observed_feature_count"],
            "runtime_version": payload["runtime_version"],
            "timestamp": _utc_timestamp(self._now),
            "status": payload["status"],
            "final_qa": False,
        }
        observation = _hash_record(base, "observation_sha256")
        path = (
            self._execution_path(execution_id)
            / "observations"
            / (observation["observation_id"] + ".json")
        )
        _write_json(path, observation)
        return observation

    def rollback_execution(
        self, execution_id: str, *, client_session: str = "server-runtime"
    ) -> dict[str, Any]:
        with self._lock:
            root = self._execution_path(execution_id)
            manifest_path = root / "rollback.json"
            if manifest_path.is_file():
                return self._read_execution_json(execution_id, "rollback.json")
            bundle = self.get_bundle(execution_id)
            receipt_path = root / "receipt.json"
            receipt_hash = file_sha256(receipt_path)
            base = {
                "schema": ROLLBACK_MANIFEST_SCHEMA,
                "rollback_id": f"rollback-{execution_id}",
                "execution_id": execution_id,
                "bundle_hash": bundle["bundle_sha256"],
                "client_session": _require_identifier(client_session, "client_session"),
                "timestamp": _utc_timestamp(self._now),
                "status": "rolled_back",
                "actions": [
                    {"action": "remove-layer", "id": bundle["layer"]["id"]},
                    {"action": "remove-source", "id": bundle["source"]["id"]},
                    *[
                        {"action": "remove-image", "id": item["id"]}
                        for item in bundle["image_resources"]
                    ],
                ],
                "receipt_preserved": True,
                "receipt_file_sha256": receipt_hash,
            }
            manifest = _hash_record(base, "rollback_sha256")
            _write_json(manifest_path, manifest)
            if not receipt_path.is_file() or file_sha256(receipt_path) != receipt_hash:
                raise SchoolHeroExecutionError("Rollback did not preserve the execution receipt.")
            return manifest


def rollback_execution(
    engine: SchoolHeroExecutionEngine,
    execution_id: str,
    *,
    client_session: str = "server-runtime",
) -> dict[str, Any]:
    return engine.rollback_execution(execution_id, client_session=client_session)

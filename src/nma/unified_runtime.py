"""DEMO-01 orchestration over the frozen School Hero, ROAD, and BUILD runtimes.

This module owns request validation, deterministic domain selection, and result-envelope
normalization only.  Planning, authorization, execution, verification, portrayal, and activation
semantics remain in their domain-owned modules.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any, Mapping

from build_contracts.demo_execution import (
    BuildDemoExecutionError,
    validate_build_demo_execution_package,
)
from build_contracts.building_production_implementation import (
    BuildingProductionError,
    implement_controlled_building,
    load_authoritative_package,
    load_frozen_contract,
    verify_implementation_result,
)
from nma.core import canonical_sha256
from nma.feature_profile_adapters import school_feature_profile
from nma.road_execution import RoadExecutionError
from nma.road_verification import RoadExecutionVerifier, RoadVerificationError
from nma.school_hero_execution import SchoolHeroExecutionError
from nma.school_hero_verification import SchoolHeroVerificationError, SchoolHeroVerifier


RUNTIME_SCHEMA = "nma.unified-runtime-result/1.0"
RUNTIME_CONTRACT = "nma.generic-domain-adapter/1.0"
SUPPORTED_DOMAINS = ("school", "road", "build")
SUPPORTED_OPERATIONS = ("preview", "replay", "execute", "verify")
REQUEST_FIELDS = frozenset(("domain", "request", "operation", "authorization", "parameters"))

_DOMAIN_ALIASES = {
    "school": "school",
    "school-hero": "school",
    "學校": "school",
    "小學": "school",
    "road": "road",
    "道路": "road",
    "公路": "road",
    "build": "build",
    "building": "build",
    "建物": "build",
    "建築": "build",
}
_DOMAIN_TERMS = {
    "school": ("school", "school hero", "elementary", "primary", "9920103", "學校", "小學"),
    "road": ("road", "county highway", "route", "9420400", "道路", "公路", "縣道", "中山街"),
    "build": ("build", "building", "9310100", "建物", "建築", "樓層"),
}
_DOMAIN_FEATURE_CODES = {
    "school": "9920103",
    "road": "9420400",
    "build": "9310100",
}


def _contains_domain_term(request: str, term: str) -> bool:
    if term.isascii():
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", request) is not None
    return term in request


class UnifiedRuntimeError(ValueError):
    """A unified request failed closed before any fallback behavior."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: int = 400,
        domain: str | None = None,
        stage: str = "request",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.domain = domain
        self.stage = stage


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UnifiedRuntimeError(
            "missing_dependency",
            f"Required frozen runtime evidence is unavailable: {path.name}.",
            status=503,
            stage="dependency",
        ) from error
    if not isinstance(value, dict):
        raise UnifiedRuntimeError(
            "invalid_dependency",
            f"Required frozen runtime evidence is invalid: {path.name}.",
            status=503,
            stage="dependency",
        )
    return value


def _profile_payload() -> dict[str, Any]:
    profile = school_feature_profile()
    return {
        "geometry_role": profile.geometry_role,
        "identity": dict(profile.identity_payload),
        "source_scope": {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in profile.source_scope_payload.items()
        },
        "metadata": dict(profile.metadata),
    }


def select_domain(explicit: Any, request: str) -> str:
    """Select one supported domain without guessing across domain boundaries."""

    if explicit is not None:
        if not isinstance(explicit, str) or not explicit.strip():
            raise UnifiedRuntimeError("invalid_request", "domain must be a non-empty string.")
        selected = _DOMAIN_ALIASES.get(explicit.strip().casefold())
        if selected is None:
            raise UnifiedRuntimeError("unsupported_domain", "The requested domain is unsupported.")
        return selected

    normalized = " ".join(request.casefold().split())
    matches = {
        domain
        for domain, terms in _DOMAIN_TERMS.items()
        if any(_contains_domain_term(normalized, term.casefold()) for term in terms)
    }
    if not matches:
        raise UnifiedRuntimeError(
            "ambiguous_domain",
            "The request does not identify exactly one supported domain.",
        )
    if len(matches) != 1:
        raise UnifiedRuntimeError(
            "ambiguous_domain",
            "The request identifies more than one supported domain.",
        )
    return matches.pop()


def _validate_feature_target(request: str, domain: str) -> None:
    """Fail closed when a request names a feature code outside the selected frozen domain."""

    feature_codes = set(re.findall(r"(?<![0-9])[0-9]{7}(?![0-9])", request))
    if feature_codes and feature_codes != {_DOMAIN_FEATURE_CODES[domain]}:
        raise UnifiedRuntimeError(
            "unsupported_capability",
            "The requested feature target is not supported by the selected frozen domain.",
            domain=domain,
            stage="routing",
        )


def _validate_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) - REQUEST_FIELDS:
        raise UnifiedRuntimeError(
            "invalid_request",
            "Expected only domain, request, operation, authorization, and parameters.",
        )
    request = payload.get("request")
    if not isinstance(request, str) or not request.strip() or len(request) > 500:
        raise UnifiedRuntimeError(
            "invalid_request", "request must contain between 1 and 500 characters."
        )
    operation = payload.get("operation", "preview")
    if operation not in SUPPORTED_OPERATIONS:
        raise UnifiedRuntimeError("invalid_request", "The requested runtime operation is invalid.")
    authorization = payload.get("authorization")
    if authorization is not None and not isinstance(authorization, Mapping):
        raise UnifiedRuntimeError("invalid_request", "authorization must be an object.")
    parameters = payload.get("parameters", {})
    if not isinstance(parameters, Mapping):
        raise UnifiedRuntimeError("invalid_request", "parameters must be an object.")
    return {
        "domain": payload.get("domain"),
        "request": " ".join(request.split()),
        "operation": operation,
        "authorization": deepcopy(dict(authorization)) if authorization is not None else None,
        "parameters": deepcopy(dict(parameters)),
    }


def _request_id(request: Mapping[str, Any], domain: str) -> str:
    basis = {
        "domain": domain,
        "request": request["request"],
        "operation": request["operation"],
        "authorization": request["authorization"],
        "parameters": request["parameters"],
        "runtime_contract": RUNTIME_CONTRACT,
    }
    return "nma-runtime-request:sha256:" + canonical_sha256(basis)


def _mutation_status() -> dict[str, bool]:
    return {
        "source_writeback": False,
        "source_repair": False,
        "silent_geometry_mutation": False,
        "portrayal_mutation_outside_domain": False,
        "automatic_build_activation": False,
        "authorization_bypass": False,
    }


def _base_result(request: Mapping[str, Any], domain: str) -> dict[str, Any]:
    return {
        "schema": RUNTIME_SCHEMA,
        "request_id": _request_id(request, domain),
        "selected_domain": domain,
        "intent_summary": request["request"],
        "operation": request["operation"],
        "adapter_contract": {
            "id": "nma.generic-domain-adapter",
            "version": "1.0",
            "domain_payload_treatment": "opaque",
        },
        "plan": None,
        "authorization": None,
        "execution": None,
        "observation": None,
        "verification": None,
        "receipt": None,
        "provenance": None,
        "visualization": {"status": "unavailable", "reason": "not-produced"},
        "warnings": [],
        "errors": [],
        "mutation": _mutation_status(),
    }


def _require_execution_authorization(request: Mapping[str, Any], domain: str) -> dict[str, str]:
    authorization = request.get("authorization")
    if not isinstance(authorization, Mapping) or set(authorization) != {
        "authorization_id",
        "idempotency_key",
    }:
        raise UnifiedRuntimeError(
            "authorization_failure",
            "Canonical execution requires authorization_id and idempotency_key only.",
            status=403,
            domain=domain,
            stage="authorization",
        )
    if not all(isinstance(authorization[key], str) for key in authorization):
        raise UnifiedRuntimeError(
            "authorization_failure",
            "Canonical authorization identifiers must be strings.",
            status=403,
            domain=domain,
            stage="authorization",
        )
    return dict(authorization)


def _read_execution_plan(engine: Any, execution_id: str) -> dict[str, Any]:
    path = Path(engine.storage_root) / "executions" / execution_id / "plan.json"
    return _load_object(path)


class SchoolRuntimeAdapter:
    domain = "school"

    def __init__(
        self, *, engine: Any, repository_root: Path, archive_path: Path, symbol_path: Path
    ):
        self.engine = engine
        self.repository_root = repository_root
        self.archive_path = archive_path
        self.symbol_path = symbol_path

    def dispatch(self, request: Mapping[str, Any]) -> dict[str, Any]:
        result = _base_result(request, self.domain)
        operation = request["operation"]
        if operation in {"preview", "replay"}:
            result["plan"] = {
                "status": "authorization-required-before-canonical-plan",
                "contract": "nma.school-hero-execution-plan/1.0",
                "identity": None,
                "capability": _profile_payload(),
            }
            result["authorization"] = {
                "required": True,
                "status": "not-presented",
                "identity": None,
            }
            result["execution"] = {
                "status": "not-requested",
                "contract": "hero-04/1.0",
                "identity": None,
                "canonical_boundary": "nma.school_hero_execution.SchoolHeroExecutionEngine",
            }
            result["warnings"].append(
                "Public School preview exposes the frozen capability; new execution requires a stored HERO-03 authorization and the protected source archive."
            )
            return result
        if operation == "execute":
            authorization = _require_execution_authorization(request, self.domain)
            try:
                receipt = self.engine.execute_by_id(authorization)
                execution_id = receipt["execution_id"]
                plan = _read_execution_plan(self.engine, execution_id)
                bundle = self.engine.get_bundle(execution_id)
            except SchoolHeroExecutionError as error:
                raise UnifiedRuntimeError(
                    "authorization_failure"
                    if "authorization" in error.code
                    else "execution_failure",
                    str(error),
                    status=error.status,
                    domain=self.domain,
                    stage="authorization" if "authorization" in error.code else "execution",
                ) from error
            result.update(
                {
                    "plan": {
                        "status": "executed",
                        "contract": plan.get("schema"),
                        "identity": plan.get("execution_plan_id"),
                        "sha256": plan.get("plan_sha256"),
                    },
                    "authorization": {
                        "required": True,
                        "status": "consumed",
                        "identity": receipt.get("authorization", {}).get("authorization_id"),
                        "sha256": receipt.get("authorization", {}).get("authorization_hash"),
                    },
                    "execution": {
                        "status": "completed-verification-pending",
                        "contract": receipt.get("schema"),
                        "identity": execution_id,
                        "activation_status": "not-supported-by-domain",
                    },
                    "receipt": {
                        "identity": receipt.get("receipt_sha256"),
                        "reference": f"/api/school-hero/executions/{execution_id}",
                    },
                    "provenance": {
                        "status": "receipt-bound-verification-pending",
                        "reference": f"/api/school-hero/executions/{execution_id}",
                    },
                    "visualization": {
                        "status": "available",
                        "maplibre": bundle,
                        "data_reference": f"/api/school-hero/executions/{execution_id}/data",
                    },
                }
            )
            return result
        return self._verify(request, result)

    def _verify(self, request: Mapping[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        parameters = request["parameters"]
        execution_id = parameters.get("execution_id")
        if (
            not isinstance(execution_id, str)
            or not re.fullmatch(r"[A-Za-z0-9._:-]{1,160}", execution_id)
            or set(parameters) != {"execution_id"}
        ):
            raise UnifiedRuntimeError(
                "invalid_request",
                "School verification requires parameters.execution_id.",
                domain=self.domain,
                stage="verification",
            )
        verifier = SchoolHeroVerifier(
            storage_root=self.engine.storage_root,
            archive_path=self.archive_path,
            official_symbol_path=self.symbol_path,
            repository_root=self.repository_root,
        )
        try:
            verified = verifier.verify(execution_id, persist=True)
        except SchoolHeroVerificationError as error:
            raise UnifiedRuntimeError(
                "verification_failure",
                str(error),
                status=422,
                domain=self.domain,
                stage="verification",
            ) from error
        result["execution"] = {"status": "existing", "identity": execution_id}
        result["verification"] = {
            "status": verified["status"],
            "identity": verified["qa"].get("qa_sha256"),
            "classification": verified["qa"].get("classification"),
        }
        result["provenance"] = {
            "status": verified["provenance"].get("status"),
            "identity": verified["provenance"].get("provenance_sha256"),
        }
        return result


class RoadRuntimeAdapter:
    domain = "road"

    def __init__(
        self,
        *,
        engine: Any,
        repository_root: Path,
        archive_path: Path,
        visual_evidence_path: Path | None = None,
        screenshot_path: Path | None = None,
    ):
        self.engine = engine
        self.repository_root = repository_root
        self.archive_path = archive_path
        self.visual_evidence_path = visual_evidence_path
        self.screenshot_path = screenshot_path

    def dispatch(self, request: Mapping[str, Any]) -> dict[str, Any]:
        result = _base_result(request, self.domain)
        operation = request["operation"]
        if operation in {"preview", "replay"}:
            return self._replay(result)
        if operation == "execute":
            authorization = _require_execution_authorization(request, self.domain)
            try:
                receipt = self.engine.execute_by_id(authorization)
                execution_id = receipt["execution_id"]
                plan = _read_execution_plan(self.engine, execution_id)
                bundle = self.engine.get_bundle(execution_id)
            except RoadExecutionError as error:
                raise UnifiedRuntimeError(
                    "authorization_failure"
                    if "authorization" in error.code
                    else "execution_failure",
                    str(error),
                    status=error.status,
                    domain=self.domain,
                    stage="authorization" if "authorization" in error.code else "execution",
                ) from error
            result.update(
                {
                    "plan": {
                        "status": "executed",
                        "contract": plan.get("schema"),
                        "identity": plan.get("execution_plan_id"),
                        "sha256": plan.get("execution_plan_sha256"),
                    },
                    "authorization": {
                        "required": True,
                        "status": "consumed",
                        "identity": receipt.get("authorization", {}).get("id"),
                        "sha256": receipt.get("authorization", {}).get("sha256"),
                    },
                    "execution": {
                        "status": "completed-verification-pending",
                        "contract": receipt.get("schema"),
                        "identity": execution_id,
                        "activation_status": "not-supported-by-domain",
                    },
                    "receipt": {
                        "identity": receipt.get("receipt_id"),
                        "sha256": receipt.get("receipt_sha256"),
                        "reference": f"/api/road/executions/{execution_id}",
                    },
                    "provenance": {
                        "status": "receipt-bound-verification-pending",
                        "frozen_identities": deepcopy(receipt.get("frozen_identities")),
                    },
                    "visualization": {
                        "status": "available",
                        "maplibre": bundle,
                        "data_reference": f"/api/road/executions/{execution_id}/data",
                    },
                }
            )
            return result
        return self._verify(request, result)

    def _replay(self, result: dict[str, Any]) -> dict[str, Any]:
        specifications = self.repository_root / "data/specifications"
        plan = _load_object(specifications / "nma-road-hero-road-04-golden-plan-v1.0.json")
        receipt = _load_object(specifications / "nma-road-hero-road-04-golden-receipt-v1.0.json")
        bundle = _load_object(
            specifications / "nma-road-hero-road-04-golden-runtime-bundle-v1.0.json"
        )
        checks = {
            "plan": plan.get("execution_plan_sha256")
            == canonical_sha256({k: v for k, v in plan.items() if k != "execution_plan_sha256"}),
            "bundle": bundle.get("bundle_sha256")
            == canonical_sha256({k: v for k, v in bundle.items() if k != "bundle_sha256"}),
            "receipt": receipt.get("receipt_sha256")
            == canonical_sha256(
                {k: v for k, v in receipt.items() if k not in {"receipt_sha256", "completed_at"}}
            ),
            "linkage": receipt.get("execution_plan", {}).get("sha256")
            == plan.get("execution_plan_sha256")
            and receipt.get("runtime_bundle", {}).get("sha256") == bundle.get("bundle_sha256"),
        }
        if not all(checks.values()):
            raise UnifiedRuntimeError(
                "verification_failure",
                "Frozen ROAD execution evidence failed canonical identity validation.",
                status=500,
                domain=self.domain,
                stage="verification",
            )
        result.update(
            {
                "plan": {
                    "status": "frozen-validated-replay",
                    "contract": plan.get("schema"),
                    "identity": plan.get("execution_plan_id"),
                    "sha256": plan.get("execution_plan_sha256"),
                },
                "authorization": {
                    "required": True,
                    "status": "frozen-consumed-evidence",
                    "identity": receipt.get("authorization", {}).get("id"),
                    "sha256": receipt.get("authorization", {}).get("sha256"),
                },
                "execution": {
                    "status": "frozen-execution-replay-not-new-execution",
                    "contract": receipt.get("schema"),
                    "identity": receipt.get("execution_id"),
                    "activation_status": "not-supported-by-domain",
                },
                "verification": {
                    "status": "passed-frozen-identity-and-linkage",
                    "checks": checks,
                },
                "receipt": {
                    "identity": receipt.get("receipt_id"),
                    "sha256": receipt.get("receipt_sha256"),
                },
                "provenance": {
                    "status": "frozen-content-addressed-lineage",
                    "frozen_identities": deepcopy(receipt.get("frozen_identities")),
                },
                "visualization": {
                    "status": "artifact-reference-only",
                    "maplibre": bundle,
                    "reason": "Public frozen ROAD geometry is intentionally not redistributed.",
                },
            }
        )
        result["warnings"].append("This is a validated frozen replay, not a new ROAD execution.")
        return result

    def _verify(self, request: Mapping[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        parameters = request["parameters"]
        execution_id = parameters.get("execution_id")
        if (
            not isinstance(execution_id, str)
            or not re.fullmatch(r"[A-Za-z0-9._:-]{1,160}", execution_id)
            or set(parameters) != {"execution_id"}
        ):
            raise UnifiedRuntimeError(
                "invalid_request",
                "ROAD verification requires parameters.execution_id.",
                domain=self.domain,
                stage="verification",
            )
        verifier = RoadExecutionVerifier(
            storage_root=self.engine.storage_root,
            archive_path=self.archive_path,
            repository_root=self.repository_root,
            visual_evidence_path=self.visual_evidence_path,
            screenshot_path=self.screenshot_path,
        )
        try:
            verified = verifier.verify(execution_id, persist=True)
        except RoadVerificationError as error:
            raise UnifiedRuntimeError(
                "verification_failure",
                str(error),
                status=422,
                domain=self.domain,
                stage="verification",
            ) from error
        result["execution"] = {"status": "existing", "identity": execution_id}
        result["verification"] = {
            "status": verified["status"],
            "identity": verified["qa"].get("qa_sha256"),
            "classification": verified["qa"].get("classification"),
        }
        result["provenance"] = {
            "status": verified["provenance"].get("status"),
            "identity": verified["provenance"].get("provenance_sha256"),
        }
        return result


class BuildRuntimeAdapter:
    domain = "build"

    def __init__(self, *, repository_root: Path, archive_path: Path):
        self.repository_root = repository_root
        self.archive_path = archive_path

    def _frozen_inputs(self) -> tuple[dict[str, Any], ...]:
        specifications = self.repository_root / "data/specifications"
        names = (
            "nma-build-04-golden-demo-authorization-v1.0.json",
            "nma-build-03a-golden-gate-resolution-v1.0.json",
            "nma-build-03-golden-gate-review-v1.0.json",
            "nma-build-02-golden-proposal-v1.0.json",
            "nma-build-02-golden-decision-v1.0.json",
        )
        return tuple(_load_object(specifications / name) for name in names)

    def dispatch(self, request: Mapping[str, Any]) -> dict[str, Any]:
        result = _base_result(request, self.domain)
        if request["operation"] in {"preview", "replay"}:
            return self._replay(result)
        if request["operation"] == "verify":
            parameters = request["parameters"]
            if parameters != {"execution_id": "build-05-demo-exec-b8b5ecd54954b190eb8cda39"}:
                raise UnifiedRuntimeError(
                    "invalid_request",
                    "Public BUILD verification accepts only the frozen BUILD-05 execution identity.",
                    domain=self.domain,
                    stage="verification",
                )
            return self._replay(result)
        authorization = request.get("authorization")
        if not isinstance(authorization, Mapping) or set(authorization) != {"policy_record_sha256"}:
            raise UnifiedRuntimeError(
                "authorization_failure",
                "Controlled BUILD execution requires policy_record_sha256 only.",
                status=403,
                domain=self.domain,
                stage="authorization",
            )
        parameters = request["parameters"]
        if set(parameters) != {"source_package_identity", "geographic_project_scope"} or not all(
            isinstance(value, str) and value for value in parameters.values()
        ):
            raise UnifiedRuntimeError(
                "invalid_request",
                "Controlled BUILD execution requires exact source_package_identity and geographic_project_scope parameters.",
                domain=self.domain,
                stage="planning",
            )
        try:
            frozen = load_frozen_contract(self.repository_root)
            if authorization["policy_record_sha256"] != frozen["policy"]["policy_record_sha256"]:
                raise UnifiedRuntimeError(
                    "authorization_failure",
                    "The BUILD policy authorization identity does not match BUILD-09F.",
                    status=403,
                    domain=self.domain,
                    stage="authorization",
                )
            loaded = load_authoritative_package(
                contract=frozen["contract"],
                archive_path=self.archive_path,
                package_identity=parameters["source_package_identity"],
                geographic_project_scope=parameters["geographic_project_scope"],
            )
            implementation = implement_controlled_building(
                contract_bundle=frozen,
                binding=loaded["binding"],
                authoritative_collection=loaded["authoritative_collection"],
                portrayal_polygonz_collection=loaded["portrayal_polygonz_collection"],
                source_crs=loaded["source_crs"],
                output_crs=loaded["output_crs"],
            )
            verify_implementation_result(implementation)
        except UnifiedRuntimeError:
            raise
        except BuildingProductionError as error:
            raise UnifiedRuntimeError(
                "authorization_failure"
                if "authorization" in error.code or "policy" in error.code
                else "execution_failure",
                str(error),
                status=403 if "authorization" in error.code or "policy" in error.code else 422,
                domain=self.domain,
                stage="authorization" if "authorization" in error.code else "execution",
            ) from error
        return self._implementation_result(result, implementation)

    def _replay(self, result: dict[str, Any]) -> dict[str, Any]:
        package = _load_object(
            self.repository_root
            / "data/specifications/nma-build-05-golden-execution-package-v1.0.json"
        )
        try:
            validated = validate_build_demo_execution_package(package, *self._frozen_inputs())
        except BuildDemoExecutionError as error:
            raise UnifiedRuntimeError(
                "verification_failure",
                str(error),
                status=500,
                domain=self.domain,
                stage="verification",
            ) from error
        result = self._package_result(result, validated)
        result["warnings"].append("This is a validated frozen replay, not a new BUILD execution.")
        return result

    def _package_result(self, result: dict[str, Any], package: Mapping[str, Any]) -> dict[str, Any]:
        receipt = package["receipt"]
        artifact = package["demo_artifact"]
        result.update(
            {
                "plan": {
                    "status": "frozen-validated-replay",
                    "contract": "nma.build-demo-consumption-plan/1.0",
                    "identity": package.get("plan_sha256"),
                    "sha256": package.get("plan_sha256"),
                },
                "authorization": {
                    "required": True,
                    "status": "frozen-consumed-evidence",
                    "identity": package.get("authorization_id"),
                    "sha256": package.get("authorization_sha256"),
                },
                "execution": {
                    "status": "frozen-execution-replay-not-new-execution",
                    "contract": package.get("schema_version"),
                    "identity": package.get("execution_id"),
                    "activation_status": "held-not-requested",
                },
                "observation": {
                    "status": artifact.get("status"),
                    "identity": artifact.get("artifact_sha256"),
                },
                "verification": {
                    "status": "passed-frozen-package-validation",
                    "identity": package.get("package_sha256"),
                },
                "receipt": {
                    "identity": receipt.get("receipt_id"),
                    "sha256": receipt.get("receipt_sha256"),
                },
                "provenance": {
                    "status": "content-addressed",
                    "identity": package.get("package_sha256"),
                    "source_commitments": deepcopy(artifact.get("source_commitments")),
                },
                "visualization": {
                    "status": "available",
                    "maplibre": deepcopy(artifact.get("maplibre_demo")),
                    "coordinate_space": artifact.get("privacy", {}).get("coordinate_space"),
                },
            }
        )
        return result

    def _implementation_result(
        self, result: dict[str, Any], implementation: Mapping[str, Any]
    ) -> dict[str, Any]:
        record = implementation["record"]
        plan = record["plan"]
        observation = record["observation"]
        verification = record["verification"]
        receipt = record["receipt"]
        provenance = record["provenance"]
        result.update(
            {
                "plan": {
                    "status": plan.get("status"),
                    "contract": plan.get("schema"),
                    "identity": plan.get("execution_plan_sha256"),
                    "sha256": plan.get("execution_plan_sha256"),
                },
                "authorization": {
                    "required": True,
                    "status": "consumed-by-controlled-implementation",
                    "identity": plan.get("policy_authorization_sha256"),
                    "sha256": plan.get("policy_authorization_sha256"),
                },
                "execution": {
                    "status": record.get("status"),
                    "contract": record.get("schema"),
                    "identity": record.get("implementation_record_sha256"),
                    "activation_status": "held-not-requested",
                },
                "observation": {
                    "status": observation.get("status"),
                    "identity": observation.get("observation_sha256"),
                },
                "verification": {
                    "status": verification.get("status"),
                    "identity": verification.get("verification_sha256"),
                },
                "receipt": {
                    "identity": receipt.get("receipt_sha256"),
                    "sha256": receipt.get("receipt_sha256"),
                },
                "provenance": {
                    "status": "content-addressed",
                    "identity": provenance.get("provenance_sha256"),
                    "source_collection_sha256": provenance.get("source_collection_sha256"),
                },
                "visualization": {
                    "status": "available",
                    "maplibre": deepcopy(implementation.get("maplibre")),
                    "coordinate_space": "EPSG:4326-derived-non-authoritative",
                },
            }
        )
        result["warnings"].append(
            "BUILD controlled implementation completed with production and official portrayal activation held."
        )
        return result


class UnifiedNMARuntime:
    """Validate one request and delegate it to exactly one domain-owned adapter."""

    def __init__(self, adapters: Mapping[str, Any]):
        if set(adapters) != set(SUPPORTED_DOMAINS):
            raise ValueError("Unified runtime requires exactly School, ROAD, and BUILD adapters.")
        self.adapters = dict(adapters)

    def dispatch(self, payload: Any) -> dict[str, Any]:
        request = _validate_request(payload)
        domain = select_domain(request["domain"], request["request"])
        _validate_feature_target(request["request"], domain)
        try:
            result = self.adapters[domain].dispatch(request)
        except UnifiedRuntimeError:
            raise
        except Exception as error:
            raise UnifiedRuntimeError(
                "execution_failure",
                "The selected canonical domain runtime failed closed.",
                status=500,
                domain=domain,
                stage="execution",
            ) from error
        if result.get("selected_domain") != domain or result.get("mutation") != _mutation_status():
            raise UnifiedRuntimeError(
                "verification_failure",
                "The unified result envelope violated its integration boundary.",
                status=500,
                domain=domain,
                stage="verification",
            )
        return result


__all__ = [
    "BuildRuntimeAdapter",
    "RoadRuntimeAdapter",
    "SchoolRuntimeAdapter",
    "SUPPORTED_DOMAINS",
    "SUPPORTED_OPERATIONS",
    "UnifiedNMARuntime",
    "UnifiedRuntimeError",
    "select_domain",
]

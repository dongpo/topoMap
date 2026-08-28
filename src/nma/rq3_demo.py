"""RQ3-DEMO-01 deterministic authorization, verification, provenance, and audit controls."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from nma.core import canonical_json, canonical_sha256
from nma.rq2_demo import execute_proposal, proposal_hash, sha256_file, validate_rq3_handoff


PREDECESSOR = "2c3c25937615cfe01e989bdeb64b25ad6c27251f"
PROPOSAL_ID = "rq2-proposal:knowledge-constrained:e635111c3be29423faf923b7"
PROPOSAL_HASH = "116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1"
PROPOSAL_BYTE_SHA256 = "8ad05eea5111a0c535be275effa6b8a6c3dce7b74c7149bf42811a1866aa4829"
EXECUTOR_ID = "rq3-deterministic-executor/1.0"
VERIFIER_ID = "rq3-deterministic-verifier/1.0"
WORKFLOW_ID = "rq3-demo-01-canonical-workflow"
EXECUTION_SCHEMA = "rq3-execution-record-schema-v1.0.json"
AUTHORIZATION_SCHEMA = "rq3-authorization-schema-v1.0.json"
VERIFICATION_SCHEMA = "rq3-verification-report-schema-v1.0.json"
AUDIT_SCHEMA = "rq3-audit-record-schema-v1.0.json"
POLICY_NAME = "rq3-trust-policy-v1.0.json"
CANONICALIZATION = "nma-canonical-json-sort-keys-utf8-sha256;exclude={}"


class RQ3DemoError(ValueError):
    """A frozen RQ3 trust contract was violated."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RQ3DemoError(f"Unreadable JSON object: {path}") from error
    if not isinstance(value, dict):
        raise RQ3DemoError(f"JSON artifact is not an object: {path}")
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(dict(value)) + b"\n")


def artifact_hash(value: Mapping[str, Any], self_hash_field: str) -> str:
    basis = deepcopy(dict(value))
    basis.pop(self_hash_field, None)
    return canonical_sha256(basis)


def validate_schema(repository_root: Path, schema_name: str, value: Mapping[str, Any]) -> list[str]:
    try:
        import jsonschema
    except ImportError as error:
        raise RQ3DemoError("jsonschema is required for RQ3 trust validation.") from error
    schema = read_json(repository_root / "data/specifications" / schema_name)
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
    )
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '$'}: {error.message}"
        for error in sorted(validator.iter_errors(dict(value)), key=lambda item: list(item.path))
    ]


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RQ3DemoError(f"Invalid RQ3 timestamp: {value}") from error
    if parsed.tzinfo is None:
        raise RQ3DemoError("RQ3 timestamps must carry a UTC offset.")
    return parsed.astimezone(timezone.utc)


def _policy(repository_root: Path) -> dict[str, Any]:
    return read_json(repository_root / "data/specifications" / POLICY_NAME)


def _authorization_hash_valid(authorization: Mapping[str, Any]) -> bool:
    return authorization.get("authorization_hash") == artifact_hash(
        authorization, "authorization_hash"
    )


def canonical_environment(repository_root: Path, fixture_path: Path) -> dict[str, str]:
    policy_path = repository_root / "data/specifications" / POLICY_NAME
    basis = {
        "environment_id": "rq3-demo-01-bounded-research-environment/1.0",
        "predecessor": PREDECESSOR,
        "policy_sha256": sha256_file(policy_path),
        "source_sha256": sha256_file(fixture_path),
        "executor_id": EXECUTOR_ID,
        "rq2_executor_id": "rq2-deterministic-gis-executor/1.0",
        "verifier_id": VERIFIER_ID,
        "network_access": False,
        "model_calls": 0,
    }
    return {"id": basis["environment_id"], "sha256": canonical_sha256(basis)}


def canonical_execution_request(
    proposal: Mapping[str, Any],
    authorization: Mapping[str, Any],
    *,
    execution_id: str,
    repository_root: Path,
    fixture_path: Path,
) -> dict[str, Any]:
    scope = authorization["authorized_scope"]
    return {
        "execution_id": execution_id,
        "workflow_id": WORKFLOW_ID,
        "subject": deepcopy(authorization["authorized_subject"]),
        "proposal_id": proposal["proposal_id"],
        "proposal_hash": proposal["proposal_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "dataset": deepcopy(scope["datasets"][0]),
        "layer_id": scope["layer_ids"][0],
        "feature_id": scope["feature_ids"][0],
        "operations": [step["operation"] for step in proposal["plan"]],
        "tools": [{"step_id": step["step_id"], "tool": step["tool"]} for step in proposal["plan"]],
        "plan_identity": proposal["provenance_seed"]["plan_identity"],
        "normalized_parameters": [
            {"step_id": step["step_id"], "inputs": deepcopy(step["inputs"])}
            for step in proposal["plan"]
        ],
        "mutation_type": scope["mutation_type"],
        "source_access": scope["source_access"],
        "source_mutation": False,
        "output_destination": scope["output_destinations"][0].replace(
            "{execution_id}", execution_id
        ),
        "authoritative_render": scope["authoritative_render"],
        "bounded_unresolved_constraint_ids": deepcopy(scope["bounded_unresolved_constraint_ids"]),
        "environment": canonical_environment(repository_root, fixture_path),
    }


def _request_fingerprint(request: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(request))
    basis.pop("execution_id", None)
    basis["output_destination"] = "artifacts/rq3/runtime/{execution_id}/derived-feature.geojson"
    return canonical_sha256(basis)


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": "rq3-idempotency-state/1.0",
            "authorization_id": None,
            "authorization_hash": None,
            "request_fingerprint": None,
            "execution_count": 0,
            "attempts": [],
        }
    state = read_json(path)
    required = {
        "schema_version",
        "authorization_id",
        "authorization_hash",
        "request_fingerprint",
        "execution_count",
        "attempts",
    }
    if set(state) != required or state["schema_version"] != "rq3-idempotency-state/1.0":
        raise RQ3DemoError("Malformed RQ3 idempotency state.")
    if state["execution_count"] != len(state["attempts"]):
        raise RQ3DemoError("Inconsistent RQ3 idempotency state.")
    return state


def _blocked(code: str, checks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "status": "BLOCK_BEFORE_MUTATION",
        "failure_code": code,
        "checks": list(checks),
        "mutation_started": False,
        "model_calls": 0,
    }


def pre_execution_gate(
    repository_root: Path,
    proposal: Mapping[str, Any],
    authorization: Mapping[str, Any] | None,
    request: Mapping[str, Any] | None,
    *,
    fixture_path: Path,
    output_root: Path,
    state_path: Path,
    execution_started_at: str,
) -> dict[str, Any]:
    """Validate every frozen trust input before creating state or result bytes."""

    checks: list[dict[str, Any]] = []

    def require(name: str, passed: bool, code: str) -> dict[str, Any] | None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL"})
        return None if passed else _blocked(code, checks)

    handoff = validate_rq3_handoff(repository_root, proposal)
    result = require(
        "PROPOSAL_SCHEMA_VALID", not handoff["schema_errors"], "PROPOSAL_HASH_MISMATCH"
    )
    if result:
        return result
    result = require(
        "PROPOSAL_ID_MATCH", proposal.get("proposal_id") == PROPOSAL_ID, "PROPOSAL_ID_MISMATCH"
    )
    if result:
        return result
    recomputed = proposal_hash(proposal)
    proposal_binding = (
        recomputed == PROPOSAL_HASH
        and proposal.get("proposal_hash") == PROPOSAL_HASH
        and all(
            declaration.get("bound_proposal_hash") == PROPOSAL_HASH
            for declaration in proposal.get("required_authorizations", [])
        )
    )
    result = require(
        "PROPOSAL_HASH_RECOMPUTED_AND_MATCHED", proposal_binding, "PROPOSAL_HASH_MISMATCH"
    )
    if result:
        return result
    result = require("AUTHORIZATION_PRESENT", authorization is not None, "AUTHORIZATION_MISSING")
    if result:
        return result
    assert authorization is not None
    result = require(
        "AUTHORIZATION_SCHEMA_VALID",
        not validate_schema(repository_root, AUTHORIZATION_SCHEMA, authorization),
        "AUTHORIZATION_MALFORMED",
    )
    if result:
        return result
    result = require(
        "AUTHORIZATION_HASH_RECOMPUTED_AND_MATCHED",
        _authorization_hash_valid(authorization),
        "AUTHORIZATION_HASH_MISMATCH",
    )
    if result:
        return result
    result = require(
        "AUTHORIZATION_DECISION_APPROVED",
        authorization["decision"] == "APPROVED",
        "AUTHORIZATION_DENIED",
    )
    if result:
        return result
    if authorization["proposal_id"] != proposal["proposal_id"]:
        return _blocked("PROPOSAL_ID_MISMATCH", checks)
    if authorization["proposal_hash"] != recomputed:
        return _blocked("PROPOSAL_HASH_MISMATCH", checks)
    policy = _policy(repository_root)
    policy_path = repository_root / "data/specifications" / POLICY_NAME
    policy_linked = authorization["policy_reference"] == {
        "id": "data/specifications/rq3-trust-policy-v1.0.json",
        "sha256": sha256_file(policy_path),
    }
    result = require("AUTHORIZATION_POLICY_LINKED", policy_linked, "AUTHORIZATION_HASH_MISMATCH")
    if result:
        return result
    started = _parse_utc(execution_started_at)
    time_valid = (
        _parse_utc(authorization["issued_at"]) <= started < _parse_utc(authorization["valid_until"])
    )
    result = require("AUTHORIZATION_TIME_VALID", time_valid, "AUTHORIZATION_EXPIRED")
    if result:
        return result
    result = require(
        "AUTHORIZED_SUBJECT_MATCH",
        authorization["authorized_subject"]
        == {
            "agent_id": EXECUTOR_ID,
            "operator_id": "rq3-research-operator:fixture-001",
            "workflow_id": WORKFLOW_ID,
        },
        "AUTHORIZATION_SCOPE_MISMATCH",
    )
    if result:
        return result
    scope_exact = authorization["authorized_scope"] == policy["canonical_scope"]
    result = require(
        "AUTHORIZED_SCOPE_EXACT_OR_NARROWER", scope_exact, "AUTHORIZATION_SCOPE_MISMATCH"
    )
    if result:
        return result
    result = require(
        "TOOLS_AND_ORDER_AUTHORIZED",
        authorization["allowed_tools"] == policy["allowed_tools"],
        "UNAUTHORIZED_TOOL",
    )
    if result:
        return result
    result = require(
        "PARAMETER_BOUNDS_AUTHORIZED",
        authorization["parameter_bounds"] == policy["parameter_bounds"],
        "PARAMETER_MISMATCH",
    )
    if result:
        return result
    result = require(
        "EXECUTION_REQUEST_PRESENT", request is not None, "AUTHORIZATION_SCOPE_MISMATCH"
    )
    if result:
        return result
    assert request is not None
    expected = canonical_execution_request(
        proposal,
        authorization,
        execution_id=str(request.get("execution_id", "")),
        repository_root=repository_root,
        fixture_path=fixture_path,
    )
    if set(request) != set(expected):
        return _blocked("AUTHORIZATION_SCOPE_MISMATCH", checks)
    if request.get("source_mutation") is not False or request.get("source_access") != "READ_ONLY":
        return _blocked("UNAUTHORIZED_MUTATION", checks)
    expected_unresolved = set(policy["canonical_scope"]["bounded_unresolved_constraint_ids"])
    observed_unresolved = set(request.get("bounded_unresolved_constraint_ids", []))
    if (
        request.get("authoritative_render") is not False
        or observed_unresolved != expected_unresolved
    ):
        return _blocked("UNRESOLVED_CONSTRAINT_ESCALATION", checks)
    if request.get("tools") != expected["tools"]:
        return _blocked("UNAUTHORIZED_TOOL", checks)
    if (
        request.get("plan_identity") != expected["plan_identity"]
        or request.get("normalized_parameters") != expected["normalized_parameters"]
    ):
        return _blocked("PARAMETER_MISMATCH", checks)
    scope_fields = (
        "workflow_id",
        "subject",
        "proposal_id",
        "proposal_hash",
        "authorization_id",
        "authorization_hash",
        "dataset",
        "layer_id",
        "feature_id",
        "operations",
        "mutation_type",
        "output_destination",
        "environment",
    )
    if any(request.get(field) != expected[field] for field in scope_fields):
        return _blocked("AUTHORIZATION_SCOPE_MISMATCH", checks)
    checks.append({"check": "REQUEST_SCOPE_TOOLS_PARAMETERS_EXACT", "status": "PASS"})
    source_hash = sha256_file(fixture_path)
    result = require(
        "INPUT_HASHES_MATCH",
        source_hash == authorization["authorized_scope"]["datasets"][0]["sha256"],
        "AUTHORIZATION_SCOPE_MISMATCH",
    )
    if result:
        return result
    resolved_source = fixture_path.resolve()
    resolved_output = output_root.resolve()
    roots_disjoint = (
        resolved_source not in resolved_output.parents
        and resolved_output not in resolved_source.parents
        and output_root.parent.resolve() == state_path.parent.resolve()
    )
    result = require(
        "SOURCE_AND_OUTPUT_ROOTS_DISJOINT",
        roots_disjoint and not output_root.exists(),
        "UNAUTHORIZED_MUTATION",
    )
    if result:
        return result
    state = _load_state(state_path)
    maximum = authorization["authorized_scope"]["maximum_execution_count"]
    if state["execution_count"] >= maximum:
        return _blocked("REPLAY_LIMIT_EXCEEDED", checks)
    fingerprint = _request_fingerprint(request)
    replay_valid = state["execution_count"] == 0 or (
        state["authorization_id"] == authorization["authorization_id"]
        and state["authorization_hash"] == authorization["authorization_hash"]
        and state["request_fingerprint"] == fingerprint
    )
    result = require("AUTHORIZATION_REPLAY_LIMIT_VALID", replay_valid, "PARAMETER_MISMATCH")
    if result:
        return result
    return {
        "status": "PASS",
        "failure_code": None,
        "checks": checks,
        "mutation_started": False,
        "model_calls": 0,
        "request_fingerprint": fingerprint,
        "execution_count_before": state["execution_count"],
    }


def _check(
    checks: list[dict[str, Any]],
    check_id: str,
    category: str,
    expected: Any,
    observed: Any,
    failure_code: str,
) -> None:
    passed = observed == expected
    checks.append(
        {
            "check_id": check_id,
            "category": category,
            "expected": expected,
            "observed": observed,
            "status": "PASS" if passed else "FAIL",
            "failure_code": None if passed else failure_code,
        }
    )


def build_execution_record(
    proposal: Mapping[str, Any],
    authorization: Mapping[str, Any],
    request: Mapping[str, Any],
    rq2_execution: Mapping[str, Any],
    *,
    output_root: Path,
    fixture_path: Path,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    raw_receipt = read_json(output_root / "execution-receipt.json")
    result_path = output_root / "derived-feature.geojson"
    plan_by_step = {step["step_id"]: step for step in proposal["plan"]}
    normalized = [
        {
            "step_id": step["step_id"],
            "inputs": deepcopy(step["inputs"]),
            "parameter_hash": canonical_sha256(step["inputs"]),
        }
        for step in proposal["plan"]
    ]
    tool_calls = []
    for observed in raw_receipt["tool_calls"]:
        planned = plan_by_step[observed["step_id"]]
        tool_calls.append(
            {
                "step_id": planned["step_id"],
                "operation": planned["operation"],
                "tool": planned["tool"],
                "parameter_hash": canonical_sha256(planned["inputs"]),
                "status": observed["status"],
                "mutation": observed["mutation"],
            }
        )
    source_ref = deepcopy(authorization["authorized_scope"]["datasets"][0])
    source_after = {"id": source_ref["id"], "sha256": sha256_file(fixture_path)}
    result_ref = {
        "id": f"rq3-result:{request['execution_id']}:derived-feature",
        "sha256": sha256_file(result_path),
    }
    record = {
        "execution_id": request["execution_id"],
        "schema_version": "rq3-execution-record/1.0",
        "proposal_id": proposal["proposal_id"],
        "proposal_hash": proposal["proposal_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "environment": deepcopy(request["environment"]),
        "authorized_tool_sequence": [
            {
                "step_id": step["step_id"],
                "operation": step["operation"],
                "tool": step["tool"],
            }
            for step in proposal["plan"]
        ],
        "tool_calls": tool_calls,
        "plan_identity": proposal["provenance_seed"]["plan_identity"],
        "normalized_parameters": normalized,
        "source_refs_before": [source_ref],
        "source_refs_after": [source_after],
        "result_refs": [result_ref],
        "result_hash": result_ref["sha256"],
        "execution_success": rq2_execution["status"] == "PASS",
        "mutation_started": bool(rq2_execution["mutation_started"]),
        "started_at": started_at,
        "completed_at": completed_at,
        "executor": {
            "id": EXECUTOR_ID,
            "rq2_executor_id": "rq2-deterministic-gis-executor/1.0",
            "model_calls": 0,
        },
        "canonicalization": CANONICALIZATION.format("execution_hash"),
        "execution_hash": "0" * 64,
    }
    record["execution_hash"] = artifact_hash(record, "execution_hash")
    return record


def verify_execution_record(
    repository_root: Path,
    proposal: Mapping[str, Any],
    authorization: Mapping[str, Any],
    execution: Mapping[str, Any],
    *,
    fixture_path: Path,
    output_root: Path,
    verification_id: str,
    previous_attempt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Independently inspect source, result, parameters, receipt, and all frozen postconditions."""

    checks: list[dict[str, Any]] = []
    result_path = output_root / "derived-feature.geojson"
    result = read_json(result_path)
    source = read_json(fixture_path)
    features = result.get("features", [])
    feature = features[0] if len(features) == 1 else {}
    source_features = source.get("features", [])
    source_feature = source_features[0] if len(source_features) == 1 else {}
    properties = feature.get("properties", {})
    portrayal = properties.get("nma_portrayal", {})
    expected_values = proposal["expected_final_state"]["derived_artifact"]["semantic_values"]
    actual_result_hash = sha256_file(result_path)
    execution_hash_valid = artifact_hash(execution, "execution_hash")
    _check(
        checks,
        "RQ3_EXECUTION_RECORD_HASH",
        "RESULT_INTEGRITY",
        execution_hash_valid,
        execution["execution_hash"],
        "ARTIFACT_HASH_MISMATCH",
    )
    _check(
        checks,
        "RQ3_PROPOSAL_BINDING",
        "PROPOSAL_INTEGRITY",
        PROPOSAL_HASH,
        execution.get("proposal_hash"),
        "PROPOSAL_HASH_MISMATCH",
    )
    _check(
        checks,
        "RQ3_AUTHORIZATION_BINDING",
        "AUTHORIZATION",
        authorization["authorization_hash"],
        execution.get("authorization_hash"),
        "AUTHORIZATION_HASH_MISMATCH",
    )
    expected_tools = [
        {"step_id": step["step_id"], "operation": step["operation"], "tool": step["tool"]}
        for step in proposal["plan"]
    ]
    _check(
        checks,
        "RQ3_TOOL_SEQUENCE",
        "TOOL_INTEGRITY",
        expected_tools,
        execution.get("authorized_tool_sequence"),
        "UNAUTHORIZED_TOOL",
    )
    expected_calls = [
        item for item in expected_tools if item["operation"] != "verify_postconditions"
    ]
    observed_calls = [
        {key: item[key] for key in ("step_id", "operation", "tool")}
        for item in execution.get("tool_calls", [])
    ]
    _check(
        checks,
        "RQ3_EXECUTED_TOOLS",
        "TOOL_INTEGRITY",
        expected_calls,
        observed_calls,
        "UNAUTHORIZED_TOOL",
    )
    _check(
        checks,
        "RQ3_PARAMETERS_EXACT",
        "PARAMETER_INTEGRITY",
        canonical_sha256(proposal["plan"]),
        execution.get("plan_identity"),
        "PARAMETER_MISMATCH",
    )
    expected_parameter_hashes = [canonical_sha256(step["inputs"]) for step in proposal["plan"]]
    observed_parameter_hashes = [
        item.get("parameter_hash") for item in execution.get("normalized_parameters", [])
    ]
    _check(
        checks,
        "RQ3_PARAMETER_HASHES",
        "PARAMETER_INTEGRITY",
        expected_parameter_hashes,
        observed_parameter_hashes,
        "PARAMETER_MISMATCH",
    )
    source_hash = sha256_file(fixture_path)
    _check(
        checks,
        "RQ3_SOURCE_BEFORE",
        "SCOPE_INTEGRITY",
        source_hash,
        execution["source_refs_before"][0]["sha256"],
        "UNAUTHORIZED_MUTATION",
    )
    _check(
        checks,
        "RQ3_SOURCE_UNCHANGED",
        "SCOPE_INTEGRITY",
        source_hash,
        execution["source_refs_after"][0]["sha256"],
        "UNAUTHORIZED_MUTATION",
    )
    _check(checks, "RQ3_FEATURE_COUNT", "POSTCONDITION", 1, len(features), "POSTCONDITION_FAILED")
    _check(
        checks,
        "RQ3_FEATURE_IDENTITY",
        "POSTCONDITION",
        authorization["authorized_scope"]["feature_ids"][0],
        feature.get("id"),
        "POSTCONDITION_FAILED",
    )
    _check(
        checks,
        "RQ3_CLASSIFICATION",
        "POSTCONDITION",
        expected_values["classification"],
        properties.get("nma_classification"),
        "POSTCONDITION_FAILED",
    )
    _check(
        checks,
        "RQ3_GEOMETRY_TYPE",
        "POSTCONDITION",
        expected_values["geometry"],
        feature.get("geometry", {}).get("type"),
        "POSTCONDITION_FAILED",
    )
    _check(
        checks,
        "RQ3_GEOMETRY_UNCHANGED",
        "POSTCONDITION",
        source_feature.get("geometry"),
        feature.get("geometry"),
        "POSTCONDITION_FAILED",
    )
    _check(
        checks,
        "RQ3_LINE_STYLE",
        "POSTCONDITION",
        expected_values["line_style"],
        portrayal.get("line_code"),
        "POSTCONDITION_FAILED",
    )
    _check(
        checks,
        "RQ3_COLOR_CODE",
        "POSTCONDITION",
        expected_values["color_code"],
        portrayal.get("color_code"),
        "POSTCONDITION_FAILED",
    )
    _check(
        checks,
        "RQ3_OBSERVED_COLOR",
        "POSTCONDITION",
        expected_values["observed_color"],
        portrayal.get("observed_color"),
        "POSTCONDITION_FAILED",
    )
    _check(
        checks,
        "RQ3_SOURCE_AUTHORITY",
        "CONSTRAINT_COMPLIANCE",
        True,
        properties.get("source_authority_evidence_bound"),
        "POSTCONDITION_FAILED",
    )
    _check(
        checks,
        "RQ3_PRODUCT_LAYER_UNRESOLVED",
        "CONSTRAINT_COMPLIANCE",
        None,
        properties.get("product_layer"),
        "UNRESOLVED_CONSTRAINT_ESCALATION",
    )
    _check(
        checks,
        "RQ3_PHYSICAL_GATES_UNRESOLVED",
        "CONSTRAINT_COMPLIANCE",
        None,
        portrayal.get("physical_profile"),
        "UNRESOLVED_CONSTRAINT_ESCALATION",
    )
    _check(
        checks,
        "RQ3_NON_AUTHORITATIVE_RESULT",
        "SCOPE_INTEGRITY",
        False,
        properties.get("authoritative_render"),
        "UNAUTHORIZED_MUTATION",
    )
    _check(
        checks,
        "RQ3_RESULT_PROPOSAL_BOUND",
        "PROPOSAL_INTEGRITY",
        proposal["proposal_hash"],
        properties.get("proposal_hash"),
        "PROPOSAL_HASH_MISMATCH",
    )
    _check(
        checks,
        "RQ3_RESULT_HASH",
        "RESULT_INTEGRITY",
        execution["result_hash"],
        actual_result_hash,
        "ARTIFACT_HASH_MISMATCH",
    )
    _check(
        checks,
        "RQ3_DECLARED_FILES_ONLY",
        "SCOPE_INTEGRITY",
        ["derived-feature.geojson", "execution-receipt.json", "execution-record.json"],
        sorted(path.name for path in output_root.iterdir()),
        "UNAUTHORIZED_MUTATION",
    )
    semantic_hash = canonical_sha256(result)
    if previous_attempt is not None:
        _check(
            checks,
            "RQ3_REPLAY_RESULT_HASH",
            "RESULT_INTEGRITY",
            previous_attempt.get("result_hash"),
            actual_result_hash,
            "ARTIFACT_HASH_MISMATCH",
        )
        _check(
            checks,
            "RQ3_REPLAY_SEMANTIC_HASH",
            "RESULT_INTEGRITY",
            previous_attempt.get("semantic_result_hash"),
            semantic_hash,
            "ARTIFACT_HASH_MISMATCH",
        )
        _check(
            checks,
            "RQ3_REPLAY_VERDICT",
            "AUTHORIZATION",
            previous_attempt.get("verification_verdict"),
            "PASS",
            "REPLAY_LIMIT_EXCEEDED",
        )
    failures = [item for item in checks if item["status"] == "FAIL"]
    verification = {
        "verification_id": verification_id,
        "schema_version": "rq3-verification-report/1.0",
        "proposal_id": proposal["proposal_id"],
        "proposal_hash": proposal["proposal_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "execution_id": execution["execution_id"],
        "execution_hash": execution["execution_hash"],
        "execution_success": bool(execution["execution_success"]),
        "checks": checks,
        "result_refs": deepcopy(execution["result_refs"]),
        "result_hash": execution["result_hash"],
        "overall_verdict": "FAIL" if failures else "PASS",
        "verifier": {"id": VERIFIER_ID, "model_calls": 0},
        "canonicalization": CANONICALIZATION.format("verification_hash"),
        "verification_hash": "0" * 64,
    }
    verification["verification_hash"] = artifact_hash(verification, "verification_hash")
    return verification


def final_acceptance(inputs: Mapping[str, bool]) -> str:
    mandatory = (
        "proposal_integrity_pass",
        "authorization_pass",
        "execution_scope_pass",
        "verification_pass",
        "provenance_complete",
    )
    return "PASS" if all(inputs.get(name) is True for name in mandatory) else "FAIL"


def assemble_audit_record(
    repository_root: Path,
    proposal: Mapping[str, Any],
    authorization: Mapping[str, Any],
    execution: Mapping[str, Any],
    verification: Mapping[str, Any],
    *,
    result_path: Path,
    audit_record_id: str,
    invalidate_evidence: bool = False,
) -> dict[str, Any]:
    evidence_hash = canonical_sha256(proposal["knowledge"]["evidence_refs"])
    observed_result_hash = sha256_file(result_path)
    policy = _policy(repository_root)
    policy_ref = {
        "id": "data/specifications/rq3-trust-policy-v1.0.json",
        "sha256": sha256_file(repository_root / "data/specifications" / POLICY_NAME),
    }
    proposal_ok = proposal.get("proposal_id") == PROPOSAL_ID and proposal_hash(
        proposal
    ) == PROPOSAL_HASH == proposal.get("proposal_hash")
    authorization_ok = (
        not validate_schema(repository_root, AUTHORIZATION_SCHEMA, authorization)
        and _authorization_hash_valid(authorization)
        and authorization.get("proposal_id") == proposal.get("proposal_id")
        and authorization.get("proposal_hash") == proposal.get("proposal_hash")
        and authorization.get("decision") == "APPROVED"
        and authorization.get("authorized_subject")
        == {
            "agent_id": EXECUTOR_ID,
            "operator_id": "rq3-research-operator:fixture-001",
            "workflow_id": WORKFLOW_ID,
        }
        and authorization.get("authorized_scope") == policy["canonical_scope"]
        and authorization.get("allowed_tools") == policy["allowed_tools"]
        and authorization.get("parameter_bounds") == policy["parameter_bounds"]
        and authorization.get("policy_reference") == policy_ref
        and _parse_utc(authorization["issued_at"])
        <= _parse_utc(execution["started_at"])
        < _parse_utc(authorization["valid_until"])
    )
    execution_ok = (
        not validate_schema(repository_root, EXECUTION_SCHEMA, execution)
        and artifact_hash(execution, "execution_hash") == execution.get("execution_hash")
        and execution.get("proposal_id") == proposal.get("proposal_id")
        and execution.get("proposal_hash") == proposal.get("proposal_hash")
        and execution.get("authorization_id") == authorization.get("authorization_id")
        and execution.get("authorization_hash") == authorization.get("authorization_hash")
    )
    verification_ok = (
        not validate_schema(repository_root, VERIFICATION_SCHEMA, verification)
        and artifact_hash(verification, "verification_hash")
        == verification.get("verification_hash")
        and verification.get("execution_hash") == execution.get("execution_hash")
        and verification.get("proposal_hash") == proposal.get("proposal_hash")
        and verification.get("authorization_hash") == authorization.get("authorization_hash")
    )
    result_ok = observed_result_hash == execution.get(
        "result_hash"
    ) and observed_result_hash == verification.get("result_hash")
    evidence_ok = not invalidate_evidence
    provenance_complete = all(
        (proposal_ok, authorization_ok, execution_ok, verification_ok, result_ok, evidence_ok)
    )
    execution_scope_pass = (
        execution.get("execution_success") is True
        and execution.get("source_refs_before") == execution.get("source_refs_after")
        and execution.get("executor", {}).get("model_calls") == 0
    )
    acceptance = final_acceptance(
        {
            "proposal_integrity_pass": proposal_ok,
            "authorization_pass": authorization_ok,
            "execution_scope_pass": execution_scope_pass,
            "verification_pass": verification.get("overall_verdict") == "PASS",
            "provenance_complete": provenance_complete,
        }
    )
    failures: list[str] = []
    if not proposal_ok:
        failures.append("PROPOSAL_HASH_MISMATCH")
    if not authorization_ok:
        failures.append("AUTHORIZATION_HASH_MISMATCH")
    if not evidence_ok:
        failures.append("PROVENANCE_INCOMPLETE")
    if not all((execution_ok, verification_ok, result_ok)):
        failures.append("ARTIFACT_HASH_MISMATCH")
    if verification.get("overall_verdict") != "PASS":
        failures.extend(
            item["failure_code"]
            for item in verification.get("checks", [])
            if item.get("failure_code")
        )
    failures = list(dict.fromkeys(failures))
    result_ref = deepcopy(execution["result_refs"][0])
    links = [
        {
            "artifact_type": "PROPOSAL",
            "artifact_id": proposal["proposal_id"],
            "artifact_hash": proposal["proposal_hash"],
            "relationship": "PROPOSED_WITH",
        },
        {
            "artifact_type": "EVIDENCE",
            "artifact_id": "rq2-evidence-set:canonical-positive",
            "artifact_hash": "0" * 64 if invalidate_evidence else evidence_hash,
            "relationship": "SUPPORTED_BY",
        },
        {
            "artifact_type": "AUTHORIZATION",
            "artifact_id": authorization["authorization_id"],
            "artifact_hash": authorization["authorization_hash"],
            "relationship": "AUTHORIZED_AS",
        },
        {
            "artifact_type": "EXECUTION",
            "artifact_id": execution["execution_id"],
            "artifact_hash": execution["execution_hash"],
            "relationship": "EXECUTED_AS",
        },
        {
            "artifact_type": "VERIFICATION",
            "artifact_id": verification["verification_id"],
            "artifact_hash": verification["verification_hash"],
            "relationship": "VERIFIED_AS",
        },
        {
            "artifact_type": "RESULT",
            "artifact_id": result_ref["id"],
            "artifact_hash": result_ref["sha256"],
            "relationship": "PRODUCED",
        },
    ]
    audit = {
        "audit_record_id": audit_record_id,
        "schema_version": "rq3-audit-record/1.0",
        "proposal_id": proposal["proposal_id"],
        "proposal_hash": proposal["proposal_hash"],
        "evidence_refs": deepcopy(proposal["knowledge"]["evidence_refs"]),
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "execution_id": execution["execution_id"],
        "execution_hash": execution["execution_hash"],
        "execution_success": bool(execution["execution_success"]),
        "verification_id": verification["verification_id"],
        "verification_hash": verification["verification_hash"],
        "verification_verdict": verification["overall_verdict"],
        "result_refs": deepcopy(execution["result_refs"]),
        "result_hashes": [item["sha256"] for item in execution["result_refs"]],
        "provenance_links": links,
        "provenance_complete": provenance_complete,
        "overall_acceptance": acceptance,
        "failure_codes": failures,
        "canonicalization": CANONICALIZATION.format("audit_record_hash"),
        "audit_record_hash": "0" * 64,
    }
    audit["audit_record_hash"] = artifact_hash(audit, "audit_record_hash")
    return audit


def run_authorized_scenario(
    repository_root: Path,
    proposal: Mapping[str, Any],
    authorization: Mapping[str, Any] | None,
    request: Mapping[str, Any] | None,
    *,
    fixture_path: Path,
    retrieval_path: Path,
    output_root: Path,
    state_path: Path,
    started_at: str,
    completed_at: str,
    verification_id: str,
    audit_record_id: str,
    execution_fault: str | None = None,
    tamper_result_after_execution: bool = False,
    invalidate_evidence: bool = False,
) -> dict[str, Any]:
    gate = pre_execution_gate(
        repository_root,
        proposal,
        authorization,
        request,
        fixture_path=fixture_path,
        output_root=output_root,
        state_path=state_path,
        execution_started_at=started_at,
    )
    if gate["status"] != "PASS":
        return {"gate": gate, "overall_acceptance": "FAIL"}
    assert authorization is not None and request is not None
    state = _load_state(state_path)
    previous = state["attempts"][-1] if state["attempts"] else None
    state.update(
        {
            "authorization_id": authorization["authorization_id"],
            "authorization_hash": authorization["authorization_hash"],
            "request_fingerprint": gate["request_fingerprint"],
        }
    )
    state["attempts"].append(
        {
            "execution_id": request["execution_id"],
            "status": "IN_PROGRESS",
            "result_hash": None,
            "semantic_result_hash": None,
            "verification_verdict": None,
        }
    )
    state["execution_count"] = len(state["attempts"])
    write_json(state_path, state)
    rq2_execution = execute_proposal(
        repository_root,
        proposal,
        {"status": "PASS", "failure_taxonomy": []},
        fixture_path=fixture_path,
        output_root=output_root,
        retrieval_package=read_json(retrieval_path),
        fault=execution_fault,
    )
    if rq2_execution["status"] != "PASS":
        state["attempts"][-1]["status"] = "EXECUTION_FAIL"
        write_json(state_path, state)
        return {"gate": gate, "execution": rq2_execution, "overall_acceptance": "FAIL"}
    execution = build_execution_record(
        proposal,
        authorization,
        request,
        rq2_execution,
        output_root=output_root,
        fixture_path=fixture_path,
        started_at=started_at,
        completed_at=completed_at,
    )
    write_json(output_root / "execution-record.json", execution)
    if tamper_result_after_execution:
        result_path = output_root / "derived-feature.geojson"
        original = result_path.read_bytes()
        tampered = original.replace(
            b'"source_claim":"research fixture derived without authoritative source mutation"',
            b'"source_claim":"tampered after execution hashing"',
        )
        if tampered == original:
            raise RQ3DemoError("The deterministic result-tamper seed did not match.")
        result_path.write_bytes(tampered)
    verification = verify_execution_record(
        repository_root,
        proposal,
        authorization,
        execution,
        fixture_path=fixture_path,
        output_root=output_root,
        verification_id=verification_id,
        previous_attempt=previous,
    )
    write_json(output_root / "verification-report.json", verification)
    audit = assemble_audit_record(
        repository_root,
        proposal,
        authorization,
        execution,
        verification,
        result_path=output_root / "derived-feature.geojson",
        audit_record_id=audit_record_id,
        invalidate_evidence=invalidate_evidence,
    )
    write_json(output_root / "audit-record.json", audit)
    semantic_hash = canonical_sha256(read_json(output_root / "derived-feature.geojson"))
    state["attempts"][-1].update(
        {
            "status": audit["overall_acceptance"],
            "result_hash": sha256_file(output_root / "derived-feature.geojson"),
            "semantic_result_hash": semantic_hash,
            "verification_verdict": verification["overall_verdict"],
        }
    )
    write_json(state_path, state)
    return {
        "gate": gate,
        "execution": execution,
        "verification": verification,
        "audit": audit,
        "overall_acceptance": audit["overall_acceptance"],
        "output_root": str(output_root),
    }


def canonical_inputs(repository_root: Path) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    proposal_path = repository_root / "artifacts/rq2/rq2-demo-01-canonical-proposal.json"
    if sha256_file(proposal_path) != PROPOSAL_BYTE_SHA256:
        raise RQ3DemoError("The frozen canonical RQ2 proposal byte identity changed.")
    proposal = read_json(proposal_path)
    if proposal.get("proposal_id") != PROPOSAL_ID or proposal_hash(proposal) != PROPOSAL_HASH:
        raise RQ3DemoError("The frozen canonical RQ2 proposal identity changed.")
    authorization = read_json(
        repository_root / "data/evaluation/rq3-demo-00/valid-authorization.json"
    )
    fixture_path = repository_root / "data/rq2/rq2-demo-01-fire-hydrant.geojson"
    retrieval_path = repository_root / "artifacts/rq2/rq2-demo-01-retrieval.json"
    return proposal, authorization, fixture_path, retrieval_path

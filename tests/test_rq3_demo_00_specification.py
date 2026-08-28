from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import jsonschema

from nma.core import canonical_sha256
from nma.rq2_demo import proposal_hash


ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = "673bcb6efb84de2aeaac5c4b23beda364bea9e44"
PROPOSAL_ID = "rq2-proposal:knowledge-constrained:e635111c3be29423faf923b7"
PROPOSAL_HASH = "116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1"
SPEC = ROOT / "data/specifications"
FIXTURES = ROOT / "data/evaluation/rq3-demo-00"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def without(value: dict[str, Any], field: str) -> dict[str, Any]:
    basis = deepcopy(value)
    basis.pop(field)
    return basis


def schema(name: str) -> dict[str, Any]:
    return load(SPEC / name)


def validator(name: str):
    return jsonschema.Draft202012Validator(
        schema(name), format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
    )


def assert_valid(name: str, instance: dict[str, Any]) -> None:
    errors = sorted(validator(name).iter_errors(instance), key=lambda error: list(error.path))
    assert not errors, "\n".join(error.message for error in errors)


def set_pointer(value: dict[str, Any], pointer: str, replacement: Any) -> None:
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
    target: Any = value
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    final = parts[-1]
    if isinstance(target, list):
        target[int(final)] = replacement
    else:
        target[final] = replacement


def authorization_failure(
    authorization: dict[str, Any], proposal: dict[str, Any], policy: dict[str, Any]
) -> str | None:
    if authorization["authorization_hash"] != canonical_sha256(
        without(authorization, "authorization_hash")
    ):
        return "AUTHORIZATION_HASH_MISMATCH"
    if authorization["proposal_id"] != proposal["proposal_id"]:
        return "PROPOSAL_ID_MISMATCH"
    if authorization["proposal_hash"] != proposal["proposal_hash"]:
        return "PROPOSAL_HASH_MISMATCH"
    if authorization["decision"] != "APPROVED":
        return "AUTHORIZATION_DENIED"
    if authorization["authorized_scope"] != policy["canonical_scope"]:
        return "AUTHORIZATION_SCOPE_MISMATCH"
    if authorization["allowed_tools"] != policy["allowed_tools"]:
        return "UNAUTHORIZED_TOOL"
    if authorization["parameter_bounds"] != policy["parameter_bounds"]:
        return "PARAMETER_MISMATCH"
    return None


def test_json_schemas_are_meta_valid() -> None:
    for name in (
        "rq3-authorization-schema-v1.0.json",
        "rq3-verification-report-schema-v1.0.json",
        "rq3-audit-record-schema-v1.0.json",
    ):
        jsonschema.Draft202012Validator.check_schema(schema(name))


def test_rq2_canonical_proposal_identity_reproduces_exactly() -> None:
    proposal = load(ROOT / "artifacts/rq2/rq2-demo-01-canonical-proposal.json")
    assert proposal["proposal_id"] == PROPOSAL_ID
    assert proposal["proposal_hash"] == PROPOSAL_HASH
    assert proposal_hash(proposal) == PROPOSAL_HASH


def test_valid_authorization_schema_hash_binding_and_policy() -> None:
    proposal = load(ROOT / "artifacts/rq2/rq2-demo-01-canonical-proposal.json")
    policy = load(SPEC / "rq3-trust-policy-v1.0.json")
    authorization = load(FIXTURES / "valid-authorization.json")
    assert_valid("rq3-authorization-schema-v1.0.json", authorization)
    assert authorization["authorization_hash"] == canonical_sha256(
        without(authorization, "authorization_hash")
    )
    assert authorization["policy_reference"]["sha256"] == file_sha256(
        SPEC / "rq3-trust-policy-v1.0.json"
    )
    assert authorization_failure(authorization, proposal, policy) is None


def test_proposal_hash_mismatch_is_a_new_artifact_and_blocks() -> None:
    proposal = load(ROOT / "artifacts/rq2/rq2-demo-01-canonical-proposal.json")
    policy = load(SPEC / "rq3-trust-policy-v1.0.json")
    authorization = load(FIXTURES / "valid-authorization.json")
    example = load(FIXTURES / "negative-proposal-hash-mismatch.json")
    set_pointer(
        authorization,
        example["mutation"]["json_pointer"],
        example["mutation"]["replacement"],
    )
    authorization["authorization_hash"] = canonical_sha256(
        without(authorization, "authorization_hash")
    )
    assert_valid("rq3-authorization-schema-v1.0.json", authorization)
    assert authorization["authorization_hash"] != load(
        FIXTURES / "valid-authorization.json"
    )["authorization_hash"]
    assert authorization_failure(authorization, proposal, policy) == example[
        "expected_failure_code"
    ]


def test_schema_valid_scope_expansion_still_blocks_by_closed_policy() -> None:
    proposal = load(ROOT / "artifacts/rq2/rq2-demo-01-canonical-proposal.json")
    policy = load(SPEC / "rq3-trust-policy-v1.0.json")
    authorization = load(FIXTURES / "valid-authorization.json")
    example = load(FIXTURES / "negative-authorization-scope.json")
    set_pointer(
        authorization,
        example["mutation"]["json_pointer"],
        example["mutation"]["replacement"],
    )
    authorization["authorization_hash"] = canonical_sha256(
        without(authorization, "authorization_hash")
    )
    assert_valid("rq3-authorization-schema-v1.0.json", authorization)
    assert authorization_failure(authorization, proposal, policy) == example[
        "expected_failure_code"
    ]


def test_verification_schema_supports_deterministic_pass_and_fail() -> None:
    passed = load(FIXTURES / "valid-verification-report.json")
    failed = load(FIXTURES / "verification-failure-report.json")
    for report in (passed, failed):
        assert_valid("rq3-verification-report-schema-v1.0.json", report)
        assert report["verification_hash"] == canonical_sha256(
            without(report, "verification_hash")
        )
        assert report["verifier"]["model_calls"] == 0
    assert passed["overall_verdict"] == "PASS"
    assert all(check["status"] != "FAIL" for check in passed["checks"])
    assert failed["execution_success"] is True
    assert failed["overall_verdict"] == "FAIL"
    assert any(check["status"] == "FAIL" for check in failed["checks"])


def test_audit_record_requires_every_mandatory_provenance_type() -> None:
    audit = load(FIXTURES / "valid-audit-record.json")
    policy = load(SPEC / "rq3-trust-policy-v1.0.json")
    assert_valid("rq3-audit-record-schema-v1.0.json", audit)
    assert audit["audit_record_hash"] == canonical_sha256(
        without(audit, "audit_record_hash")
    )
    observed = {link["artifact_type"] for link in audit["provenance_links"]}
    assert observed == set(policy["mandatory_provenance_artifact_types"])

    incomplete = deepcopy(audit)
    incomplete["provenance_links"] = [
        link for link in incomplete["provenance_links"] if link["artifact_type"] != "EVIDENCE"
    ]
    incomplete["audit_record_hash"] = canonical_sha256(
        without(incomplete, "audit_record_hash")
    )
    assert list(validator("rq3-audit-record-schema-v1.0.json").iter_errors(incomplete))


def test_trust_policy_is_closed_machine_readable_and_cases_are_unambiguous() -> None:
    proposal = load(ROOT / "artifacts/rq2/rq2-demo-01-canonical-proposal.json")
    policy = load(SPEC / "rq3-trust-policy-v1.0.json")
    expected_tools = [
        {"step_id": step["step_id"], "tool": step["tool"]} for step in proposal["plan"]
    ]
    assert policy["allowed_tools"] == expected_tools
    assert policy["parameter_bounds"]["proposal_plan_identity"] == canonical_sha256(
        proposal["plan"]
    )
    assert policy["parameter_bounds"]["parameter_overrides_allowed"] is False
    assert policy["authorization"]["scope_expansion_allowed"] is False
    assert policy["acceptance_function"]["llm_override_allowed"] is False
    cases = policy["acceptance_cases"]
    assert [case["case_id"] for case in cases] == list("ABCDEFGHIJKL")
    assert all(case["expected_gate"] and case["expected_final_acceptance"] for case in cases)
    assert [case["expected_final_acceptance"] for case in cases].count("PASS") == 2
    metrics = {entry["metric"]: entry["target"] for entry in policy["metrics"]}
    assert metrics["false_acceptance_rate"] == 0.0
    assert metrics["false_rejection_rate"] == 0.0


def test_only_rq3_demo_00_specification_artifacts_changed() -> None:
    tracked = subprocess.run(
        ["git", "diff", "--name-only", PREDECESSOR, "--"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    changed = set(tracked) | set(untracked)

    def allowed(path: str) -> bool:
        return (
            path == "RQ3-DEMO-00-Authorization-Verification-Provenance-Architecture-Specification.md"
            or path == "tests/test_rq3_demo_00_specification.py"
            or path == "artifacts/rq3/rq3-demo-00-completion-report.json"
            or path.startswith("data/specifications/rq3-")
            or path.startswith("data/evaluation/rq3-demo-00/")
        )

    assert changed
    assert all(allowed(path) for path in changed), changed

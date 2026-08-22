from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
import pytest

import build_contracts.building_production_implementation as building
import nma.core as core
import nma.road_resolution as road
import nma.school_hero_execution as school_execution


ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = "b745a98f8d465259a2cb7c2b3af3df112a10ea37"
GEN00_AUDIT_SHA256 = "2e96f00ada42e22c7dc50387cb1fbf651b6fcbbdff94af796c0fd1985ffe86e3"
PRIVATE_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
CLOSURE_PATH = ROOT / "data/specifications/nma-gen-01-generic-contract-interface-closure-v1.0.json"
CLOSURE_SCHEMA_PATH = ROOT / "schemas/generic-contract-interface-closure-v1.0.schema.json"
LIFECYCLE_SCHEMA_PATH = ROOT / "schemas/generic-lifecycle-envelope-v1.0.schema.json"
ADAPTER_SCHEMA_PATH = ROOT / "schemas/generic-domain-adapter-capability-v1.0.schema.json"
GEN00_PATHS = {
    "GEN-00-Generalization-Audit.md",
    "data/specifications/nma-gen-00-feature-production-generalization-audit-v1.0.json",
    "schemas/feature-production-generalization-audit-v1.0.schema.json",
    "tests/test_feature_production_generalization_gen00.py",
}
MANDATORY_CAPABILITIES = {
    "domain_identification",
    "contract_version_declaration",
    "input_validation",
    "canonical_identity_consumption",
    "authorization_consumption",
    "planning_boundary",
    "execution_boundary",
    "observation_production",
    "receipt_production",
    "provenance_reporting",
    "verification_boundary",
    "capability_declaration",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _git(*arguments: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        check=check,
        capture_output=True,
    )
    return result.stdout.strip()


def _ref(seed: str, contract: str) -> dict[str, str]:
    return {
        "artifact_id": f"artifact-{seed}",
        "artifact_sha256": hashlib.sha256(seed.encode()).hexdigest(),
        "contract_version": f"{contract}/1.0",
    }


def _lifecycle_instance(*, role: str = "plan") -> dict[str, Any]:
    authorization = _ref("authorization", "nma.production-authorization")
    basis: dict[str, Any] = {
        "schema_version": "nma.generic-lifecycle-envelope/1.0",
        "envelope_id": "gen01-envelope-school-plan",
        "domain_id": "school-hero",
        "adapter_contract": {"id": "nma.generic-domain-adapter", "version": "1.0"},
        "capability_declaration": _ref(
            "school-capability", "nma.generic-domain-adapter-capability"
        ),
        "lifecycle_role": role,
        "artifact": _ref("school-plan", "nma.school-hero-plan"),
        "lineage": {
            "parents": [authorization],
            "provenance_references": [_ref("school-provenance", "nma.school-provenance")],
        },
        "authorization": {
            "required_before_mutation": True,
            "state": "bound",
            "reference": authorization,
        },
        "canonical_identity": {
            "provider": "nma.core.canonical_sha256",
            "canonicalizer": "nma.core.canonical_json",
            "fallback_allowed": False,
        },
        "validation": {
            "status": "valid",
            "completed_before_domain_mutation": True,
            "checks": [{"check_id": "contract-valid", "result": "PASS"}],
        },
        "domain_payload": {
            "school_specific_field": "opaque-to-generic-layer",
            "geometry_rule": {"role": "Point"},
        },
        "ownership": {
            "payload_interpretation": "domain",
            "semantics": "domain",
            "geometry": "domain",
            "portrayal": "domain",
            "rollback_behavior": "domain",
            "activation_behavior": "domain",
        },
        "mutation_boundary": {
            "contract_processing_authorized": False,
            "domain_executor_invoked": False,
            "production_mutation_performed": False,
        },
    }
    return {**basis, "envelope_sha256": core.canonical_sha256(basis)}


def _contract_ref(contract_id: str, path: str) -> dict[str, Any]:
    return {
        "contract_id": contract_id,
        "contract_version": "1.0",
        "evidence_paths": [path],
    }


def _optional(supported: bool, contract_id: str, path: str) -> dict[str, Any]:
    return {
        "supported": supported,
        "behavior_owner": "domain",
        "contract_reference": _contract_ref(contract_id, path) if supported else None,
    }


def _adapter_declaration(domain: str) -> dict[str, Any]:
    profiles = {
        "school-hero": {
            "root": "src/nma/school_hero_execution.py",
            "verifier": "src/nma/school_hero_verification.py",
            "rollback": _optional(
                True, "nma.school-hero-rollback", "schemas/rollback-manifest-v1.0.schema.json"
            ),
            "activation": _optional(False, "unused", "unused"),
            "release": _optional(False, "unused", "unused"),
        },
        "road": {
            "root": "src/nma/road_execution.py",
            "verifier": "src/nma/road_verification.py",
            "rollback": _optional(
                True, "nma.road-rollback", "schemas/road-rollback-manifest-v1.0.schema.json"
            ),
            "activation": _optional(False, "unused", "unused"),
            "release": _optional(True, "nma.road-release", "ROAD-FINAL-Completion-Report.md"),
        },
        "build": {
            "root": "build_contracts/building_production_implementation.py",
            "verifier": "build_contracts/building_production_verification.py",
            "rollback": _optional(
                True,
                "nma.build-cleanup-and-deactivation",
                "build_contracts/building_production_activation.py",
            ),
            "activation": _optional(
                True,
                "nma.building-production-activation",
                "schemas/building-production-activation-v1.0.schema.json",
            ),
            "release": _optional(True, "nma.build-release", "BUILD-FINAL-Completion-Report.md"),
        },
    }
    profile = profiles[domain]
    basis: dict[str, Any] = {
        "schema_version": "nma.generic-domain-adapter-capability/1.0",
        "declaration_id": f"gen01-{domain}-compatibility-declaration",
        "domain": {
            "domain_id": domain,
            "contract_id": f"nma.{domain}",
            "contract_version": "1.0",
        },
        "adapter_contract": {"id": "nma.generic-domain-adapter", "version": "1.0"},
        "canonical_identity": {
            "provider": "nma.core.canonical_sha256",
            "required": True,
            "fallback_allowed": False,
        },
        "mandatory_capabilities": dict.fromkeys(sorted(MANDATORY_CAPABILITIES), True),
        "optional_capabilities": {
            "rollback_evidence": profile["rollback"],
            "activation_evidence": profile["activation"],
            "release_evidence": profile["release"],
        },
        "domain_contract_references": {
            "semantics": _contract_ref(f"nma.{domain}-semantics", profile["root"]),
            "geometry": _contract_ref(f"nma.{domain}-geometry", profile["root"]),
            "portrayal": _contract_ref(f"nma.{domain}-portrayal", profile["root"]),
            "verification": _contract_ref(f"nma.{domain}-verification", profile["verifier"]),
            "provenance": _contract_ref(f"nma.{domain}-provenance", profile["verifier"]),
        },
        "ownership": {
            "generic_payload_treatment": "opaque",
            "semantics": "domain",
            "geometry": "domain",
            "portrayal": "domain",
            "rollback_behavior": "domain",
            "activation_behavior": "domain",
        },
        "dependency_failure": {"fails_before_mutation": True, "fallback_allowed": False},
        "mutation_boundary": {
            "declaration_grants_production_authority": False,
            "validation_invokes_execution": False,
            "validation_performs_mutation": False,
        },
    }
    return {**basis, "declaration_sha256": core.canonical_sha256(basis)}


def test_closed_schemas_and_canonical_closure_identity() -> None:
    schemas = [
        _load(path) for path in (CLOSURE_SCHEMA_PATH, LIFECYCLE_SCHEMA_PATH, ADAPTER_SCHEMA_PATH)
    ]
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False

    closure = _load(CLOSURE_PATH)
    Draft202012Validator(schemas[0]).validate(closure)
    basis = deepcopy(closure)
    supplied = basis.pop("closure_sha256")
    assert supplied == core.canonical_sha256(basis)
    assert closure["verdict"] == "PASS — GENERIC CONTRACT AND DOMAIN INTERFACE CLOSED"


def test_canonical_core_identity_is_single_and_fail_closed() -> None:
    closure = _load(CLOSURE_PATH)
    boundary = closure["core_identity_boundary"]
    assert boundary == {
        "authority_count": 1,
        "fallback_authority_count": 0,
        "provider": "nma.core.canonical_sha256",
        "canonicalizer": "nma.core.canonical_json",
        "dependency_required": True,
        "missing_dependency_behavior": "fail-closed",
        "production_mutation_before_failure": False,
    }
    assert school_execution.canonical_sha256 is core.canonical_sha256
    assert road.canonical_sha256 is core.canonical_sha256
    assert building.canonical_sha256 is core.canonical_sha256


def test_lifecycle_envelope_accepts_closed_valid_instance() -> None:
    validator = Draft202012Validator(_load(LIFECYCLE_SCHEMA_PATH))
    envelope = _lifecycle_instance()
    validator.validate(envelope)
    supplied = envelope.pop("envelope_sha256")
    assert supplied == core.canonical_sha256(envelope)
    assert supplied == core.canonical_sha256(deepcopy(envelope))

    pre_authorization = _lifecycle_instance(role="intent")
    pre_authorization["authorization"] = {
        "required_before_mutation": True,
        "state": "pre-authorization",
        "reference": None,
    }
    pre_authorization.pop("envelope_sha256")
    pre_authorization["envelope_sha256"] = core.canonical_sha256(pre_authorization)
    validator.validate(pre_authorization)


def test_lifecycle_envelope_rejects_missing_extra_version_and_identity_dependency() -> None:
    validator = Draft202012Validator(_load(LIFECYCLE_SCHEMA_PATH))
    cases = []
    missing_domain = _lifecycle_instance()
    missing_domain.pop("domain_id")
    cases.append(missing_domain)
    extra = _lifecycle_instance()
    extra["generic_execution"] = True
    cases.append(extra)
    bad_version = _lifecycle_instance()
    bad_version["adapter_contract"]["version"] = "2.0"
    cases.append(bad_version)
    missing_identity = _lifecycle_instance()
    missing_identity.pop("canonical_identity")
    cases.append(missing_identity)
    fallback = _lifecycle_instance()
    fallback["canonical_identity"]["fallback_allowed"] = True
    cases.append(fallback)
    for case in cases:
        with pytest.raises(ValidationError):
            validator.validate(case)


def test_post_authorization_roles_require_authorization_linkage() -> None:
    validator = Draft202012Validator(_load(LIFECYCLE_SCHEMA_PATH))
    for role in (
        "plan",
        "execution",
        "derived-output",
        "observation",
        "receipt",
        "provenance",
        "verification",
        "rollback-evidence",
        "activation-evidence",
        "release-evidence",
    ):
        envelope = _lifecycle_instance(role=role)
        envelope["authorization"] = {
            "required_before_mutation": True,
            "state": "pre-authorization",
            "reference": None,
        }
        with pytest.raises(ValidationError):
            validator.validate(envelope)


def test_adapter_declaration_accepts_all_three_evidence_profiles() -> None:
    validator = Draft202012Validator(_load(ADAPTER_SCHEMA_PATH))
    for domain in ("school-hero", "road", "build"):
        declaration = _adapter_declaration(domain)
        validator.validate(declaration)
        basis = deepcopy(declaration)
        supplied = basis.pop("declaration_sha256")
        assert supplied == core.canonical_sha256(basis)
        paths = {
            path
            for ref in declaration["domain_contract_references"].values()
            for path in ref["evidence_paths"]
        }
        assert all((ROOT / path).is_file() for path in paths)


def test_adapter_contract_rejects_drift_and_missing_mandatory_capabilities() -> None:
    validator = Draft202012Validator(_load(ADAPTER_SCHEMA_PATH))
    bad_version = _adapter_declaration("school-hero")
    bad_version["adapter_contract"]["version"] = "2.0"
    missing = _adapter_declaration("road")
    missing["mandatory_capabilities"].pop("authorization_consumption")
    extra = _adapter_declaration("build")
    extra["universal_geometry_framework"] = True
    for case in (bad_version, missing, extra):
        with pytest.raises(ValidationError):
            validator.validate(case)


def test_capability_honesty_requires_contract_reference() -> None:
    validator = Draft202012Validator(_load(ADAPTER_SCHEMA_PATH))
    unsupported_claim = _adapter_declaration("school-hero")
    unsupported_claim["optional_capabilities"]["activation_evidence"]["supported"] = True
    with pytest.raises(ValidationError):
        validator.validate(unsupported_claim)

    false_with_reference = _adapter_declaration("road")
    false_with_reference["optional_capabilities"]["activation_evidence"] = _optional(
        False, "unused", "unused"
    )
    false_with_reference["optional_capabilities"]["activation_evidence"]["contract_reference"] = (
        _contract_ref(
            "nma.invented-activation", "schemas/building-production-activation-v1.0.schema.json"
        )
    )
    with pytest.raises(ValidationError):
        validator.validate(false_with_reference)


def test_domain_ownership_is_normative_and_opaque() -> None:
    closure = _load(CLOSURE_PATH)
    records = closure["domain_owned_responsibilities"]
    assert {item["area"] for item in records} == {
        "semantics",
        "geometry",
        "portrayal",
        "rollback",
        "activation",
    }
    assert all(item["owner"] == "DOMAIN_OWNED" for item in records)

    envelope = _lifecycle_instance()
    envelope["domain_payload"] = {
        "arbitrary_domain_schema": [1, {"feature_meaning": "not interpreted"}],
        "portrayal": {"domain_specific": True},
    }
    Draft202012Validator(_load(LIFECYCLE_SCHEMA_PATH)).validate(envelope)
    invalid_owner = _adapter_declaration("build")
    invalid_owner["ownership"]["geometry"] = "generic"
    with pytest.raises(ValidationError):
        Draft202012Validator(_load(ADAPTER_SCHEMA_PATH)).validate(invalid_owner)


def test_evidence_matrix_is_complete_and_paths_exist() -> None:
    closure = _load(CLOSURE_PATH)
    matrix = closure["evidence_matrix"]
    assert [row["concern"] for row in matrix] == [
        "Core identity",
        "Authorization",
        "Planning",
        "Execution",
        "Observation",
        "Receipt",
        "Provenance",
        "Verification/QA",
        "Semantics",
        "Geometry",
        "Portrayal",
        "Rollback",
        "Activation",
    ]
    classifications = {
        "SHARED",
        "DOMAIN_OWNED",
        "OPTIONAL_CAPABILITY",
        "NOT_SUPPORTED",
        "UNRESOLVED",
    }
    for row in matrix:
        assert row["generic_classification"] in classifications
        for domain in ("school_hero", "road", "build"):
            evidence = row[domain]
            assert evidence["classification"] in classifications
            assert all((ROOT / path).is_file() for path in evidence["evidence_paths"])


def test_mutation_boundary_has_no_production_authority() -> None:
    closure = _load(CLOSURE_PATH)
    boundary = closure["mutation_boundary"]
    assert boundary["existing_domain_execution_paths_remain_authoritative"] is True
    assert all(
        value is False
        for key, value in boundary.items()
        if key != "existing_domain_execution_paths_remain_authoritative"
    )
    for path in (LIFECYCLE_SCHEMA_PATH, ADAPTER_SCHEMA_PATH):
        text = path.read_text(encoding="utf-8")
        assert '"validation_performs_mutation": {"const": false}' in text or (
            '"production_mutation_performed": {"const": false}' in text
        )
    assert not any(
        path.startswith(("src/", "build_contracts/", "agent_contracts/"))
        for path in closure["allowed_change_paths"]
    )


def test_frozen_implementations_and_gen00_are_unchanged() -> None:
    protected = ["src", "build_contracts", "agent_contracts", *sorted(GEN00_PATHS)]
    assert _git("diff", "--name-only", PREDECESSOR, "--", *protected) == ""
    for path in GEN00_PATHS:
        assert _git("hash-object", path) == _git("rev-parse", f"{PREDECESSOR}:{path}")

    audit = _load(
        ROOT / "data/specifications/nma-gen-00-feature-production-generalization-audit-v1.0.json"
    )
    supplied = audit.pop("audit_sha256")
    assert supplied == core.canonical_sha256(audit) == GEN00_AUDIT_SHA256


def test_frozen_identities_and_private_archive_boundary() -> None:
    closure = _load(CLOSURE_PATH)
    frozen = closure["frozen_identities"]
    assert _git("rev-parse", "nma-build-v1.0-final^{}") == frozen["build_final"]["commit"]
    assert _git("cat-file", "-t", "nma-build-v1.0-final") == "tag"
    assert _git("rev-parse", "nma-core-v1.0-final^{}") == frozen["core_final"]["commit"]
    assert _git("cat-file", "-t", "nma-core-v1.0-final") == "tag"
    assert _git("rev-parse", "nma-road-v1.0-final^{}") == frozen["road_final"]["commit"]
    assert _git("cat-file", "-t", "nma-road-v1.0-final") == "tag"
    assert (
        _git("rev-parse", "refs/remotes/origin/freeze/hero-final-school-hero-56f99eb")
        == frozen["school_hero"]["commit"]
    )

    archive = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
    assert archive.is_file()
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == PRIVATE_ARCHIVE_SHA256
    assert _git("check-ignore", archive.relative_to(ROOT).as_posix())
    tracked = _git("ls-files", archive.relative_to(ROOT).as_posix())
    staged = _git("diff", "--cached", "--name-only", "--", archive.relative_to(ROOT).as_posix())
    assert tracked == staged == ""


def test_allowed_change_scope_only() -> None:
    closure = _load(CLOSURE_PATH)
    allowed = set(closure["allowed_change_paths"])
    tracked_changes = set(filter(None, _git("diff", "--name-only", PREDECESSOR).splitlines()))
    untracked = set(filter(None, _git("ls-files", "--others", "--exclude-standard").splitlines()))
    assert tracked_changes | untracked == allowed
    assert not any(
        path.startswith(("src/", "build_contracts/", "agent_contracts/"))
        for path in tracked_changes | untracked
    )


def test_invariant_matrix_is_complete_and_covered() -> None:
    closure = _load(CLOSURE_PATH)
    invariants = closure["invariants"]
    assert [item["id"] for item in invariants] == [f"GINV-{index:02d}" for index in range(1, 11)]
    assert all(item["status"] in {"ACCEPTED", "ACCEPTED_BOUNDED"} for item in invariants)
    for invariant in invariants:
        assert all(name in globals() for name in invariant["test_coverage"])
        assert all((ROOT / path).is_file() for path in invariant["evidence_paths"])

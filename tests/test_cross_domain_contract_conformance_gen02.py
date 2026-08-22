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
import nma.school_hero_execution as school


ROOT = Path(__file__).resolve().parents[1]
GEN01_COMMIT = "7bb83f05480f642da23e7a2b244b38c3804d5fb7"
GEN01_CLOSURE_SHA256 = "03b80441bbf317ac2e2b6cd92c3a86309c4cc7465109a3d34b6d24636491c35d"
GEN00_COMMIT = "b745a98f8d465259a2cb7c2b3af3df112a10ea37"
GEN00_AUDIT_SHA256 = "2e96f00ada42e22c7dc50387cb1fbf651b6fcbbdff94af796c0fd1985ffe86e3"
PRIVATE_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
DOMAIN_SCHEMA_PATH = ROOT / "schemas/domain-contract-conformance-v1.0.schema.json"
MATRIX_SCHEMA_PATH = ROOT / "schemas/cross-domain-contract-conformance-matrix-v1.0.schema.json"
LIFECYCLE_SCHEMA_PATH = ROOT / "schemas/generic-lifecycle-envelope-v1.0.schema.json"
ADAPTER_SCHEMA_PATH = ROOT / "schemas/generic-domain-adapter-capability-v1.0.schema.json"
CLOSURE_PATH = ROOT / "data/specifications/nma-gen-01-generic-contract-interface-closure-v1.0.json"
MATRIX_PATH = (
    ROOT / "data/specifications/nma-gen-02-cross-domain-contract-conformance-matrix-v1.0.json"
)
RECORD_PATHS = {
    "school-hero": ROOT
    / "data/specifications/nma-gen-02-school-hero-contract-conformance-v1.0.json",
    "road": ROOT / "data/specifications/nma-gen-02-road-contract-conformance-v1.0.json",
    "build": ROOT / "data/specifications/nma-gen-02-build-contract-conformance-v1.0.json",
}
GEN01_PATHS = {
    "GEN-01-Completion-Report.md",
    "data/specifications/nma-gen-01-generic-contract-interface-closure-v1.0.json",
    "schemas/generic-contract-interface-closure-v1.0.schema.json",
    "schemas/generic-domain-adapter-capability-v1.0.schema.json",
    "schemas/generic-lifecycle-envelope-v1.0.schema.json",
    "tests/test_generic_contract_interface_closure_gen01.py",
}
ALLOWED_PATHS = {
    "GEN-02-Completion-Report.md",
    "data/specifications/nma-gen-02-build-contract-conformance-v1.0.json",
    "data/specifications/nma-gen-02-cross-domain-contract-conformance-matrix-v1.0.json",
    "data/specifications/nma-gen-02-road-contract-conformance-v1.0.json",
    "data/specifications/nma-gen-02-school-hero-contract-conformance-v1.0.json",
    "schemas/cross-domain-contract-conformance-matrix-v1.0.schema.json",
    "schemas/domain-contract-conformance-v1.0.schema.json",
    "tests/test_cross_domain_contract_conformance_gen02.py",
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
        capture_output=True,
        check=check,
    )
    return result.stdout.strip()


def _ref(seed: str, contract: str) -> dict[str, str]:
    return {
        "artifact_id": f"artifact-{seed}",
        "artifact_sha256": hashlib.sha256(seed.encode()).hexdigest(),
        "contract_version": f"{contract}/1.0",
    }


def _lifecycle_instance(domain: str) -> dict[str, Any]:
    authorization = _ref(f"{domain}-authorization", f"nma.{domain}-authorization")
    payloads = {
        "school-hero": {
            "school_codes": ["0301"],
            "geometry": {"role": "Point"},
        },
        "road": {
            "route": {"name": "County Highway 126", "ordered_segments": [1, 2]},
            "portrayal": {"shield": "domain-owned"},
        },
        "build": {
            "source": {"geometry": "PolygonZ", "package_binding": "domain-owned"},
            "activation": {"separate_authorization_required": True},
        },
    }
    basis: dict[str, Any] = {
        "schema_version": "nma.generic-lifecycle-envelope/1.0",
        "envelope_id": f"gen02-{domain}-plan",
        "domain_id": domain,
        "adapter_contract": {"id": "nma.generic-domain-adapter", "version": "1.0"},
        "capability_declaration": _ref(
            f"{domain}-capability", "nma.generic-domain-adapter-capability"
        ),
        "lifecycle_role": "plan",
        "artifact": _ref(f"{domain}-plan", f"nma.{domain}-plan"),
        "lineage": {
            "parents": [authorization],
            "provenance_references": [_ref(f"{domain}-provenance", f"nma.{domain}-provenance")],
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
            "checks": [{"check_id": "domain-contract-valid", "result": "PASS"}],
        },
        "domain_payload": payloads[domain],
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


def _contract_ref(domain: str, area: str) -> dict[str, Any]:
    return {
        "contract_id": f"nma.{domain}-{area}",
        "contract_version": "1.0",
        "evidence_paths": [RECORD_PATHS[domain].relative_to(ROOT).as_posix()],
    }


def _optional(domain: str, area: str, supported: bool) -> dict[str, Any]:
    return {
        "supported": supported,
        "behavior_owner": "domain",
        "contract_reference": _contract_ref(domain, area) if supported else None,
    }


def _adapter_declaration(domain: str) -> dict[str, Any]:
    supported = {
        "school-hero": {"rollback": True, "activation": False, "release": False},
        "road": {"rollback": True, "activation": False, "release": True},
        "build": {"rollback": True, "activation": True, "release": True},
    }[domain]
    basis: dict[str, Any] = {
        "schema_version": "nma.generic-domain-adapter-capability/1.0",
        "declaration_id": f"gen02-{domain}-capability",
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
            "rollback_evidence": _optional(domain, "rollback", supported["rollback"]),
            "activation_evidence": _optional(domain, "activation", supported["activation"]),
            "release_evidence": _optional(domain, "release", supported["release"]),
        },
        "domain_contract_references": {
            area: _contract_ref(domain, area)
            for area in ("semantics", "geometry", "portrayal", "verification", "provenance")
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


def _all_evidence_paths(value: Any) -> set[str]:
    if isinstance(value, dict):
        paths = set(value.get("evidence_paths", []))
        for nested in value.values():
            paths.update(_all_evidence_paths(nested))
        return paths
    if isinstance(value, list):
        paths: set[str] = set()
        for nested in value:
            paths.update(_all_evidence_paths(nested))
        return paths
    return set()


def test_exact_predecessor_closure_and_gen00_identities() -> None:
    assert _git("merge-base", GEN01_COMMIT, "HEAD") == GEN01_COMMIT
    assert _git("rev-parse", "refs/heads/gen/gen-01-generic-contract-interface-closure") == (
        GEN01_COMMIT
    )
    assert (
        _git("rev-parse", "refs/remotes/origin/gen/gen-01-generic-contract-interface-closure")
        == GEN01_COMMIT
    )
    assert _git("rev-parse", "refs/heads/gen/gen-00-feature-production-generalization-audit") == (
        GEN00_COMMIT
    )
    assert (
        _git("rev-parse", "refs/remotes/origin/gen/gen-00-feature-production-generalization-audit")
        == GEN00_COMMIT
    )

    closure = _load(CLOSURE_PATH)
    supplied_closure = closure.pop("closure_sha256")
    assert supplied_closure == core.canonical_sha256(closure) == GEN01_CLOSURE_SHA256
    audit = _load(
        ROOT / "data/specifications/nma-gen-00-feature-production-generalization-audit-v1.0.json"
    )
    supplied_audit = audit.pop("audit_sha256")
    assert supplied_audit == core.canonical_sha256(audit) == GEN00_AUDIT_SHA256


def test_gen02_schemas_are_closed_draft_2020_12_schemas() -> None:
    for path in (DOMAIN_SCHEMA_PATH, MATRIX_SCHEMA_PATH):
        schema = _load(path)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False


def test_all_three_domain_records_validate_and_hash_deterministically() -> None:
    validator = Draft202012Validator(_load(DOMAIN_SCHEMA_PATH))
    expected_ids = {
        "school-hero": "GEN-02-SCHOOL-HERO",
        "road": "GEN-02-ROAD",
        "build": "GEN-02-BUILD",
    }
    for domain, path in RECORD_PATHS.items():
        record = _load(path)
        validator.validate(record)
        assert record["domain_id"] == domain
        assert record["record_id"] == expected_ids[domain]
        supplied = record.pop("record_sha256")
        assert supplied == core.canonical_sha256(record)
        assert supplied == core.canonical_sha256(deepcopy(record))
        assert all((ROOT / evidence).is_file() for evidence in _all_evidence_paths(record))


def test_aggregate_matrix_validates_links_records_and_hashes_deterministically() -> None:
    matrix = _load(MATRIX_PATH)
    Draft202012Validator(_load(MATRIX_SCHEMA_PATH)).validate(matrix)
    supplied = matrix.pop("matrix_sha256")
    assert supplied == core.canonical_sha256(matrix)
    assert supplied == core.canonical_sha256(deepcopy(matrix))
    results = {item["domain_id"]: item for item in matrix["domain_results"]}
    assert set(results) == set(RECORD_PATHS)
    for domain, path in RECORD_PATHS.items():
        record = _load(path)
        assert results[domain]["record_path"] == path.relative_to(ROOT).as_posix()
        assert results[domain]["record_sha256"] == record["record_sha256"]
        assert results[domain]["verdict"] == "CONFORMS"


def test_one_closed_lifecycle_contract_accepts_opaque_payloads_for_all_domains() -> None:
    validator = Draft202012Validator(_load(LIFECYCLE_SCHEMA_PATH))
    payloads = []
    for domain in RECORD_PATHS:
        envelope = _lifecycle_instance(domain)
        validator.validate(envelope)
        supplied = envelope.pop("envelope_sha256")
        assert supplied == core.canonical_sha256(envelope)
        payloads.append(envelope["domain_payload"])
    assert len({core.canonical_sha256(payload) for payload in payloads}) == 3
    assert {tuple(sorted(payload)) for payload in payloads} == {
        ("geometry", "school_codes"),
        ("portrayal", "route"),
        ("activation", "source"),
    }


def test_one_closed_adapter_contract_accepts_honest_domain_capabilities() -> None:
    validator = Draft202012Validator(_load(ADAPTER_SCHEMA_PATH))
    declarations = {domain: _adapter_declaration(domain) for domain in RECORD_PATHS}
    for declaration in declarations.values():
        validator.validate(declaration)
        supplied = declaration.pop("declaration_sha256")
        assert supplied == core.canonical_sha256(declaration)
    assert (
        declarations["school-hero"]["optional_capabilities"]["activation_evidence"]["supported"]
        is False
    )
    assert (
        declarations["road"]["optional_capabilities"]["activation_evidence"]["supported"] is False
    )
    assert (
        declarations["build"]["optional_capabilities"]["activation_evidence"]["supported"] is True
    )


def test_every_mandatory_capability_and_generic_invariant_conforms() -> None:
    for path in RECORD_PATHS.values():
        record = _load(path)
        assert set(record["mandatory_capabilities"]) == MANDATORY_CAPABILITIES
        assert all(
            result["classification"] == "CONFORMS"
            for result in record["mandatory_capabilities"].values()
        )
        assert set(record["generic_invariants"]) == {f"GINV-{index:02d}" for index in range(1, 11)}
        assert all(
            result["classification"] == "CONFORMS"
            for result in record["generic_invariants"].values()
        )


def test_domain_ownership_and_optional_absence_are_not_failures() -> None:
    records = {domain: _load(path) for domain, path in RECORD_PATHS.items()}
    for record in records.values():
        assert set(record["domain_owned_responsibilities"].values()) == {
            "DOMAIN_OWNED_NOT_APPLICABLE"
        }
        assert record["overall_conformance_verdict"] == "CONFORMS"
    for domain in ("school-hero", "road"):
        activation = records[domain]["optional_capabilities"]["activation_evidence"]
        assert activation == {
            "declared": False,
            "classification": "NOT_SUPPORTED_BY_DOMAIN",
            "behavior_owner": "domain",
            "contract_reference": None,
        }


def test_negative_lifecycle_examples_fail_deterministically() -> None:
    validator = Draft202012Validator(_load(LIFECYCLE_SCHEMA_PATH))
    cases = []
    wrong_version = _lifecycle_instance("school-hero")
    wrong_version["adapter_contract"]["version"] = "2.0"
    cases.append(wrong_version)
    wrong_authority = _lifecycle_instance("road")
    wrong_authority["canonical_identity"]["provider"] = "nma.road.local_sha256"
    cases.append(wrong_authority)
    missing_mandatory = _lifecycle_instance("build")
    missing_mandatory.pop("domain_id")
    cases.append(missing_mandatory)
    malformed_linkage = _lifecycle_instance("school-hero")
    malformed_linkage["authorization"] = {
        "required_before_mutation": True,
        "state": "pre-authorization",
        "reference": None,
    }
    cases.append(malformed_linkage)
    unsupported_field = _lifecycle_instance("road")
    unsupported_field["generic_geometry_algorithm"] = "invented"
    cases.append(unsupported_field)
    mutation_authority = _lifecycle_instance("build")
    mutation_authority["mutation_boundary"]["contract_processing_authorized"] = True
    cases.append(mutation_authority)
    for case in cases:
        with pytest.raises(ValidationError):
            validator.validate(case)


def test_negative_capability_claims_fail_deterministically() -> None:
    validator = Draft202012Validator(_load(ADAPTER_SCHEMA_PATH))
    false_claim = _adapter_declaration("school-hero")
    false_claim["optional_capabilities"]["activation_evidence"]["supported"] = True
    incompatible = _adapter_declaration("road")
    incompatible["optional_capabilities"]["activation_evidence"] = _optional(
        "road", "activation", True
    )
    incompatible["optional_capabilities"]["activation_evidence"]["supported"] = False
    missing_mandatory = _adapter_declaration("build")
    missing_mandatory["mandatory_capabilities"].pop("authorization_consumption")
    for case in (false_claim, incompatible, missing_mandatory):
        with pytest.raises(ValidationError):
            validator.validate(case)


def test_negative_gen02_record_examples_fail_deterministically() -> None:
    validator = Draft202012Validator(_load(DOMAIN_SCHEMA_PATH))
    wrong_contract = _load(RECORD_PATHS["school-hero"])
    wrong_contract["adapter_contract"]["version"] = "2.0"
    mutation_injected = _load(RECORD_PATHS["road"])
    mutation_injected["mutation_boundary"]["writeback"] = True
    invented_field = _load(RECORD_PATHS["build"])
    invented_field["generic_portrayal"] = {"owner": "generic"}
    for case in (wrong_contract, mutation_injected, invented_field):
        with pytest.raises(ValidationError):
            validator.validate(case)


def test_canonical_core_identity_is_shared_without_fallback() -> None:
    assert school.canonical_sha256 is core.canonical_sha256
    assert road.canonical_sha256 is core.canonical_sha256
    assert building.canonical_sha256 is core.canonical_sha256
    for domain in RECORD_PATHS:
        declaration = _adapter_declaration(domain)
        assert declaration["canonical_identity"] == {
            "provider": "nma.core.canonical_sha256",
            "required": True,
            "fallback_allowed": False,
        }


def test_gen01_contract_and_all_frozen_implementations_are_unchanged() -> None:
    assert _git("diff", "--name-only", GEN01_COMMIT, "--", *sorted(GEN01_PATHS)) == ""
    for path in GEN01_PATHS:
        assert _git("hash-object", path) == _git("rev-parse", f"{GEN01_COMMIT}:{path}")
    assert (
        _git("diff", "--name-only", GEN01_COMMIT, "--", "src", "build_contracts", "agent_contracts")
        == ""
    )
    assert _git("rev-parse", "nma-build-v1.0-final^{}") == (
        "95de5fa3657a2c8ac7847f1ee1010c48ea984cd7"
    )
    assert _git("cat-file", "-t", "nma-build-v1.0-final") == "tag"
    assert _git("rev-parse", "nma-core-v1.0-final^{}") == (
        "5eb138ae7686502431587743ebce9ddf92c5a799"
    )
    assert _git("cat-file", "-t", "nma-core-v1.0-final") == "tag"
    assert _git("rev-parse", "nma-road-v1.0-final^{}") == (
        "325c70d5335f57c43a8af85822db25032aa225c3"
    )
    assert _git("cat-file", "-t", "nma-road-v1.0-final") == "tag"
    assert _git("rev-parse", "refs/remotes/origin/freeze/hero-final-school-hero-56f99eb") == (
        "56f99eb9ae63272a68accac3041fb10eacefb986"
    )


def test_verification_artifacts_cannot_authorize_or_perform_mutation() -> None:
    matrix = _load(MATRIX_PATH)
    assert set(matrix["mutation_safety"].values()) == {False}
    for path in RECORD_PATHS.values():
        boundary = _load(path)["mutation_boundary"]
        assert boundary.pop("classification") == "CONFORMS"
        assert set(boundary.values()) == {False}
    changes = set(filter(None, _git("diff", "--name-only", GEN01_COMMIT).splitlines()))
    untracked = set(filter(None, _git("ls-files", "--others", "--exclude-standard").splitlines()))
    assert changes | untracked == ALLOWED_PATHS
    assert not any(
        path.startswith(("src/", "build_contracts/", "agent_contracts/"))
        for path in changes | untracked
    )


def test_private_archive_remains_sha_exact_ignored_untracked_and_unstaged() -> None:
    archive_relative = "data/datasets/112年多維度SHP成果_0502.zip"
    archive = ROOT / archive_relative
    assert archive.is_file()
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == PRIVATE_ARCHIVE_SHA256
    assert _git("check-ignore", archive_relative)
    assert _git("ls-files", archive_relative) == ""
    assert _git("diff", "--cached", "--name-only", "--", archive_relative) == ""


def test_aggregate_terminal_counts_and_recommendation_are_exact() -> None:
    matrix = _load(MATRIX_PATH)
    assert matrix["verdict"] == "PASS — CROSS-DOMAIN CONTRACT CONFORMANCE VERIFIED"
    assert matrix["aggregate_result"] == {
        "domains_evaluated": 3,
        "domains_conforming": 3,
        "mandatory_invariants_nonconforming": 0,
        "unresolved_mandatory_evidence": 0,
        "mutation_bypasses": 0,
    }
    assert matrix["frozen_compatibility"]["generic_contract_changes"] == 0
    assert matrix["frozen_compatibility"]["frozen_production_changes"] == 0
    assert matrix["frozen_compatibility"]["required_frozen_refactors"] == 0
    assert matrix["next_gate_recommendation"] == "READY FOR GENERALIZATION FREEZE"

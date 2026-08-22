from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from jsonschema import Draft202012Validator

from nma.core import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data/specifications/nma-generalization-final-freeze-manifest-v1.0.json"
GEN00_SHA = "b745a98f8d465259a2cb7c2b3af3df112a10ea37"
GEN01_SHA = "7bb83f05480f642da23e7a2b244b38c3804d5fb7"
GEN02_SHA = "cca6fe925e517d39a9c82df7d02cc458137b2f37"
GEN00_AUDIT_SHA256 = "2e96f00ada42e22c7dc50387cb1fbf651b6fcbbdff94af796c0fd1985ffe86e3"
GEN01_CLOSURE_SHA256 = "03b80441bbf317ac2e2b6cd92c3a86309c4cc7465109a3d34b6d24636491c35d"
PRIVATE_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
ALLOWED_FINAL_FILES = {
    "GEN-FINAL-Completion-Report.md",
    "data/specifications/nma-generalization-final-freeze-manifest-v1.0.json",
    "tests/test_generalization_architecture_freeze_final.py",
}
READ_ONLY_GIT_COMMANDS = {
    "cat-file",
    "check-ignore",
    "diff",
    "diff-tree",
    "merge-base",
    "rev-parse",
    "status",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*arguments: str, check: bool = True) -> str:
    assert arguments and arguments[0] in READ_ONLY_GIT_COMMANDS
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=check,
    )
    return result.stdout.strip()


def _canonical_self_hash(path: Path, field: str) -> str:
    value = _load(path)
    supplied = value.pop(field)
    assert supplied == canonical_sha256(value)
    return supplied


def _candidate_or_committed_change_scope() -> set[str]:
    head = _git("rev-parse", "HEAD")
    if head != GEN02_SHA:
        return set(_git("diff", "--name-only", f"{GEN02_SHA}..HEAD").splitlines())

    changed: set[str] = set()
    for line in _git("status", "--porcelain=v1").splitlines():
        if not line:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed.add(path)
    return changed


def test_manifest_is_closed_canonical_and_tamper_evident() -> None:
    manifest = _load(MANIFEST_PATH)
    assert set(manifest) == {
        "contract",
        "version",
        "status",
        "canonical_manifest_sha256",
        "repository",
        "generalization_chain",
        "frozen_domain_identities",
        "architecture_claims",
        "generic_contract_identities",
        "frozen_generalization_artifacts",
        "aggregate_conformance",
        "integrity_test",
        "production_integrity",
        "private_archive",
        "fresh_checkout_reproduction",
        "post_freeze_policy",
    }
    basis = deepcopy(manifest)
    supplied = basis.pop("canonical_manifest_sha256")
    assert supplied == canonical_sha256(basis)
    changed = deepcopy(basis)
    changed["architecture_claims"]["mutation_safety"] = False
    assert canonical_sha256(changed) != supplied
    assert manifest["contract"] == "nma.generalization-final-freeze/1.0"
    assert manifest["version"] == "1.0"
    assert manifest["status"] == (
        "release-candidate; external publication and reproduction verification required"
    )


def test_exact_generalization_chain_and_direct_predecessor_linkage() -> None:
    assert _git("rev-parse", f"{GEN01_SHA}^") == GEN00_SHA
    assert _git("rev-parse", f"{GEN02_SHA}^") == GEN01_SHA
    assert _git("merge-base", GEN00_SHA, GEN02_SHA) == GEN00_SHA
    head = _git("rev-parse", "HEAD")
    if head != GEN02_SHA:
        assert _git("rev-parse", "HEAD^") == GEN02_SHA

    manifest = _load(MANIFEST_PATH)
    chain = manifest["generalization_chain"]
    assert chain["gen00"]["commit_sha"] == GEN00_SHA
    assert chain["gen01"]["commit_sha"] == GEN01_SHA
    assert chain["gen02"]["commit_sha"] == GEN02_SHA
    assert chain["gen00"]["audit_sha256"] == GEN00_AUDIT_SHA256
    assert chain["gen01"]["closure_sha256"] == GEN01_CLOSURE_SHA256


def test_all_normative_generalization_artifacts_are_byte_exact_and_unmodified() -> None:
    manifest = _load(MANIFEST_PATH)
    artifacts = manifest["frozen_generalization_artifacts"]
    assert len(artifacts) == 18
    assert {entry["stage"] for entry in artifacts} == {"GEN-00", "GEN-01", "GEN-02"}
    for entry in artifacts:
        path = entry["path"]
        assert _file_sha256(ROOT / path) == entry["file_sha256"], path
        introduced_blob = _git("rev-parse", f"{entry['introduced_at']}:{path}")
        current_blob = _git("rev-parse", f"HEAD:{path}")
        assert current_blob == introduced_blob, path


def test_gen00_and_gen01_canonical_identities_reproduce_exactly() -> None:
    audit_path = (
        ROOT / "data/specifications/nma-gen-00-feature-production-generalization-audit-v1.0.json"
    )
    closure_path = (
        ROOT / "data/specifications/nma-gen-01-generic-contract-interface-closure-v1.0.json"
    )
    assert _canonical_self_hash(audit_path, "audit_sha256") == GEN00_AUDIT_SHA256
    assert _canonical_self_hash(closure_path, "closure_sha256") == GEN01_CLOSURE_SHA256


def test_gen02_three_of_three_conformance_and_identities_reproduce() -> None:
    manifest = _load(MANIFEST_PATH)
    aggregate = manifest["aggregate_conformance"]
    matrix_path = ROOT / aggregate["path"]
    assert _file_sha256(matrix_path) == aggregate["file_sha256"]
    assert _canonical_self_hash(matrix_path, "matrix_sha256") == aggregate["matrix_sha256"]

    matrix = _load(matrix_path)
    assert matrix["verdict"] == "PASS — CROSS-DOMAIN CONTRACT CONFORMANCE VERIFIED"
    assert matrix["aggregate_result"] == {
        "domains_evaluated": 3,
        "domains_conforming": 3,
        "mandatory_invariants_nonconforming": 0,
        "unresolved_mandatory_evidence": 0,
        "mutation_bypasses": 0,
    }
    expected_records = {
        "school-hero": "685dd08ed34ce7fbe3506c0d54e320b28592443ce371c2f0f93499e86c8d67b5",
        "road": "6b9f3c1511cb6ff9dfc3f1f731a4d315360a83f2fb8490302fe805efd7bd9288",
        "build": "d780bd83706749b37dbfcb0ae5d9d06ac1626827bc20cbc0c6226bf314ddd97a",
    }
    for domain, expected in expected_records.items():
        record = ROOT / f"data/specifications/nma-gen-02-{domain}-contract-conformance-v1.0.json"
        assert _canonical_self_hash(record, "record_sha256") == expected


def test_all_generalization_schemas_and_instances_validate() -> None:
    pairs = [
        (
            "schemas/feature-production-generalization-audit-v1.0.schema.json",
            ["data/specifications/nma-gen-00-feature-production-generalization-audit-v1.0.json"],
        ),
        (
            "schemas/generic-contract-interface-closure-v1.0.schema.json",
            ["data/specifications/nma-gen-01-generic-contract-interface-closure-v1.0.json"],
        ),
        (
            "schemas/domain-contract-conformance-v1.0.schema.json",
            [
                "data/specifications/nma-gen-02-school-hero-contract-conformance-v1.0.json",
                "data/specifications/nma-gen-02-road-contract-conformance-v1.0.json",
                "data/specifications/nma-gen-02-build-contract-conformance-v1.0.json",
            ],
        ),
        (
            "schemas/cross-domain-contract-conformance-matrix-v1.0.schema.json",
            ["data/specifications/nma-gen-02-cross-domain-contract-conformance-matrix-v1.0.json"],
        ),
    ]
    metaschemas = {
        entry["path"]
        for entry in _load(MANIFEST_PATH)["frozen_generalization_artifacts"]
        if entry["role"] in {"closed_schema", "generic_contract_schema"}
    }
    for relative_path in metaschemas:
        schema = _load(ROOT / relative_path)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False
    for schema_path, instance_paths in pairs:
        validator = Draft202012Validator(_load(ROOT / schema_path))
        for instance_path in instance_paths:
            validator.validate(_load(ROOT / instance_path))


def test_frozen_domain_identities_are_exact() -> None:
    manifest = _load(MANIFEST_PATH)
    frozen = manifest["frozen_domain_identities"]
    expected = {
        "core": "5eb138ae7686502431587743ebce9ddf92c5a799",
        "school_hero": "56f99eb9ae63272a68accac3041fb10eacefb986",
        "road": "325c70d5335f57c43a8af85822db25032aa225c3",
        "build": "95de5fa3657a2c8ac7847f1ee1010c48ea984cd7",
    }
    assert {name: value["commit_sha"] for name, value in frozen.items()} == expected
    for name in ("core", "road", "build"):
        tag = frozen[name]["annotated_tag"]
        assert _git("cat-file", "-t", f"refs/tags/{tag}") == "tag"
        assert _git("rev-parse", f"refs/tags/{tag}^{{}}") == expected[name]
    school_ref = frozen["school_hero"]["canonical_remote_branch"]
    assert _git("rev-parse", f"refs/remotes/origin/{school_ref}") == expected["school_hero"]


def test_contract_immutability_and_exact_evidence_only_scope() -> None:
    manifest = _load(MANIFEST_PATH)
    generic_paths = set(manifest["generic_contract_identities"]["immutable_paths"])
    assert len(generic_paths) == 4
    for path in generic_paths:
        assert _git("rev-parse", f"{GEN01_SHA}:{path}") == _git("rev-parse", f"HEAD:{path}")
    assert _candidate_or_committed_change_scope() == ALLOWED_FINAL_FILES
    assert all(
        not path.startswith(("src/", "build_contracts/", "schemas/"))
        for path in ALLOWED_FINAL_FILES
    )


def test_mutation_safety_is_declarative_and_has_no_write_capability() -> None:
    manifest = _load(MANIFEST_PATH)
    integrity = manifest["production_integrity"]
    assert integrity["production_source_change_count"] == 0
    assert integrity["frozen_implementation_change_count"] == 0
    assert integrity["existing_generalization_artifact_modification_count"] == 0
    assert all(value is False for value in integrity["mutation_boundary"].values())

    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls = {
        "chmod",
        "mkdir",
        "remove",
        "rename",
        "replace",
        "rmdir",
        "unlink",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_calls
    assert READ_ONLY_GIT_COMMANDS.isdisjoint({"add", "commit", "push", "tag"})


def test_integrity_test_identity_and_private_archive_policy() -> None:
    manifest = _load(MANIFEST_PATH)
    integrity_test = manifest["integrity_test"]
    assert _file_sha256(ROOT / integrity_test["path"]) == integrity_test["file_sha256"]

    archive = ROOT / manifest["private_archive"]["path"]
    if archive.exists():
        assert _file_sha256(archive) == PRIVATE_ARCHIVE_SHA256
        assert _git("check-ignore", "--", archive.relative_to(ROOT).as_posix())
        tracked = _git(
            "cat-file", "-e", f"HEAD:{archive.relative_to(ROOT).as_posix()}", check=False
        )
        assert tracked == ""
    else:
        assert manifest["private_archive"]["fresh_checkout_required"] is False
        assert manifest["fresh_checkout_reproduction"]["private_archive_copied"] is False

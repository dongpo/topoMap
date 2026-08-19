from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import nma.core as core
import nma.entity_resolution_v10 as entity_v10
import nma.entity_resolution_v101 as entity_v101
import nma.entity_resolution_v103 as entity_v103
import nma.entity_resolution_v105 as entity_v105
import nma.entity_resolution_v107 as entity_v107
import nma.entity_resolution_v108 as entity_v108
import nma.neo4j_retrieval_v028 as neo4j_retrieval
import nma.neo4j_roundtrip_v027 as neo4j_roundtrip
import nma.road_approval as road_approval
import nma.road_authorization_consumption as road_consumption
import nma.road_execution as road_execution
import nma.road_portrayal_decision as road_decision
import nma.road_resolution as road_resolution
import nma.road_verification as road_verification
import nma.runtime_graph_backend_v029 as runtime_graph
import nma.school_hero_execution as school_execution
import nma.school_hero_verification as school_verification


ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = "c661e7b06aa6810362c62809afdfd5345a2e1689"
CORE_BASELINE = "nma-core-v0.1-baseline"
ROAD_FINAL = "325c70d5335f57c43a8af85822db25032aa225c3"
AUTHORIZED_PRODUCTION = {
    "scripts/run_nma_runtime_graph_backend_v029.py",
    "src/nma/entity_resolution_v10.py",
    "src/nma/neo4j_retrieval_v028.py",
}
GENERIC_PROVIDER_NAMES = {
    "canonical_sha256",
    "_canonical_sha256",
    "_sha256",
}
SERIALIZATION_ONLY_HELPERS = {
    ("src/nma/neo4j_retrieval_v028.py", "_canonical_json"),
    ("src/nma/neo4j_roundtrip_v027.py", "_canonical_json"),
    ("src/nma/road_execution.py", "canonical_json"),
    ("src/nma/runtime_graph_backend_v029.py", "_canonical_json"),
}
DOMAIN_JSON_HASH_RULES = {
    ("scripts/run_nma_agent_server.py", "PortrayalProposalStore.create"),
    ("scripts/run_nma_agent_server.py", "QAProposalStore.create"),
    ("scripts/run_nma_agent_server.py", "RealLayerProposalStore.create"),
    ("src/nma/neo4j_projection.py", "relationship_rows_by_type"),
    ("src/nma/neo4j_roundtrip_v027.py", "_rows_sha256"),
    ("src/nma/qa_review.py", "_plan_id"),
    ("src/nma/qa_review.py", "real_diagnosis_qa_plan"),
    ("src/nma/real_layer.py", "_plan_id"),
    ("src/nma/road_authorization_consumption.py", "authorization_consumption_file_sha256"),
    ("src/nma/road_verification.py", "_canonical_file_sha256"),
}


@dataclass(frozen=True, order=True)
class AuditHit:
    path: str
    line: int
    owner: str
    kind: str
    evidence: str


def _git(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], cwd=ROOT, text=True)


def _git_bytes(reference: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{reference}:{path}"], cwd=ROOT)


def _tracked_python_paths() -> tuple[str, ...]:
    paths = _git("ls-files", "*.py").splitlines()
    return tuple(
        sorted(path for path in paths if path.startswith(("src/nma/", "scripts/", "tests/")))
    )


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _owner(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    names = (
        [node.name]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        else []
    )
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(current.name)
    return ".".join(reversed(names)) if names else "<module>"


def _discover_candidates() -> tuple[AuditHit, ...]:
    hits: list[AuditHit] = []
    for relative_path in _tracked_python_paths():
        tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
        parents = {
            child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = sorted(
                    alias.name
                    for alias in node.names
                    if alias.name in {"canonical_json", "canonical_sha256"}
                )
                if names:
                    hits.append(
                        AuditHit(
                            relative_path,
                            node.lineno,
                            _owner(node, parents),
                            "canonical-import",
                            f"{node.module}:{','.join(names)}",
                        )
                    )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                "canonical" in node.name or "sha256" in node.name
            ):
                hits.append(
                    AuditHit(
                        relative_path,
                        node.lineno,
                        _owner(node, parents),
                        "identity-definition",
                        node.name,
                    )
                )
            elif isinstance(node, ast.Call) and _call_name(node.func) == "hashlib.sha256":
                evidence = ast.unparse(node.args[0]) if node.args else "streaming-digest"
                hits.append(
                    AuditHit(
                        relative_path,
                        node.lineno,
                        _owner(node, parents),
                        "sha256-call",
                        evidence,
                    )
                )
            elif isinstance(node, ast.Call) and _call_name(node.func) == "json.dumps":
                keywords = {keyword.arg: ast.unparse(keyword.value) for keyword in node.keywords}
                if keywords.get("sort_keys") == "True" or "separators" in keywords:
                    hits.append(
                        AuditHit(
                            relative_path,
                            node.lineno,
                            _owner(node, parents),
                            "deterministic-json",
                            repr(sorted(keywords.items())),
                        )
                    )
    return tuple(sorted(hits))


def _source(relative_path: str, reference: str | None = None) -> str:
    if reference is None:
        return (ROOT / relative_path).read_text(encoding="utf-8")
    return _git_bytes(reference, relative_path).decode("utf-8")


def _generic_provider_definitions(reference: str | None = None) -> set[tuple[str, str]]:
    providers: set[tuple[str, str]] = set()
    for relative_path in _tracked_python_paths():
        if relative_path == "src/nma/core/identity.py" or not relative_path.startswith(
            ("src/nma/", "scripts/")
        ):
            continue
        source = _source(relative_path, reference)
        tree = ast.parse(source)
        helper_names = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and "canonical_json" in node.name
        }
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name not in GENERIC_PROVIDER_NAMES:
                continue
            calls = {_call_name(call.func) for call in ast.walk(node) if isinstance(call, ast.Call)}
            if "hashlib.sha256" in calls and ("json.dumps" in calls or calls & helper_names):
                providers.add((relative_path, node.name))
    return providers


def _core_fallback_count(reference: str | None = None) -> int:
    count = 0
    for relative_path in _tracked_python_paths():
        if not relative_path.startswith(("src/nma/", "scripts/")):
            continue
        source = _source(relative_path, reference)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            imports_core = any(
                isinstance(item, ast.ImportFrom)
                and item.module is not None
                and item.module.startswith("nma.core")
                for statement in node.body
                for item in ast.walk(statement)
            )
            catches_import = any(
                handler.type is not None
                and {
                    name
                    for name in (
                        [_call_name(handler.type)]
                        if not isinstance(handler.type, ast.Tuple)
                        else [_call_name(item) for item in handler.type.elts]
                    )
                }
                & {"ImportError", "ModuleNotFoundError"}
                for handler in node.handlers
            )
            count += int(imports_core and catches_import)
        count += source.count('find_spec("nma.core")')
        count += source.count("find_spec('nma.core')")
    return count


def _json_hash_rules() -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for relative_path in _tracked_python_paths():
        if relative_path == "src/nma/core/identity.py" or not relative_path.startswith(
            ("src/nma/", "scripts/")
        ):
            continue
        tree = ast.parse(_source(relative_path))
        parents = {
            child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            calls = {_call_name(call.func) for call in ast.walk(node) if isinstance(call, ast.Call)}
            has_json = "json.dumps" in calls or any(
                name.endswith("canonical_json") for name in calls
            )
            if "hashlib.sha256" in calls and has_json:
                found.add((relative_path, _owner(node, parents)))
    return found


def _load_runtime_script() -> Any:
    path = ROOT / "scripts/run_nma_runtime_graph_backend_v029.py"
    spec = importlib.util.spec_from_file_location("core04_runtime_graph_script", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _file_manifest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_repository_wide_candidate_discovery_is_deterministic_and_complete() -> None:
    first = _discover_candidates()
    second = _discover_candidates()

    assert first == second
    assert len(first) >= 100
    audited_paths = set(_tracked_python_paths())
    assert {
        "scripts/run_nma_agent_server.py",
        "src/nma/api.py",
        "src/nma/intent_planning_v05.py",
        "src/nma/qa_review.py",
        "src/nma/road_authorization_consumption.py",
        "src/nma/road_execution.py",
        "src/nma/road_verification.py",
        "src/nma/school_hero_execution.py",
        "src/nma/school_hero_verification.py",
        "tests/hero04_support.py",
    } <= audited_paths
    discovered_paths = {hit.path for hit in first}
    assert {
        "scripts/run_nma_agent_server.py",
        "scripts/run_nma_runtime_graph_backend_v029.py",
        "src/nma/core/identity.py",
        "src/nma/entity_resolution_v10.py",
        "src/nma/neo4j_projection.py",
        "src/nma/neo4j_retrieval_v028.py",
        "src/nma/neo4j_roundtrip_v027.py",
        "src/nma/qa_review.py",
        "src/nma/real_layer.py",
        "src/nma/road_execution.py",
        "src/nma/road_verification.py",
        "src/nma/school_hero_execution.py",
        "src/nma/school_hero_verification.py",
    } <= discovered_paths


def test_residual_provider_and_fallback_counts_close_exactly() -> None:
    assert _generic_provider_definitions(PREDECESSOR) == {
        ("scripts/run_nma_runtime_graph_backend_v029.py", "canonical_sha256"),
        ("src/nma/entity_resolution_v10.py", "_canonical_sha256"),
        ("src/nma/neo4j_retrieval_v028.py", "_sha256"),
    }
    assert _generic_provider_definitions() == set()
    assert _core_fallback_count(PREDECESSOR) == 0
    assert _core_fallback_count() == 0


def test_all_generic_provider_boundaries_resolve_to_exact_core_function() -> None:
    script = _load_runtime_script()
    assert road_resolution.canonical_json is core.canonical_json
    assert road_resolution.canonical_sha256 is core.canonical_sha256
    assert school_execution.canonical_json is core.canonical_json
    assert school_execution.canonical_sha256 is core.canonical_sha256
    assert school_verification.canonical_json is core.canonical_json
    assert school_verification.canonical_sha256 is core.canonical_sha256
    assert entity_v10._canonical_sha256 is core.canonical_sha256
    assert neo4j_retrieval._sha256 is core.canonical_sha256
    assert script.canonical_sha256 is core.canonical_sha256
    for module in (entity_v101, entity_v103, entity_v105, entity_v107, entity_v108):
        assert module._canonical_sha256 is core.canonical_sha256


def test_road_and_school_transitive_adoption_remains_exact() -> None:
    for provider in (
        road_decision.canonical_sha256,
        road_approval.canonical_sha256,
        road_execution.canonical_sha256,
        road_verification.canonical_sha256,
        road_consumption.canonical_sha256,
    ):
        assert provider is core.canonical_sha256
    assert school_execution.canonical_sha256 is core.canonical_sha256
    assert school_verification.canonical_sha256 is core.canonical_sha256


def test_remaining_json_hash_rules_are_domain_specific_and_fully_classified() -> None:
    assert _json_hash_rules() == DOMAIN_JSON_HASH_RULES
    definitions = {
        (hit.path, hit.evidence)
        for hit in _discover_candidates()
        if hit.kind == "identity-definition"
    }
    assert SERIALIZATION_ONLY_HELPERS <= definitions


def test_domain_authorization_and_record_self_hash_rules_remain_exact() -> None:
    school_authorization = {
        "schema": "nma.symbol-edit-authorization/1.0",
        "authorization_hash": "f" * 64,
        "proposal": {"id": "學校", "operations": ["blue", "scale"]},
    }
    school_basis = {
        key: value for key, value in school_authorization.items() if key != "authorization_hash"
    }
    assert school_execution.authorization_sha256(school_authorization) == core.canonical_sha256(
        school_basis
    )

    road_value = {"schema_version": "road", "approval_sha256": "f" * 64, "binding": [1, 2]}
    road_basis = {key: value for key, value in road_value.items() if key != "approval_sha256"}
    assert road_approval.approval_sha256(road_value) == core.canonical_sha256(road_basis)

    source = {"schema": "domain-record", "payload": {"school": "國小", "active": True}}
    assert school_execution._hash_record(source, "record_sha256") == {
        **source,
        "record_sha256": core.canonical_sha256(source),
    }
    assert road_execution._hash_record(source, "record_sha256") == {
        **source,
        "record_sha256": core.canonical_sha256(source),
    }


def test_canonical_unicode_nested_list_boolean_null_and_numeric_behavior_is_exact() -> None:
    payload = {
        "unicode": "國家地圖學校",
        "nested": {"z": [True, False, None], "a": {"integer": 7, "float": 2.5}},
        "list": [3, {"b": 2, "a": 1}],
    }
    expected = (
        b'{"list":[3,{"a":1,"b":2}],"nested":{"a":{"float":2.5,"integer":7},'
        b'"z":[true,false,null]},"unicode":"\xe5\x9c\x8b\xe5\xae\xb6\xe5\x9c\xb0\xe5\x9c\x96'
        b'\xe5\xad\xb8\xe6\xa0\xa1"}'
    )

    assert core.canonical_json(payload) == expected
    assert core.canonical_sha256(payload) == hashlib.sha256(expected).hexdigest()
    assert entity_v10._canonical_sha256(payload) == core.canonical_sha256(payload)
    assert neo4j_retrieval._sha256(payload) == core.canonical_sha256(payload)
    assert road_execution.canonical_json(payload) == expected
    assert neo4j_retrieval._canonical_json(payload).encode("utf-8") == expected
    assert neo4j_roundtrip._canonical_json(payload).encode("utf-8") == expected
    assert runtime_graph._canonical_json(payload).encode("utf-8") == expected
    assert core.canonical_sha256({"items": [1, 2]}) != core.canonical_sha256({"items": [2, 1]})


def test_missing_core_fails_closed_without_mutation_or_repair(tmp_path: Path) -> None:
    checkout = tmp_path / "missing-core-checkout"
    selected = (
        "src/nma/__init__.py",
        "src/nma/entity_resolution_v10.py",
        "src/nma/neo4j_retrieval_v028.py",
        "scripts/run_nma_runtime_graph_backend_v029.py",
    )
    for relative_path in selected:
        destination = checkout / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative_path, destination)

    before = _file_manifest(checkout)
    environment = {
        **os.environ,
        "PYTHONPATH": str(checkout / "src"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    commands = (
        [sys.executable, "-c", "import nma.entity_resolution_v10"],
        [sys.executable, "-c", "import nma.neo4j_retrieval_v028"],
        [
            sys.executable,
            "-c",
            "import runpy; runpy.run_path('scripts/run_nma_runtime_graph_backend_v029.py')",
        ],
    )
    for command in commands:
        result = subprocess.run(
            command,
            cwd=checkout,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "ModuleNotFoundError: No module named 'nma.core'" in result.stderr

    assert _file_manifest(checkout) == before
    assert not (checkout / "src/nma/core").exists()


def test_core_source_is_byte_identical_to_immutable_baseline() -> None:
    paths = _git("ls-tree", "-r", "--name-only", CORE_BASELINE, "src/nma/core").splitlines()
    assert paths == [
        "src/nma/core/__init__.py",
        "src/nma/core/feature_profile.py",
        "src/nma/core/identity.py",
    ]
    for relative_path in paths:
        assert (ROOT / relative_path).read_bytes() == _git_bytes(CORE_BASELINE, relative_path)


def test_every_unauthorized_predecessor_file_and_frozen_ref_is_unchanged() -> None:
    predecessor_paths = _git("ls-tree", "-r", "--name-only", PREDECESSOR).splitlines()
    for relative_path in predecessor_paths:
        if relative_path not in AUTHORIZED_PRODUCTION:
            assert (ROOT / relative_path).read_bytes() == _git_bytes(PREDECESSOR, relative_path)

    assert _git("rev-list", "-n", "1", "nma-core-v0.1-baseline").strip() == (
        "ce6e90c993cb36782da29d7e24369882eb303476"
    )
    assert _git("rev-list", "-n", "1", "nma-road-v1.0-final").strip() == ROAD_FINAL
    assert _git("rev-parse", "freeze/road-final-325c70d").strip() == ROAD_FINAL
    assert _git("rev-parse", "origin/freeze/road-final-325c70d").strip() == ROAD_FINAL
    assert _git("rev-parse", "origin/freeze/hero-final-school-hero").strip() == (
        "75f80d389fe48b6dc33912e45433dc1d7e7b98b5"
    )
    assert _git("rev-parse", "origin/freeze/hero-final-school-hero-56f99eb").strip() == (
        "56f99eb9ae63272a68accac3041fb10eacefb986"
    )


def test_change_scope_is_exactly_three_existing_production_files() -> None:
    changed = set(_git("diff", "--name-only", PREDECESSOR).splitlines())
    untracked = set(_git("ls-files", "--others", "--exclude-standard").splitlines())

    assert changed == AUTHORIZED_PRODUCTION | {
        "CORE-04-Completion-Report.md",
        "tests/test_core04_residual_identity_audit.py",
    }
    assert untracked == set()


def test_private_archive_remains_exact_ignored_untracked_and_unstaged_if_present() -> None:
    relative_path = "data/datasets/112年多維度SHP成果_0502.zip"
    archive = ROOT / relative_path
    if not archive.exists():
        return

    assert hashlib.sha256(archive.read_bytes()).hexdigest() == (
        "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
    )
    assert (
        subprocess.run(
            ["git", "check-ignore", "--quiet", relative_path], cwd=ROOT, check=False
        ).returncode
        == 0
    )
    assert relative_path not in _git("ls-files").splitlines()
    assert relative_path not in _git("diff", "--name-only").splitlines()
    assert relative_path not in _git("diff", "--cached", "--name-only").splitlines()

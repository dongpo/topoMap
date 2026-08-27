from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import pytest

from hero04_support import make_authorization, make_engine
import nma.core as core
import nma.school_hero_execution as execution
import nma.school_hero_verification as verification


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "a0cd39b89fa36d072605916559c54c133db8279f"
PRODUCTION_PATHS = (
    "src/nma/school_hero_execution.py",
    "src/nma/school_hero_verification.py",
)
CORE_PATHS = (
    "src/nma/core/__init__.py",
    "src/nma/core/identity.py",
    "src/nma/core/feature_profile.py",
)


def _fixture_artifacts(tmp_path: Path) -> tuple[dict[str, Any], ...]:
    authorization = make_authorization()
    engine = make_engine(tmp_path / "runtime")
    execution_id = "exec-fixture"
    plan = engine.build_plan(authorization, execution_id)
    asset = {
        "values": {
            "color": "#1565c0",
            "opacity": 1.0,
            "scale": 1.0,
            "rotation": 0.0,
        },
        "asset_sha256": "1" * 64,
        "approved_operations_sha256": authorization["human_approval"]["approved_operations_sha256"],
    }
    bundle = engine._build_bundle(execution_id, plan, asset)
    receipt = engine._build_receipt(
        authorization,
        execution_id,
        plan,
        {"output_sha256": "2" * 64, "feature_count": 15},
        asset,
        bundle,
    )
    return authorization, plan, bundle, receipt


def _file_manifest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_school_hero_canonical_serialization_is_core_behavior() -> None:
    payload = {
        "unicode": "學校",
        "nested": {"z": [True, False, None], "a": {"integer": 7, "float": 2.5}},
        "array": [3, {"b": 2, "a": 1}],
    }
    expected = (
        b'{"array":[3,{"a":1,"b":2}],"nested":{"a":{"float":2.5,"integer":7},'
        b'"z":[true,false,null]},"unicode":"\xe5\xad\xb8\xe6\xa0\xa1"}'
    )

    assert execution.canonical_json is core.canonical_json
    assert execution.canonical_json(payload) == core.canonical_json(payload) == expected


def test_school_hero_generic_object_hashing_is_core_behavior() -> None:
    payload = {"b": [2, {"school": "小學"}], "a": 1}

    assert execution.canonical_sha256 is core.canonical_sha256
    assert verification.canonical_sha256 is core.canonical_sha256
    assert execution.canonical_sha256(payload) == core.canonical_sha256(payload)
    assert verification.canonical_sha256(payload) == core.canonical_sha256(payload)


def test_authorization_domain_rule_delegates_and_identity_is_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authorization = make_authorization()
    assert authorization["authorization_hash"] == (
        "432c356180843ec27304d7a5b09dbc990c325e90ed67a9e4dcad159f66678d9d"
    )

    observed: list[dict[str, Any]] = []

    def provider(value: Any) -> str:
        observed.append(value)
        return "provider-result"

    monkeypatch.setattr(execution, "canonical_sha256", provider)
    assert execution.authorization_sha256(authorization) == "provider-result"
    assert len(observed) == 1
    assert "authorization_hash" not in observed[0]
    assert authorization["authorization_hash"] != "provider-result"


def test_plan_hash_is_exact(tmp_path: Path) -> None:
    _, plan, _, _ = _fixture_artifacts(tmp_path)

    assert plan["plan_sha256"] == (
        "67ddf457add7fb782d3c958daf28f8b771454ea81c03be0bddd12b68f1ba9874"
    )
    assert plan["plan_sha256"] == core.canonical_sha256(
        {key: value for key, value in plan.items() if key != "plan_sha256"}
    )


def test_bundle_hash_is_exact(tmp_path: Path) -> None:
    _, _, bundle, _ = _fixture_artifacts(tmp_path)

    assert bundle["bundle_sha256"] == (
        "9b67f8383d2c7a9624561c59cb0a24e320746aa4ffcd13022189776c6de3fab5"
    )
    assert bundle["bundle_sha256"] == core.canonical_sha256(
        {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    )


def test_receipt_hash_is_exact(tmp_path: Path) -> None:
    _, _, _, receipt = _fixture_artifacts(tmp_path)

    assert receipt["receipt_sha256"] == (
        "d2d7821376da9a3b49e88de9d86172e0ebad4ec706f326207497db62a9d97bbd"
    )
    assert receipt["receipt_sha256"] == core.canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )


def test_lineage_payload_hash_is_exact_and_verification_agrees() -> None:
    payload = {
        "text": "Change the school 9920103 derived symbol color to blue.",
        "automatic_execution": False,
    }
    record = verification.build_lineage_record("request", "request:fixture", payload)

    assert record["payload_sha256"] == (
        "bfbf8cfdc5423b66e145e0461643ed3f922dc8a73ef02952ebce6baba0502ed0"
    )
    assert record["payload_sha256"] == execution.canonical_sha256(payload)
    assert verification._record_hash_is_valid(record)


def test_record_self_hash_rule_delegates_to_core_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[dict[str, Any]] = []

    def provider(value: Any) -> str:
        observed.append(dict(value))
        return "provider-record-hash"

    monkeypatch.setattr(execution, "canonical_sha256", provider)
    source = {"schema": "school-record", "value": 3}
    record = execution._hash_record(source, "record_sha256")

    assert observed == [source]
    assert record == {**source, "record_sha256": "provider-record-hash"}
    assert source == {"schema": "school-record", "value": 3}


def test_authorized_production_has_no_duplicate_or_fallback_provider() -> None:
    for relative_path in PRODUCTION_PATHS:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        tree = ast.parse(source)
        local_definitions = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        core_imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "nma.core"
        ]

        assert "canonical_json" not in local_definitions
        assert "canonical_sha256" not in local_definitions
        assert core_imports
        assert "hashlib.sha256(canonical_json" not in source
        assert "except ImportError" not in source
        assert "except ModuleNotFoundError" not in source


def test_missing_core_fails_closed_without_mutating_checkout(tmp_path: Path) -> None:
    checkout = tmp_path / "missing-core-checkout"
    package = checkout / "src/nma"
    package.mkdir(parents=True)
    for relative_path in ("src/nma/__init__.py", *PRODUCTION_PATHS):
        destination = checkout / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative_path, destination)

    before = _file_manifest(checkout)
    environment = {
        **os.environ,
        "PYTHONPATH": str(checkout / "src"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    for module in ("nma.school_hero_execution", "nma.school_hero_verification"):
        result = subprocess.run(
            [sys.executable, "-c", f"import {module}"],
            cwd=checkout,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode != 0
        assert "ModuleNotFoundError: No module named 'nma.core'" in result.stderr

    assert _file_manifest(checkout) == before


@pytest.mark.parametrize("relative_path", CORE_PATHS)
def test_core_source_is_byte_identical_to_authorized_baseline(relative_path: str) -> None:
    baseline_bytes = subprocess.check_output(
        ["git", "show", f"{BASELINE}:{relative_path}"], cwd=ROOT
    )

    assert (ROOT / relative_path).read_bytes() == baseline_bytes

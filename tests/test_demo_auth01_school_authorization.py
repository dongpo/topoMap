from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from hero04_support import make_authorization
from scripts.issue_school_demo_authorization import (
    CONTROLLED_ARCHIVE_SHA256,
    CONTROLLED_FIXTURE_IDENTITY,
    EXECUTION_SCOPE,
    EXPECTED_LAYER_COUNTS,
    HISTORICAL_AUTHORIZATION_ID,
    ROOT,
    SCHOOL_FEATURE_CODE,
    SOURCE_LAYERS,
    SchoolDemoAuthorizationIssuanceError,
    build_school_demo_authorization,
)
from nma.real_layer import file_sha256
from nma.school_hero_execution import (
    ExecutionAuthorizationStore,
    ExecutionAuthorizationVerifier,
    SchoolHeroExecutionEngine,
    SchoolHeroExecutionError,
    authorization_sha256,
)
from nma.unified_runtime import (
    SchoolRuntimeAdapter,
    UnifiedNMARuntime,
    UnifiedRuntimeError,
)


ARTIFACT_ROOT = ROOT / "artifacts/runtime/school-hero/authorizations"
PRIVATE_ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
OFFICIAL_SYMBOL = ROOT / "assets/symbols/nlsc112v5.4/school.svg"
EXPECTED_AUTHORIZATION_ID = "authorization-school-demo-b4ecdbfc35ecaf73293ed497"
EXPECTED_AUTHORIZATION_HASH = "d5546bd1b2176a4ad287acb1c78740ce79a90db76d05739dc871267d901dac67"
HISTORICAL_AUTHORIZATION_HASH = "432c356180843ec27304d7a5b09dbc990c325e90ed67a9e4dcad159f66678d9d"


class _UnusedAdapter:
    def dispatch(self, request: dict) -> dict:  # pragma: no cover - routing must not reach this
        raise AssertionError(request)


def _artifact() -> dict:
    paths = list(ARTIFACT_ROOT.glob("authorization-school-demo-*.json"))
    assert len(paths) == 1
    return json.loads(paths[0].read_text(encoding="utf-8"))


def _rehash(value: dict) -> dict:
    value["authorization_hash"] = authorization_sha256(value)
    return value


def test_exact_controlled_fixture_and_authorization_identity() -> None:
    authorization = _artifact()
    binding = authorization["demo_binding"]
    assert binding["fixture_identity"] == CONTROLLED_FIXTURE_IDENTITY
    assert binding["source_archive_sha256"] == CONTROLLED_ARCHIVE_SHA256
    assert binding["source_layers"] == SOURCE_LAYERS
    assert binding["expected_layer_feature_counts"] == EXPECTED_LAYER_COUNTS
    assert binding["expected_feature_count"] == 15
    assert binding["source_filter"]["value"] == SCHOOL_FEATURE_CODE
    assert binding["domain"] == "school"
    assert binding["production_writeback"] is False
    assert authorization["execution_scope"] == EXECUTION_SCOPE
    assert authorization["authorization_id"] == EXPECTED_AUTHORIZATION_ID
    assert authorization["authorization_hash"] == EXPECTED_AUTHORIZATION_HASH
    assert authorization["authorization_id"] != HISTORICAL_AUTHORIZATION_ID
    assert authorization["authorization_hash"] == authorization_sha256(authorization)


def test_historical_hero03_identity_remains_unchanged() -> None:
    historical = make_authorization()
    assert historical["authorization_id"] == HISTORICAL_AUTHORIZATION_ID
    assert historical["authorization_hash"] == HISTORICAL_AUTHORIZATION_HASH
    assert historical["authorization_id"] != EXPECTED_AUTHORIZATION_ID
    assert historical["authorization_hash"] != EXPECTED_AUTHORIZATION_HASH


def test_explicit_human_approval_and_deterministic_issuance() -> None:
    with pytest.raises(SchoolDemoAuthorizationIssuanceError, match="human approval"):
        build_school_demo_authorization(human_approved=False)
    first = build_school_demo_authorization(human_approved=True)
    second = build_school_demo_authorization(human_approved=True)
    assert first == second == _artifact()
    assert first["human_approval"]["decision"] == "approved"
    assert first["human_approval"]["actor_type"] == "human"
    assert first["human_approval"]["approved_fixture_identity"] == CONTROLLED_FIXTURE_IDENTITY
    assert first["human_approval"]["production_writeback_approved"] is False
    assert ExecutionAuthorizationVerifier().verify(first) == first


def test_wrong_fixture_fails_before_execution(tmp_path: Path) -> None:
    with pytest.raises(SchoolDemoAuthorizationIssuanceError, match="not the controlled"):
        build_school_demo_authorization(human_approved=True, archive_sha256="f" * 64)
    wrong = deepcopy(_artifact())
    wrong["source_archive_sha256"] = "f" * 64
    _rehash(wrong)
    engine = SchoolHeroExecutionEngine(
        storage_root=tmp_path / "runtime",
        archive_path=PRIVATE_ARCHIVE,
        official_symbol_path=OFFICIAL_SYMBOL,
    )
    with pytest.raises(SchoolHeroExecutionError, match="archive checksum changed"):
        engine.execute(wrong, "demo-auth01-wrong-fixture")
    assert not (tmp_path / "runtime/executions").exists()


def test_wrong_target_domain_plan_tamper_and_missing_approval_are_rejected() -> None:
    verifier = ExecutionAuthorizationVerifier()
    wrong_target = deepcopy(_artifact())
    wrong_target["feature_identity"]["code"] = "9420400"
    _rehash(wrong_target)
    with pytest.raises(SchoolHeroExecutionError, match="outside HERO-04 scope"):
        verifier.verify(wrong_target)

    wrong_domain = deepcopy(_artifact())
    wrong_domain["feature_identity"]["geometry_role"] = "LineString"
    _rehash(wrong_domain)
    with pytest.raises(SchoolHeroExecutionError, match="outside HERO-04 scope"):
        verifier.verify(wrong_domain)

    wrong_plan = deepcopy(_artifact())
    wrong_plan["approved_operations"][0]["value"]["color"] = "#c62828"
    _rehash(wrong_plan)
    with pytest.raises(SchoolHeroExecutionError, match="approved operations"):
        verifier.verify(wrong_plan)

    tampered = deepcopy(_artifact())
    tampered["demo_binding"]["expected_feature_count"] = 16
    with pytest.raises(SchoolHeroExecutionError, match="authorization hash"):
        verifier.verify(tampered)

    missing_approval = deepcopy(_artifact())
    missing_approval["human_approval"]["decision"] = "pending"
    _rehash(missing_approval)
    with pytest.raises(SchoolHeroExecutionError, match="human approval"):
        verifier.verify(missing_approval)


def test_historical_impersonation_is_rejected_by_existing_store(tmp_path: Path) -> None:
    authorization = deepcopy(_artifact())
    requested_id = authorization["authorization_id"]
    authorization["authorization_id"] = HISTORICAL_AUTHORIZATION_ID
    _rehash(authorization)
    store = ExecutionAuthorizationStore(tmp_path)
    store.path_for(requested_id).write_text(json.dumps(authorization), encoding="utf-8")
    with pytest.raises(SchoolHeroExecutionError, match="stored authorization identity"):
        store.load(requested_id)


def test_overbroad_mutation_request_is_rejected_before_dispatch() -> None:
    runtime = UnifiedNMARuntime(
        {"school": _UnusedAdapter(), "road": _UnusedAdapter(), "build": _UnusedAdapter()}
    )
    with pytest.raises(UnifiedRuntimeError, match="operation is invalid"):
        runtime.dispatch(
            {
                "domain": "school",
                "request": "Production writeback for school 9920103",
                "operation": "production_writeback",
                "authorization": {
                    "authorization_id": _artifact()["authorization_id"],
                    "idempotency_key": "demo-auth01-overbroad",
                },
            }
        )


@pytest.mark.skipif(
    not PRIVATE_ARCHIVE.is_file() or not shutil.which("ogr2ogr"),
    reason="The private controlled fixture and GDAL are required for canonical execution.",
)
def test_unified_runtime_consumes_authorization_and_verifies_provenance(tmp_path: Path) -> None:
    assert file_sha256(PRIVATE_ARCHIVE) == CONTROLLED_ARCHIVE_SHA256
    storage = tmp_path / "school-hero"
    store = ExecutionAuthorizationStore(storage / "authorizations")
    authorization = _artifact()
    store.save(authorization)
    engine = SchoolHeroExecutionEngine(
        storage_root=storage,
        archive_path=PRIVATE_ARCHIVE,
        official_symbol_path=OFFICIAL_SYMBOL,
        authorization_store=store,
    )
    runtime = UnifiedNMARuntime(
        {
            "school": SchoolRuntimeAdapter(
                engine=engine,
                repository_root=ROOT,
                archive_path=PRIVATE_ARCHIVE,
                symbol_path=OFFICIAL_SYMBOL,
            ),
            "road": _UnusedAdapter(),
            "build": _UnusedAdapter(),
        }
    )
    executed = runtime.dispatch(
        {
            "domain": "school",
            "request": "Execute the approved controlled school 9920103 demo",
            "operation": "execute",
            "authorization": {
                "authorization_id": authorization["authorization_id"],
                "idempotency_key": "demo-auth01-canonical-execution",
            },
        }
    )
    assert executed["authorization"] == {
        "required": True,
        "status": "consumed",
        "identity": authorization["authorization_id"],
        "sha256": authorization["authorization_hash"],
    }
    assert executed["execution"]["status"] == "completed-verification-pending"
    assert executed["mutation"] == {
        "source_writeback": False,
        "source_repair": False,
        "silent_geometry_mutation": False,
        "portrayal_mutation_outside_domain": False,
        "automatic_build_activation": False,
        "authorization_bypass": False,
    }
    verified = runtime.dispatch(
        {
            "domain": "school",
            "request": "Verify the controlled school 9920103 demo execution",
            "operation": "verify",
            "parameters": {"execution_id": executed["execution"]["identity"]},
        }
    )
    assert verified["verification"]["status"] == "verified"
    assert verified["provenance"]["status"] == "verified"

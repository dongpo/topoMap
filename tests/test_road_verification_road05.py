from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Callable

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
import pytest

from nma.road_approval import approval_sha256, authorization_sha256
from nma.road_authorization_consumption import load_authorization_consumption_fixture
from nma.road_portrayal_decision import decision_sha256, proposal_sha256
from nma.road_resolution import canonical_json, canonical_sha256
from nma.road_verification import (
    ARCHIVE_SHA256,
    AUTHORIZATION_CONSUMPTION_FIXTURE,
    AUTHORIZATION_SHA256,
    BUNDLE_SHA256,
    CORE_ARTIFACTS,
    EXECUTION_ID,
    OBSERVATION_ID,
    PROVENANCE_SCHEMA,
    QA_SCHEMA,
    RECEIPT_SHA256,
    ROLLBACK_SHA256,
    VISUAL_EVIDENCE_SCHEMA,
    RoadExecutionVerifier,
    validate_emitted_records,
)


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
STORAGE = ROOT / "artifacts/runtime/road"
EXECUTION_ROOT = STORAGE / "executions" / EXECUTION_ID

pytestmark = pytest.mark.skipif(
    not shutil.which("ogr2ogr"), reason="GDAL/OGR is required for ROAD-05 reconstruction."
)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value) + b"\n")


def _rehash(value: dict[str, Any], field: str, *ignored: str) -> None:
    basis = deepcopy(value)
    basis.pop(field, None)
    for item in ignored:
        basis.pop(item, None)
    value[field] = canonical_sha256(basis)


def _visual_evidence(root: Path, runtime_sha256: str) -> tuple[Path, Path]:
    screenshot = root / "road-render.png"
    screenshot.write_bytes(b"ROAD-05 deterministic browser evidence fixture")
    screenshot_sha256 = hashlib.sha256(screenshot.read_bytes()).hexdigest()
    evidence = {
        "schema": VISUAL_EVIDENCE_SCHEMA,
        "execution_id": EXECUTION_ID,
        "bundle_sha256": BUNDLE_SHA256,
        "runtime_geojson_sha256": runtime_sha256,
        "rendering_mechanism": "MapLibre GL JS 4.7.0 isolated actual-candidate harness",
        "render_environment": {
            "maplibre_version": "4.7.0",
            "browser": "test-browser",
            "viewport": {"width": 1024, "height": 768},
            "device_pixel_ratio": 1,
            "camera": {"center": [121.0, 24.0], "zoom": 16, "bearing": 0, "pitch": 0},
            "font_source": "test-only",
        },
        "render_observation": {
            "map_loaded": True,
            "source_ids": [f"nma-road-source-{EXECUTION_ID}"],
            "layer_ids": [f"nma-road-label-{EXECUTION_ID}"],
            "rendered_label_texts": ["中山街"],
            "rendered_label_feature_count": 1,
            "unrelated_feature_count": 0,
            "shield_graphic_count": 0,
            "unexpected_layer_ids": [],
            "unexpected_source_ids": [],
            "screenshot_sha256": screenshot_sha256,
        },
        "oracle": {"status": "absent", "identity": None},
        "pixel_correctness_status": ("evidence_generated_but_no_independent_visual_oracle"),
    }
    evidence["evidence_sha256"] = canonical_sha256(evidence)
    path = root / "visual-evidence.json"
    _write_json(path, evidence)
    return path, screenshot


def _case(tmp_path: Path, *, repository_root: Path = ROOT) -> tuple[Path, RoadExecutionVerifier]:
    storage = tmp_path / "runtime"
    shutil.copytree(STORAGE, storage)
    runtime_path = storage / "executions" / EXECUTION_ID / "data/road-centreline-runtime.geojson"
    visual, screenshot = _visual_evidence(
        tmp_path, hashlib.sha256(runtime_path.read_bytes()).hexdigest()
    )
    verifier = RoadExecutionVerifier(
        storage_root=storage,
        archive_path=ARCHIVE,
        repository_root=repository_root,
        visual_evidence_path=visual,
        screenshot_path=screenshot,
    )
    return storage, verifier


def _checks(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in [*result["qa"]["checks"], *result["provenance"]["checks"]]}


def _json_mutation(
    tmp_path: Path,
    relative: str,
    mutation: Callable[[dict[str, Any]], None],
    *,
    hash_field: str | None = None,
    ignored: tuple[str, ...] = (),
) -> dict[str, Any]:
    storage, verifier = _case(tmp_path)
    path = storage / "executions" / EXECUTION_ID / relative
    value = json.loads(path.read_text(encoding="utf-8"))
    mutation(value)
    if hash_field is not None:
        _rehash(value, hash_field, *ignored)
    _write_json(path, value)
    return verifier.verify(persist=False)


def _schema_registry() -> tuple[dict[str, dict[str, Any]], Registry]:
    schemas = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in (ROOT / "schemas").glob("*.schema.json")
    }
    registry = Registry().with_resources(
        [(schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()]
    )
    return schemas, registry


def test_road05_independent_qa_and_provenance_pass(tmp_path: Path) -> None:
    storage, verifier = _case(tmp_path)
    result = verifier.verify()

    assert result["status"] == "verified"
    assert result["qa"]["schema"] == QA_SCHEMA
    assert result["qa"]["classification"] == "expected-change-verified"
    assert result["provenance"]["schema"] == PROVENANCE_SCHEMA
    assert result["provenance"]["lineage_completeness"] == "complete"
    assert validate_emitted_records(result["qa"], result["provenance"])
    execution = storage / "executions" / EXECUTION_ID
    assert (execution / "qa.json").is_file()
    assert (execution / "provenance.json").is_file()
    assert _checks(result)["source_geometry_exact"]["status"] == "passed"
    assert _checks(result)["runtime_derivative_exact"]["status"] == "passed"
    assert result["qa"]["visual_qa"]["independent_visual_oracle"] == "absent"


def test_road05_outputs_validate_against_closed_schemas(tmp_path: Path) -> None:
    _, verifier = _case(tmp_path)
    result = verifier.verify(persist=False)
    schemas, registry = _schema_registry()
    for name, value in [
        ("road-qa-v1.0.schema.json", result["qa"]),
        ("road-provenance-v1.0.schema.json", result["provenance"]),
    ]:
        Draft202012Validator.check_schema(schemas[name])
        Draft202012Validator(schemas[name], registry=registry).validate(value)
        assert schemas[name]["additionalProperties"] is False
    visual_schema = schemas["road-visual-evidence-v1.0.schema.json"]
    Draft202012Validator.check_schema(visual_schema)
    assert visual_schema["additionalProperties"] is False
    assert verifier.visual_evidence_path is not None
    Draft202012Validator(visual_schema, registry=registry).validate(
        json.loads(verifier.visual_evidence_path.read_text(encoding="utf-8"))
    )
    consumption_fixture_schema = schemas["road-authorization-consumption-fixture-v1.0.schema.json"]
    consumption_fixture, consumption = load_authorization_consumption_fixture(
        ROOT / "data/specifications" / AUTHORIZATION_CONSUMPTION_FIXTURE
    )
    Draft202012Validator.check_schema(consumption_fixture_schema)
    Draft202012Validator(consumption_fixture_schema, registry=registry).validate(
        consumption_fixture
    )
    assert (
        consumption["idempotency_key_sha256"]
        == "d4645499a8a897194ed49d7cd19edb6acd96bda5db0611fd82a701a875f343cb"
    )


@pytest.mark.parametrize(
    ("relative", "mutation", "hash_field", "ignored", "failed_check"),
    [
        (
            "data/road-centreline-runtime.geojson",
            lambda value: value["features"].append(deepcopy(value["features"][0])),
            None,
            (),
            "runtime_derivative_exact",
        ),
        (
            "data/road-centreline-source.geojson",
            lambda value: value["features"][0]["properties"].__setitem__("ROADSEGID", "changed"),
            None,
            (),
            "source_geometry_exact",
        ),
        (
            "data/road-centreline-source.geojson",
            lambda value: value["features"].reverse(),
            None,
            (),
            "source_geometry_exact",
        ),
        (
            "data/road-centreline-source.geojson",
            lambda value: value["features"][0]["properties"].__setitem__("TERRAINID", "9420300"),
            None,
            (),
            "source_geometry_exact",
        ),
        (
            "data/road-centreline-source.geojson",
            lambda value: value["features"][0]["properties"].__setitem__("ROADNUM", "縣125"),
            None,
            (),
            "source_geometry_exact",
        ),
        (
            "data/road-centreline-source.geojson",
            lambda value: value["features"][0]["geometry"]["coordinates"][0].__setitem__(0, 0),
            None,
            (),
            "source_geometry_exact",
        ),
        (
            "data/road-centreline-runtime.geojson",
            lambda value: value["features"][0]["geometry"]["coordinates"][0].__setitem__(0, 0),
            None,
            (),
            "runtime_derivative_exact",
        ),
        (
            "data/road-centreline-runtime.geojson",
            lambda value: value["features"][0]["geometry"]["coordinates"].append([121, 24]),
            None,
            (),
            "runtime_derivative_exact",
        ),
        (
            "plan.json",
            lambda value: value["scope"].__setitem__("class_code", "9420300"),
            "execution_plan_sha256",
            (),
            "plan_canonical_identity",
        ),
        (
            "derived-portrayal.json",
            lambda value: value["portrayal"].__setitem__("road_name_annotation", "別名"),
            "artifact_sha256",
            (),
            "derived_canonical_identity",
        ),
        (
            "authorization.json",
            lambda value: value["bindings"].__setitem__("class_code", "9420300"),
            None,
            (),
            "persisted_authorization_binding",
        ),
        (
            "bundle.json",
            lambda value: value["scope"].__setitem__("route_identity", "changed"),
            "bundle_sha256",
            (),
            "bundle_canonical_identity",
        ),
        (
            "receipt.json",
            lambda value: value["scope"].__setitem__("class_code", "9420300"),
            "receipt_sha256",
            ("completed_at",),
            "receipt_canonical_identity",
        ),
        (
            f"observations/{OBSERVATION_ID}.json",
            lambda value: value.__setitem__("observed_feature_count", 4),
            "observation_sha256",
            ("timestamp",),
            "observation_canonical_identity",
        ),
        (
            "rollback-manifest.json",
            lambda value: value["artifacts"][0].__setitem__("sha256", "0" * 64),
            "rollback_manifest_sha256",
            (),
            "rollback_canonical_identity",
        ),
        (
            "bundle.json",
            lambda value: value["layers"].append(deepcopy(value["layers"][0])),
            "bundle_sha256",
            (),
            "bundle_canonical_identity",
        ),
        (
            "bundle.json",
            lambda value: value["source"].__setitem__("id", "unexpected-source"),
            "bundle_sha256",
            (),
            "bundle_canonical_identity",
        ),
        (
            "bundle.json",
            lambda value: value["shield_binding"].update(
                {
                    "status": "resolved",
                    "resolver_identity": "guessed",
                    "resolved_artifact_sha256": "0" * 64,
                }
            ),
            "bundle_sha256",
            (),
            "shield_semantic_binding",
        ),
        (
            "bundle.json",
            lambda value: value["shield_binding"].__setitem__("shield_code", "9490004"),
            "bundle_sha256",
            (),
            "shield_semantic_binding",
        ),
        (
            "bundle.json",
            lambda value: value["layers"][0]["layout"].__setitem__(
                "text-field", ["literal", "別名"]
            ),
            "bundle_sha256",
            (),
            "label_semantic_contract",
        ),
        (
            "bundle.json",
            lambda value: value["scope"].__setitem__("graphic_element_roles", [5, 2]),
            "bundle_sha256",
            (),
            "bundle_canonical_identity",
        ),
        (
            "bundle.json",
            lambda value: value["shield_binding"].__setitem__("shield_orientation", "upright"),
            "bundle_sha256",
            (),
            "shield_semantic_binding",
        ),
        (
            "plan.json",
            lambda value: value["source"].__setitem__("layer", "K14_ROADA"),
            "execution_plan_sha256",
            (),
            "plan_canonical_identity",
        ),
    ],
)
def test_semantic_geometry_and_artifact_tampering_fails_closed(
    tmp_path: Path,
    relative: str,
    mutation: Callable[[dict[str, Any]], None],
    hash_field: str | None,
    ignored: tuple[str, ...],
    failed_check: str,
) -> None:
    result = _json_mutation(
        tmp_path,
        relative,
        mutation,
        hash_field=hash_field,
        ignored=ignored,
    )
    assert result["status"] == "failed"
    assert _checks(result)[failed_check]["status"] == "failed"


def test_unexpected_candidate_artifact_fails_closed(tmp_path: Path) -> None:
    storage, verifier = _case(tmp_path)
    path = storage / "executions" / EXECUTION_ID / "unexpected-candidate.json"
    path.write_text("{}\n", encoding="utf-8")
    result = verifier.verify(persist=False)
    assert result["qa"]["classification"] == "unexpected-additional-change"
    assert _checks(result)["exact_persisted_artifact_set"]["status"] == "failed"


def test_missing_lineage_element_fails_closed(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(ROOT / "data/specifications", repository / "data/specifications")
    shutil.copytree(ROOT / "data/extraction", repository / "data/extraction")
    missing = repository / "data/specifications/nma-road-hero-road-02-golden-proposal-v1.0.json"
    missing.unlink()
    _, verifier = _case(tmp_path / "case", repository_root=repository)
    result = verifier.verify(persist=False)
    assert result["status"] == "failed"
    assert _checks(result)["frozen_upstream_lineage"]["status"] == "failed"


def test_altered_road01_evidence_identity_fails_closed(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(ROOT / "data/specifications", repository / "data/specifications")
    shutil.copytree(ROOT / "data/extraction", repository / "data/extraction")
    path = repository / "data/extraction/v0.4/road-compound-portrayal-reviewed.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["record_set_id"] = "unauthorized-substitute"
    _write_json(path, value)
    _, verifier = _case(tmp_path / "case", repository_root=repository)
    result = verifier.verify(persist=False)
    assert result["status"] == "failed"
    assert _checks(result)["frozen_upstream_lineage"]["status"] == "failed"


@pytest.mark.parametrize("kind", ["fixture", "proposal", "decision", "approval", "authorization"])
def test_rehashed_unauthorized_frozen_substitutes_fail_closed(tmp_path: Path, kind: str) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(ROOT / "data/specifications", repository / "data/specifications")
    shutil.copytree(ROOT / "data/extraction", repository / "data/extraction")
    names = {
        "fixture": "nma-road-hero-road-01-v1.0.json",
        "proposal": "nma-road-hero-road-02-golden-proposal-v1.0.json",
        "decision": "nma-road-hero-road-02-golden-decision-v1.0.json",
        "approval": "nma-road-hero-road-03-golden-approval-v1.0.json",
        "authorization": "nma-road-hero-road-03-golden-authorization-v1.0.json",
    }
    path = repository / "data/specifications" / names[kind]
    value = json.loads(path.read_text(encoding="utf-8"))
    if kind == "fixture":
        value["road_identity"]["class_code"] = "9420300"
        value["fixture_sha256"] = canonical_sha256(
            [
                value["archive_sha256"],
                value["profile"],
                value["layer"],
                value["road_identity"]["class_code"],
                value["road_identity"]["canonical_identity"],
                [record["feature_id"] for record in value["source_records"]],
                sorted(value["evidence"]["evidence_ids"]),
            ]
        )
    else:
        value["bindings"]["class_code"] = "9420300"
        hashers = {
            "proposal": ("proposal_sha256", proposal_sha256),
            "decision": ("decision_sha256", decision_sha256),
            "approval": ("approval_sha256", approval_sha256),
            "authorization": ("authorization_sha256", authorization_sha256),
        }
        field, hasher = hashers[kind]
        value[field] = hasher(value)
    _write_json(path, value)
    _, verifier = _case(tmp_path / "case", repository_root=repository)
    result = verifier.verify(persist=False)
    assert result["status"] == "failed"
    assert _checks(result)["frozen_upstream_lineage"]["status"] == "failed"


def test_altered_archive_bytes_fail_closed(tmp_path: Path) -> None:
    storage, verifier = _case(tmp_path / "case")
    wrong_archive = tmp_path / "changed.zip"
    wrong_archive.write_bytes(ARCHIVE.read_bytes() + b"tamper")
    verifier = RoadExecutionVerifier(
        storage_root=storage,
        archive_path=wrong_archive,
        repository_root=ROOT,
        visual_evidence_path=verifier.visual_evidence_path,
        screenshot_path=verifier.screenshot_path,
    )
    result = verifier.verify(persist=False)
    assert result["status"] == "failed"
    assert result["qa"]["classification"] == "verification-blocked"
    assert _checks(result)["private_archive_identity"]["status"] == "failed"


def test_visual_evidence_and_screenshot_tampering_fail_closed(tmp_path: Path) -> None:
    _, verifier = _case(tmp_path)
    assert verifier.screenshot_path is not None
    verifier.screenshot_path.write_bytes(b"changed pixels")
    result = verifier.verify(persist=False)
    assert result["qa"]["classification"] == "verification-blocked"
    assert _checks(result)["actual_render_observation"]["status"] == "failed"


def test_altered_qa_parent_reference_fails_record_validation(tmp_path: Path) -> None:
    _, verifier = _case(tmp_path)
    result = verifier.verify(persist=False)
    provenance = deepcopy(result["provenance"])
    provenance["qa_parent"]["sha256"] = "0" * 64
    _rehash(provenance, "provenance_sha256")
    assert not validate_emitted_records(result["qa"], provenance)


def test_two_root_canonical_determinism(tmp_path: Path) -> None:
    results = []
    consumption_identities = []
    roots = [tmp_path / "first-checkout", tmp_path / "nested/second-checkout"]
    for repository in roots:
        shutil.copytree(ROOT / "data/specifications", repository / "data/specifications")
        shutil.copytree(ROOT / "data/extraction", repository / "data/extraction")
        archive = repository / "data/datasets/112年多維度SHP成果_0502.zip"
        archive.parent.mkdir(parents=True)
        shutil.copy2(ARCHIVE, archive)
        storage = repository / "artifacts/runtime/road"
        shutil.copytree(STORAGE, storage)
        _, consumption = load_authorization_consumption_fixture(
            repository / "data/specifications" / AUTHORIZATION_CONSUMPTION_FIXTURE
        )
        consumption_path = storage / "executions" / EXECUTION_ID / "consumption.json"
        ledger_path = storage / "ledger" / f"{AUTHORIZATION_SHA256}.json"
        _write_json(consumption_path, consumption)
        _write_json(ledger_path, consumption)
        consumption_identities.append(
            (
                consumption["idempotency_key_sha256"],
                hashlib.sha256(consumption_path.read_bytes()).hexdigest(),
                hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
            )
        )
        (repository / ".gitignore").write_text(
            "data/datasets/112年多維度SHP成果_0502.zip\nartifacts/runtime/road/\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q"], cwd=repository, check=True, capture_output=True)
        runtime_path = (
            storage / "executions" / EXECUTION_ID / "data/road-centreline-runtime.geojson"
        )
        visual, screenshot = _visual_evidence(
            repository, hashlib.sha256(runtime_path.read_bytes()).hexdigest()
        )
        verifier = RoadExecutionVerifier(
            storage_root=storage,
            archive_path=archive,
            repository_root=repository,
            visual_evidence_path=visual,
            screenshot_path=screenshot,
        )
        results.append(verifier.verify(persist=False))
    first, second = results
    assert first == second
    assert first["qa"]["qa_sha256"] == second["qa"]["qa_sha256"]
    assert first["provenance"]["provenance_sha256"] == second["provenance"]["provenance_sha256"]
    assert roots[0] != roots[1]
    assert (
        consumption_identities
        == [
            (
                "d4645499a8a897194ed49d7cd19edb6acd96bda5db0611fd82a701a875f343cb",
                "fb21f714f925922938198ac9299a42ea87aaab89b2860d5518a49f5467571330",
                "fb21f714f925922938198ac9299a42ea87aaab89b2860d5518a49f5467571330",
            )
        ]
        * 2
    )


def test_authoritative_identities_and_mutation_boundary(tmp_path: Path) -> None:
    archive_before = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    storage, verifier = _case(tmp_path)
    result = verifier.verify(persist=False)
    assert archive_before == ARCHIVE_SHA256 == hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    assert result["qa"]["expected_transition"]["bundle"]["sha256"] == BUNDLE_SHA256
    assert result["qa"]["expected_transition"]["receipt"]["sha256"] == RECEIPT_SHA256
    assert result["qa"]["expected_transition"]["rollback"]["sha256"] == ROLLBACK_SHA256
    actual = {
        path.relative_to(storage / "executions" / EXECUTION_ID).as_posix()
        for path in (storage / "executions" / EXECUTION_ID).rglob("*")
        if path.is_file()
    }
    assert set(CORE_ARTIFACTS).issubset(actual)


def test_cli_declares_no_road04_executor_dependency(tmp_path: Path) -> None:
    source = (ROOT / "src/nma/road_verification.py").read_text(encoding="utf-8")
    assert "from nma.road_execution" not in source
    assert "RoadExecutionEngine" not in source
    subprocess.run(
        ["python3", "scripts/verify_road_execution.py", "--help"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    completed = subprocess.run(
        ["python3", "scripts/verify_road_authorization_consumption.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    reproduced = json.loads(completed.stdout)
    assert reproduced["status"] == "verified"
    assert (
        reproduced["idempotency_key_sha256"]
        == "d4645499a8a897194ed49d7cd19edb6acd96bda5db0611fd82a701a875f343cb"
    )
    assert (
        reproduced["consumption_file_sha256"]
        == "fb21f714f925922938198ac9299a42ea87aaab89b2860d5518a49f5467571330"
    )
    clean_checkout = tmp_path / "clean-checkout"
    clean_files = [
        "scripts/verify_road_authorization_consumption.py",
        "src/nma/__init__.py",
        "src/nma/core/__init__.py",
        "src/nma/core/feature_profile.py",
        "src/nma/core/identity.py",
        "src/nma/road_authorization_consumption.py",
        "src/nma/road_resolution.py",
        f"data/specifications/{AUTHORIZATION_CONSUMPTION_FIXTURE}",
    ]
    for relative in clean_files:
        destination = clean_checkout / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    for relative in [path for path in clean_files if path.startswith("src/nma/core/")]:
        assert (clean_checkout / relative).read_bytes() == (ROOT / relative).read_bytes()
    road_resolution_source = (clean_checkout / "src/nma/road_resolution.py").read_text(
        encoding="utf-8"
    )
    assert "from nma.core import canonical_json as canonical_json" in road_resolution_source
    assert "from nma.core import canonical_sha256 as canonical_sha256" in road_resolution_source
    assert "except ImportError" not in road_resolution_source
    assert "def canonical_json" not in road_resolution_source
    assert "def canonical_sha256" not in road_resolution_source
    subprocess.run(
        [
            "python3",
            "-B",
            "-c",
            "import sys; sys.path.insert(0, 'src'); import nma.road_resolution",
        ],
        cwd=clean_checkout,
        check=True,
        capture_output=True,
        text=True,
    )
    clean_completed = subprocess.run(
        ["python3", "-B", "scripts/verify_road_authorization_consumption.py"],
        cwd=clean_checkout,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(clean_completed.stdout) == reproduced

    missing_core_checkout = tmp_path / "missing-core-checkout"
    shutil.copytree(clean_checkout, missing_core_checkout)
    shutil.rmtree(missing_core_checkout / "src/nma/core")
    before_failed_import = {
        path.relative_to(missing_core_checkout).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in missing_core_checkout.rglob("*")
        if path.is_file()
    }
    failed_import = subprocess.run(
        [
            "python3",
            "-B",
            "-c",
            "import sys; sys.path.insert(0, 'src'); import nma.road_resolution",
        ],
        cwd=missing_core_checkout,
        check=False,
        capture_output=True,
        text=True,
    )
    after_failed_import = {
        path.relative_to(missing_core_checkout).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in missing_core_checkout.rglob("*")
        if path.is_file()
    }
    assert failed_import.returncode != 0
    assert "No module named 'nma.core'" in failed_import.stderr
    assert after_failed_import == before_failed_import

    fixture_path = ROOT / "data/specifications" / AUTHORIZATION_CONSUMPTION_FIXTURE
    altered_fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    altered_fixture["inputs"]["idempotency_key"] = "road04-session-key"
    altered_path = tmp_path / "altered-consumption-fixture.json"
    _write_json(altered_path, altered_fixture)
    failed = subprocess.run(
        [
            "python3",
            "scripts/verify_road_authorization_consumption.py",
            "--fixture",
            str(altered_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert failed.returncode == 1
    assert json.loads(failed.stdout)["status"] == "failed"

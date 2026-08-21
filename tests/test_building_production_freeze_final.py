from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import subprocess

import pytest

import build_contracts.building_production_activation as activation
import build_contracts.building_production_implementation as implementation
from build_contracts.building_production_implementation import (
    BuildingProductionError,
    validate_authorized_source_path,
)
from nma.core import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data/specifications/nma-build-final-freeze-manifest-v1.0.json"
PREDECESSOR_SHA = "fe0f280f52ba374171010e76b1432b3e414ce927"
ALLOWED_FINAL_FILES = {
    "BUILD-FINAL-Completion-Report.md",
    "data/specifications/nma-build-final-freeze-manifest-v1.0.json",
    "tests/test_building_production_freeze_final.py",
}


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def manifest() -> dict:
    return _load(MANIFEST_PATH)


def test_manifest_identity_is_canonical_core_identity_and_tamper_fails(manifest: dict) -> None:
    basis = deepcopy(manifest)
    supplied = basis.pop("canonical_manifest_sha256")
    assert supplied == canonical_sha256(basis)
    changed = deepcopy(basis)
    changed["active_production_semantics"]["production_active"] = False
    assert canonical_sha256(changed) != supplied
    assert activation.canonical_sha256 is canonical_sha256
    assert implementation.canonical_sha256 is canonical_sha256
    assert "def canonical_sha256" not in inspect.getsource(activation)
    assert "def canonical_sha256" not in inspect.getsource(implementation)


def test_manifest_contract_and_release_identity_are_exact(manifest: dict) -> None:
    assert manifest["contract"] == "nma.building-final-freeze/1.0"
    assert manifest["version"] == "1.0"
    assert manifest["status"] == "PASS — BUILDING PRODUCTION BASELINE FROZEN"
    repository = manifest["repository"]
    assert repository["origin"] == "https://github.com/dongpo/topoMap.git"
    assert repository["predecessor"] == {
        "branch": "build/build-12-controlled-building-production-activation",
        "commit_sha": PREDECESSOR_SHA,
        "verdict": "PASS — BUILDING PRODUCTION ACTIVATED AND POST-ACTIVATION VERIFIED",
    }
    strategy = repository["final_identity_strategy"]
    assert strategy["freeze_branch_pattern"] == "freeze/build-final-<short-FINAL_SHA>"
    assert strategy["annotated_tag"] == "nma-build-v1.0-final"
    assert strategy["non_self_referential"] is True


def test_complete_activation_and_contract_identity_chain_is_exact(manifest: dict) -> None:
    chain = manifest["building_identity_chain"]
    assert chain["build09f_policy_sha256"] == (
        "dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1"
    )
    assert chain["finalized_contract_sha256"] == (
        "5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88"
    )
    assert chain["build10_implementation_sha256"] == (
        "2772ce93f81973e1dbbeb2d4ae9bb1307a29dcdcc4a61ca08f382c12b6b3c957"
    )
    assert chain["build11_readiness_sha256"] == (
        "d2ecb53e74f46e279a5672a182b5a9de602c08d4027023d4fb225132bf3d01fb"
    )
    assert chain["build11a_authorization_sha256"] == (
        "8bae65726aa0c6901927cb3a0a12a875ac766d45ac9e3a793afb23a85effdb0f"
    )
    build12 = chain["build12"]
    assert build12 == {
        "activation_id": "building-activation-03d28cbae50eb2050db4ed08",
        "activation_configuration_sha256": (
            "03d28cbae50eb2050db4ed0841009e81fab84b18dcb882a7e85fce49818565ad"
        ),
        "activation_record_sha256": (
            "6994abb821287aec015e846148b630054d03c826a6d370ceb625816dfa29d08d"
        ),
        "activation_receipt_sha256": (
            "d50cd21f5caa0428ae2dbd4f7fd8343b0bfc50e387dbd156b71ecb9a88739cb7"
        ),
        "activated_baseline_sha256": (
            "e9ebf1158caef22cb02d98d7ba8bfe4c99df46d4d9e93a47ad234f632a1755b2"
        ),
        "post_activation_verification": "20 / 20 PASS",
        "deactivation_reactivation_rehearsal": "PASS",
    }


def test_frozen_files_are_byte_exact(manifest: dict) -> None:
    frozen = manifest["frozen_files"]
    for group in frozen.values():
        for relative_path, expected_sha256 in group.items():
            assert _file_sha256(ROOT / relative_path) == expected_sha256, relative_path


def test_record_self_identities_recompute_with_core_provider(manifest: dict) -> None:
    records = [
        (
            "data/runtime/nma-building-production-activation-v1.0.json",
            "canonical_activation_record_sha256",
            manifest["building_identity_chain"]["build12"]["activation_record_sha256"],
        ),
        (
            "data/runtime/nma-building-production-activation-receipt-v1.0.json",
            "canonical_activation_receipt_sha256",
            manifest["building_identity_chain"]["build12"]["activation_receipt_sha256"],
        ),
        (
            "data/specifications/nma-build-12-golden-building-production-activated-baseline-v1.0.json",
            "canonical_activated_baseline_sha256",
            manifest["building_identity_chain"]["build12"]["activated_baseline_sha256"],
        ),
        (
            "data/specifications/nma-build-11a-golden-human-building-production-activation-authorization-v1.0.json",
            "canonical_authorization_sha256",
            manifest["building_identity_chain"]["build11a_authorization_sha256"],
        ),
        (
            "data/specifications/nma-build-11-golden-building-production-activation-readiness-v1.0.json",
            "canonical_record_sha256",
            manifest["building_identity_chain"]["build11_readiness_sha256"],
        ),
        (
            "data/specifications/nma-build-09f-golden-human-building-production-policy-authorization-v1.0.json",
            "policy_record_sha256",
            manifest["building_identity_chain"]["build09f_policy_sha256"],
        ),
        (
            "data/specifications/nma-build-09f-finalized-building-production-contract-v1.0.json",
            "finalized_contract_sha256",
            manifest["building_identity_chain"]["finalized_contract_sha256"],
        ),
    ]
    for relative_path, identity_field, expected_sha256 in records:
        basis = _load(ROOT / relative_path)
        supplied = basis.pop(identity_field)
        assert supplied == expected_sha256 == canonical_sha256(basis), relative_path


def test_active_j13_j17_bindings_counts_and_fail_closed_policy_are_frozen(
    manifest: dict,
) -> None:
    semantics = manifest["active_production_semantics"]
    assert semantics["production_active"] is True
    assert semantics["official_portrayal_active"] is True
    assert semantics["source_mutation_allowed"] is False
    assert semantics["source_mutated"] is False
    assert semantics["bindings"]["J13"]["package_identity"] == "J13_寶山都市計畫/SHP"
    assert semantics["bindings"]["J13"]["selected_layer"] == "J13_BUILD"
    assert [
        semantics["bindings"]["J13"][key]
        for key in (
            "source_feature_count",
            "derived_xy_feature_count",
            "annotation_count",
            "suppressed_unsafe_placement_count",
        )
    ] == [2968, 2968, 2967, 1]
    assert semantics["bindings"]["J17"]["package_identity"] == (
        "J17_新竹科學工業園區特定區計畫(寶山部分)/SHP"
    )
    assert semantics["bindings"]["J17"]["selected_layer"] == "J17_BUILD"
    assert [
        semantics["bindings"]["J17"][key]
        for key in (
            "source_feature_count",
            "derived_xy_feature_count",
            "annotation_count",
            "suppressed_unsafe_placement_count",
        )
    ] == [2839, 2839, 2838, 1]
    assert set(semantics["binding_policy"].values()) == {False, "fail-closed"}


def test_portrayal_geometry_and_activation_boundaries_are_exact(manifest: dict) -> None:
    portrayal = manifest["portrayal_profile"]
    assert portrayal["annotation"]["production_binding_order"] == "{BUILD_NO}{BUILD_STR}"
    assert portrayal["hatch"] == {
        "official_diagonal_semantics": True,
        "official_spacing_mm": 2,
        "local_production_angle_degrees": 45,
        "resource_policy": "procedural-canonical",
        "static_svg_dependency_required": False,
    }
    assert portrayal["line"] == {
        "official_width_mm": 0.2,
        "output_profile": "nma-screen-96dpi-v1",
        "dpi": 96,
        "derived_device_width_px": 0.7559055118110237,
        "one_px_equivalent": False,
    }
    assert portrayal["colour"] == {
        "official_rgb": [0, 0, 0],
        "device_serialization": "#000000",
        "opacity": 1.0,
        "legacy_111111_allowed": False,
    }
    geometry = manifest["geometry_boundary"]
    assert geometry["pipeline"] == [
        "authoritative-PolygonZ",
        "non-authoritative-non-writing-derived-XY",
        "portrayal-runtime",
    ]
    assert geometry["legacy_destructive_drop_z_production_reachable"] is False
    contract = manifest["activation_deactivation_contract"]
    assert contract["unconditional_global_activation_permission"] is False
    assert contract["failed_post_activation_verification_final_state"] == "inactive"


def test_private_archive_policy_and_absence_are_fail_closed(manifest: dict, tmp_path: Path) -> None:
    source = manifest["source_archive"]
    archive = ROOT / source["path"]
    if archive.exists():
        assert _file_sha256(archive) == source["sha256"]
        assert (
            subprocess.run(
                ["git", "check-ignore", "--quiet", str(archive)], cwd=ROOT, check=False
            ).returncode
            == 0
        )
        assert (
            subprocess.run(
                ["git", "ls-files", "--error-unmatch", str(archive)],
                cwd=ROOT,
                capture_output=True,
                check=False,
            ).returncode
            != 0
        )
    missing = tmp_path / archive.name
    with pytest.raises(BuildingProductionError) as caught:
        validate_authorized_source_path(missing, observed_sha256=source["sha256"])
    assert caught.value.code == "unauthorized_source_path"
    assert not missing.exists()


def test_no_alternate_identity_provider_or_production_reachable_drop_z(manifest: dict) -> None:
    providers = []
    for path in ROOT.rglob("*.py"):
        if any(part in {".git", ".venv", "node_modules"} for part in path.parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "canonical_sha256"
            for node in ast.walk(tree)
        ):
            providers.append(path.relative_to(ROOT).as_posix())
    assert providers == ["src/nma/core/identity.py"]
    record = _load(ROOT / "data/runtime/nma-building-production-activation-v1.0.json")
    isolation = record["drop_z_isolation"]
    assert isolation["production_reachable"] is False
    assert isolation["authoritative_source_write_target"] is None
    assert isolation["disposition"] == "bypassed-by-build10-controlled-building-path"
    assert record["activation_provenance"]["fallback_identity_provider"] is False
    assert (
        manifest["active_production_semantics"]["binding_policy"][
            "alternate_binding_provider_allowed"
        ]
        is False
    )


def test_build_final_diff_is_evidence_only(manifest: dict) -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head == PREDECESSOR_SHA:
        output = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, text=True
        )
        changed = {line[3:] for line in output.splitlines() if line}
    else:
        output = subprocess.check_output(
            ["git", "diff", "--name-only", PREDECESSOR_SHA + "..HEAD"], cwd=ROOT, text=True
        )
        changed = set(output.splitlines())
    assert changed == ALLOWED_FINAL_FILES == set(manifest["change_scope"]["allowed_files"])
    assert all(
        not path.startswith(("src/", "build_contracts/", "assets/", "data/datasets/"))
        for path in changed
    )
    assert manifest["change_scope"]["production_source_changed"] is False
    assert manifest["change_scope"]["source_data_changed"] is False
    assert manifest["change_scope"]["behavior_changed"] is False

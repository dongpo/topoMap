from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path
import subprocess
from typing import Any

from jsonschema import Draft202012Validator, ValidationError
import pytest

import build_contracts.demo_execution as build05
from build_contracts.demo_execution import (
    BuildDemoExecutionError,
    artifact_sha256,
    consumption_sha256,
    execute_build_demo_once,
    package_sha256,
    receipt_sha256,
    validate_build_demo_consumption_ledger,
    validate_build_demo_execution_package,
)


ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = ROOT / "data/specifications/nma-build-02-golden-decision-v1.0.json"
PROPOSAL_PATH = ROOT / "data/specifications/nma-build-02-golden-proposal-v1.0.json"
REVIEW_PATH = ROOT / "data/specifications/nma-build-03-golden-gate-review-v1.0.json"
RESOLUTION_PATH = (
    ROOT / "data/specifications/nma-build-03a-golden-gate-resolution-v1.0.json"
)
AUTHORIZATION_PATH = (
    ROOT / "data/specifications/nma-build-04-golden-demo-authorization-v1.0.json"
)
PACKAGE_PATH = (
    ROOT / "data/specifications/nma-build-05-golden-execution-package-v1.0.json"
)
LEDGER_PATH = (
    ROOT / "data/specifications/nma-build-05-authorization-consumption-v1.0.json"
)
SCHEMA_PATH = ROOT / "schemas/build-demo-execution-package-v1.0.schema.json"
ARCHIVE_PATH = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"


@pytest.fixture()
def predecessor() -> tuple[dict[str, Any], ...]:
    return tuple(
        json.loads(path.read_text(encoding="utf-8"))
        for path in (
            AUTHORIZATION_PATH,
            RESOLUTION_PATH,
            REVIEW_PATH,
            PROPOSAL_PATH,
            DECISION_PATH,
        )
    )


@pytest.fixture()
def package() -> dict[str, Any]:
    return json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))


def _fails(callable_, code: str) -> BuildDemoExecutionError:
    with pytest.raises(BuildDemoExecutionError) as caught:
        callable_()
    assert caught.value.code == code
    return caught.value


def _validate(
    candidate: dict[str, Any], predecessor: tuple[dict[str, Any], ...]
) -> dict[str, Any]:
    return validate_build_demo_execution_package(candidate, *predecessor)


def _rehash_package(candidate: dict[str, Any]) -> None:
    artifact = candidate["demo_artifact"]
    artifact["artifact_sha256"] = artifact_sha256(artifact)
    consumption = candidate["consumption_record"]
    consumption["artifact_sha256"] = artifact["artifact_sha256"]
    consumption["consumption_sha256"] = consumption_sha256(consumption)
    receipt = candidate["receipt"]
    receipt["artifact_sha256"] = artifact["artifact_sha256"]
    receipt["consumption_sha256"] = consumption["consumption_sha256"]
    receipt["receipt_sha256"] = receipt_sha256(receipt)
    candidate["package_sha256"] = package_sha256(candidate)


def test_closed_schema_is_meta_valid_and_accepts_only_golden_package(
    package: dict[str, Any],
) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    validator = Draft202012Validator(schema)
    validator.validate(package)

    changed = deepcopy(package)
    changed["production"] = {"allowed": True}
    with pytest.raises(ValidationError):
        validator.validate(changed)


def test_golden_package_validates_against_exact_predecessor_chain(
    package: dict[str, Any], predecessor: tuple[dict[str, Any], ...]
) -> None:
    assert _validate(package, predecessor) == package
    assert package["package_sha256"] == (
        "10c22339abb8d2eed489ae56a54214948213bad51a135e00f74e309931c98c97"
    )


def test_all_internal_hashes_and_identities_are_closed(package: dict[str, Any]) -> None:
    artifact = package["demo_artifact"]
    consumption = package["consumption_record"]
    receipt = package["receipt"]

    assert artifact["artifact_sha256"] == artifact_sha256(artifact)
    assert consumption["consumption_sha256"] == consumption_sha256(consumption)
    assert receipt["receipt_sha256"] == receipt_sha256(receipt)
    assert package["package_sha256"] == package_sha256(package)
    assert consumption["artifact_sha256"] == artifact["artifact_sha256"]
    assert receipt["artifact_sha256"] == artifact["artifact_sha256"]
    assert receipt["consumption_sha256"] == consumption["consumption_sha256"]


def test_independent_ledger_equals_consumption_record(package: dict[str, Any]) -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))

    assert validate_build_demo_consumption_ledger(ledger, package) == ledger
    assert ledger == package["consumption_record"]
    assert ledger["status"] == "consumed-once"
    assert ledger["replay_allowed"] is False


def test_controlled_execution_reproduces_golden_package_and_blocks_replay(
    tmp_path: Path,
    package: dict[str, Any],
    predecessor: tuple[dict[str, Any], ...],
) -> None:
    output = tmp_path / "execution.json"
    ledger = tmp_path / "consumption.json"
    archive_before = build05._file_sha256(ARCHIVE_PATH)

    actual = execute_build_demo_once(
        *predecessor,
        output_path=output,
        consumption_ledger_path=ledger,
        archive_path=ARCHIVE_PATH,
    )

    assert actual == package
    assert json.loads(output.read_text(encoding="utf-8")) == package
    assert json.loads(ledger.read_text(encoding="utf-8")) == package[
        "consumption_record"
    ]
    assert build05._file_sha256(ARCHIVE_PATH) == archive_before
    assert not output.with_name(f".{output.name}.tmp").exists()
    assert not ledger.with_name(f".{ledger.name}.tmp").exists()

    _fails(
        lambda: execute_build_demo_once(
            *predecessor,
            output_path=tmp_path / "different-output.json",
            consumption_ledger_path=ledger,
            archive_path=ARCHIVE_PATH,
        ),
        "authorization_consumed",
    )


def test_existing_consumption_claim_fails_closed_before_source_read(
    tmp_path: Path,
    predecessor: tuple[dict[str, Any], ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = tmp_path / "consumption.json"
    ledger.write_text('{"status":"claimed-fail-closed"}\n', encoding="utf-8")
    source_read = False

    def unexpected_read(_path: Path) -> dict[str, Any]:
        nonlocal source_read
        source_read = True
        raise AssertionError("source read must not occur")

    monkeypatch.setattr(build05, "_read_private_feature", unexpected_read)
    _fails(
        lambda: execute_build_demo_once(
            *predecessor,
            output_path=tmp_path / "execution.json",
            consumption_ledger_path=ledger,
            archive_path=ARCHIVE_PATH,
        ),
        "authorization_consumed",
    )
    assert source_read is False


def test_existing_output_for_same_authorization_is_consumed(
    tmp_path: Path,
    predecessor: tuple[dict[str, Any], ...],
) -> None:
    output = tmp_path / "execution.json"
    output.write_text(
        json.dumps({"authorization_id": build05.AUTHORIZATION_ID}),
        encoding="utf-8",
    )

    _fails(
        lambda: execute_build_demo_once(
            *predecessor,
            output_path=output,
            consumption_ledger_path=tmp_path / "ledger.json",
            archive_path=ARCHIVE_PATH,
        ),
        "authorization_consumed",
    )


def test_unrelated_existing_output_is_conflict(
    tmp_path: Path,
    predecessor: tuple[dict[str, Any], ...],
) -> None:
    output = tmp_path / "execution.json"
    output.write_text('{"other":true}\n', encoding="utf-8")

    _fails(
        lambda: execute_build_demo_once(
            *predecessor,
            output_path=output,
            consumption_ledger_path=tmp_path / "ledger.json",
            archive_path=ARCHIVE_PATH,
        ),
        "execution_conflict",
    )


@pytest.mark.parametrize("same_as", ["output", "source"])
def test_ledger_cannot_alias_output_or_source(
    tmp_path: Path,
    predecessor: tuple[dict[str, Any], ...],
    same_as: str,
) -> None:
    output = tmp_path / "execution.json"
    ledger = output if same_as == "output" else ARCHIVE_PATH

    _fails(
        lambda: execute_build_demo_once(
            *predecessor,
            output_path=output,
            consumption_ledger_path=ledger,
            archive_path=ARCHIVE_PATH,
        ),
        "output_path_invalid",
    )


def test_symlink_output_and_ledger_are_rejected(
    tmp_path: Path,
    predecessor: tuple[dict[str, Any], ...],
) -> None:
    target = tmp_path / "target"
    target.write_text("safe", encoding="utf-8")
    output = tmp_path / "output.json"
    output.symlink_to(target)
    _fails(
        lambda: execute_build_demo_once(
            *predecessor,
            output_path=output,
            consumption_ledger_path=tmp_path / "ledger.json",
            archive_path=ARCHIVE_PATH,
        ),
        "output_path_invalid",
    )

    output.unlink()
    ledger = tmp_path / "ledger.json"
    ledger.symlink_to(target)
    _fails(
        lambda: execute_build_demo_once(
            *predecessor,
            output_path=output,
            consumption_ledger_path=ledger,
            archive_path=ARCHIVE_PATH,
        ),
        "output_path_invalid",
    )


def test_normalized_polygon_is_closed_2d_and_non_geographic(
    package: dict[str, Any],
) -> None:
    artifact = package["demo_artifact"]
    ring = artifact["maplibre_demo"]["source"]["data"]["features"][0][
        "geometry"
    ]["coordinates"][0]

    assert len(ring) == 65
    assert ring[0] == ring[-1]
    assert all(len(coordinate) == 2 for coordinate in ring)
    assert all(0.0 <= value <= 1.0 for coordinate in ring for value in coordinate)
    assert artifact["privacy"] == {
        "coordinate_space": "normalized-local-demo-not-geographic",
        "raw_geographic_coordinates_included": False,
        "raw_attributes_included": False,
        "annotation_value_included": False,
        "derived_normalized_shape_included": True,
    }


def test_source_polygon_z_identity_is_preserved_by_commitment(
    package: dict[str, Any],
) -> None:
    assert package["demo_artifact"]["source_commitments"] == {
        "attribute_commitment_sha256": (
            "ddfa112586b9c2bc3a61bdf2638b7994ba1200bfce5d8ad34988f2a24da96078"
        ),
        "geometry_commitment_sha256": (
            "23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f"
        ),
        "source_geometry_type": "PolygonZ",
        "source_vertex_count": 65,
        "source_ring_count": 1,
    }
    assert package["boundaries"]["source_z_preserved"] is True
    assert package["boundaries"]["source_mutated"] is False


def test_demo_style_and_only_user_control_match_approved_resolution(
    package: dict[str, Any],
) -> None:
    demo = package["demo_artifact"]["maplibre_demo"]

    assert demo["style"]["hatch"] == {
        "pattern_id": "nma-building-hatch-demo",
        "spacing_css_px": "7.559055118110236",
        "angle_degrees": 45.0,
        "color": "#111111",
        "clip_to_feature_geometry": True,
    }
    assert demo["controls"] == {
        "hatch_angle_degrees": {
            "minimum_inclusive": 0.0,
            "maximum_exclusive": 180.0,
            "default": 45.0,
            "step": 1.0,
            "user_adjustable": True,
            "demo_only": True,
        }
    }


def test_annotation_is_placeholder_plus_commitment_not_raw_value(
    package: dict[str, Any],
) -> None:
    properties = package["demo_artifact"]["maplibre_demo"]["source"]["data"][
        "features"
    ][0]["properties"]

    assert properties == {
        "feature_code": "9310100",
        "display_annotation": "樓層＋結構",
        "annotation_value_sha256": (
            "17460f383142153fa58b587a2d3902b6cdbbcddb663d151cf28ce86bc6149a52"
        ),
    }


def test_receipt_proves_source_hash_before_and_after(package: dict[str, Any]) -> None:
    verification = package["receipt"]["source_verification"]

    assert verification["archive_sha256_before"] == verification[
        "archive_sha256_after"
    ]
    assert verification["archive_sha256_after"] == (
        "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
    )
    assert package["receipt"]["outcome"] == "success-derived-demo-only"


def test_boundaries_deny_runtime_production_disclosure_and_promotion(
    package: dict[str, Any],
) -> None:
    assert package["boundaries"] == build05.PACKAGE_BOUNDARIES
    for denied in (
        "raw_geographic_coordinates_disclosed",
        "raw_attributes_disclosed",
        "runtime_wired",
        "production_activated",
        "demo_policy_promoted",
        "source_mutated",
    ):
        assert package["boundaries"][denied] is False


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda value: value.update({"production": True}), "package_invalid"),
        (lambda value: value.pop("receipt"), "package_invalid"),
        (
            lambda value: value["boundaries"].update({"production_activated": True}),
            "package_invalid",
        ),
    ],
)
def test_closed_package_rejects_added_missing_or_promoted_fields(
    package: dict[str, Any],
    predecessor: tuple[dict[str, Any], ...],
    mutation,
    code: str,
) -> None:
    changed = deepcopy(package)
    mutation(changed)

    _fails(lambda: _validate(changed, predecessor), code)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda value: value["demo_artifact"]["privacy"].update(
                {"raw_attributes_included": True}
            ),
            "package_hash_mismatch",
        ),
        (
            lambda value: value["demo_artifact"]["maplibre_demo"]["source"][
                "data"
            ]["features"][0]["geometry"]["coordinates"][0][0].append(123.0),
            "package_hash_mismatch",
        ),
        (
            lambda value: value["demo_artifact"]["maplibre_demo"]["source"][
                "data"
            ]["features"][0]["properties"].update(
                {"raw_annotation": "forbidden"}
            ),
            "package_hash_mismatch",
        ),
        (
            lambda value: value["consumption_record"].update(
                {"replay_allowed": True}
            ),
            "package_invalid",
        ),
        (
            lambda value: value["receipt"]["source_verification"].update(
                {"archive_sha256_after": "0" * 64}
            ),
            "package_hash_mismatch",
        ),
    ],
)
def test_rehashed_tampering_cannot_replace_frozen_execution(
    package: dict[str, Any],
    predecessor: tuple[dict[str, Any], ...],
    mutation,
    expected_code: str,
) -> None:
    changed = deepcopy(package)
    mutation(changed)
    _rehash_package(changed)

    _fails(lambda: _validate(changed, predecessor), expected_code)


def test_tampered_ledger_is_rejected(package: dict[str, Any]) -> None:
    changed = deepcopy(package["consumption_record"])
    changed["replay_allowed"] = True
    changed["consumption_sha256"] = consumption_sha256(changed)

    _fails(
        lambda: validate_build_demo_consumption_ledger(changed, package),
        "ledger_invalid",
    )


def test_changed_predecessor_fails_closed_and_leaves_claim(
    tmp_path: Path,
    predecessor: tuple[dict[str, Any], ...],
) -> None:
    changed = list(deepcopy(predecessor))
    changed[0]["authorization_id"] = "changed"
    ledger = tmp_path / "ledger.json"

    with pytest.raises(Exception):
        execute_build_demo_once(
            *changed,
            output_path=tmp_path / "execution.json",
            consumption_ledger_path=ledger,
            archive_path=ARCHIVE_PATH,
        )

    assert json.loads(ledger.read_text(encoding="utf-8"))["status"] == (
        "claimed-fail-closed"
    )


def test_changed_archive_is_rejected_and_leaves_claim(
    tmp_path: Path,
    predecessor: tuple[dict[str, Any], ...],
) -> None:
    changed_archive = tmp_path / "changed.zip"
    changed_archive.write_bytes(ARCHIVE_PATH.read_bytes() + b"changed")
    ledger = tmp_path / "ledger.json"

    _fails(
        lambda: execute_build_demo_once(
            *predecessor,
            output_path=tmp_path / "execution.json",
            consumption_ledger_path=ledger,
            archive_path=changed_archive,
        ),
        "archive_hash_mismatch",
    )
    assert json.loads(ledger.read_text(encoding="utf-8"))["status"] == (
        "claimed-fail-closed"
    )


def test_package_does_not_disclose_raw_idempotency_key_or_source_fields(
    package: dict[str, Any],
) -> None:
    serialized = json.dumps(package, ensure_ascii=False)

    assert build05.IDEMPOTENCY_KEY not in serialized
    assert "geometry_wkb_hex" not in serialized
    for field in build05.SOURCE_FIELDS:
        assert f'"{field}"' not in serialized


def test_execution_module_has_no_network_or_runtime_adapter_dependency() -> None:
    source = inspect.getsource(build05)

    assert "requests" not in source
    assert "urllib" not in source
    assert "import maplibre" not in source.casefold()
    assert ".addlayer(" not in source.casefold()
    assert "source_write_allowed" not in source


def test_golden_files_are_canonical_json_lines() -> None:
    for path in (PACKAGE_PATH, LEDGER_PATH):
        raw = path.read_bytes()
        parsed = json.loads(raw)
        expected = (
            json.dumps(
                parsed,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )
        assert raw == expected


def test_private_archive_remains_ignored_untracked_and_unstaged() -> None:
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", str(ARCHIVE_PATH)],
        cwd=ROOT,
        check=False,
    )
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(ARCHIVE_PATH)],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    changed = subprocess.run(
        ["git", "diff", "--quiet", "--", str(ARCHIVE_PATH)],
        cwd=ROOT,
        check=False,
    )

    assert ignored.returncode == 0
    assert tracked.returncode != 0
    assert changed.returncode == 0

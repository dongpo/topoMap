from __future__ import annotations

from copy import deepcopy
from html.parser import HTMLParser
import inspect
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError
import pytest

import build_contracts.demo_freeze as build06
from build_contracts.demo_freeze import (
    BuildDemoFreezeError,
    build_build_demo_verification_freeze,
    validate_build_demo_verification_freeze,
    verification_sha256,
)
from nma.core import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PATH = (
    ROOT / "data/specifications/nma-build-05-golden-execution-package-v1.0.json"
)
LEDGER_PATH = (
    ROOT / "data/specifications/nma-build-05-authorization-consumption-v1.0.json"
)
PRESENTATION_PATH = ROOT / "buildDemoV06.html"
FREEZE_PATH = (
    ROOT / "data/specifications/nma-build-06-golden-verification-freeze-v1.0.json"
)
SCHEMA_PATH = ROOT / "schemas/build-demo-verification-freeze-v1.0.schema.json"


class _MarkupAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.scripts: list[dict[str, str | None]] = []
        self.links: list[dict[str, str | None]] = []
        self.ranges: list[dict[str, str | None]] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(str(values["id"]))
        if tag == "script":
            self.scripts.append(values)
        elif tag == "link":
            self.links.append(values)
        elif tag == "input" and values.get("type") == "range":
            self.ranges.append(values)


@pytest.fixture()
def freeze() -> dict[str, Any]:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def package() -> dict[str, Any]:
    return json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))


def _fails(callable_, code: str) -> BuildDemoFreezeError:
    with pytest.raises(BuildDemoFreezeError) as caught:
        callable_()
    assert caught.value.code == code
    return caught.value


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def _record_sha(value: dict[str, Any], field: str) -> str:
    basis = deepcopy(value)
    basis.pop(field, None)
    return canonical_sha256(basis)


def test_golden_freeze_equals_independent_verification(
    freeze: dict[str, Any],
) -> None:
    assert build_build_demo_verification_freeze() == freeze
    assert validate_build_demo_verification_freeze(freeze) == freeze
    assert freeze["verification_sha256"] == (
        "bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857"
    )


def test_closed_schema_is_meta_valid_and_accepts_only_exact_freeze(
    freeze: dict[str, Any],
) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    validator = Draft202012Validator(schema)
    validator.validate(freeze)

    changed = deepcopy(freeze)
    changed["production"] = {"activated": True}
    with pytest.raises(ValidationError):
        validator.validate(changed)


def test_verification_hash_uses_frozen_core_provider(freeze: dict[str, Any]) -> None:
    basis = deepcopy(freeze)
    basis.pop("verification_sha256")

    assert verification_sha256(freeze) == canonical_sha256(basis)


def test_predecessor_is_exact_build05_commit_and_package(freeze: dict[str, Any]) -> None:
    assert freeze["predecessor"] == {
        "branch": "build/build-05-controlled-demo-execution",
        "commit_sha": "290625111ab7a4ecb8af41be168ca186d55d949c",
        "package_sha256": (
            "10c22339abb8d2eed489ae56a54214948213bad51a135e00f74e309931c98c97"
        ),
    }


def test_input_file_and_record_hashes_are_independently_bound(
    freeze: dict[str, Any],
) -> None:
    inputs = freeze["inputs"]

    assert inputs["execution_package"] == {
        "path": "data/specifications/nma-build-05-golden-execution-package-v1.0.json",
        "file_sha256": (
            "508e3378a698f869255485c5008fdb80ed670ce174a3b72092aab5160df7431c"
        ),
        "record_sha256": (
            "10c22339abb8d2eed489ae56a54214948213bad51a135e00f74e309931c98c97"
        ),
    }
    assert inputs["consumption_ledger"]["file_sha256"] == (
        "715a5445827b77308ec32a67efe74ac8e5ed29b9037ee543285270a4da1c9d47"
    )
    assert inputs["presentation"]["file_sha256"] == (
        "de5f6d567810e42af915bdff167fb21e202967b98817e2ef8d2d494d0b47be2d"
    )


def test_all_independent_checks_pass(freeze: dict[str, Any]) -> None:
    verification = freeze["independent_verification"]
    results = {key: value for key, value in verification.items() if key != "artifact_evidence"}

    assert results
    assert set(results.values()) == {"PASS"}
    assert verification["artifact_evidence"] == {
        "ring_count": 1,
        "vertex_count": 65,
        "coordinate_dimensions": 2,
        "coordinate_space": "normalized-local-demo-not-geographic",
        "source_geometry_commitment": (
            "23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f"
        ),
        "source_attribute_commitment": (
            "ddfa112586b9c2bc3a61bdf2638b7994ba1200bfce5d8ad34988f2a24da96078"
        ),
    }


def test_freeze_boundaries_forbid_reexecution_source_and_production(
    freeze: dict[str, Any],
) -> None:
    assert freeze["boundaries"] == build06.BOUNDARIES
    for denied in (
        "build05_authorization_reconsumed",
        "build05_execution_repeated",
        "private_source_accessed",
        "private_source_required",
        "raw_geographic_coordinates_disclosed",
        "raw_attributes_disclosed",
        "network_dependency_added",
        "production_runtime_wired",
        "production_activated",
        "demo_policy_promoted",
    ):
        assert freeze["boundaries"][denied] is False
    assert freeze["boundaries"]["normalized_artifact_only"] is True


def test_freeze_policy_blocks_authorization_reuse_and_authority_expansion(
    freeze: dict[str, Any],
) -> None:
    policy = freeze["freeze_policy"]

    assert policy["immutable"] is True
    assert policy["authorization_reuse_allowed"] is False
    assert policy["source_reexecution_allowed"] is False
    assert policy["production_activation_allowed"] is False
    assert policy["demo_policy_promotion_allowed"] is False
    assert policy["change_requires_new_human_gate"] is True


def test_presentation_is_offline_demo_only_with_approved_angle_control(
    freeze: dict[str, Any],
) -> None:
    assert freeze["presentation"] == {
        "mode": "offline-static-svg-presentation",
        "clearly_labeled_demo_only": True,
        "external_network_dependencies": 0,
        "private_source_dependencies": 0,
        "default_hatch_angle_degrees": 45.0,
        "user_adjustable_hatch_angle": True,
        "angle_range": {
            "minimum_inclusive": 0.0,
            "maximum_exclusive": 180.0,
            "step": 1.0,
        },
    }


def test_presentation_markup_has_required_accessible_controls() -> None:
    source = PRESENTATION_PATH.read_text(encoding="utf-8")
    parser = _MarkupAudit()
    parser.feed(source)

    assert not parser.links
    assert len(parser.scripts) == 1
    assert parser.scripts[0].get("src") is None
    assert parser.ranges == [
        {
            "id": "hatch-angle",
            "type": "range",
            "min": "0",
            "max": "179",
            "step": "1",
            "value": "45",
            "disabled": None,
        }
    ]
    assert {
        "verification-status",
        "demo-svg",
        "building-shape",
        "annotation",
        "hatch-angle",
        "angle-output",
        "reset-angle",
        "error-message",
    } <= parser.ids


def test_presentation_has_no_external_url_or_private_source_reference() -> None:
    source = PRESENTATION_PATH.read_text(encoding="utf-8")

    assert "http://" not in source
    assert "https://" not in source
    assert "112年多維度SHP成果_0502.zip" not in source
    assert "geometry_wkb_hex" not in source
    assert '"BUILD_ID"' not in source
    assert '"BUILD_NO"' not in source
    assert '"BUILD_STR"' not in source
    assert "default-src 'self'" in source


def test_presentation_verifies_both_frozen_files_before_enabling_control() -> None:
    source = PRESENTATION_PATH.read_text(encoding="utf-8")

    assert "EXPECTED_PACKAGE_FILE_SHA256" in source
    assert "EXPECTED_LEDGER_FILE_SHA256" in source
    assert "Promise.all" in source
    assert 'slider.disabled = false' in source
    assert 'status.textContent = "凍結產物驗證通過"' in source
    assert 'status.textContent = "驗證失敗，展示已封鎖"' in source


def test_presentation_uses_only_normalized_shape_and_does_not_mutate_package() -> None:
    source = PRESENTATION_PATH.read_text(encoding="utf-8")

    assert "demo_artifact" in source
    assert "normalized-local-demo-not-geographic" in source
    assert "renderRing(verified.ring)" in source
    assert "execute_build_demo_once" not in source
    assert "fetchVerifiedJson(PACKAGE_URL" in source
    assert "method:" not in source


def test_verifier_has_no_execution_source_or_runtime_capability() -> None:
    source = inspect.getsource(build06)

    assert "demo_execution" not in source
    assert "execute_build_demo_once" not in source
    assert "from build_contracts.resolution" not in source
    assert "_read_private_feature" not in source
    assert "subprocess" not in source
    assert "tempfile" not in source
    assert "ogrinfo" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "write_text" not in source
    assert "write_bytes" not in source


def test_verifier_reads_only_three_public_frozen_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_open = Path.open
    opened: list[Path] = []

    def recording_open(path: Path, *args, **kwargs):
        opened.append(path.resolve())
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", recording_open)
    build_build_demo_verification_freeze()

    assert set(opened) == {
        PACKAGE_PATH.resolve(),
        LEDGER_PATH.resolve(),
        PRESENTATION_PATH.resolve(),
    }


def test_verification_does_not_mutate_any_input() -> None:
    before = {
        path: path.read_bytes() for path in (PACKAGE_PATH, LEDGER_PATH, PRESENTATION_PATH)
    }

    build_build_demo_verification_freeze()

    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize(
    ("target", "code"),
    [
        ("package", "package_file_mismatch"),
        ("ledger", "ledger_file_mismatch"),
        ("presentation", "presentation_file_mismatch"),
    ],
)
def test_any_input_byte_drift_fails_before_freeze(
    tmp_path: Path,
    target: str,
    code: str,
) -> None:
    package_path = tmp_path / PACKAGE_PATH.name
    ledger_path = tmp_path / LEDGER_PATH.name
    presentation_path = tmp_path / PRESENTATION_PATH.name
    package_path.write_bytes(PACKAGE_PATH.read_bytes())
    ledger_path.write_bytes(LEDGER_PATH.read_bytes())
    presentation_path.write_bytes(PRESENTATION_PATH.read_bytes())
    paths = {
        "package": package_path,
        "ledger": ledger_path,
        "presentation": presentation_path,
    }
    paths[target].write_bytes(paths[target].read_bytes() + b"drift")

    _fails(
        lambda: build_build_demo_verification_freeze(
            package_path=package_path,
            ledger_path=ledger_path,
            presentation_path=presentation_path,
        ),
        code,
    )


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda value: value["demo_artifact"]["privacy"].update(
                {"raw_attributes_included": True}
            ),
            "privacy_boundary_mismatch",
        ),
        (
            lambda value: value["demo_artifact"]["maplibre_demo"]["source"][
                "data"
            ]["features"][0]["geometry"]["coordinates"][0][0].append(9.0),
            "privacy_boundary_mismatch",
        ),
        (
            lambda value: value["demo_artifact"]["maplibre_demo"]["controls"][
                "hatch_angle_degrees"
            ].update({"default": 30.0}),
            "semantic_mismatch",
        ),
        (
            lambda value: value["consumption_record"].update(
                {"replay_allowed": True}
            ),
            "consumption_mismatch",
        ),
    ],
)
def test_semantic_tampering_fails_even_when_file_hash_gate_is_rebased(
    tmp_path: Path,
    package: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    mutation,
    code: str,
) -> None:
    changed = deepcopy(package)
    mutation(changed)
    artifact = changed["demo_artifact"]
    artifact["artifact_sha256"] = _record_sha(artifact, "artifact_sha256")
    consumption = changed["consumption_record"]
    consumption["artifact_sha256"] = artifact["artifact_sha256"]
    consumption["consumption_sha256"] = _record_sha(
        consumption, "consumption_sha256"
    )
    receipt = changed["receipt"]
    receipt["artifact_sha256"] = artifact["artifact_sha256"]
    receipt["consumption_sha256"] = consumption["consumption_sha256"]
    receipt["receipt_sha256"] = _record_sha(receipt, "receipt_sha256")
    changed["package_sha256"] = _record_sha(changed, "package_sha256")
    changed_path = tmp_path / "package.json"
    _write_json(changed_path, changed)
    monkeypatch.setattr(build06, "EXPECTED_PACKAGE_FILE_SHA256", build06._file_sha256(changed_path))
    monkeypatch.setattr(build06, "EXPECTED_PACKAGE_SHA256", changed["package_sha256"])
    monkeypatch.setattr(build06, "EXPECTED_ARTIFACT_SHA256", artifact["artifact_sha256"])
    monkeypatch.setattr(
        build06, "EXPECTED_CONSUMPTION_SHA256", consumption["consumption_sha256"]
    )
    monkeypatch.setattr(build06, "EXPECTED_RECEIPT_SHA256", receipt["receipt_sha256"])

    _fails(
        lambda: build_build_demo_verification_freeze(package_path=changed_path),
        code,
    )


def test_ledger_must_equal_package_consumption_record(
    tmp_path: Path,
    package: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = deepcopy(package["consumption_record"])
    ledger["status"] = "claimed-fail-closed"
    ledger["consumption_sha256"] = _record_sha(ledger, "consumption_sha256")
    ledger_path = tmp_path / "ledger.json"
    _write_json(ledger_path, ledger)
    monkeypatch.setattr(build06, "EXPECTED_LEDGER_FILE_SHA256", build06._file_sha256(ledger_path))

    _fails(
        lambda: build_build_demo_verification_freeze(ledger_path=ledger_path),
        "ledger_mismatch",
    )


def test_presentation_contract_rejects_network_dependency_after_rebased_file_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    presentation = tmp_path / "demo.html"
    presentation.write_text(
        PRESENTATION_PATH.read_text(encoding="utf-8").replace(
            "</body>", '<script src="https://example.com/runtime.js"></script></body>'
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        build06, "EXPECTED_PRESENTATION_FILE_SHA256", build06._file_sha256(presentation)
    )

    _fails(
        lambda: build_build_demo_verification_freeze(presentation_path=presentation),
        "network_dependency_detected",
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"production": True}),
        lambda value: value.pop("freeze_policy"),
        lambda value: value["boundaries"].update({"production_activated": True}),
        lambda value: value["freeze_policy"].update(
            {"source_reexecution_allowed": True}
        ),
    ],
)
def test_frozen_manifest_rejects_added_removed_or_expanded_authority(
    freeze: dict[str, Any], mutation
) -> None:
    changed = deepcopy(freeze)
    mutation(changed)
    changed["verification_sha256"] = verification_sha256(changed)

    _fails(lambda: validate_build_demo_verification_freeze(changed), "freeze_mismatch")


def test_known_full_suite_failures_are_exact_pre_existing_baseline(
    freeze: dict[str, Any],
) -> None:
    assert freeze["known_pre_existing_failures"] == build06.KNOWN_BASELINE_FAILURES
    assert len(freeze["known_pre_existing_failures"]) == 3


def test_golden_freeze_is_canonical_json_line(freeze: dict[str, Any]) -> None:
    expected = (
        json.dumps(
            freeze,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )

    assert FREEZE_PATH.read_bytes() == expected

from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import pytest

import build_contracts.official_production_scope_authorization as build08a
from build_contracts.official_production_scope_authorization import (
    BuildOfficialProductionScopeAuthorizationError,
    build_official_production_scope_authorization,
    official_production_scope_authorization_sha256,
    validate_official_production_scope_authorization,
)


ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR_SHA = "666a12adf4a1b369168480e13b2b65107429d935"
BUILD08_REVIEW_SHA256 = "b48337a6bb8cf1e6cffc54e0bbfe14383f62c1dcfdca54bf706c0ab045b42484"
AUTHORIZATION_SHA256 = "4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8"
TEMPLATE_PATH = ROOT / "data/specifications/nma-build-07-golden-evaluation-template-v1.0.json"
EVALUATION_PATH = ROOT / "data/specifications/nma-build-07-accepted-user-evaluation-v1.0.json"
REVIEW_PATH = (
    ROOT / "data/specifications/nma-build-08-golden-official-production-entry-review-v1.0.json"
)
AUTHORIZATION_PATH = (
    ROOT
    / "data/specifications/nma-build-08a-golden-human-official-production-scope-authorization-v1.0.json"
)
SCHEMA_PATH = ROOT / "schemas/build-human-official-production-scope-authorization-v1.0.schema.json"


@pytest.fixture()
def template() -> dict:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def evaluation() -> dict:
    return json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def review() -> dict:
    return json.loads(REVIEW_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def authorization() -> dict:
    return json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))


def _validate(authorization: dict, review: dict, template: dict, evaluation: dict) -> dict:
    return validate_official_production_scope_authorization(
        authorization, review, template, evaluation
    )


def _rehash(authorization: dict) -> dict:
    authorization["authorization_sha256"] = official_production_scope_authorization_sha256(
        authorization
    )
    return authorization


def _must_fail(
    authorization: dict,
    review: dict,
    template: dict,
    evaluation: dict,
) -> BuildOfficialProductionScopeAuthorizationError:
    with pytest.raises(BuildOfficialProductionScopeAuthorizationError) as caught:
        _validate(authorization, review, template, evaluation)
    return caught.value


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _authority(authorization: dict) -> dict[str, str]:
    return {
        item["capability_id"]: item["authority"] for item in authorization["capability_authority"]
    }


def test_authorization_is_exactly_reproducible(
    authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    actual = build_official_production_scope_authorization(review, template, evaluation)

    assert actual == authorization
    assert actual["authorization_sha256"] == AUTHORIZATION_SHA256
    assert official_production_scope_authorization_sha256(actual) == AUTHORIZATION_SHA256


def test_exact_build08_predecessor_identity(authorization: dict) -> None:
    predecessor = authorization["predecessor"]

    assert predecessor["build08_completion_commit"] == PREDECESSOR_SHA
    assert predecessor["build08_branch"] == "build/build-08-official-production-entry-review"
    assert predecessor["build08_completion_report_file_sha256"] == (
        "c4099b6cead5ddbca97edf4285d2496d129745fb4b6ca6709ccbdaa46b52d38f"
    )


def test_exact_build08_review_identity(authorization: dict) -> None:
    predecessor = authorization["predecessor"]

    assert predecessor["build08_review_sha256"] == BUILD08_REVIEW_SHA256
    assert predecessor["build08_review_file_sha256"] == (
        "be9ee241d358ba4c426ed7756345b899dffaa2e010f5f66abbe4b24ad7355b1b"
    )


def test_closed_draft_2020_12_schema_accepts_only_frozen_authorization(
    authorization: dict,
) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(authorization)


def test_all_five_gates_remain_unresolved_and_held(authorization: dict) -> None:
    gates = authorization["unresolved_gates"]

    assert [gate["gate_id"] for gate in gates] == [
        "hatch-angle-transcription",
        "building-annotation-placement",
        "real-build-schema-binding",
        "line-and-color-profile",
        "j13-polygonz-runtime-policy",
    ]
    assert len(gates) == 5
    assert all(gate["official_status"] == "unresolved" for gate in gates)
    assert all(gate["production_status"] == "hold" for gate in gates)
    assert all(gate["production_ready"] is False for gate in gates)


def test_authoritative_evidence_collection_is_authorized(authorization: dict) -> None:
    authority = _authority(authorization)

    assert authority["read-tracked-evidence"] == "allowed"
    assert authority["collect-authoritative-official-evidence"] == "allowed"
    assert authority["inspect-explicitly-supplied-official-documentation"] == "allowed"


def test_j13_j17_resolution_is_authorized_without_preselection(authorization: dict) -> None:
    assert _authority(authorization)["resolve-j13-j17-through-evidence"] == "allowed"
    policy = authorization["building_layer_policy"]
    assert policy["candidate_layer_ids"] == ["J13_BUILD", "J17_BUILD"]
    assert policy["selected_layer_id"] is None
    assert policy["selection_status"] == "hold-pending-authoritative-trace"
    assert policy["global_equivalence_assumed"] is False


def test_z_preserving_derived_xy_design_is_authorized(authorization: dict) -> None:
    assert _authority(authorization)["design-z-preserving-derived-xy-architecture"] == ("allowed")
    policy = authorization["z_dimension_policy"]
    assert policy["architecture_design_allowed"] is True
    assert policy["authoritative_source_geometry"] == "PolygonZ"
    assert policy["source_representation"] == "preserved-immutable"
    assert policy["display_representation"] == "derived-non-writing-xy"
    assert policy["source_and_display_geometry_distinct"] is True


def test_destructive_drop_z_is_not_authorized(authorization: dict) -> None:
    assert _authority(authorization)["drop-source-z"] == "forbidden"
    policy = authorization["z_dimension_policy"]
    assert policy["existing_drop_z_production_path"] == "not-approved"
    assert policy["source_transformation_authorized"] is False
    assert policy["source_z_drop_allowed"] is False


def test_annotation_binding_design_is_authorized_without_invented_binding(
    authorization: dict,
) -> None:
    assert _authority(authorization)["design-annotation-binding"] == "allowed"
    policy = authorization["annotation_policy"]
    assert policy["design_allowed"] is True
    assert policy["runtime_binding_implementation_allowed"] is False
    assert policy["current_source_fields"] == ["BUILD_NO", "BUILD_STR"]
    assert policy["current_runtime_label_field"] is None
    assert policy["binding_selected"] is False


@pytest.mark.parametrize(
    "boundary",
    [
        "official_portrayal_activation_allowed",
        "production_activation_allowed",
        "production_runtime_creation_allowed",
        "source_mutation_allowed",
        "source_z_drop_allowed",
        "private_source_access_allowed",
        "unauthorized_execution_allowed",
    ],
)
def test_forbidden_activation_source_and_execution_boundaries_fail_closed(
    authorization: dict,
    review: dict,
    template: dict,
    evaluation: dict,
    boundary: str,
) -> None:
    assert authorization["activation_and_source_boundaries"][boundary] is False
    changed = deepcopy(authorization)
    changed["activation_and_source_boundaries"][boundary] = True
    _rehash(changed)

    assert _must_fail(changed, review, template, evaluation).code == "authorization_mismatch"


def test_demo_acceptance_cannot_establish_official_authority(authorization: dict) -> None:
    policy = authorization["evidence_policy"]

    assert policy["official_semantics_independent_authority_denied"] == [
        "demo-evidence",
        "human-demo-evaluation",
    ]
    assert authorization["portrayal_policy"]["human_demo_acceptance_is_official_evidence"] is False
    assert _authority(authorization)["promote-demo-acceptance-to-official-authority"] == "forbidden"


def test_implementation_evidence_alone_cannot_establish_portrayal_authority(
    authorization: dict,
) -> None:
    assert authorization["evidence_policy"]["official_portrayal_independent_authority_denied"] == [
        "implementation-evidence"
    ]
    assert (
        authorization["portrayal_policy"]["implementation_history_is_official_authority"] is False
    )


@pytest.mark.parametrize("kind", ["evidence-class", "capability", "gate"])
def test_unknown_evidence_class_capability_or_gate_fails(
    authorization: dict,
    review: dict,
    template: dict,
    evaluation: dict,
    kind: str,
) -> None:
    changed = deepcopy(authorization)
    if kind == "evidence-class":
        changed["evidence_policy"]["authority_classes"].append("invented-authority")
    elif kind == "capability":
        changed["capability_authority"].append(
            {"capability_id": "activate-everything", "authority": "allowed"}
        )
    else:
        changed["unresolved_gates"][0]["gate_id"] = "unknown-gate"
    _rehash(changed)

    assert _must_fail(changed, review, template, evaluation).code == "authorization_mismatch"

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(changed)


def test_tampered_authorization_identity_fails(
    authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    changed = deepcopy(authorization)
    changed["authorization_sha256"] = "0" * 64

    assert _must_fail(changed, review, template, evaluation).code == "authorization_mismatch"


def test_build08_artifact_identities_remain_unchanged(authorization: dict) -> None:
    predecessor = authorization["predecessor"]

    assert (
        _file_sha256(ROOT / "BUILD-08-Completion-Report.md")
        == predecessor["build08_completion_report_file_sha256"]
    )
    assert _file_sha256(REVIEW_PATH) == predecessor["build08_review_file_sha256"]
    assert (
        json.loads(REVIEW_PATH.read_text())["review_sha256"] == predecessor["build08_review_sha256"]
    )


def test_build07_accepted_evaluation_remains_unchanged(authorization: dict) -> None:
    predecessor = authorization["predecessor"]

    assert _file_sha256(EVALUATION_PATH) == predecessor["build07_record_file_sha256"]
    assert (
        json.loads(EVALUATION_PATH.read_text())["record_sha256"]
        == predecessor["build07_record_sha256"]
    )
    assert (
        json.loads(TEMPLATE_PATH.read_text())["template_sha256"]
        == predecessor["build07_template_sha256"]
    )


def test_previous_build_and_forbidden_artifacts_remain_unchanged() -> None:
    changed = set(
        subprocess.run(
            ["git", "diff", "--name-only", PREDECESSOR_SHA, "--"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )
    allowed = {
        "BUILD-08A-Completion-Report.md",
        "build_contracts/official_production_scope_authorization.py",
        "data/specifications/nma-build-08a-golden-human-official-production-scope-authorization-v1.0.json",
        "schemas/build-human-official-production-scope-authorization-v1.0.schema.json",
        "tests/test_build_human_official_production_scope_authorization_build08a.py",
    }

    assert changed <= allowed
    assert not changed & {
        "src/nma/real_layer.py",
        "src/nma/portrayal_compile.py",
        "src/nma/maplibre_adapter.py",
        "data/specifications/nma-build-07-accepted-user-evaluation-v1.0.json",
        "data/specifications/nma-build-08-golden-official-production-entry-review-v1.0.json",
    }


def test_production_hatch_asset_is_not_created_or_approved(authorization: dict) -> None:
    asset = ROOT / "assets/symbols/nlsc112v5.4/review-candidates/building-hatch-tile-v1.svg"

    assert not asset.exists()
    assert authorization["portrayal_policy"]["hatch_asset_creation_allowed"] is False
    assert authorization["portrayal_policy"]["missing_hatch_asset_approved"] is False


def test_next_stage_is_evidence_design_only_and_not_started(authorization: dict) -> None:
    boundary = authorization["next_stage_boundary"]

    assert boundary["recommended_stage"] == "BUILD-09"
    assert boundary["evidence_and_design_first"] is True
    assert boundary["production_execution_requires_later_separate_authorization"] is True
    assert boundary["source_mutation_requires_later_separate_authorization"] is True
    assert boundary["build09_started"] is False


def test_unknown_top_level_field_fails_closed(
    authorization: dict, review: dict, template: dict, evaluation: dict
) -> None:
    changed = deepcopy(authorization)
    changed["production_ready"] = True
    _rehash(changed)

    assert _must_fail(changed, review, template, evaluation).code == (
        "authorization_fields_invalid"
    )


def test_build08a_module_has_no_execution_or_filesystem_mutation_capability() -> None:
    source = inspect.getsource(build08a)

    for forbidden in (
        "subprocess",
        "ogr2ogr",
        "execute_real_layer",
        "inspect_private_build_source",
        "open(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in source


def test_golden_authorization_is_canonical_single_json_line(authorization: dict) -> None:
    expected = (
        json.dumps(
            authorization,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )

    assert AUTHORIZATION_PATH.read_bytes() == expected

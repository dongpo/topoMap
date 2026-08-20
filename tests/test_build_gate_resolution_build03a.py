from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError
import pytest

import build_contracts.gate_resolution as build03a
from build_contracts.gate_resolution import (
    APPROVAL_DECISION,
    EXPECTED_BOUNDARIES,
    BuildGateResolutionError,
    prepare_build_gate_resolution,
    resolution_sha256,
    validate_gate_resolution,
)
from build_contracts.gate_review import BuildGateReviewError
from build_contracts.portrayal_decision import BUILD_GATE_IDS
from nma.core import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = ROOT / "data/specifications/nma-build-02-golden-decision-v1.0.json"
PROPOSAL_PATH = ROOT / "data/specifications/nma-build-02-golden-proposal-v1.0.json"
REVIEW_PATH = ROOT / "data/specifications/nma-build-03-golden-gate-review-v1.0.json"
RESOLUTION_PATH = (
    ROOT / "data/specifications/nma-build-03a-golden-gate-resolution-v1.0.json"
)
SCHEMA_PATH = ROOT / "schemas/build-gate-resolution-v1.0.schema.json"


@pytest.fixture()
def decision() -> dict[str, Any]:
    return json.loads(DECISION_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def proposal() -> dict[str, Any]:
    return json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def review() -> dict[str, Any]:
    return json.loads(REVIEW_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def resolution(
    review: dict[str, Any], proposal: dict[str, Any], decision: dict[str, Any]
) -> dict[str, Any]:
    result = prepare_build_gate_resolution(
        review, proposal, decision, APPROVAL_DECISION
    )
    assert result is not None
    return result


def _fails(callable_, code: str | None = None) -> BuildGateResolutionError:
    with pytest.raises(BuildGateResolutionError) as caught:
        callable_()
    if code is not None:
        assert caught.value.code == code
    return caught.value


def test_exact_human_decision_generates_golden_resolution(
    review: dict[str, Any], proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    actual = prepare_build_gate_resolution(
        review, proposal, decision, APPROVAL_DECISION
    )

    assert actual == json.loads(RESOLUTION_PATH.read_text(encoding="utf-8"))
    assert actual["resolution_sha256"] == (
        "a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01"
    )


def test_closed_schema_is_meta_valid_and_accepts_only_exact_resolution(
    resolution: dict[str, Any],
) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    validator = Draft202012Validator(schema)
    validator.validate(resolution)

    changed = deepcopy(resolution)
    changed["authorization"] = {"execution_allowed": True}
    with pytest.raises(ValidationError):
        validator.validate(changed)


def test_plain_language_recommendations_and_approved_resolutions_are_recorded(
    resolution: dict[str, Any],
) -> None:
    decisions = resolution["gate_decisions"]

    assert [item["gate_id"] for item in decisions] == list(BUILD_GATE_IDS)
    assert all(item["plain_language_zh_tw"] for item in decisions)
    assert all(item["recommended_resolution_zh_tw"] for item in decisions)
    assert all(item["approved_resolution_zh_tw"] for item in decisions)
    assert all(item["evidence_boundary"] for item in decisions)


def test_exact_user_approval_statement_and_scope_are_recorded(
    resolution: dict[str, Any],
) -> None:
    assert resolution["human_approval"] == {
        "actor_type": "human-project-owner",
        "decision": APPROVAL_DECISION,
        "recorded_on": "2026-08-20",
        "statement_zh_tw": (
            "核准 BUILD-03A 建議決議。剖面線角度先以45度，DEMO提供使用者調整，"
            "凡語意不清者，都是DEMO的項目。"
        ),
        "all_five_gate_decisions_explicit": True,
    }


def test_hatch_is_45_degree_adjustable_demo_default_not_source_fact(
    resolution: dict[str, Any],
) -> None:
    hatch = resolution["resolved_demo_portrayal"]["hatch"]

    assert hatch["numeric_angle_degrees"] == 45.0
    assert hatch["angle_user_adjustable"] is True
    assert hatch["demo_only"] is True
    assert resolution["scope_policy"]["user_adjustable_fields"] == [
        "hatch.numeric_angle_degrees"
    ]
    assert resolution["gate_decisions"][0]["evidence_boundary"] == (
        "human-approved-demo-default-not-source-transcription"
    )


def test_every_ambiguous_choice_is_demo_only_and_not_production_authority(
    resolution: dict[str, Any],
) -> None:
    scope = resolution["scope_policy"]

    assert scope["ambiguous_semantics_are_demo_only"] is True
    assert scope["demo_choices_are_official_source_facts"] is False
    assert scope["demo_choices_are_production_authority"] is False
    assert scope["official_portrayal_baseline_mutated"] is False
    assert all(
        item["status"] == "resolved-for-demo-scope"
        for item in resolution["gate_decisions"]
    )


def test_maplibre_demo_line_color_and_spacing_profile_is_exact(
    resolution: dict[str, Any],
) -> None:
    portrayal = resolution["resolved_demo_portrayal"]
    profile = portrayal["boundary_profile"]
    hatch = portrayal["hatch"]

    assert profile == {
        "profile_id": "nma-maplibre-web-demo-v1",
        "line_code": "2",
        "style": "solid",
        "width_css_px": 1.0,
        "color_code": "7",
        "color_hex": "#111111",
        "opacity": 1.0,
        "demo_only": True,
    }
    assert hatch["spacing_mm"] == 2.0
    assert hatch["spacing_css_px"] == "7.559055118110236"


def test_annotation_policy_is_deterministic_bounded_and_demo_only(
    resolution: dict[str, Any],
) -> None:
    annotation = resolution["resolved_demo_portrayal"]["annotation"]

    assert annotation["content_fields"] == ["BUILD_NO", "BUILD_STR"]
    assert annotation["format"] == "{BUILD_NO}{BUILD_STR}"
    assert annotation["anchor_policy"] == "polygon-pole-of-inaccessibility"
    assert annotation["collision_policy"] == (
        "suppress-if-no-interior-fit-or-higher-priority-collision"
    )
    assert annotation["outside_displacement_allowed"] is False
    assert annotation["demo_only"] is True


def test_schema_binding_is_j13_bounded_without_global_equivalence(
    resolution: dict[str, Any],
) -> None:
    binding = resolution["resolved_demo_portrayal"]["schema_binding"]

    assert binding["layer_id"] == "J13_BUILD"
    assert binding["feature_code"] == "9310100"
    assert binding["annotation_fields"] == ["BUILD_NO", "BUILD_STR"]
    assert binding["id_source_global_equivalence_asserted"] is False
    assert binding["other_layer_authority_inherited"] is False
    assert binding["demo_only"] is True


def test_polygonz_is_preserved_and_xy_is_non_mutating_demo_view(
    resolution: dict[str, Any],
) -> None:
    geometry = resolution["resolved_demo_portrayal"]["geometry_policy"]

    assert geometry == {
        "source_geometry_type": "PolygonZ",
        "authoritative_z_preserved": True,
        "demo_view_dimensions": "XY",
        "demo_xy_projection_writes_back": False,
        "source_z_dimension_drop_authorized": False,
        "geometry_repair_authorized": False,
    }


def test_demo_gates_resolve_without_execution_or_production_approval(
    resolution: dict[str, Any],
) -> None:
    assert resolution["resolution_effect"] == {
        "all_gates_resolved_for_demo_scope": True,
        "production_gates_resolved": False,
        "demo_candidate_eligible_for_later_authorization": True,
        "execution_authorization_issued": False,
    }
    assert resolution["boundaries"]["execution_allowed"] is False
    assert resolution["boundaries"]["runtime_wiring_allowed"] is False
    assert resolution["boundaries"]["production_activation_allowed"] is False


@pytest.mark.parametrize("human_decision", ["approved", "rejected", "45-degrees"])
def test_generic_or_incomplete_human_decisions_cannot_create_resolution(
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    human_decision: str,
) -> None:
    _fails(
        lambda: prepare_build_gate_resolution(
            review, proposal, decision, human_decision
        ),
        "decision_scope_mismatch",
    )


def test_absent_human_decision_creates_nothing(
    review: dict[str, Any], proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    assert prepare_build_gate_resolution(review, proposal, decision, None) is None


@pytest.mark.parametrize(
    ("change", "value"),
    [
        ("actor", "system"),
        ("statement", "approved"),
        ("scope", False),
        ("plain-language", "changed"),
        ("angle", 46.0),
        ("adjustable", False),
        ("hatch-demo", False),
        ("line-width", 2.0),
        ("annotation-outside", True),
        ("schema-equivalence", True),
        ("z-preserved", False),
        ("production-resolved", True),
        ("authorization-issued", True),
    ],
)
def test_rehashed_resolution_tampering_fails_closed(
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    change: str,
    value: object,
) -> None:
    changed = deepcopy(resolution)
    if change == "actor":
        changed["human_approval"]["actor_type"] = value
    elif change == "statement":
        changed["human_approval"]["statement_zh_tw"] = value
    elif change == "scope":
        changed["scope_policy"]["ambiguous_semantics_are_demo_only"] = value
    elif change == "plain-language":
        changed["gate_decisions"][0]["plain_language_zh_tw"] = value
    elif change == "angle":
        changed["resolved_demo_portrayal"]["hatch"][
            "numeric_angle_degrees"
        ] = value
    elif change == "adjustable":
        changed["resolved_demo_portrayal"]["hatch"]["angle_user_adjustable"] = value
    elif change == "hatch-demo":
        changed["resolved_demo_portrayal"]["hatch"]["demo_only"] = value
    elif change == "line-width":
        changed["resolved_demo_portrayal"]["boundary_profile"][
            "width_css_px"
        ] = value
    elif change == "annotation-outside":
        changed["resolved_demo_portrayal"]["annotation"][
            "outside_displacement_allowed"
        ] = value
    elif change == "schema-equivalence":
        changed["resolved_demo_portrayal"]["schema_binding"][
            "id_source_global_equivalence_asserted"
        ] = value
    elif change == "z-preserved":
        changed["resolved_demo_portrayal"]["geometry_policy"][
            "authoritative_z_preserved"
        ] = value
    elif change == "production-resolved":
        changed["resolution_effect"]["production_gates_resolved"] = value
    else:
        changed["resolution_effect"]["execution_authorization_issued"] = value
    changed["resolution_sha256"] = resolution_sha256(changed)

    _fails(
        lambda: validate_gate_resolution(changed, review, proposal, decision),
        "resolution_invalid",
    )


@pytest.mark.parametrize("boundary", sorted(EXPECTED_BOUNDARIES))
def test_authority_boundary_cannot_be_expanded(
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
    boundary: str,
) -> None:
    changed = deepcopy(resolution)
    changed["boundaries"][boundary] = not EXPECTED_BOUNDARIES[boundary]
    changed["resolution_sha256"] = resolution_sha256(changed)

    _fails(
        lambda: validate_gate_resolution(changed, review, proposal, decision),
        "resolution_invalid",
    )


def test_changed_build03_predecessor_fails_closed(
    review: dict[str, Any], proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    changed = deepcopy(review)
    changed["review"]["gates"][0]["status"] = "resolved-for-demo-scope"

    with pytest.raises(BuildGateReviewError):
        prepare_build_gate_resolution(changed, proposal, decision, APPROVAL_DECISION)


def test_hash_is_deterministic_and_uses_frozen_core_provider(
    review: dict[str, Any], proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    first = prepare_build_gate_resolution(
        review, proposal, decision, APPROVAL_DECISION
    )
    second = prepare_build_gate_resolution(
        json.loads(json.dumps(review, sort_keys=True)),
        json.loads(json.dumps(proposal, sort_keys=True)),
        json.loads(json.dumps(decision, sort_keys=True)),
        APPROVAL_DECISION,
    )

    assert first == second
    assert first is not None
    assert first["resolution_sha256"] == resolution_sha256(first)
    assert build03a.canonical_sha256 is canonical_sha256
    assert "def canonical_sha256" not in inspect.getsource(build03a)


def test_inputs_are_not_mutated(
    review: dict[str, Any], proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    before = deepcopy((review, proposal, decision))

    prepare_build_gate_resolution(review, proposal, decision, APPROVAL_DECISION)

    assert (review, proposal, decision) == before


def test_no_private_geometry_or_raw_attributes_are_disclosed(
    resolution: dict[str, Any],
) -> None:
    serialized = json.dumps(resolution, ensure_ascii=False).casefold()

    assert "2bxkp71rbn" not in serialized
    assert "coordinates" not in serialized
    assert "geometry_wkb_hex" not in serialized
    assert "source_example" not in serialized
    assert resolution["boundaries"]["raw_source_disclosure_allowed"] is False
    assert resolution["boundaries"]["redistribution_allowed"] is False


def test_module_has_no_execution_geometry_network_or_runtime_capability() -> None:
    source = inspect.getsource(build03a).casefold()

    assert "subprocess" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "shapely" not in source
    assert "maplibre_adapter" not in source
    assert ".write_" not in source
    assert "authorization_sha256" not in source
    assert "authorization_id" not in source


def test_predecessor_bindings_are_exact(
    resolution: dict[str, Any],
    review: dict[str, Any],
    proposal: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    assert resolution["bindings"]["review_sha256"] == review["review_sha256"]
    assert resolution["bindings"]["proposal_sha256"] == proposal["proposal_sha256"]
    assert resolution["bindings"]["decision_sha256"] == decision["decision_sha256"]

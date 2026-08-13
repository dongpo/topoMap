import json
from pathlib import Path

import pytest

from nma.graphrag import CanonicalGraphRetriever
from nma.portrayal_compile import compile_portrayal_preview
from nma.portrayal_review import (
    PortrayalReviewEngine,
    PortrayalReviewError,
    merge_portrayal_revision,
    validate_portrayal_edit_plan,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/portrayal-edit-plan-v0.4.schema.json"
RECIPES = (
    ROOT / "data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json"
)
GRAPH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"


def plan(code: str, geometry: str, action: str, target: str, value: dict) -> dict:
    return {
        "schema": "nma.portrayal-edit-plan/0.4",
        "source": "deterministic-test",
        "feature_code": code,
        "geometry_role": geometry,
        "operations": [{"action": action, "target": target, "value": value}],
    }


def package(query: str) -> dict:
    return CanonicalGraphRetriever.load(GRAPH).evidence_package(
        query, max_depth=3, max_nodes=40
    )


def test_portrayal_edit_schema_is_closed_and_geometry_general() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    assert schema["properties"]["geometry_role"]["enum"] == [
        "Point",
        "LineString",
        "Polygon",
    ]
    operation = schema["properties"]["operations"]["items"]
    assert operation["additionalProperties"] is False
    assert "raw_svg" not in operation["properties"]["action"]["enum"]


@pytest.mark.parametrize(
    ("query", "code", "geometry", "action", "target", "value", "primitive"),
    [
        (
            "消防栓 9350906 圖式",
            "9350906",
            "Point",
            "set_color",
            "marker",
            {"color": "#1565c0"},
            "outer-box",
        ),
        (
            "一般市區道路 9420801 圖式",
            "9420801",
            "LineString",
            "set_line_pattern",
            "stroke",
            {"pattern": "dash"},
            "roada-surveyed-road-boundary",
        ),
        (
            "養殖池 9740100 圖式",
            "9740100",
            "Polygon",
            "set_scale",
            "interior-marker",
            {"number": 1.2},
            "fish-marker",
        ),
        (
            "永久性建物 9310100 圖式",
            "9310100",
            "Polygon",
            "set_hatch_spacing",
            "hatch",
            {"number": 2.5},
            "building-diagonal-hatch",
        ),
        (
            "小學 9920103 圖式",
            "9920103",
            "Point",
            "set_rotation",
            "marker",
            {"number": 10},
            "flag-pole",
        ),
    ],
)
def test_review_engine_compiles_point_line_polygon_preferences_without_mutating_baseline(
    query, code, geometry, action, target, value, primitive
) -> None:
    engine = PortrayalReviewEngine.load(RECIPES)
    original = engine.baseline(code)
    proposal = engine.propose(
        plan(code, geometry, action, target, value), package(query)
    )

    assert proposal["status"] == "review-proposal-non-executable"
    assert proposal["feature"]["geometry_role"] == geometry
    assert proposal["official_baseline"]["immutable"] is True
    assert primitive in proposal["derived_preview_ir"]["baseline_primitive_ids"]
    assert proposal["derived_preview_ir"]["overrides"][0]["authority"] == "user-preference"
    assert proposal["derived_preview_ir"]["raw_svg_or_code_allowed"] is False
    assert proposal["evidence"]["citations"]
    assert proposal["approval"]["derived_style_approval"] == "pending-human-approval"
    assert proposal["automatic_action"] is False
    assert engine.baseline(code) == original


def test_geometry_incompatible_and_unbounded_operations_are_rejected() -> None:
    with pytest.raises(PortrayalReviewError, match="incompatible"):
        validate_portrayal_edit_plan(
            plan("9420801", "LineString", "set_fill_pattern", "fill", {"pattern": "hatch"})
        )
    with pytest.raises(PortrayalReviewError, match="out of bounds"):
        validate_portrayal_edit_plan(
            plan("9920103", "Point", "set_scale", "marker", {"number": 20})
        )
    unsafe = plan("9920103", "Point", "set_color", "marker", {"color": "#1565c0"})
    unsafe["operations"][0]["raw_svg"] = "<path/>"
    with pytest.raises(PortrayalReviewError, match="invalid shape"):
        validate_portrayal_edit_plan(unsafe)


def test_school_structural_edit_compiles_without_mutating_official_baseline() -> None:
    engine = PortrayalReviewEngine.load(RECIPES)
    original = engine.baseline("9920103")
    structural = {
        "schema": "nma.portrayal-edit-plan/0.4",
        "source": "deterministic-test",
        "feature_code": "9920103",
        "geometry_role": "Point",
        "operations": [
            {"action": "set_color", "target": "marker", "value": {"color": "#1565c0"}},
            {"action": "add_shape", "target": "support", "value": {"shape": "rectangle"}},
            {
                "action": "match_dimension",
                "target": "support",
                "value": {"reference": "flag", "relation": "proportional-width"},
            },
            {
                "action": "attach",
                "target": "flagpole-bottom",
                "value": {"reference": "support-top", "relation": "inserted-into-top"},
            },
            {
                "action": "center",
                "target": "flagpole-bottom",
                "value": {"reference": "support", "relation": "centered"},
            },
        ],
    }

    proposal = engine.propose(structural, package("小學 9920103 圖式"))
    proposal["approval"]["derived_style_approval"] = "approved-for-preview"
    observation = compile_portrayal_preview(proposal)

    assert observation["render_ir"]["channels"]["marker"]["color"] == "#1565c0"
    assert observation["render_ir"]["structure"] == {
        "flag_top_alignment": "offset",
        "support": {
            "enabled": True,
            "shape": "rectangle",
            "width_relation": "proportional-width",
        },
        "flagpole_attachment": "inserted-into-top",
        "flagpole_horizontal_alignment": "centered",
    }
    assert observation["render_ir"]["raw_svg_or_code"] is None
    assert engine.baseline("9920103") == original


def test_structural_symbol_operations_are_rejected_for_unreviewed_features() -> None:
    with pytest.raises(PortrayalReviewError, match="not reviewed"):
        validate_portrayal_edit_plan(
            {
                "schema": "nma.portrayal-edit-plan/0.4",
                "source": "deterministic-test",
                "feature_code": "9350906",
                "geometry_role": "Point",
                "operations": [
                    {
                        "action": "add_shape",
                        "target": "support",
                        "value": {"shape": "rectangle"},
                    }
                ],
            }
        )


def test_missing_or_wrong_evidence_cannot_produce_a_review_proposal() -> None:
    engine = PortrayalReviewEngine.load(RECIPES)
    school_plan = plan("9920103", "Point", "set_color", "marker", {"color": "#1565c0"})

    with pytest.raises(PortrayalReviewError, match="retrieved evidence"):
        engine.propose(
            school_plan,
            package("不存在於官方語料的虛構星際傳送門圖徵"),
        )
    with pytest.raises(PortrayalReviewError, match="source rule is absent"):
        engine.propose(school_plan, package("消防栓 9350906 圖式"))


def test_linked_revision_inherits_preferences_and_replaces_only_the_same_channel() -> None:
    engine = PortrayalReviewEngine.load(RECIPES)
    evidence = package("小學 9920103 圖式")
    parent_plan = {
        "schema": "nma.portrayal-edit-plan/0.4",
        "source": "deterministic-test",
        "feature_code": "9920103",
        "geometry_role": "Point",
        "operations": [
            {"action": "set_color", "target": "marker", "value": {"color": "#1565c0"}},
            {"action": "set_scale", "target": "marker", "value": {"number": 1.2}},
        ],
    }
    child_plan = {
        **parent_plan,
        "operations": [
            {"action": "set_color", "target": "marker", "value": {"color": "#c62828"}},
            {"action": "set_rotation", "target": "marker", "value": {"number": 10}},
        ],
    }
    parent = engine.propose(parent_plan, evidence)
    parent["approval"]["derived_style_approval"] = "approved-for-preview"
    parent_before = json.loads(json.dumps(parent, ensure_ascii=False))
    child = engine.propose(child_plan, evidence)

    revised = merge_portrayal_revision(
        parent, child, parent_proposal_id="portrayal_1234567890abcdef12345678"
    )
    operations = {
        (item["action"], item["target"]): item["value"]
        for item in revised["derived_preview_ir"]["overrides"]
    }

    assert operations[("set_color", "marker")] == {"color": "#c62828"}
    assert operations[("set_scale", "marker")] == {"number": 1.2}
    assert operations[("set_rotation", "marker")] == {"number": 10}
    assert revised["revision"] == {
        "parent_proposal_id": "portrayal_1234567890abcdef12345678",
        "depth": 1,
        "inherited_operation_count": 2,
        "new_operation_count": 2,
        "effective_operation_count": 3,
    }
    assert revised["official_baseline"] == parent["official_baseline"]
    assert revised["approval"]["derived_style_approval"] == "pending-human-approval"
    assert parent == parent_before


def test_revision_rejects_unapproved_parent_and_baseline_changes() -> None:
    engine = PortrayalReviewEngine.load(RECIPES)
    evidence = package("小學 9920103 圖式")
    edit = plan("9920103", "Point", "set_color", "marker", {"color": "#1565c0"})
    parent = engine.propose(edit, evidence)
    child = engine.propose(edit, evidence)

    with pytest.raises(PortrayalReviewError, match="approved preview"):
        merge_portrayal_revision(parent, child, parent_proposal_id="portrayal_parent")
    parent["approval"]["derived_style_approval"] = "approved-for-preview"
    child["official_baseline"]["page"] = 999
    with pytest.raises(PortrayalReviewError, match="official baseline"):
        merge_portrayal_revision(parent, child, parent_proposal_id="portrayal_parent")

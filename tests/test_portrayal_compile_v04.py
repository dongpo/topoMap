from pathlib import Path

import pytest

from nma.graphrag import CanonicalGraphRetriever
from nma.portrayal_compile import compile_portrayal_preview
from nma.portrayal_review import PortrayalReviewEngine, PortrayalReviewError


ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data/knowledge/nma-canonical-graph-v0.4.json"
RECIPES = (
    ROOT / "data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json"
)


def approved_proposal(
    *, code: str, query: str, geometry: str, action: str, target: str, value: dict
) -> dict:
    plan = {
        "schema": "nma.portrayal-edit-plan/0.4",
        "source": "deterministic-test",
        "feature_code": code,
        "geometry_role": geometry,
        "operations": [{"action": action, "target": target, "value": value}],
    }
    evidence = CanonicalGraphRetriever.load(GRAPH).evidence_package(
        query, max_depth=3, max_nodes=40
    )
    proposal = PortrayalReviewEngine.load(RECIPES).propose(plan, evidence)
    proposal["approval"]["derived_style_approval"] = "approved-for-preview"
    return proposal


@pytest.mark.parametrize(
    ("proposal", "channel", "property_name", "expected"),
    [
        (
            approved_proposal(
                code="9350906",
                query="消防栓 9350906 圖式",
                geometry="Point",
                action="set_color",
                target="marker",
                value={"color": "#1565c0"},
            ),
            "marker",
            "color",
            "#1565c0",
        ),
        (
            approved_proposal(
                code="9420801",
                query="一般市區道路 9420801 圖式",
                geometry="LineString",
                action="set_line_pattern",
                target="stroke",
                value={"pattern": "dash"},
            ),
            "stroke",
            "pattern",
            "dash",
        ),
        (
            approved_proposal(
                code="9740100",
                query="養殖池 9740100 圖式",
                geometry="Polygon",
                action="set_scale",
                target="interior-marker",
                value={"number": 1.2},
            ),
            "interior-marker",
            "scale",
            1.2,
        ),
        (
            approved_proposal(
                code="9310100",
                query="永久性建物 9310100 圖式",
                geometry="Polygon",
                action="set_hatch_spacing",
                target="hatch",
                value={"number": 2.5},
            ),
            "hatch",
            "spacing_mm",
            2.5,
        ),
    ],
)
def test_compiler_produces_safe_point_line_polygon_preview_observations(
    proposal, channel, property_name, expected
) -> None:
    observation = compile_portrayal_preview(proposal)

    assert observation["status"] == "compiled-for-review"
    assert observation["render_ir"]["channels"][channel][property_name] == expected
    assert observation["render_ir"]["raw_svg_or_code"] is None
    assert observation["official_baseline"]["immutable"] is True
    assert observation["activation_gates"]
    assert observation["map_layer_created"] is False
    assert observation["preview_only"] is True
    assert observation["automatic_action"] is False


def test_compiler_requires_explicit_preview_approval() -> None:
    proposal = approved_proposal(
        code="9920103",
        query="小學 9920103 圖式",
        geometry="Point",
        action="set_rotation",
        target="marker",
        value={"number": 10},
    )
    proposal["approval"]["derived_style_approval"] = "pending-human-approval"

    with pytest.raises(PortrayalReviewError, match="not approved"):
        compile_portrayal_preview(proposal)

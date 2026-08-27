from __future__ import annotations

from copy import deepcopy
from typing import Any

from nma.portrayal_review import PortrayalReviewError


OBSERVED_COLORS = {
    "black": "#111111",
    "red": "#c62828",
    "blue": "#1565c0",
    "white": "#ffffff",
}


def _has_type(primitives: list[dict[str, Any]], *types: str) -> bool:
    return any(item.get("type") in types for item in primitives)


def _base_channels(baseline: dict[str, Any]) -> dict[str, dict[str, Any]]:
    geometry = baseline["geometry_role"]
    primitives = baseline["primitives"]
    constraints = baseline["source_constraints"]
    color = OBSERVED_COLORS.get(constraints.get("observed_color"), "#111111")
    text_enabled = _has_type(primitives, "text-annotation")
    common = {"color": color, "opacity": 1.0}
    if geometry == "Point":
        return {
            "marker": {**common, "enabled": True, "scale": 1.0, "rotation": 0.0},
            "stroke": {**common, "enabled": True, "width": None, "pattern": "solid"},
            "outline": {**common, "enabled": _has_type(primitives, "rect"), "width": None},
            "text": {**common, "enabled": text_enabled, "visible": text_enabled},
        }
    if geometry == "LineString":
        return {
            "stroke": {**common, "enabled": True, "width": None, "pattern": "solid"},
            "outline": {**common, "enabled": False, "width": None, "pattern": "solid"},
            "text": {**common, "enabled": text_enabled, "visible": text_enabled},
        }
    if geometry == "Polygon":
        hatch = _has_type(primitives, "hatch-fill")
        interior_marker = _has_type(primitives, "svg-marker")
        spacing = constraints.get("component_dimensions_mm", {}).get("hatch_spacing")
        return {
            "fill": {
                **common,
                "enabled": hatch,
                "pattern": "hatch" if hatch else "none",
            },
            "stroke": {**common, "enabled": True, "width": None, "pattern": "solid"},
            "outline": {**common, "enabled": True, "width": None, "pattern": "solid"},
            "hatch": {
                **common,
                "enabled": hatch,
                "spacing_mm": spacing,
                "rotation": None,
            },
            "interior-marker": {
                **common,
                "enabled": interior_marker,
                "scale": 1.0,
                "rotation": 0.0,
            },
            "text": {**common, "enabled": text_enabled, "visible": text_enabled},
        }
    raise PortrayalReviewError("The preview geometry role is unsupported.")


def _targets(channels: dict[str, dict[str, Any]], target: str) -> list[dict[str, Any]]:
    if target == "portrayal":
        return list(channels.values())
    channel = channels.get(target)
    if channel is None:
        raise PortrayalReviewError("The approved target has no preview channel.")
    return [channel]


def compile_portrayal_preview(proposal: Any) -> dict[str, Any]:
    if not isinstance(proposal, dict) or proposal.get("schema") != (
        "nma.portrayal-review-proposal/0.4"
    ):
        raise PortrayalReviewError("A valid portrayal review proposal is required.")
    if proposal.get("approval", {}).get("derived_style_approval") != "approved-for-preview":
        raise PortrayalReviewError("The derived style is not approved for preview.")
    baseline = proposal.get("official_baseline", {})
    if baseline.get("immutable") is not True:
        raise PortrayalReviewError("The official portrayal baseline is not immutable.")
    preview = proposal.get("derived_preview_ir", {})
    if preview.get("raw_svg_or_code_allowed") is not False:
        raise PortrayalReviewError("The preview IR raw-code boundary is invalid.")
    channels = _base_channels(baseline)
    structure = (
        {
            "flag_top_alignment": "offset",
            "support": {
                "enabled": False,
                "shape": None,
                "width_relation": "independent",
            },
            "flagpole_attachment": "detached",
            "flagpole_horizontal_alignment": "edge",
        }
        if proposal.get("feature", {}).get("code") == "9920103"
        else None
    )
    applied: list[dict[str, Any]] = []
    for operation in preview.get("overrides", []):
        action = operation.get("action")
        target = operation.get("target")
        value = operation.get("value", {})
        selected = [] if action in {
            "align",
            "add_shape",
            "remove_shape",
            "match_dimension",
            "attach",
            "detach",
            "center",
        } else _targets(channels, target)
        if action == "set_color":
            for channel in selected:
                channel["color"] = value["color"]
        elif action == "set_opacity":
            for channel in selected:
                channel["opacity"] = value["number"]
        elif action == "set_stroke_width":
            for channel in selected:
                channel["width"] = value["number"]
        elif action == "set_scale":
            for channel in selected:
                channel["scale"] = value["number"]
        elif action == "set_rotation":
            for channel in selected:
                channel["rotation"] = value["number"]
        elif action in {"set_fill_pattern", "set_line_pattern"}:
            for channel in selected:
                channel["pattern"] = value["pattern"]
                channel["enabled"] = value["pattern"] != "none"
        elif action == "set_hatch_spacing":
            for channel in selected:
                channel["spacing_mm"] = value["number"]
        elif action == "set_text_visibility":
            for channel in selected:
                channel["visible"] = value["boolean"]
                channel["enabled"] = value["boolean"]
        elif structure is not None and action == "align":
            structure["flag_top_alignment"] = value["relation"]
        elif structure is not None and action == "add_shape":
            structure["support"]["enabled"] = True
            structure["support"]["shape"] = value["shape"]
        elif structure is not None and action == "remove_shape":
            structure["support"]["enabled"] = False
            structure["support"]["shape"] = None
        elif structure is not None and action == "match_dimension":
            structure["support"]["width_relation"] = value["relation"]
        elif structure is not None and action == "attach":
            structure["flagpole_attachment"] = value["relation"]
        elif structure is not None and action == "detach":
            structure["flagpole_attachment"] = value["relation"]
        elif structure is not None and action == "center":
            structure["flagpole_horizontal_alignment"] = value["relation"]
        else:
            raise PortrayalReviewError("The approved preview operation is unsupported.")
        applied.append(deepcopy(operation))
    gates = deepcopy(proposal["validation"].get("activation_gates", []))
    return {
        "schema": "nma.portrayal-preview-observation/0.4",
        "status": "compiled-for-review",
        "feature": deepcopy(proposal["feature"]),
        "official_baseline": {
            "source_rule_id": baseline["source_rule_id"],
            "evidence_section_id": baseline["evidence_section_id"],
            "page": baseline["page"],
            "immutable": True,
        },
        "render_ir": {
            "schema": "nma.safe-render-ir/0.4",
            "geometry_role": proposal["feature"]["geometry_role"],
            "representation_kind": proposal["feature"]["representation_kind"],
            "primitive_ids": deepcopy(preview["baseline_primitive_ids"]),
            "review_asset": deepcopy(baseline.get("review_asset")),
            "channels": channels,
            "structure": structure,
            "applied_overrides": applied,
            "raw_svg_or_code": None,
        },
        "runtime_requirements": deepcopy(baseline.get("runtime_requirements", [])),
        "runtime_evidence": deepcopy(baseline.get("runtime_evidence")),
        "activation_gates": gates,
        "official_rule_activation": "blocked-until-all-activation-gates-resolved",
        "map_layer_created": False,
        "preview_only": True,
        "automatic_action": False,
    }

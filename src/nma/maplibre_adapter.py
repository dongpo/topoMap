from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from nma.portrayal_review import PortrayalReviewError


IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,100}$")
FIELD = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
GEOMETRY_COMPATIBILITY = {
    "Point": {"Point"},
    "LineString": {"LineString", "Polygon"},
    "Polygon": {"Polygon"},
}


def validate_source_binding(binding: Any, *, feature: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema",
        "source",
        "source_layer",
        "source_geometry_type",
        "feature_code_field",
        "feature_code",
        "label_field",
    }
    if not isinstance(binding, dict) or set(binding) != required:
        raise PortrayalReviewError("The MapLibre source binding has an invalid shape.")
    if binding["schema"] != "nma.maplibre-source-binding/0.4":
        raise PortrayalReviewError("The MapLibre source binding schema is unsupported.")
    for key in ("source", "source_layer"):
        if not isinstance(binding[key], str) or not IDENTIFIER.fullmatch(binding[key]):
            raise PortrayalReviewError(f"The MapLibre {key} identifier is invalid.")
    source_geometry = binding["source_geometry_type"]
    portrayal_geometry = feature["geometry_role"]
    if source_geometry not in GEOMETRY_COMPATIBILITY.get(portrayal_geometry, set()):
        raise PortrayalReviewError("The source geometry is incompatible with the portrayal.")
    for key in ("feature_code_field", "label_field"):
        value = binding[key]
        if value is not None and (not isinstance(value, str) or not FIELD.fullmatch(value)):
            raise PortrayalReviewError(f"The MapLibre {key} is invalid.")
    if binding["feature_code"] != feature["code"]:
        raise PortrayalReviewError("The source binding feature code does not match the proposal.")
    if binding["feature_code_field"] is None:
        raise PortrayalReviewError("A reviewed feature-code field binding is required.")
    return deepcopy(binding)


def _feature_filter(binding: dict[str, Any]) -> list[Any]:
    return [
        "==",
        ["to-string", ["get", binding["feature_code_field"]]],
        binding["feature_code"],
    ]


def _line_dash(pattern: str) -> list[float] | None:
    return {"solid": None, "dash": [3.0, 2.0], "dot": [1.0, 2.0]}[pattern]


def _asset_resource(
    *, feature_code: str, role: str, asset: dict[str, Any] | None, sdf: bool
) -> dict[str, Any]:
    if not asset or not isinstance(asset.get("path"), str):
        raise PortrayalReviewError(f"The {role} preview requires a reviewed local asset.")
    path = asset["path"]
    if path.startswith("/") or ".." in path.split("/") or not path.endswith(".svg"):
        raise PortrayalReviewError("The reviewed preview asset path is unsafe.")
    return {
        "id": f"nma-{feature_code}-{role}",
        "kind": "local-svg-image",
        "path": path,
        "sdf": sdf,
        "review_status": asset.get("status"),
        "preview_color_is_authoritative": asset.get(
            "preview_color_is_authoritative", False
        ),
    }


def compile_maplibre_preview(
    observation: Any, source_binding: Any
) -> dict[str, Any]:
    if not isinstance(observation, dict) or observation.get("schema") != (
        "nma.portrayal-preview-observation/0.4"
    ):
        raise PortrayalReviewError("A compiled portrayal preview observation is required.")
    if observation.get("status") != "compiled-for-review" or not observation.get("preview_only"):
        raise PortrayalReviewError("The portrayal observation is not a review preview.")
    binding = validate_source_binding(source_binding, feature=observation["feature"])
    render_ir = observation["render_ir"]
    geometry = render_ir["geometry_role"]
    channels = render_ir["channels"]
    code = observation["feature"]["code"]
    base = {
        "source": binding["source"],
        "source-layer": binding["source_layer"],
        "filter": _feature_filter(binding),
    }
    layers: list[dict[str, Any]] = []
    resources: list[dict[str, Any]] = []
    if geometry == "Point":
        marker = channels["marker"]
        resource = _asset_resource(
            feature_code=code,
            role="marker",
            asset=render_ir.get("review_asset"),
            sdf=True,
        )
        resources.append(resource)
        layout: dict[str, Any] = {
            "icon-image": resource["id"],
            "icon-size": marker["scale"],
            "icon-rotate": marker["rotation"],
            "icon-allow-overlap": False,
        }
        text = channels["text"]
        if text["enabled"] and binding["label_field"]:
            layout.update(
                {
                    "text-field": ["to-string", ["get", binding["label_field"]]],
                    "text-offset": [0, 1.4],
                    "text-optional": True,
                }
            )
        layers.append(
            {
                "id": f"nma-preview-{code}-marker",
                "type": "symbol",
                **base,
                "layout": layout,
                "paint": {
                    "icon-color": marker["color"],
                    "icon-opacity": marker["opacity"],
                    "text-color": text["color"],
                    "text-opacity": text["opacity"] if text["enabled"] else 0,
                },
            }
        )
    elif geometry == "LineString":
        stroke = channels["stroke"]
        paint: dict[str, Any] = {
            "line-color": stroke["color"],
            "line-opacity": stroke["opacity"],
            "line-width": stroke["width"] or 1.0,
        }
        dash = _line_dash(stroke["pattern"])
        if dash:
            paint["line-dasharray"] = dash
        layers.append(
            {
                "id": f"nma-preview-{code}-stroke",
                "type": "line",
                **base,
                "layout": {"line-cap": "round", "line-join": "round"},
                "paint": paint,
            }
        )
        text = channels["text"]
        if text["enabled"] and binding["label_field"]:
            layers.append(
                {
                    "id": f"nma-preview-{code}-label",
                    "type": "symbol",
                    **base,
                    "layout": {
                        "symbol-placement": "line",
                        "text-field": ["to-string", ["get", binding["label_field"]]],
                    },
                    "paint": {
                        "text-color": text["color"],
                        "text-opacity": text["opacity"],
                    },
                }
            )
    elif geometry == "Polygon":
        fill = channels["fill"]
        hatch = channels["hatch"]
        if hatch["enabled"]:
            resource = _asset_resource(
                feature_code=code,
                role="hatch",
                asset=render_ir.get("review_asset"),
                sdf=False,
            )
            resource["spacing_mm"] = hatch["spacing_mm"]
            resources.append(resource)
            layers.append(
                {
                    "id": f"nma-preview-{code}-hatch",
                    "type": "fill",
                    **base,
                    "paint": {
                        "fill-pattern": resource["id"],
                        "fill-opacity": hatch["opacity"],
                    },
                }
            )
        elif fill["enabled"]:
            layers.append(
                {
                    "id": f"nma-preview-{code}-fill",
                    "type": "fill",
                    **base,
                    "paint": {
                        "fill-color": fill["color"],
                        "fill-opacity": fill["opacity"],
                    },
                }
            )
        outline = channels["outline"]
        layers.append(
            {
                "id": f"nma-preview-{code}-outline",
                "type": "line",
                **base,
                "paint": {
                    "line-color": outline["color"],
                    "line-opacity": outline["opacity"],
                    "line-width": outline["width"] or 1.0,
                },
            }
        )
        interior = channels["interior-marker"]
        if interior["enabled"]:
            resource = _asset_resource(
                feature_code=code,
                role="interior-marker",
                asset=render_ir.get("review_asset"),
                sdf=True,
            )
            resources.append(resource)
            layers.append(
                {
                    "id": f"nma-preview-{code}-interior-marker",
                    "type": "symbol",
                    **base,
                    "layout": {
                        "icon-image": resource["id"],
                        "icon-size": interior["scale"],
                        "icon-rotate": interior["rotation"],
                    },
                    "paint": {
                        "icon-color": interior["color"],
                        "icon-opacity": interior["opacity"],
                    },
                }
            )
    else:
        raise PortrayalReviewError("The MapLibre portrayal geometry is unsupported.")
    return {
        "schema": "nma.maplibre-preview-adapter-result/0.4",
        "status": "adapter-ready-for-preview",
        "feature": deepcopy(observation["feature"]),
        "source_binding": binding,
        "resources": resources,
        "layers": layers,
        "activation_gates": deepcopy(observation["activation_gates"]),
        "official_rule_activation": observation["official_rule_activation"],
        "preview_only": True,
        "map_mutation_performed": False,
        "automatic_action": False,
    }

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any


PLAN_SCHEMA = "nma.portrayal-edit-plan/0.4"
PROPOSAL_SCHEMA = "nma.portrayal-review-proposal/0.4"
FEATURE_CODE_PATTERN = re.compile(r"^[0-9A-Za-z._-]{1,32}$")
COLORS = {
    "#111111",
    "#ffffff",
    "#c62828",
    "#1565c0",
    "#2e7d32",
    "#f9a825",
    "#ef6c00",
    "#6d7772",
    "#6a1b9a",
}
GEOMETRY_TARGETS = {
    "Point": {
        "portrayal",
        "marker",
        "stroke",
        "outline",
        "text",
        "flag-top",
        "support",
        "flagpole-bottom",
    },
    "LineString": {"portrayal", "stroke", "outline", "text"},
    "Polygon": {
        "portrayal",
        "interior-marker",
        "stroke",
        "fill",
        "outline",
        "hatch",
        "text",
    },
}
ACTION_TARGETS = {
    "set_color": {
        "portrayal",
        "marker",
        "interior-marker",
        "stroke",
        "fill",
        "outline",
        "hatch",
        "text",
    },
    "set_opacity": {
        "portrayal",
        "marker",
        "interior-marker",
        "stroke",
        "fill",
        "outline",
        "hatch",
        "text",
    },
    "set_stroke_width": {"marker", "interior-marker", "stroke", "outline", "hatch"},
    "set_scale": {"portrayal", "marker", "interior-marker"},
    "set_rotation": {"marker", "interior-marker", "hatch", "text"},
    "set_fill_pattern": {"fill"},
    "set_line_pattern": {"stroke", "outline"},
    "set_hatch_spacing": {"hatch"},
    "set_text_visibility": {"text"},
    "align": {"flag-top"},
    "add_shape": {"support"},
    "remove_shape": {"support"},
    "match_dimension": {"support"},
    "attach": {"flagpole-bottom"},
    "detach": {"flagpole-bottom"},
    "center": {"flagpole-bottom"},
}
ACTION_VALUE_KEYS = {
    "set_color": ("color",),
    "set_opacity": ("number",),
    "set_stroke_width": ("number",),
    "set_scale": ("number",),
    "set_rotation": ("number",),
    "set_fill_pattern": ("pattern",),
    "set_line_pattern": ("pattern",),
    "set_hatch_spacing": ("number",),
    "set_text_visibility": ("boolean",),
    "align": ("reference", "relation"),
    "add_shape": ("shape",),
    "remove_shape": ("shape",),
    "match_dimension": ("reference", "relation"),
    "attach": ("reference", "relation"),
    "detach": ("reference", "relation"),
    "center": ("reference", "relation"),
}
NUMERIC_BOUNDS = {
    "set_opacity": (0.1, 1.0),
    "set_stroke_width": (0.1, 8.0),
    "set_scale": (0.5, 3.0),
    "set_rotation": (-180.0, 180.0),
    "set_hatch_spacing": (0.5, 10.0),
}
PATTERNS = {
    "set_fill_pattern": {"solid", "hatch", "none"},
    "set_line_pattern": {"solid", "dash", "dot"},
}
STRUCTURAL_ACTIONS = {
    "align",
    "add_shape",
    "remove_shape",
    "match_dimension",
    "attach",
    "detach",
    "center",
}
STRUCTURAL_FEATURES = {"9920103"}
STRUCTURAL_VALUES = {
    "align": {"reference": {"flagpole-top"}, "relation": {"aligned", "offset"}},
    "add_shape": {"shape": {"rectangle"}},
    "remove_shape": {"shape": {"none"}},
    "match_dimension": {
        "reference": {"flag"},
        "relation": {"same-width", "proportional-width"},
    },
    "attach": {
        "reference": {"support-top"},
        "relation": {"inserted-into-top"},
    },
    "detach": {"reference": {"support-top"}, "relation": {"detached"}},
    "center": {"reference": {"support"}, "relation": {"centered"}},
}


class PortrayalReviewError(ValueError):
    """A proposed portrayal edit violated evidence or geometry boundaries."""


def validate_portrayal_edit_plan(plan: Any) -> dict[str, Any]:
    required = {"schema", "source", "feature_code", "geometry_role", "operations"}
    if not isinstance(plan, dict) or set(plan) != required:
        raise PortrayalReviewError("The portrayal edit plan has an invalid shape.")
    if plan["schema"] != PLAN_SCHEMA:
        raise PortrayalReviewError("The portrayal edit plan schema is unsupported.")
    if plan["source"] not in {"responses-api", "user-supervised", "deterministic-test"}:
        raise PortrayalReviewError("The portrayal edit plan source is unsupported.")
    if not isinstance(plan["feature_code"], str) or not FEATURE_CODE_PATTERN.fullmatch(
        plan["feature_code"]
    ):
        raise PortrayalReviewError("The feature code is invalid.")
    geometry = plan["geometry_role"]
    if geometry not in GEOMETRY_TARGETS:
        raise PortrayalReviewError("The geometry role is unsupported.")
    operations = plan["operations"]
    if not isinstance(operations, list) or not 1 <= len(operations) <= 12:
        raise PortrayalReviewError("The portrayal edit plan must contain 1–12 operations.")
    seen: set[tuple[str, str]] = set()
    for operation in operations:
        if not isinstance(operation, dict) or set(operation) != {"action", "target", "value"}:
            raise PortrayalReviewError("A portrayal edit operation has an invalid shape.")
        action = operation["action"]
        target = operation["target"]
        value = operation["value"]
        if action not in ACTION_TARGETS or target not in ACTION_TARGETS[action]:
            raise PortrayalReviewError("The action cannot be applied to the requested target.")
        if target not in GEOMETRY_TARGETS[geometry]:
            raise PortrayalReviewError("The target is incompatible with the feature geometry.")
        if (action, target) in seen:
            raise PortrayalReviewError("Duplicate action and target pairs are not allowed.")
        seen.add((action, target))
        expected_keys = ACTION_VALUE_KEYS[action]
        if not isinstance(value, dict) or set(value) != set(expected_keys):
            raise PortrayalReviewError("The operation value does not match its action.")
        if action in STRUCTURAL_ACTIONS:
            if plan["feature_code"] not in STRUCTURAL_FEATURES:
                raise PortrayalReviewError(
                    "Structural symbol editing is not reviewed for this feature."
                )
            allowed = STRUCTURAL_VALUES[action]
            if any(value[key] not in allowed[key] for key in expected_keys):
                raise PortrayalReviewError("The structural portrayal relation is unsupported.")
            continue
        expected_key = expected_keys[0]
        actual = value[expected_key]
        if expected_key == "color" and actual not in COLORS:
            raise PortrayalReviewError("The requested colour is outside the approved palette.")
        if expected_key == "boolean" and not isinstance(actual, bool):
            raise PortrayalReviewError("The text visibility value must be boolean.")
        if expected_key == "pattern" and actual not in PATTERNS[action]:
            raise PortrayalReviewError("The requested pattern is unsupported for this action.")
        if action in NUMERIC_BOUNDS:
            low, high = NUMERIC_BOUNDS[action]
            if isinstance(actual, bool) or not isinstance(actual, (int, float)):
                raise PortrayalReviewError("The operation requires a numeric value.")
            if not low <= actual <= high:
                raise PortrayalReviewError("The numeric portrayal value is out of bounds.")
    return deepcopy(plan)


class PortrayalReviewEngine:
    """Compile evidence-bound, non-authoritative portrayal review proposals."""

    def __init__(self, corpus: dict[str, Any]):
        self.corpus = corpus
        self.recipes = {item["feature_code"]: item for item in corpus["recipes"]}

    @classmethod
    def load(cls, path: str | Path) -> "PortrayalReviewEngine":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def baseline(self, feature_code: str) -> dict[str, Any]:
        recipe = self.recipes.get(feature_code)
        if recipe is None:
            raise PortrayalReviewError("No reviewed portrayal recipe exists for this feature.")
        return deepcopy(recipe)

    def propose(
        self, plan: Any, evidence_package: dict[str, Any]
    ) -> dict[str, Any]:
        checked = validate_portrayal_edit_plan(plan)
        recipe = self.baseline(checked["feature_code"])
        if checked["geometry_role"] != recipe["geometry_role"]:
            raise PortrayalReviewError("The edit plan geometry does not match the reviewed recipe.")
        self._validate_evidence(recipe, evidence_package)
        citations = [
            deepcopy(item)
            for item in evidence_package.get("citations", [])
            if item.get("page") == recipe["page"]
        ]
        gates = deepcopy(recipe.get("activation_gates", []))
        return {
            "schema": PROPOSAL_SCHEMA,
            "status": "review-proposal-non-executable",
            "feature": {
                "code": recipe["feature_code"],
                "name": recipe["feature_name"],
                "geometry_role": recipe["geometry_role"],
                "representation_kind": recipe["representation_kind"],
            },
            "official_baseline": {
                "immutable": True,
                "source_rule_id": recipe["source_rule_id"],
                "evidence_section_id": recipe["evidence_section_id"],
                "page": recipe["page"],
                "geometry_role": recipe["geometry_role"],
                "representation_kind": recipe["representation_kind"],
                "source_constraints": deepcopy(recipe["source_constraints"]),
                "primitives": deepcopy(recipe["primitives"]),
                "review_asset": deepcopy(recipe.get("review_asset")),
                "runtime_requirements": deepcopy(recipe["runtime_requirements"]),
                "runtime_evidence": deepcopy(recipe.get("runtime_evidence")),
            },
            "derived_preview_ir": {
                "schema": "nma.portrayal-preview-ir/0.4",
                "geometry_role": recipe["geometry_role"],
                "representation_kind": recipe["representation_kind"],
                "baseline_primitive_ids": [item["id"] for item in recipe["primitives"]],
                "overrides": [
                    {**deepcopy(operation), "authority": "user-preference"}
                    for operation in checked["operations"]
                ],
                "raw_svg_or_code_allowed": False,
            },
            "evidence": {
                "package_schema": evidence_package.get("schema"),
                "resolved_entity_ids": [
                    item["id"] for item in evidence_package.get("resolved_entities", [])
                ],
                "evidence_node_ids": [
                    item["id"] for item in evidence_package.get("evidence_nodes", [])
                ],
                "citations": citations,
            },
            "validation": {
                "evidence_bound": True,
                "official_baseline_immutable": True,
                "geometry_compatible": True,
                "operation_count": len(checked["operations"]),
                "activation_gates": gates,
            },
            "approval": {
                "derived_style_approval": "pending-human-approval",
                "official_rule_activation": "blocked-until-all-activation-gates-resolved",
            },
            "automatic_action": False,
        }

    @staticmethod
    def _validate_evidence(recipe: dict[str, Any], package: dict[str, Any]) -> None:
        if package.get("status") != "retrieved":
            raise PortrayalReviewError("A retrieved evidence package is required.")
        node_ids = {
            item.get("id") for item in package.get("evidence_nodes", []) if isinstance(item, dict)
        }
        if recipe["source_rule_id"] not in node_ids:
            raise PortrayalReviewError("The reviewed source rule is absent from the evidence package.")
        citations = package.get("citations", [])
        if not any(
            item.get("page") == recipe["page"]
            and item.get("section_id") == recipe["evidence_section_id"]
            for item in citations
            if isinstance(item, dict)
        ):
            raise PortrayalReviewError("The reviewed source page is absent from the evidence package.")
        if package.get("automatic_rule_activation") is not False:
            raise PortrayalReviewError("The evidence package activation boundary is invalid.")


def merge_portrayal_revision(
    parent: Any,
    child: Any,
    *,
    parent_proposal_id: str,
) -> dict[str, Any]:
    """Carry approved preferences into a child without changing the official baseline."""

    if not isinstance(parent, dict) or not isinstance(child, dict):
        raise PortrayalReviewError("Parent and child portrayal proposals are required.")
    if parent.get("approval", {}).get("derived_style_approval") != "approved-for-preview":
        raise PortrayalReviewError("Only an approved preview proposal can be revised.")
    if parent.get("feature") != child.get("feature"):
        raise PortrayalReviewError("A portrayal revision cannot change the selected feature.")
    if parent.get("official_baseline") != child.get("official_baseline"):
        raise PortrayalReviewError("A portrayal revision cannot change the official baseline.")
    parent_ir = parent.get("derived_preview_ir", {})
    child_ir = child.get("derived_preview_ir", {})
    if parent_ir.get("schema") != child_ir.get("schema"):
        raise PortrayalReviewError("The portrayal revision IR schemas do not match.")
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    for operation in [*parent_ir.get("overrides", []), *child_ir.get("overrides", [])]:
        key = (operation.get("action"), operation.get("target"))
        if not all(isinstance(item, str) for item in key):
            raise PortrayalReviewError("A portrayal revision operation has no stable identity.")
        if key not in merged:
            order.append(key)
        merged[key] = deepcopy(operation)
    revised = deepcopy(child)
    revised["derived_preview_ir"]["overrides"] = [merged[key] for key in order]
    parent_revision = parent.get("revision", {})
    revised["revision"] = {
        "parent_proposal_id": parent_proposal_id,
        "depth": int(parent_revision.get("depth", 0)) + 1,
        "inherited_operation_count": len(parent_ir.get("overrides", [])),
        "new_operation_count": len(child_ir.get("overrides", [])),
        "effective_operation_count": len(merged),
    }
    revised["approval"]["derived_style_approval"] = "pending-human-approval"
    revised["automatic_action"] = False
    return revised

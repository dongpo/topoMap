from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from nma.core import canonical_sha256
from nma.readonly_knowledge_service import KnowledgeServiceGraphRetriever


DATASET_OBSERVATION_SCHEMA = "nma.build-dataset-observation/1.0"
PLAN_SCHEMA = "nma.build-portrayal-plan/1.0"
AUTHORIZATION_SCHEMA = "nma.build-portrayal-authorization/1.0"
ADAPTER_RESULT_SCHEMA = "nma.build-maplibre-adapter-result/1.0"
TOOL_OBSERVATION_SCHEMA = "nma.build-portrayal-tool-observation/1.0"
AGENT_DECISION_SCHEMA = "nma.build-portrayal-agent-decision/1.0"
QA_SCHEMA = "nma.build-portrayal-qa/1.0"

BUILD_ROOT_CODE = "9310000"
BUILD_PARENT_CODES = {"9310000": ("9310100", "9310200", "9310300")}
BUILD_PORTRAYAL_CODES = ("9310100", "9310103", "9310200", "9310300")
BUILD_NAMES = {
    "9310100": "永久性建物（建築區）",
    "9310103": "無牆建物",
    "9310200": "建築中建物",
    "9310300": "臨時性建物",
}
ANNEX7_CODES = {"9310100", "9310200", "9310300"}
EXPECTED_GEOMETRY_CLASSES = {
    "9310100": ["2", "3", "5"],
    "9310103": ["2", "3", "4"],
    "9310200": ["2", "3", "4"],
    "9310300": ["2", "3", "4"],
}
REVIEWED_FIELDS = [
    "BUILD_ID",
    "TERRAINID",
    "BUILD_STR",
    "BUILD_NO",
    "BUILD_H",
    "GROUP_ID",
    "MDATE",
]
SAFE_ACTOR = re.compile(r"^[A-Za-z0-9._:@-]{1,120}$")


class BuildPortrayalError(ValueError):
    """A BUILD portrayal request crossed an evidence or governance boundary."""


def _without_hash(value: dict[str, Any], field: str) -> dict[str, Any]:
    return {key: deepcopy(item) for key, item in value.items() if key != field}


def _hashed(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result[field] = canonical_sha256(result)
    return result


def _validate_hash(value: dict[str, Any], field: str) -> None:
    if value.get(field) != canonical_sha256(_without_hash(value, field)):
        raise BuildPortrayalError(f"The {field} identity is invalid.")


def _node(package: dict[str, Any], node_id: str) -> dict[str, Any]:
    matches = [item for item in package.get("evidence_nodes", []) if item.get("id") == node_id]
    if len(matches) != 1:
        raise BuildPortrayalError(f"Required Knowledge Graph node is unavailable: {node_id}.")
    return matches[0]


def _optional_node(package: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    matches = [item for item in package.get("evidence_nodes", []) if item.get("id") == node_id]
    if len(matches) > 1:
        raise BuildPortrayalError(f"Knowledge Graph node is ambiguous: {node_id}.")
    return matches[0] if matches else None


def _edge_targets(package: dict[str, Any], source: str, relationship_type: str) -> list[str]:
    return sorted(
        {
            item["target"]
            for item in package.get("graph_paths", {}).get("edges", [])
            if item.get("source") == source and item.get("type") == relationship_type
        }
    )


def _citation(package: dict[str, Any], section_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in package.get("citations", [])
        if isinstance(item, dict) and item.get("section_id") == section_id
    ]
    if len(matches) != 1:
        raise BuildPortrayalError(f"Required source citation is unavailable: {section_id}.")
    citation = matches[0]
    if (
        citation.get("citation_integrity") != "verified-unique-document-containment"
        or not citation.get("source_sha256")
        or not citation.get("filename")
    ):
        raise BuildPortrayalError(f"Source citation integrity failed: {section_id}.")
    return deepcopy(citation)


def _bounded_knowledge_trace(trace: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "contract",
        "operation",
        "operation_registry_version",
        "active_backend",
        "graph_revision",
        "canonical_graph_sha256",
        "graph_identity_verified",
        "read_transaction_calls",
        "incident_edges_scanned",
        "credential_scope_required",
        "driver_access_mode",
        "typed_operations_only",
        "arbitrary_cypher_allowed",
        "mutation_allowed",
        "automatic_rule_activation",
        "autonomous_canonical_kg_modification",
    )
    return {key: deepcopy(trace.get(key)) for key in keys}


def validate_build_dataset_observation(value: Any) -> dict[str, Any]:
    required = {
        "schema",
        "goal",
        "source",
        "source_layer",
        "geometry_family",
        "schema_profile",
        "classification_field",
        "identity_field",
        "annotation_fields",
        "observed_class_counts",
        "classification_resolutions",
        "feature_count",
        "total_vertex_count",
        "total_ring_count",
        "multipart_feature_count",
        "z_feature_count",
        "source_identity_rule",
        "raw_feature_bytes_transmitted",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise BuildPortrayalError("The BUILD dataset observation has an invalid shape.")
    if value["schema"] != DATASET_OBSERVATION_SCHEMA:
        raise BuildPortrayalError("The BUILD dataset observation schema is unsupported.")
    if not isinstance(value["goal"], str) or not 1 <= len(value["goal"].strip()) <= 500:
        raise BuildPortrayalError("The BUILD goal is invalid.")
    if value["source"] != "user-shapefile" or value["source_layer"] != "BUILD":
        raise BuildPortrayalError("BUILD portrayal requires a user BUILD Shapefile layer.")
    if value["geometry_family"] != "polygon":
        raise BuildPortrayalError("BUILD portrayal requires Polygon or MultiPolygon geometry.")
    profile = value["schema_profile"]
    if not isinstance(profile, dict) or set(profile) != {"id", "status", "fields"}:
        raise BuildPortrayalError("The BUILD schema profile is invalid.")
    if (
        profile["id"] != "multidimensional-build-v4"
        or profile["status"] != "reviewed-versioned-source-schema"
        or profile["fields"] != REVIEWED_FIELDS
    ):
        raise BuildPortrayalError("The BUILD schema profile is not reviewed for this adapter.")
    if value["classification_field"] != "TERRAINID":
        raise BuildPortrayalError(
            "BUILD portrayal requires the reviewed TERRAINID classification field."
        )
    if value["identity_field"] != "BUILD_ID":
        raise BuildPortrayalError("BUILD portrayal requires BUILD_ID.")
    if value["annotation_fields"] != ["BUILD_NO", "BUILD_STR"]:
        raise BuildPortrayalError("BUILD annotation requires BUILD_NO followed by BUILD_STR.")
    if value["source_identity_rule"] != "zip-relative-filename-plus-source-id":
        raise BuildPortrayalError("The BUILD source identity rule is unsupported.")
    if value["raw_feature_bytes_transmitted"] is not False:
        raise BuildPortrayalError("This demo contract cannot transmit raw feature bytes.")
    for name in ("feature_count", "total_vertex_count", "total_ring_count"):
        if type(value[name]) is not int or value[name] < 1:
            raise BuildPortrayalError(f"BUILD {name} must be positive.")
    for name in ("multipart_feature_count", "z_feature_count"):
        if type(value[name]) is not int or not 0 <= value[name] <= value["feature_count"]:
            raise BuildPortrayalError(f"BUILD {name} is invalid.")
    counts = value["observed_class_counts"]
    if not isinstance(counts, dict) or not counts or sum(counts.values()) != value["feature_count"]:
        raise BuildPortrayalError("BUILD class counts do not match feature_count.")
    for code, count in counts.items():
        if code in BUILD_PARENT_CODES:
            raise BuildPortrayalError(f"BUILD parent classification {code} requires clarification.")
        if code not in BUILD_PORTRAYAL_CODES:
            raise BuildPortrayalError(f"Unsupported BUILD polygon classification code: {code!r}.")
        if type(count) is not int or count < 1:
            raise BuildPortrayalError("Every BUILD class count must be positive.")
    resolutions = value["classification_resolutions"]
    if not isinstance(resolutions, list):
        raise BuildPortrayalError("BUILD classification resolutions must be a list.")
    for item in resolutions:
        if not isinstance(item, dict) or set(item) != {
            "source_code",
            "effective_code",
            "status",
            "confirmed_by",
        }:
            raise BuildPortrayalError("A BUILD classification resolution is invalid.")
        if (
            item["source_code"] not in BUILD_PARENT_CODES
            or item["effective_code"] not in BUILD_PARENT_CODES[item["source_code"]]
            or item["status"] != "session-human-confirmed"
            or not SAFE_ACTOR.fullmatch(str(item["confirmed_by"] or ""))
        ):
            raise BuildPortrayalError("A BUILD parent-to-child resolution is unsupported.")
    return deepcopy(value)


def _render_contract(code: str) -> dict[str, Any]:
    if code == "9310100":
        return {
            "mode": "surveyed-polygon-hatch-and-floor-structure-preview",
            "roles": [
                "building-base-fill",
                "building-hatch-preview",
                "building-outline",
                "building-floor-structure-label",
            ],
            "marker": None,
            "outline_dasharray": None,
        }
    marker = {"9310103": "C", "9310200": "中", "9310300": "T"}[code]
    return {
        "mode": "surveyed-polygon-outline-and-marker-preview",
        "roles": ["building-base-fill", "building-outline", "building-class-marker"],
        "marker": marker,
        "outline_dasharray": [2, 2] if code in {"9310200", "9310300"} else None,
    }


def _entry_for_code(code: str, package: dict[str, Any], *, feature_count: int) -> dict[str, Any]:
    if package.get("status") != "retrieved":
        raise BuildPortrayalError(f"KG evidence for {code} is not in retrieved state.")
    rule_id = f"portrayal-rule:doc01:{code}"
    rule = _node(package, rule_id)
    properties = rule.get("properties", {})
    if (
        properties.get("feature_code") != code
        or properties.get("feature_name")
        not in {BUILD_NAMES[code], BUILD_NAMES[code].replace("（", "(").replace("）", ")")}
        or properties.get("geometry_classes") != EXPECTED_GEOMETRY_CLASSES[code]
        or properties.get("activation_status") != "non-executable"
    ):
        raise BuildPortrayalError(f"The canonical BUILD rule contract changed for {code}.")
    rule_sections = _edge_targets(package, rule_id, "EVIDENCED_ON")
    if len(rule_sections) != 1:
        raise BuildPortrayalError(f"The BUILD portrayal citation path is incomplete for {code}.")
    portrayal_citation = _citation(package, rule_sections[0])
    classification_node_id = (
        f"terrain-classification:doc02:{code}"
        if code in ANNEX7_CODES
        else f"classification:doc01:{code}"
    )
    _node(package, classification_node_id)
    classification_citation = None
    classification_occurrence_id = None
    if code in ANNEX7_CODES:
        occurrences = _edge_targets(package, classification_node_id, "HAS_SOURCE_OCCURRENCE")
        if len(occurrences) != 1:
            raise BuildPortrayalError(
                f"The Annex 7 BUILD occurrence path is incomplete for {code}."
            )
        classification_occurrence_id = occurrences[0]
        class_sections = _edge_targets(package, classification_occurrence_id, "EVIDENCED_ON")
        if len(class_sections) != 1:
            raise BuildPortrayalError(f"The Annex 7 BUILD citation path is incomplete for {code}.")
        classification_citation = _citation(package, class_sections[0])
    service_trace = package.get("retrieval_trace", {}).get("readonly_knowledge_service", {})
    if (
        service_trace.get("mutation_allowed") is not False
        or service_trace.get("arbitrary_cypher_allowed") is not False
    ):
        raise BuildPortrayalError("The Knowledge Service read-only boundary is invalid.")
    recipe_id = "portrayal-recipe:doc01:9310100:review-v1"
    recipe = _optional_node(package, recipe_id) if code == "9310100" else None
    if recipe is not None and recipe.get("properties", {}).get("activation_status") != (
        "non-executable-review-candidate"
    ):
        raise BuildPortrayalError("The BUILD hatch recipe activation boundary changed.")
    knowledge_node_ids = sorted(
        {
            rule_id,
            classification_node_id,
            rule_sections[0],
            *([classification_citation["section_id"]] if classification_citation else []),
            *([classification_occurrence_id] if classification_occurrence_id else []),
            *([recipe_id] if recipe else []),
        }
    )
    knowledge_edge_ids = sorted(
        "edge:" + canonical_sha256(edge)
        for edge in package.get("graph_paths", {}).get("edges", [])
        if edge.get("source") in knowledge_node_ids and edge.get("target") in knowledge_node_ids
    )
    if not knowledge_edge_ids:
        raise BuildPortrayalError(f"The bounded BUILD evidence path is empty for {code}.")
    classification_status = (
        "annex7-109-and-doc01-defined"
        if code in ANNEX7_CODES
        else "doc01-defined-annex7-109-row-not-present"
    )
    return {
        "feature_code": code,
        "feature_name": BUILD_NAMES[code],
        "feature_count": feature_count,
        "geometry_role": "Polygon/MultiPolygon surveyed building footprint",
        "classification_status": classification_status,
        "rule": {
            "rule_id": rule_id,
            "instruction": properties.get("instruction"),
            "page": properties.get("page"),
            "line_code": properties.get("line_code"),
            "color_code": properties.get("color_code"),
            "symbol_family": properties.get("symbol_family"),
            "activation_status": properties.get("activation_status"),
        },
        "render_contract": _render_contract(code),
        "preview_profile": {
            "outline_color": "#111111",
            "outline_width_px": 1.25,
            "hatch_pattern_id": "nma-build-hatch-diagonal" if code == "9310100" else None,
            "hatch_spacing_official_mm": 2.0 if code == "9310100" else None,
            "hatch_numeric_angle": None,
            "browser_hatch_angle_policy_degrees": 45 if code == "9310100" else None,
            "browser_hatch_spacing_px": 12 if code == "9310100" else None,
            "output_profile_status": "authorized-local-preview-policy-required",
        },
        "evidence": {
            "classification_node_id": classification_node_id,
            "knowledge_node_ids": knowledge_node_ids,
            "knowledge_edge_ids": knowledge_edge_ids,
            "portrayal_citation": portrayal_citation,
            "classification_citation": classification_citation,
            "knowledge_service": _bounded_knowledge_trace(service_trace),
        },
        "activation_gates": [
            {
                "id": f"{code}:local-output-profile",
                "status": "pending-human-preview-authorization",
                "reason": "CSS width, numeric hatch angle, spacing conversion, typography, and marker placement are local preview policies.",
            },
            {
                "id": f"{code}:production-activation",
                "status": "held",
                "reason": "Document evidence does not activate an official production renderer for this user upload.",
            },
        ],
    }


class BuildPortrayalPlannerV1:
    """Build a preview-only BUILD plan from user observations and read-only KG evidence."""

    def __init__(self, graph_retriever: KnowledgeServiceGraphRetriever):
        self.graph_retriever = graph_retriever

    def propose(self, observation: Any) -> dict[str, Any]:
        checked = validate_build_dataset_observation(observation)
        entries = []
        for code, count in sorted(checked["observed_class_counts"].items()):
            classification_id = (
                f"terrain-classification:doc02:{code}"
                if code in ANNEX7_CODES
                else f"classification:doc01:{code}"
            )
            package = self.graph_retriever.package_from_seed_ids(
                f"BUILD {code} classification and portrayal evidence",
                [classification_id, f"portrayal-rule:doc01:{code}"],
                ranked_trace=[
                    {
                        "id": classification_id,
                        "type": "TerrainClassificationCode"
                        if code in ANNEX7_CODES
                        else "ClassificationCode",
                        "score": 1,
                        "matched_terms": [code],
                        "match_mode": "validated-user-build-classification",
                    }
                ],
                retrieval_mode="build-v1-validated-code-to-readonly-kg-evidence",
                max_depth=3,
                max_nodes=140,
            )
            entries.append(_entry_for_code(code, package, feature_count=count))
        graph_revisions = {
            item["evidence"]["knowledge_service"].get("graph_revision") for item in entries
        }
        graph_hashes = {
            item["evidence"]["knowledge_service"].get("canonical_graph_sha256") for item in entries
        }
        if len(graph_revisions) != 1 or None in graph_revisions:
            raise BuildPortrayalError("BUILD evidence spans inconsistent graph revisions.")
        if len(graph_hashes) != 1 or None in graph_hashes:
            raise BuildPortrayalError("BUILD evidence spans inconsistent graph identities.")
        plan = {
            "schema": PLAN_SCHEMA,
            "status": "proposed-preview-only-awaiting-human-authorization",
            "goal": checked["goal"],
            "domain": "build",
            "classification_root": BUILD_ROOT_CODE,
            "source_binding": {
                "source": checked["source"],
                "source_layer": checked["source_layer"],
                "geometry_family": checked["geometry_family"],
                "schema_profile": checked["schema_profile"],
                "classification_field": checked["classification_field"],
                "classification_resolutions": checked["classification_resolutions"],
                "runtime_classification_property": "__NMA_BUILD_CLASS",
                "identity_field": checked["identity_field"],
                "annotation_fields": checked["annotation_fields"],
                "source_identity_rule": checked["source_identity_rule"],
                "raw_feature_bytes_transmitted": False,
            },
            "geometry_observation": {
                "feature_count": checked["feature_count"],
                "total_vertex_count": checked["total_vertex_count"],
                "total_ring_count": checked["total_ring_count"],
                "multipart_feature_count": checked["multipart_feature_count"],
                "z_feature_count": checked["z_feature_count"],
                "derived_xy_view": "browser-local-non-writing-portrayal-view",
            },
            "graph_identity": {
                "graph_revision": next(iter(graph_revisions)),
                "canonical_graph_sha256": next(iter(graph_hashes)),
            },
            "entries": entries,
            "agent_trace": [
                {
                    "sequence": 1,
                    "state": "observe",
                    "outcome": "validated-user-build-polygons-and-schema",
                },
                {"sequence": 2, "state": "retrieve", "outcome": "read-only-kg-evidence-retrieved"},
                {"sequence": 3, "state": "plan", "outcome": "building-preview-plan-proposed"},
                {"sequence": 4, "state": "human-intervention", "outcome": "authorization-required"},
            ],
            "governance": {
                "human_authorization_required": True,
                "local_output_profile_authorization_required": True,
                "official_rule_activation": False,
                "production_activation": False,
                "source_z_preserved": True,
                "source_mutation_allowed": False,
                "geometry_repair_allowed": False,
                "data_export_allowed": False,
                "automatic_action": False,
            },
        }
        return _hashed(plan, "plan_sha256")


def authorize_build_portrayal(plan: Any, *, actor: str, decision: str) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise BuildPortrayalError("A valid BUILD portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    if not isinstance(actor, str) or not SAFE_ACTOR.fullmatch(actor):
        raise BuildPortrayalError("The BUILD authorization actor is invalid.")
    if decision not in {"authorize-preview", "reject"}:
        raise BuildPortrayalError("The BUILD portrayal decision is unsupported.")
    return _hashed(
        {
            "schema": AUTHORIZATION_SCHEMA,
            "status": "authorized-preview-only" if decision == "authorize-preview" else "rejected",
            "actor": actor,
            "decision": decision,
            "plan_sha256": plan["plan_sha256"],
            "authorized_operation": "compile-maplibre-preview"
            if decision == "authorize-preview"
            else None,
            "authorized_local_output_profile": decision == "authorize-preview",
            "official_rule_activation": False,
            "production_activation": False,
            "data_export_allowed": False,
            "single_plan_only": True,
        },
        "authorization_sha256",
    )


def _validate_authorization(plan: dict[str, Any], authorization: Any) -> dict[str, Any]:
    if not isinstance(authorization, dict) or authorization.get("schema") != AUTHORIZATION_SCHEMA:
        raise BuildPortrayalError("A valid BUILD preview authorization is required.")
    _validate_hash(authorization, "authorization_sha256")
    if authorization.get("status") != "authorized-preview-only":
        raise BuildPortrayalError("The BUILD portrayal preview is not authorized.")
    if authorization.get("plan_sha256") != plan.get("plan_sha256"):
        raise BuildPortrayalError("The BUILD authorization does not bind the current plan.")
    if (
        authorization.get("authorized_operation") != "compile-maplibre-preview"
        or authorization.get("authorized_local_output_profile") is not True
        or authorization.get("official_rule_activation") is not False
        or authorization.get("production_activation") is not False
    ):
        raise BuildPortrayalError("The BUILD authorization scope is invalid.")
    return deepcopy(authorization)


def _layer(
    entry: dict[str, Any], role: str, source: str, class_filter: list[Any]
) -> dict[str, Any]:
    code = entry["feature_code"]
    evidence = {
        "rule_id": entry["rule"]["rule_id"],
        "section_id": entry["evidence"]["portrayal_citation"]["section_id"],
        "page": entry["rule"]["page"],
        "classification_status": entry["classification_status"],
    }
    common = {
        "id": f"nma-build-{code}-{role}",
        "source": source,
        "filter": class_filter,
        "nma:semantic_role": role,
        "nma:evidence": evidence,
    }
    if role == "building-base-fill":
        return {**common, "type": "fill", "paint": {"fill-color": "#f3eee4", "fill-opacity": 0.28}}
    if role == "building-hatch-preview":
        return {
            **common,
            "type": "fill",
            "paint": {
                "fill-pattern": entry["preview_profile"]["hatch_pattern_id"],
                "fill-opacity": 0.9,
            },
        }
    if role == "building-outline":
        paint: dict[str, Any] = {
            "line-color": entry["preview_profile"]["outline_color"],
            "line-width": entry["preview_profile"]["outline_width_px"],
        }
        dash = entry["render_contract"]["outline_dasharray"]
        if dash:
            paint["line-dasharray"] = dash
        return {**common, "type": "line", "paint": paint}
    if role == "building-floor-structure-label":
        return {
            **common,
            "type": "symbol",
            "layout": {
                "text-field": [
                    "concat",
                    ["to-string", ["coalesce", ["get", "BUILD_NO"], ""]],
                    ["to-string", ["coalesce", ["get", "BUILD_STR"], ""]],
                ],
                "text-size": 11,
                "text-allow-overlap": False,
            },
            "paint": {"text-color": "#111111", "text-halo-color": "#ffffff", "text-halo-width": 1},
        }
    if role == "building-class-marker":
        return {
            **common,
            "type": "symbol",
            "layout": {
                "text-field": entry["render_contract"]["marker"],
                "text-size": 15,
                "text-allow-overlap": False,
            },
            "paint": {"text-color": "#111111", "text-halo-color": "#ffffff", "text-halo-width": 1},
        }
    raise BuildPortrayalError(f"Unsupported BUILD semantic role: {role}.")


def compile_build_maplibre_preview(plan: Any, authorization: Any) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise BuildPortrayalError("A valid BUILD portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    approved = _validate_authorization(plan, authorization)
    class_field = plan["source_binding"]["runtime_classification_property"]
    layers = []
    for entry in plan["entries"]:
        class_filter = ["==", ["to-string", ["get", class_field]], entry["feature_code"]]
        layers.extend(
            _layer(entry, role, "user-build", class_filter)
            for role in entry["render_contract"]["roles"]
        )
    return _hashed(
        {
            "schema": ADAPTER_RESULT_SCHEMA,
            "status": "compiled-preview-not-yet-rendered",
            "plan_sha256": plan["plan_sha256"],
            "authorization_sha256": approved["authorization_sha256"],
            "source": {
                "id": "user-build",
                "type": "geojson-runtime-binding",
                "data_included": False,
                "user_bytes_transmitted": False,
                "source_z_mutated": False,
                "derived_xy_view_only": True,
            },
            "pattern": {
                "id": "nma-build-hatch-diagonal",
                "data_included": False,
                "browser_generated": True,
                "official_numeric_angle_claimed": False,
            },
            "layers": layers,
            "expected_feature_count": plan["geometry_observation"]["feature_count"],
            "expected_total_vertex_count": plan["geometry_observation"]["total_vertex_count"],
            "expected_total_ring_count": plan["geometry_observation"]["total_ring_count"],
            "preview_only": True,
            "official_rule_activation": False,
            "production_activation": False,
            "geometry_repair": False,
            "data_export": False,
            "map_mutation_performed": False,
            "automatic_action": False,
        },
        "adapter_result_sha256",
    )


def apply_build_tool_observation(plan: Any, observation: Any) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise BuildPortrayalError("A valid BUILD portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    required = {"schema", "tool", "plan_sha256", "outcome", "detail"}
    if not isinstance(observation, dict) or set(observation) != required:
        raise BuildPortrayalError("The BUILD tool observation has an invalid shape.")
    if observation["schema"] != TOOL_OBSERVATION_SCHEMA:
        raise BuildPortrayalError("The BUILD tool observation schema is unsupported.")
    if observation["tool"] != "maplibre-build-preview-compiler":
        raise BuildPortrayalError("The BUILD tool observation names an unsupported tool.")
    if observation["plan_sha256"] != plan["plan_sha256"]:
        raise BuildPortrayalError("The BUILD tool observation is bound to another plan.")
    if not isinstance(observation["detail"], str) or len(observation["detail"]) > 500:
        raise BuildPortrayalError("The BUILD tool observation detail is invalid.")
    outcome = observation["outcome"]
    if outcome == "compiled":
        decision, reason = (
            "verify-then-stop",
            "The BUILD style compiler completed; governed verification must pass before rendering.",
        )
    elif outcome == "browser-render-verified":
        decision, reason = (
            "stop",
            "The authorized BUILD boundaries, hatch or class markers rendered and verification passed.",
        )
    elif outcome == "style-validation-failed":
        decision, reason = (
            "abstain-and-stop",
            observation["detail"] or "MapLibre validation failed.",
        )
    else:
        raise BuildPortrayalError("The BUILD tool outcome is unsupported.")
    return _hashed(
        {
            "schema": AGENT_DECISION_SCHEMA,
            "decision": decision,
            "reason": reason,
            "plan_sha256": plan["plan_sha256"],
            "observed_outcome": outcome,
            "map_mutation_allowed": False,
            "automatic_rule_activation": False,
        },
        "decision_sha256",
    )


def verify_build_maplibre_preview(
    plan: Any, authorization: Any, adapter_result: Any
) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise BuildPortrayalError("A valid BUILD portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    approved = _validate_authorization(plan, authorization)
    if (
        not isinstance(adapter_result, dict)
        or adapter_result.get("schema") != ADAPTER_RESULT_SCHEMA
    ):
        raise BuildPortrayalError("A valid BUILD MapLibre adapter result is required.")
    _validate_hash(adapter_result, "adapter_result_sha256")
    checks = []

    def check(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"id": check_id, "passed": passed, "detail": detail})

    check(
        "plan-binding",
        adapter_result.get("plan_sha256") == plan["plan_sha256"],
        "Adapter result binds the plan.",
    )
    check(
        "authorization-binding",
        adapter_result.get("authorization_sha256") == approved["authorization_sha256"],
        "Adapter result binds the preview authorization.",
    )
    layers = adapter_result.get("layers", [])
    class_field = plan["source_binding"]["runtime_classification_property"]
    semantics_valid = isinstance(layers, list)
    evidence_valid = semantics_valid
    for entry in plan["entries"]:
        expected_filter = ["==", ["to-string", ["get", class_field]], entry["feature_code"]]
        by_role = {
            layer.get("nma:semantic_role"): layer
            for layer in layers
            if isinstance(layer, dict) and layer.get("filter") == expected_filter
        }
        if set(by_role) != set(entry["render_contract"]["roles"]):
            semantics_valid = False
        if entry["feature_code"] == "9310100":
            hatch = by_role.get("building-hatch-preview", {})
            label = by_role.get("building-floor-structure-label", {})
            if hatch.get("paint", {}).get(
                "fill-pattern"
            ) != "nma-build-hatch-diagonal" or label.get("layout", {}).get("text-field") != [
                "concat",
                ["to-string", ["coalesce", ["get", "BUILD_NO"], ""]],
                ["to-string", ["coalesce", ["get", "BUILD_STR"], ""]],
            ]:
                semantics_valid = False
        for layer in by_role.values():
            evidence = layer.get("nma:evidence", {})
            if (
                evidence.get("rule_id") != entry["rule"]["rule_id"]
                or evidence.get("section_id")
                != entry["evidence"]["portrayal_citation"]["section_id"]
                or evidence.get("page") != entry["rule"]["page"]
            ):
                evidence_valid = False
    check(
        "classification-coverage",
        semantics_valid,
        "Every observed BUILD class has its reviewed preview layer set.",
    )
    check(
        "evidence-binding",
        evidence_valid,
        "Every BUILD layer preserves its rule and source-page binding.",
    )
    check(
        "feature-count",
        adapter_result.get("expected_feature_count")
        == plan["geometry_observation"]["feature_count"],
        "The user BUILD feature count is preserved.",
    )
    check(
        "vertex-and-ring-count",
        adapter_result.get("expected_total_vertex_count")
        == plan["geometry_observation"]["total_vertex_count"]
        and adapter_result.get("expected_total_ring_count")
        == plan["geometry_observation"]["total_ring_count"],
        "The observed BUILD vertex and ring counts are preserved.",
    )
    check(
        "preview-boundary",
        adapter_result.get("preview_only") is True
        and adapter_result.get("official_rule_activation") is False
        and adapter_result.get("production_activation") is False
        and adapter_result.get("geometry_repair") is False
        and adapter_result.get("data_export") is False
        and adapter_result.get("pattern", {}).get("official_numeric_angle_claimed") is False,
        "BUILD preview does not claim an official numeric hatch angle or production activation.",
    )
    source = adapter_result.get("source", {})
    check(
        "user-data-and-z-boundary",
        source.get("id") == "user-build"
        and source.get("data_included") is False
        and source.get("user_bytes_transmitted") is False
        and source.get("source_z_mutated") is False
        and source.get("derived_xy_view_only") is True,
        "The adapter binds browser-local BUILD data without bytes, mutation, repair, or Z writeback.",
    )
    check(
        "no-premature-map-mutation",
        adapter_result.get("map_mutation_performed") is False,
        "Compilation does not render or mutate a map by itself.",
    )
    failures = [item for item in checks if not item["passed"]]
    return _hashed(
        {
            "schema": QA_SCHEMA,
            "status": "pass-ready-for-browser-render" if not failures else "fail-closed",
            "plan_sha256": plan["plan_sha256"],
            "authorization_sha256": approved["authorization_sha256"],
            "adapter_result_sha256": adapter_result["adapter_result_sha256"],
            "checks": checks,
            "failed_check_ids": [item["id"] for item in failures],
            "browser_render_authorized": not failures,
            "official_rule_activation": False,
            "production_activation": False,
            "automatic_action": False,
        },
        "qa_sha256",
    )

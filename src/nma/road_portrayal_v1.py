from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from nma.core import canonical_sha256
from nma.readonly_knowledge_service import KnowledgeServiceGraphRetriever


DATASET_OBSERVATION_SCHEMA = "nma.road-dataset-observation/1.0"
PLAN_SCHEMA = "nma.road-portrayal-plan/1.0"
AUTHORIZATION_SCHEMA = "nma.road-portrayal-authorization/1.0"
ADAPTER_RESULT_SCHEMA = "nma.road-maplibre-adapter-result/1.0"
TOOL_OBSERVATION_SCHEMA = "nma.road-portrayal-tool-observation/1.0"
AGENT_DECISION_SCHEMA = "nma.road-portrayal-agent-decision/1.0"
QA_SCHEMA = "nma.road-portrayal-qa/1.0"

ROAD_ROOT_CODE = "9420000"
ROAD_PARENT_CODES = {
    "9420100": ("9420101", "9420102"),
    "9420200": ("9420201", "9420202"),
    "9420800": ("9420801", "9420802"),
}
ROAD_PORTRAYAL_CODES = (
    "9420101",
    "9420102",
    "9420201",
    "9420202",
    "9420300",
    "9420400",
    "9420500",
    "9420600",
    "9420700",
    "9420801",
    "9420802",
)
SAFE_ACTOR = re.compile(r"^[A-Za-z0-9._:@-]{1,120}$")


class RoadPortrayalError(ValueError):
    """A ROAD portrayal request crossed an evidence or governance boundary."""


def _without_hash(value: dict[str, Any], field: str) -> dict[str, Any]:
    return {key: deepcopy(item) for key, item in value.items() if key != field}


def _hashed(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result[field] = canonical_sha256(result)
    return result


def _validate_hash(value: dict[str, Any], field: str) -> None:
    if value.get(field) != canonical_sha256(_without_hash(value, field)):
        raise RoadPortrayalError(f"The {field} identity is invalid.")


def _node(package: dict[str, Any], node_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in package.get("evidence_nodes", [])
        if isinstance(item, dict) and item.get("id") == node_id
    ]
    if len(matches) != 1:
        raise RoadPortrayalError(f"Required Knowledge Graph node is unavailable: {node_id}.")
    return matches[0]


def _optional_node(package: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    matches = [
        item
        for item in package.get("evidence_nodes", [])
        if isinstance(item, dict) and item.get("id") == node_id
    ]
    if len(matches) > 1:
        raise RoadPortrayalError(f"Knowledge Graph node is ambiguous: {node_id}.")
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
        raise RoadPortrayalError(f"Required source citation is unavailable: {section_id}.")
    citation = matches[0]
    if (
        citation.get("citation_integrity") != "verified-unique-document-containment"
        or not citation.get("source_sha256")
        or not citation.get("filename")
    ):
        raise RoadPortrayalError(f"Source citation integrity failed: {section_id}.")
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


def _validate_mapping(value: Any) -> dict[str, Any]:
    required = {"source_field", "canonical_field", "status", "confirmed_by"}
    if not isinstance(value, dict) or set(value) != required:
        raise RoadPortrayalError("The ROAD classification-field mapping is invalid.")
    if value["canonical_field"] != "ROADCLASS2":
        raise RoadPortrayalError("ROAD classification must bind to Document 09 ROADCLASS2.")
    if value["source_field"] == "ROADCLASS2":
        if value["status"] != "official-direct" or value["confirmed_by"] is not None:
            raise RoadPortrayalError("The direct ROADCLASS2 mapping contract is invalid.")
    elif value["source_field"] == "TERRAINID":
        if value["status"] != "session-human-confirmed" or not SAFE_ACTOR.fullmatch(
            str(value["confirmed_by"] or "")
        ):
            raise RoadPortrayalError(
                "TERRAINID requires an explicit session mapping to Document 09 ROADCLASS2."
            )
    else:
        raise RoadPortrayalError("The ROAD classification field has no reviewed mapping.")
    return deepcopy(value)


def validate_road_dataset_observation(value: Any) -> dict[str, Any]:
    required = {
        "schema",
        "goal",
        "source",
        "source_layer",
        "geometry_family",
        "classification_field_mapping",
        "identity_field",
        "label_field",
        "route_number_fields",
        "observed_class_counts",
        "classification_resolutions",
        "feature_count",
        "total_vertex_count",
        "multipart_feature_count",
        "source_identity_rule",
        "raw_feature_bytes_transmitted",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise RoadPortrayalError("The ROAD dataset observation has an invalid shape.")
    if value["schema"] != DATASET_OBSERVATION_SCHEMA:
        raise RoadPortrayalError("The ROAD dataset observation schema is unsupported.")
    if not isinstance(value["goal"], str) or not 1 <= len(value["goal"].strip()) <= 500:
        raise RoadPortrayalError("The ROAD goal is invalid.")
    if value["source"] != "user-shapefile" or value["source_layer"] != "ROAD":
        raise RoadPortrayalError("ROAD portrayal requires a user ROAD Shapefile layer.")
    if value["geometry_family"] != "line":
        raise RoadPortrayalError("ROAD portrayal requires LineString or MultiLineString geometry.")
    mapping = _validate_mapping(value["classification_field_mapping"])
    if value["identity_field"] != "ROADSEGID" or value["label_field"] != "ROADNAME":
        raise RoadPortrayalError("ROAD portrayal requires ROADSEGID and ROADNAME.")
    if value["route_number_fields"] != ["ROADNUM", "ROADNUM1", "ROADNUM2"]:
        raise RoadPortrayalError("ROAD portrayal requires the reviewed route-number field set.")
    if value["source_identity_rule"] != "zip-relative-filename-plus-source-id":
        raise RoadPortrayalError("The ROAD source identity rule is unsupported.")
    if value["raw_feature_bytes_transmitted"] is not False:
        raise RoadPortrayalError("This demo contract cannot transmit raw feature bytes.")
    for name in ("feature_count", "total_vertex_count"):
        if type(value[name]) is not int or value[name] < 1:
            raise RoadPortrayalError(f"ROAD {name} must be positive.")
    if (
        type(value["multipart_feature_count"]) is not int
        or not 0 <= value["multipart_feature_count"] <= value["feature_count"]
    ):
        raise RoadPortrayalError("ROAD multipart_feature_count is invalid.")
    counts = value["observed_class_counts"]
    if not isinstance(counts, dict) or not counts:
        raise RoadPortrayalError("ROAD class counts are required.")
    if sum(counts.values()) != value["feature_count"]:
        raise RoadPortrayalError("ROAD class counts do not match feature_count.")
    for code, count in counts.items():
        if code in ROAD_PARENT_CODES:
            raise RoadPortrayalError(f"ROAD parent classification {code} requires clarification.")
        if code not in ROAD_PORTRAYAL_CODES:
            raise RoadPortrayalError(f"Unsupported ROAD classification code: {code!r}.")
        if type(count) is not int or count < 1:
            raise RoadPortrayalError("Every ROAD class count must be positive.")
    resolutions = value["classification_resolutions"]
    if not isinstance(resolutions, list):
        raise RoadPortrayalError("ROAD classification resolutions must be a list.")
    for item in resolutions:
        if not isinstance(item, dict) or set(item) != {
            "source_code",
            "effective_code",
            "status",
            "confirmed_by",
        }:
            raise RoadPortrayalError("A ROAD classification resolution is invalid.")
        if (
            item["source_code"] not in ROAD_PARENT_CODES
            or item["effective_code"] not in ROAD_PARENT_CODES[item["source_code"]]
            or item["status"] != "session-human-confirmed"
            or not SAFE_ACTOR.fullmatch(str(item["confirmed_by"] or ""))
        ):
            raise RoadPortrayalError("A ROAD parent-to-child resolution is unsupported.")
    checked = deepcopy(value)
    checked["classification_field_mapping"] = mapping
    return checked


def _entry_for_code(code: str, package: dict[str, Any], *, feature_count: int) -> dict[str, Any]:
    if package.get("status") != "retrieved":
        raise RoadPortrayalError(f"KG evidence for {code} is not in retrieved state.")
    classification_id = f"terrain-classification:doc02:{code}"
    rule_id = f"portrayal-rule:doc01:{code}"
    recipe_id = f"portrayal-recipe:road:{code}:compound-v1"
    classification = _node(package, classification_id)
    rule = _node(package, rule_id)
    recipe = _optional_node(package, recipe_id)
    class_properties = classification.get("properties", {})
    rule_properties = rule.get("properties", {})
    if (
        class_properties.get("code") != code
        or rule_properties.get("feature_code") != code
        or rule_properties.get("activation_status") != "non-executable"
        or rule_properties.get("geometry_classes") != ["2", "5"]
    ):
        raise RoadPortrayalError(f"The canonical ROAD rule contract changed for {code}.")
    section_targets = _edge_targets(package, rule_id, "EVIDENCED_ON")
    class_sections = _edge_targets(package, classification_id, "EVIDENCED_ON")
    color_targets = _edge_targets(package, rule_id, "USES_COLOR")
    line_targets = _edge_targets(package, rule_id, "USES_LINE_STYLE")
    symbol_targets = _edge_targets(package, rule_id, "USES_SYMBOL")
    if not all(
        len(items) == 1
        for items in (section_targets, class_sections, color_targets, line_targets, symbol_targets)
    ):
        raise RoadPortrayalError(f"The ROAD portrayal path is incomplete for {code}.")
    expected_color = "portrayal-color:doc01:7" if code == "9420700" else "portrayal-color:doc01:1"
    if color_targets[0] != expected_color:
        raise RoadPortrayalError(f"The ROAD colour evidence changed for {code}.")
    portrayal_citation = _citation(package, section_targets[0])
    classification_citation = _citation(package, class_sections[0])
    service_trace = package.get("retrieval_trace", {}).get("readonly_knowledge_service", {})
    if (
        service_trace.get("mutation_allowed") is not False
        or service_trace.get("arbitrary_cypher_allowed") is not False
    ):
        raise RoadPortrayalError("The Knowledge Service read-only boundary is invalid.")
    shield = None
    if recipe is not None:
        recipe_properties = recipe.get("properties", {})
        if (
            recipe_properties.get("road_code") != code
            or recipe_properties.get("activation_status") != "non-executable-review-candidate"
        ):
            raise RoadPortrayalError(f"The ROAD compound recipe changed for {code}.")
        shield = {
            "shield_code": recipe_properties.get("shield_code"),
            "shield_name": recipe_properties.get("shield_name"),
            "orientation": recipe_properties.get("shield_orientation"),
            "runtime_status": "semantic-binding-only-no-reviewed-renderer",
        }
    knowledge_node_ids = sorted(
        {
            classification_id,
            rule_id,
            symbol_targets[0],
            color_targets[0],
            line_targets[0],
            section_targets[0],
            class_sections[0],
            *([recipe_id] if recipe else []),
        }
    )
    knowledge_edge_ids = sorted(
        "edge:" + canonical_sha256(edge)
        for edge in package.get("graph_paths", {}).get("edges", [])
        if edge.get("source") in knowledge_node_ids and edge.get("target") in knowledge_node_ids
    )
    if not knowledge_edge_ids:
        raise RoadPortrayalError(f"The bounded ROAD evidence path is empty for {code}.")
    return {
        "feature_code": code,
        "feature_name": class_properties.get("name_zh"),
        "feature_count": feature_count,
        "parent_code": class_properties.get("parent"),
        "geometry_role": "LineString/MultiLineString centreline",
        "render_mode": "centreline-and-line-following-name-preview",
        "rule": {
            "rule_id": rule_id,
            "symbol_id": symbol_targets[0],
            "line_style_id": line_targets[0],
            "color_id": color_targets[0],
            "instruction": rule_properties.get("instruction"),
            "page": rule_properties.get("page"),
            "review_status": rule_properties.get("review_status")
            or rule_properties.get("mapping_status"),
            "activation_status": rule_properties.get("activation_status"),
        },
        "preview_style": {
            "line_color": "#111111" if code == "9420700" else "#c62828",
            "line_width_px": 4,
            "width_semantics": "derived-centreline-preview-not-surveyed-width-boundary",
        },
        "shield_binding": shield,
        "evidence": {
            "classification_node_id": classification_id,
            "knowledge_node_ids": knowledge_node_ids,
            "knowledge_edge_ids": knowledge_edge_ids,
            "portrayal_citation": portrayal_citation,
            "classification_citation": classification_citation,
            "knowledge_service": _bounded_knowledge_trace(service_trace),
        },
        "activation_gates": [
            {
                "id": f"{code}:surveyed-width-boundary",
                "status": "held",
                "reason": "User ROAD centreline geometry is not a reviewed ROADA surveyed-width boundary.",
            },
            {
                "id": f"{code}:route-shield-renderer",
                "status": "held",
                "reason": "Shield semantics may be retrieved, but no reviewed runtime shield graphic is activated.",
            },
            {
                "id": f"{code}:label-placement",
                "status": "pending-human-preview-authorization",
                "reason": "Web label repetition and collision policy require preview authorization.",
            },
        ],
    }


class RoadPortrayalPlannerV1:
    """Build a preview-only ROAD plan from user observations and read-only KG evidence."""

    def __init__(self, graph_retriever: KnowledgeServiceGraphRetriever):
        self.graph_retriever = graph_retriever

    def propose(self, observation: Any) -> dict[str, Any]:
        checked = validate_road_dataset_observation(observation)
        entries = []
        for code, count in sorted(checked["observed_class_counts"].items()):
            package = self.graph_retriever.package_from_seed_ids(
                f"ROAD {code} classification and portrayal evidence",
                [
                    f"terrain-classification:doc02:{code}",
                    f"portrayal-rule:doc01:{code}",
                ],
                ranked_trace=[
                    {
                        "id": f"terrain-classification:doc02:{code}",
                        "type": "TerrainClassificationCode",
                        "score": 1,
                        "matched_terms": [code],
                        "match_mode": "validated-user-road-classification",
                    }
                ],
                retrieval_mode="road-v1-validated-code-to-readonly-kg-evidence",
                max_depth=3,
                max_nodes=120,
            )
            entries.append(_entry_for_code(code, package, feature_count=count))
        graph_revisions = {
            item["evidence"]["knowledge_service"].get("graph_revision") for item in entries
        }
        graph_hashes = {
            item["evidence"]["knowledge_service"].get("canonical_graph_sha256") for item in entries
        }
        if len(graph_revisions) != 1 or None in graph_revisions:
            raise RoadPortrayalError("ROAD evidence spans inconsistent graph revisions.")
        if len(graph_hashes) != 1 or None in graph_hashes:
            raise RoadPortrayalError("ROAD evidence spans inconsistent graph identities.")
        plan = {
            "schema": PLAN_SCHEMA,
            "status": "proposed-preview-only-awaiting-human-authorization",
            "goal": checked["goal"],
            "domain": "road",
            "classification_root": ROAD_ROOT_CODE,
            "source_binding": {
                "source": checked["source"],
                "source_layer": checked["source_layer"],
                "geometry_family": checked["geometry_family"],
                "classification_field_mapping": checked["classification_field_mapping"],
                "classification_resolutions": checked["classification_resolutions"],
                "runtime_classification_property": "__NMA_ROAD_CLASS",
                "identity_field": checked["identity_field"],
                "label_field": checked["label_field"],
                "route_number_fields": checked["route_number_fields"],
                "source_identity_rule": checked["source_identity_rule"],
                "raw_feature_bytes_transmitted": False,
            },
            "geometry_observation": {
                "feature_count": checked["feature_count"],
                "total_vertex_count": checked["total_vertex_count"],
                "multipart_feature_count": checked["multipart_feature_count"],
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
                    "outcome": "validated-user-road-lines-and-schema",
                },
                {"sequence": 2, "state": "retrieve", "outcome": "read-only-kg-evidence-retrieved"},
                {"sequence": 3, "state": "plan", "outcome": "centreline-preview-plan-proposed"},
                {"sequence": 4, "state": "human-intervention", "outcome": "authorization-required"},
            ],
            "governance": {
                "human_authorization_required": True,
                "official_rule_activation": False,
                "production_activation": False,
                "surveyed_width_boundary_rendered": False,
                "route_shield_graphic_rendered": False,
                "source_mutation_allowed": False,
                "data_export_allowed": False,
                "automatic_action": False,
            },
        }
        return _hashed(plan, "plan_sha256")


def authorize_road_portrayal(plan: Any, *, actor: str, decision: str) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise RoadPortrayalError("A valid ROAD portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    if not isinstance(actor, str) or not SAFE_ACTOR.fullmatch(actor):
        raise RoadPortrayalError("The ROAD authorization actor is invalid.")
    if decision not in {"authorize-preview", "reject"}:
        raise RoadPortrayalError("The ROAD portrayal decision is unsupported.")
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
            "official_rule_activation": False,
            "production_activation": False,
            "data_export_allowed": False,
            "single_plan_only": True,
        },
        "authorization_sha256",
    )


def _validate_authorization(plan: dict[str, Any], authorization: Any) -> dict[str, Any]:
    if not isinstance(authorization, dict) or authorization.get("schema") != AUTHORIZATION_SCHEMA:
        raise RoadPortrayalError("A valid ROAD preview authorization is required.")
    _validate_hash(authorization, "authorization_sha256")
    if authorization.get("status") != "authorized-preview-only":
        raise RoadPortrayalError("The ROAD portrayal preview is not authorized.")
    if authorization.get("plan_sha256") != plan.get("plan_sha256"):
        raise RoadPortrayalError("The ROAD authorization does not bind the current plan.")
    if (
        authorization.get("authorized_operation") != "compile-maplibre-preview"
        or authorization.get("official_rule_activation") is not False
        or authorization.get("production_activation") is not False
    ):
        raise RoadPortrayalError("The ROAD authorization scope is invalid.")
    return deepcopy(authorization)


def compile_road_maplibre_preview(plan: Any, authorization: Any) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise RoadPortrayalError("A valid ROAD portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    approved = _validate_authorization(plan, authorization)
    class_field = plan["source_binding"]["runtime_classification_property"]
    label_field = plan["source_binding"]["label_field"]
    layers = []
    for entry in plan["entries"]:
        code = entry["feature_code"]
        evidence = {
            "rule_id": entry["rule"]["rule_id"],
            "section_id": entry["evidence"]["portrayal_citation"]["section_id"],
            "page": entry["rule"]["page"],
        }
        class_filter = ["==", ["to-string", ["get", class_field]], code]
        layers.append(
            {
                "id": f"nma-road-{code}-centreline",
                "type": "line",
                "source": "user-road",
                "filter": class_filter,
                "layout": {"line-cap": "round", "line-join": "round"},
                "paint": {
                    "line-color": entry["preview_style"]["line_color"],
                    "line-width": entry["preview_style"]["line_width_px"],
                    "line-opacity": 0.92,
                },
                "nma:semantic_role": "derived-road-centreline-preview",
                "nma:evidence": evidence,
            }
        )
        layers.append(
            {
                "id": f"nma-road-{code}-line-name",
                "type": "symbol",
                "source": "user-road",
                "filter": class_filter,
                "layout": {
                    "symbol-placement": "line",
                    "symbol-spacing": 220,
                    "text-field": ["to-string", ["get", label_field]],
                    "text-size": 12,
                    "text-keep-upright": True,
                    "text-allow-overlap": False,
                },
                "paint": {
                    "text-color": "#111111",
                    "text-halo-color": "#ffffff",
                    "text-halo-width": 1.5,
                },
                "nma:semantic_role": "line-following-road-name",
                "nma:evidence": evidence,
            }
        )
    return _hashed(
        {
            "schema": ADAPTER_RESULT_SCHEMA,
            "status": "compiled-preview-not-yet-rendered",
            "plan_sha256": plan["plan_sha256"],
            "authorization_sha256": approved["authorization_sha256"],
            "source": {
                "id": "user-road",
                "type": "geojson-runtime-binding",
                "data_included": False,
                "user_bytes_transmitted": False,
            },
            "layers": layers,
            "expected_feature_count": plan["geometry_observation"]["feature_count"],
            "expected_total_vertex_count": plan["geometry_observation"]["total_vertex_count"],
            "preview_only": True,
            "surveyed_width_boundary_rendered": False,
            "route_shield_graphic_rendered": False,
            "official_rule_activation": False,
            "production_activation": False,
            "data_export": False,
            "map_mutation_performed": False,
            "automatic_action": False,
        },
        "adapter_result_sha256",
    )


def apply_road_tool_observation(plan: Any, observation: Any) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise RoadPortrayalError("A valid ROAD portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    required = {"schema", "tool", "plan_sha256", "outcome", "detail"}
    if not isinstance(observation, dict) or set(observation) != required:
        raise RoadPortrayalError("The ROAD tool observation has an invalid shape.")
    if observation["schema"] != TOOL_OBSERVATION_SCHEMA:
        raise RoadPortrayalError("The ROAD tool observation schema is unsupported.")
    if observation["tool"] != "maplibre-road-preview-compiler":
        raise RoadPortrayalError("The ROAD tool observation names an unsupported tool.")
    if observation["plan_sha256"] != plan["plan_sha256"]:
        raise RoadPortrayalError("The ROAD tool observation is bound to another plan.")
    if not isinstance(observation["detail"], str) or len(observation["detail"]) > 500:
        raise RoadPortrayalError("The ROAD tool observation detail is invalid.")
    outcome = observation["outcome"]
    if outcome == "compiled":
        decision, reason = (
            "verify-then-stop",
            "The ROAD style compiler completed; governed verification must pass before rendering.",
        )
    elif outcome == "browser-render-verified":
        decision, reason = (
            "stop",
            "The authorized ROAD centreline and line-following labels rendered and verification passed.",
        )
    elif outcome == "style-validation-failed":
        decision, reason = (
            "abstain-and-stop",
            observation["detail"] or "MapLibre validation failed.",
        )
    else:
        raise RoadPortrayalError("The ROAD tool outcome is unsupported.")
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


def verify_road_maplibre_preview(
    plan: Any, authorization: Any, adapter_result: Any
) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise RoadPortrayalError("A valid ROAD portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    approved = _validate_authorization(plan, authorization)
    if (
        not isinstance(adapter_result, dict)
        or adapter_result.get("schema") != ADAPTER_RESULT_SCHEMA
    ):
        raise RoadPortrayalError("A valid ROAD MapLibre adapter result is required.")
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
    expected = {item["feature_code"]: item for item in plan["entries"]}
    semantics_valid = isinstance(layers, list) and len(layers) == len(expected) * 2
    evidence_valid = semantics_valid
    for code, entry in expected.items():
        by_role = {
            layer.get("nma:semantic_role"): layer
            for layer in layers
            if isinstance(layer, dict)
            and layer.get("filter")
            == [
                "==",
                ["to-string", ["get", plan["source_binding"]["runtime_classification_property"]]],
                code,
            ]
        }
        line = by_role.get("derived-road-centreline-preview")
        label = by_role.get("line-following-road-name")
        if (
            not line
            or line.get("type") != "line"
            or line.get("paint", {}).get("line-color") != entry["preview_style"]["line_color"]
            or not label
            or label.get("type") != "symbol"
            or label.get("layout", {}).get("symbol-placement") != "line"
            or label.get("layout", {}).get("text-field")
            != ["to-string", ["get", plan["source_binding"]["label_field"]]]
        ):
            semantics_valid = False
        for layer in (line, label):
            evidence = layer.get("nma:evidence", {}) if layer else {}
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
        "Every observed ROAD class has one line and one line-name layer.",
    )
    check(
        "evidence-binding",
        evidence_valid,
        "Every compiled ROAD layer preserves its rule and source-page binding.",
    )
    check(
        "feature-count",
        adapter_result.get("expected_feature_count")
        == plan["geometry_observation"]["feature_count"],
        "The user ROAD feature count is preserved.",
    )
    check(
        "vertex-count",
        adapter_result.get("expected_total_vertex_count")
        == plan["geometry_observation"]["total_vertex_count"],
        "The observed ROAD vertex count is preserved.",
    )
    check(
        "preview-boundary",
        adapter_result.get("preview_only") is True
        and adapter_result.get("surveyed_width_boundary_rendered") is False
        and adapter_result.get("route_shield_graphic_rendered") is False
        and adapter_result.get("official_rule_activation") is False
        and adapter_result.get("production_activation") is False
        and adapter_result.get("data_export") is False,
        "Centreline preview does not claim surveyed-width, shield, official, or production activation.",
    )
    source = adapter_result.get("source", {})
    check(
        "user-data-boundary",
        source.get("id") == "user-road"
        and source.get("data_included") is False
        and source.get("user_bytes_transmitted") is False,
        "The adapter binds browser-local ROAD data without user feature bytes.",
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

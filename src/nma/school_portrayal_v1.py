from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any

from nma.core import canonical_sha256
from nma.readonly_knowledge_service import KnowledgeServiceGraphRetriever


DATASET_OBSERVATION_SCHEMA = "nma.school-dataset-observation/1.0"
PLAN_SCHEMA = "nma.school-portrayal-plan/1.0"
AUTHORIZATION_SCHEMA = "nma.school-portrayal-authorization/1.0"
ADAPTER_RESULT_SCHEMA = "nma.school-maplibre-adapter-result/1.0"
TOOL_OBSERVATION_SCHEMA = "nma.school-portrayal-tool-observation/1.0"
AGENT_DECISION_SCHEMA = "nma.school-portrayal-agent-decision/1.0"
QA_SCHEMA = "nma.school-portrayal-qa/1.0"

SCHOOL_ROOT_CODE = "9920100"
SCHOOL_LEAF_CODES = (
    "9920101",
    "9920102",
    "9920103",
    "9920104",
    "9920105",
    "9920106",
)
FLAG_CODES = {"9920101", "9920102", "9920103", "9920106"}
TEXT_ONLY_CODES = {"9920104", "9920105"}
SCHOOL_FLAG_ASSET = "assets/symbols/nlsc112v5.4/school.svg"
SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
SAFE_ACTOR = re.compile(r"^[A-Za-z0-9._:@-]{1,120}$")


class SchoolPortrayalError(ValueError):
    """A School portrayal request crossed an evidence or governance boundary."""


def _without_hash(value: dict[str, Any], field: str) -> dict[str, Any]:
    return {key: deepcopy(item) for key, item in value.items() if key != field}


def _hashed(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result[field] = canonical_sha256(result)
    return result


def _validate_hash(value: dict[str, Any], field: str) -> None:
    if value.get(field) != canonical_sha256(_without_hash(value, field)):
        raise SchoolPortrayalError(f"The {field} identity is invalid.")


def _validate_field(value: Any, *, name: str) -> str:
    if not isinstance(value, str) or not SAFE_IDENTIFIER.fullmatch(value):
        raise SchoolPortrayalError(f"The {name} field is invalid.")
    return value


def validate_school_dataset_observation(value: Any) -> dict[str, Any]:
    required = {
        "schema",
        "goal",
        "source",
        "source_layer",
        "geometry_type",
        "classification_field",
        "identity_field",
        "label_field",
        "observed_class_counts",
        "source_identity_rule",
        "raw_feature_bytes_transmitted",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise SchoolPortrayalError("The School dataset observation has an invalid shape.")
    if value["schema"] != DATASET_OBSERVATION_SCHEMA:
        raise SchoolPortrayalError("The School dataset observation schema is unsupported.")
    if not isinstance(value["goal"], str) or not 1 <= len(value["goal"].strip()) <= 500:
        raise SchoolPortrayalError("The School goal is invalid.")
    if value["source"] != "user-shapefile" or value["source_layer"] != "MARK":
        raise SchoolPortrayalError("School portrayal requires the user MARK Shapefile layer.")
    if value["geometry_type"] != "Point":
        raise SchoolPortrayalError("School portrayal requires Point geometry.")
    if value["classification_field"] != "TERRAINID":
        raise SchoolPortrayalError("School portrayal requires the exact TERRAINID field.")
    identity_field = _validate_field(value["identity_field"], name="identity")
    label_field = _validate_field(value["label_field"], name="label")
    if identity_field != "MARKID" or label_field != "MARKNAME1":
        raise SchoolPortrayalError(
            "School portrayal requires the reviewed MARKID and MARKNAME1 schema binding."
        )
    if value["source_identity_rule"] != "zip-relative-filename-plus-source-id":
        raise SchoolPortrayalError("The School source identity rule is unsupported.")
    if value["raw_feature_bytes_transmitted"] is not False:
        raise SchoolPortrayalError("This public demo contract cannot transmit raw feature bytes.")
    counts = value["observed_class_counts"]
    if not isinstance(counts, dict) or not counts:
        raise SchoolPortrayalError("School class counts are required.")
    for code, count in counts.items():
        if code == SCHOOL_ROOT_CODE:
            raise SchoolPortrayalError(
                "9920100 is a classification family, not a leaf portrayal rule."
            )
        if code not in SCHOOL_LEAF_CODES:
            raise SchoolPortrayalError(f"Unsupported School classification code: {code!r}.")
        if type(count) is not int or count < 1:
            raise SchoolPortrayalError("Every observed School class count must be positive.")
    return deepcopy(value)


def _node(package: dict[str, Any], node_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in package.get("evidence_nodes", [])
        if isinstance(item, dict) and item.get("id") == node_id
    ]
    if len(matches) != 1:
        raise SchoolPortrayalError(f"Required Knowledge Graph node is unavailable: {node_id}.")
    return matches[0]


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
        raise SchoolPortrayalError(f"Required source citation is unavailable: {section_id}.")
    citation = matches[0]
    if (
        citation.get("citation_integrity") != "verified-unique-document-containment"
        or not citation.get("source_sha256")
        or not citation.get("filename")
    ):
        raise SchoolPortrayalError(f"Source citation integrity failed: {section_id}.")
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


def _entry_for_code(
    code: str,
    package: dict[str, Any],
    *,
    feature_count: int,
) -> dict[str, Any]:
    if package.get("status") != "retrieved":
        raise SchoolPortrayalError(f"KG evidence for {code} is not in retrieved state.")
    classification_id = f"terrain-classification:doc02:{code}"
    code_value_id = f"code-value:landmark-type:{code}"
    rule_id = f"portrayal-rule:doc01:{code}"
    classification = _node(package, classification_id)
    code_value = _node(package, code_value_id)
    rule = _node(package, rule_id)
    class_properties = classification["properties"]
    rule_properties = rule["properties"]
    if (
        class_properties.get("code") != code
        or class_properties.get("parent_code") != SCHOOL_ROOT_CODE
        or rule_properties.get("feature_code") != code
        or rule_properties.get("activation_status") != "non-executable"
    ):
        raise SchoolPortrayalError(f"The canonical School rule contract changed for {code}.")
    if code_value.get("properties", {}).get("code") != code:
        raise SchoolPortrayalError(f"The MARK code-list value changed for {code}.")
    section_targets = _edge_targets(package, rule_id, "EVIDENCED_ON")
    symbol_targets = _edge_targets(package, rule_id, "USES_SYMBOL")
    color_targets = _edge_targets(package, rule_id, "USES_COLOR")
    line_targets = _edge_targets(package, rule_id, "USES_LINE_STYLE")
    if len(section_targets) != 1 or len(symbol_targets) != 1:
        raise SchoolPortrayalError(f"The School portrayal path is incomplete for {code}.")
    if color_targets != ["portrayal-color:doc01:7"] or line_targets != ["line-style:doc01:2"]:
        raise SchoolPortrayalError(f"The School line/colour evidence changed for {code}.")
    section_id = section_targets[0]
    symbol_id = symbol_targets[0]
    symbol = _node(package, symbol_id)
    symbol_properties = symbol.get("properties", {})
    family = symbol_properties.get("family") or rule_properties.get("symbol_family")
    if code == "9920103":
        family = "school-flag-marker"
    expected_family = "school-flag-marker" if code in FLAG_CODES else "name-annotation-only"
    if family != expected_family:
        raise SchoolPortrayalError(f"The School symbol family changed for {code}.")
    portrayal_citation = _citation(package, section_id)
    annex_citation = _citation(package, "section:doc02-1000-production:p65")
    service_trace = package.get("retrieval_trace", {}).get("readonly_knowledge_service", {})
    if (
        service_trace.get("mutation_allowed") is not False
        or service_trace.get("arbitrary_cypher_allowed") is not False
    ):
        raise SchoolPortrayalError("The Knowledge Service read-only boundary is invalid.")
    render_mode = "school-flag-marker" if code in FLAG_CODES else "name-annotation-only"
    asset_binding = None
    gates = [
        {
            "id": f"{code}:official-rule-non-executable",
            "status": "held",
            "reason": "The canonical portrayal rule is evidence, not an activated production rule.",
        },
        {
            "id": f"{code}:label-placement",
            "status": "pending-human-preview-authorization",
            "reason": "The source requires a name annotation but does not fully define web collision placement.",
        },
    ]
    if render_mode == "school-flag-marker":
        direct = code == "9920103"
        asset_binding = {
            "path": SCHOOL_FLAG_ASSET,
            "mode": "sdf-derived-black-preview",
            "sdf": True,
            "binding_status": (
                "direct-reviewed-implementation-reference"
                if direct
                else "same-reviewed-symbol-family-derived-preview"
            ),
            "authoritative_source_geometry": False,
            "observed_color": "black",
            "web_color": "#111111",
        }
        gates.append(
            {
                "id": f"{code}:vector-preview",
                "status": "pending-human-preview-authorization",
                "reason": (
                    "The SVG preserves the reviewed flag family and dimensions as a derived preview; "
                    "it is not authoritative source geometry."
                ),
            }
        )
    knowledge_node_ids = sorted(
        {
            classification_id,
            code_value_id,
            rule_id,
            symbol_id,
            line_targets[0],
            color_targets[0],
            section_id,
            "section:doc02-1000-production:p65",
        }
    )
    knowledge_edge_ids = sorted(
        "edge:" + canonical_sha256(edge)
        for edge in package.get("graph_paths", {}).get("edges", [])
        if edge.get("source") in knowledge_node_ids and edge.get("target") in knowledge_node_ids
    )
    if not knowledge_edge_ids:
        raise SchoolPortrayalError(f"The bounded School evidence path is empty for {code}.")
    return {
        "feature_code": code,
        "feature_name": class_properties.get("name_zh"),
        "feature_count": feature_count,
        "parent_code": class_properties.get("parent_code"),
        "geometry_role": "Point",
        "render_mode": render_mode,
        "rule": {
            "rule_id": rule_id,
            "symbol_id": symbol_id,
            "symbol_family": family,
            "line_style_id": line_targets[0],
            "color_id": color_targets[0],
            "instruction": rule_properties.get("instruction"),
            "page": rule_properties.get("page"),
            "review_status": rule_properties.get("review_status"),
            "activation_status": rule_properties.get("activation_status"),
        },
        "asset_binding": asset_binding,
        "evidence": {
            "classification_node_id": classification_id,
            "code_value_node_id": code_value_id,
            "knowledge_node_ids": knowledge_node_ids,
            "knowledge_edge_ids": knowledge_edge_ids,
            "portrayal_citation": portrayal_citation,
            "classification_citation": annex_citation,
            "knowledge_service": _bounded_knowledge_trace(service_trace),
        },
        "activation_gates": gates,
    }


class SchoolPortrayalPlannerV1:
    """Build one preview-only School portrayal plan from live/snapshot KG evidence."""

    def __init__(
        self,
        graph_retriever: KnowledgeServiceGraphRetriever,
        *,
        repository_root: str | Path,
    ):
        self.graph_retriever = graph_retriever
        self.repository_root = Path(repository_root)

    def propose(self, observation: Any) -> dict[str, Any]:
        checked = validate_school_dataset_observation(observation)
        entries = []
        for code, count in sorted(checked["observed_class_counts"].items()):
            package = self.graph_retriever.package_from_seed_ids(
                f"School {code} classification and portrayal evidence",
                [
                    f"code-value:landmark-type:{code}",
                    f"terrain-classification:doc02:{code}",
                ],
                ranked_trace=[
                    {
                        "id": f"code-value:landmark-type:{code}",
                        "type": "CodeListValue",
                        "score": 1,
                        "matched_terms": [code],
                        "match_mode": "validated-user-terrainid",
                    }
                ],
                retrieval_mode="school-v1-validated-code-to-readonly-kg-evidence",
                max_depth=3,
                max_nodes=90,
            )
            entries.append(_entry_for_code(code, package, feature_count=count))
        if any(item["asset_binding"] for item in entries):
            path = self.repository_root / SCHOOL_FLAG_ASSET
            if not path.is_file():
                raise SchoolPortrayalError("The derived School preview asset is unavailable.")
        graph_revisions = {
            item["evidence"]["knowledge_service"].get("graph_revision") for item in entries
        }
        graph_hashes = {
            item["evidence"]["knowledge_service"].get("canonical_graph_sha256") for item in entries
        }
        if len(graph_revisions) != 1 or None in graph_revisions:
            raise SchoolPortrayalError("School evidence spans inconsistent graph revisions.")
        if len(graph_hashes) != 1 or None in graph_hashes:
            raise SchoolPortrayalError("School evidence spans inconsistent graph identities.")
        plan = {
            "schema": PLAN_SCHEMA,
            "status": "proposed-preview-only-awaiting-human-authorization",
            "goal": checked["goal"],
            "domain": "school",
            "classification_root": SCHOOL_ROOT_CODE,
            "source_binding": {
                "source": checked["source"],
                "source_layer": checked["source_layer"],
                "source_geometry_type": checked["geometry_type"],
                "classification_field": checked["classification_field"],
                "identity_field": checked["identity_field"],
                "label_field": checked["label_field"],
                "source_identity_rule": checked["source_identity_rule"],
                "raw_feature_bytes_transmitted": False,
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
                    "outcome": "validated-school-leaf-codes-and-source-schema",
                },
                {
                    "sequence": 2,
                    "state": "retrieve",
                    "outcome": "read-only-kg-evidence-retrieved",
                },
                {
                    "sequence": 3,
                    "state": "plan",
                    "outcome": "preview-only-portrayal-proposed",
                },
                {
                    "sequence": 4,
                    "state": "human-intervention",
                    "outcome": "authorization-required",
                },
            ],
            "revision": {"depth": 0, "parent_plan_sha256": None},
            "governance": {
                "human_authorization_required": True,
                "official_rule_activation": False,
                "production_activation": False,
                "map_mutation_allowed_before_authorization": False,
                "data_export_allowed": False,
                "automatic_action": False,
            },
        }
        return _hashed(plan, "plan_sha256")


def authorize_school_portrayal(
    plan: Any,
    *,
    actor: str,
    decision: str,
) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise SchoolPortrayalError("A valid School portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    if not isinstance(actor, str) or not SAFE_ACTOR.fullmatch(actor):
        raise SchoolPortrayalError("The authorization actor is invalid.")
    if decision not in {"authorize-preview", "reject"}:
        raise SchoolPortrayalError("The School portrayal decision is unsupported.")
    basis = {
        "schema": AUTHORIZATION_SCHEMA,
        "status": "authorized-preview-only" if decision == "authorize-preview" else "rejected",
        "actor": actor,
        "decision": decision,
        "plan_sha256": plan["plan_sha256"],
        "authorized_operation": (
            "compile-maplibre-preview" if decision == "authorize-preview" else None
        ),
        "official_rule_activation": False,
        "production_activation": False,
        "data_export_allowed": False,
        "single_plan_only": True,
    }
    return _hashed(basis, "authorization_sha256")


def _validate_authorization(plan: dict[str, Any], authorization: Any) -> dict[str, Any]:
    if not isinstance(authorization, dict) or authorization.get("schema") != (AUTHORIZATION_SCHEMA):
        raise SchoolPortrayalError("A valid School preview authorization is required.")
    _validate_hash(authorization, "authorization_sha256")
    if authorization.get("status") != "authorized-preview-only":
        raise SchoolPortrayalError("The School portrayal preview is not authorized.")
    if authorization.get("plan_sha256") != plan.get("plan_sha256"):
        raise SchoolPortrayalError("The authorization does not bind the current plan.")
    if (
        authorization.get("authorized_operation") != "compile-maplibre-preview"
        or authorization.get("official_rule_activation") is not False
        or authorization.get("production_activation") is not False
    ):
        raise SchoolPortrayalError("The authorization scope is invalid.")
    return deepcopy(authorization)


def compile_school_maplibre_preview(
    plan: Any,
    authorization: Any,
) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise SchoolPortrayalError("A valid School portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    checked_authorization = _validate_authorization(plan, authorization)
    binding = plan["source_binding"]
    code_field = binding["classification_field"]
    label_field = binding["label_field"]
    resources: dict[str, dict[str, Any]] = {}
    layers = []
    for entry in plan["entries"]:
        code = entry["feature_code"]
        base = {
            "source": "user-school",
            "filter": ["==", ["to-string", ["get", code_field]], code],
        }
        if entry["render_mode"] == "school-flag-marker":
            asset = entry["asset_binding"]
            resource_id = "nma-school-flag-family-preview"
            resources[resource_id] = {
                "id": resource_id,
                "kind": "local-svg-image",
                "path": asset["path"],
                "sdf": asset["sdf"],
                "binding_status": "shared-reviewed-school-flag-family-derived-preview",
                "authoritative_source_geometry": False,
            }
            paint = {
                "icon-opacity": 1.0,
                "text-color": "#111111",
                "text-halo-color": "#ffffff",
                "text-halo-width": 1.5,
            }
            if asset["sdf"]:
                paint["icon-color"] = asset["web_color"]
            layers.append(
                {
                    "id": f"nma-school-{code}-flag-and-name",
                    "type": "symbol",
                    **base,
                    "layout": {
                        "icon-image": resource_id,
                        "icon-size": 1.0,
                        "icon-anchor": "bottom-left",
                        # A School feature must not disappear merely because its
                        # name collides with a nearby label.  MapLibre may omit
                        # the text, but every point keeps its reviewed flag.
                        "icon-allow-overlap": True,
                        "text-field": ["to-string", ["get", label_field]],
                        "text-offset": [0.0, 1.4],
                        "text-optional": True,
                        "text-allow-overlap": False,
                    },
                    "paint": paint,
                    "nma:evidence": {
                        "rule_id": entry["rule"]["rule_id"],
                        "section_id": entry["evidence"]["portrayal_citation"]["section_id"],
                        "page": entry["rule"]["page"],
                    },
                }
            )
        elif entry["render_mode"] == "name-annotation-only":
            layers.append(
                {
                    "id": f"nma-school-{code}-name-only",
                    "type": "symbol",
                    **base,
                    "layout": {
                        "text-field": ["to-string", ["get", label_field]],
                        "text-size": 12,
                        # These classes are portrayed by name alone, so label
                        # collision cannot be allowed to erase the feature.
                        "text-allow-overlap": True,
                    },
                    "paint": {
                        "text-color": "#111111",
                        "text-halo-color": "#ffffff",
                        "text-halo-width": 1.5,
                    },
                    "nma:evidence": {
                        "rule_id": entry["rule"]["rule_id"],
                        "section_id": entry["evidence"]["portrayal_citation"]["section_id"],
                        "page": entry["rule"]["page"],
                    },
                }
            )
        else:
            raise SchoolPortrayalError(f"Unsupported School render mode for {code}.")
    result = {
        "schema": ADAPTER_RESULT_SCHEMA,
        "status": "compiled-preview-not-yet-rendered",
        "plan_sha256": plan["plan_sha256"],
        "authorization_sha256": checked_authorization["authorization_sha256"],
        "source": {
            "id": "user-school",
            "type": "geojson-runtime-binding",
            "data_included": False,
            "user_bytes_transmitted": False,
        },
        "resources": list(resources.values()),
        "layers": layers,
        "expected_feature_count": sum(item["feature_count"] for item in plan["entries"]),
        "preview_only": True,
        "official_rule_activation": False,
        "production_activation": False,
        "data_export": False,
        "map_mutation_performed": False,
        "automatic_action": False,
    }
    return _hashed(result, "adapter_result_sha256")


def apply_school_tool_observation(
    plan: Any,
    observation: Any,
) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise SchoolPortrayalError("A valid School portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    required = {"schema", "tool", "plan_sha256", "outcome", "detail"}
    if not isinstance(observation, dict) or set(observation) != required:
        raise SchoolPortrayalError("The School tool observation has an invalid shape.")
    if observation["schema"] != TOOL_OBSERVATION_SCHEMA:
        raise SchoolPortrayalError("The School tool observation schema is unsupported.")
    if observation["tool"] != "maplibre-school-preview-compiler":
        raise SchoolPortrayalError("The School tool observation names an unsupported tool.")
    if observation["plan_sha256"] != plan["plan_sha256"]:
        raise SchoolPortrayalError("The School tool observation is bound to another plan.")
    if not isinstance(observation["detail"], str) or len(observation["detail"]) > 500:
        raise SchoolPortrayalError("The School tool observation detail is invalid.")
    outcome = observation["outcome"]
    if outcome == "sdf-resource-load-failed":
        revised = deepcopy(plan)
        changed = 0
        for entry in revised["entries"]:
            asset = entry.get("asset_binding")
            if asset and asset.get("sdf") is True:
                asset["sdf"] = False
                asset["mode"] = "non-sdf-original-black-preview"
                changed += 1
        if not changed:
            return _hashed(
                {
                    "schema": AGENT_DECISION_SCHEMA,
                    "decision": "stop",
                    "reason": "No evidence-preserving resource fallback remains.",
                    "plan_sha256": plan["plan_sha256"],
                    "map_mutation_allowed": False,
                    "automatic_rule_activation": False,
                },
                "decision_sha256",
            )
        revised.pop("plan_sha256")
        revised["status"] = "replanned-preview-only-awaiting-reauthorization"
        revised["revision"] = {
            "depth": int(plan["revision"]["depth"]) + 1,
            "parent_plan_sha256": plan["plan_sha256"],
        }
        revised["agent_trace"].extend(
            [
                {
                    "sequence": len(revised["agent_trace"]) + 1,
                    "state": "observe-tool-result",
                    "outcome": "sdf-resource-load-failed",
                },
                {
                    "sequence": len(revised["agent_trace"]) + 2,
                    "state": "replan",
                    "outcome": "same-asset-non-sdf-original-black-preview",
                },
                {
                    "sequence": len(revised["agent_trace"]) + 3,
                    "state": "human-intervention",
                    "outcome": "reauthorization-required",
                },
            ]
        )
        return _hashed(revised, "plan_sha256")
    if outcome == "compiled":
        return _hashed(
            {
                "schema": AGENT_DECISION_SCHEMA,
                "decision": "verify-then-stop",
                "reason": "The compiler completed; verification must pass before map rendering.",
                "plan_sha256": plan["plan_sha256"],
                "map_mutation_allowed": False,
                "automatic_rule_activation": False,
            },
            "decision_sha256",
        )
    if outcome == "browser-render-verified":
        return _hashed(
            {
                "schema": AGENT_DECISION_SCHEMA,
                "decision": "stop",
                "reason": (
                    "The authorized MapLibre portrayal rendered in the browser and "
                    "all governed verification checks passed."
                ),
                "plan_sha256": plan["plan_sha256"],
                "observed_outcome": outcome,
                "map_mutation_allowed": False,
                "automatic_rule_activation": False,
            },
            "decision_sha256",
        )
    if outcome == "style-validation-failed":
        return _hashed(
            {
                "schema": AGENT_DECISION_SCHEMA,
                "decision": "abstain-and-stop",
                "reason": observation["detail"] or "MapLibre style validation failed.",
                "plan_sha256": plan["plan_sha256"],
                "map_mutation_allowed": False,
                "automatic_rule_activation": False,
            },
            "decision_sha256",
        )
    raise SchoolPortrayalError("The School tool outcome is unsupported.")


def verify_school_maplibre_preview(
    plan: Any,
    authorization: Any,
    adapter_result: Any,
) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise SchoolPortrayalError("A valid School portrayal plan is required.")
    _validate_hash(plan, "plan_sha256")
    checked_authorization = _validate_authorization(plan, authorization)
    if not isinstance(adapter_result, dict) or adapter_result.get("schema") != (
        ADAPTER_RESULT_SCHEMA
    ):
        raise SchoolPortrayalError("A valid School MapLibre adapter result is required.")
    _validate_hash(adapter_result, "adapter_result_sha256")
    checks = []

    def check(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"id": check_id, "passed": passed, "detail": detail})

    check(
        "plan-binding",
        adapter_result.get("plan_sha256") == plan["plan_sha256"],
        "Adapter result binds the authorized plan.",
    )
    check(
        "authorization-binding",
        adapter_result.get("authorization_sha256") == checked_authorization["authorization_sha256"],
        "Adapter result binds the preview authorization.",
    )
    expected_codes = {item["feature_code"] for item in plan["entries"]}
    expected_entries = {item["feature_code"]: item for item in plan["entries"]}
    layers = adapter_result.get("layers", [])
    layer_codes = {
        item.get("filter", [None, None, None])[2]
        for item in layers
        if isinstance(item, dict)
        and isinstance(item.get("filter"), list)
        and len(item["filter"]) == 3
    }
    check(
        "classification-coverage",
        layer_codes == expected_codes and len(layers) == len(expected_codes),
        "Every observed School leaf code has exactly one portrayal layer family.",
    )
    layer_semantics_valid = True
    evidence_binding_valid = True
    for layer in layers:
        if not isinstance(layer, dict) or layer.get("type") != "symbol":
            layer_semantics_valid = False
            evidence_binding_valid = False
            continue
        filter_value = layer.get("filter")
        code = (
            filter_value[2] if isinstance(filter_value, list) and len(filter_value) == 3 else None
        )
        entry = expected_entries.get(code)
        if entry is None:
            layer_semantics_valid = False
            evidence_binding_valid = False
            continue
        layout = layer.get("layout", {})
        has_icon = "icon-image" in layout
        expected_icon = entry["render_mode"] == "school-flag-marker"
        expected_filter = [
            "==",
            ["to-string", ["get", plan["source_binding"]["classification_field"]]],
            code,
        ]
        expected_text = [
            "to-string",
            ["get", plan["source_binding"]["label_field"]],
        ]
        if has_icon != expected_icon or filter_value != expected_filter:
            layer_semantics_valid = False
        if layout.get("text-field") != expected_text:
            layer_semantics_valid = False
        if expected_icon:
            if (
                layout.get("icon-allow-overlap") is not True
                or layout.get("text-optional") is not True
                or layout.get("text-allow-overlap") is not False
            ):
                layer_semantics_valid = False
        elif layout.get("text-allow-overlap") is not True:
            layer_semantics_valid = False
        evidence = layer.get("nma:evidence", {})
        if (
            evidence.get("rule_id") != entry["rule"]["rule_id"]
            or evidence.get("section_id") != entry["evidence"]["portrayal_citation"]["section_id"]
            or evidence.get("page") != entry["rule"]["page"]
        ):
            evidence_binding_valid = False
    check(
        "portrayal-semantics",
        layer_semantics_valid,
        "Flag and name-only layers preserve the KG-selected School rule family.",
    )
    check(
        "evidence-binding",
        evidence_binding_valid,
        "Every compiled layer preserves its rule, source section, and page binding.",
    )
    flag_entries = [item for item in plan["entries"] if item["render_mode"] == "school-flag-marker"]
    resources = adapter_result.get("resources", [])
    if flag_entries:
        expected_sdf = flag_entries[0]["asset_binding"]["sdf"]
        resource_valid = (
            isinstance(resources, list)
            and len(resources) == 1
            and isinstance(resources[0], dict)
            and resources[0].get("id") == "nma-school-flag-family-preview"
            and resources[0].get("path") == SCHOOL_FLAG_ASSET
            and resources[0].get("sdf") is expected_sdf
            and resources[0].get("authoritative_source_geometry") is False
        )
    else:
        resource_valid = resources == []
    check(
        "preview-resource",
        resource_valid,
        "The shared School flag resource is plan-bound and explicitly non-authoritative.",
    )
    check(
        "feature-count",
        adapter_result.get("expected_feature_count")
        == sum(item["feature_count"] for item in plan["entries"]),
        "The planned feature count is preserved.",
    )
    check(
        "preview-boundary",
        adapter_result.get("preview_only") is True
        and adapter_result.get("official_rule_activation") is False
        and adapter_result.get("production_activation") is False
        and adapter_result.get("data_export") is False,
        "Compilation remains preview-only and non-exporting.",
    )
    source = adapter_result.get("source", {})
    check(
        "user-data-boundary",
        source.get("id") == "user-school"
        and source.get("type") == "geojson-runtime-binding"
        and source.get("data_included") is False
        and source.get("user_bytes_transmitted") is False,
        "The adapter binds browser-local user data without including user feature bytes.",
    )
    check(
        "no-premature-map-mutation",
        adapter_result.get("map_mutation_performed") is False,
        "Style compilation does not render or mutate a map by itself.",
    )
    failures = [item for item in checks if not item["passed"]]
    qa = {
        "schema": QA_SCHEMA,
        "status": "pass-ready-for-browser-render" if not failures else "fail-closed",
        "plan_sha256": plan["plan_sha256"],
        "authorization_sha256": checked_authorization["authorization_sha256"],
        "adapter_result_sha256": adapter_result["adapter_result_sha256"],
        "checks": checks,
        "failed_check_ids": [item["id"] for item in failures],
        "browser_render_authorized": not failures,
        "official_rule_activation": False,
        "production_activation": False,
        "automatic_action": False,
    }
    return _hashed(qa, "qa_sha256")

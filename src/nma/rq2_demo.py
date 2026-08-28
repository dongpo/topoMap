"""RQ2-DEMO-01 knowledge-constrained planning and deterministic execution."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import time
from typing import Any, Callable, Mapping, Sequence
from urllib.error import URLError
from urllib.request import urlopen

from nma.core.identity import canonical_json, canonical_sha256
from nma.graphrag import CanonicalGraphRetriever
from nma.llm import LLMAdapter
from nma.llm.base import LLMResult, validate_json_schema_subset


PROPOSAL_VERSION = "rq2-proposal/1.0"
PLANNER_VERSION = "rq2-provider-neutral-plan-composer/1.0"
VALIDATOR_VERSION = "rq2-plan-validator/1.0"
EXECUTOR_VERSION = "rq2-deterministic-gis-executor/1.0"
VERIFIER_VERSION = "rq2-postcondition-verifier/1.0"
ALLOWLIST_VERSION = "rq2-tool-allowlist/1.0"
ZERO_HASH = "0" * 64
FAILURE_CODES = {
    "INTENT_AMBIGUOUS",
    "RETRIEVAL_MISS",
    "RETRIEVAL_CONFLICT",
    "CONSTRAINT_UNRESOLVED",
    "CONSTRAINT_CONTRADICTED",
    "CONSTRAINT_OMITTED_FROM_PLAN",
    "CONSTRAINT_FABRICATED",
    "PLAN_SCHEMA_INVALID",
    "UNKNOWN_TOOL",
    "FORBIDDEN_OPERATION",
    "PRECONDITION_MISSING",
    "PRECONDITION_FAILED",
    "POSTCONDITION_MISSING",
    "EXECUTION_FAILED",
    "POSTCONDITION_VIOLATION",
    "UNEXPECTED_MUTATION",
    "UNRESOLVED_BINDING_GUESSED",
    "EVIDENCE_TRACE_BROKEN",
    "PROPOSAL_HASH_MISMATCH",
    "OTHER",
}

OPERATION_CATALOG = {
    "read_feature": "rq2.feature.read/1.0",
    "validate_source_authority": "rq2.source-authority.validate/1.0",
    "validate_geometry_type": "rq2.geometry.validate/1.0",
    "derive_target_representation": "rq2.representation.derive/1.0",
    "write_derived_artifact": "rq2.artifact.write-derived/1.0",
    "verify_postconditions": "rq2.postconditions.verify/1.0",
}
MANDATORY_PRECONDITIONS = (
    "input_identity_known",
    "source_readable_hash_matches",
    "critical_constraints_resolved",
    "no_critical_contradictions",
    "geometry_compatible",
    "tool_allowlist_bound",
    "roots_disjoint",
    "proposal_hash_valid",
    "research_authorization_valid",
    "unresolved_guards_bounded",
)
CONSTRAINED_PRECONDITION = "knowledge_snapshot_known"
MANDATORY_POSTCONDITIONS = (
    "classification_exact",
    "geometry_point_unchanged",
    "line_style_exact",
    "color_code_exact",
    "observed_color_exact",
    "source_authority_evidence_bound",
    "product_layer_unresolved",
    "physical_gates_unresolved",
    "operations_match_plan",
    "receipt_bound_to_proposal",
    "source_unchanged",
    "declared_files_only",
)
TRACE_BASIS = (
    "user_intent",
    "knowledge_constraint",
    "deterministic_execution_requirement",
    "verification_requirement",
)
SEMANTIC_KEYS = (
    "classification",
    "geometry",
    "line_style",
    "color_code",
    "observed_color",
    "product_layer",
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class RQ2DemoError(ValueError):
    """An RQ2 contract or fail-closed boundary was violated."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_identity(identifier: str, sha256: str) -> dict[str, str]:
    if not identifier.strip() or SHA256_PATTERN.fullmatch(sha256) is None:
        raise RQ2DemoError("Artifact identities require a name and lowercase SHA-256.")
    return {"id": identifier, "sha256": sha256}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RQ2DemoError(f"Unreadable JSON object: {path}") from error
    if not isinstance(value, dict):
        raise RQ2DemoError(f"JSON artifact is not an object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(dict(value)) + b"\n")


def _intent_id(raw_text: str) -> str:
    return "intent:sha256:" + hashlib.sha256(raw_text.encode("utf-8")).hexdigest()


def proposal_hash(proposal: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(proposal))
    basis["proposal_hash"] = ZERO_HASH
    for declaration in basis.get("required_authorizations", []):
        declaration["bound_proposal_hash"] = ZERO_HASH
    return canonical_sha256(basis)


def bind_proposal_hash(proposal: Mapping[str, Any]) -> dict[str, Any]:
    bound = deepcopy(dict(proposal))
    digest = proposal_hash(bound)
    bound["proposal_hash"] = digest
    for declaration in bound["required_authorizations"]:
        declaration["bound_proposal_hash"] = digest
    if proposal_hash(bound) != digest:
        raise RQ2DemoError("Proposal hash binding is not stable.")
    return bound


def verify_model_identity(base_url: str, expected: Mapping[str, Any]) -> dict[str, Any]:
    try:
        with urlopen(f"{base_url.rstrip('/')}/api/tags", timeout=10) as response:
            payload = json.loads(response.read())
    except (OSError, URLError, json.JSONDecodeError) as error:
        raise RQ2DemoError("The frozen local Ollama runtime is unavailable.") from error
    matches = [item for item in payload.get("models", []) if item.get("name") == expected["name"]]
    if len(matches) != 1 or matches[0].get("digest") != expected["ollama_digest"]:
        raise RQ2DemoError("The exact frozen Qwen model identity is unavailable.")
    details = matches[0].get("details", {})
    observed = {
        "name": matches[0]["name"],
        "digest": matches[0]["digest"],
        "digest_prefix": matches[0]["digest"][:12],
        "family": details.get("family"),
        "parameter_size": details.get("parameter_size"),
        "quantization_level": details.get("quantization_level"),
    }
    if observed["digest_prefix"] != "845dbda0ea48":
        raise RQ2DemoError("The accepted predecessor model prefix changed.")
    return observed


def retrieve_rq2_evidence(repository_root: Path, intent: str) -> dict[str, Any]:
    """Reuse canonical GraphRAG ranking and typed expansion without semantic repair."""

    graph_path = repository_root / "data/knowledge/nma-canonical-graph-v0.4.json"
    retriever = CanonicalGraphRetriever.load(graph_path)
    ranked = retriever.ranked_search(intent, limit=24)
    portrayal_rules = [item for item in ranked if item["node"]["type"] == "PortrayalRule"]
    symbols = [item for item in ranked if item["node"]["type"] == "Symbol"]
    if not portrayal_rules:
        raise RQ2DemoError("RETRIEVAL_MISS: no portrayal rule matched the mapping intent.")
    selected = [portrayal_rules[0]]
    if symbols:
        selected.append(symbols[0])
    ranked_trace = [
        {
            "id": item["node"]["id"],
            "type": item["node"]["type"],
            "score": item["score"],
            "matched_terms": item["matched_terms"],
            "match_mode": item["match_mode"],
        }
        for item in ranked
    ]
    package = retriever.package_from_seed_ids(
        intent,
        [item["node"]["id"] for item in selected],
        ranked_trace=ranked_trace,
        retrieval_mode="rq2-existing-ranked-search-plus-typed-canonical-expansion",
        max_depth=2,
        max_nodes=100,
        extra_trace={
            "selection_policy": "highest-ranked portrayal rule plus highest-ranked symbol",
            "arbitrary_cypher_allowed": False,
            "semantic_repair_allowed": False,
        },
    )
    if package.get("status") != "retrieved":
        raise RQ2DemoError("RETRIEVAL_MISS: canonical graph expansion returned no evidence.")
    node_types = {item["type"] for item in package["evidence_nodes"]}
    required_types = {
        "ClassificationCode",
        "PortrayalRule",
        "PortrayalGeometryRole",
        "LineStyleReference",
        "PortrayalColorReference",
        "SpecificationDocument",
    }
    if not required_types <= node_types:
        raise RQ2DemoError("RETRIEVAL_MISS: the bounded evidence package is incomplete.")
    return package


def evidence_identities(repository_root: Path, package: Mapping[str, Any]) -> dict[str, Any]:
    graph_path = repository_root / "data/knowledge/nma-canonical-graph-v0.4.json"
    return {
        "knowledge_snapshot_identity": artifact_identity(
            "data/knowledge/nma-canonical-graph-v0.4.json", sha256_file(graph_path)
        ),
        "retrieval_identity": artifact_identity(
            "rq2-demo-01-retrieval-package", canonical_sha256(package)
        ),
    }


def _constraint(
    identifier: str,
    kind: str,
    subject: str,
    predicate: str,
    value: Any,
    evidence_refs: Sequence[str],
    authority: str,
    status: str,
    effect: str,
) -> dict[str, Any]:
    return {
        "constraint_id": identifier,
        "type": kind,
        "subject": subject,
        "predicate": predicate,
        "expected_value": value,
        "source_evidence_refs": sorted(set(evidence_refs)),
        "authority_status": authority,
        "resolution_status": status,
        "execution_effect": effect,
    }


def _resolve_value_constraint(
    *,
    identifier: str,
    kind: str,
    subject: str,
    predicate: str,
    observations: Sequence[tuple[Any, str]],
    authority: str,
    effect: str,
) -> dict[str, Any]:
    non_null = [(value, ref) for value, ref in observations if value not in (None, "")]
    by_value: dict[str, tuple[Any, set[str]]] = {}
    for value, ref in non_null:
        key = canonical_json(value).decode("utf-8")
        current = by_value.setdefault(key, (value, set()))
        current[1].add(ref)
    refs = sorted({ref for _, ref in non_null})
    if len(by_value) == 1:
        value = next(iter(by_value.values()))[0]
        return _constraint(
            identifier, kind, subject, predicate, value, refs, authority, "resolved", effect
        )
    if len(by_value) > 1:
        return _constraint(
            identifier,
            kind,
            subject,
            predicate,
            None,
            refs,
            authority,
            "contradicted",
            effect,
        )
    return _constraint(
        identifier, kind, subject, predicate, None, [], "unknown", "unresolved", effect
    )


def resolve_constraints(package: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Project accepted evidence into all six frozen constraint categories, with 0 model calls."""

    nodes = package.get("evidence_nodes", [])
    if not isinstance(nodes, list):
        raise RQ2DemoError("The retrieval package has no evidence node collection.")
    by_type: dict[str, list[Mapping[str, Any]]] = {}
    for node in nodes:
        if isinstance(node, Mapping):
            by_type.setdefault(str(node.get("type")), []).append(node)

    def observations(types: Sequence[str], keys: Sequence[str]) -> list[tuple[Any, str]]:
        found: list[tuple[Any, str]] = []
        for node_type in types:
            for node in by_type.get(node_type, []):
                properties = node.get("properties", {})
                if not isinstance(properties, Mapping):
                    continue
                for key in keys:
                    if key in properties:
                        found.append((properties[key], str(node["id"])))
                        break
        return found

    constraints = [
        _resolve_value_constraint(
            identifier="constraint:classification.feature_code",
            kind="classification",
            subject="input-feature",
            predicate="feature_code.equals",
            observations=observations(
                ("ClassificationCode", "PortrayalRule", "PortrayalRecipe"),
                ("code", "feature_code"),
            ),
            authority="authoritative_pending_review",
            effect="required",
        ),
        _resolve_value_constraint(
            identifier="constraint:geometry.type",
            kind="geometry",
            subject="input-feature.geometry",
            predicate="geometry_type.equals",
            observations=observations(
                ("PortrayalGeometryRole", "PortrayalRule", "PortrayalRecipe"),
                ("name", "geometry_role"),
            ),
            authority="authoritative_pending_review",
            effect="required",
        ),
        _resolve_value_constraint(
            identifier="constraint:portrayal.line_code",
            kind="portrayal",
            subject="derived-representation.portrayal",
            predicate="line_code.equals",
            observations=observations(
                ("LineStyleReference", "PortrayalRule"), ("code", "line_code")
            ),
            authority="authoritative_pending_review",
            effect="required",
        ),
        _resolve_value_constraint(
            identifier="constraint:portrayal.color_code",
            kind="portrayal",
            subject="derived-representation.portrayal",
            predicate="color_code.equals",
            observations=observations(
                ("PortrayalColorReference", "PortrayalRule"), ("code", "color_code")
            ),
            authority="authoritative_pending_review",
            effect="required",
        ),
        _resolve_value_constraint(
            identifier="constraint:portrayal.observed_color",
            kind="portrayal",
            subject="derived-representation.portrayal",
            predicate="observed_color.equals",
            observations=observations(
                ("PortrayalColorReference", "PortrayalRule"), ("observed_color",)
            ),
            authority="derived_from_authoritative",
            effect="required",
        ),
    ]
    documents = by_type.get("SpecificationDocument", [])
    authority_refs = [str(item["id"]) for item in documents]
    authority_value = [
        {
            "document_id": item["id"],
            "revision": item.get("properties", {}).get("revision"),
            "sha256": item.get("properties", {}).get("sha256"),
        }
        for item in documents
    ]
    constraints.append(
        _constraint(
            "constraint:source.authority",
            "source_authority",
            "knowledge-evidence",
            "source_identity.accepted",
            authority_value,
            authority_refs,
            "authoritative",
            "resolved" if authority_refs else "unresolved",
            "required",
        )
    )
    product_layers = by_type.get("ProductLayer", [])
    mapping_refs = [
        str(node["id"])
        for node in nodes
        if "unresolved" in str(node.get("properties", {}).get("mapping_status", "")).casefold()
    ]
    if product_layers:
        product_values = sorted(str(item["id"]) for item in product_layers)
        constraints.append(
            _constraint(
                "constraint:relationship.product_layer",
                "relationship_binding",
                "input-feature",
                "product_layer.equals",
                product_values[0] if len(product_values) == 1 else None,
                product_values,
                "authoritative_pending_review",
                "resolved" if len(product_values) == 1 else "contradicted",
                "guard",
            )
        )
    else:
        constraints.append(
            _constraint(
                "constraint:relationship.product_layer",
                "relationship_binding",
                "input-feature",
                "product_layer.equals",
                None,
                mapping_refs,
                "authoritative_pending_review" if mapping_refs else "unknown",
                "unresolved",
                "guard",
            )
        )
    for gate in sorted(by_type.get("ActivationGate", []), key=lambda item: str(item["id"])):
        gate_name = str(gate.get("properties", {}).get("id", gate["id"])).replace("_", "-")
        constraints.append(
            _constraint(
                f"constraint:guard.{gate_name}",
                "execution_guard",
                "authoritative-render",
                f"{gate_name}.resolved",
                None,
                [str(gate["id"])],
                "authoritative_pending_review",
                "unresolved",
                "guard",
            )
        )
    inactive_refs = [
        str(node["id"])
        for node in nodes
        if str(node.get("properties", {}).get("activation_status", "")).startswith("non-executable")
    ]
    constraints.append(
        _constraint(
            "constraint:guard.authoritative_render",
            "execution_guard",
            "authoritative-render",
            "authoritative_render.allowed",
            False,
            inactive_refs,
            "authoritative_pending_review",
            "resolved",
            "forbidden",
        )
    )
    grouped = {"resolved": [], "unresolved": [], "contradicted": []}
    for item in constraints:
        grouped[item["resolution_status"]].append(item)
    for values in grouped.values():
        values.sort(key=lambda item: item["constraint_id"])
    return grouped


def constraint_summary(constraints: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict]:
    return [
        {
            "constraint_id": item["constraint_id"],
            "type": item["type"],
            "predicate": item["predicate"],
            "expected_value": item["expected_value"],
            "resolution_status": item["resolution_status"],
            "execution_effect": item["execution_effect"],
            "source_evidence_refs": item["source_evidence_refs"],
        }
        for status in ("resolved", "unresolved", "contradicted")
        for item in constraints.get(status, [])
    ]


PLAN_DRAFT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "normalized_goal": {"type": "string", "minLength": 1, "maxLength": 500},
        "execution_status": {
            "type": "string",
            "enum": ["PROCEED", "PROCEED_WITH_BOUNDED_UNRESOLVED", "BLOCK"],
        },
        "reason_codes": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "PLANNER_PROPOSED_EXECUTION",
                    "BOUNDED_UNRESOLVED_GUARDS",
                    "CONSTRAINT_UNRESOLVED",
                    "ALL_EXECUTION_CRITICAL_CONSTRAINTS_RESOLVED",
                ],
            },
            "minItems": 1,
            "maxItems": 32,
        },
        "semantic_values": {
            "type": "object",
            "properties": {
                key: {"type": ["string", "null"], "maxLength": 200} for key in SEMANTIC_KEYS
            }
            | {"source_authority_handled": {"type": "boolean"}},
            "required": [*SEMANTIC_KEYS, "source_authority_handled"],
            "additionalProperties": False,
        },
        "steps": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "items": {
                "type": "object",
                "properties": {
                    "step_id": {"type": "string", "minLength": 1, "maxLength": 100},
                    "operation": {
                        "type": "string",
                        "enum": list(OPERATION_CATALOG),
                    },
                    "tool": {
                        "type": "string",
                        "enum": list(OPERATION_CATALOG.values()),
                    },
                    "trace_basis": {
                        "type": "array",
                        "items": {"type": "string", "enum": list(TRACE_BASIS)},
                        "minItems": 1,
                    },
                },
                "required": [
                    "step_id",
                    "operation",
                    "tool",
                    "trace_basis",
                ],
                "additionalProperties": False,
            },
        },
        "precondition_ids": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [*MANDATORY_PRECONDITIONS, CONSTRAINED_PRECONDITION],
            },
            "minItems": 1,
        },
        "expected_postcondition_ids": {
            "type": "array",
            "items": {"type": "string", "enum": list(MANDATORY_POSTCONDITIONS)},
            "minItems": 1,
        },
        "constraint_refs": {
            "type": "array",
            "items": {"type": "string", "minLength": 1, "maxLength": 200},
        },
    },
    "required": [
        "normalized_goal",
        "execution_status",
        "reason_codes",
        "semantic_values",
        "steps",
        "precondition_ids",
        "expected_postcondition_ids",
        "constraint_refs",
    ],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class PlannerOutput:
    draft: dict[str, Any]
    model_trace: dict[str, Any]


class RQ2Planner:
    """Provider-neutral LLM composer shared without branching between architectures."""

    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter

    def compose(
        self,
        *,
        intent: str,
        fixture: Mapping[str, Any],
        architecture: str,
        constraints: Mapping[str, Sequence[Mapping[str, Any]]] | None,
    ) -> PlannerOutput:
        if architecture not in {"llm-only", "knowledge-constrained"}:
            raise RQ2DemoError("Unsupported planning architecture.")
        supplied_constraints = [] if constraints is None else constraint_summary(constraints)
        context = {
            "intent": intent,
            "input_feature": dict(fixture),
            "architecture": architecture,
            "knowledge_constraints": supplied_constraints,
            "operation_catalog": OPERATION_CATALOG,
            "mandatory_preconditions": list(MANDATORY_PRECONDITIONS),
            "constrained_only_precondition": CONSTRAINED_PRECONDITION,
            "mandatory_postconditions": list(MANDATORY_POSTCONDITIONS),
            "safety_boundary": {
                "source_mutation": "forbidden",
                "output": "isolated symbolic derived artifact only",
                "authoritative_render": "forbidden unless every physical gate is resolved",
                "unknown_tools": "forbidden",
                "shell_or_python": "forbidden",
            },
        }
        instructions = (
            "Compose the executable mapping proposal plan yourself. Select and order the smallest "
            "complete sequence of catalog operations; select the global preconditions and "
            "postconditions that make the plan safe and verifiable. Fill semantic_values from supplied knowledge "
            "constraints when present. When constraints are absent, reason only from the intent and "
            "ordinary task instructions: do not claim retrieval, invent evidence IDs, or pretend a "
            "guess is knowledge. In llm-only mode the top-level constraint_refs must be empty. In "
            "knowledge-constrained mode, cite every applicable required/guard/forbidden constraint "
            "at top level and preserve unresolved values as null. The deterministic contract "
            "projection will bind your selected global conditions and constraints to every selected step. Include all mandatory "
            "postconditions at top level. Use knowledge_snapshot_known only in constrained mode. "
            "A safe symbolic derived artifact requires read, authority validation, geometry "
            "validation, representation derivation, isolated write, and verification; do not render. "
            "Use exact operation/tool pairs from the catalog. Return only the plan draft JSON."
            " Use only uppercase reason_codes from their schema enum; reason codes are not trace bases."
        )
        started = time.monotonic()
        result: LLMResult = self.adapter.generate_structured(
            task="compose-rq2-executable-mapping-proposal",
            instructions=instructions,
            context=context,
            output_schema=PLAN_DRAFT_SCHEMA,
        )
        planning_ms = round((time.monotonic() - started) * 1000)
        validate_json_schema_subset(result.output, PLAN_DRAFT_SCHEMA)
        trace = result.to_trace()
        trace["planning_latency_ms"] = planning_ms
        trace["temperature"] = 0
        trace["planner_identity"] = PLANNER_VERSION
        return PlannerOutput(deepcopy(result.output), trace)


def _all_constraints(constraints: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict]:
    return [
        deepcopy(dict(item))
        for status in ("resolved", "unresolved", "contradicted")
        for item in constraints.get(status, [])
    ]


def _constraint_refs_for_condition(
    condition_id: str,
    refs: Sequence[str],
    constraints: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[str]:
    index = {item["constraint_id"]: item for item in _all_constraints(constraints)}
    expected_types = {
        "classification_exact": {"classification"},
        "geometry_point_unchanged": {"geometry"},
        "line_style_exact": {"portrayal"},
        "color_code_exact": {"portrayal"},
        "observed_color_exact": {"portrayal"},
        "source_authority_evidence_bound": {"source_authority"},
        "product_layer_unresolved": {"relationship_binding"},
        "physical_gates_unresolved": {"execution_guard"},
    }.get(condition_id)
    if expected_types is None:
        return sorted(set(refs))
    return sorted({ref for ref in refs if ref in index and index[ref]["type"] in expected_types})


def _condition(
    condition_id: str,
    semantic_values: Mapping[str, Any],
    constraint_refs: Sequence[str],
    constraints: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    prefix: str,
    fixture: Mapping[str, Any],
    knowledge_snapshot: Mapping[str, Any] | None,
    allowlist_sha256: str,
) -> dict[str, Any]:
    values: dict[str, tuple[str, str, Any]] = {
        "input_identity_known": ("identity", "input-feature", "identity.known", fixture),
        "source_readable_hash_matches": (
            "readability",
            "input-feature",
            "source_hash.matches",
            fixture["sha256"],
        ),
        "knowledge_snapshot_known": (
            "identity",
            "knowledge-snapshot",
            "identity.known",
            knowledge_snapshot,
        ),
        "critical_constraints_resolved": (
            "verification",
            "proposal",
            "critical_constraints.resolved",
            True,
        ),
        "no_critical_contradictions": (
            "verification",
            "proposal",
            "critical_contradictions.absent",
            True,
        ),
        "geometry_compatible": (
            "geometry",
            "input-feature.geometry",
            "geometry_type.equals",
            semantic_values["geometry"],
        ),
        "tool_allowlist_bound": (
            "tool",
            "proposal",
            "tool_allowlist.equals",
            {"version": ALLOWLIST_VERSION, "sha256": allowlist_sha256},
        ),
        "roots_disjoint": ("mutation", "execution", "source_output.disjoint", True),
        "proposal_hash_valid": ("identity", "proposal", "proposal_hash.valid", True),
        "research_authorization_valid": (
            "authority",
            "execution",
            "research_authorization.valid",
            True,
        ),
        "unresolved_guards_bounded": (
            "binding",
            "proposal",
            "unresolved_guards.bounded",
            True,
        ),
        "classification_exact": (
            "attribute",
            "derived-feature",
            "classification.equals",
            semantic_values["classification"],
        ),
        "geometry_point_unchanged": (
            "geometry",
            "derived-feature.geometry",
            "geometry.equals_source",
            semantic_values["geometry"],
        ),
        "line_style_exact": (
            "attribute",
            "derived-feature.portrayal",
            "line_style.equals",
            semantic_values["line_style"],
        ),
        "color_code_exact": (
            "attribute",
            "derived-feature.portrayal",
            "color_code.equals",
            semantic_values["color_code"],
        ),
        "observed_color_exact": (
            "attribute",
            "derived-feature.portrayal",
            "observed_color.equals",
            semantic_values["observed_color"],
        ),
        "source_authority_evidence_bound": (
            "authority",
            "derived-feature",
            "source_authority.evidence_bound",
            semantic_values["source_authority_handled"],
        ),
        "product_layer_unresolved": (
            "binding",
            "derived-feature",
            "product_layer.equals",
            semantic_values["product_layer"],
        ),
        "physical_gates_unresolved": (
            "binding",
            "derived-feature",
            "physical_portrayal_gates.unresolved",
            True,
        ),
        "operations_match_plan": (
            "verification",
            "execution-receipt",
            "operations.match_plan",
            True,
        ),
        "receipt_bound_to_proposal": (
            "identity",
            "execution-receipt",
            "proposal_hash.bound",
            True,
        ),
        "source_unchanged": ("mutation", "input-feature", "source_hash.unchanged", True),
        "declared_files_only": (
            "mutation",
            "isolated-output",
            "unexpected_files.absent",
            True,
        ),
    }
    if condition_id not in values:
        raise RQ2DemoError(f"Unknown condition identifier: {condition_id}")
    kind, subject, predicate, expected = values[condition_id]
    refs = _constraint_refs_for_condition(condition_id, constraint_refs, constraints)
    return {
        "condition_id": f"{prefix}:{condition_id}",
        "type": kind,
        "subject": subject,
        "predicate": predicate,
        "expected_value": expected,
        "constraint_refs": refs,
    }


def assemble_proposal(
    *,
    architecture: str,
    intent: str,
    draft: Mapping[str, Any],
    model_identity: str,
    fixture: Mapping[str, Any],
    created_at: str,
    allowlist_sha256: str,
    constraints: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    evidence_refs: Sequence[str] = (),
    retrieval_identity: Mapping[str, Any] | None = None,
    knowledge_snapshot_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    knowledge_mode = "none" if architecture == "llm-only" else "graphrag"
    constraint_sets = (
        {"resolved": [], "unresolved": [], "contradicted": []}
        if constraints is None
        else deepcopy(dict(constraints))
    )
    draft_hash = canonical_sha256(draft)
    proposal_id = f"rq2-proposal:{architecture}:{draft_hash[:24]}"
    run_identity = f"rq2-run:{architecture}:{draft_hash[:24]}"
    semantic_values = draft["semantic_values"]
    all_draft_refs = sorted(set(draft["constraint_refs"]))
    fixture_identity = {"id": fixture["id"], "sha256": fixture["sha256"]}
    input_identities = [deepcopy(fixture_identity)]
    if knowledge_snapshot_identity is not None:
        input_identities.append(deepcopy(dict(knowledge_snapshot_identity)))
    plan: list[dict[str, Any]] = []
    for position, source_step in enumerate(draft["steps"], start=1):
        operation = source_step["operation"]
        tool = source_step["tool"]
        step_id = source_step["step_id"]
        if not str(step_id).startswith("step:"):
            step_id = f"step:{position:02d}-{str(step_id).replace('_', '-')}"
        inputs: dict[str, Any]
        if operation == "read_feature":
            inputs = {
                "artifact_identity": deepcopy(fixture_identity),
                "feature_selector": fixture["feature_selector"],
            }
        elif operation == "validate_source_authority":
            inputs = {
                "source_identity": deepcopy(fixture_identity),
                "evidence_refs": list(evidence_refs),
                "knowledge_snapshot_identity": deepcopy(knowledge_snapshot_identity),
            }
        elif operation == "validate_geometry_type":
            inputs = {
                "feature_snapshot_identity": deepcopy(fixture_identity),
                "expected_geometry_type": semantic_values["geometry"],
            }
        elif operation == "derive_target_representation":
            inputs = {
                "feature_snapshot_identity": deepcopy(fixture_identity),
                "resolved_constraint_values": deepcopy(dict(semantic_values)),
            }
        elif operation == "write_derived_artifact":
            inputs = {
                "derived_representation_identity": {
                    "id": f"in-memory-representation:{run_identity}",
                    "sha256": canonical_sha256(semantic_values),
                },
                "isolated_output_identity": f"isolated-output:{run_identity}",
            }
        else:
            inputs = {
                "proposal_hash": "bind:top-level-proposal_hash",
                "execution_receipt_identity": f"execution-receipt:{run_identity}",
                "expected_postconditions": list(draft["expected_postcondition_ids"]),
            }
        step_refs = list(draft["constraint_refs"])
        preconditions = [
            _condition(
                identifier,
                semantic_values,
                step_refs,
                constraint_sets,
                prefix=f"precondition:{position:02d}",
                fixture=fixture,
                knowledge_snapshot=knowledge_snapshot_identity,
                allowlist_sha256=allowlist_sha256,
            )
            for identifier in draft["precondition_ids"]
        ]
        postconditions = [
            _condition(
                identifier,
                semantic_values,
                step_refs,
                constraint_sets,
                prefix=f"postcondition:{position:02d}",
                fixture=fixture,
                knowledge_snapshot=knowledge_snapshot_identity,
                allowlist_sha256=allowlist_sha256,
            )
            for identifier in draft["expected_postcondition_ids"]
        ]
        plan.append(
            {
                "step_id": step_id,
                "operation": operation,
                "tool": tool,
                "inputs": inputs,
                "input_identities": deepcopy(input_identities),
                "preconditions": preconditions,
                "expected_postconditions": postconditions,
                "constraint_refs": step_refs,
                "trace_basis": list(source_step["trace_basis"]),
            }
        )
    write_steps = [
        item["step_id"] for item in plan if item["operation"] == "write_derived_artifact"
    ]
    authorizations = []
    if write_steps:
        authorizations.append(
            {
                "authorization_type": "research-derived-artifact-execution",
                "scope": (
                    "one content-addressed fixture; isolated derived output; no source mutation; "
                    "no authoritative render"
                ),
                "bound_proposal_hash": ZERO_HASH,
                "required_before_step": write_steps[0],
            }
        )
    expected_postconditions = [
        _condition(
            identifier,
            semantic_values,
            all_draft_refs,
            constraint_sets,
            prefix="postcondition:top",
            fixture=fixture,
            knowledge_snapshot=knowledge_snapshot_identity,
            allowlist_sha256=allowlist_sha256,
        )
        for identifier in draft["expected_postcondition_ids"]
    ]
    constraint_ids = sorted(item["constraint_id"] for item in _all_constraints(constraint_sets))
    proposal = {
        "proposal_id": proposal_id,
        "proposal_version": PROPOSAL_VERSION,
        "proposal_hash": ZERO_HASH,
        "intent": {
            "intent_id": _intent_id(intent),
            "raw_text": intent,
            "normalized_goal": draft["normalized_goal"],
        },
        "knowledge": {
            "mode": knowledge_mode,
            "evidence_refs": sorted(set(evidence_refs)),
            "retrieval_identity": deepcopy(retrieval_identity),
            "knowledge_snapshot_identity": deepcopy(knowledge_snapshot_identity),
        },
        "constraints": constraint_sets,
        "decision": {
            "execution_status": draft["execution_status"],
            "reason_codes": list(dict.fromkeys(draft["reason_codes"])),
        },
        "plan": plan,
        "required_authorizations": authorizations,
        "expected_postconditions": expected_postconditions,
        "expected_final_state": {
            "source_unchanged": True,
            "derived_artifact": {
                "kind": "symbolic-fire-hydrant-research-feature",
                "semantic_values": deepcopy(dict(semantic_values)),
                "authoritative_render": False,
            },
            "verification_required": True,
        },
        "provenance_seed": {
            "proposal_id": proposal_id,
            "intent_id": _intent_id(intent),
            "knowledge_snapshot_identity": deepcopy(knowledge_snapshot_identity),
            "evidence_refs": sorted(set(evidence_refs)),
            "constraint_ids": constraint_ids,
            "planner_identity": PLANNER_VERSION,
            "model_identity": model_identity,
            "plan_identity": canonical_sha256(plan),
            "input_feature_identities": [deepcopy(fixture_identity)],
            "tool_allowlist_version": ALLOWLIST_VERSION,
            "tool_allowlist_sha256": allowlist_sha256,
            "validator_version": VALIDATOR_VERSION,
            "run_identity": run_identity,
            "created_at": created_at,
        },
    }
    return bind_proposal_hash(proposal)


def _schema_errors(repository_root: Path, proposal: Mapping[str, Any]) -> list[str]:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource
    except ImportError as error:
        raise RQ2DemoError("jsonschema and referencing are required for RQ2 validation.") from error
    proposal_schema = _read_json(
        repository_root / "data/specifications/rq2-proposal-schema-v1.0.json"
    )
    constraint_schema = _read_json(
        repository_root / "data/specifications/rq2-constraint-schema-v1.0.json"
    )
    registry = Registry().with_resource(
        constraint_schema["$id"], Resource.from_contents(constraint_schema)
    )
    validator = Draft202012Validator(
        proposal_schema, registry=registry, format_checker=FormatChecker()
    )
    return [
        f"{'/'.join(str(item) for item in error.absolute_path) or '$'}: {error.message}"
        for error in sorted(validator.iter_errors(dict(proposal)), key=lambda item: list(item.path))
    ]


def _check(
    checks: list[dict[str, Any]],
    rule_id: str,
    passed: bool,
    *,
    expected: Any,
    observed: Any,
    failure_code: str,
) -> None:
    if failure_code not in FAILURE_CODES:
        raise RQ2DemoError(f"Unknown RQ2 failure taxonomy code: {failure_code}")
    checks.append(
        {
            "rule_id": rule_id,
            "status": "PASS" if passed else "FAIL",
            "expected": expected,
            "observed": observed,
            "failure_code": None if passed else failure_code,
        }
    )


def validate_proposal(
    repository_root: Path,
    proposal: Mapping[str, Any],
    *,
    expected_constraints: Mapping[str, Sequence[Mapping[str, Any]]] | None,
    retrieval_package: Mapping[str, Any] | None,
    fixture: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply the frozen ordered validator with no model calls and no repair."""

    checks: list[dict[str, Any]] = []
    errors = _schema_errors(repository_root, proposal)
    _check(
        checks,
        "V01_SCHEMA",
        not errors,
        expected="valid rq2-proposal/1.0",
        observed=errors or "valid",
        failure_code="PLAN_SCHEMA_INVALID",
    )
    if errors:
        return _validation_result(checks)
    actual_hash = proposal_hash(proposal)
    _check(
        checks,
        "V02_PROPOSAL_HASH",
        proposal["proposal_hash"] == actual_hash,
        expected=actual_hash,
        observed=proposal["proposal_hash"],
        failure_code="PROPOSAL_HASH_MISMATCH",
    )
    expected_intent_id = _intent_id(proposal["intent"]["raw_text"])
    _check(
        checks,
        "V02_INTENT_ID",
        proposal["intent"]["intent_id"] == expected_intent_id,
        expected=expected_intent_id,
        observed=proposal["intent"]["intent_id"],
        failure_code="PLAN_SCHEMA_INVALID",
    )
    expected_plan_identity = canonical_sha256(proposal["plan"])
    _check(
        checks,
        "V02_PLAN_IDENTITY",
        proposal["provenance_seed"]["plan_identity"] == expected_plan_identity,
        expected=expected_plan_identity,
        observed=proposal["provenance_seed"]["plan_identity"],
        failure_code="PROPOSAL_HASH_MISMATCH",
    )
    constraints = proposal["constraints"]
    all_constraints = _all_constraints(constraints)
    step_ids = [item["step_id"] for item in proposal["plan"]]
    condition_ids = [
        condition["condition_id"]
        for step in proposal["plan"]
        for group in ("preconditions", "expected_postconditions")
        for condition in step[group]
    ]
    constraint_ids = [item["constraint_id"] for item in all_constraints]
    unique = (
        len(step_ids) == len(set(step_ids))
        and len(condition_ids) == len(set(condition_ids))
        and len(constraint_ids) == len(set(constraint_ids))
    )
    _check(
        checks,
        "V03_UNIQUE_IDENTITIES",
        unique,
        expected="unique step, condition, and constraint identities",
        observed={"steps": step_ids, "conditions": condition_ids, "constraints": constraint_ids},
        failure_code="PLAN_SCHEMA_INVALID",
    )
    placement_valid = all(
        item["resolution_status"] == status
        for status in ("resolved", "unresolved", "contradicted")
        for item in constraints[status]
    )
    _check(
        checks,
        "V04_CONSTRAINT_PLACEMENT",
        placement_valid,
        expected="constraint array matches resolution_status",
        observed=placement_valid,
        failure_code="PLAN_SCHEMA_INVALID",
    )
    mode = proposal["knowledge"]["mode"]
    if mode == "none":
        isolated = (
            not proposal["knowledge"]["evidence_refs"]
            and proposal["knowledge"]["retrieval_identity"] is None
            and proposal["knowledge"]["knowledge_snapshot_identity"] is None
            and not all_constraints
        )
        _check(
            checks,
            "V05_BASELINE_ISOLATION",
            isolated,
            expected="no evidence, knowledge identities, or constraints",
            observed=proposal["knowledge"],
            failure_code="EVIDENCE_TRACE_BROKEN",
        )
    else:
        package_refs = {item["id"] for item in (retrieval_package or {}).get("evidence_nodes", [])}
        declared_refs = set(proposal["knowledge"]["evidence_refs"])
        evidence_valid = bool(package_refs) and declared_refs <= package_refs
        _check(
            checks,
            "V05_EVIDENCE_MEMBERSHIP",
            evidence_valid,
            expected="all evidence refs present in immutable retrieval package",
            observed=sorted(declared_refs - package_refs),
            failure_code="EVIDENCE_TRACE_BROKEN",
        )
    expected_sets = (
        {"resolved": [], "unresolved": [], "contradicted": []}
        if expected_constraints is None
        else expected_constraints
    )
    exact_constraints = canonical_sha256(constraints) == canonical_sha256(expected_sets)
    _check(
        checks,
        "V06_CONSTRAINT_EVIDENCE_CONSISTENCY",
        exact_constraints,
        expected=canonical_sha256(expected_sets),
        observed=canonical_sha256(constraints),
        failure_code="CONSTRAINT_FABRICATED",
    )
    known_constraints = set(constraint_ids)
    referenced_constraints = {
        ref
        for step in proposal["plan"]
        for ref in [
            *step["constraint_refs"],
            *(ref for item in step["preconditions"] for ref in item["constraint_refs"]),
            *(ref for item in step["expected_postconditions"] for ref in item["constraint_refs"]),
        ]
    }
    unknown_refs = referenced_constraints - known_constraints
    _check(
        checks,
        "V07_CONSTRAINT_REFERENCES",
        not unknown_refs,
        expected="references resolve to declared constraints",
        observed=sorted(unknown_refs),
        failure_code="EVIDENCE_TRACE_BROKEN",
    )
    required_ids = {
        item["constraint_id"]
        for item in all_constraints
        if item["execution_effect"] in {"required", "forbidden", "guard"}
    }
    omitted = required_ids - referenced_constraints
    declared_block = proposal["decision"]["execution_status"] == "BLOCK"
    _check(
        checks,
        "V08_REQUIRED_CONSTRAINT_COVERAGE",
        not omitted or declared_block,
        expected=("not applicable to empty BLOCK plan" if declared_block else sorted(required_ids)),
        observed=sorted(referenced_constraints),
        failure_code="CONSTRAINT_OMITTED_FROM_PLAN",
    )
    allowlist = _read_json(repository_root / "data/specifications/rq2-tool-allowlist-v1.0.json")
    allowlisted = {item["tool_id"]: item["operation_type"] for item in allowlist["tools"]}
    tool_errors = [
        {"step": item["step_id"], "operation": item["operation"], "tool": item["tool"]}
        for item in proposal["plan"]
        if item["tool"] not in allowlisted or allowlisted[item["tool"]] != item["operation"]
    ]
    _check(
        checks,
        "V09_TOOL_ALLOWLIST",
        not tool_errors,
        expected="exact allowlisted operation/tool bindings",
        observed=tool_errors,
        failure_code="UNKNOWN_TOOL",
    )
    serialized_plan = canonical_json(proposal["plan"]).decode("utf-8").casefold()
    forbidden_literals = [
        literal
        for literal in (
            "/bin/sh",
            "shell_command",
            "python -c",
            "subprocess",
            "http://",
            "https://",
        )
        if literal in serialized_plan
    ]
    _check(
        checks,
        "V09_FORBIDDEN_OPERATIONS",
        not forbidden_literals,
        expected="no shell, unrestricted Python, network, or direct endpoint",
        observed=forbidden_literals,
        failure_code="FORBIDDEN_OPERATION",
    )
    fixture_identity = {"id": fixture["id"], "sha256": fixture["sha256"]}
    declared_inputs = {canonical_sha256(fixture_identity)}
    snapshot = proposal["knowledge"]["knowledge_snapshot_identity"]
    if snapshot is not None:
        declared_inputs.add(canonical_sha256(snapshot))
    invalid_inputs = [
        identity
        for step in proposal["plan"]
        for identity in step["input_identities"]
        if canonical_sha256(identity) not in declared_inputs
    ]
    _check(
        checks,
        "V10_INPUT_IDENTITIES",
        not invalid_inputs,
        expected="only registered fixture/snapshot identities",
        observed=invalid_inputs,
        failure_code="PRECONDITION_FAILED",
    )
    observed_pre = {
        item["condition_id"].rsplit(":", 1)[1]
        for step in proposal["plan"]
        for item in step["preconditions"]
    }
    required_pre = set(MANDATORY_PRECONDITIONS)
    if mode == "graphrag":
        required_pre.add(CONSTRAINED_PRECONDITION)
    missing_pre = required_pre - observed_pre
    _check(
        checks,
        "V11_PRECONDITIONS",
        not missing_pre or declared_block,
        expected=("not applicable to empty BLOCK plan" if declared_block else sorted(required_pre)),
        observed=sorted(observed_pre),
        failure_code="PRECONDITION_MISSING",
    )
    observed_post = {
        item["condition_id"].rsplit(":", 1)[1] for item in proposal["expected_postconditions"]
    }
    missing_post = set(MANDATORY_POSTCONDITIONS) - observed_post
    step_post_complete = all(step["expected_postconditions"] for step in proposal["plan"])
    _check(
        checks,
        "V12_POSTCONDITIONS",
        not missing_post and step_post_complete,
        expected=list(MANDATORY_POSTCONDITIONS),
        observed=sorted(observed_post),
        failure_code="POSTCONDITION_MISSING",
    )
    trace_errors = [
        step["step_id"]
        for step in proposal["plan"]
        if not step["trace_basis"]
        or (
            mode == "graphrag"
            and step["operation"]
            in {
                "validate_source_authority",
                "validate_geometry_type",
                "derive_target_representation",
                "write_derived_artifact",
            }
            and ("knowledge_constraint" not in step["trace_basis"] or not step["constraint_refs"])
        )
    ]
    _check(
        checks,
        "V13_TRACE_BASIS",
        not trace_errors,
        expected="truthful trace basis for every step",
        observed=trace_errors,
        failure_code="EVIDENCE_TRACE_BROKEN",
    )
    semantic_values = proposal["expected_final_state"]["derived_artifact"]["semantic_values"]
    unresolved_binding = [
        item for item in constraints["unresolved"] if item["type"] == "relationship_binding"
    ]
    guessed_binding = bool(unresolved_binding) and semantic_values.get("product_layer") is not None
    _check(
        checks,
        "V14_UNRESOLVED_BINDING",
        not guessed_binding,
        expected=None,
        observed=semantic_values.get("product_layer"),
        failure_code="UNRESOLVED_BINDING_GUESSED",
    )
    unresolved_guards = [
        item for item in constraints["unresolved"] if item["execution_effect"] == "guard"
    ]
    render_steps = [
        item["step_id"]
        for item in proposal["plan"]
        if item["tool"] == "rq2.portrayal.render-review/1.0"
    ]
    _check(
        checks,
        "V15_MUTATION_AND_RENDER_BOUNDARY",
        not render_steps if unresolved_guards else True,
        expected="no render while physical gates remain unresolved",
        observed=render_steps,
        failure_code="FORBIDDEN_OPERATION",
    )
    critical_contradictions = [
        item
        for item in constraints["contradicted"]
        if item["execution_effect"] in {"required", "guard"}
    ]
    expected_decision = (
        "BLOCK"
        if critical_contradictions
        else "PROCEED_WITH_BOUNDED_UNRESOLVED"
        if unresolved_guards
        else "PROCEED"
    )
    _check(
        checks,
        "V16_DECISION",
        proposal["decision"]["execution_status"] == expected_decision,
        expected=expected_decision,
        observed=proposal["decision"]["execution_status"],
        failure_code=(
            "CONSTRAINT_CONTRADICTED" if critical_contradictions else "CONSTRAINT_UNRESOLVED"
        ),
    )
    block_shape = expected_decision != "BLOCK" or not proposal["plan"]
    _check(
        checks,
        "V17_BLOCK_HAS_NO_PLAN",
        block_shape,
        expected="empty executable plan for BLOCK",
        observed=len(proposal["plan"]),
        failure_code="FORBIDDEN_OPERATION",
    )
    declarations = proposal["required_authorizations"]
    write_step_ids = {
        item["step_id"]
        for item in proposal["plan"]
        if item["operation"] == "write_derived_artifact"
    }
    authorization_valid = bool(declarations) and all(
        item["bound_proposal_hash"] == proposal["proposal_hash"]
        and item["required_before_step"] in write_step_ids
        for item in declarations
    )
    _check(
        checks,
        "V18_AUTHORIZATION_DECLARATIONS",
        authorization_valid if expected_decision != "BLOCK" else not declarations,
        expected="proposal-hash-bound declaration gates a real write step",
        observed=declarations,
        failure_code="PRECONDITION_MISSING",
    )
    return _validation_result(checks)


def _validation_result(checks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    failures = [item for item in checks if item["status"] == "FAIL"]
    return {
        "validator_version": VALIDATOR_VERSION,
        "model_calls": 0,
        "status": "PASS" if not failures else "FAIL",
        "checks": list(checks),
        "failure_taxonomy": list(
            dict.fromkeys(item["failure_code"] for item in failures if item["failure_code"])
        ),
    }


def _load_feature(path: Path, selector: str) -> dict[str, Any]:
    payload = _read_json(path)
    matches = [item for item in payload.get("features", []) if item.get("id") == selector]
    if len(matches) != 1:
        raise RQ2DemoError("The exact fixture selector did not resolve one feature.")
    feature = matches[0]
    geometry = feature.get("geometry", {})
    coordinates = geometry.get("coordinates")
    finite = (
        isinstance(coordinates, list)
        and len(coordinates) == 2
        and all(
            not isinstance(item, bool) and isinstance(item, (int, float)) and math.isfinite(item)
            for item in coordinates
        )
    )
    if geometry.get("type") != "Point" or not finite:
        raise RQ2DemoError("The frozen fixture is not a finite Point feature.")
    return deepcopy(feature)


def execute_proposal(
    repository_root: Path,
    proposal: Mapping[str, Any],
    validation: Mapping[str, Any],
    *,
    fixture_path: Path,
    output_root: Path,
    retrieval_package: Mapping[str, Any] | None,
    fault: str | None = None,
) -> dict[str, Any]:
    """Run only approved semantic tools after a complete read-only gate."""

    started = time.monotonic()
    tool_calls: list[dict[str, Any]] = []
    source_sha_before = sha256_file(fixture_path)
    if validation["status"] != "PASS":
        return {
            "executor_version": EXECUTOR_VERSION,
            "status": "BLOCKED",
            "reason_codes": list(validation["failure_taxonomy"]),
            "tool_calls": [],
            "mutation_started": False,
            "execution_latency_ms": round((time.monotonic() - started) * 1000),
        }
    if proposal["decision"]["execution_status"] == "BLOCK":
        return {
            "executor_version": EXECUTOR_VERSION,
            "status": "BLOCKED",
            "reason_codes": ["CONSTRAINT_CONTRADICTED"],
            "tool_calls": [],
            "mutation_started": False,
            "execution_latency_ms": round((time.monotonic() - started) * 1000),
        }
    if output_root.exists():
        raise RQ2DemoError("The isolated execution output root must not already exist.")
    semantic_values = proposal["expected_final_state"]["derived_artifact"]["semantic_values"]
    feature: dict[str, Any] | None = None
    authority_valid = False
    geometry_valid = False
    representation: dict[str, Any] | None = None
    evidence_ids = {item["id"] for item in (retrieval_package or {}).get("evidence_nodes", [])}
    # Read-only precondition phase: no output path is created before every gate passes.
    for step in proposal["plan"]:
        if step["operation"] == "read_feature":
            feature = _load_feature(fixture_path, step["inputs"]["feature_selector"])
            tool_calls.append(
                {
                    "step_id": step["step_id"],
                    "tool": step["tool"],
                    "status": "PASS",
                    "mutation": False,
                }
            )
        elif step["operation"] == "validate_source_authority":
            refs = set(step["inputs"]["evidence_refs"])
            snapshot = step["inputs"]["knowledge_snapshot_identity"]
            authority_valid = bool(refs) and refs <= evidence_ids and snapshot is not None
            tool_calls.append(
                {
                    "step_id": step["step_id"],
                    "tool": step["tool"],
                    "status": "PASS" if authority_valid else "FAIL",
                    "mutation": False,
                    "matched_evidence_refs": sorted(refs & evidence_ids),
                }
            )
        elif step["operation"] == "validate_geometry_type":
            observed = None if feature is None else feature["geometry"]["type"]
            geometry_valid = observed == step["inputs"]["expected_geometry_type"]
            tool_calls.append(
                {
                    "step_id": step["step_id"],
                    "tool": step["tool"],
                    "status": "PASS" if geometry_valid else "FAIL",
                    "mutation": False,
                    "observed_geometry_type": observed,
                }
            )
        if step["operation"] == "derive_target_representation":
            break
    gates = {
        "source_hash_matches": source_sha_before == sha256_file(fixture_path),
        "feature_read": feature is not None,
        "source_authority_evidence_bound": authority_valid,
        "geometry_compatible": geometry_valid,
        "proposal_hash_valid": proposal_hash(proposal) == proposal["proposal_hash"],
        "critical_contradictions_absent": not proposal["constraints"]["contradicted"],
        "product_layer_unresolved": semantic_values.get("product_layer") is None,
        "output_absent": not output_root.exists(),
        "research_authorization_bound": all(
            item["bound_proposal_hash"] == proposal["proposal_hash"]
            for item in proposal["required_authorizations"]
        ),
    }
    if not all(gates.values()):
        return {
            "executor_version": EXECUTOR_VERSION,
            "status": "BLOCKED",
            "reason_codes": ["PRECONDITION_FAILED"],
            "precondition_gate": gates,
            "tool_calls": tool_calls,
            "mutation_started": False,
            "execution_latency_ms": round((time.monotonic() - started) * 1000),
        }
    output_root.mkdir(parents=True)
    derived_path = output_root / "derived-feature.geojson"
    for step in proposal["plan"]:
        operation = step["operation"]
        if operation == "derive_target_representation":
            assert feature is not None
            actual_values = deepcopy(dict(semantic_values))
            if fault == "classification_mismatch":
                actual_values["classification"] = "fault-injected-mismatch"
            representation = {
                "type": "FeatureCollection",
                "name": "rq2-symbolic-derived-fire-hydrant",
                "features": [
                    {
                        "type": "Feature",
                        "id": feature["id"],
                        "geometry": deepcopy(feature["geometry"]),
                        "properties": {
                            **deepcopy(feature["properties"]),
                            "nma_classification": actual_values["classification"],
                            "nma_portrayal": {
                                "line_code": actual_values["line_style"],
                                "color_code": actual_values["color_code"],
                                "observed_color": actual_values["observed_color"],
                                "physical_profile": None,
                            },
                            "product_layer": actual_values["product_layer"],
                            "source_authority_evidence_bound": authority_valid,
                            "authoritative_render": False,
                            "proposal_hash": proposal["proposal_hash"],
                        },
                    }
                ],
            }
            tool_calls.append(
                {
                    "step_id": step["step_id"],
                    "tool": step["tool"],
                    "status": "PASS",
                    "mutation": False,
                    "output_identity": canonical_sha256(representation),
                }
            )
        elif operation == "write_derived_artifact":
            if representation is None:
                raise RQ2DemoError("The plan attempted to write before deriving a representation.")
            derived_path.write_bytes(canonical_json(representation) + b"\n")
            tool_calls.append(
                {
                    "step_id": step["step_id"],
                    "tool": step["tool"],
                    "status": "PASS",
                    "mutation": True,
                    "created": derived_path.name,
                    "sha256": sha256_file(derived_path),
                }
            )
    if not derived_path.is_file():
        return {
            "executor_version": EXECUTOR_VERSION,
            "status": "FAIL",
            "reason_codes": ["EXECUTION_FAILED"],
            "precondition_gate": gates,
            "tool_calls": tool_calls,
            "mutation_started": True,
            "execution_latency_ms": round((time.monotonic() - started) * 1000),
        }
    source_sha_after = sha256_file(fixture_path)
    receipt = {
        "schema": "nma.rq2-execution-receipt/1.0",
        "executor_version": EXECUTOR_VERSION,
        "proposal_id": proposal["proposal_id"],
        "proposal_hash": proposal["proposal_hash"],
        "decision": proposal["decision"]["execution_status"],
        "approved_operations": [item["tool"] for item in proposal["plan"]],
        "tool_calls": tool_calls,
        "source_sha256_before": source_sha_before,
        "source_sha256_after": source_sha_after,
        "created_files": [{"path": derived_path.name, "sha256": sha256_file(derived_path)}],
        "fault_injection": fault,
    }
    receipt_path = output_root / "execution-receipt.json"
    _write_json(receipt_path, receipt)
    return {
        "executor_version": EXECUTOR_VERSION,
        "status": "PASS",
        "reason_codes": [],
        "precondition_gate": gates,
        "tool_calls": tool_calls,
        "mutation_started": True,
        "derived_artifact": artifact_identity(
            f"derived-artifact:{proposal['proposal_id']}", sha256_file(derived_path)
        ),
        "execution_receipt": artifact_identity(
            f"execution-receipt:{proposal['proposal_id']}", sha256_file(receipt_path)
        ),
        "output_root": str(output_root),
        "execution_latency_ms": round((time.monotonic() - started) * 1000),
    }


def verify_execution(
    proposal: Mapping[str, Any],
    execution: Mapping[str, Any],
    *,
    fixture_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    checks: list[dict[str, Any]] = []
    if execution["status"] != "PASS":
        return {
            "verifier_version": VERIFIER_VERSION,
            "model_calls": 0,
            "status": "N/A",
            "checks": [],
            "failure_taxonomy": [],
            "verification_latency_ms": round((time.monotonic() - started) * 1000),
        }
    derived_path = output_root / "derived-feature.geojson"
    receipt_path = output_root / "execution-receipt.json"
    derived = _read_json(derived_path)
    receipt = _read_json(receipt_path)
    feature = derived["features"][0]
    source = _load_feature(fixture_path, feature["id"])
    properties = feature["properties"]
    portrayal = properties["nma_portrayal"]
    semantic_values = proposal["expected_final_state"]["derived_artifact"]["semantic_values"]

    def exact(identifier: str, expected: Any, observed: Any, code: str) -> None:
        _check(
            checks,
            identifier,
            observed == expected,
            expected=expected,
            observed=observed,
            failure_code=code,
        )

    exact(
        "P01_CLASSIFICATION",
        semantic_values["classification"],
        properties.get("nma_classification"),
        "POSTCONDITION_VIOLATION",
    )
    exact(
        "P02_GEOMETRY_TYPE",
        semantic_values["geometry"],
        feature["geometry"].get("type"),
        "POSTCONDITION_VIOLATION",
    )
    exact(
        "P02_GEOMETRY_UNCHANGED",
        source["geometry"],
        feature["geometry"],
        "POSTCONDITION_VIOLATION",
    )
    exact(
        "P03_LINE_STYLE",
        semantic_values["line_style"],
        portrayal.get("line_code"),
        "POSTCONDITION_VIOLATION",
    )
    exact(
        "P04_COLOR_CODE",
        semantic_values["color_code"],
        portrayal.get("color_code"),
        "POSTCONDITION_VIOLATION",
    )
    exact(
        "P04_OBSERVED_COLOR",
        semantic_values["observed_color"],
        portrayal.get("observed_color"),
        "POSTCONDITION_VIOLATION",
    )
    exact(
        "P05_SOURCE_AUTHORITY",
        semantic_values["source_authority_handled"],
        properties.get("source_authority_evidence_bound"),
        "POSTCONDITION_VIOLATION",
    )
    exact(
        "P06_PRODUCT_LAYER_UNRESOLVED",
        None,
        properties.get("product_layer"),
        "UNRESOLVED_BINDING_GUESSED",
    )
    exact(
        "P07_PHYSICAL_GATES_UNRESOLVED",
        None,
        portrayal.get("physical_profile"),
        "POSTCONDITION_VIOLATION",
    )
    exact(
        "P08_OPERATIONS_MATCH_PLAN",
        [item["tool"] for item in proposal["plan"] if item["operation"] != "verify_postconditions"],
        [item["tool"] for item in receipt["tool_calls"]],
        "POSTCONDITION_VIOLATION",
    )
    exact(
        "P09_RECEIPT_BOUND",
        proposal["proposal_hash"],
        receipt.get("proposal_hash"),
        "POSTCONDITION_VIOLATION",
    )
    exact(
        "P10_SOURCE_UNCHANGED",
        receipt.get("source_sha256_before"),
        receipt.get("source_sha256_after"),
        "UNEXPECTED_MUTATION",
    )
    exact(
        "P11_DECLARED_FILES_ONLY",
        ["derived-feature.geojson", "execution-receipt.json"],
        sorted(path.name for path in output_root.iterdir()),
        "UNEXPECTED_MUTATION",
    )
    failures = [item for item in checks if item["status"] == "FAIL"]
    result = {
        "verifier_version": VERIFIER_VERSION,
        "model_calls": 0,
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failure_taxonomy": list(
            dict.fromkeys(item["failure_code"] for item in failures if item["failure_code"])
        ),
        "verification_latency_ms": round((time.monotonic() - started) * 1000),
    }
    _write_json(output_root / "verification.json", result)
    return result


def evaluate_run(
    proposal: Mapping[str, Any],
    validation: Mapping[str, Any],
    execution: Mapping[str, Any],
    verification: Mapping[str, Any],
    truth: Mapping[str, Any],
) -> dict[str, Any]:
    semantic = proposal["expected_final_state"]["derived_artifact"]["semantic_values"]
    semantic_checks = {
        "classification": semantic["classification"] == truth["classification"],
        "geometry": semantic["geometry"] == truth["geometry"],
        "line_style": semantic["line_style"] == truth["line_style"],
        "color_code": semantic["color_code"] == truth["color_code"],
        "observed_color": semantic["observed_color"] == truth["observed_color"],
        "source_authority": semantic["source_authority_handled"] is True,
        "product_layer_unresolved": semantic["product_layer"] is None,
    }
    required_constraint_ids = {
        item["constraint_id"]
        for item in _all_constraints(proposal["constraints"])
        if item["execution_effect"] in {"required", "guard", "forbidden"}
    }
    referenced = {ref for step in proposal["plan"] for ref in step["constraint_refs"]}
    observed_pre = {
        item["condition_id"].rsplit(":", 1)[1]
        for step in proposal["plan"]
        for item in step["preconditions"]
    }
    required_pre = set(MANDATORY_PRECONDITIONS)
    if proposal["knowledge"]["mode"] == "graphrag":
        required_pre.add(CONSTRAINED_PRECONDITION)
    observed_post = {
        item["condition_id"].rsplit(":", 1)[1] for item in proposal["expected_postconditions"]
    }
    applicable = [
        semantic_checks["classification"],
        semantic_checks["geometry"],
        semantic_checks["line_style"],
        semantic_checks["color_code"],
        semantic_checks["observed_color"],
        semantic_checks["product_layer_unresolved"],
    ]
    return {
        "semantic_checks": semantic_checks,
        "constraint_resolution_accuracy": {
            "correct": sum(applicable[:5]),
            "resolvable": 5,
            "ratio": sum(applicable[:5]) / 5,
        },
        "constraint_coverage": {
            "represented": len(required_constraint_ids & referenced),
            "required": len(required_constraint_ids),
            "ratio": (
                len(required_constraint_ids & referenced) / len(required_constraint_ids)
                if required_constraint_ids
                else None
            ),
        },
        "semantic_plan_validity": "PASS" if all(semantic_checks.values()) else "FAIL",
        "preconditions_completeness": {
            "represented": len(required_pre & observed_pre),
            "required": len(required_pre),
            "ratio": len(required_pre & observed_pre) / len(required_pre),
        },
        "postconditions_completeness": {
            "represented": len(set(MANDATORY_POSTCONDITIONS) & observed_post),
            "required": len(MANDATORY_POSTCONDITIONS),
            "ratio": len(set(MANDATORY_POSTCONDITIONS) & observed_post)
            / len(MANDATORY_POSTCONDITIONS),
        },
        "unresolved_knowledge_preservation": (
            "PASS" if semantic_checks["product_layer_unresolved"] else "FAIL"
        ),
        "executability": "PASS" if validation["status"] == "PASS" else "FAIL",
        "execution_success": "PASS" if execution["status"] == "PASS" else "FAIL",
        "constraint_preservation_after_execution": {
            "satisfied": sum(applicable) if execution["status"] == "PASS" else 0,
            "applicable": len(applicable),
            "ratio": sum(applicable) / len(applicable) if execution["status"] == "PASS" else 0,
        },
        "verification_success": "PASS" if verification["status"] == "PASS" else "FAIL",
        "unknown_or_forbidden_operations": sum(
            code in {"UNKNOWN_TOOL", "FORBIDDEN_OPERATION"}
            for code in validation["failure_taxonomy"]
        ),
    }


def validate_rq3_handoff(repository_root: Path, proposal: Mapping[str, Any]) -> dict[str, Any]:
    errors = _schema_errors(repository_root, proposal)
    required = {
        "proposal_id",
        "proposal_hash",
        "intent",
        "knowledge",
        "constraints",
        "decision",
        "plan",
        "required_authorizations",
        "expected_postconditions",
        "expected_final_state",
        "provenance_seed",
    }
    missing = required - set(proposal)
    checks = {
        "schema_valid": not errors,
        "proposal_hash_valid": proposal_hash(proposal) == proposal.get("proposal_hash"),
        "required_fields_complete": not missing,
        "authorization_declarations_present": bool(proposal.get("required_authorizations")),
        "expected_postconditions_present": bool(proposal.get("expected_postconditions")),
        "knowledge_identity_present": (
            proposal.get("knowledge", {}).get("knowledge_snapshot_identity") is not None
        ),
        "load_without_replanning": True,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "schema_errors": errors,
        "missing_fields": sorted(missing),
        "planner_model_calls": 0,
    }


def mutate_and_rehash(
    proposal: Mapping[str, Any], mutate: Callable[[dict[str, Any]], None]
) -> dict:
    changed = deepcopy(dict(proposal))
    mutate(changed)
    changed["provenance_seed"]["plan_identity"] = canonical_sha256(changed["plan"])
    return bind_proposal_hash(changed)

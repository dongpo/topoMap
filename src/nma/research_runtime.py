from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from agent_contracts.governance import request_identity

from nma.llm import LLMAdapter, LLMAdapterError
from nma.llm.base import canonical_json, validate_json_schema_subset
from nma.research_trace import RQ1TraceRecorder
from nma.runtime_graph_backend_v029 import (
    load_runtime_graph_settings,
    select_runtime_graph_backend_v029,
)


RQ1_RESULT_SCHEMA = "nma.ama-rq1-result/1.0"
RQ2_PLAN_SCHEMA = "nma.ama-bounded-plan/1.0"
PLAN_CATALOG_SCHEMA = "nma.ama-reviewed-plan-catalog/1.0"
RQ1_TRACE_REQUIRED_NODE_IDS = (
    "line-style:doc01:2",
    "portrayal-color:doc01:7",
    "portrayal-geometry:Point",
    "classification:doc01:9350906",
    "portrayal-rule:doc01:9350906",
    "portrayal-recipe:doc01:9350906:review-v1",
)


class ResearchRuntimeError(ValueError):
    """A live research mechanism crossed an evidence or planning boundary."""


def _sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _bounded_properties(properties: object) -> dict[str, Any]:
    if not isinstance(properties, Mapping):
        return {}
    keys = (
        "code",
        "feature_code",
        "feature_name",
        "name",
        "label",
        "geometry_role",
        "product_layer",
        "field_name",
        "source_layer",
    )
    return {key: properties[key] for key in keys if key in properties}


def _const_schema(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {
            "type": "object",
            "properties": {str(key): _const_schema(item) for key, item in value.items()},
            "required": list(value),
            "additionalProperties": False,
        }
    if isinstance(value, list):
        return {"type": "array", "const": value}
    if value is None:
        return {"type": "null", "const": None}
    if isinstance(value, bool):
        return {"type": "boolean", "const": value}
    if isinstance(value, int):
        return {"type": "integer", "const": value}
    if isinstance(value, float):
        return {"type": "number", "const": value}
    return {"type": "string", "const": value}


class AMAResearchRuntime:
    """Provider-neutral, proposal-only live research runtime for RQ1 and RQ2."""

    def __init__(
        self,
        *,
        repository_root: str | Path,
        adapter: LLMAdapter,
        graph_settings: dict[str, str] | None = None,
        trace_recorder: RQ1TraceRecorder | None = None,
    ) -> None:
        self.repository_root = Path(repository_root)
        self.adapter = adapter
        self.trace_recorder = trace_recorder
        settings = graph_settings or load_runtime_graph_settings(
            self.repository_root / ".env.local"
        )
        self.retriever, self.graph_backend_trace = select_runtime_graph_backend_v029(
            canonical_graph_path=(
                self.repository_root / "data/knowledge/nma-canonical-graph-v0.4.json"
            ),
            citation_registry_path=(
                self.repository_root / "data/knowledge/nma-citation-source-registry-v0.6.json"
            ),
            settings=settings,
        )
        self.graph_path = self.repository_root / "data/knowledge/nma-canonical-graph-v0.4.json"

    def _entity_candidates(self, request: str) -> list[dict[str, Any]]:
        ranked: dict[str, dict[str, Any]] = {}
        for item in [
            *self.retriever.alias_search(request, limit=12),
            *self.retriever.ranked_search(request, limit=12),
        ]:
            node = item["node"]
            current = ranked.get(node["id"])
            candidate = {
                "id": node["id"],
                "type": node["type"],
                "score": item["score"],
                "match_mode": item["match_mode"],
                "properties": _bounded_properties(node.get("properties")),
            }
            if current is None or candidate["score"] > current["score"]:
                ranked[node["id"]] = candidate
        return sorted(ranked.values(), key=lambda item: (-item["score"], item["id"]))[:12]

    def retrieve_with_live_interpretation(
        self, request: str
    ) -> tuple[dict[str, Any], dict[str, object]]:
        if not isinstance(request, str) or not request.strip() or len(request) > 500:
            raise ResearchRuntimeError(
                "Research requests must be non-empty and at most 500 characters."
            )
        candidates = self._entity_candidates(request)
        if not candidates:
            raise ResearchRuntimeError(
                "No allowlisted canonical graph candidates matched the request."
            )
        allowed_ids = [item["id"] for item in candidates]
        schema = {
            "type": "object",
            "properties": {
                "selected_node_ids": {
                    "type": "array",
                    "items": {"type": "string", "enum": allowed_ids},
                    "minItems": 1,
                    "maxItems": 6,
                }
            },
            "required": ["selected_node_ids"],
            "additionalProperties": False,
        }
        task = "resolve-bounded-canonical-graph-entities"
        instructions = (
            "Select only candidate node IDs directly relevant to the request. Return no query, "
            "Cypher, path, command, explanation, authorization, or invented identity."
        )
        context = {"request": request, "allowlisted_candidates": candidates}
        if self.trace_recorder is not None:
            self.trace_recorder.record_model_input(
                stage="entity resolution",
                task=task,
                instructions=instructions,
                context=context,
                output_schema=schema,
            )
        result = self.adapter.generate_structured(
            task=task,
            instructions=instructions,
            context=context,
            output_schema=schema,
        )
        if self.trace_recorder is not None:
            self.trace_recorder.record_model_output(stage="entity resolution", output=result.output)
        validate_json_schema_subset(result.output, schema)
        raw_selected = result.output["selected_node_ids"]
        selected = list(dict.fromkeys(raw_selected))
        if self.trace_recorder is not None:
            self.trace_recorder.record_resolved_entities(
                candidates=candidates,
                selected_ids=selected,
                graph_nodes=self.retriever.nodes,
            )
            self.trace_recorder.record_canonical_required_nodes(
                required_ids=list(RQ1_TRACE_REQUIRED_NODE_IDS),
                graph_nodes=self.retriever.nodes,
            )
        trace_candidates = [
            {
                "id": item["id"],
                "type": item["type"],
                "score": item["score"],
                "matched_terms": [],
                "match_mode": item["match_mode"],
            }
            for item in candidates
        ]
        package = self.retriever.package_from_seed_ids(
            request,
            selected,
            ranked_trace=trace_candidates,
            retrieval_mode="provider-neutral-entity-selection-plus-typed-canonical-graph",
            max_depth=2,
            max_nodes=60,
            extra_trace={
                "model_selected_seed_ids": selected,
                "duplicate_model_seed_ids_removed": len(raw_selected) - len(selected),
                "graph_backend": deepcopy(self.graph_backend_trace),
                "arbitrary_cypher_allowed": False,
            },
            expand_product_fields=any(
                term in request.casefold() for term in ("field", "attribute", "欄位", "屬性")
            ),
        )
        if package["status"] == "abstained-no-match":
            raise ResearchRuntimeError(
                "Selected entities did not resolve canonical graph evidence."
            )
        if self.trace_recorder is not None:
            self.trace_recorder.record_retrieved_graph(package)
        return package, result.to_trace()

    @staticmethod
    def validate_grounded_answer(
        output: Mapping[str, Any],
        evidence_package: Mapping[str, Any],
        *,
        trace_recorder: RQ1TraceRecorder | None = None,
    ) -> dict[str, Any]:
        node_by_id = {item["id"]: item for item in evidence_package["evidence_nodes"]}
        citation_by_id = {item["citation_id"]: item for item in evidence_package["citations"]}
        node_ids = output["evidence_node_ids"]
        citation_ids = output["citation_ids"]
        source_ids = output["source_document_ids"]
        node_ids_invalid = len(node_ids) != len(set(node_ids)) or any(
            item not in node_by_id for item in node_ids
        )
        if trace_recorder is not None:
            trace_recorder.add_validator_check(
                name="evidence node identity uniqueness and membership",
                status="FAIL" if node_ids_invalid else "PASS",
                input_examined={
                    "declared_evidence_node_ids": node_ids,
                    "retrieved_evidence_node_ids": list(node_by_id),
                },
                reason=(
                    "declared IDs contain duplicates or IDs absent from retrieved evidence"
                    if node_ids_invalid
                    else "declared IDs are unique and present in retrieved evidence"
                ),
                matched_ids_or_values=node_ids,
            )
        if node_ids_invalid:
            raise ResearchRuntimeError(
                "The grounded answer invented or duplicated evidence node IDs."
            )
        citation_ids_invalid = len(citation_ids) != len(set(citation_ids)) or any(
            item not in citation_by_id for item in citation_ids
        )
        if trace_recorder is not None:
            trace_recorder.add_validator_check(
                name="citation identity uniqueness and membership",
                status="FAIL" if citation_ids_invalid else "PASS",
                input_examined={
                    "declared_citation_ids": citation_ids,
                    "retrieved_citation_ids": list(citation_by_id),
                },
                reason=(
                    "declared citation IDs contain duplicates or IDs absent from retrieved citations"
                    if citation_ids_invalid
                    else "declared citation IDs are unique and present in retrieved citations"
                ),
                matched_ids_or_values=citation_ids,
            )
        if citation_ids_invalid:
            raise ResearchRuntimeError("The grounded answer invented or duplicated citation IDs.")
        cited_documents = {citation_by_id[item].get("document_id") for item in citation_ids}
        source_ids_invalid = len(source_ids) != len(set(source_ids)) or any(
            item not in cited_documents for item in source_ids
        )
        if trace_recorder is not None:
            trace_recorder.add_validator_check(
                name="source document identity uniqueness and citation membership",
                status="FAIL" if source_ids_invalid else "PASS",
                input_examined={
                    "declared_source_document_ids": source_ids,
                    "documents_referenced_by_declared_citations": sorted(
                        item for item in cited_documents if isinstance(item, str)
                    ),
                },
                reason=(
                    "declared source IDs contain duplicates or are absent from declared citations"
                    if source_ids_invalid
                    else "declared source IDs are unique and referenced by declared citations"
                ),
                matched_ids_or_values=source_ids,
            )
        if source_ids_invalid:
            raise ResearchRuntimeError(
                "The grounded answer claimed a source absent from citations."
            )
        if trace_recorder is not None:
            trace_recorder.add_validator_check(
                name="exact machine-checkable claim presence",
                status="PASS" if output["exact_claims"] else "FAIL",
                input_examined=output["exact_claims"],
                reason=(
                    "at least one exact_claims entry was supplied"
                    if output["exact_claims"]
                    else "no exact_claims entry was supplied"
                ),
                matched_ids_or_values=len(output["exact_claims"]),
            )
        if not output["exact_claims"]:
            raise ResearchRuntimeError("Grounded answers require an exact machine-checkable claim.")
        for index, claim in enumerate(output["exact_claims"]):
            node_id = claim["node_id"]
            declared_node_valid = node_id in node_ids
            if trace_recorder is not None:
                trace_recorder.add_validator_check(
                    name=f"exact claim {index} references declared evidence",
                    status="PASS" if declared_node_valid else "FAIL",
                    input_examined={"claim": claim, "declared_evidence_node_ids": node_ids},
                    reason=(
                        "claim node_id is present in declared evidence IDs"
                        if declared_node_valid
                        else "claim node_id is absent from declared evidence IDs"
                    ),
                    matched_ids_or_values=node_id,
                )
            if node_id not in node_ids:
                raise ResearchRuntimeError("An exact claim does not reference declared evidence.")
            properties = node_by_id[node_id].get("properties", {})
            property_name = claim["property"]
            exact_property_valid = (
                property_name in properties and properties[property_name] == claim["value"]
            )
            if trace_recorder is not None:
                trace_recorder.add_validator_check(
                    name=f"exact claim {index} property equality",
                    status="PASS" if exact_property_valid else "FAIL",
                    input_examined={
                        "node_id": node_id,
                        "property": property_name,
                        "claimed_value": claim["value"],
                        "retrieved_value": properties.get(property_name),
                    },
                    reason=(
                        "claimed property value exactly equals the retrieved node property"
                        if exact_property_valid
                        else "claimed property is absent or differs from the retrieved node property"
                    ),
                    matched_ids_or_values={property_name: properties.get(property_name)},
                )
            if not exact_property_valid:
                raise ResearchRuntimeError(
                    "A grounded answer changed an exact reviewed classification or rule value."
                )
        if trace_recorder is not None:
            trace_recorder.add_validator_check(
                name="claim-level natural-language grounding",
                status="NOT IMPLEMENTED",
                input_examined="answer free text",
                reason="No current validator branch parses or grounds natural-language answer claims.",
            )
            trace_recorder.add_validator_check(
                name="question-answer coverage",
                status="NOT IMPLEMENTED",
                input_examined="question requirements versus answer free text",
                reason="No current validator branch tests whether every requested element is answered.",
            )
        return dict(output)

    def run_rq1(self, request: str) -> dict[str, Any]:
        evidence, interpretation_trace = self.retrieve_with_live_interpretation(request)
        node_ids = [item["id"] for item in evidence["evidence_nodes"]]
        evidence_by_id = {item["id"]: item for item in evidence["evidence_nodes"]}
        selected_ids = evidence["retrieval_trace"]["model_selected_seed_ids"]
        claim_node_id = next(
            (item for item in selected_ids if item.startswith("portrayal-rule:")),
            selected_ids[0],
        )
        claim_properties = evidence_by_id[claim_node_id].get("properties", {})
        preferred_claim_properties = (
            "feature_code",
            "feature_name",
            "geometry_role",
            "activation_status",
        )
        required_exact_claims = [
            {"node_id": claim_node_id, "property": key, "value": claim_properties[key]}
            for key in preferred_claim_properties
            if isinstance(claim_properties.get(key), str)
        ]
        if not required_exact_claims:
            required_exact_claims = [
                {"node_id": claim_node_id, "property": key, "value": value}
                for key, value in claim_properties.items()
                if isinstance(value, str)
            ][:4]
        if not required_exact_claims:
            raise ResearchRuntimeError("Retrieved evidence has no exact string claims to validate.")
        citation_ids = [item["citation_id"] for item in evidence["citations"]]
        document_ids = sorted(
            {
                item["document_id"]
                for item in evidence["citations"]
                if isinstance(item.get("document_id"), str)
            }
        )
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string", "minLength": 1, "maxLength": 2000},
                "evidence_node_ids": {
                    "type": "array",
                    "const": [claim_node_id],
                },
                "citation_ids": {
                    "type": "array",
                    "const": citation_ids,
                },
                "source_document_ids": {
                    "type": "array",
                    "const": document_ids,
                },
                "exact_claims": {
                    "type": "array",
                    "const": required_exact_claims,
                },
            },
            "required": [
                "answer",
                "evidence_node_ids",
                "citation_ids",
                "source_document_ids",
                "exact_claims",
            ],
            "additionalProperties": False,
        }
        answer_task = "answer-with-authoritative-canonical-graph-evidence"
        answer_instructions = (
            "Answer only from the evidence package. Cite exact existing node, citation, and "
            "document IDs. Each identity or reviewed value claim must copy an exact node "
            "property into exact_claims. Preserve every full identity prefix, including "
            "'citation:'. Copy required_exact_claims exactly. Abstain rather than invent."
        )
        answer_context = {
            "request": request,
            "authoritative_evidence_package": evidence,
            "allowed_identity_values": {
                "evidence_node_ids": node_ids,
                "citation_ids": citation_ids,
                "source_document_ids": document_ids,
            },
            "required_identity_references": {
                "evidence_node_ids": [claim_node_id],
                "citation_ids": citation_ids,
                "source_document_ids": document_ids,
            },
            "required_exact_claims": required_exact_claims,
        }
        if self.trace_recorder is not None:
            self.trace_recorder.record_serialized_evidence(evidence)
            self.trace_recorder.record_model_input(
                stage="grounded answer generation",
                task=answer_task,
                instructions=answer_instructions,
                context=answer_context,
                output_schema=schema,
            )
        answer_result = self.adapter.generate_structured(
            task=answer_task,
            instructions=answer_instructions,
            context=answer_context,
            output_schema=schema,
        )
        if self.trace_recorder is not None:
            self.trace_recorder.record_model_output(
                stage="grounded answer generation", output=answer_result.output
            )
        normalized_output = deepcopy(answer_result.output)
        normalized_citations = []
        citation_normalizations = []
        for item in normalized_output.get("citation_ids", []):
            normalized = "citation:" + item if "citation:" + item in citation_ids else item
            normalized_citations.append(normalized)
            if normalized != item:
                citation_normalizations.append({"model_value": item, "canonical_value": normalized})
        normalized_output["citation_ids"] = normalized_citations
        validate_json_schema_subset(normalized_output, schema)
        if self.trace_recorder is not None:
            self.trace_recorder.add_validator_check(
                name="closed output-schema subset validation",
                status="PASS",
                input_examined={"output": normalized_output, "schema": schema},
                reason="normalized structured output satisfies the existing closed schema",
            )
            self.trace_recorder.record_postprocessing(
                raw_output=answer_result.output,
                postprocessed_output=normalized_output,
                transformations=[
                    {
                        "function": "AMAResearchRuntime.run_rq1 citation identity normalization",
                        "operation": (
                            "prefix a citation with 'citation:' only when that exact prefixed "
                            "identity exists in retrieved citation_ids"
                        ),
                        "changes": citation_normalizations,
                    },
                    {
                        "function": "validate_json_schema_subset",
                        "operation": "validation only; no transformation",
                        "changes": [],
                    },
                ],
            )
            self.trace_recorder.record_validator_input(
                output=normalized_output, evidence_package=evidence
            )
        answer = self.validate_grounded_answer(
            normalized_output,
            evidence,
            trace_recorder=self.trace_recorder,
        )
        if self.trace_recorder is not None:
            self.trace_recorder.record_validator_result(
                {
                    "runtime_validation": "passed",
                    "returned_answer_object": answer,
                }
            )
        return {
            "schema": RQ1_RESULT_SCHEMA,
            "request_identity": request_identity(request),
            "provider": answer_result.provider,
            "model_id": answer_result.model_id,
            "graph_backend": deepcopy(self.graph_backend_trace),
            "evidence_package_identity": "evidence-package:sha256:" + _sha256(evidence),
            "evidence_package": evidence,
            "answer": answer,
            "deterministic_identity_normalizations": citation_normalizations,
            "model_calls": [interpretation_trace, answer_result.to_trace()],
            "validation": "passed",
            "execution_performed": False,
        }

    def _load_plan_candidate(self) -> dict[str, Any]:
        path = self.repository_root / "data/research/ama-demo-02-school-plan-catalog-v1.0.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        if catalog.get("schema") != PLAN_CATALOG_SCHEMA:
            raise ResearchRuntimeError("The reviewed plan catalog schema is unsupported.")
        candidates = catalog.get("candidates")
        if not isinstance(candidates, list) or len(candidates) != 1:
            raise ResearchRuntimeError("AMA-DEMO-02 requires exactly one reviewed plan candidate.")
        return candidates[0]

    @staticmethod
    def validate_bounded_plan(
        output: Mapping[str, Any],
        *,
        candidate: Mapping[str, Any],
        evidence_package: Mapping[str, Any],
    ) -> dict[str, Any]:
        if dict(output) != dict(candidate):
            raise ResearchRuntimeError(
                "The model changed a reviewed machine field or selected unsupported semantics."
            )
        evidence_ids = {item["id"] for item in evidence_package["evidence_nodes"]}
        citation_ids = {item["citation_id"] for item in evidence_package["citations"]}
        if any(item not in evidence_ids for item in output["evidence_node_ids"]):
            raise ResearchRuntimeError("The bounded plan invented an evidence node identity.")
        if any(item not in citation_ids for item in output["citation_ids"]):
            raise ResearchRuntimeError("The bounded plan invented a citation identity.")
        if output["execution_performed"] is not False or output["approval_required"] is not True:
            raise ResearchRuntimeError("A bounded proposal cannot execute or bypass approval.")
        return dict(output)

    def propose_rq2(self, request: str) -> dict[str, Any]:
        evidence, interpretation_trace = self.retrieve_with_live_interpretation(request)
        candidate = self._load_plan_candidate()
        schema = _const_schema(candidate)
        try:
            result = self.adapter.generate_structured(
                task="select-reviewed-bounded-mapping-plan",
                instructions=(
                    "Return the reviewed candidate exactly when it satisfies the request and "
                    "evidence. Do not change fields, operations, geometry, classification, source, "
                    "path, citation, approval, authorization, or execution state."
                ),
                context={
                    "request": request,
                    "authoritative_evidence_package": evidence,
                    "reviewed_candidate": candidate,
                },
                output_schema=schema,
            )
            validate_json_schema_subset(result.output, schema)
            validated = self.validate_bounded_plan(
                result.output, candidate=candidate, evidence_package=evidence
            )
        except LLMAdapterError as error:
            raise ResearchRuntimeError(f"Deterministic plan validation failed: {error}") from error
        body = {
            "schema": RQ2_PLAN_SCHEMA,
            "request_identity": request_identity(request),
            "candidate": validated,
            "evidence_package_identity": "evidence-package:sha256:" + _sha256(evidence),
            "status": "validated-proposal",
            "execution_performed": False,
        }
        return {
            **body,
            "plan_id": "ama-plan:sha256:" + _sha256(body),
            "provider": result.provider,
            "model_id": result.model_id,
            "graph_backend": deepcopy(self.graph_backend_trace),
            "evidence_package": evidence,
            "model_calls": [interpretation_trace, result.to_trace()],
        }

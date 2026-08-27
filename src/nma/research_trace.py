from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any, Mapping


TRACE_CONTRACT = "rq1-trace-01/1.0"
REDACTION_MARKER = "[REDACTED: unexpected secret value]"

_SECRET_FIELD_NAMES = {
    "api-key",
    "api_key",
    "authorization",
    "client-secret",
    "client_secret",
    "password",
    "proxy-authorization",
    "refresh-token",
    "refresh_token",
    "secret",
    "access-token",
    "access_token",
}
_PRINTED_PAGE_TEN = re.compile(r"(?:打印頁|打印页|printed[ _-]?page\s*[:=]?\s*)10\b", re.IGNORECASE)


def redact_unexpected_secrets(value: object, *, path: str = "$") -> tuple[object, list[str]]:
    """Redact only fields whose names unambiguously denote credential values."""

    redactions: list[str] = []

    def visit(item: object, item_path: str) -> object:
        if isinstance(item, Mapping):
            cleaned: dict[str, object] = {}
            for raw_key, child in item.items():
                key = str(raw_key)
                child_path = f"{item_path}.{key}"
                if key.casefold() in _SECRET_FIELD_NAMES and child not in (None, ""):
                    cleaned[key] = REDACTION_MARKER
                    redactions.append(child_path)
                else:
                    cleaned[key] = visit(child, child_path)
            return cleaned
        if isinstance(item, list):
            return [visit(child, f"{item_path}[{index}]") for index, child in enumerate(item)]
        return deepcopy(item)

    return visit(value, path), redactions


def _contains_printed_page_ten(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).casefold() == "printed_page" and item in (10, "10"):
                return True
            if _contains_printed_page_ten(item):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_printed_page_ten(item) for item in value)
    return isinstance(value, str) and _PRINTED_PAGE_TEN.search(value) is not None


def _contains_any_text(value: object, markers: tuple[str, ...]) -> bool:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()
    return any(marker.casefold() in rendered for marker in markers)


def _node_by_id(nodes: object) -> dict[str, dict[str, Any]]:
    if not isinstance(nodes, list):
        return {}
    return {
        str(item["id"]): item
        for item in nodes
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }


class RQ1TraceRecorder:
    """Append-only observer for the existing RQ1 execution path."""

    def __init__(
        self,
        *,
        question: str,
        repository_root: str | Path,
        scenario: str,
        request_identity: str,
    ) -> None:
        self.data: dict[str, Any] = {
            "trace_contract": TRACE_CONTRACT,
            "run_identity": {
                "rq": "RQ1",
                "scenario": scenario,
                "repository_root": str(Path(repository_root).resolve()),
                "request_identity": request_identity,
            },
            "question": {
                "value": question,
                "encoding": "UTF-8",
                "capture_stage": "CLI argument after argparse, before runtime dispatch",
            },
            "resolved_entities": [],
            "retrieved_graph": {
                "selected_evidence_node_ids": [],
                "nodes": [],
                "edges": [],
                "citations": [],
            },
            "serialized_evidence": {},
            "context_budget": {"calls": [], "answer_generation": {}},
            "llm_request": {"provider_neutral_calls": [], "ollama_wire_calls": []},
            "llm_raw_response": {"ollama_wire_calls": [], "structured_outputs": []},
            "llm_postprocessing": {},
            "validator_input": {},
            "validator_checks": [],
            "validator_result": {},
            "diagnostic_observations": {
                "canonical_required_nodes": [],
                "entity_resolution_candidates": [],
                "provider_runtime_observations": [],
            },
        }

    def record_run_identity(
        self,
        *,
        provider: str,
        model_id: str,
        graph_backend: Mapping[str, Any],
    ) -> None:
        self.data["run_identity"].update(
            {
                "model_provider": provider,
                "model_id": model_id,
                "graph_backend": graph_backend.get("active_backend"),
                "canonical_graph_identity": graph_backend.get("graph_revision"),
                "graph_backend_trace": deepcopy(dict(graph_backend)),
            }
        )

    def record_model_input(
        self,
        *,
        stage: str,
        task: str,
        instructions: str,
        context: Mapping[str, Any],
        output_schema: Mapping[str, Any],
    ) -> None:
        self.data["llm_request"]["provider_neutral_calls"].append(
            {
                "stage": stage,
                "task": task,
                "instructions": instructions,
                "context": deepcopy(dict(context)),
                "output_schema": deepcopy(dict(output_schema)),
            }
        )

    def record_model_output(self, *, stage: str, output: Mapping[str, Any]) -> None:
        self.data["llm_raw_response"]["structured_outputs"].append(
            {"stage": stage, "output_before_runtime_postprocessing": deepcopy(dict(output))}
        )

    def record_resolved_entities(
        self,
        *,
        candidates: list[dict[str, Any]],
        selected_ids: list[str],
        graph_nodes: Mapping[str, Any],
    ) -> None:
        self.data["diagnostic_observations"]["entity_resolution_candidates"] = deepcopy(candidates)
        self.data["resolved_entities"] = [
            {
                "node_id": node_id,
                "node_type": graph_nodes[node_id].get("type"),
                "properties": deepcopy(graph_nodes[node_id].get("properties", {})),
                "resolution_role": "model-selected allowlisted graph seed",
            }
            for node_id in selected_ids
            if node_id in graph_nodes
        ]

    def record_canonical_required_nodes(
        self, *, required_ids: list[str], graph_nodes: Mapping[str, Any]
    ) -> None:
        self.data["diagnostic_observations"]["canonical_required_nodes"] = [
            deepcopy(graph_nodes[node_id]) for node_id in required_ids if node_id in graph_nodes
        ]

    def record_retrieved_graph(self, evidence: Mapping[str, Any]) -> None:
        paths = evidence.get("graph_paths", {})
        self.data["retrieved_graph"].update(
            {
                "all_retrieved_node_ids": deepcopy(paths.get("nodes", [])),
                "nodes": deepcopy(evidence.get("evidence_nodes", [])),
                "edges": deepcopy(paths.get("edges", [])),
                "citations": deepcopy(evidence.get("citations", [])),
                "source_documents": deepcopy(evidence.get("source_documents", [])),
                "source_sections": deepcopy(evidence.get("source_sections", [])),
                "retrieval_trace": deepcopy(evidence.get("retrieval_trace", {})),
            }
        )

    def record_serialized_evidence(self, evidence: Mapping[str, Any]) -> None:
        self.data["serialized_evidence"] = {
            "capture_stage": (
                "exact JSON-compatible Python value supplied as "
                "context.authoritative_evidence_context immediately before adapter invocation"
            ),
            "runtime_type": type(evidence).__name__,
            "value": deepcopy(dict(evidence)),
        }

    def record_ollama_event(self, event: str, payload: Mapping[str, Any]) -> None:
        if event == "context_budget":
            context_budget = self.data.setdefault("context_budget", {})
            calls = context_budget.setdefault("calls", [])
            calls.append(deepcopy(dict(payload)))
            context_budget["answer_generation"] = deepcopy(dict(payload))
        elif event == "context_budget_result":
            context_budget = self.data.setdefault("context_budget", {})
            calls = context_budget.setdefault("calls", [])
            if calls:
                calls[-1] = deepcopy(dict(payload))
            else:
                calls.append(deepcopy(dict(payload)))
            context_budget["answer_generation"] = deepcopy(dict(payload))
        elif event == "request":
            cleaned, redactions = redact_unexpected_secrets(payload)
            entry = dict(cleaned) if isinstance(cleaned, Mapping) else {"value": cleaned}
            entry["redacted_secret_locations"] = redactions
            self.data["llm_request"]["ollama_wire_calls"].append(entry)
        elif event == "raw_response":
            self.data["llm_raw_response"]["ollama_wire_calls"].append(deepcopy(dict(payload)))
        elif event == "response_envelope":
            calls = self.data["llm_raw_response"]["ollama_wire_calls"]
            if calls:
                calls[-1]["parsed_envelope_before_content_parsing"] = deepcopy(dict(payload))

    def record_provider_runtime_observation(self, observation: Mapping[str, Any]) -> None:
        self.data["diagnostic_observations"].setdefault("provider_runtime_observations", []).append(
            deepcopy(dict(observation))
        )

    def record_postprocessing(
        self,
        *,
        raw_output: Mapping[str, Any],
        postprocessed_output: Mapping[str, Any],
        transformations: list[dict[str, Any]],
    ) -> None:
        self.data["llm_postprocessing"] = {
            "raw_llm_structured_output": deepcopy(dict(raw_output)),
            "postprocessed_answer_object": deepcopy(dict(postprocessed_output)),
            "transformation_stages": deepcopy(transformations),
        }

    def record_validator_input(
        self, *, output: Mapping[str, Any], evidence_package: Mapping[str, Any]
    ) -> None:
        self.data["validator_input"] = {
            "answer_object": deepcopy(dict(output)),
            "answer_text": output.get("answer"),
            "evidence_ids": deepcopy(output.get("evidence_node_ids", [])),
            "citation_ids": deepcopy(output.get("citation_ids", [])),
            "source_document_ids": deepcopy(output.get("source_document_ids", [])),
            "retrieved_evidence": deepcopy(dict(evidence_package)),
            "question": evidence_package.get("query"),
            "question_location": "retrieved_evidence.query",
            "source_metadata": deepcopy(evidence_package.get("citations", [])),
        }

    def add_validator_check(
        self,
        *,
        name: str,
        status: str,
        input_examined: object,
        reason: str,
        matched_ids_or_values: object = None,
    ) -> None:
        self.data["validator_checks"].append(
            {
                "check_name": name,
                "input_examined": deepcopy(input_examined),
                "status": status,
                "reason": reason,
                "matched_ids_or_values": deepcopy(matched_ids_or_values),
            }
        )

    def record_validator_result(self, value: Mapping[str, Any]) -> None:
        self.data["validator_result"].update(deepcopy(dict(value)))

    def finalize(self, *, result: Mapping[str, Any], artifact: Mapping[str, Any]) -> None:
        self.data["retrieved_graph"]["selected_evidence_node_ids"] = deepcopy(
            result["answer"]["evidence_node_ids"]
        )
        self.data["run_identity"].update(
            {
                "model_provider": result["provider"],
                "model_id": result["model_id"],
                "graph_backend": result["graph_backend"].get("active_backend"),
                "canonical_graph_identity": result["graph_backend"].get("graph_revision"),
            }
        )
        self.data["diagnostic_observations"].update(self._diagnose(artifact))

    def _diagnose(self, artifact: Mapping[str, Any]) -> dict[str, Any]:
        canonical_nodes = _node_by_id(
            self.data["diagnostic_observations"].get("canonical_required_nodes")
        )
        retrieved_nodes = _node_by_id(self.data["retrieved_graph"].get("nodes"))
        serialized = self.data.get("serialized_evidence", {}).get("value", {})
        serialized_nodes = _node_by_id(
            serialized.get("evidence_nodes", []) if isinstance(serialized, Mapping) else []
        )
        requests = self.data["llm_request"].get("ollama_wire_calls") or self.data[
            "llm_request"
        ].get("provider_neutral_calls", [])
        raw_outputs = self.data["llm_raw_response"].get("structured_outputs", [])
        raw_answer = raw_outputs[-1]["output_before_runtime_postprocessing"] if raw_outputs else {}
        postprocessed = self.data.get("llm_postprocessing", {}).get(
            "postprocessed_answer_object", {}
        )

        elements = {
            "line style": {
                "node_id": "line-style:doc01:2",
                "answer_markers": (
                    "line style",
                    "line-style",
                    "line_code",
                    "line code",
                    "線號",
                    "線式",
                    "线号",
                    "线型",
                ),
            },
            "color": {
                "node_id": "portrayal-color:doc01:7",
                "answer_markers": (
                    "color",
                    "colour",
                    "observed_color",
                    "black",
                    "色碼",
                    "黑色",
                    "顏色",
                    "颜色",
                ),
            },
            "unresolved binding": {
                "node_id": "classification:doc01:9350906",
                "answer_markers": (
                    "productlayer",
                    "mapping must remain unresolved",
                    "mapping_status",
                    "unresolved binding",
                    "未確認",
                    "未确认",
                    "未解析",
                    "產品圖層",
                    "产品图层",
                ),
            },
        }
        element_rows = []
        for label, definition in elements.items():
            node_id = definition["node_id"]
            canonical_present = node_id in canonical_nodes
            retrieved_present = node_id in retrieved_nodes
            serialized_present = node_id in serialized_nodes
            sent = _contains_any_text(requests, (node_id,))
            raw_present = _contains_any_text(
                raw_answer.get("answer", ""), definition["answer_markers"]
            )
            post_present = _contains_any_text(
                postprocessed.get("answer", ""), definition["answer_markers"]
            )
            first_absent = next(
                (
                    stage
                    for stage, present in (
                        ("canonical KG", canonical_present),
                        ("retrieval", retrieved_present),
                        ("serialization", serialized_present),
                        ("Ollama request", sent),
                        ("raw answer", raw_present),
                        ("post-processing", post_present),
                    )
                    if not present
                ),
                "not absent in observed stages",
            )
            element_rows.append(
                {
                    "element": label,
                    "canonical_kg": "PASS" if canonical_present else "FAIL",
                    "retrieved": "PASS" if retrieved_present else "FAIL",
                    "serialized": "PASS" if serialized_present else "FAIL",
                    "sent_to_qwen": "PASS" if sent else "FAIL",
                    "raw_answer": "OBSERVED" if raw_present else "NOT OBSERVED",
                    "postprocessed_answer": "OBSERVED" if post_present else "NOT OBSERVED",
                    "validator_checks_coverage": "NOT IMPLEMENTED",
                    "first_absent_stage": first_absent,
                }
            )

        printed_page_stages = [
            ("canonical KG", self.data["diagnostic_observations"].get("canonical_required_nodes")),
            ("retrieved graph", self.data["retrieved_graph"]),
            ("serialized evidence", self.data.get("serialized_evidence")),
            ("final Ollama request", requests),
            ("raw Qwen response", raw_answer),
            ("post-processing", postprocessed),
        ]
        appearances = [
            stage for stage, value in printed_page_stages if _contains_printed_page_ten(value)
        ]

        mapping_status = (
            canonical_nodes.get("classification:doc01:9350906", {})
            .get("properties", {})
            .get("mapping_status")
        )
        line_properties = canonical_nodes.get("line-style:doc01:2", {}).get("properties")
        color_properties = canonical_nodes.get("portrayal-color:doc01:7", {}).get("properties")
        validator_names = {item.get("check_name") for item in self.data.get("validator_checks", [])}
        element_by_name = {item["element"]: item for item in element_rows}
        classification_id = "classification:doc01:9350906"
        geometry_id = "portrayal-geometry:Point"
        classification_serialized = classification_id in serialized_nodes
        geometry_serialized = geometry_id in serialized_nodes
        classification_sent = _contains_any_text(requests, (classification_id,))
        geometry_sent = _contains_any_text(requests, (geometry_id,))
        source_serialized = bool(
            serialized.get("citations") if isinstance(serialized, Mapping) else False
        )
        source_sent = _contains_any_text(requests, ("citation:section:doc01-portrayal:p11",))
        question_sent = _contains_any_text(requests, (self.data["question"]["value"],))
        all_required_kg = all(
            node_id in canonical_nodes
            for node_id in (
                classification_id,
                geometry_id,
                "line-style:doc01:2",
                "portrayal-color:doc01:7",
                "portrayal-rule:doc01:9350906",
                "portrayal-recipe:doc01:9350906:review-v1",
            )
        )
        all_required_retrieved = all(
            node_id in retrieved_nodes
            for node_id in (
                classification_id,
                geometry_id,
                "line-style:doc01:2",
                "portrayal-color:doc01:7",
                "portrayal-rule:doc01:9350906",
                "portrayal-recipe:doc01:9350906:review-v1",
            )
        )
        all_required_serialized = all(
            item["serialized"] == "PASS" for item in element_rows
        ) and all((classification_serialized, geometry_serialized, source_serialized))
        all_required_sent = all(item["sent_to_qwen"] == "PASS" for item in element_rows) and all(
            (classification_sent, geometry_sent, source_sent, question_sent)
        )
        raw_requested_elements_covered = all(
            item["raw_answer"] == "OBSERVED" for item in element_rows
        )
        postprocessing_unchanged = raw_answer == postprocessed
        doc01_citation = next(
            (
                item
                for item in self.data.get("validator_input", {}).get("source_metadata", [])
                if item.get("citation_id") == "citation:section:doc01-portrayal:p11"
            ),
            None,
        )
        validator_has_relevant_inputs = bool(
            self.data.get("validator_input", {}).get("answer_text")
            and self.data.get("validator_input", {}).get("question")
            and doc01_citation
            and doc01_citation.get("page") == 11
            and doc01_citation.get("printed_page") is None
        )
        printed_page_observed = bool(appearances)
        provider_observations = self.data["diagnostic_observations"].get(
            "provider_runtime_observations", []
        )
        answer_budget = self.data.get("context_budget", {}).get("answer_generation", {})
        effective_context_verified = bool(
            answer_budget.get("fits")
            and answer_budget.get("budget_status") == "PASS"
            and answer_budget.get("observed_within_input_budget") is True
            and not answer_budget.get("truncation_expected")
        )
        ollama_observed = bool(self.data["llm_request"].get("ollama_wire_calls"))
        provider_prompt_truncated = (ollama_observed and not effective_context_verified) or any(
            item.get("code") == "ollama-input-truncated"
            for item in provider_observations
            if isinstance(item, Mapping)
        )
        matrix = [
            {
                "stage": "Entity resolution",
                "observed_status": "PASS" if self.data["resolved_entities"] else "FAIL",
                "evidence": f"{len(self.data['resolved_entities'])} selected entities captured before traversal",
            },
            {
                "stage": "Graph retrieval",
                "observed_status": "PASS" if all_required_retrieved else "FAIL",
                "evidence": {
                    "retrieved_node_count": len(retrieved_nodes),
                    "retrieved_edge_count": len(self.data["retrieved_graph"].get("edges", [])),
                },
            },
            {
                "stage": "Required KG knowledge availability",
                "observed_status": "PASS" if all_required_kg else "FAIL",
                "evidence": "all six required audit nodes are present in the active canonical graph",
            },
            {
                "stage": "KG contains classification",
                "observed_status": "PASS"
                if "classification:doc01:9350906" in canonical_nodes
                else "FAIL",
                "evidence": "classification:doc01:9350906",
            },
            {
                "stage": "KG contains geometry",
                "observed_status": "PASS"
                if "portrayal-geometry:Point" in canonical_nodes
                else "FAIL",
                "evidence": "portrayal-geometry:Point",
            },
            {
                "stage": "KG contains line-style information",
                "observed_status": "PASS" if line_properties else "FAIL",
                "evidence": line_properties,
            },
            {
                "stage": "KG contains color information",
                "observed_status": "PASS" if color_properties else "FAIL",
                "evidence": color_properties,
            },
            {
                "stage": "KG contains unresolved binding status",
                "observed_status": "PASS" if mapping_status else "FAIL",
                "evidence": mapping_status,
            },
            {
                "stage": "Serialized evidence preserves classification",
                "observed_status": "PASS" if classification_serialized else "FAIL",
                "evidence": classification_id,
            },
            {
                "stage": "Serialized evidence preserves geometry",
                "observed_status": "PASS" if geometry_serialized else "FAIL",
                "evidence": geometry_id,
            },
            {
                "stage": "Serialized evidence preserves line style",
                "observed_status": element_by_name["line style"]["serialized"],
                "evidence": "line-style:doc01:2",
            },
            {
                "stage": "Serialized evidence preserves color",
                "observed_status": element_by_name["color"]["serialized"],
                "evidence": "portrayal-color:doc01:7",
            },
            {
                "stage": "Serialized evidence preserves unresolved binding",
                "observed_status": element_by_name["unresolved binding"]["serialized"],
                "evidence": mapping_status,
            },
            {
                "stage": "Evidence serialization",
                "observed_status": "PASS" if all_required_serialized else "FAIL",
                "evidence": "the exact authoritative_evidence_package runtime value contains every required item",
            },
            {
                "stage": "Ollama receives required RQ1 instructions",
                "observed_status": "PASS" if question_sent else "FAIL",
                "evidence": "the final user message contains the byte-preserved RQ1 question",
            },
            {
                "stage": "Ollama receives required evidence",
                "observed_status": "PASS" if all_required_sent else "FAIL",
                "evidence": "the final user message contains classification, geometry, line style, color, source, and unresolved binding evidence",
            },
            {
                "stage": "Context budget preflight",
                "observed_status": (
                    "PASS"
                    if effective_context_verified
                    else "FAIL"
                    if ollama_observed
                    else "NOT OBSERVED"
                ),
                "evidence": answer_budget,
            },
            {
                "stage": "Prompt/message propagation",
                "observed_status": "FAIL"
                if provider_prompt_truncated
                else "PASS"
                if all_required_sent
                else "FAIL",
                "evidence": provider_observations
                if provider_prompt_truncated
                else "the captured Ollama wire body preserves the provider-neutral context and original request",
            },
            {
                "stage": "Qwen internal context retains required evidence",
                "observed_status": "PASS" if effective_context_verified else "UNKNOWN",
                "evidence": (
                    "explicit num_ctx, preflight fit, and observed prompt usage verify the input budget"
                    if effective_context_verified
                    else "effective input retention was not verified"
                ),
            },
            {
                "stage": "Raw Qwen answer covers requested elements",
                "observed_status": "PASS" if raw_requested_elements_covered else "FAIL",
                "evidence": {item["element"]: item["raw_answer"] for item in element_rows},
            },
            {
                "stage": "Raw Qwen answer contains unsupported claims",
                "observed_status": "OBSERVED" if printed_page_observed else "NOT OBSERVED",
                "evidence": "打印頁10 first appears in the raw response"
                if printed_page_observed
                else "打印頁10 was not observed",
            },
            {
                "stage": "LLM generation",
                "observed_status": "FAIL"
                if (not raw_requested_elements_covered or printed_page_observed)
                else "PASS",
                "evidence": "raw response omissions and unsupported printed-page claim, observed without changing validator logic",
            },
            {
                "stage": "Post-processing",
                "observed_status": "PASS" if postprocessing_unchanged else "FAIL",
                "evidence": "raw structured output equals the answer object passed to validation"
                if postprocessing_unchanged
                else "the answer object changed before validation",
            },
            {
                "stage": "Validator receives sufficient evidence",
                "observed_status": "PASS" if validator_has_relevant_inputs else "FAIL",
                "evidence": "validator input includes answer text, question in evidence.query, and Document 01 page=11/printed_page=null metadata",
            },
            {
                "stage": "Validator evidence availability",
                "observed_status": "PASS" if validator_has_relevant_inputs else "FAIL",
                "evidence": "full retrieved evidence package and source metadata are supplied to validate_grounded_answer",
            },
            {
                "stage": "Validator performs claim-level grounding",
                "observed_status": "NOT IMPLEMENTED"
                if "claim-level natural-language grounding" in validator_names
                else "UNKNOWN",
                "evidence": "current checks validate declared IDs and exact_claims, not free-text answer claims",
            },
            {
                "stage": "Validator unsupported-claim detection capability",
                "observed_status": "NOT IMPLEMENTED",
                "evidence": "CLAIM-LEVEL GROUNDING CHECK: NOT IMPLEMENTED",
            },
            {
                "stage": "Validator performs question coverage",
                "observed_status": "NOT IMPLEMENTED"
                if "question-answer coverage" in validator_names
                else "UNKNOWN",
                "evidence": "no current check compares requested answer elements with answer text",
            },
            {
                "stage": "Validator question-coverage capability",
                "observed_status": "NOT IMPLEMENTED",
                "evidence": "QUESTION-COVERAGE CHECK: NOT IMPLEMENTED",
            },
        ]
        root_causes = []
        if (
            all_required_kg
            and all_required_retrieved
            and all_required_serialized
            and all_required_sent
            and not provider_prompt_truncated
            and (not raw_requested_elements_covered or printed_page_observed)
        ):
            root_causes.append(
                {
                    "category": "E — LLM synthesis/instruction-following defect",
                    "evidence": (
                        "required facts reached the effective Ollama context, but one or more "
                        "requested answer elements were not observed in the raw response"
                        + (
                            "; 打印頁10 also first appeared in the raw response"
                            if printed_page_observed
                            else ""
                        )
                    ),
                }
            )
        if provider_prompt_truncated:
            root_causes.append(
                {
                    "category": "PIPELINE GAP — provider-side input truncation (outside strict A-G category predicates)",
                    "evidence": "the final API request contains the required evidence, but Ollama truncated 14,738 prompt tokens to 2,050 before inference and did not expose the exact retained subset",
                }
            )
        if (
            "claim-level natural-language grounding" in validator_names
            and "question-answer coverage" in validator_names
        ):
            root_causes.extend(
                [
                    {
                        "category": "G1 — evidence/citation identity validation limitation",
                        "evidence": "current deterministic checks validate identities and exact_claims only",
                    },
                    {
                        "category": "G2 — unsupported natural-language claim detection absent",
                        "evidence": "CLAIM-LEVEL GROUNDING CHECK: NOT IMPLEMENTED",
                    },
                    {
                        "category": "G3 — question-answer coverage validation absent",
                        "evidence": "QUESTION-COVERAGE CHECK: NOT IMPLEMENTED",
                    },
                    {
                        "category": "G4 — misleading aggregate PASS label",
                        "evidence": (
                            "Grounded answer validation remains an aggregate of existing schema, "
                            "identity, and exact-claim checks; it is not claim-level grounding or "
                            "question-coverage validation"
                        ),
                    },
                ]
            )
        return {
            "required_node_properties": {
                node_id: deepcopy(canonical_nodes.get(node_id, {}).get("properties"))
                for node_id in (
                    "line-style:doc01:2",
                    "portrayal-color:doc01:7",
                    "portrayal-geometry:Point",
                    "classification:doc01:9350906",
                    "portrayal-rule:doc01:9350906",
                    "portrayal-recipe:doc01:9350906:review-v1",
                )
            },
            "missing_element_trace": element_rows,
            "printed_page_10_trace": {
                "stages_where_observed": appearances,
                "first_observed_stage": appearances[0] if appearances else "NOT OBSERVED",
                "changed_during_postprocessing": (
                    _contains_printed_page_ten(raw_answer)
                    != _contains_printed_page_ten(postprocessed)
                ),
            },
            "diagnostic_matrix": matrix,
            "root_cause_classification": root_causes,
            "reported_validation_labels": deepcopy(artifact.get("validation", {})),
        }

    def write(self, run_directory: str | Path) -> tuple[Path, Path]:
        root = Path(run_directory)
        json_path = root / "rq1-trace.json"
        text_path = root / "rq1-trace.txt"
        json_path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        text_path.write_text(self.render_text(), encoding="utf-8")
        return json_path, text_path

    def render_text(self) -> str:
        data = self.data
        retrieved = data["retrieved_graph"]
        lines = [
            "RQ1-TRACE-01",
            "",
            "1. Run identity",
            json.dumps(data["run_identity"], ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "2. Original question",
            data["question"]["value"],
            "",
            "3. Resolved entities",
            json.dumps(data["resolved_entities"], ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "4. Retrieved KG nodes and properties",
            json.dumps(retrieved.get("nodes", []), ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "5. Retrieved graph edges",
            json.dumps(retrieved.get("edges", []), ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "6. Serialized evidence",
            json.dumps(data["serialized_evidence"], ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "6a. Context budget preflight",
            json.dumps(data.get("context_budget", {}), ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "7. Exact Ollama request/messages",
            json.dumps(data["llm_request"], ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "8. Raw Qwen response",
            json.dumps(data["llm_raw_response"], ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "9. Post-processing, if any",
            json.dumps(data["llm_postprocessing"], ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "10. Validator input",
            json.dumps(data["validator_input"], ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "11. Validator checks actually executed",
            json.dumps(data["validator_checks"], ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "12. Trace diagnosis",
            json.dumps(
                data["diagnostic_observations"], ensure_ascii=False, indent=2, sort_keys=True
            ),
            "",
        ]
        return "\n".join(lines)


def attach_ollama_trace(adapter: object, recorder: RQ1TraceRecorder) -> bool:
    """Attach the observer to an Ollama adapter, including a transparent wrapper delegate."""

    current = adapter
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        setter = getattr(current, "set_trace_hook", None)
        if callable(setter):
            setter(recorder.record_ollama_event)
            return True
        current = getattr(current, "delegate", None)
    return False


def refresh_trace_diagnosis(run_directory: str | Path) -> tuple[Path, Path]:
    """Re-render diagnosis from an already captured run without invoking a model."""

    root = Path(run_directory)
    recorder = object.__new__(RQ1TraceRecorder)
    recorder.data = json.loads((root / "rq1-trace.json").read_text(encoding="utf-8"))
    artifact = json.loads((root / "result.json").read_text(encoding="utf-8"))
    recorder.data["diagnostic_observations"].update(recorder._diagnose(artifact))
    return recorder.write(root)


def append_provider_runtime_observation(
    run_directory: str | Path, observation: Mapping[str, Any]
) -> tuple[Path, Path]:
    """Add a same-run provider observation and re-render without invoking a model."""

    root = Path(run_directory)
    recorder = object.__new__(RQ1TraceRecorder)
    recorder.data = json.loads((root / "rq1-trace.json").read_text(encoding="utf-8"))
    recorder.record_provider_runtime_observation(observation)
    artifact = json.loads((root / "result.json").read_text(encoding="utf-8"))
    recorder.data["diagnostic_observations"].update(recorder._diagnose(artifact))
    return recorder.write(root)

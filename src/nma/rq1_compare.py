from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import time
from typing import Any, Callable, Iterable, Mapping

from agent_contracts.governance import request_identity

from nma.llm import LLMAdapter
from nma.llm.base import canonical_json, validate_json_schema_subset
from nma.research_answer_validation import validate_rq1_answer
from nma.research_runtime import AMAResearchRuntime


PROTOCOL_SCHEMA = "nma.rq1-compare-01-protocol/1.0"
RESULTS_SCHEMA = "nma.rq1-compare-01-results/1.0"
ARCHITECTURES = ("llm-only", "text-rag", "graphrag")
SHARED_TASK = "answer-reviewed-authoritative-portrayal-question"
SHARED_INSTRUCTIONS = (
    "Answer the request in natural prose and address every requested semantic requirement. "
    "Do not use a fixed answer-slot template. Preserve unresolved or unknown states and abstain "
    "rather than inventing a value or source. Do not claim that evidence was retrieved unless "
    "retrieved evidence is present in the supplied context."
)
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string", "minLength": 1, "maxLength": 2000}},
    "required": ["answer"],
    "additionalProperties": False,
}
CHUNK_ID_PATTERN = re.compile(r"text-chunk-[0-9]{4}-[0-9a-f]{12}")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def estimate_component_tokens(value: object) -> int:
    """Use the accepted Qwen byte estimator without chat-template allowance."""

    raw = value if isinstance(value, bytes) else canonical_json(value)
    return math.ceil(math.ceil(len(raw) / 3) * 1.2)


def load_protocol(repository_root: Path) -> dict[str, Any]:
    path = repository_root / "data/evaluation/rq1-compare-01-evaluation-protocol.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != PROTOCOL_SCHEMA:
        raise ValueError("RQ1 comparison protocol identity is unsupported.")
    fixture = repository_root / value["question_fixture"]
    if sha256_file(fixture) != value["question_fixture_sha256"]:
        raise ValueError("RQ1 question fixture hash differs from the frozen protocol.")
    return value


def load_questions(repository_root: Path, protocol: Mapping[str, Any]) -> list[dict[str, str]]:
    payload = json.loads((repository_root / protocol["question_fixture"]).read_text("utf-8"))
    questions = [payload["canonical"], *payload["variants"]]
    if len(payload["variants"]) != 10 or len(questions) != 11:
        raise ValueError("RQ1 comparison requires canonical plus exactly ten variants.")
    if len({item["id"] for item in questions}) != 11:
        raise ValueError("RQ1 question IDs must be unique.")
    return questions


def _flatten_recipe(recipe: Mapping[str, Any], source: Mapping[str, Any]) -> tuple[str, dict]:
    constraints = recipe.get("source_constraints", {})
    payload = {
        "document": source.get("filename"),
        "document_revision": source.get("revision"),
        "document_sha256": source.get("sha256"),
        "page": recipe.get("page"),
        "feature_code": recipe.get("feature_code"),
        "feature_name": recipe.get("feature_name"),
        "geometry_role": recipe.get("geometry_role"),
        "representation_kind": recipe.get("representation_kind"),
        "activation_status": recipe.get("activation_status"),
        "source_constraints": {
            key: constraints.get(key)
            for key in (
                "line_code",
                "color_code",
                "observed_color",
                "instruction",
                "overall_width_mm",
                "overall_height_mm",
            )
            if key in constraints
        },
        "runtime_requirements": recipe.get("runtime_requirements", []),
        "activation_gates": [
            {"reason": item.get("reason"), "status": item.get("status")}
            for item in recipe.get("activation_gates", [])
        ],
    }
    facts = {
        "feature_code": [recipe.get("feature_code")],
        "feature_name": [recipe.get("feature_name")],
        "geometry": [recipe.get("geometry_role")],
        "line_style": [constraints.get("line_code")],
        "color_code": [constraints.get("color_code")],
        "color_name": [constraints.get("observed_color")],
        "source_page": [recipe.get("page")],
        "revision": [source.get("revision")],
    }
    return canonical_json(payload).decode("utf-8"), _clean_facts(facts)


def _flatten_extraction(record: Mapping[str, Any]) -> tuple[str, dict]:
    payload = {
        key: record.get(key)
        for key in (
            "record_id",
            "document_id",
            "document",
            "version",
            "effective_date",
            "page",
            "feature_name",
            "feature_code",
            "production_stage",
            "geometry_classes",
            "line_code",
            "color_code",
            "instruction",
            "source_text",
            "extraction_method",
            "review_status",
            "source_uri",
        )
    }
    facts = {
        "feature_code": [record.get("feature_code")],
        "feature_name": [record.get("feature_name")],
        "line_style": [record.get("line_code")],
        "color_code": [record.get("color_code")],
        "source_page": [record.get("page")],
        "record_id": [record.get("record_id")],
        "revision": [record.get("version")],
    }
    return canonical_json(payload).decode("utf-8"), _clean_facts(facts)


def _clean_facts(facts: Mapping[str, Iterable[object]]) -> dict[str, list[str]]:
    return {
        category: sorted({str(value) for value in values if value not in (None, "")})
        for category, values in facts.items()
        if any(value not in (None, "") for value in values)
    }


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Invalid deterministic text chunk configuration.")
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        if start + size >= len(text):
            break
        start += size - overlap
    return chunks


def build_text_corpus(repository_root: Path, protocol: Mapping[str, Any]) -> list[dict[str, Any]]:
    config = protocol["text_rag"]
    records: list[tuple[str, str, str, dict[str, list[str]], dict[str, Any]]] = []
    extraction_path = repository_root / protocol["authoritative_text_sources"][0]
    for line_number, line in enumerate(extraction_path.read_text("utf-8").splitlines(), start=1):
        record = json.loads(line)
        text, facts = _flatten_extraction(record)
        records.append(
            (
                str(extraction_path.relative_to(repository_root)),
                f"line:{line_number}",
                text,
                facts,
                {
                    "document": record.get("document"),
                    "page": record.get("page"),
                    "authority": "authoritative-source-text-extraction; human-review-required",
                },
            )
        )
    recipe_path = repository_root / protocol["authoritative_text_sources"][1]
    recipe_payload = json.loads(recipe_path.read_text("utf-8"))
    for index, recipe in enumerate(recipe_payload["recipes"], start=1):
        text, facts = _flatten_recipe(recipe, recipe_payload["source"])
        records.append(
            (
                str(recipe_path.relative_to(repository_root)),
                f"recipe:{index}",
                text,
                facts,
                {
                    "document": recipe_payload["source"].get("filename"),
                    "page": recipe.get("page"),
                    "authority": "reviewed visual transcription; non-executable review candidate",
                },
            )
        )
    chunks = []
    seen: set[str] = set()
    chunk_number = 0
    for source_path, location, text, facts, provenance in records:
        for part_number, part in enumerate(
            _split_text(
                text,
                int(config["chunk_size_characters"]),
                int(config["chunk_overlap_characters"]),
            ),
            start=1,
        ):
            text_hash = sha256_bytes(part.encode("utf-8"))
            if text_hash in seen:
                continue
            seen.add(text_hash)
            chunk_number += 1
            chunks.append(
                {
                    "chunk_id": f"text-chunk-{chunk_number:04d}-{text_hash[:12]}",
                    "text_sha256": text_hash,
                    "source_path": source_path,
                    "source_location": f"{location}:part:{part_number}",
                    "provenance": provenance,
                    "text": part,
                    "facts": deepcopy(facts),
                }
            )
    return chunks


def _terms(text: str) -> list[str]:
    normalized = text.casefold()
    terms = re.findall(r"[a-z0-9][a-z0-9_.-]*", normalized)
    cjk_runs = re.findall(r"[\u3400-\u9fff]+", normalized)
    for run in cjk_runs:
        terms.extend(run)
        terms.extend(run[index : index + 2] for index in range(max(0, len(run) - 1)))
    return terms


def feature_hash_embedding(text: str, dimensions: int = 1024) -> dict[int, float]:
    counts = Counter(_terms(text))
    vector: dict[int, float] = {}
    for term, count in counts.items():
        digest = hashlib.sha256(term.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] = vector.get(index, 0.0) + sign * (1.0 + math.log(count))
    norm = math.sqrt(sum(value * value for value in vector.values()))
    return {index: value / norm for index, value in vector.items()} if norm else {}


def cosine(left: Mapping[int, float], right: Mapping[int, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(index, 0.0) for index, value in left.items())


def retrieve_text_chunks(
    question: str,
    corpus: list[dict[str, Any]],
    *,
    evidence_token_budget: int,
    candidate_top_k: int = 12,
    dimensions: int = 1024,
) -> dict[str, Any]:
    started = time.monotonic()
    query_vector = feature_hash_embedding(question, dimensions)
    ranked = sorted(
        (
            {
                **chunk,
                "similarity": round(
                    cosine(query_vector, feature_hash_embedding(chunk["text"], dimensions)), 12
                ),
                "evidence_tokens": estimate_component_tokens(chunk["text"].encode("utf-8")),
            }
            for chunk in corpus
        ),
        key=lambda item: (-item["similarity"], item["chunk_id"]),
    )[:candidate_top_k]
    selected = []
    used_tokens = 0
    for item in ranked:
        if used_tokens + item["evidence_tokens"] <= evidence_token_budget:
            selected.append(item)
            used_tokens += item["evidence_tokens"]
    if not selected:
        raise ValueError("Text-RAG budget could not fit the highest-ranked text chunk.")
    return {
        "retrieved_items": len(ranked),
        "selected_items": len(selected),
        "selected_chunks": selected,
        "evidence_tokens": used_tokens,
        "maximum_evidence_tokens": evidence_token_budget,
        "retrieval_latency_ms": round((time.monotonic() - started) * 1000),
    }


def _answer_output(answer: str) -> dict[str, Any]:
    return {
        "answer": answer,
        "evidence_node_ids": [],
        "citation_ids": [],
        "source_document_ids": [],
        "exact_claims": [],
    }


def _context_budgets_from_calls(calls: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [deepcopy(item["context_budget"]) for item in calls if item.get("context_budget")]


def assert_context_safe(context_budgets: list[Mapping[str, Any]]) -> None:
    if not context_budgets:
        raise ValueError("Controlled live run did not expose a context budget.")
    for budget in context_budgets:
        if not budget.get("fits") or budget.get("silent_truncation") is not False:
            raise ValueError("Controlled run failed the no-truncation preflight contract.")
        if budget.get("observed_within_input_budget") is False:
            raise ValueError("Observed prompt usage exceeded the controlled input budget.")


def _usage(calls: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(
        int(item.get("usage", {}).get(key, 0))
        for item in calls
        if isinstance(item.get("usage"), Mapping)
    )


def _requirement_accuracy(validation: Mapping[str, Any]) -> dict[str, bool]:
    claims = validation["claim_grounding"]["claims"]
    by_category: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        by_category.setdefault(claim["normalized_claim"]["category"], []).append(claim)

    def supported(category: str, value: object) -> bool:
        return any(
            item["status"] == "SUPPORTED"
            and str(item["normalized_claim"]["value"]).casefold() == str(value).casefold()
            for item in by_category.get(category, [])
        )

    def no_bad(*categories: str) -> bool:
        return not any(
            item["status"] in {"UNSUPPORTED", "CONTRADICTED"}
            for category in categories
            for item in by_category.get(category, [])
        )

    return {
        "classification": supported("feature_code", "9350906")
        and supported("feature_name", "消防栓")
        and no_bad("feature_code", "feature_name"),
        "geometry": supported("geometry", "Point") and no_bad("geometry"),
        "line_style": supported("line_style", "2") and no_bad("line_style"),
        "color": supported("color_code", "7")
        and supported("color_name", "black")
        and no_bad("color_code", "color_name"),
        "source_evidence": (
            supported("source_page", "11")
            or supported("record_id", "DOC01-P11-HYDRANT")
            or supported("revision", "NLSC112V5.4")
        )
        and no_bad(
            "source_page",
            "printed_page",
            "document_id",
            "document_name",
            "record_id",
            "revision",
        ),
        "unresolved_binding": supported("mapping_unresolved", True)
        and no_bad("mapping_unresolved", "product_layer"),
    }


def _failure_taxonomy(
    requirement_accuracy: Mapping[str, bool], validation: Mapping[str, Any]
) -> list[dict[str, str]]:
    coverage = {
        item["id"]: item["status"] for item in validation["question_coverage"]["requirements"]
    }
    claims = validation["claim_grounding"]["claims"]
    failures = []
    for requirement, correct in requirement_accuracy.items():
        if correct:
            continue
        if coverage[requirement] != "PASS":
            category = "OMISSION"
        elif requirement == "unresolved_binding" and any(
            item["normalized_claim"]["category"] == "product_layer"
            and item["status"] == "CONTRADICTED"
            for item in claims
        ):
            category = "UNRESOLVED_BINDING_GUESSED"
        elif any(item["status"] == "CONTRADICTED" for item in claims):
            category = "INCORRECT_VALUE"
        elif any(item["status"] == "UNSUPPORTED" for item in claims):
            category = "UNSUPPORTED_CLAIM"
        else:
            category = "OTHER"
        failures.append({"requirement": requirement, "category": category})
    return failures


def evaluate_answer(answer: str, evidence_package: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_rq1_answer(_answer_output(answer), evidence_package)
    accuracy = _requirement_accuracy(validation)
    coverage = validation["question_coverage"]["requirements"]
    return {
        "shared_validation": validation,
        "requirements": accuracy,
        "requirement_accuracy": sum(accuracy.values()) / 6,
        "exact_6_of_6": all(accuracy.values()),
        "coverage": sum(item["status"] == "PASS" for item in coverage) / 6,
        "exact_coverage_6_of_6": all(item["status"] == "PASS" for item in coverage),
        "failures": _failure_taxonomy(accuracy, validation),
    }


def evaluate_text_grounding(
    answer: str, retrieved: Mapping[str, Any], shared_validation: Mapping[str, Any]
) -> dict[str, Any]:
    facts: dict[str, set[str]] = {}
    selected_ids = set()
    for chunk in retrieved["selected_chunks"]:
        selected_ids.add(chunk["chunk_id"])
        for category, values in chunk["facts"].items():
            facts.setdefault(category, set()).update(str(value).casefold() for value in values)
    evaluated = []
    for claim in shared_validation["claim_grounding"]["claims"]:
        category = claim["normalized_claim"]["category"]
        value = str(claim["normalized_claim"]["value"]).casefold()
        available = facts.get(category, set())
        if value in available:
            status = "SUPPORTED"
        elif available:
            status = "CONTRADICTED"
        else:
            status = "UNSUPPORTED"
        evaluated.append(
            {
                "text": claim["text"],
                "normalized_claim": claim["normalized_claim"],
                "status": status,
            }
        )
    cited = sorted(set(CHUNK_ID_PATTERN.findall(answer)))
    counts = {
        f"{status.casefold()}_count": sum(item["status"] == status for item in evaluated)
        for status in ("SUPPORTED", "UNSUPPORTED", "CONTRADICTED")
    }
    return {
        "architecture": "text-rag",
        "claims": evaluated,
        **counts,
        "retrieved_reference_integrity": {
            "cited_chunk_ids": cited,
            "invalid_chunk_ids": sorted(set(cited) - selected_ids),
            "verdict": "PASS" if set(cited) <= selected_ids else "FAIL",
        },
    }


def _run_id(architecture: str, question_id: str, model: Mapping[str, Any], phase: str) -> str:
    payload = {
        "protocol": PROTOCOL_SCHEMA,
        "architecture": architecture,
        "question_id": question_id,
        "model": model,
        "phase": phase,
    }
    return "rq1-compare-run:sha256:" + sha256_bytes(canonical_json(payload))


class RQ1ComparisonRunner:
    def __init__(self, *, repository_root: Path, adapter: LLMAdapter) -> None:
        self.repository_root = repository_root
        self.adapter = adapter
        self.protocol = load_protocol(repository_root)
        self.questions = load_questions(repository_root, self.protocol)
        self.corpus = build_text_corpus(repository_root, self.protocol)

    def _base_record(
        self, architecture: str, question: Mapping[str, str], phase: str
    ) -> dict[str, Any]:
        model = self.protocol["model"]
        return {
            "run_id": _run_id(architecture, question["id"], model, phase),
            "phase": phase,
            "architecture": architecture,
            "question_id": question["id"],
            "question_identity": request_identity(question["text"]),
            "question": question["text"],
            "model": model["name"],
            "temperature": model["temperature"],
            "context_window": model["context_window"],
            "reserved_output_tokens": model["reserved_output_tokens"],
        }

    def run_graphrag(
        self, question: Mapping[str, str], *, phase: str = "primary"
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        started = time.monotonic()
        result = AMAResearchRuntime(
            repository_root=self.repository_root,
            adapter=self.adapter,
            graph_settings={
                "NMA_GRAPH_BACKEND": "canonical-json",
                "NMA_GRAPH_FALLBACK": "canonical-json",
            },
        ).run_rq1(question["text"])
        total_ms = round((time.monotonic() - started) * 1000)
        calls = result["model_calls"]
        budgets = _context_budgets_from_calls(calls)
        assert_context_safe(budgets)
        evaluation = evaluate_answer(result["answer"]["answer"], result["evidence_package"])
        grounding = result["answer_validation"]["claim_grounding"]
        record = {
            **self._base_record("graphrag", question, phase),
            "retrieval_latency_ms": total_ms - int(calls[-1]["latency_ms"]),
            "generation_latency_ms": int(calls[-1]["latency_ms"]),
            "total_latency_ms": total_ms,
            "retrieved_items": len(result["evidence_package"]["evidence_nodes"]),
            "llm_facing_items": len(result["llm_evidence_context"]["evidence_nodes"]),
            "retrieval_evidence_tokens": estimate_component_tokens(
                result["llm_evidence_context"]
            ),
            "prompt_tokens": _usage(calls, "input_tokens"),
            "answer_prompt_tokens": int(calls[-1].get("usage", {}).get("input_tokens", 0)),
            "completion_tokens": _usage(calls, "output_tokens"),
            "total_tokens": _usage(calls, "input_tokens") + _usage(calls, "output_tokens"),
            "preflight_context_margin": min(
                int(item["remaining_input_margin"]) for item in budgets
            ),
            "observed_context_margin": min(
                int(item["observed_input_margin"])
                for item in budgets
                if "observed_input_margin" in item
            ),
            "silent_truncation": False,
            "context_budgets": budgets,
            "answer": result["answer"]["answer"],
            "answer_raw_response_hash": calls[-1]["raw_response_hash"],
            "evaluation": evaluation,
            "grounding": {
                "architecture": "graphrag",
                "supported_count": grounding["supported_count"],
                "unsupported_count": grounding["unsupported_count"],
                "contradicted_count": grounding["contradicted_count"],
                "reference_integrity": result["answer_validation"]["reference_integrity"],
                "claims": grounding["claims"],
            },
            "graph": {
                "backend": result["graph_backend"]["active_backend"],
                "identity": result["graph_backend"]["graph_revision"],
                "retrieved_edges": len(result["evidence_package"]["graph_paths"]["edges"]),
                "projected_edges": len(result["llm_evidence_context"]["evidence_edges"]),
            },
        }
        return record, result

    def _run_baseline(
        self,
        architecture: str,
        question: Mapping[str, str],
        evidence_package: Mapping[str, Any],
        *,
        evidence_budget: int,
        phase: str,
    ) -> dict[str, Any]:
        retrieved = None
        retrieval_ms = 0
        evidence_context: dict[str, Any] = {
            "retrieval_status": "not-provided",
            "evidence": [],
        }
        if architecture == "text-rag":
            retrieved = retrieve_text_chunks(
                question["text"],
                self.corpus,
                evidence_token_budget=evidence_budget,
                candidate_top_k=int(self.protocol["text_rag"]["candidate_top_k"]),
                dimensions=int(self.protocol["text_rag"]["embedding_dimensions"]),
            )
            retrieval_ms = retrieved["retrieval_latency_ms"]
            evidence_context = {
                "retrieval_status": "authoritative-text-evidence-retrieved",
                "evidence": [
                    {
                        "chunk_id": item["chunk_id"],
                        "source_path": item["source_path"],
                        "source_location": item["source_location"],
                        "provenance": item["provenance"],
                        "text": item["text"],
                    }
                    for item in retrieved["selected_chunks"]
                ],
            }
        context = {
            "request": question["text"],
            "evidence_delivery": architecture,
            **evidence_context,
        }
        started = time.monotonic()
        result = self.adapter.generate_structured(
            task=SHARED_TASK,
            instructions=SHARED_INSTRUCTIONS,
            context=context,
            output_schema=ANSWER_SCHEMA,
        )
        generation_ms = round((time.monotonic() - started) * 1000)
        validate_json_schema_subset(result.output, ANSWER_SCHEMA)
        budgets = [result.context_budget] if result.context_budget else []
        assert_context_safe(budgets)
        answer = result.output["answer"]
        evaluation = evaluate_answer(answer, evidence_package)
        grounding: dict[str, Any]
        if architecture == "llm-only":
            shared = evaluation["shared_validation"]["claim_grounding"]
            grounding = {
                "architecture": "llm-only",
                "retrieval_grounding": "N/A",
                "unsupported_factual_assertions": shared["unsupported_count"],
                "contradicted_factual_assertions": shared["contradicted_count"],
                "claims": shared["claims"],
            }
        else:
            assert retrieved is not None
            grounding = evaluate_text_grounding(
                answer, retrieved, evaluation["shared_validation"]
            )
        usage = result.usage or {}
        record = {
            **self._base_record(architecture, question, phase),
            "retrieval_latency_ms": retrieval_ms,
            "generation_latency_ms": generation_ms,
            "total_latency_ms": retrieval_ms + generation_ms,
            "retrieved_items": 0 if retrieved is None else retrieved["retrieved_items"],
            "llm_facing_items": 0 if retrieved is None else retrieved["selected_items"],
            "retrieval_evidence_tokens": 0 if retrieved is None else retrieved["evidence_tokens"],
            "prompt_tokens": int(usage.get("input_tokens", 0)),
            "answer_prompt_tokens": int(usage.get("input_tokens", 0)),
            "completion_tokens": int(usage.get("output_tokens", 0)),
            "total_tokens": int(usage.get("input_tokens", 0))
            + int(usage.get("output_tokens", 0)),
            "preflight_context_margin": int(budgets[0]["remaining_input_margin"]),
            "observed_context_margin": int(budgets[0].get("observed_input_margin", 0)),
            "silent_truncation": False,
            "context_budgets": budgets,
            "answer": answer,
            "answer_raw_response_hash": result.raw_response_hash,
            "evaluation": evaluation,
            "grounding": grounding,
            "prompt_contract": {
                "task": SHARED_TASK,
                "instructions": SHARED_INSTRUCTIONS,
                "evidence_delivery": architecture,
                "answer_schema_fields": ["answer"],
            },
        }
        if retrieved is not None:
            record["text_retrieval"] = retrieved
        return record

    def run_primary(
        self, on_run: Callable[[dict[str, Any], int], None] | None = None
    ) -> dict[str, Any]:
        canonical = self.questions[0]
        canonical_graph, graph_result = self.run_graphrag(canonical)
        evidence_package = graph_result["evidence_package"]
        evidence_budget = canonical_graph["retrieval_evidence_tokens"]
        runs = [canonical_graph]
        if on_run is not None:
            on_run(canonical_graph, len(runs))
        runs.append(
            self._run_baseline(
                "llm-only",
                canonical,
                evidence_package,
                evidence_budget=evidence_budget,
                phase="primary",
            )
        )
        if on_run is not None:
            on_run(runs[-1], len(runs))
        runs.append(
            self._run_baseline(
                "text-rag",
                canonical,
                evidence_package,
                evidence_budget=evidence_budget,
                phase="primary",
            )
        )
        if on_run is not None:
            on_run(runs[-1], len(runs))
        for question in self.questions[1:]:
            runs.append(
                self._run_baseline(
                    "llm-only",
                    question,
                    evidence_package,
                    evidence_budget=evidence_budget,
                    phase="primary",
                )
            )
            if on_run is not None:
                on_run(runs[-1], len(runs))
            runs.append(
                self._run_baseline(
                    "text-rag",
                    question,
                    evidence_package,
                    evidence_budget=evidence_budget,
                    phase="primary",
                )
            )
            if on_run is not None:
                on_run(runs[-1], len(runs))
            graph_record, _ = self.run_graphrag(question)
            runs.append(graph_record)
            if on_run is not None:
                on_run(runs[-1], len(runs))
        if len(runs) != 33 or len({item["run_id"] for item in runs}) != 33:
            raise ValueError("Primary RQ1 run identities do not reconcile to 33 unique runs.")
        return self.build_results(runs, evidence_budget=evidence_budget)

    def build_results(
        self, runs: list[dict[str, Any]], *, evidence_budget: int
    ) -> dict[str, Any]:
        return {
            "schema": RESULTS_SCHEMA,
            "protocol": deepcopy(self.protocol),
            "source_identity": {
                path: sha256_file(self.repository_root / path)
                for path in self.protocol["authoritative_text_sources"]
            },
            "text_corpus": {
                "chunk_count": len(self.corpus),
                "identity_sha256": sha256_bytes(canonical_json(self.corpus)),
                "graph_ids_present": any(
                    "portrayal-rule:" in item["text"] or "section:doc" in item["text"]
                    for item in self.corpus
                ),
            },
            "normalization": {
                "canonical_graphrag_evidence_tokens": evidence_budget,
                "text_rag_maximum_evidence_tokens": evidence_budget,
                "tolerance_tokens": 0,
            },
            "raw_runs": runs,
            "aggregate": aggregate_results(runs),
        }

    def run_reproducibility(
        self,
        *,
        evidence_budget: int,
        repeats: int = 3,
        on_run: Callable[[dict[str, Any], int], None] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if repeats != 3:
            raise ValueError("RQ1-COMPARE-01 freezes three canonical repeats per architecture.")
        canonical = self.questions[0]
        runs: list[dict[str, Any]] = []
        evidence_package = None
        for index in range(1, repeats + 1):
            record, graph_result = self.run_graphrag(
                canonical, phase=f"reproducibility-{index}"
            )
            evidence_package = evidence_package or graph_result["evidence_package"]
            runs.append(record)
            if on_run is not None:
                on_run(record, len(runs))
        assert evidence_package is not None
        for architecture in ("llm-only", "text-rag"):
            for index in range(1, repeats + 1):
                record = self._run_baseline(
                    architecture,
                    canonical,
                    evidence_package,
                    evidence_budget=evidence_budget,
                    phase=f"reproducibility-{index}",
                )
                runs.append(record)
                if on_run is not None:
                    on_run(record, len(runs))
        summary = {}
        for architecture in ARCHITECTURES:
            items = [item for item in runs if item["architecture"] == architecture]
            answer_hashes = [sha256_bytes(item["answer"].encode("utf-8")) for item in items]
            summary[architecture] = {
                "repeat_count": len(items),
                "distinct_answer_count": len(set(answer_hashes)),
                "answer_sha256": answer_hashes,
                "requirement_accuracy": [
                    item["evaluation"]["requirement_accuracy"] for item in items
                ],
                "coverage": [item["evaluation"]["coverage"] for item in items],
                "identical_answers": len(set(answer_hashes)) == 1,
            }
        return runs, summary


def _distribution(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "mean": statistics.fmean(values) if values else 0,
        "median": statistics.median(values) if values else 0,
        "min": min(values) if values else 0,
        "max": max(values) if values else 0,
    }


def aggregate_results(runs: list[Mapping[str, Any]]) -> dict[str, Any]:
    result = {}
    for architecture in ARCHITECTURES:
        items = [item for item in runs if item["architecture"] == architecture]
        requirement_accuracy = [item["evaluation"]["requirement_accuracy"] for item in items]
        coverage = [item["evaluation"]["coverage"] for item in items]
        per_requirement = {
            requirement: sum(item["evaluation"]["requirements"][requirement] for item in items)
            / len(items)
            for requirement in (
                "classification",
                "geometry",
                "line_style",
                "color",
                "source_evidence",
                "unresolved_binding",
            )
        }
        if architecture == "llm-only":
            supported: int | str = "N/A"
            unsupported = sum(
                item["grounding"]["unsupported_factual_assertions"] for item in items
            )
            contradicted = sum(
                item["grounding"]["contradicted_factual_assertions"] for item in items
            )
        else:
            supported = sum(item["grounding"]["supported_count"] for item in items)
            unsupported = sum(item["grounding"]["unsupported_count"] for item in items)
            contradicted = sum(item["grounding"]["contradicted_count"] for item in items)
        result[architecture] = {
            "run_count": len(items),
            "requirement_accuracy": _distribution(requirement_accuracy),
            "exact_6_of_6_count": sum(item["evaluation"]["exact_6_of_6"] for item in items),
            "exact_6_of_6_rate": sum(item["evaluation"]["exact_6_of_6"] for item in items)
            / len(items),
            "coverage": _distribution(coverage),
            "exact_coverage_count": sum(
                item["evaluation"]["exact_coverage_6_of_6"] for item in items
            ),
            "exact_coverage_rate": sum(
                item["evaluation"]["exact_coverage_6_of_6"] for item in items
            )
            / len(items),
            "per_requirement_accuracy": per_requirement,
            "supported_claims": supported,
            "unsupported_claims": unsupported,
            "contradicted_claims": contradicted,
            "retrieval_evidence_tokens": _distribution(
                [item["retrieval_evidence_tokens"] for item in items]
            ),
            "prompt_tokens": _distribution([item["prompt_tokens"] for item in items]),
            "completion_tokens": _distribution([item["completion_tokens"] for item in items]),
            "total_latency_ms": _distribution([item["total_latency_ms"] for item in items]),
            "silent_truncation_events": sum(item["silent_truncation"] for item in items),
            "failure_count": sum(len(item["evaluation"]["failures"]) for item in items),
        }
    return result

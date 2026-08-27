from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


EVIDENCE_CONTEXT_SCHEMA = "nma.question-relevant-evidence-context/1.0"


_INTENT_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "classification",
        ("classification", "class code", "feature code", "分類", "編碼"),
        ("PORTRAYED_BY",),
    ),
    (
        "geometry",
        (
            "geometry",
            "geometric",
            "point geometry",
            "line geometry",
            "polygon geometry",
            "幾何",
        ),
        ("APPLIES_TO_GEOMETRY",),
    ),
    (
        "line-style",
        ("line style", "line-style", "line code", "stroke", "線號", "線式"),
        ("USES_LINE_STYLE",),
    ),
    (
        "color",
        ("color", "colour", "color code", "colour code", "顏色", "色碼"),
        ("USES_COLOR",),
    ),
    (
        "source-provenance",
        ("source", "evidence", "citation", "provenance", "來源", "證據", "引文"),
        ("EVIDENCED_ON", "CONTAINS"),
    ),
    (
        "review-authority",
        ("reviewed", "authoritative", "authority", "review", "權威", "審查"),
        ("TRANSCRIBES_RULE", "DEFINES", "EVIDENCED_ON", "CONTAINS"),
    ),
    (
        "binding-state",
        (
            "binding",
            "schema",
            "product-layer",
            "product layer",
            "field mapping",
            "綁定",
            "欄位",
        ),
        ("PORTRAYED_BY",),
    ),
)


def _question_intents(question: str) -> tuple[list[str], set[str]]:
    normalized = question.casefold()
    labels: list[str] = []
    predicates: set[str] = set()
    for label, markers, relationships in _INTENT_RULES:
        if any(marker in normalized for marker in markers):
            labels.append(label)
            predicates.update(relationships)
    return labels, predicates


def _selected_anchor_ids(
    evidence: Mapping[str, Any], nodes_by_id: Mapping[str, Mapping[str, Any]], intents: list[str]
) -> list[str]:
    retrieval_trace = evidence.get("retrieval_trace", {})
    selected = (
        retrieval_trace.get("model_selected_seed_ids", [])
        if isinstance(retrieval_trace, Mapping)
        else []
    )
    selected = [item for item in selected if isinstance(item, str) and item in nodes_by_id]
    if not selected:
        return []
    if any(intent in intents for intent in ("review-authority", "source-provenance")):
        rules = [item for item in selected if nodes_by_id[item].get("type") == "PortrayalRule"]
        if rules:
            return rules
    return selected


def _citation_matches_projected_nodes(
    citation: Mapping[str, Any], projected_node_ids: set[str], projected_record_ids: set[str]
) -> bool:
    return bool(
        citation.get("section_id") in projected_node_ids
        or citation.get("record_id") in projected_record_ids
    )


def project_question_relevant_evidence(
    *, question: str, evidence: Mapping[str, Any]
) -> dict[str, Any]:
    """Project retrieved evidence into a compact, provenance-preserving LLM context.

    Retrieval remains untouched. Selection is based on question intent, model-selected canonical
    entities, typed graph relationships, and source containment rather than feature identities or
    expected answer values.
    """

    nodes = evidence.get("evidence_nodes", [])
    paths = evidence.get("graph_paths", {})
    edges = paths.get("edges", []) if isinstance(paths, Mapping) else []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("Retrieved evidence must contain node and edge lists.")
    nodes_by_id = {
        item["id"]: item
        for item in nodes
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    intents, relevant_predicates = _question_intents(question)
    anchors = _selected_anchor_ids(evidence, nodes_by_id, intents)
    if not anchors:
        raise ValueError("Evidence projection requires at least one retrieved selected entity.")

    # Grounded generation always carries source provenance, even when the question does not ask
    # for a citation explicitly.
    relevant_predicates.update(("EVIDENCED_ON", "CONTAINS"))

    projected_node_ids = set(anchors)
    projected_edges: list[dict[str, Any]] = []
    projected_edge_keys: set[tuple[str, str, str]] = set()

    def include_edge(edge: Mapping[str, Any]) -> None:
        source = edge.get("source")
        target = edge.get("target")
        relationship = edge.get("type")
        if not all(isinstance(item, str) for item in (source, target, relationship)):
            return
        if source not in nodes_by_id or target not in nodes_by_id:
            return
        key = (source, relationship, target)
        if key in projected_edge_keys:
            return
        projected_edge_keys.add(key)
        projected_node_ids.update((source, target))
        projected_edges.append(deepcopy(dict(edge)))

    for item in edges:
        if not isinstance(item, Mapping) or item.get("type") not in relevant_predicates:
            continue
        if item.get("source") in anchors or item.get("target") in anchors:
            include_edge(item)

    # Preserve the authoritative document identity for every selected evidence section.
    section_ids = {
        node_id
        for node_id in projected_node_ids
        if nodes_by_id[node_id].get("type") == "DocumentSection"
    }
    for item in edges:
        if (
            isinstance(item, Mapping)
            and item.get("type") == "CONTAINS"
            and item.get("target") in section_ids
        ):
            include_edge(item)

    projected_nodes = [
        deepcopy(dict(item))
        for item in nodes
        if isinstance(item, Mapping) and item.get("id") in projected_node_ids
    ]
    projected_record_ids = {
        value
        for item in projected_nodes
        for value in (
            item.get("properties", {}).get("record_id"),
            item.get("properties", {}).get("evidence_record"),
        )
        if isinstance(value, str)
    }
    citations = [
        deepcopy(dict(item))
        for item in evidence.get("citations", [])
        if isinstance(item, Mapping)
        and _citation_matches_projected_nodes(item, projected_node_ids, projected_record_ids)
    ]
    cited_hashes = {
        item.get("source_sha256") for item in citations if isinstance(item.get("source_sha256"), str)
    }
    cited_filenames = {
        item.get("filename") for item in citations if isinstance(item.get("filename"), str)
    }
    source_documents = [
        deepcopy(dict(item))
        for item in evidence.get("source_documents", [])
        if isinstance(item, Mapping)
        and (item.get("sha256") in cited_hashes or item.get("filename") in cited_filenames)
    ]

    return {
        "schema": EVIDENCE_CONTEXT_SCHEMA,
        "query": question,
        "projection": {
            "basis": "question-intent + selected-entity + typed-relationship + provenance",
            "detected_intents": intents,
            "anchor_node_ids": anchors,
            "retrieved_node_count": len(nodes_by_id),
            "projected_node_count": len(projected_nodes),
            "omitted_node_count": len(nodes_by_id) - len(projected_nodes),
        },
        "evidence_nodes": projected_nodes,
        "evidence_edges": projected_edges,
        "citations": citations,
        "source_documents": source_documents,
        "epistemic_context": {
            key: deepcopy(evidence.get(key))
            for key in (
                "status",
                "automatic_rule_activation",
                "clarification",
                "conflicts",
                "missing_evidence",
            )
            if key in evidence
        },
    }

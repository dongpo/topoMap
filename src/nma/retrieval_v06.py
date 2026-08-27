from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .graphrag import CanonicalGraphRetriever
from .retrieval_v05 import HybridGraphRetrieverV05


class CitationIntegrityError(ValueError):
    """The v0.6 citation resolver or reviewed source registry is invalid."""


def load_citation_source_registry(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != "nma.citation-source-registry/0.6":
        raise CitationIntegrityError("Unsupported citation-source registry schema.")
    if not isinstance(payload.get("documents"), dict):
        raise CitationIntegrityError("Citation-source registry documents are missing.")
    return payload


class CitationIntegrityGraphRetrieverV06(CanonicalGraphRetriever):
    """Resolve every section citation through its canonical CONTAINS edge.

    v0.4 used a convenience fallback that assigned an unconnected section to the only document
    present in the selected subgraph. That can cross document boundaries. v0.6 instead inspects
    the complete canonical graph, requires exactly one containing document, and never guesses.
    """

    def __init__(self, graph: dict[str, Any], source_registry: dict[str, Any]):
        super().__init__(graph)
        if source_registry.get("schema") != "nma.citation-source-registry/0.6":
            raise CitationIntegrityError("Unsupported citation-source registry schema.")
        self.source_registry = source_registry
        self.section_document_ids: dict[str, list[str]] = {}
        for edge in self.edges:
            if edge["type"] != "CONTAINS":
                continue
            source = self.nodes.get(edge["source"])
            target = self.nodes.get(edge["target"])
            if not source or not target or target["type"] != "DocumentSection":
                continue
            is_document = source["type"] == "SpecificationDocument" or (
                source["type"] == "CrossGraphReference"
                and source.get("properties", {}).get("expected_type")
                == "SpecificationDocument"
            )
            if is_document:
                self.section_document_ids.setdefault(edge["target"], []).append(edge["source"])
        for section_id in self.section_document_ids:
            self.section_document_ids[section_id] = sorted(
                set(self.section_document_ids[section_id])
            )

    @classmethod
    def load_with_registry(
        cls, graph_path: str | Path, registry_path: str | Path
    ) -> "CitationIntegrityGraphRetrieverV06":
        graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
        return cls(graph, load_citation_source_registry(registry_path))

    def document_properties(self, document_id: str) -> tuple[dict[str, Any], str]:
        graph_properties = dict(self.nodes.get(document_id, {}).get("properties", {}))
        registry_properties = dict(
            self.source_registry.get("documents", {}).get(document_id, {})
        )
        properties = graph_properties | registry_properties
        provenance = "canonical-graph"
        if registry_properties:
            provenance = "canonical-graph-plus-reviewed-source-registry"
        return properties, provenance

    def citation_integrity_inventory(self) -> list[dict[str, Any]]:
        inventory: list[dict[str, Any]] = []
        for section_id, section in sorted(self.nodes.items()):
            if section["type"] != "DocumentSection":
                continue
            document_ids = self.section_document_ids.get(section_id, [])
            if len(document_ids) != 1:
                inventory.append(
                    {
                        "section_id": section_id,
                        "document_ids": document_ids,
                        "status": (
                            "missing-document-containment"
                            if not document_ids
                            else "ambiguous-document-containment"
                        ),
                        "metadata_complete": False,
                    }
                )
                continue
            document_id = document_ids[0]
            properties, provenance = self.document_properties(document_id)
            inventory.append(
                {
                    "section_id": section_id,
                    "document_ids": document_ids,
                    "status": "verified-unique-document-containment",
                    "metadata_complete": bool(
                        properties.get("filename") and properties.get("sha256")
                    ),
                    "metadata_provenance": provenance,
                }
            )
        return inventory

    def _citations(
        self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        del edges  # selected-subgraph edges must not control document identity
        citations: list[dict[str, Any]] = []
        for section in sorted(nodes, key=lambda item: item["id"]):
            if section["type"] != "DocumentSection":
                continue
            section_id = section["id"]
            section_properties = section.get("properties", {})
            document_ids = self.section_document_ids.get(section_id, [])
            if len(document_ids) == 1:
                document_id = document_ids[0]
                document_properties, metadata_provenance = self.document_properties(document_id)
                integrity = "verified-unique-document-containment"
            else:
                document_id = None
                document_properties = {}
                metadata_provenance = None
                integrity = (
                    "missing-document-containment"
                    if not document_ids
                    else "ambiguous-document-containment"
                )
            citations.append(
                {
                    "citation_id": f"citation:{section_id}",
                    "section_id": section_id,
                    "document_id": document_id,
                    "filename": document_properties.get("filename"),
                    "revision": document_properties.get("revision"),
                    "source_sha256": document_properties.get("sha256"),
                    "page": section_properties.get("page"),
                    "printed_page": section_properties.get("printed_page"),
                    "record_id": section_properties.get("record_id"),
                    "review_status": section_properties.get("review_status"),
                    "source_text": section_properties.get("source_text"),
                    "citation_integrity": integrity,
                    "document_candidates": document_ids,
                    "metadata_provenance": metadata_provenance,
                }
            )
        return citations


class HybridGraphRetrieverV06(HybridGraphRetrieverV05):
    """v0.5 retrieval policy plus strict source-document citation integrity."""

    def evidence_package(self, query: str, **kwargs: Any) -> dict[str, Any]:
        package = super().evidence_package(query, **kwargs)
        citations = package.get("citations", [])
        integrity_failures = [
            citation
            for citation in citations
            if citation.get("citation_integrity")
            != "verified-unique-document-containment"
            or not citation.get("filename")
            or not citation.get("source_sha256")
        ]
        trace = package["retrieval_trace"]
        trace["retrieval_policy_version"] = "0.6"
        trace["v06_citation_policy"] = "strict-canonical-containment-no-single-document-fallback"
        trace["v06_citation_integrity"] = (
            "passed" if not integrity_failures else "failed"
        )
        if integrity_failures:
            package["missing_evidence"] = list(package.get("missing_evidence", [])) + [
                "One or more evidence sections lack a unique, metadata-complete source-document containment relation."
            ]
        package["automatic_rule_activation"] = False
        return package

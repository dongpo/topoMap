from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def compile_portrayal_graph(records_path: Path, profile_path: Path) -> dict[str, Any]:
    """Compile reviewed PDF observations into a portable property graph.

    Extraction observations and rendering implementations stay separate. This prevents a
    hand-drawn demo glyph from being mistaken for a fact extracted from an official PDF.
    """

    records = _read_jsonl(records_path)
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    document_id = records[0]["document_id"]
    nodes: list[dict[str, Any]] = [
        {
            "id": f"document:{document_id}",
            "type": "SpecificationDocument",
            "properties": {
                "title": records[0]["document"],
                "uri": records[0]["source_uri"],
                "sha256": profile.get("source", {}).get("sha256"),
                "pages": profile.get("source", {}).get("pages"),
                "visual_verification_pages": profile.get("source", {}).get(
                    "visual_verification_pages", []
                ),
            },
        },
        {
            "id": f"version:{profile['profile_id']}",
            "type": "SpecificationVersion",
            "properties": {
                "name": profile["version"],
                "scale_denominator": profile["scale_denominator"],
                "effective_date": records[0]["effective_date"],
                "profile_id": profile["profile_id"],
                "source_verification_date": profile.get("source", {}).get(
                    "verification_date"
                ),
            },
        },
    ]
    edges: list[dict[str, Any]] = [
        {
            "from": f"document:{document_id}",
            "type": "HAS_VERSION",
            "to": f"version:{profile['profile_id']}",
        }
    ]

    for record in records:
        feature_id = f"feature:{record['feature_code']}"
        observation_id = f"observation:{record['record_id']}"
        rule_id = f"rule:portrayal:{profile['profile_id']}:{record['feature_code']}"
        section_id = f"section:{document_id}:p{record['page']}"
        implementation = profile["implementations"][record["feature_code"]]
        symbol_id = f"symbol:{implementation['symbol_id']}"
        source_layers = profile["source_layers"][record["feature_code"][:2]]
        nodes.extend(
            [
                {
                    "id": feature_id,
                    "type": "FeatureType",
                    "properties": {
                        "name": record["feature_name"],
                        "code": record["feature_code"],
                        "aliases": _aliases(record["feature_name"]),
                    },
                },
                {
                    "id": section_id,
                    "type": "DocumentSection",
                    "properties": {"page": record["page"]},
                },
                {
                    "id": observation_id,
                    "type": "SourceObservation",
                    "properties": {
                        "production_stage": record["production_stage"],
                        "geometry_classes": record["geometry_classes"],
                        "line_code": record["line_code"],
                        "color_code": record["color_code"],
                        "instruction": record["instruction"],
                        "source_text": record["source_text"],
                        "extraction_method": record["extraction_method"],
                        "review_status": record["review_status"],
                    },
                },
                {
                    "id": rule_id,
                    "type": "PortrayalRule",
                    "properties": {
                        "feature_code": record["feature_code"],
                        "scale_denominator": profile["scale_denominator"],
                        "source_layers": source_layers,
                        "instruction": record["instruction"],
                        "implementation_status": profile["implementation_status"],
                    },
                },
                {
                    "id": symbol_id,
                    "type": "Symbol",
                    "properties": implementation,
                },
            ]
        )
        edges.extend(
            [
                {"from": f"version:{profile['profile_id']}", "type": "DEFINES", "to": feature_id},
                {"from": f"document:{document_id}", "type": "CONTAINS", "to": section_id},
                {"from": section_id, "type": "YIELDS", "to": observation_id},
                {"from": observation_id, "type": "DESCRIBES", "to": feature_id},
                {"from": feature_id, "type": "PORTRAYED_BY", "to": rule_id},
                {"from": rule_id, "type": "USES_SYMBOL", "to": symbol_id},
                {"from": rule_id, "type": "SUPPORTED_BY", "to": observation_id},
                {"from": observation_id, "type": "EVIDENCED_ON", "to": section_id},
            ]
        )

    for conflict in profile.get("known_conflicts", []):
        conflict_id = f"conflict:{conflict['conflict_id']}"
        nodes.append({"id": conflict_id, "type": "ProfileConflict", "properties": conflict})
        edges.extend(
            {
                "from": f"feature:{code}",
                "type": "HAS_PROFILE_CONFLICT",
                "to": conflict_id,
            }
            for code in conflict["subject_codes"]
        )

    # Nodes such as a shared school symbol occur repeatedly. Merge only identical IDs while
    # retaining every feature-specific rule and evidence path.
    merged = {node["id"]: node for node in nodes}
    return {
        "graph_id": "nma-portrayal-knowledge-v0.1",
        "profile": profile,
        "nodes": list(merged.values()),
        "edges": edges,
        "statistics": {"nodes": len(merged), "edges": len(edges), "observations": len(records)},
    }


def _aliases(name: str) -> list[str]:
    aliases = [part.strip() for part in re.split(r"[、,/，]", name) if part.strip()]
    translations = {
        "消防栓": ["fire hydrant", "hydrant"],
        "養殖池": ["fish pond", "aquaculture pond"],
        "郵局": ["post office"],
        "警察局": ["police station"],
        "分駐所": ["police substation"],
        "派出所": ["police office"],
        "小學": ["elementary school", "primary school"],
        "中學": ["secondary school"],
        "大專院校": ["college", "university"],
        "幼兒園": ["kindergarten"],
        "特殊學校": ["special school"],
        "職訓中心": ["vocational training centre", "vocational training center"],
    }
    for part in list(aliases):
        aliases.extend(translations.get(part, []))
    if name == "大專院校":
        aliases.extend(["學校", "school"])
    if any(term in name for term in ("學", "幼兒園", "職訓中心")):
        aliases.extend(["學校", "school"])
    return sorted(set(aliases))


@dataclass(frozen=True)
class GraphPath:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {"nodes": [node["id"] for node in self.nodes], "edges": self.edges}


class PortrayalGraph:
    def __init__(self, graph: dict[str, Any]):
        self.graph = graph
        self.nodes = {node["id"]: node for node in graph["nodes"]}
        self.outgoing: dict[str, list[dict[str, Any]]] = {}
        for edge in graph["edges"]:
            self.outgoing.setdefault(edge["from"], []).append(edge)

    @classmethod
    def load(cls, path: str | Path) -> "PortrayalGraph":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def feature(self, code: str) -> dict[str, Any] | None:
        return self.nodes.get(f"feature:{code}")

    def find_features(self, query: str) -> list[dict[str, Any]]:
        normalized = query.casefold()
        codes = set(re.findall(r"\b\d{7}\b", query))
        ranked: list[tuple[int, dict[str, Any]]] = []
        for node in self.nodes.values():
            if node["type"] != "FeatureType":
                continue
            props = node["properties"]
            terms = [props["name"], props["code"], *props.get("aliases", [])]
            score = 100 if props["code"] in codes else 0
            score += max((len(term) for term in terms if term.casefold() in normalized), default=0)
            if score:
                ranked.append((score, node))
        return [node for _, node in sorted(ranked, key=lambda item: (-item[0], item[1]["id"]))]

    def portrayal_path(self, code: str) -> GraphPath | None:
        feature_id = f"feature:{code}"
        if feature_id not in self.nodes:
            return None
        edges: list[dict[str, Any]] = []
        node_ids = [feature_id]
        for edge in self.outgoing.get(feature_id, []):
            if edge["type"] == "PORTRAYED_BY":
                edges.append(edge)
                node_ids.append(edge["to"])
                for next_edge in self.outgoing.get(edge["to"], []):
                    if next_edge["type"] in {"USES_SYMBOL", "SUPPORTED_BY"}:
                        edges.append(next_edge)
                        node_ids.append(next_edge["to"])
                        if next_edge["type"] == "SUPPORTED_BY":
                            for evidence_edge in self.outgoing.get(next_edge["to"], []):
                                if evidence_edge["type"] == "EVIDENCED_ON":
                                    edges.append(evidence_edge)
                                    node_ids.append(evidence_edge["to"])
        return GraphPath([self.nodes[node_id] for node_id in dict.fromkeys(node_ids)], edges)

    def nodes_of_type(self, node_type: str) -> Iterable[dict[str, Any]]:
        return (node for node in self.nodes.values() if node["type"] == node_type)

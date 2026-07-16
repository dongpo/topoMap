from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .knowledge import PortrayalGraph


@dataclass(frozen=True)
class PortrayalDecision:
    status: str
    feature_code: str | None
    feature_name: str | None
    symbol: dict[str, Any] | None
    rule: dict[str, Any] | None
    evidence: dict[str, Any] | None
    graph_path: dict[str, Any] | None
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "feature_code": self.feature_code,
            "feature_name": self.feature_name,
            "symbol": self.symbol,
            "rule": self.rule,
            "evidence": self.evidence,
            "graph_path": self.graph_path,
            "reason": self.reason,
        }


class PortrayalAgent:
    """A small, auditable agent over executable portrayal knowledge.

    The language model boundary is intentionally optional. The research claim is evaluated on
    graph retrieval, rule selection, evidence and compiled map output—not conversational fluency.
    """

    def __init__(self, graph: PortrayalGraph):
        self.graph = graph

    def select_symbol(
        self,
        feature_code: str,
        *,
        scale_denominator: int = 1000,
        profile_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> PortrayalDecision:
        profile = self.graph.graph["profile"]
        if profile_id and profile_id != profile["profile_id"]:
            return PortrayalDecision(
                "abstain",
                feature_code,
                None,
                None,
                None,
                None,
                None,
                f"Profile {profile_id!r} is not loaded; refusing to borrow a symbol from "
                f"{profile['profile_id']!r}.",
            )
        if scale_denominator != profile["scale_denominator"]:
            return PortrayalDecision(
                "abstain",
                feature_code,
                None,
                None,
                None,
                None,
                None,
                f"No reviewed portrayal rule for scale 1:{scale_denominator}.",
            )
        path = self.graph.portrayal_path(feature_code)
        if not path:
            return PortrayalDecision(
                "not_found",
                feature_code,
                None,
                None,
                None,
                None,
                None,
                "No feature or portrayal rule was found in the loaded executable knowledge.",
            )
        by_type = {node["type"]: node for node in path.nodes}
        feature = by_type["FeatureType"]["properties"]
        rule = by_type["PortrayalRule"]["properties"] | {
            "rule_id": by_type["PortrayalRule"]["id"]
        }
        symbol = by_type["Symbol"]["properties"]
        section = by_type["DocumentSection"]["properties"]
        observation = by_type["SourceObservation"]["properties"]
        document = next(self.graph.nodes_of_type("SpecificationDocument"))["properties"]
        version = next(self.graph.nodes_of_type("SpecificationVersion"))["properties"]
        evidence = {
            "document": document["title"],
            "version": version["name"],
            "page": section["page"],
            "text": observation["source_text"],
            "uri": document["uri"],
            "review_status": observation["review_status"],
        }
        if symbol.get("exception", {}).get("condition") == "large_detached_building" and (
            attributes or {}
        ).get("large_detached_building"):
            symbol = symbol | {"selected_action": "text_only", "icon_image": None}
            reason = "The rule's large-detached-building exception selects a text annotation."
        else:
            symbol = symbol | {"selected_action": "draw_symbol"}
            reason = "Feature code, profile and scale matched an evidence-backed portrayal rule."
        return PortrayalDecision(
            "selected",
            feature_code,
            feature["name"],
            symbol,
            rule,
            evidence,
            path.as_dict(),
            reason,
        )

    def answer(self, question: str) -> dict[str, Any]:
        features = self.graph.find_features(question)
        if not features:
            return {
                "status": "abstain",
                "answer": "The loaded portrayal knowledge does not contain a matching feature.",
                "feature_codes": [],
                "evidence": [],
                "graph_paths": [],
            }
        decisions = [self.select_symbol(node["properties"]["code"]) for node in features]
        lowered = question.casefold()
        if any(term in lowered for term in ("code", "代碼", "編碼")):
            answer = "；".join(
                f"{decision.feature_name}: {decision.feature_code}" for decision in decisions
            )
        elif any(term in lowered for term in ("page", "哪一頁", "頁")):
            answer = "；".join(
                f"{decision.feature_name}: page {decision.evidence['page']}"
                for decision in decisions
                if decision.evidence
            )
        elif any(term in lowered for term in ("large", "大型", "獨幢", "exception", "例外")):
            answer = "；".join(
                decision.rule["instruction"] for decision in decisions if decision.rule
            )
        elif any(term in lowered for term in ("symbol", "符號", "圖式", "呈現", "portray")):
            answer = "；".join(
                f"{decision.feature_name} → {decision.symbol['symbol_id']}"
                for decision in decisions
                if decision.symbol
            )
        else:
            answer = "；".join(
                f"{decision.feature_name} ({decision.feature_code}), "
                f"{decision.rule['instruction']}"
                for decision in decisions
                if decision.rule
            )
        return {
            "status": "answered",
            "answer": answer,
            "feature_codes": [decision.feature_code for decision in decisions],
            "evidence": [decision.evidence for decision in decisions],
            "graph_paths": [decision.graph_path for decision in decisions],
        }


def compile_maplibre_layers(graph: PortrayalGraph) -> list[dict[str, Any]]:
    profile = graph.graph["profile"]
    agent = PortrayalAgent(graph)
    layers: list[dict[str, Any]] = []
    for feature in sorted(graph.nodes_of_type("FeatureType"), key=lambda node: node["id"]):
        code = feature["properties"]["code"]
        decision = agent.select_symbol(code)
        if decision.status != "selected":
            continue
        symbol = decision.symbol or {}
        for source_layer in decision.rule["source_layers"]:
            base = {
                "id": f"nma-{code}-{source_layer.lower()}",
                "type": symbol["maplibre_type"],
                "source": "data",
                "source-layer": source_layer,
                "filter": ["==", ["to-string", ["get", "TERRAINID"]], code],
                "metadata": {
                    "nma:profile": profile["profile_id"],
                    "nma:featureCode": code,
                    "nma:featureName": decision.feature_name,
                    "nma:ruleId": decision.rule["rule_id"],
                    "nma:evidence": decision.evidence,
                    "nma:graphPath": decision.graph_path,
                    "nma:implementationStatus": decision.rule["implementation_status"],
                },
            }
            if symbol["maplibre_type"] == "symbol":
                base["layout"] = {
                    "icon-image": symbol["icon_image"],
                    "icon-size": ["interpolate", ["linear"], ["zoom"], 13, 0.9, 16, 1.1, 18, 1.3],
                    "icon-allow-overlap": True,
                    "icon-ignore-placement": True,
                }
            else:
                base["paint"] = symbol["paint"]
            layers.append(base)
            if symbol.get("companion_icon"):
                layers.append(
                    {
                        "id": f"nma-{code}-icon-{source_layer.lower()}",
                        "type": "symbol",
                        "source": "data",
                        "source-layer": source_layer,
                        "filter": base["filter"],
                        "metadata": base["metadata"] | {"nma:role": "portrayal-icon"},
                        "layout": {
                            "icon-image": symbol["companion_icon"],
                            "icon-size": [
                                "interpolate",
                                ["linear"],
                                ["zoom"],
                                15,
                                0.8,
                                18,
                                1.2,
                            ],
                            "icon-allow-overlap": True,
                        },
                    }
                )
            if symbol.get("label_field"):
                layers.append(
                    {
                        "id": f"nma-{code}-label-{source_layer.lower()}",
                        "type": "symbol",
                        "source": "data",
                        "source-layer": source_layer,
                        "filter": base["filter"],
                        "metadata": base["metadata"] | {"nma:role": "label"},
                        "layout": {
                            "text-field": [
                                "coalesce",
                                ["get", symbol["label_field"]],
                                ["get", "NAME"],
                                "",
                            ],
                            "text-size": ["interpolate", ["linear"], ["zoom"], 13, 10, 17, 12],
                            "text-offset": [0, 1.1],
                            "text-anchor": "top",
                            "text-allow-overlap": True,
                        },
                        "paint": {
                            "text-color": "#111111",
                            "text-halo-color": "#ffffff",
                            "text-halo-width": 1.2,
                        },
                    }
                )
    return layers

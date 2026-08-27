from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from nma.neo4j_retrieval_v028 import load_live_projection_v028, open_neo4j_driver
from nma.retrieval_v06 import (
    CitationIntegrityGraphRetrieverV06,
    load_citation_source_registry,
)


ALLOWED_LOCAL_SETTINGS = {
    "NMA_GRAPH_BACKEND",
    "NMA_GRAPH_FALLBACK",
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "NEO4J_DATABASE",
}


class RuntimeGraphBackendError(RuntimeError):
    """The requested runtime graph backend cannot be activated safely."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normal_nodes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(graph["nodes"], key=lambda item: item["id"])


def _normal_edges(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        graph["edges"],
        key=lambda item: (
            item["type"],
            item["source"],
            item["target"],
            _canonical_json(item.get("properties", {})),
            tuple(item.get("source_graphs", [])),
        ),
    )


def load_runtime_graph_settings(
    local_path: str | Path,
    *,
    environ: dict[str, str] | None = None,
) -> dict[str, str]:
    """Read only allowlisted graph settings; never execute or expose the local file."""

    environment = os.environ if environ is None else environ
    values: dict[str, str] = {}
    path = Path(local_path)
    if path.is_file():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            name, value = line.split("=", 1)
            name = name.strip()
            if name in ALLOWED_LOCAL_SETTINGS:
                values[name] = value.strip().strip("'\"")
    merged = {
        key: environment.get(key) or values.get(key) or ""
        for key in ALLOWED_LOCAL_SETTINGS
    }
    neo4j_complete = all(
        merged[key] for key in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD")
    )
    merged["NMA_GRAPH_BACKEND"] = merged["NMA_GRAPH_BACKEND"] or (
        "neo4j" if neo4j_complete else "canonical-json"
    )
    merged["NMA_GRAPH_FALLBACK"] = merged["NMA_GRAPH_FALLBACK"] or "canonical-json"
    merged["NEO4J_DATABASE"] = merged["NEO4J_DATABASE"] or "neo4j"
    return merged


def _canonical_retriever(
    canonical_graph: dict[str, Any], registry: dict[str, Any]
) -> CitationIntegrityGraphRetrieverV06:
    return CitationIntegrityGraphRetrieverV06(canonical_graph, registry)


def select_runtime_graph_backend_v029(
    *,
    canonical_graph_path: str | Path,
    citation_registry_path: str | Path,
    settings: dict[str, str],
    driver_factory: Callable[[str, str, str], Any] = open_neo4j_driver,
) -> tuple[CitationIntegrityGraphRetrieverV06, dict[str, Any]]:
    canonical_path = Path(canonical_graph_path)
    canonical_graph = json.loads(canonical_path.read_text(encoding="utf-8"))
    registry = load_citation_source_registry(citation_registry_path)
    requested = settings.get("NMA_GRAPH_BACKEND", "canonical-json")
    fallback = settings.get("NMA_GRAPH_FALLBACK", "canonical-json")
    if requested not in {"canonical-json", "neo4j"}:
        raise RuntimeGraphBackendError(f"Unsupported graph backend: {requested!r}.")
    if fallback not in {"canonical-json", "none"}:
        raise RuntimeGraphBackendError(f"Unsupported graph fallback: {fallback!r}.")
    base_trace = {
        "contract": "nma.runtime-graph-backend/0.29",
        "requested_backend": requested,
        "active_backend": "canonical-json",
        "fallback_backend": fallback,
        "fallback_used": False,
        "fallback_reason_code": None,
        "graph_revision": canonical_graph["graph_id"],
        "graph_identity_verified": True,
        "active_graph_authoritative": True,
        "neo4j_database": None,
        "typed_tool_only": True,
        "arbitrary_cypher_allowed": False,
        "automatic_rule_activation": False,
    }
    if requested == "canonical-json":
        return _canonical_retriever(canonical_graph, registry), base_trace

    required = {
        key: settings.get(key, "")
        for key in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD")
    }
    missing = sorted(key for key, value in required.items() if not value)
    failure_code = None
    failure: Exception | None = None
    if missing:
        failure_code = "neo4j-settings-incomplete"
        failure = RuntimeGraphBackendError(
            f"Neo4j backend settings are incomplete: {', '.join(missing)}"
        )
    else:
        driver = None
        try:
            driver = driver_factory(
                required["NEO4J_URI"], required["NEO4J_USER"], required["NEO4J_PASSWORD"]
            )
            database = settings.get("NEO4J_DATABASE") or "neo4j"
            live_graph = load_live_projection_v028(
                driver,
                database=database,
                graph_revision=canonical_graph["graph_id"],
            )
            if (
                _normal_nodes(live_graph) != _normal_nodes(canonical_graph)
                or _normal_edges(live_graph) != _normal_edges(canonical_graph)
            ):
                raise RuntimeGraphBackendError(
                    "The live Neo4j projection differs from the canonical graph revision."
                )
            trace = {
                **base_trace,
                "active_backend": "live-neo4j",
                "neo4j_database": database,
                "live_nodes": len(live_graph["nodes"]),
                "live_edges": len(live_graph["edges"]),
            }
            return CitationIntegrityGraphRetrieverV06(live_graph, registry), trace
        except Exception as error:  # fail closed or use only the explicit safe fallback
            failure_code = (
                "neo4j-projection-mismatch"
                if isinstance(error, RuntimeGraphBackendError)
                else "neo4j-unavailable"
            )
            failure = error
        finally:
            if driver is not None:
                driver.close()

    if fallback != "canonical-json":
        raise RuntimeGraphBackendError(
            f"Neo4j activation failed with {failure_code}; canonical fallback is disabled."
        ) from failure
    return _canonical_retriever(canonical_graph, registry), {
        **base_trace,
        "fallback_used": True,
        "fallback_reason_code": failure_code,
        "graph_identity_verified": False,
        "active_graph_authoritative": True,
    }

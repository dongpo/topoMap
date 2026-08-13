from __future__ import annotations

import base64
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .graphrag import CanonicalGraphRetriever


EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_DIMENSIONS = 512
DEFAULT_TEXT_MAX_CHARS = 4_000


class VectorIndexError(ValueError):
    """The embedding request, stored index, or hybrid retrieval result is invalid."""


def canonical_graph_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def embedding_text_for_node(
    node: dict[str, Any], *, max_chars: int = DEFAULT_TEXT_MAX_CHARS
) -> str:
    if max_chars < 200:
        raise VectorIndexError("Embedding text bound must be at least 200 characters.")
    properties = json.dumps(
        node.get("properties", {}), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    source_graphs = ", ".join(sorted(node.get("source_graphs", [])))
    text = (
        f"NMA knowledge graph entity\n"
        f"type: {node['type']}\n"
        f"id: {node['id']}\n"
        f"properties: {properties}\n"
        f"source graphs: {source_graphs}"
    )
    return text[:max_chars]


def _encode_vector(vector: list[float], dimensions: int) -> str:
    if len(vector) != dimensions:
        raise VectorIndexError(
            f"Embedding dimensions differ: expected {dimensions}, got {len(vector)}."
        )
    if not all(math.isfinite(value) for value in vector):
        raise VectorIndexError("Embedding contains a non-finite value.")
    return base64.b64encode(struct.pack(f"<{dimensions}f", *vector)).decode("ascii")


def _decode_vector(encoded: str, dimensions: int) -> tuple[float, ...]:
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as error:
        raise VectorIndexError("Stored embedding is not valid base64.") from error
    expected_bytes = dimensions * 4
    if len(raw) != expected_bytes:
        raise VectorIndexError(
            f"Stored embedding byte length differs: expected {expected_bytes}, got {len(raw)}."
        )
    return struct.unpack(f"<{dimensions}f", raw)


class OpenAIEmbeddingClient:
    def __init__(
        self,
        api_key: str,
        *,
        url: str = EMBEDDINGS_URL,
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key.strip():
            raise VectorIndexError("OpenAI API key is empty.")
        self._api_key = api_key
        self.url = url
        self.timeout_seconds = timeout_seconds

    def embed_batch(
        self, texts: list[str], *, model: str, dimensions: int
    ) -> dict[str, Any]:
        if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
            raise VectorIndexError("Embedding batch must contain non-empty strings.")
        payload = {
            "input": texts,
            "model": model,
            "encoding_format": "float",
            "dimensions": dimensions,
        }
        request = Request(
            self.url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "nma-vector-index-v0.4",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise VectorIndexError(f"OpenAI embeddings request failed with HTTP {error.code}.") from error
        except (URLError, TimeoutError) as error:
            raise VectorIndexError("OpenAI embeddings request could not reach the API.") from error
        except json.JSONDecodeError as error:
            raise VectorIndexError("OpenAI embeddings response was not valid JSON.") from error
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or len(data) != len(texts):
            raise VectorIndexError("OpenAI embeddings response count differs from the request.")
        ordered = sorted(data, key=lambda item: item.get("index", -1))
        vectors = [item.get("embedding") for item in ordered]
        if any(not isinstance(vector, list) for vector in vectors):
            raise VectorIndexError("OpenAI embeddings response is missing a vector.")
        usage = body.get("usage", {})
        return {
            "vectors": vectors,
            "response_model": body.get("model"),
            "usage": {
                "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                "total_tokens": int(usage.get("total_tokens", 0)),
            },
        }


def build_vector_index(
    graph: dict[str, Any],
    *,
    graph_path: str | Path,
    embed_batch: Callable[..., dict[str, Any]],
    model: str = DEFAULT_EMBEDDING_MODEL,
    dimensions: int = DEFAULT_DIMENSIONS,
    batch_size: int = 128,
    text_max_chars: int = DEFAULT_TEXT_MAX_CHARS,
) -> dict[str, Any]:
    if dimensions < 1 or batch_size < 1:
        raise VectorIndexError("Embedding dimensions and batch size must be positive.")
    nodes = sorted(graph["nodes"], key=lambda item: item["id"])
    texts = [embedding_text_for_node(node, max_chars=text_max_chars) for node in nodes]
    records = []
    total_prompt_tokens = 0
    total_tokens = 0
    response_models: set[str] = set()
    for start in range(0, len(nodes), batch_size):
        batch_nodes = nodes[start : start + batch_size]
        batch_texts = texts[start : start + batch_size]
        response = embed_batch(batch_texts, model=model, dimensions=dimensions)
        vectors = response.get("vectors")
        if not isinstance(vectors, list) or len(vectors) != len(batch_nodes):
            raise VectorIndexError("Embedding provider returned an invalid batch.")
        usage = response.get("usage", {})
        total_prompt_tokens += int(usage.get("prompt_tokens", 0))
        total_tokens += int(usage.get("total_tokens", 0))
        if isinstance(response.get("response_model"), str):
            response_models.add(response["response_model"])
        for node, text, vector in zip(batch_nodes, batch_texts, vectors, strict=True):
            records.append(
                {
                    "node_id": node["id"],
                    "node_type": node["type"],
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "vector_f32_le_base64": _encode_vector(vector, dimensions),
                }
            )
    graph_hash = canonical_graph_sha256(graph_path)
    return {
        "schema": "nma.vector-index/0.4",
        "status": "provider-backed-semantic-index-built; rebuildable-runtime-index",
        "index_id": f"nma-vector:{graph['graph_id']}:{model}:{dimensions}",
        "canonical_graph_id": graph["graph_id"],
        "canonical_graph_sha256": graph_hash,
        "embedding": {
            "provider": "openai",
            "request_model": model,
            "response_models": sorted(response_models),
            "dimensions": dimensions,
            "encoding": "float32-little-endian-base64",
            "similarity": "cosine",
            "text_max_chars": text_max_chars,
        },
        "statistics": {
            "records": len(records),
            "batches": math.ceil(len(records) / batch_size),
            "batch_size": batch_size,
        },
        "usage": {
            "prompt_tokens": total_prompt_tokens,
            "total_tokens": total_tokens,
        },
        "records": records,
        "canonical_json_remains_source_of_truth": True,
        "automatic_rule_activation": False,
    }


class VectorIndex:
    def __init__(self, payload: dict[str, Any]):
        if payload.get("schema") != "nma.vector-index/0.4":
            raise VectorIndexError("Unsupported vector index schema.")
        self.payload = payload
        self.dimensions = int(payload["embedding"]["dimensions"])
        self.model = payload["embedding"]["request_model"]
        records = payload.get("records")
        if not isinstance(records, list) or not records:
            raise VectorIndexError("Vector index has no records.")
        self.vectors: dict[str, tuple[float, ...]] = {}
        self.node_types: dict[str, str] = {}
        for record in records:
            node_id = record["node_id"]
            if node_id in self.vectors:
                raise VectorIndexError(f"Duplicate vector node ID: {node_id}.")
            self.vectors[node_id] = _decode_vector(
                record["vector_f32_le_base64"], self.dimensions
            )
            self.node_types[node_id] = record["node_type"]

    @classmethod
    def load(cls, path: str | Path) -> "VectorIndex":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def search(
        self, query_vector: list[float], *, limit: int = 20, min_similarity: float = -1.0
    ) -> list[dict[str, Any]]:
        if len(query_vector) != self.dimensions:
            raise VectorIndexError("Query embedding dimensions differ from the index.")
        query_norm = math.sqrt(sum(value * value for value in query_vector))
        if query_norm == 0:
            raise VectorIndexError("Query embedding has zero norm.")
        ranked = []
        for node_id, vector in self.vectors.items():
            vector_norm = math.sqrt(sum(value * value for value in vector))
            similarity = (
                sum(left * right for left, right in zip(query_vector, vector, strict=True))
                / (query_norm * vector_norm)
                if vector_norm
                else -1.0
            )
            if similarity >= min_similarity:
                ranked.append((similarity, node_id))
        return [
            {
                "node_id": node_id,
                "node_type": self.node_types[node_id],
                "similarity": similarity,
            }
            for similarity, node_id in sorted(ranked, key=lambda item: (-item[0], item[1]))[
                :limit
            ]
        ]


def build_query_embedding_cache(
    queries: list[dict[str, str]],
    *,
    embed_batch: Callable[..., dict[str, Any]],
    model: str,
    dimensions: int,
) -> dict[str, Any]:
    if not queries or any(set(item) != {"id", "query"} for item in queries):
        raise VectorIndexError("Query embedding cache requires id and query records.")
    if len({item["id"] for item in queries}) != len(queries):
        raise VectorIndexError("Query embedding cache IDs must be unique.")
    response = embed_batch(
        [item["query"] for item in queries], model=model, dimensions=dimensions
    )
    vectors = response.get("vectors")
    if not isinstance(vectors, list) or len(vectors) != len(queries):
        raise VectorIndexError("Embedding provider returned an invalid query batch.")
    return {
        "schema": "nma.query-embedding-cache/0.4",
        "status": "development-query-vectors-built; not-a-held-out-evaluation",
        "embedding": {
            "provider": "openai",
            "request_model": model,
            "response_model": response.get("response_model"),
            "dimensions": dimensions,
            "encoding": "float32-little-endian-base64",
        },
        "usage": response.get("usage", {}),
        "records": [
            {
                "task_id": item["id"],
                "query_sha256": hashlib.sha256(item["query"].encode("utf-8")).hexdigest(),
                "vector_f32_le_base64": _encode_vector(vector, dimensions),
            }
            for item, vector in zip(queries, vectors, strict=True)
        ],
        "held_out_claim_allowed": False,
    }


class QueryEmbeddingCache:
    def __init__(self, payload: dict[str, Any]):
        if payload.get("schema") != "nma.query-embedding-cache/0.4":
            raise VectorIndexError("Unsupported query embedding cache schema.")
        self.model = payload["embedding"]["request_model"]
        self.dimensions = int(payload["embedding"]["dimensions"])
        self.usage = payload.get("usage", {})
        self.vectors = {
            record["query_sha256"]: list(
                _decode_vector(record["vector_f32_le_base64"], self.dimensions)
            )
            for record in payload["records"]
        }

    @classmethod
    def load(cls, path: str | Path) -> "QueryEmbeddingCache":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def embed_query(self, query: str, model: str, dimensions: int) -> dict[str, Any]:
        if model != self.model or dimensions != self.dimensions:
            raise VectorIndexError("Query cache model or dimensions differ from the vector index.")
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        vector = self.vectors.get(query_hash)
        if vector is None:
            raise VectorIndexError("Query is absent from the bounded development cache.")
        return {"vector": vector, "usage": {"cached": True, "total_tokens": 0}}


class HybridGraphRetriever:
    def __init__(
        self,
        graph_retriever: CanonicalGraphRetriever,
        vector_index: VectorIndex,
        embed_query: Callable[[str, str, int], dict[str, Any]],
        *,
        min_vector_similarity: float = 0.34,
        lexical_weight: float = 1.0,
        vector_weight: float = 1.5,
        rrf_constant: int = 60,
    ) -> None:
        self.graph_retriever = graph_retriever
        self.vector_index = vector_index
        self.embed_query = embed_query
        self.min_vector_similarity = min_vector_similarity
        self.lexical_weight = lexical_weight
        self.vector_weight = vector_weight
        self.rrf_constant = rrf_constant
        self.known_feature_codes = {
            str(value).casefold()
            for node in graph_retriever.nodes.values()
            for key in ("code", "feature_code", "id")
            for value in [node.get("properties", {}).get(key)]
            if isinstance(value, (str, int))
        }

    def evidence_package(
        self,
        query: str,
        *,
        seed_limit: int = 6,
        vector_limit: int = 24,
        max_depth: int = 2,
        max_nodes: int = 60,
    ) -> dict[str, Any]:
        lexical = self.graph_retriever.evidence_package(
            query, seed_limit=seed_limit, max_depth=max_depth, max_nodes=max_nodes
        )
        embedded = self.embed_query(query, self.vector_index.model, self.vector_index.dimensions)
        query_vector = embedded.get("vector")
        if not isinstance(query_vector, list):
            raise VectorIndexError("Query embedding provider returned no vector.")
        raw_vector_hits = self.vector_index.search(
            query_vector,
            limit=max(vector_limit * 8, vector_limit),
            min_similarity=self.min_vector_similarity,
        )
        vector_hits = []
        selected_vector_types: set[str] = set()
        for hit in raw_vector_hits:
            if hit["node_type"] in selected_vector_types:
                continue
            selected_vector_types.add(hit["node_type"])
            vector_hits.append(hit)
            if len(vector_hits) >= vector_limit:
                break
        lexical_ids = lexical["retrieval_trace"]["selected_seed_ids"]
        field_scope_requested = any(
            keyword in query.casefold()
            for keyword in ("欄位", "屬性", "field", "attribute")
        )
        supplied_codes = {
            match.casefold()
            for match in re.findall(r"(?<![0-9A-Za-z])[0-9]{7}[0-9A-Za-z]*(?![0-9A-Za-z])", query)
        }
        unknown_supplied_codes = sorted(supplied_codes - self.known_feature_codes)
        if unknown_supplied_codes and not lexical_ids:
            vector_hits = []
        scores: dict[str, float] = {}
        traces: dict[str, dict[str, Any]] = {}
        for rank, node_id in enumerate(lexical_ids, start=1):
            scores[node_id] = scores.get(node_id, 0.0) + self.lexical_weight / (
                self.rrf_constant + rank
            )
            traces.setdefault(node_id, {})["lexical_rank"] = rank
        for rank, hit in enumerate(vector_hits, start=1):
            node_id = hit["node_id"]
            if node_id not in self.graph_retriever.nodes:
                continue
            scores[node_id] = scores.get(node_id, 0.0) + self.vector_weight / (
                self.rrf_constant + rank
            )
            traces.setdefault(node_id, {}).update(
                {"vector_rank": rank, "vector_similarity": hit["similarity"]}
            )
        ordered_ids = [
            node_id
            for node_id, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[
                :seed_limit
            ]
        ]
        selected_ids = ordered_ids[:1]
        if field_scope_requested:
            for desired_type in ("ProductField", "ProductLayer", "EvidenceObservation"):
                candidate = next(
                    (
                        node_id
                        for node_id, _ in sorted(
                            scores.items(), key=lambda item: (-item[1], item[0])
                        )
                        if self.graph_retriever.nodes[node_id]["type"] == desired_type
                    ),
                    None,
                )
                if candidate and candidate not in selected_ids and len(selected_ids) < seed_limit:
                    selected_ids.append(candidate)
        if selected_ids:
            anchor = self.graph_retriever.nodes[selected_ids[0]]
            anchor_codes = {
                str(value).casefold()
                for key in ("code", "feature_code", "id")
                for value in [anchor.get("properties", {}).get(key)]
                if isinstance(value, (str, int))
            }
            for node_id, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0])):
                candidate = self.graph_retriever.nodes[node_id]
                if candidate["type"] != "ClassificationHierarchy":
                    continue
                candidate_code = candidate.get("properties", {}).get("code")
                if not isinstance(candidate_code, (str, int)):
                    continue
                normalized = str(candidate_code).casefold()
                if any(
                    normalized.startswith(code) or code.startswith(normalized)
                    for code in anchor_codes
                ):
                    if node_id not in selected_ids and len(selected_ids) < seed_limit:
                        selected_ids.append(node_id)
                    break
        ranked_trace = [
            {
                "id": node_id,
                "type": self.graph_retriever.nodes[node_id]["type"],
                "score": score,
                "matched_terms": [],
                "match_mode": "hybrid-rrf",
                "lexical_rank": traces[node_id].get("lexical_rank"),
                "vector_rank": traces[node_id].get("vector_rank"),
                "vector_similarity": traces[node_id].get("vector_similarity"),
            }
            for node_id, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[
                : max(seed_limit * 2, 10)
            ]
        ]
        package = self.graph_retriever.package_from_seed_ids(
            query,
            selected_ids,
            ranked_trace=ranked_trace,
            retrieval_mode=(
                "hybrid-openai-embedding-plus-deterministic-full-text-plus-typed-graph; "
                "neo4j-projection-ready-live-roundtrip-pending"
            ),
            max_depth=max_depth,
            max_nodes=max_nodes,
            expand_product_fields=field_scope_requested,
            extra_trace={
                "lexical_status": lexical["status"],
                "embedding_model": self.vector_index.model,
                "embedding_dimensions": self.vector_index.dimensions,
                "vector_similarity_threshold": self.min_vector_similarity,
                "vector_diversification": "best-candidate-per-node-type",
                "seed_policy": "semantic-anchor-plus-task-scoped-support",
                "unknown_explicit_identifiers": unknown_supplied_codes,
                "query_embedding_usage": embedded.get("usage", {}),
            },
        )
        package["automatic_rule_activation"] = False
        return package

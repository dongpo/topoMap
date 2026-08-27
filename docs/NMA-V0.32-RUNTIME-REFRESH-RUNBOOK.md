# NMA v0.32 runtime refresh runbook

This runbook completes F02 without overwriting any historical runtime artifact. Run it from the
repository root in a normal local terminal, because the Codex workspace sandbox blocks both
outbound API DNS resolution and local Bolt connections.

## Preconditions

- `.env.local` contains the existing ignored `OPENAI_API_KEY` and Neo4j settings.
- Neo4j is running locally.
- The canonical graph SHA-256 is
  `4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4`.

The commands below use the provider-backed embedding API and a MERGE-only Neo4j import. The import
does not delete existing nodes or relationships.

## Commands

The four gated steps can be run as one bounded command:

```bash
zsh scripts/run_nma_v032_external_runtime_refresh.sh
```

Its expanded commands are retained below for review or individual retry:

```bash
.venv/bin/python scripts/build_nma_vector_index_v04.py \
  --out data/runtime/vector/nma-vector-index-v0.32.json

.venv/bin/python scripts/run_nma_neo4j_roundtrip_v027.py \
  --live --allow-write \
  --out data/runtime/neo4j/nma-neo4j-round-trip-live-v0.32.json

.venv/bin/python scripts/run_nma_neo4j_retrieval_parity_v028.py \
  --out data/runtime/neo4j/nma-neo4j-retrieval-parity-v0.32.json

.venv/bin/python scripts/run_nma_runtime_graph_backend_v029.py \
  --out data/runtime/neo4j/nma-runtime-graph-backend-v0.32.json
```

## Acceptance checks

1. The vector index reports `4293` records and binds the current graph SHA-256.
2. The live round trip reports `live_import_executed: true`,
   `live_round_trip_verified: true`, and `canonical_reconstruction_lossless: true`.
3. Retrieval parity passes all five fixed point/line/polygon cases with matching graph identity.
4. Runtime graph-backend wiring reports the Neo4j backend and the current graph revision.
5. No command changes the preserved v0.4 vector index, v0.27 offline result, v0.30 live result, or
   any historical seal.

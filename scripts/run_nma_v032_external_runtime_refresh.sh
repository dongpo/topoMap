#!/bin/zsh
set -euo pipefail

script_dir="${0:A:h}"
repo_dir="${script_dir:h}"
cd "$repo_dir"

.venv/bin/python scripts/build_nma_vector_index_v04.py \
  --out data/runtime/vector/nma-vector-index-v0.32.json

.venv/bin/python scripts/run_nma_neo4j_roundtrip_v027.py \
  --live --allow-write \
  --out data/runtime/neo4j/nma-neo4j-round-trip-live-v0.32.json

.venv/bin/python scripts/run_nma_neo4j_retrieval_parity_v028.py \
  --out data/runtime/neo4j/nma-neo4j-retrieval-parity-v0.32.json

.venv/bin/python scripts/run_nma_runtime_graph_backend_v029.py \
  --out data/runtime/neo4j/nma-runtime-graph-backend-v0.32.json

echo "NMA v0.32 external runtime refresh completed."

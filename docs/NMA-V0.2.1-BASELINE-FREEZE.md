# NMA v0.2.1 Baseline Freeze

## Freeze identity

- Baseline tag: `nma-v0.2.1-baseline`
- Runtime contract: `nma.runtime-baseline/0.32`
- Verified source commit: `991269cea4a8eb6f6e4e9955f592bdf369fcd44c`
- Freeze manifest: `data/runtime/nma-baseline-freeze-v0.2.1.json`

The annotated Git tag is the authority for the final freeze-record commit containing this document and the freeze manifest. The verified source commit identifies the synchronized runtime state reviewed before these two release records were added.

This baseline represents:

> An open, reproducible engineering baseline for an evidence-bearing executable portrayal graph and Agent-assisted geospatial portrayal workflow.

## Included

- the executable portrayal graph and its consolidated canonical graph authority;
- the GraphRAG retrieval runtime;
- the v0.32 graph-bound vector index;
- portable and live-verified Neo4j projection support;
- the MapLibre portrayal pipeline;
- evidence and citation tracing from feature resolution to source document and page; and
- the School Hero workflow contract from Resolve through Cite.

## Excluded

- private or non-redistributable datasets and derived local caches;
- claims of autonomous authoritative map production;
- claims of production deployment readiness;
- complete national mapping specification or ontology coverage;
- reconstruction of unavailable component graph artifacts; and
- the three historical freeze/catalog failures classified in `docs/NMA-V0.2.1-HISTORICAL-TEST-STATUS.md`.

## Core artifact identities

### Knowledge graph

- Path: `data/knowledge/nma-canonical-graph-v0.4.json`
- Graph ID: `nma-canonical-graph-v0.4`
- SHA-256: `4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4`
- Nodes: 4,293
- Edges: 11,244

### Vector index

- Path: `data/runtime/vector/nma-vector-index-v0.32.json`
- Index ID: `nma-vector:nma-canonical-graph-v0.4:text-embedding-3-small:512`
- SHA-256: `9f45ba4196e7431eff094b202c8c55d0e99ca4c6f7d39c39fb600dd4d92f4d99`
- Embedding model: `text-embedding-3-small`
- Dimensions: 512
- Records: 4,293
- Canonical graph SHA-256: `4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4`

### Neo4j projection

- Database: `mapfeatures`
- Database ID: `60912A41C00A5078F9EF3E7055537F150D8E4D28D12FFDF10816F70066738F46`
- Nodes: 4,293
- Relationships: 11,244
- Canonical graph SHA-256: `4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4`
- Portable projection identity: verified
- Normalized round trip: lossless
- Live database verification: read-only and passed during REC-03B

## Verification boundary

The approved baseline checks verify graph identity, vector identity and graph binding, Neo4j projection consistency, explicit backend selection, supported retrieval with Document 01 page 61 evidence, unsupported-query abstention, and the public School Hero workflow contract.

The verified School Hero boundary covers contract ordering, evidence grounding, citation paths, and public runtime behavior. It does not claim that the private Shapefile execution path can be reproduced without the authorized archive, compatible GDAL/OGR inputs, and external credentials.

## Known limitations

- Private-data validation remains bounded by the non-redistributable archive and local GDAL/OGR environment described in `docs/NMA-V0.2.1-DATA-BOUNDARY.md`.
- Live Neo4j verification requires external database credentials that are not stored in the public repository.
- Three pre-existing historical Agentic v0.3 freeze/catalog tests remain unresolved and are excluded from this baseline's acceptance criteria.
- This freeze does not establish production deployment readiness, autonomous authority, complete national coverage, or complete ontology reconstruction.

## Immutability policy

The annotated tag `nma-v0.2.1-baseline` identifies this freeze. Corrections or extensions must use a new reviewed version or tag; the baseline tag and the recorded graph, vector, and runtime identities must not be moved or rewritten.

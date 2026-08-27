# NMA v0.2.1 Runtime Provenance Policy

## Purpose

This policy defines the graph authority and provenance boundary for the National Map Agent v0.2.1 runtime. It records the recovered state without reconstructing unavailable component artifacts.

## Canonical graph authority

`data/knowledge/nma-canonical-graph-v0.4.json` is the authoritative consolidated knowledge graph for the v0.2.1 runtime artifact. Its identity is:

- Graph ID: `nma-canonical-graph-v0.4`
- SHA-256: `4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4`
- Nodes: 4,293
- Edges: 11,244

The graph artifact revision (`v0.4`) and runtime release (`v0.2.1`) are separate identifiers. This policy does not rename or alter the graph schema or graph contents.

The runtime baseline, vector index, and Neo4j projection must bind to the canonical graph SHA-256 above. A component path is not an alternative runtime source and must not override the consolidated graph.

## Component graph paths

The canonical graph's `components` array records the following historical source paths as provenance metadata:

1. `data/knowledge/nma-feature-foundation-v0.4.json`
2. `data/knowledge/nma-production-workflow-v0.4.json`
3. `data/knowledge/nma-product-layers-v0.4.json`
4. `data/knowledge/nma-portrayal-v0.4.json`
5. `data/knowledge/nma-portrayal-batch-02-v0.4.json`
6. `data/knowledge/nma-portrayal-batch-03-v0.4.json`
7. `data/knowledge/nma-portrayal-batch-04-v0.4.json`
8. `data/knowledge/nma-portrayal-batch-05-v0.4.json`
9. `data/knowledge/nma-portrayal-batch-06-v0.4.json`
10. `data/knowledge/nma-portrayal-batch-07-v0.4.json`
11. `data/knowledge/nma-portrayal-batch-08-v0.4.json`
12. `data/knowledge/nma-portrayal-batch-09-v0.4.json`
13. `data/knowledge/nma-portrayal-batch-10-v0.4.json`
14. `data/knowledge/nma-portrayal-recipe-batch-01-v0.4.json`
15. `data/knowledge/nma-annex7-full-v0.4.json`
16. `data/knowledge/nma-road-compound-portrayal-v0.4.json`
17. `data/knowledge/nma-quality-assurance-v0.4.json`

These paths preserve lineage identifiers, component status, and recorded node/edge contributions. Their presence in metadata does not assert that the component files are available in the recovery branch and does not make them runtime dependencies.

## Deferred reconstruction

Full component reconstruction is deferred. REC-03A does not recreate, infer, split, or reverse-engineer any missing component graph from the consolidated graph.

Until a separately reviewed reconstruction process is authorized, the consolidated graph is the only runtime authority. Any future reconstructed component set must be reviewed independently and must demonstrate that recomposition reproduces the canonical graph identity before it can replace provenance-only metadata.

## Operational boundary

This policy changes provenance interpretation only. It does not expand ontology, modify graph schema, change benchmark definitions, or authorize new graph content.

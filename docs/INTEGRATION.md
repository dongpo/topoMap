# Profile and data integration guide

NMA core is framework-independent. A new national profile is integrated through data contracts,
validators, and evidence rather than a new agent framework.

## Required inputs

1. Legally usable specification documents with stable title, version, page, and source URI.
2. A bounded layer/profile with explicit geometry, CRS, fields, domains, and topology rules.
3. Public synthetic fixtures or legally redistributable samples.
4. Expert-approved expected outcomes and an unresolved-case policy.

## Integration sequence

1. Hash and inventory source documents without redistributing them by default.
2. Render and visually verify every page used as evidence.
3. Encode the smallest executable rule subset in `data/specifications/`.
4. Generate controlled clean and defective fixtures from transparent source files.
5. Freeze exact issue keys in `benchmark/ground-truth.json`.
6. Add knowledge, evidence, tool, validation, and safety tasks.
7. Obtain expert sign-off; record unresolved discrepancies as observations, not truth.
8. Run tests, offline ablations, and named-model experiments separately.

## Existing-data audit

Use read-only execution first:

```bash
nma validate --spec data/specifications/taiwan-5000-riverl-112.json \
  --dataset /path/to/RIVERL.shp \
  --json-out audit.json
```

Do not automatically rename fields, infer official identifiers, repair topology, overwrite source
files, or publish outputs. The flow is proposal -> preview -> approval -> execution -> revalidation
-> audit.

## Agent adapters

Agno, OpenAI Agents SDK, LangGraph, MCP, QGIS, and other runtimes should call the stable NMA tools.
They must not own the specification, validation, provenance, or approval data model.

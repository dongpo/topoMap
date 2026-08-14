# NMA v0.2.1 Data Boundary

## Purpose

This document defines the data boundary for reproducing and validating the National Map Agent v0.2.1 runtime baseline. It distinguishes the public Git artifact from private or restricted inputs used by the School Hero real-data execution path.

## Public baseline assets

The recovery branch contains the assets required to inspect, configure, and exercise the public runtime baseline:

- source code for the Agent runtime, API, demo, and supporting tools;
- `data/runtime/nma-runtime-baseline-v0.32.json`, which records the runtime contract `nma.runtime-baseline/0.32`;
- `data/knowledge/nma-canonical-graph-v0.4.json`, the authoritative consolidated graph artifact;
- `data/runtime/vector/nma-vector-index-v0.32.json`, the graph-bound vector index artifact;
- portable Neo4j projection metadata and read-only identity checks;
- public tests, deterministic fixtures, and golden retrieval checks; and
- recovery, provenance, integration, and operating documentation.

These assets are sufficient to reproduce the public runtime identity, confirm graph and vector provenance, exercise public retrieval behavior, and verify the School Hero workflow contract and evidence path.

## Private / non-redistributable assets

The following inputs are outside the public baseline:

- the reviewed private Shapefile archive used by the School Hero real-data path;
- restricted or owner-provided source datasets contained in that archive;
- local GDAL/OGR execution inputs and derived working files; and
- local caches or outputs produced while validating the private dataset.

The repository records validation expectations for these inputs, including checksum-bound loading, schema and geometry checks, and expected feature counts. It does not include or redistribute the private source data. Derived local files are runtime artifacts and are not public baseline dependencies.

## Reproducibility policy

### Runtime reproducibility

A clean checkout of the recovery branch must reproduce the public runtime identity without private data. At minimum, it must verify the runtime manifest, canonical graph identity, vector-to-graph hash binding, configured backend identity, public golden retrieval paths, and deterministic School Hero control-flow contract.

Absence of the private archive must not change the declared runtime contract, canonical graph, active vector source, or evidence citations. Any fallback or unavailable state must remain explicit.

### Private validation reproducibility boundary

The complete School Hero `Execute → Observe → QA → Cite` validation against reviewed real data can be reproduced only in an authorized environment that provides:

1. the exact private archive accepted by the runtime's recorded checksum policy;
2. a compatible GDAL/OGR installation; and
3. permission to process the restricted inputs locally.

When those prerequisites are absent, public tests may skip the private integration boundary. Such a skip means that private-data acceptance is not verified in that environment; it must not be replaced with synthetic data or reported as a completed real-data validation.

### Why private data is not included

The private archive and restricted datasets are excluded because redistribution permission has not been established for the public recovery artifact. This boundary preserves source restrictions and prevents private inputs or derived copies from entering Git history, release archives, or public deployments.

This policy documents the existing boundary only. It does not change licensing, grant redistribution rights, or alter runtime, graph, vector, benchmark, or schema behavior.

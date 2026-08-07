# Agentic v0.3 candidate freeze

Freeze date: 2026-08-07

Status: candidate frozen; owner review and public deployment remain separate gates.

## Why this is a new freeze

The original `nma-demo-v0.2-rc1` remains the stable evidence-only public release. Approved A01–A06
work added a materially different runtime: a 42-entry capability catalog, an interactive evidence
graph, supervised symbol versions, bounded GPT tool routing, approval-controlled Shapefile layer
creation, and an NLSC/local-basemap fallback. Those changes must not be validated against or
published under the old v0.2 fingerprints.

This freeze therefore creates a new Agentic v0.3 candidate boundary and verifies the v0.2 release
from its immutable Git snapshots.

## Frozen capabilities

| Increment | Frozen outcome |
|---|---|
| A01 | 42-entry PMTiles capability catalog with explicit evidence states |
| A02 | interactive evidence graph and complete typed path |
| A03 | immutable V0 symbol baseline plus reviewed derived versions |
| A04 | `gpt-5.6-terra` intent adapter, deterministic fallback, and application-owned gates |
| A05 | read-only Shapefile inspection, GeoJSON transformation, and separately approved MapLibre layer |
| A06 | NLSC EMAP primary basemap, local PMTiles fallback, and five-scene acceptance |

## Acceptance boundary

- Five original scenes and both abstention controls still pass.
- The catalog contains 42 registered capabilities: 5 evidence-backed, 4 conflicted, 28
  implementation-only, and 5 style variants.
- Only 9 catalog entries have a graph-evidence relationship; only 5 are clean evidence-backed
  examples.
- The graph remains the bounded 44-node, 85-edge reviewed-gate subset.
- The supervised school fixture contains 12 synthetic points, is read through GDAL/OGR from
  EPSG:3826, and is transformed to EPSG:4326 without changing the source.
- Natural-language output cannot approve a symbol or layer by itself.
- The public Pages site remains v0.2 evidence-only; Agentic v0.3 is not deployed by this freeze.

## Historical traceability

The checker verifies three earlier release records against the Git snapshots where their payloads
were frozen:

- v0.2 five-scene feature freeze;
- v0.2 Stable Demo RC1;
- deployed D21 bounded public-assets RC.

This lets the old release remain independently verifiable while the current working tree advances.

## Reproduce

```bash
make agentic-freeze
```

The command verifies every current artifact fingerprint, the five-scene contract, offline/browser
acceptance record, catalog counts, graph shape, bounded intent set, synthetic Shapefile contract,
and all three historical snapshots.

## Gates after freeze

1. Owner approval of the v0.3 freeze record.
2. Push the two local commits and wait for GitHub Actions.
3. If public access is approved, build a new bounded Pages candidate and repeat browser acceptance.
4. Keep PMTiles out of public artifacts until redistribution permission is confirmed.
5. Retain expert review, held-out evaluation, and DOI as explicit publication gates.

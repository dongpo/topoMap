# NMA v0.2 open architecture

## Design decision

NMA is specification-aware geospatial infrastructure with an optional agent at its boundary. The
core is not an agent framework and does not ask an LLM to perform deterministic GIS checks.

```text
User / QGIS / Web / CLI
          │
          ▼
Agent or task router (replaceable)
          │ structured operation
          ▼
NMA application boundary ───── approval policy
          │
     ┌────┴────────┐
     ▼             ▼
Specification   Deterministic validators
and evidence    CRS · schema · domain · geometry · topology
     │             │
     └────┬────────┘
          ▼
Validation report + provenance + repair proposal
          │ explicit approval
          ▼
Safe repair executor → revalidation → audit artifacts
```

## Component contracts

| Component | Owns | Must not own |
|---|---|---|
| Agent adapter | intent, tool choice, explanation | truth of a spatial validation |
| Specification store | versioned rules and evidence | mutable chat memory |
| Validator | reproducible pass/fail findings | open-ended policy interpretation |
| Repair policy | risk class and approval | silent authoritative writes |
| Report | result, evidence, tool provenance | hidden chain-of-thought |
| Benchmark | tasks, ground truth, scoring | promotional aggregate only |

## Current implementation

The implementation uses Python plus the GDAL/OGR command-line runtime. OGR reads Shapefile or
GeoJSON features in read-only mode and records the GDAL version, driver, layer, feature count, CRS,
extent, geometry, and detailed field definitions in provenance. Future validators can add direct
PROJ, GEOS/Shapely, PostGIS, and QGIS Processing execution while preserving the same report
contract.

The JSON profile, defined by `schemas/executable-profile.schema.json`, is the portable export
boundary for a future Neo4j knowledge graph. A graph
adapter should map entities (`Specification`, `Version`, `Layer`, `Field`, `ValidationRule`,
`DocumentSection`) into the same `Specification` and `Rule` domain objects. Core validation must
not contain Cypher or Neo4j session state.

## Trust boundaries

1. Document ingestion may propose rules but cannot publish them.
2. A rule is executable only after schema and expert review.
3. Validators accept frozen rule versions and emit deterministic findings.
4. LLM text may explain a finding but cannot replace its computed result.
5. Repairs are classified as `none`, `proposal`, or `safe`; even `safe` requires an explicit
   workflow approval.
6. Reports record the specification source and engine version.

## Extension interfaces

- `Specification.load`: replaceable storage adapter (JSON now, Neo4j/RDF later).
- `Validator`: registry point for GDAL/PostGIS/SHACL validators.
- `nma.api`: stable JSON boundary for QGIS, web applications, and MCP tools.
- `nma.baselines`: deterministic architecture controls.
- `nma.external`: shell-free `nma-bench-adapter/1.0` boundary for named model/runtime
  configurations and repeated runs.
- `Rule.repair`: policy metadata rather than executable model output.

## Deliberate omissions

The slice validates a single RIVERL layer and feature-level line self-intersection. It does not yet
execute cross-layer RIVERL/RIVERA intersection rules, full topology, complete feature-catalogue
coverage, graph reasoning, production identity management, or multi-agent orchestration. These are
explicit next layers, not hidden claims.

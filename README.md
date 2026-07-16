# National Map Agent v0.2

An open, reproducible vertical slice for testing whether a national-mapping agent can turn
authoritative specification pages into deterministic geospatial validation, evidence, and
human-controlled repair.

NMA v0.2 focuses on one defensible workflow: validation of the Taiwan 1:5,000 basic-topographic-map
`RIVERL` Shapefile profile. It does not claim autonomous national-map production or readiness for
deployment by a National Mapping Authority.

## What this release proves

- A bounded executable profile traces every rule to an official document, version, section, page,
  and source URL.
- GDAL/OGR reads a real Shapefile schema, CRS, feature count, geometry, attributes, and provenance
  without changing the source.
- Thirteen deterministic rules cover layer identity, TWD97/TM121, line geometry, exact field
  definitions, required values, identifier pattern, classification domain, self-intersection, and
  excess whitespace.
- The end-to-end demo detects four controlled defects, proposes three non-silent responses, applies
  only one explicitly approved safe normalization, and revalidates the result.
- NMA-Bench v0.1 freezes 31 tasks spanning specification knowledge, evidence, version awareness,
  tool selection, Shapefile validation, and authoritative-write safety.
- Existing `topoMap` PMTiles/static-map demos remain in the repository and are linked from the
  project landing page.

The source rules are authoritative-source-derived, but their machine-readable interpretation and
benchmark labels remain **pending domain-expert sign-off**.

## Five-minute reproduction

Requirements: Python 3.11+ and GDAL/OGR (`ogrinfo` and `ogr2ogr`).

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ".[dev]"
nma demo --approve-safe-repairs
nma-bench --root .
```

Or use containers:

```bash
docker compose --profile tools run --rm demo
docker compose --profile tools run --rm benchmark
```

Open `artifacts/demo/validation-before.html` for the spatial findings and cited evidence. The
controlled fixture contains three errors and one warning. Approval removes only the full-width
leading/trailing spaces; missing identity, undocumented classification, and self-intersection are
left for authoritative review.

## Evidence chain

```text
official PDF page
      ↓
machine-readable rule + source hash
      ↓
synthetic Shapefile with controlled defects
      ↓ GDAL/OGR, read-only
deterministic validation
      ↓
feature-level issue + exact evidence
      ↓
repair proposal
      ↓ explicit approval
safe normalization + revalidation + audit record
```

The primary source set is inventoried in
[`data/sources/authoritative-sources.json`](data/sources/authoritative-sources.json). The PDFs are
referenced rather than redistributed. Public benchmark Shapefiles contain synthetic geometries and
can be regenerated from the transparent CSV/VRT sources; see [`data/README.md`](data/README.md).

## Real-data observation

The user-provided `112年多維度SHP成果_0502.zip` was inspected read-only. It contains six sampled
`RIVERL` and `RIVERA` layer sets in TWD97[2020]/TM121. The `RIVERL` layers expose `RIVERID`, while
the cited 112-year specification page 39 states `RIVERLID`.

NMA reports this as a candidate schema discrepancy. It is not silently renamed, treated as proven
production error, or included as benchmark truth until an authority expert resolves whether the
cause is a specification revision, profile difference, or data defect.

## NMA-Bench v0.1

The checked-in smoke run produces these architecture-control results:

| Configuration | Accuracy | Provenance completeness |
|---|---:|---:|
| Ungrounded offline proxy | 0.226 | 0.000 |
| Document retrieval proxy | 0.290 | 0.000 |
| Structured retrieval | 0.645 | 0.812 |
| Full deterministic NMA | 1.000 | 1.000 |

These are harness and ablation checks, not empirical results for named LLMs. The ungrounded and
document systems are deterministic offline controls. Before publication, run frozen named models
through the answer-key-isolated adapter protocol in
[`docs/MODEL-BASELINES.md`](docs/MODEL-BASELINES.md) and follow
[`docs/RESEARCH-PROTOCOL.md`](docs/RESEARCH-PROTOCOL.md).

## Commands

```bash
# List executable rules and evidence
nma rules --spec data/specifications/taiwan-5000-riverl-112.json

# Inspect any supported vector dataset through GDAL/OGR
nma inspect data/datasets/authoritative/riverl-defective/RIVERL.shp

# Validate a Shapefile and render evidence
nma validate \
  --spec data/specifications/taiwan-5000-riverl-112.json \
  --dataset data/datasets/authoritative/riverl-defective/RIVERL.shp \
  --json-out artifacts/report.json \
  --html-out artifacts/report.html

# Start the dependency-free HTTP JSON API
nma serve --host 127.0.0.1 --port 8000
```

The API exposes `GET /health`, `GET /v1/specification`, `GET /v1/rules`, and
`POST /v1/validate`. The current HTTP validation body remains GeoJSON-oriented; Shapefile execution
is provided through the CLI and Python validator.

## Architecture boundary

The specification model, validators, repair policy, and benchmark do not depend on a large agent
framework. Agno, an LLM SDK, MCP, QGIS, or another runtime can be connected through adapters. The
agent may select a tool; deterministic code decides whether the data satisfies a rule, and
authoritative writes require approval. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## FOSS4G Hiroshima 2026

The accepted talk is **“National Map Agent: An Open Geospatial Architecture for Knowledge
Graph–Driven GeoAI.”** This implementation aligns with FOSS4G through Apache-2.0 code,
GDAL/OGR-based Shapefile execution, transparent fixture generation, open JSON contracts, Docker,
CI, reproducible scoring, and extension points for other national profiles. The demo and conference
claim boundary are in [`docs/FOSS4G-HIROSHIMA-2026.md`](docs/FOSS4G-HIROSHIMA-2026.md).

## Repository map

```text
src/nma/                         specification, OGR, validation, repair, API, CLI, benchmark
data/specifications/             executable official-source-derived and synthetic profiles
data/datasets/authoritative/     controlled public Shapefile fixtures
data/fixtures-source/            reproducible CSV/VRT fixture sources
data/sources/                    document and test-archive provenance
benchmark/tasks/                 31 machine-readable tasks
benchmark/ground-truth.json      frozen expected issue keys and review boundary
schemas/                         portable JSON contracts
tests/                           deterministic regression tests
docs/                            architecture, protocol, benchmark, and FOSS4G handoff
artifacts/                       regenerated demo and benchmark results
MapOutputDemo.html               preserved existing static map demo
pmtilesDemo.html                 preserved existing PMTiles demo
```

## License and citation

Code is Apache-2.0. Synthetic fixture geometries and CSV/VRT sources are CC0-1.0. No license is
asserted for the referenced official PDFs or the private test archive, neither of which is
redistributed. See `LICENSE`, `NOTICE`, and `CITATION.cff`.

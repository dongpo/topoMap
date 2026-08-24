# NMA ROAD browser integration v1

## Outcome

This slice extends the staged NMA application to a user's own ROAD Shapefile. It validates line
geometry and the Document 09 schema boundary in the browser, asks bounded questions when a safe
mapping is missing, retrieves classification and portrayal evidence through the read-only
Knowledge Service, requires plan-bound human authorization, and renders a MapLibre centreline and
line-following road-name preview.

Entry point: `nmaRoadDemoV1.html`

This is an engineering integration candidate. It is not the public GitHub Pages release and does
not activate an official or production road portrayal.

## Why ROAD is not School with a different colour

ROAD tests a different geometry and knowledge problem:

- LineString and MultiLineString source geometry;
- feature and vertex preservation;
- the distinction between Document 09 `ROADCLASS2` and observed `TERRAINID`;
- parent and child classification levels;
- a line-following `ROADNAME` annotation;
- optional route-number semantics from `ROADNUM`, `ROADNUM1`, and `ROADNUM2`;
- a governed boundary between the user's ROAD centreline and a surveyed-width ROADA boundary;
- a governed boundary between a retrieved shield code and an approved runtime shield graphic.

The application therefore does not reuse the frozen `中山街` filter or assume that every upload is
`9420400`. Every valid feature in the user's file remains in scope.

## Data gate

The archive gate is fail-closed:

- maximum ZIP size: 16 MiB;
- exactly one `ROAD` or `*_ROAD` Shapefile family;
- `.shp`, `.shx`, `.dbf`, and `.prj` are mandatory;
- `.cpg` is optional;
- LineString and MultiLineString geometry only;
- exact `ROADSEGID`, `ROADNAME`, `ROADNUM`, `ROADNUM1`, and `ROADNUM2` fields;
- either canonical `ROADCLASS2` or a `TERRAINID` field that a human explicitly maps for this
  session;
- non-empty `ROADSEGID` and unique `zip-relative-filename::ROADSEGID` identity;
- valid WGS84 coordinates after `.prj` transformation;
- maximum 50,000 features, plus ZIP entry and uncompressed-size limits.

Empty `ROADNAME` values do not erase the line. They produce no name label for that feature, while
the centreline remains visible. Route-number values may also be empty even though the reviewed
fields must exist.

The browser calculates feature count, total vertex count, per-feature vertex counts, multipart
count, named-feature count, numbered-feature count, and effective classification counts. Only the
bounded summary needed by the Agent crosses the API boundary; per-feature vertex arrays and source
geometry remain local.

## Schema and classification questions

The application distinguishes two kinds of ambiguity.

### `TERRAINID` versus `ROADCLASS2`

Document 09 defines `ROADCLASS2`. The reviewed K14/J17 profile uses `TERRAINID`. NMA does not assert
that every field named `TERRAINID` is globally equivalent. When it is observed, the application
asks the human whether it carries the Annex 7 road classification for this upload. The mapping is
stored in the plan as `session-human-confirmed`; it is not written to the canonical KG.

An upload with neither `ROADCLASS2` nor `TERRAINID` stops before planning.

### Parent classifications

The graph preserves the hierarchy rather than flattening it:

| Parent observed | Required child clarification |
|---|---|
| `9420100` 國道 | `9420101` 國道高速公路 or `9420102` 國道快速公路 |
| `9420200` 省道 | `9420201` 一般省道 or `9420202` 省道快速公路 |
| `9420800` 市區道路 | `9420801` 一般市區道路 or `9420802` 市區快速道路 |

The UI asks whether all features carrying that parent code belong to one reviewed child. It does
not silently inherit or select a portrayal. If that dataset-wide assertion is not valid, the user
must correct or subdivide the source data outside this preview.

Directly supported portrayal codes are:

`9420101`, `9420102`, `9420201`, `9420202`, `9420300`, `9420400`, `9420500`,
`9420600`, `9420700`, `9420801`, and `9420802`.

Other road families stop as unsupported in this slice; the Agent does not substitute a nearby
rule.

## Knowledge and Agent loop

For every effective class in the upload, the planner retrieves the exact Document 02 Annex 7
classification node and Document 01 portrayal rule, with graph paths and verified document/page
citations. Where a reviewed compound recipe exists, the plan also exposes route-shield code and
orientation as a semantic binding.

The active backend may be the identity-verified Neo4j projection or canonical JSON snapshot. The
Agent cannot submit arbitrary Cypher and cannot mutate the KG.

The observable loop is:

```text
observe ROAD geometry, schema mapping, counts, and vertices
→ retrieve classification and portrayal evidence
→ propose a centreline preview plan
→ request human authorization
→ observe compiler result
→ decide verify-then-stop
→ verify bindings, layers, counts, and governance boundary
→ render browser-local ROAD lines and line-following names
→ observe actual browser render
→ decide stop
```

A MapLibre style or render failure changes the next decision to `abstain-and-stop`. The presence of
an LLM is not required for this bounded symbolic Agent loop.

## Portrayal boundary

The browser creates two evidence-bound MapLibre layers for each effective class:

1. a derived centreline reference layer using the reviewed red or black colour family;
2. a `symbol-placement: line` layer using `ROADNAME`.

The fixed browser line width is explicitly a derived preview and is not a conversion of surveyed
road width. Official rules that say `實寬，註記名稱` require a reviewed association to ROADA
boundary geometry for full production portrayal. This slice does not infer that association,
derive road edges, repair topology, or claim surveyed-width correctness.

Likewise, `9490003`–`9490007` shield semantics may be retrieved, but no shield graphic is rendered
without a reviewed runtime renderer and asset binding.

The default map has a local blank background so user coordinates do not enter tile requests.
`?basemap=nlsc` explicitly opts into the NLSC EMAP WMTS basemap.

## Current implementation boundary

- Parsing and `.prj` conversion are browser-local through pinned `shpjs` 6.2.0. A production
  upload service should restore the repository's GDAL/OGR validation and CRS pipeline.
- Session mappings and parent-class answers are not persisted to the KG.
- Shapefile and parsed GeoJSON bytes remain in the browser tab.
- No data is exported.
- No ROADA surveyed-width boundary, route-shield graphic, official rule, or production runtime is
  activated.
- The accepted historical K14 evidence remains authority for its frozen controlled execution, but
  it is no longer a hard-coded filter for arbitrary user uploads.

## Verification

Focused checks:

```bash
node --check nmaRoadDemoV1.js
node --check assets/js/nma-road-upload-v1.js
PYTHONPATH=src:. python3 -m pytest -q \
  tests/test_road_browser_v1.py \
  tests/test_road_portrayal_v1.py
```

Browser QA used an actual local Shapefile ZIP with three contiguous `9420400` LineStrings,
per-feature vertex counts `4 / 3 / 4`, `ROADNUM=縣126`, and `ROADNAME=中山街`. The fixture was
generated only to exercise the upload and browser path; it is ignored and is not presented as an
official or publication baseline. QA confirmed the schema question, official pages, red connected
line, line-following name, final `stop` decision, hashes, and empty browser console.

A localhost-only `qaFixture` query parameter supports repeatable browser QA. It is ignored on
non-local hosts and is not exposed in the user interface.

# NMA BUILD browser integration v1

## Outcome

This slice extends the staged NMA application to a user's own BUILD Shapefile. It validates the
reviewed multidimensional BUILD schema and polygon geometry in the browser, asks rather than
guesses when a parent classification is observed, retrieves classification and portrayal evidence
through the read-only Knowledge Service, requires plan-bound human authorization, and renders a
MapLibre boundary, hatch, annotation, or class-marker preview.

Entry point: `nmaBuildDemoV1.html`

This is an engineering integration candidate. It is not the public GitHub Pages release and does
not activate an official or production building portrayal.

## BUILD classification boundary

This application supports the reviewed polygon classes that occur in the source BUILD profile:

| Code | Presented name | Annex 7 (109) | Document 01 portrayal | Preview |
|---|---|---|---|---|
| `9310100` | 永久性建物（建築區） | physical p.49 | p.8 | boundary, diagonal hatch, `{BUILD_NO}{BUILD_STR}` |
| `9310103` | 無牆建物 | no canonical Annex 7 row | p.8 | outline and `C` marker |
| `9310200` | 建築中建物 | physical p.50 | p.8 | dashed outline and `中` marker |
| `9310300` | 臨時性建物 | physical p.50 | p.8 | dashed outline and `T` marker |

`9310200` and `9310103` are therefore never presented as unnamed or unknown subclasses.
`9310103` has an exact Document 01 portrayal identity even though the 109 Annex 7 graph has no
corresponding row. The application preserves that document boundary instead of manufacturing an
Annex 7 citation.

`9310000` is treated as a parent classification. The browser asks the user to resolve all features
carrying it to `9310100`, `9310200`, or `9310300` for this session. If one answer is not valid for
the entire group, the source must be corrected or subdivided before the preview. Polygon uploads
carrying the line-oriented `9310101` or `9310102` stop as geometry/classification mismatches.

## Versioned schema boundary

The accepted source profile is the reviewed multidimensional BUILD V4 profile:

`BUILD_ID, TERRAINID, BUILD_STR, BUILD_NO, BUILD_H, GROUP_ID, MDATE`

The current canonical graph also contains a different Taiwan electronic-map BUILD profile with a
reduced `ID, MDATE, SOURCE` field set. NMA does not silently treat those versions as equivalent.
This adapter requires `TERRAINID` and the complete multidimensional source field set; a file that
matches only the reduced profile stops before planning because it cannot support the requested
classification-grounded portrayal.

The source identity is `zip-relative-filename::BUILD_ID`. This prevents cross-layer collisions
without pretending that an upstream identifier is globally unique.

## Data and geometry gate

The browser gate is fail-closed:

- maximum ZIP size: 16 MiB;
- exactly one `BUILD` or `*_BUILD` Shapefile family;
- `.shp`, `.shx`, `.dbf`, and `.prj` are mandatory;
- `.cpg` is optional;
- Polygon and MultiPolygon only;
- all seven reviewed fields must be present on every feature;
- non-empty `BUILD_ID` and unique filename-plus-ID identity;
- supported `TERRAINID` or an explicitly resolved parent code;
- WGS84 coordinates after `.prj` transformation;
- closed rings with at least four vertices;
- non-zero ring area;
- no browser-detected ring self-intersection;
- maximum 50,000 features and 1,000,000 vertices, plus ZIP expansion limits.

Browser validation is deliberately stricter than checking only a geometry type, but it is not a
replacement for the repository's GDAL/OGR production validation. Hole containment and complex
polygon topology require the future GDAL-backed upload service.

The browser calculates feature, vertex, ring, multipart, Z-feature, annotation, and class counts.
Only bounded summaries cross the API boundary. Source geometry, per-feature counts, Shapefile
bytes, and Z coordinates remain in the browser.

## Knowledge and Agent loop

The planner retrieves exact graph nodes and verified citations for each effective class. It uses
Document 02 Annex 7 occurrences when present and Document 01 portrayal identities for all four
classes. Names displayed to the user are reviewed presentation names, not page-wrap fragments from
machine extraction.

The active backend may be the identity-verified Neo4j projection or the canonical JSON snapshot.
The Agent cannot issue arbitrary Cypher and cannot mutate the KG.

The observable loop is:

```text
observe BUILD schema, polygon validity, class counts, rings, vertices, and Z
→ retrieve classification and portrayal evidence
→ propose a class-specific MapLibre preview plan
→ request human authorization for the local output profile
→ observe compiler result
→ decide verify-then-stop
→ verify hashes, evidence, layer roles, counts, and mutation boundaries
→ render browser-local BUILD layers
→ observe actual boundary and hatch render
→ decide stop
```

A MapLibre pattern, style, or render failure changes the next decision to `abstain-and-stop`.

## Portrayal and local output profile

The official evidence supports a surveyed building footprint, diagonal hatch semantics, 2 mm
hatch spacing for `9310100`, and the floor-then-structure annotation content. It does not directly
define a browser CSS conversion, numeric hatch angle, glyph placement algorithm, collision policy,
or production MapLibre asset.

The authorized browser preview therefore uses these explicit local values:

- black `1.25 px` outline;
- procedural diagonal hatch rising from lower-left to upper-right;
- `45°` and `12 px` tile spacing as local browser values;
- polygon-centroid text placement subject to MapLibre collision handling;
- `{BUILD_NO}{BUILD_STR}` for permanent-building annotation;
- `C`, `中`, and `T` class markers for the reviewed non-permanent portrayals.

The UI and plan both state that the official numeric angle is not claimed. Human authorization
binds these values only to the current preview plan.

## PolygonZ boundary

PolygonZ coordinates remain in the browser-local parsed collection. MapLibre consumes a
non-writing derived XY view for portrayal. NMA does not remove Z from the source, expose a write
handle, repair geometry, or export a derivative. Feature, ring, vertex, source-dimension, Z-feature,
archive, plan, authorization, adapter, and QA identities remain visible in provenance.

## Verification

Focused checks:

```bash
node --check nmaBuildDemoV1.js
node --check assets/js/nma-build-upload-v1.js
PYTHONPATH=src:. python3 -m pytest -q \
  tests/test_build_browser_v1.py \
  tests/test_build_portrayal_v1.py
```

Browser QA used an actual local PolygonZ Shapefile ZIP with four features, 20 vertices, four rings,
all four supported BUILD classes, and the complete reviewed field set. QA confirmed visible solid
and dashed boundaries, procedural hatch, `3RC`, `C`, `中`, and `T`, final `stop`, provenance hashes,
no source-Z mutation, and an empty browser console. The generated fixture is ignored and is not an
official or publication baseline.

A localhost-only `qaFixture` query parameter supports repeatable browser QA. It is ignored on
non-local hosts and is not exposed in the user interface.

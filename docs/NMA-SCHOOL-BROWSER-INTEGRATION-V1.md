# NMA School browser integration v1

## Outcome

This slice turns the School portrayal Agent loop into a staged mapping application for a user's
own Shapefile. It is not a fixed evidence replay and it does not substitute external open data.
The application accepts one user `MARK` Point layer, stops invalid data before planning, retrieves
the rules for the School classes actually present, requires a plan-bound human authorization, and
only then creates a browser-local MapLibre preview.

Entry point: `nmaSchoolDemoV1.html`

This branch is an engineering integration candidate. It is not yet the public GitHub Pages release
and must not be described as production activation.

## User flow

The application exposes one stage at a time:

1. **Data gate** — inspect the ZIP, Shapefile family, schema, geometry, CRS result, IDs, labels, and
   `TERRAINID` values.
2. **KG evidence** — show only the classes observed in the user's data, the selected portrayal
   family, Knowledge Service identity, and official document/page bindings.
3. **Human authorization** — bind approval to the exact plan hash and preview-only operation.
4. **Map preview** — compile the evidence-bound MapLibre layers, pass server-side QA, and then bind
   the user's GeoJSON to the map in the browser.
5. **Verification** — separate governed checks, the Agent's observation-driven decision trace, and
   content-addressed provenance.

The UI is an application workflow, not an RQ dashboard or a raw JSON research workbench. Research
claims remain in the test and audit material; the user sees the mapping task and its governance
boundary.

## Data gate

The archive gate is fail-closed:

- maximum ZIP size: 16 MiB;
- exactly one `MARK` or `*_MARK` Shapefile family;
- `.shp`, `.shx`, `.dbf`, and `.prj` are mandatory;
- `.cpg` is optional;
- Point geometry only for this School slice;
- exact reviewed fields `MARKID`, `TERRAINID`, and `MARKNAME1`;
- non-empty School names and IDs;
- unique `zip-relative-filename::MARKID` composite identity;
- only leaf codes `9920101`–`9920106`; `9920100` is the family root, not a filter value;
- valid WGS84 coordinates after browser parsing and `.prj` transformation;
- maximum 50,000 features, plus ZIP entry and uncompressed-size limits.

There is no 15-point restriction. A valid file can contain any mixture and count of the six School
leaf classes within the bounded browser limit.

`assets/js/nma-school-upload-v1.js` also rejects encrypted, multi-disk, path-unsafe, malformed, and
over-expanding archives before Shapefile parsing.

## Knowledge and Agent boundary

After the data gate, only the following observation crosses the browser/API boundary:

- user goal;
- reviewed source/schema bindings;
- geometry type;
- observed School class counts;
- composite identity rule;
- `raw_feature_bytes_transmitted: false`.

The Shapefile bytes and parsed GeoJSON remain in the browser tab. The server uses the existing
read-only Knowledge Service to retrieve classification and portrayal evidence. The active backend
can be the identity-verified Neo4j projection or the canonical JSON snapshot. The Agent cannot
submit arbitrary Cypher and cannot mutate the formal KG.

This slice is a bounded symbolic Agent: it does not require an LLM, but it does implement a real
observation/decision loop. A successful run records:

```text
observe source schema and class counts
→ retrieve read-only KG evidence
→ propose preview plan
→ request human authorization
→ observe compiler result
→ decide verify-then-stop
→ verify governed adapter result
→ render browser-local MapLibre layers
→ observe actual browser render
→ decide stop
```

If an SDF image load fails, the observation changes the next plan to the same reviewed SVG in a
non-SDF black preview, invalidates the previous authorization, and asks the human to authorize the
new plan. If MapLibre style validation fails and no evidence-preserving fallback remains, the Agent
abstains and stops.

## Portrayal behavior

The compiler creates one filtered MapLibre symbol layer for every School leaf code actually
observed:

- `9920101`, `9920102`, `9920103`, and `9920106`: reviewed School flag family plus `MARKNAME1`;
- `9920104` and `9920105`: `MARKNAME1` annotation only.

Flag icons allow overlap so a nearby label collision cannot erase a School point. Flag labels use
collision management and are optional; name-only classes allow text overlap because the name is
their only visible portrayal. Every compiled layer retains its rule, official section, and page
binding in `nma:evidence`.

The default background is a local blank canvas to avoid disclosing user coordinates through map
tile requests. `?basemap=nlsc` explicitly opts into the NLSC EMAP WMTS basemap.

## Current implementation boundary

- Shapefile parsing is browser-local through vendored, pinned `shpjs` 6.2.0.
- `.prj` conversion is therefore handled by `shpjs`/Proj4 in this slice, not the repository's GDAL
  backend. A production upload service should restore the reviewed GDAL/OGR CRS and geometry
  validation path.
- Session mappings are not written back to the KG.
- No LLM is required or bundled. A future LLM route may translate freer language into the same
  bounded schemas, but it may not bypass validation, evidence, authorization, or QA.
- No data is exported and no official or production portrayal rule is activated.
- ROAD and BUILD require their own geometry, classification, and portrayal integrations; this
  School slice must not be presented as cross-geometry completion.

## Verification

Focused checks:

```bash
node --check nmaSchoolDemoV1.js
node --check assets/js/nma-school-upload-v1.js
PYTHONPATH=src:. python3 -m pytest -q \
  tests/test_school_browser_v1.py \
  tests/test_school_portrayal_v1.py
```

Browser QA must use an actual Shapefile ZIP and confirm all five stages, the visible MapLibre
portrayal, final `stop` decision after `browser-render-verified`, PASS checks, and provenance. A
localhost-only `qaFixture` query parameter exists for automated browser QA because the in-app file
chooser cannot reliably populate file inputs; it is ignored on non-local hosts and is not exposed
in the UI.

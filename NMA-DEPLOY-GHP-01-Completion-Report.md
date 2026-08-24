# DEPLOY-GHP-01 — User Shapefile NMA Research Demo

## Terminal verdict

> **PASS — USER-SHAPEFILE NMA RESEARCH DEMO DEPLOYED TO GITHUB PAGES**

The earlier normalized accepted-replay page was not an adequate NMA demo: it rejected uploads and
rendered preloaded GeoJSON. That implementation has been withdrawn. The public site now requires a
user-selected Shapefile ZIP before it can produce any School, ROAD, or BUILD result.

This verdict is based on an external browser execution at the public URL with the controlled user
archive, not localhost-only testing.

## What the demo demonstrates

The pre-hero NMA architecture, SHP/OSM tools, CRS handling, PMTiles/MapLibre experience,
verification methods, Agent bench, and future research routes remain the research baseline. This
demo isolates one narrower claim:

> Can reviewed mapping knowledge control one authorized, executable, verifiable, and traceable
> operation on a user's Shapefile?

The visible lifecycle is:

`user request → user SHP intake → Agent interpretation replay → GraphRAG/mapping-rule replay → plan
→ human authorization → browser-local execution → QA/verification → provenance`

The frozen Agent and GraphRAG steps are deterministic reviewed-knowledge replays. The site does not
claim that FastAPI, an LLM Agent, Neo4j, or production GIS writeback is live.

## Publication source

The original `test` placeholder was published from `main` by GitHub Actions. Its workflow uploaded
the repository root and therefore served the root `index.html` containing `<p>test</p>`. There was
no active `docs/` or `gh-pages` source.

The current source is:

- branch: `main`;
- mechanism: GitHub Actions Pages deployment;
- workflow: `.github/workflows/static.yml`;
- uploaded directory: `public/gh-pages`;
- authority: `nma-v1.0-final` / `eb87bde775333811529efb6f651573ea21cf456b`;
- user-Shapefile artifact commit: `d0b1949bb749e1e7f2c58036b3dc8a7755c3c116`;
- successful deployment run: `32683993790`;
- deployment job: `97305582763`;
- public URL: `https://dongpo.github.io/topoMap/`.

All steps in run `32683993790` passed: checkout, focused tests, Pages setup, artifact upload, and
deployment. GitHub emitted a non-failing annotation that Node.js 20 actions are being forced to
Node.js 24; it did not affect the deployment.

## User-data and privacy contract

- Before a user chooses a ZIP, the result area says `USER SHP REQUIRED` and contains no map result
  geometry.
- The file input uses the browser File API. ZIP inventory, safety gates, SHA-256, Shapefile parsing,
  CRS conversion, filtering, verification, receipt construction, and MapLibre rendering occur in
  browser memory.
- The page has no upload endpoint and performs no open-data or OSM substitution.
- User SHP/DBF/SHX/PRJ/CPG bytes are not persisted by the page and are not included in the deployed
  artifact.
- No OpenAI, Neo4j, FastAPI, or production credentials are present.
- Every execution requires a proposal to pass the component, geometry, CRS, and identity gates and
  then requires an explicit browser-session authorization click.

The public artifact vendors pinned MapLibre 4.7.0, shpjs 6.2.0, fflate 0.8.3, Noto glyphs, and the
corresponding licenses. All asset paths are relative and safe under `/topoMap/`.

## Controlled user-Shapefile evidence

External acceptance used the controlled archive only through the public page's file chooser. The
archive was not committed or published.

- archive: `112年多維度SHP成果_0502.zip`;
- compressed size shown by the page: 12.2 MB;
- archive SHA-256:
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`;
- ZIP entries inventoried: 1,318;
- Shapefile component groups parsed: 128;
- source CRS reported from PRJ: `TWD97[2020]_TM121`;
- browser preview CRS: WGS84.

### School

- user layers: six user `*_MARK` Shapefiles;
- controlled filter: `TERRAINID=9920103`;
- output: 15 user-source points;
- identity: 15/15 `MARKID` present and unique;
- geometry mismatch: 0;
- frozen count contract: MATCH;
- authorization: explicit browser-session authorization;
- execution: MapLibre canvas created from the user features.

### ROAD

- user layer: `K14_ROAD` only (196 source features);
- controlled filter: `TERRAINID=9420400 AND ROADNAME=中山街`;
- output: 3 user-source line features;
- identity: 3/3 `ROADSEGID` present and unique;
- accepted ROADSEGID sequence: MATCH;
- vertex sequence: actual `4/3/4`, expected `4/3/4` — MATCH;
- portrayal: MapLibre line with line-following `中山街` label;
- authorization: explicit browser-session authorization.

### BUILD

- user layer: `J17_BUILD` only (2,839 source features);
- controlled filter: `TERRAINID=9310100`;
- output: 2,769 user-source polygon features;
- identity: 2,769/2,769 `BUILD_ID` present and unique;
- Z coordinate observed after browser parse: YES;
- frozen count contract: MATCH;
- portrayal: MapLibre boundary plus clipped 45-degree hatch;
- authorization: browser preview only;
- production activation: **HELD / DISABLED** before and after preview execution.

For every profile, the evidence ledger includes the archive hash, selected source layers, required
sidecar completeness, component SHA-256 values, retrieved mapping-rule identities, filter plan,
authorization state, feature/ID/geometry/CRS checks, and a proposal/receipt SHA-256.

## Verification

- focused static acceptance tests: 9 passed;
- JavaScript syntax: passed;
- Python lint: passed;
- diff integrity check: passed;
- local real-browser user-Shapefile QA: School, ROAD, BUILD passed;
- external public-URL user-Shapefile QA: School, ROAD, BUILD passed;
- external MapLibre canvases: created for all three authorized scenarios;
- external browser console: 0 errors/warnings;
- previous `test` placeholder: absent;
- previous preloaded `data/scenarios.json`: deleted and not deployed.

## Explicit limitations

- This is a static browser-local controlled execution, not a live FastAPI/Agent/Neo4j service.
- The frozen knowledge selection is replayed deterministically; the demo does not claim live
  GraphRAG retrieval.
- PMTiles generation is not performed in the browser. It remains a CLI/backend tool-chain step.
- Hausdorff distance is displayed as not run because no separate user reference geometry is
  supplied. The page does not fabricate that metric.
- No OSM comparison or SHP↔OSM conversion is run by this page; those remain existing capabilities,
  not evidence produced in this execution.
- Large or highly layered archives are bounded by explicit compressed-size, uncompressed-size, and
  entry-count safety limits and may take noticeable time to parse in browser memory.

## Changed files for the user-Shapefile correction

- `.github/workflows/static.yml`
- `NMA-DEPLOY-GHP-01-Completion-Report.md`
- `public/gh-pages/app.css`
- `public/gh-pages/app.js`
- `public/gh-pages/assets/fflate-0.8.3-LICENSE.txt`
- `public/gh-pages/assets/fflate-0.8.3.min.js`
- `public/gh-pages/assets/school-blue.svg` (deleted)
- `public/gh-pages/assets/shpjs-6.2.0-LICENSE.txt`
- `public/gh-pages/assets/shpjs-6.2.0.min.js`
- `public/gh-pages/data/scenarios.json` (deleted)
- `public/gh-pages/index.html`
- `public/gh-pages/release.json`
- `scripts/build_gh_pages_release_manifest.py`
- `tests/test_gh_pages_static_demo.py`

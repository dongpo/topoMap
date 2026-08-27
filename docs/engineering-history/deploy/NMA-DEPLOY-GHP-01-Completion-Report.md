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
- user-Shapefile artifact commit: `d94cf30a6d78ddc1231bd10fd2e4e60a0c353a82`;
- successful deployment run: `32685867037`;
- deployment job: `97310679232`;
- public URL: `https://dongpo.github.io/topoMap/`.

All steps in run `32685867037` passed: checkout, focused tests, Pages setup, artifact upload, and
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

School schema handling has two explicit paths:

- reviewed-rule path: case-insensitive/normalized `TERRAINID=9920103` filtering followed by the
  frozen contract checks;
- user-prefiltered path: when the selected point layer already contains exactly 15 features but has
  no reviewed code match, the Agent maps identity aliases such as `SCHOOL_ID`, labels the proposal
  `PROPOSABLE · PREFILTERED`, and requires authorization while stating that classification is
  user-declared and was not re-verified from `TERRAINID`.

The user-prefiltered path was externally tested with a 15-point School Shapefile containing
`SCHOOL_ID/SCHOOL_NAME` and no `TERRAINID`. It produced 15 unique IDs, a WGS84 MapLibre canvas, the
badge `EXECUTED · PREFILTERED`, and zero console errors. It did not claim a reviewed-code match.

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

- focused static acceptance tests: 10 passed;
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

## 2026-08-24 Knowledge Graph and Agenticity recovery

The previous Pages implementation was rejected because its JavaScript embedded a simplified
classification table and therefore bypassed the already-built canonical Knowledge Graph. It also
treated missing schema mappings as an unrecoverable blocked state.

The recovered application now:

- builds `data/nma-runtime-knowledge-v0.4.json` reproducibly from
  `nma-v1.0-final:data/knowledge/nma-canonical-graph-v0.4.json`;
- loads 861 selected canonical nodes and 1,040 edges in the browser, including Document 09
  MARK/ROAD/BUILD schemas, Annex 7 classifications, portrayal evidence, runtime observations, and
  activation gates;
- obtains School, ROAD, and BUILD classification labels from graph nodes, including
  `9310103 無牆建物` and `9310200 建築中建物`;
- requires exact `TERRAINID` and validates its values against KG codes before planning;
- recognizes graph-defined ROAD attribute-suffix composition such as `9420900a` and `9420900b`;
- asks a bounded clarification question when no approved schema mapping exists;
- records an affirmative answer only as a non-reusable, current-browser-run mapping;
- uses that observation to replan, which exercises the symbolic Agent loop without claiming that an
  LLM is necessary;
- uses ZIP-relative filename plus source ID as logical source identity; record index is renderer-only;
- removes the fixed 15-school, K14 three-road, and J17 permanent-building acceptance counts from
  general planning;
- renders the authorized result only; it does not export data or activate production.

Focused validation now contains 12 tests. Browser-local verification with private user data
confirmed:

- School: six MARK layers, clarification answered, 77 KG-classified points rendered, no console
  errors;
- ROAD: a complete K14 ROAD Shapefile, clarification answered, 192 KG-classified lines rendered,
  including graph-composed `9420900a/b`, no console errors;
- BUILD: a complete J17 BUILD Shapefile, clarification answered, 2,839 polygons rendered
  (`9310100` and `9310103`), production held, no console errors.

The full supplied archive correctly stops the ROAD run at intake because `K01_ROAD` lacks the
required `TERRAINID`. This is the requested fail-closed behavior, not a recoverable mapping question.
The ROAD and BUILD browser checks used private, temporary scenario-specific ZIP subsets; no private
fixture bytes are present in the repository or Pages artifact.

Changed files for this recovery:

- `NMA-DEPLOY-GHP-01-Completion-Report.md`
- `public/gh-pages/app.css`
- `public/gh-pages/app.js`
- `public/gh-pages/data/nma-runtime-knowledge-v0.4.json`
- `public/gh-pages/index.html`
- `public/gh-pages/release.json`
- `scripts/build_gh_pages_knowledge_projection.py`
- `tests/test_gh_pages_static_demo.py`

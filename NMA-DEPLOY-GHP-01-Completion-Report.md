# DEPLOY-GHP-01 — Static GitHub Pages NMA Research Demo

## Terminal verdict

> **PASS — STATIC NMA RESEARCH DEMO DEPLOYED TO GITHUB PAGES**

The `main` Pages workflow succeeded and the external public URL passed School, ROAD, BUILD,
MapLibre, evidence-panel, path-prefix, and console acceptance checks. This verdict is not based on
localhost-only testing.

## Publication-source finding

Before this deployment, `https://dongpo.github.io/topoMap/` displayed only `test`. The exact source
was:

- branch: `main` at `c608acb0c7a0b07459de371c1b2fea4c8a4f62ac`;
- mechanism: GitHub Actions Pages deployment;
- workflow: `.github/workflows/static.yml`;
- uploaded source: repository root (`path: '.'`);
- placeholder: root `index.html`, containing `<p>test</p>`.

An external browser independently rendered the same single `test` paragraph. There was no active
`docs/` or `gh-pages` publication path. The earlier DEPLOY-02 branch was also inspected: it built an
older v0.2 five-scene site, while `public/nma` depended on `/nma/api/v1` and was not standalone
GitHub Pages content.

## Final Pages source

- allowed source branch: `main`;
- mechanism: GitHub Actions Pages deployment;
- source directory: `public/gh-pages`;
- workflow: `.github/workflows/static.yml`;
- deployment authority: `nma-v1.0-final` / `eb87bde775333811529efb6f651573ea21cf456b`;
- demo authority: `nma-demo-v1.0-final` / `05af154a14e781f20b5cf2d3996eac8191875b0f`.
- deployed artifact commit: `79150559eb56df58b10d90a3e8a4f62261c2ace2`;
- successful workflow: run `32654202890`, run number `41`, job `97230328919`.

The dedicated directory replaces the previous whole-repository upload and excludes the root
PMTiles archive and all unrelated repository content.

## Static replay scope

This artifact is explicitly an **accepted execution replay**, not a live FastAPI or Agent service.
It contains:

- School: accepted 15-point result, blue portrayal, accepted authorization, GraphRAG/rule
  projection, QA, receipt, and provenance;
- ROAD: accepted `K14_ROAD` evidence, ordered 4/3/4 vertices, line-following `中山街`, accepted
  authorization, QA, receipt, and provenance;
- BUILD: frozen normalized polygon, clipped 45-degree hatch, receipt and verification, with
  production activation visibly held/disabled;
- eight inspectable stages from request through provenance;
- vendored MapLibre 4.7.0 and Noto glyph assets with `/topoMap/`-safe relative URLs.

School and ROAD are count/topology-faithful normalized public views. They do not publish private
source coordinates, names, attributes, raw fixture bytes, or substitute external open data. BUILD
uses the already frozen normalized-local, non-geographic artifact.

## Enforced boundaries

- no external data substitution, arbitrary upload, URL fetch, or writeback;
- no live FastAPI, Agent, LLM, or Neo4j process;
- no OpenAI, Neo4j, or production credentials;
- no `.zip`, `.shp`, `.dbf`, `.shx`, or `.pmtiles` deployment payload;
- no production activation or frozen semantic change.

## Verification before deployment

- focused static acceptance tests: **8 passed**;
- lint, formatting, compile, and diff checks: **passed**;
- local browser console after final reload: **0 errors/warnings**;
- School MapLibre: **15 individually visible public-safe points**;
- ROAD MapLibre: **ordered 4/3/4 trace and line-following 中山街**;
- BUILD MapLibre: **boundary and clipped hatch; activation held**;
- bounded selector: supported request resolves locally; production request fails closed.

## Deployment history

An initial attempt from `deploy/deploy-02-github-pages-public-demo` at
`d875210956e02bfb61e8a2e2e23b70529ca8862e` failed before any steps ran. GitHub check annotation
stated that the branch was not allowed by `github-pages` environment protection rules (run
`32654032385`). The solution preserves that protection and publishes the same tested artifact from
the allowed `main` branch.

Run `32654202890` completed successfully. Checkout, focused acceptance tests, Pages setup, bounded
artifact upload, and Pages deployment all concluded `success`.

## External acceptance

`https://dongpo.github.io/topoMap/` was reloaded after the successful workflow and verified in a
real browser:

- title: `NMA v1.0 · Accepted Execution Replay`;
- old `test` placeholder: absent;
- School: 15-point caption, accepted authorization identity, MapLibre canvas, and 8 lifecycle
  stages present;
- ROAD: accepted `K14_ROAD`, 4/3/4, line-following `中山街`, MapLibre canvas, evidence checks, and
  8 stages present;
- BUILD: accepted normalized boundary/hatch visible, production activation held/disabled,
  MapLibre canvas, and 8 stages present;
- browser console: 0 errors/warnings.

## Changed files

- `.gitignore`
- `.github/workflows/static.yml`
- `NMA-DEPLOY-GHP-01-Completion-Report.md`
- `public/gh-pages/.nojekyll`
- `public/gh-pages/app.css`
- `public/gh-pages/app.js`
- `public/gh-pages/index.html`
- `public/gh-pages/release.json`
- `public/gh-pages/data/scenarios.json`
- `public/gh-pages/assets/NotoSans-LICENSE.txt`
- `public/gh-pages/assets/NotoSansRegular-0-255.pbf`
- `public/gh-pages/assets/NotoSansRegular-19968-20223.pbf`
- `public/gh-pages/assets/NotoSansRegular-23552-23807.pbf`
- `public/gh-pages/assets/NotoSansRegular-34816-35071.pbf`
- `public/gh-pages/assets/maplibre-gl-4.7.0-LICENSE.txt`
- `public/gh-pages/assets/maplibre-gl-4.7.0.css`
- `public/gh-pages/assets/maplibre-gl-4.7.0.js`
- `public/gh-pages/assets/school-blue.svg`
- `tests/test_gh_pages_static_demo.py`

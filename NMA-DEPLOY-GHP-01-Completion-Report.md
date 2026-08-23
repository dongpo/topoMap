# DEPLOY-GHP-01 — Static GitHub Pages NMA Research Demo

## Terminal verdict

Deployment remains **PENDING** until the branch is pushed, the GitHub Pages workflow succeeds,
and `https://dongpo.github.io/topoMap/` passes an external browser acceptance check. A local-only
result is not sufficient for PASS.

## Publication-source finding

Before this change, the public URL displayed only `test`. The source was established without
guessing:

- repository default branch: `main` at `c608acb0c7a0b07459de371c1b2fea4c8a4f62ac`;
- publication mechanism: GitHub Actions Pages deployment;
- workflow: `.github/workflows/static.yml`;
- uploaded source: repository root (`path: '.'`);
- placeholder source: root `index.html`, containing `<p>test</p>`;
- external browser pre-deployment observation: the public URL rendered one paragraph, `test`.

There was no active `docs/` or `gh-pages` publication path. Existing remote DEPLOY-01/02 work was
also inspected. DEPLOY-02 still built the older v0.2 five-scene evidence-only site, while
`public/nma` required a `/nma/api/v1` backend and therefore was not independently runnable on
GitHub Pages.

## New Pages source

- publication mechanism: GitHub Actions Pages deployment;
- source branch: `deploy/deploy-02-github-pages-public-demo`;
- workflow: `.github/workflows/static.yml`;
- build command: `python3 scripts/build_gh_pages.py --output artifacts/tmp/gh-pages`;
- uploaded artifact: `artifacts/tmp/gh-pages`;
- deployment authority: `nma-v1.0-final` / `eb87bde775333811529efb6f651573ea21cf456b`;
- demo authority: `nma-demo-v1.0-final` / `05af154a14e781f20b5cf2d3996eac8191875b0f`.

The exact deployment commit and workflow run are reported after the external acceptance gate.

## Static replay scope

The public artifact is explicitly an **accepted execution replay**, not a live FastAPI or Agent
service. It includes:

- School: accepted 15-point result, blue School portrayal, accepted authorization, QA, receipt,
  provenance, and deterministic GraphRAG/rule projection;
- ROAD: accepted `K14_ROAD` evidence, ordered 4/3/4 vertices, `中山街` line-following portrayal,
  accepted authorization, QA, receipt, provenance, and deterministic GraphRAG/rule projection;
- BUILD: frozen normalized polygon, solid boundary, clipped 45-degree hatch, accepted demo
  authorization and receipt, with production activation visibly held/disabled;
- eight inspectable stages: request, Agent interpretation, GraphRAG/mapping rules, plan,
  authorization, execution replay, QA/verification, and provenance;
- vendored MapLibre 4.7.0 and Noto glyph assets, addressed with relative URLs for `/topoMap/`
  path-prefix safety.

School and ROAD use count/topology-faithful normalized public views. They do not publish the
controlled fixture's private source coordinates, names, attributes, or raw bytes. BUILD uses the
already frozen normalized-local, non-geographic demo artifact.

## Enforced boundaries

- no external open-data substitution;
- no arbitrary upload, path, or URL ingestion;
- no live execution or writeback;
- no OpenAI, Neo4j, or production credentials;
- no `.zip`, `.shp`, `.dbf`, `.shx`, or `.pmtiles` payload;
- no production activation;
- no frozen semantic or authorization change.

## Focused verification

- static contract tests: **8 passed**;
- Python formatting/lint/compile: **passed**;
- path-prefix and local-link checks: **passed**;
- private-byte, credential, live-API, and activation exclusions: **passed**;
- local browser console: **0 errors/warnings after final reload**;
- local School MapLibre: **PASS — 15 individually visible public-safe points**;
- local ROAD MapLibre: **PASS — ordered 4/3/4 trace and line-following 中山街**;
- local BUILD MapLibre: **PASS — boundary and clipped hatch; activation held**;
- bounded selector: **PASS — supported request resolves locally; production request fails closed**.

## Changed files

- `.github/workflows/static.yml`
- `NMA-DEPLOY-GHP-01-Completion-Report.md`
- `scripts/build_gh_pages.py`
- `site/index.html`
- `site/app.css`
- `site/app.js`
- `tests/test_gh_pages_static_demo.py`

Generated `artifacts/tmp/gh-pages` content is intentionally not committed; the workflow rebuilds
and tests it deterministically before upload.

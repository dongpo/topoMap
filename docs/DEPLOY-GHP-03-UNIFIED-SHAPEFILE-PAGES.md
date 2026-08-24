# DEPLOY-GHP-03 — unified user-Shapefile Pages application

## Publication-source audit

The repository root `index.html` on `main` contains the historical `<p>test</p>` placeholder, but it
is not the deployed Pages payload. GitHub Pages is configured with `build_type=workflow`; the active
workflow is `.github/workflows/static.yml` on `main`. It runs the focused static-demo tests and
uploads only `public/gh-pages` through `actions/upload-pages-artifact`.

There is no `gh-pages` publication branch and the deployment does not serve repository root or
`docs/` directly.

## UI architecture

`public/gh-pages/index.html` is now a task-selection entry point. It contains no file input, map, or
combined research workbench. It links to three separate, domain-locked application runs:

- `run.html?domain=school` — `MARK` / Point;
- `run.html?domain=road` — `ROAD` / LineString;
- `run.html?domain=build` — `BUILD` / Polygon.

`run.html` retains the existing browser-local static adapter and shows only the selected domain's
data intake, plan, authorization, map, and evidence record. Changing domain reloads a clean browser
run so observation, mapping, authorization, and geometry state cannot bleed between tasks.

## Frozen knowledge and execution boundary

- Semantic authority remains `nma-v1.0-final` at
  `eb87bde775333811529efb6f651573ea21cf456b`.
- The browser runtime loads the derived `nma-canonical-graph-v0.4` projection.
- Required Shapefile components are `.shp`, `.shx`, `.dbf`, and `.prj`; `.cpg` is optional.
- User ZIP, Shapefile, GeoJSON, and vertex data remain in the browser.
- The public artifact contains no fixture ZIP/SHP bytes, OpenAI or Neo4j credential, PMTiles file,
  arbitrary upload endpoint, external open-data substitution, or production activation.
- Missing mapping enters a bounded question. The answer is scoped to the current run and changes
  the next decision; it does not write back to the canonical KG.

## Pre-deployment acceptance

The focused Pages suite contains 14 tests covering the canonical projection, Document 09 fields,
School/ROAD/BUILD classification labels, strict intake, filename-plus-source-ID identity,
observation-driven mapping/replanning, human authorization, MapLibre Point/Line/Polygon capability,
path-prefix-safe links, exact artifact manifest, and exclusion of fixtures and credentials.

Actual browser-local static runs were completed before deployment:

| Domain | Local user archive result | Terminal browser result |
| --- | --- | --- |
| School | 12 classified Point features | clarification → replan → authorization → MapLibre rendered |
| ROAD | 3 classified LineString features | clarification → replan → authorization → MapLibre rendered |
| BUILD | 4 classified PolygonZ features | clarification → replan → authorization → MapLibre boundary/hatch rendered; production held |

Desktop and 390 px layouts were inspected. Browser warning/error collection was empty for the
landing and all three completed runs. Live URL and Actions run evidence must still be recorded only
after the `main` deployment completes.

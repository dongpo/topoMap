# NMA unified Shapefile application v1

## Purpose

This work package integrates the School, ROAD, and BUILD portrayal slices into one application
entry point without collapsing their geometry-specific workflows into a single page.

Entry point: `nmaApplicationV1.html`

The application begins with the user's data task:

| Task | Expected layer | Geometry | Result being verified |
| --- | --- | --- | --- |
| School | `MARK` / `*_MARK` | Point | class-aware school symbol and name portrayal |
| ROAD | `ROAD` / `*_ROAD` | LineString / MultiLineString | centreline and line-following name portrayal |
| BUILD | `BUILD` / `*_BUILD` | Polygon / MultiPolygon, including Z | boundary, hatch, annotation, and reviewed class marker portrayal |

The entry point is an application router, not a research dashboard. It does not expose RQ1–RQ10 as
navigation, embed three demonstrations in iframes, accept data itself, or imply that one generic
tool can safely process every geometry.

## Shared governed interaction

Every domain keeps the same five human-visible stages:

1. fail-closed user Shapefile inspection;
2. read-only Knowledge Service evidence retrieval and plan proposal;
3. plan-bound human authorization;
4. geometry-specific MapLibre portrayal;
5. browser observation, verification, and Agent decision.

The domain workflow remains responsible for its own schema, classification hierarchy, mapping
questions, portrayal compiler, and QA contract. Shared navigation does not weaken those gates.

## Agenticity claim boundary

The UI describes observable decisions rather than claiming that LLM use makes the system an Agent.
The final observation may lead to `replan`, `abstain`, `request human`, or `stop`. A successful
browser render therefore becomes an input to the decision loop. The current slices demonstrate
bounded observation-driven behavior; they do not establish open-ended autonomy.

## Runtime and data boundary

- `nmaApplicationV1.js` queries the path-prefix-safe `api/nma/runtime` endpoint.
- The shell requires the runtime capability contract to advertise School, ROAD, and BUILD.
- If the runtime is unavailable or mismatched, the landing page says that operation pages will
  stop rather than claiming readiness.
- Raw Shapefile, GeoJSON, and per-vertex geometry remain in the browser.
- The Agent receives only the governed observation defined by the selected domain.
- No application path exports a transformed dataset or activates a production portrayal profile.
- The Agent cannot write to the canonical Knowledge Graph.

## Publication boundary

This work package intentionally does not replace the repository's historical `index.html` or alter
the GitHub Pages source. The public landing-page replacement and deployment verification belong to
the subsequent merge/deployment package, after this integrated application candidate passes review.

## Focused verification

```bash
node --check nmaApplicationV1.js
python -m pytest -q tests/test_unified_shapefile_application_v1.py
python -m pytest -q \
  tests/test_school_browser_v1.py \
  tests/test_road_browser_v1.py \
  tests/test_build_browser_v1.py
```

Browser acceptance additionally checks the integrated task selection, transitions into all three
domain pages, return navigation, live runtime capability state, and the three actual user-Shapefile
portrayal paths.

## 2026-08-25 browser acceptance record

The application was exercised against the local NMA server through the actual file inputs. The
fixtures were synthetic local QA archives; no private source fixture was committed or transmitted.

| Path | Observed user-data result | Governance and map result |
| --- | --- | --- |
| School | 12 Point features from `J01_MARK`; archive remained browser-local | canonical read-only KG evidence, plan-bound authorization, 1 rendered class layer, QA PASS, Agent `stop` |
| ROAD | 3 LineString features, 11 vertices, per-feature `4 / 3 / 4` | explicit session question before `TERRAINID → ROADCLASS2`, 4 visible line hits, 2 line-following label hits, QA PASS, Agent `stop` |
| BUILD | 4 PolygonZ features, 20 vertices, 4 rings, 4 Z features | four reviewed BUILD classes, 6 visible boundary hits, 2 hatch hits, QA PASS, Agent `stop`; official and production activation false |

The integration landing advertised all three runtime capabilities, each domain page returned to
the landing, and browser console warning/error collection was empty for the landing and all three
completed workflows. Desktop and 390 px responsive layouts were visually inspected.

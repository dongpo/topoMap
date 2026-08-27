# BUILD-06A — Safe GitHub Pages Publication Completion Report

Completion date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-06A IS COMPLETE AS A BOUNDED, PUBLIC, DEMO-ONLY GITHUB PAGES RELEASE**

The exact BUILD-06 offline presentation and its two redacted BUILD-05 JSON inputs are now
available at:

`https://dongpo.github.io/topoMap/build-demo/`

The live release contains exactly the three approved BUILD-06A files under `build-demo/`. Their
downloaded bytes match the BUILD-06 freeze inputs. No private archive, raw geographic coordinate,
raw source attribute, source PDF, PMTiles file, credential, production adapter, or official
portrayal claim was added by BUILD-06A.

## 2. Predecessor and publication identities

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Required predecessor branch | `build/build-06-demo-verification-freeze` | PASS |
| Required predecessor commit | `ac8552066f85e07358751b1f15a6fbc085f7fc67` | PASS |
| BUILD-06 freeze SHA-256 | `bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857` | PASS |
| BUILD-06A preparation branch | `build/build-06a-safe-demo-publication` | PASS |
| BUILD-06A preparation commit | `4e562613c5a9f85e56f3e8284a002aa0870b872b` | PASS |
| Minimal Pages branch | `build/build-06a-pages-publication` | PASS |
| Public `main` commit | `88290fa55832edbbe190a68095b115cab93c4eb9` | PASS |
| Publication manifest SHA-256 | `83c22625ad99dbc0cb26af614d39cf6fd12e6e77b1c863b501656e46f6d105a9` | PASS |

## 3. Minimal integration decision

The BUILD-06A preparation branch was 81 commits and approximately 500 changed files ahead of
`main`. Merging that branch wholesale would have expanded the publication change far beyond the
approved DEMO. It was therefore not merged into `main`.

Instead, a clean branch was created from the exact current `origin/main` commit
`1f3c886b3dcc61a5ee74c46e7cd7a9be5c668a3d`. Only the three approved public payload files were
added. The resulting one-commit fast-forward to `main` preserved the existing site and triggered
the repository's already-established `.github/workflows/static.yml` Pages workflow.

The dedicated bounded builder and proposed future workflow remain on the BUILD-06A preparation
branch for review. They were not needed on `main` for this minimal release and were not mixed into
the public integration commit.

## 4. Exact live payload

| Public path under `build-demo/` | Bytes | Live SHA-256 | Result |
|---|---:|---|---|
| `index.html` | 14981 | `de5f6d567810e42af915bdff167fb21e202967b98817e2ef8d2d494d0b47be2d` | PASS |
| `data/specifications/nma-build-05-golden-execution-package-v1.0.json` | 6767 | `508e3378a698f869255485c5008fdb80ed670ce174a3b72092aab5160df7431c` | PASS |
| `data/specifications/nma-build-05-authorization-consumption-v1.0.json` | 737 | `715a5445827b77308ec32a67efe74ac8e5ed29b9037ee543285270a4da1c9d47` | PASS |

All three URLs returned successfully. Each live file was downloaded after deployment and hashed
locally; every result equals its frozen source file hash.

## 5. Live presentation boundary

The deployed page continues to enforce and display the BUILD-06 decisions:

- `DEMO ONLY · 非正式圖式` is visible as the authority boundary;
- hatch angle begins at the approved 45-degree default;
- the DEMO control permits adjustment from 0 through 179 degrees in one-degree steps;
- only same-directory, same-origin JSON inputs are fetched;
- the normalized coordinate space remains `normalized-local-demo-not-geographic`;
- no external script, style, font, map, API, or production runtime is used;
- no user adjustment changes the frozen package, consumption ledger, or approved decision.

Publication does not resolve the five portrayal semantics that remain DEMO evaluation topics:
hatch angle preference, annotation placement, authoritative schema binding, production line/color
profile, and PolygonZ-to-2D production policy. None was promoted to official or production status.

## 6. Deployment result

GitHub Actions workflow run:

`https://github.com/dongpo/topoMap/actions/runs/32369081401`

The initial job (`96425213117`) stalled during artifact upload. It was canceled before the Pages
deployment step; no partial public release occurred. The same workflow run was then rerun without
changing the commit or payload. The replacement job (`96429343661`) completed successfully in 12
seconds, including artifact upload and GitHub Pages deployment.

The only workflow annotation was GitHub's Node.js 20 deprecation notice for existing third-party
actions. It did not affect this release. Updating those existing actions is a separate maintenance
task and was not added to BUILD-06A.

## 7. Verification and regression results

- BUILD-06A focused acceptance: **29 passed**;
- BUILD-06A plus Core residual-freeze and existing Pages acceptance: **44 passed**;
- BUILD-00A through BUILD-06A chain acceptance: **302 passed**;
- complete repository regression: **904 collected; 901 passed; 3 failed**;
- live Pages payload: **3 of 3 files reachable and byte-exact**;
- GitHub Pages deployment: **successful**.

The three complete-suite failures are the exact known pre-existing Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD-06A, BUILD chain, Core, ROAD, source-integrity, privacy, identity-provider, or production
runtime regression was introduced.

## 8. Exact changed files

BUILD-06A preparation branch:

1. `.github/workflows/build06a-pages.yml` — isolated future bounded Pages workflow.
2. `BUILD-06A-Completion-Report.md` — this completion and live-verification record.
3. `build_contracts/demo_publication.py` — exact three-file publication builder and validator.
4. `data/specifications/nma-build-06a-golden-safe-publication-v1.0.json` — deterministic preflight publication manifest.
5. `schemas/build-demo-safe-publication-v1.0.schema.json` — closed publication schema.
6. `tests/test_build_demo_safe_publication_build06a.py` — publication, disclosure, workflow, and drift tests.

Minimal public `main` commit:

1. `build-demo/index.html`
2. `build-demo/data/specifications/nma-build-05-golden-execution-package-v1.0.json`
3. `build-demo/data/specifications/nma-build-05-authorization-consumption-v1.0.json`

Existing `src/nma`, production runtime wiring, official portrayal artifacts, private archives, and
the existing `main` Pages workflow changed: **no**.

## 9. Readiness recommendation

**BUILD-06A is complete. The published DEMO is ready for user evaluation.**

The next work should be a human DEMO evaluation record, not automatic production adoption. User
feedback may select or revise the still-ambiguous portrayal semantics, but any official schema
binding, production runtime wiring, or official portrayal declaration requires a new explicit
human gate and a separately authorized phase.

# BUILD-07 — DEMO User Evaluation & Semantic Decision Gate Report

Prepared on: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**READY FOR HUMAN EVALUATION — BUILD-07 IS PUBLISHED, BUT NO USER DECISION HAS BEEN RECORDED**

BUILD-07 provides an offline, non-identifying evaluation page for the five DEMO-only building
semantics approved in BUILD-03A and presented by BUILD-06/06A. A reviewer must explicitly accept
the current DEMO or request a DEMO revision for every item. The exported JSON is a local review
record only; it cannot authorize production, official portrayal, source access, runtime wiring, or
source mutation.

Live evaluation page:

`https://dongpo.github.io/topoMap/build-demo/`

BUILD-07 is not a completed semantic decision until a human reviewer uses the page and returns the
exported record for validation and project recording.

## 2. Exact predecessor boundary

| Item | Value | Result |
|---|---|---|
| BUILD-06A completion branch | `build/build-06a-safe-demo-publication` | PASS |
| BUILD-06A completion commit | `540153127d26db0197ab0891fb9c07c7fe8f012e` | PASS |
| Public `main` commit | `88290fa55832edbbe190a68095b115cab93c4eb9` | PASS |
| BUILD-06A publication SHA-256 | `83c22625ad99dbc0cb26af614d39cf6fd12e6e77b1c863b501656e46f6d105a9` | PASS |
| BUILD-06 freeze SHA-256 | `bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857` | PASS |
| BUILD-03A resolution SHA-256 | `a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01` | PASS |
| BUILD-07 branch | `build/build-07-demo-user-evaluation` | PASS |

## 3. Five evaluation decisions

| Gate | Current DEMO choice | Reviewer action |
|---|---|---|
| Hatch angle | Default 45 degrees; adjustable from 0 through 179 degrees | Accept 45 degrees or request another DEMO default with a note |
| Annotation placement | Interior pole of inaccessibility; suppress on no fit or higher-priority collision; never move outside | Accept or request revision with a note |
| J13 schema binding | `BUILD_NO` plus `BUILD_STR` only; no global `ID`/`SOURCE` equivalence | Accept or request revision with a note |
| Line and color profile | `#111111`, solid 1 CSS px, opacity 1 in the DEMO web profile | Accept or request revision with a note |
| PolygonZ policy | Preserve source PolygonZ; use XY only in the derived DEMO; never write back or remove Z | Accept or request revision with a note |

Only the hatch angle remains a direct visual control, matching the exact BUILD-03A authorization.
The other four items are reviewed textually; the page cannot change their rendering or data policy.

## 4. Evaluation outcomes

The evaluator must decide all five gates. The only allowed overall outcomes are:

- `accepted-demo-only` — all five current DEMO choices are accepted, including the frozen 45-degree default;
- `revision-requested-demo-only` — one or more choices require a documented DEMO revision.

There is no `official`, `production`, `approved-for-runtime`, or source-changing outcome. A revision
request must include a note. Accepting the current angle while the slider is not at 45 degrees is
rejected; the reviewer must either reset to 45 degrees or request a revision and record the
preferred whole-degree value.

## 5. Privacy and authority boundary

The page:

- verifies the exact BUILD-05 package, consumed-once ledger, and BUILD-07 evaluation template
  before enabling interaction;
- fetches only same-origin frozen JSON;
- uses only the normalized non-geographic polygon already published by BUILD-06A;
- records no reviewer name or identifier;
- does not use cookies, local storage, session storage, a server submission, analytics, or an
  external network dependency;
- downloads the evaluation JSON locally with `identity_recorded: false`;
- marks the export as non-authorizing and keeps every production/source boundary false.

## 6. Artifact identities

| Artifact | SHA-256 |
|---|---|
| BUILD-07 evaluation template identity | `0fea2e7fe6b8ec9dd10816ba5679b04773ecd3f0761ca7b58e339f7df91139e6` |
| Evaluation template file | `9e2b183260c5ac689831b1f5945defad28f27f49447f1a0d3f2b5b0425189364` |
| BUILD-07 evaluation page | `260c2da8c0916eb66b0745d2fa41206887fbdab6e716c82ca2a1901a2b27047a` |

Every completed export receives a canonical Core SHA-256 identity over its exact decisions,
evaluation date, summary, and immutable authority boundary.

## 7. Browser acceptance

The page was served from a sanitized temporary directory containing only the evaluation HTML and
three frozen JSON inputs. The repository root and private files were not exposed. The temporary
server and directory were removed after acceptance.

Observed behavior:

- frozen package, consumed-once ledger, and evaluation template verification: passed;
- initial angle: 45 degrees;
- angle change to 120 degrees: output `120°`, pattern `rotate(120)`;
- five accepted choices: progress `5 / 5`, export enabled;
- accept-current-DEMO with a non-45-degree angle: blocked with explicit correction;
- requested revision without a note: blocked;
- accepted 45-degree evaluation record: `accepted-demo-only`;
- documented 60-degree angle revision: `revision-requested-demo-only`;
- 390-pixel responsive layout: passed, no horizontal overflow;
- browser warnings and errors: 0.

## 8. Automated acceptance

- BUILD-07 focused contract/schema/HTML acceptance: **45 passed**;
- BUILD-00A through BUILD-07 chain acceptance: **347 passed**;
- frozen Core residual identity and change-scope checks: **12 passed**;
- complete repository regression: **949 collected; 946 passed; 3 failed**.

The three executed failures are the exact known pre-existing Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD-07, BUILD chain, Core identity-provider, source-integrity, privacy, ROAD, or production
runtime regression was found.

## 9. Exact BUILD-07 changed files

1. `BUILD-07-Evaluation-Gate-Report.md` — readiness, evaluation, browser acceptance, and hold record.
2. `buildDemoV07.html` — offline five-gate user evaluation and local JSON export page.
3. `build_contracts/demo_evaluation.py` — deterministic template, completed-record construction, validation, and authority boundary.
4. `data/specifications/nma-build-07-golden-evaluation-template-v1.0.json` — canonical five-gate evaluation template.
5. `schemas/build-demo-user-evaluation-v1.0.schema.json` — closed template and completed-record schema.
6. `tests/test_build_demo_user_evaluation_build07.py` — identity, gate, revision, privacy, UI, and anti-promotion tests.

Existing BUILD-06/06A freezes, `src/nma`, production runtime, official portrayal evidence, private
archives, and the two existing published BUILD-05 JSON files changed: **no**.

## 10. Publication result

Minimal public `main` commit:

`c608acb0c7a0b07459de371c1b2fea4c8a4f62ac`

GitHub Pages workflow run:

`https://github.com/dongpo/topoMap/actions/runs/32432613474`

The deployment job `96627238115` completed successfully in 16 seconds. The live public directory
contains exactly four approved files:

| Public file | Live SHA-256 |
|---|---|
| `build-demo/index.html` | `260c2da8c0916eb66b0745d2fa41206887fbdab6e716c82ca2a1901a2b27047a` |
| `build-demo/data/specifications/nma-build-05-golden-execution-package-v1.0.json` | `508e3378a698f869255485c5008fdb80ed670ce174a3b72092aab5160df7431c` |
| `build-demo/data/specifications/nma-build-05-authorization-consumption-v1.0.json` | `715a5445827b77308ec32a67efe74ac8e5ed29b9037ee543285270a4da1c9d47` |
| `build-demo/data/specifications/nma-build-07-golden-evaluation-template-v1.0.json` | `9e2b183260c5ac689831b1f5945defad28f27f49447f1a0d3f2b5b0425189364` |

The only workflow annotation is the existing GitHub Node.js 20 deprecation notice for third-party
actions. It did not affect this deployment and remains a separate repository-maintenance item.

## 11. Next human gate

The project owner should open the live page, decide all five items, download the evaluation JSON,
and return that file for validation and project recording. The next stage can then record either
acceptance or a bounded DEMO revision request.

Official portrayal and production entry remain **HOLD** under both possible evaluation outcomes.

# NMA DEMO-02 — End-to-End Demo Acceptance Report

**Branch:** `demo/demo-02-end-to-end-demo-acceptance`

**Mandatory predecessor:** `2d382a46585faa89311ea6a5502923464ace7758`

**Machine record:** `data/specifications/nma-demo-02-end-to-end-acceptance-record-v1.0.json`

## 1. Terminal verdict

> **FAIL — NMA END-TO-END DEMO NOT ACCEPTED**

The successful terminal verdict `PASS — NMA END-TO-END DEMO ACCEPTED` is not awarded.

The unified runtime is real, user-reachable, deterministic, fail-closed, and provenance-preserving
for the public ROAD and BUILD replays. BUILD provides a verified browser-rendered polygon and hatch.
It does not, however, satisfy the mandatory three-domain end-to-end acceptance:

1. School's public unified path is capability-only. It has no canonical plan identity, consumed
   authorization, execution, observation, verification, receipt, provenance, or map result.
2. ROAD's public replay validates a real frozen plan/receipt/bundle lineage, but the public checkout
   intentionally omits its geometry; the browser therefore renders no ROAD feature.
3. The browser/API public path cannot perform a new valid School or ROAD execution without protected
   source data, and School also lacks a public HERO-03 authorization issuer.
4. The current unified result envelope does not explicitly distinguish domain execution artifact
   mutation from protected source mutation.

Closing those findings requires more than DEMO-02 acceptance evidence. The recommendation is:

> **DEMO-01A — Unified Runtime Integration Closure**

No authorization, frozen-domain, GEN, portrayal, or activation assertion was weakened to obtain a
more favorable result.

## 2. Predecessor and repository gate

The gate passed before the branch was created:

| Check | Result |
|---|---|
| Fetch/push origin | `https://github.com/dongpo/topoMap.git` |
| Local DEMO-01 | exact `2d382a46585faa89311ea6a5502923464ace7758` |
| Local upstream | exact `2d382a46585faa89311ea6a5502923464ace7758` |
| Canonical remote ref after fetch | exact `2d382a46585faa89311ea6a5502923464ace7758` |
| Starting worktree | clean |
| DEMO-02 local/remote branch before creation | absent |

The DEMO-02 branch was created directly from that exact predecessor.

## 3. Frozen architecture verification

| Freeze | Required identity | Result |
|---|---|---|
| GEN-FINAL | `380cc6ea2a4498ce83690521c933accfd918818e`; `nma-generalization-v1.0-final^{}` | exact |
| BUILD-FINAL | `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7`; `nma-build-v1.0-final^{}` | exact |
| CORE-FINAL | `5eb138ae7686502431587743ebce9ddf92c5a799` | exact ancestor |
| ROAD-FINAL | `325c70d5335f57c43a8af85822db25032aa225c3` | exact ancestor |
| School Hero | `56f99eb9ae63272a68accac3041fb10eacefb986` | exact ancestor |

Frozen history, tags, manifests, contracts, domain implementations, and portrayals changed: **0**.

## 4. Actual DEMO-01 runtime inspected

Acceptance was based on implementation evidence, not only the DEMO-01 report.

| Concern | Direct implementation evidence |
|---|---|
| Server entry point | `scripts/run_nma_agent_server.py::main` |
| Unified API route | `GET/POST /api/nma/runtime` in `NMARequestHandler` |
| Browser surface | `nmaAgentDemoV1.html?basemap=local` |
| Dispatcher | `src/nma/unified_runtime.py::UnifiedNMARuntime.dispatch` |
| School path | `SchoolRuntimeAdapter` → real `SchoolHeroExecutionEngine.execute_by_id` / `SchoolHeroVerifier.verify` |
| ROAD path | `RoadRuntimeAdapter` → real `RoadExecutionEngine.execute_by_id` / `RoadExecutionVerifier.verify` |
| BUILD path | `BuildRuntimeAdapter` → `load_frozen_contract` → `load_authoritative_package` → `implement_controlled_building` → `verify_implementation_result` |
| Result envelope | `nma.unified-runtime-result/1.0` |
| Authorization | stored ID + idempotency for School/ROAD; exact BUILD-09F policy identity and scope for BUILD |
| Visualization | domain-owned MapLibre bundle/data or BUILD frozen derived polygon |
| Safe default | preview/replay do not execute; private archive startup access is opt-in; BUILD auto-activation is false |

The server constructs exactly one `UnifiedNMARuntime` with the three real adapters. No production
demo executor, fake authorization object, or generic semantic executor was found.

## 5. Canonical launch and browser verification

Command:

```text
PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 18083
```

- Host/port: `127.0.0.1:18083`
- Demo: `http://127.0.0.1:18083/nmaAgentDemoV1.html?basemap=local`
- API: `http://127.0.0.1:18083/api/nma/runtime`
- Observed mode: deterministic fallback
- Protected archive at startup: disabled

Real in-app browser observations:

- page loaded with the canonical title and all domain/operation/request controls;
- capability request returned `school / road / build` and BUILD auto-activation false;
- MapLibre initialized with canvas and controls;
- fatal JavaScript errors: 0;
- School request submitted and selected School, but rendered no geometry;
- ROAD request submitted and selected ROAD, but rendered no geometry by explicit public policy;
- BUILD request submitted and selected BUILD; one polygon with boundary and diagonal hatch was
  visibly rendered from the response's current in-page GeoJSON;
- BUILD receipt, verification, provenance, activation hold, and no-mutation state were visible;
- an unknown School target displayed an understandable `unsupported_capability` error.

The browser screenshot was used for direct visual acceptance of the BUILD polygon/hatch and was not
committed as decorative evidence.

## 6. Canonical scenario traces

### DEMO02-SCHOOL-001 — FAIL

Request: `Show the School Hero capability for feature 9920103.`

| Stage | Evidence |
|---|---|
| Routing | selected `school`; deterministic request ID present |
| Intent identity | `PASS_NOT_APPLICABLE`; no canonical identity defined |
| Plan | status `authorization-required-before-canonical-plan`; identity absent |
| Authorization | required; not presented; identity absent |
| Execution | `not-requested`; real School engine named as boundary |
| Observation | absent |
| Verification | absent |
| Receipt/provenance | absent |
| Visualization | unavailable; no map feature |
| Mutation | all reported false |
| User result | capability and protected authorization requirement only |

This is not the old portrayal/evidence query, but it is also not canonical School execution. It does
not meet Scenario A.

### DEMO02-ROAD-001 — PARTIAL

Request: `Replay County Highway 126 ROAD and verify its receipt.`

| Stage | Evidence |
|---|---|
| Routing | selected `road` through the unified browser/API boundary |
| Plan | `road-plan-cd434d50bd5b49a012bd1e10`; frozen hash revalidated |
| Authorization | `road-03-authorization-f68220ecef989e589dd6e28c`; frozen consumed evidence |
| Execution | `road-exec-33766f336d9cc18eb2ac159e`; explicitly frozen replay, not new execution |
| Observation | absent from unified envelope |
| Verification | plan/bundle/receipt/linkage checks all true |
| Receipt | `road-receipt-road-exec-33766f336d9cc18eb2ac159e`; SHA-256 present |
| Provenance | six frozen identity links preserved |
| Visualization | MapLibre bundle identity present; status `artifact-reference-only` |
| Map | no source/layer rendered because public geometry is not distributed |
| Mutation | all reported false |

ROAD is reachable through the unified runtime and its real frozen lineage is auditable. It does not
meet Scenario B's visible geometry/map result.

### DEMO02-BUILD-001 — PASS

Request: `Replay the frozen BUILD result and verify its receipt.`

| Stage | Evidence |
|---|---|
| Routing | selected `build` through the unified browser/API boundary |
| Plan | `b8b5ecd5…b52b0b71`; frozen plan revalidated |
| Authorization | `build-04-demo-auth-a5a8f11b94784a60`; frozen consumed evidence |
| Execution | `build-05-demo-exec-b8b5ecd54954b190eb8cda39`; frozen replay, not new execution |
| Observation | `9131df53…d3400d84`; `rendered-derived-demo` |
| Verification | `10c22339…c98c97`; passed frozen package validation |
| Receipt | `build-05-receipt-b8b5ecd54954b190eb8cda39`; SHA-256 present |
| Provenance | content-addressed package and source commitments present |
| Visualization | feature `build-feature:sha256:14ea3d…241801f`; `Polygon`; MapLibre profile |
| Map | polygon, solid boundary, and diagonal hatch visibly rendered |
| Activation | `held-not-requested`; automatic production activation false |
| Mutation | source and activation mutation false |

The UI labels this accurately as validated frozen replay rather than a new BUILD-10 execution.

## 7. Acceptance matrix

| Criterion | School | ROAD | BUILD | Overall |
|---|---|---|---|---|
| User request | PASS | PASS | PASS | PASS |
| Routing | PASS | PASS | PASS | PASS |
| Planning | PARTIAL | PASS | PASS | PARTIAL |
| Authorization | PARTIAL | PARTIAL | PARTIAL | PARTIAL |
| Canonical execution | FAIL | PARTIAL | PARTIAL | FAIL |
| Observation | FAIL | FAIL | PASS | FAIL |
| Verification | FAIL | PASS | PASS | FAIL |
| Receipt/provenance | FAIL | PASS | PASS | FAIL |
| User-visible result | PARTIAL | PASS | PASS | PARTIAL |
| Map/visualization | FAIL | FAIL | PASS | FAIL |
| Fail-closed safety | PASS | PASS | PASS | PASS |
| Public reproducibility | PARTIAL | PARTIAL | PASS | PARTIAL |

No material PARTIAL or FAIL is aggregated into PASS.

## 8. Routing and LLM/fallback acceptance

Passed deterministic tests:

- explicit School, ROAD, BUILD;
- natural-language School, ROAD, BUILD;
- ambiguous cross-domain request;
- explicit unsupported domain;
- unknown explicit feature code after the bounded acceptance fix.

The unified endpoint does not call OpenAI. `UNIFIED_RUNTIME.dispatch(payload)` receives neither API
key nor model. The optional credential changes legacy agent mode only; the unified path remains the
same deterministic selector and canonical domain execution/replay boundary. The observed server
ran in deterministic fallback mode, proving the public demo does not require paid credentials.

## 9. Authorization and negative acceptance

| ID | Scenario | Result | Failure point / evidence | Mutation |
|---|---|---|---|---|
| N1 | Unsupported Domain | PASS | `unsupported_domain`, HTTP 400 | false |
| N2 | Ambiguous Domain | PASS | `ambiguous_domain`, HTTP 400 | false |
| N3 | Invalid Request | PASS | `invalid_request`, HTTP 400 | false |
| N4 | Missing Required Authorization | PASS | `authorization_failure`, HTTP 403 | false |
| N5 | Invalid Authorization | PASS | BUILD-09F mismatch, HTTP 403 | false |
| N6 | Malformed Lifecycle Input | PASS | invalid BUILD verification identity, HTTP 400 | false |
| N7 | Capability Misrepresentation | PASS | unsupported activation operation rejected | false |
| N8 | BUILD Activation Safety | PASS | replay succeeds; activation held/false | false |
| N9 | Missing Required Dependency | PARTIAL | real adapter fails `missing_dependency`; live checkout not mutated | false |
| N10 | Unknown Feature Target | PASS | `unsupported_capability`, HTTP 400 | false |

Missing and invalid authorization fail before the School/ROAD execution engines or BUILD source
loader are reached. The demo origin has no bypass. A valid new source execution was not used as
acceptance evidence because public reproduction cannot supply protected source data and School has
no public authorization issuer. Frozen replay authorization identities remain linked downstream.

## 10. Bounded DEMO-02 acceptance fix

Before correction, this live request returned HTTP 200 and substituted the School `9920103`
capability:

```json
{"domain":"school","request":"Show School feature 9999999","operation":"preview"}
```

The defect was limited to DEMO-01-owned routing. The correction adds a fail-closed check for an
explicit seven-digit target against the selected frozen domain's feature code. The request now
returns HTTP 400, `unsupported_capability`, stage `routing`, and `mutation_performed=false` in API
and browser flows.

The fix does not alter GEN contracts, frozen domain semantics, authorization, execution, portrayal,
or activation. A focused regression test covers it.

## 11. Mutation and activation acceptance

For all exercised public success/replay and negative flows:

- source writeback: false;
- source repair: false;
- geometry mutation: false;
- portrayal mutation outside the domain: false;
- authorization bypass: false;
- production activation: false;
- routing and validation mutation: false.

BUILD reports `held-not-requested`, and both the capability endpoint and result envelope report
automatic activation false. The BUILD receipt's frozen boundaries also state production activation
false.

Limitation: the unified `mutation` object has no explicit domain-execution-artifact field. School and
ROAD engines persist plans/bundles/receipts on valid execute, but the normalized envelope's fixed
integration mutation object is all false. Because valid protected executions were not run, that
state remains unresolved rather than inferred.

## 12. Provenance and result-envelope acceptance

ROAD answers which request selected which plan, authorization, execution, receipt, and frozen
identity chain. BUILD additionally links observation, verification, receipt, provenance, source
commitments, feature identity, and visualization. Normalization preserves those domain identities.

School preview correctly uses null/absent optional identities instead of inventing evidence, but it
cannot answer the full lineage question. ROAD has no observation object in its replay envelope. The
envelope accurately labels replay versus execution and BUILD activation hold; it is partial overall.

## 13. Cross-domain consistency and no-stub audit

- one server route: `/api/nma/runtime`;
- one dispatcher and one generic Core identity architecture;
- three domain adapters calling domain-owned code;
- no generic planning, portrayal, execution, or verification semantics;
- production-reachable demo stubs: **0**;
- test-only tripwires/spies are isolated in tests and were not used as successful execution evidence;
- frozen replay identities come from validated tracked artifacts, not generated success placeholders.

The production path contains real `execute_by_id` calls for School/ROAD and the real controlled BUILD
implementation function. Static searches found no fake/stub/mock executor, hard-coded
`authorized=true`, API credential, or private key in DEMO-02 scope.

## 14. DEMO-A1 through DEMO-A12 re-evaluation

| Criterion | Classification | Reason |
|---|---|---|
| DEMO-A1 Single Entry Point | PASS | Browser and all domains use `/api/nma/runtime`. |
| DEMO-A2 User Intent | PARTIAL | Deterministic supported terms work; no canonical intent identity exists. |
| DEMO-A3 Domain Routing | PASS | Explicit/natural/ambiguous/unsupported paths are deterministic. |
| DEMO-A4 Real Planning | PARTIAL | ROAD/BUILD replay real plans; School preview has no plan identity. |
| DEMO-A5 Authorization | PARTIAL | Fail-closed and frozen linkage pass; no public valid new execution. |
| DEMO-A6 Real Execution | FAIL | No three-domain current canonical execution from the public UI. |
| DEMO-A7 Observable Result | PARTIAL | BUILD passes; ROAD lineage-only; School capability-only. |
| DEMO-A8 Map Result | FAIL | School and ROAD render no feature. |
| DEMO-A9 Verification | PARTIAL | ROAD/BUILD pass; School absent. |
| DEMO-A10 Provenance | PARTIAL | ROAD/BUILD pass; School absent. |
| DEMO-A11 Fail-Closed | PASS | Negative routing/auth/dependency/target flows fail without mutation. |
| DEMO-A12 Reproducibility | PARTIAL | Public replay is reproducible but full three-domain E2E is not. |

## 15. Focused and frozen regression results

| Suite | Result |
|---|---:|
| DEMO-02 focused | 20 passed |
| DEMO-01 focused | 15 passed |
| Combined focused (standalone runs) | 35 passed |
| Core/School | 46 passed |
| ROAD-01/02/03 | 104 passed |
| BUILD contract/policy | 57 passed, 2 documented stage-scope deselections |
| Public BUILD-FINAL | 8 passed, 2 private/historical-scope deselections |
| Exact detached GEN-00 | 11 passed |
| Exact detached GEN-01 public | 14 passed, private-archive test deselected |
| Exact detached GEN-02 public | 15 passed, private-archive test deselected |
| Exact detached GEN-FINAL | 10 passed |

The full GEN-01/GEN-02 count was intentionally not obtained by linking the private archive into the
temporary worktrees. The substantive public checks match the established DEMO-01 treatment.
The DEMO-01 live-loopback case skips inside the restricted test sandbox and passes when the same
focused suite is run with loopback binding enabled; the recorded standalone result is 15 passed.

## 16. Static and security gates

Candidate gates include Ruff lint, Ruff format check, JSON parse and schema checks, deterministic
hash validation through the frozen suites, frontend source checks, `git diff --check`, credential
pattern scanning, production-stub scanning, frozen identity checks, and exact change-scope review.

No OpenAPI gate applies: the canonical server is Python standard-library HTTP and exposes no
generated OpenAPI document.

## 17. Private archive

Path: `data/datasets/112年多維度SHP成果_0502.zip`

SHA-256: `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`

- exact checksum;
- ignored;
- untracked;
- unstaged;
- not extracted;
- layer contents not inspected;
- not used by accepted scenarios;
- not copied or linked into regression/fresh reproduction checkouts;
- startup access disabled.

Public limitations are reported rather than hidden by relying on the archive.

## 18. Public reproducibility

Candidate fresh-clone reproduction is recorded after the candidate commit. It must use the public
repository only, with no private archive, no local untracked runtime directory, and no `.env.local`.
The machine record is updated with the exact reproduced candidate SHA and results afterward.

## 19. Required closure before a future PASS

A bounded acceptance-only change cannot create the missing artifacts without changing the runtime
contract or distribution posture. DEMO-01A should decide and implement, under separate authority:

1. a public, canonical, authorization-preserving School execution/replay scenario with plan,
   execution, verification, receipt, provenance, and map linkage;
2. a public ROAD geometry/observation representation that remains policy-compliant and renders from
   the same evidence being verified;
3. a user workflow that advances execute → observe → verify without severing identity linkage;
4. explicit normalized mutation fields for domain execution artifacts versus protected source and
   production activation.

Until then, DEMO-02 remains an evidence-backed FAIL, not an architectural redesign disguised as
acceptance.

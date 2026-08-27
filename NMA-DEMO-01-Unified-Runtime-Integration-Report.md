# NMA-DEMO-01 — Unified Runtime Integration Report

**Date:** 2026-08-22 (Asia/Taipei)

**Canonical repository:** `https://github.com/dongpo/topoMap.git`

**Exact predecessor:** `37c8c989daa2f9f54aadb32a9159d82ce35ea160`
**Branch:** `demo/demo-01-unified-runtime-integration`

## 1. Verdict

> **PASS — UNIFIED NMA RUNTIME INTEGRATED**

One user-reachable runtime now routes School Hero, ROAD, and BUILD requests without changing the
frozen domain implementations, generic contracts, authorization semantics, identity provider, or
portrayal ownership. New execution remains authorization-gated; public preview/replay is explicitly
distinguished from new execution; BUILD activation is always held unless separately authorized by
the frozen activation lifecycle.

Recommendation:

> **READY FOR DEMO-02 — END-TO-END DEMO ACCEPTANCE**

DEMO-02 is not performed here.

## 2. Canonical repository

- Origin fetch/push URL: `https://github.com/dongpo/topoMap.git`.
- Origin refs and tags were fetched before modification.
- The implementation branch was created directly from the exact DEMO-00 predecessor.
- No merge, tag, force-push, or frozen-history rewrite is part of DEMO-01.

## 3. Exact DEMO-00 predecessor

Before modification, all three references resolved to
`37c8c989daa2f9f54aadb32a9159d82ce35ea160`:

- local `demo/demo-00-runtime-readiness-audit`;
- local remote-tracking `origin/demo/demo-00-runtime-readiness-audit`;
- authoritative GitHub `refs/heads/demo/demo-00-runtime-readiness-audit`.

The starting worktree was clean. `NMA-DEMO-00-Runtime-Readiness-Audit.md` remains unchanged.

## 4. Branch

`demo/demo-01-unified-runtime-integration`

The branch did not exist locally or remotely before creation.

## 5. Final local SHA

The exact final local commit SHA is reported in the post-push task handoff. A Git commit cannot
contain its own object ID; this follows the repository convention recorded by GEN-01, GEN-02, and
DEMO-00.

## 6. Upstream SHA

The exact upstream SHA is reported in the post-push task handoff after
`@{upstream}` is established and verified.

## 7. Remote SHA

The exact canonical GitHub branch SHA is reported in the post-push task handoff from
`git ls-remote origin refs/heads/demo/demo-01-unified-runtime-integration`.

## 8. Equality result

Acceptance requires and the task handoff records:

`local HEAD = @{upstream} = canonical remote branch SHA`

No report text substitutes for that post-push Git evidence.

## 9. Exact changed-file list

Permitted DEMO-01 scope only:

1. `src/nma/unified_runtime.py` — bounded dispatcher, adapters, validation, envelopes, and errors.
2. `scripts/run_nma_agent_server.py` — unified runtime registration, endpoint, startup safety, and URL.
3. `nmaAgentDemoV1.html` — canonical DEMO-01 MapLibre user surface.
4. `tests/test_demo01_unified_runtime.py` — focused routing, authorization, reuse, safety, API, and UI tests.
5. `NMA-DEMO-01-Unified-Runtime-Integration-Report.md` — this report.

No frozen implementation, GEN artifact, contract schema, frozen portrayal asset, or source dataset
is modified.

## 10. Canonical server entry point

```bash
PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 8080
```

Protected-archive startup reads are disabled by default. Existing private School dataset preparation
is available only with the explicit local opt-in `NMA_ENABLE_PRIVATE_ARCHIVE=1`; that opt-in does
not bypass any domain authorization.

## 11. Canonical demo URL

`http://127.0.0.1:8080/nmaAgentDemoV1.html?basemap=local`

The historical v0.32 page remains reachable at
`http://127.0.0.1:8080/nmaAgentDemoV032.html?basemap=local`.

## 12. Canonical API route

- `GET /api/nma/runtime` — bounded capability declaration.
- `POST /api/nma/runtime` — unified request dispatch.

The existing server is Python standard-library HTTP rather than FastAPI, so it has no live OpenAPI
generator or `/docs` surface. DEMO-01 does not introduce a competing framework/server merely to
add Swagger.

Request fields are closed to:

```json
{
  "domain": "school | road | build (optional)",
  "request": "bounded natural-language intent",
  "operation": "preview | replay | execute | verify",
  "authorization": {},
  "parameters": {}
}
```

## 13. Domain dispatcher design

`UnifiedNMARuntime` owns only:

- closed request-shape validation;
- explicit-domain precedence;
- bounded deterministic classification when no domain is supplied;
- ambiguous/unsupported fail-closed behavior;
- exactly one adapter lookup;
- generic result-envelope integrity.

It does not implement School, ROAD, or BUILD semantics. Each adapter calls the existing
domain-owned runtime and returns an opaque normalized envelope consistent with the GEN-01/GEN-02
boundary.

## 14. School runtime path

```text
UnifiedNMARuntime
  → SchoolRuntimeAdapter
  → existing SchoolHeroExecutionEngine.execute_by_id
  → persisted canonical plan/receipt/bundle
  → existing SchoolHeroVerifier.verify (verify operation)
```

- Public preview exposes the frozen `school_feature_profile()` identity/capability without creating
  a fake plan.
- Canonical planning occurs inside `SchoolHeroExecutionEngine` after a stored HERO-03 authorization
  is successfully loaded and validated.
- The adapter does not accept client-submitted GIS parameters or authorization bodies.
- Visualization reuses the School runtime bundle and existing execution data route.

## 15. ROAD runtime path

```text
UnifiedNMARuntime
  → RoadRuntimeAdapter
  → existing RoadExecutionEngine.execute_by_id
  → persisted canonical plan/receipt/bundle
  → existing RoadExecutionVerifier.verify (verify operation)
```

- Execute accepts only the frozen authorization identifier plus idempotency key already required by
  ROAD.
- Public replay validates the frozen ROAD-04 plan, receipt, bundle, hashes, and linkage, and labels
  the result `frozen-execution-replay-not-new-execution`.
- Public ROAD geometry remains undistributed; replay reports an explicit artifact-reference-only
  visualization fallback.

## 16. BUILD runtime path

```text
UnifiedNMARuntime
  → BuildRuntimeAdapter
  → load_frozen_contract (BUILD-09F contract + policy identity)
  → load_authoritative_package (exact package/scope, protected execute only)
  → implement_controlled_building (BUILD-10)
  → verify_implementation_result
  → activation hold
```

- Live execute requires the exact BUILD-09F `policy_record_sha256` and exact package/project scope.
- The BUILD-10 result includes canonical plan, observation, verification, receipt, provenance, and
  MapLibre candidate records.
- `production_active`, `official_portrayal_active`, and automatic activation remain false.
- Public replay separately validates the frozen BUILD-05 redacted execution package; it never claims
  to be a new BUILD-10 execution.

## 17. Natural-language and structured-input behavior

Selection hierarchy:

1. explicit supported `domain`;
2. bounded deterministic School/ROAD/BUILD terms in `request`;
3. fail closed if zero or multiple domains match.

No OpenAI request is required. Structured domain input is the canonical deterministic testing and
automation interface. Natural language remains available for bounded routing.

## 18. Authorization preservation

- School: stored HERO-03 authorization ID + idempotency key; existing verifier/engine consume it.
- ROAD: frozen ROAD-03 authorization ID + idempotency key; existing verifier/engine consume it.
- BUILD: exact BUILD-09F policy record identity + exact package/project scope; BUILD-10 controlled
  implementation consumes the frozen contract and preserves activation hold.
- Missing/malformed authorization returns `authorization_failure` before execution.
- The dispatcher does not accept full replacement authorizations or client GIS paths.
- Verification rejects client-controlled screenshot/evidence filesystem paths.

Authorization bypass count: `0`.

## 19. Canonical identity preservation

- Runtime correlation IDs use `nma.core.canonical_sha256` over the normalized request envelope.
- They do not replace domain identities.
- Domain plan, authorization, execution, receipt, verification, and provenance identities are copied
  from canonical domain records.
- Identity fallback providers added: `0`.
- GEN-01 canonical provider remains `nma.core.canonical_sha256`.

## 20. Result-envelope design

Schema: `nma.unified-runtime-result/1.0`.

Fields:

- request correlation ID;
- selected domain and intent summary;
- operation and adapter contract;
- plan;
- authorization;
- execution and activation status;
- observation;
- verification;
- receipt;
- provenance;
- visualization;
- warnings/errors;
- six explicit mutation-safety booleans.

Optional/missing domain stages remain `null` or explicitly unavailable rather than fabricated.

## 21. Visualization status

- School execute: existing School MapLibre bundle/data/image references.
- ROAD execute: existing ROAD MapLibre bundle/data references.
- ROAD public replay: explicit artifact-reference-only fallback because private coordinates are not
  redistributed.
- BUILD public replay: visible frozen normalized polygon using its frozen boundary/hatch values.
- BUILD controlled execute: domain-owned BUILD-10 sources/resources/layers are consumed directly.

No generic cartographic engine or frozen portrayal change is introduced.

## 22. Mutation-safety result

Unified envelope defaults and verified behavior:

| Boundary | Result |
|---|---|
| Source writeback | false |
| Source repair | false |
| Silent geometry mutation | false |
| Portrayal mutation outside domain | false |
| Automatic BUILD activation | false |
| Authorization bypass | false |

Routing, preview, replay, invalid input, and missing authorization produced no files or source
mutation. BUILD controlled output remains an in-memory derived candidate with activation held.

## 23. Browser verification

Verified against a live server at port `18081` using the canonical launch command with no private
opt-in:

- canonical page loaded;
- unified capability endpoint reported all three domains;
- MapLibre initialized;
- BUILD replay routed, displayed its normalized result, receipt, verification, and provenance;
- BUILD polygon and hatch rendered visibly;
- School preview routed to the frozen capability;
- ROAD replay validated frozen identity/linkage;
- ambiguous `school + road` input displayed `ambiguous_domain` and did not mutate;
- preserved v0.32 page loaded and reported its local PMTiles MapLibre fallback ready;
- browser console warnings/errors: `0`.

## 24. Public/fresh-clone reproducibility

The public workflow depends only on tracked files:

- School capability preview;
- ROAD frozen execution replay/link validation;
- BUILD redacted frozen execution replay/visualization;
- negative routing and authorization flows;
- canonical page and API startup.

New School/ROAD/BUILD source execution remains protected-data dependent by frozen design. DEMO-01
does not fabricate public source data to disguise that limitation. Post-commit fresh-checkout
startup/API/page/replay evidence is recorded in the final handoff.

After starting the server, these public, non-mutating examples are reproducible:

```bash
curl -sS http://127.0.0.1:8080/api/nma/runtime \
  -H 'Content-Type: application/json' \
  -d '{"domain":"school","request":"Inspect the School Hero capability","operation":"preview","authorization":{},"parameters":{}}'

curl -sS http://127.0.0.1:8080/api/nma/runtime \
  -H 'Content-Type: application/json' \
  -d '{"domain":"road","request":"Replay the frozen ROAD execution","operation":"replay","authorization":{},"parameters":{}}'

curl -sS http://127.0.0.1:8080/api/nma/runtime \
  -H 'Content-Type: application/json' \
  -d '{"domain":"build","request":"Replay the frozen BUILD execution","operation":"replay","authorization":{},"parameters":{}}'
```

- School selects `school`, exposes the frozen capability/profile and authorization requirement,
  performs no execution, and identifies visualization as unavailable until authorized execution.
- ROAD selects `road`, exposes the frozen ROAD plan/authorization/execution/verification identities,
  validates receipt/provenance linkage, and reports the explicit artifact-reference visualization
  fallback.
- BUILD selects `build`, exposes the frozen BUILD plan/authorization/execution/verification
  identities, validates receipt/provenance linkage, and returns the redacted polygon visualization.

The correlation ID and all applicable plan, authorization, execution, verification, receipt, and
provenance fields are returned in each response envelope; absent School preview lifecycle stages
are explicitly unavailable rather than fabricated.

## 25. Focused tests

`tests/test_demo01_unified_runtime.py` covers:

- exact three-adapter construction;
- explicit and natural-language selection;
- School/ROAD/BUILD routes;
- unsupported and ambiguous failures;
- canonical School/ROAD engine delegation;
- canonical BUILD-10 controlled implementation delegation;
- missing/invalid authorization;
- rejection of client-controlled verification paths;
- replay identity/link validation;
- BUILD activation hold;
- no-mutation preview/replay/error paths;
- endpoint/page/legacy page registration;
- live loopback startup, page, API, positive BUILD, and negative ambiguity.

Result outside the loopback-restricted sandbox: **15 passed**.

## 26. Regression results

| Suite | Result |
|---|---:|
| DEMO-01 focused | 15 passed |
| Existing API/v0.32/Agentic VS2/School API | 26 passed |
| Core/School frozen functional baseline | 46 passed |
| ROAD-01/02/03 frozen functional baseline | 104 passed |
| BUILD contract/policy public baseline | 57 passed |
| Public BUILD-FINAL integrity | 8 passed |
| Exact detached GEN-00 | 11 passed |
| Exact detached GEN-01 public checks | 14 passed; private archive identity test excluded |
| Exact detached GEN-02 public checks | 15 passed; private archive identity test excluded |
| Exact detached GEN-FINAL public checks | 9 passed; private archive identity test excluded |

Current-descendant GEN scope assertions were not weakened. Their historical exact-file-set
assumptions intentionally reject later GEN-FINAL, DEMO-00, and DEMO-01 files; exact detached
worktrees reproduced the frozen public checks.

Ruff check/format for the new module and focused test: `PASS`. `git diff --check`: `PASS`.

## 27. Frozen baseline integrity

Verified exact ancestors/tags before modification:

| Freeze | Required identity | Result |
|---|---|---|
| GEN-FINAL | `380cc6ea2a4498ce83690521c933accfd918818e`; `nma-generalization-v1.0-final^{}` | exact |
| BUILD-FINAL | `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7`; `nma-build-v1.0-final^{}` | exact |
| CORE-FINAL | `5eb138ae7686502431587743ebce9ddf92c5a799` | exact ancestor |
| ROAD-FINAL | `325c70d5335f57c43a8af85822db25032aa225c3` | exact ancestor |
| School Hero | `56f99eb9ae63272a68accac3041fb10eacefb986` | exact ancestor |

Frozen source/contract modifications: `0`.

## 28. Private archive status

Path: `data/datasets/112年多維度SHP成果_0502.zip`.

- present locally;
- ignored;
- untracked;
- unstaged;
- not copied into any worktree/fresh checkout;
- not required by public preview/replay/UI/startup;
- startup auto-read disabled unless `NMA_ENABLE_PRIVATE_ARCHIVE=1`.

Process note: an early invocation of the existing private ROAD-04 integration suite exercised its
canonical archive reader locally. It confirmed the frozen read-only path and did not modify, track,
stage, copy, or redistribute the archive. All subsequent DEMO-01, detached GEN, browser, and public
reproducibility checks excluded private archive access. This deviation is disclosed rather than
mischaracterized as a public-runtime dependency.

## 29. Known limitations

1. A fresh public checkout cannot create new School/ROAD/BUILD source executions because the frozen
   engines correctly require protected source data; public preview/replay remains available.
2. School new execution also requires a separately stored valid HERO-03 authorization; DEMO-01 does
   not introduce an issuer or demo bypass.
3. ROAD public replay cannot render undistributed geometry and reports the fallback explicitly.
4. First-load MapLibre library delivery uses the same external CDN class as the preserved demo and
   may require network/cache availability.
5. The standard-library server has no generated OpenAPI UI.
6. Full rendered ROAD verification still requires actual browser observation evidence and belongs
   in DEMO-02 acceptance.

## 30. DEMO-02 readiness

> **READY FOR DEMO-02 — END-TO-END DEMO ACCEPTANCE**

DEMO-02 should validate complete authorized scenarios with suitable data/authorization fixtures,
browser observations, negative controls, receipts/provenance, public distribution policy, and fresh
reproduction. It must not reinterpret DEMO-01 replay as new execution.

## 31. Final worktree status

Acceptance requires a clean worktree after the independent DEMO-01 commit and normal push. The
post-push task handoff records the final clean `git status --porcelain=v1` result together with the
exact local/upstream/remote SHA equality.

No merge, tag, amend of a frozen commit, or force-push is performed.

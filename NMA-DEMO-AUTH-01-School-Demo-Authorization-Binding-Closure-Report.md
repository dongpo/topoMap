# DEMO-AUTH-01 — School Demo Authorization Binding Closure Report

## 1. Verdict

**PASS — SCHOOL DEMO AUTHORIZATION BINDING CLOSED**

The exact controlled School fixture can now be intentionally issued a new, deterministic,
human-approved, demo-only authorization through the existing frozen HERO-03 authorization schema,
hashing, verifier, filesystem store, execution engine, and verification/provenance machinery. The
authorization is additive. It does not impersonate the historical authorization and does not
change School, GraphRAG, portrayal, geometry, Core, ROAD, BUILD, or generic NMA semantics.

**READY FOR DEMO-02 RETRY — CONTROLLED END-TO-END DEMO ACCEPTANCE**

DEMO-02 Retry remains a separate task and must use the same controlled School and ROAD fixtures,
accepted BUILD path, unified runtime, and the authorization recorded here.

## 2. Repository and Git identity

| Item | Exact result |
|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` |
| Mandatory predecessor | `00bd681f2cc5f42873053f37b85724aefc8bec03` |
| Predecessor local/upstream/origin | exact equality before modification |
| Branch | `demo/demo-auth-01-school-demo-authorization-binding` |
| Starting task worktree | clean; unrelated original checkout preserved untouched |
| Final local/upstream/origin | exact equality verified in the terminal handoff |
| Final SHA | reported by the terminal handoff because a Git commit cannot embed its own content-addressed SHA without changing that SHA |
| Merge/tag/force-push | none |

Frozen identities were re-resolved without modification:

- GEN-FINAL: `380cc6ea2a4498ce83690521c933accfd918818e`, with
  `nma-generalization-v1.0-final` peeling to the same commit;
- CORE-FINAL: `5eb138ae7686502431587743ebce9ddf92c5a799`;
- School Hero freeze: `56f99eb9ae63272a68accac3041fb10eacefb986`;
- ROAD-FINAL: `325c70d5335f57c43a8af85822db25032aa225c3`;
- BUILD-FINAL: `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7`.

## 3. Exact changed-file scope

1. `artifacts/runtime/school-hero/authorizations/authorization-school-demo-b4ecdbfc35ecaf73293ed497.json`
2. `scripts/issue_school_demo_authorization.py`
3. `tests/test_demo_auth01_school_authorization.py`
4. `NMA-DEMO-AUTH-01-School-Demo-Authorization-Binding-Closure-Report.md`

Frozen School executor/verifier changes: **0**. Unified runtime/server changes: **0**. GraphRAG,
portrayal, geometry, fixture, ROAD, BUILD, Core, and generic-contract changes: **0**.

## 4. Controlled School fixture binding

| Property | Exact binding |
|---|---|
| Fixture identity | `nma-demo-fixture:school:sha256:77802b44b97c6687bc626d257e14b57c3d7427949a65942fa721d05bb79fc12d` |
| Aggregate SHA-256 | `77802b44b97c6687bc626d257e14b57c3d7427949a65942fa721d05bb79fc12d` |
| Private package SHA-256 | `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53` |
| Domain / target | School / `TERRAINID=9920103` / Point |
| Layers | `J01_MARK`, `J13_MARK`, `J17_MARK`, `K01_MARK`, `K02_MARK`, `K14_MARK` |
| Selected counts | `0 + 1 + 0 + 12 + 1 + 1 = 15` |
| Fixture role | controlled demo input only |
| Raw fixture modification/redistribution | none |

The issuer reads the authoritative DEMO-FIXTURE-00 record and fails closed unless its exact
identity, package hash, layer order, per-layer selected counts, source filter, geometry role, and
15-feature result remain unchanged. It also hashes the actual local package before issuance. It
does not recompute or replace the established aggregate identity.

## 5. Existing HERO-03 authorization model audit

Direct implementation evidence, not report inference:

| Concern | Existing code/schema/evidence path | Finding |
|---|---|---|
| Authorization schema and self-hash | `src/nma/school_hero_execution.py` — `AUTHORIZATION_SCHEMA`, `authorization_sha256`, `ExecutionAuthorizationVerifier` | `nma.symbol-edit-authorization/1.0`; canonical JSON SHA-256 excluding `authorization_hash` |
| Human approval | `ExecutionAuthorizationVerifier.verify` | requires `decision=approved`, `actor_type=human`, exact proposal identity, and approved-operation hash |
| Proposal/plan binding | `ExecutionAuthorizationVerifier.verify`; `SchoolHeroExecutionEngine.build_plan` | authorization binds proposal payload/hash; canonical execution plan is deterministically derived after authorization and records authorization ID/hash |
| Fixture/data binding | verifier and `_execute_atomic` | authorization binds exact archive SHA; execution re-hashes the actual archive before any materialization |
| School target binding | `_identity`; `REAL_LAYER_PROFILES["school-point"]` | exact `9920103` / Point and frozen six-layer/filter/field/15-feature profile |
| Scope | `REQUIRED_SCOPE`; verifier | requires derived real layer, derived portrayal, and candidate MapLibre layer |
| Validity | verifier | ready, unused, unexpired, not future-issued, and not invalidated |
| Storage/discovery | `ExecutionAuthorizationStore`; `scripts/run_nma_agent_server.py` | `{storage_root}/authorizations/{authorization_id}.json`; stored ID must equal requested ID |
| Consumption | `execute_by_id` → `verify` → `_execute_atomic`; `SchoolRuntimeAdapter` | client supplies only authorization ID and idempotency key; no GIS parameters or bypass flag reach executor |
| Rejection | verifier/store/engine | incomplete, rejected, expired, tampered, wrong proposal/target/baseline/scope/archive/store identity, replay mismatch, and unsafe source state fail closed |
| Verification/provenance | `src/nma/school_hero_verification.py` | re-verifies auth/plan/receipt/bundle/input/output hashes and six-record lineage through approval |

The frozen model had no production/demo issuer. Its historical test-support constructor was not
promoted or reused as authority. The new bounded utility calls the canonical hashing, intent,
lineage, verifier, and store functions and can issue only this one controlled-demo capability.

## 6. Historical binding classification

| Existing binding | Classification | DEMO-AUTH-01 treatment |
|---|---|---|
| `nma.symbol-edit-authorization/1.0`, verification rules, School profile, executor | STRUCTURAL CONTRACT | unchanged and reused |
| archive SHA `4888db…` and official symbol baseline | HISTORICAL FIXTURE IDENTITY | unchanged; new namespaced fixture commitment is additionally bound in the proposal/approval |
| `authorization-school-blue` / `432c3561…` | HISTORICAL AUTHORIZATION IDENTITY | unchanged and explicitly unequal to demo ID/hash |
| `actor_type=human` and `decision=approved` | ISSUER REQUIREMENT | used exactly; no person or invented PII added |
| approved proposal payload/hash, then derived execution plan | PLAN REQUIREMENT | new demo proposal binds fixture/action/scope; live plan records its auth ID/hash |
| three required derived-only scope values | EXECUTION-SCOPE REQUIREMENT | exact list retained; writeback, repair, activation, publication absent/false |
| runtime authorization directory and ID-addressed JSON | STORAGE/DISCOVERY REQUIREMENT | tracked artifact placed at the unchanged canonical discovery location |
| BUILD exact changed-file/direct-parent assertions | STALE TEST ASSUMPTION | two known later-descendant failures reproduced; not changed |
| School authorization semantics | UNRESOLVED | none |

## 7. New authorization and explicit approval

| Property | Exact value |
|---|---|
| Authorization ID | `authorization-school-demo-b4ecdbfc35ecaf73293ed497` |
| Authorization self-hash | `d5546bd1b2176a4ad287acb1c78740ce79a90db76d05739dc871267d901dac67` |
| Proposal ID | `proposal-school-demo-bd5981eb31d0bf7f567ede4d` |
| Proposal hash | `588bc2dfcbb704543637b33f3827f85b653f5c2f21e9abb5fc295421262fbfb5` |
| Schema | `nma.symbol-edit-authorization/1.0` |
| Approval | `decision=approved`, `actor_type=human` |
| Issued / expires | `2026-08-23T00:00:00Z` / `2030-01-01T00:00:00Z` |
| Approved action | existing derived School symbol color operation `#1565c0` |
| Scope | exact frozen three-value derived-only scope |
| Writeback / repair / activation | false / false / false |

The approval record binds the proposal hash, fixture identity, exact demo-scope hash, School feature
identity, portrayal baseline, and operation hash. Invoking the issuer without `--human-approved`
fails and creates no artifact. Identical approved canonical inputs reproduce byte-identical JSON,
the same authorization ID, and the same self-hash.

Historical HERO-03 identity remains:

- authorization ID: `authorization-school-blue`;
- self-hash: `432c356180843ec27304d7a5b09dbc990c325e90ed67a9e4dcad159f66678d9d`.

Neither value is reused by the controlled-demo record.

## 8. Consumption, execution, verification, and mutation safety

The canonical live path completed as follows:

```text
controlled fixture 77802b…
→ proposal proposal-school-demo-bd5981… / 588bc2…
→ human approval
→ authorization authorization-school-demo-b4ecdb… / d5546b…
→ existing ExecutionAuthorizationStore + ExecutionAuthorizationVerifier
→ plan plan-0ffa743ff11612ef2a452691 / 795c7c…
→ existing SchoolHeroExecutionEngine
→ receipt d4aff432…
→ QA f524f4ec… (expected-change-verified)
→ provenance ac6dfb9b… (verified)
```

Live unified runtime result:

- selected domain: `school`;
- authorization: `consumed`, exact new ID/hash;
- execution: `exec-0ffa743ff11612ef2a452691`;
- result: 15 Point features in EPSG:4326 from the exact six layers;
- MapLibre result: available through the existing bundle path;
- authoritative source mutation: false;
- source repair: false;
- official portrayal activation: false;
- PMTiles rebuild/publication: false;
- authorization bypass: false.

The existing School verifier returned `expected-change-verified`; provenance returned `verified`
and linked the request, intent, fixture/GraphRAG evidence, decision, proposal, human approval,
authorization, execution, QA, and artifact commitments. No provenance link was fabricated outside
the existing six-record lineage and verifier behavior.

The canonical server command was used on `127.0.0.1:8080`. Browser verification loaded
`nmaAgentDemoV1.html?basemap=local` with no console errors/warnings and inspected the live receipt,
which visibly contained the new authorization ID/hash, package hash, six layers, 15 Point features,
proposal, plan, and zero-mutation governance fields.

Generated execution state was removed after verification; it is deterministically reproducible.
The tracked authorization artifact remains at the canonical discovery location.

## 9. Negative authorization results

| Case | Result before prohibited mutation |
|---|---|
| A1 wrong fixture/package hash | issuer rejects; engine independently rejects archive checksum |
| A2 wrong TERRAINID/geometry target | frozen `_identity` rejects outside HERO-04 scope |
| A3 wrong domain (ROAD/BUILD-shaped identity) | frozen School identity gate rejects |
| A4 wrong proposal/approved plan operation | frozen proposal/approved-operation binding rejects |
| A5 tampered authorization/demo commitment | frozen self-hash rejects |
| A6 missing/pending human approval | frozen human-approval gate rejects |
| A7 historical ID impersonation in demo artifact | existing ID-addressed store rejects stored/requested identity mismatch |
| A8 production writeback operation | unified runtime rejects unsupported operation before domain dispatch |

Focused DEMO-AUTH-01 suite: **8 passed**.

## 10. Regression, static, and security results

| Gate | Result |
|---|---|
| DEMO-FIXTURE-00 focused | 7 passed |
| DEMO-01 + DEMO-02 | 34 passed, 1 loopback skip |
| School/Core/real-layer/HERO frozen selection | 54 passed |
| ROAD-01 through ROAD-05 | 199 passed |
| exact detached GEN-FINAL | 10 passed |
| BUILD-10/11/11A/12 | 87 passed, 2 known stage-local exact-scope/direct-parent failures |
| Ruff lint / format | PASS |
| authorization canonical verifier/self-hash | PASS |
| generated plan/receipt/bundle/QA/provenance JSON Schema instances | 5 PASS |
| repository JSON parse | PASS |
| deterministic regeneration/byte comparison | PASS |
| tamper/negative gates | PASS |
| secret/private-key pattern scan of changed artifacts | PASS; no credentials |
| frozen implementation diff | empty |
| `git diff --check` | PASS |

The two BUILD failures are materially identical to DEMO-FIXTURE-00: a BUILD-11A assertion demands
its historical exact changed-file set, and a BUILD-12 assertion demands BUILD-11A as the direct
branch parent. They are stage-local lineage/scope assertions, not functional failures. No new
School, ROAD, BUILD, Core, GraphRAG, geometry, portrayal, authorization, or execution failure was
observed.

## 11. Fresh reproduction

Fresh reproduction used the exact committed candidate, supplied the private package only through
the documented local fixture path, verified package SHA `4888db…`, regenerated and byte-compared
the authorization, ran the focused suite, executed the representative School request through the
unified adapter, and verified QA/provenance. Raw fixture bytes and coordinates were not added to
Git.

Reproduction model:

```text
public code
+ controlled package SHA-256 4888db… supplied locally
+ explicit --human-approved issuance
+ authorization-school-demo-b4ecdb…
→ canonical unified School execution and verification
```

Fresh result: **PASS**.

## 12. Closure counts and DEMO-02 readiness

| Closure item | Count/result |
|---|---|
| External-data searches/downloads/substitutions | **0** |
| Controlled fixture modifications | **0** |
| Raw fixture bytes/coordinates committed | **0** |
| Historical authorization identities reused | **0** |
| Authorization bypasses | **0** |
| Frozen semantic changes | **0** |
| Final worktree | clean after commit/push verification |
| DEMO-A5 Authorization | PASS candidate |
| DEMO-A6 Real Execution | PASS candidate |

The remaining School blocker identified by DEMO-FIXTURE-00 is closed. This report does not claim
DEMO-02 acceptance and does not begin DEMO-02 Retry.

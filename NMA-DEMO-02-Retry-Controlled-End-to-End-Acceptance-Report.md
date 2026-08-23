# DEMO-02 Retry — Controlled End-to-End Demo Acceptance Report

## 1. Verdict

**PASS — NMA CONTROLLED END-TO-END DEMO ACCEPTED**

The controlled NMA v1.0 research claim is accepted: with the exact owner-supplied School/ROAD
fixture package, the unified Agent runtime uses retrieved/reviewed cartographic knowledge and
frozen domain paths to plan, authorize, execute or replay, observe, verify, preserve provenance,
and present rule-aligned School, ROAD, and BUILD results.

This verdict does not claim arbitrary open-data ingestion, public redistribution of the controlled
Shapefiles, an approved ROAD shield graphic, or pixel-perfect cartography.

**READY FOR DEMO-FINAL — NMA CONTROLLED DEMO FREEZE**

DEMO-FINAL is not begun by this task.

## 2. Canonical repository and Git gate

| Item | Accepted identity/result |
|---|---|
| Repository | `https://github.com/dongpo/topoMap.git` |
| Mandatory predecessor branch | `demo/demo-auth-01-school-demo-authorization-binding` |
| Exact predecessor | `aa3a59ddececa1bc8b893058febe5cb43d307656` |
| Retry branch | `demo/demo-02-retry-controlled-end-to-end-acceptance` |
| Local predecessor | exact |
| Configured upstream predecessor | exact |
| Fetched canonical remote predecessor | exact |
| Starting worktree | clean |
| Final local/upstream/remote | established after the evidence commit; exact SHA is reported by the canonical branch ref and terminal completion response |

A Git commit cannot contain its own final SHA without changing that SHA. The machine record states
this self-reference boundary; post-push local/upstream/remote equality is the terminal authority.
No merge, tag, or force-push was performed.

## 3. Exact change scope

Expected committed files:

1. `NMA-DEMO-02-Retry-Controlled-End-to-End-Acceptance-Report.md`
2. `data/specifications/nma-demo-02-retry-controlled-e2e-acceptance-record-v1.0.json`
3. `tests/test_demo02_retry_controlled_e2e_acceptance.py`
4. `nmaAgentDemoV1.html`
5. `scripts/run_nma_agent_server.py`
6. `src/nma/unified_runtime.py`

The first three are retry evidence/tests. The last three are bounded DEMO-owned integration fixes.
Frozen School, ROAD, BUILD, Core, GEN, GraphRAG, authorization, portrayal, geometry, and verifier
semantics changed: **0**.

Runtime/source integration files changed: **3**. New capability introduced: **0**. Authorization
weakened: **0**.

## 4. Minimal integration corrections

Live browser acceptance exposed two bounded defects:

1. `nmaAgentDemoV1.html` did not declare the glyph source required by the frozen School and ROAD
   symbol layers and did not load the School execution's exact image resource. MapLibre therefore
   rejected the text layers or could not decode the School resource. The page now declares the
   same reviewed glyph endpoint used by ROAD-05 and loads the exact execution-owned School SVG.
2. The unified ROAD verify adapter did not pass the standard ignored ROAD-05 visual-evidence and
   screenshot paths to `RoadExecutionVerifier`. All geometry, identity, semantics, and lineage
   checks passed, but `actual_render_observation` was necessarily absent. The adapter/server now
   pass those paths; the frozen verifier remains unchanged and still fails closed if either file is
   absent, invalid, or hash-mismatched.

Regression coverage proves both corrections are production-reachable. No success, QA, execution,
authorization, geometry, or provenance value is hard-coded by either correction.

## 5. Frozen baseline integrity

| Baseline | Required SHA | Result |
|---|---|---|
| GEN-FINAL | `380cc6ea2a4498ce83690521c933accfd918818e` | exact ancestor; tag target exact |
| CORE-FINAL | `5eb138ae7686502431587743ebce9ddf92c5a799` | exact ancestor |
| School Hero freeze | `56f99eb9ae63272a68accac3041fb10eacefb986` | exact ancestor |
| ROAD-FINAL | `325c70d5335f57c43a8af85822db25032aa225c3` | exact ancestor |
| BUILD-FINAL | `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7` | exact ancestor; tag target exact |

Frozen artifact changes: **0**. Frozen implementation/semantic changes: **0**.

## 6. Controlled fixture identities

Package: `data/datasets/112年多維度SHP成果_0502.zip` (ignored, untracked, not redistributed).

| Property | Value |
|---|---|
| Package SHA-256 | `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53` |
| Size | 12,822,898 bytes |
| Inspection/execution | read-only GDAL/OGR |
| External substitution | 0 |
| Controlled fixture modifications | 0 |

School identity:

`nma-demo-fixture:school:sha256:77802b44b97c6687bc626d257e14b57c3d7427949a65942fa721d05bb79fc12d`

- layers: `J01_MARK`, `J13_MARK`, `J17_MARK`, `K01_MARK`, `K02_MARK`, `K14_MARK`;
- selected distribution: `0 / 1 / 0 / 12 / 1 / 1`;
- total: 15 unique, labelled, valid Point features;
- filter: `TERRAINID=9920103`;
- fields used: `MARKID`, `TERRAINID`, `MARKNAME1`.

ROAD identity:

`nma-demo-fixture:road:sha256:dc82db8bfc96dd6ab16b3206866e000459b9fd59a8f6d44602fcf06586b1ae79`

- exact `K14_ROAD.{shp,shx,dbf,prj,cpg}`;
- 196 source features; `TWD97[2020]_TM121`;
- ordered target IDs: `K0000004671 / K0000004913 / K0000005348`;
- source/runtime vertex counts: `4 / 3 / 4`;
- exact source geometry hashes:
  `42616b9b…8f800 / c0759439…b9faf / 88ad286f…2cc6`;
- finite, valid, simple, contiguous LineStrings with class `9420400`, route `縣126`, name `中山街`.

## 7. School demo authorization

| Property | Accepted value |
|---|---|
| Authorization ID | `authorization-school-demo-b4ecdbfc35ecaf73293ed497` |
| Authorization hash | `d5546bd1b2176a4ad287acb1c78740ce79a90db76d05739dc871267d901dac67` |
| Human decision | approved |
| Fixture binding | exact controlled School identity/archive/six-layer/15-feature scope |
| Plan/scope | derived real layer, derived portrayal, candidate MapLibre layer only |
| Production writeback | false |
| Historical HERO-03 identity reused | false |
| Deterministic canonical validation | pass |

No different authorization was generated.

## 8. Unified runtime

Command:

```text
PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 8080
```

- demo URL: `http://127.0.0.1:8080/nmaAgentDemoV1.html?basemap=local`;
- API route: `http://127.0.0.1:8080/api/nma/runtime`;
- one `UnifiedNMARuntime`, one page, one API route, three frozen-domain adapters;
- deterministic fallback is sufficient; no OpenAI credential is required;
- automatic BUILD production activation: false.

## 9. Scenario S — School complete trace

User request:

> Produce the authorized controlled School map for TERRAINID 9920103 using the retrieved NLSC
> school portrayal rule, then expose execution and map provenance.

| Stage | Accepted evidence |
|---|---|
| Request | `nma-runtime-request:sha256:29dd75e8…458b92d` |
| Routing | `school` |
| Intent/evidence | request `request:6458…`; intent `intent:478a…`; evidence `evidence:d8390501f96f29918fbc` |
| GraphRAG | four exact School node IDs below |
| Plan | `plan-8d174b62fb63189987eafdb6`; SHA `b7afb381…fa0347` |
| Authorization | exact DEMO-AUTH-01 ID/hash consumed |
| Execution | `exec-8d174b62fb63189987eafdb6`; real HERO-04 engine |
| Receipt | SHA `ab929277…d1d36b` |
| Observation/result | 15 Point features; data SHA `7f62b625…932548` |
| QA | passed; `2fcc1d90…32cb538`; expected-change-verified |
| Provenance | verified; `bc939235…e05e8ae2` |
| Map bundle | `5b4212a0…b83d49e`; exact execution SVG/data references |
| Mutation | all integration/source/activation flags false |

Result: **School E2E = PASS**.

### School GraphRAG and mapping-rule alignment

Retrieved/bound node IDs:

- `code-value:landmark-type:9920103`;
- `portrayal-rule:doc01:9920103` (page 61, Point, school-name annotation);
- `portrayal-recipe:doc01:9920103:review-v1`;
- `product-layer:MARK`.

The evidence record is a parent of the decision, proposal, human approval, execution, QA, and
provenance chain. The plan filters the exact six MARK layers by `TERRAINID=9920103`. The executed
bundle uses the School image resource, `MARKNAME1` text, approved blue portrayal, collision-aware
symbol placement, and the expected 15-feature source. QA independently matches data, portrayal,
bundle, authorization, graph identity, and lineage hashes.

The accepted claim is rule/plan/execution alignment. It is not merely “15 points rendered.”

## 10. Scenario R — ROAD complete trace

User request:

> Produce the authorized controlled ROAD map for County Highway 126 and ROAD class 9420400 using
> the frozen line-label and route-shield portrayal rules, preserving exact K14_ROAD geometry.

| Stage | Accepted evidence |
|---|---|
| Request | `nma-runtime-request:sha256:63d73cc8…6a2082d` |
| Routing | `road` |
| Graph/rule evidence | five frozen evidence IDs and six canonical nodes below |
| Plan | `road-plan-cd434d50bd5b49a012bd1e10`; SHA `e51e42b9…bf04a0` |
| Authorization | `road-03-authorization-f68220ecef989e589dd6e28c` consumed |
| Execution | `road-exec-33766f336d9cc18eb2ac159e`; real ROAD-04 engine/lineage |
| Observation | `road-observation-4c88e2e424168c1c712145c1`; exact bundle/source/layer/count |
| Receipt | `road-receipt-road-exec-33766f336d9cc18eb2ac159e`; SHA `0ab5964f…610720` |
| Geometry | exact three source hashes and ordered `4 / 3 / 4` vertices |
| QA | passed; `8f31ecb2…464a82`; expected-change-verified |
| Provenance | verified; `130a24e1…bc70` |
| Map bundle | `33aa7c6b…4a286d`; actual runtime GeoJSON data reference |
| Visual evidence | `830087a0…707662b`; screenshot hash `4124aef8…9062` |
| Mutation | source/topology/ROADA/ROAD-edge/canonical-runtime flags false |

Result: **ROAD E2E = PASS**.

### ROAD GraphRAG and mapping-rule alignment

Frozen evidence IDs:

- `BMAP096-P5-TABLE1-GRAPHIC-ELEMENT-CODES`;
- `DOC01-P22-P24-ROAD-BOUNDARY-LABEL`;
- `DOC01-P34-P35-ROUTE-SHIELDS`;
- `DOC02-P45-P46-ANNEX7-CODING-SCHEME`;
- `DOC02-P53-P55-ROAD-CODE-BRANCH`.

Canonical nodes include `portrayal-rule:doc01:9420400`,
`portrayal-rule:doc01:9490005`, `portrayal-recipe:road:9420400:compound-v1`, the ROAD class
node, name-label primitive, and route-shield primitive. The proposal, decision, authorization,
plan, derived portrayal, bundle, observation, QA, and provenance preserve the same class, route,
name, evidence IDs, ordered segments, and exact geometry commitments.

The executed result applies one line-following literal `中山街` label to the controlled LineString
source. Shield code `9490005` remains `road-parallel` and `semantic_binding_only`; no unsupported
graphic is invented. The browser visibly showed the name following the controlled line path.
Exact geometry was independently reconstructed and hash/vertex/continuity checked.

No independent pixel oracle exists. Pixel-perfect correctness is not claimed.

## 11. Scenario B — BUILD complete trace

User request:

> Replay the accepted BUILD 9310100 result, verify its provenance, and keep production activation
> disabled.

| Stage | Accepted evidence |
|---|---|
| Routing | `build` |
| Plan | `b8b5ecd5…b52b0b71`; frozen validated replay |
| Authorization | `build-04-demo-auth-a5a8f11b94784a60`; frozen consumed evidence |
| Execution/replay | `build-05-demo-exec-b8b5ecd54954b190eb8cda39` |
| Observation | `9131df53…d3400d84`; rendered-derived-demo |
| Verification/provenance | `10c22339…c98c97`; passed package validation/content-addressed |
| Receipt | `build-05-receipt-b8b5ecd54954b190eb8cda39`; `c4ff4017…45573` |
| Map | accepted polygon, solid boundary, diagonal hatch |
| Activation | `held-not-requested`; automatic activation false |
| Mutation | source and activation mutation false |

Result: **BUILD E2E = PASS**.

BUILD is accurately labelled as the accepted execution/replay path, not a new production
activation. BUILD implementation was not modified.

## 12. DEMO-A1–A12

| Criterion | Result | Basis |
|---|---|---|
| DEMO-A1 — Single Entry Point | PASS | one page/API/runtime |
| DEMO-A2 — User Intent | PASS | actual requests and deterministic intent/domain interpretation |
| DEMO-A3 — Domain Routing | PASS | explicit/natural and negative routing verified |
| DEMO-A4 — Real Planning | PASS | three traceable domain-correct plans |
| DEMO-A5 — Authorization | PASS | exact School; canonical ROAD; accepted BUILD; negatives fail closed |
| DEMO-A6 — Real Execution | PASS | School real execution; ROAD canonical execution lineage; BUILD accepted execution/replay |
| DEMO-A7 — Observable Result | PASS | School data/map, ROAD observation/map, BUILD observation/map |
| DEMO-A8 — Map Result | PASS | three browser-visible rule-aligned results |
| DEMO-A9 — Verification | PASS | School/ROAD verified; BUILD package validation passed |
| DEMO-A10 — Provenance | PASS | request/plan/auth/execution/QA/receipt chains traceable |
| DEMO-A11 — Fail-Closed | PASS | N1–N12 and mutation tripwires |
| DEMO-A12 — Controlled Reproducibility | PASS | exact repo + fixtures + auth + procedure; fresh clone reproduced |

**DEMO-A6 — PASS**
**DEMO-A8 — PASS**

## 13. Acceptance matrix

| Criterion | School | ROAD | BUILD | Overall |
|---|---|---|---|---|
| Controlled fixture | PASS | PASS | PASS | PASS |
| User request | PASS | PASS | PASS | PASS |
| GraphRAG retrieval | PASS | PASS | PASS_NOT_APPLICABLE | PASS |
| Mapping-rule alignment | PASS | PASS | PASS | PASS |
| Planning | PASS | PASS | PASS | PASS |
| Authorization | PASS | PASS | PASS | PASS |
| Real execution | PASS | PASS | PASS | PASS |
| Observation | PASS | PASS | PASS | PASS |
| Verification/QA | PASS | PASS | PASS | PASS |
| Receipt/provenance | PASS | PASS | PASS | PASS |
| Map/result | PASS | PASS | PASS | PASS |
| Fail-closed | PASS | PASS | PASS | PASS |
| Controlled reproducibility | PASS | PASS | PASS | PASS |

Machine-readable record:
`data/specifications/nma-demo-02-retry-controlled-e2e-acceptance-record-v1.0.json`.

## 14. Authorization and mutation safety negatives

| ID | Scenario | Result |
|---|---|---|
| N1 | unsupported domain | PASS — `unsupported_domain` before execution |
| N2 | ambiguous domain | PASS — `ambiguous_domain` deterministic clarification boundary |
| N3 | invalid request | PASS — `invalid_request` before execution |
| N4 | missing authorization | PASS — `authorization_failure` before engine call |
| N5 | invalid authorization | PASS — rejected before mutation |
| N6 | wrong School fixture/package identity | PASS — canonical issuer rejects |
| N7 | wrong School plan/scope | PASS — approved-operation/scope validation rejects |
| N8 | unknown feature target | PASS — `unsupported_capability`; no substitution |
| N9 | unsupported capability | PASS — explicit unsupported/invalid response |
| N10 | BUILD activation without authority | PASS — operation rejected; no activation |
| N11 | missing controlled fixture | PASS — clear archive failure; no fallback/download |
| N12 | tampered evidence | PASS — canonical hash/identity mismatch rejected |

All checked negative requests preserved the runtime artifact set and all mutation flags remained
false. External data substitutions: **0**.

## 15. Provenance answer

For every success, the evidence answers: what request produced the result, under which plan and
authorization, through which execution, and how it was verified.

- School links request → intent → GraphRAG evidence → decision → proposal → human approval → plan
  → execution/receipt → data/portrayal/map bundle → QA → provenance.
- ROAD links reviewed evidence/fixture → proposal/decision → approval/authorization → plan → exact
  source/runtime geometry → derived portrayal/bundle → observation/receipt → visual QA → provenance.
- BUILD links frozen plan/authorization → accepted execution/replay → observation → package
  verification → receipt/provenance → browser visualization and activation hold.

Receipt/provenance acceptance: **PASS**.

## 16. Browser acceptance

The canonical page was tested in the Codex in-app browser against the live port-8080 server.

- School request was entered and submitted with the exact authorization/idempotency key. Routing,
  plan, consumed authorization, execution, receipt, provenance-pending state, and map availability
  were shown. The map visibly rendered the approved blue School flag symbol and School labels.
  A separate unified verify request displayed `verified` QA and verified provenance.
- ROAD request was entered and submitted with the canonical authorization/key. Routing, plan,
  execution, receipt hash, frozen lineage, and map availability were shown. The browser visibly
  rendered `中山街` following the controlled line path. A separate unified verify request displayed
  `verified` QA and verified provenance.
- BUILD request was entered and submitted. The accepted polygon, boundary, and hatch were visible;
  observation, verification, receipt, provenance, and `held-not-requested` activation were shown.

Fatal JavaScript errors after the bounded fix: **0**. Screenshots were inspected as transient
acceptance evidence and were not promoted to pixel goldens.

## 17. No-stub/no-substitution audit

Production-reachable demo path inspection confirmed:

- School/ROAD call `self.engine.execute_by_id(authorization)`;
- BUILD calls `implement_controlled_building(...)` for controlled execution and validates frozen
  packages for replay;
- no `DemoStub`, `authorized = True`, fake execution/QA/provenance generator, external downloader,
  OSM/NLSC substitute, or synthetic ROAD geometry was added;
- the visual fix consumes the exact execution bundle/resource/data references;
- the ROAD verification fix delegates to the unchanged canonical verifier.

Production-reachable demo stubs: **0**. External data substitutions: **0**.

## 18. Focused and regression verification

| Suite | Result |
|---|---:|
| DEMO-02 Retry focused | **18 passed** |
| DEMO-AUTH-01 exact | **8 passed** |
| DEMO-FIXTURE-00 exact/live | **7 passed** |
| DEMO-01/02 integration baseline | **34 passed, 1 expected loopback skip** |
| School/Core/real-layer/HERO superset | **76 passed** (covers the required 54-pass selection) |
| ROAD-01 through ROAD-05 | **199 passed** |
| Exact detached GEN-FINAL | **10 passed** |
| BUILD-10/11/11A/12 | **87 passed, 2 documented historical stage-local failures** |

The two BUILD failures are the unchanged expected assertions that (a) demand BUILD-11A's exact
historical changed-file set and (b) demand BUILD-11A as the current branch's direct parent. They are
not functional failures and are identical in kind to the predecessor's documented baseline. No new
functional regression occurred.

## 19. Static/security gates

Candidate gates:

- Ruff lint over the focused test and changed runtime module, plus the server entrypoint with its
  three inherited unused-import warnings excluded;
- Ruff format check over the newly authored test and changed runtime module; the two-line server
  wiring is formatter-compatible, while formatting that full legacy entrypoint would create a
  broad unrelated rewrite under the current Ruff version;
- repository JSON parse and the focused closed-record validator;
- frozen School/ROAD/BUILD JSON Schema suites;
- deterministic authorization/fixture/plan/bundle/receipt/QA/provenance hash checks;
- inline frontend JavaScript syntax and live MapLibre execution;
- unified API GET/POST/error-path integration checks;
- existing OpenAPI YAML parse (the standalone unified demo endpoint is outside that reference API);
- secret/private-key token scan over exact changed scope;
- frozen ancestor/tag and diff immutability checks;
- controlled fixture before/after SHA-256;
- production-reachable stub scan;
- `git diff --check` and exact changed-file review.

Result: **PASS**. No credential or private-key material was introduced.

## 20. Controlled fresh-clone reproduction

The candidate/final SHA was reproduced from a fresh canonical clone by:

1. checking out the exact candidate SHA;
2. supplying the exact ignored fixture package and verifying its SHA-256;
3. verifying deterministic School authorization reproduction/equality;
4. launching the canonical port-8080 runtime;
5. executing and verifying School;
6. recreating the exact ROAD execution/observation and verifying controlled geometry/lineage;
7. replaying BUILD and checking activation false;
8. checking browser/API-visible results and focused retry tests;
9. verifying no external-data substitution and no unrelated persisted state requirement.

Public fixture redistribution is not required. Transient School/ROAD executions and visual QA are
generated under ignored runtime paths and are not required as committed Git state.

Fresh-clone reproduction: **PASS**.

## 21. Final accounting

| Item | Count/result |
|---|---:|
| External data substitutions | 0 |
| Production-reachable demo stubs | 0 |
| Controlled fixture modifications | 0 |
| Frozen implementation/semantic changes | 0 |
| Runtime/source integration files modified | 3 |
| New capabilities | 0 |
| Authorization weakening | 0 |
| Browser acceptance | PASS |
| Controlled fresh clone | PASS |
| Final worktree | clean after evidence commit/push verification |
| DEMO-FINAL readiness | READY |

The terminal result is therefore:

**PASS — NMA CONTROLLED END-TO-END DEMO ACCEPTED**

Recommendation:

**READY FOR DEMO-FINAL — NMA CONTROLLED DEMO FREEZE**

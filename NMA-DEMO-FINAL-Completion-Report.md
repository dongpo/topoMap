# DEMO-FINAL — NMA Controlled Demo Freeze Completion Report

## 1. Verdict

**PASS — NMA v1.0 CONTROLLED DEMO FROZEN**

This verdict is final only together with the terminal handoff's post-commit proof: the canonical
freeze branch, annotated-tag object and peeled target, local/upstream/remote equality, fresh
detached-tag reproduction, and clean canonical worktree. Those Git identities cannot be embedded
in the commit they identify; the terminal handoff is their authority.

## 2. Canonical identity

| Item | Identity |
|---|---|
| Repository | `https://github.com/dongpo/topoMap.git` |
| DEMO-02 Retry predecessor | `b80ea93e5e750948827bfa46fef9fdc1b1352305` |
| Accepted predecessor verdict | `PASS — NMA CONTROLLED END-TO-END DEMO ACCEPTED` |
| DEMO-FINAL commit | peeled target of annotated tag `nma-demo-v1.0-final` |
| Freeze branch | canonical `freeze/demo-final-<short-FINAL_SHA>` matching the tag target |
| Annotated tag | `nma-demo-v1.0-final` |
| Tag object/target | recorded by the terminal handoff after tag creation |
| Equality | local/upstream/remote equality recorded by the terminal handoff |

The final commit cannot embed its own content-addressed SHA, its SHA-derived branch suffix, or the
future annotated-tag object without changing those identities. This report therefore follows the
repository's established non-self-referential freeze convention: the peeled annotated-tag target
is the final SHA authority, the canonical branch suffix is derived from it, and the terminal
handoff records exact post-commit objects and equality.

## 3. Exact change scope

1. `NMA-DEMO-FINAL-Completion-Report.md`
2. `data/specifications/nma-demo-final-freeze-manifest-v1.0.json`
3. `tests/test_demo_final_controlled_freeze.py`

Production/runtime, School, ROAD, BUILD, GraphRAG, mapping-rule, controlled-fixture,
authorization-semantics, and generic-architecture changes: **0**.

## 4. Manifest

| Item | Value |
|---|---|
| Contract | `nma.demo-final-freeze/1.0` |
| Path | `data/specifications/nma-demo-final-freeze-manifest-v1.0.json` |
| Canonical self-hash | `a4ef21b45f94118661448ad33bd797566c82e72e5090c553b066675e14fa8001` |
| Serialization | deterministic Unicode-preserving sorted-key canonical JSON for self-hash |

## 5. Frozen evidence chain and architecture

| Baseline | Exact SHA / tag |
|---|---|
| DEMO-00 | `37c8c98e17280e6b89ba1470fc6e176e7fb00fb4` |
| DEMO-01 | `2d382a46585faa89311ea6a5502923464ace7758` |
| DEMO-FIXTURE-00 | `00bd681f2cc5f42873053f37b85724aefc8bec03` |
| DEMO-AUTH-01 | `aa3a59ddececa1bc8b893058febe5cb43d307656` |
| DEMO-02 Retry | `b80ea93e5e750948827bfa46fef9fdc1b1352305` |
| GEN-FINAL | `380cc6ea2a4498ce83690521c933accfd918818e`; `nma-generalization-v1.0-final` |
| CORE-FINAL | `5eb138ae7686502431587743ebce9ddf92c5a799` |
| School Hero | `56f99eb9ae63272a68accac3041fb10eacefb986` |
| ROAD-FINAL | `325c70d5335f57c43a8af85822db25032aa225c3` |
| BUILD-FINAL | `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7`; `nma-build-v1.0-final` |

Failed DEMO-02 and DEMO-01A/01B remain explicitly historical evidence only. They are not members
of the manifest's authoritative successful-path predecessor chain.

## 6. Controlled School fixture

| Property | Exact commitment |
|---|---|
| Fixture identity | `nma-demo-fixture:school:sha256:77802b44b97c6687bc626d257e14b57c3d7427949a65942fa721d05bb79fc12d` |
| Aggregate SHA-256 | `77802b44b97c6687bc626d257e14b57c3d7427949a65942fa721d05bb79fc12d` |
| Layers | `J01_MARK`, `J13_MARK`, `J17_MARK`, `K01_MARK`, `K02_MARK`, `K14_MARK` |
| Target | `TERRAINID=9920103`; valid Point geometry; unique IDs; labels present |
| Distribution | `0 + 1 + 0 + 12 + 1 + 1 = 15` |
| CRS | `TWD97[2020]_TM121` |

The manifest freezes every `.cpg`, `.dbf`, `.prj`, `.shp`, and `.shx` component hash for all six
layers. Raw fixture bytes remain ignored, untracked, and unredistributed.

## 7. Controlled ROAD fixture

| Property | Exact commitment |
|---|---|
| Fixture identity | `nma-demo-fixture:road:sha256:dc82db8bfc96dd6ab16b3206866e000459b9fd59a8f6d44602fcf06586b1ae79` |
| Package | `K14_ROAD.{shp,shx,dbf,prj,cpg}`; all component hashes frozen in the manifest |
| Features / CRS | 196 / `TWD97[2020]_TM121` |
| Ordered targets | `K0000004671`, `K0000004913`, `K0000005348` |
| Vertices | `4 / 3 / 4` |
| Geometry | finite, valid, simple, contiguous LineStrings |
| Semantics | class `9420400`, route `縣126`, name `中山街` |

Coordinate-array and source-geometry SHA-256 commitments match ROAD-04/05. Private coordinate
arrays are not published.

## 8. School demo authorization

| Property | Exact value |
|---|---|
| Authorization ID | `authorization-school-demo-b4ecdbfc35ecaf73293ed497` |
| Authorization hash | `d5546bd1b2176a4ad287acb1c78740ce79a90db76d05739dc871267d901dac67` |
| Human approval | approved |
| Binding | exact controlled School fixture/domain/plan/scope |
| Validation/consumption | PASS; linked to `exec-8d174b62fb63189987eafdb6` |
| Historical HERO-03 reused | false |

Historical `authorization-school-blue` / `432c3561…8d9d` remains unchanged and distinct.

## 9. Canonical runtime

```text
PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 8080
```

- Demo URL: `http://127.0.0.1:8080/nmaAgentDemoV1.html?basemap=local`
- Unified API: `http://127.0.0.1:8080/api/nma/runtime`
- `nmaAgentDemoV1.html`: `8921b61c…23ffbd`
- `scripts/run_nma_agent_server.py`: `792f3921…6db95`
- `src/nma/unified_runtime.py`: `ba1eedaa…8754`

These are the exact accepted DEMO-02 Retry runtime/integration bytes.

## 10. Accepted scenarios

### Scenario S — School

Exact controlled fixture, GraphRAG School nodes, plan `plan-8d174b62fb63189987eafdb6`, accepted
demo authorization, execution `exec-8d174b62fb63189987eafdb6`, 15-point data, QA/provenance, and
official blue School symbol with labels remain frozen and accepted.

### Scenario R — ROAD

Exact K14 fixture, frozen ROAD evidence/nodes, plan `road-plan-cd434d50bd5b49a012bd1e10`,
execution `road-exec-33766f336d9cc18eb2ac159e`, exact `4/3/4` geometry, QA/provenance, and
line-following `中山街` portrayal remain frozen and accepted.

### Scenario B — BUILD

Accepted BUILD execution/replay `build-05-demo-exec-b8b5ecd54954b190eb8cda39`, package
verification/provenance, boundary/hatch portrayal, and `held-not-requested` activation remain
frozen. Automatic production activation is **false**.

GraphRAG/rule evidence and mapping-rule alignment are preserved exactly. Retrieved knowledge does
not become authorization, and the BUILD scenario does not add an unsupported GraphRAG claim.

## 11. DEMO-A1–A12

| Criterion | Result |
|---|---|
| A1 Single Entry Point | PASS |
| A2 User Intent | PASS |
| A3 Domain Routing | PASS |
| A4 Real Planning | PASS |
| A5 Authorization | PASS |
| A6 Real Execution | PASS |
| A7 Observable Result | PASS |
| A8 Map Result | PASS |
| A9 Verification | PASS |
| A10 Provenance | PASS |
| A11 Fail-Closed | PASS |
| A12 Controlled Reproducibility | PASS |

**DEMO-A6 — PASS**

**DEMO-A8 — PASS**

## 12. Safety accounting

| Item | Count/result |
|---|---:|
| External-data substitutions | 0 |
| Production-reachable demo stubs | 0 |
| Controlled fixture modifications | 0 |
| Frozen semantic changes | 0 |
| Runtime/School/ROAD/BUILD source changes | 0 |
| GraphRAG/mapping-rule changes | 0 |
| Authorization/GEN contract changes | 0 |
| BUILD automatic activation | false |

## 13. Browser reverification

The exact launch command and canonical URL in section 9 were used with the Codex in-app browser.

- School: **PASS** — exact request/plan/authorization/execution were visible; the map rendered the
  approved blue School flag and labels; the envelope committed to 15 features; a separate verify
  request returned `verified` QA and provenance.
- ROAD: **PASS** — exact request/plan/authorization/execution/receipt were visible; the map rendered
  `中山街` following the controlled line path; a separate verify request returned exact accepted QA
  `8f31ecb2…464a82` and provenance `130a24e1…bc70`.
- BUILD: **PASS** — accepted boundary/hatch polygon was visible; observation, frozen-package
  verification, receipt, and content-addressed provenance were visible; activation remained
  `held-not-requested` and automatic activation false.
- Browser console errors/warnings: **0**.

No pixel-perfect claim is added.

## 14. Regression and static/security verification

| Suite / gate | Result |
|---|---:|
| DEMO-FINAL DF-01–DF-14 | **14 passed** |
| DEMO-02 Retry focused | **18 passed** |
| DEMO-AUTH-01 | **8 passed** |
| DEMO-FIXTURE-00 | **7 passed** |
| DEMO integration baseline | **34 passed, 1 expected loopback skip** |
| School/Core accepted selection | **76 passed** |
| ROAD-01 through ROAD-05 | **199 passed** |
| Exact detached GEN-FINAL | **10 passed** |
| BUILD-10/11/11A/12 | **87 passed, 2 documented historical stage-local failures** |
| Ruff lint / format check | PASS |
| Repository JSON parse / inline Draft 2020-12 manifest schema | PASS |
| Deterministic manifest/authorization/fixture/evidence hashes | PASS |
| Frontend JavaScript syntax / live runtime | PASS |
| OpenAPI YAML parse (`3.1.0`, 8 paths) / unified API integration | PASS |
| Credential/private-key scan of exact scope | PASS |
| Frozen artifact/runtime identity and fixture hashes | PASS |
| Production-reachable stub scan | PASS — 0 |
| Git diff scope / `git diff --check` | PASS |

The two BUILD assertions are exactly the accepted historical failures: BUILD-11A demands its old
stage-local changed-file set, and BUILD-12 demands BUILD-11A as the current direct parent. No new
functional failure occurred, and they were not repaired here.

## 15. Fresh tagged reproduction and publication

Post-commit publication and fresh reproduction use the exact annotated tag and controlled inputs
specified here. The terminal handoff records:

- final DEMO-FINAL SHA and `freeze/demo-final-<short-FINAL_SHA>` branch;
- annotated tag object and exact peeled target;
- local/upstream/canonical remote equality;
- detached checkout equality to the final SHA;
- manifest self-hash and fixture package/hash verification;
- exact School authorization verification;
- School execution/verification, ROAD exact geometry/verification, and BUILD replay/activation hold;
- DEMO-FINAL integrity suite, no external substitution, no production-reachable stub, and final
  clean worktree.

Fresh tagged reproduction: **PASS**, with exact post-commit identities supplied by the terminal
handoff under the repository's non-self-referential freeze convention.

## 16. Reproduction boundary

The frozen reproduction model is:

```text
canonical repository
+ exact controlled School fixture package
+ exact controlled ROAD fixture package
+ fixture hash verification
+ accepted School demo authorization
+ documented runtime launch
```

This freezes a controlled research demonstration. It does not claim arbitrary public-data
reproducibility, arbitrary ingestion/schema/CRS/topology repair, universal domain generalization,
or pixel-perfect rendering.

## 17. NMA-FINAL gate

**READY FOR NMA-FINAL — INTEGRATED REFERENCE IMPLEMENTATION RELEASE FREEZE**

Architecture, generalization, unified runtime acceptance, controlled-demo acceptance, and the
controlled-demo freeze are now established. NMA-FINAL is not begun here.

Final worktree: clean, with exact status recorded by the terminal handoff after publication and
fresh-tag reproduction.

# NMA-FINAL — Integrated Reference Implementation Release Freeze

## 1. Final verdict and status

**PASS — NMA v1.0 REFERENCE IMPLEMENTATION FINALIZED AND FROZEN**

**NMA v1.0 COMPLETE**

This verdict is final together with the terminal handoff's post-commit proof of the exact final
commit, SHA-derived freeze branch, annotated-tag object and target, canonical remote equality,
fresh detached-tag reproduction, and clean canonical worktree.

## 2. Canonical repository and release identity

| Item | Exact identity / authority |
|---|---|
| Repository | `https://github.com/dongpo/topoMap.git` |
| Exact DEMO-FINAL predecessor | `05af154a14e781f20b5cf2d3996eac8191875b0f` |
| Predecessor branch | `freeze/demo-final-05af154` |
| Predecessor annotated tag | `nma-demo-v1.0-final` |
| Predecessor tag object | `794a71ab8fdf56c4504f85521f7a063a9acb63f9` |
| NMA-FINAL commit / tag target | peeled target of annotated tag `nma-v1.0-final` |
| Freeze branch | canonical `freeze/nma-final-<short-FINAL_SHA>` matching the peeled tag target |
| Annotated tag | `nma-v1.0-final` |
| Tag object | exact object recorded by the terminal handoff after tag creation |
| Local/upstream/remote equality | exact values recorded by the terminal handoff after publication |

Git commit identities are content-addressed: a commit cannot embed its own SHA, its SHA-derived
branch suffix, or the future annotated-tag object without changing those identities. This release
therefore uses the repository's established non-self-referential freeze convention. The peeled
`nma-v1.0-final` target is the final SHA authority; the canonical branch suffix derives from it;
the terminal handoff records the exact post-commit identities and equality.

## 3. Exact committed-file list and no-functional-change gate

1. `NMA-FINAL-Completion-Report.md`
2. `data/specifications/nma-v1.0-final-release-manifest.json`
3. `tests/test_nma_final_release_integrity.py`

| Frozen area | Modifications |
|---|---:|
| Production runtime | 0 |
| Core | 0 |
| School | 0 |
| ROAD | 0 |
| BUILD | 0 |
| GraphRAG | 0 |
| Mappings/rules | 0 |
| Generic contracts | 0 |
| Controlled fixtures | 0 |
| Authorization semantics | 0 |

The final diff is release evidence only.

## 4. Release manifest

| Item | Value |
|---|---|
| Contract | `nma.final-release/1.0` |
| Path | `data/specifications/nma-v1.0-final-release-manifest.json` |
| Canonical self-hash | value of `canonical_manifest_sha256`; reproduced in NF-14 and recorded exactly in the terminal handoff |
| Serialization | deterministic Unicode-preserving, sorted-key canonical JSON with the self-hash field excluded from its hash basis |

The manifest hashes this report and the focused integrity test. Its own canonical self-hash is
therefore intentionally not copied into this report, avoiding a circular report↔manifest hash.
The terminal handoff supplies the exact reproducible self-hash.

## 5. Required frozen identity chain

| Freeze | Exact commit | Annotated tag / manifest |
|---|---|---|
| CORE-FINAL | `5eb138ae7686502431587743ebce9ddf92c5a799` | `nma-core-v1.0-final` |
| School Hero | `56f99eb9ae63272a68accac3041fb10eacefb986` | `freeze/hero-final-school-hero-56f99eb` |
| ROAD-FINAL | `325c70d5335f57c43a8af85822db25032aa225c3` | `nma-road-v1.0-final` |
| BUILD-FINAL | `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7` | `nma-build-v1.0-final` |
| GEN-FINAL | `380cc6ea2a4498ce83690521c933accfd918818e` | `nma-generalization-v1.0-final`; manifest `71683e0486b4ff952e41ad9cd98e6e0405c61f07e09d40b553540a0203c874f1` |
| DEMO-FINAL | `05af154a14e781f20b5cf2d3996eac8191875b0f` | `nma-demo-v1.0-final`; object `794a71ab8fdf56c4504f85521f7a063a9acb63f9`; manifest `a4ef21b45f94118661448ad33bd797566c82e72e5090c553b066675e14fa8001` |

Before artifact creation, local, upstream, and canonical remote DEMO-FINAL refs were equal and the
starting worktree was clean. All listed frozen identities were exact ancestors of DEMO-FINAL; all
canonical frozen branches and annotated-tag objects/targets matched the canonical remote.

## 6. NMA v1.0 release claim and architecture

NMA v1.0 is a reference implementation of an AI-agent-assisted national mapping architecture in
which controlled geospatial feature-production tasks are interpreted through Agent/GraphRAG-
supported cartographic knowledge, planned, authorized, executed through domain-specific
production paths, verified, provenance-linked, and presented through a unified runtime.

```text
User / Cartographer
        ↓
Unified NMA Runtime
        ↓
Agent Intent Interpretation
        ↓
GraphRAG / Cartographic Knowledge Retrieval
        ↓
Planning
        ↓
Authorization
        ↓
Generic Lifecycle / Domain Adapter Boundary
        ↓
Domain Execution
   ├── School
   ├── ROAD
   └── BUILD
        ↓
Observation / Derived Result
        ↓
Verification / QA
        ↓
Receipt / Provenance
        ↓
Map / User-visible Result
```

Cross-cutting frozen concerns are canonical Core identity, deterministic artifact identity,
authorization, auditability, provenance, fail-closed mutation safety, and domain-specific
semantics/geometry/portrayal. Each domain retains ownership of semantics, geometry, portrayal,
rollback, and activation.

## 7. Explicit non-claims

NMA v1.0 does not claim arbitrary open-data ingestion, unrestricted data onboarding, universal
schema harmonization, automatic CRS or topology repair, universal feature-domain coverage,
unrestricted autonomous production authority, automatic conformance of all future map features,
removal of human cartographic authority, production-quality AGI, or pixel-perfect equivalence.

This is a controlled reference implementation.

## 8. Canonical runtime identity and demo launch

| File | SHA-256 |
|---|---|
| `nmaAgentDemoV1.html` | `8921b61c9d7181ec97a38174f82f12fdd8a14493e0dd0e5dd5b368aacd23ffbd` |
| `scripts/run_nma_agent_server.py` | `792f3921b1055b3092f2ae047722f37d0c6c84a19d50bfd745ca001abfc6db95` |
| `src/nma/unified_runtime.py` | `ba1eedaae92674df6d564ab3ff8a76950d4bd2b118cf0ba3445de47116fb8754` |

Launch command:

```text
PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 8080
```

- Host: `127.0.0.1`
- Port: `8080`
- Canonical browser URL: `http://127.0.0.1:8080/nmaAgentDemoV1.html?basemap=local`
- Unified API route: `http://127.0.0.1:8080/api/nma/runtime`

## 9. Canonical generic-contract identities

| Artifact | SHA-256 |
|---|---|
| `src/nma/core/identity.py` | `d9c4ac0d0d385f6942c552a0b2ffc4c12b3deb0ee876d569aeadc036b1a92e78` |
| `schemas/generic-lifecycle-envelope-v1.0.schema.json` | `1ba0395fcec1b2234f05406acb9dcfcd066c6af79c773cc50dec201b8eb36bad` |
| `schemas/generic-domain-adapter-capability-v1.0.schema.json` | `79114463a7be4eaf5c1b83c5b98535068e798973864113933aca9630f8e72ffa` |
| `schemas/generic-contract-interface-closure-v1.0.schema.json` | `111e192611c66894e2e863fe32905843e3771737c07c3a5142768b4f388204b3` |

## 10. Controlled fixture reproduction contract

NMA v1.0 code and release evidence are canonical public repository artifacts. The controlled
School and ROAD fixture packages are supplied separately and validated by exact cryptographic
identities before demo execution. This is the canonical v1.0 reproducibility model.

The separately supplied archive is
`data/datasets/112年多維度SHP成果_0502.zip`, size `12,822,898` bytes, SHA-256
`4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.
It remains ignored, untracked, and unredistributed.

### School commitment

- Identity: `nma-demo-fixture:school:sha256:77802b44b97c6687bc626d257e14b57c3d7427949a65942fa721d05bb79fc12d`
- Six layers: `J01_MARK`, `J13_MARK`, `J17_MARK`, `K01_MARK`, `K02_MARK`, `K14_MARK`
- `TERRAINID=9920103`; 15 valid Point features; distribution `0/1/0/12/1/1`
- CRS: `TWD97[2020]_TM121`; unique identifiers and labels present

### ROAD commitment

- Identity: `nma-demo-fixture:road:sha256:dc82db8bfc96dd6ab16b3206866e000459b9fd59a8f6d44602fcf06586b1ae79`
- Package: `K14_ROAD.{shp,shx,dbf,prj,cpg}`; 196 features
- Ordered targets: `K0000004671`, `K0000004913`, `K0000005348`
- Exact vertex counts: `4 / 3 / 4`; finite, valid, simple, contiguous LineStrings
- Class `9420400`; route `縣126`; name `中山街`

All per-component and geometry hashes are frozen in the release manifest through the exact
DEMO-FINAL manifest commitment.

## 11. Human authority and School authorization

| Item | Exact value |
|---|---|
| Authorization ID | `authorization-school-demo-b4ecdbfc35ecaf73293ed497` |
| Authorization hash | `d5546bd1b2176a4ad287acb1c78740ce79a90db76d05739dc871267d901dac67` |
| Human approval | approved |
| Bound execution | `exec-8d174b62fb63189987eafdb6` |

The Agent does not receive unrestricted production authority. Unauthorized or failed requests
fail closed. BUILD automatic production activation remains false. NMA v1.0 is accurately
characterized as **AI-agent-assisted / governed autonomous execution**.

## 12. Accepted School, ROAD, and BUILD scenarios

### School — PASS

The controlled six-layer fixture, `TERRAINID 9920103`, 15 Point features, accepted authorization,
GraphRAG/rule evidence, canonical execution, verified QA/provenance, official blue School symbol,
labels, and visible map remain exact.

### ROAD — PASS

The controlled K14 package, 196 features, exact frozen segments and `4/3/4` geometry, planning,
execution, rule-aligned portrayal, line-following `中山街`, verification/provenance, and visible map
remain exact.

### BUILD — PASS

The accepted controlled/replay path, boundary/hatch portrayal, browser result, verification and
provenance remain exact. Activation is `held-not-requested`; automatic production activation is
false.

## 13. Agent, GraphRAG, and mapping-rule alignment

GraphRAG provides relevant cartographic knowledge/rule retrieval that is traceably aligned with
Agent planning and execution in the accepted controlled scenarios. Retrieval is not authorization,
does not automatically activate rules, and is not claimed to autonomously determine every action.

- School: exact reviewed knowledge nodes and fixture attributes remain linked through plan,
  authorization, execution, QA, and provenance.
- ROAD: frozen evidence, semantics, geometry, portrayal, QA, and provenance remain aligned.
- BUILD: accepted frozen execution/replay and portrayal alignment are preserved; no separate
  GraphRAG claim is added.

Mapping-rule alignment status: **PASS**.

## 14. DEMO-A1–A12

| Criterion | Status |
|---|---|
| DEMO-A1 Single Entry Point | PASS |
| DEMO-A2 User Intent | PASS |
| DEMO-A3 Domain Routing | PASS |
| DEMO-A4 Real Planning | PASS |
| DEMO-A5 Authorization | PASS |
| DEMO-A6 Real Execution | PASS |
| DEMO-A7 Observable Result | PASS |
| DEMO-A8 Map Result | PASS |
| DEMO-A9 Verification | PASS |
| DEMO-A10 Provenance | PASS |
| DEMO-A11 Fail-Closed | PASS |
| DEMO-A12 Controlled Reproducibility | PASS |

## 15. Verification, provenance, and safety

| Gate | Result |
|---|---:|
| Verification / QA | PASS |
| Receipt / provenance linkage | PASS |
| Fail-closed mutation safety | PASS |
| External-data substitutions | 0 |
| Production-reachable demo stubs | 0 |
| Frozen semantic modifications | 0 |
| Controlled fixture modifications | 0 |
| BUILD automatic activation | false |

## 16. Regression verification

| Suite | Result |
|---|---:|
| NMA-FINAL NF-01–NF-14 | **14 passed** |
| DEMO-FINAL | **14 passed** |
| DEMO-02 Retry | **18 passed** |
| DEMO-AUTH-01 | **8 passed** |
| DEMO-FIXTURE-00 | **7 passed** |
| DEMO integration | **34 passed, 1 expected loopback skip** |
| School/Core | **76 passed** |
| ROAD | **199 passed** |
| GEN-FINAL | **10 passed** |
| BUILD baseline | **87 passed, 2 documented historical stage-local assertions** |

The two BUILD assertions are the unchanged historical exact-stage-scope and direct-parent checks.
They are not functional regressions and were not repaired in NMA-FINAL.

## 17. Browser reverification

The command, host, port, URL, and API route in section 8 were used against the release candidate.

- School: **PASS** — controlled request, GraphRAG/rule evidence, planning, explicit authorization,
  execution, blue official symbol, labels, QA/provenance, and map result were preserved.
- ROAD: **PASS** — controlled request, planning, execution, exact geometry, line-following
  `中山街`, QA/provenance, and map result were preserved.
- BUILD: **PASS** — accepted controlled/replay result, boundary/hatch portrayal, QA/provenance,
  and activation hold were preserved.
- Browser console errors/warnings: **0**.

No pixel-perfect claim is made.

## 18. Fresh tagged release reproduction

The terminal handoff records the exact fresh-clone path and post-publication proof:

1. cloned canonical origin without dependence on the canonical worktree;
2. fetched and checked out annotated `nma-v1.0-final` detached;
3. matched the peeled final SHA;
4. reproduced the final, GEN-FINAL, and DEMO-FINAL manifest self-hashes;
5. verified every frozen predecessor branch/tag identity;
6. supplied the exact controlled archive separately and verified its size/hash and School/ROAD
   commitments;
7. reproduced the School authorization;
8. launched the canonical runtime and reproduced School, ROAD, and BUILD;
9. reran NMA-FINAL and representative regression suites;
10. reconfirmed zero substitutions, zero production stubs, and false BUILD auto-activation.

Fresh tagged reproduction: **PASS**, with exact identities in the terminal handoff.

## 19. Final Git and worktree status

Publication uses a normal push only: no merge, no force-push, no existing branch overwrite, and no
tag replacement. Exact final SHA, `freeze/nma-final-<shortsha>`, tag object/target, local/upstream/
remote equality, and the final clean worktree are recorded by the terminal handoff.

Final canonical worktree: **clean** after publication and detached-tag reproduction.

## 20. Post-v1.0 recommendations

All future work is post-v1.0. Candidate work includes RIVERL independent-domain validation,
additional domains, richer GraphRAG and autonomous-reasoning evaluation, arbitrary-data onboarding
architecture, semantic interoperability, production deployment, UX improvements, broader
cartographic QA, and a benchmark/evaluation framework. None is started by NMA-FINAL.

NMA v1.0 is frozen at the proven evidence boundary.

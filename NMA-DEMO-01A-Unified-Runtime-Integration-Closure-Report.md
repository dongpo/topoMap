# NMA DEMO-01A — Unified Runtime Integration Closure Report

**Repository:** `https://github.com/dongpo/topoMap.git`

**Branch:** `demo/demo-01a-unified-runtime-integration-closure`

**Exact DEMO-02 predecessor:** `daf4a7b7ae4d2f95de2d23af561843ef3de18232`

## 1. Verdict

> **FAIL — PUBLIC DATA BLOCKER**

The successful terminal verdict `PASS — UNIFIED NMA RUNTIME INTEGRATION CLOSED` is not awarded.
Neither demonstrated blocker can be closed from canonical public repository evidence without
fabricating or redistributing domain data:

1. School has a real frozen executor, but the public checkout has neither a compatible canonical
   execution fixture nor a canonical HERO-03 authorization artifact or issuer.
2. ROAD has verified frozen lineage and exact geometry commitments, but its public frozen artifacts
   omit the coordinate payload required by a representation-only GeoJSON serializer.

The task required a fail-closed stop if public School execution or ROAD geometry could not be
exposed without private data, synthetic substitution, or frozen semantic change. No closure code
was therefore implemented.

## 2. Repository and predecessor gate

All mandatory checks passed before branch creation:

| Check | Result |
|---|---|
| Fetch/push origin | `https://github.com/dongpo/topoMap.git` |
| Starting branch | `demo/demo-02-end-to-end-demo-acceptance` |
| Starting HEAD | `daf4a7b7ae4d2f95de2d23af561843ef3de18232` |
| Local DEMO-02 branch | exact predecessor |
| Configured upstream | `origin/demo/demo-02-end-to-end-demo-acceptance` |
| Upstream SHA | exact predecessor |
| Canonical remote ref after fetch | exact predecessor |
| Starting worktree | clean |

The DEMO-01A branch was created directly from the exact predecessor only after these checks passed.

## 3. Branch and final Git identity

- Branch: `demo/demo-01a-unified-runtime-integration-closure`.
- Predecessor: `daf4a7b7ae4d2f95de2d23af561843ef3de18232`.
- Final local/upstream/remote equality is verified after the report commit and normal push.
- The containing commit cannot embed its own SHA without changing that SHA; the exact equality is
  therefore recorded in the post-push task handoff.
- No merge, tag, amend of frozen history, or force-push is performed.

## 4. Exact changed-file list

The bounded terminal diff contains one report only:

- `NMA-DEMO-01A-Unified-Runtime-Integration-Closure-Report.md`

Runtime code, server code, browser code, tests, schemas, public fixtures, frozen artifacts, and BUILD
files changed: **0**.

## 5. DEMO-02 evidence preservation

The authoritative DEMO-02 findings remain intact:

- School remains capability-only publicly.
- ROAD retains verified frozen lineage but no public renderable geometry.
- BUILD retains its accepted public replay, provenance, and browser-map path.
- DEMO-A6 Real Execution remains failed.
- DEMO-A8 Map Result remains failed.
- The unknown-feature-target correction remains present and tested.
- No private archive was required for the accepted DEMO-02 paths or this audit.

No DEMO-02 record, report, fixture, assertion, or verdict was rewritten.

## 6. School original blocker

`SchoolRuntimeAdapter` exposes capability metadata for public preview/replay. Canonical execution is
delegated to `SchoolHeroExecutionEngine.execute_by_id`, which consumes a stored complete HERO-03
authorization and invokes the frozen real-layer path.

The server currently binds that executor to
`data/datasets/112年多維度SHP成果_0502.zip`, an ignored private archive. The public checkout does not
contain a production HERO-03 issuer or a tracked complete School execution authorization.

## 7. Canonical School execution path inspected

| Stage | Canonical implementation |
|---|---|
| Capability/profile | `nma.feature_profile_adapters.school_feature_profile` |
| Planning | `SchoolHeroExecutionEngine.build_plan` and `_real_layer_plan` |
| Authorization storage | `ExecutionAuthorizationStore` |
| Authorization validation | `ExecutionAuthorizationVerifier.verify` |
| Execution | `SchoolHeroExecutionEngine.execute_by_id` / `execute` / `_execute_atomic` |
| Real geometry materialization | `nma.real_layer.execute_real_layer` |
| Runtime portrayal | `SchoolHeroExecutionEngine._build_bundle` |
| Receipt | `SchoolHeroExecutionEngine._build_receipt` |
| Observation | `SchoolHeroExecutionEngine.observe` |
| Verification/provenance | `SchoolHeroVerifier.verify` |
| Unified integration | `SchoolRuntimeAdapter` |

The canonical executor is real and unchanged. The blocker is not missing School implementation.

## 8. School public fixture compatibility

The only tracked public School Shapefile is
`data/datasets/authoritative/school-points/SCHOOL_POINT.*`. Its tracked inspection record declares:

- dataset label: `Bundled synthetic school points`;
- `synthetic: true`;
- layer: `SCHOOL_POINT`;
- feature count: `12`;
- geometry: `Point`;
- CRS: `EPSG:3826`.

The frozen canonical School path requires:

- exactly six source layers: `J01_MARK`, `J13_MARK`, `J17_MARK`, `K01_MARK`, `K02_MARK`, `K14_MARK`;
- exact output feature count: `15`;
- a source archive SHA bound into the HERO-03 authorization;
- a complete stored `nma.symbol-edit-authorization/1.0` authorization;
- a valid human approval and full upstream lineage for provenance verification.

The public 12-feature, one-layer synthetic fixture cannot satisfy those frozen requirements. Renaming,
duplicating, or repartitioning its records and minting a matching authorization would create a new
demo fixture/authority path, not expose existing canonical evidence.

## 9. School closure implementation

**Not implemented — fail-closed.**

No parallel School executor, fixture packager, authorization issuer, static authorization override,
hard-coded result, synthetic success envelope, or runtime identity substitute was created.

## 10. School canonical execution evidence

Canonical execution capability is proven by the frozen implementation and its existing domain tests,
but no valid public execution can be performed from this checkout. The production issuer is absent,
and the compatible reviewed archive is private.

DEMO-01A therefore does not claim a new School plan, authorization, execution, or result identity.

## 11. School verification and provenance evidence

`SchoolHeroVerifier` verifies canonical execution artifacts when supplied the matching execution
storage and source archive. A fresh public clone cannot produce those inputs. No fake QA hash,
provenance hash, receipt reference, or observation identity was populated.

## 12. School visualization evidence

The public synthetic 12-point dataset can be visualized by legacy/public inspection surfaces, but it
is not a canonical School Hero execution result. It was not substituted into the unified execution
envelope. School map closure remains unachieved.

## 13. ROAD original blocker

`RoadRuntimeAdapter._replay` validates the frozen ROAD execution plan, receipt, runtime bundle, and
their content-addressed linkage. The bundle references
`/api/road/executions/road-exec-33766f336d9cc18eb2ac159e/data`, but the corresponding GeoJSON is not
tracked in the public repository.

## 14. Canonical ROAD artifacts inspected

The tracked frozen evidence includes:

- plan: `nma-road-hero-road-04-golden-plan-v1.0.json`;
- derived portrayal: `nma-road-hero-road-04-golden-derived-portrayal-v1.0.json`;
- runtime bundle: `nma-road-hero-road-04-golden-runtime-bundle-v1.0.json`;
- observation: `nma-road-hero-road-04-golden-observation-v1.0.json`;
- receipt: `nma-road-hero-road-04-golden-receipt-v1.0.json`;
- rollback manifest: `nma-road-hero-road-04-golden-rollback-manifest-v1.0.json`;
- ROAD-05 verification/provenance implementation and frozen reports.

These establish the authoritative execution and result lineage, but not the coordinate payload.

## 15. ROAD canonical geometry lineage

The frozen evidence records:

- execution: `road-exec-33766f336d9cc18eb2ac159e`;
- plan: `road-plan-cd434d50bd5b49a012bd1e10`;
- derived artifact: `road-derived-092adadc29954c5151ae43a7`;
- runtime bundle: `road-bundle-road-exec-33766f336d9cc18eb2ac159e`;
- observation: `road-observation-4c88e2e424168c1c712145c1`;
- receipt: `road-receipt-road-exec-33766f336d9cc18eb2ac159e`;
- runtime geometry file commitment:
  `d13096fb82a1e0588898ade94070becec531ebc07e77fe7795a3d92f8d56db08`;
- ordered segments: `K0000004671`, `K0000004913`, `K0000005348`;
- runtime geometry types: three `LineString` values;
- runtime vertex counts: `4`, `3`, `4`;
- per-geometry SHA-256 identities:
  `b7272294ba1c52c3550293465192acdff6a48a1fc0eeb401bc4f009c88749f93`,
  `bfb72e14ba6b9292d6de578b97bddf269940e9973f4e64add7b48a29dc06993f`, and
  `90c17d200b2bb85c91ff1415a90f761c6e184cc2bcfd2256476dbe1b9bcba7ad`.

These commitments prove identity and ordering but cannot be inverted into coordinates.

## 16. ROAD serialization proof

**Not possible from public evidence.**

A permitted representation-only serializer must preserve coordinate values, ordering, and geometry
type. The public frozen JSON records contain hashes and counts, not coordinate arrays. No tracked
`road-centreline-runtime.geojson` exists at the predecessor or ROAD-FINAL tree. Generating a polyline
from endpoints, screenshots, hashes, counts, or unrelated public features would violate the no
reconstruction and no synthetic geometry rules.

## 17. ROAD closure implementation and visualization evidence

**Not implemented — fail-closed.**

No ignored local runtime artifact was opened, copied, staged, or redistributed. No private archive
was opened. No demo polyline, generic geometry reconstruction, stale screenshot, or unrelated public
geometry was substituted. ROAD remains lineage-visible and geometry-unavailable publicly.

## 18. BUILD regression result

BUILD code and data changed: **0**. The existing DEMO-01 and DEMO-02 focused suites pass, including
the accepted BUILD replay, verification/provenance envelope, browser-map contract assertions, and
`automatic_build_activation == false` checks.

No BUILD semantic, execution, portrayal, authorization, or activation change was attempted.

## 19. DEMO-A6 closure evidence

**Not closed.**

- School: canonical execution remains unreachable from public repository evidence.
- ROAD: frozen canonical execution lineage remains reachable, but its result payload is absent.
- BUILD: remains accepted.

Aggregate DEMO-A6 is not a PASS candidate.

## 20. DEMO-A8 closure evidence

**Not closed.**

- School: no canonical execution result/map is publicly reproducible.
- ROAD: no public coordinate payload can be rendered.
- BUILD: existing accepted map remains unchanged.

Aggregate DEMO-A8 is not a PASS candidate.

## 21. Unified runtime result

The unified endpoint remains singular at `/api/nma/runtime`. Its dispatcher, response schema,
domain-owned adapter boundaries, canonical Core identity authority, and mutation/activation safety
are unchanged. Because the required public domain inputs are absent, the endpoint cannot truthfully
return the newly required School and ROAD result envelopes.

## 22. Negative-flow results

The unchanged DEMO-01/DEMO-02 focused suites cover and pass:

- unsupported domain;
- ambiguous domain;
- invalid request;
- unknown feature target;
- missing authorization;
- invalid authorization;
- malformed lifecycle request;
- unsupported capability/operation;
- BUILD activation safety;
- missing dependency with no fallback.

The DEMO-02 unknown-feature-target fix remains intact. No assertion was weakened.

## 23. Mutation and authorization safety

- Runtime or domain code changes: 0.
- New authority-granting paths: 0.
- Static authorization overrides: 0.
- Fallback executors: 0.
- Generic mutation paths: 0.
- Source writes or repairs: 0.
- BUILD automatic activation: false.

Failing to close the task is preferable to inventing authority or geometry.

## 24. Browser verification

Not run as closure acceptance because the prerequisite public runtime artifacts do not exist. The
unchanged browser assertions pass in the focused suites, but DEMO-01A does not claim School or ROAD
browser success from API/static tests.

## 25. Fresh public-clone reproduction

A fresh clone of `https://github.com/dongpo/topoMap.git` was checked out detached at exact predecessor
`daf4a7b7ae4d2f95de2d23af561843ef3de18232` and verified clean. Nothing was copied or linked from the
working checkout.

Observed in the fresh public clone:

- private archive: absent;
- ignored ROAD runtime directory: absent;
- tracked ROAD runtime geometry GeoJSON: absent;
- tracked complete School authorization artifact: absent;
- public School dataset: `synthetic: true`;
- public School layer: `SCHOOL_POINT`;
- public School feature count: `12`.

The blocker therefore reproduces from the canonical public repository and is not caused by local
configuration.

## 26. Focused tests

| Suite | Result |
|---|---:|
| DEMO-02 focused baseline | 20 passed |
| DEMO-01 focused baseline with loopback enabled | 15 passed |
| Combined restricted-sandbox run | 34 passed, 1 loopback-only skip |

No DEMO-01A implementation tests were added because no truthful implementation candidate exists.

## 27. Regression suites and static/security gates

The task stopped at the mandatory public-data gate before implementation. Full GEN, Core/School,
ROAD, BUILD, browser, Ruff, schema, frontend, OpenAPI, secret, and stub acceptance matrices were not
rerun as candidate gates because there is no candidate runtime diff to validate.

The unchanged focused baselines passed, and the exact diff is documentation-only. This report does
not reinterpret unrun gates as passing.

## 28. Frozen identities

| Freeze | Required identity | Verification |
|---|---|---|
| GEN-FINAL | `380cc6ea2a4498ce83690521c933accfd918818e` | exact branch and tag target |
| GEN tag | `nma-generalization-v1.0-final` | exact target |
| BUILD-FINAL | `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7` | exact branch and tag target |
| BUILD tag | `nma-build-v1.0-final` | exact target |
| CORE-FINAL | `5eb138ae7686502431587743ebce9ddf92c5a799` | exact freeze branch |
| ROAD-FINAL | `325c70d5335f57c43a8af85822db25032aa225c3` | exact freeze branch |
| School Hero | `56f99eb9ae63272a68accac3041fb10eacefb986` | exact canonical remote freeze object |

Frozen branches, tags, manifests, contracts, domain implementations, semantics, and portrayals
changed: **0**.

## 29. Private archive state

Expected path: `data/datasets/112年多維度SHP成果_0502.zip`.

Expected SHA-256: `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.

- present locally;
- ignored by `.gitignore`;
- untracked;
- unstaged;
- unextracted by DEMO-01A;
- contents and checksum uninspected by DEMO-01A;
- not opened, copied, linked, or used;
- absent from the fresh public clone.

Only path existence and ignore/tracking status were checked.

## 30. Production-reachable stub count and final worktree

Production-reachable demo stubs introduced by DEMO-01A: **0**.

Production runtime changes introduced by DEMO-01A: **0**.

The exact pre-commit diff is this report only. Final clean worktree status and exact
local/upstream/remote equality are verified after commit and push and recorded in the task handoff.

## 31. DEMO-02 Retry readiness

> **NOT READY FOR DEMO-02 RETRY — PUBLIC SCHOOL EXECUTION AND ROAD GEOMETRY EVIDENCE REQUIRED**

The required success recommendation
`READY FOR DEMO-02 RETRY — END-TO-END DEMO ACCEPTANCE` is not issued.

Safe next work must supply, through an explicitly authorized public-data publication process:

1. a public School execution fixture compatible with the frozen School executor plus a canonical
   domain-owned HERO-03 authorization artifact/issuer path; and
2. the exact canonical ROAD runtime geometry artifact whose SHA-256 is already frozen, or another
   already-canonical public artifact containing the same coordinate arrays.

After those artifacts are lawfully and canonically available, a new bounded integration task may
serialize and expose them without changing domain semantics. DEMO-02 Retry must still be a separate
full acceptance task.

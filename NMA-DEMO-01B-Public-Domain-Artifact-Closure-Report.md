# NMA DEMO-01B — Public Domain Artifact Authorization & Publication Closure Report

**Repository:** `https://github.com/dongpo/topoMap.git`

**Branch:** `demo/demo-01b-public-domain-artifact-closure`

**Exact DEMO-01A predecessor:** `9e59237296ed3baed551db2bbd565234a1b02db5`

**Audit date:** `2026-08-22` (`Asia/Taipei`)

## 1. Verdict

> **FAIL — PUBLICATION AUTHORITY OR CANONICAL PAYLOAD STILL UNAVAILABLE**

DEMO-01B cannot truthfully publish either required domain artifact:

1. School still has no tracked, executor-compatible six-layer/15-feature public fixture and no
   canonical domain-owned HERO-03 authorization artifact or already-authorized issuer path.
2. ROAD still has no tracked or otherwise identified lawful canonical public artifact containing
   the exact frozen coordinate arrays. The tracked commitments contain hashes, counts, ordering,
   and lineage, but not coordinates.

Both gates therefore fail. In accordance with the mandatory stop boundary, the only project change
is this report. No public artifact, manifest, schema, test, runtime integration, or endpoint change
was implemented.

## 2. Repository and predecessor gate

All mandatory checks completed before branch creation:

| Check | Result |
|---|---|
| Canonical fetch/push origin | `https://github.com/dongpo/topoMap.git` |
| Starting branch | `demo/demo-01a-unified-runtime-integration-closure` |
| Starting local HEAD | `9e59237296ed3baed551db2bbd565234a1b02db5` |
| Configured upstream | `origin/demo/demo-01a-unified-runtime-integration-closure` |
| Upstream SHA after fetch | exact predecessor |
| Canonical remote branch SHA | exact predecessor |
| Starting worktree | clean |
| Required predecessor report | tracked and inspected |

The DEMO-01B branch was created directly from the exact predecessor. It has no upstream and has not
been pushed. Stage, commit, push, PR, merge, and tag actions remain pending separate authorization.

## 3. Frozen identity gate

Local objects, fetched remote-tracking branches, and canonical remote refs were checked. All
canonical frozen identities are exact:

| Domain | Annotated tag object | Peeled/freeze commit | Remote freeze result |
|---|---|---|---|
| Core | `5729f2db0fc441b3eb0a22c1f76b0f6af3f368ea` | `5eb138ae7686502431587743ebce9ddf92c5a799` | exact |
| ROAD | `d60fffa873428d1ba8b308ea0d4d2028ac8431fd` | `325c70d5335f57c43a8af85822db25032aa225c3` | exact |
| School Hero | no final tag asserted | `56f99eb9ae63272a68accac3041fb10eacefb986` | canonical suffixed branch exact |
| BUILD | `1b55ff67fd670a482da74975ce41fa86df5dd71f` | `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7` | exact |
| GEN | `9ba26ff032e23f0ba5de80d809f08eb6e973bb4f` | `380cc6ea2a4498ce83690521c933accfd918818e` | exact |

`nma-build-v1.0-final` remains an annotated tag and peels to exact BUILD-FINAL. Frozen code,
contracts, manifests, semantics, portrayal, authorization boundaries, and activation state changed:
**0**.

## 4. Audit method and safety boundary

The repository audit used only tracked Git objects and a new canonical public clone. It examined:

- `git ls-files`, `git ls-tree`, `git rev-list --objects --all`, `git grep`, and tracked files;
- all fetched public refs and reachable tracked history for plausible School authorization and ROAD
  coordinate-payload paths;
- official NLSC public metadata pages, without downloading or opening any data payload.

The working checkout's private archive and ignored ROAD runtime directories were not opened,
listed, copied, hashed, extracted, serialized, or used. No content was taken from a local artifact
that would be absent from a fresh public clone. No coordinates were reconstructed or approximated.

## 5. School canonical requirements recovered

The frozen executor and closed plan schema require all of the following:

- implementation authority:
  `freeze/hero-final-school-hero-56f99eb` at
  `56f99eb9ae63272a68accac3041fb10eacefb986`;
- authorization contract: `nma.symbol-edit-authorization/1.0`;
- exactly six ordered logical source layers:
  `J01_MARK`, `J13_MARK`, `J17_MARK`, `K01_MARK`, `K02_MARK`, `K14_MARK`;
- exact output count: `15` Point features in `EPSG:4326`;
- source archive, proposal, validation, human approval, operation, baseline, plan, bundle, receipt,
  observation, verification, and provenance identities;
- `synthetic: false` and `random_coordinates: false` in materialized output provenance.

The real domain path remains
`ExecutionAuthorizationStore.load -> ExecutionAuthorizationVerifier.verify ->
SchoolHeroExecutionEngine.execute -> SchoolHeroVerifier.verify`.

## 6. School public-source finding

The only tracked public School Shapefile candidate is explicitly declared:

| Property | Tracked value |
|---|---|
| Dataset | `Bundled synthetic school points` |
| Synthetic | `true` |
| Layer | `SCHOOL_POINT` |
| Feature count | `12` |
| Geometry | `Point` |
| Source CRS | `EPSG:3826` |

It is incompatible with the frozen six-layer/15-feature contract. It was not renamed, duplicated,
repartitioned, or substituted.

No tracked public file on any reachable ref contains an executor-compatible School archive or
fixture. Public sample/inspection GeoJSON files are not canonical School Hero execution inputs and
do not establish domain publication authority.

## 7. School publication-authority finding

No tracked complete School `nma.symbol-edit-authorization/1.0` artifact exists. The only School
authorization constructor is test support (`tests/hero04_support.py`); it manufactures test inputs
and is not a production/domain issuer. Production code contains a consumer/store/verifier but no
issuer path.

Official NLSC metadata confirms that multi-dimensional base-map products exist and are supplied
through platform services or application workflows. It does not identify the repository's exact
frozen School source archive, publish the required six MARK layers as a fresh-clone fixture, grant a
repository-specific right to redistribute that exact payload, or issue the domain-owned HERO-03
execution authorization. See:

- `https://www.nlsc.gov.tw/cp.aspx?n=17087`
- `https://www.nlsc.gov.tw/cp.aspx?n=16733`

Therefore the School source and authorization gates both fail. No authorization was minted.

## 8. School artifact identities

| Artifact | Identity/status |
|---|---|
| Canonical School Hero implementation | `56f99eb9ae63272a68accac3041fb10eacefb986` |
| Required source archive commitment | `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53` |
| Required authorization artifact | unavailable publicly |
| Required compatible six-layer fixture | unavailable publicly |
| Required canonical 15-feature result | unavailable publicly |
| Tracked public candidate | rejected: synthetic, one layer, 12 features |

Because no canonical public School artifact exists, DEMO-01B assigns no new plan, authorization,
execution, result, receipt, observation, QA, or provenance identity.

## 9. ROAD canonical requirements recovered

The frozen tracked lineage is:

| Artifact | Identity |
|---|---|
| ROAD-FINAL | `325c70d5335f57c43a8af85822db25032aa225c3` |
| Execution | `road-exec-33766f336d9cc18eb2ac159e` |
| Plan | `road-plan-cd434d50bd5b49a012bd1e10` / `e51e42b955ade0d3ff5c6b8fbe00919aac4d9b9f90fe59bd548e14b7a9bf04a0` |
| Derived artifact | `road-derived-092adadc29954c5151ae43a7` / `fb8762642e4e3e633912028b18ca6aa11545117e15572839896770537a5971b6` |
| Runtime bundle | `road-bundle-road-exec-33766f336d9cc18eb2ac159e` / `33aa7c6b0d557fa9a72e2fa4e0106493d8dfe10ec9201bd7762e204bb14a286d` |
| Observation | `road-observation-4c88e2e424168c1c712145c1` / `e5263aa67dbb400e0c3a63b7cd1457d9d95428a8d519aef34b3c9b4396ce1d9a` |
| Receipt | `road-receipt-road-exec-33766f336d9cc18eb2ac159e` / `0ab5964fcc2e1f47d43fd328dbc3771a7e624bf4a3707f91236a1485f5610720` |
| Runtime geometry file commitment | `d13096fb82a1e0588898ade94070becec531ebc07e77fe7795a3d92f8d56db08` |

The required ordered segment IDs remain `K0000004671`, `K0000004913`, `K0000005348`.

## 10. ROAD coordinate and publication finding

All reachable tracked filenames and history were searched. No tracked
`road-centreline-runtime.geojson`, `road-centreline-source.geojson`, or equivalent artifact
containing these segment coordinates exists. The frozen plan and derived portrayal contain only
geometry type, CRS, ordering, vertex counts, endpoint hashes, source geometry hashes, and runtime
geometry hashes.

The required runtime geometry commitments remain:

| Ordered geometry | Type | Vertices | SHA-256 |
|---:|---|---:|---|
| 1 | `LineString` | 4 | `b7272294ba1c52c3550293465192acdff6a48a1fc0eeb401bc4f009c88749f93` |
| 2 | `LineString` | 3 | `bfb72e14ba6b9292d6de578b97bddf269940e9973f4e64add7b48a29dc06993f` |
| 3 | `LineString` | 4 | `90c17d200b2bb85c91ff1415a90f761c6e184cc2bcfd2256476dbe1b9bcba7ad` |

Those identities are non-invertible commitments, not coordinate payloads.

Official NLSC metadata states that 112-year road-model results are available through services and
that physical data is supplied to agencies/organizations through an application workflow. It does
not identify the exact frozen K14 three-segment EPSG:4326 derivative, expose its coordinate arrays,
or establish authorization for this repository to redistribute that exact derivative:

- `https://www.nlsc.gov.tw/NLSC_Content.aspx?n=1742&s=314637`
- `https://www.nlsc.gov.tw/cp.aspx?n=16733`

The exact filename `112年多維度SHP成果_0502.zip` was not found in public search results. No payload
was downloaded to investigate it. Therefore neither exact payload availability nor repository
publication authority is established.

## 11. ROAD artifact identities and closure status

The existing plan, derived portrayal, bundle, observation, receipt, rollback, and authorization
identities remain canonical and unchanged. The missing artifact is specifically the coordinate-
bearing runtime geometry committed by
`d13096fb82a1e0588898ade94070becec531ebc07e77fe7795a3d92f8d56db08`.

Hashes, endpoint hashes, vertex counts, source endpoints, screenshots, service endpoints, or visual
approximations were not used to recreate it. ROAD closure therefore fails without semantic or
representation changes.

## 12. Implementation result and changed files

The two-domain precondition is false, so implementation stopped before artifact/schema/test or
runtime work.

Exact changed-file list:

- `NMA-DEMO-01B-Public-Domain-Artifact-Closure-Report.md`

Source code, endpoint code, browser code, fixtures, schemas, tests, frozen artifacts, ROAD, School,
Core, BUILD, and GEN files changed: **0**.

The unified `/api/nma/runtime` endpoint is unchanged. BUILD remains frozen; automatic Building
production activation remains false.

## 13. Verification results

All test execution used the clean public clone at exact DEMO-01A predecessor unless an exact frozen
commit is named.

| Check | Result |
|---|---:|
| DEMO-01 + DEMO-02 focused public baselines | 34 passed, 1 loopback-only skip |
| School Hero freeze/authorization | 18 passed |
| ROAD-01/02/03 frozen functional baseline | 104 passed |
| ROAD-04 execution at public predecessor | 56 skipped: exact private archive/GDAL input gate |
| BUILD-FINAL exact detached `95de5fa...` | 10 passed |
| GEN-FINAL exact detached `380cc6e...` | 10 passed |
| Core/BUILD/GEN descendant aggregate | 67 passed, 9 stage-scope/environment failures |
| CORE-FINAL exact detached `5eb138a...` | 11 passed, 1 normal-clone local-ref failure |
| GEN-02 exact detached public (`private_archive` deselected) | 14 passed, 1 normal-clone local-ref failure, 1 deselected |

No DEMO-01B artifact/schema/tamper tests exist because the mandatory gate forbids creating an
artifact candidate. ROAD-05 verification/provenance was not run: its public-predecessor fixture is
the ignored runtime directory that this task explicitly forbids inspecting or supplying. Browser
acceptance was not run because both public artifacts do not exist.

## 14. Pre-existing unrelated and environment-scoped failures

The nine descendant failures are not DEMO-01B regressions:

- historical Core/BUILD/GEN exact-change-scope tests intentionally reject later GEN/DEMO files;
- exact predecessor-link tests expect the historical stage HEAD rather than the DEMO-01A descendant;
- one GEN test explicitly requires the forbidden private archive;
- normal `git clone` creates remote-tracking refs but not the local historical branch names expected
  by one CORE-FINAL and one GEN-02 assertion.

Exact detached BUILD-FINAL and GEN-FINAL suites pass. The relevant canonical remote refs were also
verified directly and are exact. The two local-ref portability failures are reported, not relabeled
as passes.

## 15. Fresh public-clone reproduction

A new clone of `https://github.com/dongpo/topoMap.git` was checked out detached at
`9e59237296ed3baed551db2bbd565234a1b02db5` and verified clean. Nothing was copied or linked from
the working checkout.

Tracked-public observations:

- the private archive path is not tracked;
- no tracked ROAD runtime geometry payload exists;
- no tracked complete School authorization artifact exists;
- the public School candidate is `synthetic: true`, layer `SCHOOL_POINT`, feature count `12`;
- focused public baselines reproduce (`34 passed, 1 loopback-only skip`);
- School authorization and ROAD-01/02/03 public baselines reproduce.

The blocker is therefore reproducible from the canonical public repository and is not a local
runtime configuration issue.

## 16. Static, schema, security, and complete-regression gates

Because there is no implementation candidate and the exact diff is documentation-only:

- frozen identity and exact change-scope review: complete;
- production code diff: none;
- all 189 tracked JSON documents parse successfully;
- the new report has no trailing whitespace and its credential-pattern scan is clear;
- full-repository Ruff lint reports four pre-existing findings (three unused server imports and one
  unused `graphrag.py` local); full-repository Ruff format check reports 80 pre-existing files that
  would be reformatted;
- OpenAPI gate: not applicable; the canonical server is standard-library HTTP and exposes no
  generated OpenAPI document;
- full repository regression: not run after the mandatory blocker stop, because portions require
  the forbidden private archive or ignored ROAD runtime artifacts;
- schema and browser candidate gates: not applicable because no schema/browser/artifact candidate
  exists.

No blocked or unrun check is recorded as passing.

## 17. Private-data non-use evidence

- Working-checkout private archive content access: **0**.
- Working-checkout private archive hashes computed: **0**.
- Ignored ROAD runtime directories inspected: **0**.
- Files copied or linked from private/local runtime storage: **0**.
- Coordinates reconstructed, approximated, repaired, resampled, or derived: **0**.
- Synthetic School records substituted into canonical execution: **0**.
- New authorization or issuer artifacts minted: **0**.

All artifact-absence evidence came from Git tracking/history and the clean public clone.

## 18. Authorization, mutation, BUILD, and stub safety

- New authority-granting paths: **0**.
- Static authorization overrides: **0**.
- Fallback executors or success stubs: **0**.
- Hard-coded successful results: **0**.
- Source writes, geometry mutation, or repair: **0**.
- Frozen contract changes: **0**.
- BUILD changes: **0**.
- Automatic Building production activation: **false**.
- Production-reachable demo stubs introduced by DEMO-01B: **0**.
- Total production-reachable demo stub count: **0**, unchanged from the verified predecessor and
  supported by a zero production-code diff.

## 19. Final recommendation

The next safe action is an explicit domain-owner publication process, outside this stage:

1. School owners must publish an executor-compatible, public-safe six-MARK-layer source fixture and
   a canonical HERO-03 authorization artifact or authorized issuer path, with redistribution and
   public/private authority boundaries stated.
2. ROAD/data owners must publish the exact canonical coordinate-bearing runtime payload (or an
   already-canonical public artifact containing exactly the same arrays) together with explicit
   lawful redistribution authority and frozen-lineage binding.

Only after both artifacts exist may a separate bounded task add minimal manifests, closed schemas,
validation tests, and later runtime reintegration. DEMO-01B issues no readiness statement for
runtime reintegration or any retry stage.

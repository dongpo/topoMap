# ROAD-04 Completion Report

## Verdict

PASS

ROAD-04 executed the exact frozen ROAD-03 capability once against the exact private archive. It materialized only the three authorized `K14_ROAD` LineStrings into an isolated ignored candidate runtime root. It did not mutate authoritative source data, topology, ROADA, road edges, frozen ROAD inputs, School Hero, or the canonical/live runtime.

## Canonical Repository Context

- Repository root: `/Users/dongpodeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/topoMap`
- Origin: `https://github.com/dongpo/topoMap.git`
- Starting freeze branch: `freeze/road-03-approved-5eb2ad7`
- Starting SHA: `5eb2ad703ec4b2e3678f511eabfe6a119bef5ac9`
- ROAD-04 branch: `road/road-04-controlled-execution`
- Lineage check: `git merge-base --is-ancestor 5eb2ad703ec4b2e3678f511eabfe6a119bef5ac9 HEAD` returned 0.

## Preflight

- Git baseline verification: PASS; clean tracked working tree, correct origin, exact frozen branch and SHA.
- Private archive presence: PASS at `data/datasets/112年多維度SHP成果_0502.zip`.
- Private archive SHA-256: `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53` — exact match.
- Git-ignore status: PASS; exact `.gitignore` rule, untracked, unstaged.
- Frozen authorization identity: `f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38` — exact match and accepted by the recovered ROAD verifier.
- Baseline ROAD-01/02/03 regression: `104 passed`, 0 failed, 0 skipped.
- Baseline School Hero regression: `11 passed`, 0 failed, 0 skipped.
- Baseline Ruff lint and five frozen ROAD schema/document checks: PASS.

## Frozen Inputs

| Input | Canonical identity | Result |
|---|---|---|
| ROAD-01 package | `b5df3f57c33843f354371206c937f52d37ddbbd9d047a31ad7c334532ce30e9a` | PASS |
| ROAD-01 fixture | `b01e261971f65cbfc127aed4f1ba17b01b194dd89f256d3c024170c1dc7338f0` | PASS |
| ROAD-02 proposal | `3d45d1ed039c2af1aa7f050fa1e3c22158c891390c001285054b05a02959ce06` | PASS |
| ROAD-02 decision | `0d671b1fed3f4b19e4204e745bdcb13f872f3a00dcb4ef5050a091a14065e090` | PASS |
| ROAD-03 approval | `f333defee511e0ae82702444d18befe2f9e115d75608ab61a5c20f91c52f2f07` | PASS |
| ROAD-03 rejection | `a327ae30d6bd4efa53c5df43859e80b0ae0a771035bb2de40d6881f82a62f6eb` | PASS |
| ROAD-03 authorization | `f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38` | PASS |
| Private archive | `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53` | PASS |

Whole-file ROAD hashes recorded before implementation matched after execution. `git diff --exit-code` against the starting SHA returned 0 for all 17 frozen ROAD files and all checked School Hero files.

## Implemented Scope

- `.gitignore` — narrow ignore for isolated ROAD candidate runtime state.
- `src/nma/road_execution.py` — typed fail-closed verifier, exact real-source extraction, deterministic artifact construction, process-safe at-most-once execution, observation, and hash-guarded rollback.
- `tests/test_road_execution_road04.py` — ROAD-04 focused acceptance, real-data, determinism, concurrency, replay, rollback, schema, golden, and API tests.
- `scripts/build_road04_goldens.py` — deterministic real-archive golden generator.
- `scripts/run_nma_agent_server.py` — minimal capability-oriented ROAD execute/read/observe/rollback routes.
- `schemas/road-execution-plan-v1.0.schema.json`
- `schemas/road-derived-portrayal-v1.0.schema.json`
- `schemas/road-runtime-bundle-v1.0.schema.json`
- `schemas/road-runtime-observation-v1.0.schema.json`
- `schemas/road-execution-receipt-v1.0.schema.json`
- `schemas/road-rollback-manifest-v1.0.schema.json`
- Six `data/specifications/nma-road-hero-road-04-golden-*.json` closed-schema goldens containing identities and provenance, not geometry coordinates.
- `ROAD-04-Completion-Report.md` — this report.

No ROAD-01, ROAD-02, ROAD-03, School Hero, source archive, canonical style, HTML runtime, worker, or PMTiles file was changed.

## Authorized Execution

- Route: `ROADNUM=縣126|ROADNUM1=|ROADNUM2=|ROADNAME=中山街`
- Class: `9420400`
- Ordered segments: `K0000004671`, `K0000004913`, `K0000005348`
- Source layer: `K14_ROAD`
- Shield: `9490005`
- Orientation: `road-parallel`
- Annotation: `中山街`
- Graphic element roles: `[2, 5]`
- Execution target: `derived road-centreline portrayal artifact`

## Geometry Provenance

| Segment | Source geometry SHA-256 | Type | Source CRS | Vertices | Runtime derivative SHA-256 | Runtime vertices |
|---|---|---|---|---:|---|---:|
| `K0000004671` | `42616b9b91d91efd4582171b23ad70259156c586bef776098329cdd81aa8f800` | LineString | `TWD97[2020]_TM121` | 4 | `b7272294ba1c52c3550293465192acdff6a48a1fc0eeb401bc4f009c88749f93` | 4 |
| `K0000004913` | `c075943948c1184493d41672f0ca00e610c90bfa7c721f24a645765dc48b9faf` | LineString | `TWD97[2020]_TM121` | 3 | `bfb72e14ba6b9292d6de578b97bddf269940e9973f4e64add7b48a29dc06993f` | 3 |
| `K0000005348` | `88ad286f2b368130e0870360acd07d1d79614d8005ee53eed966b8db6abd2cc6` | LineString | `TWD97[2020]_TM121` | 4 | `90c17d200b2bb85c91ff1415a90f761c6e184cc2bcfd2256476dbe1b9bcba7ad` | 4 |

- Selected native geometry file SHA-256: `8baf555b9d4b69bf9e56731fe2233a29822c897f095d0f6257436aa192c89bea`.
- Runtime EPSG:4326 derivative file SHA-256: `d13096fb82a1e0588898ade94070becec531ebc07e77fe7795a3d92f8d56db08`.
- Transformation: explicit GDAL/OGR coordinate transformation to EPSG:4326 with XY vertex count preserved.
- Native geometry and runtime derivative are separate files and identities.
- Endpoint identities prove the authorized order is continuous without snapping or tolerance-based repair.
- No snap, simplify, smooth, densify, buffer, offset, merge, split, polygonize, topology repair, ROADA read, or road-edge derivation operation exists in the execution plan or code path.

## Runtime Translation

Frozen semantic decision:

- `shield_code = 9490005`
- `shield_orientation = road-parallel`
- `road_name_annotation = 中山街`
- `graphic_element_roles = [2, 5]`

ROAD-04 technical runtime implementation:

- Isolated GeoJSON source with deterministic source ID.
- Exact three-feature EPSG:4326 runtime derivative with explicit provenance.
- One deterministic MapLibre symbol layer using the existing reviewed line-following mechanism: `symbol-placement = line` and literal `中山街`.
- No line colour, width, casing, halo, font policy, semantic offset, or other unapproved styling was introduced.
- No live or canonical runtime file was changed.

## Shield Resolution

semantic binding only

Repository inspection found reviewed MapLibre line-following mechanisms but no reviewed resolver or asset that binds semantic shield code `9490005`. ROAD-04 therefore preserved `9490005` and `road-parallel` as closed runtime semantics, created no icon/image resource, and did not display literal `9490005` as substitute map text.

## Execution Identities

- Execution ID: `road-exec-33766f336d9cc18eb2ac159e`
- Plan ID: `road-plan-cd434d50bd5b49a012bd1e10`
- Plan SHA-256: `e51e42b955ade0d3ff5c6b8fbe00919aac4d9b9f90fe59bd548e14b7a9bf04a0`
- Derived artifact ID: `road-derived-092adadc29954c5151ae43a7`
- Derived artifact SHA-256: `fb8762642e4e3e633912028b18ca6aa11545117e15572839896770537a5971b6`
- Runtime bundle ID: `road-bundle-road-exec-33766f336d9cc18eb2ac159e`
- Runtime bundle SHA-256: `33aa7c6b0d557fa9a72e2fa4e0106493d8dfe10ec9201bd7762e204bb14a286d`
- Observation ID: `road-observation-4c88e2e424168c1c712145c1`
- Observation SHA-256: `e5263aa67dbb400e0c3a63b7cd1457d9d95428a8d519aef34b3c9b4396ce1d9a`
- Receipt ID: `road-receipt-road-exec-33766f336d9cc18eb2ac159e`
- Receipt SHA-256: `0ab5964fcc2e1f47d43fd328dbc3771a7e624bf4a3707f91236a1485f5610720`
- Rollback manifest ID: `road-rollback-road-exec-33766f336d9cc18eb2ac159e`
- Rollback manifest SHA-256: `03bc4f84d27b9b55baa7403d4ff4abc758ff223d0ffe7b7aaaa11233da162ae2`

## At-Most-Once / Replay / Concurrency

- A process-safe `flock` plus in-process lock serializes execution across engine instances.
- The atomically promoted execution directory contains its immutable consumption record; the separate ledger is written from that promoted record.
- Exact replay returned execution `road-exec-33766f336d9cc18eb2ac159e` and receipt `0ab5964f...` without creating another execution or ledger entry: counts remained `1 execution`, `1 ledger`.
- Replay with another idempotency key returns `authorization_already_consumed`.
- Two separate engine instances concurrently executing the same authorization/key returned the same receipt and promoted one execution only.
- Staged-failure testing left no final output and no false ledger entry.

## Rollback Rehearsal

- The rollback manifest binds the execution, receipt, bundle, exact candidate artifact relative paths, expected file hashes, runtime IDs, allowed `remove-file` operation, and rollback root `.`.
- Rehearsal removed only the four candidate artifacts after verifying all hashes.
- Receipt, plan, authorization copy, consumption record, rollback manifest, observation directory, source archive, and all frozen inputs were preserved.
- A hash-mismatched bundle caused `rollback_precondition_failed` before any removal.
- A second rollback returned the same immutable rollback result.

## Mutation Audit

- Source unchanged: before and after `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.
- Topology unchanged: no mutation/repair operation; native vertex counts and endpoint identities preserved.
- ROADA unused: no ROADA source or operation in plan, bundle, receipt, or code path.
- Road edges absent: only authorized centreline geometry and a label layer were materialized.
- Frozen ROAD unchanged: `git diff --exit-code` against `5eb2ad7...` returned 0 for all 17 frozen files; before/after whole-file hashes match.
- School Hero unchanged: core whole-file hashes remained `cc1974bb...` and `256d8886...`; checked School Hero diff returned 0; regression is 11/11.
- Canonical runtime unchanged: checked HTML/worker/runtime files diff returned 0; candidate state exists only under ignored `artifacts/runtime/road/`.

## Acceptance Matrix

| AT | Result | Evidence |
|---:|---|---|
| AT-01 | PASS | Canonical origin and repository root verified. |
| AT-02 | PASS | Branch descends directly from exact `5eb2ad7...`. |
| AT-03 | PASS | Private archive exists in this checkout. |
| AT-04 | PASS | Archive hash exact. |
| AT-05 | PASS | Archive ignored, untracked, and unstaged. |
| AT-06 | PASS | All frozen ROAD identities exact. |
| AT-07 | PASS | Exact authorization executed once. |
| AT-08 | PASS | Changed/rehashed authorization rejected. |
| AT-09 | PASS | Changed proposal binding rejected. |
| AT-10 | PASS | Changed decision binding rejected. |
| AT-11 | PASS | Changed ROAD-01 binding rejected. |
| AT-12 | PASS | Changed archive binding and wrong archive bytes rejected. |
| AT-13 | PASS | Changed fixture and fixture binding rejected. |
| AT-14 | PASS | Non-executable capability rejected. |
| AT-15 | PASS | Only `K14_ROAD` opened/extracted. |
| AT-16 | PASS | Exact three segment IDs only. |
| AT-17 | PASS | Authorization order preserved. |
| AT-18 | PASS | Missing authorized segment rejected. |
| AT-19 | PASS | Extra authorized scope rejected. |
| AT-20 | PASS | Replacement segment rejected. |
| AT-21 | PASS | Route identity exact. |
| AT-22 | PASS | Class `9420400` exact. |
| AT-23 | PASS | All source geometries are LineString. |
| AT-24 | PASS | Source CRS recorded as `TWD97[2020]_TM121`. |
| AT-25 | PASS | Per-segment source geometry hashes recorded. |
| AT-26 | PASS | Geometry path is selection plus explicit reprojection only. |
| AT-27 | PASS | No snapping. |
| AT-28 | PASS | No simplification. |
| AT-29 | PASS | No buffering. |
| AT-30 | PASS | No offset geometry. |
| AT-31 | PASS | No polygonization. |
| AT-32 | PASS | No road edges derived. |
| AT-33 | PASS | ROADA not read or used. |
| AT-34 | PASS | EPSG:4326 derivative is separate and provenance-bound. |
| AT-35 | PASS | Shield code exactly `9490005`. |
| AT-36 | PASS | Orientation exactly `road-parallel`. |
| AT-37 | PASS | Annotation exactly `中山街`. |
| AT-38 | PASS | Roles exactly ordered `[2, 5]`. |
| AT-39 | PASS | Changed and extra portrayal semantics rejected. |
| AT-40 | PASS | Reviewed line mechanism reused; no reviewed `9490005` resolver exists. |
| AT-41 | PASS | Semantic-binding-only mode used without fabricated graphic. |
| AT-42 | PASS | Missing visual shield asset did not falsify semantic execution. |
| AT-43 | PASS | Plan validates against closed schema. |
| AT-44 | PASS | Derived portrayal validates against closed schema. |
| AT-45 | PASS | Runtime bundle and observed candidate identifiers/count validate. |
| AT-46 | PASS | Receipt validates against closed schema. |
| AT-47 | PASS | Rollback manifest validates against closed schema. |
| AT-48 | PASS | Two temporary roots produced identical canonical identities. |
| AT-49 | PASS | Absolute root paths do not enter identity inputs. |
| AT-50 | PASS | Different timestamps produced identical receipt identity. |
| AT-51 | PASS | Forced pre-promotion failure cleaned staging and created no final/ledger. |
| AT-52 | PASS | Separate concurrent engines promoted at most once. |
| AT-53 | PASS | Replay returned same receipt; no new identity. |
| AT-54 | PASS | Rollback removed only four exact ROAD candidate files. |
| AT-55 | PASS | Receipt and audit evidence preserved. |
| AT-56 | PASS | Hash mismatch rejected before removal. |
| AT-57 | PASS | Second rollback idempotent. |
| AT-58 | PASS | Private source archive byte hash unchanged. |
| AT-59 | PASS | Frozen ROAD files unchanged. |
| AT-60 | PASS | School Hero files unchanged. |
| AT-61 | PASS | Canonical/live runtime unchanged. |
| AT-62 | PASS | ROAD-01/02/03 `104/104 passed`. |
| AT-63 | PASS | School Hero `11/11 passed`. |
| AT-64 | PASS | Ruff passed on all ROAD source/tests/generator and the affected server with its baseline F401 exclusions. |
| AT-65 | PASS | Six new schemas pass Draft 2020-12 metaschema validation. |
| AT-66 | PASS | Six ROAD-04 goldens validate and match real execution identities. |
| AT-67 | PASS | Git scope is ROAD-04 plus minimal additive server/ignore integration only. |

## Regression Results

Commands and exact results:

- `PYTHONPATH=src python3 -m pytest -o addopts='' -q tests/test_road_execution_road04.py` — `56 passed in 6.63s`.
- `PYTHONPATH=src python3 -m pytest -o addopts='' -q tests/test_road_resolution_road01.py tests/test_road_portrayal_decision_road02.py tests/test_road_approval_road03.py` — `104 passed in 0.17s`.
- `PYTHONPATH=src python3 -m pytest -o addopts='' -q tests/test_hero04_authorization.py tests/test_hero04_execution.py tests/test_hero04_maplibre.py tests/test_hero04_rollback.py` — `11 passed in 4.61s`.
- `PYTHONPATH=src python3 -m pytest -o addopts='' -q tests/test_api.py tests/test_hero04_api.py` — `9 passed in 0.07s`.
- Ruff ROAD source/tests/generator — PASS.
- Ruff affected server with the three unchanged baseline F401 exclusions — PASS.
- Ruff format check on new Python files — PASS.
- Six Draft 2020-12 metaschemas — PASS.
- Six ROAD-04 goldens — PASS.
- Promoted actual plan/derived/bundle/receipt/rollback/observation validation — six PASS.
- Skips: 0 in every reported acceptance/regression command.

## Git Diff Scope

Tracked scope is 18 files including this report:

- ROAD-04 implementation/test/generator: 3 files.
- ROAD-04 schemas: 6 files.
- ROAD-04 goldens: 6 files.
- Minimal shared integration: `.gitignore` and `scripts/run_nma_agent_server.py`.
- Completion report: 1 file.

The private archive is absent from `git ls-files`, absent from staging, and remains ignored. Promoted candidate runtime state is also ignored and absent from the tracked diff.

## Remaining Limitations

- Shield `9490005` is intentionally `semantic_binding_only`; there is no reviewed resolver or visual asset in this repository. No shield image was fabricated.
- The ROAD runtime observation proves engineering identifiers, bundle identity, and feature count. It is not pixel-level or cartographic visual acceptance.
- Final shield rendering, label collision/placement inspection, and pixel-level correctness belong to ROAD-05 QA and Provenance.
- The legacy server file has three unrelated pre-existing F401 imports. ROAD-04 did not remove or suppress them; its server Ruff command used those baseline exclusions while all ROAD-04 code itself passes Ruff without exclusions.

## Final Acceptance Statement

ROAD-04 is ready to commit and proceed to ROAD-05 QA and Provenance.

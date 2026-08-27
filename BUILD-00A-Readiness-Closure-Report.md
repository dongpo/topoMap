# BUILD-00A — BUILD-01 Readiness Closure Report

Closure date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-01 IS READY TO ENTER AS A SEPARATELY AUTHORIZED, BOUNDED DOMAIN TASK**

The blockers identified by BUILD-00 are closed without implementing BUILD execution, granting
authorization, mutating source geometry, wiring a runtime route, or changing frozen CORE, ROAD,
School Hero, or Agent behavior.

BUILD-01 may now begin architecture and implementation work from the accepted BUILD fixture and
Core-owned profile boundary. This report does not itself authorize execution or production
integration.

## 2. Baseline and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Required predecessor branch | `agent/agent-06-authorization-handoff-boundary` | PASS |
| Required predecessor SHA | `ebf24f7c962851282a24844097651917a120fab8` | PASS |
| Immutable Core predecessor | `nma-core-v1.0-final` / `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Closure branch | `build/build-00a-readiness-closure` | PASS |
| Starting tracked worktree | clean | PASS |

## 3. Fixture selection closure

All six primary BUILD candidates in the verified private archive were inspected under the same
read-only criteria:

| Candidate | Total | `9310100` | Null/blank IDs | Duplicate ID groups | Invalid geometry | Decision |
|---|---:|---:|---:|---:|---:|---|
| `J01_BUILD` | 3,334 | 3,314 | 0 | 0 | 2 | reject |
| `J13_BUILD` | 2,968 | 2,962 | 0 | 0 | 0 | **accept** |
| `J17_BUILD` | 2,839 | 2,769 | 0 | 0 | 1 | reject |
| `K01_BUILD` | 46,875 | 46,855 | 0 | 1 | 5 | reject |
| `K02_BUILD` | 10,645 | 10,645 | 0 | 0 | 0 | reject |
| `K14_BUILD` | 2,116 | 2,099 | 0 | 0 | 2 | reject |

`J13_BUILD` is the smallest candidate with zero null/blank identifiers, zero duplicate identifier
groups, zero null/empty geometry, and zero invalid geometry. `K02_BUILD` also has zero observed
defects but is materially larger. The legacy v0.4 `J17_BUILD` experiment remains unchanged and is
not promoted because its source contains one invalid geometry.

The accepted manifest freezes:

- the private archive SHA-256
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`;
- all five `J13_BUILD` component hashes;
- the exact seven-field schema;
- `PolygonZ` source geometry and canonical Core role `Polygon`;
- the source CRS name with authority deliberately unasserted;
- the exact total and feature-code populations;
- all six candidate observations and the selection policy;
- a non-executing, non-mutating, non-redistributing boundary.

Fixture identity is the full Core-owned content identity:

`build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a`

## 4. QA specification closure

`data/specifications/taiwan-temap-build-v0.4.json` now supplies the missing bounded BUILD
diagnostic profile. It intentionally distinguishes:

- documented `ID` and `SOURCE` fields;
- observed archive fields `BUILD_ID`, `TERRAINID`, `BUILD_STR`, `BUILD_NO`, `BUILD_H`, `GROUP_ID`,
  and `MDATE`;
- documentary authority from dataset observation;
- diagnosis from repair or execution.

The existing `build-real-polygon` QA path now runs deterministically on legacy `J17_BUILD` and
reports exactly the two documented schema-boundary findings. It proposes no safe repair, performs
no mutation, and grants no automatic acceptance.

## 5. Core identity and profile closure

BUILD adopts the exact frozen objects exported by `nma.core`:

- `canonical_sha256` for the complete fixture content identity;
- `validate_sha256` for strict component and archive digests;
- `FeatureProfile` for immutable BUILD identity and source scope.

The adapter is BUILD-owned in `build_contracts/feature_profile.py`. The fixture validator is
BUILD-owned in `build_contracts/fixture.py`. They are deliberately outside frozen `src/nma` and do
not modify the shared `src/nma/feature_profile_adapters.py` file.

No fallback, stub, copy, repair, or local replacement provider exists. Removing `nma.core` produces
a deterministic `ModuleNotFoundError` before fixture identity processing and creates no substitute
Core package.

## 6. Boundary closure

The BUILD readiness contract contains no:

- authorization ID, grant, or validator;
- execution plan, command, endpoint, or tool payload;
- idempotency or consumption identity;
- source mutation or geometry repair;
- Z-dimension drop authority;
- runtime or public-browser wiring;
- receipt, observation, rollback, or provenance claim;
- redistribution permission.

Those are BUILD-01-or-later responsibilities and require separate authorization. The accepted
fixture only supplies deterministic evidence and the Core-owned entry profile.

## 7. Acceptance results

Environment:

- Python 3.13.5;
- pytest 9.1.1;
- GDAL 3.11.0;
- private archive present and hash-exact.

BUILD-00A focused acceptance: **14 passed**.

Frozen-boundary regression subset (BUILD-00A plus CORE-01/02/04): **42 passed**.

Complete repository regression: **616 collected; 613 passed; 3 failed**.

The three failures are the exact known, pre-existing Agentic/demo drift recorded by CORE-FINAL:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD, Core, ROAD, School Hero, or Agent contract regression was introduced.

## 8. Exact changed files

1. `BUILD-00A-Readiness-Closure-Report.md` — closure evidence and BUILD-01 entry verdict.
2. `build_contracts/__init__.py` — BUILD-owned non-executing contract exports.
3. `build_contracts/feature_profile.py` — exact Core `FeatureProfile` adapter.
4. `build_contracts/fixture.py` — closed fixture identity and boundary validator.
5. `data/specifications/nma-build-fixture-manifest-v1.0.json` — accepted J13 fixture and six-candidate comparison.
6. `data/specifications/taiwan-temap-build-v0.4.json` — missing bounded BUILD diagnostic specification.
7. `schemas/build-fixture-manifest-v1.0.schema.json` — closed Draft 2020-12 fixture schema.
8. `tests/test_build00a_readiness_closure.py` — fixture, Core provider, tamper, QA, private-source, missing-Core, and determinism acceptance.

Existing production source changed: **no**.

Frozen `src/nma`, Core, ROAD, School Hero, Agent contracts, schemas, fixtures, and public runtime
files changed: **no**.

Private archive tracked, staged, modified, or published: **no**.

## 9. BUILD-01 entry recommendation

**GO — with a new explicit BUILD-01 authorization and exact predecessor binding.**

BUILD-01 should start from the accepted BUILD-00A commit on
`build/build-00a-readiness-closure`, consume `J13_BUILD` only through the accepted manifest, and
preserve these gates:

1. fixture identity and component hashes are immutable;
2. Core identity/provider objects are imported exactly;
3. source remains read-only and private;
4. `PolygonZ` handling requires an explicit domain decision;
5. proposal, authorization, execution, verification, rollback, and provenance ownership must be
   defined before runtime wiring;
6. no generic v0.4 approval object may be promoted into BUILD authorization;
7. full frozen-boundary and two-root determinism verification remains mandatory.

# BUILD-08 — Official Semantics & Production Entry Review Completion Report

Completion date: 2026-08-21 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-08 REVIEW IS COMPLETE; OFFICIAL PORTRAYAL AND PRODUCTION ENTRY REMAIN HOLD**

BUILD-08 independently bound the accepted BUILD-07 DEMO evaluation to the tracked official-rule
evidence, real-layer path, portrayal compiler, and MapLibre adapter. All five choices remain valid
for the frozen DEMO, but zero of five is ready for production entry.

The result is evidence-based rather than a precautionary default. The current repository has a
J13/J17 layer mismatch, no polygon annotation binding, an explicit `drop-z` execution step, a
preview-only portrayal path, and a missing reviewed hatch asset. BUILD-07 acceptance cannot cure
those differences because it explicitly carries no official or production authority.

## 2. Exact predecessor and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Required predecessor branch | `build/build-07-demo-user-evaluation` | PASS |
| Required predecessor commit | `153037a165683e0a2b39d36620c688955ca935fd` | PASS |
| BUILD-07 record file SHA-256 | `7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d` | PASS |
| BUILD-07 record SHA-256 | `ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c` | PASS |
| BUILD-07 template SHA-256 | `0fea2e7fe6b8ec9dd10816ba5679b04773ecd3f0761ca7b58e339f7df91139e6` | PASS |
| BUILD-06 freeze SHA-256 | `bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857` | PASS |
| BUILD-03A resolution SHA-256 | `a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01` | PASS |
| BUILD-08 branch | `build/build-08-official-production-entry-review` | PASS |
| Starting tracked worktree | clean | PASS |

## 3. Audit scope and method

BUILD-08 used only tracked evidence and read-only inspection of existing runtime paths. It did not:

- open or extract the private source archive;
- execute a real layer or the BUILD-05 capability;
- change the DEMO, source, portrayal corpus, or production runtime;
- infer a human official-policy decision;
- publish or activate an official rule.

The review distinguishes three separate questions:

1. whether the frozen DEMO may continue — **GO**;
2. whether official evidence may be collected under a new explicit scope — **CONDITIONAL GO**;
3. whether the current choices may enter official portrayal or production — **HOLD**.

## 4. Concrete production-path findings

| Finding | Tracked evidence | Production effect |
|---|---|---|
| Layer identity mismatch | BUILD-07 is bounded to `J13_BUILD`; `REAL_LAYER_PROFILES["building-polygon"]` selects `J17_BUILD`. | No single authoritative production layer/field contract exists. |
| Annotation path incomplete | BUILD-07 requires `BUILD_NO` + `BUILD_STR`; the real-layer building profile has `label_field: null`. | The accepted DEMO annotation cannot be emitted by the existing polygon runtime binding. |
| Z policy conflict | BUILD-07 forbids source Z removal; the real-layer plan lists `drop-z` and invokes `-dim XY`. | The existing execution path is incompatible with the accepted PolygonZ preservation boundary. |
| Portrayal remains review-only | Compiler output is `compiled-for-review`; adapter output is `adapter-ready-for-preview`, `preview_only: true`, and performs no map mutation. | There is no official activation path. |
| Hatch asset absent | The reviewed 9310100 recipe points to `building-hatch-tile-v1.svg`, which is not present. | A deployable reviewed production hatch resource is unavailable. |

Frozen runtime evidence file identities:

| File | SHA-256 |
|---|---|
| `src/nma/real_layer.py` | `d9eb720b5f84c35b63df8c9cd828a7530497d4b71f502117bdf7470148d890e9` |
| `src/nma/portrayal_compile.py` | `3b2183bc14143bdb34ebce5d7869bdb421d0aa5527feaf129e63c509a842d4db` |
| `src/nma/maplibre_adapter.py` | `9fdf76fec8d1e4786e4ba7f24572b7f41336f13d628af9c089af697c04cf2f3a` |
| `data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json` | `9ba4f3c5e9dd2acec78ab56bf9fce270efac9b8343937459a6f4b3f16830a512` |

## 5. Five official/production gate decisions

| Gate | BUILD-07 DEMO | BUILD-08 official/production result | Required next evidence |
|---|---|---|---|
| Hatch angle | Accept 45° DEMO default | HOLD | Authoritative numeric-angle rule or explicit production convention, plus a reviewed deployable hatch asset. |
| Annotation placement | Accept DEMO interior/suppress policy | HOLD | Approved placement/collision policy and explicit `BUILD_NO` + `BUILD_STR` runtime binding. |
| Real BUILD schema | Accept J13-bounded DEMO binding | HOLD | One versioned authoritative contract selecting J13 or J17 without unsupported global equivalence. |
| Line/color profile | Accept 1 px / `#111111` DEMO profile | HOLD | Approved output-profile mappings for line code 2 and colour code 7. |
| PolygonZ/XY policy | Accept Z-preserving DEMO boundary | HOLD | Z-preserving production contract with an explicitly derived, non-writing XY display path. |

Every gate still requires a human official/production scope decision. No accepted DEMO verdict was
relabelled as official evidence.

## 6. Entry decision

| Target | BUILD-08 decision |
|---|---|
| Existing frozen DEMO | `go` |
| Read-only official evidence collection | `conditional-go-explicit-scope-required` |
| Official portrayal promotion | `hold` |
| Production runtime entry | `hold` |
| Source execution or mutation | `hold` |
| Production-ready gates | `0 / 5` |
| Unresolved official gates | `5 / 5` |
| Next gate | `build-08a-human-official-production-scope-resolution` |

## 7. Review identity and fail-closed behavior

Golden BUILD-08 review SHA-256:

`b48337a6bb8cf1e6cffc54e0bbfe14383f62c1dcfdca54bf706c0ab045b42484`

The review is generated by the frozen Core `canonical_sha256` provider. The closed schema and
validator reject a rehashed change that promotes production, promotes official portrayal, permits
source operations, claims a production-ready gate, changes J17 to J13 without evidence, invents a
label binding, removes the `drop-z` conflict, invents the missing asset, or claims private-source
access.

## 8. Authority boundary

BUILD-08 keeps all of the following false:

- private source accessed;
- human official decision inferred;
- official semantics decided;
- official portrayal activation allowed;
- production runtime wiring allowed;
- production activation allowed;
- source access, execution, or mutation allowed;
- source Z-dimension drop allowed;
- DEMO changed.

The review module has no subprocess, GDAL, private-source reader, execution, or filesystem-write
capability.

## 9. Pre-publication acceptance results

Environment:

- Python 3.11.9;
- pytest 8.3.3;
- Ruff static acceptance passed;
- JSON and Draft 2020-12 schema validation passed.

Results before stage/commit/push authorization:

- BUILD-08 focused acceptance: **32 passed**;
- BUILD-00A through BUILD-08 chain: **391 passed**;
- frozen Core identity checks: **11 passed; 1 publication-scope gate deselected**;
- complete functional regression excluding that publication-scope gate:
  **992 executed; 989 passed; 3 failed; 1 deselected**.

The deselected Core test is the existing guard that requires no untracked files. It must remain
pending until the project owner separately authorizes staging these BUILD-08 files. After staging,
it must be rerun and pass before commit or push.

The three executed failures are the exact known pre-existing Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD, Core identity-provider, ROAD, source-integrity, privacy, official portrayal, or
production runtime regression was introduced.

## 10. Exact changed files

1. `BUILD-08-Completion-Report.md` — evidence findings, HOLD decision, tests, boundaries, and next gate.
2. `build_contracts/production_entry_review.py` — deterministic read-only evidence and entry-review contract.
3. `data/specifications/nma-build-08-golden-official-production-entry-review-v1.0.json` — frozen BUILD-08 review decision.
4. `schemas/build-official-production-entry-review-v1.0.schema.json` — closed exact review schema.
5. `tests/test_build_official_production_entry_review_build08.py` — predecessor, runtime, gate, identity, tamper, and no-execution acceptance.

Existing BUILD-00A through BUILD-07 artifacts, the public DEMO and Pages payload, `src/nma`,
portrayal evidence, source data, private archive, runtime wiring, and official rules changed:
**no**.

## 11. Next human gate recommendation

**CONDITIONAL GO — BUILD-08A MAY RECORD A HUMAN-APPROVED OFFICIAL/PRODUCTION SCOPE; PRODUCTION
IMPLEMENTATION REMAINS HOLD.**

The recommended human decision is to accept the BUILD-08 HOLD finding and authorize only a
bounded next scope. BUILD-08A should decide which source layer contract (J13 or J17) is the target,
which items require authoritative evidence rather than local policy, and whether a Z-preserving
derived-XY architecture may be designed. It must not approve the existing `drop-z` path, infer an
official 45-degree rule, or activate a runtime.

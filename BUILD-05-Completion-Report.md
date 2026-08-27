# BUILD-05 — Controlled Single-Consumption Building DEMO Execution Completion Report

Completion date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-05 IS COMPLETE AS ONE CONTROLLED, DERIVED, DEMO-ONLY EXECUTION**

BUILD-05 consumed the exact BUILD-04 capability once, read only the exact bound private J13
building feature, and emitted one normalized non-geographic MapLibre DEMO artifact. The source
archive remained byte-identical, its `PolygonZ` identity remained committed, and neither raw
source coordinates nor raw attributes were published.

The BUILD-04 authorization is now permanently recorded as `consumed-once`. An independent,
fail-closed consumption ledger blocks replay even when a caller changes the output path. No
production runtime was wired and no DEMO policy was promoted to official authority.

## 2. Exact predecessor and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Required predecessor branch | `build/build-04-demo-authorization-boundary` | PASS |
| Required predecessor SHA | `be1dc97f077918c7cc7c27a230015b364823cbd6` | PASS |
| BUILD-04 authorization | `f609fa99ae0280987e11a3328e04d26484c15a65f72a0266566f2aaa9f650b2d` | PASS |
| BUILD-04 plan | `b8b5ecd54954b190eb8cda398710039f334e8424fd0969816380b4a2b52b0b71` | PASS |
| BUILD-03A resolution | `a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01` | PASS |
| BUILD-05 branch | `build/build-05-controlled-demo-execution` | PASS |
| Starting tracked worktree | clean | PASS |

## 3. Exact authorized execution

The executor validated the complete frozen predecessor chain before accepting the BUILD-04
request. The consumed capability remained bound to:

- authorization ID: `build-04-demo-auth-a5a8f11b94784a60`;
- execution ID: `build-05-demo-exec-b8b5ecd54954b190eb8cda39`;
- operation: `render-derived-maplibre-building-demo`;
- target: `derived MapLibre web DEMO portrayal candidate`;
- layer: `J13_BUILD`;
- feature code: `9310100`;
- feature reference:
  `build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f`;
- default hatch angle: 45 degrees.

Changes to the authorization, predecessor, archive, feature identity, operation, or output state
fail closed.

## 4. Source integrity and PolygonZ preservation

The exact ignored private archive was accessed read-only:

- archive SHA-256 before:
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`;
- archive SHA-256 after:
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`;
- source geometry: `PolygonZ`;
- rings: 1;
- vertices: 65;
- attribute commitment:
  `ddfa112586b9c2bc3a61bdf2638b7994ba1200bfce5d8ad34988f2a24da96078`;
- geometry commitment:
  `23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f`.

The source was not repaired, rewritten, staged, tracked, redistributed, or stripped of Z. Only a
derived XY view was used to construct the redacted DEMO artifact.

## 5. Derived DEMO artifact and privacy boundary

The artifact contains one closed, 65-vertex polygon normalized into a local `[0, 1]` coordinate
space. Those coordinates are not geographic and cannot reproduce the source location. The
artifact contains no raw source attribute names or values, no source WKB, and no Z ordinates.

The display annotation is the approved placeholder `樓層＋結構`. Its actual source-derived value
is not disclosed; only this commitment is retained:

`17460f383142153fa58b587a2d3902b6cdbbcddb663d151cf28ce86bc6149a52`

The derived MapLibre DEMO profile preserves the BUILD-03A decision:

- solid `#111111` one-CSS-pixel boundary;
- `#111111` hatch with 2 mm / `7.559055118110236` CSS-pixel spacing;
- default angle 45 degrees;
- user-adjustable angle from 0 degrees inclusive to 180 degrees exclusive, in 1-degree steps;
- adjustment remains DEMO-only;
- annotation remains inside the polygon and is suppressed when no safe fit exists.

## 6. Single-consumption and replay prevention

The authorization consumption is independently persisted as:

- consumption ID: `build-05-consumption-f609fa99ae0280987e11a332`;
- status: `consumed-once`;
- replay allowed: false;
- consumption SHA-256:
  `44ab99947d9cb196de6a4f5a5238b4af33eb306a911a104224774425c7ebb108`.

Before any source read, the executor atomically claims a distinct consumption-ledger path. An
existing claim or completed record rejects the request as already consumed. If validation or
source access fails after the claim, the claim remains `claimed-fail-closed`; it is not silently
released for retry. Successful execution atomically replaces the claim with the immutable exact
consumption record.

Tests prove that replay remains blocked when the caller supplies a different output filename.
Output, ledger, source aliases, symlinks, and pre-existing conflicting output are also rejected.

## 7. Receipt and identity chain

Exact frozen identities:

| Record | SHA-256 |
|---|---|
| Derived DEMO artifact | `9131df533365e2f42e01edb8988804b850b65e69b932c55b672e0addd3400d84` |
| Authorization consumption | `44ab99947d9cb196de6a4f5a5238b4af33eb306a911a104224774425c7ebb108` |
| Execution receipt | `c4ff4017c01aa3ef861530a91204fcd8357387a8400f4a47fcd637033f445573` |
| Complete BUILD-05 package | `10c22339abb8d2eed489ae56a54214948213bad51a135e00f74e309931c98c97` |

The receipt binds the authorization, resolution, plan, artifact, consumption record, and identical
source hashes before and after execution. Every internal record and the package use the frozen
Core canonical SHA-256 provider. Rehashed alterations cannot replace the exact frozen package.

## 8. Runtime and authority boundary

BUILD-05 records all of the following:

- authorization consumed: true;
- execution performed: true;
- source accessed read-only: true;
- source mutated: false;
- source Z preserved: true;
- raw geographic coordinates disclosed: false;
- raw attributes disclosed: false;
- runtime wired: false;
- production activated: false;
- DEMO policy promoted: false.

The executor contains no network client and no live MapLibre runtime adapter. The output is a
derived DEMO data/style candidate, not a deployment or production activation.

## 9. Acceptance results

Environment:

- Python 3.13.5;
- pytest 9.1.1;
- Ruff static acceptance passed;
- JSON and Draft 2020-12 schema validation passed.

Results:

- BUILD-05 focused acceptance: **32 passed**;
- BUILD-00A through BUILD-05 chain acceptance: **242 passed**;
- complete repository regression: **844 collected; 841 passed; 3 failed**.

The three failures are the exact known, pre-existing Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

The complete suite was rerun with its established `artifacts/tmp` write access. Two initial
sandbox-only failures disappeared. No BUILD, Core, ROAD, School Hero, Agent contract, source
integrity, or identity-provider regression was introduced.

## 10. Exact changed files

1. `BUILD-05-Completion-Report.md` — execution, source integrity, privacy, consumption, receipt, acceptance, and readiness record.
2. `build_contracts/__init__.py` — BUILD-05 public execution and ledger-validation exports.
3. `build_contracts/demo_execution.py` — exact source read, redacted derivation, atomic fail-closed consumption, receipt, and validation.
4. `data/specifications/nma-build-05-authorization-consumption-v1.0.json` — independent immutable consumed-once ledger.
5. `data/specifications/nma-build-05-golden-execution-package-v1.0.json` — frozen redacted DEMO artifact, consumption record, and receipt.
6. `schemas/build-demo-execution-package-v1.0.schema.json` — closed Draft 2020-12 execution-package schema.
7. `tests/test_build_demo_execution_build05.py` — execution, replay, identity, privacy, tamper, source-integrity, and boundary acceptance.

Existing production `src/nma` changed: **no**.

BUILD-00A through BUILD-04, frozen Core, ROAD, School Hero, Agent, public runtime, official
portrayal evidence, and private source archive files changed: **no**.

## 11. BUILD-06 readiness recommendation

**CONDITIONAL GO — BUILD-06 MAY ENTER ONLY AS INDEPENDENT VERIFICATION, FREEZE, AND OPTIONAL NON-PRODUCTION DEMO PRESENTATION.**

BUILD-06 may verify the exact BUILD-05 package, independently confirm the consumption ledger and
privacy/source commitments, freeze the result, and present the existing normalized artifact in a
clearly labeled non-production DEMO. It may not repeat source execution because the BUILD-04
authorization is consumed. It also may not disclose private source data, wire production runtime
behavior, or promote the DEMO portrayal to official authority without a new explicit human gate
and separately scoped authorization.

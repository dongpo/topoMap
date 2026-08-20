# BUILD-03A — Human Gate Resolution for DEMO Scope Completion Report

Completion date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-03A IS COMPLETE AS AN EXPLICIT, HUMAN-APPROVED, DEMO-SCOPED GATE-RESOLUTION STAGE**

The human project owner approved all five BUILD gate decisions with one explicit override: the
DEMO hatch angle starts at 45 degrees and is user-adjustable. Every choice whose official meaning
remains unclear is limited to the DEMO and cannot be promoted into official evidence or production
authority.

BUILD-03A records the plain-language explanation, original recommendation, approved resolution,
and evidence boundary for every gate. It does not issue execution authorization, wire a runtime,
modify source data, or activate a production rule.

## 2. Exact predecessor and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Required predecessor branch | `build/build-03-gate-review-boundary` | PASS |
| Required predecessor SHA | `b5f3122b141384bb89a87602e36e5a2f27570d33` | PASS |
| BUILD-03 review | `4177a2cc29738ad7b1bc6f00f2c10c724fec3c475e57dee45ad2e8e1f105cbdd` | PASS |
| BUILD-02 proposal | `1e588ea2d7752ce7b02c28d6117c4deb1d6c8995dcbace14cfcb542eca847749` | PASS |
| BUILD-02 decision | `624fafe1f84164f6f28396d21153a3ed0f9795ead87b6e9c605115b35ee3c846` | PASS |
| BUILD-01 semantic package | `59b6f972046dbe9af295de414525230b03ed6da4f0e78374076b5cc4a2cdd7de` | PASS |
| BUILD-03A branch | `build/build-03a-human-gate-resolution` | PASS |
| Starting tracked worktree | clean | PASS |

## 3. Recorded human approval

The frozen decision records:

- actor type: `human-project-owner`;
- decision: `approved-demo-scope-with-45-degree-adjustable-hatch`;
- date: 2026-08-20;
- all five gate decisions explicit: true;
- approved statement:
  `核准 BUILD-03A 建議決議。剖面線角度先以45度，DEMO提供使用者調整，凡語意不清者，都是DEMO的項目。`

A generic `approved`, incomplete angle choice, rejection string, or absent decision cannot be
substituted for this exact scoped decision. An absent decision creates no artifact.

## 4. Recorded gate decisions

| Gate | Plain-language issue | Human-approved DEMO resolution |
|---|---|---|
| `hatch-angle-transcription` | The source shows a lower-left-to-upper-right diagonal but states no numeric angle. | Start at 45 degrees and permit user adjustment. The value is a DEMO default, not source transcription. |
| `building-annotation-placement` | Floor/structure text is required, but placement and collision behavior are unspecified. | Use the polygon pole of inaccessibility; suppress when it cannot fit or conflicts with a higher-priority label; never displace outside. DEMO only. |
| `real-build-schema-binding` | J13 exposes `BUILD_NO` and `BUILD_STR`, while the reviewed document has a different reduced field description. | Bind only those two fields for the verified J13 DEMO scope; assert no global `ID`/`SOURCE` equivalence and inherit no other-layer authority. |
| `line-and-color-profile` | Line code 2 and colour code 7 do not define web width or color values. | Use the `nma-maplibre-web-demo-v1` profile: solid 1 CSS px, `#111111`, opacity 1.0; convert 2 mm at 96 CSS px/in. DEMO only. |
| `j13-polygonz-runtime-policy` | The source is `PolygonZ`, while the MapLibre display path is 2D. | Preserve authoritative `PolygonZ`; use XY only in a derived DEMO view; never write back, repair, or authorize source Z removal. |

Each structured gate record also contains the Chinese plain-language explanation, original
recommendation, approved resolution, and a machine-checkable evidence boundary.

## 5. DEMO portrayal policy

The resolved DEMO candidate is frozen to:

- feature-following hatched polygon representation;
- source geometry `PolygonZ`, authoritative Z preserved;
- non-writing XY DEMO view;
- boundary line code 2, solid 1 CSS px;
- colour code 7 rendered as `#111111` at full opacity;
- 2.0 mm hatch spacing converted to `7.559055118110236` CSS px;
- default hatch angle 45 degrees;
- user-adjustable field: `hatch.numeric_angle_degrees`;
- annotation content `{BUILD_NO}{BUILD_STR}`;
- interior pole-of-inaccessibility anchoring and deterministic suppression;
- J13-only schema authority for feature code `9310100`.

The official portrayal baseline remains immutable. None of these DEMO mappings defines an
official numeric angle, line metric, color profile, annotation policy, or production Z policy.

## 6. Resolution and authorization effects

All five gates are resolved for the DEMO scope. They are not resolved for production scope.

The resolution makes a DEMO candidate eligible for a separately designed later authorization,
but BUILD-03A itself has no authorization artifact or execution capability. It keeps all of the
following false:

- execution;
- runtime wiring;
- source mutation;
- geometry repair;
- source Z-dimension removal;
- production activation;
- raw source disclosure;
- redistribution;
- promotion of DEMO policy to official or production authority.

## 7. Artifact identity

Golden BUILD-03A gate-resolution SHA-256:

`a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01`

The artifact uses the exact frozen Core `canonical_sha256` provider. Any change to the human
statement, explanations, recommendations, approved values, DEMO boundaries, predecessor chain,
or no-authorization effect fails closed even when rehashed.

## 8. Acceptance results

Environment:

- Python 3.13.5;
- pytest 9.1.1;
- Ruff static acceptance passed.

Results:

- BUILD-03A focused acceptance: **43 passed**;
- BUILD-00A through BUILD-03A + portrayal review + frozen Core: **206 passed**;
- complete repository regression: **756 collected; 753 passed; 3 failed**.

The three failures are the exact known, pre-existing Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD, Core, ROAD, School Hero, or Agent contract regression was introduced.

## 9. Exact changed files

1. `BUILD-03A-Completion-Report.md` — approval, recorded explanations, resolutions, boundaries, acceptance, and readiness.
2. `build_contracts/__init__.py` — BUILD-03A public resolution-contract exports.
3. `build_contracts/gate_resolution.py` — deterministic human-approved DEMO resolution contract.
4. `data/specifications/nma-build-03a-golden-gate-resolution-v1.0.json` — frozen scoped decision artifact.
5. `schemas/build-gate-resolution-v1.0.schema.json` — closed Draft 2020-12 resolution schema.
6. `tests/test_build_gate_resolution_build03a.py` — approval, recording, scope, tamper, privacy, determinism, and non-execution acceptance.

Existing production `src/nma` changed: **no**.

BUILD-00A through BUILD-03, frozen Core, ROAD, School Hero, Agent, official portrayal evidence,
public runtime, and private archive files changed: **no**.

## 10. BUILD-04 readiness recommendation

**CONDITIONAL GO — BUILD-04 MAY ENTER ONLY AS A DEMO-SCOPED AUTHORIZATION DESIGN STAGE.**

BUILD-04 may bind the exact BUILD-03A resolution and design a non-transferable, revocable DEMO
capability. It must not treat BUILD-03A as production approval, change official evidence, mutate
the source, remove source Z, or activate a production runtime. Actual execution remains forbidden
until BUILD-04 independently defines and validates the allowed DEMO operations and consumption
boundary.

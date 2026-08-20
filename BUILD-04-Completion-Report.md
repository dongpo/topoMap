# BUILD-04 — Single-Use Building DEMO Authorization Completion Report

Completion date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-04 IS COMPLETE AS A SINGLE-USE, NON-TRANSFERABLE, REVOCABLE DEMO AUTHORIZATION STAGE**

BUILD-04 issues one capability bound to the exact BUILD-03A human-approved DEMO resolution. The
capability can be consumed only once, only for the exact J13 building reference, and only to
render a derived MapLibre web DEMO. The hatch angle is the sole adjustable parameter.

The authorization is issued but not consumed. BUILD-04 validates consumption requests and returns
a `validated-not-executed` plan; it does not access the source, render output, persist consumption,
wire a runtime, or activate production behavior.

## 2. Exact predecessor and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Required predecessor branch | `build/build-03a-human-gate-resolution` | PASS |
| Required predecessor SHA | `baf64a59f0b12ea8ab1b9a7ddbdff1d39e3578bc` | PASS |
| BUILD-03A resolution | `a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01` | PASS |
| BUILD-03 review | `4177a2cc29738ad7b1bc6f00f2c10c724fec3c475e57dee45ad2e8e1f105cbdd` | PASS |
| BUILD-02 proposal | `1e588ea2d7752ce7b02c28d6117c4deb1d6c8995dcbace14cfcb542eca847749` | PASS |
| BUILD-02 decision | `624fafe1f84164f6f28396d21153a3ed0f9795ead87b6e9c605115b35ee3c846` | PASS |
| BUILD-01 semantic package | `59b6f972046dbe9af295de414525230b03ed6da4f0e78374076b5cc4a2cdd7de` | PASS |
| BUILD-04 branch | `build/build-04-demo-authorization-boundary` | PASS |
| Starting tracked worktree | clean | PASS |

## 3. Authorization issuance

The authorization records:

- authorization ID: `build-04-demo-auth-a5a8f11b94784a60`;
- issuance decision: `issue-single-consumption-build-demo-authorization`;
- phase-entry statement: `進行 BUILD-04。`;
- basis: exact human-approved BUILD-03A DEMO resolution;
- status: `issued-not-consumed`.

An absent issuance decision creates nothing. Generic `approved`, `execute`, or abbreviated phase
strings cannot issue this capability.

## 4. Non-transferable capability scope

The capability is frozen to:

- target: `derived MapLibre web DEMO portrayal candidate`;
- operation: `render-derived-maplibre-building-demo`;
- source archive SHA-256:
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`;
- fixture:
  `build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a`;
- layer: `J13_BUILD`;
- feature code: `9310100`;
- feature reference:
  `build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f`;
- source access mode: read-only single feature, and only after consumption validation.

Changing the archive, fixture, layer, feature code, feature reference, target, or operation makes
the request non-transferable and fails closed.

## 5. User-adjustable DEMO angle

The only permitted override is `hatch.numeric_angle_degrees`:

- minimum: 0 degrees inclusive;
- maximum: 180 degrees exclusive;
- default: 45 degrees;
- step: 1 degree;
- scope: DEMO only.

All other BUILD-03A portrayal fields remain fixed. Non-numeric, non-finite, fractional, negative,
or 180-degree-and-higher values fail closed. A valid non-default value is marked
`user_adjusted_from_default: true` in the non-executing plan.

## 6. Lifecycle, expiry, revocation, and idempotency

The capability is:

- single-consumption;
- non-transferable;
- revocable before consumption;
- expired by first consumption, explicit revocation, or any predecessor change;
- protected by a required restricted-character idempotency key.

The consumption guard accepts caller-provided revoked and consumed authorization state. A revoked
authorization cannot be planned. A consumed authorization cannot be reused. The raw idempotency
key is not returned; only its Core canonical SHA-256 commitment appears in the plan.

## 7. Permission and execution boundary

The authorization permits a later controlled DEMO consumer to read only the exact bound feature
after validation. It keeps all of the following forbidden:

- production execution;
- source write or mutation;
- geometry repair;
- source Z-dimension removal;
- runtime wiring;
- network access;
- raw source disclosure;
- redistribution;
- promotion of DEMO policy to official or production authority.

BUILD-04 itself contains no source reader, renderer, geometry library, MapLibre adapter, network,
filesystem write, persistence, or execution capability.

## 8. Non-executing consumption plan

The golden 45-degree request validates to a plan with:

- status `validated-not-executed`;
- `user_adjusted_from_default: false`;
- source accessed: false;
- source mutated: false;
- runtime wired: false;
- production activated: false;
- execution performed: false.

Golden plan SHA-256:

`b8b5ecd54954b190eb8cda398710039f334e8424fd0969816380b4a2b52b0b71`

This plan is a validation result only. It is not a receipt or consumption record.

## 9. Artifact identity

Golden BUILD-04 authorization SHA-256:

`f609fa99ae0280987e11a3328e04d26484c15a65f72a0266566f2aaa9f650b2d`

The authorization and plan use the exact frozen Core `canonical_sha256` provider. Any change to
scope, source identity, angle range, lifecycle, revocability, permissions, or no-execution effect
fails closed even when rehashed.

## 10. Acceptance results

Environment:

- Python 3.13.5;
- pytest 9.1.1;
- Ruff static acceptance passed.

Results:

- BUILD-04 focused acceptance: **56 passed**;
- BUILD-00A through BUILD-04 + portrayal review + frozen Core: **262 passed**;
- complete repository regression: **812 collected; 809 passed; 3 failed**.

The three failures are the exact known, pre-existing Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD, Core, ROAD, School Hero, or Agent contract regression was introduced.

## 11. Exact changed files

1. `BUILD-04-Completion-Report.md` — authorization scope, lifecycle, consumption boundary, acceptance, and readiness.
2. `build_contracts/__init__.py` — BUILD-04 public authorization exports.
3. `build_contracts/demo_authorization.py` — issuance, validation, revocation/reuse guard, and non-executing consumption planning.
4. `data/specifications/nma-build-04-golden-demo-authorization-v1.0.json` — frozen single-use authorization.
5. `schemas/build-demo-authorization-v1.0.schema.json` — closed Draft 2020-12 authorization schema.
6. `tests/test_build_demo_authorization_build04.py` — issuance, binding, angle, lifecycle, tamper, privacy, and non-execution acceptance.

Existing production `src/nma` changed: **no**.

BUILD-00A through BUILD-03A, frozen Core, ROAD, School Hero, Agent, official portrayal evidence,
public runtime, and private archive files changed: **no**.

## 12. BUILD-05 readiness recommendation

**CONDITIONAL GO — BUILD-05 MAY ENTER ONLY AS THE CONTROLLED SINGLE-CONSUMPTION DEMO EXECUTION STAGE.**

BUILD-05 must validate the exact authorization and request, check revocation and prior consumption,
read only the exact bound J13 feature, render only the derived DEMO artifact, preserve the source
`PolygonZ`, write an immutable consumption record and receipt, and prevent replay. It must not
wire production runtime behavior, disclose raw private source data, or promote DEMO policies to
official authority.

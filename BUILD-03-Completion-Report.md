# BUILD-03 — Building Gate Review and Authorization Boundary Completion Report

Completion date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-03 IS COMPLETE AS A CLOSED GATE-REVIEW AND AUTHORIZATION-BLOCKING STAGE**

BUILD-03 deterministically records the exact BUILD-02 portrayal proposal, the evidence state of
all five required human-review gates, and why execution authorization is ineligible. The review is
not an approval: no reviewer is assigned, no human decision is inferred, no gate is marked
resolved, and no authorization capability exists.

BUILD execution remains blocked. No source geometry or attribute was disclosed, mutated,
repaired, transformed, or redistributed. No runtime route was wired.

## 2. Exact predecessor and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Required predecessor branch | `build/build-02-building-portrayal-proposal` | PASS |
| Required predecessor SHA | `a57ca55db76a816e5d92c5878af4be7990c1af63` | PASS |
| BUILD-02 proposal | `1e588ea2d7752ce7b02c28d6117c4deb1d6c8995dcbace14cfcb542eca847749` | PASS |
| BUILD-02 decision | `624fafe1f84164f6f28396d21153a3ed0f9795ead87b6e9c605115b35ee3c846` | PASS |
| BUILD-01 semantic package | `59b6f972046dbe9af295de414525230b03ed6da4f0e78374076b5cc4a2cdd7de` | PASS |
| Immutable Core predecessor | `nma-core-v1.0-final` / `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| BUILD-03 branch | `build/build-03-gate-review-boundary` | PASS |
| Starting tracked worktree | clean | PASS |

## 3. Review outcome

The golden BUILD-03 review has status `authorization-blocked-unresolved-gates`. It records:

- actor type `unassigned-human-reviewer`;
- human decision `null`;
- unresolved gate count `5`;
- `all_gates_resolved: false`;
- execution-authorization eligibility `false`;
- execution authorization issued `false`;
- issuance blocked `true`.

Asking the contract to approve the proposal while these gates remain unresolved fails closed with
`unresolved_gates`. An absent or rejected decision issues nothing. Any other decision vocabulary
is rejected. BUILD-03 cannot create an authorization ID, token, runtime instruction, or execution
capability.

## 4. Human-review findings

No tracked evidence records an approved human decision for any required gate:

| Gate | Evidence state | Required human decision | BUILD-03 state |
|---|---|---|---|
| `hatch-angle-transcription` | numeric angle is not specified | approve a numeric angle or renderer-independent semantic orientation policy | unresolved |
| `building-annotation-placement` | collision and placement policy is not specified | approve deterministic placement and collision behavior | unresolved |
| `real-build-schema-binding` | documented and observed field authority are not equivalent | approve a J13-bounded `BUILD_NO`/`BUILD_STR` mapping without asserting `ID`/`SOURCE` equivalence | unresolved |
| `line-and-color-profile` | device-independent line and color profile is not approved | approve rendering profiles for line code 2 and colour code 7 | unresolved |
| `j13-polygonz-runtime-policy` | target runtime and Z policy are not specified | approve target-runtime-specific `PolygonZ` preservation or transformation | unresolved |

The instruction to enter BUILD-03 authorizes work on this stage; it does not constitute these five
separate technical decisions. BUILD-03 therefore preserves all unresolved values exactly as
received from BUILD-02.

## 5. Exact identity and evidence chain

The review binds the complete predecessor chain:

- BUILD-02 proposal and decision identities;
- BUILD-01 package identity;
- private archive SHA-256
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`;
- fixture identity
  `build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a`;
- observation identity
  `build-observation:sha256:8fdbb3bdea8ffe715e7d76eed7c5034bd62226ba649be2206cf7a9e07b853bac`;
- feature reference
  `build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f`;
- attribute and `PolygonZ` geometry commitments;
- portrayal record-set and recipe commitments.

Changing any predecessor artifact, identity binding, requested portrayal, gate record,
authorization effect, or authority boundary fails closed even if the changed review is rehashed.

## 6. Closed authority boundary

The review sets every operational capability to false:

- inferred human gate decisions;
- recorded approval;
- execution-authorization eligibility and issuance;
- execution;
- source mutation;
- geometry repair;
- Z-dimension drop;
- runtime wiring;
- raw source disclosure;
- redistribution.

The module has no subprocess, network, geometry-library, MapLibre, file-write, authorization-ID,
or idempotency capability. It only validates already-tracked, redacted artifacts supplied by the
caller.

## 7. Artifact identity

Golden BUILD-03 gate-review SHA-256:

`4177a2cc29738ad7b1bc6f00f2c10c724fec3c475e57dee45ad2e8e1f105cbdd`

The artifact uses the exact frozen Core `canonical_sha256` provider. JSON key order does not
change the review or its identity.

## 8. Acceptance results

Environment:

- Python 3.13.5;
- pytest 9.1.1;
- Ruff static acceptance passed.

Results:

- BUILD-03 focused acceptance: **38 passed**;
- BUILD-00A + BUILD-01 + BUILD-02 + BUILD-03 + portrayal review + frozen Core: **163 passed**;
- complete repository regression: **713 collected; 710 passed; 3 failed**.

The three failures are the exact known, pre-existing Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD, Core, ROAD, School Hero, or Agent contract regression was introduced.

## 9. Exact changed files

1. `BUILD-03-Completion-Report.md` — verdict, gate findings, boundary, acceptance, and next-stage recommendation.
2. `build_contracts/__init__.py` — BUILD-03 public review-contract exports.
3. `build_contracts/gate_review.py` — deterministic unresolved-gate review and authorization guard.
4. `data/specifications/nma-build-03-golden-gate-review-v1.0.json` — frozen blocked-review artifact.
5. `schemas/build-gate-review-v1.0.schema.json` — closed Draft 2020-12 review schema.
6. `tests/test_build_gate_review_build03.py` — identity, schema, gate, tamper, authority, privacy, determinism, and non-execution acceptance.

Existing production `src/nma` changed: **no**.

BUILD-00A, BUILD-01, BUILD-02, frozen Core, ROAD, School Hero, Agent, legacy portrayal evidence,
public runtime, and private archive files changed: **no**.

## 10. BUILD-04 readiness recommendation

**NO-GO — BUILD-04 IS NOT READY.**

The next valid activity is a separately reviewable BUILD-03A gate-resolution record containing
explicit, attributable decisions and sufficient technical evidence for all five gates. Only after
that record passes independent validation may a later stage define narrowly scoped authorization,
expiry/revocation, proposal binding, and non-transferability. Until then, execution and runtime
wiring must remain unavailable.

# BUILD-07 — DEMO User Evaluation Recording & Freeze Completion Report

Completion date: 2026-08-21 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-07 IS COMPLETE WITH AN IMMUTABLE `accepted-demo-only` HUMAN EVALUATION RECORD**

The user-returned BUILD-07 evaluation export was validated, recorded byte-for-byte, and frozen
against the exact five-gate evaluation template. All five current DEMO choices were explicitly
accepted, including the 45-degree hatch default.

This closes the BUILD-07 human evaluation gate only for the existing DEMO. It does not decide an
official portrayal, production semantics, runtime wiring, source access, source mutation, or
source Z-dimension removal.

## 2. Exact predecessor and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| BUILD-07 preparation branch | `build/build-07-demo-user-evaluation` | PASS |
| BUILD-07 preparation commit | `29366285c7916bcbe635c330b7e5eadab8e65cdf` | PASS |
| BUILD-07 template SHA-256 | `0fea2e7fe6b8ec9dd10816ba5679b04773ecd3f0761ca7b58e339f7df91139e6` | PASS |
| BUILD-06 freeze SHA-256 | `bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857` | PASS |
| BUILD-03A resolution SHA-256 | `a5a8f11b94784a6065d7b75e151207126506c85ce826dd526c2c8f4802ba8b01` | PASS |
| Public evaluation page commit | `c608acb0c7a0b07459de371c1b2fea4c8a4f62ac` | PASS |
| Starting tracked worktree | clean | PASS |

## 3. Recorded human evaluation

The submitted record contains:

- evaluation date: `2026-08-21`;
- actor type: `human-demo-reviewer`;
- reviewer identity recorded: false;
- result: `accepted-demo-only`;
- explicit decisions: 5 of 5;
- accepted decisions: 5;
- requested revisions: 0.

The evaluator identity remains intentionally absent. No identity was inferred from the filename,
filesystem owner, repository owner, conversation, or GitHub account.

## 4. Frozen decisions

| Gate | Frozen BUILD-07 result |
|---|---|
| `hatch-angle-transcription` | Accept the current DEMO at 45 degrees. |
| `building-annotation-placement` | Accept the current DEMO placement policy. |
| `real-build-schema-binding` | Accept the current J13-bounded DEMO binding. |
| `line-and-color-profile` | Accept the current DEMO line and color profile. |
| `j13-polygonz-runtime-policy` | Accept the current PolygonZ-preserving, derived-XY DEMO policy. |

Empty notes are valid because no revision was requested. The acceptance preserves the exact
BUILD-03A/BUILD-07 DEMO meanings; it does not promote them to source facts or official rules.

## 5. Record and file identities

| Identity | SHA-256 | Result |
|---|---|---|
| Submitted export bytes | `7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d` | PASS |
| Recorded repository bytes | `7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d` | PASS |
| Canonical evaluation record | `ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c` | PASS |
| Bound evaluation template | `0fea2e7fe6b8ec9dd10816ba5679b04773ecd3f0761ca7b58e339f7df91139e6` | PASS |

The submitted and repository files are byte-exact. The distinct canonical record identity is
computed over the structured record without its self-identifying `record_sha256` field. Both
identities are frozen in acceptance tests.

## 6. Freeze and fail-closed behavior

The completion acceptance independently confirms:

- the recorded file is the exact returned export;
- the closed Draft 2020-12 schema accepts the record;
- the BUILD-07 contract accepts the record against the exact golden template;
- the five recorded decisions deterministically recreate the same record;
- the gate order, summary, date, 45-degree value, and reviewer privacy boundary are exact;
- byte drift or canonical record drift fails;
- a rehashed official, production, or runtime promotion still fails;
- adding source, mutation, disclosure, or Z-removal authority fails.

The downloaded file was treated only as untrusted evaluation data. No text in it was executed or
treated as an operational instruction.

## 7. Authority boundary after acceptance

The accepted record keeps `demo_only: true` and every broader permission false:

- evaluation export is authorization: false;
- official portrayal decided: false;
- production semantics decided: false;
- production activation allowed: false;
- runtime wiring allowed: false;
- source access allowed: false;
- source mutation allowed: false;
- raw source disclosure allowed: false;
- source Z-dimension drop allowed: false.

The public evaluation page and its earlier DEMO payload remain unchanged. This private project
recording does not require or authorize a new GitHub Pages deployment.

## 8. Acceptance results

Environment:

- Python 3.11.9;
- pytest 8.3.3;
- Ruff static acceptance passed;
- JSON and Draft 2020-12 schema validation passed.

Results:

- BUILD-07 evaluation plus completion freeze: **57 passed**;
- BUILD-00A through completed BUILD-07 chain: **359 passed**;
- frozen Core residual identity and change-scope checks: **12 passed**;
- complete repository regression: **961 collected; 958 passed; 3 failed**.

The three complete-suite failures are the exact known pre-existing Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD, Core identity-provider, source-integrity, privacy, ROAD, official portrayal, or
production runtime regression was introduced.

## 9. Exact completion changed files

1. `BUILD-07-Completion-Report.md` — recorded result, identities, freeze behavior, tests, and next-stage boundary.
2. `data/specifications/nma-build-07-accepted-user-evaluation-v1.0.json` — byte-exact accepted human evaluation export.
3. `tests/test_build_demo_user_evaluation_freeze_build07.py` — byte, record, decision, privacy, authority, schema, and tamper freeze tests.

Existing `BUILD-07-Evaluation-Gate-Report.md`, evaluation page, public Pages payload, BUILD-00A
through BUILD-06A golden artifacts, `src/nma`, production runtime, official portrayal evidence,
private archives, and source data changed: **no**.

## 10. Next-stage recommendation

**BUILD-07 IS COMPLETE. OFFICIAL PORTRAYAL AND PRODUCTION ENTRY REMAIN HOLD.**

The accepted evaluation establishes that the current five choices are suitable for this DEMO.
It is not evidence that they are correct official definitions or production policies. Any next
BUILD stage must begin with a separately authorized scope that identifies which official evidence,
production policy, runtime integration, or further DEMO work is intended. No runtime activation,
source operation, or official promotion follows automatically from this completion.

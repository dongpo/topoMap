# CORE-FINAL Completion Report

## Verdict

PASS

## Baseline

- Canonical root: `/Users/dongpodeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/topoMap`
- Predecessor branch: `core/core-04-residual-identity-audit`
- Predecessor SHA: `e460b241e0b5b6d1340a329b18f7c978c13c7dc3`
- CORE-04 verdict: `PASS — BOUNDED-CLOSURE`
- Starting local SHA: `e460b241e0b5b6d1340a329b18f7c978c13c7dc3`
- Starting upstream SHA: `e460b241e0b5b6d1340a329b18f7c978c13c7dc3`
- Starting remote SHA: `e460b241e0b5b6d1340a329b18f7c978c13c7dc3`
- Starting worktree status: clean

## Final Freeze

- FINAL_SHA: the exact peeled target of `nma-core-v1.0-final`.
- Freeze branch: `freeze/core-final-<short-FINAL_SHA>` using that exact peeled target.
- Local branch SHA: `FINAL_SHA`.
- Remote branch SHA: `FINAL_SHA`.
- Branch equality: PASS; local and remote freeze refs resolve to the annotated tag target.
- Annotated tag: `nma-core-v1.0-final`.
- Tag object SHA: the exact object identity of `refs/tags/nma-core-v1.0-final`.
- Local tag target: `FINAL_SHA`.
- Remote tag target: `FINAL_SHA`.
- Tag equality: PASS; the local and remote annotated tag objects and peeled targets are equal.
- Final worktree status: clean.

The repository's established ROAD-FINAL convention is intentionally non-self-referential: a
tracked blob cannot contain the SHA of the commit that contains that blob. The immutable annotated
tag is therefore the in-repository authority for the exact final commit. The exact commit, branch,
and tag-object SHAs are recorded after publication in the GEO-130 delivery and Linear evidence.

## Architecture Closure

- Core canonical identity ownership: PASS
- ROAD provider adoption: PASS
- School execution adoption: PASS
- School verification adoption: PASS
- authorization semantics preserved: PASS
- self-hash semantics preserved: PASS
- residual provider count: 0
- fallback/stub provider count: 0
- missing-Core fail-closed: PASS
- missing-Core no-mutation: PASS

`nma.core.canonical_json` and `nma.core.canonical_sha256` are the sole generic canonical JSON and
SHA-256 primitive. ROAD resolves through the exact Core objects. School Hero execution and
verification import the exact Core objects. ROAD and School authorization field selection and
record self-hash field exclusion remain in their domain modules.

The missing-Core tests use deliberately minimal isolated checkouts with `PYTHONDONTWRITEBYTECODE=1`.
Entity resolution, Neo4j retrieval, the runtime graph script, School execution, and School
verification fail before identity processing with deterministic `ModuleNotFoundError: No module
named 'nma.core'`. Complete before/after file manifests are equal, no `src/nma/core` replacement is
created, and no fallback, stub, copy, repair, or reconstruction is observed.

## Acceptance Results

- CORE: `53 passed`
- ROAD historical: `199 passed`
- School Hero: `42 passed`
- ROAD schemas: `15 PASS`
- final manifest validation: PASS
- fresh-checkout CORE: `53 passed`
- fresh-checkout ROAD historical: `199 passed`
- fresh-checkout School Hero: `42 passed`
- fresh-checkout ROAD schemas: `15 PASS`
- fresh-checkout provider audit: residual `0`; fallback/stub `0`
- fresh-checkout missing-Core fail-closed/no-mutation: PASS
- canonical/fresh-checkout acceptance equality: PASS

No previously passing CORE, ROAD, or School test became skipped, xfailed, or deselected. The
CORE-04 exact-scope assertion is pinned to the immutable CORE-03-to-CORE-04 commit range so that it
continues to prove exactly three production/script changes without treating later evidence-only
freeze commits as CORE-04 implementation changes.

## Known Non-Core Baseline Failures

The complete candidate run reports `477 passed, 3 failed`. The same three exact node IDs were run
under the same Python 3.11.9 / pytest 8.3.3 environment in an isolated clean checkout at exact
CORE-03 commit `c661e7b06aa6810362c62809afdfd5345a2e1689`.

### `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`

- Candidate failure signature: `AssertionError`; generated capability `9920103` has editable
  parameters `[scale, color, stroke_width, outline, opacity, rotation, flag_top_alignment,
  support_shape, support_proportion, flag_attachment]`, while the tracked expected catalog adds
  `flagpole_horizontal_alignment`.
- CORE-03 failure signature: the same `AssertionError`, capability code, observed list, and expected
  list.
- Reproduction result: MATERIALLY IDENTICAL.
- Classification: PRE-EXISTING / NON-CORE.

### `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`

- Candidate failure signature: `ValueError: scripts/run_nma_agent_server.py size: expected 29586,
  got 133875`.
- CORE-03 failure signature: the same exception type, path, expected value, and observed value.
- Reproduction result: MATERIALLY IDENTICAL.
- Classification: PRE-EXISTING / NON-CORE.

### `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

- Candidate failure signature: `ValueError: data/demo/pmtiles-capability-catalog.json size differs
  from the candidate manifest`.
- CORE-03 failure signature: the same exception type, asset path, and functional failure mode.
- Reproduction result: MATERIALLY IDENTICAL.
- Classification: PRE-EXISTING / NON-CORE.

No fix attempted under CORE-FINAL.

## Integrity

- Core source equality: PASS. Inventory is exactly `src/nma/core/__init__.py`,
  `src/nma/core/feature_profile.py`, and `src/nma/core/identity.py`; all are byte-identical to
  `ce6e90c993cb36782da29d7e24369882eb303476`; mismatch count: `0`.
- Canonical Core source SHA-256 values: `a3e410a77ece724eaf505ce8b9dc6694b808d4a7cc96a720500757578077a4f2`,
  `e0de362e5f733f0f1d7d5776f830939922a6d66cc552e05186046ca0d71e09f0`, and
  `d9c4ac0d0d385f6942c552a0b2ffc4c12b3deb0ee876d569aeadc036b1a92e78` in inventory order.
- ROAD frozen equality: PASS; fixtures, goldens, authorization, plan, derived portrayal, runtime
  bundle, observations, receipts, rollback, QA, provenance, schemas, and accepted specifications
  are byte/hash exact. The complete historical suite reproduces all frozen identities.
- School frozen equality: PASS; fixtures, source/public data, execution/runtime records,
  authorization, verification, rollback, QA, provenance, schemas, and accepted freeze records are
  byte/hash exact. The complete School suite reproduces all accepted identities.
- Historical tag integrity: PASS. `nma-core-v0.1-baseline` tag object
  `d86b77392c1dc9c9edc1d4adc370fc73e7e14f75` peels to
  `ce6e90c993cb36782da29d7e24369882eb303476`; `nma-road-v1.0-final` tag object
  `d60fffa873428d1ba8b308ea0d4d2028ac8431fd` peels to
  `325c70d5335f57c43a8af85822db25032aa225c3`; the accepted Hero references remain at
  `75f80d389fe48b6dc33912e45433dc1d7e7b98b5` and
  `56f99eb9ae63272a68accac3041fb10eacefb986`.
- Freeze manifest integrity: PASS; deterministic JSON, contract `nma-core-final-freeze/1.0`, no
  timestamp, no invented self-hash, and exact Core file hashes.
- Private archive status: SHA-256
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`; ignored,
  untracked, unstaged, unmodified, and unpublished.
- Changed-file inventory relative to CORE-04:
  1. `CORE-FINAL-Completion-Report.md` — final acceptance evidence.
  2. `data/specifications/nma-core-final-freeze-manifest-v1.0.json` — deterministic freeze manifest.
  3. `tests/test_core04_residual_identity_audit.py` — historical CORE-04 range pin only.
- production source changed: NO
- canonical/fresh-checkout equality: PASS

## Final Recommendation

CORE identity architecture FROZEN. Further Core changes require a separately authorized post-freeze issue.

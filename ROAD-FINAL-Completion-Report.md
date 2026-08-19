# ROAD-FINAL Completion Report

## Verdict

PASS

ROAD is accepted for immutable freeze. The historical lineage is preserved exactly as
`ROAD-05 → ROAD-05A corrective closure → ROAD-FINAL`; this report does not rewrite ROAD-05 as
though it originally contained the ROAD-05A authorization-consumption correction.

## Repository and Lineage

- Canonical root: `/Users/dongpodeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/topoMap`
- Origin: `https://github.com/dongpo/topoMap.git`
- ROAD-05 branch: `road/road-05-qa-provenance`
- Accepted ROAD-05 SHA: `5d23274d7c5d90f86506646de9deb0cc77d86921`
- ROAD-05A branch: `road/road-05a-authorization-consumption-determinism`
- Accepted ROAD-05A SHA: `e2bf999cd19e830d5687da52b826b0fedf69db6a`
- ROAD-05A ancestry: exactly one commit descended from the accepted ROAD-05 SHA
- ROAD-FINAL branch pattern: `freeze/road-final-<short FINAL_SHA>`
- Annotated tag: `nma-road-v1.0-final`
- FINAL_SHA and annotated tag object SHA: recorded after the evidence commit because a commit
  cannot contain its own identity without changing that identity

## ROAD-05A Corrective-Diff Audit

The complete `5d23274d...e2bf999c` diff contains exactly nine reviewed files:

1. `data/specifications/nma-road-hero-road-04-authorization-consumption-fixture-v1.0.json`
2. `docs/ROAD-05-QA-PROVENANCE.md`
3. `schemas/road-authorization-consumption-fixture-v1.0.schema.json`
4. `scripts/build_road04_goldens.py`
5. `scripts/verify_road_authorization_consumption.py`
6. `src/nma/road_authorization_consumption.py`
7. `src/nma/road_verification.py`
8. `tests/test_road_execution_road04.py`
9. `tests/test_road_verification_road05.py`

The correction only closes deterministic reconstruction and validation of the historical
authorization consumption. It does not alter ROAD execution semantics, geometry, labels, shields,
runtime artifacts, QA identity, or provenance identity. No existing acceptance assertion was
weakened; canonical consumption and ledger assertions were added.

## Authorization-Consumption Contract

- Contract: `road-05a-authorization-consumption/1.0`
- Canonical key: `road04-controlled-execution-v1`
- Key serialization: exact UTF-8 bytes, without normalization or line ending
- Algorithm: SHA-256
- Idempotency hash:
  `d4645499a8a897194ed49d7cd19edb6acd96bda5db0611fd82a701a875f343cb`
- Consumption serialization: sorted keys, compact separators, UTF-8, exactly one trailing LF
- Consumption-file SHA-256:
  `fb21f714f925922938198ac9299a42ea87aaab89b2860d5518a49f5467571330`
- Reconstructed bytes equal accepted runtime and ledger bytes: PASS
- Canonical-key mutation fails validation: PASS
- Canonical reconstruction: PASS
- Fresh remote reconstruction: PASS
- Minimal-root reconstruction: PASS

The minimal root contained only the standalone verifier, its two permitted source dependencies,
the package marker, and the tracked consumption fixture. It contained no `.git`, runtime artifacts,
ledger, private archive, caches, or environment files.

## Complete Accepted Chain

| Node | Accepted identity |
|---|---|
| Authorization | `f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38` |
| Plan | `e51e42b955ade0d3ff5c6b8fbe00919aac4d9b9f90fe59bd548e14b7a9bf04a0` |
| Derived artifact | `fb8762642e4e3e633912028b18ca6aa11545117e15572839896770537a5971b6` |
| Runtime bundle | `33aa7c6b0d557fa9a72e2fa4e0106493d8dfe10ec9201bd7762e204bb14a286d` |
| Observation | `e5263aa67dbb400e0c3a63b7cd1457d9d95428a8d519aef34b3c9b4396ce1d9a` |
| Receipt | `0ab5964fcc2e1f47d43fd328dbc3771a7e624bf4a3707f91236a1485f5610720` |
| Rollback | `03bc4f84d27b9b55baa7403d4ff4abc758ff223d0ffe7b7aaaa11233da162ae2` |
| Authorization consumption | `d4645499a8a897194ed49d7cd19edb6acd96bda5db0611fd82a701a875f343cb` |
| QA | `8f31ecb25f62b5bc71465db33503a7c37d63fe18e9006ce6801a2ab639464a82` |
| Provenance | `130a24e15126743466b57dc03e2ca8a652335553b56522e316f47104cc9dbc70` |

No identity drift was observed.

## Geometry, Label, Shield, and Visual Boundary

- Source geometry file SHA-256:
  `8baf555b9d4b69bf9e56731fe2233a29822c897f095d0f6257436aa192c89bea`
- Runtime geometry file SHA-256:
  `d13096fb82a1e0588898ade94070becec531ebc07e77fe7795a3d92f8d56db08`
- Ordered segments: `K0000004671`, `K0000004913`, `K0000005348`
- CRS: `TWD97[2020]_TM121` source; `EPSG:4326` runtime
- Source/runtime vertex counts: `4 / 3 / 4`
- Exact source/runtime reconstruction and order: PASS
- Label: exactly one rendered line-following `中山街`; no duplicate or unrelated contamination
- Shield: `9490005`, `road-parallel`, `semantic_binding_only`; no fabricated graphic or
  literal replacement
- Screenshot evidence SHA-256:
  `4124aef859cd71847f4515ad9bbf09039f35dfeacee37dd78a06921b43379062`
- Independent visual/pixel oracle: absent
- Pixel-perfect verification: not claimed

## Canonical Acceptance

- Authorization consumption: PASS
- ROAD-05 focused: `39 passed`, 0 failed, 0 skipped
- Combined ROAD: `199 passed`, 0 failed, 0 skipped
- School Hero: `11 passed`, 0 failed, 0 skipped
- ROAD schemas: `15 PASS`
- Canonical fixture and emitted record validation: PASS
- Accepted ROAD-05A Ruff check: PASS
- Accepted ROAD-05A format check: PASS
- Tamper and mutation validation: PASS

The accepted lint/format gate covers the ROAD-05A corrective Python scope. Unrelated historical
repository-wide lint/format findings are outside this evidence-only freeze and were not modified.

## Fresh Remote Reproduction

A fresh clone of the remote ROAD-05A branch resolved to exact HEAD
`e2bf999cd19e830d5687da52b826b0fedf69db6a`. The private archive remained ignored, untracked,
unstaged, and byte-identical at
`4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.

Runtime state was regenerated from the private archive and frozen tracked inputs. The regenerated
consumption, plan, derived artifact, bundle, observation, receipt, rollback, QA, and provenance
files were byte-identical to the canonical accepted files.

- Fresh combined ROAD: `199 passed`
- Fresh School Hero: `11 passed`
- Fresh ROAD schemas: `15 PASS`
- Fresh accepted-scope Ruff/format: PASS
- Canonical/fresh determinism: PASS

## Final Tamper Gate

Fail-closed behavior was confirmed for canonical-key, fixture-shape, contract-version,
authorization-binding, expected-idempotency-hash, consumption-serialization,
expected-consumption-hash, ROAD artifact substitution, provenance-parent binding, frozen-source,
archive, geometry, label, shield, screenshot, and unexpected-artifact mutations. Rehashed
substitutes did not bypass validation. No auto-repair or silent regeneration occurred.

## Evidence-Only Scope and Immutability

ROAD-FINAL changes only:

1. `data/specifications/nma-road-final-freeze-manifest-v1.0.json`
2. `ROAD-FINAL-Completion-Report.md`

ROAD-FINAL does not modify `src/nma`, ROAD-05A implementation, tests, schemas, ROAD execution,
School Hero, canonical runtime, or frozen ROAD artifacts. The ROAD-05 and ROAD-05A remote branches
remain at their accepted SHAs. The private archive remains ignored, untracked, unstaged, and
unchanged.

## Final Statement

All pre-commit ROAD-FINAL acceptance gates pass. Branch, remote, tag, final-checkout, and final-tree
identities are recorded and reverified after the evidence-only commit.

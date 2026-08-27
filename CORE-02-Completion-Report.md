# CORE-02 Completion Report

## 1. Verdict

PASS. GEO-128 adopts the frozen NMA Core canonical identity provider at the ROAD provider boundary,
preserves all accepted identities, repairs the ROAD-05 minimal-checkout dependency closure, and
passes every required acceptance gate.

## 2. Baseline and Branch

- Canonical root: `/Users/dongpodeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/topoMap`
- Branch: `core/core-02-road-identity-adoption`
- Core baseline tag: `nma-core-v0.1-baseline`
- Core baseline tag object: `d86b77392c1dc9c9edc1d4adc370fc73e7e14f75`
- Core baseline commit: `ce6e90c993cb36782da29d7e24369882eb303476`
- Historical ROAD tag: `nma-road-v1.0-final`
- Historical ROAD tag object: `d60fffa873428d1ba8b308ea0d4d2028ac8431fd`
- Historical ROAD commit: `325c70d5335f57c43a8af85822db25032aa225c3`
- Local and remote annotated tags peel to the expected commits.

## 3. Exact Changed Files

1. `src/nma/road_resolution.py` — replaces the duplicate canonical identity implementation with
   imports from `nma.core`; formatter-only normalization is included in this authorized file.
2. `tests/test_core02_road_identity_adoption.py` — adds focused provider, parity, frozen-identity,
   non-finite-value, transitive-adoption, and Core-immutability tests.
3. `tests/test_road_verification_road05.py` — repairs only the minimal-checkout dependency closure
   and adds explicit dependency-presence/removal assertions.
4. `CORE-02-Completion-Report.md` — this report.

No other tracked file changed.

## 4. Provider Architecture

Before CORE-02, `nma.road_resolution` locally implemented `canonical_json` and
`canonical_sha256`. ROAD-02, ROAD-03, and ROAD-04 consumed the local hash provider through their
existing imports from `road_resolution`.

After CORE-02, `nma.road_resolution` imports and re-exports the exact `nma.core.canonical_json` and
`nma.core.canonical_sha256` function objects. ROAD-02, ROAD-03, and ROAD-04 continue using their
unchanged compatibility imports, so the complete provider-consumer chain is:

`nma.core` → `road_resolution` → ROAD-02 → ROAD-03 → ROAD-04 → ROAD-05 verification.

The public compatibility names `nma.road_resolution.canonical_json` and
`nma.road_resolution.canonical_sha256` remain available. Object-identity tests prove that both are
the Core functions and that the hash functions consumed by ROAD-02, ROAD-03, and ROAD-04 resolve
to the same Core provider. ROAD-04's separate `canonical_json` write serializer was not migrated.

## 5. ROAD-05 Minimal Checkout

PASS. The reconstructed checkout now copies the actual tracked canonical package files:

- `src/nma/core/__init__.py`
- `src/nma/core/identity.py`
- `src/nma/core/feature_profile.py`

The test verifies that these bytes equal the canonical checkout, imports `nma.road_resolution`
successfully, and reproduces byte-for-byte the same accepted authorization-consumption result as
the canonical checkout. It also verifies that `road_resolution.py` contains the canonical Core
imports and contains no `ImportError` fallback or local `canonical_json`/`canonical_sha256`
implementation.

In a separate temporary copy, the test deliberately removes `src/nma/core`, verifies that import
fails with `ModuleNotFoundError: No module named 'nma.core'`, and compares every remaining file
hash before and after the failure. The checkout is neither repaired nor mutated. No tracked or
frozen artifact is changed by this negative test.

## 6. Acceptance Results

- CORE provider adoption: PASS
- ROAD-02 transitive adoption: PASS
- ROAD-03 transitive adoption: PASS
- ROAD-04 transitive adoption: PASS
- ROAD-05 reconstruction/minimal-checkout compatibility: PASS
- CORE-02 focused: `11 passed`, 0 failed, 0 skipped
- CORE-01 regression: `17 passed`, 0 failed, 0 skipped
- Frozen School Hero regression: `11 passed`, 0 failed, 0 skipped
- Complete ROAD-01 through ROAD-05 historical suite: `199 passed`, 0 failed, 0 skipped
- ROAD schemas: `15 PASS`
- Ruff check: PASS for all three authorized Python files
- Ruff format check: PASS for all three authorized Python files

## 7. Accepted Identity Equality

All accepted identities remain exact:

| Identity | Accepted SHA-256 | Result |
| --- | --- | --- |
| ROAD-01 package | `b5df3f57c33843f354371206c937f52d37ddbbd9d047a31ad7c334532ce30e9a` | PASS |
| ROAD-02 proposal | `3d45d1ed039c2af1aa7f050fa1e3c22158c891390c001285054b05a02959ce06` | PASS |
| ROAD-02 decision | `0d671b1fed3f4b19e4204e745bdcb13f872f3a00dcb4ef5050a091a14065e090` | PASS |
| ROAD-03 approval | `f333defee511e0ae82702444d18befe2f9e115d75608ab61a5c20f91c52f2f07` | PASS |
| Authorization | `f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38` | PASS |
| Plan | `e51e42b955ade0d3ff5c6b8fbe00919aac4d9b9f90fe59bd548e14b7a9bf04a0` | PASS |
| Derived | `fb8762642e4e3e633912028b18ca6aa11545117e15572839896770537a5971b6` | PASS |
| Bundle | `33aa7c6b0d557fa9a72e2fa4e0106493d8dfe10ec9201bd7762e204bb14a286d` | PASS |
| Observation | `e5263aa67dbb400e0c3a63b7cd1457d9d95428a8d519aef34b3c9b4396ce1d9a` | PASS |
| Receipt | `0ab5964fcc2e1f47d43fd328dbc3771a7e624bf4a3707f91236a1485f5610720` | PASS |
| Rollback | `03bc4f84d27b9b55baa7403d4ff4abc758ff223d0ffe7b7aaaa11233da162ae2` | PASS |
| Authorization consumption | `d4645499a8a897194ed49d7cd19edb6acd96bda5db0611fd82a701a875f343cb` | PASS |
| QA | `8f31ecb25f62b5bc71465db33503a7c37d63fe18e9006ce6801a2ab639464a82` | PASS |
| Provenance | `130a24e15126743466b57dc03e2ca8a652335553b56522e316f47104cc9dbc70` | PASS |

## 8. Integrity Results

- Prior 79-file School/ROAD inventory: membership remains 79; 77 files are byte-identical and the
  only two mismatches are the authorized `src/nma/road_resolution.py` and
  `tests/test_road_verification_road05.py` changes.
- Frozen ROAD artifacts, schemas, fixtures, goldens, specifications, runtime artifacts, QA,
  provenance, and freeze reports: byte-identical to the baseline.
- School implementation, tests, schemas, and frozen artifacts: byte-identical to the baseline.
- Downstream ROAD implementation files: byte-identical to the baseline.
- Core source (`src/nma/core/__init__.py`, `identity.py`, `feature_profile.py`, and
  `src/nma/feature_profile_adapters.py`): byte-identical to `nma-core-v0.1-baseline`.
- No canonical Core source was copied into ROAD, forked, stubbed, or reimplemented.
- Private archive: SHA-256
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`; ignored,
  untracked, unstaged, and unchanged.

## 9. Commit and Publication

The authoritative final local and remote commit SHA is reported in the task's final response after
this report is committed and the branch is pushed. A commit cannot embed its own SHA in tracked
content because changing that content changes the commit SHA. Publication is accepted only when
the local and remote branch SHAs are equal.

## 10. Recommendation

READY for the next separately authorized, bounded Core adoption. Do not start CORE-03 as part of
CORE-02.

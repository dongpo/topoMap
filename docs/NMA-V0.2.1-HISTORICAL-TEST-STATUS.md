# NMA v0.2.1 Historical Test Status

## Purpose

This record classifies three failures observed during REC-03B full-repository verification. It preserves their status without repairing or redefining the historical Agentic v0.3 freeze and publication artifacts.

## Classification basis

REC-03B reproduced the same failures at parent commit `a74cac89227be6b7552b2136a81ee2ef5412f049`, before the REC-03A alignment commit `25314b9715582c6c67891fa30e1bf69a1f676865` was applied. The REC-03A commit changed the recovered v0.32 runtime identity, vector selection, and provenance documentation; it did not rebuild the PMTiles catalog or revise the historical v0.3 freeze and Pages snapshots.

The failures are therefore classified as:

- pre-existing historical snapshot or catalog drift;
- not caused by REC-03A; and
- excluded from the v0.2.1 runtime-baseline acceptance criteria.

This classification does not mark the historical tests as passing and does not authorize changing their expectations.

## Recorded failures

### 1. PMTiles capability catalog reproducibility mismatch

- Test: `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
- Scope: reproduction of the historical PMTiles capability catalog.
- Observed status: generated catalog content differs from the checked-in historical catalog.
- Classification: pre-existing historical catalog drift; not caused by REC-03A; excluded from v0.2.1 baseline acceptance.

### 2. Historical v0.3 freeze manifest server-size mismatch

- Test: `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
- Scope: verification of frozen Agentic v0.3 artifact fingerprints.
- Observed status: the historical manifest records the Agent server size as 29,586 bytes while the recovered server artifact is 125,905 bytes.
- Classification: expected historical snapshot drift after later runtime development; not caused by REC-03A; excluded from v0.2.1 baseline acceptance.

### 3. Historical Pages-candidate PMTiles catalog-size mismatch

- Test: `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`
- Scope: verification of the frozen Agentic v0.3 Pages candidate manifest.
- Observed status: the historical Pages manifest records a PMTiles catalog size that differs from the current checked-in catalog.
- Classification: pre-existing historical publication-snapshot drift; not caused by REC-03A; excluded from v0.2.1 baseline acceptance.

## v0.2.1 baseline acceptance boundary

REC-03C baseline acceptance is limited to the recovered runtime surfaces reviewed by REC-03A and REC-03B:

- canonical graph identity;
- active v0.32 vector index identity and graph-hash binding;
- Neo4j projection identity and normalized comparison;
- runtime contract `nma.runtime-baseline/0.32`;
- explicit Agent backend selection and fallback reporting;
- existing supported and unsupported golden retrieval behavior; and
- the public School Hero workflow contract and evidence path.

The three failures above belong to older Agentic v0.3 freeze/catalog publication records. They remain visible and unresolved, but they are not evidence of inconsistency in the recovered v0.2.1 runtime baseline.

## Non-action statement

REC-03C does not modify the failing tests, update frozen hashes or sizes, rebuild the PMTiles catalog, change benchmark definitions, or redefine the historical releases. Any future maintenance of those records requires separate scope and review.

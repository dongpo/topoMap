# ROAD-03F Completion Report

## Verdict

PASS

ROAD-01, ROAD-02, and ROAD-03 were recovered byte-for-byte from the approved non-Git recovery source onto the exact canonical HERO freeze lineage. No frozen ROAD artifact was regenerated or normalized. The exact private archive was recovered separately by byte hash, installed locally at the already-ignored canonical dataset path, and inspected read-only. ROAD-04 was not executed.

The ROAD source/artifacts and private source archive were recovered from separate historical workspaces before execution under this controlled baseline-recovery procedure.

## Recovery Sources

- Canonical Git repository: `https://github.com/dongpo/topoMap.git`
- Canonical HERO baseline: `freeze/hero-final-school-hero-56f99eb` at `56f99eb9ae63272a68accac3041fb10eacefb986`
- Non-Git ROAD recovery source: `/Users/dongpodeng/Documents/Codex/2026-08-14/codex-task-hero-05-school-hero`
- Private archive recovery source: `/Users/dongpodeng/Documents/Codex/2026-08-04/referenced-chatgpt-conversation-this-is-an/work/topoMap-d04/data/datasets/112年多維度SHP成果_0502.zip`

The historical ROAD workspace was used only for ROAD-01/02/03 tracked files. The historical archive workspace was used only for the exact private ZIP. Neither workspace was treated as canonical Git history.

## Canonical Git Baseline

- Repository root: `/Users/dongpodeng/Documents/Codex/2026-08-19/files-pasted-by-the-user-road/topoMap-road03f`
- Remote: `origin https://github.com/dongpo/topoMap.git`
- Starting branch: `freeze/hero-final-school-hero-56f99eb`
- Starting SHA: `56f99eb9ae63272a68accac3041fb10eacefb986`
- Recovery branch: `recovery/road-03f-git-baseline`
- Initial working tree: clean
- Lineage: recovery branch directly descends from the frozen HERO commit

## Recovered Files

Recovered tracked-file count: 17. Every file below was copied from the non-Git recovery source and verified byte-identical with `cmp` after copying.

### ROAD-01

- `src/nma/road_resolution.py`
- `tests/test_road_resolution_road01.py`
- `schemas/road-resolution-evidence-package-v1.0.schema.json`
- `data/specifications/nma-road-hero-road-01-v1.0.json`

### ROAD-02

- `src/nma/road_portrayal_decision.py`
- `tests/test_road_portrayal_decision_road02.py`
- `schemas/road-portrayal-proposal-v1.0.schema.json`
- `schemas/road-portrayal-decision-v1.0.schema.json`
- `data/specifications/nma-road-hero-road-02-golden-proposal-v1.0.json`
- `data/specifications/nma-road-hero-road-02-golden-decision-v1.0.json`

### ROAD-03

- `src/nma/road_approval.py`
- `tests/test_road_approval_road03.py`
- `schemas/road-approval-v1.0.schema.json`
- `schemas/road-execution-authorization-v1.0.schema.json`
- `data/specifications/nma-road-hero-road-03-golden-approval-v1.0.json`
- `data/specifications/nma-road-hero-road-03-golden-rejection-v1.0.json`
- `data/specifications/nma-road-hero-road-03-golden-authorization-v1.0.json`

### Documentation

- `ROAD-03F-Completion-Report.md`

No required shared source file or `.gitignore` change was needed. The HERO baseline already contained the exact narrow ignore rule for the private archive.

## Frozen Identity Verification

Canonical identities were computed with the recovered repository's existing canonicalization functions.

| Artifact | Expected | Actual | Result |
|---|---|---|---|
| ROAD-01 package | `b5df3f57c33843f354371206c937f52d37ddbbd9d047a31ad7c334532ce30e9a` | `b5df3f57c33843f354371206c937f52d37ddbbd9d047a31ad7c334532ce30e9a` | PASS |
| ROAD-01 fixture | `b01e261971f65cbfc127aed4f1ba17b01b194dd89f256d3c024170c1dc7338f0` | `b01e261971f65cbfc127aed4f1ba17b01b194dd89f256d3c024170c1dc7338f0` | PASS |
| ROAD-02 proposal | `3d45d1ed039c2af1aa7f050fa1e3c22158c891390c001285054b05a02959ce06` | `3d45d1ed039c2af1aa7f050fa1e3c22158c891390c001285054b05a02959ce06` | PASS |
| ROAD-02 decision | `0d671b1fed3f4b19e4204e745bdcb13f872f3a00dcb4ef5050a091a14065e090` | `0d671b1fed3f4b19e4204e745bdcb13f872f3a00dcb4ef5050a091a14065e090` | PASS |
| ROAD-03 approved approval | `f333defee511e0ae82702444d18befe2f9e115d75608ab61a5c20f91c52f2f07` | `f333defee511e0ae82702444d18befe2f9e115d75608ab61a5c20f91c52f2f07` | PASS |
| ROAD-03 rejected decision | `a327ae30d6bd4efa53c5df43859e80b0ae0a771035bb2de40d6881f82a62f6eb` | `a327ae30d6bd4efa53c5df43859e80b0ae0a771035bb2de40d6881f82a62f6eb` | PASS |
| ROAD-03 execution authorization | `f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38` | `f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38` | PASS |

The recovered ROAD-03 verifier accepted the frozen approval, rejection, proposal, decision, and authorization without executing the authorization.

## Whole-File Hash Verification

| Frozen file | Expected SHA-256 | Actual SHA-256 | Result |
|---|---|---|---|
| ROAD-01 fixture | `96884dbc4a048d555e17da437253ec943b6ce99766f638644f2349612055d429` | `96884dbc4a048d555e17da437253ec943b6ce99766f638644f2349612055d429` | PASS |
| ROAD-02 proposal | `1d86555de5e6146750fa976d48c3ecb0219a0d4ee210f3e933ab86524189dff3` | `1d86555de5e6146750fa976d48c3ecb0219a0d4ee210f3e933ab86524189dff3` | PASS |
| ROAD-02 decision | `9307939c1cfcc87374dfeb45a3e730f90bd2ab98c150011f484ab8c830afed69` | `9307939c1cfcc87374dfeb45a3e730f90bd2ab98c150011f484ab8c830afed69` | PASS |
| ROAD-03 approved approval | `fceda149ac1d0de9d2d579855e837479394fd69c2884fd1001c86175ed4cb4ca` | `fceda149ac1d0de9d2d579855e837479394fd69c2884fd1001c86175ed4cb4ca` | PASS |
| ROAD-03 rejected decision | `1b00475e9279bfbcdf59b0aecb3854f748840dbd86ec93e414a471cede9fdb48` | `1b00475e9279bfbcdf59b0aecb3854f748840dbd86ec93e414a471cede9fdb48` | PASS |
| ROAD-03 authorization | `ba010892193145cad8f6ee8d3331824f3a972cdb422ca902e6bd9c04801e9283` | `ba010892193145cad8f6ee8d3331824f3a972cdb422ca902e6bd9c04801e9283` | PASS |

Canonical identities and whole-file SHA-256 values were evaluated as distinct integrity concepts.

## ROAD Regression

- ROAD-01 focused suite: `23 passed`
- ROAD-01 + ROAD-02 + ROAD-03 combined suite: `104 passed`
- Failed: 0
- Skipped: 0
- Acceptance tests weakened or modified: NO

## School Hero Regression

Command scope:

- `tests/test_hero04_authorization.py`
- `tests/test_hero04_execution.py`
- `tests/test_hero04_maplibre.py`
- `tests/test_hero04_rollback.py`

Result after installing the hash-verified private archive: `11 passed`, 0 failed, 0 skipped.

School Hero code changes required: NO.

## Schema and Ruff Verification

- Ruff on all recovered ROAD source and tests: PASS
- ROAD schemas checked against JSON Schema Draft 2020-12 metaschema: `5 PASS`
- Frozen ROAD documents checked against their schemas: `5 PASS`
- Generated ROAD-01 package checked against its recovered schema: PASS
- Schemas loosened or modified after recovery: NO

## Private Archive Verification

- Local relative path: `data/datasets/112年多維度SHP成果_0502.zip`
- Expected SHA-256: `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`
- Actual SHA-256: `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`
- Archive size: 12,822,898 bytes
- Exists locally: YES
- Git tracked: NO
- Git staged: NO
- Safely ignored: YES (`.gitignore:18` exact-path rule)
- `.gitignore` changed: NO

The archive was located and accepted by byte hash, not by filename alone.

## Source Readiness

- ZIP readable: PASS
- `K14_ROAD` primary family present: YES
- Required components present: `.shp`, `.shx`, `.dbf`, `.prj`
- Optional `.cpg` present: YES
- GDAL/OGR: `GDAL 3.11.0`; ESRI Shapefile opened read-only: PASS
- GDAL layer name: `K14_ROAD`
- Geometry: `Line String`
- Feature count: 196
- CRS: `TWD97[2020]_TM121`
- `K0000004671`: PRESENT
- `K0000004913`: PRESENT
- `K0000005348`: PRESENT
- Permanent extracted dataset created: NO
- ROAD-04 output created: NO

Read-only inspection used a temporary directory that was automatically removed.

## Git Scope Audit

Pre-commit `git diff --stat`:

```text
18 files changed, 3046 insertions(+)
```

Tracked changes comprise exactly:

- 17 byte-preserved ROAD-01/02/03 recovery files listed above
- 1 ROAD-03F completion report

Classification:

- ROAD-01: 4 files
- ROAD-02: 6 files
- ROAD-03: 7 files
- Required shared additive code: 0 files
- Documentation: 1 file

- Unrelated changes: NO
- Frozen HERO artifact mutations: NO
- ROAD-04 code/artifacts introduced: NO
- Private archive included in diff or index: NO

## ROAD-04 Readiness

All recovered tracked code and frozen artifacts, the frozen authorization, and the exact hash-bound private source now coexist in one canonical Git checkout. The private archive remains local-only and ignored. Terminal commit, freeze-ref, push, and remote-SHA evidence are recorded in the task handoff after this pre-commit report is committed.

ROAD-04 READY = YES

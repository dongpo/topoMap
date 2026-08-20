# BUILD-01 — Building Polygon Resolution and Evidence Completion Report

Completion date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-01 IS COMPLETE AS A BOUNDED, READ-ONLY BUILDING-POLYGON RESOLUTION STAGE**

BUILD-01 deterministically resolves one accepted `J13_BUILD` polygon and emits a closed,
content-addressed, redacted evidence package. It does not disclose source coordinates or raw source
attributes, mutate or repair geometry, drop the Z dimension, grant execution authority, redistribute
the private archive, or wire a runtime route.

## 2. Exact predecessor and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Required predecessor branch | `build/build-00a-readiness-closure` | PASS |
| Required predecessor SHA | `a889ee8ba74a4bbdec4845f3ee8714e497f0c56e` | PASS |
| Immutable Core predecessor | `nma-core-v1.0-final` / `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| BUILD-01 branch | `build/build-01-building-resolution` | PASS |
| Starting tracked worktree | clean | PASS |

## 3. Deterministic resolution

The accepted BUILD-00A fixture remains unchanged:

- archive SHA-256:
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`;
- fixture identity:
  `build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a`;
- source layer: `J13_BUILD`;
- feature code: `9310100`;
- eligible, valid polygon population: 2,962.

BUILD-01 applies one frozen rule:

`largest-valid-2d-area-desc-then-build-id-asc`

The selected polygon is rank 1 with no largest-area tie. Its public-safe reference is:

`build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f`

The source feature identifier, seven raw source attributes, geometry coordinates, and WKB are not
tracked or disclosed. Instead, the observation stores independent attribute and geometry
commitments. A future authorized stage can re-verify the same private source without requiring
BUILD-01 to publish it.

## 4. Geometry evidence

The selected source geometry is a valid, single-ring `PolygonZ` with 65 vertices and a measured 2D
area of `1316.686891452159` square metres. The runner-up area is
`1252.979028436020`, proving that the selected maximum is unique under the accepted observation.

BUILD-01 preserves the following distinction:

- source geometry type: `PolygonZ`;
- Core geometry role: `Polygon`;
- Z dimension present: true;
- geometry repair required: false;
- Z-dimension drop authorized: false.

Geometry commitment SHA-256:

`23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f`

## 5. Core identity and provider use

BUILD-01 imports the exact frozen `nma.core.canonical_sha256` and `nma.core.validate_sha256`
objects. It consumes the exact immutable `nma.core.FeatureProfile` returned by the BUILD-owned
adapter and commits to both its identity payload and source-scope payload.

No local canonical-JSON or canonical-SHA implementation, experimental `nma.real_layer` binding,
fallback Core package, or alternate identity provider was introduced.

Redacted source-observation identity:

`build-observation:sha256:8fdbb3bdea8ffe715e7d76eed7c5034bd62226ba649be2206cf7a9e07b853bac`

Golden semantic package SHA-256:

`59b6f972046dbe9af295de414525230b03ed6da4f0e78374076b5cc4a2cdd7de`

Equivalent supported request wording produces the same semantic package hash; the raw request text
is deliberately excluded from that hash.

## 6. Private-source verification path

The optional acceptance path reads the private archive only when it is locally present. It:

1. verifies the archive SHA-256;
2. finds exactly one safe five-part `J13_BUILD` Shapefile family;
3. verifies every component hash against BUILD-00A;
4. extracts only to an automatically removed temporary directory;
5. invokes GDAL in read-only mode;
6. recomputes the population, deterministic rank, commitments, geometry type, validity, area,
   vertex/ring counts, and Z presence;
7. compares the complete redacted observation with the tracked golden observation.

The archive's size and modification time remained unchanged during acceptance. No private source
file is tracked, staged, modified, copied into the repository, or redistributed.

## 7. Closed boundary

The BUILD-01 package explicitly sets all of the following to false:

- source mutation;
- geometry repair;
- Z-dimension drop authorization;
- BUILD execution authorization;
- runtime wiring authorization;
- redistribution authorization.

The package contains no authorization ID, idempotency/consumption identity, command payload,
runtime endpoint, receipt, rollback claim, or provenance claim. Those remain later-stage concerns
that require separate contracts and authorization.

## 8. Acceptance results

Environment:

- Python 3.13.5;
- pytest 9.1.1;
- GDAL 3.11.0;
- private archive present and hash-exact.

Results:

- BUILD-01 focused acceptance: **19 passed**;
- BUILD-00A + BUILD-01 + frozen CORE-01/02/04 regression: **73 passed**;
- complete repository regression: **635 collected; 632 passed; 3 failed**.

The three failures are the exact known, pre-existing Agentic/demo drift recorded before BUILD-01:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD, Core, ROAD, School Hero, or Agent contract regression was introduced.

## 9. Exact changed files

1. `BUILD-01-Completion-Report.md` — completion verdict, evidence, boundaries, and next-stage gate.
2. `build_contracts/__init__.py` — BUILD-01 public contract exports.
3. `build_contracts/resolution.py` — deterministic redacted resolution, validation, hashing, and optional private-source inspection.
4. `data/specifications/nma-build-source-observation-v1.0.json` — redacted, content-addressed golden source observation.
5. `schemas/build-resolution-evidence-package-v1.0.schema.json` — closed Draft 2020-12 resolution-package schema.
6. `schemas/build-source-observation-v1.0.schema.json` — closed Draft 2020-12 observation schema.
7. `tests/test_build_resolution_build01.py` — positive, negative, tamper, privacy, Core, determinism, predecessor, and private-source acceptance.

Existing production `src/nma` changed: **no**.

Frozen Core, ROAD, School Hero, Agent, legacy BUILD v0.4, public runtime, and private archive files
changed: **no**.

## 10. BUILD-02 readiness recommendation

**GO — only for a separately authorized BUILD-02 proposal stage bound to the exact BUILD-01 commit.**

BUILD-02 may consume the redacted feature reference and commitments to define a non-executing
building portrayal proposal. It should not execute or wire a runtime until later contracts define:

1. the authoritative portrayal evidence and rule ownership for class `9310100`;
2. the explicit `PolygonZ` preservation or dimensional-transformation decision;
3. authorization identity and validation;
4. idempotent execution/consumption identity;
5. post-execution verification, rollback, and provenance ownership;
6. continued private-source non-redistribution and full frozen-boundary regression.

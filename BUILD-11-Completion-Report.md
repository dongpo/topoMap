# BUILD-11 Completion Report

## Verdict

**PASS — CONTROLLED BUILDING PRODUCTION VERIFIED; HUMAN ACTIVATION GATE READY**

BUILD-11 independently verifies the activation-held BUILD-10 implementation against the finalized
BUILD-09F contract. It does not activate production, activate official portrayal, mutate source
data, remove source Z, or change production behavior.

Readiness state:

`READY-FOR-HUMAN-ACTIVATION-GATE`

The distinction remains explicit:

`implementation verified != production activated`

## 1. Starting gate

- canonical repository: `https://github.com/dongpo/topoMap.git`;
- exact clean starting branch: `build/build-10-controlled-building-production-implementation`;
- exact BUILD-10 predecessor commit:
  `790a1bcd5624e38fb4a42060044bb73af152a5be`;
- exact BUILD-10 verdict:
  `PASS — CONTROLLED BUILDING PRODUCTION IMPLEMENTATION COMPLETE; ACTIVATION HOLD`;
- exact BUILD-09F predecessor commit:
  `816faa0209d3bbb83ceb71a3df4f27e8d99e4407`;
- BUILD-09F policy-record SHA-256:
  `dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1`;
- finalized production-contract SHA-256:
  `5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88`;
- BUILD-10 implementation file identity:
  `2772ce93f81973e1dbbeb2d4ae9bb1307a29dcdcc4a61ca08f382c12b6b3c957`;
- authorized source archive SHA-256:
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.

The BUILD-09F identities recomputed through the frozen Core provider. All seven frozen BUILD-09E2
artifact file hashes and the four BUILD-10 artifact file hashes recomputed exactly. The archive was
present, ignored, untracked, unstaged, and unchanged. No predecessor frozen identity drifted.

BUILD-11 branch:

`build/build-11-controlled-building-production-verification`

## 2. Verification implementation and closed record

`build_contracts/building_production_verification.py` is verification-only. It runs two complete
real controlled replays per authorized package, verifies every BUILD-10 record with the existing
BUILD-10 verifier, compares full loaded inputs and outputs, checks source identities before and
after, executes explicit fail-closed and tamper matrices, and creates a deterministic readiness
record.

The verifier imports `nma.core.canonical_sha256`; it defines no duplicate or fallback canonical
identity provider. It contains no activation code, persistent derived output, source output target,
or automatic repair.

Machine-readable record:

`data/specifications/nma-build-11-golden-building-production-activation-readiness-v1.0.json`

Canonical readiness-record SHA-256:

`d2ecb53e74f46e279a5672a182b5a9de602c08d4027023d4fb225132bf3d01fb`

The Draft 2020-12 schema uses an exact `const` over the complete record, closing all top-level and
nested properties and values. The readiness record contains no timestamps; `created_on` is a fixed
stage date, and no runtime timestamp is included or excluded conditionally.

## 3. J13 controlled replay

Binding:

`J13_寶山都市計畫/SHP -> J13_BUILD`

Results:

- source features: `2,968`;
- derived non-authoritative XY features: `2,968`;
- annotations: `2,967`;
- unsafe placement suppressions: `1`;
- source PolygonZ collection SHA-256 before and after:
  `49192d22b201961d8db5815c6cbc1ed52d42eab0d29cc331cd0de8500e842910`;
- derived XY collection SHA-256:
  `c32d57a4399898bf60cfe1f30cb47633fbf5c05a0652eb46a2bd763d30f28df0`;
- annotation collection SHA-256:
  `c199a661decad22fb0ee166dc6de84cea168c8e0a7b958095af396db2d4a2d57`;
- portrayal bundle SHA-256:
  `db5334d6e09981a0028fe0f6ed890578b56427d69793eda95d662bbd344cb74c`;
- verification SHA-256:
  `7ac8d12c2367c4fda00bc2a8fc892a38bbe97a26eb635c651c8c7e5dcb53921d`;
- receipt SHA-256:
  `868535bdb245b602d19934c79f62dc53cccfa4f2e366a23ac787a05ca6c82094`;
- BUILD-10 implementation-record SHA-256:
  `ccffdf038cecf06d1dd3341d49b15745f37029f2af78c51bf68b1ab677035b4a`.

Both complete runs were canonically identical.

## 4. J17 controlled replay

Binding:

`J17_新竹科學工業園區特定區計畫(寶山部分)/SHP -> J17_BUILD`

Results:

- source features: `2,839`;
- derived non-authoritative XY features: `2,839`;
- annotations: `2,838`;
- unsafe placement suppressions: `1`;
- source PolygonZ collection SHA-256 before and after:
  `67d30181f4b7a35b655e5e1ce01060f78ef12199f26c6513c9db5b13f6effbef`;
- derived XY collection SHA-256:
  `66fa69d919f54e5903dfaad468f7387f102e3dc7c6f5258c2e992ef8c4a8b661`;
- annotation collection SHA-256:
  `a15ac87b3389549cbee37396a01c47a3bf180c9039004871def54deee0cbb568`;
- portrayal bundle SHA-256:
  `9dd99e095a721d16d811f7e109c70659834d617ac3da2bc4128f8ee7e1cf393c`;
- verification SHA-256:
  `5991436b518590c632ba0e429644f009c9e15ed5cb7f93683b93aceea9823434`;
- receipt SHA-256:
  `3a2c8216e79f8ab1684d728b5946b494f69818ce063841aedf8e3ef614991ab1`;
- BUILD-10 implementation-record SHA-256:
  `0722007704a5a12fb6f314d71bf7898ab1718dd3185bc9060687160a0ce119a7`.

Both complete runs were canonically identical.

## 5. Fail-closed and tamper verification

Positive controls pass for exact J13/J13_BUILD and J17/J17_BUILD binding. The following reject with
the expected closed error and no fallback:

- cross-package J13/J17 layer mismatch in both directions;
- unknown and ambiguous package identity;
- missing and duplicate candidate Building layers;
- seven-field schema mismatch;
- changed archive/package identity;
- changed binding-policy identity.

The tamper matrix additionally rejects changed policy record, production contract, source identity,
derived XY, output-profile DPI, physical line width, official RGB tuple, local hatch angle, layer
name, provenance record, and receipt. Tampered evidence is never repaired or silently rehashed.

## 6. Schema, annotation, and placement

The exact delivered schema remains seven ordered fields:

`BUILD_ID`, `TERRAINID`, `BUILD_STR`, `BUILD_NO`, `BUILD_H`, `GROUP_ID`, `MDATE`.

The delivered adapter order is part of the frozen BUILD-10 schema identity; missing, reordered,
extra, or changed fields fail closed. `BUILD_H`, `GROUP_ID`, and `MDATE` remain opaque passthrough.
BUILD-11 assigns no new semantics.

Annotation is exactly `{BUILD_NO}{BUILD_STR}`. Both present values produce floor count followed by
structure. Missing floor, missing structure, or both missing suppress the incomplete label without
fabrication. Malformed values fail closed.

Deterministic placement was repeated for convex, concave, and narrow polygons. Identical geometry
produced identical interior points. The real J13 and J17 members each reproduced the known single
unsafe-placement suppression; no external relocation or arbitrary fallback occurred.

## 7. Hatch, line, colour, and opacity

Procedural hatch verification passes:

- official semantic: diagonal;
- official spacing: `2.0 mm`;
- local production angle: `45 degrees`, authority `local-production-policy`;
- resource policy: `procedural-canonical`;
- static dependency: none;
- `building-hatch-tile-v1.svg`: not referenced;
- canonical resource SHA-256:
  `b0c5321fe711df44ed357d00605f64d2442394c7623779676c1dafdf230644fb`.

The record does not relabel 45 degrees as official.

Line conversion is exact and unquantized:

`0.20 * 96 / 25.4 = 0.7559055118110237 device px`

The `0.20 mm` physical source value, `96 DPI`, formula, fractional device value, and unset renderer
quantization are separately preserved.

Official colour remains `RGB (0,0,0)`. `#000000` remains only the derived device serialization;
`#111111` is absent. Opacity remains `1.0` under `local-output-profile-policy`.

## 8. PolygonZ, derived XY, and legacy drop-z

For each of four real executions, archive and source collection identities before and after are
equal. Every source member remains PolygonZ; Z is present, finite, hashed, preserved, and
recoverable. No source write handle, repair, writeback, in-place normalization, or dimensional
reduction was used.

Derived XY remains separate, ephemeral, non-authoritative, non-writing, portrayal-only, and bound
to the exact archive, component family, source feature identities, and PolygonZ geometry hashes.
No persistent cache is trusted. Changed derived content fails verification.

The legacy `nma.real_layer` global J17 `drop-z`/`-dim XY` route remains classified
`incompatible-non-authoritative-vs3-path` and is bypassed. The controlled implementation contains
no `execute_real_layer` call, `-dim` request, `drop-z` request, or authoritative source write target.

## 9. Provenance and cleanup

Both packages establish the complete identity-bound chain:

`BUILD-09F policy -> finalized contract -> BUILD-10 implementation -> package -> layer -> schema -> PolygonZ source -> derived XY -> annotation -> portrayal/output profile -> observation -> verification -> receipt`

Cleanup classification:

`rollback-not-required-source-immutable`

Derived artifacts exist only within temporary or in-memory boundaries and are discarded. The
authoritative source never requires rollback because it never changes. Replay after cleanup
reproduces every canonical derived identity. Cleanup cannot target the source or frozen evidence.

## 10. Acceptance and regression

- Ruff and Python static checks: **PASS**;
- Draft 2020-12 schema checks: **PASS**;
- focused BUILD-10 rerun: **21 passed**;
- focused BUILD-11 verification: **17 passed**;
- J13 controlled replay: **PASS**, two identical real runs;
- J17 controlled replay: **PASS**, two identical real runs;
- BUILD historical regression: **632 passed; 4 failed**;
- Core integrity: **53 passed** after the exact BUILD-11 files were staged;
- ROAD integrity: **199 passed**;
- School Hero integrity: **37 passed**;
- complete repository regression: **1231 passed; 7 failed**.

The four BUILD historical failures exactly reproduce BUILD-10's inherited descendant-scope
assertions:

1. `tests/test_build_human_official_production_scope_authorization_build08a.py::test_previous_build_and_forbidden_artifacts_remain_unchanged`;
2. `tests/test_building_production_contract_build09.py::test_previous_build_frozen_artifacts_and_runtime_remain_unchanged`;
3. `tests/test_official_evidence_closure_build09e.py::test_previous_artifacts_runtime_and_source_scope_remain_unchanged`;
4. `tests/test_human_building_production_policy_build09f.py::test_build09f_scope_is_exact_and_contains_no_runtime_source_or_asset_change`.

The complete suite additionally reproduces BUILD-10's three inherited Agentic/demo drift failures:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`.

There is no new material functional, contract, source-integrity, Core, ROAD, School Hero, or
controlled integration regression against exact BUILD-10.

## 11. Exact change scope

Verification and evidence only:

1. `BUILD-11-Completion-Report.md`;
2. `build_contracts/building_production_verification.py`;
3. `data/specifications/nma-build-11-golden-building-production-activation-readiness-v1.0.json`;
4. `schemas/building-production-activation-readiness-v1.0.schema.json`;
5. `tests/test_building_production_verification_build11.py`.

No production module, BUILD-09F artifact, finalized contract, source archive, source geometry,
existing portrayal asset, Core/ROAD/School Hero implementation, or activation flag changed.

## 12. Activation boundary and next stage

Final boundary:

- `implementation_ready: true`;
- `production_activation_allowed: false`;
- `production_active: false`;
- `official_portrayal_activation_allowed: false`;
- `official_portrayal_active: false`;
- `source_mutation_allowed: false`;
- `source_mutated: false`.

Remaining blockers: none within BUILD-11 verification scope.

Recommend:

`BUILD-11A — Human Building Production Activation Authorization`

BUILD-11A must be a separate minimal human authorization stage. It must not redesign semantics or
implementation. BUILD-11 does not begin BUILD-11A and grants it no automatic authority.

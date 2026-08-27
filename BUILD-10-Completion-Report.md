# BUILD-10 Completion Report

## Verdict

**PASS — CONTROLLED BUILDING PRODUCTION IMPLEMENTATION COMPLETE; ACTIVATION HOLD**

BUILD-10 implements the finalized BUILD-09F Building production candidate as a package-scoped,
source-immutable, deterministic portrayal path. It does not activate production or official
portrayal.

## 1. Starting gate

- canonical repository: `https://github.com/dongpo/topoMap.git`;
- clean starting branch: `build/build-09f-human-building-production-policy-resolution`;
- exact local and remote BUILD-09F predecessor commit:
  `816faa0209d3bbb83ceb71a3df4f27e8d99e4407`;
- BUILD-09F verdict:
  `PASS — HUMAN BUILDING PRODUCTION POLICY RESOLVED; BUILD-10 READY`;
- BUILD-09F policy-record SHA-256:
  `dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1`;
- finalized BUILD-09F production-contract SHA-256:
  `5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88`;
- exact BUILD-09E2 commit:
  `d92fd15bd6b7e40714abf25a8e7857d205fcca10`;
- BUILD-09E2 applicability resolution:
  `1a4a406da130eb34a7f6871e92230d0c82fe4bcf9e475651418780bedd5d1262`;
- BUILD-09E2 successor contract:
  `71b7f25239eb001454af61358acb67917d9820957ea4aeb2191ff613ee54a043`;
- BUILD-09E1 portrayal findings: recomputed through the frozen BUILD-09F validator and retained;
- BUILD-09 PolygonZ/derived-XY architecture: retained exactly;
- production activation: false;
- official portrayal activation: false;
- source mutation: forbidden;
- destructive source Z removal: forbidden.

The fetched remote BUILD-09F and BUILD-09E2 branch heads equaled their local heads. Every canonical
identity and all seven frozen BUILD-09E2 artifact file hashes recomputed exactly before the branch
was created.

BUILD-10 branch:

`build/build-10-controlled-building-production-implementation`

## 2. Authoritative contract consumption

`build_contracts/building_production_implementation.py` loads the frozen BUILD-09F policy authorization and finalized
contract, recomputes both with `nma.core.canonical_sha256`, requires their exact frozen identities,
and consumes production semantics from the finalized contract. It fails before derivation on a
changed contract, changed policy record, readiness regression, activation permission, mutation
permission, or Z-removal permission.

The implementation trace is:

`BUILD-09F policy authorization → finalized production contract → deterministic execution plan → immutable PolygonZ validation → derived XY portrayal → observation → verification → receipt`

The runtime result emits content-addressed plan, provenance, observation, verification, receipt,
MapLibre bundle, procedural resource, source geometry, and derived geometry identities. It imports
the frozen Core identity provider and defines no parallel canonical hash provider.

## 3. Package-scoped J13/J17 binding

The implementation requires exactly one explicit source-package identity and exactly one Building
member in that package.

| Package identity | Geographic/project scope | Only permitted layer |
| --- | --- | --- |
| `J13_寶山都市計畫/SHP` | Baoshan urban-plan project area | `J13_BUILD` |
| `J17_新竹科學工業園區特定區計畫(寶山部分)/SHP` | Hsinchu Science Park special-plan project area, Baoshan portion | `J17_BUILD` |

The binding record preserves source package, scope, selected layer, seven-field schema identity,
source archive and component identities, and binding-policy identity. Unknown or multiple package
identities, unsupported prefixes, absent or multiple Building layers, cross-prefix selection,
package/layer mismatch, scope mismatch, schema mismatch, or changed source identity fail closed.
No J13/J17 fallback or global equivalence exists.

## 4. Seven-field BUILD schema and annotation

Both authorized members were inspected as `PolygonZ` with the exact delivered seven-field schema:

`BUILD_ID`, `TERRAINID`, `BUILD_STR`, `BUILD_NO`, `BUILD_H`, `GROUP_ID`, `MDATE`.

The implementation records both the official logical definitions and the exact delivered OGR
representation. `BUILD_H`, `GROUP_ID`, and `MDATE` remain intentionally opaque to BUILD-10.
Unknown, missing, reordered, or changed fields fail before portrayal derivation.

Annotation binding is exactly `{BUILD_NO}{BUILD_STR}`: floor count followed by structure, with no
separator or fallback. Both present values are concatenated in that order. If either or both values
are absent, that label is suppressed. Malformed `BUILD_NO` or `BUILD_STR` fails closed.

Placement uses the local deterministic
`nma.deterministic-polygon-interior-point/1.0` algorithm. It prefers an interior center and then a
deterministic scanline representative point. It never emits an outside-polygon fallback. MapLibre
collision avoidance remains enabled (`text-allow-overlap: false`, `text-ignore-placement: false`),
and unsafe placements are suppressed rather than externally relocated.

## 5. Portrayal and output profile

The Building hatch is generated as a reproducible procedural SVG resource from the canonical
specification. There is no dependency on `building-hatch-tile-v1.svg` and no static hatch asset was
created.

- official hatch semantics: diagonal, lower-left to upper-right;
- official spacing: `2.0 mm`;
- local numeric angle: `45°`, authority `local-production-policy`;
- resource policy: `procedural-canonical`;
- official line width: `0.20 mm`;
- output profile: `nma-screen-96dpi-v1`, `96 DPI`;
- conversion: `device_px = physical_mm × output_dpi / 25.4`;
- derived unquantized line width: `0.7559055118110237 device px`;
- derived unquantized hatch spacing: `7.559055118110237 device px`;
- renderer quantization: separate and unset; fractional values are retained;
- official colour: black, original representation `RGB (0,0,0)`;
- MapLibre serialization: `#000000`, classified `derived-device-serialization`;
- rejected historical device colour: `#111111`;
- opacity: `1.0`, authority `local-output-profile-policy`.

The MapLibre candidate contains derived-XY GeoJSON and annotation-point sources, procedural hatch,
fractional-width black outline, and a collision-aware annotation layer. Every layer records exact
package, source-layer, schema, contract, policy, and non-authoritative derived-XY metadata.

## 6. PolygonZ preservation and legacy path disposition

The production implementation boundary is:

`authoritative source archive → exact temporary read-only component family → validated immutable PolygonZ collection → separate reprojected PolygonZ stdout artifact → derived non-writing XY view → MapLibre production candidate`

The source collection is hashed before and after derivation. Every source feature records its
`BUILD_ID` and PolygonZ geometry hash including Z; every derived feature records its separate XY
geometry hash. Attributes must remain identical across the separate reprojection boundary. Source
Z stays recoverable, geometry repair is never performed, derived XY is explicitly non-authoritative
and portrayal-only, and no source write handle or writeback target exists.

The historical `nma.real_layer` Building profile remains byte-identical as frozen predecessor
evidence. BUILD-10 classifies its global J17 / `drop-z` / `-dim XY` behavior as an incompatible,
non-authoritative VS3 path and bypasses it. The BUILD-10 portrayal path does not call `execute_real_layer`,
does not request `-dim XY`, and does not import its Building profile. It reuses only the existing
archive inventory/extraction helpers, operates on temporary component copies, captures external
reprojection from stdout, preserves Z through reprojection, and performs dimensional projection in
memory under the explicit `derive-xy-for-portrayal` boundary.

## 7. Controlled real-package integration

The authorized private archive was available and remained exactly:

`4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.

Controlled full-member observations:

| Package | Source | Derived XY | Annotation points | Unsafe placement suppression | Repair | Production active |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| J13 | 2,968 | 2,968 | 2,967 | 1 | false | false |
| J17 | 2,839 | 2,839 | 2,838 | 1 | false | false |

J13 implementation-record SHA-256:
`ccffdf038cecf06d1dd3341d49b15745f37029f2af78c51bf68b1ab677035b4a`.

J17 implementation-record SHA-256:
`0722007704a5a12fb6f314d71bf7898ab1718dd3185bc9060687160a0ce119a7`.

Both complete provenance chains recomputed successfully. The source archive hash was identical
before and after each run. No derived artifact was materialized outside temporary storage, so the
receipt records cleanup/rollback as unnecessary for ephemeral artifacts and source rollback as
unnecessary.

## 8. Fail-closed behavior

Focused acceptance proves failure before output/activation on unknown or ambiguous packages,
J13/J17 mismatch, missing or unexpected layers, schema drift, contract or policy tampering,
unauthorized archive identity/path, malformed annotation semantics, missing Z, unsupported output
profile, changed portrayal contract, tampered binding/provenance/MapLibre resources, and missing
Core imports. No DEMO defaults, repair, fallback binding, automatic activation, or identity-provider
fallback exists.

## 9. Verification

- static/Ruff and Draft 2020-12 schema validation: **PASS**;
- focused BUILD-10: **21 passed**;
- J13 package binding and controlled real-package integration: **PASS**;
- J17 package binding and controlled real-package integration: **PASS**;
- mismatch/fail-closed: **PASS**;
- annotation content and placement: **PASS**;
- procedural hatch, colour, opacity, and output-profile conversion: **PASS**;
- PolygonZ preservation, derived XY, provenance, and identity: **PASS**;
- BUILD-00A through BUILD-10 historical regression: **615 passed; 4 failed**;
- frozen Core integrity: **53 passed**;
- frozen ROAD integrity: **199 passed**;
- frozen School Hero integrity: **37 passed**;
- complete repository regression with no deselections: **1214 passed; 7 failed**.

The four BUILD-chain failures are descendant-scope assertions, not behavioral or identity
regressions:

1. `tests/test_build_human_official_production_scope_authorization_build08a.py::test_previous_build_and_forbidden_artifacts_remain_unchanged`;
2. `tests/test_building_production_contract_build09.py::test_previous_build_frozen_artifacts_and_runtime_remain_unchanged`;
3. `tests/test_official_evidence_closure_build09e.py::test_previous_artifacts_runtime_and_source_scope_remain_unchanged`;
4. `tests/test_human_building_production_policy_build09f.py::test_build09f_scope_is_exact_and_contains_no_runtime_source_or_asset_change`.

The first three were already documented as inherited stage-local descendant-scope failures by
BUILD-09F. The fourth is BUILD-09F's pre-commit dirty-file assertion: it passes only while the exact
BUILD-09F files are the current dirty set and fails from the clean committed BUILD-09F predecessor
even before BUILD-10 changes. All predecessor artifacts and frozen runtime evidence recompute
byte-exactly.

The complete suite additionally reproduces the three known Agentic/demo drift failures:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`.

No new functional, contract, mutation, Core, ROAD, School Hero, or controlled integration failure
is accepted.

## 10. Scope and activation gate

Production file changed:

- `build_contracts/building_production_implementation.py`.

Evidence and test files changed:

- `schemas/building-controlled-production-implementation-v1.0.schema.json`;
- `tests/test_building_controlled_production_build10.py`;
- `BUILD-10-Completion-Report.md`.

No BUILD-09F policy artifact, BUILD-09E2 or earlier evidence artifact, frozen Core/ROAD/School
implementation, authoritative dataset, source geometry, portrayal asset, or existing renderer was
changed. No parallel identity provider was added.

Final boundaries:

- `implementation_ready: true`;
- `production_activation_allowed: false`;
- `production_active: false`;
- `official_portrayal_activation_allowed: false`;
- `official_portrayal_active: false`;
- `source_mutation_allowed: false`;
- `source_mutated: false`;
- `source_z_drop_allowed: false`;
- `source_z_preserved: true`.

## 11. Next stage

Recommend `BUILD-11 — Controlled Building Production Verification & Activation Readiness`.
BUILD-11 should independently verify controlled real-source/package provenance, rendered output,
resource loading, collision/suppression observations, cleanup/rollback, and activation boundaries,
then determine whether a later human activation authorization is justified. BUILD-10 does not
begin BUILD-11 and does not activate production.

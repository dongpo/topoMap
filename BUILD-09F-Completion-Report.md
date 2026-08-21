# BUILD-09F Completion Report

## Verdict

**PASS — HUMAN BUILDING PRODUCTION POLICY RESOLVED; BUILD-10 READY**

BUILD-09F records the remaining Building rendering choices as explicit local NMA production
policy and finalizes the five-gate Building contract as `production-candidate`. It does not
implement or activate production behavior.

## 1. Starting gate

- canonical repository: `https://github.com/dongpo/topoMap.git`;
- predecessor branch: `build/build-09e2-j13-j17-production-applicability-resolution`;
- predecessor commit: `d92fd15bd6b7e40714abf25a8e7857d205fcca10`;
- BUILD-09 contract: `0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c`;
- BUILD-09E evidence closure: `bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed`;
- BUILD-09E1 evidence resolution: `f75c44bcb834090277588b3c23cfe48f00e965c947754497f64831d4b47b9b65`;
- BUILD-09E2 applicability resolution: `1a4a406da130eb34a7f6871e92230d0c82fe4bcf9e475651418780bedd5d1262`;
- BUILD-09E2 successor contract: `71b7f25239eb001454af61358acb67917d9820957ea4aeb2191ff613ee54a043`;
- BUILD-08A authorization: `4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8`.

The starting worktree was clean, the fetched remote predecessor equaled the local predecessor,
all canonical identities recomputed exactly, and the focused BUILD-09E2 suite passed 42 tests.
Production activation, official portrayal activation, source mutation, and destructive Z removal
were all forbidden before the BUILD-09F branch was created.

## 2. Frozen official findings

The authoritative J13/J17 result remains
`authoritative-applicability-boundary-not-published`. The official evidence search remains closed,
additional acquisition is not justified, and neither package has official NMA production
precedence. Annotation content remains floor count followed by structure. Hatch semantics remain
diagonal with official 2 mm spacing. Line width remains exactly 0.20 mm. Colour remains official
black in the original `RGB (0,0,0)` representation. No official numeric hatch angle, placement
algorithm, CSS-pixel width, HEX definition, opacity, or global J13/J17 equivalence is invented.

## 3. Authorized local production policies

### J13/J17 binding

Classification: `local-version-package-scoped-production-binding`.

The future controlled runtime must consume the exact layer in the explicitly selected and verified
package: `J13_寶山都市計畫/SHP` binds only to `J13_BUILD`, and
`J17_新竹科學工業園區特定區計畫(寶山部分)/SHP` binds only to `J17_BUILD`. Package identity,
package scope, exact layer identity, and schema identity are provenance requirements. Cross-prefix
substitution, global equivalence, package/layer mismatches, and unsupported prefixes are forbidden
or fail closed.

### Hatch

- official diagonal semantics: true;
- official spacing: 2.0 mm;
- local angle: 45 degrees, authority `local-production-policy`;
- resource policy: `procedural-canonical`;
- spacing is physical at the defined cartographic/output-profile scale;
- line colour follows official black unless another officially supported mapping applies;
- deterministic procedural rendering required;
- asset optional and no asset created or deployed.

### Annotation

Official content and the established `{BUILD_NO}{BUILD_STR}` field binding are preserved. Local
placement prefers a deterministic interior or representative point inside the polygon, maintains
near-feature/center semantics, permits collision suppression, and suppresses unsafe labels instead
of moving them arbitrarily. The algorithm authority is `local-production-policy`.

### Line, colour, and opacity output profile

- official width: 0.20 mm;
- local screen profile: `nma-screen-96dpi-v1`, 96 DPI;
- conversion: `device_px = physical_mm * output_dpi / 25.4`;
- derived width: `0.7559055118110237` device pixels;
- no official 1 CSS px rule and no silent rounding;
- canonical device colour: `rgb(0, 0, 0)`;
- optional `#000000`: `derived-device-serialization`, never an official definition;
- `#111111`: rejected;
- opacity: 1.0, authority `local-output-profile-policy`.

## 4. PolygonZ / derived XY boundary

The BUILD-09 P2 architecture is unchanged: source PolygonZ is authoritative, immutable, and fully
recoverable; derived XY is non-authoritative, non-writing, portrayal-only, and either ephemeral or
a content-addressed read-only cache. Provenance binds it to exact source identity and geometry.
The destructive legacy drop-z path remains incompatible. BUILD-09F implements none of this path;
BUILD-10 or later may bypass, replace, or isolate the legacy path under the finalized contract.

## 5. Final contract and authorization

All five gates are exactly `P2-production-candidate`:

| Gate | State |
| --- | --- |
| hatch | `P2-production-candidate` |
| annotation | `P2-production-candidate` |
| J13/J17 | `P2-production-candidate` |
| line/colour | `P2-production-candidate` |
| PolygonZ/derived XY | `P2-production-candidate` |

The successor status is `production-candidate`, never `production-active`.
`controlled_production_implementation_design_allowed` and
`controlled_production_implementation_allowed` are true for the next stage. Production activation,
official portrayal activation, source mutation, source Z removal, and unbounded runtime wiring
remain false.

BUILD-10 readiness is `READY-FOR-BUILD-10`.

## 6. Deterministic artifacts

- policy authorization record:
  `data/specifications/nma-build-09f-golden-human-building-production-policy-authorization-v1.0.json`;
- policy record SHA-256:
  `dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1`;
- finalized Building production contract:
  `data/specifications/nma-build-09f-finalized-building-production-contract-v1.0.json`;
- finalized contract SHA-256:
  `5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88`.

Both identities are canonical JSON SHA-256 values computed by the frozen Core identity provider.
Both closed Draft 2020-12 schemas reject unknown top-level fields, policy states, activation states,
and gate states. The deterministic validator recomputes every predecessor and BUILD-09F identity
and compares the full reviewed artifact shape.

## 7. Verification

- focused BUILD-09F: **28 passed**;
- BUILD-00A through BUILD-09F historical regression: **595 passed; 3 failed**;
- frozen Core integrity: **53 passed**;
- frozen ROAD integrity: **199 passed**;
- School Hero integrity: **37 passed**;
- complete repository regression with no deselections: **1194 passed; 6 failed**.

The three BUILD-chain failures are inherited stage-local descendant-scope assertions:

1. `tests/test_build_human_official_production_scope_authorization_build08a.py::test_previous_build_and_forbidden_artifacts_remain_unchanged`;
2. `tests/test_building_production_contract_build09.py::test_previous_build_frozen_artifacts_and_runtime_remain_unchanged`;
3. `tests/test_official_evidence_closure_build09e.py::test_previous_artifacts_runtime_and_source_scope_remain_unchanged`.

Each fails only because its frozen stage-local allowed-file set excludes authorized later BUILD
artifacts. No predecessor, runtime, source, geometry, or portrayal asset changed.

The complete suite additionally reproduces the three known Agentic/demo drift failures:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`.

These pre-existing PMTiles catalog and Agentic freeze/source-asset drifts are classified and not
repaired. No new failure is accepted.

## 8. Scope

BUILD-09F changes exactly this report, one non-executing policy builder/validator, two deterministic
JSON artifacts, two closed JSON schemas, and one focused acceptance-test file. It changes no file
under `src/`, `assets/`, or source datasets. It does not modify `src/nma/real_layer.py`, implement
J13/J17 routing, alter MapLibre styles, create a hatch asset, execute a real layer, mutate geometry,
drop Z, activate portrayal, activate production, reopen evidence, or alter a predecessor artifact.

## 9. Next stage

Recommend `BUILD-10 — Controlled Building Production Implementation`. BUILD-10 may implement the
finalized package-scoped binding, deterministic annotation placement, procedural hatch, physical
width conversion, RGB serialization, and Z-preserving derived-XY path. It must keep production
activation separately gated. Do not begin BUILD-10 in this stage.

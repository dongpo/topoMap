# BUILD-12 Completion Report

## Verdict

**PASS — BUILDING PRODUCTION ACTIVATED AND POST-ACTIVATION VERIFIED**

BUILD-12 performed the first authorization-bound activation of the exact BUILD-10 Building
implementation, immediately verified both real active package paths, rehearsed controlled
deactivation and same-identity reactivation, and froze the final active baseline. It did not alter
Building semantics, BUILD-09F policy, the finalized contract, BUILD-10 or BUILD-11 implementation,
the source archive, PolygonZ geometry, or any Core, ROAD, or School Hero production file.

## 1. Starting gate and exact authorization chain

- canonical repository: `https://github.com/dongpo/topoMap.git`;
- clean starting branch:
  `build/build-11a-human-building-production-activation-authorization`;
- exact BUILD-11A predecessor commit:
  `3370c1a33c46d4ab929911de4d2671a9cd82e6ce`;
- BUILD-11A authorization SHA-256:
  `8bae65726aa0c6901927cb3a0a12a875ac766d45ac9e3a793afb23a85effdb0f`;
- BUILD-11 readiness canonical SHA-256:
  `d2ecb53e74f46e279a5672a182b5a9de602c08d4027023d4fb225132bf3d01fb`;
- BUILD-11 readiness file SHA-256:
  `d65c33803a2d5a5b3a78a00c5d09606100d0c253d306f6b015bf425f8d728770`;
- BUILD-10 implementation identity:
  `2772ce93f81973e1dbbeb2d4ae9bb1307a29dcdcc4a61ca08f382c12b6b3c957`;
- BUILD-09F policy SHA-256:
  `dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1`;
- finalized contract SHA-256:
  `5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88`;
- frozen Core identity provider file SHA-256:
  `d9c4ac0d0d385f6942c552a0b2ffc4c12b3deb0ee876d569aeadc036b1a92e78`;
- source archive SHA-256:
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.

The canonical remote BUILD-11A branch and the clean local starting checkout both resolved to the
required predecessor commit. The authorization record recomputed exactly, remained
`authorized-for-controlled-activation`, targeted only BUILD-12, and explicitly authorized both
controlled production activation and controlled official portrayal activation. Starting production
and portrayal state were false. All source mutation, writeback, repair, and Z-drop permissions were
false. No predecessor artifact was repaired.

BUILD-12 branch:

`build/build-12-controlled-building-production-activation`

## 2. Pre-activation verification

All sixteen independent gates passed before activation:

1. authorization record valid;
2. authorization targets BUILD-12;
3. BUILD-10 implementation identity exact;
4. BUILD-09F policy identity exact;
5. finalized contract identity exact;
6. BUILD-11 readiness identity exact;
7. remaining blockers none;
8. Core identity provider exact;
9. J13/J17 binding policy exact;
10. seven-field BUILD schema exact;
11. annotation contract exact;
12. hatch contract exact;
13. line/colour output profile exact;
14. PolygonZ/derived-XY boundary exact;
15. source archive identity unchanged;
16. no new material regression.

BUILD-12 then independently rebuilt the complete BUILD-11 verification record from two real
replays per package and required byte-canonical equality with the frozen readiness record before
constructing any active state.

## 3. Bounded activation mechanism and identity

The repository had no existing checked-in Building activation registry. BUILD-12 therefore added
one bounded state-layer implementation at
`build_contracts/building_production_activation.py`. It wraps the frozen BUILD-10 executor and
does not modify it. It exposes no authoritative source write handle and activates only verified
ephemeral derived-XY portrayal output.

Runtime revision:

`nma.building-production-runtime/1.0`

Exact runtime-module SHA-256:

`a67f79c87072ab23cf546367183a418f60e94baa4fbf48e1d79b93629c4ce484`

Activation ID:

`building-activation-03d28cbae50eb2050db4ed08`

Activation-configuration SHA-256:

`03d28cbae50eb2050db4ed0841009e81fab84b18dcb882a7e85fce49818565ad`

The activation configuration binds authorization, readiness, implementation, policy, contract,
source archive, runtime revision and exact module, seven-field schema, exact J13/J17 package
bindings, active portrayal profile, output profile, and active/non-writing state. The activation ID
is derived from that complete configuration and cannot exist independently of authorization.

Final canonical state:

- `production_active: true`;
- `official_portrayal_active: true`;
- `source_mutation_allowed: false`;
- `source_writeback_allowed: false`;
- `source_repair_allowed: false`;
- `source_z_drop_allowed: false`.

## 4. Activation record, receipt, and frozen baseline

Canonical activation record:

- path: `data/runtime/nma-building-production-activation-v1.0.json`;
- canonical record SHA-256:
  `6994abb821287aec015e846148b630054d03c826a6d370ceb625816dfa29d08d`;
- file SHA-256:
  `b5ee8deb67da770348f6ba4449acbcd71c0277ea8e486f4bf22be699a7ac285f`.

Canonical activation receipt:

- path: `data/runtime/nma-building-production-activation-receipt-v1.0.json`;
- canonical receipt SHA-256:
  `d50cd21f5caa0428ae2dbd4f7fd8343b0bfc50e387dbd156b71ecb9a88739cb7`;
- file SHA-256:
  `83857148f9cd54e69a4fc9ab25470260552fdb7c417b2846d79a7755d58b76fd`.

Frozen activated baseline:

- path:
  `data/specifications/nma-build-12-golden-building-production-activated-baseline-v1.0.json`;
- canonical baseline SHA-256:
  `e9ebf1158caef22cb02d98d7ba8bfe4c99df46d4d9e93a47ad234f632a1755b2`;
- file SHA-256:
  `b88b1025dbab0a1fb1cc7640173f2af2d110213f3520f085fc7a9ac38837d1e7`.

Canonical identities exclude timestamps. Three Draft 2020-12 `const` schemas close the complete
activation record, receipt, and baseline, including nested values and unknown fields.

## 5. Real J13 active verification

Exact binding:

`J13_寶山都市計畫/SHP -> J13_BUILD`

- source features: `2968`;
- derived XY features: `2968`;
- annotations: `2967`;
- suppressed unsafe placements: `1`;
- source PolygonZ collection SHA-256 before and after:
  `49192d22b201961d8db5815c6cbc1ed52d42eab0d29cc331cd0de8500e842910`;
- derived-XY SHA-256:
  `c32d57a4399898bf60cfe1f30cb47633fbf5c05a0652eb46a2bd763d30f28df0`;
- annotation SHA-256:
  `c199a661decad22fb0ee166dc6de84cea168c8e0a7b958095af396db2d4a2d57`;
- portrayal-bundle SHA-256:
  `db5334d6e09981a0028fe0f6ed890578b56427d69793eda95d662bbd344cb74c`;
- active-runtime observation SHA-256:
  `0f139473852ba9b79c66332185b26ca12e844554136c8b1ea9c4fe9ff32f9d49`.

Result: **PASS**. Package, layer, source, derived, annotation, portrayal, activation, provenance,
and receipt identities are exact.

## 6. Real J17 active verification

Exact binding:

`J17_新竹科學工業園區特定區計畫(寶山部分)/SHP -> J17_BUILD`

- source features: `2839`;
- derived XY features: `2839`;
- annotations: `2838`;
- suppressed unsafe placements: `1`;
- source PolygonZ collection SHA-256 before and after:
  `67d30181f4b7a35b655e5e1ce01060f78ef12199f26c6513c9db5b13f6effbef`;
- derived-XY SHA-256:
  `66fa69d919f54e5903dfaad468f7387f102e3dc7c6f5258c2e992ef8c4a8b661`;
- annotation SHA-256:
  `a15ac87b3389549cbee37396a01c47a3bf180c9039004871def54deee0cbb568`;
- portrayal-bundle SHA-256:
  `9dd99e095a721d16d811f7e109c70659834d617ac3da2bc4128f8ee7e1cf393c`;
- active-runtime observation SHA-256:
  `cc7b77d220278098a754643f7e26eb0d90cfcf90b0426292c2c312aaa90abc5d`.

Result: **PASS**. Package, layer, source, derived, annotation, portrayal, activation, provenance,
and receipt identities are exact.

## 7. Immediate post-activation verification

All twenty post-activation gates passed. The runtime reports Building production and official
portrayal active; implementation, policy, contract, authorization, schema, bindings, annotation,
hatch, line, colour, opacity, PolygonZ, derived-XY, source, provenance, and receipt identities are
exact. Post-activation observation SHA-256:

`94fc32800a47041a1624cd643397b3ad2e9b790318f3516257188cfc47d15bea`

Post-activation verification SHA-256:

`723ea166b9aecab6bf5edf4e98d23607cdcbdb858acc8d6226b64808467885de`

The state machine sets active state only after successful pre-verification. Any exception or false
result from the mandatory post-verifier immediately invokes deactivation and leaves both active
flags false. The focused failure-injection test proves this behavior without retry or criteria
relaxation.

## 8. Active fail-closed matrix

Positive controls passed:

- valid J13 package + `J13_BUILD`;
- valid J17 package + `J17_BUILD`.

Active rejection controls passed:

- J13 + `J17_BUILD`: `package_layer_mismatch`;
- J17 + `J13_BUILD`: `package_layer_mismatch`;
- unknown package: `unknown_package`;
- ambiguous package: `ambiguous_package`;
- missing layer: `missing_building_layer`;
- duplicate Building layer: `unexpected_layer`;
- schema mismatch: `schema_mismatch`;
- tampered contract: `contract_identity_drift`;
- tampered authorization: `authorization_invalid`;
- tampered runtime activation identity: `activation_identity_mismatch`.

Tampered records and receipts fail even after their self-hash is recomputed. Unknown activation
state values and unknown schema properties fail. No fallback or automatic substitution is present.

## 9. Portrayal verification

The active portrayal remains exactly the finalized contract:

- annotation content: `{BUILD_NO}{BUILD_STR}`, floor count followed by structure;
- placement: deterministic interior/representative point, outside fallback forbidden, unsafe
  placement suppressed;
- diagonal hatch: procedural canonical;
- physical spacing: `2.0 mm`;
- local angle: `45°`;
- official line width: `0.20 mm`;
- output profile: `nma-screen-96dpi-v1` at `96 DPI`;
- derived unquantized line width: `0.7559055118110237 px`;
- official colour: RGB `(0,0,0)`;
- device serialization: `#000000`;
- opacity: `1.0`.

No historical DEMO value or static hatch dependency was activated.

## 10. PolygonZ and derived-XY integrity

The authoritative archive remained byte-identical at
`4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.
Both per-package PolygonZ collection identities were equal before and after every replay. Z exists
and remains recoverable. No geometry repair, source writeback, source overwrite, in-place XY
conversion, or source mutation occurred.

Derived XY remains separate, ephemeral, non-authoritative, deterministic, source-bound,
non-writing, discardable, and rebuildable. The incompatible legacy `nma.real_layer`
`building-polygon` drop-Z path remains classified
`bypassed-by-build10-controlled-building-path`, is not production-reachable, requests no `-dim`
operation, and owns no authoritative write target.

## 11. Activation provenance and rollback rehearsal

The canonical chain is:

`BUILD-11A authorization -> BUILD-11 readiness -> BUILD-10 implementation -> BUILD-09F policy -> finalized contract -> activation event -> exact runtime activation module -> active runtime state -> J13/J17 package -> PolygonZ source -> derived XY -> portrayal -> post-activation observation -> verification -> activation receipt`

All seventeen links use the frozen `nma.core.canonical_sha256` provider. Provenance-record
SHA-256:

`97da5bd6c52b392edbce46be204dc49112a8e00f94305a8a0e7e957eb039395e`

Controlled deactivation changed only the process-local Building activation binding and produced:

- `production_active: false`;
- `official_portrayal_active: false`.

The archive and source collection identities remained unchanged. Reactivation with the same
authorization and configuration reproduced activation ID
`building-activation-03d28cbae50eb2050db4ed08` and configuration SHA-256
`03d28cbae50eb2050db4ed0841009e81fab84b18dcb882a7e85fce49818565ad`.
Final BUILD-12 state is active.

## 12. Acceptance and regression verification

- Ruff and Python static checks: **PASS**;
- closed Draft 2020-12 schema checks: **PASS**;
- focused BUILD-12 acceptance: **31 passed**;
- focused BUILD-11A rerun: **19 passed; 1 inherited stage-local scope failure**;
- focused BUILD-11 rerun: **17 passed**;
- focused BUILD-10 rerun: **21 passed**;
- BUILD historical regression: **682 passed; 5 stage-local scope failures**;
- Core integrity: **53 passed**;
- ROAD integrity: **199 passed**;
- School Hero integrity: **37 passed**;
- complete repository regression: **1281 passed; 8 inherited/stage-local failures**.

The five BUILD regression failures are stage-local descendant-scope assertions. Four were already
inherited by BUILD-11A:

1. `tests/test_build_human_official_production_scope_authorization_build08a.py::test_previous_build_and_forbidden_artifacts_remain_unchanged`;
2. `tests/test_building_production_contract_build09.py::test_previous_build_frozen_artifacts_and_runtime_remain_unchanged`;
3. `tests/test_human_building_production_policy_build09f.py::test_build09f_scope_is_exact_and_contains_no_runtime_source_or_asset_change`;
4. `tests/test_official_evidence_closure_build09e.py::test_previous_artifacts_runtime_and_source_scope_remain_unchanged`.

The fifth is BUILD-11A's own stage-local exact-change assertion, which correctly ceases to hold
once authorized BUILD-12 artifacts exist:

5. `tests/test_human_building_production_activation_authorization_build11a.py::test_build11a_changed_file_scope_is_exact_and_production_sources_are_untouched`.

The complete suite additionally reproduces the three pre-existing Agentic/demo failures:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`.

The PMTiles catalog and Agentic freeze/source-asset drifts predate BUILD-12. No failure touches the
Building activation, source integrity, Core, ROAD, or School Hero acceptance surface. Inherited
failures were classified and not repaired.

## 13. Exact change scope

Nine bounded files:

1. `BUILD-12-Completion-Report.md`;
2. `build_contracts/building_production_activation.py`;
3. `data/runtime/nma-building-production-activation-v1.0.json`;
4. `data/runtime/nma-building-production-activation-receipt-v1.0.json`;
5. `data/specifications/nma-build-12-golden-building-production-activated-baseline-v1.0.json`;
6. `schemas/building-production-activation-v1.0.schema.json`;
7. `schemas/building-production-activation-receipt-v1.0.schema.json`;
8. `schemas/building-production-activated-baseline-v1.0.schema.json`;
9. `tests/test_building_production_activation_build12.py`.

No official evidence, BUILD-09F policy, finalized contract, BUILD-10 implementation, BUILD-11
readiness, BUILD-11A authorization, source archive, existing `src/` runtime, portrayal asset, Core,
ROAD, or School Hero file changed. No release tag was created.

## 14. Next stage

Recommend:

`BUILD-FINAL — Building Production Freeze & Release Baseline`

BUILD-FINAL should freeze the activated implementation, authorization chain, policy, contract,
active runtime and portrayal identities, activation receipt, source-integrity identity, exact
J13/J17 package bindings, and activation/deactivation contract. BUILD-12 does not begin BUILD-FINAL.

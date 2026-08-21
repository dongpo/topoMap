# BUILD-11A Completion Report

## Verdict

**PASS — HUMAN BUILDING PRODUCTION ACTIVATION AUTHORIZED; BUILD-12 READY**

BUILD-11A records the explicit human decision:

`AUTHORIZE CONTROLLED BUILDING PRODUCTION ACTIVATION IN THE NEXT SEPARATELY EXECUTED STAGE.`

This stage authorizes BUILD-12 to activate the exact verified Building implementation. BUILD-11A
does not activate production or official portrayal, modify implementation or runtime code, mutate
source data or geometry, remove source Z, or redesign semantics, policy, portrayal, or architecture.

## 1. Starting gate

- canonical repository: `https://github.com/dongpo/topoMap.git`;
- clean predecessor branch: `build/build-11-controlled-building-production-verification`;
- exact BUILD-11 predecessor commit:
  `fb8421d222685742f504fe8397bd03acfc94e3db`;
- exact BUILD-11 verdict:
  `PASS — CONTROLLED BUILDING PRODUCTION VERIFIED; HUMAN ACTIVATION GATE READY`;
- exact BUILD-11 readiness state: `READY-FOR-HUMAN-ACTIVATION-GATE`;
- BUILD-11 remaining blockers: none;
- BUILD-11 readiness canonical SHA-256:
  `d2ecb53e74f46e279a5672a182b5a9de602c08d4027023d4fb225132bf3d01fb`;
- BUILD-11 readiness file SHA-256:
  `d65c33803a2d5a5b3a78a00c5d09606100d0c253d306f6b015bf425f8d728770`;
- BUILD-10 implementation identity:
  `2772ce93f81973e1dbbeb2d4ae9bb1307a29dcdcc4a61ca08f382c12b6b3c957`;
- BUILD-09F policy SHA-256:
  `dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1`;
- finalized production-contract SHA-256:
  `5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88`;
- authoritative source archive SHA-256:
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.

The starting worktree was clean. The local and canonical remote BUILD-11 branch both resolved to
the required predecessor commit. Every canonical identity recomputed exactly. BUILD-11 still had
`implementation_ready: true`, while production activation, production active state, official
portrayal activation, official portrayal active state, source mutation, and source-mutated state
remained false. No predecessor evidence was repaired.

BUILD-11A branch:

`build/build-11a-human-building-production-activation-authorization`

## 2. Authorization and exact identity binding

Authorization state:

`authorized-for-controlled-activation`

The authorization is bound to the exact BUILD-11 readiness record, BUILD-10 implementation,
BUILD-09F policy, finalized production contract, source archive and packages, seven-field schema,
output profile, portrayal profile, Core identity provider, and authorization record itself. Any
drift invalidates authorization. Mismatch handling is fail-closed; automatic repair and
reauthorization by inference are forbidden.

Machine-readable record:

`data/specifications/nma-build-11a-golden-human-building-production-activation-authorization-v1.0.json`

Canonical authorization SHA-256:

`8bae65726aa0c6901927cb3a0a12a875ac766d45ac9e3a793afb23a85effdb0f`

The deterministic builder uses only `nma.core.canonical_sha256`. The closed Draft 2020-12 schema
uses an exact `const` over the complete reviewed record, rejecting omissions, unknown values,
authorization broadening, active-state claims, source-write authority, and non-BUILD-12 targets.

## 3. Authorized package scope

The BUILD-09F package-scoped policy is preserved exactly:

- `J13_寶山都市計畫/SHP -> J13_BUILD`;
- `J17_新竹科學工業園區特定區計畫(寶山部分)/SHP -> J17_BUILD`.

Exact package, exact layer, and exact seven-field schema identities are required. J13-to-J17 and
J17-to-J13 fallback, global equivalence, unknown prefixes, automatic substitution, and unverified
package activation are forbidden and fail closed.

The schema identity remains
`3f9bdc1d88da286165c185dfae152b867e39cfb6308d17ffe7ff8c4aa79ffa76`,
covering `BUILD_ID`, `TERRAINID`, `BUILD_STR`, `BUILD_NO`, `BUILD_H`, `GROUP_ID`, and `MDATE`.

## 4. Authorized portrayal and output profile

The authorization is limited to the exact finalized profile:

- annotation content `{BUILD_NO}{BUILD_STR}`, floor count followed by structure;
- finalized deterministic interior placement and suppression policy;
- procedural canonical diagonal hatch;
- official hatch spacing `2.0 mm`;
- local production-policy hatch angle `45 degrees`;
- official line width `0.20 mm`;
- output profile `nma-screen-96dpi-v1` at `96 DPI`;
- exact unquantized width `0.7559055118110237` device pixels;
- official black RGB `(0,0,0)`;
- derived device serialization `#000000`;
- opacity `1.0`.

Portrayal-profile SHA-256:
`d9d8c7d329508f4b61c4d0fd15c3d9af5512f5fbac2ab473e47171120a716244`.

Output-profile SHA-256:
`bc0c2174433f73691b82dd4f5ba6f93835a32bc26baa7f1d0f814c590779004f`.

The authorization does not create general authority to change NLSC official rules or authorize
any other Building behavior.

## 5. Source and geometry boundary

The authorized architecture remains:

`authoritative PolygonZ -> non-writing derived XY -> portrayal/runtime`

BUILD-12 may read authoritative source and create the exact derived portrayal view. Source
mutation, geometry repair, source writeback, source Z drop, and source overwrite remain forbidden.
Source PolygonZ must remain authoritative, intact, recoverable, and outside any rollback target.

## 6. Activation-state distinction

Authorization for BUILD-12 is explicit:

- `controlled_production_activation_authorized: true`;
- `production_activation_allowed_for_build12: true`;
- `controlled_official_portrayal_activation_authorized: true`;
- `official_portrayal_activation_allowed_for_build12: true`.

Current BUILD-11A state remains:

- `production_active: false`;
- `official_portrayal_active: false`;
- `source_mutated: false`;
- automatic activation performed: false;
- activation in BUILD-11A performed: false.

Authorization is permission for a later controlled action; it is not evidence that activation has
occurred.

## 7. BUILD-12 pre-activation and post-activation gates

BUILD-12 must independently reverify the authorization record; implementation, contract, policy,
and readiness identities; supported package and exact J13/J17 binding; schema; source archive;
PolygonZ and derived-XY boundary; provenance; regression status; and explicitly bounded target.
Failure means `do-not-activate-fail-closed`.

Immediate post-activation verification must confirm active runtime and exact active identities,
fail-closed J13/J17 behavior, unchanged source and PolygonZ, non-writing derived XY, deterministic
output, an activation receipt/provenance event, and an available rollback/deactivation path.
Failure requires fail-closed deactivation when the activation state is reversible. Source data must
never require rollback.

## 8. Acceptance and regression verification

- focused BUILD-11A acceptance: **20 passed**;
- focused BUILD-11 verification: **17 passed**;
- focused BUILD-10 acceptance: **21 passed**;
- BUILD historical regression: **652 passed; 4 failed**;
- Core integrity: **53 passed** after the exact BUILD-11A files were staged;
- ROAD integrity: **199 passed**;
- School Hero integrity: **37 passed**;
- complete repository regression: **1251 passed; 7 failed**.

The four BUILD historical failures exactly reproduce BUILD-11's inherited descendant-scope
assertions:

1. `tests/test_build_human_official_production_scope_authorization_build08a.py::test_previous_build_and_forbidden_artifacts_remain_unchanged`;
2. `tests/test_building_production_contract_build09.py::test_previous_build_frozen_artifacts_and_runtime_remain_unchanged`;
3. `tests/test_human_building_production_policy_build09f.py::test_build09f_scope_is_exact_and_contains_no_runtime_source_or_asset_change`;
4. `tests/test_official_evidence_closure_build09e.py::test_previous_artifacts_runtime_and_source_scope_remain_unchanged`.

Each fails only because its frozen stage-local allowed-file set excludes authorized later BUILD
artifacts. The complete suite additionally reproduces BUILD-11's three inherited Agentic/demo
drift failures:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`.

The PMTiles catalog and Agentic freeze/source-asset drifts predate BUILD-11A and are classified, not
repaired. There is no new material functional, authorization, source-integrity, Core, ROAD, School
Hero, or controlled Building regression against exact BUILD-11.

## 9. Exact change scope

Authorization evidence only:

1. `BUILD-11A-Completion-Report.md`;
2. `build_contracts/human_building_production_activation_authorization.py`;
3. `data/specifications/nma-build-11a-golden-human-building-production-activation-authorization-v1.0.json`;
4. `schemas/building-human-production-activation-authorization-v1.0.schema.json`;
5. `tests/test_human_building_production_activation_authorization_build11a.py`.

No production implementation, BUILD-11 artifact, BUILD-09F artifact, finalized contract, `src/`
file, runtime wiring, portrayal compiler, MapLibre adapter, annotation or hatch implementation,
source dataset, source geometry, or Z value changed.

## 10. Next stage

Recommend:

`BUILD-12 — Controlled Building Production Activation & Post-Activation Verification`

BUILD-12 must reverify this authorization and every bound identity, activate only the bounded
Building path, immediately verify active runtime state and J13/J17 behavior, preserve source and
PolygonZ, record activation provenance and receipt, verify deactivation/rollback, and freeze the
active production identity only if all gates pass. BUILD-11A does not begin BUILD-12.

# ROAD-05 Completion Report

## Verdict

PASS

ROAD-05 independently verified the exact persisted ROAD-04 change, reconstructed both native and
runtime geometry from the immutable private archive, closed the ROAD-01 through ROAD-05 provenance
chain, rendered the actual candidate bundle for cartographic inspection, and rejected all exercised
tamper and unexpected-output cases. No independent visual oracle exists; pixel correctness is
reported with that limitation rather than falsely certified.

## Repository Identity

- Canonical root: `/Users/dongpodeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/topoMap`
- Origin: `https://github.com/dongpo/topoMap.git`
- Starting ROAD-04 branch: `road/road-04-controlled-execution`
- Exact starting ROAD-04 SHA: `7d5bacd87eb97c878ebabfd245bc7660971601a5`
- ROAD-03 freeze ancestor: `5eb2ad703ec4b2e3678f511eabfe6a119bef5ac9` — verified
- ROAD-05 branch: `road/road-05-qa-provenance`
- Final HEAD: recorded in the final Codex response after the report commit (a commit cannot contain
  its own SHA without changing that SHA).

## Frozen Upstream Identities

| Node | Verified canonical SHA-256 |
|---|---|
| Private archive | `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53` |
| ROAD-01 package | `b5df3f57c33843f354371206c937f52d37ddbbd9d047a31ad7c334532ce30e9a` |
| ROAD-01 fixture | `b01e261971f65cbfc127aed4f1ba17b01b194dd89f256d3c024170c1dc7338f0` |
| ROAD-02 proposal | `3d45d1ed039c2af1aa7f050fa1e3c22158c891390c001285054b05a02959ce06` |
| ROAD-02 decision | `0d671b1fed3f4b19e4204e745bdcb13f872f3a00dcb4ef5050a091a14065e090` |
| ROAD-03 approval | `f333defee511e0ae82702444d18befe2f9e115d75608ab61a5c20f91c52f2f07` |
| ROAD-03 authorization | `f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38` |
| ROAD-04 execution | `road-exec-33766f336d9cc18eb2ac159e` |
| ROAD-04 plan | `e51e42b955ade0d3ff5c6b8fbe00919aac4d9b9f90fe59bd548e14b7a9bf04a0` |
| ROAD-04 derived portrayal | `fb8762642e4e3e633912028b18ca6aa11545117e15572839896770537a5971b6` |
| ROAD-04 runtime bundle | `33aa7c6b0d557fa9a72e2fa4e0106493d8dfe10ec9201bd7762e204bb14a286d` |
| ROAD-04 observation | `e5263aa67dbb400e0c3a63b7cd1457d9d95428a8d519aef34b3c9b4396ce1d9a` |
| ROAD-04 receipt | `0ab5964fcc2e1f47d43fd328dbc3771a7e624bf4a3707f91236a1485f5610720` |
| ROAD-04 rollback manifest | `03bc4f84d27b9b55baa7403d4ff4abc758ff223d0ffe7b7aaaa11233da162ae2` |

## QA Identity

- QA ID: `road-qa-bf4b2fc160b9c316162e9dd9`
- QA SHA-256: `8f31ecb25f62b5bc71465db33503a7c37d63fe18e9006ce6801a2ab639464a82`
- Verdict: `expected-change-verified`

## Provenance Identity

- Provenance ID: `road-provenance-0f9cff5d79078a54f42bd7a7`
- Provenance SHA-256: `130a24e15126743466b57dc03e2ca8a652335553b56522e316f47104cc9dbc70`
- Lineage completeness: `complete`

The chain contains the private archive, actual ROAD-01 evidence/fixture/package, ROAD-02
decision/proposal, ROAD-03 approval/authorization, ROAD-04 execution/plan/derived/bundle/
observation/receipt/rollback, ROAD-05 QA, and the verified artifact set. Missing authored IDs are
represented as null rather than invented.

## Geometry QA

| Segment | Native geometry SHA-256 | Type | Vertices | Runtime geometry SHA-256 | Runtime vertices |
|---|---|---|---:|---|---:|
| `K0000004671` | `42616b9b91d91efd4582171b23ad70259156c586bef776098329cdd81aa8f800` | LineString | 4 | `b7272294ba1c52c3550293465192acdff6a48a1fc0eeb401bc4f009c88749f93` | 4 |
| `K0000004913` | `c075943948c1184493d41672f0ca00e610c90bfa7c721f24a645765dc48b9faf` | LineString | 3 | `bfb72e14ba6b9292d6de578b97bddf269940e9973f4e64add7b48a29dc06993f` | 3 |
| `K0000005348` | `88ad286f2b368130e0870360acd07d1d79614d8005ee53eed966b8db6abd2cc6` | LineString | 4 | `90c17d200b2bb85c91ff1415a90f761c6e184cc2bcfd2256476dbe1b9bcba7ad` | 4 |

- Native source file: `8baf555b9d4b69bf9e56731fe2233a29822c897f095d0f6257436aa192c89bea`
- EPSG:4326 runtime file: `d13096fb82a1e0588898ade94070becec531ebc07e77fe7795a3d92f8d56db08`
- Exact order, route identity, class, geometry type, endpoint continuity, and vertex counts: PASS.
- Independent archive extraction and GDAL/OGR reprojection matched persisted bytes exactly.
- No snap, simplify, smooth, densify, buffer, offset, topology repair, merge/split,
  polygonization, ROADA use, or road-edge derivation was present.

## Visual QA

- Rendering mechanism: isolated MapLibre GL JS 4.7.0 harness loading the actual ROAD-04 bundle and
  runtime GeoJSON.
- Browser renderer: Chromium 151.0.0.0, viewport 1024 × 768, device-pixel ratio 2.
- Camera: center `[120.85060214999999, 24.5782990011825]`, zoom
  `17.93960735962007`, bearing 0, pitch 0.
- Annotation: one rendered/queryable `中山街` label, following the line geometry.
- Collision/placement: three source features produced one visible same-name label after MapLibre
  collision handling; no duplicate text values or unrelated rendered features appeared.
- Candidate layers/sources: one authorized ROAD label layer and one authorized ROAD GeoJSON source;
  no unexpected candidate IDs.
- Shield: `9490005`, `road-parallel`, `semantic_binding_only`; zero images and zero rendered shield
  graphics. No literal `9490005` text or guessed substitute appeared.
- Screenshot SHA-256: `4124aef859cd71847f4515ad9bbf09039f35dfeacee37dd78a06921b43379062`.
- Visual evidence SHA-256: `830087a06a3aa0c05d587532e90649ca5fed5d4418c7d864eb9f6ec9a707662b`.
- Independent visual oracle: absent.
- Pixel status: `evidence_generated_but_no_independent_visual_oracle`.

The neutral harness background and glyph endpoint are recorded render-environment inputs, not
candidate styling or a reviewed golden.

## Tamper Testing

All manipulated cases failed closed, including:

- archive bytes; ROAD-01 evidence/fixture; ROAD-02 proposal/decision; ROAD-03
  approval/authorization; persisted authorization;
- rehashed but unauthorized upstream substitutes and a missing lineage record;
- plan, derived portrayal, bundle, observation, receipt, rollback manifest, and QA parent binding;
- segment replacement/order, class, route, source layer, annotation, shield code/orientation,
  graphic-role order, source geometry, runtime derivative, and vertex count;
- unexpected feature, layer, source, fabricated shield resolution, extra candidate artifact, visual
  evidence, and screenshot bytes.

Recomputing a tampered record's local hash did not bypass frozen parent or authoritative identity
bindings.

## Determinism

- Two independent temporary checkout roots, each with its own Git metadata, private archive copy,
  runtime copy, and visual-evidence copy produced byte-identical QA/provenance objects.
- QA and provenance IDs/hashes were identical across roots.
- Reverification of the actual persisted execution produced byte-identical result JSON.
- Absolute paths and generated timestamps are absent from canonical identity.
- Canonical provenance determinism: PASS.
- Renderer/pixel determinism: one captured renderer observation is hash-bound; repeated cross-engine
  pixel determinism is not claimed.

## Mutation Audit

- Private archive before/after:
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.
- Private archive remains ignored, untracked, and unstaged.
- All frozen ROAD-01/02/03/04 tracked records are unchanged from
  `7d5bacd87eb97c878ebabfd245bc7660971601a5`.
- All checked School Hero source, tests, and schemas are unchanged.
- ROAD-04 authorization, plan, derived portrayal, bundle, geometry, observation, receipt, rollback,
  consumption, and ledger identities remain unchanged.
- Canonical/live runtime, source topology, native geometry, runtime geometry, MapLibre canonical
  style, and shield semantics were not mutated.
- ROAD-05 added only ignored `qa.json` and `provenance.json` beside the execution and ignored visual
  evidence under `artifacts/tmp/`.

## Test Results

- ROAD-05 focused: `39 passed`, 0 failed, 0 skipped.
- ROAD-01/02/03/04 regression: `160 passed`, 0 failed, 0 skipped.
- Combined ROAD-01 through ROAD-05: `199 passed`, 0 failed, 0 skipped.
- School Hero regression: `11 passed`, 0 failed, 0 skipped.
- Ruff: PASS for all ROAD-05 source, CLI, and tests; format check PASS.
- Schema: 14 ROAD schemas pass Draft 2020-12 metaschema; actual QA, provenance, and visual evidence
  validate; ROAD-04 goldens and actual records remain covered by the ROAD regression.

## Acceptance Matrix

| Gate | Result | Evidence |
|---|---|---|
| AT-01 | PASS | Canonical root and origin verified after fetch. |
| AT-02 | PASS | Exact ROAD-04 base `7d5bacd...` recorded. |
| AT-03 | PASS | ROAD-03 freeze is an ancestor of ROAD-04. |
| AT-04 | PASS | Archive hash and Git boundary exact. |
| AT-05 | PASS | All frozen ROAD-01/02/03 identities and bindings verified. |
| AT-06 | PASS | All immutable ROAD-04 identities verified. |
| AT-07 | PASS | Independent verifier imports no ROAD-04 engine. |
| AT-08 | PASS | Expected native/runtime state reconstructed independently. |
| AT-09 | PASS | Exact persisted artifact set verified. |
| AT-10 | PASS | Geometry provenance and byte equality verified. |
| AT-11 | PASS | Frozen road/label/shield semantics exact. |
| AT-12 | PASS | Actual label render and collision result inspected. |
| AT-13 | PASS | Semantic-only shield verified; no fabricated graphic. |
| AT-14 | PASS | Screenshot evidence recorded; no-oracle limitation explicit. |
| AT-15 | PASS | Content-addressed lineage complete. |
| AT-16 | PASS | Provenance tamper matrix fails closed. |
| AT-17 | PASS | Unexpected-change matrix fails closed. |
| AT-18 | PASS | Independent-root canonical determinism exact. |
| AT-19 | PASS | ROAD combined regression 199/199. |
| AT-20 | PASS | School Hero regression 11/11. |
| AT-21 | PASS | Ruff, metaschema, and record validation pass. |
| AT-22 | PASS | Frozen-source and authoritative-runtime mutation audit pass. |

## Remaining Limitations

- No reviewed resolver or graphic asset exists for shield code `9490005`; the verified result remains
  intentionally `semantic_binding_only`.
- No reviewed independent ROAD visual oracle/golden exists. The screenshot is observation evidence,
  not independent pixel correctness approval.
- ROAD-04 does not specify a glyph endpoint, font asset, camera, or viewport. ROAD-05 records the
  isolated render environment but does not retroactively authorize it as production styling.
- Cross-engine/browser pixel reproducibility was not established and is not conflated with canonical
  provenance determinism.

## Final Statement

ROAD-05 is ready to proceed to ROAD-FINAL.

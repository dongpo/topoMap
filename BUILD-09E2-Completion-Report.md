# BUILD-09E2 Completion Report

## Verdict

**PASS — OFFICIAL J13/J17 APPLICABILITY BOUNDARY CLOSED; HUMAN PRODUCTION BINDING POLICY REQUIRED**

BUILD-09E2 establishes that `J13_BUILD` and `J17_BUILD` are Building members in distinct
geographic/project packages of the same authoritative 112 multidimensional SHP delivery. The
original official V4 workbook publishes one logical `BUILD` polygon schema, fields, and Building
semantics, but it publishes no application-level rule selecting either package member for NMA
production. Layer existence, layer semantics, and production applicability are therefore recorded
as three separate claims.

The authoritative result is exactly:

`authoritative-applicability-boundary-not-published`

The official evidence search is closed. No additional authoritative evidence acquisition is
justified, no J13/J17 value is selected, and the remaining choice is exactly:

`human-production-binding-policy-required`

BUILD-09F readiness is:

`READY-FOR-BUILD-09F`

No PASS in this report authorizes production implementation or activation.

## 1. Starting gate

- canonical repository: `https://github.com/dongpo/topoMap.git`;
- canonical root: the repository containing this report;
- clean starting branch: `build/build-09e1-targeted-official-binding-portrayal-resolution`;
- exact local and remote BUILD-09E1 predecessor commit:
  `ee4bbc1bf4dc5d70032dcd3129801039f3813a36`;
- BUILD-09E1 evidence-resolution identity:
  `f75c44bcb834090277588b3c23cfe48f00e965c947754497f64831d4b47b9b65`;
- BUILD-09 contract identity:
  `0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c`;
- BUILD-09E evidence-closure identity:
  `bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed`;
- BUILD-08A authorization identity:
  `4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8`;
- predecessor readiness: `J13-J17-BINDING-STILL-BLOCKING`;
- no production/runtime/source mutation authority was introduced.

All four canonical record identities were recomputed from their canonical JSON bases before the
required branch was created:

`build/build-09e2-j13-j17-production-applicability-resolution`

## 2. Authority boundary and evidence inspected

The evidence search prioritized the original official and delivery artifacts already identified by
the repository provenance:

1. original `多維度繪製圖層V4.xlsx`, Drive file
   `1C12PmP-8ZZtZbHVKRAKv0mmWE22kgzEw`, V4 decision date 2023-11-10, raw SHA-256
   `d3f065a57d10c306e9e4e686641c07ddf2fb5a6d3638b68ec4d3ea533839f308`;
2. authoritative 112 source delivery `112年多維度SHP成果_0502.zip`, SHA-256
   `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`;
3. frozen BUILD-09E1 resolution and reviewed repository provenance derived from those sources;
4. BUILD-00A J13/J17 quality observations and legacy J17 runtime use, inspected only as
   non-authoritative implementation context.

The original V4 workbook is available within the authorized evidence environment. Direct content
inspection confirms:

- logical title `(三)建物BUILD(面)`;
- logical layer code `BUILD`;
- geometry `面` (polygon);
- fields `BUILD_ID`, `TERRAINID`, `BUILD_STR`, `BUILD_NO`, `BUILD_H`, `GROUP_ID`, and `MDATE`,
  with the published types and meanings recorded in the resolution;
- terrain classes `9310100`, `9310200`, and `9310300` for permanent, under-construction, and
  temporary Building concepts;
- zero occurrences of `J13_BUILD` or `J17_BUILD` in the workbook.

The source archive contains no PDF, workbook, CSV, text, XML, JSON, Markdown, or Word manifest that
publishes an additional applicability rule. Its package paths establish both member identities and
their geographic/project scopes. Absence of an NMA-specific rule is not treated as defective
official documentation.

## 3. J13 authoritative trace

| Edge | Established value | Evidence |
| --- | --- | --- |
| official authority | 內政部國土測繪中心 (NLSC) | official V4 workbook; official 112 delivery |
| document/specification | `多維度繪製圖層V4.xlsx` | original official workbook |
| version/date | V4, 2023-11-10; delivery year 112 | workbook and delivery |
| dataset/product | 112 multidimensional spatial-information SHP delivery | delivery archive |
| package | `J13_寶山都市計畫/SHP` | archive member path |
| geographic/product scope | Baoshan urban-plan project area | archive member path |
| layer code | `J13_BUILD` | archive member path |
| official layer title | logical `(三)建物BUILD(面)`; no member-specific title published | workbook and delivery |
| geometry type | official logical polygon; delivered `PolygonZ` | workbook and delivery |
| official field schema | seven-field V4 BUILD schema | workbook and delivery |
| Building semantic meaning | BUILD carrier for terrain classes 9310100/9310200/9310300 | workbook and delivery |
| production applicability | **missing** | no authoritative edge published |

Missing edge:

`J13_BUILD → NMA production applicability`

BUILD-07 DEMO/fixture selection is explicitly non-promoting and cannot supply this edge.

## 4. J17 authoritative trace

| Edge | Established value | Evidence |
| --- | --- | --- |
| official authority | 內政部國土測繪中心 (NLSC) | official V4 workbook; official 112 delivery |
| document/specification | `多維度繪製圖層V4.xlsx` | original official workbook |
| version/date | V4, 2023-11-10; delivery year 112 | workbook and delivery |
| dataset/product | 112 multidimensional spatial-information SHP delivery | delivery archive |
| package | `J17_新竹科學工業園區特定區計畫(寶山部分)/SHP` | archive member path |
| geographic/product scope | Hsinchu Science Park special-plan project area, Baoshan portion | archive member path |
| layer code | `J17_BUILD` | archive member path |
| official layer title | logical `(三)建物BUILD(面)`; no member-specific title published | workbook and delivery |
| geometry type | official logical polygon; delivered `PolygonZ` | workbook and delivery |
| official field schema | seven-field V4 BUILD schema | workbook and delivery |
| Building semantic meaning | BUILD carrier for terrain classes 9310100/9310200/9310300 | workbook and delivery |
| production applicability | **missing** | no authoritative edge published |

Missing edge:

`J17_BUILD → NMA production applicability`

Legacy `src/nma/real_layer.py` use is explicitly non-promoting and cannot supply this edge.

## 5. Version, package, and scope hypotheses

| Hypothesis | Result | Finding |
| --- | --- | --- |
| specification version | not supported as differentiator | both members use the inspected V4 logical BUILD definition |
| source dataset version | not supported as differentiator | both occur in the same content-addressed 112 archive |
| geographic package | evidenced differentiator | Baoshan urban plan versus Science Park special plan (Baoshan portion) |
| product package | evidenced differentiator | distinct official project/package members |
| scale/product family | not supported as differentiator | no separate assignment is published |
| delivery format | not supported as differentiator | both are SHP `PolygonZ` members |
| semantic role | not supported as differentiator | both carry the same BUILD schema and terrain-class semantics |
| historical schema evolution | not established | no reviewed evidence assigns the prefixes to schema evolution |
| another boundary | not applicable | no additional deterministic boundary is published |

The corpus therefore establishes geographic/package distinction, not version routing, semantic-role
distinction, global equivalence, or production precedence.

## 6. Frozen non-J13/J17 findings

BUILD-09E2 copies and validates these findings without reinterpretation:

- annotation content: `officially-supported`, floor count followed by structure;
- annotation placement: `local-policy-required`;
- hatch spacing: `officially-supported`, exactly `2 mm`;
- hatch angle: `local-policy-required-with-official-diagonal-semantics`, no numeric angle;
- hatch resource: `local-policy-required`, no asset created or deployed;
- line code `2`: `official-physical-width-established`, exactly `0.20 mm`, no CSS-pixel value;
- colour code `7`: official black, original representation `RGB值 (R-G-B)` value `(0,0,0)`,
  no official HEX notation;
- rendering conversion: `local-output-profile-policy-required`;
- PolygonZ/derived XY: immutable and recoverable authoritative source Z, non-authoritative and
  non-writing derived XY, destructive drop-z incompatible, source mutation forbidden.

The seven BUILD-09E1 predecessor artifacts are bound by file SHA-256 and remain byte-identical.

## 7. Closure and later policy boundary

The exact distinction is:

- layer existence: `established`;
- layer semantics: `established-within-versioned-logical-BUILD-and-delivered-package-scope`;
- production applicability: `not-published`;
- official evidence search closed: `true`;
- human production-binding policy required: `true`;
- additional authoritative evidence acquisition justified: `false`;
- concrete unavailable artifact: `null`;
- selected layer or selection rule: `null`.

BUILD-09F may choose the shape and value of a local production binding among a bounded package,
version/package routing, or fail-closed single-package support. BUILD-09E2 does not select among
those policies.

## 8. Five-gate readiness

| Gate | Final state |
| --- | --- |
| hatch angle/asset | `local-policy-required` |
| annotation placement/binding | `local-policy-required` |
| J13/J17 identity | `human-production-binding-policy-required` |
| line/colour portrayal | `local-output-profile-policy-required` |
| PolygonZ/derived XY | `P2-production-candidate` |

J13/J17 is no longer an official-evidence blocker. It is a bounded human production-policy
decision. Production activation remains forbidden.

## 9. Deterministic artifacts

- applicability-resolution record:
  `data/specifications/nma-build-09e2-golden-j13-j17-production-applicability-resolution-v1.0.json`;
- canonical resolution SHA-256:
  `1a4a406da130eb34a7f6871e92230d0c82fe4bcf9e475651418780bedd5d1262`;
- successor human-policy-hold contract:
  `data/specifications/nma-build-09e2-successor-building-production-contract-v1.0.json`;
- successor contract SHA-256:
  `71b7f25239eb001454af61358acb67917d9820957ea4aeb2191ff613ee54a043`;
- successor status: `human-policy-hold`;
- remaining authoritative evidence blockers: none.

The successor binds the BUILD-09E1 commit and resolution, BUILD-09 contract, BUILD-09E closure,
BUILD-08A authorization, and BUILD-09E2 applicability resolution. It selects no layer, creates no
runtime behavior, and cannot become `production-active`.

## 10. Verification

- focused BUILD-09E2: **42 passed**;
- BUILD-00A through BUILD-09E2 historical regression: **567 passed; 3 failed**;
- frozen Core integrity: **53 passed**;
- frozen ROAD integrity: **199 passed**;
- frozen School Hero integrity: **32 passed**;
- complete repository regression with no deselections: **1166 passed; 6 failed**.

The three BUILD-chain failures are inherited stage-local descendant-scope assertions:

1. `tests/test_build_human_official_production_scope_authorization_build08a.py::test_previous_build_and_forbidden_artifacts_remain_unchanged`;
2. `tests/test_building_production_contract_build09.py::test_previous_build_frozen_artifacts_and_runtime_remain_unchanged`;
3. `tests/test_official_evidence_closure_build09e.py::test_previous_artifacts_runtime_and_source_scope_remain_unchanged`.

Each fails only because its frozen stage-local allowed-file set excludes authorized later BUILD
artifacts. No predecessor, production runtime, source, geometry, or portrayal asset changed.

The complete suite additionally reproduces the three known Agentic/demo drift failures:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`.

These pre-existing PMTiles catalog and Agentic freeze/source-asset drifts are classified and not
repaired. No other failure is accepted.

## 11. Scope

BUILD-09E2 changes exactly this report, one non-executing builder/validator, two deterministic JSON
artifacts, two closed JSON schemas, and focused tests. It does not change `src/`, production runtime
behavior, source archives, source geometry, portrayal assets, predecessor BUILD artifacts, Core,
ROAD, or School Hero files.

## 12. Next stage

Recommend:

`BUILD-09F — Human Building Production Policy Resolution`

BUILD-09F may resolve J13/J17 local production binding and the remaining explicitly bounded hatch,
annotation, line/device, and colour/output-profile policies. Do not create another general evidence
audit and do not begin BUILD-10.

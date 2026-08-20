# BUILD-02 — Building Portrayal Decision and Proposal Completion Report

Completion date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-02 IS COMPLETE AS A CLOSED, REVIEW-ONLY PORTRAYAL PROPOSAL STAGE**

BUILD-02 deterministically produces one evidence-bound decision and one portrayal proposal for the
BUILD-01 building reference. Both artifacts remain non-executable and preserve every unresolved
cartographic, schema, and `PolygonZ` decision as a pending human-review gate.

No source geometry or attribute was disclosed, mutated, repaired, transformed, or redistributed.
No runtime route was wired and no execution authorization was issued.

## 2. Exact predecessor and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Required predecessor branch | `build/build-01-building-resolution` | PASS |
| Required predecessor SHA | `2637bf03b2c866a668cfb2e43ce12058ad436196` | PASS |
| BUILD-01 semantic package | `59b6f972046dbe9af295de414525230b03ed6da4f0e78374076b5cc4a2cdd7de` | PASS |
| Immutable Core predecessor | `nma-core-v1.0-final` / `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| BUILD-02 branch | `build/build-02-building-portrayal-proposal` | PASS |
| Starting tracked worktree | clean | PASS |

## 3. Exact upstream bindings

The decision and proposal bind the complete BUILD-01 identity chain:

- private archive SHA-256:
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`;
- fixture identity:
  `build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a`;
- redacted observation identity:
  `build-observation:sha256:8fdbb3bdea8ffe715e7d76eed7c5034bd62226ba649be2206cf7a9e07b853bac`;
- redacted feature reference:
  `build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f`;
- attribute commitment:
  `ddfa112586b9c2bc3a61bdf2638b7994ba1200bfce5d8ad34988f2a24da96078`;
- `PolygonZ` geometry commitment:
  `23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f`;
- Core profile identity and source-scope commitments.

Any change to those bindings, the BUILD-01 content, privacy flags, or non-execution permissions
fails closed before a BUILD-02 artifact is produced.

## 4. Portrayal evidence

BUILD-02 consumes the existing NLSC112V5.4 review record set without changing it:

| Evidence | Identity |
|---|---|
| Record set | `nma-portrayal-recipe-review-batch-01-v0.4` |
| Record-set canonical SHA-256 | `70ef0c8e8e86ed5d2a2a4a588b41086f3fd20fb6987138e3897b71378f4b294a` |
| BUILD recipe canonical SHA-256 | `450ee18fe87ea2a7f1d783747ee22ae927c73a2f46424f65900f28f9981f2e20` |
| Source document SHA-256 | `1f9c4457d7ced86f2b7681e21be9ad3b7b7ae364981ab995ef27b468e0fa2620` |
| Source rule | `portrayal-rule:doc01:9310100` |
| Evidence section | `section:doc01-portrayal:p8` |

The record set explicitly remains a human-signoff-pending, non-executable review candidate.
BUILD-02 does not promote its legacy `J17_BUILD` runtime observation into authority; the proposal
explicitly sets `legacy_j17_runtime_binding_allowed` to false and remains bound only to the BUILD-01
`J13_BUILD` source scope.

## 5. Proposed portrayal

The proposal is closed to the source-supported representation:

- representation: feature-following hatched polygon;
- geometry: source `PolygonZ`, Core role `Polygon`, Z preserved;
- boundary primitive: `surveyed-building-boundary`;
- boundary references: line code `2`, colour code `7`;
- hatch primitive: `building-diagonal-hatch`;
- hatch clipping: feature geometry;
- hatch spacing: 2.0 mm;
- hatch orientation: semantic lower-left to upper-right diagonal;
- numeric hatch angle: unresolved (`null`);
- annotation primitive: `floor-and-structure-annotation`;
- annotation fields: `BUILD_NO`, `BUILD_STR`;
- annotation placement: unresolved pending human review.

BUILD-02 rejects attempts to invent a 45-degree angle, centroid placement, altered spacing,
geometry repair, or Z-dimension removal—even when the altered artifact is rehashed.

## 6. Open review gates

The decision and proposal freeze five required gates as `pending-human-review`:

1. `hatch-angle-transcription` — numeric hatch angle is not stated by the reviewed rule.
2. `building-annotation-placement` — collision and placement behavior is not specified.
3. `real-build-schema-binding` — observed BUILD fields are not declared globally equivalent to the documented reduced schema.
4. `line-and-color-profile` — device-independent rendering for line code 2 and colour code 7 is not approved.
5. `j13-polygonz-runtime-policy` — any future 2D runtime transformation or Z handling requires an explicit policy.

`all_gates_resolved` remains false. BUILD-02 contains no mechanism that can mark these gates
approved.

## 7. Closed authority boundary

Both artifacts require authorization and human review while setting all operational capabilities
to false:

- execution;
- source mutation;
- geometry repair;
- Z-dimension drop;
- runtime wiring;
- raw source disclosure;
- redistribution;
- legacy J17 runtime binding.

The BUILD-02 module has no subprocess, network, geometry-library, MapLibre, file-write,
authorization-ID, or idempotency capability. Its only filesystem access reads the already-tracked
portrayal evidence record.

## 8. Artifact identities

Golden BUILD-02 decision SHA-256:

`624fafe1f84164f6f28396d21153a3ed0f9795ead87b6e9c605115b35ee3c846`

Golden BUILD-02 proposal SHA-256:

`1e588ea2d7752ce7b02c28d6117c4deb1d6c8995dcbace14cfcb542eca847749`

Both use the exact frozen Core `canonical_sha256` provider. Equivalent supported BUILD-01 request
wording and semantically identical JSON key ordering produce the same two artifacts.

## 9. Acceptance results

Environment:

- Python 3.13.5;
- pytest 9.1.1;
- private archive present and hash-exact for inherited BUILD-01 acceptance.

Results:

- BUILD-02 focused acceptance: **40 passed**;
- BUILD-00A + BUILD-01 + BUILD-02 + portrayal review + frozen CORE-01/02/04: **125 passed**;
- complete repository regression: **675 collected; 672 passed; 3 failed**.

The three failures are the exact known, pre-existing Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD, Core, ROAD, School Hero, or Agent contract regression was introduced.

## 10. Exact changed files

1. `BUILD-02-Completion-Report.md` — completion verdict, evidence, open gates, boundaries, and next-stage recommendation.
2. `build_contracts/__init__.py` — BUILD-02 public contract exports.
3. `build_contracts/portrayal_decision.py` — evidence validation and deterministic decision/proposal contracts.
4. `data/specifications/nma-build-02-golden-decision-v1.0.json` — frozen decision artifact.
5. `data/specifications/nma-build-02-golden-proposal-v1.0.json` — frozen proposal artifact.
6. `schemas/build-portrayal-decision-v1.0.schema.json` — closed Draft 2020-12 decision schema.
7. `schemas/build-portrayal-proposal-v1.0.schema.json` — closed Draft 2020-12 proposal schema.
8. `tests/test_build_portrayal_decision_build02.py` — positive, schema, evidence, tamper, gate, privacy, authority, and determinism acceptance.

Existing production `src/nma` changed: **no**.

BUILD-00A, BUILD-01, frozen Core, ROAD, School Hero, Agent, legacy portrayal evidence, public
runtime, and private archive files changed: **no**.

## 11. BUILD-03 readiness recommendation

**CONDITIONAL GO — BUILD-03 MAY ENTER ONLY AS A GATE-RESOLUTION AND HUMAN-APPROVAL STAGE.**

BUILD-03 must not issue execution authorization while any of the five gates remains unresolved.
Before an executable authorization can exist, BUILD-03 must supply separately reviewable evidence
and an explicit decision for:

1. numeric hatch angle or an approved renderer-independent semantic orientation policy;
2. deterministic annotation placement and collision behavior;
3. bounded `J13_BUILD` field authority without inventing `ID`/`SOURCE` equivalence;
4. line-code 2 and colour-code 7 rendering profiles;
5. `PolygonZ` preservation/transformation behavior for the intended runtime;
6. exact authorization scope, expiry/revocation, and non-transferable proposal identity.

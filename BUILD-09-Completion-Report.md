# BUILD-09 — Official Building Semantics & Production Contract Resolution

Completion date: 2026-08-21 (Asia/Taipei)

## 1. Verdict

**PASS — PARTIAL PRODUCTION CONTRACT ESTABLISHED; UNRESOLVED GATES REMAIN**

BUILD-09 establishes a deterministic, closed, evidence-classified Building production-contract
candidate without selecting an unsupported source layer, activating production or official
portrayal, opening the private archive, changing runtime behavior, or mutating source data. The
PolygonZ/derived-XY architecture reaches P2. The other four inherited gates reach P1 because
their evidence is explicit but authoritative layer identity or production portrayal policy remains
incomplete.

The machine contract status is `partial-production-candidate`; it never emits
`production-active`.

## 2. Starting gate

| Item | Frozen value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| BUILD-08A predecessor branch | `build/build-08a-human-official-production-scope-resolution` | PASS |
| BUILD-08A predecessor commit | `6e62481530228c76c250ff0e0119752c83f655a4` | PASS |
| BUILD-08A authorization SHA-256 | `4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8` | PASS |
| BUILD-08 review SHA-256 | `b48337a6bb8cf1e6cffc54e0bbfe14383f62c1dcfdca54bf706c0ab045b42484` | PASS |
| Required BUILD-09 branch | `build/build-09-official-building-production-contract` | PASS |
| Starting tracked worktree | clean | PASS |

The local and remote BUILD-08A branch references both resolved to the required commit. The
BUILD-08A focused suite reproduced all 31 checks. Its authorization still permits evidence
collection, J13/J17 resolution through evidence, Z-preserving derived-XY design, annotation
binding design, portrayal mapping design, and labeled local-policy candidates. It still forbids
production/runtime activation, official portrayal activation, private-source automatic access,
source mutation, source Z removal, and DEMO-to-official promotion.

No predecessor artifact was repaired.

## 3. Evidence authority ledger

Every contract evidence reference has one closed BUILD-08A authority class and an exact file or
source identity. Principal evidence is:

| Evidence | Authority class | Supported scope |
|---|---|---|
| Official Document 01, NLSC112V5.4, page 8, SHA-256 `1f9c4457…` | `authoritative-official` | Surveyed building boundary, hatch, 2 mm spacing, floor/structure annotation, line code 2, colour code 7 |
| Reviewed Document 01 recipe transcription, file SHA-256 `9ba4f3c5…` | `reviewed-project-evidence` | Visual hatch orientation, observed black, candidate resource, tracked J17 observation |
| Official Document 09 revision 114.12.04, SHA-256 `b3c26f6e…` | `authoritative-schema` | Logical `BUILD` Polygon layer and `ID`, `SOURCE`, `MDATE` meanings |
| BUILD-00A J13 manifest, file SHA-256 `a5b089f7…` | `reviewed-project-evidence` | Exact-archive J13 fields, PolygonZ, counts, and bounded DEMO-fixture selection |
| BUILD-01 redacted observation, file SHA-256 `35dd7f9f…` | `reviewed-project-evidence` | Immutable J13 PolygonZ identity and commitments |
| BUILD-07 accepted evaluation, file SHA-256 `7b95e813…` | `human-demo-evaluation` | DEMO usability only |
| Existing real-layer path, file SHA-256 `d9eb720b…` | `implementation-evidence` | J17 binding, null label field, and destructive-dimensionality conflict |

The tracked private archive was not opened. Its already-frozen identity is referenced only through
the predecessor observations: `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.

## 4. Authoritative Building layer result

**Result: `indeterminate`. No layer is selected.**

The official evidence defines the logical product layer `BUILD`, Polygon geometry, and the NMA
Building concept `9310100`. The tracked exact-archive observations establish:

- `J13_BUILD`: `PolygonZ`, 2,968 records, seven observed fields; chosen previously only as the
  zero-defect, bounded DEMO fixture;
- `J17_BUILD`: `PolygonZ`, 2,839 records, the same seven observed field names; retained by the
  legacy runtime observation and containing one previously observed invalid geometry.

Repository-accessible official evidence does not identify either member as the intended global
production layer, nor does it authoritatively define their relationship. J13's prior quality
selection and J17's implementation history are not source-layer authority. Consequently:

- `selected_layer_id` is `null`;
- global J13/J17 equivalence is false;
- cross-version equivalence is false;
- a later contract must bind an exact source family/version and authoritative layer naming rule
  before selecting either layer.

Any rehashed contract that selects J13 or J17 while the resolution is `indeterminate` fails closed.

## 5. Field semantics

| Field | Authority | NMA semantic role | Allowed production use / implication |
|---|---|---|---|
| `ID` | `authoritative-schema` | Authoritative source feature identity | Document 09 conformant source only; no `BUILD_ID` equivalence |
| `SOURCE` | `authoritative-schema` | Source provenance code | Document 09 metadata only; absent observed field must not be invented |
| `MDATE` | `authoritative-schema` | Source production date | Metadata only; same-name observed field still needs value/domain validation |
| `BUILD_ID` | `reviewed-project-evidence` | Dataset-scoped record identity | Exact-archive provenance/addressing only; cannot substitute for official `ID` |
| `TERRAINID` | `reviewed-project-evidence` | Dataset-scoped Building classification | Exact-archive candidate filter for `9310100`; no global field equivalence |
| `BUILD_NO` | `reviewed-project-evidence` | Building floor count | First exact-archive annotation component; binding not an official field definition |
| `BUILD_STR` | `reviewed-project-evidence` | Building structure code | Second annotation component; official code domain remains missing |
| `BUILD_H` | `unknown` | Unbound source metadata | Opaque passthrough only; no semantic or portrayal use |
| `GROUP_ID` | `unknown` | Unbound source metadata | Opaque passthrough only; no identity/grouping/portrayal use |

Feature identity, classification, annotation content, and metadata are separate. No field receives
an official role solely because a DEMO, test, or implementation uses it.

## 6. Annotation contract

**Status: `local-policy-candidate`.**

The official content semantic is “floor count followed by structure code.” The exact-archive
candidate binding is the expression `{BUILD_NO}{BUILD_STR}` with no separator. That binding is
`reviewed-project-evidence`, not an official field definition.

The proposed placement and collision behavior remains explicitly local policy:

- anchor at the polygon pole of inaccessibility;
- require the label to remain inside the polygon;
- suppress it when no interior fit exists or a higher-priority annotation collides;
- never displace it outside the building.

A future authorized rendering adapter, not the source layer, owns formatting, placement,
collision, and suppression. It consumes derived XY plus the two bound attributes. It does not
reuse `label_field: null`, and a single source label field is not required. Font, size, halo, and
priority remain unresolved.

## 7. Portrayal and hatch resolution

| Property | Authority | Support | Result |
|---|---|---|---|
| Hatched surveyed polygon | `authoritative-official` | `officially-supported` | Retained |
| Lower-left-to-upper-right diagonal | `reviewed-project-evidence` | `implementation-supported` | Semantic orientation only |
| 45° numeric angle | `local-policy-candidate` | `local-policy-candidate` | Retained as candidate, explicitly not official |
| 2 mm hatch spacing | `authoritative-official` | `officially-supported` | Physical output spacing |
| Transparent background | `local-policy-candidate` | `local-policy-candidate` | Candidate |
| Boundary line code 2 / colour code 7 | `authoritative-official` | `officially-supported` | Official references only |
| 1 CSS px, `#111111`, opacity 1 | `local-policy-candidate` | `local-policy-candidate` | MapLibre web output candidate |
| Z-order | `unknown` | `indeterminate` | Unresolved |
| Annotation styling | `unknown` | `indeterminate` | Unresolved |

The missing `building-hatch-tile-v1.svg` is neither required by identity nor deployable. The
resource contract permits either a procedural hatch definition or an independently reviewed,
versioned equivalent asset. It requires:

- feature clipping, seamless renderer-space repetition, and scale-aware 2 mm physical spacing;
- semantic orientation plus separately governed numeric angle;
- transparent candidate background and line-code 2/colour-code 7 references;
- versioned resource identity, canonical SHA-256, parameter manifest, renderer compatibility
  result, official-row citation, visual comparison, and target-profile approval.

No hatch asset was created or deployed. A missing asset cannot be marked deployable.

## 8. PolygonZ to derived XY production boundary

**Status: `production-candidate-design-only` / P2.**

The contract fixes this boundary:

`authoritative PolygonZ → immutable source representation → derived non-writing XY portrayal view → rendering adapter`

The authoritative source remains immutable; all Z values remain preserved, recoverable, and part
of the source geometry identity. The deriver receives no source write handle. Derived XY is
non-authoritative, portrayal-only, non-writing, and may exist only ephemerally or in a
content-addressed read-only cache. It may not repair geometry or write back.

Provenance must bind the source archive, selected source layer and component hashes, source
feature identity, source PolygonZ hash including Z, derivation algorithm/version, source/output
CRS, and derived XY content hash. Rendering consumes only the derived representation.

The existing `drop-z` / `-dim XY` path is classified **`incompatible`** and must be
**bypassed by a future non-writing derived-view adapter**. Reuse as-is is forbidden. BUILD-09
does not implement that adapter.

## 9. Five-gate readiness

| Inherited gate | Classification | Reason |
|---|---|---|
| Hatch angle/asset | `P1-evidence-supported` | Official hatch and spacing exist; numeric angle and deployable resource remain local/unresolved |
| Annotation placement/binding | `P1-evidence-supported` | Content semantics and candidate fields exist; field authority, placement, collision, and styling remain unresolved |
| J13/J17 schema identity | `P1-evidence-supported` | Both observations and logical BUILD are explicit; neither member can be authoritatively selected |
| Line/color portrayal | `P1-evidence-supported` | Official code references exist; numeric output mappings remain local candidates |
| PolygonZ/derived XY | `P2-production-candidate` | Semantics, immutable boundary, provenance, renderer consumption, and legacy-path disposition are explicit |

P2 gates: **1 / 5**. P1 gates: **4 / 5**. P0 gates: **0 / 5**.

## 10. Contract identity and fail-closed behavior

Canonical BUILD-09 production-contract SHA-256:

`0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c`

The deterministic builder uses frozen Core `canonical_sha256`. The closed Draft 2020-12 schema
accepts only the exact candidate. The validator rejects forced J13/J17 selection, undocumented
field semantics, unknown evidence/readiness states, DEMO or implementation evidence promoted to
official authority, deployable missing resources, destructive Z removal, writing derived XY,
source mutation, activation, changed predecessors, and rehashed semantic changes.

## 11. Activation and source boundaries

All of the following remain false:

- production activation;
- production runtime creation;
- official portrayal activation;
- source mutation or geometry repair;
- source Z removal;
- derived output writeback;
- private-source access during BUILD-09;
- production execution.

BUILD-09 authorizes no production behavior. The existing DEMO remains unchanged.

## 12. Acceptance and regression results

Environment:

- Python 3.11.9;
- pytest 8.3.3;
- Ruff static and format checks passed;
- JSON and Draft 2020-12 schema checks passed.

Results:

- BUILD-09 focused acceptance: **31 passed**;
- BUILD-00A through BUILD-09 historical chain: **453 passed**;
- frozen Core identity/integrity: **53 passed** (52 checks plus the staged untracked-scope guard);
- frozen ROAD integrity: **199 passed**;
- frozen School Hero integrity: **24 passed**;
- complete repository regression with no deselections: **1051 passed; 4 failed**.

Before staging, the CORE-04 guard reproduced its expected refusal of untracked files. It passed
after exactly the five authorized BUILD-09 files were staged.

Three complete-suite failures exactly reproduce the known BUILD-08A predecessor Agentic/demo
drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`.

The fourth failure is the inherited, stage-local BUILD-08A scope assertion:

4. `tests/test_build_human_official_production_scope_authorization_build08a.py::test_previous_build_and_forbidden_artifacts_remain_unchanged`.

That test intentionally permits only BUILD-08A's five files relative to the BUILD-08 commit, so it
cannot pass after any descendant BUILD files are staged. It passed in the pre-stage BUILD historical
regression while the new files were untracked. BUILD-09's descendant-aware scope test replaces no
predecessor artifact and proves that the exact five BUILD-09 files are the only changes while all
BUILD-08A, BUILD-08, BUILD-07, runtime, source, Core, ROAD, and School Hero paths remain unchanged.
The predecessor test was reproduced and classified, not repaired or modified.

No new BUILD, Core, ROAD, School Hero, identity, privacy, source-integrity, portrayal-activation,
or production-runtime failure was introduced.

## 13. Exact changed files

1. `BUILD-09-Completion-Report.md` — evidence, semantics, readiness, verdict, boundaries, tests, and next-stage recommendation.
2. `build_contracts/building_production_contract.py` — deterministic non-executing builder and fail-closed validator.
3. `data/specifications/nma-build-09-golden-building-production-contract-v1.0.json` — canonical machine-readable partial production candidate.
4. `schemas/building-production-contract-candidate-v1.0.schema.json` — closed exact Draft 2020-12 schema.
5. `tests/test_building_production_contract_build09.py` — identity, evidence, semantics, resource, geometry, readiness, tamper, and frozen-boundary acceptance.

No `src/nma` runtime, source data, source geometry, private archive, production asset, BUILD-08A,
BUILD-08, BUILD-07, previous BUILD artifact, Core, ROAD, School Hero, portrayal compiler, or
MapLibre adapter changed.

## 14. Unresolved evidence and next stage

Remaining evidence gaps are:

- authoritative J13/J17 relationship and exact production layer binding;
- authoritative mappings/domains for the observed BUILD fields;
- official numeric hatch angle or an approved local production convention;
- independently reviewed hatch implementation;
- approved annotation binding, placement, collision, and style policy;
- device-independent line-code 2 and colour-code 7 profile;
- Building z-order.

Because authoritative evidence itself is missing, the recommended next stage is:

**BUILD-09E — Official Evidence Closure**

BUILD-10 is not recommended. Production activation would still require explicit separate
authorization even after all five gates reach P2. BUILD-09E has not begun.

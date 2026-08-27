# BUILD-08A — Human Official / Production Scope Resolution Completion Report

Completion date: 2026-08-21 (Asia/Taipei)

## 1. Verdict

**PASS — HUMAN OFFICIAL/PRODUCTION RESOLUTION SCOPE AUTHORIZED; PRODUCTION REMAINS HOLD**

BUILD-08A records the human decision supplied for this stage as a bounded authorization to collect
and classify evidence and design production contracts. It does not resolve an official semantic
gate, select J13 or J17, activate portrayal or production, access or execute private source data,
mutate source geometry, remove source Z, or begin BUILD-09.

## 2. Starting gate and predecessor

| Item | Frozen value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| BUILD-08 branch | `build/build-08-official-production-entry-review` | PASS |
| BUILD-08 completion commit | `666a12adf4a1b369168480e13b2b65107429d935` | PASS |
| BUILD-08 review SHA-256 | `b48337a6bb8cf1e6cffc54e0bbfe14383f62c1dcfdca54bf706c0ab045b42484` | PASS |
| BUILD-08 review file SHA-256 | `be9ee241d358ba4c426ed7756345b899dffaa2e010f5f66abbe4b24ad7355b1b` | PASS |
| BUILD-08 report file SHA-256 | `c4099b6cead5ddbca97edf4285d2496d129745fb4b6ca6709ccbdaa46b52d38f` | PASS |
| BUILD-07 completion commit | `153037a165683e0a2b39d36620c688955ca935fd` | PASS |
| BUILD-07 accepted record file SHA-256 | `7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d` | PASS |
| BUILD-07 accepted record SHA-256 | `ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c` | PASS |
| BUILD-07 template SHA-256 | `0fea2e7fe6b8ec9dd10816ba5679b04773ecd3f0761ca7b58e339f7df91139e6` | PASS |
| Required BUILD-08A branch | `build/build-08a-human-official-production-scope-resolution` | PASS |
| Starting tracked worktree | clean | PASS |

The finalized BUILD-08 focused suite reproduced all 32 checks before branch creation. BUILD-08's
entry decision was confirmed exactly: frozen DEMO `go`; official evidence collection
`conditional-go-explicit-scope-required`; official portrayal `hold`; production runtime `hold`;
zero of five gates production-ready; five of five gates unresolved.

## 3. Human-approved decisions

### A. Building layer/schema identity

Evidence-based resolution of J13 versus J17 is authorized. Neither candidate is selected. The
required trace remains:

`authoritative source specification → layer identity → field definitions → semantic meaning → NMA Building contract`

J13 is not promoted from the DEMO, J17 is not promoted from the current runtime profile, and global
J13/J17 equivalence is not assumed.

### B. Official portrayal evidence

Collection and classification of evidence for hatch orientation/pattern, fill, outline, line width,
color, opacity, annotation content/placement/collision, and portrayal order is authorized. The
45-degree hatch, current annotation placement, current 1 px line, and current `#111111` color
remain DEMO-only. When no official rule exists, only an explicitly classified
`local-policy-candidate` may be proposed.

### C. PolygonZ / derived-XY architecture

Design of a `PolygonZ authoritative source → immutable source representation → derived non-writing
XY display representation → MapLibre` architecture is authorized. The current production
`drop-z` path remains not approved. Source transformation, destructive Z removal, and treating
`-dim XY` as source normalization remain forbidden.

### D. Annotation binding

Evidence and design work may resolve `BUILD_NO + BUILD_STR` versus `label_field: null`. No binding
has been selected or implemented. The required semantic trace is source field, documented meaning,
NMA semantic concept, annotation content, and placement policy.

### E. Hatch asset

Requirements and adoption planning are authorized only after semantics are resolved. The missing
`building-hatch-tile-v1.svg` is not approved and BUILD-08A did not create it.

## 4. Closed capability matrix

| Capability | Authority |
|---|---|
| Continue frozen DEMO | `allowed` |
| Read tracked evidence | `allowed` |
| Collect authoritative official evidence | `allowed` |
| Inspect explicitly supplied official documentation | `allowed` |
| Resolve J13/J17 through evidence | `allowed` |
| Design Z-preserving derived-XY architecture | `allowed` |
| Design annotation binding | `allowed` |
| Define candidate portrayal mappings | `allowed-with-evidence-classification` |
| Define local-policy-candidate | `allowed` |
| Create production runtime | `forbidden` |
| Activate production portrayal | `forbidden` |
| Execute production Building mutation | `forbidden` |
| Access private source archive automatically | `forbidden` |
| Mutate source data | `forbidden` |
| Drop source Z | `forbidden` |
| Promote DEMO acceptance to official authority | `forbidden` |
| Invent missing official evidence | `forbidden` |

The machine record uses only `allowed`, `allowed-with-evidence-classification`, and `forbidden`.
Its closed Draft 2020-12 schema and exact validator reject unknown capabilities, unknown gate IDs,
unknown evidence classes, rehashed scope expansion, identity changes, activation, source operations,
DEMO promotion, and layer preselection.

## 5. Evidence authority policy

The closed evidence vocabulary is:

- `authoritative-official`;
- `authoritative-schema`;
- `documented-source-semantics`;
- `reviewed-project-evidence`;
- `implementation-evidence`;
- `demo-evidence`;
- `human-demo-evaluation`;
- `local-policy-candidate`;
- `unknown`.

`demo-evidence` and `human-demo-evaluation` cannot independently establish official semantics.
`implementation-evidence` cannot independently establish an official portrayal rule.

## 6. Five unresolved gates

| Gate | Official status | Production status | Production-ready | Authorized next work |
|---|---|---|---|---|
| Hatch angle/asset | `unresolved` | `hold` | `false` | Official evidence and hatch-asset requirements |
| Building annotation placement/binding | `unresolved` | `hold` | `false` | Annotation semantics, placement, and binding design |
| J13/J17 schema identity | `unresolved` | `hold` | `false` | Evidence-based Building contract resolution |
| Line/color portrayal | `unresolved` | `hold` | `false` | Official evidence or classified local policy |
| PolygonZ/derived-XY architecture | `unresolved` | `hold` | `false` | Z-preserving derived-XY architecture design |

Production-ready gates remain **0 / 5** and unresolved official gates remain **5 / 5**.

## 7. Authorization identity and explicit boundaries

Canonical BUILD-08A authorization SHA-256:

`4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8`

The record explicitly fixes all of the following to `false`:

- `production_activation_allowed`;
- `production_runtime_creation_allowed`;
- `official_portrayal_activation_allowed`;
- `source_access_allowed`;
- `source_execution_allowed`;
- `source_mutation_allowed`;
- `source_z_drop_allowed`;
- `private_source_access_allowed`;
- `unauthorized_execution_allowed`;
- `demo_to_official_promotion_allowed`.

The deterministic contract delegates identity generation to frozen Core `canonical_sha256` and has
no subprocess, GDAL, private-source inspection, execution, or filesystem-write capability.

## 8. Acceptance and regression results

Environment:

- Python 3.11.9;
- pytest 8.3.3;
- Ruff static and format acceptance passed;
- JSON and Draft 2020-12 schema validation passed.

Results:

- BUILD-08A focused acceptance: **31 passed**;
- BUILD-00A through BUILD-08A historical chain: **422 passed**;
- frozen Core identity/integrity: **53 passed** (52 identity/frozen checks plus the staged
  publication-scope guard);
- frozen ROAD integrity: **199 passed**;
- frozen School Hero integrity: **23 passed**;
- complete repository regression with no deselections: **1021 passed; 3 failed**.

The pre-existing CORE-04 stage-specific check that requires an empty untracked set was deselected
during pre-stage preparation, then rerun after the five authorized files were staged and passed.

The three executed failures exactly reproduce the known BUILD-08 predecessor Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`.

No new BUILD, Core identity, ROAD, School Hero, source-integrity, privacy, official portrayal, or
production runtime failure was introduced.

## 9. Exact changed files

1. `BUILD-08A-Completion-Report.md` — human decision, boundaries, tests, verdict, and next-stage recommendation.
2. `build_contracts/official_production_scope_authorization.py` — deterministic bounded authorization and fail-closed validator.
3. `data/specifications/nma-build-08a-golden-human-official-production-scope-authorization-v1.0.json` — canonical machine-readable authorization.
4. `schemas/build-human-official-production-scope-authorization-v1.0.schema.json` — closed Draft 2020-12 exact authorization schema.
5. `tests/test_build_human_official_production_scope_authorization_build08a.py` — predecessor, identity, gate, authority, tamper, and frozen-integrity acceptance.

No source/runtime implementation, source data, BUILD-07 evaluation, BUILD-08 review, previous BUILD
golden, Core, ROAD, School Hero, MapLibre adapter, portrayal compiler, production hatch asset, J13/J17
binding, annotation binding, or Z adapter changed.

## 10. Next-stage recommendation

**BUILD-09 — Official Building Semantics & Production Contract Resolution**

BUILD-09 may resolve through evidence and architecture design: J13 versus J17, official versus
local-policy portrayal, annotation semantics/runtime contract, Z-preserving derived-XY architecture,
and deployable hatch requirements. BUILD-09 remains evidence/design first. Production execution or
source mutation requires a later, separately authorized stage. BUILD-09 has not begun.

# GEN-00 — Feature Production Architecture Generalization Audit

## Verdict

**PASS — GENERALIZATION PARTIAL; DOMAIN BOUNDARIES REQUIRE CLOSURE**

The repository supports a canonical feature-production boundary, but it does not support treating
the complete BUILD lifecycle as a mandatory universal implementation. Canonical identity is
already established. A thin FeatureProfile is already established. Source binding, closed
lifecycle records, authorization consumption, controlled execution, verification, and release
identity are reusable contract candidates. Semantic mappings, geometry algorithms, portrayal
policy, effect rollback, and the need for a separate activation state remain domain-owned.

GEN-00 authorizes no refactor, migration, activation, source operation, or RIVERL implementation.

## 1. Scope, baseline, and method

The audit was performed from the exact frozen BUILD final baseline and moved to the separate branch
gen/gen-00-feature-production-generalization-audit before any deliverable was added.

| Identity | Verified value |
| --- | --- |
| BUILD FINAL_SHA | 95de5fa3657a2c8ac7847f1ee1010c48ea984cd7 |
| BUILD freeze branch | freeze/build-final-95de5fa |
| BUILD annotated tag | nma-build-v1.0-final, annotated, peeled to FINAL_SHA |
| BUILD freeze-manifest identity | 627f129f56c22b4f55db51a22fbba02cacaf25e3832056254baf2b850749e30c |
| Core final | nma-core-v1.0-final → 5eb138ae7686502431587743ebce9ddf92c5a799 |
| ROAD final | nma-road-v1.0-final → 325c70d5335f57c43a8af85822db25032aa225c3 |
| School canonical freeze | freeze/hero-final-school-hero-56f99eb → 56f99eb9ae63272a68accac3041fb10eacefb986 |

The BUILD manifest identity was independently recomputed with nma.core.canonical_sha256 after
removing canonical_manifest_sha256. The declared and computed values are equal.

The audit inspected tracked code, closed schemas, deterministic records, focused tests, completion
reports, release manifests, and tracked data inventory. The private archive was not opened or
extracted. Only its already-established SHA-256 and Git boundary were checked.

## 2. Existing generic primitives

| Component | Classification | Finding |
| --- | --- | --- |
| src/nma/core/identity.py canonical_json and canonical_sha256 | canonical-core | The sole adopted generic canonical JSON/content-identity provider across School, ROAD, and BUILD. |
| src/nma/core/identity.py ArtifactReference | canonical-core | A valid immutable domain-neutral id/digest primitive, but not a lifecycle or lineage contract. |
| src/nma/core/feature_profile.py FeatureProfile | canonical-core | A canonical thin immutable compatibility envelope for geometry role, identity payload, source scope, and metadata. It deliberately does not interpret domain keys or grant authority. |
| src/nma/feature_profile_adapters.py | generic-candidate | School and ROAD read-only compatibility adapters prove adapter feasibility, but neither frozen executor consumes these views. |
| build_contracts/feature_profile.py | domain-specific | A BUILD-owned adapter tied to the accepted J13 entry fixture and BUILD-01 readiness scope; it explicitly grants no execution authority. |
| src/nma/real_layer.py REAL_LAYER_PROFILES | legacy | A mixed VS3 School/RIVERL/Building table. School still consumes it; BUILD-10 explicitly bypasses its global J17 and destructive drop-z Building behavior. |
| src/nma/real_layer.py archive inventory/extraction helpers | generic-candidate | Safe, reused component-family inventory and copy extraction, but still coupled to ZIP/Shapefile/GDAL assumptions. |
| Domain self-hash and JSON persistence helpers | duplicated | Core hashing is shared, but self-hash exclusion, canonical-file bytes, record verification, and JSON writing repeat in School, ROAD, and BUILD. |

### Primitive conclusion

Core identity is genuinely canonical. FeatureProfile is also canonical, but only at its deliberately
thin compatibility level. It is not a production profile, source-binding protocol, semantic
contract, or execution contract.

The School/ROAD adapters are partial abstractions: useful evidence for a future adapter boundary,
not authoritative execution dependencies. The BUILD adapter is not a generic primitive disguised
by its filename; it is visibly BUILD-owned and fixture-specific.

No replacement primitive is created by GEN-00.

## 3. Lifecycle crosswalk

| Lifecycle stage | School Hero | ROAD | BUILD | Classification |
| --- | --- | --- | --- | --- |
| Evidence and semantics | Evidence/proposal lineage exists. The production HERO-03 issuer is absent from this checkout. | ROAD-01 binds exact K14 records, topology, route, fixture, archive, and reviewed evidence. | BUILD-01 and BUILD-08 through 09E2 separate observation, official semantics, evidence authority, applicability, and local-policy gaps. | intentional-divergence |
| Human policy/authorization | HERO-04 consumes a complete human-approved authorization; it does not produce one. | ROAD-03 emits frozen approval and a restricted execution capability. | BUILD-08A bounds evidence scope; BUILD-09F authorizes local production policy; BUILD-11A separately authorizes activation. | generic-candidate |
| Production contract | No separate artifact; responsibility is embedded in authorization and execution code. | No named contract; proposal, capability, and ROAD-04 constants form an implicit frozen contract. | BUILD-09 candidate becomes the closed finalized BUILD-09F production contract. | generic-candidate |
| Implementation/execution | Atomic point-data and marker portrayal engine with idempotency and persisted artifacts. | Atomic line-data execution with native/runtime derivatives, portrayal, consumption, and ledger. | BUILD-10 package-scoped PolygonZ validation and ephemeral derived-XY portrayal, still inactive. | generic-candidate |
| Observation/receipt | Runtime observation, plan, bundle, receipt, data, and derived SVG. | Runtime observation, derived portrayal, bundle, receipt, geometry artifacts, consumption, rollback. | Controlled implementation plan, provenance, observation, verification, receipt, derived data, resource, and bundle identities. | duplicated |
| Verification/provenance | HERO-05 independently replays expected data/portrayal/bundle and emits QA plus request-to-artifact provenance. | ROAD-05 independently reconstructs native/runtime geometry, frozen lineage, render evidence, QA, and provenance. | BUILD-11 independently verifies J13/J17 deterministic replays and emits activation readiness. | generic-candidate |
| Rollback/cleanup | Removes runtime layer/source/image; preserves receipt; cleans staging after failure. | Deterministic rollback manifest, staging cleanup, and immutable authorization-consumption state. | BUILD-10 discards ephemeral output; BUILD-12 deactivates only process-local state; source rollback is unnecessary. | intentional-divergence |
| Activation | No separate production activation authorization/state. | No separate post-verification activation state machine. | BUILD-11A authorization precedes BUILD-12 precheck, activation, postcheck, receipt, reversible state, and activated baseline. | intentional-divergence |
| Freeze/release | Canonical freeze branch is referenced by later integrity evidence; no comparable School final manifest is present. | ROAD-FINAL has annotated tag, freeze branch, manifest/report, and deterministic final identities. | BUILD-FINAL has annotated tag, freeze branch, closed manifest, active baseline, and source/release identities. | generic-candidate |

### Crosswalk conclusion

The shared lifecycle is a set of roles, not a single required state machine. BUILD offers the
strongest explicit separation of evidence, policy, contract, verification, activation, and freeze.
ROAD proves a mature path can legitimately omit separate activation. School proves that a mature
executor/verifier may consume external authorization while the issuer remains outside the
checkout. These differences are architectural evidence, not missing fields to fill with invented
records.

## 4. Component classification

Every major audited component has exactly one classification in the machine record. The principal
results are:

| Component group | Classification | Boundary |
| --- | --- | --- |
| Core canonical JSON/content hashing | canonical-core | Shared identity mechanism |
| Core ArtifactReference | canonical-core | Shared immutable artifact reference |
| Core FeatureProfile | canonical-core | Shared thin compatibility envelope only |
| School/ROAD FeatureProfile adapters | generic-candidate | Read-only adapter examples, not execution authority |
| BUILD FeatureProfile adapter | domain-specific | BUILD entry fixture and readiness scope |
| REAL_LAYER_PROFILES table | legacy | Mixed VS3 profiles; frozen BUILD path is explicitly incompatible |
| Archive inventory/extraction helpers | generic-candidate | Reused read-only source mechanics |
| School executor/verifier | domain-specific | School point/schema/portrayal/runtime semantics |
| ROAD resolution/authorization/executor/verifier | domain-specific | Exact route/topology/line portrayal capability |
| BUILD evidence resolution | domain-specific | Building official/local-policy and J13/J17 semantics |
| BUILD policy/contract separation | generic-candidate | Reusable lifecycle role with Building-specific content |
| BUILD implementation and activation registry | domain-specific | PolygonZ, Building portrayal, and one active binding |
| Domain record-hash/persistence helpers | duplicated | Same mechanics around the canonical Core provider |
| Agent run/handoff provenance | intentional-divergence | Governance trace only; it must never impersonate production authority |

No audited major component is classified indeterminate. Indeterminacy remains in future source
availability and in the unproven shape of the proposed generic contracts.

## 5. Required generalization dimensions

| # | Dimension | Classification | Common behavior | Domain variation / duplication | Reusable contract? |
| ---: | --- | --- | --- | --- | --- |
| 1 | Canonical identity | canonical-core | Canonical UTF-8 JSON and SHA-256 | Record hash bases, self-hash exclusions, file identities, and prefixes remain domain-owned; helper logic repeats. | Yes |
| 2 | Feature profile | generic-candidate | Immutable geometry role, identity, and source scope | Payload keys and authority differ; BUILD is entry-fixture-only; three adapters map manually. | Yes, thin only |
| 3 | Source/package binding | generic-candidate | Bind exact source, scope, and selected members before output | Six School MARK layers, ordered ROAD segments, and one BUILD package member use separate checks. | Yes |
| 4 | Schema validation | duplicated | Fail closed on geometry, fields, CRS/profile, and invariants | School GeoJSON, ROAD OGR/topology, and BUILD ordered seven-field validators are separate. | Yes, envelope only |
| 5 | Evidence provenance | generic-candidate | Bind evidence/source identities and authority context | School injects upstream lineage; ROAD uses fixed reviewed IDs; BUILD classifies official/reviewed/local policy. | Yes |
| 6 | Semantic mapping | domain-specific | Map source fields/codes to NMA concepts | Point classification, route identity, and Building floor/structure meaning are materially different. | No shared mapping |
| 7 | Human policy/authorization | generic-candidate | Explicit hash-bound authority separated from provenance | School consumes external authority; ROAD freezes a capability; BUILD separates policy and activation authority. | Yes |
| 8 | Production contract | generic-candidate | Bind semantics, policy, source scope, safety, and readiness | Explicit only in BUILD; implicit and distributed in School/ROAD. | Yes |
| 9 | Geometry policy | domain-specific | State geometry type and forbid unauthorized mutation | Point filtering, line continuity, and PolygonZ preservation/interior point cannot share one algorithm. | No universal policy |
| 10 | Derived geometry | generic-candidate | Separate authoritative geometry from deterministic derivative with provenance | School points, ROAD native/runtime lines, and BUILD PolygonZ-to-XY have different dimensional rules. | Yes |
| 11 | Portrayal policy | domain-specific | Derived portrayal is evidence/policy-bound | School SVG, ROAD label/shield, and BUILD hatch/annotation/output profile differ. | No universal policy |
| 12 | Execution plan | duplicated | Deterministic hash-bound plan before effects | Three independent plan shapes and self-hash conventions. | Yes |
| 13 | Execution receipt | duplicated | Bind authority, execution identity, outputs, and completion | School/ROAD persist artifacts; BUILD-10 is ephemeral and BUILD-12 adds activation receipt. | Yes |
| 14 | Provenance chain | generic-candidate | Content-addressed parent links across lifecycle | Node kinds vary; chain mechanics/completeness checks repeat. | Yes |
| 15 | Observation | duplicated | Separate observed state from plan/receipt | Layer events, line/render evidence, and package replay observations use separate schemas. | Yes |
| 16 | Verification | generic-candidate | Independently derive expected state and compare observed identities | DomainVerifier predicates are necessarily different; orchestration/check envelopes repeat. | Yes |
| 17 | Fail-closed behavior | generic-candidate | Stop on missing, ambiguous, stale, unauthorized, or tampered input without fallback | Failure codes and invalidation predicates vary; exact-field/digest/error logic repeats. | Yes |
| 18 | Rollback/cleanup | intentional-divergence | Explicit cleanup/reversibility; source is never rollback target | Runtime-object removal, ledger rollback, ephemeral cleanup, and state deactivation are different effect models. | No universal rollback |
| 19 | Activation authorization | generic-candidate | Where activation exists, authorize it separately after verification | Only BUILD implements it; School/ROAD do not prove it mandatory. | Yes, optional |
| 20 | Activation state | intentional-divergence | Explicit/verifiable when a switchable binding exists | Only BUILD has the active-state machine. | No mandatory state |
| 21 | Freeze/release identity | generic-candidate | Bind immutable release ref/manifest and production identities | ROAD/BUILD have full finals; School has only referenced freeze identity here. | Yes |

The machine record preserves the full rationale for every row and an exact boolean decision for
whether a reusable contract is justified.

## 6. Explicit duplication matrix

| Capability | School | ROAD | BUILD | Common primitive? | Domain-specific? | Duplication risk |
| --- | --- | --- | --- | --- | --- | --- |
| Canonical identity | Core adopted | Core adopted transitively | Core adopted | Yes | No | Medium |
| Feature profile | Read-only adapter; executor uses REAL_LAYER_PROFILES | Read-only adapter; executor does not consume it | BUILD-owned entry adapter used by resolution binding | Yes | Yes | Medium |
| Source/package binding | Six MARK layers + archive | K14/layer/route/ordered segments | Package scope → J13/J17 member | No | Yes | High |
| Schema validation | Point/TERRAINID/count | Line fields/CRS/count/topology | Ordered seven-field/PolygonZ/package | No | Yes | High |
| Evidence provenance | Injected request-to-approval lineage | Frozen reviewed evidence/package | Official/reviewed/local-policy chain | No | Yes | High |
| Semantic mapping | School code/MARK fields | Route/segment identity | Building class/floor/structure/package | No | Yes | Low |
| Human policy/authorization | External HERO-03 artifact | ROAD-03 capability | BUILD-09F policy + BUILD-11A activation | No | Yes | High |
| Production contract | Implicit in authorization/engine | Implicit in proposal/capability/constants | Explicit finalized contract | No | Yes | High |
| Geometry policy | Point XY/reprojection | Continuity/order/vertex preservation | PolygonZ/XY/interior point | No | Yes | Low |
| Derived geometry | Derived School GeoJSON | Native + EPSG:4326 lines | Non-authoritative XY | No | Yes | High |
| Portrayal policy | SVG marker operations | Line label/semantic shield | Hatch/outline/annotation/profile | No | Yes | Medium |
| Execution plan | School plan | ROAD plan | BUILD plan | No | Yes | High |
| Execution receipt | Persisted receipt | Receipt + consumption | Controlled + activation receipts | No | Yes | High |
| Provenance chain | Request → artifact | Archive/evidence → rollback/artifact | Evidence/policy/contract → activation | No | Yes | High |
| Observation | Runtime layer observation | Runtime + visual observations | Controlled + active replay observations | No | Yes | High |
| Verification | Expected-state replay | Archive/render reconstruction | Controlled/post-activation matrices | No | Yes | High |
| Fail closed | Reject + clean before commit | Reject without fallback/mutation | Reject before activation; deactivate on postcheck failure | No | No | High |
| Rollback/cleanup | Runtime removal + staging cleanup | Rollback manifest + ledger | Ephemeral cleanup + deactivation | No | Yes | Medium |
| Activation authorization | No separate stage | No separate stage | BUILD-11A | No | Yes | Low |
| Activation state | No separate state | No separate state | Process-local active flags | No | Yes | Low |
| Freeze/release identity | Referenced freeze branch | Tag/branch/manifest/report | Tag/branch/manifest/active baseline | No | No | High |

### Quantification

- School-adjacent execution/verification schemas: 7.
- ROAD schemas: 15.
- BUILD/Building schemas: 28.
- Total adjacent domain schema family count: 50.
- Controlled execution surfaces: 3.
- Domain verifier surfaces: 3.
- Explicit domain record/self-hash helper surfaces: at least 4.
- Explicit domain canonical JSON writer surfaces: at least 3.

These are structural lower bounds. The more important duplication is semantic and lifecycle
duplication: plan, receipt, observation, provenance, fail-closed, and release roles are independently
specified even when their source text is dissimilar.

## 7. Candidate canonical architecture

The repository evidence supports this target, with activation explicitly optional:

NMA Core Identity
→ Feature Profile
→ Evidence / Semantic Contract
→ Human Policy Authorization
→ Feature Production Contract
→ Domain Adapter
→ Controlled Execution
→ Verification
→ Optional Activation
→ Freeze

### Framework-owned responsibilities

- canonical identity and strict digest validation;
- immutable feature-profile envelope;
- artifact and parent references;
- closed lifecycle envelopes for production contract, plan, receipt, observation, verification,
  and release;
- uniform fail-closed status/check vocabulary;
- explicit declaration of optional activation and effect-specific cleanup capabilities.

### Domain-owned responsibilities

- source meaning and semantic mapping;
- schema particulars and domain codes;
- geometry algorithms and invariants;
- portrayal semantics and output-profile values;
- domain verification predicates;
- effect-specific rollback;
- whether activation is a distinct lifecycle stage.

### Evidence limit

The architecture is supported as a separation of responsibilities, not as a mandate that every
feature replay BUILD's stage count or file layout. School lacks a local authorization producer and
full final manifest. ROAD lacks a distinct production contract and activation stage. BUILD's
activation registry is process-local and Building-specific. GEN-01 must preserve these facts.

## 8. Candidate domain adapter boundary

| Interface | Owns | Must not own |
| --- | --- | --- |
| SourceBinding | Exact source/package/layer selection; component identities; ambiguity/availability checks; read-only source handle description | Semantic meaning; portrayal; execution authority; mutation or repair |
| SchemaContract | Closed fields/geometry/CRS/dimensionality; schema identity; validation results | Source selection; semantic equivalence; repair; authorization |
| SemanticMapping | Field/code → NMA concept; annotation content; mapping evidence/authority | Geometry mutation; device portrayal; execution/activation authority; fallback equivalence |
| GeometryPolicy | Allowed geometry and transformations; source immutability; derivative algorithm identity; geometry checks | Package selection; portrayal styling; human policy; writeback |
| PortrayalPolicy | Domain portrayal semantics; resources; output-profile conversion; runtime bundle fragments | Source authority; invented semantics; execution authorization; geometry repair |
| DomainVerifier | Independent expected-state derivation; invariants; tamper tests; QA classification | Authorization issuance; execution; silent repair/fallback; activation without separate authority |

The framework may own the envelope and protocol conformance. Adapter implementations own domain
content. An adapter must never become an authority escalator.

## 9. Data availability audit

### RIVERL

Status: **tracked-source-available**.

Verified tracked evidence:

- four complete Shapefile component families: clean, defective, schema-mismatch, and wrong-CRS;
- 20 tracked .shp/.shx/.dbf/.prj/.cpg components;
- eight tracked VRT/CSV fixture-source files for the same four families;
- data/specifications/taiwan-5000-riverl-112.json;
- clean/defective fixtures are LineString with the declared RIVERL fields;
- schema-mismatch exposes RIVERID rather than RIVERLID;
- wrong-CRS has a distinct projection identity;
- existing validator/QA tests already exercise RIVERL rules.

This is sufficient source availability for a later generalization proof. It is not production
authorization.

### LANDUSE

Status: **not-established**. No tracked LANDUSE-named source shapefile or fixture family was found.
LANDUSE is not the default proof candidate.

### STREAM

Status: **unverified-source-availability**. No dedicated tracked STREAM-named source shapefile or
fixture family was found.

### Pond / fish pond

Status: **portrayal-evidence-only-source-unverified**. The tracked fish-pond SVG and demo/presentation
evidence establish portrayal evidence, not a dedicated production pond source layer.

### Private source archive

Status: **unknown-not-inspected**. The archive remains ignored, untracked, and unstaged at the
already-frozen SHA-256 4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53.
GEN-00 did not open or extract it and infers no private layer availability.

## 10. Future proof-feature ranking

| Rank | Candidate | Recommendation | Reason |
| ---: | --- | --- | --- |
| 1 | RIVERL | Recommended for a later proof | Tracked source and failure fixtures exist; river LineString semantics and quality rules materially differ from BUILD PolygonZ portrayal. |
| 2 | Pond/fish pond | Hold | Useful portrayal evidence, but no dedicated tracked production source is established. |
| 3 | STREAM | Hold | Dedicated source availability is unverified. |
| 4 | LANDUSE | Do not use as default | No tracked LANDUSE source shapefile is established. |

RIVERL is the strongest candidate precisely because it can challenge BUILD-shaped assumptions:
LineString geometry, river topology/quality rules, schema and CRS failure fixtures, and different
semantic/portrayal needs.

## 11. GEN-01 recommendation

**GEN-01 — Feature Production Contract Boundary Closure**

Objective: define and test closed, domain-neutral lifecycle envelopes and adapter protocols without
migrating or refactoring frozen School, ROAD, or BUILD implementations.

In scope:

- artifact and parent-reference envelope;
- feature production contract envelope;
- plan, receipt, observation, verification, and release record envelopes;
- ownership protocols for SourceBinding, SchemaContract, SemanticMapping, GeometryPolicy,
  PortrayalPolicy, and DomainVerifier;
- conformance fixtures proving optional activation and effect-specific cleanup;
- a RIVERL proof plan using only tracked fixtures.

Out of scope:

- any frozen implementation migration;
- RIVERL production implementation;
- LANDUSE nomination;
- private archive inspection;
- source or portrayal asset mutation;
- runtime activation.

GEN-01 exit gate: a later RIVERL proof may begin only when the closed envelopes preserve domain
ownership, optional lifecycle stages, and fail-closed behavior without requiring BUILD-specific
fields.

## 12. Deliverables and integrity

- GEN-00-Generalization-Audit.md — this evidence-backed architecture decision.
- data/specifications/nma-gen-00-feature-production-generalization-audit-v1.0.json — canonical
  machine-readable classifications, matrices, data availability, and GEN-01 recommendation.
- schemas/feature-production-generalization-audit-v1.0.schema.json — closed Draft 2020-12 schema.
- tests/test_feature_production_generalization_gen00.py — focused identity, schema, matrix,
  availability, adapter-boundary, frozen-integrity, and scope tests.

The audit record is content-addressed with nma.core.canonical_sha256 after excluding its
audit_sha256 field. No timestamp or private-source content participates in its identity.

Validation results:

- focused GEN-00 audit: 11 passed;
- Core identity/profile, Core adoption, and School authorization regression: 46 passed;
- ROAD-01 resolution, ROAD-02 portrayal decision, and ROAD-03 authorization regression:
  104 passed;
- BUILD production-contract and human-policy regression: 57 passed, 2 historical
  stage-local exact-diff assertions deselected;
- public/non-private BUILD-FINAL integrity: 8 passed, 2 tests deselected;
- JSON parsing, Draft 2020-12 meta-schema and record validation: PASS;
- Ruff check and format check for the focused test: PASS;
- Git diff whitespace check: PASS;
- exact four-file GEN-00 scope from nma-build-v1.0-final: PASS.

The two BUILD-FINAL deselections are the private-archive policy test and BUILD-FINAL's historical
own-stage diff assertion. The BUILD contract/policy deselections are predecessor-stage dirty/diff
assertions that intentionally reject later authorized artifacts. GEN-00 did not run a private
source replay, inspect private archive contents, or relax any functional assertion.

A PASS at GEN-00 establishes only the partial boundary described above. It does not authorize refactoring.

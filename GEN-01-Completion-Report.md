# GEN-01 — Generic Contract & Domain Interface Closure

## 1. Verdict

**PASS — GENERIC CONTRACT AND DOMAIN INTERFACE CLOSED**

GEN-01 closes a minimum, machine-verifiable architecture boundary around canonical identity,
lifecycle linkage, capability declaration, validation, and a conceptual domain-adapter interface.
It creates no runtime framework and changes no production implementation. Domain payloads remain
opaque to the generic layer.

## 2. Canonical repository and branch

- Repository: `https://github.com/dongpo/topoMap.git`
- Predecessor branch: `gen/gen-00-feature-production-generalization-audit`
- GEN-01 branch: `gen/gen-01-generic-contract-interface-closure`
- Starting worktree: clean
- History rewrite, merge, tag, or force-push: none

## 3. Exact predecessor

Local and canonical remote GEN-00 resolved exactly to
`b745a98f8d465259a2cb7c2b3af3df112a10ea37` after remote refs and tags were fetched.
GEN-01 was created from that exact commit.

The four GEN-00 artifacts are byte-identical to the predecessor. The GEN-00 audit identity was
independently recomputed with `nma.core.canonical_sha256` after excluding `audit_sha256`:

`2e96f00ada42e22c7dc50387cb1fbf651b6fcbbdff94af796c0fd1985ffe86e3`

## 4. Final local, upstream, and remote identity

This tracked report follows the repository's non-self-referential finalization convention: a file
cannot contain the SHA of the commit that contains that file. The exact final local SHA, upstream
SHA, and canonical remote SHA are therefore recorded in the post-push delivery. Acceptance
requires all three to be equal, with a clean worktree, after a normal non-force push.

## 5. Frozen identity verification

| Baseline | Canonical identity | Verification |
| --- | --- | --- |
| BUILD-FINAL | `nma-build-v1.0-final^{}` → `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7` | annotated tag and remote freeze branch exact |
| CORE-FINAL | `nma-core-v1.0-final^{}` → `5eb138ae7686502431587743ebce9ddf92c5a799` | annotated tag exact |
| ROAD-FINAL | `nma-road-v1.0-final^{}` → `325c70d5335f57c43a8af85822db25032aa225c3` | annotated tag exact |
| School Hero | `freeze/hero-final-school-hero-56f99eb` → `56f99eb9ae63272a68accac3041fb10eacefb986` | canonical remote branch exact |

No frozen branch, tag, manifest, implementation, runtime, or historical artifact was modified.

## 6. Primary architecture answer

The minimum stable generic contract is:

1. one canonical Core identity dependency with no fallback;
2. a closed lifecycle envelope carrying identity, domain and adapter contract versions,
   capability-declaration identity, lifecycle role, authorization state/reference, parent and
   provenance references, pre-mutation validation, opaque domain payload, ownership, and an
   explicit non-authorizing mutation boundary;
3. a closed machine-readable domain capability declaration;
4. a conceptual adapter boundary for validation, authorization consumption, planning, execution,
   observation, receipt, provenance, and verification;
5. explicit optional declarations for rollback, activation, and release evidence.

This lets a future domain describe or implement the contract without changing canonical Core,
duplicating the generic linkage vocabulary, or transferring domain knowledge to the generic
layer.

## 7. Layer A — canonical Core identity boundary

The sole generic identity authority is `nma.core.canonical_sha256` over
`nma.core.canonical_json`, implemented by `src/nma/core/identity.py`.

- canonical authorities: `1`
- fallback authorities: `0`
- compatibility, shadow, local, or domain substitutes: forbidden
- missing Core identity dependency: fail closed before mutation

The schemas express the provider and canonicalizer as constants and require
`fallback_allowed: false`.

## 8. Layer B — generic lifecycle envelope

The lifecycle envelope is a role envelope, not a universal state machine. It does not require
School, ROAD, and BUILD to use the same stage count or stage order. Its generic content is limited
to architecture identity and linkage. `domain_payload` is deliberately open internally and is
normatively opaque to generic processing.

Mandatory envelope structure:

- schema, envelope, artifact, domain, adapter, and capability-declaration identity;
- explicit lifecycle role and contract versions;
- parent, authorization, and provenance linkage;
- canonical Core identity dependency;
- pre-mutation validation result;
- ownership declaration;
- non-authorizing and non-mutating processing declaration;
- opaque domain payload.

Post-authorization roles require a bound authorization reference. Intent and authorization roles
may represent a pre-authorization state, but still declare that authorization is required before
mutation.

## 9. Mandatory and optional lifecycle capabilities

Mandatory for a conforming feature-production domain:

- domain identification and contract/version declaration;
- input validation and canonical identity consumption;
- authorization consumption before mutation;
- planning and execution boundaries;
- derived-output reference, observation, and receipt production;
- provenance reporting and a verification boundary;
- machine-readable capability declaration.

Optional and honest only when explicitly declared with a domain-owned contract reference:

- rollback evidence;
- activation evidence;
- release evidence.

Not mandatory are a single stage sequence, a local intent/authorization issuer, a standalone
production-contract file, rollback behavior, production activation behavior, or a ROAD/BUILD-style
release manifest.

## 10. Layer C — domain adapter contract

`nma.generic-domain-adapter/1.0` is a conceptual, machine-verifiable sidecar interface. It declares
the boundaries a domain supplies; GEN-01 does not implement dispatch, execution, discovery, or a
base class.

The minimum interface covers domain identification, contract/version declaration, input
validation, canonical identity consumption, authorization consumption, planning boundary,
execution boundary, observation production, receipt production, provenance reporting,
verification boundary, and optional capability declaration.

It must not interpret domain payload, issue authorization, execute mutation, repair content,
perform rollback, perform activation, or substitute identity.

## 11. Capability declaration decision

A machine-readable capability declaration is required. The declaration includes only architecture
boundary fields:

- domain, adapter, and contract identities/versions;
- canonical identity dependency and no-fallback rule;
- mandatory boundary capabilities;
- optional rollback, activation, and release capability declarations;
- semantic, geometry, portrayal, verification, and provenance contract references;
- ownership, dependency-failure, and mutation-boundary rules;
- deterministic declaration identity.

It contains no universal feature ontology, RIVERL field, feature semantics, geometry algorithm,
portrayal value, rollback procedure, or activation implementation. A supported optional capability
requires a contract reference; an unsupported capability requires `null`.

## 12. Domain-owned responsibilities

| Area | Generic layer may carry | Generic layer must not own |
| --- | --- | --- |
| Semantics | contract identity/version and evidence reference | meaning, classification, ontology/schema interpretation, relationships, eligibility |
| Geometry | contract identity/version and derived artifact reference | construction, topology, validation semantics, repair, dimensional changes, transformations |
| Portrayal | contract identity/version and output reference | symbols, styles, labels, shields, ordering, rendering rules |
| Rollback | capability and evidence identity/reference | cleanup selection, restoration, removal, state mutation |
| Activation | capability and evidence identity/status/reference | readiness meaning, authority, gates, production activation, domain checks |

## 13. Final generic invariants

| ID | Resolution | Enforcement |
| --- | --- | --- |
| GINV-01 | ACCEPTED — canonical lifecycle identity consumes Core | provider/canonicalizer constants and self-hash tests |
| GINV-02 | ACCEPTED — no identity fallback | fallback false and authority count zero |
| GINV-03 | ACCEPTED — mandatory dependencies fail before mutation | required fields and authorization conditional |
| GINV-04 | ACCEPTED, BOUNDED — determinism applies only where promised | Core canonicalization and contract-specific hash rules |
| GINV-05 | ACCEPTED — domain knowledge stays domain-owned | opaque payload and ownership constants |
| GINV-06 | ACCEPTED — lifecycle lineage is reconstructable | artifact, parent, authorization, provenance, and version linkage |
| GINV-07 | ACCEPTED — generic processing has no production authority | all generic mutation/authority flags false |
| GINV-08 | ACCEPTED — versions are explicit | closed version constants and validation rejection |
| GINV-09 | ACCEPTED — capability claims require evidence contracts | supported/reference schema conditional |
| GINV-10 | ACCEPTED — no frozen refactor required | allowlist and predecessor blob-equality tests |

The machine record contains the full normative statement, evidence, enforcement, focused test
coverage, and status for every invariant.

## 14. Architecture evidence matrix

| Concern | School Hero | ROAD | BUILD | Generic resolution |
| --- | --- | --- | --- | --- |
| Core identity | SHARED — Core imported | SHARED — Core imported | SHARED — Core imported | mandatory shared authority |
| Authorization | SHARED — external authorization consumed | SHARED — restricted capability issued/consumed | SHARED — policy authorization consumed | mandatory consumption boundary |
| Planning | SHARED — hash-bound plan | SHARED — closed plan | SHARED — controlled plan | mandatory boundary, domain payload |
| Execution | SHARED — point/marker engine | SHARED — line/portrayal engine | SHARED — non-activating PolygonZ implementation | mandatory boundary, never generic execution |
| Observation | SHARED — runtime observation | SHARED — runtime/visual observations | SHARED — controlled observation | mandatory reference role |
| Receipt | SHARED | SHARED | SHARED | mandatory linkage role |
| Provenance | SHARED — request-to-artifact | SHARED — frozen lineage | SHARED — source/derivation/contract lineage | mandatory linkage role |
| Verification/QA | SHARED — independent replay | SHARED — independent reconstruction | SHARED — independent readiness verification | mandatory boundary, domain predicates |
| Semantics | DOMAIN_OWNED | DOMAIN_OWNED | DOMAIN_OWNED | references only |
| Geometry | DOMAIN_OWNED | DOMAIN_OWNED | DOMAIN_OWNED | references only |
| Portrayal | DOMAIN_OWNED | DOMAIN_OWNED | DOMAIN_OWNED | references only |
| Rollback | OPTIONAL_CAPABILITY — runtime cleanup | OPTIONAL_CAPABILITY — manifest/ledger | OPTIONAL_CAPABILITY — ephemeral cleanup/deactivation | evidence reference only; behavior domain-owned |
| Activation | NOT_SUPPORTED | NOT_SUPPORTED | OPTIONAL_CAPABILITY — separate authorized activation | optional evidence reference; behavior domain-owned |

The full machine matrix records evidence paths and findings. It does not manufacture symmetry.

## 15. Frozen compatibility result

- compatible with frozen Core, School Hero, ROAD, BUILD, and Agent runtime: `true`
- required frozen production refactors: `0`
- existing frozen implementations required to consume the new schema: `false`
- compatibility method: external description using existing evidence

The contract is therefore additive architecture evidence, not a migration mandate.

## 16. Mutation-boundary audit

Generic validation, envelope processing, capability declaration, and adapter description grant no
production authority and invoke no executor. Generic writeback, repair, source mutation, geometry
mutation, portrayal mutation, activation, and authorization bypass are all schema-forbidden.
Existing authorized domain execution paths remain authoritative.

## 17. Machine-readable artifacts

1. `schemas/generic-lifecycle-envelope-v1.0.schema.json`
2. `schemas/generic-domain-adapter-capability-v1.0.schema.json`
3. `schemas/generic-contract-interface-closure-v1.0.schema.json`
4. `data/specifications/nma-gen-01-generic-contract-interface-closure-v1.0.json`

All schemas use JSON Schema Draft 2020-12 and are closed except the deliberately opaque interior of
`domain_payload`. The GEN-01 closure record identity is computed by excluding `closure_sha256` and
hashing the remainder with canonical Core identity:

`03b80441bbf317ac2e2b6cd92c3a86309c4cc7465109a3d34b6d24636491c35d`

## 18. Focused GEN-01 tests

Focused tests cover schema meta-validation, valid instances, missing/extra fields, version drift,
identity dependency, no fallback, authorization linkage, three representative domain capability
profiles, capability honesty, domain ownership, evidence paths, mutation safety, deterministic
hashes, frozen blob equality, private-archive hygiene, invariant coverage, and exact change scope.

Result: **15 passed**. Ruff lint and format checks for the focused module also pass.

## 19. GEN-00 preservation

- expected and required focused predecessor result: `11 passed`
- four GEN-00 artifacts modified: `0`
- GEN-00 audit self-hash: exact

Result: **11 passed** in a clean detached checkout of exact GEN-00. On the GEN-01 descendant
worktree, ten substantive GEN-00 tests pass and its historical exact-four-file scope assertion
rejects the six authorized GEN-01 additions as expected. Independent blob and self-hash checks in
GEN-01 prove that no GEN-00 artifact changed.

## 20. Regression verification

Canonical focused coverage is run for Core, School Hero, ROAD, BUILD contract/policy, and public
BUILD-FINAL integrity. Historical exact-diff assertions that intentionally reject descendant
stage artifacts are deselected only where the GEN-00 predecessor established the same selection;
no functional assertion is weakened.

Results:

- Core identity/profile, ROAD and School Core adoption, and School authorization: **46 passed**;
- ROAD-01 resolution, ROAD-02 portrayal decision, and ROAD-03 authorization: **104 passed**;
- BUILD production contract and human policy: **57 passed**, with the same two predecessor-stage
  dirty/diff assertions deselected;
- public/non-private BUILD-FINAL integrity: **8 passed**, with the private-archive policy replay and
  BUILD-FINAL's own-stage exact-diff assertion deselected.

There is no unexplained regression.

## 21. Static verification

The final gate includes Ruff lint, Ruff format check, JSON parsing, Draft 2020-12 metaschema
validation, schema-instance validation, deterministic identity reproduction, `git diff --check`,
and exact diff-scope inspection.

Result: **PASS** — three schemas meta-validate; the closure instance validates; canonical closure
identity reproduces exactly; all new JSON parses; Ruff lint and format pass; `git diff --check`
passes; and the observed change scope is exactly the six files listed below.

## 22. Private archive boundary

`data/datasets/112年多維度SHP成果_0502.zip` remains present only as private local input with SHA-256
`4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`. It is ignored,
untracked, and unstaged. GEN-01 did not extract it, inspect layer contents, download a replacement,
or synthesize private data.

## 23. RIVERL boundary

RIVERL remains reserved for a later separately authorized proof. GEN-01 creates no river fixture,
semantic rule, geometry rule, portrayal, plan, executor, private-layer inspection, or preparatory
production change. A later proof may consume these closed contracts using tracked evidence.

## 24. Exact changed-file list

1. `GEN-01-Completion-Report.md`
2. `data/specifications/nma-gen-01-generic-contract-interface-closure-v1.0.json`
3. `schemas/generic-contract-interface-closure-v1.0.schema.json`
4. `schemas/generic-domain-adapter-capability-v1.0.schema.json`
5. `schemas/generic-lifecycle-envelope-v1.0.schema.json`
6. `tests/test_generic_contract_interface_closure_gen01.py`

Production source changes: `0`. Frozen implementation changes: `0`. Existing GEN-00 artifact
changes: `0`.

## 25. Closure

GEN-01 establishes a bounded contract/interface closure only. It does not prove a new feature
domain, authorize RIVERL, or create a universal feature framework. The next proof must conform to
the same canonical identity, capability honesty, domain ownership, authorization, lineage,
versioning, frozen compatibility, and mutation-safety invariants without widening this contract
through speculative domain knowledge.

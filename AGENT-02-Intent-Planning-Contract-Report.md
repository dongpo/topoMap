# AGENT-02 — Intent / Planning Contract Consolidation Report

Report date: 2026-08-19 (Asia/Taipei)

## 1. Verdict

**PASS — ONE CLOSED PROPOSAL-ONLY CONTRACT ESTABLISHED**

AGENT-02 establishes `nma.intent-planning/1.0` as the single shared intent/planning contract.
Its complete route vocabulary is:

1. `present_evidence`;
2. `propose_portrayal_preview`;
3. `abstain`.

The contract is versioned, closed, deterministic, and structurally proposal-only. It cannot carry
authorization, execution, mutation, filesystem, endpoint, command, tool, approval-consumption,
ROAD-substitution, or School-Hero-substitution state.

The deployed `nma-public-evidence-runtime/v0.2`, its Pages builder, its dependency manifest, and its
public behavior remain byte-identical to the accepted AGENT-01 baseline. Core, ROAD, and School
Hero frozen files and semantics also remain exact.

## 2. Baseline and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap` | PASS |
| Required starting SHA | `15881646dd47062f5a15e248380dcb583da9bb8b` | PASS |
| Parent AGENT-00 | `113cab95f2d898feb8a58b41bbc88e1590b79cc3` | PASS |
| CORE-FINAL | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Required branch | `agent/agent-02-intent-planning-contract` | PASS |
| Starting worktree | clean | PASS |
| Validated implementation commit | `a0152008ede05b68ca069454902c302908a8960d` | PASS |

The branch was created directly from the accepted AGENT-01 SHA. Work did not start from `main` or
an earlier Agent branch head.

## 3. Exact changed-file list

The completed AGENT-02 content changes exactly these five files relative to AGENT-01:

| File | Scope reason |
|---|---|
| `agent_contracts/__init__.py` | Declares the repository-level contract package outside the frozen installed v0.2 production package. |
| `agent_contracts/intent_planning.py` | Owns the closed vocabulary, deterministic canonical planner, strict validator, production adapter, retained-demo adapter, and v0.5 disposition registry. |
| `schemas/intent-planning-v1.0.schema.json` | Publishes the single Draft 2020-12 closed schema and route invariants. |
| `tests/test_intent_planning_contract_agent02.py` | Supplies executable production parity, fail-closed, adapter, schema, dependency, and frozen-boundary evidence. |
| `AGENT-02-Intent-Planning-Contract-Report.md` | Records the decision, proof, validation, and handoff evidence. |

No existing production, Core, ROAD, School Hero, server, browser, demo, data, dependency, or freeze
file was modified. The implementation is deliberately outside `src/nma`: the frozen Core residual
audit treats the installed package inventory as immutable, and AGENT-02 does not widen that package.

## 4. Contract identity and closed vocabulary

**Contract identity:** `nma.intent-planning/1.0`.

The exact output fields are:

| Field | Closed values / constraint |
|---|---|
| `schema` | constant `nma.intent-planning/1.0` |
| `boundary` | `canonical-production` or `retained-demo` |
| `route_kind` | `present_evidence`, `propose_portrayal_preview`, or `abstain` |
| `disposition` | `proposal` or `abstention` |
| `feature_code` | seven digits or `null` |
| `display_intent` | `evidence_panel`, `portrayal_preview`, or `none` |
| `evidence_intent` | `required` or `none` |
| `reason_code` | six enumerated, non-free-form reason codes |

The JSON Schema has `additionalProperties: false`. The dependency-free runtime validator requires
the exact same field set, version, vocabulary, feature-code pattern, and cross-field combinations.
Unknown versions, route kinds, fields, display intents, evidence intents, reasons, malformed feature
codes, and inconsistent combinations raise `IntentPlanningError`.

## 5. Production subset

The `canonical-production` subset matches only the bounded behavior already owned by
`nma-public-evidence-runtime/v0.2`:

| Contract route | Existing bounded production meaning |
|---|---|
| `present_evidence` | Propose display of reviewed portrayal evidence for one feature in the public graph. |
| `propose_portrayal_preview` | Propose a derived, client-visible portrayal preview; the official baseline remains immutable. |
| `abstain` | Produce no display/evidence proposal for unsupported, unsafe, missing-context, or ambiguous input. |

The public browser retains its existing route representation and state gates unchanged. The
production adapter projects only evidence and derived-preview proposals into the shared contract.
Its legacy approval, discard, finish, layer-confirmation, and reset route names are treated as
downstream state transitions and project to `abstain`; they do not enter the planning contract.

The reviewed production feature vocabulary is finite and executable tests prove exact equality to
the `FeatureType` codes in `data/knowledge/portrayal-graph.json`. Generic `school` requests are
ambiguous across reviewed school types and therefore abstain.

## 6. Proposal-only and forbidden-field proof

The contract contains no free-form reply, request, operation, parameter, command, target path, URL,
endpoint, tool, authorization, approval, execution, mutation, receipt, or durable state field.

Structural invariants are:

```text
present_evidence
  -> proposal + evidence_panel + evidence required + one feature code

propose_portrayal_preview
  -> proposal + portrayal_preview + evidence required + one feature code

abstain
  -> abstention + no display + no evidence + null feature code
```

The schema and manual validator reject any added field, including `authorization_id`, and reject
route values such as `execute_mutation`, display values such as `write_file`, or path-shaped feature
values. Tests also audit every contract field name and serialized output for forbidden authority or
execution vocabulary.

Accordingly, a planning result can describe only the next bounded evidence/display proposal. It
cannot confer authority or carry an executable request. The architectural chain remains:

```text
request
  -> reasoning/planning
  -> proposal
  -> authorization
  -> execution
  -> verification/provenance
```

## 7. Canonical deterministic planner ownership

`agent_contracts.intent_planning.plan_request()` is the canonical deterministic implementation for
the consolidated contract. It:

- normalizes case and whitespace deterministically;
- uses one finite reviewed feature vocabulary;
- accepts an optional bounded active-feature context;
- proposes evidence display or a derived portrayal preview only;
- abstains on unsafe, unsupported, missing-context, conflicting, or multi-feature input;
- rejects invalid active context and overlong/empty input;
- validates every output before returning it.

The module imports only Python standard-library facilities. It adds no installed or public runtime
dependency and has no model, network, database, filesystem-write, or domain-executor call.

## 8. Parity and fail-closed test matrix

| Evidence | Covered behavior | Result |
|---|---|---|
| Schema/meta-schema | Draft 2020-12 validity, exact version, exact fields, closed routes | PASS |
| Supported evidence intent | Primary school evidence query -> `present_evidence` | PASS |
| Supported preview intent | Active reviewed feature + color change -> `propose_portrayal_preview` | PASS |
| Unsupported input | Official deletion, shell, unrelated, deployment language -> `abstain` | PASS |
| Ambiguous input | Generic school, multiple feature codes, mixed inspect/change -> `abstain` | PASS |
| Missing context | Featureless evidence/edit request -> `abstain` | PASS |
| Determinism | Case/whitespace equivalents and repeated calls are identical | PASS |
| Version enforcement | Unknown contract version rejected | PASS |
| Route enforcement | Unknown route rejected | PASS |
| Field enforcement | Unknown field and invalid combination rejected | PASS |
| Proposal-only | Forbidden authorization/execution/mutation field audit | PASS |
| Production feature parity | Contract vocabulary equals public graph `FeatureType` codes | PASS |
| Public runtime parity | Byte-identical browser routes project to production evidence/preview/abstention | PASS |
| V04/V031/V032 parity | Exact retained vocabularies project through one shared adapter | PASS |
| State-transition isolation | Approve/discard/finish/layer/reset routes project to `abstain` | PASS |
| Dependency boundary | Public HTML, builder, and `pyproject.toml` byte-identical | PASS |
| Historical v0.5 compatibility | Historical planner byte-identical; explicit deprecation registry | PASS |

Focused AGENT-02 result: **22 passed** (18 new contract tests plus four retained v0.5 tests).

## 9. `intent_planning_v05.plan_intent()` disposition

**Decision: B — deprecated.**

`src/nma/intent_planning_v05.py::plan_intent()` is a historical HERO-05 lineage compatibility
producer, not the shared planner. Replacement ownership is:

- contract: `nma.intent-planning/1.0`;
- implementation: `agent_contracts.intent_planning.plan_request`.

The historical file remains byte-identical at SHA-256
`327769d3a37665f699fe603b196d40468979debdce5151c917efad69071e9ae7`. This preserves frozen
HERO-05 lineage records using `nma.intent-plan/0.5` without allowing that historical payload or its
`approval_required` compatibility field into the new shared contract. New callers must use the
replacement owner. Deletion is deferred to a separately authorized retirement issue.

## 10. V04 / V031 / V032 disposition

V04 and V031 remain `deprecated`; V032 remains `demo`. They do not become production planners.
Their identical legacy route vocabularies remain unchanged and are tested against one retained-demo
adapter:

- `inspect_feature` -> `present_evidence`;
- `propose_style_revision` -> `propose_portrayal_preview`;
- `abstain` -> `abstain`;
- approval, discard, finish, layer confirmation, and reset -> `abstain` with
  `downstream_state_transition`.

No V04/V031/V032 file, builder, worker, server route, or deployment classification changed.

## 11. Production dependency comparison

| Boundary | Before AGENT-02 | After AGENT-02 | Result |
|---|---|---|---|
| `pyproject.toml` dependencies | `[]` | `[]` | exact |
| `pyproject.toml` SHA-256 | `ccf4d084…9592d34` | `ccf4d084…9592d34` | exact |
| `nmaAgentDemo.html` SHA-256 | `8b6d6310…5a470` | `8b6d6310…5a470` | exact |
| `scripts/build_public_site.py` SHA-256 | `6f9e6e75…a50c55e` | `6f9e6e75…a50c55e` | exact |
| Public builder inputs | existing v0.2 allowlist | unchanged | exact |
| Installed `src/nma` inventory | accepted frozen inventory | unchanged | exact |
| OpenAI / Neo4j / GDAL / server dependency | absent from production | absent from production | exact |

The schema and repository-level reference implementation are verification/contract artifacts. The
Pages artifact neither imports nor publishes them, so no new production dependency exists.

## 12. Core, ROAD, and School Hero integrity

No file under the frozen Core, ROAD, or School Hero boundaries differs from AGENT-01.

| Gate | Result |
|---|---|
| Exact CORE-01 through CORE-04 suite | `53 passed` |
| Frozen ROAD-01 through ROAD-05 historical suite | `199 passed` |
| School Hero / HERO-04 / HERO-05 / V032 / School intelligence suite | `42 passed` |
| Core source SHA-256 values | exact AGENT-00/01 values |
| ROAD/Hero changed-file diff | empty |
| Core provider/fallback residual audit | PASS |

Core source identities remain:

| File | SHA-256 |
|---|---|
| `src/nma/core/__init__.py` | `a3e410a77ece724eaf505ce8b9dc6694b808d4a7cc96a720500757578077a4f2` |
| `src/nma/core/feature_profile.py` | `e0de362e5f733f0f1d7d5776f830939922a6d66cc552e05186046ca0d71e09f0` |
| `src/nma/core/identity.py` | `d9c4ac0d0d385f6942c552a0b2ffc4c12b3deb0ee876d569aeadc036b1a92e78` |

Planning does not import or substitute ROAD or School Hero authorization/execution. Their exact
domain gates, identities, idempotency, execution, verification, receipt, and provenance semantics
remain authoritative and separate.

## 13. Known baseline failures

The accepted failures were run in the inclusive Agent suite, twice as an exact focused set, and in
the full repository suite. The same three node IDs and materially identical signatures appeared:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
   - same generated-versus-tracked capability catalog assertion drift;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
   - same `scripts/run_nma_agent_server.py size: expected 29586, got 133875` error;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`
   - same `data/demo/pmtiles-capability-catalog.json size differs from the candidate manifest`
     error.

AGENT-02 did not modify the guarded files, manifests, generators, or checks. These failures remain
demo/generated-artifact evidence outside the canonical production planning path. No test was
weakened, skipped, xfailed, deleted, or rewritten to hide them.

## 14. Complete validation results

| Validation | Result |
|---|---|
| Focused AGENT-02 + retained v0.5 | `22 passed` |
| Inclusive Agent/demo/runtime sweep | `128 passed, 3 known failed` |
| Exact known failures, repeat run | exactly the same 3 failed |
| Relevant schema/meta-schema set | `20 passed` |
| Exact Core suite | `53 passed` |
| Complete ROAD historical suite | `199 passed` |
| Complete School Hero suite | `42 passed` |
| Full repository suite | `495 passed, 3 known failed` (498 total) |
| Ruff static checks | PASS |
| Ruff formatting | PASS |
| `git diff --check` | PASS |

The full-suite delta from AGENT-01 is exactly 18 new passing tests: `477 passed / 3 failed` became
`495 passed / 3 failed`. No new failure was introduced.

## 15. Commit, remote equality, and worktree closure

The exact implementation validated by every suite is commit
`a0152008ede05b68ca069454902c302908a8960d`.

The report-containing commit cannot embed its own Git object ID: the object ID hashes this report,
so putting that ID into the report would change the ID recursively. The exact final branch SHA is
therefore recorded in the GEO-133 completion comment and final handoff after the report commit is
created. Completion requires and performs these checks against that exact SHA:

```text
git rev-parse HEAD
git rev-parse @{upstream}
git ls-remote origin refs/heads/agent/agent-02-intent-planning-contract
git status --short --branch
```

Acceptance state at handoff: local HEAD, upstream tracking ref, and remote branch are equal; final
worktree is clean. No PR is created.

## 16. Recommendation

The next bounded Agent issue should be **AGENT-03 — Semantic / Evidence Ownership Contract**, and
only after separate authorization. It should define read-only semantic/evidence ownership and
parity across the small public portrayal graph and retained experimental retrieval adapters. It
must not add authorization, execution, deployment, memory, vector/embedding changes, Neo4j
promotion, or ROAD/School Hero public integration unless those are separately scoped and accepted.

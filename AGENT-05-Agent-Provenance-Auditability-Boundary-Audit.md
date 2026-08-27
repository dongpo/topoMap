# AGENT-05 — Agent Provenance & Auditability Boundary Audit

Report date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — AGENT RUN PROVENANCE IS TRACEABILITY, AUDIT, AND REPLAY METADATA ONLY**

AGENT-05 defines `nma.agent-run-record/1.0` as a closed, content-addressed record of one completed
Agent governance chain. The record links the exact request, deterministic intent plan, immutable
evidence references, proposal, proposal-quality evaluation, and accountability decision record.
It records explicit timestamps, contract/runtime versions, and deterministic replay metadata.

The run record explains what happened and why the proposal can be reproduced. It is not a bearer
token, authorization grant, execution plan, command, mutation request, ROAD authority, School Hero
authority, or proof that a domain effect occurred. Replay requires explicitly supplied immutable
artifacts and no hidden mutable state, execution privilege, or production mutation access.

The canonical production runtime remains `nma-public-evidence-runtime/v0.2`. The canonical planning
contract remains `nma.intent-planning/1.0`. Evidence remains immutable, content-addressed, and
proposal-only. Evaluation remains proposal-quality-only and accountability support only. Core,
ROAD, School Hero, production dependencies, deployment, and experimental semantic systems are
unchanged from the accepted AGENT-04 predecessor.

## 2. Baseline and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap` | PASS |
| Required starting SHA | `22b84e80f6771935e364fef580cf4c8adbe95218` | PASS |
| AGENT-03 predecessor | `5d589b9ddfe815f925de3cc2eb0c7765af27d6d3` | PASS |
| AGENT-02 predecessor | `f8499fbe33dc633f44f48a5e28fb7c12670f0f0c` | PASS |
| AGENT-01 predecessor | `15881646dd47062f5a15e248380dcb583da9bb8b` | PASS |
| AGENT-00 predecessor | `113cab95f2d898feb8a58b41bbc88e1590b79cc3` | PASS |
| CORE-FINAL predecessor | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Required branch | `agent/agent-05-provenance-auditability-boundary` | PASS |
| Starting worktree | clean | PASS |
| Validated implementation commit | `9669ae9112bbfd3e312d71578f01a0e25226937f` | PASS |

The required branch was absent locally and remotely, then created directly from the exact accepted
AGENT-04 SHA. Work did not begin from `main`, an earlier Agent SHA, or a dirty worktree.

## 3. Exact changed files

AGENT-05 changes exactly these four files relative to accepted AGENT-04:

| File | Scope reason |
|---|---|
| `agent_contracts/provenance.py` | Defines content-addressed Agent Run Records, exact chain validation, deterministic replay verification, version/timestamp linkage, and fail-closed authority separation outside the frozen installed package. |
| `schemas/agent-run-record-v1.0.schema.json` | Publishes the closed Draft 2020-12 Agent Run Record schema. |
| `tests/test_agent_provenance_auditability_agent05.py` | Verifies identity, linkage, replay, completeness, authority rejection, schema closure, dependency isolation, and protected production hashes. |
| `AGENT-05-Agent-Provenance-Auditability-Boundary-Audit.md` | Records the architecture decision, ownership audit, validation evidence, frozen integrity, and closure protocol. |

No existing `src/nma`, dependency, public runtime, public builder, data, graph, Core, ROAD, School
Hero, demo, freeze, workflow, deployment, or predecessor Agent contract file changes.

## 4. Agent Run Record boundary

### 4.1 Contract decision

`nma.agent-run-record/1.0` is a finalized audit envelope for a completed and verified governance
chain. Incomplete or unresolved chains are not valid completed run records. Lower-stage records may
explain where a failed-closed attempt stopped, but they cannot set the run-record completion claim.

The complete record field set is:

| Field | Bounded meaning |
|---|---|
| `schema` | Constant `nma.agent-run-record/1.0` contract version. |
| `run_id` | `agent-run:sha256:<digest>` identity over the complete canonical record body. |
| `request_identity` | Content address of the exact request text. |
| `intent_reference` | Exact `nma.intent-planning/1.0` contract and deterministic plan identity. |
| `evidence_references` | Non-empty, unique, proposal-purpose references resolved through the immutable evidence registry. |
| `proposal_identity` | Content address of the reconstructed closed evidence-backed proposal. |
| `evaluation_reference` | Content address of the validated proposal-quality evaluation. |
| `decision_record_reference` | Content address of the validated accountability-only decision record. |
| `timestamps` | Explicit UTC-second `started_at` and `completed_at`; completion cannot precede start. |
| `versions` | Exact runtime, intent, evidence, proposal, evaluation, decision, and run-record versions. |
| `reproducibility` | Constant deterministic-reference replay method, canonicalization, and explicit declarations that hidden state and execution access are not required. |
| `completion` | Constant `complete` plus `verified`; any partial, missing, or altered completion claim fails closed. |
| `boundary` | Constant `traceability-audit-replay-only`. |
| `provenance` | Bounded recorder identity and UTC record timestamp; recording cannot precede completion. |

The content identity covers timestamps, version links, reproducibility metadata, completion state,
boundary, recorder, and every chain reference. A changed field cannot retain the previous run ID.
Every nested object and the top-level object use exact field sets in both Python validation and JSON
Schema. Added control, authorization, permission, command, mutation, tool, ROAD, or School Hero
fields are rejected.

### 4.2 Completion semantics

`complete` means only that the recorded Agent governance chain is present and internally verified.
It does not mean that a reviewer accepted the proposal, that authorization exists, that execution
occurred, or that ROAD/School Hero verification passed. Review status remains owned by the decision
record; authorization, execution, and domain verification remain outside the run record.

## 5. Replay and audit model decision

The replay verifier receives all replay inputs explicitly:

```text
exact request text
  -> supplied intent-plan snapshot
  -> immutable evidence registry
  -> supplied proposal snapshot
  -> supplied evaluation object
  -> supplied decision-record object
  -> supplied Agent Run Record
```

Replay performs these fail-closed checks in order:

1. validate the run-record shape, version, content address, timestamps, completion, and boundary;
2. resolve every evidence identity in the explicit immutable registry with no fallback;
3. validate evaluation and decision identities and their exact request/intent/evidence/proposal linkages;
4. hash the exact supplied request and require equality with `request_identity`;
5. rerun `nma.intent-planning/1.0` and require byte-equivalent canonical plan output;
6. rebuild the proposal from the validated plan and resolved evidence references;
7. require the rebuilt proposal and content identity to equal the supplied and recorded proposal;
8. return a deterministic audit-verification trace of the request-to-decision identity sequence.

Equivalent explicit inputs produce the identical run record and replay trace. A different request,
plan, evidence object, proposal, evaluation, decision record, timestamp, version, or recorder either
produces a different identity or is rejected. Replay never calls a production endpoint, invokes a
tool, writes a domain object, consumes authorization, executes ROAD/School Hero behavior, or reads
unrecorded conversation/session state.

The deterministic audit sequence is:

```text
request:sha256
  -> intent:sha256
  -> evidence:sha256[]
  -> proposal:sha256
  -> evaluation:sha256
  -> decision-record:sha256
  -> agent-run:sha256
```

Every prefix names an immutable record class, never a capability.

## 6. Provenance ownership matrix

| Component | Provenance owner | What it records | What it must not impersonate |
|---|---|---|---|
| Agent runtime | Run lifecycle metadata | Run identity and explicit start/completion timing when a future authorized adapter emits the record. AGENT-05 only defines the verification contract; it does not integrate runtime emission. | Planner, evidence producer, evaluator, reviewer, authorizer, executor, domain verifier. |
| `nma.intent-planning/1.0` | Intent planning contract | Deterministic plan identity for the exact request. | Evidence, proposal acceptance, review, authorization, execution. |
| `nma.agent-evidence/1.0` | Evidence object | Immutable artifact/content provenance, citation, review metadata, and reproduction inputs. | Plan ownership, proposal acceptance, authorization, execution. |
| `nma.agent-evaluation/1.0` | Evaluation layer | Proposal-quality dimensions, result, evaluator, method, and evaluation time. | Human/domain review, authorization, execution, post-effect truth. |
| `nma.agent-decision-record/1.0` | Decision-record layer | Governance accountability: observed review state and exact request-to-evaluation linkage. | Authorization grant, approval consumption, execution command, domain verification. |
| `nma.agent-run-record/1.0` | Audit/provenance layer | Cross-stage identities, lifecycle timestamps, version linkage, deterministic replay metadata, and chain completion. | Any upstream record owner or downstream authority/executor/verifier. |
| ROAD verification | Frozen ROAD domain | ROAD post-execution observation, QA, receipt, rollback, and provenance under ROAD contracts. | Generic Agent evaluation, Agent run ownership, retroactive authorization. |
| School Hero verification | Frozen School Hero domain | School post-execution observation, QA, receipt, rollback, and provenance under School contracts. | Generic Agent evaluation, Agent run ownership, retroactive authorization. |

GraphRAG, vector retrieval, Neo4j projection, large knowledge graph, and entity resolution remain
experimental and non-authoritative. They are not imported by the provenance contract and gain no
planning, evidence, evaluation, audit, review, authorization, execution, or verification ownership.

## 7. Provenance versus authorization

Provenance answers:

> Why did this Agent produce this proposal, and which immutable records support that account?

Authorization answers:

> Who is permitted to perform a particular domain action under the owning domain contract?

Those questions remain separate. AGENT-05 rejects both prohibited implications:

```text
provenance -> authorization
evaluation score/result -> execution permission
```

A valid run ID proves only integrity of the traceability envelope. A verified replay proves only
that the recorded proposal chain reconstructs from explicit immutable inputs. An accepted review
inside the linked decision record remains an accountability observation and cannot become a ROAD
or School Hero authorization. No run field can grant, carry, consume, or infer execution authority.

## 8. Governance-chain verification

The required governance chain remains exact:

```text
request
  -> intent planning
  -> evidence reference
  -> proposal
  -> evaluation
  -> decision record
  -> audit/provenance record
```

AGENT-05 adds only the final audit/provenance link. It does not insert authorization or execution
into this chain and does not remove the separately owned human/domain review, authorization,
execution, or post-execution verification boundaries established by AGENT-04.

## 9. Boundary-test evidence

| Required behavior | Executable proof | Result |
|---|---|---|
| Missing run identity fails closed | Deleting `run_id` violates the exact Python field set and the JSON Schema required set. | PASS |
| Invalid provenance references rejected | Forged request/proposal/evaluation/decision links are rejected; unresolved evidence fails with no fallback. | PASS |
| Incomplete record cannot claim completion | `incomplete`, `partial`, missing, or expanded completion metadata violates the constant closed completion contract. | PASS |
| Replay resolves deterministically | Identical explicit inputs reproduce the identical run ID and ordered audit trace. | PASS |
| Request/plan replay is exact | A different request or non-deterministic supplied plan fails before proposal reconstruction. | PASS |
| Proposal replay is exact | The proposal is rebuilt only from the deterministic plan and resolved immutable evidence, then compared by canonical value and content identity. | PASS |
| Provenance cannot carry authority | Authorization grants, ROAD/Hero authority, commands, mutations, permissions, and tool fields fail Python and schema validation. | PASS |
| Timestamps/version linkage exact | Non-monotonic UTC timestamps and runtime/contract drift are rejected. | PASS |
| No hidden state or privileges | Replay metadata constants require `hidden_state=not-required` and `execution_access=not-required`. | PASS |
| Production dependency boundary | Protected hashes are exact, `dependencies=[]`, public builder excludes AGENT-05, and provenance imports no domain/experimental stack. | PASS |
| Schema closed and meta-valid | Draft 2020-12 meta-schema validation passes and every object boundary sets `additionalProperties=false`. | PASS |

## 10. Complete validation results

Environment: Python 3.11.9, pytest 8.3.3, jsonschema 4.23.0.

| Validation | Result |
|---|---|
| Focused AGENT-05 provenance/auditability boundary | `24 passed` |
| Canonical AGENT-02 + AGENT-03 + AGENT-04 + AGENT-05 contracts | `85 passed` |
| Agent/demo/runtime focused sweep | `188 passed, 3 known failed` (191 total) |
| Exact known failure set | Same three node IDs and materially identical signatures | PASS |
| New run-record schema and meta-schema checks | Included in `24 passed`; PASS |
| Exact Core suite | `53 passed` |
| Complete ROAD historical suite | `199 passed` |
| Complete School Hero suite | `42 passed` |
| Full repository suite | `562 passed, 3 known failed` (565 total) |
| Ruff static checks on AGENT-05 Python scope | PASS |
| Ruff formatting on AGENT-05 Python scope | PASS |
| JSON syntax and schema checks | PASS |
| `git diff --check` | PASS |

The full-suite delta from accepted AGENT-04 is exactly 24 new passing tests: `538 passed / 3 failed`
became `562 passed / 3 failed`. No test was weakened, skipped, xfailed, deleted, or changed to hide a
failure.

### 10.1 Accepted baseline failures

The same three predecessor failures remain materially identical and outside canonical production:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
   - same generated-versus-tracked PMTiles capability catalog assertion drift;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
   - same `scripts/run_nma_agent_server.py size: expected 29586, got 133875` error;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`
   - same `data/demo/pmtiles-capability-catalog.json size differs from the candidate manifest`
     error.

AGENT-05 modifies none of those tests, generators, catalogs, server files, demo manifests, freeze
records, or Pages candidates. None becomes provenance relevant. No repair was attempted.

## 11. Frozen integrity verification

The path-limited diff from accepted AGENT-04 is empty for `src/nma`, Core, ROAD, School Hero,
production dependencies, public runtime, public builder, protected knowledge data, and all frozen
domain schemas/specifications.

| Frozen boundary | Evidence | Result |
|---|---|---|
| Core | Exact five-file acceptance suite: `53 passed` | PASS |
| ROAD | Complete ROAD-01 through ROAD-05 historical suite: `199 passed` | PASS |
| School Hero | Complete HERO-04/HERO-05/V032/intelligence suite: `42 passed` | PASS |
| Frozen boundary diff | Empty relative to `22b84e80…` | PASS |
| Core final tag target | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| ROAD final tag target | `325c70d5335f57c43a8af85822db25032aa225c3` | PASS |
| School Hero frozen remote ref | `56f99eb9ae63272a68accac3041fb10eacefb986` | PASS |

Canonical Core source SHA-256 values remain:

| File | SHA-256 |
|---|---|
| `src/nma/core/__init__.py` | `a3e410a77ece724eaf505ce8b9dc6694b808d4a7cc96a720500757578077a4f2` |
| `src/nma/core/feature_profile.py` | `e0de362e5f733f0f1d7d5776f830939922a6d66cc552e05186046ca0d71e09f0` |
| `src/nma/core/identity.py` | `d9c4ac0d0d385f6942c552a0b2ffc4c12b3deb0ee876d569aeadc036b1a92e78` |

Protected production hashes remain:

| File | SHA-256 |
|---|---|
| `nmaAgentDemo.html` | `8b6d6310d3ac6b45e71b73102de023869b0f56422dfbf1c74d81a6650ba5a470` |
| `scripts/build_public_site.py` | `6f9e6e75281f50eb4d6297d9fea7018e165cfdcb0d6ac56873f9940e0a50c55e` |
| `data/knowledge/portrayal-graph.json` | `0f90dc365805aaac07ab5aaf61323006bcea1ba8a078470c6872ad63a7eeacca` |
| `pyproject.toml` | `ccf4d084262633d8806b48645a56ab56c2f6b58566cadcb6fc3c24e6a9592d34` |

## 12. Commit, synchronization, and worktree closure

The exact implementation validated by every suite is commit
`9669ae9112bbfd3e312d71578f01a0e25226937f`.

The report-containing commit cannot embed its own Git object ID because that ID hashes this report;
embedding it would change the ID recursively. Following the accepted AGENT-02/03/04 pattern, the
exact final branch SHA and local/upstream/remote equality are recorded after the report commit and
push in the GEO-136 final handoff.

Closure requires these exact checks:

```text
git rev-parse HEAD
git rev-parse @{upstream}
git ls-remote origin refs/heads/agent/agent-05-provenance-auditability-boundary
git status --short --branch
```

PASS requires local HEAD, the upstream tracking ref, and the remote branch to be equal, with a clean
final worktree. No pull request is created.

## 13. Recommendation for the next bounded Agent issue

GEO-136 should close **PASS** only after the report commit, push, SHA equality, and final-cleanliness
verification.

The next separately authorized Agent issue should address **portable audit-bundle fixtures and an
independent read-only replay verifier interface**. It may serialize representative immutable
request/plan/evidence/proposal/evaluation/decision/run fixtures and prove replay parity across a
bounded verifier. It must not implement Agent memory, conversation history, generic authorization,
execution integration, production mutation access, ROAD/School Hero integration, semantic-platform
unification, deployment redesign, or changes to Core/ROAD/School Hero semantics.

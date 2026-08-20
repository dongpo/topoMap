# AGENT-04 — Agent Evaluation & Governance Boundary Audit

Report date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — AGENT EVALUATION IS PROPOSAL-QUALITY GOVERNANCE, NEVER AUTHORIZATION**

AGENT-04 defines `nma.agent-evaluation/1.0` as a deterministic, content-addressed proposal-quality
record and `nma.agent-decision-record/1.0` as a content-addressed accountability record. Both are
closed contracts outside the frozen production package. Neither contract contains an authorization
grant, execution command, mutation permission, tool call, ROAD authorization ID, School Hero
authorization ID, or approval-consumption field.

Every satisfactory evaluation explicitly requires human/domain review. A satisfactory result means
only that the proposal passed the bounded quality dimensions. A recorded reviewer acceptance means
only that an externally owned review decision was observed. Neither state grants, consumes, or
substitutes for domain authorization.

The canonical production runtime remains `nma-public-evidence-runtime/v0.2`. The canonical planning
contract remains `nma.intent-planning/1.0`. The evidence boundary remains immutable,
content-addressed, and proposal-only. Core identity, ROAD semantics, School Hero semantics, the
public runtime, and production dependencies are unchanged from the accepted AGENT-03 predecessor.

## 2. Baseline and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap` | PASS |
| Required starting SHA | `5d589b9ddfe815f925de3cc2eb0c7765af27d6d3` | PASS |
| AGENT-02 predecessor | `f8499fbe33dc633f44f48a5e28fb7c12670f0f0c` | PASS |
| AGENT-01 predecessor | `15881646dd47062f5a15e248380dcb583da9bb8b` | PASS |
| AGENT-00 predecessor | `113cab95f2d898feb8a58b41bbc88e1590b79cc3` | PASS |
| CORE-FINAL predecessor | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Required branch | `agent/agent-04-evaluation-governance-boundary` | PASS |
| Starting worktree | clean | PASS |
| Validated implementation commit | `aa08721039ffa561e251489b11a191fd17d70d67` | PASS |

The branch was created directly from the exact accepted AGENT-03 SHA. Work did not begin from
`main`, an earlier Agent SHA, or a dirty worktree.

## 3. Exact changed files

AGENT-04 changes exactly these five files relative to AGENT-03:

| File | Scope reason |
|---|---|
| `agent_contracts/governance.py` | Defines deterministic proposal evaluation, content-addressed evaluation identity, bounded review recording, decision-record integrity, and fail-closed validation outside the frozen installed package. |
| `schemas/agent-evaluation-v1.0.schema.json` | Publishes the closed Draft 2020-12 proposal-quality evaluation schema. |
| `schemas/agent-decision-record-v1.0.schema.json` | Publishes the closed Draft 2020-12 accountability-only decision-record schema. |
| `tests/test_agent_evaluation_governance_agent04.py` | Verifies evaluation dimensions, invalid/missing evidence behavior, provenance validation, unsupported requests, authority-field rejection, record linkage, schema closure, dependency isolation, and production hashes. |
| `AGENT-04-Agent-Evaluation-Governance-Boundary-Audit.md` | Records architecture decisions, governance ownership, validation results, frozen integrity, and closure evidence. |

No existing `src/nma`, dependency, public page, public builder, data, graph, Core, ROAD, School Hero,
demo, freeze, workflow, or deployment file changes.

## 4. Agent evaluation model decision

### 4.1 Ownership and result semantics

The repository-level `agent_contracts.governance.evaluate_proposal` contract owns deterministic
Agent proposal-quality evaluation. It does not own production request ingress, evidence retrieval,
human review, domain authorization, execution, or domain verification.

The model deliberately uses categorical per-dimension results instead of a scalar score. This
avoids implying that a numeric threshold can become a capability threshold. A record result is:

- `satisfactory` only when every dimension is `pass`; or
- `rejected` when one or more dimensions are `fail`.

The contract creator returns a satisfactory record only after all inputs validate. Invalid inputs,
missing evidence, unsupported requests, unreviewed evidence, provenance defects, non-deterministic
proposals, or contract drift raise and fail closed rather than producing partial success.

Every valid record contains the constants:

```text
review_requirement = human-domain-review-required
boundary = proposal-quality-only
```

Changing either value invalidates the record. Therefore even the strongest possible evaluation
result cannot authorize execution, consume authorization, bypass review, or replace ROAD or School
Hero verification.

### 4.2 Evaluation dimensions

| Dimension | Bounded evaluation decision |
|---|---|
| Intent correctness | The supplied plan must equal the deterministic `nma.intent-planning/1.0` result for the exact request. |
| Evidence completeness | The proposal must contain a non-empty, unique list of proposal-purpose references and every identity must resolve in the supplied immutable registry. |
| Evidence provenance validity | Every resolved object must pass its content-addressed AGENT-03 envelope validation; malformed or forged provenance is rejected. |
| Proposal determinism | Rebuilding the proposal from the exact validated plan and evidence references must reproduce the supplied proposal. |
| Unsupported request handling | An abstention or unsupported request cannot be promoted into a proposal evaluation. |
| Fail-closed behavior | Any invalid field, missing reference, linkage mismatch, or unknown version raises; there is no fallback, repair, substitution, or partial pass. |
| Reproducibility | Evidence reproduction metadata and hashes must validate, and proposal reconstruction must be exact. |
| Contract compliance | Intent, evidence, proposal, evaluation, and nested field sets must use their exact closed versions and shapes. |

Evidence quality affects proposal evaluation without becoming authority. `unreviewed` evidence
cannot receive a satisfactory evaluation. `reviewed` or `validated` evidence may pass the quality
gate, but those statuses remain descriptive provenance and still require human/domain review and a
separate authorization owner.

## 5. Agent Decision Record model

`nma.agent-decision-record/1.0` preserves the accountability chain without becoming a bearer token.
Its complete field set is:

| Field | Meaning |
|---|---|
| `schema` | Constant decision-record contract version. |
| `decision_record_id` | SHA-256 identity of the complete versioned record body. |
| `request_identity` | Content address of the exact bounded request. |
| `intent_reference` | Canonical planning contract version and deterministic intent-plan identity. |
| `evidence_references` | Exact non-empty proposal-purpose evidence identities preserved from proposal and evaluation. |
| `proposal_identity` | Content address of the closed evidence-backed proposal. |
| `evaluation_reference` | Content address of the supplied validated evaluation record. |
| `review` | `pending`, `accepted`, or `rejected`, plus reviewer and an external review-decision identity where applicable. |
| `boundary` | Constant `accountability-only`. |
| `provenance` | Bounded recorder identity and recorded timestamp. |

Pending review cannot name a reviewer or decision. Completed review requires a reviewer and a
content-addressed `review-decision:sha256:<digest>` reference. That reference identifies an
externally owned review observation only; its namespace is deliberately distinct from every ROAD
or School Hero authorization namespace.

Creation and validation require request, intent, evidence, proposal, and evaluation linkages to be
exactly equal. The record identity is recomputed from the entire body, so changed review status,
reviewer, provenance, evidence, proposal, or evaluation linkage cannot retain the old identity.

The schema and validator reject added execution authority, authorization grants, ROAD or School
Hero authorization IDs, mutation permissions, tool commands, shell commands, API operations,
approval consumption, or arbitrary control fields. Decision records preserve accountability. They
do not grant authority.

## 6. Governance ownership matrix

| Component | Classification | Governance role and prohibited role |
|---|---|---|
| `nma-public-evidence-runtime/v0.2` | **Canonical production** | Owns the deployed read-only public evidence presentation runtime. It is not the planner, evaluator, reviewer, authorizer, executor, or verifier. |
| `nma.intent-planning/1.0` | **Canonical planning contract** | Owns deterministic proposal-only intent classification. Its output is evaluated but cannot evaluate itself or grant authority. |
| `nma.agent-evidence/1.0` Evidence Objects | **Canonical evidence contract** | Own immutable, content-addressed evidence identity, provenance, citation, review metadata, and reproducibility. Evidence quality informs evaluation; evidence never authorizes. |
| `nma.agent-evaluation/1.0` | **Canonical governance contract** | Owns deterministic Agent proposal-quality evaluation only. It always requires human/domain review and contains no authority. |
| `nma.agent-decision-record/1.0` | **Canonical accountability contract** | Preserves request-to-review provenance and integrity linkage. It is a record, not an authorization or execution instruction. |
| GraphRAG | **Experimental** | May produce candidate retrieval/evidence in its experimental family. It has no production, governance, evaluation, review, authorization, execution, or verification authority. |
| Vector retrieval | **Experimental** | Similarity ranking may suggest candidates. Rank is not truth, proposal acceptance, authorization, or verification. |
| Neo4j projection | **Experimental** | Remains a projection of the experimental graph family. Backend parity does not confer governance or evaluation ownership. |
| Large knowledge graph | **Experimental** | Remains outside canonical production evidence ownership. Its filename or graph position cannot confer governance authority. |
| Entity resolution | **Experimental** | Candidate entity selection remains non-authoritative and cannot activate rules, pass evaluation, authorize, or execute. |
| ROAD verification | **Domain** | Owns post-execution ROAD verification and provenance under frozen ROAD semantics. It is not generic Agent evaluation. |
| School Hero verification | **Domain** | Owns post-execution School Hero verification and provenance under frozen School Hero semantics. It is not generic Agent evaluation. |

No experimental component is imported by the governance contract. No experimental component
becomes a governance, evaluation, review, authorization, execution, or verification authority.

## 7. Evaluation, review, authorization, execution, and verification separation

The preserved architectural chain is:

```text
request
  -> nma.intent-planning/1.0
  -> immutable content-addressed evidence retrieval
  -> proposal-only evidence-backed proposal
  -> proposal-quality evaluation
  -> human/domain review
  -> separately owned domain authorization
  -> domain-owned execution
  -> ROAD / School Hero / domain verification and provenance
```

| Stage | Owns | Does not own |
|---|---|---|
| Agent proposal | A proposed evidence presentation or portrayal preview. | Acceptance, authorization, mutation, execution, verification. |
| Agent evaluation | Contract, determinism, evidence, provenance, reproducibility, and fail-closed proposal quality. | Human judgment, domain authorization, capability issuance, execution, post-execution truth. |
| Human/domain review | Acceptance or rejection of the proposal for the relevant review context. | Generic execution capability; a review record is not an authorization grant. |
| Authorization | Domain-specific authority issued under the separately owned domain contract. | Agent proposal scoring or evidence retrieval. |
| Execution | Authorized effects owned and constrained by the relevant domain system. | Retrospective quality evaluation or verification ownership. |
| Verification | Observation, QA, tamper detection, and provenance after execution. | Retroactive authorization or generic Agent evaluation. |

A satisfactory evaluation cannot create or consume ROAD authorization, cannot create or consume
School Hero authorization, cannot bypass a reviewer, cannot invoke a tool, and cannot become proof
that an effect occurred. Human review cannot be inferred from evaluation. Authorization cannot be
inferred from a human review status. Execution cannot be inferred from authorization. Verification
cannot be inferred from any prior stage.

## 8. Provenance and accountability model

The content-addressed chain is:

```text
request:sha256
  -> intent:sha256
  -> evidence:sha256[]
  -> proposal:sha256
  -> evaluation:sha256
  -> review-decision:sha256 (when externally completed)
  -> decision-record:sha256
```

Each prefix names an object class, not a capability. Evaluation provenance records the bounded
evaluator, timestamp, and constant deterministic validation method. Decision provenance records the
bounded recorder and timestamp. Evidence provenance remains owned by the immutable AGENT-03
Evidence Object. Exact equality checks ensure the decision record preserves the same evidence list,
intent reference, proposal identity, evaluation identity, and request identity.

The record can answer which request, plan, evidence snapshot, proposal, quality result, reviewer
observation, and recorder produced the accountability state. It cannot answer “may this execute?”;
that question belongs to a separately versioned domain authorization contract that is intentionally
absent from AGENT-04.

## 9. Boundary-test evidence

| Required behavior | Executable proof | Result |
|---|---|---|
| Invalid evaluation record fails closed | Dimension/result inconsistency fails both Python validation and JSON Schema validation. | PASS |
| Missing evidence prevents success | Empty registry cannot resolve the proposal reference; evaluation raises with no fallback. | PASS |
| Invalid provenance rejected | Forged/empty evidence producer fails immutable evidence validation before evaluation. | PASS |
| Unreviewed evidence affects quality | Unreviewed evidence is structurally valid evidence but cannot receive satisfactory evaluation. | PASS |
| Unsupported request handling | An unsupported execution request cannot reuse a supported proposal/plan and fails deterministic intent comparison. | PASS |
| Proposal authority boundary | Authorization IDs, execution commands, mutation fields, and tool commands at top-level or nested locations violate exact proposal field sets. | PASS |
| Decision authority boundary | Authorization grants, ROAD/Hero authorization IDs, commands, and mutation permissions violate exact decision-record field sets. | PASS |
| Decision-record integrity | Request, intent, evidence, proposal, and evaluation linkage must be exact; broken or missing links are rejected. | PASS |
| Human review remains separate | Every satisfactory evaluation says `human-domain-review-required`; pending and completed review states have closed invariants. | PASS |
| Evaluation identity deterministic | Identical inputs and provenance produce the identical evaluation body and SHA-256 identity. | PASS |
| Production dependency boundary | Protected hashes are exact, `dependencies=[]`, public builder excludes the new contracts, and governance imports no `nma` domain/experimental stack. | PASS |
| Schemas closed and meta-valid | Both new Draft 2020-12 schemas pass meta-schema validation and set `additionalProperties=false` at every contract object boundary. | PASS |

## 10. Complete validation results

Environment: Python 3.11.9, pytest 8.3.3, jsonschema 4.23.0.

| Validation | Result |
|---|---|
| Focused AGENT-04 evaluation/governance boundary | `25 passed` |
| Canonical AGENT-02 + AGENT-03 + AGENT-04 contracts | `61 passed` |
| Agent/demo focused sweep | `123 passed, 3 known failed` |
| Exact known failures | the same three node IDs and materially identical signatures |
| New evaluation/decision schema and meta-schema checks | included in `25 passed`; PASS |
| Exact Core suite | `53 passed` |
| Complete ROAD historical suite | `199 passed` |
| Complete School Hero suite | `42 passed` |
| Full repository suite | `538 passed, 3 known failed` (541 total) |
| Ruff static checks on AGENT-04 Python scope | PASS |
| Ruff formatting on AGENT-04 Python scope | PASS |
| JSON syntax checks | PASS |
| `git diff --check` | PASS |

The full-suite delta from accepted AGENT-03 is exactly 25 new passing tests: `513 passed / 3 failed`
became `538 passed / 3 failed`. No test was weakened, skipped, xfailed, deleted, or changed to hide a
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

AGENT-04 modifies none of those tests, generators, catalogs, server files, demo manifests, freeze
records, or Pages candidates. None becomes governance relevant. No repair was attempted.

## 11. Frozen integrity verification

The path-limited diff from accepted AGENT-03 is empty for Core, ROAD, School Hero, their schemas,
and their frozen specification artifacts.

| Frozen boundary | Evidence | Result |
|---|---|---|
| Core | Exact five-file acceptance suite: `53 passed` | PASS |
| ROAD | Exact ROAD-01 through ROAD-05 historical suite: `199 passed` | PASS |
| School Hero | Complete HERO-04/HERO-05/V032/intelligence suite: `42 passed` | PASS |
| Frozen boundary diff | Empty relative to `5d589b9d…` | PASS |
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

## 12. Commit, remote equality, and worktree closure

The exact implementation validated by every suite is commit
`aa08721039ffa561e251489b11a191fd17d70d67`.

The report-containing commit cannot embed its own Git object ID because that ID hashes this report;
embedding it would change the ID recursively. Following the accepted AGENT-02 and AGENT-03 report
pattern, the exact final branch SHA is recorded after the report commit in the GEO-135 final handoff.

Completion requires these exact checks after the report commit and push:

```text
git rev-parse HEAD
git rev-parse @{upstream}
git ls-remote origin refs/heads/agent/agent-04-evaluation-governance-boundary
git status --short --branch
```

PASS requires local HEAD, upstream tracking ref, and remote branch to be equal, with a clean final
worktree. No PR is created.

## 13. Recommendation for the next bounded Agent issue

GEO-135 should close **PASS** only after commit/push/SHA equality and final-cleanliness verification.

The next separately authorized Agent issue should address **evaluation fixture replay and reviewer
interface parity**: persist representative request/plan/evidence/proposal/evaluation/decision-record
fixtures and prove deterministic replay across a bounded adapter. It must remain proposal-quality
and accountability-only. It must not add memory, connect generic Agent evaluation to execution,
create generic authorization, change review semantics, promote GraphRAG/vector/Neo4j/KG/entity
resolution, alter deployment, or modify Core/ROAD/School Hero contracts.

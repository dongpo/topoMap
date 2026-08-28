# RQ3-DEMO-01 — Authorized Execution, Deterministic Verification & Tamper-Evident Provenance Report

## 1. Verdict

**PASS WITH FINDINGS.** The frozen RQ3 trust architecture was instantiated without changing the
canonical RQ2 proposal or any frozen mapping semantic subsystem. The canonical positive proposal
was explicitly authorized, executed through the unchanged deterministic RQ2 GIS executor,
independently verified, linked through content-addressed provenance, and accepted by the frozen
Boolean audit function. Cases B–K were rejected as specified, and Case L produced the permitted
exact replay with the same semantic and byte-level result identity.

The bounded findings do not invalidate the experiment: the authorization uses research identity
and a deterministic research clock rather than production PKI/trusted time; the accepted result is
an isolated, non-authoritative symbolic artifact; ProductLayer and three physical portrayal gates
remain unresolved; and the broad repository suite retains historical freeze/scope failures already
present at the exact predecessor.

## 2. Repository identity

| Evidence | Value |
|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` (`origin`) |
| Required predecessor | `2c3c25937615cfe01e989bdeb64b25ad6c27251f` |
| Predecessor branch | `rq3/rq3-demo-00-trust-architecture-acceptance` |
| Predecessor local/upstream/remote | exact equality at `2c3c25937615cfe01e989bdeb64b25ad6c27251f` |
| Task branch | `rq3/rq3-demo-01-authorized-execution-verification-provenance` |
| Branch point | exact required predecessor; no intervening commit |
| Initial task worktree | clean |
| Final SHA | verified after final commit and reported in the task completion response |
| Remote SHA | verified after push and reported in the task completion response |
| Final local/upstream/remote equality | verified after push and reported in the task completion response |
| Final worktree | verified after push and reported in the task completion response |

The primary iCloud checkout was on unrelated branch `app/app-standalone-file-layout` at
`ac350c8fcef6e58d820ee6da456b1d1f0ef012f6` and contained unrelated untracked paths. It was not
modified or repaired. The already-registered clean RQ3-DEMO-00 worktree was validated, and this
task received a separate clean worktree and branch from the exact predecessor.

A commit cannot contain its own final SHA without changing that SHA. Final Git identity is
therefore verified externally after commit/push and recorded in the completion response, following
the predecessor task's established non-self-referential reporting practice.

## 3. Research question and hypothesis

RQ3 asks:

> Can authorization, deterministic verification and provenance make probabilistic AI agents
> suitable for authoritative mapping workflows?

H3 evaluates whether a probabilistic mapping proposal can participate safely when the exact action
is explicitly authorized, authorization is bound to the immutable proposal, execution is limited
to deterministic allowlisted tools and scope, postconditions are independently verified,
provenance connects every trust artifact, and inconsistency fails closed.

This experiment does not claim that probabilistic AI is intrinsically or generally trustworthy.

## 4. Canonical proposal identity

| Field | Frozen/observed value | Result |
|---|---|---|
| Path | `artifacts/rq2/rq2-demo-01-canonical-proposal.json` | loaded directly; not recreated |
| Proposal ID | `rq2-proposal:knowledge-constrained:e635111c3be29423faf923b7` | PASS |
| Proposal SHA-256 | `116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1` | PASS |
| Proposal byte SHA-256 | `8ad05eea5111a0c535be275effa6b8a6c3dce7b74c7149bf42811a1866aa4829` | PASS |
| Plan identity | `2bff5483934eb90a3bce3cdb9ab45e800b7f4c2deffca82e8a07fc31bec40e30` | PASS |

The proposal hash was independently recomputed with the unchanged frozen RQ2 zero-substitution
basis in `nma.rq2_demo.proposal_hash` before authorization was accepted. Every RQ2
`bound_proposal_hash` declaration matched. No LLM regenerated or normalized the proposal.

## 5. Trust-chain implementation

### 5.1 Proposal validation

The RQ3 integrity gate validates the RQ2 schema, exact proposal ID, recomputed frozen hash, every
self-binding declaration, plan identity, content-addressed source input, and frozen proposal byte
identity. Any difference blocks before state or result bytes are created.

### 5.2 Authorization and binding

The unchanged RQ3-DEMO-00 authorization artifact is schema-valid and has authorization hash
`e74a36cd08d73c5188e59ed93f77b2c0651f002a7d7b98a5eccc47d47828f63d`. The gate independently
recomputes that hash and checks proposal ID/hash, decision, subject, deterministic validity time,
policy file hash, exact scope, tools/order, exact parameters, unresolved constraints, source access,
output destination, environment identity, and replay state.

### 5.3 Deterministic execution boundary

`src/nma/rq3_demo.py` is a bounded adapter around the unchanged
`nma.rq2_demo.execute_proposal`. It introduces no shell, network, arbitrary Python, or LLM path.
The RQ2 executor receives only a proposal and request that passed the full RQ3 read-only gate. The
source fixture and output root are content-bound, fresh, and disjoint. Only the isolated derived
artifact and trust-control records are written.

### 5.4 Execution record

`data/specifications/rq3-execution-record-schema-v1.0.json` closes the execution-observation gap
identified by RQ3-DEMO-00. Each record contains proposal and authorization identities, deterministic
environment identity, complete authorized tool sequence, actual calls, normalized parameter hashes,
source identities before/after, result identity/hash, executor identities, zero model calls, bounded
timestamps, and a canonical execution hash.

### 5.5 Independent verification

The verifier reads the resulting source and derived state rather than trusting executor success.
It independently checks record integrity, proposal/authorization binding, actual/authorized tools,
plan and parameter identities, source preservation, feature identity/count, classification,
geometry, portrayal attributes, unresolved ProductLayer/physical gates, non-authoritative output,
declared files, result hash, and replay stability. It emits the frozen RQ3 verification schema with
`model_calls = 0`.

### 5.6 Provenance and audit

The audit assembler independently recomputes proposal, authorization, execution, verification,
evidence-set, and result identities. The schema-valid audit record carries all six mandatory typed
links: `PROPOSAL`, `EVIDENCE`, `AUTHORIZATION`, `EXECUTION`, `VERIFICATION`, and `RESULT`. Missing or
invalid evidence cannot be reconstructed or overridden.

The exact frozen acceptance function is implemented as:

```text
proposal_integrity_pass
AND authorization_pass
AND execution_scope_pass
AND verification_pass
AND provenance_complete
```

Missing is false. Executor success alone cannot produce acceptance.

## 6. Positive canonical scenario

| Stage | Result | Evidence |
|---|---|---|
| Proposal identity | PASS | exact ID, canonical hash, byte hash, plan identity |
| Authorization | PASS | explicit `APPROVED`, schema/hash/policy/time/scope valid |
| Proposal-hash binding | PASS | authorization and execution bind exact RQ2 hash |
| Execution boundary | PASS | exact allowlist/order/parameters; zero model calls |
| Deterministic execution | PASS | unchanged RQ2 executor; isolated derived write only |
| Postcondition verification | PASS | all independent expected/observed checks passed |
| Unauthorized mutation | NONE | source before/after hash identical |
| Provenance | PASS | all six mandatory artifact types content-linked |
| Audit | PASS | schema/hash valid and reconstructable |
| Final acceptance | PASS | every mandatory Boolean input true |

Canonical Case A identities:

| Artifact | Canonical identity |
|---|---|
| Result SHA-256 | `31354dfef7fcc9988ce6bfa748aaea3b2cf1a2b498e1d14b007424e6c895bbc0` |
| Execution hash | `2578a6d836150d30b79b45416cc9d8771b63f6e75e77f8a302a161e4c31898ed` |
| Verification hash | `f5337533ac8c4668cf91b899da6e6345130aa048a4baacdf712f57b1cabbee4d` |
| Audit record hash | `ffb86917e603012b4a73daff873abc496eadad5345951d3a2bcd2c71e049f8f5` |

The accepted result keeps `authoritative_render = false`, `product_layer = null`, physical portrayal
profile `null`, Point geometry unchanged, and the source fixture unchanged.

## 7. Negative and tamper scenarios

The machine-readable source is
`artifacts/rq3/rq3-demo-01/experiment-summary.json`.

| Case | Frozen violation | Expected | Actual | Mutation prevented | Result |
|---|---|---|---|---|---|
| A | Canonical positive path | accept | PASS | only authorized isolated write | PASS |
| B | Missing authorization | pre-block | `AUTHORIZATION_MISSING` | yes | PASS |
| C | Proposal tampered after authorization | pre-block | `PROPOSAL_HASH_MISMATCH` | yes | PASS |
| D | Authorization scope mismatch | pre-block | `AUTHORIZATION_SCOPE_MISMATCH` | yes | PASS |
| E | Unauthorized tool substitution | pre-block | `UNAUTHORIZED_TOOL` | yes | PASS |
| F | Parameter tampering | pre-block | `PARAMETER_MISMATCH` | yes | PASS |
| G | Tool success; postcondition violation | verification/audit fail | `POSTCONDITION_FAILED` | authoritative mutation absent | PASS |
| H | Invalid mandatory provenance | audit fail | `PROVENANCE_INCOMPLETE` | authoritative mutation absent | PASS |
| I | Source mutation attempt | pre-block | `UNAUTHORIZED_MUTATION` | yes | PASS |
| J | Unresolved constraint escalation | pre-block | `UNRESOLVED_CONSTRAINT_ESCALATION` | yes | PASS |
| K | Result changed after hashing | integrity/audit fail | `ARTIFACT_HASH_MISMATCH` | authoritative mutation absent | PASS |
| L | One exact idempotent replay | accept stable result | PASS; same result hash | only authorized isolated write | PASS |

All seven cases required by the frozen policy to block before mutation (B–F, I, J) created neither
an output directory nor replay state. G, H, and K operated only on isolated, non-authoritative
derived artifacts and were rejected before authoritative acceptance. No negative case changed the
source fixture.

Additional focused adversarial checks reject authorization-content tampering, authorization
substitution, source substitution, unknown request-field expansion, execution-record tampering,
verification-record tampering, and a third replay attempt.

## 8. Determinism

Case A and Case L both accepted with result SHA-256
`31354dfef7fcc9988ce6bfa748aaea3b2cf1a2b498e1d14b007424e6c895bbc0`. Their permitted execution,
verification, audit IDs, hashes, and bounded timestamps differ; the proposal, authorization, tool
sequence, parameters, environment, semantic result, byte-level result, and verdict match.

The complete A–L experiment was then executed into a second fresh isolated root. Recursive byte
comparison of the two complete bundles reported no differences. The execution-count state permits
exactly two executions and blocks a third with `REPLAY_LIMIT_EXCEEDED` before output mutation.

## 9. Provenance completeness

The Case A audit record reconstructs:

```text
RQ2 proposal
→ canonical evidence-set identity and knowledge references
→ proposal-bound authorization
→ deterministic execution record and environment
→ isolated result identity/hash
→ independent verification report
→ final audit record and PASS decision
```

All referenced trust artifacts have IDs and canonical hashes; the audit does not rely on paths
alone. Case H proves that a structurally present but hash-invalid mandatory evidence link produces
`provenance_complete = false` and final acceptance `FAIL`.

## 10. Semantic integrity

```text
KG: NO
GraphRAG retrieval: NO
Evidence projection: NO
RQ2 constraint semantics: NO
RQ2 proposal semantics: NO
Mapping semantics: NO
Classification: NO
Geometry: NO
Portrayal: NO
ProductLayer: NO
Model: NO
ROAD: NO
School Hero: NO
BUILD: NO
Core: NO
Authoritative source data: NO
```

The new source is isolated to the RQ3 trust adapter. The existing RQ2 executor and all frozen
semantic implementation files remain byte-identical to the predecessor.

## 11. Regression and validation

### Focused RQ3

```text
PYTHONPATH=src:. /Users/dongpodeng/.pyenv/versions/3.11.9/bin/python3 \
  -m pytest -o addopts='' -q tests/test_rq3_demo_01.py
24 passed
```

The 24 tests cover proposal/authorization identity, A–L, zero-write pre-blocks, exact replay and
replay exhaustion, schema meta-validation, schema-valid positive/negative trust records, explicit
five-input acceptance logic, source preservation, request/source/authorization substitution, and
record-chain tampering.

### Schema validation and lint

Four schemas meta-validate under JSON Schema 2020-12: authorization, execution record,
verification report, and audit record. Every emitted A/G/H/K/L execution, verification, and audit
record validates against its contract. Canonical self-hashes recompute exactly. Ruff reports all
checks passed for the implementation, runner, and focused tests.

### Targeted regression

The clean post-commit RQ1/RQ2/RQ3, Core, ROAD, School Hero, and BUILD targeted run
produced:

```text
854 passed, 177 skipped, 2 failed
```

Both failures are branch/file-scope assertions embedded in historical BUILD tasks and already
invalid on the exact predecessor: one compares the current repository to its historical
BUILD-08A-only change set, and one requires the working tree to contain exactly the historical
BUILD-09F candidate files. No semantic/domain test failed. The skipped tests are bounded
private-data gates.

### Broad regression and exact predecessor baseline

| Run | Result | Classification |
|---|---|---|
| Candidate before commit | `1335 passed, 208 skipped, 31 failed` | 27 inherited + 3 dirty-candidate scope assertions + 1 expected RQ3-DEMO-00 successor-scope assertion |
| Exact predecessor `2c3c259` | `1315 passed, 208 skipped, 27 failed` | inherited failures reproduced exactly |
| Clean candidate after commit | `1338 passed, 208 skipped, 28 failed` | exact 27 inherited failures + 1 expected RQ3-DEMO-00 successor-scope assertion |

The 27 inherited failures cover historical branch/predecessor exact-scope assertions, old protected
byte/freeze-manifest expectations, a repository tag expectation invalidated before this task, and
historical Core residual-audit assumptions. The only persistent successor-specific broad finding is
`test_rq3_demo_00_specification.py::test_only_rq3_demo_00_specification_artifacts_changed`, whose
purpose is to require the previous task to contain only RQ3-DEMO-00 files; it necessarily rejects a
legitimate RQ3-DEMO-01 successor. It does not exercise RQ3 runtime semantics. No unrelated repair
was attempted.

Final focused tests remained `24 passed`; lint remained clean. The clean candidate added all 24
RQ3-DEMO-01 tests as passes and cleared the three dirty-candidate scope failures. The single
additional broad failure is the expected predecessor-task scope assertion described above.

**RQ3 semantic regressions: 0.**

## 12. Findings

1. Deterministic proposal/authorization hashing prevents modified or substituted proposals from
   reaching execution.
2. A closed request contract is necessary in addition to authorization schema validity; exact
   scope, tool order, parameters, source identity, unresolved constraints, and unknown-field
   rejection are all enforced before writes.
3. Executor success is insufficient. Case G returns successful deterministic tool execution but is
   rejected by independent observable-state verification.
4. Content-addressed provenance is operative rather than decorative. Cases H and K fail because
   links no longer resolve, despite otherwise complete-looking records.
5. Persistent replay state can permit one exact idempotent replay while blocking a third attempt.
6. Research authorization identity/time semantics are not production non-repudiation. Production
   deployment would still require governed identity, signing/key lifecycle, trusted time,
   revocation, and durable policy administration.
7. The experiment covers one frozen symbolic mapping proposal and does not establish external
   validity for other agents, proposals, datasets, or authoritative mutation types.

## 13. Hypothesis verdict

**H3: SUPPORTED WITH FINDINGS.**

The experiment supports the hypothesis that explicit authorization, proposal-bound execution,
deterministic postcondition verification, and tamper-evident provenance can constrain a
probabilistic mapping agent sufficiently to participate in an auditable authoritative mapping
workflow under the tested conditions.

It does not prove that AI agents are generally trustworthy, nor does it authorize production
source mutation or authoritative rendering.

## 14. Completion artifacts

| Artifact | Path |
|---|---|
| Required report | `RQ3-DEMO-01-Authorized-Execution-Verification-Provenance-Report.md` |
| Trust implementation | `src/nma/rq3_demo.py` |
| Execution schema | `data/specifications/rq3-execution-record-schema-v1.0.json` |
| A–L experiment runner | `scripts/run_rq3_demo_01.py` |
| Focused tests | `tests/test_rq3_demo_01.py` |
| Machine-readable bundle | `artifacts/rq3/rq3-demo-01/` |
| Canonical positive audit | `artifacts/rq3/rq3-demo-01/case-a/audit-record.json` |
| Experiment summary | `artifacts/rq3/rq3-demo-01/experiment-summary.json` |

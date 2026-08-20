# AGENT-06 — Authorization Handoff & Controlled Execution Boundary Audit

Report date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — AUTHORIZATION HANDOFF IS A NON-EXECUTING DOMAIN-VALIDATION REQUEST ONLY**

AGENT-06 defines exactly one closed contract, `nma.authorization-handoff-request/1.0`, for carrying
the immutable Agent governance chain to a named domain authorization boundary. The handoff can
identify only one of two frozen target/capability pairs, contains the exact proposal, evaluation,
decision-record, run-record, and evidence-set references, and records deterministic duplicate
metadata. It cannot contain a domain authorization, grant, permission, command, tool payload,
endpoint, path, execution identity, mutation instruction, or domain idempotency identity.

The required `domain_authorization_reference` slot is structurally `null`. An authorization remains
a separate input owned, issued, stored, validated, and consumed by ROAD or School Hero. Merely
constructing a string that resembles a domain authorization identifier can never satisfy this
contract. A valid handoff therefore remains non-executing and reports
`requires-domain-authorization-validation` with `execution_eligible=false`.

AGENT-06 does not connect the public runtime to either execution engine and does not implement a
generic authorization validator or a final production execution adapter. The canonical production
runtime remains `nma-public-evidence-runtime/v0.2`; production dependencies remain empty; the
planning, evidence, proposal, evaluation, decision, and run-record boundaries remain unchanged.
Core, ROAD, and School Hero behavior and identities remain frozen.

## 2. Baseline and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap` | PASS |
| Required starting SHA | `c40f3a2cdc9b87cd03f3f14ff1d0635cd64229bd` | PASS |
| AGENT-04 predecessor | `22b84e80f6771935e364fef580cf4c8adbe95218` | PASS |
| AGENT-03 predecessor | `5d589b9ddfe815f925de3cc2eb0c7765af27d6d3` | PASS |
| AGENT-02 predecessor | `f8499fbe33dc633f44f48a5e28fb7c12670f0f0c` | PASS |
| AGENT-01 predecessor | `15881646dd47062f5a15e248380dcb583da9bb8b` | PASS |
| AGENT-00 predecessor | `113cab95f2d898feb8a58b41bbc88e1590b79cc3` | PASS |
| CORE-FINAL predecessor | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Required branch | `agent/agent-06-authorization-handoff-boundary` | PASS |
| Starting worktree | clean | PASS |

The branch was created directly from the exact accepted AGENT-05 commit. Work did not start from
`main`, an earlier Agent commit, or a dirty worktree.

## 3. Exact changed files

AGENT-06 changes exactly these four files relative to the accepted AGENT-05 commit:

| File | Scope reason |
|---|---|
| `agent_contracts/handoff.py` | Creates and validates the closed non-authoritative handoff, exact governance linkage, content identity, and duplicate metadata outside production `src/nma`. |
| `schemas/authorization-handoff-request-v1.0.schema.json` | Publishes the single closed Draft 2020-12 handoff schema, including closed target pairs and a null-only authorization slot. |
| `tests/test_authorization_handoff_boundary_agent06.py` | Verifies closure, linkage, target vocabulary, authority injection rejection, replay, non-execution, dependencies, and frozen Core hashes. |
| `AGENT-06-Authorization-Handoff-Controlled-Execution-Boundary-Audit.md` | Records the contract decision, domain ownership audits, validation evidence, integrity evidence, and future gate. |

No existing `src/nma`, public runtime, public builder, dependency, data, graph, Core, ROAD, School
Hero, predecessor Agent contract, demo, freeze, fingerprint, schema, or verification file changes.

## 4. Authorization handoff contract identity and version

Contract identity: `nma.authorization-handoff-request/1.0`.

Artifact schema: `schemas/authorization-handoff-request-v1.0.schema.json`.

Each handoff has identity `authorization-handoff:sha256:<digest>`, computed from canonical UTF-8
JSON of every field except the self-identity. The digest therefore covers the target, complete
governance reference set, null authorization slot, replay rules, all version links, boundary, and
recording provenance. Any changed field must produce a different handoff identity or fail closed.

The contract carries these exact top-level fields:

| Field | Bounded meaning |
|---|---|
| `schema` | Constant handoff contract version. |
| `handoff_id` | Content identity of the complete handoff body. |
| `target` | One closed domain, operation class, and domain authorization-contract class. |
| `proposal_reference` | Exact immutable evidence-backed proposal identity. |
| `evaluation_reference` | Exact proposal-quality evaluation identity. |
| `decision_record_reference` | Exact accountability-only decision identity. |
| `run_record_reference` | Exact traceability-only run identity. |
| `evidence_references` | Non-empty, unique proposal-purpose evidence set, identical across the proposal/evaluation/decision/run chain. |
| `domain_authorization_reference` | Required `null`; domain authorization must be supplied separately to the domain-owned validator. |
| `replay` | Stable governance/target handoff key and constants stating no new authority and domain-owned idempotency. |
| `versions` | Exact production runtime and Agent contract version links. |
| `boundary` | Constant `domain-validation-request-only`. |
| `provenance` | Bounded recorder and UTC-second record time after the linked run record. |

The handoff creator accepts governance objects, target vocabulary, and recording metadata only. It
has no parameter for authorization, execution, mutation, endpoint, tool, command, filesystem path,
or domain idempotency key.

## 5. Closed target-domain and capability vocabulary

Exactly two domain/operation/authorization-contract triples are valid:

| Domain | Operation class | Domain-owned authorization contract |
|---|---|---|
| `road` | `derived-road-centreline-portrayal` | `nma.road-execution-authorization/1.0` |
| `school-hero` | `school-symbol-derived-layer-portrayal` | `nma.symbol-edit-authorization/1.0` |

The triples are coupled, not independently mixable. Unknown domains, unknown operations, a School
Hero operation paired with ROAD, a ROAD operation paired with School Hero, and mismatched contract
versions fail both Python validation and JSON Schema validation. The vocabulary exposes no route,
API path, handler, tool, command, file path, generic mutation, or arbitrary capability string.

## 6. Allowed field matrix

| Input | Allowed representation | Ownership retained by |
|---|---|---|
| Handoff identity | Content-addressed request ID | Agent handoff contract; never domain idempotency or authority |
| Target domain | `road` or `school-hero` | Closed handoff routing vocabulary |
| Operation class | One exact operation coupled to its domain | Domain remains owner of actual execution scope |
| Authorization contract class | Exact frozen schema name only | ROAD or School Hero |
| Proposal | Content reference only | Evidence-backed proposal contract |
| Evaluation | Content reference only | Proposal-quality evaluation layer |
| Decision record | Content reference only | Accountability layer |
| Run record | Content reference only | Traceability/audit layer |
| Evidence | Exact immutable proposal-purpose references | Evidence registry/producer |
| Domain authorization slot | `null` only | Domain issuer, store, and validator; supplied outside handoff |
| Replay key | Content identity of target plus governance references | Agent duplicate detection only |
| Version links | Exact canonical constants | Existing contract owners |
| Recorder/time | Bounded audit metadata | Handoff recorder; no authority effect |

## 7. Forbidden field matrix

| Forbidden content | Why it is rejected |
|---|---|
| ROAD or School Hero authorization ID/hash/object | The authorization slot accepts `null` only; extra fields are rejected. |
| Authorization grant, approval, permission, or consumption state | Handoff is a validation request, never a capability or ledger. |
| Execution ID, plan, receipt, or observation as a command | Those objects are domain-owned downstream artifacts. |
| Shell command or argument list | No command field exists; top-level and nested objects are closed. |
| Tool name or tool payload | No tool field exists and arbitrary operation strings are rejected. |
| API route, endpoint, URL, or handler | Target vocabulary contains semantic domain/capability constants only. |
| Filesystem path or write target | No path field exists. |
| Generic mutation parameters or durable write instructions | No mutation payload field exists. |
| Evaluation score as permission | Evaluation identity is linkage only and remains proposal-quality-only. |
| Decision/run/evidence confidence as permission | These references preserve governance accountability and traceability only. |
| Agent-owned domain idempotency key | Replay declares `domain_idempotency=external-domain-owned`. |

## 8. ROAD authorization ownership audit

| Concern | Exact existing owner and entry point | AGENT-06 treatment |
|---|---|---|
| Authorization creation/issuance | `src/nma/road_approval.py::authorize_road_portrayal` issues the frozen ROAD-03 capability only after exact proposal/decision validation and explicit human approval. | Referenced as external authority; not imported, called, copied, stubbed, or emulated. |
| Authorization identity | `authorization_sha256` in `road_approval.py`; frozen `AUTHORIZATION_ID` and expected hash in `road_execution.py`. | Handoff cannot contain either identity. |
| Authorization storage/lookup | `RoadAuthorizationStore.load` is the read-only store for the single frozen ROAD-03 capability. | Future adapter must use this domain store, never an Agent value. |
| Authorization validation | `FrozenRoadAuthorizationVerifier.verify`, with `validate_authorization` and the frozen ROAD-01/02/03 chain. | Required external validation boundary; not implemented by AGENT-06. |
| Authorization consumption | `RoadExecutionEngine._existing_execution`, the immutable consumption record, SHA-bound ledger, and `road_authorization_consumption.py`. | Remains ROAD-owned and unchanged. |
| Idempotency | `RoadExecutionEngine.execute` hashes the exact supplied domain idempotency key; replay must match the existing consumption record. | Handoff replay key cannot replace it. |
| Execution | `RoadExecutionEngine.execute_by_id` permits exactly `authorization_id` plus `idempotency_key`, then `execute` validates and atomically materializes the frozen scope. | Not connected to Agent/public runtime. |
| Observation/receipt | ROAD execution persists the runtime observation, receipt, and consumption artifacts; `get_execution` reads the receipt. | Downstream domain output only. |
| Rollback | `RoadExecutionEngine.rollback_execution` and module adapter `rollback_execution`. | Domain-owned and unchanged. |
| QA/verification | `RoadExecutionVerifier.verify`. | Remains the independent ROAD post-execution verifier. |
| Provenance | ROAD-05 QA/provenance schemas and verifier output. | Never substituted by Agent run/handoff provenance. |

ROAD’s current local future-handoff surface is therefore
`RoadAuthorizationStore.load -> FrozenRoadAuthorizationVerifier.verify -> RoadExecutionEngine.execute`.
The public request adapter `execute_by_id` is a domain execution entry point, not an Agent handoff
entry point. A future issue must place a separately authenticated domain-controlled adapter before
it and must not pass the handoff identity as the authorization or idempotency identity.

## 9. School Hero authorization ownership audit

| Concern | Exact existing owner and entry point | AGENT-06 treatment |
|---|---|---|
| Authorization creation/issuance | The upstream HERO-03 mechanism is the issuer of `nma.symbol-edit-authorization/1.0`; this checkout consumes its complete artifact and does not provide a production Agent issuer. | AGENT-06 does not invent or emulate an issuer. |
| Authorization identity | `authorization_id` is issuer-supplied; `authorization_sha256` recomputes `authorization_hash` from the complete domain artifact. | Handoff cannot contain either. |
| Authorization storage/lookup | `ExecutionAuthorizationStore.save/load`, described as the filesystem handoff from HERO-03. | Future adapter must load from this domain-owned store. |
| Authorization validation | `ExecutionAuthorizationVerifier.verify` validates hash, ready state, non-consumption, proposal/baseline/operation binding, validation result, human approval, scope, expiry, and invalidation. | Required external domain check; not implemented by AGENT-06. |
| Idempotency/consumption | `SchoolHeroExecutionEngine.execute` and its `nma.school-hero-idempotency-index/1.0` index bind authorization ID/hash to the hashed domain idempotency key and execution ID. | Handoff replay identity cannot replace or widen it. |
| Execution | `SchoolHeroExecutionEngine.execute_by_id` accepts only authorization ID and domain idempotency key; `execute` verifies before atomic execution. | Not connected to Agent/public runtime. |
| Observation/receipt | HERO-04 persists observation, receipt, bundle, data, and symbol artifacts; `get_execution` returns the exact receipt. | Domain-owned downstream result. |
| Rollback | `SchoolHeroExecutionEngine.rollback_execution` and module adapter `rollback_execution`. | Domain-owned and unchanged. |
| Verification | `SchoolHeroVerifier.verify` independently checks authorization, plan, receipt, bundle, runtime data, full lineage, and artifacts. | Remains the post-execution verification owner. |
| Provenance | HERO-05 `nma.school-hero-provenance/1.0` output and complete upstream lineage checks. | Never substituted by Agent handoff/run provenance. |

The existing local future-handoff surface is
`ExecutionAuthorizationStore.load -> ExecutionAuthorizationVerifier.verify -> SchoolHeroExecutionEngine.execute`.
As with ROAD, `execute_by_id` is a domain execution API and not an Agent handoff adapter.

## 10. Agent handoff versus domain authorization

| Property | Agent handoff request | Domain authorization |
|---|---|---|
| Purpose | Ask a named domain mechanism to validate separately supplied authority for one governed proposal. | Grant an exact bounded domain capability under domain rules. |
| Issuer | Agent governance/handoff recorder. | ROAD-03 or School Hero HERO-03 authority. |
| Identity | Content address of governance references and target. | Domain authorization ID/hash under domain semantics. |
| Carries permission | No. | Yes, only after exact domain validation. |
| Can execute | No. | Only through the owning domain engine and consumption semantics. |
| Replay meaning | Duplicate request; no new authority. | Domain-owned idempotency/consumption rules decide replay. |
| Verification | Governance-link consistency only. | Domain authorization verification plus post-execution domain verification. |

The only allowed architecture remains:

```text
request -> intent planning -> evidence -> proposal -> evaluation -> decision record
        -> run/provenance record -> authorization handoff request
        -> separate domain authorization validation -> domain execution
        -> domain verification/receipt/provenance
```

The handoff validates the left side and names the boundary. It never crosses the boundary by itself.

## 11. Replay and idempotency analysis

`replay.handoff_key` is a content address over the contract version, exact target triple, proposal,
evaluation, decision, run, and evidence-set references. Identical governance/target input therefore
has the same handoff key even if a later recorder/time creates a distinct audit envelope.

This identity has exactly one declared effect: `same-request-no-new-authority`. It does not name or
reserve an execution, authorize a retry, consume approval, or act as a ROAD/School Hero
idempotency key. `domain_idempotency=external-domain-owned` makes that separation explicit.

| Replay condition | Result |
|---|---|
| Exact duplicate Agent handoff | Same replay key, authorization slot still null, no authority created. |
| Changed target or governance reference | Different deterministic key or rejected stale linkage. |
| Modified replay key | Rejected. |
| Replay claiming new authorization effect | Rejected. |
| Replay claiming Agent-owned idempotency | Rejected. |
| Same handoff paired with a different domain authorization | Domain validator must reject deterministic proposal/authorization mismatch. |
| Same authorization with different domain idempotency key | Existing ROAD/Hero consumption rules decide and fail closed as already implemented. |
| Agent handoff ID used as domain idempotency ID | Forbidden; identities have different ownership and semantics. |

## 12. Fail-closed behavior matrix

| Condition | AGENT-06 result |
|---|---|
| Missing proposal/evaluation/decision/run reference | Reject exact field set and schema. |
| Empty/missing evidence set | Reject. |
| Unknown or cross-paired domain/operation | Reject. |
| Stale/mismatched proposal reference | Reject. |
| Stale/mismatched evaluation reference | Reject. |
| Stale/mismatched decision reference | Reject. |
| Stale/mismatched run reference | Reject. |
| Mismatched evidence set anywhere in the chain | Reject. |
| Unsatisfactory evaluation or non-accepted accountability decision | Reject handoff request; neither condition can become authority. |
| Agent-minted ROAD/Hero authorization-like value | Reject because authorization slot must be null. |
| Grant, permission, mutation, execution, command, tool, API, or path field | Reject closed object shape. |
| Stale timestamp or version linkage | Reject. |
| Replay/idempotency claim changed | Reject. |
| Valid handoff, domain authorization missing | Non-executing; requires domain validation. |
| Valid handoff, domain authorization invalid/stale/mismatched | Future domain adapter must return no execution. Existing validators already fail closed for their domain artifacts. |
| Valid handoff plus exact domain authorization | Eligible only for a separately authorized future domain-owned adapter to invoke the existing execution path; AGENT-06 does not implement that connection. |

Evaluation scores, decision records, run/provenance, evidence confidence, semantic inference, public
browser state, Agent-generated identifiers, routes, and intents have no transition to authorization.

## 13. Production runtime and dependency comparison

| Boundary | Before AGENT-06 | After AGENT-06 | Result |
|---|---|---|---|
| Production runtime identity | `nma-public-evidence-runtime/v0.2` | Same constant in handoff version linkage | PASS |
| `pyproject.toml` runtime dependencies | `dependencies = []` | Byte-identical, still empty | PASS |
| Public runtime HTML | SHA-256 `8b6d6310…a5a470` | Byte-identical | PASS |
| Public site builder | SHA-256 `6f9e6e75…a50c55e` | Byte-identical; does not import/publish handoff | PASS |
| Public portrayal graph | SHA-256 `0f90dc36…eacca` | Byte-identical | PASS |
| Production `src/nma` | Accepted AGENT-05 tree | No diff | PASS |
| Agent handoff imports | Not present | Standard library plus existing Agent contract modules only | PASS |
| ROAD/Hero execution reachability from public runtime | Not reachable | Not reachable | PASS |

The handoff implementation imports no ROAD, School Hero, GraphRAG, vector, Neo4j, retrieval,
entity-resolution, shell, network, filesystem execution, or production runtime module.

## 14. Future controlled-execution prerequisites

A separately authorized future issue must satisfy every prerequisite before any connection is made:

1. freeze `nma.authorization-handoff-request/1.0` and its content/canonicalization rules;
2. explicitly freeze the supported domain/capability set (currently the two exact pairs above);
3. identify the authenticated deployment boundary around
   `RoadAuthorizationStore.load/FrozenRoadAuthorizationVerifier.verify` and
   `ExecutionAuthorizationStore.load/ExecutionAuthorizationVerifier.verify`;
4. define deterministic proposal/evidence/decision/run-to-domain-authorization bindings without
   deriving authorization from any Agent record;
5. define domain-owned idempotency, consumption, concurrency, and replay rules without using the
   handoff or run identity as a substitute;
6. define fail-closed error codes and guarantee no call to execution on missing, invalid, stale,
   expired, invalidated, consumed, mismatched, or ambiguous authorization;
7. define the exact domain receipt/observation/verification/provenance return path and ensure Agent
   provenance never claims that an effect occurred;
8. define production authentication, authorization-store access, deployment, secret, network, and
   audit-log requirements outside the public evidence runtime;
9. prove there is no GitHub Pages, public-browser, route, intent, semantic, tool, API, or direct
   mutation bypass around domain validation and consumption;
10. preserve ROAD rollback expectations and School Hero rollback/observation behavior, including
    explicit operator authority for rollback where required;
11. add independent negative tests that assert execution entry points are not called on every
    failed validation path;
12. obtain a separate issue authorization before implementing, deploying, or promoting the adapter.

AGENT-06 intentionally implements none of these production connections.

## 15. Validation results

Environment: Python 3.11.9, pytest 8.3.3, jsonschema 4.23.0.

| Validation | Result |
|---|---|
| Focused AGENT-06 authorization-handoff boundary | `37 passed` |
| Canonical AGENT-02/03/04/05/06 contract suites | `122 passed` |
| Agent-focused tests | `184 passed, 3 known failed` (187 total) |
| Exact Core suite | `53 passed` |
| Complete ROAD historical suite | `199 passed` |
| Complete School Hero suite | `42 passed` |
| Relevant schema/meta-schema validation | Included in focused/contract suites; Draft 2020-12 meta-validation PASS |
| Full repository suite | `599 passed, 3 known failed` (602 total) |
| Ruff static checks on AGENT-06 Python scope | PASS |
| Ruff formatting on AGENT-06 Python scope | PASS |
| JSON syntax | PASS |
| `git diff --check` | PASS |

The focused suite contains executable checks for both domain/capability pairs, every required
governance reference, stale and mismatched linkages, evidence-set equality, authority identifiers,
grant/permission fields, execution IDs, mutation payloads, shell commands, tool payloads, API
endpoints, filesystem paths, null-only authorization, non-execution before validation, stable
duplicate identity, domain-owned idempotency, version/timestamp linkage, schema closure, import
isolation, production hashes, dependency identity, and Core hashes.

### 15.1 Final staged validation

This section is finalized after all four expected files are staged so the frozen Core test that
asserts an empty untracked-file set observes the intended complete change set.

| Validation | Final result |
|---|---|
| Agent-focused suite | `184 passed, 3 known failed` (187 total) |
| Exact Core suite | `53 passed` |
| Full repository suite | `599 passed, 3 known failed` (602 total) |
| Exact known baseline failure set/signatures | Same three node IDs and materially identical signatures; PASS |

## 16. Frozen integrity

| Frozen boundary | Evidence | Result |
|---|---|---|
| Core | Three canonical source SHA-256 values unchanged; exact five-file acceptance suite: `53 passed` | PASS |
| ROAD | Complete ROAD-01 through ROAD-05 historical suite: `199 passed`; no ROAD diff | PASS |
| School Hero | Complete HERO-04/HERO-05/V032/intelligence suite: `42 passed`; no Hero diff | PASS |
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

## 17. Treatment of the three accepted baseline failures

The accepted baseline is `562 passed / 3 failed`. AGENT-06 does not repair or alter:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`.

Their expected signatures remain respectively the generated/tracked PMTiles capability-catalog
drift, the historical server-size freeze mismatch, and the Pages candidate manifest catalog-size
mismatch. AGENT-06 changes none of their tests, generators, catalogs, server files, manifests,
freeze records, or Pages artifacts. The new handoff contract does not import, reference, publish,
or authorize those systems. They remain materially identical, non-production, and
authorization-irrelevant.

## 18. Final SHA and synchronization protocol

The report-containing commit cannot embed its own Git object ID because the ID hashes this report;
embedding it would recursively change the ID. Following the accepted AGENT-02/03/04/05 closure
pattern, the exact final SHA is recorded in the GEO-137 final handoff after the report commit and
push.

Closure requires:

```text
git rev-parse HEAD
git rev-parse @{upstream}
git ls-remote origin refs/heads/agent/agent-06-authorization-handoff-boundary
git status --short --branch
```

PASS requires local HEAD, upstream tracking ref, and remote branch to be equal, with a clean final
worktree. No pull request is created.

## 19. Final worktree status

Final cleanliness and local/upstream/remote SHA equality are recorded in the GEO-137 final handoff
after commit and push. A dirty worktree or unequal SHA is a FAIL-CLOSED result.

## 20. Recommendation for the next bounded Agent issue

GEO-137 should close **PASS** only after final staged validation, commit, push, SHA equality, and a
clean worktree.

The next separately authorized issue should freeze a **read-only domain-authorization binding
profile and independent adapter conformance harness**. It should define deterministic mappings from
the two closed handoff targets to the existing domain validator inputs and prove, with spies/fakes
that cannot execute, that missing, stale, expired, invalidated, consumed, cross-domain, or
mismatched authorization never reaches an execution engine. It must not connect the public runtime,
deploy an adapter, call production execution, introduce generic authorization, alter domain IDs or
idempotency, implement Agent memory, promote semantic systems, or change Core/ROAD/School Hero.

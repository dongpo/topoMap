# AGENT-03 — Evidence & Semantic Boundary Audit

Report date: 2026-08-19 (Asia/Taipei)

## 1. Verdict

**PASS — EVIDENCE AND SEMANTIC AUTHORITY REMAIN BOUNDED**

AGENT-03 defines `nma.agent-evidence/1.0` as an immutable, content-addressed evidence envelope and
`nma.agent-evidence-reference/1.0` as its closed reference form. It also defines the deliberately
narrow `nma.evidence-backed-proposal/1.0` envelope that binds a validated
`nma.intent-planning/1.0` result to resolved evidence references and presentation metadata only.

Evidence may support explanation, a proposal, verification, or provenance. It cannot grant
authorization, supply an execution command, carry a mutation permission, consume an approval, or
substitute for ROAD or School Hero authority. Missing or invalid evidence fails closed with no
generation, fallback, or silent substitution.

The only canonical production runtime remains `nma-public-evidence-runtime/v0.2`. The only
canonical planning contract remains `nma.intent-planning/1.0`. The public runtime, public portrayal
graph, production builder, dependency manifest, Core identity, ROAD, and School Hero boundaries
remain byte-identical to the accepted AGENT-02 predecessor.

## 2. Baseline and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap` | PASS |
| Required starting SHA | `f8499fbe33dc633f44f48a5e28fb7c12670f0f0c` | PASS |
| AGENT-01 predecessor | `15881646dd47062f5a15e248380dcb583da9bb8b` | PASS |
| AGENT-00 predecessor | `113cab95f2d898feb8a58b41bbc88e1590b79cc3` | PASS |
| CORE-FINAL predecessor | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Required branch | `agent/agent-03-evidence-semantic-boundary` | PASS |
| Starting worktree | clean | PASS |
| Validated implementation commit | `f85ab0f757244b4fa8b51f8672cbc5b6ae5c216a` | PASS |

The branch was created directly from the accepted AGENT-02 SHA. Work did not begin from `main`, an
earlier Agent branch, or an uncommitted worktree.

## 3. Exact changed-file list

AGENT-03 changes exactly these five files relative to AGENT-02:

| File | Scope reason |
|---|---|
| `agent_contracts/evidence.py` | Defines immutable evidence objects/references, deterministic identity, fail-closed resolution, and a closed evidence-backed proposal boundary outside the frozen installed package. |
| `schemas/agent-evidence-v1.0.schema.json` | Publishes the closed Draft 2020-12 evidence envelope schema. |
| `schemas/evidence-backed-proposal-v1.0.schema.json` | Publishes the closed proposal/reference schema with proposal-only metadata. |
| `tests/test_evidence_semantic_boundary_agent03.py` | Verifies identity, provenance, immutability, missing/invalid evidence behavior, authority rejection, semantic dependency isolation, and production hashes. |
| `AGENT-03-Evidence-Semantic-Boundary-Audit.md` | Records the ownership decision, dependency proof, validation, and closure evidence. |

No existing `src/nma`, public page, public builder, dependency, data, graph, Core, ROAD, School Hero,
demo, freeze, or deployment file changes.

## 4. Evidence Object model decision

### 4.1 Contract and ownership

An Agent Evidence Object is a read-only metadata envelope for one reproducible evidence selection.
It is evidence infrastructure, not a semantic runtime, planner, authorization source, command
carrier, or executor.

The complete evidence envelope contains:

| Field | Meaning |
|---|---|
| `schema` | Constant `nma.agent-evidence/1.0`. |
| `evidence_id` | `evidence:sha256:<digest>` identity of the complete immutable envelope body. |
| `source_artifact` | Source artifact identity, explicit version, and SHA-256 of the source bytes. |
| `content_sha256` | SHA-256 of the canonical JSON evidence payload selected from the source. |
| `provenance` | Bounded producer identity and recorded timestamp. |
| `citation` | Human-auditable locator and label for the cited evidence. |
| `review` | Explicit `unreviewed`, `reviewed`, or `validated` status and bounded reviewer identity. |
| `reproducibility` | Closed method, bounded recipe, and SHA-256 identities of reproduction inputs. |

The Python representation uses frozen dataclasses. Nested evidence metadata is also frozen, the
registry owns only an immutable tuple, and `to_dict()` returns a detached serialization copy. The
canonical runtime can therefore consume a reference or serialized copy without gaining a mutation
surface over the registered evidence snapshot.

### 4.2 Identity and independent verification

The implementation computes, rather than accepts, these identities:

1. source artifact SHA-256 from supplied source bytes;
2. evidence content SHA-256 from canonical JSON with sorted keys, compact separators, UTF-8, and
   non-finite numbers rejected;
3. reproduction input SHA-256 values from supplied input bytes;
4. evidence identity from the complete versioned body containing source linkage, content hash,
   provenance, citation, review, and reproducibility metadata.

Validation recomputes the evidence identity and rejects any mismatch. An independently held source
artifact, evidence payload, and reproduction inputs can therefore reproduce the recorded hashes and
envelope identity. The same complete envelope produces the same identity. A changed payload, source
artifact, version, citation, provenance snapshot, review state, or recipe produces a new identity;
copying the old identity onto changed content is rejected.

### 4.3 Reference semantics

`nma.agent-evidence-reference/1.0` contains exactly:

- the reference schema version;
- one valid `evidence_id`;
- one purpose from `explanation`, `proposal`, `verification`, or `provenance`.

The purpose describes why evidence is cited; it grants no capability. Proposal construction accepts
only `purpose=proposal`, resolves every reference through an explicit immutable registry, and rejects
an empty registry, missing identity, malformed identity, unknown version, or unknown purpose. There
is no callback, model generation, nearest-neighbor substitution, alternate graph, or network fallback.

### 4.4 Explicitly absent authority

Neither evidence schema contains authorization grants, approvals, permissions, execution IDs,
commands, endpoints, arbitrary API calls, paths, filesystem writes, mutation parameters, approval
consumption, ROAD authorization substitution, or School Hero authorization substitution.

Review status is descriptive provenance. `reviewed` and `validated` do not mean approved for
execution and cannot be transformed into a capability grant.

## 5. Semantic ownership audit

The required classification vocabulary is:

- **A — Canonical production**;
- **B — Production adapter**;
- **C — Compatibility**;
- **D — Experimental**;
- **E — Deprecated**.

The word `canonical` inside the large JSON graph's filename describes the source of truth inside its
experimental graph family. It does not confer canonical-production status.

| Semantic component | Class | Ownership and boundary decision |
|---|---|---|
| Allowlisted `data/knowledge/portrayal-graph.json` in the built evidence-only public runtime | **A** | The small reviewed public portrayal graph remains the only canonical production semantic/evidence graph. Read-only presentation use only. |
| Reviewed public five-scene contract, capability catalog, and allowlisted portrayal assets | **A** | Canonical public evidence inputs within the frozen v0.2 artifact; they cannot authorize durable effects. |
| Built `nmaAgentDemo.html` evidence lookup and evidence panel | **A** | Canonical runtime presentation owner. It owns only client display behavior and visible evidence provenance. |
| `scripts/build_public_site.py`, Pages workflow, and stable worker packaging | **B** | Package the allowlisted public evidence runtime. They do not add a planner, semantic service, or authorization source. |
| Stable local `src/nma/knowledge.py`, `portrayal.py`, `api.py`, and `cli.py` v0.2 interfaces | **C** | Retained deterministic local interfaces. They do not own deployed ingress or production evidence authority. |
| Raw local/full-mode branches retained in stable browser lineage | **C** | Preserved local behavior; only the forced evidence-only built artifact is canonical production. |
| `data/knowledge/nma-canonical-graph-v0.4.json` | **D** | Large experimental semantic graph source. It is not the production graph, planner, evidence authority, or authorization source. |
| `src/nma/graphrag.py` and portrayal compile/review consumers | **D** | Experimental large-graph retrieval and derived-preview evidence assembly. No automatic rule activation or production ownership. |
| `src/nma/vector_index.py`, embedding cache/client, and vector build artifacts | **D** | Optional experimental ranking infrastructure. Similarity is candidate evidence, never semantic truth or authority. |
| Active retrieval ladder through `retrieval_v108.py` | **D** | Experimental local server retrieval owner. It cannot become a production planner, evidence authority, or executor by being the newest version. |
| Active entity-resolution helpers and current v106/v108 chain | **D** | Experimental candidate selection. Selected node IDs do not activate rules, authorize mutation, or become execution commands. |
| `runtime_graph_backend_v029.py` | **D** | Experimental backend selector. Its JSON/Neo4j parity policy does not make either backend production. |
| `neo4j_projection.py`, round-trip/retrieval helpers, optional driver, and scripts | **D** | Experimental verified projection of the large JSON graph. Neo4j is not a separate semantic authority. |
| Semantic candidate/review registries and large-graph citation/retrieval anchors | **D** | Experimental semantic evidence inputs; not imported or packaged by canonical production. |
| Superseded `retrieval_v105` concrete wrapper | **E** | Historical wrapper retained for tests/compatibility; no new caller may treat it as an owner. |
| Superseded entity/retrieval wrapper variants outside the selected experimental chain | **E** | Retained historical implementations pending a separately authorized retirement issue. |

### 5.1 Ownership conclusions

1. The public portrayal graph stays a small, stable, independent production evidence product.
2. The large JSON graph is not adapted into the public runtime and is not promoted.
3. GraphRAG, vector retrieval, Neo4j projection, the retrieval ladder, and entity resolution all
   remain experimental.
4. Neo4j can only be a verified projection of the large experimental JSON graph, never a separate
   authority.
5. Vector rank, model output, entity selection, and retrieval recency cannot confer production
   evidence ownership or authorization.
6. No semantic component becomes the canonical planner; `nma.intent-planning/1.0` remains the only
   canonical planning contract.

## 6. Evidence, proposal, authorization, and execution boundary

The preserved chain is:

```text
request
  -> nma.intent-planning/1.0 reasoning/planning
  -> read-only evidence lookup
  -> evidence-backed presentation proposal
  -> separately owned authorization
  -> separately owned execution
  -> verification/provenance
```

The proposal envelope contains exactly:

| Field | Allowed content |
|---|---|
| `schema` | Constant `nma.evidence-backed-proposal/1.0`. |
| `intent_reference` | The canonical planning contract version and deterministic plan hash. |
| `evidence_references` | A non-empty list of resolved proposal-purpose references. |
| `presentation` | `evidence_panel` or `portrayal_preview`, plus one seven-digit feature code. |
| `metadata` | Constant `boundary=proposal-only`. |

The builder accepts only a validated planning result whose disposition is `proposal` and whose
evidence intent is `required`. An abstention cannot be promoted. Exact nested field sets reject
authorization IDs, execution IDs, permission lists, mutation parameters, shell commands, paths,
API operations, ROAD authorization, School Hero execution, and any other added state.

An intent hash proves which plan was referenced. An evidence ID proves which immutable evidence
snapshot was referenced. Neither hash is a bearer token, approval, capability, permission, command,
receipt, or proof of execution.

ROAD authorization/execution remains owned only by the frozen ROAD chain. School Hero
authorization/execution remains owned only by the frozen School Hero chain. Public browser approval
remains a client presentation-state gate and cannot substitute for either domain.

## 7. Production and experimental dependency analysis

The evidence module is intentionally outside `src/nma`, following the accepted AGENT-02 contract
pattern. It imports only Python standard-library modules and the repository-level canonical planning
contract. It imports no `nma` package module, graph retriever, model client, vector index, Neo4j
driver, entity resolver, semantic service, ROAD module, School Hero module, or executor.

| Boundary | AGENT-02 | AGENT-03 | Result |
|---|---|---|---|
| `pyproject.toml` production dependencies | `[]` | `[]` | exact |
| `pyproject.toml` SHA-256 | `ccf4d084…9592d34` | `ccf4d084…9592d34` | exact |
| Built source `nmaAgentDemo.html` SHA-256 | `8b6d6310…5a470` | `8b6d6310…5a470` | exact |
| Public builder SHA-256 | `6f9e6e75…a50c55e` | `6f9e6e75…a50c55e` | exact |
| Public portrayal graph SHA-256 | `0f90dc36…eacca` | `0f90dc36…eacca` | exact |
| Public builder allowlist | frozen v0.2 set | frozen v0.2 set | exact |
| Installed `src/nma` inventory/content | accepted predecessor | unchanged | exact |
| GraphRAG/vector/Neo4j/entity external dependency | absent from production | absent from production | exact |

The new contract and schemas are architecture/verification artifacts. The public builder neither
imports nor publishes them. Production deployment behavior and dependency direction are unchanged.

## 8. Provenance and fail-closed validation

| Required behavior | Executable proof | Result |
|---|---|---|
| Same evidence has stable identity | Repeated complete-envelope construction is byte/identity equal. | PASS |
| Hash/version linkage deterministic | Source bytes, canonical payload, input bytes, and versioned envelope are hashed. | PASS |
| Changed evidence cannot keep old identity | Payload and source changes produce new IDs; forged old ID is rejected. | PASS |
| Evidence immutable/read-only | Frozen evidence and nested metadata reject mutation. | PASS |
| Missing evidence fails closed | Empty/missing registry raises; no generation or substitution hook exists. | PASS |
| Invalid evidence reference rejected | Unknown schema, malformed ID, unknown purpose, and unresolved ID raise. | PASS |
| Evidence-backed proposal requires evidence | Empty references and abstention promotion raise. | PASS |
| Authorization-like proposal fields rejected | Top-level and nested authority fields violate exact field sets. | PASS |
| Execution-like proposal fields rejected | Execution IDs, commands, mutation permissions, and domain substitutions violate exact field sets. | PASS |
| Schemas closed and meta-valid | Draft 2020-12 meta-schema checks pass; `additionalProperties=false`. | PASS |
| Experimental stacks isolated | Contract source imports none of GraphRAG/vector/Neo4j/retrieval/entity resolution. | PASS |
| Production dependency graph unchanged | Protected production hashes and empty core dependency list match. | PASS |

## 9. Complete validation results

| Validation | Result |
|---|---|
| Focused AGENT-03 evidence boundary | `18 passed` |
| AGENT-03 plus canonical AGENT-02 planning contract | `36 passed` |
| Agent/demo focused sweep | `98 passed, 3 known failed` |
| Exact known failures, repeat run | exactly the same 3 failed |
| New evidence/proposal schema and meta-schema checks | included in `18 passed`; PASS |
| Exact Core suite | `53 passed` |
| Complete ROAD historical suite | `199 passed` |
| Complete School Hero suite | `42 passed` |
| Full repository suite | `513 passed, 3 known failed` (516 total) |
| Ruff static checks | PASS |
| Ruff formatting | PASS |
| `git diff --check` | PASS |

The full-suite delta from AGENT-02 is exactly 18 new passing tests: `495 passed / 3 failed` became
`513 passed / 3 failed`. No test was weakened, skipped, xfailed, deleted, or changed to hide a
failure.

### 9.1 Accepted failures

The same three predecessor failures remain materially identical and outside the canonical
production path:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
   - same generated-versus-tracked PMTiles capability catalog assertion drift;
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
   - same `scripts/run_nma_agent_server.py size: expected 29586, got 133875` error;
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`
   - same `data/demo/pmtiles-capability-catalog.json size differs from the candidate manifest`
     error.

AGENT-03 does not modify the catalog, generator, server, demo freeze, Pages candidate, or manifest.
None of these failures affects evidence ownership, semantic ownership, or the canonical production
dependency graph. They remain reserved for a separately authorized evidence-refresh issue.

## 10. Frozen integrity

No Core, ROAD, or School Hero file differs from the accepted AGENT-02 predecessor.

| Frozen boundary | Evidence | Result |
|---|---|---|
| Core | Exact five-file acceptance suite, `53 passed` | PASS |
| ROAD | Exact ROAD-01 through ROAD-05 suite, `199 passed` | PASS |
| School Hero | Complete HERO-04/HERO-05/V032/intelligence suite, `42 passed` | PASS |
| Frozen boundary diff | Empty relative to `f8499fbe…` | PASS |
| Core provider/fallback residual audit | Included in Core suite | PASS |

Core source identities remain:

| File | SHA-256 |
|---|---|
| `src/nma/core/__init__.py` | `a3e410a77ece724eaf505ce8b9dc6694b808d4a7cc96a720500757578077a4f2` |
| `src/nma/core/feature_profile.py` | `e0de362e5f733f0f1d7d5776f830939922a6d66cc552e05186046ca0d71e09f0` |
| `src/nma/core/identity.py` | `d9c4ac0d0d385f6942c552a0b2ffc4c12b3deb0ee876d569aeadc036b1a92e78` |

## 11. Commit, remote equality, and worktree closure

The exact implementation validated by every suite is commit
`f85ab0f757244b4fa8b51f8672cbc5b6ae5c216a`.

The report-containing commit cannot embed its own Git object ID because that ID hashes this report;
embedding it would change the ID recursively. The exact final branch SHA is therefore recorded in
the GEO-134 completion evidence and final handoff after the report commit is created.

Completion requires these exact checks:

```text
git rev-parse HEAD
git rev-parse @{upstream}
git ls-remote origin refs/heads/agent/agent-03-evidence-semantic-boundary
git status --short --branch
```

Acceptance state at handoff must have local HEAD, upstream tracking ref, and remote branch equal,
with a clean final worktree. No PR is created.

## 12. Final recommendation

GEO-134 should close **PASS** after commit/push/SHA equality verification. Evidence ownership,
semantic ownership, proposal-only planning, production runtime identity, and frozen domain
authority are explicit and executable.

The next bounded Agent issue should address **evidence adapter parity and deterministic replay** only
if separately authorized. It may map the existing small public graph into `nma.agent-evidence/1.0`
references or add replay fixtures, but it must not unify graph architectures, add memory, promote
GraphRAG/vector/Neo4j/entity resolution, alter deployment, or connect generic Agent planning to ROAD
or School Hero execution.

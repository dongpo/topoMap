# AGENT-00 — Agentic Architecture Baseline & Boundary Audit

Audit date: 2026-08-19 (Asia/Taipei)

## 1. Verdict

**PASS — ARCHITECTURE BASELINED WITH FINDINGS**

The repository's Agent layer can be baselined reliably without changing production code or any
frozen HERO, ROAD, or CORE artifact. The authoritative frozen predecessor is intact and the exact
CORE acceptance suite passes.

The principal finding is not a Core defect. The repository contains several deliberately bounded
but parallel Agent architectures:

1. the stable v0.2 deterministic portrayal API/CLI and deployed evidence-only browser demo;
2. the local Agentic v0.31/v0.32 Responses API orchestration server;
3. a browser-side deterministic Agent router and execution coordinator used as a demo fallback;
4. an isolated HERO-01 deterministic intent planner that has no runtime caller;
5. domain-specific School intelligence, School Hero, ROAD, portrayal-review, real-layer, and QA
   paths with different orchestration and authorization contracts.

No production-reachable mutating action was found to bypass frozen canonical Core identity. The
only deployed production path is a static evidence-only Pages artifact and has no server-side
mutation capability. Frozen School Hero and ROAD execution use the exact Core provider. The local
experimental portrayal, real-layer, and QA routes do not share the frozen HERO/ROAD authorization
contract; they remain derived-output-only and explicitly approved, but promotion to production
must be blocked until that separate boundary is intentionally resolved.

The three known Agentic/demo failures reproduce deterministically and are stale demo/fingerprint
evidence, not Core regressions or production defects. No repair was attempted.

## 2. Baseline identity

| Item | Verified value | Result |
|---|---|---|
| Repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Audit checkout branch | `freeze/core-final-5eb138a` | PASS |
| HEAD | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Local freeze branch | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Upstream tracking ref | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Remote freeze branch | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Annotated tag object | `5729f2db0fc441b3eb0a22c1f76b0f6af3f368ea` | PASS |
| Peeled `nma-core-v1.0-final` target | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| CORE acceptance | `53 passed` | PASS |

Core source hashes match the freeze manifest exactly:

| File | SHA-256 |
|---|---|
| `src/nma/core/__init__.py` | `a3e410a77ece724eaf505ce8b9dc6694b808d4a7cc96a720500757578077a4f2` |
| `src/nma/core/feature_profile.py` | `e0de362e5f733f0f1d7d5776f830939922a6d66cc552e05186046ca0d71e09f0` |
| `src/nma/core/identity.py` | `d9c4ac0d0d385f6942c552a0b2ffc4c12b3deb0ee876d569aeadc036b1a92e78` |

Remote refs were checked directly with `git ls-remote`; the tag object and peeled target match the
local objects.

## 3. Repository state

- Starting worktree: clean.
- Starting branch and upstream: `freeze/core-final-5eb138a` and
  `origin/freeze/core-final-5eb138a`.
- Python: 3.11.9.
- pytest: 8.3.3.
- Packaging status: project version 0.2.0, development classifier `Alpha`.
- Public deployment: `.github/workflows/static.yml` builds only the bounded v0.2 static Pages
  artifact from `scripts/build_public_site.py`.
- Agentic v0.3 status: the README and `docs/AGENTIC-V0.3-FREEZE.md` explicitly say candidate,
  separate from stable v0.2, and not deployed.
- Local optional runtime dependencies present during audit: `ogrinfo`, `ogr2ogr`, and the ignored,
  untracked private source archive. No external model or Neo4j call was required for the audit.
- No repository-local `AGENTS.md` was present.

Status terms in this report mean:

- **PRODUCTION**: deployed or stable public release path.
- **PRODUCTION-SUPPORT**: documented stable package/runtime support used to build, serve, or verify
  the production release, but not itself a deployed service.
- **EXPERIMENTAL**: executable locally and materially integrated, but explicitly outside the
  deployed stable boundary.
- **DEMO**: presentation/reproduction path whose purpose is demonstrative.
- **TEST-ONLY**: no non-test runtime caller was found.
- **LEGACY**: retained and reachable or imported for compatibility/history, but superseded by a
  newer path.
- **DEAD/UNREACHABLE**: no runtime or test caller was found.
- **UNCERTAIN**: evidence cannot distinguish intended state. No material component required this
  classification.

## 4. Agent component inventory

The table lists every materially relevant Agent component or tightly coupled component group. A
range denotes a version chain whose files are individually named in the range description.

| File/module | Primary responsibility | Callers | Downstream dependencies | Core / ROAD / School dependency | External dependency | Runtime reachability | Status |
|---|---|---|---|---|---|---|---|
| `nmaAgentDemo.html` | Stable five-scene browser UI; deterministic catalog/graph lookup, portrayal, approval UI, and MapLibre rendering | Public Pages `index.html`; local HTTP servers | portrayal graph, demo contract, catalog, MapLibre/PMTiles/NLSC | No Core; no ROAD; School is a demo scene | Browser CDNs, NLSC WMTS, optional PMTiles | Deployed after `build_public_site.py` forces evidence-only mode; richer local mode remains reachable | PRODUCTION |
| `nmaDemoWorker.js` | Offline asset/cache support for stable demo | `nmaAgentDemo.html` | static assets/cache | None | Browser service worker | Public/local browser | PRODUCTION-SUPPORT |
| `scripts/build_public_site.py` | Builds the bounded stable Pages payload and excludes PMTiles/server secrets | Pages workflow, release tests | stable HTML, graph, catalog, assets | None | Filesystem only | Main-branch Pages deployment | PRODUCTION-SUPPORT |
| `src/nma/cli.py`, `src/nma/api.py` | Installed `nma` commands and dependency-free local JSON API | `nma` console script; local operator | `knowledge`, `portrayal`, validator/demo modules | No direct Core/ROAD/School dependency | HTTP server; GDAL only for other CLI commands | Documented stable v0.2 local interface | PRODUCTION-SUPPORT |
| `src/nma/knowledge.py` | Compiles and loads the small executable portrayal graph | CLI, demo contract, tests | reviewed records/profile JSON | No Core | Filesystem | Stable package path | PRODUCTION-SUPPORT |
| `src/nma/portrayal.py` | Deterministic `PortrayalAgent`, profile/scale/exception guards, answer projection, MapLibre compilation | CLI/API, demo contract, benchmark | `PortrayalGraph` | No Core | None | Stable package path | PRODUCTION-SUPPORT |
| `src/nma/demo_contract.py`, `demo_freeze.py`, `demo_soak.py`, `demo_offline.py`, `demo_backup.py`, `demo_rc1.py`, `agentic_freeze.py` | Demo reconstruction, freeze, soak, offline, backup, and candidate checks | CLI/Makefile/tests | stable/candidate manifests and artifacts | No Core provider responsibility | Filesystem, Git for historical checks | Verification only; some currently fail on stale Agentic fingerprints | DEMO |
| `src/nma/graphrag.py` | Deterministic lexical/alias search and bounded typed graph expansion over the larger canonical graph | retrieval chain, Neo4j parity, tests | canonical graph JSON | No direct Core | None | Local experimental server and tools | EXPERIMENTAL |
| `src/nma/vector_index.py` | OpenAI embedding client, vector index, query cache, hybrid retrieval | local Agent server, index builder, retrieval v0.5+ | `graphrag` | File/query hashing is domain-specific; no ROAD/School | OpenAI Embeddings API | Local server when semantic retrieval is invoked | EXPERIMENTAL |
| `src/nma/retrieval_v05.py`, `retrieval_v06.py`, `retrieval_v07.py`, `retrieval_v08.py`, `retrieval_v09.py`, `retrieval_v101.py` | Layered hybrid retrieval, citation integrity, deterministic semantic-link policy, source grounding, reviewed support | later retrieval versions, server loaders, tests | vector index, canonical retriever, registries | No direct Core | Embedding callback | Transitively active under v108; some concrete classes are superseded but their modules remain active | EXPERIMENTAL |
| `src/nma/retrieval_v105.py` | v0.10.5 policy-validated retrieval | tests; imported but not instantiated by current server | v101 and entity v105 | Core transitively through entity identity | Resolver callback | Current server imports class/error but v108 is instantiated | LEGACY |
| `src/nma/retrieval_v108.py` | Current segment-aware candidate pool, resolver handoff, typed graph package | `retrieve_evidence()` in local Agent server | v101, entity v108, resolver/cache | Core transitively via entity candidate-pool identity | OpenAI through injected embedding/resolver clients | Live local v0.31/v0.32 path | EXPERIMENTAL |
| `src/nma/entity_resolution_v10.py`, `entity_resolution_v101.py`, `entity_resolution_v106.py` | Candidate construction, strict Responses API entity resolution, policy wrapper, caches | retrieval chain/local server/tests | vector index and policy helpers | Exact `nma.core.canonical_sha256` for candidate-pool identities | OpenAI Responses API | v106 client/wrapper is current; v10/v101 supply shared code/loaders | EXPERIMENTAL |
| `src/nma/entity_resolution_v102.py`, `v103.py`, `v104.py`, `v105.py`, `v107.py`, `v108.py` | Successive hierarchy, multi-entity, source-discriminator, segmentation, and cap policies | v106/v108 chain and tests | preceding entity versions | Exact Core hash imported through v10 where content identity is required | Embedding cache callback | Helper functions are active transitively; superseded wrappers remain within active modules | EXPERIMENTAL |
| `src/nma/runtime_graph_backend_v029.py` | Chooses canonical JSON or Neo4j, verifies structural parity, exposes fallback trace | local Agent server, runtime tools/tests | retrieval v06, Neo4j adapter | Neo4j adapter consumes Core identity; local `_canonical_json` is serialization-only | Optional Neo4j | Local server initialization | EXPERIMENTAL |
| `src/nma/neo4j_projection.py`, `neo4j_roundtrip_v027.py`, `neo4j_retrieval_v028.py` | Projection, round-trip/parity, typed live retrieval | runtime backend and scripts/tests | canonical graph | v028 uses exact Core `canonical_sha256` | Optional Neo4j | Adapter/tool path; not required by stable production | EXPERIMENTAL |
| `src/nma/agentic_vs1.py` | Grounded-answer schema, parser, usage, and trace validation | local Agent server/tests | typed evidence package | No direct Core; trusts package identifiers from canonical retrieval | Responses API response object | `/api/agent` inspection and zero-credit School evidence | EXPERIMENTAL |
| `src/nma/agentic_vs2.py` | Bounded portrayal planning payload/parser | local Agent server/tests | portrayal-review validation | No Core/ROAD/School | OpenAI Responses API via server | `/api/portrayal-review` | EXPERIMENTAL |
| `src/nma/agentic_vs3.py` | Bounded real-layer planning payload/parser | local Agent server/tests | real-layer reviewed profile | No direct Core | OpenAI Responses API via server; GDAL downstream | `/api/real-layer` | EXPERIMENTAL |
| `src/nma/agentic_vs4.py` | Bounded QA explanation/planning payload/parser | local Agent server | QA plan/evidence | No direct Core | OpenAI Responses API via server; GDAL downstream | Direct `/api/qa-review`; no browser caller and no focused tests found | EXPERIMENTAL |
| `src/nma/intent_planning_v05.py` | Deterministic non-executing HERO-01 intent plan | tests and HERO verification test only | None | No Core/ROAD/School | None | No runtime import or API route | TEST-ONLY |
| `src/nma/portrayal_review.py`, `portrayal_compile.py`, `maplibre_adapter.py` | Immutable official baseline, derived edit proposal, preview compilation, MapLibre adapter | Agent server and tests | reviewed recipe/evidence package | No Core; no ROAD/School | None | Local portrayal-review routes | EXPERIMENTAL |
| `src/nma/real_layer.py` | Read-only archive inspection, exact reviewed plan, approved GDAL conversion to derived GeoJSON | Agent server and tests | reviewed profiles/evidence | Local plan identity is an accepted domain rule, not a generic provider | GDAL/OGR, private archive | Local real-layer routes | EXPERIMENTAL |
| `src/nma/qa_review.py` | Deterministic diagnosis, bounded repair plan, approved derived-copy repair and reinspection | Agent server | validator/specification, real-layer file tools | Local QA plan identity is an accepted domain rule | GDAL-related datasets/files | Direct local QA routes; no browser caller found | EXPERIMENTAL |
| `src/nma/agents/school_agent/discovery.py`, `reasoning.py`, `evidence.py`, `proposal.py` | Deterministic correlation of NMA, OSM, and official School data into update proposals | `/api/school-agent/analyze`, tests | three data connectors | No Core/ROAD; logically School-domain but separate from frozen School Hero execution | Local/provider-prepared datasets | Direct local API; not wired through `/api/agent` | EXPERIMENTAL |
| `src/nma/school_hero_execution.py`, `school_hero_verification.py` | Frozen authorization consumption, durable execution, observation, rollback, QA/provenance | dedicated local server routes and Hero tests | real-layer tools, frozen Hero artifacts | Direct exact Core provider | GDAL/OGR, private archive | Local capability routes | PRODUCTION-SUPPORT |
| `src/nma/road_resolution.py`, `road_portrayal_decision.py`, `road_approval.py`, `road_execution.py`, `road_verification.py`, `road_authorization_consumption.py` | Frozen ROAD resolve/propose/authorize/execute/observe/rollback chain | dedicated local server routes and ROAD tests | frozen ROAD artifacts | Exact Core provider transitively through `road_resolution` | GDAL/OGR, private archive | Local capability routes | PRODUCTION-SUPPORT |
| `scripts/run_nma_agent_server.py` | Local static server, all experimental Agent APIs, proposal/session stores, model calls, semantic spine, tool dispatch | local operator and demo HTML | all VS1–VS4, retrieval, portrayal/real-layer/QA, School Hero, ROAD | Core only through downstream components | OpenAI, Neo4j, GDAL, local datasets | Executable local server; not deployed by Pages | DEMO |
| `scripts/build_pmtiles_capability_catalog.py` | Rebuilds demo capability catalog | tests/operator | `pmtilesDemo.html`, portrayal graph | None | Filesystem | Build path; currently drifts from tracked catalog | DEMO |
| `scripts/build_nma_agentic_v031_demo.py`, `build_nma_agentic_v032_demo.py` | Deterministically derive v0.31 and v0.32 HTML/workers | tests/operator | prior HTML/worker versions | None | Filesystem | Build path | DEMO |
| `scripts/build_agentic_v03_pages.py`, `check_agentic_v03_pages.py`, `check_agentic_v03_freeze.py` | Candidate Pages/freeze materialization and verification | tests/Makefile | candidate manifests and historical Git snapshots | None | Git/filesystem | Candidate verification; two known failures | DEMO |
| `scripts/build_nma_vector_index_v04.py`, `build_nma_neo4j_projection_v04.py`, `run_nma_neo4j_roundtrip_v027.py`, `run_nma_neo4j_retrieval_parity_v028.py`, `run_nma_runtime_graph_backend_v029.py`, `run_nma_v032_external_runtime_refresh.sh` | Offline/live semantic and graph build/parity utilities | operator/runbook/tests | graph/vector/Neo4j modules | runtime script uses exact Core hash for package identity | OpenAI and/or Neo4j | Operator-only tooling | EXPERIMENTAL |
| `scripts/verify_school_hero_execution.py`, `verify_road_execution.py`, `verify_road_authorization_consumption.py` | Frozen execution verification wrappers | operator/acceptance | frozen engines/verifiers | Exact Core transitively | GDAL/archive as applicable | Acceptance tooling | PRODUCTION-SUPPORT |
| `nmaAgentDemoV04.html`, `nmaDemoWorkerV04.js` | Preserved pre-v0.31 Agentic demo | local server; v031 builder source | local Agent APIs/static graph | None | Browser services | Explicitly advertised as preserved | LEGACY |
| `nmaAgentDemoV031.html`, `nmaDemoWorkerV031.js` | Verified-runtime-spine demo and source for v032 | local server; v032 builder | `/api/agent` and experimental routes | None directly | Browser services | Explicitly advertised; superseded by v032 | LEGACY |
| `nmaAgentDemoV032.html`, `nmaDemoWorkerV032.js` | Current School Hero demo with server proposal IDs, two approval gates, verified real geometry | local server/tests | `/api/agent`, portrayal, real-layer, zero-credit evidence | Frozen Hero execution is separate, not used by this UI flow | Browser services, local server | Main local demo | DEMO |
| `benchmark/adapters/openai_compatible.py`, `src/nma/portrayal_bench.py` | Optional external-model and deterministic benchmark comparisons | benchmark CLI/operator | portrayal graph/agent | No Core | OpenAI-compatible endpoint | Explicit experiment, not correctness dependency | EXPERIMENTAL |
| Agent/semantic/ROAD/HERO test files under `tests/` | Contract, route, demo, Core identity, frozen execution, and reproducibility evidence | pytest | modules above | Test consumers | Some conditionally use GDAL/archive | Test runner only | TEST-ONLY |

No materially relevant Agent file was classified `DEAD/UNREACHABLE`. Superseded classes and pages
remain import-, test-, builder-, or URL-reachable and are therefore `LEGACY`, not dead.

## 5. Runtime entry points

| Entry point | Boundary | Reachable result |
|---|---|---|
| GitHub Pages workflow on `main` | `build_public_site.py` | Stable v0.2 evidence-only static demo; no Agent backend |
| `nma ask`, `nma portray`, `nma compile-style` | `nma.cli:main` | Deterministic portrayal answer/decision/style |
| `nma serve` | `nma.api:serve` | Local v0.2 JSON endpoints `/v1/agent/ask` and `/v1/agent/portray` |
| `nma-bench` | `nma.portrayal_bench:main` | Deterministic benchmark; optional model experiment elsewhere |
| `python scripts/run_nma_agent_server.py` | `NMARequestHandler` | Static V04/V031/V032 pages and local `/api/*` Agent/tool routes |
| Direct browser open of `nmaAgentDemo.html` | embedded JavaScript | Stable/local deterministic graph and fallback behavior |
| `make agentic-freeze` | freeze checker | Candidate fingerprint verification; currently fails |
| `scripts/build_*` / `scripts/run_*` graph utilities | operator CLI | Vector/Neo4j build, parity, and external runtime evidence |

There is no deployed production Agent API server in the repository's deployment workflow.

## 6. Execution-path map

### P1 — deployed stable browser path

```text
User click/question
  -> embedded deterministic browser routing/search
  -> portrayal-graph.json + five-scene-demo.json + capability catalog
  -> client-side portrayal decision/evidence panel
  -> evidence-only display (Pages forces degraded mode)
  -> no server execution, durable write, or source mutation
```

Reference-model mapping: interpretation is deterministic JavaScript; planning is a bounded UI
choice; knowledge is the small portrayal graph/catalog; authorization is browser state for derived
preview only; execution is display/map state; observation and verification are the evidence panel
and frozen demo contracts.

### P2 — stable local v0.2 API/CLI path

```text
CLI command or explicit HTTP route
  -> command/path dispatch
  -> PortrayalGraph.find_features
  -> PortrayalAgent.answer or select_symbol
  -> profile + scale + exception guards
  -> structured decision / MapLibre layer response
```

There is no model call, autonomous loop, task decomposition, or durable request-driven mutation.

### P3 — local Agentic v0.31/v0.32 conversational path

```text
Browser message
  -> POST /api/agent
  -> Responses API route_nma_turn (one strict tool call)
  -> validate_route
  -> for inspection: embedding + v108 candidate pool
       -> deterministic precedence or v106 LLM entity resolver
       -> canonical JSON or verified Neo4j typed graph expansion
       -> local reviewed School fact projection or second grounded-answer model call
       -> strict identifier/citation validation and trace
  -> route returned to browser
  -> browser executeAgentRoute applies UI state or invokes a domain API
  -> tool result returned on the next conversational turn
```

Orchestration begins twice: server-side at `orchestrate()` for model/retrieval work and client-side
at `executeAgentRoute()` for tool execution. It ends only after the browser has applied or rejected
the returned route. This split ownership is a material architecture finding.

### P4 — local portrayal-review path

```text
POST /api/portrayal-review
  -> reviewed immutable baseline + semantic evidence
  -> LLM plan, or deterministic translation of router SymbolEditPlan
  -> strict plan/evidence validation
  -> in-memory pending proposal
  -> POST decision {proposal_id, approve|discard}
  -> approved preview compile
  -> optional MapLibre adapter response
```

Only a derived preview is produced; official rule activation remains blocked.

### P5 — local real-layer path

```text
POST /api/real-layer
  -> semantic evidence -> strict LLM mapping selection
  -> read-only checksum-bound GDAL inspection -> pending proposal
  -> POST /api/real-layer/execute {proposal_id, decision: approve}
  -> exact plan revalidation + source checksum check
  -> GDAL derived GeoJSON -> observation + QA + citations
  -> browser verifies QA/provenance before adding a map source/layer
```

### P6 — local QA path

```text
POST /api/qa-review
  -> semantic evidence -> deterministic diagnosis
  -> strict LLM explanation of fixed observations/repairs
  -> pending proposal
  -> POST /api/qa-review/execute {proposal_id, decision: approve}
  -> exact plan/source/specification revalidation
  -> derived copy repair -> reinspection + audit
```

The route is directly API-reachable but no browser caller or focused VS4 test was found.

### P7 — School intelligence path

```text
POST /api/school-agent/analyze {administrative_area}
  -> discover NMA + OSM + official registry features
  -> deterministic spatial/administrative/semantic/attribute matching
  -> require evidence from two source types
  -> JSON-LD-compatible update proposals
```

This path is proposal-only and is not connected to `/api/agent` or frozen School Hero execution.

### P8 — frozen School Hero and ROAD capability paths

```text
Dedicated execution POST with authorization_id + idempotency_key
  -> stored authorization load
  -> frozen scope/hash/source verification through Core identity
  -> atomic derived execution + receipt/bundle/consumption records
  -> dedicated observe/read/rollback routes
```

These paths begin at dedicated API endpoints, not at the conversational Agent router.

## 7. Intent/planning architecture

Multiple intent/planning paths exist:

| Path | Implementation | Model | Runtime state | Execution authority |
|---|---|---|---|---|
| v0.2 question interpretation | `PortrayalAgent.answer()` and graph lexical matching | None | None | Read-only answer/decision |
| HERO-01 deterministic plan | `intent_planning_v05.plan_intent()` | None | None | Explicit `no_execution`; test-only |
| Conversational route | server `INSTRUCTIONS`, `ROUTE_TOOL`, `parse_openai_route()` | OpenAI Responses API | response ID, pending call ID, max 8 turns | Proposes one route only |
| Browser fallback route | `deterministicRoute()` embedded in V04/V031/V032/stable source | None | browser workshop/layer state | Client coordinator invokes bounded APIs |
| Portrayal plan | `agentic_vs2` or `translate_symbol_edit_plan()` | Optional | proposal store | Derived preview after approval |
| Real-layer plan | `agentic_vs3` + `real_layer.propose_real_layer()` | OpenAI plus deterministic inspection | proposal store | Derived GeoJSON after approval |
| QA plan | `agentic_vs4` + deterministic diagnosis | OpenAI plus deterministic inspection | proposal store | Derived repair after approval |
| School intelligence | `agents.school_agent` | None | None | Proposal-only |
| ROAD resolution/planning | frozen ROAD-01/02/03 modules | None | frozen artifacts | Separate stored capability |

There is no generic autonomous planner or recursive agent loop. The closest loop is a bounded
multi-turn Responses API continuation controlled by browser-returned tool observations. No retry or
backoff loop was found in model invocation code.

Finding: intent definitions are duplicated across server prompt/schema, browser deterministic
fallback, the isolated HERO-01 planner, and domain planners. The browser/server pair intentionally
duplicates route semantics for fallback, but there is no single executable contract proving their
semantic equivalence.

## 8. Semantic/knowledge architecture

Four parallel knowledge paths are material:

1. **Small portrayal graph** — `data/knowledge/portrayal-graph.json`, loaded by
   `PortrayalGraph`; deterministic exact/name/alias matching for stable v0.2.
2. **Large canonical graph** — `data/knowledge/nma-canonical-graph-v0.4.json`, loaded by
   `CanonicalGraphRetriever`; typed expansion and citations for experimental Agentic flows.
3. **Hybrid semantic stack** — vector index, retrieval v05–v108, approved semantic links,
   resolution support, query embeddings, and v106 structured entity resolution. It resolves only
   allowlisted candidate IDs and does not activate rules.
4. **Neo4j projection** — optional structural mirror of the large canonical graph. The runtime can
   fall back visibly to canonical JSON; arbitrary Cypher is not exposed to the model.

Additional bounded domain knowledge exists in the capability catalog, portrayal recipes, real
layer/QA profiles, the three School intelligence datasets, and frozen ROAD/HERO artifacts.

The stable portrayal graph and experimental canonical graph are not one runtime abstraction. They
have different schemas, retrievers, callers, and deployment states. This is parallel semantic
architecture, not merely two storage backends. The Neo4j path, by contrast, is a backend variant of
the larger canonical graph and is structurally checked against it.

## 9. Core consumption map

| Consumer | Core consumption |
|---|---|
| Entity resolution v10/v101/v103/v105/v107/v108 | Candidate-pool content identities resolve to the exact `nma.core.canonical_sha256` object imported by v10 |
| Neo4j retrieval v028 | Package identity uses exact Core `canonical_sha256`; runtime backend consumes v028 transitively |
| School Hero execution/verification | Direct exact imports of `canonical_json` and `canonical_sha256` for authorizations, plans, records, receipts, bundles, QA, and provenance |
| ROAD resolution/decision/approval/execution/verification | `road_resolution` imports exact Core functions; downstream ROAD modules consume them transitively |
| Runtime graph utility script | Imports exact Core `canonical_sha256` for its package identity |
| Agentic VS1–VS4 | No direct identity provider; consumes already identified evidence/plan objects |
| Stable `PortrayalAgent` | No Core dependency; deterministic read-only portrayal decisions predate the frozen identity boundary |
| Portrayal review | No generic content identity; proposal store identity is time-salted domain state |
| Real-layer and QA | Local plan-ID rules were explicitly classified by CORE-04 as domain-specific, not generic provider copies |

The exact-object assertions and repository-wide provider discovery are covered by the passing CORE
suite. Missing Core fails closed without reconstructing, stubbing, or mutating a checkout.

## 10. Authorization boundary analysis

| Action | Reachability/status | Authorization/policy gate | Core identity | Finding |
|---|---|---|---|---|
| Stable Pages evidence display/client map state | PRODUCTION | Bounded evidence-only build and browser state | Not required; no durable mutation | No bypass |
| v0.2 ask/portray API | PRODUCTION-SUPPORT | Explicit route plus deterministic profile/scale/exception guards | Not required; read-only | No bypass |
| Portrayal derived preview | EXPERIMENTAL | Exact proposal ID, separate approve/discard, approved-for-preview state, immutable baseline | No; domain proposal state | No source/official mutation; separate architecture |
| Real-layer derived GeoJSON | EXPERIMENTAL | Request must contain only exact proposal ID and `decision: approve`; plan ID and source hashes revalidated | Domain plan hash, not Core | No production bypass; promotion requires convergence decision |
| QA derived-copy repair | EXPERIMENTAL | Exact proposal ID and `decision: approve`; plan, source, and specification revalidated | Domain plan hash, not Core | No production bypass; no UI caller found |
| School Hero durable execution | PRODUCTION-SUPPORT local route | Stored frozen authorization, exact client field set, idempotency, atomic execution | Exact Core | No bypass |
| ROAD durable execution | PRODUCTION-SUPPORT local route | Stored frozen authorization, exact client field set, idempotency/consumption ledger, atomic execution | Exact Core | No bypass |

Result: **no production-reachable mutating bypass exists**. The deployed artifact cannot call a
deployed mutation service because none is shipped. Every durable frozen HERO/ROAD mutation path
uses Core.

Finding: the local Agent server exposes experimental derived-output mutation endpoints alongside
frozen capability endpoints, but they do not share one authorization abstraction. Their explicit
approval and exact-plan checks are real, not labels, yet they must not be treated as equivalent to
frozen canonical authorization without a future, separately authorized decision.

## 11. Duplicate/fallback provider audit

The passing CORE audit establishes:

- residual generic identity provider definitions outside Core: **0**;
- Core import fallback/stub/auto-repair providers: **0**;
- missing-Core behavior: deterministic fail-closed with no mutation;
- School and ROAD generic identity objects: exact Core objects.

No Agent-layer compatibility identity provider, embedded Core copy, or provider fallback was
found. The following are not duplicate Core providers and were already explicitly classified by
CORE-04:

- serialization-only `_canonical_json` helpers used for stable ordering/comparison;
- raw file/member/query/idempotency SHA-256 rules;
- time-salted in-memory proposal IDs;
- bounded real-layer and QA plan-ID rules;
- persisted-file byte hashes.

Non-identity runtime fallbacks do exist:

- browser deterministic intent/SymbolEditPlan fallback when the Agent server/model is unavailable;
- canonical JSON graph fallback when Neo4j is unavailable or mismatched and fallback is enabled;
- zero-credit reviewed School fact projection and School SymbolEditPlan translation;
- local PMTiles/evidence-only browser fallbacks;
- service-worker cache fallback.

These are visible in traces/UI and do not reconstruct Core. There is no alternate model provider in
the live Agent server. The benchmark alone supports an optional OpenAI-compatible endpoint.

Finding: model invocation is implemented independently in the server route/answer client, vector
embedding client, and several entity resolver versions. This is duplicate transport/error-handling
architecture, not duplicate identity logic.

## 12. Legacy/demo/experimental classification

- Stable production is the bounded v0.2 static evidence-only Pages artifact.
- Stable local package support is `nma.cli`, `nma.api`, `knowledge`, and `portrayal`.
- V04 and V031 pages/workers are retained legacy demo versions. They remain reachable and are
  builder inputs, so they are not dead.
- V032 is the current local School Hero demo, not deployed production.
- The semantic v0.31/v0.32 server, VS1–VS4, vector/Neo4j stack, portrayal review, real layer, QA,
  and School intelligence are experimental.
- Frozen School Hero and ROAD execution are production-support trust-boundary components exposed
  through the local demo server, not conversational Agent tools.
- `intent_planning_v05` is test-only and disconnected from runtime.
- Older retrieval/entity wrappers and caches are legacy where superseded; shared helper functions
  remain transitively active.
- No material file is dead/unreachable. No classification remains uncertain.

## 13. Three pre-existing failure analysis

All three were run twice as a focused set and once in the complete suite. Signatures were stable.

### Failure 1 — capability catalog reproducibility

- Node ID: `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
- Exact error class: `AssertionError`
- Exact functional message/diff: generated capability `9920103` has editable parameters
  `[scale, color, stroke_width, outline, opacity, rotation, flag_top_alignment, support_shape,
  support_proportion, flag_attachment]`; tracked expected catalog adds
  `flagpole_horizontal_alignment`.
- Component classification: DEMO.
- Production reachability: the tracked catalog is shipped by the stable Pages builder, but the
  failing operation is a build reproducibility assertion; the public evidence-only runtime does
  not execute the generator.
- Core relation: none; no Core identity path is entered.
- Agent relation: v0.32 added centered School flagpole semantics in HTML/tracked catalog without
  synchronizing the catalog generator's derivation source.
- Deterministic: yes, reproduced twice and in the full suite.
- Classification: **stale demo/generated-artifact code**, with architectural evidence drift; not a
  genuine production behavior defect.

### Failure 2 — Agentic v0.3 freeze fingerprint

- Node ID:
  `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
- Exact error class/message: `ValueError: scripts/run_nma_agent_server.py size: expected 29586,
  got 133875`.
- Component classification: DEMO.
- Production reachability: none; Agentic v0.3 is explicitly not deployed and the stable Pages
  builder does not ship this server.
- Core relation: none; failure occurs in manifest size verification before runtime identity work.
- Agent relation: the v0.3 freeze still fingerprints the earlier 29,586-byte server while later
  v0.31/v0.32, School Hero, and ROAD integration expanded the same file.
- Deterministic: yes, reproduced twice and in the full suite.
- Classification: **stale demo freeze evidence / architecture debt**, not environment dependency or
  production defect.

### Failure 3 — Agentic v0.3 Pages candidate fingerprint

- Node ID:
  `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`
- Exact error class/message: `ValueError: data/demo/pmtiles-capability-catalog.json size differs from
  the candidate manifest`.
- Observed values: candidate manifest expects 25,780 bytes; tracked catalog is 25,821 bytes.
- Component classification: DEMO.
- Production reachability: none; this is the separate Agentic candidate builder, not the stable
  Pages workflow.
- Core relation: none; source-asset size verification fails before build/runtime identity work.
- Agent relation: downstream fingerprint drift from the tracked catalog update described in
  Failure 1.
- Deterministic: yes, reproduced twice and in the full suite.
- Classification: **stale demo candidate manifest**, not environment dependency or genuine
  production defect.

These are the same three node IDs and materially identical signatures recorded by CORE-FINAL
against CORE-03. AGENT-00 did not repair them.

## 14. Architectural risks

1. **Split orchestration ownership.** `/api/agent` proposes routes, while embedded browser code
   executes them and invokes other APIs. Direct callers can bypass browser-only sequencing even
   though server endpoints retain their own exact approval checks.
2. **Parallel production/candidate Agent stacks.** Stable portrayal and experimental canonical
   GraphRAG have different graph schemas, retrieval logic, and API surfaces.
3. **Duplicated intent contracts.** Model router, browser deterministic fallback, HERO-01 planner,
   and domain planners can drift; the catalog failure demonstrates adjacent artifact drift already.
4. **Single large demo server.** `run_nma_agent_server.py` owns HTTP routing, model transport,
   sessions, semantic assembly, proposal stores, domain orchestration, frozen execution adapters,
   and static serving in 133,875 bytes.
5. **Version-ladder ambiguity.** Many retrieval/entity versions remain transitively active while
   superseded classes are still imported or tested. Current live instantiation is v108 + v106, but
   ownership is not apparent from filenames alone.
6. **Authorization heterogeneity.** Experimental derived-output approvals are valid but are not the
   frozen HERO/ROAD capability architecture. Accidental promotion could overstate equivalence.
7. **Unlinked VS4 path.** QA orchestration is directly API-reachable, has no browser caller, and has
   no focused `agentic_vs4` test, increasing the risk of an unobserved contract drift.
8. **Multiple direct OpenAI clients.** Route/answer, embeddings, and entity resolution repeat
   transport and error behavior with no shared retry policy. No retry currently means failures are
   generally fail-closed, but behavior differs by caller.
9. **Stale release evidence.** Three deterministic failures show the v0.3 freeze and candidate
   fingerprints no longer describe the current local Agent server/demo artifacts.
10. **In-memory proposal state.** Portrayal, real-layer, and QA proposal stores are process-local,
    time-limited, and non-replayable after restart; frozen HERO/ROAD use durable artifacts instead.

## 15. Recommended bounded follow-up sequence

Only evidence-supported follow-ups are recommended. Each must be a separate issue and must preserve
the frozen Core boundary unless separately authorized.

1. **AGENT-01 — Runtime ownership and production boundary decision.** Select and document one
   canonical Agent entry point for future production work; explicitly classify the stable v0.2
   portrayal API, `/api/agent`, browser coordinator, and dedicated frozen capability routes. Do not
   add features. This is the immediate recommendation.
2. **AGENT-02 — Intent/planning contract consolidation.** After AGENT-01, establish one versioned
   route/plan contract and executable parity tests for model and deterministic implementations;
   decide whether `intent_planning_v05` is adopted or retired.
3. **AGENT-03 — Canonical semantic/KG access boundary.** Decide whether the small portrayal graph
   remains a stable independent product or is adapted behind the larger canonical graph contract;
   retain JSON/Neo4j as backend variants, not separate semantic authorities.
4. **AGENT-04 — Authorization enforcement for any promoted Agent tools.** Before any experimental
   mutation endpoint becomes production-reachable, bind it to an explicitly approved capability
   architecture or document why its derived-only domain contract is sufficient. Preserve frozen
   School Hero/ROAD behavior.
5. **AGENT-05 — Legacy/demo retirement and evidence refresh.** Separately decide which V04/V031,
   old resolver/retriever classes, unused imports, and candidate manifests remain supported; repair
   the three failures only in that authorized issue.
6. **AGENT-06 — Observability and deterministic replay.** If the selected runtime needs production
   operation, replace process-local trace/proposal history with bounded receipts and replay evidence
   without exposing hidden reasoning.
7. **AGENT-07 — Agent API stabilization.** Only after the prior decisions, define deployment,
   authentication, persistence, error, retry, and compatibility policy for a production Agent API.

Agent memory architecture is not recommended yet: current state is bounded continuation IDs and
short-lived proposal stores, and the runtime ownership decision must precede a memory design. Tool
orchestration is covered by AGENT-01/02/04 rather than proposed as an independent feature issue.

## 16. Files changed

Exactly one audit artifact was added:

1. `AGENT-00-Architecture-Audit.md` — this report.

Production source changes: **ZERO**.

Frozen HERO / ROAD / CORE artifact changes: **ZERO**.

New tests or production modules: **ZERO**.

## 17. Test evidence

| Command/evidence | Result |
|---|---|
| Exact CORE-01 through CORE-04 suite | `53 passed in 6.70s` |
| Focused three known failures, first run | exactly 3 failed with expected signatures |
| Focused three known failures, second run | exactly the same 3 failed in 0.08s |
| Full pytest collection | `480 tests collected` |
| Full pytest execution | `477 passed, 3 failed`; only the three recorded node IDs failed |
| Remote freeze branch/tag verification | branch and peeled tag equal CORE-FINAL |
| Core source SHA-256 comparison | all three files exact |
| Generic identity/fallback audit | residual providers 0; fallback/stub providers 0 |

Exact CORE command:

```text
PYTHONPATH=src python3 -m pytest -o addopts='' -q \
  tests/test_core01_identity.py \
  tests/test_core01_feature_profiles.py \
  tests/test_core02_road_identity_adoption.py \
  tests/test_core03_school_hero_identity_adoption.py \
  tests/test_core04_residual_identity_audit.py
```

No focused AGENT-00 test was added: existing executable contracts and repository/static reachability
evidence were sufficient, and adding a new test was not necessary to establish an architectural
fact.

## 18. Final repository state

- HEAD remains `5eb138ae7686502431587743ebce9ddf92c5a799`.
- Branch/upstream remain the frozen CORE-FINAL branch.
- Only `AGENT-00-Architecture-Audit.md` is an authorized AGENT-00 worktree addition.
- No tracked production, test, data, schema, demo, HERO, ROAD, or CORE file changed.
- The ignored private archive remains untracked and unstaged.
- Frozen predecessor integrity remains exact.

AGENT-00 establishes the baseline and closes audit-only. The bounded next issue is AGENT-01:
runtime ownership and production boundary decision.

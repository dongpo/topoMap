# AGENT-01 — Canonical Runtime Ownership & Production Boundary Decision

Decision date: 2026-08-19 (Asia/Taipei)

## 1. Verdict

**PASS — ONE CANONICAL PRODUCTION RUNTIME SELECTED**

The single authoritative NMA Agent production runtime is the bounded **NMA v0.2 public
evidence runtime**: the `nmaAgentDemo.html` browser application only as transformed and packaged
by `scripts/build_public_site.py` for the GitHub Pages workflow, with
`PUBLIC_EVIDENCE_ONLY=true`.

This decision selects the runtime that is actually deployed. It does not promote the local
v0.31/v0.32 Agent server, an OpenAI-backed route, the stable local Python API, a domain capability
engine, or Core identity into a second production Agent runtime.

The production runtime is intentionally read-only with respect to durable and authoritative data.
Its only execution authority is bounded client-side evidence display and map/UI state. Agent
reasoning and planning cannot authorize or perform durable mutation. ROAD and School Hero retain
their frozen domain-specific authorization, execution, verification, receipt, and provenance
semantics behind non-public production-adapter boundaries.

No production-reachable mutation bypass exists under this decision. The three known failures
reproduced twice with materially identical signatures, remained outside the selected runtime, and
were the only failures in both the focused Agent validation and the complete repository suite.

## 2. Decision status and scope

This document is the architecture decision for Linear issue GEO-132. It is documentation-only.
It does not redirect an import, alter a deployment, change an API, repair stale evidence, delete a
legacy implementation, change an authorization rule, or implement AGENT-02.

The classifications in this document are normative for production promotion work after AGENT-01.
They describe ownership, not new runtime behavior. A component classified `production-adapter`
is not necessarily reachable from the current public deployment; it is an allowed boundary around
the canonical runtime or an authoritative domain capability, not another orchestration owner.

## 3. Baseline identity and evidence

| Item | Verified value | Result |
|---|---|---|
| Repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Accepted AGENT-00 predecessor | `113cab95f2d898feb8a58b41bbc88e1590b79cc3` | PASS |
| AGENT-00 parent / CORE-FINAL | `5eb138ae7686502431587743ebce9ddf92c5a799` | PASS |
| Starting branch | `agent/agent-00-architecture-audit` | PASS |
| Starting worktree | clean | PASS |
| AGENT-01 branch | `agent/agent-01-runtime-ownership-decision` | PASS |
| AGENT-00 evidence | `AGENT-00-Architecture-Audit.md` at the accepted predecessor | PASS |
| Python / pytest evidence | Python 3.11.9 / pytest 8.3.3 | PASS |

AGENT-00 is the complete inventory and reachability baseline. AGENT-01 re-inspected the public
deployment workflow, public builder, stable page and local API entry points, local Agent server
routes, browser coordinators, planner implementations, semantic/evidence stacks, proposal stores,
and frozen ROAD and School Hero capability paths before making this decision.

The production facts controlling the decision are:

1. `.github/workflows/static.yml` is the only repository deployment workflow and deploys a bounded
   static artifact from `scripts/build_public_site.py`.
2. The builder forces `PUBLIC_EVIDENCE_ONLY=true`, copies an explicit public-file allowlist,
   rejects PMTiles publication, and does not publish an Agent API server.
3. No deployed `/api/agent`, OpenAI, Neo4j, GDAL, private archive, ROAD execution, or School Hero
   execution service exists in that artifact.
4. `scripts/run_nma_agent_server.py` is a local demo server containing experimental and frozen
   capability routes; it is not in the Pages payload.
5. Frozen ROAD and School Hero execution continue to consume exact Core identity and their own
   closed domain authorizations.

## 4. Canonical production runtime decision

### 4.1 Selected runtime

**Canonical production runtime identity:** `nma-public-evidence-runtime/v0.2`.

**Executable owner:** the built `nmaAgentDemo.html` browser artifact in forced public
evidence-only mode.

**Production ingress:** the GitHub Pages `index.html` link into the built browser artifact.

**Production orchestration owner:** the browser's bounded deterministic request interpretation,
evidence lookup, presentation-state proposal, explicit client-state gate, and display coordinator
inside the built artifact.

**Production effects:** evidence panels, reviewed decision display, and client-side map/UI state.
No durable write, source mutation, authorization consumption, server tool execution, or official
rule activation is within this runtime.

The runtime boundary is the generated public artifact, not every behavior present in the raw
repository source page. Relative `/api/*` calls in local source are not production dependencies:
the Pages build ships no handler and forces the evidence-only branch. A future deployment that
adds a backend, disables the forced mode, or makes an experimental API required would be a new
architecture and must not inherit this `canonical-production` classification automatically.

### 4.2 Rejected alternatives

| Candidate | Decision | Reason |
|---|---|---|
| `scripts/run_nma_agent_server.py` and `/api/agent` | not canonical | Local demo only; split server/browser orchestration; model, proposal, persistence, authentication, and deployment contracts are not production-stable. |
| V031/V032 browser coordinator | not canonical | Demo clients coupled to local experimental routes; V032 is the current local demo, not the deployed artifact. |
| `nma.api` / `nma.cli` / `PortrayalAgent` | not canonical | Stable compatibility interface, but not the deployed production ingress and not the owner of the Pages browser lifecycle. |
| `intent_planning_v05.plan_intent()` | not canonical | Test-only, explicitly non-executing, and has no runtime caller. |
| VS1–VS4 and domain proposal stores | not canonical | Experimental planners and proposal mechanisms behind local routes. |
| ROAD or School Hero execution engine | not canonical | Authoritative domain capability engines, not a general Agent runtime or planner. |
| Core identity | not canonical | Canonical infrastructure primitive, not Agent orchestration. |
| Canonical JSON / Neo4j semantic runtime | not canonical | Experimental semantic/evidence backend pair; neither owns production ingress or authorization. |

Selecting the local Agentic server would make its stale freeze fingerprint production-relevant and
would leave split browser/server ownership unresolved. AGENT-01 therefore could not select it and
still pass the stated fail-closed acceptance gates.

## 5. Authoritative production chain

The current production chain is explicit and terminates in read-only presentation effects:

```text
GitHub Pages request
  -> built public nmaAgentDemo.html
  -> deterministic bounded interpretation and evidence lookup
  -> evidence-backed presentation proposal
  -> in-browser explicit state gate
  -> client-only display/map-state execution
  -> evidence panel + reviewed contract + release-manifest provenance
```

Mapped to the required invariant:

```text
request
  -> reasoning/planning
  -> proposal
  -> authorization
  -> execution
  -> verification/provenance
```

For the selected runtime, `authorization` means only a local presentation-state gate. It grants no
durable capability. `execution` means only browser display/map state. An absent, malformed, or
unsupported input must abstain or retain the evidence-only state; it must not fall through to a
server mutation path.

If a future production request needs a durable ROAD or School Hero effect, the allowed ownership
shape is:

```text
canonical Agent request/planning (no mutation authority)
  -> immutable domain proposal
  -> ROAD or School Hero production adapter
  -> exact domain authorization validation
  -> domain-owned execution
  -> domain-owned observation, receipt, verification, and provenance
```

That future connection is not implemented or production-reachable by this decision.

## 6. Runtime responsibility matrix

| Stage | Authoritative owner | Input/output boundary | Fail-closed rule |
|---|---|---|---|
| Production ingress | Pages `index.html` and built public page | Static request to allowlisted artifact | No backend or private input is implied by the public URL. |
| Request interpretation | Built browser deterministic logic | User text/UI event to bounded supported intent or abstention | Unsupported or ambiguous requests abstain; no arbitrary tool name or path is accepted. |
| Reasoning/planning | Built browser bounded planner | Public catalog/graph/contract to a presentation plan | Planning is read-only and cannot mint durable authority. |
| Semantic/evidence access | Allowlisted public portrayal graph, five-scene contract, capability catalog, and reviewed assets | Read-only tracked JSON/assets | Missing or invalid evidence stops the action or leaves evidence-only display; no model or backend substitution is authoritative. |
| Proposal/decision | Browser session state | Evidence-backed proposed UI/style/display state | A proposal is not an authorization and cannot mutate an official source. |
| Production authorization | Browser explicit presentation-state gate | Pending client proposal to approved/discarded client state | Scope is client display only; it cannot be translated into ROAD/School/general mutation authority. |
| Production execution | Browser display/map coordinator | Approved presentation state to DOM/map state | No durable, source, schema, data, or official-rule mutation is allowed. |
| Production verification | Evidence panel and frozen public demo contracts | Rendered state plus cited reviewed evidence | Verification must remain visible; missing evidence cannot be silently hidden or invented. |
| Production provenance | Public release manifest and tracked evidence identifiers | Built-file hashes and evidence/citation identifiers | Only allowlisted public files are attributable to this release. |
| Core identity | `nma.core` | Canonical JSON/hash infrastructure for consumers that require durable identity | No Agent, adapter, or domain may copy, reconstruct, stub, or fall back around Core. |
| ROAD authorization/execution | Frozen ROAD modules and stored ROAD artifacts | Exact authorization ID/idempotency request to scoped execution/receipt | Agent/browser/model state cannot replace or widen ROAD authorization. |
| School Hero authorization/execution | Frozen School Hero modules and stored Hero artifacts | Exact authorization ID/idempotency request to scoped execution/receipt | Agent/browser/model state cannot replace or widen School Hero authorization. |
| ROAD/Hero verification and provenance | Frozen domain verifiers | Execution artifacts to observation/QA/receipt/provenance | Verification remains domain-owned and bound to exact Core identity. |

## 7. Entry-point and architecture classification matrix

Each row has exactly one classification from the GEO-132 vocabulary. The classification applies to
the named entry point or architecture in its stated role. A source file containing both an active
helper and a superseded wrapper is split by symbol/role so that no live helper is incorrectly
declared dead.

| Entry point / architecture | Classification | Disposition and ownership |
|---|---|---|
| Built public `nmaAgentDemo.html` with `PUBLIC_EVIDENCE_ONLY=true` | `canonical-production` | The one production runtime and orchestration owner; client-only evidence/display effects. |
| Pages `index.html`, `.github/workflows/static.yml`, `scripts/build_public_site.py` | `production-adapter` | The only production ingress/build/deployment adapter; may package only the allowlisted canonical runtime. |
| `nmaDemoWorker.js` in the stable public lineage | `production-adapter` | Cache/offline adapter for public static assets; no planning or mutation authority. |
| Raw local/full-mode behavior in `nmaAgentDemo.html` | `compatibility` | Retains stable local v0.2 behavior, but only its forced evidence-only build is canonical production. |
| `nma ask`, `nma portray`, `nma compile-style`, `nma serve`; `src/nma/cli.py`, `api.py`, `knowledge.py`, `portrayal.py` | `compatibility` | Stable deterministic v0.2 local interfaces; no ownership of deployed production ingress. |
| `nma-bench`, `src/nma/portrayal_bench.py`, `benchmark/adapters/openai_compatible.py` | `experimental` | Optional evaluation path, never a correctness or production dependency. |
| Stable demo reconstruction/freeze/soak/offline/backup/RC modules | `demo` | Demonstration and release-evidence tooling; not runtime authority. |
| `scripts/build_pmtiles_capability_catalog.py` | `demo` | Demo catalog generator; its known reproducibility drift does not define runtime truth. |
| `scripts/build_agentic_v03_pages.py`, `check_agentic_v03_pages.py`, `check_agentic_v03_freeze.py` | `demo` | Candidate/fingerprint evidence only; not the production Pages workflow. |
| `scripts/build_nma_agentic_v031_demo.py`, `build_nma_agentic_v032_demo.py` | `demo` | Demo derivation tools only. |
| `scripts/run_nma_agent_server.py` process and static serving role | `demo` | Local demonstration host; not deployed and not a canonical orchestration owner. |
| `/api/agent`, server `orchestrate()`, Responses route tool, session continuation | `experimental` | Experimental route/planning service; it may propose routes but has no production or mutation authority. |
| V04 browser/worker | `deprecated` | Preserved pre-v0.31 demo and builder source; no new production dependency may target it. |
| V031 browser/worker | `deprecated` | Superseded demo and V032 builder source; retained only until an authorized retirement issue. |
| V032 browser/worker and `executeAgentRoute()` coordinator | `demo` | Current local School Hero demonstration; explicit browser gates remain demonstrative. |
| `deterministicRoute()` copies in V04/V031/V032 | `demo` | Demo fallback copies; not authoritative for production contract evolution. |
| `src/nma/intent_planning_v05.py` / HERO-01 planner | `test-only` | Explicit `no_execution`; no runtime caller. AGENT-02 must decide adoption or deprecation. |
| `src/nma/agentic_vs1.py` grounded answer assembly | `experimental` | Model-assisted evidence answer path behind the local Agent server. |
| `src/nma/agentic_vs2.py` portrayal planner | `experimental` | Produces bounded proposals only; no production authorization. |
| `src/nma/agentic_vs3.py` real-layer planner | `experimental` | Produces bounded proposals only; execution remains separately gated. |
| `src/nma/agentic_vs4.py` QA planner | `experimental` | Direct local API path with no browser caller; no production status. |
| `portrayal_review.py`, `portrayal_compile.py`, `maplibre_adapter.py` | `experimental` | Derived-preview proposal/compile path; official rule activation remains forbidden. |
| `real_layer.py` and `/api/real-layer*` | `experimental` | Checksum-bound derived GeoJSON proposal/execution; not production-reachable. |
| `qa_review.py` and `/api/qa-review*` | `experimental` | Derived-copy repair path; not production-reachable. |
| `agents/school_agent/*` and `/api/school-agent/analyze` | `experimental` | Proposal-only School intelligence; separate from frozen School Hero. |
| `graphrag.py` large canonical graph retriever | `experimental` | Experimental semantic/evidence implementation; not public production semantic authority. |
| `vector_index.py` and embedding client | `experimental` | Optional OpenAI-backed hybrid retrieval; not a production dependency. |
| Active retrieval v05–v101 helpers used transitively by v108 | `experimental` | Internal experimental semantic stack; not independent runtime owners. |
| `retrieval_v108.py` live server retrieval | `experimental` | Current experimental server retrieval owner. |
| Superseded `retrieval_v105` concrete wrapper | `deprecated` | Imported/tested historical wrapper, not instantiated by the current server. |
| Active entity-resolution helpers v10/v101/v102/v103/v104/v105/v107/v108 and current v106 wrapper | `experimental` | One experimental resolution chain under v108; no production planning or authorization role. |
| Superseded entity wrapper variants not selected by the live v108/v106 chain | `deprecated` | Historical/test compatibility only; retained pending authorized cleanup. |
| `runtime_graph_backend_v029.py` | `experimental` | Experimental backend selector with visible JSON fallback/parity enforcement. |
| `neo4j_projection.py`, `neo4j_roundtrip_v027.py`, `neo4j_retrieval_v028.py` | `experimental` | Optional backend/projection tooling for the large graph; not a second semantic authority. |
| Vector/Neo4j build, refresh, parity, and runtime utility scripts | `experimental` | Operator tooling for the experimental semantic stack. |
| Frozen School Hero execution and verification modules | `production-adapter` | Authoritative School domain capability boundary; not a generic Agent runtime and not publicly reachable today. |
| Dedicated `/api/school-hero/executions*` local routes | `production-adapter` | Thin local adapter to frozen School authority; the hosting demo server does not become canonical. |
| Frozen ROAD resolution/decision/approval/execution/verification/consumption modules | `production-adapter` | Authoritative ROAD domain capability boundary; not a generic Agent runtime and not publicly reachable today. |
| Dedicated `/api/road/executions*` local routes | `production-adapter` | Thin local adapter to frozen ROAD authority; exact domain authorization remains mandatory. |
| `scripts/verify_school_hero_execution.py`, `verify_road_execution.py`, `verify_road_authorization_consumption.py` | `production-adapter` | Acceptance/verification adapters for frozen domain capabilities. |
| Agent, semantic, demo, ROAD, Hero, and Core tests under `tests/` | `test-only` | Executable contract and regression evidence; never runtime ingress. |

`dead/orphaned` count: **zero**. Every material component found by AGENT-00 is deployed, packaged,
imported, tested, used by a builder/operator path, or intentionally retained. `deprecated` means
superseded and barred from new production dependencies, not presently unreachable.

## 8. Disposition by parallel planning architecture

| Parallel architecture | Owner after AGENT-01 | Disposition |
|---|---|---|
| Public deterministic v0.2 browser interpretation | canonical public runtime | Keep as the only production planner; read-only, bounded, and evidence-backed. |
| Stable Python `PortrayalAgent` question/selection path | compatibility package | Keep supported locally without calling it the production orchestration owner. |
| OpenAI Responses route tool | experimental Agent server | Keep experimental; it proposes exactly one route and cannot authorize execution. |
| Browser fallback routers in local demo versions | demo pages | Freeze as demo behavior until AGENT-02 supplies one versioned contract and parity tests. |
| HERO-01 `plan_intent()` | tests | Keep test-only; AGENT-02 must explicitly adopt or deprecate it. |
| VS2 portrayal plan | experimental portrayal-review boundary | Keep proposal-only and outside production. |
| VS3 real-layer plan | experimental real-layer boundary | Keep proposal-only and outside production. |
| VS4 QA plan | experimental QA boundary | Keep proposal-only and outside production; direct API reachability is not promotion. |
| School intelligence reasoning | experimental School intelligence boundary | Keep proposal-only and separate from frozen School Hero. |
| ROAD planning/decision/approval | frozen ROAD domain | Preserve as authoritative domain capability semantics; never subsume into generic Agent planning. |
| School Hero authorization/execution | frozen School Hero domain | Preserve as authoritative domain capability semantics; never derive authority from browser/model approval. |

## 9. Semantic and evidence ownership

The canonical production runtime owns access only to the explicit public evidence allowlist:

- `data/knowledge/portrayal-graph.json`;
- `data/demo/five-scene-demo.json`;
- `data/demo/pmtiles-capability-catalog.json`;
- reviewed public symbol and release assets copied by `build_public_site.py`.

The small portrayal graph is therefore authoritative only for the current bounded public runtime.
This decision does not declare it the universal NMA knowledge graph.

The large canonical graph, hybrid vector/retrieval/entity-resolution chain, and verified Neo4j
projection remain one experimental semantic architecture. Canonical JSON is the source backend and
Neo4j is a parity-checked backend variant within that architecture. Neither is allowed to bypass
the public runtime's evidence allowlist or to confer authorization.

Domain evidence used by ROAD, School Hero, School intelligence, portrayal review, real-layer, and
QA remains owned by those domain boundaries. Evidence identity can support a proposal or verifier;
it cannot turn a planner result into an authorization.

## 10. Proposal, authorization, and mutation boundaries

### 10.1 Proposal ownership

The canonical runtime may create only transient presentation proposals in browser state. Local
experimental routes may create their existing proposal objects, but those objects remain owned by
their route-specific stores and have no production standing.

A proposal ID, model tool call, browser confirmation, plan hash, or evidence package is never by
itself a durable authorization.

### 10.2 Authorization ownership

- Public v0.2 authorization is limited to an explicit client presentation-state gate.
- ROAD authorization is owned only by the frozen ROAD decision/approval capability chain.
- School Hero authorization is owned only by the frozen School Hero capability artifacts.
- Experimental portrayal, real-layer, and QA approval contracts remain domain-local and
  derived-output-only; this decision does not equate them with frozen ROAD/Hero authorization.
- A generic Agent, model, browser coordinator, API handler, or Core identity primitive owns no
  authorization semantics.

### 10.3 Mutation and execution ownership

The canonical production runtime has no durable mutation owner because durable mutation is outside
its scope. Client display/map-state changes are its complete execution boundary.

ROAD and School Hero engines remain the only owners of their respective durable derived execution,
and only after exact domain authorization validation. They must continue to reject extra client
parameters, wrong identities, widened scope, replay violations, and missing Core.

Experimental portrayal preview, real-layer derived GeoJSON, and QA derived-copy operations remain
non-production. Their existence in the same local demo server does not authorize production use.

## 11. Verification, receipt, and provenance ownership

| Effect class | Verification owner | Receipt/provenance owner |
|---|---|---|
| Public evidence/display | Browser evidence panel and frozen public demo/release checks | Public release manifest plus reviewed evidence/citation identifiers |
| ROAD derived execution | Frozen ROAD verifier | ROAD observation, receipt, bundle, consumption, QA, rollback, and provenance artifacts |
| School Hero derived execution | Frozen School Hero verifier | School Hero observation, receipt/bundle, QA, rollback, and provenance artifacts |
| Experimental portrayal preview | Portrayal-review validation/compile boundary | In-memory proposal history only; not acceptable as production durable provenance |
| Experimental real-layer output | Real-layer observation/QA checks | Route-local proposal/execution evidence; not production durable provenance |
| Experimental QA repair | QA reinspection/audit boundary | Route-local proposal/audit evidence; not production durable provenance |

Agent reasoning traces, model response IDs, browser messages, and in-memory proposal stores are not
receipts. Hidden reasoning is not provenance. Only bounded observable inputs, outputs, evidence
identifiers, authorization identities, execution records, and verifier results may be retained as
operational evidence.

## 12. Allowed dependency directions

Allowed directions are one-way unless a future issue explicitly changes them:

```text
Pages deployment adapter
  -> canonical public evidence runtime
  -> allowlisted public evidence/assets

compatibility interfaces
  -> stable v0.2 portrayal/knowledge behavior

demo clients and experimental planners
  -> experimental semantic/evidence adapters
  -> Core identity where content identity is required

canonical or experimental planner
  -> immutable proposal
  -> domain production adapter
  -> domain authorization
  -> domain execution
  -> domain verification/receipt/provenance

ROAD and School Hero domain modules
  -> exact Core identity primitives
```

The following directions are forbidden:

1. The canonical production runtime must not require `/api/agent`, OpenAI, Neo4j, GDAL, a private
   archive, or any V031/V032 demo artifact.
2. A planner, model tool call, evidence answer, browser state, or proposal store must not call a
   durable executor while bypassing exact domain authorization.
3. Browser approval must not be interpreted as ROAD or School Hero authorization.
4. Experimental proposal IDs or plan hashes must not become generic mutation capabilities.
5. ROAD and School Hero must not depend on Agent orchestration to validate their authority.
6. No domain, Agent, test, demo, or compatibility path may copy, reconstruct, stub, or repair Core
   identity when Core is absent.
7. Neo4j must not become a separate semantic authority from its verified canonical JSON source.
8. Compatibility, demo, experimental, deprecated, or test-only components must not be imported by
   the canonical runtime without a separately accepted promotion issue.
9. A documentation classification must not be used as evidence that deployment, authentication,
   persistence, replay, or operational security has been implemented.

## 13. Known failure treatment

The three AGENT-00 baseline failures were run twice as a focused set before the acceptance suites.
Both focused runs produced exactly the same three node IDs and materially identical functional
signatures.

### 13.1 Capability catalog reproducibility

- Node: `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`.
- Signature: `AssertionError`; generated capability `9920103` omits
  `flagpole_horizontal_alignment` from the tracked expected editable parameters.
- Classification: demo generator evidence drift.
- Production treatment: the tracked catalog is an allowlisted public runtime input, but the failing
  generator is not executed by the deployed runtime. The failure does not show a malformed tracked
  runtime asset or a production behavior error and does not add mutation reachability.

### 13.2 Agentic v0.3 freeze fingerprint

- Node:
  `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`.
- Signature: `ValueError: scripts/run_nma_agent_server.py size: expected 29586, got 133875`.
- Classification: demo freeze evidence drift.
- Production treatment: the server is classified `demo`, `/api/agent` is `experimental`, and
  neither is present in the canonical public artifact.

### 13.3 Agentic v0.3 Pages candidate fingerprint

- Node:
  `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`.
- Signature:
  `ValueError: data/demo/pmtiles-capability-catalog.json size differs from the candidate manifest`.
- Classification: demo candidate-manifest drift.
- Production treatment: this is the separate Agentic v0.3 candidate builder, not
  `.github/workflows/static.yml` or `scripts/build_public_site.py`.

The focused Agent set reported `110 passed, 3 failed`. The full suite reported `477 passed,
3 failed`. No new failure, skipped replacement, production failure, Core failure, ROAD failure, or
School Hero failure appeared. Repair remains reserved for an authorized evidence-refresh issue.

## 14. Validation evidence

| Gate | Result |
|---|---|
| Focused known-failure reproduction, run 1 | exactly the recorded 3 failed; materially identical |
| Focused known-failure reproduction, run 2 | exactly the recorded 3 failed; materially identical |
| CORE-01 through CORE-04 | `53 passed` |
| Complete frozen ROAD suite | `199 passed` |
| Complete School Hero suite | `42 passed` |
| Agent-focused suite | `110 passed, 3 known failed` |
| Full repository collection/execution | `480 total`; `477 passed, 3 known failed` |
| New or production-relevant failure | none |

The ROAD set is the exact 199-test union of ROAD-01 resolution, ROAD-02 portrayal decision,
ROAD-03 approval/authorization, ROAD-04 execution, and ROAD-05 verification. The 42-test School
set covers HERO-04, HERO-05, the V032 School Hero contract, and School feature intelligence, matching
the accepted complete School baseline.

Tests were executed with bytecode and pytest cache writes disabled. Repository-generated temporary
artifacts used the established temporary artifact boundary. The tracked worktree remained clean
after validation.

## 15. Frozen integrity and change boundary

The branch began at the accepted AGENT-00 SHA. Before this document was created:

- tracked worktree status was clean;
- Core acceptance was exact at 53 passing tests;
- ROAD acceptance was exact at 199 passing tests;
- School Hero acceptance was exact at 42 passing tests;
- full-suite behavior matched the accepted 477/3 baseline;
- no production, test, schema, data, Core, ROAD, or Hero file differed from the predecessor;
- the ignored private archive remained untracked and unstaged.

AGENT-01 authorizes exactly one changed file:

1. `AGENT-01-Runtime-Ownership-Decision.md` — this architecture decision.

Any other tracked change is a fail-closed condition and must prevent commit or push.

## 16. Risks and unresolved questions

1. The raw stable page still contains local API/fallback code even though the public builder forces
   evidence-only mode. The generated artifact, not the raw page alone, must remain the production
   identity.
2. The same route ideas are duplicated in public/stable browser logic, V04/V031/V032 fallback
   functions, the server tool schema/prompt, and the isolated HERO-01 planner.
3. The experimental server still combines static hosting, model transport, semantic retrieval,
   proposal stores, derived-output routes, and frozen capability adapters in one process.
4. Experimental proposal state is in-memory and is not a production receipt or replay ledger.
5. The small public portrayal graph and the large experimental canonical graph have different
   schemas and ownership; AGENT-01 does not unify them.
6. The stale demo/fingerprint evidence remains intentionally unresolved and can obscure new drift
   if future work does not compare exact node IDs and signatures.
7. `agentic_vs4` remains directly API-reachable locally without a browser caller or focused VS4
   test; it remains experimental and must not be promoted implicitly.
8. Direct model clients have different error handling and no shared retry policy. They remain
   outside production, so AGENT-01 does not standardize them.
9. `production-adapter` labels on frozen domain paths express trust-boundary readiness, not current
   public deployment. Authentication and hosting remain separate future decisions.

None of these questions creates a current production mutation bypass. Each would require a
separate bounded issue before changing the selected runtime or its dependency boundary.

## 17. Bounded AGENT-02 recommendation

AGENT-02 should be limited to **intent/planning contract consolidation**:

1. define one versioned, closed route/plan contract whose production subset matches the bounded
   read-only v0.2 public runtime;
2. make planner output explicitly proposal-only and incapable of expressing authorization or
   execution parameters;
3. add executable parity tests for the canonical deterministic implementation and any retained
   model/demo adapters;
4. decide explicitly whether `intent_planning_v05.plan_intent()` is adopted behind that contract
   or deprecated;
5. document compatibility behavior for V04/V031/V032 without promoting them;
6. preserve ROAD, School Hero, and Core boundaries exactly;
7. do not implement semantic/KG unification, generic authorization, durable execution, memory,
   deployment, or legacy deletion under AGENT-02.

AGENT-02 must start from the accepted AGENT-01 evidence commit and fail closed on any production
dependency expansion or mutation-authority drift.

## 18. Final decision

The production ownership question is closed as follows:

> The built NMA v0.2 public evidence runtime is the one canonical production Agent runtime. It owns
> bounded deterministic interpretation, public evidence access, presentation proposals, client
> display authorization, client-only execution, and visible evidence provenance. It owns no
> durable mutation authority. All local model, semantic, demo, and derived-output architectures
> remain outside production. ROAD and School Hero remain authoritative domain capability adapters
> for their own authorization, execution, verification, receipt, and provenance chains, with Core
> identity as shared canonical infrastructure rather than an Agent runtime.

This decision satisfies GEO-132 without implementing runtime consolidation.

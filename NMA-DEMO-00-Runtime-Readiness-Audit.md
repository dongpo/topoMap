# NMA-DEMO-00 — Runtime & Demo Readiness Audit

**Audit date:** 2026-08-22 (Asia/Taipei)

**Audit branch:** `demo/demo-00-runtime-readiness-audit`

**Baseline:** `380cc6ea2a4498ce83690521c933accfd918818e`
**Scope:** evidence-only; no production, runtime, frozen-artifact, or GEN changes

## 1. Verdict

> **PARTIAL — ARCHITECTURE COMPLETE; DEMO RUNTIME INCOMPLETE**

NMA does **not** currently have one user-facing runtime that accepts a request and routes it through canonical planning, authorization, execution, observation, verification, receipt, and provenance for School Hero, ROAD, and BUILD.

What exists is split into three classes:

1. a runnable portrayal/evidence UI and CLI/API surface;
2. frozen, real School Hero and ROAD execution engines and controlled BUILD activation/verification modules, each independently evidenced and mostly private-data dependent; and
3. historical, static, or generated demo artifacts.

The generic GEN contracts are shared by the domains, but contract conformance is not runtime integration. The canonical production public runtime is intentionally evidence-only. The local v0.32 server exposes direct School Hero and ROAD engine routes, but its Agent flow does not select or dispatch those engines; BUILD is not registered at all. Therefore architecture completion and test coverage do not constitute a unified demonstrator.

**Required completion path:**

> **Path C — DEMO-01 Unified Runtime → DEMO-02 E2E Acceptance → DEMO-FINAL → NMA-FINAL**

No evidence found requires a post-freeze contract change. The remaining work is runtime, wiring, UI, data, documentation, and environment work within the existing contract boundaries.

## 2. Canonical repository and generalization freeze

| Check | Evidence | Result |
|---|---|---|
| Canonical origin | `git remote get-url origin` → `https://github.com/dongpo/topoMap.git` | PASS |
| Starting branch | `freeze/gen-final-380cc6e` tracked `origin/freeze/gen-final-380cc6e` | PASS |
| Starting HEAD | `380cc6ea2a4498ce83690521c933accfd918818e` | PASS |
| Remote branch target | `refs/heads/freeze/gen-final-380cc6e` resolved to the same SHA | PASS |
| Annotated tag object | `9ba26ff032e23f0ba5de80d809f08eb6e973bb4f`, object type `tag`, subject `NMA generalization architecture v1.0 final` | PASS |
| Tag target | `nma-generalization-v1.0-final^{}` → `380cc6ea2a4498ce83690521c933accfd918818e`; remote peeled target identical | PASS |
| Initial worktree | clean | PASS |
| Audit branch | created as `demo/demo-00-runtime-readiness-audit` directly from the exact baseline | PASS |

No tag was created or changed. No merge was performed.

## 3. Audit method and safety boundary

The audit combined repository inspection, focused existing tests, actual CLI/API starts, direct HTTP probes, and an in-browser launch of the current local MapLibre UI. Tests were treated as evidence about their asserted layer only, never as proof of a user demo.

The private archive was not copied, opened, listed internally, hashed, or inspected. Its expected contract SHA remains:

`4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`

Public-clone checks used a separate fresh clone at the exact baseline with the archive absent. The audit did not make an OpenAI request or any other paid model call, and it did not expose credentials.

## 4. Complete runtime entry-point inventory

### 4.1 User-facing and potentially user-facing entry points

| Path | Invocation / location | Purpose and actual surface | Status | Requirements | Domains | Audience / provenance |
|---|---|---|---|---|---|---|
| `src/nma/cli.py` (`nma`) | `nma <command>` after install, or `PYTHONPATH=src python3 -m nma.cli <command>` | Top-level validation, portrayal, evidence, server, and demo CLI | Active compatibility runtime | Python ≥3.11; command-specific tracked evidence; GDAL for data operations; no credential for tested commands | Generic portrayal/RIVERL; not School/ROAD/BUILD routing | User/technical; compatibility, not canonical production Agent runtime |
| `nma validate` | `nma validate <dataset> --profile RIVERL` | Validates a dataset against rule evidence | Active | Dataset; GDAL/OGR as applicable | Generic/RIVERL | User/technical; production-capable validation utility |
| `nma rules` | `nma rules --profile RIVERL` | Lists rule evidence | Active | Tracked specifications | Generic/RIVERL | User/technical |
| `nma inspect` | `nma inspect <dataset>` | Dataset inspection | Active | Dataset; GDAL/OGR | Generic | User/technical |
| `nma demo` | `nma demo --profile RIVERL [--approval-file ... --output ...]` | Legacy rule-validation and repair proposal demonstration; approval can apply a bounded repair to an output copy | Active compatibility demo, not unified NMA | Supplied or synthetic demo data; optional approval file | RIVERL only | User demo utility; predates GEN-final domain integration |
| `nma compare` | `nma compare <before> <after> --profile RIVERL` | Compares validation reports | Active | Two report artifacts | Generic/RIVERL | Technical/internal |
| `nma ask` | `nma ask "<question>"` | Deterministic portrayal evidence retrieval | Active | Tracked portrayal graph; optional Neo4j configuration for alternate backend | Portrayal concepts | User CLI; real evidence retrieval, no feature execution |
| `nma portray` | `nma portray <feature-code>` | Selects a portrayal symbol and emits evidence/map/log output | Active | Tracked graph and symbols | Portrayal | User CLI; real selection, not domain feature production |
| `nma compile-style` | `nma compile-style --output <json>` | Compiles tracked portrayal graph into MapLibre style layers | Active | Tracked graph | Portrayal | Technical/runtime-build utility |
| `nma compile-knowledge` | `nma compile-knowledge ...` | Builds knowledge evidence | Active | Source specifications; optional backend inputs | Portrayal | Maintenance/internal |
| `nma serve` / `src/nma/api.py` | `nma serve --host 127.0.0.1 --port 8000`; `http://127.0.0.1:8000` | Dependency-free JSON HTTP API | Active compatibility API | Python standard library; tracked evidence; no credential for exposed routes | Generic validation/portrayal only | API user; not canonical production Agent runtime |
| `nma-bench` / `src/nma/portrayal_bench.py` | `nma-bench ...` | Portrayal benchmark runner | Active | Benchmark data/config; provider configuration for external adapters | Portrayal | Evaluation/internal, not demo |
| `nma-validation-bench` / `src/nma/bench.py` | `nma-validation-bench ...` | Validation benchmark runner | Active | Benchmark cases and data | Generic validation | Evaluation/internal, not demo |
| `Dockerfile` | `docker build ...`; container command `nma serve --host 0.0.0.0 --port 8000` | Packages the compatibility API | Active packaging | Docker; `gdal-bin`; build context | Generic API | Deployment utility; does not add domain routing |
| `compose.yaml` | `docker compose up nma`; optional `demo`/`benchmark` profiles | Starts API/tools containers | Active packaging | Docker Compose | Generic API/demo utilities | Technical |
| `nmaAgentDemo.html` | `python3 -m http.server 8000`, then `http://127.0.0.1:8000/nmaAgentDemo.html?basemap=local` | Five-scene MapLibre portrayal/evidence UI with browser-side deterministic routing | Active public/compatibility presentation surface | Browser; tracked PMTiles/graph/symbols; CDN assets on uncached first load; no credential | Portrayal catalog, not frozen domain engines | User demo; canonical production deployment is forced read-only evidence mode |
| `scripts/run_nma_agent_server.py` | `PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 8080` | Static-file server plus local experimental Agent, portrayal, real-layer, School Hero, and ROAD APIs | Active local demo host, not canonical production runtime | Python; tracked fixtures; optional OpenAI key; private archive for real layers/domain engines; GDAL for those paths | School-oriented UI; direct School/ROAD APIs; no BUILD API | Local demo/experimental host; non-canonical runtime |
| `nmaAgentDemoV032.html` | server above; `http://127.0.0.1:8080/nmaAgentDemoV032.html?basemap=local` | Current local MapLibre School-oriented evidence and portrayal workbench | Active demo | Browser; tracked PMTiles/graph/symbols; synthetic School fixture works; OpenAI key and private archive needed for full real-layer path | School presentation; portrayal catalog; not canonical School engine dispatch; no frozen ROAD/BUILD dispatch | User demo, non-production v0.32 |
| `nmaAgentDemoV031.html` | same server, `/nmaAgentDemoV031.html` | Prior local Agent demo | Deprecated | Same class of local requirements | Portrayal/School experiments | Historical demo |
| `nmaAgentDemoV04.html` | same server, `/nmaAgentDemoV04.html` | Earlier Agent demo | Deprecated | Browser and tracked assets | Portrayal experiments | Historical demo |
| `pmtilesDemo.html` | static HTTP server, `/pmtilesDemo.html` | Legacy generic topographic MapLibre viewer | Legacy/static | Browser; remote GitHub Pages PMTiles URL; CDN | Displays many ROAD/BUILD-named source layers, but no NMA execution | User viewer; not an Agent workflow |
| `MapOutputDemo.html` | static HTTP server, `/MapOutputDemo.html` | Legacy standalone map/export page | Legacy/static | Browser; CDN/remote resources | Generic output visualization | User viewer; not integrated runtime |
| `buildDemoV06.html` | static HTTP server, `/buildDemoV06.html` | BUILD-06 visual comparison of tracked BUILD-05 golden outputs; hatch slider changes presentation only | Artifact-only demo | Browser; tracked golden package/ledger | BUILD | User-readable static artifact; no source mutation or new authorization |
| `buildDemoV07.html` | static HTTP server, `/buildDemoV07.html` | BUILD-07 acceptance/revision evaluation page and JSON download | Artifact-only evaluation UI | Browser; tracked BUILD artifacts | BUILD | User-readable static artifact; browser-local decisions, no production right |
| `index.html` | static HTTP server, `/index.html` | Public landing/evidence surface | Active presentation | Browser and tracked assets | General NMA evidence | User documentation/presentation |
| `artifacts/presentation/nma-demo-backup/PLAYBACK.html` | static HTTP server at its path | Recorded backup playback | Artifact-only | Tracked recording assets | Portrayal demo recording | User presentation; explicitly not live execution |
| `artifacts/demo/validation-before/index.html` and `validation-after/index.html` | static HTTP server at their paths | Generated validation reports | Artifact-only | Tracked report assets | RIVERL validation | Evidence artifact, not integrated NMA demo |
| `docs/openapi.yaml` | Open as a file or feed to an OpenAPI viewer | Static API description | Active specification | External viewer if desired | Generic validation/portrayal | Documentation only; no bundled Swagger/OpenAPI UI |

The compatibility API routes verified at runtime were:

- `GET /health`
- `GET /v1/specification`
- `GET /v1/rules`
- `GET /v1/knowledge/portrayal`
- `GET /v1/maplibre/portrayal-layers`
- `POST /v1/agent/ask`
- `POST /v1/agent/portray`
- `POST /v1/validate`

`GET /docs` returned HTTP 404. No FastAPI or Flask application and no live Swagger UI was found.

### 4.2 Domain execution, verification, activation, and rollback entry points

| Path | Invocation / API | Purpose and status | Requirements | Domains | Surface / provenance |
|---|---|---|---|---|---|
| `src/nma/school_hero_execution.py` (`SchoolHeroExecutionEngine`) | Python API; also direct local routes `POST/GET /api/school-hero/executions...`, observation, rollback | Canonical frozen School Hero plan, authorization consumption, atomic execution, bundle/receipt persistence, observation, rollback | Private archive at expected SHA; official symbol; pre-stored complete HERO-03 authorization; writable runtime storage; GDAL | School Hero | Production adapter/internal pipeline; no public issuer or Agent dispatcher |
| `scripts/verify_school_hero_execution.py` | `PYTHONPATH=src:. python3 scripts/verify_school_hero_execution.py <execution-id> --storage-root <root> --archive <archive> [--official-symbol ...] [--no-persist]` | Canonical School execution verification | Existing execution; private archive; symbol; GDAL | School Hero | Internal verifier; frozen School evidence |
| `src/nma/road_execution.py` (`RoadExecutionEngine`) | Python API; direct local routes `POST/GET /api/road/executions...`, observation, rollback | Canonical frozen ROAD execution and receipt/bundle lifecycle | Private archive; frozen authorization ID; runtime storage; GDAL | ROAD | Production adapter/internal pipeline; not selected by Agent/UI |
| `scripts/verify_road_execution.py` | `PYTHONPATH=src:. python3 scripts/verify_road_execution.py <execution-id> --storage-root <root> --archive <archive> [--no-persist]` | Canonical ROAD execution verification | Existing execution; private archive; GDAL | ROAD | Internal verifier; frozen ROAD evidence |
| `scripts/verify_road_authorization_consumption.py` | `PYTHONPATH=src:. python3 scripts/verify_road_authorization_consumption.py` | Deterministic fixture audit of authorization acceptance/rejection | Tracked fixtures only | ROAD | Test/evidence utility; not real domain execution |
| `build_contracts/building_production_implementation.py` | Import and call `implement_controlled_building(...)` | Controlled BUILD executor | Private archive; frozen BUILD authorization/gates; GDAL/runtime dependencies | BUILD/J13/J17 | Production adapter/internal pipeline; no server route |
| `build_contracts/building_production_verification.py` | `PYTHONPATH=src:. python3 -m build_contracts.building_production_verification` | BUILD production readiness verification | Private archive at hard-coded expected location; frozen evidence | BUILD | Internal verification CLI |
| `build_contracts/building_production_activation.py` | `PYTHONPATH=src:. python3 -m build_contracts.building_production_activation` | Builds activation record, execution receipt, and baseline; maintains process-local activation registry | Private archive; frozen verification and implementation inputs | BUILD | Controlled production activation module, not hosted runtime |
| `build_contracts/demo_publication.py` | `PYTHONPATH=src:. python3 -m build_contracts.demo_publication ...` | BUILD demo-publication evidence workflow | Tracked BUILD artifacts | BUILD | Publication/build utility, not feature execution UI |

The School and ROAD local HTTP routes are thin direct adapters. Their presence does not make them Agent-reachable. BUILD has no route in the local server.

### 4.3 Build, maintenance, benchmark, and evidence-only executables

These are callable but are not public demo entry points:

| Paths | Representative invocation | Role | Classification |
|---|---|---|---|
| `scripts/build_nma_agentic_v031_demo.py`, `scripts/build_agentic_v03_pages.py`, `scripts/build_pmtiles_capability_catalog.py`, `scripts/build_public_site.py`, `scripts/build_review_package.py` | `PYTHONPATH=src:. python3 <script>` | Generate or package demo/public artifacts | Build-time maintenance; not runtime |
| `scripts/check_agentic_v03_pages.py`, `scripts/check_agentic_v03_freeze.py`, `scripts/check_public_assets_rc.py`, `release/review-package/VERIFY.py` | `python3 <script>` | Verify historical/generated artifacts and release packages | Audit/release checks; not runtime |
| `scripts/build_nma_vector_index_v04.py`, `scripts/build_nma_neo4j_projection_v04.py`, `scripts/run_nma_neo4j_roundtrip_v027.py`, `scripts/run_nma_neo4j_retrieval_parity_v028.py`, `scripts/run_nma_runtime_graph_backend_v029.py` | `PYTHONPATH=src:. python3 <script>` | Build/test optional retrieval backends | Internal tooling; Neo4j credentials/service may be required; canonical JSON fallback remains available |
| `scripts/build_road04_goldens.py`, `scripts/sync_school_fixture.py` | `PYTHONPATH=src:. python3 <script>` | Generate/synchronize domain fixtures/goldens | Test/evidence maintenance |
| `benchmark/adapters/openai_compatible.py` | benchmark adapter invocation | External-provider benchmark adapter | Evaluation only; provider endpoint/credentials required |
| `tools/create_demo_backup_video.py` | `python3 tools/create_demo_backup_video.py ...` | Creates backup presentation media | Artifact generation only |
| `nma demo-scenes`, `demo-freeze`, `demo-soak`, `demo-offline`, `demo-backup`, `demo-rc1` | `nma <command>` or Make targets | Validate demo scenes and release evidence | QA/release commands, not the demo runtime itself |

## 5. Candidate demo audit

| Candidate | Exact launch | What the user can do | Real components exercised | What it is not | Reproducibility |
|---|---|---|---|---|---|
| Current local v0.32 workbench | `PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 8080`; open `http://127.0.0.1:8080/nmaAgentDemoV032.html?basemap=local` | Ask School portrayal/evidence questions; inspect citations and trace; propose, approve, and preview structured portrayal edits; browse five scenes/capabilities; view a MapLibre map | Tracked portrayal graph, PMTiles, symbols, deterministic School evidence, structured preview adapter, synthetic 12-feature School fixture | Not the canonical production Agent runtime; UI does not call `SchoolHeroExecutionEngine`; no ROAD/BUILD dispatch; preview explicitly reports no map mutation; real 15-school path needs private archive and model key | **PUBLICLY REPRODUCIBLE** for evidence/synthetic preview; **PRIVATE-DATA/ENVIRONMENT DEPENDENT** for real layer flow |
| Public/compatibility five-scene page | `python3 -m http.server 8000`; open `http://127.0.0.1:8000/nmaAgentDemo.html?basemap=local` | Explore five portrayal scenes, ask deterministic evidence questions, inspect graph/evidence, see symbols/map | Browser-side deterministic portrayal logic and tracked assets | Canonical deployment is deliberately evidence-only; no domain authorization or execution | **PUBLICLY REPRODUCIBLE**, subject to browser CDN availability/cache |
| Generic CLI/API | Install or use `PYTHONPATH=src`; run `nma ask`, `nma portray`, `nma demo`, or `nma serve` | Retrieve evidence, compile/select portrayal, validate and propose bounded RIVERL repairs | Real tracked rules/graph and compatibility API | Not School/ROAD/BUILD routing; no unified lifecycle; no Swagger UI | **PUBLICLY REPRODUCIBLE** for tested commands |
| School canonical direct engine/API | Call Python engine or direct `/api/school-hero/executions` route | With pre-created authorization and private inputs, execute, observe, verify, retrieve receipt/bundle, and rollback | Real frozen School engine | No user intent interpretation, public authorization issuer, or UI; direct structured internal API | **PRIVATE-DATA DEPENDENT** and **LOCAL-ENVIRONMENT DEPENDENT** |
| ROAD canonical direct engine/API | Call Python engine or direct `/api/road/executions` route | With frozen authorization/private input, execute, observe, verify, retrieve receipt/bundle, and rollback | Real frozen ROAD engine | No Agent selection or UI | **PRIVATE-DATA DEPENDENT** and **LOCAL-ENVIRONMENT DEPENDENT** |
| BUILD controlled modules | Import controlled executor; run verification/activation modules | Verify and activate bounded J13/J17 controlled execution in process | Real frozen BUILD gates and production adapters | No server, prompt route, interactive UI, or durable hosted activation service | **PRIVATE-DATA DEPENDENT** and **LOCAL-ENVIRONMENT DEPENDENT** |
| BUILD v0.6/v0.7 pages | Static server; open `/buildDemoV06.html` or `/buildDemoV07.html` | Inspect golden visual output; change a display slider; record/download a local evaluation decision | Tracked BUILD golden/evaluation artifacts | No current source execution, new authorization, Agent, server persistence, or production mutation | **PUBLICLY REPRODUCIBLE ARTIFACT**, not runtime demo |
| Legacy PMTiles/MapOutput viewers | Static server; open `/pmtilesDemo.html` or `/MapOutputDemo.html` | View map layers/exports | MapLibre viewer assets | No intent, plan, auth, execution, receipt, or QA chain | **LOCAL/NETWORK DEPENDENT** static viewers |
| Backup/report HTML | Static server at artifact paths | Replay recording or inspect reports | Pre-generated artifacts | Not live; no action reaches runtime | **PUBLICLY REPRODUCIBLE ARTIFACT** |

The v0.32 UI was actually opened in the in-app browser against the fresh-clone server. Its local PMTiles map loaded, the School symbol and label were visible, five scene buttons and 42 capability entries rendered, and the default School question returned a deterministic reviewed evidence answer. Browser error and warning logs were empty. The trace stopped before production proposal/execution, as expected.

## 6. Domain runtime status

### 6.1 School Hero — **RUNNABLE INTERNAL PIPELINE**

| Stage | Evidence | Status |
|---|---|---|
| Input | Private archive and official School symbol; synthetic 12-feature fixture exists only for local demo inspection | Internal/private; synthetic demo available |
| Planning | `SchoolHeroExecutionEngine` builds and persists a canonical plan; shared Agent planner exists separately | Engine plan working; Agent-to-plan disconnected |
| Authorization | Execution consumes a complete stored HERO-03 authorization; no production issuer/runtime route was found; test support creates the authorization | Working boundary, unavailable to normal user |
| Execution | Atomic canonical engine and direct local API route exist | Working internal pipeline, private-data dependent |
| Map/result | Runtime bundle/MapLibre output is produced by canonical engine; v0.32 shows synthetic portrayal but bypasses that engine | Internal result available; public UI disconnected |
| Verification | Dedicated verifier and engine verification evidence exist | Working internal pipeline |
| Provenance | Plan, authorization, receipt, bundle, and data artifacts are linked | Working internal pipeline |
| Rollback | Engine/API rollback path exists and is tested | Working internal pipeline |

The v0.32 School UI is a **partial experimental demo**, not proof of the canonical School Hero path. Its real-layer endpoints are separate from `SchoolHeroExecutionEngine`; its approval interaction is not the frozen HERO authorization artifact.

### 6.2 ROAD — **RUNNABLE INTERNAL PIPELINE**

| Stage | Evidence | Status |
|---|---|---|
| Input | Private archive at the expected SHA | Private-data dependent |
| Planning | Frozen ROAD plan/evidence and engine plan handling exist | Working internally; user intent disconnected |
| Authorization | Frozen authorization `road-03-authorization-f68220ecef989e589dd6e28c`; consumption rules and fixture verifier pass | Working internally |
| Execution | `RoadExecutionEngine` and direct local HTTP route exist | Working internal pipeline; private archive required |
| Map/result | Derived artifact and MapLibre runtime bundle are engine outputs | Available internally; no ROAD UI |
| Verification | Dedicated execution verifier exists | Working internally |
| Provenance | Receipt/bundle/authorization linkage exists | Working internally |
| Rollback | Engine/API rollback path exists | Working internally |

No tracked runtime execution output was found under `artifacts/runtime`. Tracked ROAD goldens and passing authorization-consumption tests are validation evidence, not a current runnable public demonstrator.

### 6.3 BUILD — **RUNNABLE INTERNAL PIPELINE**

| Stage | Evidence | Status |
|---|---|---|
| Input | Private archive and frozen J13/J17 inputs | Private-data dependent |
| Planning | Frozen production plan/gates | Available internally; no user planner connection |
| Authorization | Controlled BUILD authorization and production gates | Working internally |
| Execution | `implement_controlled_building(...)` | Working internal import-only pipeline |
| Map/result | Controlled outputs and tracked BUILD-05 golden visual artifacts | Runtime internal; public pages are artifact-only |
| Verification | `building_production_verification` | Working with private input |
| Provenance | Activation record, execution receipt, baseline, and frozen evidence | Working internally |
| Rollback | Activation registry can deactivate process-local state; no interactive rollback UI/service | Partial/internal |

`production_active: true` means the bounded production execution path passed its frozen gates and was activated through the controlled activation model. It does **not** mean there is a hosted, interactive, or user-accessible BUILD demo. The activation registry is process-local; BUILD is absent from the local Agent server. BUILD v0.6/v0.7 are static golden/evaluation pages, not BUILD-12 runtime access.

## 7. Agent runtime audit

The current canonical production Agent runtime is identified by the frozen Agent evidence as `nma-public-evidence-runtime/v0.2`, built from `nmaAgentDemo.html` in forced public evidence-only mode. The same evidence classifies v0.32 as a demo, `nma.api`/`nma.cli` as compatibility surfaces, and School/ROAD engines as production adapters not publicly reachable.

| Capability | Classification | Exact evidence |
|---|---|---|
| 1. Accept a natural-language request | **PARTIAL** | Public/v0.32 pages accept portrayal/School questions; local `/api/agent` accepts text only when a model key is available. No generic frozen-domain production request entry exists. |
| 2. Interpret intent | **PARTIAL** | Browser deterministic routing and optional model-based local analysis work for bounded portrayal/School flows. They do not yield unified frozen-domain execution intent. |
| 3. Select the correct feature domain | **NOT CONNECTED** | Catalog selection is portrayal-feature selection, not School/ROAD/BUILD execution-domain routing. No canonical dispatcher selects those engines. |
| 4. Construct a plan | **PARTIAL / TEST-ONLY AT CANONICAL SHARED LAYER** | Shared `plan_request()` is deterministic and proposal-only, with tests; it is not called by the public runtime. Local experimental endpoints create bounded plans, but are School-oriented and optionally key-gated. |
| 5. Obtain/validate authorization | **NOT CONNECTED** | Domain engines validate their own stored artifacts. UI approvals belong to experimental portrayal review and are not canonical School/ROAD/BUILD authorizations. |
| 6. Execute through domain boundary | **NOT CONNECTED** | Agent handler does not dispatch `SchoolHeroExecutionEngine`, `RoadExecutionEngine`, or BUILD. Direct engine routes are separate. |
| 7. Observe result | **PARTIAL** | Portrayal previews and direct engine observation endpoints exist; no Agent-driven cross-domain observation flow. |
| 8. Verify result | **NOT CONNECTED** | Domain verifiers exist, but Agent does not automatically invoke them after execution. |
| 9. Return user-readable result | **PARTIAL** | Evidence answers, map preview, and CLI JSON are readable; canonical feature-production result is not returned through one user flow. |
| 10. Produce provenance/audit evidence | **PARTIAL** | Evidence citations and individual domain receipts exist; the Agent does not return an integrated request-to-receipt chain. |

The frozen Agent integration evidence explicitly preserves the separation: it projects generic proposal contracts but does not connect the public runtime to School Hero or ROAD execution engines. That is direct evidence of an intentional runtime boundary, not an inference from missing tests.

## 8. Unified runtime status

**Does a unified NMA runtime currently exist? No.**

The domains are **architecture-conformant**: School Hero, ROAD, and BUILD conform to the generic GEN contract and have frozen domain evidence.

They are not **runtime-integrated**:

- the canonical public runtime is evidence-only;
- the local v0.32 Agent/UI is School-oriented and calls experimental portrayal/real-layer endpoints rather than the canonical School engine;
- the local server exposes School and ROAD direct engine APIs, but the Agent router never selects them;
- BUILD has no local server route or Agent registration;
- no one process/UI returns execution, canonical verification, receipt, and provenance for two or more frozen domains.

Direct APIs sitting beside an Agent handler in one server file are not sufficient: there must be a request-to-domain dispatch path, and no such path was found or observed.

## 9. Natural-language interaction and credentials

| Element | Current state |
|---|---|
| LLM integration | Local server supports an OpenAI Responses-based path when `OPENAI_API_KEY` is configured. It was unavailable in the fresh-clone audit and was not called. |
| Deterministic fallback | Working for School evidence and structured portrayal review/preview; public page also uses deterministic browser routing. |
| Intent parser | Bounded portrayal/School logic exists; no canonical multi-domain execution intent parser is connected. |
| Planner | Shared proposal-only planner exists and is tested but disconnected from public runtime; experimental planners do not unify domains. |
| Tool/domain selection | Portrayal catalog selection works; frozen School/ROAD/BUILD domain selection is absent. |
| Execution | Only direct structured domain adapters; no natural-language dispatch. |
| Verification response | Evidence review and separate canonical verifiers exist; no automatic execution-verification response. |

Credential classification:

- OpenAI credential is **optional** for deterministic School evidence and structured portrayal preview.
- It is **required** for the local `/api/agent` model path and `/api/real-layer` planning path.
- It was **unavailable/unconfigured in the fresh-clone audit environment**.
- No credential value was read or printed.
- Neo4j/service credentials are optional for alternate graph backends; the canonical tracked JSON evidence fallback is available.

Runtime probes confirmed fail-closed behavior: `/api/agent` and `/api/real-layer` returned HTTP 503 with `key_missing` when no key was configured.

## 10. Map visualization status

**Can a user see an NMA-related result on a map today? Yes, for portrayal/evidence and synthetic School presentation. No, not as the result of a unified canonical School/ROAD/BUILD action.**

Verified reproducible launch:

```bash
PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 8080
```

Open:

`http://127.0.0.1:8080/nmaAgentDemoV032.html?basemap=local`

The checked-in `out1120902.pmtiles` (9,595,077 bytes), portrayal graph, MapLibre style adapter, symbol SVGs, and v0.32 UI rendered in the audit browser. The local server exposed a synthetic `school-points` Shapefile with 12 features when the private archive was absent. The UI displayed the School symbol/label and a deterministic evidence trace.

The structured preview API compiled a MapLibre layer but truthfully returned `automatic_action: false` and `map_mutation_performed: false`. A full real-school layer requires the private archive and a model-assisted plan. ROAD and BUILD action results have no connected browser viewer. Existence of portrayal tests, screenshots, PMTiles source layers, or static BUILD pages therefore does not prove interactive domain execution.

## 11. End-to-end traceability

Legend: **CONNECTED**, **AVAILABLE BUT DISCONNECTED**, **TEST-ONLY**, **ABSENT**.

| Candidate | Request | Intent | Plan | Authorization | Execution | Observation | Receipt | Provenance | QA |
|---|---|---|---|---|---|---|---|---|---|
| Canonical public evidence runtime | CONNECTED | CONNECTED | CONNECTED for evidence/presentation only | ABSENT for feature production | ABSENT | CONNECTED to presentation | ABSENT | CONNECTED to cited evidence | AVAILABLE BUT DISCONNECTED |
| Local v0.32 School workbench | CONNECTED | CONNECTED for bounded School/portrayal | CONNECTED for preview; model/private path conditional | CONNECTED only to experimental review; canonical School auth AVAILABLE BUT DISCONNECTED | Experimental real-layer path conditional; canonical School engine AVAILABLE BUT DISCONNECTED | CONNECTED for preview/map | Canonical receipt AVAILABLE BUT DISCONNECTED | CONNECTED for citations; execution provenance AVAILABLE BUT DISCONNECTED | AVAILABLE BUT DISCONNECTED |
| Canonical School direct engine/API | AVAILABLE BUT DISCONNECTED from user intent | AVAILABLE BUT DISCONNECTED | CONNECTED after direct structured call | CONNECTED if pre-stored artifact exists | CONNECTED | CONNECTED | CONNECTED | CONNECTED | CONNECTED |
| Canonical ROAD direct engine/API | AVAILABLE BUT DISCONNECTED | AVAILABLE BUT DISCONNECTED | CONNECTED after direct structured call | CONNECTED to frozen authorization | CONNECTED | CONNECTED | CONNECTED | CONNECTED | CONNECTED |
| Controlled BUILD modules | AVAILABLE BUT DISCONNECTED | AVAILABLE BUT DISCONNECTED | CONNECTED to frozen plan/gates | CONNECTED | CONNECTED | CONNECTED internally | CONNECTED | CONNECTED | CONNECTED |
| BUILD v0.6/v0.7 pages | ABSENT (display controls only) | ABSENT | ABSENT | ABSENT | ABSENT | CONNECTED to golden artifacts | ABSENT; evaluation download is not execution receipt | CONNECTED to static artifact metadata | TEST-ONLY / artifact review |

No row has a user action connected through all stages.

## 12. Public reproducibility

A new public clone was made from `https://github.com/dongpo/topoMap.git`, detached at the exact baseline. It was clean; the private archive was neither tracked nor present. It was not copied into the clone.

### 12.1 What reproduced

- `nma ask` returned School portrayal evidence.
- `nma portray 9920103` selected a symbol and emitted evidence/map/log data.
- `nma compile-style` generated 133 MapLibre layers into a temporary file.
- `nma demo-scenes` passed its five scenes and negative controls.
- `nma demo-offline` and `nma demo-backup` passed.
- `nma demo` ran a RIVERL proposal-only path, and a separately approved bounded output-copy repair path.
- The compatibility API started and served health, ask, portray, and 133 MapLibre layers; `/docs` was absent.
- The v0.32 local server started with 12 synthetic School features, zero-credit School evidence available, and model mode `deterministic-fallback`.
- Existing focused runtime tests covering the API, v0.32, Agentic VS2, and School API passed: **23 passed** after installing their undeclared `jsonschema` test dependency in a temporary virtual environment.
- The standalone GEN-FINAL focused suite passed: **10 passed**.
- ROAD authorization-consumption fixture verification passed.

### 12.2 What did not reproduce as a complete demo

- School direct execution failed closed because no stored authorization existed.
- ROAD direct execution reported the private source archive missing.
- BUILD verification and activation raised `FileNotFoundError` for the absent private archive.
- School/ROAD execution verifiers reported no execution at their empty default storage locations.
- `nma demo-freeze` failed because the tracked current `nmaAgentDemo.html` size no longer matched the historical manifest (`98,521` versus `20,541`).
- `nma demo-rc1` failed because the current offline runtime artifact size no longer matched its historical manifest (`3,287` versus `2,246`).
- A broader historical candidate suite had 23 passes and 3 drift failures: capability catalog drift, Agentic v0.3 server-size drift, and Pages-candidate catalog-size drift.
- A broader GEN-02-inclusive suite had 45 passes and 3 environment/history failures: a missing local branch ref in the fresh clone, stage-local allowed-path assumptions that reject later GEN-FINAL files, and the intentionally absent private archive.

Some historical demo tests verify files as they existed at old Git commits instead of validating the current working artifact. Their pass status is historical freeze evidence, not current launch readiness.

| Runtime path | Classification |
|---|---|
| Portrayal CLI/API and five-scene UI | **PUBLICLY REPRODUCIBLE** (browser CDN may make first load network dependent) |
| v0.32 evidence/synthetic School preview | **PUBLICLY REPRODUCIBLE** plus browser/local-environment dependency |
| v0.32 model/real-layer flow | **PRIVATE-DATA DEPENDENT** and **LOCAL-ENVIRONMENT DEPENDENT** |
| Canonical School execution | **PRIVATE-DATA DEPENDENT** and **LOCAL-ENVIRONMENT DEPENDENT** |
| Canonical ROAD execution | **PRIVATE-DATA DEPENDENT** and **LOCAL-ENVIRONMENT DEPENDENT** |
| Controlled BUILD execution/activation | **PRIVATE-DATA DEPENDENT** and **LOCAL-ENVIRONMENT DEPENDENT** |
| BUILD v0.6/v0.7 static pages | **PUBLICLY REPRODUCIBLE ARTIFACT**, not runtime execution |
| Unified multi-domain demo | **NOT REPRODUCIBLE**, because it does not exist |

Packaging also has a reproducibility gap: focused tests import `jsonschema`, but the project’s development dependency list contains only `pytest` and `ruff`; the audit had to install `jsonschema` separately in the temporary environment.

## 13. DEMO-A1–A12 acceptance matrix

| Criterion | Result | Exact evidence |
|---|---|---|
| DEMO-A1 — Single Entry Point | **FAIL** | No documented entry reaches the canonical multi-domain lifecycle. Public page is evidence-only; v0.32 is a non-canonical School-oriented demo; domain engines require separate direct calls. |
| DEMO-A2 — User Intent | **PARTIAL** | Natural-language evidence questions and structured CLI/API input work. Natural language does not route to frozen domain production. |
| DEMO-A3 — Domain Routing | **FAIL** | No running Agent routes to even two frozen feature-production domains. |
| DEMO-A4 — Real Planning | **PARTIAL** | Canonical proposal planner and domain plans exist, but shared planning is disconnected; v0.32 planning is bounded/experimental and School-oriented. |
| DEMO-A5 — Authorization | **PARTIAL** | Canonical authorization boundaries work inside individual engines. User/UI approvals are not connected to those artifacts. |
| DEMO-A6 — Real Execution | **FAIL** | Real domain executors exist, but no user demo invokes them through one runtime; public and v0.32 preview paths are non-mutating or experimental. |
| DEMO-A7 — Observable Result | **PARTIAL** | CLI JSON, evidence answers, previews, domain bundles, and static artifacts are inspectable, but not through one full flow. |
| DEMO-A8 — Map Result | **PARTIAL** | MapLibre portrayal/synthetic School view works. No canonical School/ROAD/BUILD action is rendered through the demo. |
| DEMO-A9 — Verification | **PARTIAL** | Canonical per-domain verifiers exist and are tested; they are not automatically invoked by a user workflow. |
| DEMO-A10 — Provenance | **PARTIAL** | Evidence citations and per-domain receipts exist; no unified request-to-receipt response. |
| DEMO-A11 — Fail-Closed | **PASS** | Public runtime is read-only; previews report no mutation; missing key, authorization, or archive blocked direct probes; domain engines enforce authorization. |
| DEMO-A12 — Reproducibility | **FAIL** | Public portrayal pieces reproduce, but full domain paths need the private archive/authorization/environment and the unified demo is absent. Current release manifests also drift. |

## 14. Architecture / Tests / Runtime / User Demo matrix

`PASS` means evidence at that column only. It does not propagate rightward.

| Capability | Architecture | Tests/evidence | Runtime | User demo |
|---|---|---|---|---|
| Identity | PASS: frozen canonical identity/contracts | PASS | Available in evidence and domain records | No unified identity display/control |
| Agent | PASS: frozen Agent contract boundaries | PASS | Partial evidence-only and experimental local handlers | Partial School/portrayal interaction only |
| Planning | PASS: generic proposal contracts and domain plans | PASS | Available but disconnected across domains | Partial preview plan; no multi-domain production plan |
| Authorization | PASS: fail-closed boundaries | PASS | Working inside direct domain engines | No canonical authorization flow in UI |
| School Hero | PASS: frozen domain contract | PASS | Canonical private internal engine; separate experimental UI path | Partial v0.32 portrayal/synthetic demo, not canonical execution |
| ROAD | PASS: frozen domain contract | PASS | Canonical private internal engine/direct API | None |
| BUILD | PASS: frozen domain contract and controlled activation | PASS | Private import-only controlled pipeline | Static artifact/evaluation pages only |
| Execution | PASS: domain execution boundaries | PASS | Real in individual private pipelines | No unified real execution |
| Portrayal | PASS | PASS | Working CLI/API/MapLibre adapter | Working portrayal map demo |
| Verification | PASS: per-domain verification contracts | PASS | Working as separate engines/CLIs | Not connected after a user action |
| Provenance | PASS: receipts/evidence schemas | PASS | Working per engine/evidence query | Citations visible; execution receipt absent |
| Rollback | PASS where domain applicable | PASS | School/ROAD engine APIs; BUILD process-local deactivation | No rollback UI |
| Activation | PASS for controlled BUILD model | PASS | Process-local BUILD registry/records | No hosted/interactable activation |
| Map visualization | PASS: portrayal/runtime-bundle contracts | PASS | MapLibre/PMTiles portrayal works; domain bundles internal | Yes for portrayal/synthetic School; no canonical action result |

## 15. Exact gaps and classifications

| Gap | Classification | Minimum evidence-based closure |
|---|---|---|
| No canonical request-to-domain dispatcher for School/ROAD/BUILD | **WIRING** | Connect canonical intent/plan output to a typed domain registry and at least two frozen domain adapters. |
| Canonical shared planner is not called by public/local production flow | **WIRING** | Use the shared proposal planner in the one runtime without weakening proposal-only semantics. |
| UI approval does not produce/consume canonical domain authorization | **WIRING** | Bridge approval to existing authorization boundary and retain fail-closed artifact validation. |
| Execution observation, verification, receipt, and provenance are separate endpoints/modules | **WIRING** | Orchestrate them into one response lifecycle and expose status/retry/idempotency coherently. |
| BUILD is absent from the runtime server/domain registry | **WIRING / RUNTIME** | Add a runtime adapter around the already controlled BUILD boundary; do not change its frozen contract. |
| No single lifecycle/session/orchestrator owns the cross-stage state | **RUNTIME** | Implement the minimum unified runtime state machine around existing contracts. |
| No user UI for ROAD/BUILD and no one result/receipt view | **UI** | Extend one current surface or provide one thin new surface for intent, approval, map/result, QA, and receipt. |
| No redistributable public execution data for two frozen domains | **DATA** | Define small public/synthetic fixtures that exercise the real adapters without copying the private archive. |
| Model-assisted routes require unavailable configuration | **ENVIRONMENT** | Document optional key behavior and retain a deterministic structured-input fallback; do not require paid calls for acceptance. |
| Full domain engines require GDAL/private inputs/pre-issued authorization | **ENVIRONMENT / DATA** | Package documented prerequisites and public acceptance fixtures, with explicit private-production separation. |
| Canonical current demo launch/status is not documented as one workflow | **DOCUMENTATION** | Document a single launch, URL/command, supported domains, prerequisites, and expected outputs. |
| Historical demo/RC manifests do not match current tracked artifacts | **DOCUMENTATION / WIRING** | Reconcile which current artifact is canonical during DEMO acceptance; do not mistake old snapshot tests for current readiness. |
| `jsonschema` required by focused tests is absent from declared dev dependencies | **ENVIRONMENT / DOCUMENTATION** | Declare or document the audit/test prerequisite in the future implementation task. |
| Frozen GEN contract support | **CONTRACT: NO GAP FOUND** | Existing generic proposal/authorization/execution/receipt boundaries are sufficient based on current evidence. |

## 16. Minimum completion plan

### Selected: Path C — Runtime + Acceptance Required

**DEMO-01 Unified Runtime** should be the smallest implementation task that:

1. chooses one canonical launch entry point;
2. connects actual user intent or a documented structured equivalent to the canonical planner;
3. routes to at least two frozen domains through a typed domain registry;
4. consumes existing authorization artifacts/boundaries without weakening them;
5. executes real adapters against public acceptance fixtures;
6. observes, verifies, and returns result + receipt + provenance;
7. renders a relevant map result; and
8. keeps invalid/unauthorized requests fail-closed.

**DEMO-02 E2E Acceptance** is required because this audit found disconnected components, private-data constraints, stale demo manifests, and no existing one-action trace. Acceptance should run from a fresh public clone and prove the complete trace for at least two domains, including a negative unauthorized case, without paid model calls or the private archive.

Then proceed to **DEMO-FINAL → NMA-FINAL**.

Path A is rejected because A1/A3/A6/A12 fail. Path B is insufficient because a cross-stage runtime lifecycle and public acceptance data are materially missing, not merely one import connection. Path D is not supported because no frozen contract blocker was found.

## 17. Recommended next task

> **NMA-DEMO-01 — Unified Runtime**

Scope it to runtime wiring against existing frozen contracts. Preserve School Hero, ROAD, BUILD, GEN, authorization, and receipt schemas. Require an explicit public-fixture strategy and deterministic structured fallback in its definition of done; defer broad UI polish and release evidence to DEMO-02/DEMO-FINAL.

## 18. Audit test and runtime evidence summary

No audit-specific tests were added. Existing tests and direct probes were sufficient, and avoiding a new test file kept the audit diff evidence-only.

| Check | Result |
|---|---|
| Fresh clone at exact baseline | PASS, clean, archive untracked and absent |
| Focused API/v0.32/Agentic VS2/School API tests | 23 passed |
| Standalone GEN-FINAL tests | 10 passed |
| Five demo scenes + negative controls | PASS |
| Offline and backup demo checks | PASS |
| Current demo-freeze check | FAIL, historical size drift |
| Current demo-RC1 check | FAIL, offline-runtime size drift |
| Compatibility server start/probes | PASS; no `/docs` UI |
| v0.32 server/browser start | PASS for evidence/synthetic portrayal |
| OpenAI-backed Agent request | Not called; route correctly reported missing key |
| School canonical direct route without auth | Fail-closed (`authorization_not_found`) |
| ROAD canonical direct route without archive | Fail-closed (`source_archive_missing`) |
| BUILD verification/activation without archive | Not reproducible; missing-file failure |
| ROAD authorization-consumption fixture check | PASS, test/evidence only |

## 19. Change accounting and finalization record

Expected and actual audit source impact:

| Change class | Count |
|---|---:|
| Production source changes | 0 |
| Runtime source changes | 0 |
| Frozen artifact changes | 0 |
| GEN changes | 0 |
| Historical test changes | 0 |
| Focused audit test additions | 0 |
| Evidence document additions | 1 |

Exact changed-file list before commit:

- `NMA-DEMO-00-Runtime-Readiness-Audit.md` — this evidence-only audit report

Finalization criteria for this report are:

| Final Git check | Required/verified outcome |
|---|---|
| Independent DEMO-00 commit | One evidence-only commit on `demo/demo-00-runtime-readiness-audit` |
| Local HEAD / upstream / remote branch | Exact equality after normal push |
| Final worktree status | Clean (`git status --porcelain=v1` has no output) |
| Tag / merge action | None |

The resulting commit SHA and the post-push equality/clean-status command output are reported in the task handoff, because a commit cannot contain its own final object ID.

## 20. Critical final question

### Where is the NMA demo, and what can a user actually do with it today?

There is **no unified NMA demo** today.

The closest current runnable user surface is the local v0.32 portrayal/School workbench:

```bash
PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/nmaAgentDemoV032.html?basemap=local`.

A user can ask bounded School portrayal/evidence questions, inspect citations and a trace, browse portrayal capabilities, propose/approve a non-mutating structured preview, and see tracked PMTiles/symbol content plus a synthetic School layer on a MapLibre map. With an OpenAI key and the private archive, the separate experimental real-layer flow can go further, but it still does not dispatch the canonical School Hero engine and it does not route to ROAD or BUILD.

The canonical public page, `nmaAgentDemo.html`, is an evidence-only portrayal experience. School Hero and ROAD are separately callable private-data-dependent internal execution pipelines; BUILD is a separately callable controlled internal module with static golden/evaluation pages. Architecture completeness, frozen tests, receipts, screenshots, and golden artifacts do not change that runtime fact.

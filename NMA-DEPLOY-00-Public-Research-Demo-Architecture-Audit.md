# NMA DEPLOY-00 — Public Research Demo Deployment Architecture & Safety Audit

**Audit date:** 2026-08-23 (Asia/Taipei)

**Audit branch:** `deploy/deploy-00-public-research-demo-audit`

**Canonical release:** annotated tag `nma-v1.0-final`

**Canonical release commit:** `eb87bde775333811529efb6f651573ea21cf456b`

**Deployment changes made by DEPLOY-00:** **0**

**Internet-facing deployment authorized by this report:** **No**

## 1. Verdict

> **PASS — PUBLIC NMA RESEARCH DEMO DEPLOYMENT ARCHITECTURE READY**

This is an **architecture-readiness verdict**, not authorization to publish a service. The frozen
NMA runtime and domain semantics do not need to change. A public deployment can be built as a new,
default-deny deployment adapter around the accepted NMA v1.0 artifacts and domain engines.

The current local server **must not** be placed directly on the Internet. It serves the repository
root, exposes experimental and mutation-capable routes, accepts a CLI host override, has no public
rate limiter or concurrency ceiling, and lacks the browser and HTTP hardening required for an
anonymous service. DEPLOY-01 must introduce a dedicated public gateway, dedicated UI, isolated
service account, read-only mounts, restricted route surface, and reverse proxy. Those are
deployment-boundary changes; they do not change the frozen NMA lifecycle, domain semantics,
GraphRAG evidence, authorizations, or accepted results.

The verdict is conditional on every DEPLOY-01 gate in this report passing. In particular, no public
go-live may occur until controlled-output display/redistribution authority is confirmed, the
fixture mount is verified, production authority is absent, the BUILD execution/activation surface
is structurally unreachable, and the public negative-security tests pass.

## 2. Canonical starting-point verification

| Check | Observed evidence | Result |
|---|---|---|
| Origin | `https://github.com/dongpo/topoMap.git` for fetch and push | PASS |
| Starting worktree | Clean on `freeze/nma-final-eb87bde` | PASS |
| Starting `HEAD` | `eb87bde775333811529efb6f651573ea21cf456b` | PASS |
| Tag type | `nma-v1.0-final` is an annotated tag | PASS |
| Local tag object | `f710da4828cd9ebf170fb60bd6af8f81e4e7abff` | PASS |
| Remote tag object | `f710da4828cd9ebf170fb60bd6af8f81e4e7abff` | PASS |
| Local peeled target | `eb87bde775333811529efb6f651573ea21cf456b` | PASS |
| Remote peeled target | `eb87bde775333811529efb6f651573ea21cf456b` | PASS |
| Release manifest | `data/specifications/nma-v1.0-final-release-manifest.json`; canonical self-hash `623860a18e82ad268ab389b417f3e9edc29c6c398b5dd923b37dbba3b2ba3bb4` | PASS |
| Frozen runtime files | UI/server/runtime SHA-256 values equal the release manifest | PASS |
| Release integrity suite | `14 passed` | PASS |
| Unified/controlled E2E suites | `32 passed, 1 skipped` | PASS |
| Audit branch base | Created from `nma-v1.0-final`; exact release commit | PASS |

The ignored private archive was present during the audit and matched both required properties:

* size: `12,822,898` bytes;
* SHA-256: `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.

It remained ignored, unstaged, and unmodified.

## 3. Research purpose and scope

The public demo exists to make the frozen NMA research proposition observable:

> Given controlled high-quality geospatial fixtures, an NMA Agent can use GraphRAG-retrieved
> cartographic knowledge to plan, authorize, execute, verify, and present rule-aligned map
> production through a governed and auditable lifecycle.

The deployment is a controlled research demonstrator. It is not a new product phase and not a
general geospatial service. Its scientific value comes from exposing the links among intent,
retrieved knowledge, plan, pre-existing authority, bounded execution, verification, provenance,
and the map result—not from accepting arbitrary data or prompts.

### 3.1 Supported hypotheses

| Hypothesis | Public evidence required | Deployment treatment |
|---|---|---|
| H1 — knowledge-grounded cartographic reasoning | Rule/node identifiers, reviewed citations, plan alignment, and portrayed result | Show a redacted typed evidence projection. Never expose hidden reasoning or unrestricted graph data. |
| H2 — governed execution | Distinct intent, plan, authorization, execution, verification, activation state | Render each lifecycle stage separately, including held/not-supported activation. |
| H3 — auditable agency | Request, plan, authorization, execution, QA, receipt, provenance identities | Provide an evidence drawer and downloadable public-safe JSON projection for the current session. |
| H4 — domain-general architecture | School, ROAD, and BUILD through one runtime/UI with domain-owned behavior | Use one gateway and UI; preserve the three frozen adapters/scenarios without generic mocks. |

### 3.2 Explicit non-goals

The public deployment must not provide:

* arbitrary file, Shapefile, URL, GeoJSON, or open-data upload;
* arbitrary dataset, layer, feature, path, CRS, schema, or domain selection;
* geospatial ETL, schema inference, CRS repair, topology repair, or source writeback;
* free-form tool calls, arbitrary Cypher, arbitrary subprocess arguments, or shell access;
* new anonymous authorizations;
* production editing, publication, activation, or credentials;
* a generic autonomous map-generation API.

## 4. Public user experience

### 4.1 Recommended input mode

Use **Mode B — Guided Scenario Input as the authoritative path**, plus a tightly bounded form of
**Mode A — Bounded Natural Language** for demonstration value.

The UI presents three scenario cards and a small set of allowed request phrasings/parameters. A
visitor may either select a scenario or enter a paraphrase. The gateway maps input to exactly one
closed scenario ID. It accepts no file/path/URL and no execution, authorization, feature, layer, or
tool parameter from the visitor. Ambiguous, multi-domain, or out-of-scope text fails closed.

The bounded-language classifier should be deterministic for v1.0. It may show how the accepted
intent was selected, but it must not imply that arbitrary language or arbitrary work is supported.

### 4.2 What a visitor can do

1. Open one HTTPS URL.
2. Select School, ROAD, or BUILD, or enter a bounded paraphrase of one accepted request.
3. See the selected domain and controlled scenario identity.
4. Inspect the public-safe GraphRAG/rule evidence and its link to the plan.
5. Inspect the frozen or deterministically reconstructed plan.
6. See the existing authorization identity and its bounded scope.
7. Trigger the bounded scenario run.
8. Inspect execution/replay status, verification/QA, receipt, and provenance.
9. Inspect the MapLibre result.
10. Restart the presentation session without creating new authority or changing a fixture.

“Run” has a precise meaning. For School and ROAD it invokes the exact server-held authorization and
fixed accepted idempotency key in a dedicated demo state, returning the same content-addressed
execution on repeat calls. For BUILD it validates and replays the already accepted BUILD package;
it never invokes the BUILD implementation or activation path. The UI must label repeat calls as
**idempotent controlled execution/replay**, not as new production work.

### 4.3 What a visitor cannot do

A visitor cannot upload or select data, name a server path, choose an arbitrary layer or feature,
change a portrayal, submit authorization material, create an authorization, choose an idempotency
key, call internal routes, run BUILD implementation, activate production, retrieve raw fixtures,
modify repository or source data, retrieve secrets, or request an unsupported task.

## 5. Accepted scenarios exposed

| Scenario ID | Frozen input/result | Public run behavior | Public evidence |
|---|---|---|---|
| `school-v1` | Six MARK layers; `TERRAINID=9920103`; 15 valid Points; fixture aggregate `77802b44…fc12d`; blue accepted School portrayal | Exact server-held School demo authorization and fixed idempotency key; derived-only output; repeated calls return the same accepted identity | GraphRAG nodes, plan `plan-8d174b62fb63189987eafdb6`, authorization `authorization-school-demo-b4ecdbfc35ecaf73293ed497`, QA/provenance, receipt, MapLibre result |
| `road-v1` | Exact K14_ROAD package; 196 features; frozen segments `K0000004671`, `K0000004913`, `K0000005348`; vertex counts 4/3/4; line-following `中山街` | Exact ROAD authorization and accepted idempotency key; source read-only; deterministic accepted execution/replay only | Reviewed ROAD evidence IDs and nodes, plan `road-plan-cd434d50bd5b49a012bd1e10`, authorization, geometry/portrayal QA, receipt/provenance, MapLibre result |
| `build-v1` | Frozen accepted BUILD package; normalized public demo geometry; diagonal hatch; activation held | Validation and replay only. Live BUILD `execute` is not mounted and not callable. | Mapping-rule evidence with honest GraphRAG `not-applicable` boundary from accepted evaluation, plan/auth/receipt identities, source commitments, verification, activation `held-not-requested`, MapLibre result |

BUILD must not be presented as having GraphRAG evidence that the accepted record marks
`PASS_NOT_APPLICABLE`. The UI should show the frozen mapping-rule evidence and the explicit
GraphRAG applicability boundary. This is more scientifically accurate than fabricating a common
evidence path.

## 6. Current runtime Internet-facing audit

### 6.1 Summary findings

| Concern | Current canonical state | Internet consequence |
|---|---|---|
| Binding | Defaults to `127.0.0.1:8080`; CLI permits another host | Default is local-safe, but `--host 0.0.0.0` can expose it. Do not use this server as the public listener. |
| HTTP stack | `ThreadingHTTPServer` + `SimpleHTTPRequestHandler` | Development/reference stack; thread creation has no service-level concurrency limit. |
| Static serving | Handler root is the repository root; unmatched GET falls through to static serving/directory behavior | Critical public exposure risk. Source, manifests, artifacts, ignored files, and any `.env.local` placed in the root could become readable. `.env.local` was absent during this audit, but the architecture is unsafe. |
| API surface | Unified route plus numerous experimental, dataset, proposal, execution, observation, and rollback routes | Far broader than the research demo requires. |
| Body limit | `32,768` bytes for POST | A useful local bound, but proxy/gateway should reduce to 16 KiB and validate schemas before dispatch. |
| Request validation | Many routes use closed JSON shapes; unified request text limited to 500 characters | Good frozen fail-closed behavior, but direct public exposure still permits capabilities that should not exist publicly. |
| CORS | No permissive CORS header | Same-origin by default is useful. Explicitly reject unexpected `Origin`; do not add wildcard CORS. |
| Security headers | No CSP, HSTS, frame, MIME, permissions, or referrer policy from the local handler | Must be added at nginx and supported by the new UI. |
| Authentication | None | Acceptable only for a strictly bounded anonymous demo with no production authority and strong abuse controls. |
| Sessions | Agent sessions have turn/TTL limits; proposal stores have record caps; unified requests are not session-authorized | Useful local controls, not a complete anonymous abuse boundary. Session store can accumulate unique IDs until touched/pruned. |
| Timeouts | OpenAI/embedding/entity calls use 60–120 second timeouts; GDAL calls use 30–60 seconds; HTTP handler has no overall deadline | Add end-to-end deadlines and worker concurrency limits. |
| Subprocesses | Fixed-list GDAL/OGR invocations; no shell; bounded timeouts | Arguments are mostly server-derived, but all legacy real-layer/QA routes must be disabled. Run in an isolated service. |
| Paths | Most paths are server constants; route execution IDs allow `.` and `:` and are joined into runtime paths | Do not expose raw execution-ID filesystem lookups. Public IDs must be gateway-owned opaque IDs mapped to exact accepted records. |
| Writes | Execution, verification, observations, rollback, real-layer, QA repair, caches, ledgers, and proposal flows can write beneath repository artifact paths | Incompatible with a read-only public release checkout and much broader than needed. |
| Errors | Known errors are structured; unknown errors return a generic message | Good baseline, but internal known-error text can still reveal implementation detail; gateway needs a public error vocabulary. |
| Logging | Standard request log only; no structured lifecycle/security metrics | Insufficient for operations, abuse detection, or research evaluation. |
| Secrets | Server loads `OPENAI_API_KEY`, graph/Neo4j settings, and `.env.local` | Direct repository static serving creates an unacceptable secret-exposure combination. |
| GraphRAG | Canonical JSON or verified Neo4j backend; provider-backed query embeddings/LLM resolver on live semantic path | Accepted scenario-bound retrieval can be deterministic and local; live external model access is avoidable. |
| UI | Unified lifecycle page shows plan/auth/execution/receipt fields and map, but not adequate GraphRAG evidence; uses unescaped `innerHTML` facts and remote MapLibre/glyph resources | Presentation and XSS/supply-chain gaps require a bounded new public UI. |
| Docker/Compose | Existing image launches the older `nma serve` compatibility API on `0.0.0.0`; Compose maps port 8000 | Not the frozen unified public-demo topology and must not be reused as-is. |

### 6.2 Current route classification

Classification applies to the current `scripts/run_nma_agent_server.py`, not the proposed gateway.
`PUBLIC_WITH_RESTRICTIONS` means the capability may be represented only through a new redacting,
scenario-bound gateway; it does not authorize direct proxying.

| Method and current route | Current function | Classification | Public treatment |
|---|---|---|---|
| GET `/api/nma/runtime` | Unified capability metadata | PUBLIC_WITH_RESTRICTIONS | Project only safe metadata through `/nma/api/v1/scenarios`; omit direct operation/authorization controls. |
| POST `/api/nma/runtime` | Preview/replay/execute/verify for three domains | INTERNAL_ONLY | Gateway constructs requests from a closed scenario table. Never proxy caller JSON. BUILD execute forbidden. |
| GET `/api/hero/school/evidence` | School evidence package | PUBLIC_WITH_RESTRICTIONS | Return a redacted evidence projection with allowlisted fields and bounded node/citation counts. |
| GET `/api/agent/status` | Key/model/backend and graph status | INTERNAL_ONLY | Replace with minimal liveness/readiness routes; do not disclose paths, model, graph backend, or credential state. |
| POST `/api/agent` | LLM intent routing/session orchestration | DISABLE_FOR_PUBLIC_DEMO | Baseline public demo uses deterministic bounded intent mapping. |
| POST `/api/school-agent/analyze` | Dataset-backed School analysis | DISABLE_FOR_PUBLIC_DEMO | Outside accepted public scenario and dependent on configurable datasets. |
| POST `/api/portrayal-review` | Portrayal proposal orchestration | DISABLE_FOR_PUBLIC_DEMO | Allows public proposal generation outside accepted scenario. |
| POST `/api/portrayal-review/decision` | Decide a proposal | DISABLE_FOR_PUBLIC_DEMO | Anonymous visitors cannot approve new portrayal proposals. |
| POST `/api/portrayal-review/preview` | Compile proposal preview | DISABLE_FOR_PUBLIC_DEMO | Not required by the frozen scenario presentation. |
| POST `/api/portrayal-review/maplibre` | Compile MapLibre proposal | DISABLE_FOR_PUBLIC_DEMO | Not required; accepts proposal/source-binding state. |
| POST `/api/real-layer` | LLM/GDAL real-layer proposal | DISABLE_FOR_PUBLIC_DEMO | Arbitrary public real-layer workflow is a non-goal. |
| POST `/api/real-layer/execute` | Materialize derived layer | DISABLE_FOR_PUBLIC_DEMO | Write/subprocess surface; outside exact scenario gateway. |
| POST `/api/qa-review` | Diagnose and propose repair | DISABLE_FOR_PUBLIC_DEMO | Repair workflow is an explicit non-goal. |
| POST `/api/qa-review/execute` | Execute QA repair | DISABLE_FOR_PUBLIC_DEMO | Mutation/write surface; forbidden. |
| GET `/api/datasets/{id}/inspect` | Inspect bundled dataset | DISABLE_FOR_PUBLIC_DEMO | Dataset API is outside scope. |
| GET `/api/datasets/{id}/geojson` | Export bundled dataset | DISABLE_FOR_PUBLIC_DEMO | Prevent dataset enumeration/export and GDAL cost. |
| POST `/api/school-hero/executions` | Direct authorization consumption/execution | INTERNAL_ONLY | Only gateway-owned exact authorization/key may invoke it; no caller fields pass through. |
| GET `/api/school-hero/executions/{id}` | Receipt | PUBLIC_WITH_RESTRICTIONS | Project the exact session result; do not expose raw execution-ID path lookup. |
| GET `/api/school-hero/executions/{id}/bundle` | MapLibre bundle | PUBLIC_WITH_RESTRICTIONS | Return validated allowlisted bundle only. |
| GET `/api/school-hero/executions/{id}/data` | Derived School data | PUBLIC_WITH_RESTRICTIONS | Require display authority; expose only exact accepted derivative, not raw fixture. |
| POST `/api/school-hero/executions/{id}/observations` | Persist observation | DISABLE_FOR_PUBLIC_DEMO | Browser cannot write canonical runtime observations. |
| POST `/api/school-hero/executions/{id}/rollback` | Persist rollback record | DISABLE_FOR_PUBLIC_DEMO | No public rollback/mutation route. |
| POST `/api/road/executions` | Direct frozen ROAD execution | INTERNAL_ONLY | Gateway-owned exact authorization/key only. |
| GET `/api/road/executions/{id}` | Receipt | PUBLIC_WITH_RESTRICTIONS | Redacted session projection only. |
| GET `/api/road/executions/{id}/bundle` | MapLibre bundle | PUBLIC_WITH_RESTRICTIONS | Exact validated accepted bundle only. |
| GET `/api/road/executions/{id}/data` | Derived ROAD data | PUBLIC_WITH_RESTRICTIONS | Require display authority; exact three-segment derivative only. |
| POST `/api/road/executions/{id}/observations` | Persist observation | DISABLE_FOR_PUBLIC_DEMO | Browser cannot persist domain observations. |
| POST `/api/road/executions/{id}/rollback` | Persist rollback | DISABLE_FOR_PUBLIC_DEMO | No public rollback route. |
| GET any unmatched path | Repository-root static server/directory fallback | DISABLE_FOR_PUBLIC_DEMO | Replace with exact static allowlist; return 404 for everything else. |
| GET exact current demo HTML/assets | Local UI/assets | PUBLIC_WITH_RESTRICTIONS | Use a new hardened UI and self-hosted, content-pinned assets. |

No current route is classified `PUBLIC_SAFE` for direct Internet exposure.
No inspected route remains `UNRESOLVED`; every current route/pattern is assigned above. The
proposed gateway routes do not inherit these classifications until their DEPLOY-01 tests pass.

## 7. Recommended deployment topology

```text
Public Internet
    |
    v
Cloudflare DNS/WAF/TLS edge
    |  HTTPS only; coarse abuse/rate rules
    v
nginx dedicated vhost: demo.geomni.tw
    |  exact /nma/ allowlist; headers; limits; logs
    |  Unix domain socket only
    v
nma-demo.service (user nma-demo; no network egress)
    |
    +-- Public demo gateway (new deployment adapter)
    |      +-- bounded intent/scenario registry
    |      +-- public evidence projection
    |      +-- frozen UnifiedNMARuntime/domain adapters
    |      +-- startup identity verification
    |
    +-- read-only canonical release /opt/nma-demo/releases/eb87bde.../
    +-- read-only fixtures /srv/nma-demo/fixtures/nma-v1.0/
    +-- read-only GraphRAG/rule assets /srv/nma-demo/assets/nma-v1.0/
    +-- read-only demo authority /srv/nma-demo/authority/nma-v1.0/
    +-- bounded runtime state /var/lib/nma-demo/runtime/
    +-- private temporary output /var/lib/nma-demo/tmp/
    +-- structured logs/metrics via journald

Explicitly absent:
    production data mounts
    production authorization/activation stores
    production credentials
    Docker/host socket
    arbitrary outbound network access
```

### 7.1 Trust boundaries

* **Public:** Cloudflare-facing URL, hardened static UI, and six allowlisted API route families.
* **Proxy trust boundary:** nginx terminates origin HTTPS or accepts authenticated Cloudflare origin
  traffic, enforces path/body/rate/time constraints, and proxies only to a Unix socket.
* **Application trust boundary:** the gateway converts untrusted input into one of three immutable
  scenario IDs. Caller JSON is never forwarded to domain engines.
* **Controlled-data boundary:** fixtures, graph assets, release files, and demo authority are
  read-only and root-managed.
* **Write boundary:** only disposable/session output and structured logs. Nothing under the release,
  fixtures, GraphRAG, authority, or production paths is writable.

### 7.2 URL recommendation

`https://demo.geomni.tw/nma/` is appropriate **if** `demo.geomni.tw` is a dedicated demo vhost and
nginx denies every path except the exact `/nma/` surface. `/nma` should return a single 308 redirect
to `/nma/`, and all application/API paths must stay beneath `/nma/`.

Read-only checks on 2026-08-23 found:

* `demo.geomni.tw` did not resolve in DNS;
* `geomni.tw` resolved, served HTTPS through Cloudflare, and returned HTTP 200;
* no nginx/systemd/Cloudflare configuration for the candidate NMA service exists in this repository.

Therefore the candidate is a planned target, not existing infrastructure. If `demo.geomni.tw` will
host unrelated applications or share cookies/security policy, the technically safer alternative is
the dedicated origin `https://nma-demo.geomni.tw/`. A separate origin reduces cross-application
XSS, cookie, service-worker, CSP, and routing blast radius. DEPLOY-01 must record which model is
selected; this report prefers the proposed URL only under a dedicated-vhost invariant.

No WebSocket is required. Use ordinary JSON HTTP requests.

## 8. Public API design

### 8.1 Allowlist

| Method | Public route | Purpose | Constraints |
|---|---|---|---|
| GET | `/nma/` | Hardened demo UI | Exact file; no directory listing. |
| GET | `/nma/assets/{fingerprinted-name}` | JS/CSS/MapLibre/glyph/image assets | Build-time manifest allowlist; immutable cache; no arbitrary filesystem mapping. |
| GET | `/nma/api/v1/health/live` | Process liveness | Returns only `{"status":"ok"}` and release ID. |
| GET | `/nma/api/v1/health/ready` | Startup readiness | Returns ready/not-ready and coarse failing component code; no paths/hashes/secrets. |
| GET | `/nma/api/v1/scenarios` | Three public scenario cards | Static public-safe metadata only. |
| POST | `/nma/api/v1/runs` | Submit scenario ID or bounded text and trigger exact run | JSON only; max 16 KiB at proxy, schema max 2 KiB, text max 500 chars; no caller auth/paths/URLs/feature IDs. |
| GET | `/nma/api/v1/runs/{public_run_id}` | Lifecycle/result projection | 128-bit opaque ID, session-bound, TTL, fixed schema. |
| GET | `/nma/api/v1/runs/{public_run_id}/evidence` | Redacted rules, plan, QA, receipt, provenance | Allowlisted fields/counts; no raw graph dump, filesystem path, prompt, token, or hidden reasoning. |
| GET | `/nma/api/v1/runs/{public_run_id}/map` | Validated MapLibre/GeoJSON result | Same-origin only; exact accepted result; size/count/geometry/style schema validation. |

`POST /runs` accepts either:

```json
{"scenario_id":"school-v1","input_type":"guided"}
```

or:

```json
{"request":"Show the accepted School mapping lifecycle.","input_type":"bounded-natural-language"}
```

No other keys are accepted. The response never echoes arbitrary HTML and never accepts or returns
a server path.

### 8.2 Explicit deny list

nginx and the gateway must return 404 (or 405 for a wrong method on an allowlisted path) for:

* all current `/api/*` routes;
* `/admin`, `/debug`, `/docs`, `/openapi.json`, `/metrics` from the public network;
* dotfiles, repository files, source code, manifests not explicitly projected, directory listings,
  and backup/temp suffixes;
* upload, dataset, file, path, URL-fetch, query/Cypher, authorization-creation, observation,
  rollback, activation, repair, writeback, or subprocess routes;
* arbitrary execution IDs and raw fixture/GraphRAG asset paths;
* all methods except allowlisted GET and POST; `TRACE` always disabled.

Metrics may listen on a separate Unix socket or loopback-only operator endpoint and must not be
proxied publicly.

## 9. Fixture deployment model

### 9.1 Mount and identity

Place the owner-supplied controlled archive outside Git at:

`/srv/nma-demo/fixtures/nma-v1.0/112年多維度SHP成果_0502.zip`

The parent directory is root-owned; the file is readable by the `nma-demo` group and not writable
by the service. Bind-mount it read-only with `nodev,nosuid,noexec`. Do not copy it into the public
web root, container image, Git repository, session output, logs, or downloadable artifact.

At every service start, before readiness becomes true:

1. verify archive size `12,822,898` and SHA-256 `4888dbf9…da53`;
2. open it read-only and reject unsafe/absolute/parent-path members;
3. verify the exact six School layers and aggregate `77802b44…fc12d`;
4. verify `TERRAINID=9920103`, layer distribution `0/1/0/12/1/1`, 15 valid unique Points,
   expected CRS, and required label fields;
5. verify exact K14_ROAD components, aggregate `dc82db8b…ae79`, 196 features, selected IDs,
   4/3/4 vertices, source-geometry hashes, class, route, and name;
6. verify the accepted BUILD package and all source/geometry/attribute commitments used by replay;
7. compare all checked identities with the final release manifest and a deployment manifest;
8. fail readiness and refuse scenario runs on any difference.

No public request can choose this path, trigger replacement, or change validation parameters.

### 9.2 Public display/data governance gate

The archive itself is never redistributed. Public MapLibre responses contain only the exact,
reviewed derived display data required for the three scenarios. Before go-live, the owner must
record permission to display the School derivative and exact three-segment ROAD derivative. The
current ROAD replay text intentionally says frozen ROAD geometry is not redistributed; DEPLOY-01
must not silently override that boundary. If display authority is not documented, public go-live
is blocked even though implementation and offline acceptance may continue.

## 10. GraphRAG deployment and evidence projection

### 10.1 Required assets

The accepted scenario evidence path requires the canonical graph and reviewed supporting assets,
including:

* `data/knowledge/nma-canonical-graph-v0.4.json` — about 6.2 MiB;
* citation registry, retrieval anchors, approved semantic links, entity-resolution support, and
  reviewed geometry-role source;
* accepted scenario/evaluation records that bind School and ROAD evidence/node IDs to plans and
  execution evidence;
* optionally, `data/runtime/vector/nma-vector-index-v0.32.json` — about 12 MiB, 4,293 records,
  512 dimensions—only if live semantic query retrieval is separately enabled.

Observed process memory during this audit:

* loading the canonical graph retriever added about 52 MiB RSS;
* loading the full Python vector index added about 145 MiB RSS;
* a deterministic scenario-bound service should fit within a 512 MiB service limit;
* a later live vector/LLM mode should receive a separate capacity test and preferably a 1 GiB
  limit rather than weakening the deterministic service limit.

### 10.2 Baseline strategy

Use the canonical JSON graph locally and deterministically traverse from the exact accepted node
IDs stored in the frozen scenario evidence. Verify graph identity at startup. Produce a typed,
bounded evidence package at run time, then project only:

* reviewed rule/node IDs and types;
* short public-safe rule summaries;
* reviewed citation ID, document label, and page where disclosure is permitted;
* typed graph relationships relevant to the plan;
* which evidence IDs are used by which plan fields;
* graph/release identity status and retrieval mode.

This is not canned output: the service validates the canonical graph, verifies the accepted seeds,
performs typed traversal, validates citation containment, and joins the result to the frozen plan.
The UI must label it `deterministic accepted-scenario GraphRAG path`. If any asset or relationship
is missing or changed, it fails closed. It must not substitute hard-coded prose.

Do not expose raw graph dumps, unrestricted node lookup, arbitrary Cypher, vector contents,
internal prompts, model chain-of-thought, Neo4j credentials/addresses, or local paths.

## 11. LLM exposure strategy

**Classification for the public v1.0 baseline: avoidable using the deterministic accepted path.**

No `OPENAI_API_KEY`, embedding request, external LLM, or Neo4j service is required for the three
accepted public scenarios. This gives predictable cost/latency, removes prompt-exfiltration risk,
prevents arbitrary prompt abuse, and preserves repeatability. It still demonstrates accepted Agent
reasoning by exposing the content-addressed intent/evidence/plan/authorization lineage.

Live LLM mode may be evaluated later, but is outside DEPLOY-01. If separately authorized, it needs
a distinct configuration and tests: server-only key, egress allowlist, per-IP and global budgets,
token ceilings, max 500-character input, closed tool schema, no caller tool/domain parameters,
output validation, timeouts, cost alarms, and deterministic fail-closed behavior. It must never
silently replace a failed GraphRAG call with canned evidence.

## 12. Authorization and production isolation

### 12.1 Public authorization model

Use **server-held exact demo authority** with a closed scenario lookup:

| Domain | Public authorization treatment |
|---|---|
| School | Server holds the accepted authorization `authorization-school-demo-b4ecdbfc35ecaf73293ed497` read-only and uses the fixed accepted idempotency key. UI shows identity, human approval, exact fixture/scope binding, no writeback, and no activation. |
| ROAD | Server holds the frozen ROAD authorization and fixed accepted idempotency key. UI shows its identity and exact K14/segment/portrayal scope. |
| BUILD | Server exposes only the already consumed accepted demo authorization inside the frozen execution package. No BUILD authorization or policy hash is accepted from the browser. |

Anonymous visitors never create, upload, modify, select, or consume a new authorization. Public
run IDs are presentation/session identities, not domain authorizations.

### 12.2 Isolation invariants

* Dedicated `nma-demo` Unix user with no login and no production group membership.
* Dedicated service, Unix socket, state directory, fixture mount, and demo authority directory.
* No production datastore, filesystem, API, queue, VPN route, host, token, certificate, IAM role,
  activation store, or writeback credential mounted or configured.
* Network egress denied for the baseline service; nginx is reached through a Unix socket.
* Release, fixtures, GraphRAG assets, and demo authority read-only.
* Domain execution writes only to the dedicated disposable runtime state.
* Public gateway has no route or callable branch for BUILD implementation/activation.
* Any environment variable whose name indicates production/activation/writeback causes startup
  failure; absence is verified, not assumed.

### 12.3 BUILD activation prevention

BUILD safety must be structural:

1. the gateway scenario registry maps `build-v1` only to frozen-package validation/replay;
2. it never constructs `operation=execute` for BUILD;
3. no BUILD source/production authorization/activation credentials or stores are mounted;
4. BUILD production/activation modules are not exported as gateway tools;
5. service filesystem denies production paths;
6. service egress denies production APIs;
7. startup reports `production_activation_capability=not-mounted`;
8. negative tests attempt BUILD execution, policy-hash submission, activation fields, direct route
   access, module-level bypass, and path access, and must all fail without mutation.

The required state is **disabled/not mounted**, not “button hidden.”

## 13. Browser and HTTP security

### 13.1 Current UI gaps

`nmaAgentDemoV1.html` exposes lifecycle fields but does not provide an adequate GraphRAG evidence
view. Its `facts()` function inserts server values into `innerHTML` without escaping; warnings are
also interpolated. It loads MapLibre CSS/JS from `unpkg.com`, glyphs from
`demotiles.maplibre.org`, and accepts server-provided source/resource paths. These are unacceptable
for the public baseline without a stronger response schema and CSP-compatible implementation.

DEPLOY-01 must create a separate public UI. It must:

* use DOM `textContent`/element construction for untrusted values;
* prohibit dynamic HTML and sanitize any unavoidable markup with a pinned audited sanitizer;
* accept only same-origin relative result paths matching the public API pattern;
* validate GeoJSON type, feature count, geometry type, coordinate bounds/finite values, property
  allowlist, style keys, and resource IDs before passing data to MapLibre;
* self-host pinned MapLibre JS/CSS, glyphs, and images with integrity recorded in the deployment
  manifest;
* never log tokens, full evidence packages, fixture contents, or server errors to the console;
* avoid persistent service workers initially; if added later, scope them to `/nma/` and test cache
  isolation and emergency invalidation;
* store no credential in browser storage; use an anonymous HttpOnly/Secure/SameSite session cookie
  only if session binding is needed.

### 13.2 Required security headers

At nginx, with a UI that contains no inline script/style:

```text
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; manifest-src 'self'; upgrade-insecure-requests
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
Cache-Control: no-store
```

Fingerprint static assets may use `Cache-Control: public, max-age=31536000, immutable`; API,
HTML, evidence, map, and errors remain `no-store`. Do not enable wildcard CORS. Validate the
`Origin` header on POST as exactly the selected public origin and require JSON content type.

## 14. Reverse proxy controls

Use Cloudflare for DNS/TLS/WAF/coarse abuse controls and nginx for origin enforcement. The Python
service listens only on `/run/nma-demo/nma-demo.sock`; no host TCP port is exposed.

Required nginx behavior:

* exact dedicated `server_name` and HTTPS; HTTP redirects to HTTPS;
* `/nma` -> `/nma/` with 308;
* exact location allowlist under `/nma/`; `location / { return 404; }` on the dedicated vhost;
* `client_max_body_size 16k` and reject chunked/unsupported bodies at the gateway schema layer;
* `proxy_connect_timeout 3s`, `proxy_send_timeout 10s`, `proxy_read_timeout 90s`;
* buffering enabled; cap upstream response sizes in the gateway;
* no WebSocket upgrade forwarding;
* hide upstream `Server`; do not expose Python version;
* health checks call readiness locally; Cloudflare checks only a coarse public health endpoint;
* separate limits: static, result GET, and run POST;
* real client IP accepted only from current Cloudflare address ranges; direct origin access denied
  by firewall/security group where available;
* sanitized access log with request ID, route template, status, bytes, and latency—not request body,
  query string, evidence, fixture data, authorization, or cookies.

## 15. Process and filesystem isolation

### 15.1 `nma-demo.service`

Recommended unit properties:

* `User=nma-demo`, `Group=nma-demo`, `UMask=0077`;
* `WorkingDirectory=/opt/nma-demo/releases/eb87bde775333811529efb6f651573ea21cf456b`;
* `EnvironmentFile=/etc/nma-demo/nma-demo.env` (root-owned, `0640`);
* `RuntimeDirectory=nma-demo`, `StateDirectory=nma-demo`, `LogsDirectory=nma-demo` if file logs are
  needed; prefer journald;
* `ExecStartPre` runs startup identity validation; nonzero exit prevents service start;
* `ExecStart` launches the dedicated public gateway on the Unix socket;
* `Restart=on-failure`, bounded restart delay/burst; no restart loop on identity failure;
* `NoNewPrivileges=true`, `PrivateTmp=true`, `PrivateDevices=true`, `ProtectSystem=strict`,
  `ProtectHome=true`, `ProtectKernelTunables=true`, `ProtectKernelModules=true`,
  `ProtectControlGroups=true`, `LockPersonality=true`, `RestrictSUIDSGID=true`;
* `RestrictAddressFamilies=AF_UNIX` for deterministic baseline; no network egress;
* syscall filtering compatible with Python/GDAL, tested fail-closed;
* `MemoryMax=512M`, `TasksMax=64`, `CPUQuota=200%`, file descriptor limit appropriate to four
  workers/sessions;
* graceful stop deadline; remove stale Unix socket on restart.

### 15.2 Filesystem matrix

| Path class | Recommended path | Mode | Purpose |
|---|---|---|---|
| Release/runtime | `/opt/nma-demo/releases/eb87…/` | read-only | Frozen code, schemas, accepted records, public UI manifest |
| Fixtures | `/srv/nma-demo/fixtures/nma-v1.0/` | read-only mount | Exact controlled archive; never web-served |
| GraphRAG/rules | `/srv/nma-demo/assets/nma-v1.0/` | read-only mount | Canonical graph and reviewed evidence assets |
| Demo authority | `/srv/nma-demo/authority/nma-v1.0/` | read-only mount | Exact School/ROAD demo authorizations and accepted BUILD package |
| Runtime state | `/var/lib/nma-demo/runtime/` | service-write, quota/TTL | Idempotency ledger and exact derived demo execution state only |
| Temporary output | `/var/lib/nma-demo/tmp/` or private `/tmp` | service-write, noexec, quota/TTL | Atomic staging; cleaned safely |
| Logs | journald / `/var/log/nma-demo/` | append/operator-controlled | Structured operational events; no fixture contents |
| Production paths | all | absent and denied | No mounts, credentials, sockets, or write permissions |
| Repository checkout metadata | `.git`, developer worktree | absent from runtime image or denied | Public service cannot mutate or enumerate Git/repository state |

Set filesystem quotas and clean only known session directories older than the retention window.
Never run a broad recursive deletion against an unresolved path.

## 16. Rate limiting, concurrency, and abuse controls

Initial conservative limits for an anonymous research demo:

| Control | Initial value | Behavior |
|---|---|---|
| POST `/runs` per IP | 5/minute, burst 2 | HTTP 429 with `Retry-After`; no run created when rejected |
| Result/evidence/map GET per IP | 30/minute, burst 10 | 429 after burst |
| Static requests | 120/minute per IP | Cloudflare/nginx cache where safe |
| Per-IP active runs | 1 | Second run gets 429/service-busy |
| Global active runs | 4 | Queue at most 4 for at most 2 seconds; otherwise 503 service-busy |
| Scenario runs per anonymous session | 20/hour | Session resets do not grant production authority |
| Request JSON | nginx 16 KiB; schema 2 KiB; text 500 chars | Reject before expensive work |
| Graph traversal | accepted seeds only; bounded depth/nodes | Reject any caller-supplied seed/depth/count |
| Domain execution deadline | 60 seconds | Cancel/fail safely; clean only own staging directory |
| End-to-end request deadline | 90 seconds | Public `execution_failed`/`service_busy`; no stack trace |
| LLM calls | 0 in baseline | No external-model abuse/cost surface |

Cloudflare should add bot/challenge rules for obvious automation and high-volume sources, but the
origin must remain safe if Cloudflare controls fail. Limits must be load-tested and adjusted from
observed latency without broadening functional scope.

## 17. Observability and research logging

### 17.1 Operational events and metrics

Emit structured events with a request ID and coarse error code:

* request accepted/rejected, route template, scenario/domain, input type;
* scenario selection/ambiguity/unsupported result;
* GraphRAG startup and retrieval validation status/latency;
* plan, authorization lookup, execution/replay, verification, and presentation status/latency;
* fixture/asset identity failure without sensitive path/content;
* HTTP/browser error code, rate-limit event, concurrency rejection, timeout, worker restart;
* BUILD invariant value `activation_capability=not-mounted` at startup and in readiness checks.

Metrics should include request/run counts, domain counts, success/failure by coarse stage, p50/p95
latency, GraphRAG latency, execution latency, verification outcome, rate-limit events, busy events,
startup validation state, active runs, and process CPU/memory. Alert on identity failure, any BUILD
activation invariant failure, repeated 5xx, sustained rate limiting, or resource exhaustion.

### 17.2 Research-evaluation record

Record only:

* random anonymous session ID (rotated; not a fingerprint);
* timestamp bucket;
* selected scenario/domain;
* guided vs bounded-language input type;
* bounded intent classification outcome (not raw free text by default);
* retrieved public rule/node IDs;
* plan ID;
* authorization outcome/identity class;
* execution/replay, verification, and task-completion outcomes;
* stage latencies and public error code.

Do not store raw prompts by default, IP addresses in the research dataset, user-agent fingerprints,
precise location, cookies beyond the anonymous session, fixture records, credentials, hidden model
traces, or unnecessary personal data. Proxy security logs and de-identified research records must
be separate. Recommended initial retention: security access logs 14 days; detailed anonymous
research events 30 days; aggregate metrics 90 days, subject to owner policy.

Display a concise privacy notice. This logging does not start human-subject research. Recruitment,
consent, experimental assignment, questionnaires, and publication of user-study results require a
separate ethics/privacy review.

## 18. Public-safe failure behavior

| Condition | Status | Public code/message |
|---|---:|---|
| Unknown scenario/out-of-scope text | 400 | `scenario_unsupported` — “This public demo supports only the accepted School, ROAD, and BUILD scenarios.” |
| Ambiguous/multi-domain request | 400 | `request_ambiguous` — “Choose one supported scenario or clarify the bounded request.” |
| Invalid JSON/body/schema | 400/413/415 | `invalid_request` — “The request format is not supported.” |
| Fixture hash/startup failure | 503 | `fixture_unavailable` — “The controlled fixture is unavailable; no execution occurred.” |
| Graph/rule identity failure | 503 | `evidence_unavailable` — “Verified mapping-rule evidence is unavailable; the run was stopped.” |
| Demo authorization missing/mismatch | 503 | `authorization_unavailable` — “The accepted demo authorization is unavailable; no execution occurred.” |
| Execution failure/timeout | 422/504 | `execution_failed` — “The bounded demo execution did not complete; no production action occurred.” |
| Verification failure | 422 | `verification_failed` — “Verification did not pass; the result is withheld.” |
| Rate/concurrency limit | 429/503 | `rate_limited` / `service_busy` — retry guidance |
| Unknown server error | 500 | `internal_error` — “The demo could not complete the request.” plus request ID |

Never expose exception text, tracebacks, source/fixture paths, hashes not intended as public
provenance, environment values, credentials, model tokens, upstream bodies, Python/server version,
or proxy configuration.

## 19. Deployment readiness matrix

| Concern | Current state | Public risk | Required action | DEPLOY-01 gate |
|---|---|---|---|---|
| Runtime | Frozen unified runtime passes; hosted by local all-in-one server | Local server is Internet-unsafe | New restrictive gateway; import/reuse frozen adapters without semantic edits | Gateway positive/negative contract tests pass |
| UI | Lifecycle/map visible; GraphRAG view insufficient | XSS sink, CDN dependency, overbroad controls | New CSP-compatible evidence-first UI | XSS/CSP/accessibility/browser tests pass |
| API | Broad current routes | Mutation, cost, data and internal-state exposure | Exact prefixed allowlist and deny-all default | Route enumeration proves only allowlist reachable |
| School fixture | Exact archive/hash and accepted auth available | Replacement, raw disclosure, repeated authority misuse | Read-only external mount, startup aggregate validation, fixed server-held auth/key | Identity and tamper-startup tests pass; display authority recorded |
| ROAD fixture | Exact package/196/segments/vertices frozen | Raw package disclosure, route/ID abuse, display-rights boundary | Same read-only archive, exact package validation, fixed auth/key, derived result only | Identity/geometry/tamper tests pass; display authority recorded |
| BUILD safety | Replay safe; current unified execute branch exists | Caller could try policy hash/source scope; future activation confusion | Gateway has replay only; implementation/activation not mounted/reachable | BUILD bypass suite proves structural impossibility |
| GraphRAG | Canonical graph and accepted School/ROAD nodes available | Raw graph leakage, external model cost, silent fallback | Local typed accepted-seed traversal; startup identities; redacted projection | Evidence-to-plan linkage and tamper tests pass |
| Authorization | Exact frozen demo authority exists | Anonymous new authorization or caller-controlled key | Read-only server lookup; public sends no authority fields | Request schema rejects all authority/idempotency keys |
| Secrets | Local server can load OpenAI/Neo4j and serve repo root | Catastrophic key exposure if config appears under root | Baseline app has no API/Neo4j/production secret; external proxy TLS only; no repo static server | Secret scan, dotfile denial, egress and environment tests pass |
| nginx/HTTPS | Base domain uses Cloudflare; demo host absent; no repo config | No current origin/path/TLS boundary | Dedicated vhost, Cloudflare/origin TLS, Unix socket, headers/limits | External staging header/TLS/path tests pass |
| Rate limits | None in app | Anonymous resource exhaustion | Cloudflare + nginx + app semaphores/quotas | Load/429/503/recovery tests pass |
| Logging | Basic access log only | Cannot distinguish failures/abuse/research stages | Structured operational events/metrics and minimal research schema | Log redaction and event completeness tests pass |
| Production isolation | Frozen semantics deny writes, but local server shares worktree/paths | Misconfiguration may mount production authority | Dedicated user/process/mounts/state; no production network/credentials | Deployment inspection proves absent/not-mounted |

## 20. Bounded threat model

| Threat actor/scenario | Attack surface | Existing protection | Residual risk | Mandatory DEPLOY-01 mitigation |
|---|---|---|---|---|
| Anonymous abusive caller | Public endpoints | Body limit and some schema validation | No rate/global concurrency limit | Edge/origin/app limits, active-run semaphore, quotas, 429/503 metrics |
| Malicious/free-form prompt | Request text, optional LLM | Unified 500-char limit and domain checks | Legacy `/api/agent`/LLM routes and prompt injection | Deterministic scenario mapping; legacy routes absent; no LLM/key/egress |
| Malformed API request | JSON/body headers | Closed shapes on many routes | Parser/handler load and inconsistent error projection | 16 KiB proxy cap, 2 KiB schema cap, strict content type/keys/types, safe errors |
| High-volume requester | Threaded HTTP, GraphRAG/GDAL | Local timeouts | Thread/process/CPU/memory exhaustion | nginx/app concurrency, systemd limits, per-IP/session limits, load tests |
| BUILD activation attempt | Unified BUILD execute parameters; hidden future code | Frozen result says held; policy hash required | UI hiding is insufficient; caller may target route directly | Replay-only gateway, no direct route, no authority/activation mounts/egress, bypass tests |
| Arbitrary file selection | Dataset/real-layer routes and path-like IDs | Most dataset IDs and constants are allowlisted | Repo static serving and raw execution path lookup | No repo static server; public schema has no file/path/URL/id field; opaque mapping |
| Fixture overwrite/replacement | Writable worktree/artifact paths | Source engines verify archive hash | Service could share writable developer checkout | Root-owned read-only mount, read-only release, startup/repeated hash checks, no upload |
| Prompt injection to expose graph/internal data | LLM/evidence response | Typed tools, no arbitrary Cypher, hidden reasoning flag | Live resolver may be induced to reveal excess evidence | No live LLM baseline; fixed accepted seeds; redacted field/count projection |
| Secret retrieval | Repository static fallback, status route, errors, console | `.env.local` absent at audit; generic 500 | Future env file could be web-readable; key/model/backend disclosure | Separate web root/gateway, deny dotfiles, no app keys, secret scan, generic health/errors |
| Path traversal | Static handler and execution ID path joins | stdlib normalizes static parent segments; regex forbids slashes | `.`/`..`-like raw IDs can affect runtime-root joins; entire repo remains exposed | No raw path lookup; opaque 128-bit IDs mapped in memory/state; resolve/containment checks |
| Arbitrary command execution | GDAL subprocess routes | Argument arrays, no shell, fixed tools, timeouts | Legacy endpoints can invoke expensive processing | Remove endpoints from public process; fixed scenario worker; systemd sandbox/no egress |
| XSS/GeoJSON/style injection | `innerHTML`, warnings, MapLibre definitions/resources | Some older UIs escape; raw JSON uses textContent | Unified UI does not escape facts/warnings; server paths/styles trusted broadly | DOM-safe new UI, strict response schema, same-origin URLs, CSP, self-hosted dependencies |
| Cross-site request abuse | Anonymous POST | No permissive CORS | Browser can still send simple/cross-site traffic in some cases | JSON content type, exact Origin check, SameSite cookie, no wildcard CORS |
| Evidence/receipt enumeration | Predictable canonical IDs | Domain engines validate format | Public direct GET could reveal internal records | Session-bound opaque run IDs; no list endpoint; rate limits; public projection only |
| Log/privacy leakage | Access/app logs | Credentials not intentionally logged | Request bodies/free text and fixture detail could be retained | Structured allowlist logging, no raw text/body/cookies, retention and access controls |
| Supply-chain/CDN compromise | Unpkg/remote glyphs | Version string pinned in URL | No SRI; runtime depends on third parties | Vendor and hash all browser assets; CSP `self`; deployment manifest/SBOM scan |

## 21. DEPLOY-01 bounded implementation specification

DEPLOY-01 may implement only the deployment adapter, public presentation, deployment manifests,
configuration, and tests below. It must not change frozen NMA semantics.

### 21.1 Exact repository files allowed to be added/changed

New files:

1. `src/nma/public_demo_gateway.py` — closed scenario registry, public schemas/projections, startup
   validator, session/run orchestration, semaphore/deadline enforcement. It may call frozen
   components but cannot alter them.
2. `scripts/run_nma_public_demo.py` — Unix-socket process entry point for the gateway only.
3. `scripts/verify_nma_public_demo_startup.py` — offline fixture/release/GraphRAG/authority identity
   verifier used by `ExecStartPre`.
4. `public/nma/index.html` — hardened evidence-first UI shell.
5. `public/nma/nma-demo.js` — DOM-safe UI and validated MapLibre presentation.
6. `public/nma/nma-demo.css` — CSP-compatible styles.
7. `public/nma/assets/manifest.json` — content hashes and public allowlist for vendored MapLibre,
   glyph, image, JS, and CSS assets.
8. `deploy/nma-demo/nma-demo.service` — least-privilege systemd unit.
9. `deploy/nma-demo/nginx-nma-demo.conf` — dedicated-vhost/path, headers, size/time/rate controls.
10. `deploy/nma-demo/nma-demo.env.example` — non-secret config names and fail-closed defaults.
11. `deploy/nma-demo/nma-demo-deployment-manifest.json` — release, fixture, evidence, authority,
    public-asset, and configuration commitments.
12. `deploy/nma-demo/README.md` — exact install/rollback/verification procedure; no go-live command
    without a separate approval step.
13. `tests/test_public_demo_gateway_deploy01.py` — positive scenario and projection contracts.
14. `tests/test_public_demo_security_deploy01.py` — route/input/path/XSS/BUILD/secret/mutation
    negative tests.
15. `tests/test_public_demo_startup_deploy01.py` — identity/tamper/mount/startup failure tests.
16. `tests/test_public_demo_browser_deploy01.py` — CSP/header/DOM/MapLibre/browser acceptance tests.

Vendored MapLibre/glyph files may be added only beneath `public/nma/assets/` and must appear in its
hash manifest and software/license inventory.

No other tracked file may change without stopping DEPLOY-01 for a new scope decision. In
particular, the following are immutable:

* `src/nma/unified_runtime.py`;
* `scripts/run_nma_agent_server.py`;
* School, ROAD, BUILD, Core, GraphRAG/retrieval, authorization, verification, and identity modules;
* all frozen schemas, controlled fixtures, accepted records, manifests, maps, and portrayal rules;
* `nmaAgentDemoV1.html` and preserved earlier demo pages;
* `.github/workflows/static.yml`, DNS, Cloudflare, production nginx, firewall, and production
  services during repository implementation.

If implementation proves that one of these frozen files must change, DEPLOY-01 must stop and the
verdict must be reconsidered; it may not broaden its scope silently.

### 21.2 Required environment/configuration

Allowed application variables:

```text
NMA_DEMO_RELEASE_COMMIT=eb87bde775333811529efb6f651573ea21cf456b
NMA_DEMO_RELEASE_MANIFEST=/opt/nma-demo/releases/.../data/specifications/nma-v1.0-final-release-manifest.json
NMA_DEMO_FIXTURE_ARCHIVE=/srv/nma-demo/fixtures/nma-v1.0/112年多維度SHP成果_0502.zip
NMA_DEMO_GRAPH_ROOT=/srv/nma-demo/assets/nma-v1.0
NMA_DEMO_AUTHORITY_ROOT=/srv/nma-demo/authority/nma-v1.0
NMA_DEMO_STATE_ROOT=/var/lib/nma-demo/runtime
NMA_DEMO_SOCKET=/run/nma-demo/nma-demo.sock
NMA_DEMO_PUBLIC_ORIGIN=https://demo.geomni.tw
NMA_DEMO_PUBLIC_PREFIX=/nma/
NMA_DEMO_MAX_ACTIVE_RUNS=4
NMA_DEMO_RUN_TTL_SECONDS=1800
NMA_DEMO_LLM_MODE=disabled
NMA_DEMO_BUILD_ACTIVATION=not-mounted
```

The validator rejects unknown `NMA_DEMO_*` variables and rejects any configured OpenAI, Neo4j,
production, activation, writeback, upload, external dataset, or arbitrary path setting. Baseline
application secrets required: **none**. TLS/origin credentials belong to Cloudflare/nginx and are
not readable by `nma-demo`. If a session signing key is later introduced, store it outside the
release in the root-owned environment/credential store and never expose/log it.

### 21.3 Health checks

* **Liveness:** process/event loop and Unix socket respond; no dependency details.
* **Readiness:** exact release/tag manifest, UI assets, fixture aggregates, graph/citations,
  scenario evidence IDs, authorization identities, accepted packages, state permissions, no
  production mounts/credentials, BUILD not-mounted invariant, and one in-memory dry validation per
  scenario all pass.
* Readiness becomes false immediately after a periodic identity check fails.
* No check mutates a fixture, creates production authority, calls an LLM, or exposes paths publicly.

### 21.4 Smoke tests

Offline/staging smoke tests must prove:

1. process starts only from exact commit/manifest and verified read-only mounts;
2. all three scenario metadata records load;
3. deterministic GraphRAG projection resolves accepted School/ROAD seeds and plan links;
4. School exact execution/replay returns 15 Points and frozen identities;
5. ROAD exact execution/replay returns three ordered 4/3/4 LineStrings and line-following
   `中山街` portrayal;
6. BUILD frozen replay validates, renders, and reports activation `held-not-requested` and
   capability `not-mounted`;
7. repeated School/ROAD runs are idempotent and do not create new authority;
8. source archive hash is unchanged before/after all tests;
9. only expected session/state files are written;
10. service remains healthy after rate, malformed input, timeout, and restart tests.

### 21.5 Public acceptance/security tests

Against a non-public staging host with production isolation equivalent to the intended host:

* one URL loads with no mixed content, third-party requests, console errors, or CSP violations;
* each scenario shows domain, evidence/rule alignment, plan, authorization, execution/replay,
  verification, receipt/provenance, and MapLibre output;
* BUILD activation is visibly held and structurally unavailable;
* unsupported/ambiguous language produces public-safe errors and no run;
* every direct current `/api/*`, admin, docs, source, dotfile, fixture, graph, manifest, directory,
  traversal, upload, activation, observation, rollback, and wrong-method request is denied;
* caller-supplied auth/idempotency/policy/source/path/URL/feature/layer/GeoJSON/style fields fail;
* XSS payloads remain text; server-provided malicious test fixtures cannot create DOM/script/URL
  execution;
* headers, origin/CORS behavior, request/response sizes, timeouts, 429/503, concurrency recovery,
  and log redaction match this report;
* a fixture/graph/auth/public-asset byte change prevents readiness;
* service user cannot read production paths, open Internet sockets, modify release/fixtures, or
  write outside its two state/temp locations;
* local/upstream release commit remains unchanged and DEPLOY-01 diff stays within the exact list.

### 21.6 Infrastructure work after repository acceptance

Only after a separate deployment approval:

1. provision dedicated host/vhost or select the safer separate hostname;
2. install root-owned release and read-only mounts;
3. confirm public display/redistribution authority for exact derivatives;
4. install/enable—but do not yet publicly route—the service and nginx config;
5. run local/staging smoke and security tests;
6. configure Cloudflare DNS/TLS/WAF/rate controls and origin restriction;
7. execute public acceptance tests;
8. record deployed commit/config/asset identities and rollback procedure.

DNS, Cloudflare, production nginx, firewall, service launch, and fixture copying are explicitly not
part of DEPLOY-00.

## 22. Required completion questions

1. **What research purpose does the public demo serve?** It makes the frozen knowledge-grounded,
   governed, auditable, three-domain NMA lifecycle observable and repeatable under controlled
   fixtures.
2. **What exactly can a public user do?** Select or boundedly phrase one accepted scenario, inspect
   its evidence/plan/authority, trigger its exact controlled run/replay, inspect QA/receipt/
   provenance, and view the MapLibre result.
3. **What can they explicitly not do?** Upload/select data or paths, create authority, change
   portrayal/data, run arbitrary tools/queries, write sources, activate production, or call internal
   routes.
4. **Which scenarios are exposed?** Exact `school-v1`, `road-v1`, and accepted `build-v1` described
   in Section 5.
5. **How is GraphRAG evidence shown?** As a redacted typed traversal from frozen accepted node IDs,
   linked to plan fields and citations; BUILD honestly shows its accepted `PASS_NOT_APPLICABLE`
   GraphRAG boundary plus mapping-rule evidence.
6. **How is planning shown?** A dedicated plan stage shows status, ID/hash, bounded operations,
   input/evidence links, and domain-owned semantics without hidden chain-of-thought.
7. **How is authorization shown?** Exact existing demo authorization identity, human decision,
   fixture/scope binding, consumption state, and explicit no-write/no-activation boundaries.
8. **How are QA/provenance shown?** Dedicated verification and evidence views show check outcomes,
   identity hashes, receipt, source commitments, and request-to-result linkage.
9. **Where do controlled fixtures reside?** Root-owned, read-only outside Git at
   `/srv/nma-demo/fixtures/nma-v1.0/`.
10. **How are identities validated?** Size/SHA-256, aggregate/layer/feature/geometry/field checks,
    accepted IDs/hashes, release manifest, and startup/readiness fail-closed validation.
11. **How is production isolated?** Dedicated user/process/socket/state/mounts, no production
    paths/credentials/network/IAM, and read-only release/fixture/graph/authority.
12. **How is BUILD activation prevented?** Replay-only dispatch, implementation/activation not
    mounted/exported/routed, no credentials/egress, startup invariant, and bypass tests.
13. **What API routes are exposed?** Only the prefixed allowlist in Section 8.1.
14. **What routes are disabled?** All current direct `/api/*`, legacy proposal/dataset/execution/
    observation/rollback routes, arbitrary static paths, uploads, admin/debug/docs/metrics, and all
    unlisted paths/methods.
15. **What secrets are required?** No application secret in deterministic baseline. Proxy TLS/
    Cloudflare material remains outside the app. OpenAI/Neo4j/production secrets are absent.
16. **What rate limits are required?** Initial limits in Section 16: 5 run POSTs/min/IP, one active
    run/IP, four globally, bounded GET/static rates, quotas, size and time ceilings.
17. **What logging is required?** Structured operational stage/security events and metrics with
    request IDs, coarse outcomes, latency, rate/timeout events, and strict redaction.
18. **What research metrics can be captured?** Anonymous session, domain/scenario, input type,
    retrieved rule IDs, plan, authority/execution/verification outcomes, completion, and latency—no
    unnecessary personal data or raw text by default.
19. **What are the major Internet threats?** Abuse/resource exhaustion, malicious/malformed input,
    BUILD activation attempts, arbitrary file/data selection, fixture overwrite, prompt/graph/
    secret exfiltration, traversal, command invocation, XSS/GeoJSON injection, enumeration,
    cross-site abuse, log leakage, and supply-chain compromise.
20. **What mitigations are mandatory?** The default-deny gateway, read-only mounts, production
    absence, replay-only BUILD, strict schemas/IDs, no LLM baseline, proxy/app limits, process
    sandbox, CSP/self-hosting, safe DOM/render validation, redacted logs, and complete negative tests.
21. **Is `demo.geomni.tw/nma` appropriate?** Yes, only as `https://demo.geomni.tw/nma/` on a
    dedicated deny-by-default vhost. It is currently unresolved. If the host is shared, use
    `https://nma-demo.geomni.tw/` for safer origin isolation.
22. **What exact DEPLOY-01 work remains?** The 16-file bounded implementation, vendored assets,
    service/nginx/env/deployment manifests, read-only mounts, security controls, startup validator,
    health/smoke/public acceptance tests, then separately approved infrastructure provisioning.
23. **Can DEPLOY-01 proceed without changing frozen NMA semantics?** **Yes.** It adds a public
    deployment adapter and presentation projection around the frozen runtime. Any need to edit a
    frozen file is a stop condition.

## 23. Final safety statement

The public deployment is justified only as a way to make NMA v1.0 accessible, observable,
repeatable, safe, and auditable. It must preserve controlled School and ROAD fixtures, the accepted
BUILD replay, frozen architecture and domain ownership, exact authorization identities, GraphRAG/
mapping-rule evidence, content-addressed QA/provenance, and fail-closed behavior.

The architecture is ready. The current local server is not public-ready. DEPLOY-01 is authorized by
this verdict only as the bounded, offline/staging implementation specified above; public Internet
activation still requires a separate explicit approval after every gate passes.

> **PASS — PUBLIC NMA RESEARCH DEMO DEPLOYMENT ARCHITECTURE READY**

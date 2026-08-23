# NMA DEPLOY-01 — Public Research Demo Deployment Report

**Date:** 2026-08-23 (Asia/Taipei)

## 1. Verdict

> **FAIL — PUBLIC URL NOT EXTERNALLY REPRODUCIBLE**

DEPLOY-01 did not deploy or activate a public service. This is the required fail-closed result.
Two independent mandatory gates are unresolved:

1. `demo.geomni.tw` has no DNS A/AAAA/CNAME answer, HTTPS cannot resolve, and this workspace has
   no deploy host, SSH identity, Cloudflare connection, or infrastructure credentials.
2. The frozen `NMA-DEMO-DATA-00` authority matrix has zero accepted public fixtures, zero public
   demo authorizations, and `FAIL_CLOSED` decisions for School and ROAD. It expressly forbids
   publishing a substitute fixture or claiming the historical frozen execution identity.

The second blocker exists even if infrastructure access is later supplied. DEPLOY-00 made public
display/redistribution authority a go-live prerequisite and said the exact ROAD derivative must
not silently override the existing coordinate boundary. DEPLOY-01 therefore makes the service
startup verifier exit nonzero after validating the other controlled identities.

The requested PASS and PARTIAL verdicts are not applicable: the public URL is not deployed.

## 2. Canonical repository and predecessor

| Item | Exact result |
|---|---|
| Repository | `https://github.com/dongpo/topoMap.git` |
| DEPLOY-00 branch | `deploy/deploy-00-public-research-demo-audit` |
| Exact predecessor | `4fec00c4fd3d0aca8e972079b65ecfa721c06d98` |
| Local/upstream/fetched remote before work | exact equality at `4fec00c…` |
| Starting worktree | clean |
| DEPLOY-01 branch | `deploy/deploy-01-public-nma-research-demo` |
| Final SHA | recorded in the terminal handoff after the report-containing commit is created and pushed; a commit cannot contain its own SHA |

## 3. Frozen NMA identity and integrity

| Item | Exact result |
|---|---|
| `nma-v1.0-final^{}` | `eb87bde775333811529efb6f651573ea21cf456b` |
| annotated tag object | `f710da4828cd9ebf170fb60bd6af8f81e4e7abff` |
| release manifest self-hash | `623860a18e82ad268ab389b417f3e9edc29c6c398b5dd923b37dbba3b2ba3bb4` reproduced |
| frozen semantic file changes | **0** |
| controlled fixture changes | **0** |
| GraphRAG/mapping-rule changes | **0** |
| authorization semantic changes | **0** |

No frozen Core, School, ROAD, BUILD, GraphRAG, generic contract, fixture, mapping-rule,
authorization, or unified-runtime file was edited. Deployment additions remain outside the frozen
semantic implementation.

## 4. Exact changed files

Deployment boundary and launch:

- `src/nma/public_demo_gateway.py`
- `scripts/run_nma_public_demo.py`
- `scripts/verify_nma_public_demo_startup.py`
- `deploy/nma-demo/nma-demo.service`
- `deploy/nma-demo/nginx-nma-demo.conf`
- `deploy/nma-demo/nma-demo.env.example`
- `deploy/nma-demo/nma-demo-deployment-manifest.json`
- `deploy/nma-demo/README.md`

Public UI and self-hosted assets:

- `public/nma/index.html`
- `public/nma/nma-demo.js`
- `public/nma/nma-demo.css`
- `public/nma/assets/manifest.json`
- `public/nma/assets/maplibre-gl-4.7.0.js`
- `public/nma/assets/maplibre-gl-4.7.0.css`
- `public/nma/assets/maplibre-gl-4.7.0-LICENSE.txt`
- `public/nma/assets/NotoSans-LICENSE.txt`
- `public/nma/assets/NotoSansRegular-0-255.pbf`
- `public/nma/assets/NotoSansRegular-19968-20223.pbf`
- `public/nma/assets/NotoSansRegular-23552-23807.pbf`
- `public/nma/assets/NotoSansRegular-34816-35071.pbf`
- `public/nma/assets/school-blue.svg`

Focused verification and report:

- `tests/test_public_demo_gateway_deploy01.py`
- `tests/test_public_demo_security_deploy01.py`
- `tests/test_public_demo_startup_deploy01.py`
- `tests/test_public_demo_browser_deploy01.py`
- `NMA-DEPLOY-01-Public-Research-Demo-Deployment-Report.md`

The vendored MapLibre and Noto files are pinned by SHA-256 and include their license records.

## 5. Public URL, DNS, and HTTPS

Target: `https://demo.geomni.tw/nma/`

External verification on 2026-08-23 returned no A, AAAA, or CNAME record. `curl` failed with
`Could not resolve host: demo.geomni.tw`; therefore TLS, HTTP, asset, scenario, provenance, and
rate-limit acceptance cannot be claimed publicly. The apex `geomni.tw` remains Cloudflare-backed,
but that does not create or authorize the dedicated vhost.

## 6. Gateway and nginx topology

The bounded staging design is:

```text
Cloudflare / HTTPS -> dedicated default-deny nginx vhost -> Unix socket
  -> nma-demo.service -> closed public gateway -> frozen controlled components
```

The Python development server is not used and was never exposed. The nginx template defines only
the `/nma/` surface, rate zones, body/time limits, upstream failure handling, security headers,
and `location / { return 404; }`. It has no catch-all proxy. Because there is no origin host,
existing nginx configuration could not be captured or validated and no nginx file was installed,
reloaded, or changed.

## 7. Dedicated service and process

`nma-demo.service` uses `User=nma-demo`, `Group=nma-demo`, a dedicated working directory,
`ExecStartPre` integrity verification, a Unix socket, bounded restart policy, `UMask=0077`,
read-only system protection, private devices/tmp, `AF_UNIX` only, `IPAddressDeny=any`, 512 MiB
memory, 64 tasks, and 200% CPU limits. It is a template only; it was not installed or started on a
public host. Baseline egress and host TCP binding are structurally absent.

## 8. Public route allowlist

| Method | Route | Purpose | Request bound | Authorization source | Rate |
|---|---|---|---|---|---|
| GET | `/nma/` | exact UI | no body | none | 120/min/IP |
| GET | `/nma/assets/{manifest-name}` | manifest-listed assets only | no body | none | 120/min/IP |
| GET | `/nma/api/v1/health/live` | coarse liveness | no body | none | 30/min/IP |
| GET | `/nma/api/v1/health/ready` | coarse readiness | no body | server-side gate | 30/min/IP |
| GET | `/nma/api/v1/scenarios` | three static cards | no body | none | 30/min/IP |
| POST | `/nma/api/v1/runs` | exact scenario or bounded text | JSON ≤2 KiB app/16 KiB proxy; text ≤500 | exact server-held/frozen evidence only | 5/min/IP, burst 2 |
| GET | `/nma/api/v1/runs/{128-bit-id}` | lifecycle projection | opaque session-bound ID | server-side | 30/min/IP |
| GET | `/nma/api/v1/runs/{128-bit-id}/evidence` | redacted evidence | opaque session-bound ID | server-side | 30/min/IP |
| GET | `/nma/api/v1/runs/{128-bit-id}/map` | validated result | opaque session-bound ID | server-side | 30/min/IP |

POST accepts exactly `{"scenario_id":"…","input_type":"guided"}` or
`{"request":"…","input_type":"bounded-natural-language"}`. No caller authorization,
idempotency key, source, path, URL, feature, layer, style, GeoJSON, activation, or policy field is
accepted.

## 9. Route denylist and negative security

All unlisted paths and methods deny. Explicitly unavailable are direct `/api/*`, admin, debug,
docs, OpenAPI, metrics, fixture management, arbitrary files/directories, dotfiles, source,
manifests, raw graph/index access, upload, URL fetch, dataset selection, Cypher/query, authorization
issuance, execution-ID lookup, activation, writeback, repair, observation, rollback, and subprocess
routes.

Local Unix-socket HTTP tests returned:

- raw `/api/nma/runtime`: `404`;
- activation field injection: `400`;
- wrong Origin: `403`;
- traversal: `404`;
- ambiguous bounded language: controlled unsupported response;
- sixth POST within one minute: `429` with the public rate-limit message.

## 10. Request, input, concurrency, and session controls

- explicit JSON content type and content length required;
- chunked request bodies rejected;
- application JSON maximum 2 KiB; nginx maximum 16 KiB;
- text maximum 500 Unicode characters;
- exactly three scenario IDs and two closed request schemas;
- deterministic single-domain matching; ambiguity and blocked path/URL/secret/tool/production terms
  reject before execution;
- one active run/IP, four globally, two-second acquire bound;
- 20 runs/hour/session and 1,800-second in-memory TTL;
- opaque 128-bit run ID plus Secure/HttpOnly/SameSite=Strict session binding;
- no browser credential storage and no permissive CORS.

## 11. Controlled fixture mount and startup verification

The runbook specifies a root-owned read-only archive at
`/srv/nma-demo/fixtures/nma-v1.0/112年多維度SHP成果_0502.zip`, outside Git and the web root.
Startup verified the exact archive size `12,822,898`, SHA-256 `4888dbf9…da53`, safe ZIP member
paths, and every School and K14_ROAD component size/hash. It verified School aggregate
`77802b44…fc12d` and ROAD aggregate `dc82db8b…ae79`. No request can replace or select this path.

The gate then intentionally fails because the public authority matrix does not permit these
private/historical inputs to be exposed as public demo fixtures.

## 12. GraphRAG deployment strategy

The gateway loads the local canonical graph JSON with exact SHA-256
`4c37cc24…820cb4`, verifies all accepted School/ROAD seed nodes, and performs only an accepted-seed
typed projection. It returns allowlisted node types, identifiers, short properties, relationships,
and plan linkage. It exposes no vector dump, arbitrary node query, Cypher, prompt, hidden reasoning,
or chain-of-thought. BUILD honestly reports the frozen `not-applicable` GraphRAG boundary and its
mapping-rule resolution.

## 13. LLM and Neo4j status

The baseline requires no OpenAI key, external LLM, paid inference, embedding call, Neo4j service,
or Neo4j credential. Unknown or provider/production/activation/writeback/upload `NMA_DEMO_*`
configuration fails startup. The systemd service denies Internet address families.

## 14. Authorization deployment

The exact School identity and self-hash were verified:

- `authorization-school-demo-b4ecdbfc35ecaf73293ed497`
- `d5546bd1b2176a4ad287acb1c78740ce79a90db76d05739dc871267d901dac67`

The adapter never issues authority or accepts it from a visitor. ROAD and BUILD use frozen consumed
evidence. However, `NMA-DEMO-DATA-00` records no public demo authorization and forbids treating the
historical identities as a new public authorization. That conflict is a startup blocker, not a
reason to weaken the verifier.

## 15. BUILD replay-only proof

BUILD dispatch exists only as frozen-package validation/replay. The gateway has no BUILD execute,
activation, authorization-issuance, or policy-selection branch. The environment requires
`NMA_DEMO_BUILD_ACTIVATION=not-mounted`; any other value fails. The unit denies egress, and the
mount plan excludes production sources, stores, write paths, and credentials. The UI visibly says
`production activation disabled/unavailable`. Activation capability is absent/not mounted, not
merely false.

## 16. Browser security and UI

The dedicated prefix-safe UI uses `/nma/` API/asset paths, DOM `textContent`/element creation, no
`innerHTML`, no inline script/style, no service worker, and only self-hosted MapLibre/glyph/image
assets. CSP restricts all resource classes to self (plus image/blob/data requirements), with
`object-src none`, `base-uri none`, and `frame-ancestors none`. HSTS, nosniff, DENY framing,
no-referrer, Permissions-Policy, COOP, CORP, and no-store API/HTML behavior are configured.

Local in-app-browser staging QA rendered live MapLibre canvases for all scenarios:

- School: accepted 15 points, official blue flag, and labels;
- ROAD: exact three-feature 4/3/4-vertex derivative and line-following `中山街`;
- BUILD: accepted normalized boundary and diagonal hatch, with activation unavailable.

Planning, authorization, execution/replay, verification, receipt/provenance, and rule evidence
were visible. Browser console errors/warnings and CSP violations: **0**. These local results are
not public acceptance.

## 17. File-system and secret status

The intended release, fixtures, graph, and authority paths are read-only; only bounded state and
runtime socket paths are writable. Production data, credentials, activation stores, `.git`, host
sockets, and arbitrary paths are absent. A focused private-key/token pattern scan found no secret.
The configuration contains only explicit statements that OpenAI, Neo4j, and production credentials
are absent. TLS/Cloudflare secrets are not part of the repository or service process.

## 18. Operational and research logging

The adapter emits structured coarse events containing scenario/domain, input type, result,
verification state, and latency. It does not log raw request text, body, cookie, fixture content,
coordinates, authorization payload, evidence package, token, or secret. nginx logging is separated
for the NMA vhost. No formal human-subject study or personal identifier collection is enabled.

## 19. Health and readiness

Liveness would expose only status and release ID. Readiness is intentionally unavailable because
the startup data-authority gate fails. No paths, credentials, topology, or detailed configuration
are returned publicly. The service cannot partially start with substituted assets.

## 20. Configuration validation and existing-infrastructure safety

All repository JSON parsed through focused tests, Python compiled/imported, asset hashes matched,
and the nginx/systemd security structure passed focused assertions. Actual `nginx -t`,
`systemd-analyze verify`, permission inspection, socket ownership, origin TLS, and service reload
were not possible because no Linux deployment host is configured. No existing nginx, systemd,
Cloudflare, DNS, firewall, or unrelated service was modified.

## 21. Regression results

| Suite | Result |
|---|---:|
| DEPLOY-01 focused gateway/security/startup/browser | **23 passed** |
| DEMO-DATA-00 authority blocker | **10 passed** (confirms fail-closed state) |
| NMA-FINAL detached exact tag | **14 passed** |
| DEMO-FINAL detached exact tag | **14 passed** |
| DEMO-02 Retry | **18 passed** |
| DEMO-AUTH-01 | **8 passed** |
| DEMO-FIXTURE-00 | **7 passed** |
| demo integration | **34 passed, 1 expected loopback skip** |
| School/Core selected superset | **76 passed** |
| ROAD-01 through ROAD-05 | **199 passed** |
| GEN-FINAL detached exact tag | **10 passed** |
| BUILD-10/11/11A/12 | **87 passed, 2 documented historical stage-local assertions** |

The complete repository run reached 100% with 25 failures. Twenty-two are historical exact-stage
scope/direct-parent or earlier-chain audit assertions that intentionally fail on descendant/dirty
worktrees. Three are pre-existing Agentic PMTiles/catalog freeze drift checks unrelated to the
DEPLOY-01 files. No scenario, execution, verification, geometry, fixture, GraphRAG, authorization,
or deployment-focused functional test regressed.

## 22. School, ROAD, and BUILD public acceptance

| Scenario | isolated adapter/browser staging | actual public URL |
|---|---|---|
| School | PASS | **NOT RUN — DNS and data-authority blocked** |
| ROAD | PASS | **NOT RUN — DNS and data-authority blocked** |
| BUILD replay | PASS | **NOT RUN — DNS blocked** |

No localhost or Unix-socket result is represented as public PASS.

## 23. External verification and negative public tests

DNS and HTTPS fail before HTTP. Consequently page load, public API, public map assets, public
scenario execution, public provenance, public 429 behavior, origin firewall policy, and public
error handling remain unverified. This independently requires the terminal failure verdict.

## 24. Rollback verification

No public infrastructure change occurred, so operational rollback was not needed. The temporary
local Unix socket and loopback browser bridge were stopped; the socket was removed. The documented
future rollback disables only the NMA Cloudflare route/vhost, stops only `nma-demo.service`,
restores captured predecessor nginx config after `nginx -t`, preserves logs/evidence, and leaves
NMA v1.0 untouched.

## 25. Final repository state and Git publication

The exact diff is deployment adapter/config/UI/test/report material only. Frozen semantic and
fixture paths remain unchanged. The terminal handoff records the post-commit local/upstream/remote
SHA equality and clean worktree because those facts occur after this report is committed.

## 26. DEPLOY-02 readiness

**NOT READY FOR DEPLOY-02.** DEPLOY-02 must not be performed. A future separately authorized stage
must first close public School/ROAD fixture and domain-owned demo authorization compatibility
without claiming historical equivalence or modifying the frozen NMA v1.0 semantics. Infrastructure
owners must also provision the dedicated DNS/vhost/origin access and validate nginx/systemd/TLS
before DEPLOY-01 can be rerun.

## 27. Terminal statement

The implementation evidence proves that a safe default-deny adapter is feasible, but the required
person-outside-the-machine criterion is false and the frozen public-data authority gate is closed.
No security or scientific-governance boundary was weakened to manufacture a PASS.

> **FAIL — PUBLIC URL NOT EXTERNALLY REPRODUCIBLE**

# AMA live developer guide

## Components and ownership

| Component | Location | Responsibility |
| --- | --- | --- |
| demo UI | `public/ama-live/` | intent control, real progress polling, graphs, trace, MapLibre |
| AMA runtime | `src/nma/ama_live.py` | run lifecycle, fresh identities, narrow views, orchestration |
| HTTP API | `src/nma/ama_live_server.py` | localhost routes, bounded payloads, static assets |
| scenario | `CANONICAL_INTENT` plus `data/evaluation/rq2-demo-01-protocol.json` | supported intent, fixture, truth, frozen model |
| KG/rules | `data/knowledge/nma-canonical-graph-v0.4.json` and `src/nma/rq2_demo.py` | GraphRAG, constraints, planner/proposal rules |
| mapping data | `data/rq2/rq2-demo-01-fire-hydrant.geojson` | immutable redistributable test fixture |
| execution records | `artifacts/ama-live/runtime/<run-id>/` | result, receipt, provenance, run record |

This separation is intentionally scenario-oriented, not a claim of arbitrary GIS support.

## Runtime dependencies

- Python: `>=3.11`; accepted locally on CPython 3.11.9.
- Python validation/test packages: `jsonschema>=4.23,<5`, `referencing>=0.35,<1`, `pytest>=8`.
- Ollama: accepted with client 0.32.15 and local HTTP `/api/chat`.
- Frozen model: `qwen2.5:latest`, digest
  `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`, 7.6B,
  Q4_K_M, context 8192, output reserve 2048, temperature 0.
- GraphRAG: canonical JSON graph and `CanonicalGraphRetriever`; Neo4j remains optional and is not
  required by this reference scenario.
- GIS: the frozen RQ2 deterministic GeoJSON executor; no shell and no arbitrary GDAL command.
- Frontend: browser-native HTML/CSS/JavaScript; no Node build step.
- Map: bundled MapLibre GL JS 4.7.0 in `public/gh-pages/assets/`.

`Node v24.10.0` was present during acceptance but is not a runtime dependency.

## API

The server binds to `127.0.0.1` by default.

```text
POST /ama/run                         {"intent":"<canonical preset>"}
GET  /ama/run/{id}                    current backend state and compact/raw records
GET  /ama/run/{id}/evidence           bounded live graph evidence
GET  /ama/run/{id}/proposal           proposal plus frozen-validator result
GET  /ama/run/{id}/verification       postcondition checks
GET  /ama/run/{id}/provenance         compact linked provenance
GET  /ama/run/{id}/result             current run derived GeoJSON
POST /ama/run/{id}/tamper-test         protected-field fail-closed test
GET  /ama/context                     bounded canonical domain context
GET  /ama/rq1-comparison              frozen RQ1 aggregates
GET  /ama/source                      immutable canonical fixture
```

The API does not accept a filesystem path, shell command, tool name, model selector, graph query,
production write, or replay-as-live mode. Polling reflects persisted stage transitions.

## How the live path works

1. `retrieve_rq2_evidence` ranks the exact intent and performs typed canonical-graph expansion.
2. Evidence identities and a bounded evidence projection are recorded for this request.
3. `resolve_constraints` produces the frozen six-category constraint set; unresolved ProductLayer
   and physical portrayal gates retain null values.
4. `RQ2Planner` calls the exact local Qwen model through `OllamaAdapter`.
5. `assemble_proposal` creates a new RQ2 proposal hash using the current creation timestamp.
6. `validate_proposal` applies the frozen schema, evidence, constraint, condition, and allowlist
   checks without repair.
7. The RQ3 authorization schema/policy issue a short-lived record bound to the exact proposal hash,
   plan identity, tools, parameters, scope, read-only source, and unresolved guards.
8. `execute_proposal` writes only the isolated derived GeoJSON and receipt.
9. `verify_execution` checks classification, geometry, portrayal values, unresolved values,
   tool/receipt binding, unchanged source hash, and declared files.
10. AMA emits a fresh linked provenance record and the UI fetches the produced GeoJSON.

## Adding another scenario

Do not add a preset alone. A developer must provide and review all four boundaries:

1. scenario protocol: exact intent, fixture identity, feature selector, truth, frozen model;
2. input dataset: redistributable immutable fixture and declared output boundary;
3. KG/rules: reviewed graph evidence plus constraint semantics with explicit unresolved states;
4. planning/execution: proposal schema compatibility, allowlisted tool sequence, authorization scope,
   deterministic executor, postconditions, and map adapter.

Then add a scenario registry entry, scenario-specific acceptance fixtures, a tamper case, and a
redistribution entry. Do not generalize the current resolver, authorization, or GIS semantics merely
to make a new preset pass.

## Cloud readiness

The same runtime can be exposed remotely, but deployment was not required for acceptance.

| Deployment unit | Can co-host? | Production note |
| --- | --- | --- |
| static frontend | yes, CDN/static host | configure API origin and CSP |
| AMA API/runtime | yes with KG and bounded GIS workspace | add TLS, auth, rate/size limits, durable job store |
| LLM runtime | separate recommended | GPU capacity, request queue, no public Ollama port |
| KG/GraphRAG | co-host with API for canonical JSON | keep full graph server-side |
| GIS workspace | co-host with API per isolated worker | ephemeral per-run volume, immutable source mount |

Remote readiness is **READY WITH FINDINGS**: 409.28 seconds was observed locally, so a GPU-backed
LLM runtime or presenter preflight is needed for a conference-quality response time. A remote build
must not replace this path with replay or a simplified semantic runtime.

## Redistribution gate

| Artifact class | Browser/public treatment | Decision |
| --- | --- | --- |
| fire-hydrant GeoJSON fixture | tracked bounded derived fixture | public within repository license |
| RQ1 aggregate results | tracked frozen research evidence | public |
| full canonical KG and citation registry | server-side only | bounded pending file-level source/license review |
| live retrieved subgraph | bounded properties/citations only | bounded; do not publish source text/PDF bytes |
| source PDFs and local production ZIP | ignored, never used by this scenario or served | controlled/non-redistributable |
| MapLibre and fonts | bundled with upstream license files | public under recorded licenses |
| runtime records | ignored per-run operational data | do not commit by default |

The gate verdict is **BOUNDED**. Full KG/text redistribution remains subject to the DEMO-PUBLIC-00
file-level review. No research semantics were changed to bypass that review.

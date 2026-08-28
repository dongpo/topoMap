# AMA-LIVE-01 completion report

Verdict: **PASS WITH FINDINGS**

AMA-LIVE-01 now provides a reusable, localhost-first, end-to-end live reference demo on the frozen
RQ-FINAL lineage. The accepted run invoked the exact frozen Qwen model and GraphRAG/constraint/
proposal mechanisms, generated a fresh proposal hash, authorized and executed that exact hash,
verified the derived GeoJSON, emitted linked provenance, rendered the current result through the
MapLibre UI, and rejected a protected-field tamper before mutation.

## Baseline and semantic freeze

- Research freeze: `8411cad14a16d8ce1b8b23ab0f1be1e8b4bc1a4b`.
- `git merge-base --is-ancestor 8411cad… 6185ac…` passed.
- Implementation branch started exactly at the research freeze.
- Only DEMO-PUBLIC-00 specification/evidence/diagram artifacts were imported before implementation.
- Frozen KG, retrieval, evidence, constraint, planner, proposal, GIS, authorization policy,
  verification, provenance, source, and model artifacts were not edited.
- Protected artifact hashes in the DEMO-PUBLIC evidence manifest pass the new acceptance test.

## Accepted live run

The accepted run is recorded in
`artifacts/ama-live/ama-live-01-acceptance-results.json`. Runtime files remain ignored.

| Check | Result |
| --- | --- |
| user intent | LIVE canonical preset, exact text visible |
| GraphRAG | LIVE, 28 retrieved nodes |
| evidence projection | LIVE, 11 projected evidence nodes |
| constraint resolution | LIVE, 7 resolved / 4 bounded unresolved / 0 contradicted |
| planner | LIVE `qwen2.5:latest` digest `845dbda0ea48…` |
| new proposal hash | `c2cdf20081b4c163e3951b6f873e8139a1a7ad6f1212d37501a23c900364e705` |
| proposal validation | PASS |
| proposal-bound authorization | PASS |
| authorized hash equals executed hash | PASS |
| deterministic GIS execution | PASS |
| postcondition verification | PASS, 13 checks |
| source mutation | NONE; before/after SHA-256 identical |
| provenance | COMPLETE |
| map payload | current run GeoJSON, proposal hash bound |
| tamper test | DENIED before execution; no output/mutation |
| unresolved state | ProductLayer plus three physical portrayal gates remain null |

## Runtime and usability

`nma.ama_live_server` provides bounded polling and safe inspection endpoints. The frontend in
`public/ama-live/` provides the intent control, real backend stage state, domain and retrieved KG
views, evidence/constraint trace, plan/proposal/authorization identities, RQ1 supporting panel,
tamper control, provenance, and input/result MapLibre overlay. It has no build step and uses the
existing bundled MapLibre 4.7.0 asset.

HTTP acceptance returned 200 for the UI, bounded graph context, live run, live result GeoJSON, and
MapLibre JavaScript. No browser instance was connected in the acceptance environment, so visual
screenshot QA is recorded as not run instead of inferred from HTTP success.

## Performance

Observed local timing:

| Stage | Time |
| --- | ---: |
| GraphRAG | 270.10 ms |
| evidence projection | 4.23 ms |
| constraint resolution | 0.07 ms |
| Qwen planning | 408.46 s |
| proposal validation | 399.78 ms |
| authorization | 3.49 ms |
| GIS execution | 2.99 ms |
| verification | 0.28 ms |
| end to end | 409.28 s |

The result is functionally reliable but slow for an interactive conference segment on the accepted
local hardware. Presenter preflight and a GPU-backed serving host are recommended. The reference
does not hide latency with replay or fake progress.

## Test and regression classification

- Focused AMA-LIVE tests: 11 passed.
- RQ1/RQ2/RQ3/RQ-FINAL/GIS targeted selection: semantic tests passed. Historical freeze tests that
  assert an exact old branch or an evidence-only changed path fail by design away from their frozen
  refs; the observed result was 89 passed and 3 historical-scope exclusions.
- Broad regression: 1,608 collected; 1,570 passed, 2 skipped, and 36 historical/baseline-scope
  failures. The failures assert exact old milestone branches/change sets/tags or baseline byte
  identities already inconsistent at RQ-FINAL; none exercises a changed frozen semantic source.
- No new semantic regression was observed.

## Reuse, redistribution, and cloud

The demo UI, runtime, scenario protocol, KG/rules, and mapping fixture have explicit boundaries in
`docs/demo/ama-live-developer-guide.md`. The redistribution gate is **BOUNDED**: the tracked fixture,
aggregates, and licensed UI assets are public; the full KG/citation bundle remains server-side
pending file-level source/license review; ignored source PDFs and production ZIP are never served.

Cloud readiness is **READY WITH FINDINGS**. The same runtime can be deployed with a static frontend,
API/KG/GIS worker, isolated run storage, and separate private LLM service. TLS, authentication,
rate/size limits, durable jobs, and GPU capacity remain deployment work. A simplified replay runtime
would not satisfy this result.

## Findings

1. Live planning latency (408.46 seconds) is the primary demonstration risk.
2. Full KG/text redistribution still needs the DEMO-PUBLIC file-level review.
3. Browser screenshot QA remains to be completed in an environment with a connected browser.

Next recommended work: provision and benchmark the unchanged frozen Qwen model on a GPU-backed
local/private serving host, then repeat the same AMA-LIVE acceptance without changing semantics.

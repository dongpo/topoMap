# AMA-DEMO-02 Completion Report

## Final status

AMA-DEMO-02 Verdict: **PASS WITH FINDINGS**

AMA-CLOUD-01 predecessor: `0ebe7193951a8d4f5c5c6d10f3e5de4c71698284`

Branch: `ama-demo/ama-demo-02-public-live-flow`

Final SHA: the completion-report commit; its exact content-addressed SHA is reported in the final handoff after this file is committed.

Remote SHA: required to equal the final SHA and verified in the final handoff. Deployed application source SHA: `c060fe2aa5d6b33caa6a614a09a0b17233e9a144`.

Local/upstream/remote equality: verified after the completion-report commit and reported in the final handoff.

Research semantics: **UNCHANGED**. Protected GraphRAG, RQ1, RQ2, RQ3, GIS, verification, provenance, mapping, geometry, portrayal, ProductLayer, ROAD, School Hero, BUILD, Core, model, and authoritative-source semantics were not changed.

Public AMA endpoint: <https://ama-cloud-01-555420096938.asia-southeast1.run.app>

Deployment: Cloud Run revision `ama-cloud-01-00007-fkx`, Cloud Build `18796d7b-cd38-43f4-8000-8f06b6e45054`, image digest `sha256:ad922db35bbb7ee9f2da0f0606e7530fb8b8bfab1a282d85749aeda9cdf81250`, 100% traffic.

Canonical demo scenario: create a safe symbolic derived fire-hydrant feature for classification `9350906` using reviewed knowledge, preserve unresolved ProductLayer and physical portrayal gates, and leave the authoritative source unchanged.

Demo mode: explicit **LIVE** and **VERIFIED REPLAY** support. No third mode and no silent substitution.

## RQ1 comparison

Controlled-question identity: `request:sha256:8ec999772276b94f4bc4d4f39240e297aea9760f94649a5c6c240d9570ef7394`.

Controlled question: “For fire hydrant 9350906, explain the reviewed authoritative portrayal rule. Include its classification, geometry, line style, color, source evidence, and any unresolved schema or product-layer binding. Do not infer information that is not supported by the retrieved evidence.”

- LLM-only: **FAIL**, 2/6 requirements, grounding FAIL, coverage FAIL, no retriever (`NOT APPLICABLE`), 15.964 s total.
- Text-RAG: **FAIL**, 3/6 requirements, grounding PASS, coverage FAIL, 12 retrieved items, projected evidence `NOT APPLICABLE`, 43.708 s total.
- GraphRAG: **PASS**, 6/6 requirements, grounding PASS, coverage PASS, 46 retrieved items, 9 projected evidence items, 184.254 s total.

Grounding comparison: LLM-only lacked evidence context; Text-RAG grounded retrieved text but missed the required ProductLayer relationship; GraphRAG grounded all requirements through typed nodes, relationships, and projected evidence.

Coverage comparison: LLM-only and Text-RAG failed complete requirement coverage; GraphRAG covered classification, geometry, line style, color, source evidence, and the unresolved ProductLayer binding.

The exact model, prompt/question identities, temperature, context settings, retrieval modes, retrieved/projected counts, validators, answers, claim classifications, citations, and timings are preserved in `artifacts/ama-demo/ama-demo-02-rq1-comparison.json`.

## Observable evidence-to-action flow

Domain KG visualization: **AVAILABLE**, bounded from the frozen canonical KG.

Retrieved KG visualization: **AVAILABLE**, runtime-bound; final public browser acceptance rendered 28 retrieved and 11 projected nodes.

Evidence-to-action trace: **AVAILABLE**, runtime-bound from user requirement through evidence, constraints, planner steps, proposal, authorization, GIS execution, verification, and provenance.

Constraint resolution: **VISIBLE AND CORRECT**. Seven constraints resolved, four explicitly bounded-unresolved, no concealed resolution.

Fresh proposal: **PASS**, final-revision cold acceptance run `ama-live-run:f04f9a5825f949eea61f782fef2c910f`.

Proposal hash: `5ea0d2bb79412ba3e287b58f8ac497227ebfc4f836a46ca0245c67fff75906d1`.

Authorization: **PASS**.

Authorized proposal == executed proposal: **PASS**; the proposal, authorization, execution, provenance, and map feature carried the same hash.

GIS execution: **LIVE PASS**, isolated derived-artifact write only; authoritative input remained read-only.

Verification: **PASS**, 13 visible expected-versus-observed checks.

Provenance: **COMPLETE**, including retrieval, plan, proposal, authorization, execution, verification, receipt, result, and source-before/after identities.

Map result: **LIVE RESULT**, bound to the accepted proposal hash and rendered in MapLibre.

Tamper test: **PASS**. Protected classification mutation changed the recomputed hash, authorization was `DENIED`, execution was not attempted, mutation did not start, and no output was created.

Unauthorized mutation: **NONE**.

## Failure safety and operations

Reset: **PASS**. Five transient final-acceptance run IDs were removed; canonical source mutation was false; stale proposal and authorization reuse were false. The browser returned to `NO RUN SELECTED`, and refresh preserved the clean state.

Sequential live run: **PASS**. One cold plus three warm final-revision runs all passed with four unique fresh proposal hashes.

Replay package: **AVAILABLE AND VERIFIED**, replay ID `ama-demo-02-replay:0405530c1daa766618adcd02`, source run `ama-live-run:2491a89d5dd2483abed5e6da02dd7144`, manifest hashes every included artifact.

Silent live→replay substitution: **NONE**. Unsupported intent produced HTTP 400 and a visible error while the UI remained labeled `LIVE CLOUD RUN`; replay occurred only after the explicit fallback button was selected.

Cloud failure fallback: **PASS**, explicit `VERIFIED REPLAY` with replay identity and `REPLAY RESULT`; no new inference or execution is claimed.

Browser integration: **PASS** in the in-app browser. Final public checks covered initial state, replay, genuine live progression, all 11 stages, three RQ1 cards, both runtime graph SVGs, MapLibre result, hash identity, 13 verification checks, provenance, tamper, visible failure, explicit fallback, reset, refresh, zero console warnings/errors, and zero horizontal overflow at 1280 CSS pixels. Local acceptance also passed at 1600×900.

Cold latency: 16.650 s end-to-end; 16.259 s planner.

Warm latency: 16.545–16.633 s end-to-end, median 16.571 s; classified **GOOD FOR LIVE DEMO**.

Focused tests: **PASS**, 41/41 across AMA-DEMO-02, AMA-LIVE-01, and AMA-CLOUD-01.

Targeted regression: **PASS**, 87 passed and 1 expected skip across frozen RQ1, RQ2, RQ3, unified runtime, and documentation selections.

New semantic regressions: **0**.

Redistribution boundary: public-safe derived JSON, hashes, bounded graph projections, UI assets, documentation, and replay evidence only. No credentials, private cloud state, authoritative-source mutation, or redundant copyrighted source documents were added.

Conference live-demo readiness: **READY WITH DOCUMENTED RQ1 METADATA LIMITATION**.

## Findings

Key findings:

1. The complete public narrative is now observable from the same controlled question through GraphRAG evidence, constraints, proposal, authorization, exact execution, verification, provenance, and live map result.
2. Final public live latency is stable around 16.6 seconds after model preload, with unique run/proposal identities and fail-closed tamper behavior.
3. Replay packaging and 1280px live-identity overflow defects found during public acceptance were fixed, regression-guarded, redeployed, and reaccepted.

Remaining findings:

1. Frozen RQ1-COMPARE-01 records exact run identities and measured latencies but not wall-clock execution timestamps. AMA-DEMO-02 truthfully displays `NOT RECORDED`; it did not re-run or alter frozen RQ1 research semantics merely to manufacture missing metadata.
2. The RQ1 comparison timings are the frozen controlled-record timings, not new Cloud Run RQ1 measurements. Current Cloud Run timing is reported separately for the live evidence-to-action pipeline.

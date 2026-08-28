# DEMO-PUBLIC-00 — Live Demo Architecture, RQ1 Comparison & Deployment Acceptance Specification

Specification date: 2026-08-28 (Asia/Taipei)

Research freeze SHA: `8411cad14a16d8ce1b8b23ab0f1be1e8b4bc1a4b`

Research predecessor: `3fed8fb77e759d004a7b91b23d933d41d8f70225`

Working branch: `demo-public/demo-public-00-architecture-acceptance`

Verdict: **PASS WITH FINDINGS**

## Executive recommendation

Build the public NMA research demonstrator as a replay-first static application at
`https://dongpo.github.io/topoMap/`, backed by an optional, scenario-bounded Cloud Run CPU API and
an independently deployable private Cloud Run GPU inference service. The browser must contain a
complete frozen canonical bundle so RQ1, all three knowledge-graph views, RQ2, RQ3, and the canonical
tamper rejection remain usable when every cloud dependency is absent.

The default conference mode is **CANONICAL REPLAY**. It replays frozen probabilistic answers and
plans, while invoking the real deterministic validators, authorization, verification, provenance,
and audit code when the CPU backend is healthy. **LIVE MODEL** is an optional separately labelled
run. **OFFLINE REPLAY** is a locally served/static package with no API keys, external model, graph
database, Cloud Run service, or internet dependency. The architecture never requires live
inference to complete the presentation.

The result is a research demonstrator, not a production NMA, unrestricted chatbot, institutional
authorization service, general cloud GIS executor, or legal assertion of authority. The research
claim shown at the end is the conservative frozen conclusion:

> The experiment supports an architecture in which probabilistic Agent behavior is bounded by
> explicit geographic knowledge before action and deterministic trust controls before
> authoritative acceptance.

## Research baseline and freeze boundary

DEMO-PUBLIC-00 is based exactly on the verified `RQ-FINAL-00 — Integrated RQ1–RQ3 Research
Evidence, Hypothesis Closure and Demo Freeze` at commit
`8411cad14a16d8ce1b8b23ab0f1be1e8b4bc1a4b`. Its research predecessor is
`3fed8fb77e759d004a7b91b23d933d41d8f70225`. The canonical repository is
`https://github.com/dongpo/topoMap.git`. The isolated task branch was created directly from that
commit after fetching `origin`; no research result was reconstructed or redesigned.

Canonical identities:

| Evidence | Frozen identity |
|---|---|
| Verified research freeze commit | `8411cad14a16d8ce1b8b23ab0f1be1e8b4bc1a4b` |
| Research freeze manifest | `artifacts/research/rq-final-00-freeze-manifest.json` |
| Research freeze manifest SHA-256 | `bcce87599254b18a0628f4b756ff0e668ef55f24f6862227f610686a098dc913` |
| Canonical KG | `data/knowledge/nma-canonical-graph-v0.4.json` |
| Canonical KG SHA-256 | `4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4` |
| RQ1 comparison | `rq1-compare-01-results.json` |
| RQ2 retrieval identity | `8f6fefa8b9ee96860a29b994cbcdcac9a48e6a1ca002777165f6c17dda904b25` |
| RQ2 proposal ID | `rq2-proposal:knowledge-constrained:e635111c3be29423faf923b7` |
| RQ2 proposal SHA-256 | `116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1` |
| RQ2 proposal byte SHA-256 | `8ad05eea5111a0c535be275effa6b8a6c3dce7b74c7149bf42811a1866aa4829` |
| RQ3 experiment | `artifacts/rq3/rq3-demo-01/experiment-summary.json` |

Freeze verification result: **PASS**. RQ1 evidence is `VALIDATED` and its proposition is
`SUPPORTED WITH FINDINGS`; RQ2 evidence is `VALIDATED`, H2 is `SUPPORTED`, and H2b is `SUPPORTED`;
RQ3 evidence is `VALIDATED` and H3 is `SUPPORTED WITH FINDINGS`. The `WITH FINDINGS`
qualifications are mandatory visible labels, not footnotes.

The RQ1→RQ2 boundary is a **SEMANTIC/ARCHITECTURAL HANDOFF**: the experiments share the frozen KG,
retrieval architecture, evidence identifiers, and provenance vocabulary, but RQ2 does not consume
an RQ1 answer or byte-identical RQ1 output. The RQ2→RQ3 boundary is a **DIRECT IMMUTABLE ARTIFACT
HANDOFF** of the exact canonical proposal. Every visualization and narration must preserve this
distinction.

This task changes documentation, Mermaid sources, and focused evidence-integrity checks only. It
does not change KG, retrieval, evidence projection, RQ1 evaluation/validation, RQ2 constraints or
proposal, mapping/classification/geometry/portrayal/ProductLayer, model choice/configuration,
authorization, verification, provenance, ROAD, School Hero, BUILD, Core, or authoritative data.

## Audience goal and public research argument

After 5–7 minutes, a first-time audience should be able to explain five increasingly strong
distinctions:

1. **LLM-only:** the model can answer without retrieved external evidence.
2. **Text-RAG:** the same model can answer with ranked passages, but passage retrieval does not
   explicitly encode the entity-to-entity relationships shown by the KG.
3. **GraphRAG:** the same model receives explicit geographic entities, typed relations, source
   identities, and bounded unresolved state.
4. **RQ2:** explicit knowledge becomes constraints that change what the same planner may propose
   and what deterministic execution is permitted to do.
5. **RQ3:** the result is accepted only when exact proposal authorization, deterministic execution
   and verification, complete provenance, and audit all pass.

The primary visual language must use consistent badges/colors for three component categories:

| Category | Meaning | Required examples |
|---|---|---|
| `PROBABILISTIC REASONING` | model generation; variable natural-language output | RQ1 answers, RQ2 plan draft, optional live inference |
| `EXPLICIT GEOGRAPHIC KNOWLEDGE` | retrieved text/KG evidence and explicit relations | chunks, nodes, edges, source identities, resolved/unresolved constraints |
| `DETERMINISTIC CONTROL` | zero-model-call checks and bounded execution | validators, authorization gate, executor, verifier, provenance, audit |

## Four-scene architecture and presenter controls

Scene 0 must establish the integrated argument in 20–30 seconds:

```text
USER MAPPING INTENT
        ↓
RQ1 — KNOW       GraphRAG / evidence              SUPPORTED WITH FINDINGS
        ↓
RQ2 — CONSTRAIN  knowledge-constrained proposal  H2/H2b SUPPORTED
        ↓
RQ3 — TRUST      authorization / verification     H3 SUPPORTED WITH FINDINGS
        ↓
AUTHORITATIVE MAPPING ACTION UNDER TEST CONDITIONS
```

Scene 1 is the frozen three-way RQ1 comparison and KG inspection. Scene 2 is the paired RQ2
planner comparison with resolved and bounded-unresolved constraints. Scene 3 is the exact RQ3
proposal-bound trust chain, positive acceptance, and Case C rejection. The conclusion returns to
`KNOW → CONSTRAIN → TRUST` and states: **The evidence supports a layered National Map Agent
architecture under the tested frozen mapping domain.** It may close with: **The AI may remain
probabilistic. The authoritative mapping workflow does not have to be.** This is presentation
language, not a stronger research claim.

Closing line: **The AI may remain probabilistic. The authoritative mapping workflow does not have to be.**

Required controls are `Start Demo`, `RQ1 Compare`, `Show Evidence`, `Show Domain KG`, `Show
Retrieved KG`, `RQ2 Plan`, `Show Constraints`, `Show Canonical Proposal`, `RQ3 Authorize`,
`Execute`, `Verify`, `Show Provenance`, `Tamper Proposal`, `Reset`, and `Research Conclusion`.
Reset is always visible after start and immediately restores the immutable canonical state.

## RQ1 controlled comparison

### Controlled design

The primary action is **Compare RQ1**. It always supplies the same canonical question and the same
frozen model configuration to three architectures. The experimental variable is knowledge and
retrieval architecture, not the LLM:

> For fire hydrant 9350906, explain the reviewed authoritative portrayal rule. Include its
> classification, geometry, line style, color, source evidence, and any unresolved schema or
> product-layer binding. Do not infer information that is not supported by the retrieved evidence.

All three conditions use Qwen 2.5 7.6B Q4_K_M, temperature `0`, `num_ctx=8192`, and a 2,048-token
output reserve. RQ1 consists of 33 primary records (three architectures × eleven wordings) and nine
canonical repeats. The UI must show `FROZEN RESEARCH EVIDENCE` next to all published metrics.

### Frozen aggregate metrics

| Metric | LLM-only | Text-RAG | GraphRAG |
|---|---:|---:|---:|
| Mean requirement accuracy | 15.15% | 45.45% | 75.76% |
| Median requirement accuracy | 16.67% | 50.00% | 66.67% |
| Accuracy range | 0–33.33% | 33.33–66.67% | 50–100% |
| Exact 6/6 answers | 0/11 | 0/11 | 3/11 |
| Mean question coverage | 40.91% | 68.18% | 86.36% |
| Exact 6/6 coverage | 0/11 | 0/11 | 4/11 |
| Supported retrieval-grounded claims | N/A | 49 | 96 |
| Unsupported claims | N/A for retrieval grounding | 18 | 0 |
| Contradicted claims | 6 full-truth findings | 0 | 2 |
| Mean evidence tokens | 0 | 2,002.09 | 2,042.64 |
| Mean total latency | 19.27 s | 43.51 s | 125.54 s |

The presenter may say that GraphRAG achieved higher measured requirement accuracy and coverage than
both baselines on all eleven frozen wordings. The presenter must also say that Text-RAG and
GraphRAG tied on geometry, Text-RAG had zero contradicted selected-text claims, GraphRAG had two
parser-induced contradictions in one conversational variant, and GraphRAG cost substantially more
latency. The demo must not claim universal `GraphRAG > Text-RAG > LLM-only` superiority.

### Three-column interaction contract

Each column shows its retrieval architecture, canonical answer, canonical evaluation, aggregate
metrics, limitations, and expandable evidence/claim details. The canonical detail is:

| Canonical run | LLM-only | Text-RAG | GraphRAG |
|---|---:|---:|---:|
| Retrieved / LLM-facing items | 0 / 0 | 12 / 5 chunks | 46 / 9 graph nodes |
| Requirement accuracy | 33.33% | 50.00% | 100% |
| Coverage | 66.67% | 66.67% | 100% |
| Supported claims | 3 | 4 | 11 |
| Unsupported claims | 0 | 1 | 0 |
| Contradicted claims | 1 | 0 | 0 |
| Evidence tokens | 0 | 2,008 | 2,074 |
| Total latency | 15.964 s | 43.708 s | 184.254 s |

The LLM-only column explicitly states `NO RETRIEVED EXTERNAL EVIDENCE`. It shows the frozen answer
and surfaces the contradicted color claim plus omitted/incorrect requirements without relabelling
them as retrieval-grounding failures.

The Text-RAG column shows the five selected chunk IDs and expandable passage text/provenance. The
canonical top-five set includes the relevant hydrant chunk and unrelated school, building, and
road chunks. It must explain that this baseline is a deterministic feature-hashing Unicode
bag-of-words retrieval configuration, not a modern multilingual embedding claim. The visible
limitation is evidence-based: ranked passages carry facts and provenance but no graph node types,
typed edges, traversal path, or explicit relation identity. The canonical answer contains one
unsupported unresolved-binding statement and omits line-style/source-evidence requirements under
the frozen evaluator.

The GraphRAG column shows the canonical answer, the 46→9 retrieved/projected count, evidence and
citation identities, 11 supported claims, and the button **Show Evidence Graph**. The expanded graph
is KG-2 below. Graph retrieval is labelled `EXPLICIT GEOGRAPHIC KNOWLEDGE`, not an LLM result.

### Evidence-based Text-RAG versus GraphRAG distinction

The interface must show actual canonical relations in uppercase repository form. For the selected
hydrant case these include:

```text
ClassificationCode --PORTRAYED_BY--> PortrayalRule
PortrayalRule --APPLIES_TO_GEOMETRY--> PortrayalGeometryRole
PortrayalRule --USES_LINE_STYLE--> LineStyleReference
PortrayalRule --USES_COLOR--> PortrayalColorReference
PortrayalRule --EVIDENCED_ON--> DocumentSection
SpecificationDocument --CONTAINS--> DocumentSection
PortrayalRecipe --TRANSCRIBES_RULE--> PortrayalRule
PortrayalRecipe --BLOCKED_BY--> ActivationGate
```

Do not display invented generic relations such as `supported_by` or `constrained_by` as if they
were KG predicates. Constraint derivation may be shown as a separately labelled RQ2 trace edge,
not as an edge in the frozen KG.

## RQ2 knowledge-constrained flow

The presenter proceeds from the GraphRAG evidence into the canonical RQ2 intent:

> Please prepare this fire hydrant feature for authoritative map production using the applicable
> national mapping rules.

The UI compares the same planner and six semantic capabilities under two evidence conditions. The
baseline receives zero evidence, null knowledge identities, and zero constraints. It proposes
`fire_hydrant`, lowercase `point`, null line/color values, and no evidence-bound source authority.
Its structure validates, but the common read-only source-authority precondition blocks execution
before mutation.

The constrained path shows, in order:

1. canonical KG snapshot SHA-256;
2. retrieval package SHA-256;
3. `7 resolved / 4 bounded unresolved / 0 contradicted`;
4. resolved class `9350906`, geometry `Point`, line `2`, color `7`/`black`, accepted source identity,
   and `authoritative_render=false`;
5. unresolved ProductLayer, device-independent stroke width, color profile, and internal glyph
   approval;
6. decision `PROCEED_WITH_BOUNDED_UNRESOLVED`;
7. all `11/11` applicable constraint references;
8. proposal validation `PASS` with zero validation model calls;
9. deterministic isolated symbolic execution `PASS`;
10. constraint preservation `6/6`, postconditions `12/12`, source hash unchanged, verification
    `PASS` with zero model calls.

The accepted deterministic operation order is frozen:

```text
rq2.feature.read/1.0
rq2.source-authority.validate/1.0
rq2.geometry.validate/1.0
rq2.representation.derive/1.0
rq2.artifact.write-derived/1.0
rq2.postconditions.verify/1.0
```

The UI may render the first five as execution steps and the sixth as the independent verification
boundary. It must state that output is a research-safe symbolic derived artifact with
`authoritative_render=false`; it is not a final authoritative render or source mutation.

## RQ3 authorization, verification, provenance, and audit flow

RQ3 loads the exact RQ2 proposal; it does not retrieve knowledge or rerun the planner. The visible
trust chain is:

```text
canonical proposal ID + canonical hash + byte hash + plan identity
→ proposal-bound RESEARCH AUTHORIZATION
→ authorized proposal == executed proposal
→ deterministic allowlisted execution (0 model calls)
→ independent postcondition verification (0 model calls)
→ six mandatory provenance link types
→ Boolean audit
→ ACCEPT
```

The acceptance function is displayed as deterministic logic:

```text
proposal_integrity_pass
AND authorization_pass
AND execution_scope_pass
AND verification_pass
AND provenance_complete
```

The positive path exposes proposal ID/hash, authorization ID/hash, result SHA-256, execution hash,
verification hash, audit hash, source-before/source-after equality, and all six provenance types:
`PROPOSAL`, `EVIDENCE`, `AUTHORIZATION`, `EXECUTION`, `VERIFICATION`, `RESULT`. Labels must say
`RESEARCH AUTHORIZATION` and `DETERMINISTIC VALIDATION`; they must never imply legal or
institutional authorization.

### Canonical tamper interaction

The obvious action is **Tamper Proposal**. It clones the already authorized canonical proposal in
an isolated demo request and changes the expected final-state classification to `tampered` after
authorization, exactly following frozen RQ3 Case C's proposal-tampering path. The real backend gate,
when reachable, recomputes the proposal hash and returns:

```text
REJECT — FAIL CLOSED
PROPOSAL_HASH_MISMATCH
blocked before mutation
```

The frontend must not alter the original canonical object or authorization. In Canonical Replay
and Offline Replay it replays Case C from the frozen RQ3 experiment summary with a visible replay
badge. It must not substitute Case F's `PARAMETER_MISMATCH` label when presenting Case C. Backend
tests may separately retain all A–L cases.

The compact adversarial panel must say: `12/12 bounded A–L cases matched expected outcomes; all
10 negative/tamper cases B–K failed closed; 0 unauthorized authoritative mutations.` Cases A and
L are positive canonical/replay cases, so the UI must not inaccurately call all twelve negative
tests. The panel is labelled **BOUNDED TEST SET — NOT GENERAL CYBERSECURITY PROOF**.

## Knowledge-graph visualization specification

All three graph views are bounded, accessible, and derived from committed repository identities.
They use keyboard-operable selection, a tabular node/edge alternative, a legend, source-detail
drawer, fit-to-view/reset controls, and no force-layout randomness in captured/video mode.

### KG-1 — NMA knowledge graph conceptual model

Purpose: explain the kinds of knowledge actually present in `nma-canonical-graph-v0.4`, not a
decorative ontology. Use a curated schema projection of real types and predicates. Recommended
clusters are:

| Cluster | Actual node types | Example actual relations |
|---|---|---|
| Feature/classification | `FeatureConcept`, `FeatureType`, `AbstractFeatureType`, `ClassificationCode`, `ClassificationOccurrence`, `ClassificationHierarchy`, `ClassificationLevel` | `CLASSIFIED_BY`, `HAS_SOURCE_OCCURRENCE`, `HAS_ANCESTOR`, `SPECIALIZES` |
| Geometry/layers | `GeometryType`, `StorageGeometryType`, `ApplicationSchema`, `ProductLayer`, `ProductField`, `CodeList`, `CodeListValue` | `HAS_GEOMETRY`, `HAS_LAYER`, `HAS_FIELD`, `STORED_IN_LAYER`, `USES_CODE_LIST` |
| Portrayal | `PortrayalRule`, `PortrayalRecipe`, `PortrayalProfile`, `PortrayalGeometryRole`, `LineStyleReference`, `PortrayalColorReference`, `Symbol`, `VectorPrimitive` | `PORTRAYED_BY`, `APPLIES_TO_GEOMETRY`, `USES_LINE_STYLE`, `USES_COLOR`, `USES_SYMBOL`, `COMPOSED_OF`, `TRANSCRIBES_RULE` |
| Evidence/authority | `SpecificationDocument`, `DocumentSection`, `SourceBasisCell`, `GovernanceEvidence`, `NormativeAuthority`, `EvidenceObservation` | `CONTAINS`, `EVIDENCED_ON`, `HAS_SOURCE_OR_BASIS`, `CITES_AUTHORITY`, `OBSERVES` |
| Workflow/control | `ProductionWorkflow`, `ProductionStage`, `ProductionMethod`, `QualityRule`, `QualityInspectionItem`, `ActivationGate` | `INCLUDES`, `PRECEDES`, `USES_METHOD`, `VALIDATES`, `BLOCKED_BY` |

`ExecutionOperation` and `VerificationRule` belong to the RQ2/RQ3 trace model, not the frozen KG
schema, and must not be rendered as canonical KG types. The source graph contains 4,293 nodes and
11,244 edges, but KG-1 must show a readable schema subset and disclose that it is a conceptual
projection.

### KG-2 — canonical evidence subgraph

Purpose: show exactly the evidence used for the selected hydrant research case. The source is the
RQ2 canonical retrieval package (28 evidence nodes and the committed typed graph paths), with the
RQ1 canonical 46→9 projection disclosed separately. The default focus set contains:

- `classification:doc01:9350906` (`ClassificationCode`);
- `portrayal-rule:doc01:9350906` (`PortrayalRule`);
- `portrayal-recipe:doc01:9350906:review-v1` (`PortrayalRecipe`);
- `portrayal-geometry:Point` (`PortrayalGeometryRole`);
- `line-style:doc01:2` (`LineStyleReference`);
- `portrayal-color:doc01:7` (`PortrayalColorReference`);
- `document:doc01-portrayal` and `section:doc01-portrayal:p11`;
- the three `activation-gate:doc01:9350906:*` unresolved nodes;
- the relevant profile, symbol, and review-asset nodes when expanded.

Resolved nodes/edges use the knowledge color; pending gates and unresolved ProductLayer state use
a dashed amber outline; authoritative source/document linkage uses a distinct source icon and solid
blue edge. The details drawer shows IDs, stored properties, relation type, source revision/hash,
and whether the item is retrieved, projected to the LLM, or used only by RQ2 constraint resolution.
ProductLayer remains absent/unresolved; the visualization must not fabricate a ProductLayer node.

### KG-3 — knowledge-to-action trace

Purpose: show knowledge becoming a bounded research action across research-question boundaries:

```text
RQ1: frozen KG → retrieved evidence → grounded answer/evaluation
  -- SEMANTIC/ARCHITECTURAL HANDOFF -->
RQ2: RQ2 retrieval → resolved/unresolved constraints → plan decision
     → canonical proposal → deterministic execution → postconditions
  -- DIRECT IMMUTABLE ARTIFACT HANDOFF -->
RQ3: proposal authorization → execution binding → verification
     → provenance → audit → ACCEPT
```

Nodes are clickable to reveal the exact artifact identity. Probabilistic generation nodes use the
probabilistic color; evidence and constraint nodes use the knowledge color; validation and trust
nodes use the deterministic color. A prominent annotation states that RQ1 does not directly hand a
byte-identical answer or subgraph to RQ2.

## Runtime modes

| Mode | Probabilistic stages | Deterministic stages | Evidence persistence | Required label and behavior |
|---|---|---|---|---|
| Canonical Replay (default) | replay frozen RQ1 answers and RQ2 plan/proposal | call live CPU validators/trust controls when healthy; otherwise replay their frozen records | immutable canonical bundle only | `CANONICAL REPLAY`; never presented as fresh inference |
| Live Model (optional) | run the fixed canonical question/intent through the exact model configuration | live retrieval/constraints/validators/trust controls in an isolated run | separate ephemeral demo-run namespace; cannot overwrite canonical bundle | `LIVE MODEL`; show model/digest/time and link back to frozen metrics |
| Offline / Local Replay | replay every frozen stage | replay deterministic receipts/results; no claim of fresh backend execution | packaged static files only | `OFFLINE REPLAY`; no network, cloud, keys, Ollama, or Neo4j |

Mode changes reset to `READY` and preserve the canonical evidence object. A live result is never
written into a canonical filename, aggregate, metric, proposal identity, or research-info field.

### RQ1 inference decision

The selected conference mode is **Option C — fully deterministic replay**. Optional live inference
is a secondary rehearsal or audience-inspection feature and is never required to finish the talk.

| Configuration | Latency and load | Reproducibility | Audience/scientific effect | Decision |
|---|---|---|---|---|
| 3 × live sequential | frozen means total about 188 s; canonical runs can exceed 4 min | variable text and three failure points | visibly live but breaks the 5–8 minute narrative | reject |
| 3 × live parallel | peak memory/concurrency and correlated service failure | same model but nondeterministic completion order | hard to follow and needs three inference slots | reject |
| 1 live GraphRAG + 2 replay | one high-latency call; canonical GraphRAG was 184.254 s | comparison mixes run times and must carry mode badges | defensible only as an optional post-demo feature | secondary only |
| 3 replay | sub-second local lookup target; no model dependency | exact frozen evidence | clearest controlled comparison when labelled | **select** |

The frozen measured means are direct evidence that live is not automatically better. A presenter
may run the fixed GraphRAG condition after the canonical story, but its result is labelled `LIVE
MODEL — NOT THE FROZEN EXPERIMENT RESULT` and never replaces the three replayed columns.

### Scene component classification

The authoritative per-component classification is
`artifacts/demo-public/demo-public-00-mode-manifest.json`. At scene level: Scene 0 is `STATIC
VISUALIZATION`; Scene 1 comparison is `FROZEN EVIDENCE` rendered by `DETERMINISTIC REPLAY`, with
KG-1 static and KG-2 a frozen/read-only projection; Scene 2 is `DETERMINISTIC REPLAY` of frozen
constraints and the canonical proposal; Scene 3 uses frozen records and deterministic replay, with
an optional `LIVE READ-ONLY QUERY`/deterministic Case C tamper check; the conclusion is `STATIC
VISUALIZATION`. No replayed result is called live inference.

## Deployment alternatives and decision

The architecture decision is **STATIC-FIRST**: GitHub Pages and an offline-equivalent bundle are
the complete primary demo; a bounded Cloud Run API is optional progressive enhancement. This is
the minimum infrastructure that communicates the validated research without converting cloud
availability into a scientific or presentation dependency.

| Requirement | A: Static Pages | B: Static + Cloud backend | C: Full hosted app |
|---|---:|---:|---:|
| RQ1 comparison visible | Yes | Yes | Yes |
| Three KG views | Yes | Yes | Yes |
| RQ2 constraint trace | Yes | Yes | Yes |
| RQ3 trust chain / Case C | Replay | Replay or deterministic live check | Live/replay |
| Live frozen LLM | No | Optional | Yes |
| Offline fallback | Complete | Complete by design | Separate package required |
| Research reproducibility | Highest | High with explicit per-stage labels | Dependent on runtime capture |
| Operational reliability | Highest | High; backend noncritical | Lowest |
| Recurring cost | None for static hosting | CPU/GPU while enabled | Highest |
| Setup complexity | Low | Medium/high | High |
| Conference risk | Low | Low when static remains primary | High |

Architecture A alone passes the public communication acceptance criteria. Architecture B is the
selected layering because it preserves A completely and permits later read-only/live inspection;
that does **not** change the `STATIC-FIRST` decision. Architecture C is rejected because live model,
backend, and frontend failures become coupled without improving the frozen research conclusion.

Decision drivers, alternatives, live/replay/offline components, and cloud requirements are frozen
in `artifacts/demo-public/demo-public-00-deployment-decision.json`.

## Frontend architecture

The preferred frontend is the existing GitHub Pages publication boundary at
`https://dongpo.github.io/topoMap/`. DEMO-PUBLIC-01 should add a bounded static route/package without
changing production content in this task. The package contains:

- MapLibre GL and locally packaged style/glyph/demo-layer assets;
- a canonical scenario manifest and content hashes;
- RQ1 frozen answers, aggregates, canonical evaluations, Text-RAG chunks, and GraphRAG graph data;
- KG-1 schema projection, KG-2 canonical subgraph, and KG-3 trace;
- RQ2 retrieval/constraints/proposal/execution/verification records;
- RQ3 authorization/execution/verification/provenance/audit and Case C tamper evidence;
- mode/state/failure indicators, Reset Demo, presenter progress, and research-info panel;
- a service worker or equivalent local caching policy for the hosted shell, plus a fully
  self-contained local static package for true internet loss.

The app must render its canonical replay path before contacting a backend. Backend discovery is a
progressive enhancement with a short timeout; failure changes the status badge and leaves the
current deterministic presentation state intact. Map tiles are nonessential. The canonical
research layer and a neutral local/fallback basemap must remain visible without a tile service.

The expandable research-info panel exposes:

- RQ-FINAL-00 SHA;
- RQ1 protocol/results identities;
- RQ2 experiment identity, proposal ID, canonical hash, and byte hash;
- RQ3 experiment identity;
- public-demo build Git SHA and canonical-bundle SHA-256;
- model name/full digest/configuration and pinned Ollama container digest;
- KG graph ID/file SHA and bounded snapshot SHA;
- current runtime mode and whether each stage was generated, executed, or replayed.

## Backend architecture

The preferred backend is a Cloud Run CPU service that owns NMA orchestration, canonical artifact
loading, optional snapshot retrieval, deterministic constraint resolution, proposal validation,
RQ3 authorization gates, isolated execution, verification, provenance, and audit. It does not own
model weights. The GPU inference service is private and callable only by the CPU service using
service-to-service identity.

The public API accepts only a versioned envelope such as:

```json
{
  "build_id": "expected-public-demo-build",
  "scenario_id": "rq-hydrant-9350906",
  "mode": "canonical-replay-or-live-model",
  "action": "RQ1_COMPARE_OR_RQ2_VALIDATE_OR_RQ3_EXECUTE_OR_RQ3_TAMPER_CASE_C",
  "request_id": "client-generated-idempotency-id"
}
```

The route allowlist is limited to `GET /demo/status`, `/demo/rq1/question`,
`/demo/rq1/results`, `/demo/rq1/evidence`, `/demo/rq1/kg/domain`,
`/demo/rq1/kg/retrieved`, `/demo/rq2/scenario`, `/demo/rq2/constraints`,
`/demo/rq2/proposal`, `/demo/rq3/proposal`, `/demo/rq3/audit`, and `POST
/demo/rq3/tamper-check`. A future `POST /demo/rq1/run` is allowed only for the one canonical
scenario and exact frozen model configuration after DEMO-PUBLIC-02 acceptance. Generic
`/prompt`, `/execute`, `/shell`, arbitrary query, upload, and mutation routes are prohibited.

No endpoint accepts an arbitrary prompt, Cypher, filesystem path, shell command, tool name,
proposal body, source mutation, URL fetch, or Python expression. Response envelopes include mode,
stage provenance (`generated`, `executed`, or `replayed`), canonical/live run identity, hashes,
failure code, and safe retry/reset advice. CORS is restricted to the Pages origin and explicitly
approved local rehearsal origins. Rate limits, request-size bounds, idempotency, timeouts, structured
logging, and no-store handling for live run responses are required.

## LLM architecture and reproducibility

The live path uses the same research model on different infrastructure. It must not upgrade Qwen,
replace it with Gemini/GPT/Llama, or resolve `latest` without digest verification.

| Configuration | Frozen value / deployment requirement |
|---|---|
| Model family / architecture | Qwen 2.5 / `qwen2` |
| Ollama model identifier | `qwen2.5:latest` (name only; must be pinned by digest) |
| Full Ollama digest | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` |
| Parameters | 7.6B |
| Quantization | `Q4_K_M` |
| Temperature | `0` |
| Context | explicit `num_ctx=8192` |
| Output reserve | explicit `num_predict=2048` |
| Adapter timeout used by RQ1 closure | 600 seconds |
| RQ1 task identity | `answer-reviewed-authoritative-portrayal-question` |
| RQ1 prompt contract | `src/nma/rq1_compare.py` shared instructions + one-field answer schema; canonical derived SHA-256 `710217e5388585805b35cd689c72afdd1416766152ef846421ef8824d9833221` |
| Shared system prompt | `src/nma/llm/ollama.py`; canonical text SHA-256 `4aa935ef67e22fd0bbc7e9c08bb3181833693f3a4f778e694061ab519ad9db16` |
| RQ2 planner identity | `rq2-provider-neutral-plan-composer/1.0` |
| RQ2 draft contract | `rq2-compact-plan-draft/1.0` |
| Ollama version | **not committed in frozen evidence**; pin an image digest and prove bounded compatibility before DEMO-PUBLIC-02 acceptance |

The prior RQ1 defect was an implicit Ollama context allocation of about 2,050 tokens when
`num_ctx` was omitted. Readiness must inspect the actual request options and observed prompt count;
a model metadata claim of a larger context is insufficient.

The inference container must obtain a content-addressed model artifact, verify the full digest
before starting, and reject mutable-tag drift. Prefer a pinned container-image digest and a pinned
model blob mirrored in controlled object storage or baked into a distinct content-addressed layer;
do not pull `qwen2.5:latest` from the public internet at audience request time. Google currently
documents Cloud Run GPU service support and one-GPU-per-instance deployment, while its inference
guidance recommends fast-loading formats, deliberate context/concurrency tuning, and a startup
probe that does not pass merely because Ollama opened a TCP port:
[GPU services](https://cloud.google.com/run/docs/configuring/services/gpu),
[GPU inference best practices](https://cloud.google.com/run/docs/configuring/services/gpu-best-practices),
and [Cloud Run health checks](https://cloud.google.com/run/docs/configuring/healthchecks).

An L4-class instance is the initial portability candidate, not a frozen performance result. The
7.6B Q4_K_M model is expected to be feasible, but DEMO-PUBLIC-02 must empirically prove GPU memory
sufficiency with the 8,192 context, warm canonical inference, and low concurrency. A larger GPU may
be selected only as infrastructure, without changing model bytes or generation settings.

Cloud feasibility verdict: **FEASIBLE WITH WARM INSTANCE / COST TRADE-OFF; NOT RECOMMENDED AS THE
LIVE-DEMO CRITICAL PATH**. The frozen repository proves the 7.6B Q4_K_M identity but does not
commit the exact model-blob byte size, Ollama image version, measured peak RAM/VRAM, cloud startup,
or cloud request latency. A 4-bit 7.6B parameter payload has a theoretical weight floor near 3.8 GB
before quantization metadata/runtime overhead; this is an engineering lower bound, not a measured
artifact size. DEMO-PUBLIC-02 must record actual image/model bytes and peak host/GPU memory.

Current official Cloud Run constraints make an L4 trial plausible: one L4 supplies 24 GB VRAM and
requires at least 4 vCPU/16 GiB instance memory (8 vCPU/32 GiB recommended); the platform advertises
about five seconds to GPU availability, but that excludes container/model download and load. The
service request maximum is 60 minutes and container startup limit is four minutes; those platform
limits accommodate frozen runs but are not acceptable audience latency. Set model concurrency to
`1` initially, minimum instance to `1` only during rehearsals/presentation, maximum instance to a
small quota-bound value, and use a model-aware readiness probe. Sources:
[Cloud Run GPU support](https://docs.cloud.google.com/run/docs/configuring/services/gpu),
[AI inference GPU best practices](https://docs.cloud.google.com/run/docs/configuring/services/gpu-best-practices),
[quotas and limits](https://docs.cloud.google.com/run/quotas), and
[request timeouts](https://docs.cloud.google.com/run/docs/configuring/request-timeout).

## Cold-start and readiness strategy

During the presentation window:

1. set GPU minimum instances to `1` and instance-based billing;
2. deploy the exact pinned container/model revision before rehearsal;
3. load the model into GPU memory during startup and keep it resident;
4. make startup/readiness pass only after full model-digest verification and a successful bounded
   warm inference with `num_ctx=8192`, `num_predict=2048`, temperature `0`;
5. run a presenter preflight health/readiness request and canonical warm request 15–30 minutes
   before the session;
6. configure inference concurrency at `1` initially, raising it only after measured memory/latency
   tests; cap maximum GPU instances and requests;
7. keep Canonical Replay selected until the presenter deliberately chooses Live Model;
8. automatically return a typed `LIVE_MODEL_UNAVAILABLE` fallback response without changing the
   canonical state.

Cloud Run documents minimum instances as the mechanism for reducing scale-from-zero latency, but
minimum instances do not by themselves prove that an Ollama model is loaded. The model-aware warm
probe is mandatory: [minimum instances](https://cloud.google.com/run/docs/configuring/min-instances)
and [general startup guidance](https://cloud.google.com/run/docs/tips/general).

## KG deployment architecture

### Strategy A — frozen KG snapshot (preferred)

The authoritative semantic source is the existing canonical JSON graph and its SHA-256. For the
public demo, produce a deterministic manifest containing either the full graph (only if a separate
publication review passes) or a bounded derivative with the exact node/edge records needed for
KG-1/KG-2/KG-3, RQ1 evidence replay, and RQ2 constraint trace. The derivation must select existing
records by ID and preserve properties/edges byte-semantically; it must not rename types, invent
relations, infer ProductLayer, or reconstruct missing semantics.

The snapshot manifest records source KG path/hash, selection algorithm/version, ordered node and
edge IDs, source evidence identities, output SHA-256, and public-data review decision. The browser
and CPU API verify this identity on load. JSON is preferred because it is already repository-native
and works in browser, Python, and Cloud Run without a graph service.

### Strategy B — live Neo4j/graph database (optional)

A live graph may serve the same allowlisted retrieval only after parity tests prove identical node,
edge, property, ordering, unresolved-state, source identity, and canonical subgraph results. The API
exposes no arbitrary Cypher. On timeout, mismatch, or health failure it atomically selects the
frozen snapshot and marks `GRAPH_DB_FALLBACK`. Neo4j is never presentation-critical.

## Demo state machine

The state machine is deterministic in Replay/Offline and server-confirmed in Live Model. Every
state retains a canonical snapshot, current mode, stage provenance, and last stable state. Invalid
actions are disabled rather than queued.

| State | Required data | Visible elements / behavior | Permitted next actions | Fallback |
|---|---|---|---|---|
| `READY` | verified bundle/build/mode identities | mode badge, scenario card, Reset disabled | Select Intent, change mode | remain READY with offline bundle |
| `INTENT_SELECTED` | canonical RQ1 question + RQ2 intent | same-intent/same-model banner | Compare RQ1, Reset | canonical question from bundle |
| `RQ1_COMPARE` | three answers/evaluations/aggregates | three columns, frozen metric labels | Show Evidence Graph, Reset | replay all three columns |
| `RQ1_GRAPH_OPEN` | KG-2 nodes/edges/sources | expanded graph + accessible table | Continue to RQ2 Baseline, close graph, Reset | bounded static graph |
| `RQ2_BASELINE` | baseline proposal/gate record | guessed/null values and BLOCKED-before-mutation | Run Constrained Planner, Reset | replay baseline block |
| `RQ2_CONSTRAINED` | retrieval + 7/4/0 constraints + proposal | resolved/unresolved trace and validator PASS | Execute, Reset | replay canonical proposal |
| `RQ2_EXECUTED` | receipt + source hashes + 12 postconditions | deterministic execution/verification PASS | Authorize RQ3, Reset | replay receipt/verification |
| `RQ3_AUTHORIZED` | exact proposal + authorization | ID/hash equality and RESEARCH AUTHORIZATION | Verify Trust Chain, Reset | replay authorization |
| `RQ3_VERIFIED` | execution/verification/provenance | all deterministic checks and six link types | Audit / Accept, Reset | replay trust records |
| `RQ3_ACCEPTED` | Boolean audit PASS | ACCEPT with research boundary note | Tamper Proposal, Complete, Reset | replay Case A acceptance |
| `RQ3_TAMPERED` | isolated Case C clone | changed-field/hash diff; original preserved | Validate Tamper, Reset | replay Case C input |
| `RQ3_REJECTED` | Case C rejection record | REJECT — FAIL CLOSED / hash mismatch / zero mutation | Complete, Reset | replay Case C result |
| `COMPLETE` | conclusion copy and evidence identity | conservative conclusion + research-info link | Restart/Reset | remain fully offline |

`Reset Demo` cancels in-flight requests, discards ephemeral live-run state, restores the immutable
canonical bundle, sets the state to `READY`, retains the chosen mode if healthy, and falls back to
Canonical Replay/Offline Replay when it is not. It must not require a browser reload.

## Canonical 5–7 minute conference flow

| Time | Presenter action | Audience takeaway |
|---|---|---|
| 0:00–0:30 | select canonical hydrant intent; point to same-question/same-model banner | retrieval architecture is the controlled variable |
| 0:30–2:00 | Compare RQ1; scan exact metrics; open KG-2 | no retrieval vs passages vs explicit entities/relations |
| 2:00–3:30 | show baseline block, 7/4/0 constraints, constrained proposal, execution and 12/12 verification | knowledge changes the plan before execution and unresolved state remains bounded |
| 3:30–5:00 | show proposal/hash, research authorization, execution equality, verification, provenance, audit, ACCEPT | trust is deterministic and proposal-bound, not an LLM judgment |
| 5:00–5:45 | Tamper Proposal; show Case C hash mismatch and pre-mutation rejection | fail closed on changed authorized content |
| 5:45–6:15 | show conservative conclusion and optional research-info panel | layered evidence and controls bound probabilistic behavior |

The presenter script must state the active mode once near the beginning and again before any live
model call. If a live call exceeds 15 seconds, select Canonical Replay and continue without waiting.

## Failure and fallback matrix

| Failure | Detection | Visible fallback | Preserved behavior | Presenter action |
|---|---|---|---|---|
| F1 — Cloud API unavailable | startup/short request timeout or non-2xx | badge `CANONICAL REPLAY — API UNAVAILABLE` | full RQ1/KG/RQ2/RQ3/tamper replay | continue; no retry loop |
| F2 — live model unavailable | model-aware readiness false, timeout, digest mismatch | replay canonical LLM outputs; deterministic CPU stages remain live if healthy | frozen metrics and proposal untouched | say “live model unavailable; replaying frozen run” |
| F3 — graph DB unavailable | health/query timeout or parity mismatch | `FROZEN KG SNAPSHOT` | all graph views/retrieval traces | continue; Neo4j optional |
| F4 — internet unavailable | browser offline / fetch failure | local `OFFLINE REPLAY` package | every research state and Reset | launch local static package |
| F5 — map tile/base map unavailable | MapLibre source error | local neutral basemap or no-basemap research layer | scenario geometry/trace and graphs | continue; tiles are nonessential |
| F6 — unexpected exception | top-level error boundary/invalid state | preserve last stable state; offer `Reset Demo` | canonical bundle remains immutable | reset; if repeated, use video |
| F7 — LLM cold start/timeout | readiness false or presenter 15 s budget expires | canonical RQ1/RQ2 replay | all frozen comparisons | cancel request and continue |
| F8 — GraphRAG service unavailable | retrieval timeout/noncanonical hash | frozen KG snapshot and evidence projection | 46→9 RQ1 and RQ2 trace | continue with frozen badge |
| F9 — stale browser cache/build mismatch | build/bundle identity mismatch | hard-reset to packaged local build | canonical hashes | use local launcher; no mixed assets |
| F10 — CORS failure | browser blocks optional API | static replay; show API unavailable | full guided flow | do not reconfigure live on stage |
| F11 — RQ3 backend unavailable | tamper/verification endpoint fails | replay frozen Case A and Case C records | trust argument with replay labels | continue; no retry loop |
| F12 — presenter changes ephemeral state | canonical object/hash guard or invalid action | discard clone and Reset Demo | original proposal remains immutable | press Reset |
| Static package/browser/device failure | local launch/render failure | emergency recording | complete core argument | play Video B |

Fallback is one-way during an active presenter step: `LIVE MODEL → CANONICAL REPLAY → OFFLINE REPLAY
→ VIDEO`. Recovery may be tested after Reset, but the UI must not oscillate automatically.

## Security boundary

Public functionality is deny-by-default and scenario-bounded:

- one canonical scenario and fixed action enumeration;
- fixed tool allowlist/order and deterministic parameter schemas;
- no arbitrary prompt, shell, Python, GIS command, filesystem path, Cypher, URL, upload, or source
  mutation;
- no private API key, cloud credential, Neo4j credential, model-store credential, production
  authorization credential, or secret in Pages assets;
- CPU API public ingress only where necessary; GPU/Ollama private ingress and authenticated service
  identity; graph credentials confined to the CPU service;
- isolated ephemeral output root, strict size/time/concurrency limits, no authoritative write target;
- CORS origin allowlist, content security policy, dependency pinning/SRI where applicable, safe
  structured error messages, and audit logs without raw secrets;
- replay/offline modes require no secret and perform no outbound data submission.

Research authorization artifacts are fixtures used to evaluate the deterministic trust boundary.
They are not production credentials and must be visibly labelled as such.

## Public data and fixture boundary

The canonical RQ2 Point GeoJSON is a committed research fixture with SHA-256
`6888bb077c6f7de2183ca1d4b1ca7d4bee934f939be7235520243c6cb4d10611`; it states that it was
derived without authoritative source mutation. RQ2/RQ3 operate only on an isolated symbolic
derivative and keep the source unchanged.

However, repository evidence does not authorize a general public-data substitution. The earlier
`NMA-DEMO-DATA-00` closure failed to establish executable public School/ROAD fixtures under the
frozen contracts. The private School archive and raw source PDFs remain excluded by
`.gitignore`/the v0.2.1 data boundary. Therefore:

- use only the committed hydrant research fixture and committed research records for this demo;
- do not introduce School/ROAD scenarios, infer historical coordinates, or emulate missing domain
  authorization;
- do not publish raw source PDFs, private archives, restricted attributes, or local caches;
- do not assume that committing the entire canonical KG proves redistribution permission for a
  new public bundle;
- require a file-level publication review for the bounded KG derivative and canonical text chunks,
  recording attribution/derivative status before DEMO-PUBLIC-01 publication;
- if any field is not publishable, replace it only with an already accepted bounded frozen
  derivative or omit it explicitly—never with semantically reconstructed public data.

This is a **FINDING**, not a semantic blocker to the architecture: the complete interaction can be
specified and replayed from committed bounded research artifacts, but publication eligibility of
the exact future static bundle must be closed before Pages deployment.

## Performance targets and measured risk

Targets are implementation gates, not measured cloud results:

| Stage | Target | Acceptance interpretation |
|---|---:|---|
| Static shell usable | < 3 s under normal conference connectivity | measure production bundle; offline launch also tested |
| Canonical replay transition | < 1 s | local/static transition, excluding optional API |
| bounded KG-2 interaction | < 2 s | deterministic layout or cached coordinates |
| warm live LLM first usable result | < 15 s where practical | not required for conference PASS; fall back at 15 s |
| deterministic canonical validation | < 2 s where practical | correctness dominates latency |

The frozen measured means were 19.27 s (LLM-only), 43.51 s (Text-RAG), and 125.54 s (GraphRAG);
the canonical GraphRAG run was 184.254 s. RQ2 local planning totals were about 151 s baseline and
228 s constrained. GPU performance is unmeasured. Consequently, live GraphRAG and RQ2 planning are
the primary latency risks and replay-first is mandatory. Static graphs, replay transitions, and
deterministic validators are the conference-critical path.

## Backup video specification

### Video A — full research demo

Target 5–6 minutes. Record the canonical replay path in a clean offline-capable build:

`User Intent → LLM-only → Text-RAG → GraphRAG → Evidence Graph → baseline blocked → constrained
plan → deterministic execution → RQ3 authorization → verification → provenance → tamper → FAIL
CLOSED → conservative conclusion`.

The recording must display the runtime-mode badge, frozen-evidence badge, proposal identity, and
tamper failure code. Capture at conference resolution with legible graph labels and an accessible
transcript/captions. Record the build/bundle identities in metadata and the research-info panel at
the end.

### Video B — emergency demo

Target 90–150 seconds:

`same intent/model → three-column RQ1 comparison → GraphRAG evidence relations → constrained
execution PASS → authorization/verification ACCEPT → Tamper Proposal → PROPOSAL_HASH_MISMATCH /
REJECT → conclusion`.

Both recordings are future DEMO-PUBLIC-03 outputs; this task does not record them.

## Implementation acceptance criteria

### DEMO-PUBLIC-01 — static / replay frontend

Pass only when:

- the Pages route and downloadable local package are built from the same canonical bundle;
- RQ1 shows LLM-only, Text-RAG, and GraphRAG with the exact frozen question/model/metrics/answers;
- Text-RAG passages and GraphRAG relations are visibly different and source-identifiable;
- KG-1, KG-2, and KG-3 meet the semantics/accessibility requirements above;
- RQ2 replays 7/4/0, the baseline pre-mutation block, constrained PASS, 6/6 preservation, and
  12/12 verification;
- RQ3 replays the exact proposal/authorization/trust chain and Case C tamper rejection;
- mode, stage-provenance, frozen-evidence, Reset Demo, and failure labels are always truthful;
- initial rendering and all state transitions work with backend calls blocked;
- the local package works with network disabled and no secret/configuration;
- CSP/dependency/publication/data review passes; no private/raw/restricted data or credential ships;
- canonical bundle hashes and the research-info panel are verified in CI;
- no semantic source file changes are included.

Readiness: **READY WITH BOUNDED PREREQUISITES** — close the bounded-bundle publication review and
implement the route/package without changing the current production Pages content until accepted.

### DEMO-PUBLIC-02 — cloud live backend

Pass only when:

- CPU orchestration and private GPU inference are separately deployed with least-privilege identity;
- container and model are pinned by full digests; exact Qwen 2.5 7.6B Q4_K_M identity is checked;
- the Ollama version/image digest is recorded and compatibility-tested;
- captured requests prove `num_ctx=8192`, `num_predict=2048`, temperature `0`, and the frozen
  system/task/prompt contracts;
- LLM-only, Text-RAG, and GraphRAG use the same inference endpoint/model/settings;
- model-aware startup/readiness, minimum instance `1` during presentation, explicit warm inference,
  low concurrency, memory sufficiency, timeouts, and a warm-model runbook are proven;
- snapshot retrieval matches canonical identities; optional graph DB parity/fallback is proven;
- deterministic RQ2/RQ3 code runs live with zero trust-stage model calls and unchanged proposal;
- public API inputs are allowlisted and cannot reach shell, arbitrary tools/Cypher, source mutation,
  credentials, or private data;
- live outputs are isolated from frozen evidence and every failure returns replay-safe status;
- failure drills demonstrate API/model/graph outages without interrupting the canonical path.

Readiness: **READY WITH BOUNDED PREREQUISITES** — GPU quota/region, exact container/model
availability, Ollama compatibility, memory, latency, and operational cost remain to be measured.

### DEMO-PUBLIC-03 — conference rehearsal and video

Pass only when:

- the 5–7 minute script is rehearsed end-to-end on the actual presentation device/network;
- mode declarations and scientific caveats are spoken and visible;
- live-to-replay, API, model, graph, internet, tile, exception/reset, and device/video drills pass;
- static, online, local/offline, and emergency-video launch instructions are tested by a second
  operator;
- Video A and Video B meet the sequence/duration/identity/caption requirements;
- performance observations are recorded without rewriting research metrics;
- a final go/no-go checklist confirms exact build/bundle/model/KG/proposal identities and backup
  availability.

Readiness: **READY WITH BOUNDED PREREQUISITES** after DEMO-PUBLIC-01 and DEMO-PUBLIC-02 are accepted;
the conference may still choose replay-only if live latency is not reliable.

## Semantic non-change audit

The branch diff and evidence hashes must prove: `KG: NO CHANGE`; `GraphRAG retrieval: NO CHANGE`;
`Evidence projection: NO CHANGE`; `RQ1 prompt/evaluator/comparison: NO CHANGE`; `RQ2 constraints:
NO CHANGE`; `RQ2 canonical proposal: NO CHANGE`; `Mapping semantics, geometry, classification,
portrayal and ProductLayer: NO CHANGE`; `Model: NO CHANGE`; `Authorization, verification and
provenance semantics: NO CHANGE`; and `Authoritative data: NO CHANGE`. The only permitted changed
paths are this report, demo-public manifests/storyboard, Mermaid specification sources, and the
focused acceptance test. Any protected-path diff is a semantic regression and fails closed.

At DEMO-PUBLIC-00 completion the audit result is **UNCHANGED**, subject to the focused test proving
all canonical byte hashes and the changed-path allowlist from the exact freeze SHA.

## Focused evidence-integrity checks

`tests/test_demo_public_00_specification.py` is the focused structural gate. It validates:

- branch/predecessor ancestry and canonical repository identity;
- every RQ1/RQ2/RQ3 evidence hash in the RQ-FINAL freeze and public evidence manifests;
- RQ2 proposal ID/hash/byte hash/blob identity and RQ3 continuity;
- frozen RQ3 Case C tamper evidence;
- exact model digest/family/parameters/quantization/context/temperature;
- canonical KG hash, required actual types/relations, and hydrant subgraph sources;
- report sections and all four Mermaid sources;
- the architecture-only changed-path allowlist, preventing semantic source changes.

The check deliberately validates structure and source identity rather than asserting arbitrary
prose sentences.

## Findings, limitations, and deployment risks

### A. RQ1 live comparability

**Technically yes; conference path replay-first.** The same inference service can run all three
conditions with the same model/settings and only the retrieval context changed. Reliability is not
yet sufficient for live-first presentation: local GraphRAG latency was high, GraphRAG natural text
was not byte-identical across all temperature-zero repeats, and live output cannot replace frozen
evidence.

### B. Model portability

**READY WITH BOUNDED PREREQUISITES.** Cloud Run supports GPU-hosted Ollama-like inference, and the
Q4_K_M 7.6B model is a plausible one-GPU workload. Acceptance still requires exact model artifact
availability, full-digest verification, pinned Ollama image/version, 8,192-context memory testing,
warm inference, GPU quota/region, and latency/cost measurement. No newer Qwen or alternative model
may enter the canonical live path.

### C. KG portability

**READY WITH BOUNDED PREREQUISITES.** The repository already has a content-addressed canonical JSON
graph and an RQ2 bounded retrieval package, so no semantic reconstruction is needed. A deterministic
selection/manifest and public-file review must precede publication; optional Neo4j must prove parity
and is not a fallback dependency.

### D. Data-authority boundary

**FINDING.** The hydrant fixture and research records are committed and bounded, but the prior
School/ROAD public-fixture task failed closed and raw/private sources remain excluded. Publication
must use only reviewed bounded derivatives and must not assume that all graph/text records are
redistributable merely because they are present in Git.

### E. Latency risk

**High for live model stages; low for static/replay/trust stages subject to measurement.** RQ1
GraphRAG and both RQ2 planning conditions exceed the desired conference threshold in frozen local
measurements. Prewarming cannot guarantee sub-15-second model output. The presenter never waits on
live inference after the fallback threshold.

### F. Cloud dependency risk

**No cloud service is presentation-critical.** Cloud Run CPU improves live deterministic
demonstration; GPU enables optional live inference; Neo4j is optional. GitHub Pages is needed for
the public URL but not after the offline package is prepared. The local package and videos are the
conference continuity boundary.

Additional scientific limitations remain those of RQ-FINAL-00: one fire-hydrant task family, one
model/runtime, a bounded validator and Text-RAG baseline, one RQ2 fixture/proposal, symbolic output,
unresolved ProductLayer/physical portrayal, and research identities rather than PKI, trusted time,
revocation, legal authority, or production non-repudiation.

## Next-step recommendation

Proceed only in this order:

1. **DEMO-PUBLIC-01:** create and accept the hashed static/replay bundle, three graph views, state
   machine, reset/fallback behavior, local package, and public-data review. Make this fully reliable
   before any cloud dependency.
2. **DEMO-PUBLIC-02:** deploy the allowlisted CPU API and private pinned Qwen/Ollama GPU service,
   prove exact configuration/readiness/fallback, and keep live output isolated.
3. **DEMO-PUBLIC-03:** rehearse, time, drill failures, package offline assets, record both videos,
   and make the final go/no-go decision.

Stop after this accepted specification. Do not deploy Cloud Run, modify production Pages, record
the conference video, merge, or tag as part of DEMO-PUBLIC-00.

## Architecture diagram sources

- Diagram A — [Public Runtime Architecture](docs/diagrams/demo-public-00/diagram-a-public-runtime-architecture.mmd)
- Diagram B — [RQ1 Controlled Comparison](docs/diagrams/demo-public-00/diagram-b-rq1-controlled-comparison.mmd)
- Diagram C — [Full Research Demo Flow](docs/diagrams/demo-public-00/diagram-c-full-research-demo-flow.mmd)
- Diagram D — [Fallback Architecture](docs/diagrams/demo-public-00/diagram-d-fallback-architecture.mmd)

## Acceptance verdict

**PASS WITH FINDINGS.** Criteria A–N are specified: the three-way RQ1 comparison, evidence-based
Text-RAG/GraphRAG distinction, actual KG semantics, full RQ2/RQ3 sequence, three runtime modes,
implementation-ready cloud boundary, exact-Qwen and context controls, cold-start/failure strategy,
tamper action, static/offline/video fallback, security/data boundaries, zero semantic changes, and
future task gates. Findings are bounded to live latency, missing frozen Ollama version, cloud
operational prerequisites, and public-bundle publication review.

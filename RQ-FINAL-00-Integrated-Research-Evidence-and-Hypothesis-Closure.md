# RQ-FINAL-00 — Integrated Research Evidence and Hypothesis Closure

Report date: 2026-08-28 (Asia/Taipei)

## Executive verdict

**READY FOR FREEZE WITH FINDINGS.** The committed experiments support a bounded layered National
Map Agent (NMA) architecture under the tested fire-hydrant portrayal task family and canonical
symbolic-execution scenario. RQ1 found that explicit graph-grounded geographic knowledge improved
measured answer correctness, coverage, and combined grounding relative to the frozen LLM-only and
Text-RAG conditions. RQ2 found that propagating explicit knowledge-derived constraints into the
same planner changed its plan before execution, produced the only semantically valid executable
proposal, and supported deterministic execution and postcondition verification. RQ3 admitted that
exact RQ2 proposal through proposal-bound authorization, deterministic execution and verification,
content-addressed provenance, and audit, while rejecting the frozen tamper/unauthorized cases.

This is an experimental architecture conclusion, not a universal claim that GraphRAG is superior,
that hallucination is eliminated, that an LLM is intrinsically trustworthy, or that the workflow
is production-certified or institutionally authorized.

## Research questions

### RQ1 — Knowledge Grounding

Does explicit geographic knowledge grounding improve the Agent's ability to answer mapping
questions accurately and with traceable evidence? The frozen comparison is LLM-only versus
Text-RAG versus GraphRAG. RQ1 concerns evidence-supported reasoning, not execution authorization.

### RQ2 — Constrained Agentic Execution

Can a knowledge-grounded agent translate mapping intent into executable plans while maintaining
explicit cartographic and geospatial constraints? The frozen comparison is the LLM Planner versus
the Knowledge-Constrained Planner under the same intent, model, proposal contract, tools,
validator, executor, and verifier. The intervention is explicit constraint propagation into
planning; tool calling alone is not the research treatment.

### RQ3 — Trustworthy / Auditable Mapping

Can authorization, deterministic verification, and provenance make probabilistic AI agents
suitable for authoritative mapping workflows? RQ3 tests the deterministic workflow boundary around
a frozen probabilistic proposal. It does not assert that the LLM becomes deterministic or
inherently trustworthy.

## Experimental lineage

The canonical repository is `https://github.com/dongpo/topoMap.git`. The ancestry below is linear;
each listed commit is an ancestor of predecessor
`3fed8fb77e759d004a7b91b23d933d41d8f70225`.

| RQ / task | Commit | Parent / role |
|---|---|---|
| RQ1-TRACE-01 | `cf41fdacaa719efa440307df1afca067768e2d8a` | End-to-end evidence-to-answer trace; identified provider truncation and validator gaps |
| RQ1-PROMPT-01 | `596dc67cd026116637e5d4c1fe4ec92aedaadbc8` | Exact successor; closed context-budget and prompt propagation |
| RQ1-VALIDATOR-01 | `6961b992d3fd49714fd14023afba60cba2f4e1d2` | Exact successor; closed claim-grounding and coverage validation |
| RQ1-COMPARE-01 | `d3c7dacbb1c3aea988e27909d1ebe0f0595dd3d6` | Exact successor; frozen three-architecture comparison |
| RQ2-DEMO-00 | `802d76ac79c34d0f681911a8e956b253bf62bd05` | Exact successor; architecture and acceptance freeze |
| RQ2-DEMO-01 | `673bcb6efb84de2aeaac5c4b23beda364bea9e44` | Exact successor; accepted constrained-planning experiment |
| RQ3-DEMO-00 definition | `cfe4878579cc9f10c0010985eeeeb9d6ceced776` | Exact successor; trust architecture definition |
| RQ3-DEMO-00 final | `2c3c25937615cfe01e989bdeb64b25ad6c27251f` | Completion verification |
| RQ3-DEMO-01 final / RQ-FINAL predecessor | `3fed8fb77e759d004a7b91b23d933d41d8f70225` | Authorized execution, verification, provenance, and audit experiment |

RQ-FINAL-00 was branched directly from the last identity. No historical result was recreated or
rewritten for this report.

## Experimental design matrix

| RQ | Hypothesis | Intervention / comparison | Controlled factors | Dependent variables / observable outcomes | Canonical scenario and acceptance criteria | Evidence source | Verdict | External-validity boundary |
|---|---|---|---|---|---|---|---|---|
| RQ1 | Explicit geographic knowledge grounding improves accurate, traceable mapping-question answers under the frozen evaluation. The frozen work did not assign this proposition an `H1` identifier. | LLM-only vs Text-RAG vs GraphRAG across the same canonical question and ten frozen semantic variants | Qwen 2.5 7.6B identity, temperature 0, 8,192 context, 2,048 output reserve, authoritative domain, six requirements, deterministic evaluator, no-truncation guard; comparable Text-RAG/GraphRAG evidence-token ceilings | Requirement accuracy; six-category coverage; exact 6/6 answers; supported, unsupported, and contradicted claims; evidence/citation identity integrity; truncation; token and latency cost | Fire-hydrant `9350906` portrayal question family; all 33 primary runs and 9 repeats retained; accepted validator applied without post-hoc answer repair | `rq1-compare-01-results.json`, comparison report, protocol/fixture, prompt and validator closure reports | **SUPPORTED WITH FINDINGS** | One semantic task family, 11 wordings, one local model/runtime, one KG/corpus, bounded validator, non-modern Text-RAG embedding baseline |
| RQ2 | H2: a knowledge-grounded planner preserves explicit geographic/cartographic constraints more reliably than an unconstrained LLM planner | Same planner with no evidence/constraints vs canonical GraphRAG retrieval → deterministic constraint resolution → explicit constraints supplied before planning | Same intent and fixture, model/identity, temperature/context, proposal schema, tool allowlist, validator, executor, verifier; no validator-to-planner repair | Retrieval integrity; 7 resolved/4 bounded unresolved/0 contradicted constraints; proposal validity; baseline pre-mutation block; constrained execution; 6/6 constraint preservation; 12/12 postconditions; source unchanged | Prepare one fire-hydrant feature for authoritative map production; constrained proposal must validate, execute only in isolated output, and verify; baseline receives no hidden knowledge | RQ2 report, retrieval/constraints/proposals/comparison/summary artifacts, Cases A–G | **SUPPORTED** | One feature/scenario, one model and graph snapshot, symbolic derived artifact rather than final authoritative render; unresolved ProductLayer and physical portrayal |
| RQ2 | H2b: knowledge grounding contributes at the planning layer before execution | Persist and compare first-pass baseline/constrained drafts and their proposal traces before tool execution | Same paired controls as H2; no rendered-output dependency; no post-hoc semantic repair | Plan-level semantic differences; decision difference; 11/11 constraint references; evidence-to-constraint-to-plan trace completeness | Pre-execution plan must expose class, geometry, portrayal, source authority, unresolved states, decision, and trace differences | `artifacts/rq2/rq2-demo-01-comparison.json` and canonical proposal | **SUPPORTED** | Conservative global constraint-to-step references and one paired accepted run limit generalization |
| RQ3 | H3: exact authorization, deterministic execution/verification, and complete provenance can bound a probabilistic proposal for auditable workflow participation | Frozen canonical proposal through positive trust chain plus Cases B–K invalid/tampered variants and Case L exact replay | Exact RQ2 proposal bytes/hash/plan, frozen schemas and policy, source identity, closed request, deterministic environment, unchanged RQ2 executor, zero model calls at trust controls | Proposal/hash binding; authorization; scope/tool/parameter checks; source mutation boundary; execution record; independent postconditions; provenance completeness; audit integrity; final acceptance; tamper rejection; replay stability | Case A must accept, B–K must fail closed, L must reproduce byte-identical result; no authoritative source mutation | RQ3 report, authorization, A/L records, audit, and experiment summary | **SUPPORTED WITH FINDINGS** | One symbolic proposal; research identity/clock; no PKI, trusted time, revocation, institutional authority, final rendering, or production source mutation |

## RQ1 findings

### Controlled comparison

The repository contains 33 primary records (three architectures × eleven questions) and nine raw
canonical repeats. All 42 stored runs report no silent truncation. The exact frozen aggregates are:

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

GraphRAG had higher measured requirement accuracy and coverage than both baselines on all eleven
wordings, but it did not dominate every subtype: Text-RAG and GraphRAG tied on geometry; Text-RAG
had zero contradicted selected-text claims while GraphRAG had two parser-induced contradictions in
one conversational variant. GraphRAG was also materially more expensive in tokens and latency.
The evidence supports specific grounding, coverage, and relationship advantages in this task; it
does not support the universal ordering `GraphRAG > Text-RAG > LLM-only` for all mapping work.

### Context, evidence projection, and validation closure

RQ1-TRACE-01 found that the complete 46-node/54-edge evidence package reached the constructed
request, but Ollama's implicit context allocation evaluated only about 2,050 of 14,738 tokens. The
missing answer elements therefore could not safely be attributed to the KG or the model-synthesis
architecture. RQ1-PROMPT-01 kept retrieval unchanged, projected nine question-relevant nodes/eight
edges, explicitly configured 8,192 context with a 2,048-token reserve, observed 2,841 prompt tokens,
and reproduced all six requested elements with no truncation. RQ1-VALIDATOR-01 then separately
closed evidence-ID integrity, citation-ID integrity, claim grounding, and six-category question
coverage with zero validation model calls. The comparison experiment inherited these closures.

### RQ1 hypothesis closure

- **Statement:** explicit geographic knowledge grounding improves accurate and traceable answers
  to the frozen mapping questions, compared under LLM-only, Text-RAG, and GraphRAG architectures.
  This is the closest canonical proposition in the frozen RQ1 work; no retroactive `H1` label is
  introduced.
- **Evidence:** the controlled aggregates above; 11/11 GraphRAG evidence/citation integrity checks;
  lower combined applicable adverse-claim rate (2/98 versus Text-RAG 18/67); the exact context and
  validator closures; and comprehensive committed raw/aggregate records.
- **Alternative explanations:** wording sensitivity, one model, the bounded claim extractor,
  GraphRAG's stricter evidence-bearing answer contract, retrieval representation, and the simple
  deterministic Text-RAG embedding may contribute to measured differences. The old incomplete
  answer is specifically attributable to a context-delivery defect and is not evidence against
  the KG or synthesis architecture.
- **Verdict:** **SUPPORTED WITH FINDINGS**.
- **Claim boundary:** the experiment does not establish universal GraphRAG superiority,
  hallucination elimination, cross-domain mapping accuracy, model-independent benefit, or
  human-equivalent semantic judgment.

## RQ2 findings

### Causal comparison

The independent variable is explicit knowledge-derived constraints supplied before planning, not
the mere use of GraphRAG or GIS tools.

```text
same intent + fixture                    same intent + fixture
        │                                        │
        ▼                                        ▼
LLM Planner (no evidence)               canonical GraphRAG retrieval
        │                                        │
        ▼                                        ▼
structurally valid proposal             deterministic constraint resolution
        │                               7 resolved / 4 bounded unresolved / 0 contradicted
        ▼                                        │
common precondition gate                         ▼
        │                               same Knowledge-Constrained Planner
        ▼                                        │
BLOCKED before mutation                           ▼
                                        semantically valid proposal
                                                 │
                                                 ▼
                                        deterministic GIS execution
                                                 │
                                                 ▼
                                        postcondition verification: PASS
```

The baseline selected the same six capabilities but guessed `fire_hydrant`/`point`, supplied no
line/color values, and could not bind source authority to evidence. Its proposal passed structural
validation but the common source-authority precondition blocked it before mutation. The constrained
condition retrieved explicit evidence, resolved class `9350906`, geometry `Point`, line `2`, color
`7`/`black`, accepted source authority, and the no-authoritative-render guard; it preserved
ProductLayer and three physical portrayal matters as bounded unresolved constraints. Its proposal
validated, executed the allowlisted isolated symbolic operations, preserved all six applicable
semantic constraints, and passed 12/12 postconditions. Successful execution alone was insufficient:
Case G executed but failed independent postcondition verification.

### H2 closure

- **Statement:** a knowledge-grounded mapping agent can generate executable GIS plans that preserve
  explicit geographic and cartographic constraints more reliably than an unconstrained LLM planner.
- **Evidence:** same-intent paired comparison; 7 resolved, 4 bounded unresolved, 0 contradicted;
  constrained semantic proposal validity; 11/11 constraint coverage; baseline blocked before
  mutation; constrained execution PASS; 6/6 preservation and 12/12 postcondition PASS.
- **Alternative explanations:** one fixture and scenario, model-output variation, planner/validator
  implementation coupling, and deterministic gate design bound causal reach. Three pre-acceptance
  attempts exposed timeout/draft-cap/reason-code issues; they are preserved and no failed proposal
  was repaired or executed. The evidence isolates the operative treatment as explicit constraint
  propagation, not GraphRAG alone.
- **Verdict:** **SUPPORTED** for the bounded paired scenario.
- **Claim boundary:** no universal planner superiority, production authorization, final physical
  portrayal, resolved ProductLayer, or performance across other map operations is established.

### H2b closure

- **Statement:** knowledge grounding contributes observably at the planning layer before execution,
  not merely in the final rendered result.
- **Evidence:** persisted first-pass plans differ in classification, geometry, portrayal values,
  source authority, unresolved-state semantics, decision, and trace; the comparison contains a
  complete 11-constraint evidence-to-plan trace.
- **Alternative explanations:** the compact draft's global constraint set produces conservative,
  non-minimal per-step references; one paired scenario does not measure trace quality broadly.
- **Verdict:** **SUPPORTED**.
- **Claim boundary:** trace completeness here does not prove optimal plans, minimal explanations,
  or general causal interpretability of arbitrary LLM reasoning.

## RQ3 findings

### Causal trust-chain argument

```text
probabilistic frozen RQ2 proposal
        ↓ exact ID + canonical hash + byte hash + plan identity
proposal-bound authorization
        ↓ closed scope, tools, parameters, source, unresolved guards, replay state
deterministic execution boundary (unchanged RQ2 executor; zero model calls)
        ↓ execution record
independent deterministic verification
        ↓ content-addressed provenance
Boolean audit and final acceptance
```

Case A was accepted with the exact canonical proposal, explicit authorization, unchanged source,
deterministic execution, independent verification, all six mandatory provenance link types, and a
reconstructable PASS audit. Cases B–K each failed as frozen: missing authorization, proposal
tampering, scope mismatch, unauthorized tool, parameter tampering, postcondition violation,
incomplete provenance, unauthorized mutation, unresolved-constraint escalation, and artifact
tampering. Case L accepted one exact replay with the same result SHA-256. Thus all 12 A–L cases
matched their expected fail-closed/accept behavior; no negative case changed the source fixture.

### H3 closure

- **Statement:** a probabilistic AI-generated mapping proposal can be incorporated into an
  authoritative mapping workflow when execution is explicitly authorized, bound to immutable
  proposal identity, limited to deterministic allowlisted GIS operations, independently verified
  against explicit conditions, and recorded through complete provenance.
- **Evidence:** independently recomputed proposal hash; authorization and exact scope binding;
  authorized proposal equals executed proposal; deterministic execution and verification PASS;
  no unauthorized source mutation; valid receipt; complete provenance; audit integrity; Case A
  accept; B–K reject; L stable replay; 12/12 expected outcomes.
- **Alternative explanations:** the trust adapter and validators share repository contracts and
  fixtures; deterministic validators only cover encoded conditions; tamper cases are a bounded
  adversarial set; the research clock/identity are not external institutional controls; one
  proposal limits generality.
- **Verdict:** **SUPPORTED WITH FINDINGS**.
- **Claim boundary:** RQ3 evaluates the trustworthiness of the workflow boundary, not intrinsic LLM
  trustworthiness. It does not supply PKI, trusted time, revocation, legal authority, production
  non-repudiation, source-mutation approval, or universal tamper coverage.

## Cross-RQ artifact handoff

### RQ1 → RQ2: SEMANTIC/ARCHITECTURAL HANDOFF

RQ2 technically reuses the accepted canonical graph identity
`4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4`,
`CanonicalGraphRetriever`, typed graph expansion, evidence identifiers, properties, and source
provenance patterns established in RQ1. It then creates its own RQ2 retrieval package
(`rq2-demo-01-retrieval-package`, canonical identity
`8f6fefa8b9ee96860a29b994cbcdcac9a48e6a1ca002777165f6c17dda904b25`) and deterministically
projects that evidence into resolved/unresolved/contradicted constraints.

RQ2 does **not** consume `rq1-compare-01-results.json`, an RQ1 answer, or the exact RQ1 nine-node
LLM projection as its input artifact. Its retrieval retains activation gates and unresolved mapping
state needed for constraint resolution. Therefore the experiments establish architectural and
semantic continuity through a shared frozen KG/retrieval/evidence vocabulary, but not byte-for-byte
continuity from an RQ1 output to RQ2. Calling this a direct immutable artifact handoff would
overstate the evidence.

### RQ2 → RQ3: DIRECT IMMUTABLE ARTIFACT HANDOFF

| Check | Evidence | Result |
|---|---|---|
| RQ2 produced proposal | RQ2 final `673bcb6...`; canonical path and report | PASS |
| Exact Git blob persisted | Blob `c7ba805bf44763249e842512b01fbe2308fb6724` is identical at `673bcb6`, `2c3c259`, and `3fed8fb` | PASS |
| Proposal ID | `rq2-proposal:knowledge-constrained:e635111c3be29423faf923b7` | PASS |
| Frozen canonical proposal hash | `116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1` | PASS |
| File byte SHA-256 | `8ad05eea5111a0c535be275effa6b8a6c3dce7b74c7149bf42811a1866aa4829` | PASS |
| RQ3 loaded, did not regenerate | Direct canonical path load; zero planner calls; RQ3 report and tests | PASS |
| Independent hash validation | Frozen RQ2 zero-substitution hash recomputed before authorization | PASS |
| Authorization binding | Authorization ID/hash and proposal ID/hash match | PASS |
| Execution/verification binding | Case A execution and verification records carry exact ID/hash | PASS |
| Provenance/audit binding | Case A audit `PROPOSAL` link and top-level identity carry exact ID/hash | PASS |

## Hypothesis–Evidence Matrix

| Hypothesis | Experimental comparison / intervention | Evidence | Result | Claim boundary |
|---|---|---|---|---|
| RQ1 comparison proposition (no frozen `H1` label) | LLM-only vs Text-RAG vs GraphRAG; same 11 questions/model/context/evaluator | GraphRAG 75.76% mean accuracy and 86.36% coverage vs 45.45%/68.18% Text-RAG and 15.15%/40.91% LLM-only; 96 supported, 0 unsupported, 2 contradicted claims; context and validator closures | **SUPPORTED WITH FINDINGS** | One task family/model/KG and bounded evaluator; no universal ranking or hallucination elimination |
| RQ2 H2 | Knowledge-constrained planning vs baseline LLM planning | 7 resolved, 4 bounded unresolved, 0 contradicted; both proposals schema-valid; baseline blocked before mutation; constrained execution PASS; 6/6 preservation; postcondition verification PASS | **SUPPORTED** | One symbolic fire-hydrant scenario; causal treatment is explicit constraint propagation, not GraphRAG alone |
| RQ2 H2b | Persisted pre-execution plan comparison and trace | Plan-level differences in values/authority/guards/decision; 11/11 constraint-to-plan trace COMPLETE | **SUPPORTED** | Trace is conservative/global, not proof of optimal or universally interpretable reasoning |
| RQ3 H3 | Trust controls applied to the frozen exact RQ2 proposal | Exact proposal-hash binding; authorization; deterministic execution and verification; complete provenance; PASS audit; no unauthorized mutation; A–L 12/12 expected outcomes | **SUPPORTED WITH FINDINGS** | Trust boundary only; research identity/time and one proposal; no intrinsic LLM trust or institutional authorization |

## Integrated architecture

```text
USER MAPPING INTENT
        │
        ▼
RQ1 — KNOWLEDGE GROUNDING
canonical KG + GraphRAG + projected geographic evidence
        │
        │ SEMANTIC/ARCHITECTURAL HANDOFF
        │ shared frozen KG identity, retriever, typed relationships,
        │ evidence identifiers/provenance — not an RQ1 result-file handoff
        ▼
RQ2 — CONSTRAINED AGENTIC EXECUTION
RQ2 evidence package
  → resolved / bounded-unresolved / contradicted constraints
  → plan
  → canonical proposal
  → deterministic GIS execution
  → postcondition verification
        │
        │ DIRECT IMMUTABLE ARTIFACT HANDOFF
        │ exact proposal ID + canonical hash + byte identity
        ▼
RQ3 — TRUSTWORTHY / AUDITABLE MAPPING
proposal identity
  → authorization
  → deterministic execution boundary
  → independent deterministic verification
  → content-addressed provenance
  → audit
        │
        ▼
ACCEPTED AUDITABLE MAPPING ACTION UNDER TEST CONDITIONS
```

The final node is not a production authorization. The accepted artifact remains isolated,
symbolic, non-authoritative, and constrained by unresolved ProductLayer/physical portrayal gates.

## Claim ladder

| Claim | Classification | Evidence boundary |
|---|---|---|
| C1 — Explicit geographic knowledge can ground mapping-related LLM reasoning under the tested cases. | **SUPPORTED** | RQ1 controlled grounding, correctness, coverage, and trace results |
| C2 — Knowledge-constrained planning improves compliance with explicit geographic/cartographic constraints under the canonical scenario. | **SUPPORTED** | Same-intent paired RQ2 comparison; constrained semantic PASS vs baseline pre-mutation block |
| C3 — A knowledge-constrained Agent can produce a valid executable mapping proposal under the tested scenario. | **SUPPORTED** | Canonical RQ2 proposal validates, executes in isolation, and verifies |
| C4 — Deterministic GIS execution can enforce the boundary between proposal and mutation. | **SUPPORTED** | Allowlist/preconditions, source preservation, and blocked negative cases under encoded operations |
| C5 — Authorization bound to proposal identity can prevent unauthorized execution. | **SUPPORTED** | Missing/mismatched/tampered proposal/authorization/scope variants blocked before mutation |
| C6 — Deterministic postcondition verification can detect invalid execution outcomes. | **SUPPORTED** | RQ2 Case G and RQ3 Case G reject successful execution with invalid observed state |
| C7 — Provenance and audit records can reconstruct the tested mapping action. | **SUPPORTED** | Six mandatory content-addressed links and canonical Case A audit |
| C8 — Tampered trust-chain variants can be rejected fail-closed. | **SUPPORTED** | RQ3 A–L matched expected outcomes; B–K all rejected |
| C9 — The complete architecture is suitable for all authoritative national mapping workflows. | **NOT TESTED** | One symbolic scenario cannot establish all-workflow suitability |
| C10 — The experiments prove that LLMs are trustworthy. | **NOT JUSTIFIED** | Experiments bound proposals with external knowledge and deterministic controls; they do not change intrinsic model trust |

## Threats to validity

### Internal validity

- The earlier implicit Ollama context limit caused truncation. The controlled comparison explicitly
  configured and observed budgets, but prompt construction and local runtime remain causal factors.
- Temperature zero did not make GraphRAG wording byte-deterministic; model and runtime variation can
  affect free-form answers and plans.
- RQ2 planner, schema projection, validator, executor, and verifier share repository contracts.
  Their tests establish consistency with frozen contracts, not complete implementation independence.
- Fixtures and negative cases were designed around the canonical fire-hydrant scenario; they may
  align unusually well with encoded validators.
- RQ2's three failed pre-acceptance attempts demonstrate implementation sensitivity. Retention of
  those attempts reduces reporting bias but does not create statistical replication.
- RQ3 verification is independent of executor success but not institutionally independent software;
  common contract mistakes could escape both components.

### Construct validity

- RQ1 requirement accuracy/coverage and bounded claim extraction operationalize grounding; they do
  not measure every aspect of geographic knowledge quality or natural-language correctness.
- The validator under-recognizes some semantic equivalents and produced two conversational
  ProductLayer contradictions. Exact numeric scores are therefore bounded-observable measures.
- RQ2 constraint satisfaction operationalizes constrained agentic correctness. A compliant plan may
  still be non-optimal or unsuitable for an unencoded cartographic concern.
- RQ3 tamper rejection operationalizes workflow trustworthiness. It does not measure social,
  organizational, legal, cyberphysical, or model-behavior trust in full.
- Provenance completeness shows that required typed links resolve and reconstruct the tested action;
  it does not by itself establish truth, non-repudiation, or long-term records governance.

### External validity

- RQ1 covers one portrayal task family and eleven wordings, not independent mapping task diversity.
- RQ2/RQ3 cover one Point feature class, one canonical proposal, and isolated symbolic derivation;
  no multi-feature editing, topology, generalization, conflation, raster processing, or final render
  is evaluated.
- One KG/schema snapshot, one local Qwen model/quantization, and a deterministic feature-hash
  Text-RAG baseline limit model, retrieval, and corpus generalization.
- There is no multi-agent or organizational federation, real NMA institutional authorization,
  PKI, trusted time, revocation, durable policy administration, or legal accountability.
- Results do not establish applicability to other agencies, datasets, jurisdictions, scales,
  feature classes, or authoritative mutation types.

### Reproducibility validity

- Frozen Git SHAs, committed protocols, fixtures, schemas, result bundles, and exact artifact hashes
  make the deterministic evidence package repository-addressable.
- RQ1 free-form model runs depend on a local Ollama model identity/runtime and hardware. The complete
  controlled output is committed, but live regeneration requires that external model environment.
- Some RQ1 exact live rerun directories cited by predecessor reports were under `/private/tmp` and
  are transient. Their conclusions and artifact hashes are captured in committed reports/tests;
  the central controlled comparison is fully committed in `rq1-compare-01-results.json`.
- RQ2/RQ3 generated bundles are committed and deterministic validators can inspect them without
  transient state. Live execution still depends on filesystem and runtime assumptions encoded by
  the fixtures.
- Broad regressions contain historical exact-scope/freeze failures. They must be interpreted only
  against the exact predecessor baseline; all-green rewriting would damage historical evidence.

## Findings and limitations

| Finding | Classification | Origin | Affects hypothesis support? | Affects reproducibility? | Future work? | Blocks freeze? |
|---|---|---|---|---|---|---|
| Earlier incomplete RQ1 answer followed provider context truncation; attribution to KG/model synthesis was unsafe | methodological / implementation | RQ1-TRACE-01 → PROMPT-01 | No after closure; changes interpretation of earlier observation | No; closure settings/results recorded | Only for broader provider/runtime replication | No |
| Bounded RQ1 validator misses some semantic equivalents and induced two conversational ProductLayer contradictions | methodological / construct | RQ1-VALIDATOR-01 / COMPARE-01 | Bounds exact effect sizes; does not reverse tested ordering | Raw answers/claims retained | Improve only under a separately frozen evaluator study | No |
| Text-RAG uses deterministic feature hashing, not a modern learned multilingual embedding | external-validity | RQ1-COMPARE-01 | Limits baseline-generalization claim | Reproducible by design | Compare stronger baselines separately | No |
| GraphRAG used more tokens/latency and absolute results varied by wording | scope / methodological | RQ1-COMPARE-01 | Requires `WITH FINDINGS` and bounded claim | Metrics committed | Broader benchmark/replication | No |
| Three RQ2 pre-acceptance attempts failed (timeout, draft cap, lowercase reason codes); none was repaired/executed | implementation | RQ2-DEMO-01 | No for accepted bounded attempt; limits robustness inference | Yes positively: failures are committed | Planner/runtime robustness study | No |
| ProductLayer and physical stroke/color/glyph gates remain unresolved; output is symbolic, non-authoritative | scope | RQ2/RQ3 | No for bounded symbolic hypotheses | Explicitly preserved in proposal/audit | Required before physical production claims | No |
| Constraint-to-step references are complete but conservatively global rather than minimal | non-semantic technical debt | RQ2-DEMO-01 | No for H2b completeness; limits explanation precision | No | Optional trace-minimization study | No |
| Research authorization identity and deterministic clock are not PKI, trusted time, revocation, or non-repudiation | external-validity / scope | RQ3-DEMO-01 | No for research H3; prevents production claim | Deterministic research reproduction is improved | Required for production/institutional deployment | No |
| One canonical proposal and bounded A–L cases do not establish universal tamper or workflow coverage | external-validity | RQ3-DEMO-01 | Requires `WITH FINDINGS` | No | Replicate across scenarios/threat models | No |
| Historical broad-suite freeze/scope assertions fail at the exact predecessor; one additional RQ3-DEMO-00 successor-scope assertion fails after RQ3-DEMO-01 | inherited regression | RQ3-DEMO-01 baseline comparison | No semantic/domain impact | Requires predecessor-relative interpretation | Historical test governance, separately authorized | No |
| Some predecessor reports cite transient `/private/tmp` live-run directories | reproducibility | RQ1 prompt/validator tasks | No; central comparison and conclusions are committed | Limits byte recovery of those exact auxiliary runs | Archive future live bundles by policy | No |

Non-blocking findings are documented, not fixed in RQ-FINAL-00.

## Regression interpretation

The accepted RQ3-DEMO-01 baseline records:

- focused RQ3: **24 passed**;
- targeted RQ1/RQ2/RQ3/Core/ROAD/School Hero/BUILD: **854 passed, 177 skipped,
  2 inherited historical scope failures, 0 semantic failures**;
- clean broad candidate: **1338 passed, 208 skipped, 28 failed**;
- exact RQ3-DEMO-00 predecessor: **1315 passed, 208 skipped, 27 failed**;
- delta: all 27 predecessor failures persist plus one expected
  `test_rq3_demo_00_specification.py::test_only_rq3_demo_00_specification_artifacts_changed`
  successor-scope assertion;
- RQ3 semantic regressions: **0**.

RQ-FINAL-00 adds a focused structural evidence-integrity test. It does not rewrite historical tests
or reclassify a failure without exact-predecessor evidence. Current validation results are recorded
in the machine-readable manifest after execution.

## Reproducibility package

All evidence needed for the central conclusions is repository-addressable: RQ1 protocols, question
fixtures, controlled raw/aggregate results and closure reports; RQ2 schemas, protocol, retrieval,
constraints, paired results, canonical proposal, receipts and verification; and RQ3 schemas,
authorization, A–L summary, execution/verification/provenance/audit records. The manifest records
their paths and hashes. A clean checkout can validate identities, aggregates, proposal continuity,
trust-record binding, and report structure without `/private/tmp`.

Live regeneration of probabilistic RQ1/RQ2 model outputs is a stronger requirement and still
depends on the frozen Ollama/Qwen environment. This does not invalidate the committed experimental
records, but it bounds independent rerun reproducibility.

## Semantic integrity audit

Comparison of RQ-FINAL-00 against predecessor
`3fed8fb77e759d004a7b91b23d933d41d8f70225` is restricted to this report, the integrated manifest,
and the focused evidence-integrity test.

```text
KG: NO
GraphRAG retrieval: NO
Evidence projection: NO
RQ1 answer-generation semantics: NO
RQ1 validator semantics: NO
RQ2 constraint semantics: NO
RQ2 proposal semantics: NO
RQ2 canonical proposal: NO
Mapping semantics: NO
Classification: NO
Geometry: NO
Portrayal: NO
ProductLayer: NO
Model: NO
Authorization semantics: NO
Verification semantics: NO
Provenance semantics: NO
ROAD: NO
School Hero: NO
BUILD: NO
Core: NO
Authoritative source data: NO
```

## Freeze readiness

| Criterion | Result | Basis |
|---|---|---|
| F1 — RQ evidence closure | PASS | Accepted committed evidence for RQ1, RQ2, RQ3 |
| F2 — Hypothesis closure | PASS | RQ1 proposition, H2, H2b, and H3 have bounded verdicts |
| F3 — Artifact lineage | PASS | Linear Git ancestry and content identities recorded |
| F4 — RQ2 → RQ3 immutable handoff | PASS | Exact proposal Git blob, ID, canonical hash, byte hash, and trust-record bindings |
| F5 — RQ1 → RQ2 relationship | PASS | Honestly classified SEMANTIC/ARCHITECTURAL HANDOFF |
| F6 — Claim boundaries | PASS | Universal trust/production/generalization claims excluded |
| F7 — Semantic integrity | PASS | No frozen semantic subsystem changed |
| F8 — Regression classification | PASS | No unclassified semantic regression; predecessor-relative failures bounded |
| F9 — Reproducibility | PASS WITH FINDINGS | Central evidence committed; live probabilistic reruns retain environment dependency |
| F10 — Findings bounded | PASS | Findings recorded and do not invalidate core hypotheses |

**Freeze verdict: READY FOR FREEZE WITH FINDINGS.** This task determines readiness only. It does
not create a release/freeze tag, merge a branch, deploy the demo, or authorize production use.

## Optional paper-facing synthesis

- **Methods:** three RQ architectures; RQ1 three-condition comparison and six-requirement evaluator;
  RQ2 paired planner intervention with persisted constraints/plans; RQ3 frozen trust chain and A–L
  cases; content-addressed fixtures, contracts, and acceptance rules.
- **Results:** RQ1 grounding/coverage/cost table; RQ2 pre-execution plan difference and deterministic
  execution/verification; RQ3 exact proposal binding, positive acceptance, and fail-closed cases.
- **Discussion:** executable geographic knowledge; semantic constraint propagation versus generic
  tool calling; deterministic operational boundaries around probabilistic proposals; distinction
  between semantic grounding, operational trust, auditability, and institutional authority; stated
  validity and reproduction limits.

## Research conclusion

Under the tested national-mapping scenarios and frozen implementations, the experiments support a
layered architecture in which explicit geographic knowledge improves evidence-grounded reasoning,
knowledge-derived constraints govern Agent planning and deterministic GIS execution, and exact
proposal-bound authorization, deterministic verification, provenance, and audit govern the
transition from a probabilistic Agent proposal to an auditable mapping action. The conclusion is
bounded to the tested task family, proposal, fixtures, model/runtime, validators, and research-safe
execution boundary; it is not a universal guarantee of AI trustworthiness or production NMA
suitability.

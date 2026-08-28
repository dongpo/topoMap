# RQ1-COMPARE-01 Completion Report

## A. Verdict

**PASS WITH LIMITATIONS — CONTROLLED EVALUATION COMPLETE**

All three architectures executed for the exact canonical RQ1 and ten frozen semantic-equivalent
variants: 33 primary runs. An additional three canonical repeats per architecture produced nine
raw reproducibility records. The same local Qwen model, temperature, context window, output
reserve, authoritative domain, deterministic evaluator, and no-truncation guard were used
throughout.

GraphRAG had higher measured requirement accuracy and coverage than both baselines on every one
of the eleven questions. Its primary mean requirement accuracy was 75.76%, compared with 45.45%
for Text-RAG and 15.15% for LLM-only. Absolute GraphRAG performance was wording-sensitive: it
ranged from 3/6 to 6/6, and only 3 of 11 primary answers were exact 6/6.

The verdict is limited because this is one small semantic task family and because the accepted
deterministic validator intentionally recognizes a bounded vocabulary. Some natural equivalents,
notably English `line code 2` and some Chinese point-geometry wording, were not promoted to claims.
The raw answers and claim records are preserved so that this limitation is visible rather than
silently repaired post hoc.

## B. Repository identity

| Item | Value |
|---|---|
| Required predecessor SHA | `6961b992d3fd49714fd14023afba60cba2f4e1d2` |
| Branch | `rq1/rq1-compare-01-controlled-baselines` |
| Isolated worktree | `/private/tmp/rq1-compare-01-controlled-baselines` |
| Starting HEAD | exact predecessor; ancestry and clean-worktree gate passed |
| Final local SHA | reported in the final console handoff because a commit cannot contain its own SHA |
| Remote SHA | reported in the final console handoff after push |
| Local/upstream/remote equality | verified and reported after final push |
| Original calling worktree | left untouched on `app/app-standalone-file-layout` |

The predecessor first reproduced its accepted RQ1 state: 28 predecessor RQ1 tests passed, and the
exact live RQ1 returned 6/6 with 46 retrieved nodes, 9 projected nodes, 2,841 observed answer-prompt
tokens, a 3,303-token observed input margin, and no truncation.

## C. Frozen variables

| Variable | Frozen value |
|---|---|
| Model | `qwen2.5:latest` |
| Ollama model identity | `845dbda0ea48` |
| Architecture / parameters | Qwen2 / 7.6B |
| Quantization | `Q4_K_M` |
| Temperature | `0` |
| Context window | `8,192` |
| Reserved output tokens | `2,048` |
| Canonical question identity | `request:sha256:8ec999772276b94f4bc4d4f39240e297aea9760f94649a5c6c240d9570ef7394` |
| Canonical graph identity | `nma-canonical-graph-v0.4`; file SHA-256 `4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4` |
| Validator identity | predecessor `6961b992`; `nma.rq1-answer-validation/1.0` unchanged |

Authoritative Text-RAG source identities:

- `data/extraction/portrayal-records.jsonl`: `ccd732aa3996481682dfe3038d1a8fbf6e115e78a3e6bb29c0c6c4316ce200cb`
- `data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json`:
  `9ba4f3c5e9dd2acec78ab56bf9fce270efac9b8343937459a6f4b3f16830a512`

## D. Three architectures

### LLM-only

The canonical/variant question, shared natural-prose instructions, and a one-field JSON transport
envelope containing only `answer` were sent directly to Qwen. The context explicitly stated that
retrieval evidence was not provided and supplied an empty evidence list. No graph, chunk, source,
expected value, or hidden retrieval fact entered the generation prompt.

### Text-RAG

The same baseline answer prompt received only ranked, provenance-bearing text chunks. The chunks
contain no graph relations, graph types, graph IDs, projected nodes, traversal output, or
GraphRAG-specific citations. The model still synthesized a natural answer; no answer slots were
introduced.

### GraphRAG

`AMAResearchRuntime.run_rq1` was used unchanged. Its existing two-call path performed bounded
entity interpretation, canonical graph retrieval, typed question-relevant projection, and the
accepted grounded-answer generation/validation. Primary runs retrieved the existing graph path
and projected only current question-relevant evidence; the canonical observation was 46 retrieved
nodes to 9 LLM-facing nodes.

## E. Text-RAG configuration

| Setting | Value |
|---|---|
| Source corpus | the two frozen source-derived artifacts listed in Section C |
| Corpus chunks | 17 deterministic chunks |
| Chunking | record boundary; split above 1,200 characters |
| Overlap | 120 characters for split records |
| Chunk identity | sequential corpus position plus 12 hex characters of text SHA-256 |
| Embedding model | `deterministic-feature-hashing-unicode-bow-1024/1.0` |
| Features | normalized ASCII terms plus Chinese runs/bigrams |
| Dimensions | 1,024 |
| Similarity | cosine |
| Candidate top-k | 12 |
| Ordering | descending cosine, then ascending stable chunk ID |
| Deduplication | canonical chunk-text SHA-256 |
| Corpus identity | `bd90c1bafc038a5a63486948c449005bd21541b384250551f313da010d0f8b87` |
| Graph-ID leakage audit | `false` |

The embedding is deliberately small, deterministic, credential-free, and reproducible in the
existing dependency-free repository. It is a conventional vector-space text baseline, not a
claim that feature hashing is a state-of-the-art multilingual embedding model.

The canonical measured GraphRAG LLM-facing evidence estimate was 2,074 tokens. Text-RAG was capped
at exactly that numeric ceiling with zero tolerance. Its observed maximum was 2,060 and mean was
2,002.09 tokens. GraphRAG was not modified or restricted; its observed mean was 2,042.64 and range
was 1,925–2,074.

## F. Evaluation corpus

The corpus contains the byte-preserved accepted canonical question plus ten additional variants.
Variants reorder classification, geometry, style, source, and binding emphasis; include compact,
conversational, alternate-English, and two Chinese wordings; and retain all six semantic
requirements.

| Artifact | Identity |
|---|---|
| Question fixture | `data/evaluation/rq1-compare-01-question-variants.json` |
| Fixture SHA-256 | `b3f66ead096c7dd186fef95b415f06fde766e6f5c3e838ab461e236e16c3909c` |
| Protocol | `data/evaluation/rq1-compare-01-evaluation-protocol.json` |
| Protocol SHA-256 | `bd3986e19a48ef1a17a4e304005c5f58395a127e778605bf016a6cd3e7d10157` |
| Primary design | 3 architectures × 11 questions = 33 runs |
| Reproducibility | 3 canonical repeats × 3 architectures = 9 additional runs |

The variants and their hash were frozen before the first comparison result was observed.

## G. Main results

| Metric | LLM-only | Text-RAG | GraphRAG |
|---|---:|---:|---:|
| Mean requirement accuracy | 15.15% | 45.45% | 75.76% |
| Median requirement accuracy | 16.67% | 50.00% | 66.67% |
| Requirement accuracy min–max | 0–33.33% | 33.33–66.67% | 50.00–100% |
| Exact 6/6 answer rate | 0/11 (0%) | 0/11 (0%) | 3/11 (27.27%) |
| Mean coverage | 40.91% | 68.18% | 86.36% |
| Median coverage | 33.33% | 66.67% | 83.33% |
| Coverage min–max | 16.67–66.67% | 33.33–83.33% | 66.67–100% |
| Exact 6/6 coverage rate | 0/11 (0%) | 0/11 (0%) | 4/11 (36.36%) |
| Classification accuracy | 0% | 45.45% | 90.91% |
| Geometry accuracy | 36.36% | 81.82% | 81.82% |
| Line-style accuracy | 0% | 0% | 81.82% |
| Color accuracy | 0% | 36.36% | 63.64% |
| Source requirement accuracy | 0% | 54.55% | 72.73% |
| ProductLayer-unresolved accuracy | 54.55% | 54.55% | 63.64% |
| Supported claims | retrieval N/A | 49 | 96 |
| Unsupported claims | 0 deterministic full-truth findings | 18 | 0 |
| Contradicted claims | 6 deterministic full-truth findings | 0 | 2 |
| Mean retrieval evidence tokens | 0 | 2,002.09 | 2,042.64 |
| Mean prompt tokens, all architecture calls | 255.00 | 2,326.18 | 3,961.64 |
| Mean completion tokens, all architecture calls | 90.45 | 164.36 | 521.18 |
| Mean total latency | 19.27 s | 43.51 s | 125.54 s |
| Silent truncation events | 0 | 0 | 0 |

LLM-only supported-claim count is intentionally N/A because no retrieval evidence existed. Its
unsupported/contradicted values are separate deterministic comparisons against the frozen truth,
not retrieval-grounding scores.

## H. Per-requirement results

GraphRAG improved classification by 90.91 percentage points over LLM-only and 45.46 points over
Text-RAG. GraphRAG and Text-RAG tied on geometry at 81.82%. GraphRAG scored higher on line style,
color, authoritative source, and unresolved binding. These exact values reflect the bounded
validator vocabulary: Text-RAG often generated the correct source term `line code 2`, which the
unchanged accepted validator does not treat as the `line style` claim pattern. That observable
limitation is not post hoc corrected.

## I. Per-question results

Each cell is `correct requirements / covered requirements`, each out of six.

| Question | LLM-only | Text-RAG | GraphRAG |
|---|---:|---:|---:|
| canonical | 2 / 4 | 3 / 4 | 6 / 6 |
| variant-01 classification-first | 1 / 2 | 3 / 4 | 4 / 5 |
| variant-02 geometry-first | 1 / 4 | 3 / 5 | 4 / 5 |
| variant-03 style-first | 1 / 2 | 4 / 4 | 5 / 5 |
| variant-04 source-first | 1 / 2 | 2 / 4 | 6 / 6 |
| variant-05 binding-first | 0 / 1 | 2 / 4 | 4 / 5 |
| variant-06 compact | 2 / 4 | 3 / 5 | 6 / 6 |
| variant-07 conversational | 1 / 2 | 2 / 5 | 4 / 6 |
| variant-08 Chinese reordered | 0 / 1 | 2 / 2 | 3 / 4 |
| variant-09 Chinese natural | 0 / 1 | 3 / 4 | 4 / 4 |
| variant-10 alternate English | 1 / 4 | 3 / 4 | 4 / 5 |

No failure is hidden by the aggregate: GraphRAG was higher than both baselines on each question,
but its own result varied materially from 3/6 to 6/6.

## J. Grounding results

### LLM-only

`retrieval_grounding = N/A`. LLM-only was not failed merely because it lacked retrieval. The
deterministic full-truth check still observed six contradicted claims across eleven answers. The
canonical answer called the hydrant red and attributed the rule to a city public works department;
both conflict with or lack the frozen authoritative evidence.

### Text-RAG

Across claims deterministically extractable from its answers, 49 were supported by selected text,
18 were unsupported, and none was contradicted by selected text. Every chunk ID uniquely mapped to
one selected text unit. Models emitted no chunk-ID citation strings, so there were no invalid chunk
references but citation integrity was not strongly exercised. Natural document/page references
were scored through the common source-requirement validator.

### GraphRAG

GraphRAG produced 96 supported, 0 unsupported, and 2 contradicted claims, with 11/11 evidence-ID and
citation-ID integrity checks passing. Both contradictions occurred in the conversational variant:
the bounded extractor interpreted `binding to a specific ProductLayer is required` as concrete
ProductLayer claims (`a` and `required`) against explicit unresolved status. This observable parser
interaction is retained in the raw record.

The applicable adverse-claim rate was 18/67 (26.87%) for Text-RAG and 2/98 (2.04%) for GraphRAG,
but GraphRAG did not dominate each subtype: it had two contradicted claims while Text-RAG had zero.

## K. Context and efficiency

| Architecture | Mean evidence tokens | Mean all-call prompt tokens | Mean completion tokens | Mean total latency | Mean observed margin | Minimum observed margin |
|---|---:|---:|---:|---:|---:|---:|
| LLM-only | 0 | 255.00 | 90.45 | 19.27 s | 5,889 | 5,873 |
| Text-RAG | 2,002.09 | 2,326.18 | 164.36 | 43.51 s | 3,817.82 | 3,462 |
| GraphRAG | 2,042.64 | 3,961.64 | 521.18 | 125.54 s | 3,323.91 | 3,271 |

GraphRAG cost approximately 1.70× Text-RAG prompt tokens and 2.89× Text-RAG latency. Relative to
LLM-only, it cost approximately 15.54× prompt tokens and 6.51× latency. GraphRAG's total includes
its accepted entity-interpretation call plus answer-generation call. Latency is local-hardware
dependent and small differences should not be generalized.

Every call carried explicit `num_ctx=8192`, `num_predict=2048`, and `temperature=0`. Preflight and
observed margins were recorded for every call. Silent truncation status was `NO` for all 42 stored
runs (33 primary plus 9 reproducibility).

## L. Failure analysis

| Taxonomy | LLM-only | Text-RAG | GraphRAG |
|---|---:|---:|---:|
| OMISSION | 39 | 21 | 9 |
| INCORRECT_VALUE | 8 | 3 | 1 |
| UNRESOLVED_BINDING_GUESSED | 2 | 3 | 1 |
| OTHER bounded mismatch | 7 | 9 | 5 |
| Total failed requirements | 56 | 36 | 16 |

Concrete observations:

- LLM-only commonly omitted source, line-style, and exact classification detail and sometimes
  supplied conventional-but-unsupported red hydrant styling or municipal source claims.
- Text-RAG recovered Point geometry and source metadata well, but often phrased line semantics as
  `line code` rather than the validator's `line style` pattern. Its flat text did not explicitly
  encode the absence-based Document 09 ProductLayer relation, and answers sometimes guessed that
  the binding was resolved or treated another pending review gate as the binding state.
- GraphRAG most consistently preserved classification, typed portrayal relations, and source
  provenance. Its remaining failures were natural-answer omissions, bounded-language recognition
  gaps, and one conversational ProductLayer phrasing that the extractor treated as a concrete
  binding.

No hidden model reasoning was inferred. Categories describe only observable answer/evaluator
behavior.

## M. Research interpretation

### Q1 — GraphRAG versus LLM-only factual correctness

Yes, within this controlled RQ1 experiment. Mean requirement accuracy was 75.76% versus 15.15%, a
60.61-point difference. GraphRAG was higher on every question and achieved 3 exact answers versus
zero. This does not establish a general GraphRAG-versus-LLM result outside RQ1.

### Q2 — GraphRAG versus Text-RAG factual correctness

Yes, within this experiment. Mean accuracy was 75.76% versus 45.45%, a 30.30-point difference.
GraphRAG was higher on every question and achieved 3 exact answers versus zero.

### Q3 — Question coverage

Yes. Mean coverage was 86.36% for GraphRAG, 68.18% for Text-RAG, and 40.91% for LLM-only.
GraphRAG achieved complete coverage on 4/11 questions; both baselines achieved 0/11.

### Q4 — Unsupported or contradicted claims

GraphRAG reduced the combined applicable adverse-claim count and rate relative to Text-RAG
(2/98 versus 18/67). It eliminated unsupported claims but had two contradicted claims in one
conversational answer, while Text-RAG had zero contradictions. The finding is therefore positive
for combined grounding, not universal for every subtype.

### Q5 — Structured semantic relationships

GraphRAG was higher on classification, line style, color, authoritative source, and unresolved
binding; it tied Text-RAG on geometry. The largest observable structural gains were classification
(90.91% versus 45.45%) and line style (81.82% versus 0% under the bounded validator). The line-style
difference is partly entangled with terminology recognition and must not be interpreted as pure
retrieval failure.

### Q6 — Token/context/latency cost

GraphRAG used a comparable LLM-facing evidence budget to Text-RAG but higher total prompt and
completion tokens because of its structured context and entity-resolution call. It was roughly
2.89× slower than Text-RAG and 6.51× slower than LLM-only on this local runtime. No architecture
approached the context limit or truncated.

### Q7 — Stability across wording

The ranking was stable: GraphRAG exceeded both baselines on all eleven wordings. Absolute results
were not stable: GraphRAG varied from 3/6 to 6/6, Text-RAG from 2/6 to 4/6, and LLM-only from 0/6 to
2/6. Chinese and binding-first variants were especially challenging. In three canonical repeats,
accuracy/coverage were stable for every architecture. LLM-only and Text-RAG answers were byte
identical; GraphRAG produced two distinct natural phrasings but remained 6/6 in all three repeats.

Bounded conclusion:

> Under the controlled NMA RQ1 evaluation, using the same Qwen model, context budget, task
> semantics, and authoritative source domain, GraphRAG achieved higher measured correctness,
> coverage, and combined grounding than LLM-only and Text-RAG, at materially greater token and
> latency cost. The result is specific to the frozen RQ1 task family and bounded evaluator.

## N. Limitations

- one semantic task family;
- eleven questions are a small controlled wording sample, not a broad benchmark;
- one LLM family, one quantization, and one local runtime;
- one authoritative corpus and one source-extraction representation;
- the deterministic feature-hash Text-RAG embedding is reproducible and fair but not a modern
  learned multilingual embedding benchmark;
- variant wording is not equivalent to independent task diversity;
- the frozen bounded validator under-recognizes some natural semantic equivalents;
- Text-RAG chunk-ID citation integrity was not strongly exercised because answers did not emit
  chunk IDs;
- GraphRAG's accepted answer schema carries stricter evidence-identity constraints than the
  baseline one-answer-field transport, an unavoidable architecture-specific difference;
- local latency depends on hardware, model residency, and runtime state;
- temperature zero did not guarantee byte-identical GraphRAG natural wording.

## O. Semantic-change audit

| Boundary | Changed |
|---|---|
| KG changed | NO |
| GraphRAG retrieval semantics changed | NO |
| GraphRAG evidence projection changed | NO |
| Authoritative source semantics changed | NO |
| Model changed | NO |
| Validator correctness semantics changed | NO |
| Deterministic answer frame introduced | NO |
| Fixed answer-slot schema introduced | NO |
| Production behavior changed | NO |

The only source module added is the isolated comparison harness. Existing
`research_runtime.py`, `research_context.py`, `research_answer_validation.py`, `llm/ollama.py`, and
the canonical graph are byte-unchanged from predecessor `6961b992`.

## P. Verification

| Verification | Result |
|---|---|
| Predecessor focused RQ1 reproduction | 28 passed |
| Exact live predecessor canonical RQ1 | 6/6; 46→9 nodes; no truncation |
| Comparison + RQ1 + relevant graph suites | 54 passed |
| Comparison-only focused suite | 14 passed |
| Ruff, modified Python scope | all checks passed |
| `git diff --check` | passed |
| Full suite | 1,293 passed, 208 skipped, 30 failed |

The 30 full-suite failures are inherited historical freeze/scope/hash assertions and the existing
`ama-foss4g-2026-freeze` tag assertion. They require their own historical branch/commit or exact
change scope and are not maintained cross-branch tests. The three final-release integrity failures
were rerun on the untouched exact predecessor worktree and failed identically. No unrelated failure
was repaired in this branch.

Machine-readable result artifact:

- `rq1-compare-01-results.json`
- SHA-256 `9b60b97c7097a960c8c237e4e08e68622a053d00312b98c41dedc6a8fd4355de`
- 33 reconciled primary records, 9 raw reproducibility records, aggregates, source identities,
  prompt/context metrics, answers, validation records, and failure taxonomy.

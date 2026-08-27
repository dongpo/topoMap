# RQ1-TRACE-01 Completion Report

## A. Verdict

**PASS — END-TO-END TRACE COMPLETE**

One diagnostic-only RQ1 run captured the existing evidence-to-answer path without changing the
canonical graph, retrieval policy, prompt semantics, model configuration, generation path,
validator rules, answer, or scientific claim boundary.

The run artifacts are:

- `artifacts/tmp/research-demo/20260827T153302261894Z-rq1/rq1-trace.json`
- `artifacts/tmp/research-demo/20260827T153302261894Z-rq1/rq1-trace.txt`
- `artifacts/tmp/research-demo/20260827T153302261894Z-rq1/result.json`
- `artifacts/tmp/research-demo/20260827T153302261894Z-rq1/summary.txt`

## B. Repository identity

| Item | Value |
|---|---|
| Source repository root | `/Users/dongpodeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/topoMap` |
| Calling checkout at task start | `app/app-standalone-file-layout` at `ac350c8fcef6e58d820ee6da456b1d1f0ef012f6` |
| RQ1 implementation baseline | `codex/ama-demo-03-rq-aligned-packaging` at `b2cb911e81c7455bb525de87921edd932c9def82` |
| Audit worktree root | `/private/tmp/rq1-trace-01.yxzKsr` |
| Working branch | `codex/rq1-trace-01` |
| Starting SHA | `b2cb911e81c7455bb525de87921edd932c9def82` |
| Finalization identity | This report is included in the single `codex/rq1-trace-01` branch-tip commit; the immutable commit SHA and remote-equality verification are recorded in the final handoff |
| Predecessor remote identity | Starting SHA equals `origin/codex/ama-demo-03-rq-aligned-packaging` and `origin/codex/ama-canonical-reconciliation` |
| Artifact retention | Generated trace artifacts remain under the existing ignored `artifacts/tmp/` convention and are not staged |

The starting checkout did not contain the tracked RQ1 source tree. A dedicated clean worktree was
therefore created from the current RQ1 packaging baseline rather than switching across or
overwriting the calling checkout's untracked assets.

## C. Runtime identity

| Item | Observed value |
|---|---|
| RQ | `RQ1` |
| Question | `For fire hydrant 9350906, explain the reviewed authoritative portrayal rule. Include its classification, geometry, line style, color, source evidence, and any unresolved schema or product-layer binding. Do not infer information that is not supported by the retrieved evidence.` |
| Request identity | `request:sha256:8ec999772276b94f4bc4d4f39240e297aea9760f94649a5c6c240d9570ef7394` |
| Model provider | `ollama` |
| Model ID | `qwen2.5:latest` |
| Graph backend | `canonical-json` |
| Canonical graph identity | `nma-canonical-graph-v0.4` |
| Scenario | `Fire hydrant 9350906 KG-grounded portrayal answer` |
| Model calls | 2 total: existing entity-resolution generation plus existing grounded-answer generation |
| Additional trace generation | None |
| Provider context observation | Ollama truncated the answer prompt from 14,738 tokens to 2,050, retaining a four-token prefix; the exact retained evidence subset is not exposed |

The captured final Ollama API request retained the existing system message, ordered `messages[]`,
JSON format, and `options.temperature=0`. No model or generation option was changed by trace mode.
The same-run Ollama server stderr subsequently reported `truncating input prompt limit=2050
prompt=14738 keep=4 new=2050`; the raw response independently records
`prompt_eval_count=2050`. The trace therefore distinguishes the exact request accepted by the API
from the internal Qwen context, whose exact retained evidence subset is **UNKNOWN**.

## D. Trace findings

| Stage | Observed status | Evidence |
|---|---|---|
| Entity resolution | PASS | Five full selected seeds were captured before traversal: classification occurrence, Document 01 classification, portrayal recipe, portrayal rule, and terrain classification. |
| Graph retrieval | PASS | 46 nodes and 54 typed edges were retrieved. |
| Required KG knowledge availability | PASS | All six required audit nodes exist in the active canonical graph. |
| KG contains classification | PASS | `classification:doc01:9350906`: code `9350906`, label `消防栓`. |
| KG contains geometry | PASS | `portrayal-geometry:Point`: `name=Point`. |
| KG contains line-style information | PASS | `line-style:doc01:2`: `code=2`; the stored observation says the semantic stroke-width lookup is not defined by the reviewed rows. |
| KG contains color information | PASS | `portrayal-color:doc01:7`: `code=7`, `observed_color=black`; exact device-independent colour values are not stated. |
| KG contains unresolved binding status | PASS | `mapping_status` states that Document 09 has no confirmed ProductLayer/field binding and the mapping must remain unresolved. |
| Serialized evidence preserves classification | PASS | The exact `authoritative_evidence_package` contains `classification:doc01:9350906` and all stored properties. |
| Serialized evidence preserves geometry | PASS | The exact package contains `portrayal-geometry:Point`. |
| Serialized evidence preserves line style | PASS | The exact package contains `line-style:doc01:2` and both stored properties. |
| Serialized evidence preserves color | PASS | The exact package contains `portrayal-color:doc01:7` and all stored properties. |
| Serialized evidence preserves unresolved binding | PASS | The exact package contains the unresolved `mapping_status` on the classification and portrayal rule. |
| Evidence serialization | PASS | The captured runtime value supplied to `context.authoritative_evidence_package` preserved all required items. |
| Ollama receives required RQ1 instructions | PASS | The exact final user message contains the byte-preserved question and existing answer instructions. |
| Ollama receives required evidence | PASS | The wire message contains classification, Point geometry, line style 2, color 7/black, citations/source metadata, and unresolved binding status. |
| Prompt/message propagation | FAIL | Provider-neutral input and the API wire body agree, but Ollama truncated 14,738 prompt tokens to 2,050 before inference. |
| Qwen internal context retains required evidence | UNKNOWN | Ollama did not expose which evidence tokens survived truncation. |
| Raw Qwen answer covers requested elements | FAIL | Line style, color, and unresolved ProductLayer/schema binding are not present in the raw answer. |
| Raw Qwen answer contains unsupported claims | OBSERVED | `打印页10` first appears in the raw model response. Document 01 evidence says `page=11`, `printed_page=null`. |
| LLM generation | FAIL | The raw output omits three requested elements and introduces the unsupported printed-page value; attribution to synthesis versus provider truncation remains UNKNOWN. |
| Post-processing | PASS | Raw structured output equals the answer object passed to validation; no answer text was lost or changed. |
| Validator receives sufficient evidence | PASS | Input includes the answer, full evidence package, the question at `evidence.query`, and Document 01 `page=11`, `printed_page=null`. |
| Validator evidence availability | PASS | The complete retrieved evidence and source metadata are supplied to `validate_grounded_answer`. |
| Validator performs claim-level grounding | NOT IMPLEMENTED | **CLAIM-LEVEL GROUNDING CHECK: NOT IMPLEMENTED.** |
| Validator performs question coverage | NOT IMPLEMENTED | **QUESTION-COVERAGE CHECK: NOT IMPLEMENTED.** |

## E. Missing-element trace

| Element | KG | Retrieved | Serialized | Present in captured Ollama request | Raw answer | Post-processing | Validator checks coverage | First absent stage |
|---|---|---|---|---|---|---|---|---|
| Line style | PASS | PASS | PASS | PASS | NOT OBSERVED | NOT OBSERVED | NOT IMPLEMENTED | Raw Qwen answer |
| Color | PASS | PASS | PASS | PASS | NOT OBSERVED | NOT OBSERVED | NOT IMPLEMENTED | Raw Qwen answer |
| Unresolved ProductLayer/schema binding | PASS | PASS | PASS | PASS | NOT OBSERVED | NOT OBSERVED | NOT IMPLEMENTED | Raw Qwen answer |

Because Ollama truncated the prompt before inference, `PASS` in the request column does not assert
that Qwen retained or saw the corresponding evidence tokens; the retained subset is unknown.

The line-style evidence is concrete only to the stored boundary: line code `2` is observed, while
the semantic metric/stroke-width lookup remains undefined. The color evidence similarly stores
code `7` and observed black while explicitly withholding an exact device-independent colour.

## F. Unsupported-claim trace

| Checkpoint | `printed_page=10` / `打印页10` observed? |
|---|---|
| Active canonical KG snapshots | NO |
| Retrieved graph/evidence | NO |
| Serialized evidence | NO |
| Exact final Ollama request | NO |
| Raw Qwen response | YES — first appearance |
| Post-processed answer | YES — unchanged from raw response |

For `citation:section:doc01-portrayal:p11`, the captured evidence and validator input contain
`page=11` and `printed_page=null`. Other retrieved Document 02 citations contain printed pages 43,
44, and 48; none supplies printed page 10.

## G. Validator interpretation

The labels mean the following in the executed code path:

- **Evidence IDs valid** checks that answer-declared evidence node IDs are unique and a subset of
  retrieved node IDs. It does not inspect the natural-language answer.
- **Citation IDs valid** checks that answer-declared citation IDs are unique and a subset of
  retrieved citation IDs. It does not verify that each free-text claim is supported by a cited
  source.
- **Unsupported evidence invented** is computed only as
  `NOT (evidence_ids_valid AND citation_ids_valid)`. A displayed `NO` therefore means no unknown or
  duplicate evidence/citation identity was declared; it does not mean that free-text claims were
  grounded.
- **Grounded answer validation** is the conjunction of the runtime's existing structured checks,
  evidence-ID validity, and citation-ID validity. The runtime checks source-document membership,
  requires `exact_claims`, and compares those exact claim properties to retrieved node values. It
  does not parse the answer text, ground every natural-language claim, or compare requested slots
  against answer coverage.

Consequently, the observed PASS/NO labels are consistent with the implemented identity and exact
claim contract, but they are not evidence that `打印页10` was checked or that line style, color, and
unresolved binding were answered.

## H. Root-cause classification

### Supported

- **G — Validator capability defect.** The trace distinguishes:
  - **G1:** evidence/citation identity validation is narrower than natural-language grounding;
  - **G2:** unsupported natural-language claim detection is absent;
  - **G3:** requested-question coverage validation is absent;
  - **G4:** the aggregate PASS label can be read more broadly than the checks it actually
    represents.

### Observed pipeline gap outside the strict A–G predicates

- **Provider-side input truncation.** The exact final API request contains all required facts, but
  Ollama truncated 14,738 prompt tokens to 2,050 before inference and retained only a four-token
  prefix plus an unexposed suffix. The missing facts' presence in Qwen's internal context is
  therefore **UNKNOWN**. This blocks a conclusive E classification for the omissions.

### Not supported or not yet conclusive

- **A — KG knowledge defect:** not supported; required knowledge exists.
- **B — Retrieval defect:** not supported; required nodes/properties and edges were retrieved.
- **C — Evidence serialization defect:** not supported; required evidence survives unchanged.
- **D — Prompt/message propagation defect, strict definition:** the final API request contains the
  question and required evidence, so the task's stated D predicate is not met. A provider-side
  propagation failure nevertheless occurs after request capture because of input truncation.
- **E — LLM synthesis/instruction-following defect:** not conclusive because the exact evidence
  subset retained in Qwen's internal context is unknown.
- **F — Post-processing defect:** not supported; answer text is unchanged before validation.

## I. Recommendation

Recommend two independent follow-on work packages, neither implemented here:

1. **RQ1-PROMPT-01** — isolate and resolve or explicitly bound provider-side context truncation,
   then repeat the same trace before attributing omissions to model synthesis.
2. **RQ1-VALIDATOR-01** — separately define and review any desired natural-language claim grounding,
   question-coverage checks, and reporting-label semantics.

No KG, retrieval, evidence-serialization, or post-processing work package is supported by this
trace. `RQ1-LLM-01` should be considered only after a follow-up confirms that the relevant evidence
was retained in the model's actual inference context.

## Verification

- Pre-instrumentation RQ1 baseline: `6 passed`.
- Post-instrumentation focused RQ1 plus original RQ1 suites: `10 passed`.
- Broader AMA-DEMO-02/03 research-demo regression: `23 passed, 1 skipped`.
- Ruff checks: passed.
- Live required RQ1 trace: exit code `0`; exactly two existing model calls; no retry and no trace-only
  generation.
- Changed tracked scope: RQ1 trace module, RQ1 runtime/CLI/reporting observers, Ollama wire observer,
  focused tests, and this completion report. No `data/`, graph, prompt content, model settings,
  validator acceptance logic, or production semantics file was modified.

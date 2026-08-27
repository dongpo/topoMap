# RQ1-PROMPT-01 Completion Report

## A. Verdict

**PASS — CONTEXT BUDGET AND PROMPT PROPAGATION CLOSED**

The existing canonical graph retrieval produced the same 46-node, 54-edge neighborhood as
RQ1-TRACE-01. A new question-relevant, typed-relationship projection supplied nine directly
relevant nodes and eight provenance-bearing edges to `qwen2.5:latest`. The final answer prompt used
2,841 observed tokens inside an explicitly configured 8,192-token context window with a 2,048-token
output reserve. No provider truncation occurred.

The acceptance run's raw answer included classification `9350906 / 消防栓`, Point geometry, line
style `2`, color `7 / black`, authoritative Document 01 page 11 evidence, and the unresolved
ProductLayer/field binding. The prior unsupported printed-page-10 statement was not observed.
This is one probabilistic observation, not a universal correctness claim.

Canonicalized baseline and final full evidence packages have the identical SHA-256
`38e0b9de817f645c4bec37c0d4a3e58baecccb040f5718dc069a72c7385a0bed`.

## B. Repository identity

| Item | Value |
|---|---|
| Required predecessor | `cf41fdacaa719efa440307df1afca067768e2d8a` |
| Calling checkout | `app/app-standalone-file-layout` at `ac350c8fcef6e58d820ee6da456b1d1f0ef012f6`, with unrelated untracked user files left untouched |
| Isolated worktree | `/private/tmp/rq1-prompt-01.Pe7NVa` |
| Branch | `rq1/rq1-prompt-01-context-closure` |
| Starting SHA | `cf41fdacaa719efa440307df1afca067768e2d8a` |
| Starting worktree | clean |
| Finalization identity | This report is included in the single branch-tip commit; the immutable final SHA, remote SHA, equality check, and clean final status are recorded in the final handoff |
| Canonical graph file SHA-256 | `4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4` before and after |

The calling checkout was not cleaned, switched, or otherwise modified. The dedicated branch was
created directly from the exact predecessor in a separate clean worktree.

## C. Root-cause finding

The prior 2,050-token effective prompt was introduced by Ollama's runtime default when the
application omitted `options.num_ctx`:

- `qwen2.5:latest` model metadata advertises a 32,768-token context length;
- its generated Modelfile contains no `PARAMETER num_ctx` override;
- the predecessor application sent only `options.temperature=0`;
- no wrapper, environment, or application context-window setting was present;
- the exact predecessor rerun again constructed 14,738 prompt tokens and Ollama evaluated only
  2,050;
- a controlled one-output-token request with the same captured prompt and omitted `num_ctx` again
  returned `prompt_eval_count=2050`;
- explicitly supplying `num_ctx=32768` changed `ollama ps` to `CONTEXT 32768` (the deliberately
  large diagnostic request exceeded its client timeout and was not used as acceptance evidence).

Therefore, the defect was not Qwen's 32K model metadata and not explicit application truncation.
It was the Ollama runner's approximately 2K implicit context allocation reached because the
application did not set `num_ctx`. The predecessor trace's server observation expressed the
effective limit as 2,050 tokens after Qwen chat-template handling.

The final adapter sends `num_ctx=8192`, `num_predict=2048`, and `temperature=0` on both existing
calls. The local timeout is 600 seconds so a cold or CPU-heavy local model remains fail-closed
without misreporting a slow response as immediate model unavailability.

## D. Prompt-budget analysis

Ollama exposes exact prompt usage only after generation, not a tokenize-only endpoint. The tables
below allocate the exact observed totals proportionally to UTF-8 serialized component size and are
therefore approximate component counts. Totals are the actual `prompt_eval_count` values.

### RQ1-TRACE-01 baseline

| Prompt component | Approx. tokens | % |
|---|---:|---:|
| System, JSON, role, and chat-template overhead | 827 | 5.6 |
| Task and answer instructions | 121 | 0.8 |
| User question (duplicated in outer context and package query) | 187 | 1.3 |
| Resolved entities duplicated from evidence nodes | 1,126 | 7.6 |
| Full graph nodes | 5,555 | 37.7 |
| Graph-path node ID list duplicated from nodes | 579 | 3.9 |
| Full graph edges | 2,144 | 14.5 |
| Four citation records | 1,088 | 7.4 |
| Source sections and source documents | 639 | 4.3 |
| Retrieval trace | 1,069 | 7.3 |
| Other package metadata | 147 | 1.0 |
| Repeated allowed/required identities and exact claims | 912 | 6.2 |
| Output schema | 344 | 2.3 |
| **Total observed** | **14,738** | **100.0** |

The main causes were full 46-node serialization, 54 graph edges, graph-path identity duplication,
duplicated resolved entities, four broad citations/source sections, the retrieval audit trace, and
identity lists repeated in both context and output constraints.

### RQ1-PROMPT-01 final

| Prompt component | Approx. tokens | % |
|---|---:|---:|
| System, JSON, role, and chat-template overhead | 259 | 9.1 |
| Task and answer instructions | 157 | 5.5 |
| User question (outer context and projected-context query) | 186 | 6.6 |
| Nine projected graph nodes | 870 | 30.6 |
| Eight projected graph edges | 280 | 9.9 |
| One citation and authoritative source document | 270 | 9.5 |
| Projection and epistemic metadata | 222 | 7.8 |
| Allowed/required identities and exact claims | 313 | 11.0 |
| Output schema | 285 | 10.0 |
| **Total observed** | **2,841** | **100.0** |

Preflight uses `ceil((UTF-8 bytes / 3 + 256 template tokens) * 1.20)`, calibrated against both the
14,738-token baseline and 2,841-token final Qwen observations. The final conservative estimate was
3,704 tokens, below the 6,144-token input budget by 2,440 tokens. Actual observed input margin was
3,303 tokens. The full predecessor prompt estimates at approximately 17.8K and fails before an 8K
Ollama invocation.

## E. Evidence projection

The projection is implemented as a general RQ1 evidence-context layer, not a retrieval change and
not an answer template. It derives intent from the question, chooses model-selected canonical
entities, follows typed relationships relevant to those intents, and adds source containment needed
for provenance.

For the baseline it retained:

- `portrayal-rule:doc01:9350906` as the selected rule anchor;
- `classification:doc01:9350906` through `PORTRAYED_BY`;
- `portrayal-geometry:Point` through `APPLIES_TO_GEOMETRY`;
- `line-style:doc01:2` through `USES_LINE_STYLE`;
- `portrayal-color:doc01:7` through `USES_COLOR`;
- the reviewed recipe through `TRANSCRIBES_RULE`;
- the authoritative portrayal profile through `DEFINES`;
- Document 01 section p11 through `EVIDENCED_ON`;
- the containing Document 01 identity through `CONTAINS`;
- the matching citation, revision, page, record ID, review status, hashes, and source document;
- retrieved epistemic metadata and every relevant node property, including non-executable,
  review-candidate, unknown, and unresolved states.

It omitted 37 nodes from only the LLM-facing context. Those nodes remain in the retrieved graph and
validator input. Omitted material consisted of unrelated production workflow/stage branches,
classification-scheme hierarchy, neighboring code `9350900`, vector glyph construction and
activation-gate branches not requested by the question, Document 02 coding-scheme excerpts,
duplicated path node IDs, duplicated resolved-entity properties, and the retrieval audit trace.

The mechanism contains no `9350906`, `消防栓`, fire-hydrant, line-code-2, or color-7 special case.
A synthetic non-9350906 regression proves selection of a different classification, geometry, line,
color, source, document, and unresolved binding while excluding an unrelated node.

## F. Required-evidence propagation

| Required item | Retrieved | Projected/serialized | Final request | Within effective context |
|---|---|---|---|---|
| Classification `9350906 / 消防栓` | PASS | PASS | PASS | PASS |
| Geometry `Point` | PASS | PASS | PASS | PASS |
| Line style `2` | PASS | PASS | PASS | PASS |
| Color `7 / black` | PASS | PASS | PASS | PASS |
| Authoritative Document 01 source evidence | PASS | PASS | PASS | PASS |
| Unresolved ProductLayer/field binding | PASS | PASS | PASS | PASS |
| `printed_page=unknown` for Document 01 | PASS | PASS (`null`) | PASS (`null`) | PASS |

“Final request” means present in the captured API request. “Within effective context” additionally
means the explicit 8,192 context, preflight estimate, 2,048 output reserve, and observed 2,841 input
usage jointly prove that the request fit without provider truncation.

## G. Exact RQ1 rerun

| Item | Observed value |
|---|---|
| Question | Exact required question, byte-preserved |
| Provider/model | `ollama` / `qwen2.5:latest` |
| Graph backend/identity | `canonical-json` / `nma-canonical-graph-v0.4` |
| Scenario | Fire hydrant 9350906 KG-grounded portrayal answer |
| Model calls | 2 total: existing entity selection plus existing grounded answer; no retry or hidden call |
| Retrieved graph | 46 nodes / 54 edges / 4 citations |
| LLM projection | 9 nodes / 8 edges / 1 directly relevant citation |
| Context window | 8,192 |
| Output reserve | 2,048 |
| Available input | 6,144 |
| Prompt estimate | 3,704 |
| Observed prompt tokens | 2,841 |
| Observed input margin | 3,303 |
| Budget status | PASS |
| Silent truncation | NO |
| Raw output tokens | 380 |
| Answer-call latency | 53,859 ms |

Raw Qwen answer:

> 消防栓（分类代码9350906）的表示规则在第11页（记录ID：DOC01-P11-HYDRANT）被详细规定。该规则指示使用点几何图形（几何角色：Point）进行表示。表示规则采用线型代码2（图式线号2）和颜色代码7（实测，颜色为黑色）。此规则的激活状态为非执行状态（non-executable），且未确认与产品图层的绑定关系。因此，该规则的状态为未执行且未绑定到具体的产品图层字段。

The raw structured output and postprocessed answer object are identical. No printed-page-10 value
appears. The persisted ignored artifacts are under
`/private/tmp/rq1-prompt-01-final-4/20260827T165528237685Z-rq1/`; refreshed trace SHA-256 is
`e9d04beec903fa703c936a9a29ec636f41491b9576c93eb4e8cf2db718a63957`.

## H. LLM interpretation

**LLM omission attribution: no longer observed in this run.**

Context delivery is closed. Qwen included the previously omitted line style, color, and unresolved
binding after receiving all required evidence inside the verified effective context. This does not
establish universal instruction-following or statistical superiority over LLM-only, RAG, or any
other system.

## I. Validator boundary

- claim-level grounding validation: unchanged / **NOT IMPLEMENTED**;
- question-coverage validation: unchanged / **NOT IMPLEMENTED**;
- NLI, entailment, completeness scoring, and semantic validator remediation: not implemented.

The existing structured validator again reported PASS. That label still covers schema, declared
identity membership, source membership, and exact-property checks—not full natural-language claim
grounding or requested-element coverage. Diagnostic marker additions are trace-only observations
and do not alter validator acceptance.

## J. Runtime comparison

| Metric | RQ1-TRACE-01 baseline | RQ1-PROMPT-01 |
|---|---:|---:|
| Retrieved evidence nodes | 46 | 46 |
| Retrieved graph edges | 54 | 54 |
| LLM-facing evidence nodes | 46 plus duplicated structures | 9 |
| Prompt tokens | 14,738 | 2,841 |
| Configured context window | implicit approximately 2K | 8,192 explicit |
| Effective input budget | approximately 2,050 observed | 6,144 |
| Required evidence in constructed request | YES | YES |
| Required evidence fits effective context | UNKNOWN / NO | YES |
| Silent truncation risk | YES | NO |
| Line style in raw answer | NO | YES |
| Color in raw answer | NO | YES |
| Unresolved binding in raw answer | NO | YES |
| Unsupported claim observed | `打印页10` | not observed |

## K. Verification and scope

- Focused plus research-demo regression: **36 passed, 1 skipped**.
- Ruff on all changed Python files: passed.
- Exact live RQ1: passed; exactly two model calls.
- Canonical graph byte SHA-256: unchanged.
- No retrieval module, canonical data, ontology, graph identity, validator rule, model ID, graph
  backend, or research question changed.
- Full mixed-history suite on the clean predecessor: 27 historical freeze/hash/scope failures.
- Full mixed-history suite on this branch: those same 27 failures plus three old work-package
  change-scope guards that reject any current RQ1 file change. These are inapplicable historical
  branch assertions; no related source was modified. No unrelated failure was fixed.

Changed scope is limited to the Ollama context policy/observability, provider-neutral result
metadata, RQ1 evidence projection and reporting/trace integration, focused tests, one updated RQ1
mechanism assertion, and this report.

## L. Next recommendation

`RQ1-VALIDATOR-01 — READY`

`RQ1-LLM-01 — NOT READY` because the corrected-context acceptance run did not observe the prior
omission. A separate LLM work package should be opened only on evidence from a complete effective
context, not from the truncated TRACE-01 run.

No validator remediation was performed.

# RQ1-VALIDATOR-01 Completion Report

## A. Verdict

**PASS — CLAIM GROUNDING AND QUESTION COVERAGE VALIDATION CLOSED**

RQ1 now validates the displayed postprocessed answer along four separately inspectable axes:
evidence-ID integrity, citation-ID integrity, claim-level natural-language grounding, and semantic
question coverage. The aggregate passes only when all four pass. Validation remains deterministic,
post hoc, observational, and non-remediating.

## B. Repository identity

| Item | Value |
|---|---|
| Required RQ1-PROMPT-01 predecessor | `596dc67cd026116637e5d4c1fe4ec92aedaadbc8` |
| Predecessor verification | PASS |
| Calling checkout | `app/app-standalone-file-layout` at `ac350c8fcef6e58d820ee6da456b1d1f0ef012f6`; unrelated untracked user files were not changed |
| Isolated worktree | `/private/tmp/rq1-validator-01-grounding-coverage` |
| Branch | `rq1/rq1-validator-01-grounding-coverage` |
| Starting SHA | `596dc67cd026116637e5d4c1fe4ec92aedaadbc8` |
| Starting worktree | clean |
| Finalization identity | This report is part of the single branch-tip commit; final SHA, remote SHA, equality, and clean status are recorded in the final handoff |
| Canonical graph SHA-256 before and after | `4c37cc241a30c72a054da7b83cab1e2e367926e1a48f5060e6e7f0bb8f820cb4` |

The calling checkout materially differed from the required predecessor and contained user-owned
untracked files. A dedicated clean worktree was therefore created directly from the exact
predecessor instead of switching or cleaning the calling checkout.

## C. Validator architecture

### Claim extraction

`src/nma/research_answer_validation.py` performs bounded deterministic extraction of atomic RQ1
propositions from the exact displayed answer. The categories are feature code/name, geometry, line
style, color code/name, PDF/source page, printed page, document/revision, activation status, and
ProductLayer binding state. Common English, Traditional Chinese, and Simplified Chinese forms are
controlled aliases, not unrestricted fuzzy matching. Connective text is not promoted to a factual
claim.

The extractor contains no hydrant code, label, or expected answer. Coverage requirements are
semantic identifiers and do not contain expected values.

### Claim normalization

Extracted values are normalized only within bounded categories, for example `Point`, point
geometry, and point-geometry Chinese forms to `Point`, and `black`/`黑色` to `black`. Original
claim text remains attached to every decision.

### Evidence normalization

The validator builds a validation-only view from the already retrieved evidence package. It
preserves entity IDs/types/properties and citation document, revision, page, and printed-page
metadata. This view is never supplied to answer generation. PDF page and printed page remain
distinct; `printed_page=null` is represented as unknown rather than coerced to a page number.

### Grounding decision

Every extracted factual claim receives `SUPPORTED`, `UNSUPPORTED`, or `CONTRADICTED`; the contract
also carries an explicit `UNVERIFIABLE` count for claims that future bounded extractors cannot
decide. Grounding passes only when unsupported and contradicted counts are both zero.

### Coverage decision

The reusable RQ1 requirement contract contains:

- classification;
- geometry;
- line style;
- color;
- source evidence;
- unresolved ProductLayer binding.

Each requirement receives `PASS`, `PARTIAL`, or `FAIL`. Coverage checks whether the category was
substantively addressed; it does not decide whether the stated value was true.

### Aggregate decision

`Overall answer validation: PASS` requires reference integrity, claim grounding, and question
coverage all to pass. A failed semantic result is returned as a failed result; the answer is not
rewritten, supplemented, retried, or regenerated. Validation model-call count is explicitly zero.

## D. Legacy-validator interpretation

The predecessor's `Unsupported evidence invented` label meant only that declared evidence and
citation identifiers were unique and present. Its `Grounded answer validation` aggregate combined
schema, identifier, source-membership, and exact-property checks. Neither label established
natural-language grounding or question coverage.

The ambiguous labels are no longer primary RQ1 report fields. Reports now show:

1. reference integrity, with evidence and citation IDs separately;
2. claim grounding, with claim records and status counts;
3. question coverage, requirement by requirement;
4. overall answer validation.

The original exact-claim and identifier validators remain intact as compatibility checks.

## E. Historical regression

Fixture evidence:

```text
PDF page = 11
printed_page = unknown
```

Historical answer claim:

```text
打印页10
```

Observed decision:

```text
category = printed_page
value = 10
status = UNSUPPORTED
claim grounding = FAIL
```

The PDF page value is not reused as a printed-page value, and unknown printed-page metadata remains
unknown.

## F. Independence tests

| Deterministic fixture | Grounding | Coverage | Expected/observed |
|---|---|---|---|
| Correct classification and geometry only | PASS | FAIL | PASS |
| All six categories, but black changed to red | FAIL | PASS | PASS |
| All six categories with supported values | PASS | PASS | PASS |

Additional fixtures detect `LineString` against `Point`, red against black, a concrete invented
ProductLayer against explicit unresolved status, missing line style, missing color, missing source
evidence, missing binding, multiple omissions, invalid evidence IDs, and invalid citation IDs.

## G. Exact RQ1 rerun

Final-code run directory:

```text
/private/tmp/rq1-validator-01-definitive-live/20260827T174951002571Z-rq1/
```

| Item | Observed value |
|---|---|
| Question | exact required question |
| Provider/model | `ollama` / `qwen2.5:latest` |
| Graph backend/identity | `canonical-json` / `nma-canonical-graph-v0.4` |
| Model calls | 2 generation calls; 0 validation calls; no retry |
| Retrieved/projected evidence | 46 nodes → 9 LLM-facing nodes |
| Context window/output reserve | 8,192 / 2,048 |
| Prompt estimate/observed | 3,704 / 2,841 tokens |
| Silent truncation | NO |
| Raw equals postprocessed answer | YES |
| Reference integrity | PASS |
| Claim grounding | PASS: 11 supported, 0 unsupported, 0 contradicted, 0 unverifiable |
| Question coverage | PASS: all six requirements |
| Overall answer validation | PASS |

Raw Qwen answer:

> 消防栓（分类代码9350906）的表示规则在第11页（记录ID：DOC01-P11-HYDRANT）被详细规定。该规则指示使用点几何图形（几何角色：Point）进行表示。表示规则采用线型代码2（图式线号2）和颜色代码7（实测，颜色为黑色）。此规则的激活状态为非执行状态（non-executable），且未确认与产品图层的绑定关系。因此，该规则的状态为未执行且未绑定到具体的产品图层字段。

The validator grounded the displayed answer itself. It did not validate a repaired or hidden answer.

Final live artifact SHA-256 values:

| Artifact | SHA-256 |
|---|---|
| `result.json` | `8867fcf5414d37fb3937572e09a2fb07bab18d06a1f80ab5ebe0c5cec8f56f06` |
| `rq1-trace.json` | `90150fd0ad08bd06dd22652afd331dac3ef39c1162d785ecf4ce94e9e1f5a27b` |
| `summary.txt` | `5608570fb89ba440da5037444bcb94557bbbb74237b2317778bd96e3d0e07840` |

## H. Semantic integrity

| Boundary | Changed |
|---|---|
| Canonical KG | NO |
| Graph identity | NO |
| Graph traversal/retrieval semantics | NO |
| Evidence projection | NO |
| Prompt text/semantics | NO |
| Context configuration/budgeting | NO |
| Model/model options | NO |
| Answer generation | NO |
| Deterministic answer frame | NO |
| Automatic repair/retry | NO |

The diff contains only validator implementation/integration, validation trace/reporting, focused
fixtures, predecessor expectation updates, and this report. `src/nma/research_context.py`,
`src/nma/llm/ollama.py`, and the canonical graph are byte-unchanged.

## I. Verification

Focused deterministic and runtime suites:

```text
40 passed, 1 skipped
```

Final validator/RQ1 focused rerun after contract metadata:

```text
28 passed
```

Maintained Ruff check:

```text
All checks passed!
```

Full non-historical regression collection contains 1,480 tests. The run completed with one failure:

```text
tests/test_ama_repository_reconciliation.py::
test_version_and_compatibility_namespaces_are_explicit
```

This is inherited and unrelated: the assertion requires no `ama-*` tag, while the repository has
the global tag `ama-foss4g-2026-freeze`. The identical test was rerun on the pristine predecessor
worktree at `596dc67` and failed identically. No tag was created, removed, or changed by this work.

`git diff --check` passes.

## J. Research status

RQ1 now has an auditable end-to-end chain from canonical evidence retrieval through bounded prompt
delivery and free-form Qwen generation to separately reported reference integrity, claim grounding,
question coverage, and aggregate validation. This supports the bounded claim that the runtime can
audit retrieved-evidence grounding and RQ1 semantic coverage. It does not establish perfect
hallucination prevention, universal semantic correctness, statistical superiority, cross-task
generalization, or human-equivalent judgment.

**RQ1 end-to-end validation chain: CLOSED.**

Next evidence-supported work: if broader research questions are added, define their semantic
requirement contracts and category-specific bounded normalizers rather than weakening this RQ1
validator into unrestricted fuzzy matching.

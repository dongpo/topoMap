# NMA-Bench v0.1: what it proves

## The simple answer

The user is right that the benchmark should look like questions asked of a human. NMA-Bench now
contains those questions and scores whether the answer is correct.

However, a fluent answer can still be a lucky guess. A National Mapping Authority also needs to
know whether the agent selected the correct rule, used it on the map, and can prove where it came
from. Therefore each human question is the first layer of a three-layer benchmark:

| Layer | Human analogy | Why it matters |
|---|---|---|
| Question answering | Ask a cartographer for the code/page/rule | tests knowledge correctness |
| Symbol decision | Give a feature, scale, profile, and exception | tests executable reasoning and safe abstention |
| Map compilation | Ask the system to draw it in a vector map | tests that the answer becomes a correct software action |

For example:

```text
Question: According to NLSC112V5.4, what is the code for an elementary school?
Expected answer: 9920103
Expected evidence: PDF page 61

Execution input: code=9920103, scale=1:1,000
Expected decision: school symbol, draw_symbol
Expected path: FeatureType → PortrayalRule → Symbol → SourceObservation → page 61

Map check: a MapLibre layer filters TERRAINID=9920103 on J01_MARK
Expected metadata: same rule ID and page 61
```

This is more convincing than question accuracy alone because the same fact must survive from the
answer, through the agent decision, into the vector-tile style.

## Task set

| Family | Tasks | Coverage |
|---|---:|---|
| Human questions | 8 | hydrant, fish pond, police, schools, post office, unknown feature |
| Symbol decisions | 8 | five positive cases, post-office exception, wrong scale, wrong profile |
| Map compilation | 5 | BUILD, WATERA, and MARK vector-source layers |

Questions and inputs are in `benchmark/portrayal/tasks.jsonl`. Expected answers are stored
separately in `benchmark/portrayal/ground-truth.json`; systems receive only the input task.

## Metrics

- **Accuracy:** complete task result is correct.
- **Evidence accuracy:** cited PDF page exactly matches frozen ground truth.
- **Graph grounding:** path contains `PORTRAYED_BY`, `USES_SYMBOL`, `SUPPORTED_BY`, and
  `EVIDENCED_ON`.
- **Per-task-family accuracy:** prevents map failures from hiding behind easy questions.
- **Input fingerprint:** detects any changed task, answer, graph, or source record.

Wrong scale/profile cases are correct only when the system abstains. This matters because borrowing
a symbol from a different specification is an unsafe mapping decision.

## Ablation controls

| Configuration | Has PDF text | Has graph | Selects symbol | Compiles map |
|---|---:|---:|---:|---:|
| Ungrounded control | no | no | no | no |
| PDF search | yes | no | no | no |
| GraphRAG | via graph evidence | yes | yes | no |
| Full NMA | via graph evidence | yes | yes | yes |

Current deterministic development-set result:

| Configuration | Accuracy | Evidence | Graph path |
|---|---:|---:|---:|
| Ungrounded control | 0.000 | 0.000 | 0.000 |
| PDF search | 0.381 | 0.350 | 0.000 |
| GraphRAG | 0.762 | 0.722 | 0.722 |
| Full NMA | 1.000 | 1.000 | 1.000 |

The difference between GraphRAG and Full NMA is the five map-compilation tasks. This isolates the
value of converting retrieved knowledge into an actual vector-map style.

## What these numbers do not prove

They do not measure a named LLM, generalization to all features, production readiness, or expert
agreement. The set was used during development and has only 21 tasks. It is a regression proof that
the architecture works as specified.

Publication requires:

1. two mapping/cartography experts independently review source records and answers;
2. disagreements are adjudicated and recorded;
3. a larger held-out test set is sealed before model/prompt tuning;
4. named model and PDF-RAG configurations use frozen versions and repeated runs;
5. symbol-image similarity or cartographer acceptance is added after official glyph extraction;
6. confidence intervals and error analysis are reported.

## Reproduce

```bash
nma-bench --root . --output artifacts/benchmark/portrayal-results.json
```

The earlier RIVERL validation benchmark is retained as a supporting regression suite:

```bash
nma-validation-bench --root .
```

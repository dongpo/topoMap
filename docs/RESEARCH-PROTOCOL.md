# Research protocol for NMA validation

## Primary research question

To what extent does a specification-aware, tool-augmented geospatial agent reliably retrieve,
interpret, and execute national-mapping rules, and how much do structured knowledge, deterministic
GIS tools, provenance, and approval controls improve performance over ungrounded and document-only
baselines?

## Hypotheses

- H1: structured retrieval improves rule, version, and field accuracy over document retrieval.
- H2: deterministic GIS tools improve defect detection and localization over language-only systems.
- H3: explicit evidence records improve provenance completeness and reduce unsupported conclusions.
- H4: an approval policy reduces unsafe writes without reducing read-only task completion.

## Experimental factors

Use the same model family, temperature, prompt budget, and task wording across these configurations:

1. plain model with no retrieval or tools;
2. document RAG with frozen chunking, embedding, index, and top-k;
3. structured/knowledge-graph retrieval without GIS tools;
4. full NMA with structured retrieval, deterministic tools, provenance, and approval policy.

The current offline proxy is not configuration 1 and must never be labelled as such in a paper.

## Dataset construction

- Select one or two national-mapping layers with 20–30 independently formalized rules.
- Obtain written permission or confirm an open licence for every redistributed source.
- Use synthetic geometries where authoritative production data cannot be shared.
- Inject defects from a preregistered catalogue, then have a second expert verify the ground truth.
- Keep at least 25% of cases sealed from prompt and system development.
- Include clean controls, single-defect cases, multi-defect cases, ambiguous cases, and corrupted input.

## Measures

- Knowledge: exact answer, entity precision/recall, version accuracy.
- Retrieval: rule recall@k, evidence-section and evidence-page accuracy.
- Tool use: tool/argument accuracy, unnecessary calls, completion rate.
- Validation: feature-level precision, recall, F1, severity accuracy.
- Provenance: document/version/section/page/rule/tool/input/output completeness.
- Safety: unsafe execution rate, approval-request precision/recall, obsolete-rule detection.
- Operations: latency, cost, repeatability, failure recovery, abstention.

## Run controls

- Record model/provider snapshot and run date.
- Freeze prompts and tool schemas by commit hash.
- Use low temperature; run stochastic configurations at least three times.
- Record raw outputs and tool traces without chain-of-thought.
- Score automatically where possible; blind expert adjudication elsewhere.
- Report confidence intervals and per-category results.
- Analyze every false positive, false negative, unsafe action, and unsupported citation.
- Run named model and RAG configurations through `nma-bench-adapter/1.0`; verify that result files
  contain immutable model/server metadata and no placeholder values.

## Claim boundary

Success on one layer supports the claim that the architecture can operationalize a bounded
specification subset. It does not support autonomous national-map production, generalization to all
authorities, or legal equivalence to expert judgment.

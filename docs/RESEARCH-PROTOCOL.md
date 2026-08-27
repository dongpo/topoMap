# Research protocol for NMA portrayal

## Primary research question

To what extent can a specification-aware, graph-grounded geospatial agent correctly answer
national-map portrayal questions, select applicable symbols, and compile those decisions into an
auditable vector-tile map—and what do graph structure and executable tools add beyond PDF search?

## Hypotheses

- **H1:** GraphRAG improves feature/rule/version retrieval over PDF text search.
- **H2:** Executable graph constraints improve correct abstention for unsupported profiles/scales.
- **H3:** Full NMA compiles more correct map decisions than GraphRAG without execution.
- **H4:** Complete graph paths improve evidence traceability over page retrieval alone.
- **H5:** Expert-reviewed official glyph extraction improves symbol acceptance over implementation
  approximations.

## Experimental configurations

1. named plain model with no documents or tools;
2. named model with frozen PDF RAG;
3. the same model with frozen GraphRAG context but no map compiler;
4. full NMA with GraphRAG, portrayal decision tool, evidence, abstention, and style compiler.

Checked-in deterministic systems are architecture controls, not substitutes for named-model runs.

## Task families

- human questions: codes, pages, instructions, versions, and exceptions;
- symbol decisions: feature + attributes + scale + profile → symbol/action/abstention;
- graph evidence: exact entity, rule, symbol, observation, and page path;
- map compilation: vector layer, feature filter, style, rule and evidence metadata;
- visual portrayal: official symbol crop versus generated glyph, assessed by experts;
- robustness: ambiguous names, conflicting profiles, missing features, wrong scale, and multilingual
  wording.

## Ground-truth construction

1. Two experts independently review each PDF observation and official symbol crop.
2. Reviewers answer tasks without seeing NMA output.
3. Disagreements are adjudicated and preserved in an audit file.
4. Development and held-out cases are separated before system tuning.
5. At least 25% remains sealed; synonymous question forms do not cross splits.
6. Ambiguous tasks have an explicit acceptable set or expected abstention.

## Measures

- exact or semantic answer accuracy;
- feature/entity precision and recall;
- PDF page and evidence-span accuracy;
- symbol/action accuracy and exception accuracy;
- unsupported-profile/scale abstention precision and recall;
- MapLibre source-layer, filter, and metadata correctness;
- official-glyph similarity and blind cartographer acceptance;
- unsupported-claim rate;
- latency, cost, repeated-run consistency, and tool failures.

Report every task-family score rather than one opaque aggregate.

## Run controls

- freeze model digest, server, prompt, retrieval corpus, chunking, top-k, graph revision, and style
  compiler commit;
- ensure ground truth is never included in requests;
- use at least three runs for stochastic configurations;
- record raw answers, retrieved context, tool traces, evidence paths, failures, latency and cost;
- perform blind expert adjudication for semantic and visual results;
- report confidence intervals and failure taxonomy.

## Claim boundary

The current 21-task suite is a development regression proving that the implemented path behaves as
specified. Publication-grade claims require official symbol-cell verification, independent expert
ground truth, a sealed held-out set, and named-model comparisons.

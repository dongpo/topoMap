# AMA Research and Open-Source Contribution Model

## Purpose

Authoritative Mapping Agent (AMA) is intentionally developed as both GIScience research and open geospatial research software. The two tracks share artifacts, but they use different success criteria.

## Two-track model

| Dimension | GIScience research | Open-source engineering |
| --- | --- | --- |
| Core question | Is the claim true, and under what conditions? | Does the implementation work and can others reuse it? |
| Unit of progress | research question, hypothesis, experiment | module, contract, profile, release |
| Validation | baselines, ablation, held-out tasks, expert review | unit/integration tests, CI, reproducible builds |
| Meaning of PASS | evidence supports a bounded hypothesis | implementation satisfies a specified contract |
| Generalization | scientific external validity | portability and extensibility |
| Main outputs | paper, benchmark, experiment data | code, schemas, profiles, API, release |

A software acceptance test MUST NOT be cited as evidence that an empirical research hypothesis is true.

## GIScience research questions

### RQ1 — Knowledge grounding
Can explicit geospatial and cartographic knowledge improve an LLM's understanding of mapping entities, schemas, classifications, and portrayal rules?

### RQ2 — Constrained agentic execution
Can a knowledge-grounded agent translate mapping intent into executable plans while maintaining explicit cartographic and geospatial constraints?

### RQ3 — Trust and auditability
Can authorization, deterministic verification, and provenance make probabilistic AI agents suitable for authoritative mapping workflows?

## Open-source contribution units

### O1 — AMA Core
A vendor-neutral, replaceable-component architecture for knowledge-grounded geospatial agents.

### O2 — Executable mapping knowledge
A reproducible pipeline from source specification to candidate extraction, expert-reviewed observation, graph compilation, retrieval, executable rule, and evidence path.

### O3 — AMA Contracts
Machine-readable structures for intent, evidence, rules, execution plans, authorization, verification, receipts, and provenance.

### O4 — AMA-Bench / NMA-Bench
An open benchmark and adapter layer that can compare ungrounded LLM, text/vector RAG, GraphRAG, and full AMA configurations under common tasks and metrics.

### O5 — Mapping knowledge profiles
Portable jurisdiction- or specification-specific packages containing source metadata, vocabulary, classifications, portrayal rules, constraints, provenance, and tests.

## Research-to-software traceability

| Research objective | Primary open artifact | Publication evidence required |
| --- | --- | --- |
| RQ1 knowledge grounding | knowledge compiler, graph, retriever, profiles | controlled LLM-only vs RAG vs GraphRAG comparison |
| RQ2 constrained execution | planner, contracts, GIS adapters | plan correctness, rule compliance, execution success, generalization |
| RQ3 trust/auditability | authorization, verifier, provenance/receipt | verification reliability, reproducibility, provenance completeness, failure analysis |
| Overall evaluation | AMA-Bench | held-out tasks, independent expert review, explicit experimental protocol |

## Planned comparative experiment

The publication-grade experiment should keep the task set and input data constant while changing the knowledge/execution condition:

1. **LLM only** — no external mapping knowledge.
2. **Text/vector RAG** — authoritative documents retrievable as text chunks.
3. **GraphRAG** — explicit mapping knowledge graph used for retrieval/reasoning.
4. **Full AMA** — GraphRAG plus explicit constraints, executable plan, deterministic geospatial execution, verification, authorization boundary, and provenance.

Recommended metrics:

- mapping-rule compliance;
- feature/class/schema accuracy;
- planning accuracy;
- hallucination rate;
- abstention correctness;
- execution success;
- deterministic verification pass/fail accuracy;
- run-to-run reproducibility;
- provenance completeness;
- generalization across Point, LineString, Polygon and unseen mapping tasks.

## Contribution acceptance model

A contribution can be valuable even when it does not change the core software. Accepted contribution classes should include:

- mapping profiles;
- reviewed executable rules;
- validators;
- benchmark cases and baseline adapters;
- open GIS execution adapters;
- documentation of reproducible experiments;
- interoperability mappings to external standards or software.

Rule contributions must declare source identity, version, licence/redistribution boundary, target entity or operation, constraints, severity/authority level, provenance, and review status. Automatically extracted knowledge remains non-executable until reviewed under the profile's declared governance process.

## Naming transition

The research programme is moving from **National Map Agent (NMA)** toward **Authoritative Mapping Agent (AMA)** because the architecture is not inherently limited to national mapping agencies. `Authoritative` describes the critical property: mapping actions are grounded in explicitly sourced, reviewable, versioned mapping knowledge.

The transition is deliberately non-destructive:

- historical tags and frozen evidence retain NMA names;
- the Python package and CLI retain `national-map-agent` / `nma` until a compatibility plan is implemented;
- new research prose may use `Authoritative Mapping Agent (AMA), formerly National Map Agent (NMA)` during the transition;
- no frozen identifier is rewritten.

## FOSS4G vs journal publication

### FOSS4G contribution
Emphasize reusable open geospatial infrastructure:

- executable mapping knowledge;
- reference architecture;
- portable graph and schemas;
- MapLibre/GDAL/open tooling integration;
- benchmark harness;
- contribution model for additional mapping profiles.

The central question is: **What reusable open components does AMA add to the GeoAI/FOSS4G ecosystem?**

### Journal contribution
Emphasize scientific evaluation:

- research gap and RQ1–RQ3;
- controlled baselines;
- held-out tasks;
- quantitative and expert evaluation;
- ablation and failure analysis;
- limits of generalization.

The central question is: **What does the AMA experiment establish about knowledge-grounded geospatial agents?**

## Development rule going forward

New work should satisfy at least one of these conditions:

1. it is required to test one of RQ1–RQ3; or
2. it creates a reusable open-source contribution unit O1–O5.

Work that satisfies neither condition should normally be deferred until after the research and FOSS4G release objectives are met.

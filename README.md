# Authoritative Mapping Agent (AMA)

**Open research architecture and reference implementation for knowledge-grounded, rule-constrained, verifiable, and auditable geospatial agents.**

AMA evolves the National Map Agent (NMA) research prototype into an open geospatial research-software project. The project investigates how AI agents can use explicit cartographic and geospatial knowledge to perform mapping actions that remain evidence-backed, constrained by authoritative rules, independently verifiable, and auditable.

> **Compatibility note:** the existing Python package, CLI commands, schemas, frozen tags, and historical evidence continue to use the `nma` / `national-map-agent` identifiers. They are intentionally retained during the AMA transition so that published evidence and reproducible builds are not broken.

## Why this project exists

LLM-based GIS systems can already interpret natural-language requests, select geoprocessing tools, generate code, and create maps. GraphRAG can improve domain grounding. The remaining research problem is not simply whether an LLM can *do GIS*, but whether an AI agent can safely participate in authoritative mapping workflows where decisions must be traceable to explicit knowledge, respect domain constraints, and produce outputs that can be verified independently of the model.

AMA therefore separates probabilistic reasoning from authoritative execution:

```text
user intent
    ↓
knowledge grounding
    ↓
evidence-backed mapping rules
    ↓
constrained execution plan
    ↓
human / policy authorization
    ↓
deterministic geospatial execution
    ↓
verification
    ↓
provenance / execution receipt
```

## GIScience research questions

**RQ1 — Knowledge grounding**  
Can explicit geospatial and cartographic knowledge improve an LLM's understanding of mapping entities, schemas, classifications, and portrayal rules?

**RQ2 — Constrained agentic execution**  
Can a knowledge-grounded agent translate mapping intent into executable plans while maintaining explicit cartographic and geospatial constraints?

**RQ3 — Trust and auditability**  
Can authorization, deterministic verification, and provenance make probabilistic AI agents suitable for authoritative mapping workflows?

These questions define the scientific programme. Passing software tests is not treated as evidence that a research hypothesis is true; publication-grade evaluation requires controlled baselines, held-out tasks, and independent review.

## Open-source contributions

AMA is designed to contribute reusable infrastructure rather than only a conference demo.

1. **Reference architecture** — a replaceable-component architecture for knowledge-grounded geospatial agents.
2. **Executable mapping knowledge** — a reproducible pipeline from authoritative specifications to reviewed observations, graph knowledge, executable rules, and evidence paths.
3. **Agent contracts** — machine-readable intent, evidence, plan, authorization, verification, receipt, and provenance structures.
4. **AMA-Bench / NMA-Bench** — an open evaluation harness for knowledge-grounded geospatial agents, with baseline adapters and separated ground truth.
5. **Mapping knowledge profiles** — a path for mapping authorities and communities to contribute jurisdiction- or specification-specific knowledge without changing the core architecture.

See [`docs/RESEARCH-AND-OPEN-SOURCE-CONTRIBUTIONS.md`](docs/RESEARCH-AND-OPEN-SOURCE-CONTRIBUTIONS.md) for the research/software boundary and contribution model.

## Current reference implementation

The frozen implementation converts reviewed national topographic-map portrayal knowledge into executable graph knowledge and uses it to drive evidence-bearing map decisions.

```text
authoritative portrayal specification
        ↓ candidate extraction
candidate observations (not executable)
        ↓ expert review gate
reviewed observations
        ↓ reproducible compiler
executable knowledge graph
        ↓ GraphRAG / graph retrieval
feature + rule + evidence path
        ↓ agent planning
mapping decision / abstention / exception
        ↓ deterministic compiler / GIS execution
MapLibre layers + verification + provenance
```

The reference implementation currently includes Python modules, CLI tools, JSON/JSONL knowledge artifacts, JSON Schemas, tests, benchmark tasks, optional Neo4j support, MapLibre/PMTiles portrayal, and reproducible evidence artifacts.

## Open and replaceable stack

- Python for knowledge compilation, retrieval, planning, verification, benchmarking, and APIs
- JSON / JSONL for portable knowledge and evidence
- optional Neo4j adapter; Neo4j is not required to reproduce the research artifacts
- GDAL/OGR and geospatial Python tooling for deterministic GIS operations
- MapLibre GL JS and PMTiles for open web-map portrayal
- JSON Schema and OpenAPI-compatible interfaces
- no dependency on a single LLM vendor or agent framework

The architectural goal is **stable contracts with replaceable implementations**: LLM, retriever, graph store, GIS engine, and renderer can be substituted without changing the research boundary.

## Quick start

Requirements: Python 3.11+. Poppler `pdftotext` is needed only when re-extracting source PDFs.

```bash
git clone https://github.com/dongpo/topoMap.git
cd topoMap
git switch contrib/ama-open-research-software
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ".[dev]"

make test
nma-bench --root .
```

Useful commands from the existing compatibility CLI:

```bash
nma compile-knowledge
nma ask "依 NLSC112V5.4，小學的代碼是什麼？"
nma portray 9950201 --large-detached-building
nma compile-style
nma-bench --root .
```

## Benchmark status

The repository contains a small deterministic development benchmark covering human mapping questions, symbol decisions, map compilation, evidence accuracy, and graph-path completeness. It is useful for architecture regression and reproducibility, but it is **not yet a publication-grade estimate of LLM performance**.

The planned scientific evaluation compares:

```text
A. LLM only
B. vector/text RAG
C. GraphRAG
D. full AMA: GraphRAG + constraints + execution + verification
```

Primary evaluation dimensions include rule compliance, schema/feature accuracy, planning accuracy, hallucination rate, execution success, verification pass rate, reproducibility, provenance completeness, and cross-feature generalization.

## Mapping profiles and community contribution

The long-term project model separates a stable AMA core from reusable mapping profiles:

```text
AMA Core
 ├─ Taiwan NLSC profile
 ├─ Japan GSI profile        (future/community)
 ├─ OSM/community profile    (future/community)
 └─ user-defined profile
```

A profile may contribute source metadata, vocabulary/ontology terms, feature classifications, portrayal rules, constraints, test cases, and provenance. Automated extraction never becomes authoritative executable knowledge until it passes the declared review boundary.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) before proposing rules, validators, profiles, or benchmark cases.

## Research integrity and authority boundary

AMA does **not** claim autonomous authoritative map production. The current public demonstrations prove bounded implementation properties such as evidence retrieval, controlled planning, deterministic execution, verification, authorization hand-off, and provenance. They do not by themselves prove that live LLM + GraphRAG collaboration improves mapping quality.

Publication-grade claims require independent expert review, sealed held-out evaluation, explicit baselines, and reproducible experimental protocols.

Restricted or non-redistributable source documents and private test archives are never required to understand the architecture. Official source specifications may be referenced without being redistributed when their licence does not permit redistribution.

## Repository map

```text
src/nma/                     reference implementation (legacy-compatible package name)
data/extraction/             reviewed observations / extraction boundary
data/knowledge/              portable executable knowledge
schemas/                     machine-readable contracts
benchmark/                   benchmark tasks, ground truth, adapters
tests/                       implementation and regression tests
docs/                        architecture, research, runbooks, historical evidence
assets/                      reusable open assets where licensing permits
```

Historical ROAD / BUILD / CORE / AGENT / HERO / DEMO reports and frozen tags remain part of the engineering evidence trail. They are not substitutes for scientific experimental evidence.

## Citation and licence

Code is released under **Apache-2.0**. Synthetic validation fixtures are CC0-1.0 where marked. No licence is asserted for authoritative source PDFs or private test archives.

See [`CITATION.cff`](CITATION.cff) for software citation metadata.

## Project status

**Current phase: research-software normalization before publication-grade comparative evaluation.**

For FOSS4G, AMA/NMA is presented as an open geospatial architecture, executable-knowledge pipeline, benchmark, and reference implementation. The subsequent journal study will evaluate the GIScience hypotheses with controlled LLM-only, RAG, GraphRAG, and full-AMA experiments.

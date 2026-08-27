# Authoritative Mapping Agent (AMA)

Authoritative Mapping Agent (AMA) is an open research architecture and reference implementation
for knowledge-grounded, rule-constrained, verifiable, and auditable geospatial agents.

AMA was developed from the National Map Agent (NMA) research prototype. Historical `nma`
package names, CLI commands, schemas, tags, and frozen evidence remain unchanged for
reproducibility.

## Research problem

LLM-based GIS systems can interpret requests, select tools, and generate maps. Authoritative
mapping adds a harder requirement: every consequential decision must be grounded in explicit
knowledge, constrained by mapping rules, independently verifiable, and attributable after the
model has finished reasoning.

AMA investigates three GIScience questions:

- **RQ1 — Knowledge grounding:** Can explicit geospatial and cartographic knowledge improve the
  correctness and traceability of agent reasoning?
- **RQ2 — Constrained agentic execution:** Can a knowledge-grounded agent translate mapping
  intent into executable plans while preserving explicit mapping rules and constraints?
- **RQ3 — Trust and auditability:** Can authorization, deterministic verification, and provenance
  make probabilistic AI agents suitable for authoritative mapping workflows?

Software tests establish implementation conformance. They do not, by themselves, validate these
research questions.

## Five open-source contributions

1. **AMA Core** — an open, vendor-neutral reference architecture for authoritative geospatial
   agents with replaceable reasoning, retrieval, graph, GIS, and rendering components.
2. **Executable Mapping Knowledge** — a governed path from authoritative specification to
   reviewed observations, machine-readable graph, executable mapping rules, and evidence paths.
3. **AMA Contracts** — machine-readable intent, evidence, plan, authorization, execution,
   verification, provenance, and receipt structures.
4. **AMA-Bench** — a benchmark and evaluation harness intended to support a controlled comparison
   of LLM-only, Vector RAG, GraphRAG, and Full AMA systems.
5. **Mapping Knowledge Profiles** — reusable authority- or community-specific knowledge packages
   that keep local vocabularies, rules, constraints, provenance, and tests outside the stable core.

School, ROAD, and BUILD are bounded reference and validation cases for these contributions; they
are not the core contributions themselves. See the
[research and open-source contribution model](docs/research/RESEARCH-AND-OPEN-SOURCE-CONTRIBUTIONS.md).

## Architecture

```text
mapping intent
    ↓
knowledge grounding ← authoritative sources + reviewed mapping profile
    ↓
evidence-bearing plan + explicit constraints
    ↓
human / policy authorization
    ↓
deterministic GIS execution
    ↓
independent verification
    ↓
provenance + execution receipt
```

The Python implementation, JSON/JSONL knowledge, JSON Schemas, optional Neo4j projection,
MapLibre portrayal, and benchmark adapters implement these boundaries with open and replaceable
components. The [architecture index](docs/architecture/README.md) links the detailed contracts and
integration notes.

## Smallest reproducible example

Requirements: Python 3.11+. GDAL/OGR is required for the complete geospatial verification suite;
Poppler is needed only when source PDFs are re-extracted.

```bash
git clone https://github.com/dongpo/topoMap.git
cd topoMap
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ".[dev]"

nma compile-knowledge
nma ask "依 NLSC112V5.4，小學的代碼是什麼？"
```

The compatibility CLI also exposes `nma portray`, `nma compile-style`, and the controlled demo
commands. More involved reproduction paths remain in [the quickstart](docs/QUICKSTART.md).

## Run AMA-Bench

```bash
nma-bench --root .
```

The checked-in benchmark is a deterministic development and regression harness. Prompts/tasks and
ground truth are separated, and external baseline adapters are available under `benchmark/`.
[Benchmark documentation](docs/BENCHMARK.md) explains the task families and interpretation limits.

## Currently validated claims

The repository's automated and frozen evidence validates bounded software properties:

- reviewed observations compile into deterministic executable knowledge;
- retrieval and planning can return explicit evidence and constraints for the covered cases;
- authorization, execution, verification, and provenance contracts are machine-checkable;
- School, ROAD, and BUILD controlled reference cases satisfy their frozen implementation gates;
- the browser-local static demo is path-prefix safe, bounded, credential-free, and deployable from
  `public/gh-pages` without making `main` a Pages-only branch.

These are implementation-conformance claims, not evidence that an empirical GIScience hypothesis
is true or that AMA has autonomous production authority.

## Remaining research work

Publication-grade evidence still requires a preregistered or otherwise explicit protocol,
controlled LLM-only / Vector RAG / GraphRAG / Full AMA comparisons, held-out tasks, independent
expert review, ablation and failure analysis, and evaluation across unseen mapping tasks and
geometry types. No current test result substitutes for that work.

## Contribute

Contributions are welcome as mapping profiles, reviewed executable rules, deterministic
validators, benchmark cases and baseline adapters, open GIS integrations, or reproducible research
protocols. Every rule contribution must identify its source, version, licence/redistribution
boundary, review status, constraints, provenance, and expected validation cases.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [mapping-profile guide](profiles/README.md) before
submitting a profile, rule, validator, or benchmark.

## NMA → AMA compatibility

AMA is the public research/software identity. During the FOSS4G transition, compatibility-facing
identifiers remain:

- Python distribution: `national-map-agent` version `0.2.0`;
- import package and CLI: `nma`;
- benchmark command: `nma-bench`;
- historical schemas, manifests, artifacts, branches, and tags: their existing NMA names;
- immutable implementation baseline: annotated tag `nma-v1.0-final`.

The package version and frozen evidence tag series are separate version namespaces. The repository
does not claim an `ama-v1.0` release. See the [version and compatibility policy](docs/open-source/VERSIONING.md).

## Repository map

```text
src/nma/                     compatibility package and reference implementation
profiles/                    mapping-profile authoring and package index
schemas/                     machine-readable AMA/NMA contracts
benchmark/                   AMA-Bench tasks, ground truth, and adapters
tests/                       implementation and regression tests
data/                        reviewed knowledge, fixtures, and frozen records
assets/                      redistributable open assets
docs/research/               research questions, claims, and experiment boundary
docs/architecture/           architecture and repository reconciliation
docs/open-source/            versioning, compatibility, and contributor policy
docs/engineering-history/    preserved milestone and freeze reports
public/gh-pages/             the only GitHub Pages deployment artifact
.github/                     verification and Pages workflows
```

## Citation, licence, and status

Code is released under [Apache-2.0](LICENSE). Synthetic validation fixtures are CC0-1.0 where
marked. No licence is asserted for authoritative source PDFs or private test archives; those are
not redistributed. Use [CITATION.cff](CITATION.cff) for software citation metadata.

Current phase: canonical research-software normalization before FOSS4G release preparation and
publication-grade AMA-Bench experiment design.

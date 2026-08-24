# National Map Agent v0.2

NMA v0.2 is an open research vertical slice that turns national topographic-map portrayal facts
into executable graph knowledge, lets an agent retrieve evidence-backed symbol rules, and compiles
those decisions into MapLibre layers over an existing PMTiles vector map.

The main demonstration covers fire hydrants, aquaculture/fish ponds, police facilities, six school
types, and post offices. Every symbol decision returns the graph path and the exact authoritative
PDF page that supports it.

**Current status:** Stable public five-scene Demo RC1 (`nma-demo-v0.2-rc1`) plus a separately
fingerprinted Agentic v0.3 candidate. The public Pages release remains bounded and evidence-only;
Agentic v0.3 has not been deployed.

[Demo entry file](nmaAgentDemo.html) · [Two-minute quickstart](docs/QUICKSTART.md) ·
[RC1 evidence](docs/STABLE-DEMO-RC1.md) · [Architecture](docs/ARCHITECTURE.md) ·
[Conference narrative](docs/FIVE-SCENE-NARRATIVE.md) ·
[D20 review package](release/review-package/README.md) ·
[Presentation v0.9](artifacts/presentation/nma-foss4g-presentation-v0.9.pptx) ·
[D21 public-assets RC](docs/PUBLIC-ASSETS-RC1.md) ·
[D24 Q&A](docs/D24-QA.md) ·
[D24 public-link audit](docs/D24-PUBLIC-DELIVERY.md) ·
[Agentic v0.3 freeze](docs/AGENTIC-V0.3-FREEZE.md)

## Five scenes, five agent capabilities

All five scenes use one reviewed-record → graph → retrieval → portrayal → MapLibre pipeline. They
are deliberately different tests of the same agent boundary, not five disconnected feature demos.

| Scene | Agent capability | Frozen evidence |
|---|---|---|
| School | Versioned retrieval, governance, evidence path, and map execution | code `9920103`, PDF p. 61 |
| Fire hydrant | Deterministic symbol choice with authoritative dimensions | code `9350906`, PDF p. 11 |
| Police | Alias resolution plus labelled portrayal | code `9910603`, PDF p. 60 |
| Fish pond | Geometry-aware fill, outline, and companion icon | code `9740100`, PDF p. 50 |
| Post office | Conditional exception handling and explicit abstention boundary | code `9950201`, PDF p. 69 |

## What is implemented

```text
authoritative portrayal PDF
        ↓ Poppler extraction
code-anchored candidates (not executable)
        ↓ human review gate
reviewed observations
        ↓ reproducible compiler
executable portrayal graph
        ↓ GraphRAG retrieval
feature + rule + symbol + evidence path
        ↓ portrayal agent
symbol decision / abstention / exception
        ↓ style compiler
evidence-bearing MapLibre layers
        ↓
PMTiles vector map + governance panel
```

The checked-in graph currently contains 10 source observations, 44 nodes, and 85 edges from
`01-一千分之一地形圖圖式規格表.pdf`, version `NLSC112V5.4` dated 2024-02-28.

Open [`nmaAgentDemo.html`](nmaAgentDemo.html) to see the vector-tile portrayal demo. It loads
`out1120902.pmtiles`, applies graph-compiled layers, answers sample cartographer questions, and
shows the evidence path when a result or rendered feature is selected.

## Status and research boundary

The source PDF is now locally hashed and pages 11, 50, 60–62, and 69 were rendered and visually
verified. The original police and hydrant approximations were replaced with open SVG/Canvas
implementations matching the official crossed-circle and boxed-`火` geometry. Fish, school, and
post-office geometry and dimensions were also verified. Independent cartographer sign-off remains
the publication gate; official PDF crops are not redistributed.

Source-derived records and benchmark labels also require independent expert review before
publication. NMA does not claim autonomous authoritative map production.

## Quickstart

Requirements: Python 3.11+. Poppler's `pdftotext` is required only when extracting a PDF again.

```bash
git clone https://github.com/dongpo/topoMap.git
cd topoMap
git switch codex/nma-v0.2-authoritative
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ".[dev]"

# Deterministically rebuild the shared graph/style, then verify Stable Demo RC1
make demo-reset
make demo-rc1
make test

# Serve the same files used by the live browser demo
python -m http.server 8000
```

Open <http://localhost:8000/nmaAgentDemo.html>. The tested live sequence, expected evidence,
online preflight, evidence-only fallback, and recovery steps are in the
[quickstart](docs/QUICKSTART.md). Stop after the RC1 checks if only command-line reproduction is
needed.

### Inspect individual stages

```bash
nma compile-knowledge
nma ask "依 NLSC112V5.4，小學的代碼是什麼？"
nma portray 9950201 --large-detached-building
nma compile-style
nma-bench --root .
```

Candidate extraction from a locally supplied official PDF is separate from review and publication:

```bash
nma extract-portrayal \
  --pdf path/to/01-一千分之一地形圖圖式規格表.pdf \
  --out artifacts/extraction-candidates.jsonl
```

Candidate records are explicitly marked `candidate-not-executable`. Only reviewed records in
`data/extraction/portrayal-records.jsonl` are compiled.

## Frozen five-scene demo

The RC1 school, fire-hydrant, police, fish-pond, and post-office sequence is frozen as one executable
data contract. Check the exact inputs, outputs, evidence fields, map layers, paths, licences, and
timing with:

```bash
make demo-scenes
make demo-freeze
make demo-soak
make demo-offline
make demo-backup
make demo-rc1
```

Use `make demo-reset` to deterministically rebuild the shared graph and MapLibre style before a
rehearsal. See [`docs/FIVE-SCENE-DEMO.md`](docs/FIVE-SCENE-DEMO.md) for the five-minute script and
setup procedure.
The feature-complete freeze manifest records the approved D12 commit, the clean five-scene
walkthrough, all accepted capabilities and known issues, and cryptographic fingerprints for the
runtime artifacts. `make demo-freeze` fails if one of those artifacts drifts without an explicit
freeze update.

`make demo-soak` runs 20 clean-reset repetitions, records per-run and percentile timing, captures
recovery steps, and classifies failures as blocking defects with an owner and next action. Browser
rounds are recorded separately because they require a running preview. See
[`docs/FIVE-SCENE-SOAK.md`](docs/FIVE-SCENE-SOAK.md) for the protocol, measured result, defect
triage, and recovery sequence.

`make demo-offline` verifies the local PMTiles path, pinned service-worker runtime cache, explicit
evidence-only fallback, and owned non-blocking deferrals. See
[`docs/OFFLINE-RUNTIME.md`](docs/OFFLINE-RUNTIME.md) for the online preflight and degraded-mode
test.

`make demo-backup` verifies the portable D16 video, screenshots, evidence panels, player, runbook,
and checksums. `make demo-rc1` then verifies the complete D17 Stable Demo RC1 gate: 20 clean-reset
runs, ten cached live-map browser rounds, both D15 runtime modes, the human-approved D16 fallback,
the versioned environment and runbooks, and zero unresolved blocking defects. See
[`docs/STABLE-DEMO-RC1.md`](docs/STABLE-DEMO-RC1.md).

## NMA-Bench v0.1

The primary benchmark now matches the questions a cartographer or mapping-authority analyst asks:

| Task family | Count | Example | Correct means |
|---|---:|---|---|
| Human questions | 8 | “What is the code for a fire hydrant?” | correct answer, entity set, PDF page |
| Symbol decisions | 8 | “How should 9950201 be portrayed?” | correct symbol/action, rule, evidence, or abstention |
| Map compilation | 5 | Compile fish pond into `J01_WATERA` | correct source layer, filter, rule ID, PDF page |

The expected answers are stored separately and never included in a system request. The four
checked-in controls produce:

| System | Overall accuracy | Evidence accuracy | Complete graph path |
|---|---:|---:|---:|
| Ungrounded control | 0.000 | 0.000 | 0.000 |
| PDF text search | 0.381 | 0.350 | 0.000 |
| GraphRAG | 0.762 | 0.722 | 0.722 |
| Full NMA | 1.000 | 1.000 | 1.000 |

These are deterministic architecture tests over a small development set—not results for a named
LLM and not yet a publication-grade estimate. The next gate is independent expert review and a
sealed held-out set. The earlier 31-task RIVERL validator suite remains available as a supporting
regression check through `nma-validation-bench`; it is no longer presented as the main NMA proof.

See [`docs/BENCHMARK.md`](docs/BENCHMARK.md) for a plain-language explanation of why question
accuracy alone is insufficient and how the layers of evidence make the result more convincing.

## Open architecture and FOSS4G

NMA uses open, replaceable components and portable files:

- Poppler for PDF text extraction;
- JSONL observations and an inspectable JSON property graph;
- Python for GraphRAG, agent decisions, benchmarking, and APIs;
- MapLibre GL JS and PMTiles for vector-tile portrayal;
- GDAL/OGR for the supporting validation workflow;
- JSON/OpenAPI interfaces that do not require Agno or another large agent framework.

The v0.33 read-only Knowledge Service can query an identity-verified Neo4j projection through fixed,
parameterized operations; Neo4j is not required for reproduction. The portable graph remains the
reviewed semantic authority, and the Agent cannot submit Cypher or modify the canonical KG. See
[`docs/NMA-V0.33-READONLY-KNOWLEDGE-SERVICE.md`](docs/NMA-V0.33-READONLY-KNOWLEDGE-SERVICE.md).

The API adds:

- `GET /v1/knowledge/portrayal`
- `GET /v1/maplibre/portrayal-layers`
- `POST /v1/agent/ask`
- `POST /v1/agent/portray`

The FOSS4G Hiroshima narrative is in
[`docs/FOSS4G-HIROSHIMA-2026.md`](docs/FOSS4G-HIROSHIMA-2026.md).
The D18 evidence-backed slide storyboard, architecture figure, golden-path figure, and
claim-to-evidence guardrails are in
[`docs/FIVE-SCENE-NARRATIVE.md`](docs/FIVE-SCENE-NARRATIVE.md).

## D20 review package

`make review-package` builds a deterministic, portable review ZIP, verifies every payload
checksum, reruns the frozen five-scene decisions and abstention controls, and rejects secrets or
machine-specific paths. The package documents provenance, licences, schemas, benchmark gates,
roadmap, and a paper skeleton. It deliberately excludes the PMTiles archive and official PDF until
their redistribution boundary permits publication; no new demo functionality is introduced.

See the [review-package README](release/review-package/README.md),
[dataset record](release/review-package/DATASET.md),
[portable ZIP](artifacts/release/nma-v0.2-review-package.zip), and
[machine-readable verification](artifacts/release/nma-v0.2-review-package-verification.json).

## D21 public-assets freeze

`make public-assets-rc` freezes and verifies the repository, bounded public website artifact,
runnable review package, and presentation RC against Stable Demo RC1. The Pages artifact is
evidence-only and explicitly excludes the PMTiles archive while its redistribution terms remain
unconfirmed. See the [D21 release-candidate audit](docs/PUBLIC-ASSETS-RC1.md).

The bounded evidence-only Pages artifact was explicitly approved and deployed from commit
`60eb285` in [run #36](https://github.com/dongpo/topoMap/actions/runs/31019900015). Live verification
covered the homepage, five scene controls, evidence path, architecture image, and browser console.

## Public entry points

| Entry point | Purpose | Release state |
|---|---|---|
| [Repository](https://github.com/dongpo/topoMap) | Source, issues, and review history | Public |
| [RC1 candidate branch](https://github.com/dongpo/topoMap/tree/codex/nma-v0.2-authoritative) | Exact reviewed implementation | Public candidate |
| [Stable RC1 tag](https://github.com/dongpo/topoMap/tree/nma-demo-v0.2-rc1) | Frozen D17 executable baseline | Public |
| [GitHub Pages demo](https://dongpo.github.io/topoMap/nmaAgentDemo.html?mode=degraded) | Hosted evidence-only five-scene demo | Public RC1 |
| [Conference materials](docs/FIVE-SCENE-NARRATIVE.md) | D18 narrative and figures | Candidate; not a published paper |

## Known limitations

- The reviewed subset contains 10 observations for one NLSC portrayal version and five demo
  scenes; it is not a complete national specification.
- Independent cartographer sign-off and a sealed held-out benchmark remain publication gates.
- RC1 GraphRAG is deterministic lexical entity retrieval plus typed graph traversal, not general
  semantic retrieval or a named-LLM evaluation.
- Online first load is required to prime the pinned browser cache; evidence-only mode and the D16
  recording are the supported offline fallbacks.
- PMTiles redistribution terms must be confirmed before publishing the portable map archive.
- The public GitHub Pages artifact intentionally excludes the PMTiles archive and therefore runs
  in evidence-only mode; use the local rehearsal setup for the full live-map RC1.

## Repository map

```text
data/extraction/portrayal-records.jsonl    reviewed PDF observations
data/knowledge/portrayal-profile.json      rendering implementation boundary
data/knowledge/portrayal-graph.json        compiled executable knowledge
data/demo/five-scene-demo.json             frozen scene inputs, outputs and shared data contract
data/demo/five-scene-freeze.json           feature-complete fingerprints and change-control policy
data/demo/stable-rc1.json                   Stable Demo RC1 release manifest and final gate
assets/symbols/nlsc112v5.4/               source-hashed, visually verified open SVG symbols
src/nma/extraction.py                      PDF candidate extraction
src/nma/knowledge.py                       graph compiler and retrieval
src/nma/portrayal.py                       agent and MapLibre compiler
benchmark/portrayal/                       questions and separate ground truth
nmaAgentDemo.html                          PMTiles map + question/evidence UI
index.html                                 responsive public landing page and release boundary
docs/QUICKSTART.md                         install, RC1 verification, preview and recovery path
docs/FIVE-SCENE-DEMO.md                    deterministic setup, reset and live runbook
artifacts/portrayal/maplibre-layers.json   reproducibly generated evidence-bearing styles
```

Code is Apache-2.0. Official PDFs are referenced, not redistributed. Synthetic validation fixtures
are CC0-1.0; no licence is asserted for the authoritative PDFs or private test archive.

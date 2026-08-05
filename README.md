# National Map Agent v0.2

NMA v0.2 is an open research vertical slice that turns national topographic-map portrayal facts
into executable graph knowledge, lets an agent retrieve evidence-backed symbol rules, and compiles
those decisions into MapLibre layers over an existing PMTiles vector map.

The main demonstration covers fire hydrants, aquaculture/fish ponds, police facilities, six school
types, and post offices. Every symbol decision returns the graph path and the exact authoritative
PDF page that supports it.

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

## Important research boundary

The source PDF is now locally hashed and pages 11, 50, 60–62, and 69 were rendered and visually
verified. The original police and hydrant approximations were replaced with open SVG/Canvas
implementations matching the official crossed-circle and boxed-`火` geometry. Fish, school, and
post-office geometry and dimensions were also verified. Independent cartographer sign-off remains
the publication gate; official PDF crops are not redistributed.

Source-derived records and benchmark labels also require independent expert review before
publication. NMA does not claim autonomous authoritative map production.

## Reproduce executable knowledge and map styles

Requirements: Python 3.11+. Poppler's `pdftotext` is required only when extracting a PDF again.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ".[dev]"

# Recompile reviewed PDF records into the portable property graph
nma compile-knowledge

# Ask GraphRAG a human question
nma ask "依 NLSC112V5.4，小學的代碼是什麼？"

# Ask the agent to select a symbol and return its evidence path
nma portray 9950201 --large-detached-building

# Compile graph decisions into MapLibre vector-tile layers
nma compile-style

# Run the answer-key-isolated human-question/portrayal benchmark
nma-bench --root .

pytest
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

An optional Neo4j adapter may load the same node/edge graph later; Neo4j is not required for
reproduction. The portable graph, rule evidence, benchmark, and style output remain the research
assets.

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
docs/FIVE-SCENE-DEMO.md                    deterministic setup, reset and live runbook
artifacts/portrayal/maplibre-layers.json   reproducibly generated evidence-bearing styles
```

Code is Apache-2.0. Official PDFs are referenced, not redistributed. Synthetic validation fixtures
are CC0-1.0; no licence is asserted for the authoritative PDFs or private test archive.

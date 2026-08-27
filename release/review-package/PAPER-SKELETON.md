# Paper skeleton: National Map Agent v0.2

## Provisional title

From National Portrayal Specifications to Auditable Map Execution: An Evidence-Bearing Agent
Architecture and Five-Scene Demonstration

## Research question

Can reviewed national portrayal evidence become executable while its source authority remains
inspectable through retrieval, symbol selection, exception handling, and map-layer compilation?

## Bounded contributions

1. A source-to-execution provenance model separating extraction candidates, reviewed facts,
   executable profiles, graph knowledge, agent decisions, and compiled map output.
2. A portable evidence contract that returns source version, page, hash, review status, graph path,
   and execution log with each selected result.
3. Five heterogeneous demo scenes that exercise retrieval, deterministic dimensions, alias
   resolution, geometry-aware portrayal, conditional exceptions, and abstention.
4. A reproducible development benchmark with explicit publication gates for expert review,
   held-out evaluation, and named baselines.

## Abstract skeleton

- Problem: national portrayal rules are authoritative but commonly remain document-bound.
- Method: reviewed facts are compiled into a typed property graph joined to a versioned rendering
  profile, then queried by an agent that returns evidence-bearing decisions and MapLibre layers.
- Demonstration: five frozen Taiwan NLSC112V5.4 scenes at 1:1,000 test distinct capabilities.
- Current evidence: deterministic development tasks, repeated RC1 execution, explicit abstention,
  and portable package verification.
- Boundary: no claim of autonomous authoritative production; expert review and held-out evaluation
  remain required.

## Section outline

1. **Introduction** — document-bound authority, execution gap, research question, contributions.
2. **Related work** — digital cartographic specifications, knowledge graphs, GraphRAG, agentic GIS,
   portrayal standards, reproducible geospatial benchmarks.
3. **Authority and evidence model** — candidate/review/executable states, versioning, provenance,
   licence and redistribution boundaries.
4. **System design** — extraction, typed graph, guarded retrieval, portrayal agent, style compiler,
   map/evidence interface.
5. **Five-scene demonstration** — why each scene tests a different capability and how all five use
   one pipeline.
6. **Evaluation protocol** — task families, evidence metrics, graph-path completeness, abstention,
   repeated execution, browser checks, and portable-package verification.
7. **Results** — report only versioned development results; separate deterministic controls from
   future named-model evaluation.
8. **Limitations and threats to validity** — small reviewed slice, expert sign-off, held-out data,
   language and jurisdiction scope, symbol-implementation fidelity, PMTiles release boundary.
9. **Reproducibility and governance** — manifests, checksums, data schemas, human approval points,
   release exclusions, and change control.
10. **Conclusion and roadmap** — move from review candidate to expert-reviewed benchmark and public
    research release.

## Claim-to-evidence matrix

| Candidate claim | Current evidence | Publication gate |
|---|---|---|
| Decisions remain source-auditable | page/hash/review fields, typed graph path, execution log | independent source and schema review |
| One architecture handles five portrayal situations | frozen five-scene contract and verifier | cartographer review of scene validity |
| Guardrails prevent unsupported execution | scale/profile abstention controls | expand adversarial and out-of-domain tests |
| The implementation is reproducible | deterministic assets, checksums, RC1 logs, portable verifier | independent clean-room reproduction |
| Full NMA improves over simple controls on the development set | versioned development benchmark | sealed held-out set and named baseline runs |

## Roadmap gates

1. Cartographer sign-off on reviewed observations and symbol implementations.
2. Seal held-out questions and portrayal cases before model evaluation.
3. Run named, versioned baselines with configuration and cost/latency records.
4. Obtain independent package reproduction and address reported discrepancies.
5. Confirm PMTiles redistribution terms or publish a clearly licensed replacement dataset.
6. Release public artifacts and submit the paper only after the preceding gates are recorded.

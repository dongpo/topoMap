# NMA v0.2 completion audit

Audit date: 16 July 2026

| Objective | Evidence | Status |
|---|---|---|
| Existing repository inspection | `dongpo/topoMap` cloned; static demos and Pages workflow preserved | complete |
| Authoritative source access | 11 Drive PDFs inventoried; four relevant PDFs hashed and inspected; evidence pages 8, 9, 14, 22, 34, 35, and 39 visually verified | complete for bounded RIVERL profile |
| Real geospatial package inspection | 12 RIVERL/RIVERA layer sets extracted read-only from the supplied archive; archive hash frozen | complete, private source not redistributed |
| End-to-end validation demo | 13 rules -> Shapefile -> four defects -> page evidence -> approval -> one safe repair -> revalidation | complete for controlled fixture |
| NMA-Bench v0.1 | 31 tasks, four baselines, frozen issue keys, fingerprints, per-category results | complete as harness/ablation benchmark |
| Open architecture | Apache-2.0 code, GDAL/OGR, transparent CSV/VRT fixtures, CLI, API, Docker, CI, JSON contracts | complete |
| FOSS4G alignment | open stack, reproducible commands, source/data boundary, community-extension plan, Pages demo | documented |
| Automated verification | unit/integration tests, lint, format, package, container configuration, artifact generation | complete locally |
| Domain-expert ground-truth sign-off | machine-readable interpretation and `RIVERID`/`RIVERLID` observation reviewed by an authority expert | pending |
| Named-model baselines | frozen LLM/document-RAG runs through answer-key-isolated adapter | pending endpoint/model choice |
| Held-out evaluation | sealed cases not used during implementation | pending expert curation |

## Defensible claim

NMA v0.2 is an open, reproducible specification-aware validation architecture that executes a
bounded set of page-grounded Taiwan RIVERL rules on controlled Shapefiles, localizes defects,
attaches provenance, and prevents silent authoritative repair.

## Claims not yet permitted

- readiness for deployment by a National Mapping Authority;
- proof that the supplied archive contains an official production defect;
- superiority over named LLM or RAG systems;
- generalization to all layers, scales, countries, and production workflows;
- autonomous repair or publication of authoritative map data.

## Remaining scientific gates

1. Authority expert confirms rule transcription, scope, severity, and the schema-name discrepancy.
2. Freeze development and held-out task splits.
3. Run named model baselines with exact model/server/prompt versions and repeated trials.
4. Report confidence intervals, error taxonomy, and disagreements rather than one opaque score.
5. Conduct user evaluation with national-mapping professionals.

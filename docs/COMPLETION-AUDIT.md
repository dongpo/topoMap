# NMA v0.2 completion audit

Audit date: 16 July 2026

| Objective | Evidence | Status |
|---|---|---|
| Authoritative portrayal source | 83-page PDF locally verified as SHA-256 `1f9c4457…fa2620`; pages 11, 50, 60–62, 69 rendered | complete |
| Executable knowledge | 10 reviewed-gate observations compile to 44 nodes and 85 edges | implemented; expert sign-off pending |
| GraphRAG agent | human questions and symbol decisions return complete evidence paths | implemented and tested |
| Landmark decisions | hydrant, fish pond, police, six school types, post office and exception | implemented for NLSC112V5.4 subset |
| Vector-tile map | 133 generated MapLibre layers over the existing PMTiles source | implemented; clean-browser visual QA pending hosted build |
| Evidence governance | document, version, page, text, rule ID, graph path and review status embedded | implemented |
| NMA-Bench v0.1 | 21 separated human-question, symbol-decision and map-compilation tasks | implemented as development regression benchmark |
| Supporting validation | GDAL/OGR RIVERL workflow and 31-task regression suite | preserved |
| Automated verification | 26 tests, lint, JSON, SVG, JavaScript syntax and diff checks | complete locally |
| Official glyph verification | hydrant, fish pond, police, school and post geometry/dimensions visually compared; incorrect police/hydrant implementations replaced | complete technically; independent cartographer sign-off pending |
| Independent ground truth | two experts review observations, symbols and benchmark answers | pending |
| Held-out/named-model study | sealed test set and frozen LLM/PDF-RAG runs | pending |

## Defensible claim

NMA v0.2 demonstrates a reproducible, open mechanism that compiles a bounded set of
authoritative-source-derived portrayal observations into executable graph knowledge, retrieves
evidence-backed symbol decisions, and compiles them into auditable MapLibre vector-tile layers.

## Claims not yet permitted

- independent cartographer acceptance of the open symbol implementations;
- authority-wide or cross-country accuracy;
- deployment readiness for a National Mapping Authority;
- superiority over named LLM or production PDF-RAG systems;
- autonomous authoritative map production;
- publication-grade accuracy from the 21-task development set.

## Remaining scientific gates

1. Obtain independent cartographer acceptance of the open symbol implementations.
2. Have two experts independently review records and answers; adjudicate disagreements.
3. Seal a larger held-out benchmark before changing retrieval/prompts.
4. Run named model and PDF-RAG baselines with frozen versions and repeated trials.
5. Test the hosted PMTiles demo in a clean browser and retain an offline recording.

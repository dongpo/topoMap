# NMA v0.2 completion audit

Audit date: 16 July 2026

| Objective | Evidence | Status |
|---|---|---|
| Authoritative portrayal source | Drive PDF 01 text accessed; version and six pages recorded | text extraction complete; local file hash and visual cells pending |
| Executable knowledge | 10 reviewed-gate observations compile to 44 nodes and 85 edges | implemented; expert sign-off pending |
| GraphRAG agent | human questions and symbol decisions return complete evidence paths | implemented and tested |
| Landmark decisions | hydrant, fish pond, police, six school types, post office and exception | implemented for NLSC112V5.4 subset |
| Vector-tile map | 133 generated MapLibre layers over the existing PMTiles source | implemented; clean-browser visual QA pending hosted build |
| Evidence governance | document, version, page, text, rule ID, graph path and review status embedded | implemented |
| NMA-Bench v0.1 | 21 separated human-question, symbol-decision and map-compilation tasks | implemented as development regression benchmark |
| Supporting validation | GDAL/OGR RIVERL workflow and 31-task regression suite | preserved |
| Automated verification | 25 tests, lint, JSON, JavaScript syntax and diff checks | complete locally |
| Official glyph verification | PDF symbol cells extracted and compared to Canvas implementations | pending local PDF copy and cartographer review |
| Independent ground truth | two experts review observations, symbols and benchmark answers | pending |
| Held-out/named-model study | sealed test set and frozen LLM/PDF-RAG runs | pending |

## Defensible claim

NMA v0.2 demonstrates a reproducible, open mechanism that compiles a bounded set of
authoritative-source-derived portrayal observations into executable graph knowledge, retrieves
evidence-backed symbol decisions, and compiles them into auditable MapLibre vector-tile layers.

## Claims not yet permitted

- exact visual equivalence between demo glyphs and official PDF symbols;
- authority-wide or cross-country accuracy;
- deployment readiness for a National Mapping Authority;
- superiority over named LLM or production PDF-RAG systems;
- autonomous authoritative map production;
- publication-grade accuracy from the 21-task development set.

## Remaining scientific gates

1. Place PDF 01 locally, hash it, render pages 11, 50, 60–62, and 69, and crop official symbol cells.
2. Compare/replace the implementation glyphs and obtain cartographer acceptance.
3. Have two experts independently review records and answers; adjudicate disagreements.
4. Seal a larger held-out benchmark before changing retrieval/prompts.
5. Run named model and PDF-RAG baselines with frozen versions and repeated trials.
6. Test the hosted PMTiles demo in a clean browser and retain an offline recording.

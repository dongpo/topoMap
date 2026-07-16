# FOSS4G Hiroshima 2026 demonstration plan

Talk: **National Map Agent: An Open Geospatial Architecture for Knowledge Graph–Driven GeoAI**.

## Claim to demonstrate

An open geospatial agent can turn a reviewed subset of a national portrayal specification into
executable graph knowledge, use that graph to choose landmark symbols, compile those decisions into
vector-tile styles, and show the PDF evidence for every rendered decision.

The talk does not claim autonomous authoritative production. The demonstration establishes a
bounded, reproducible research mechanism.

## Live narrative

1. Open the authoritative 1:1,000 portrayal PDF at the fire-hydrant, school, fish-pond, police, and
   post-office pages.
2. Show that extracted candidates are not automatically trusted; only reviewed observations enter
   executable knowledge.
3. Open the property graph and trace one path:
   `FeatureType → PortrayalRule → Symbol → SourceObservation → DocumentSection`.
4. Ask: “According to NLSC112V5.4, what is the code for an elementary school?”
5. Show answer `9920103`, page 61, and the graph path. Contrast this with the old manually labelled
   map, which used a different school-code interpretation.
6. Ask the agent to portray a post office, then show the large-detached-building exception selecting
   text-only annotation.
7. Open `nmaAgentDemo.html`: MapLibre loads the PMTiles vector map and graph-compiled layers for
   landmarks, fire hydrants, and fish ponds.
8. Click a rendered feature and show the embedded rule ID, PDF page, graph path, and review status.
9. Finish with the 21-task human-question/symbol/map benchmark and its ablation table.

Keep a screen recording and checked-in benchmark result as offline fallbacks.

## Why this follows the FOSS4G path

| FOSS4G value | Concrete NMA implementation |
|---|---|
| Open source | Apache-2.0 code, tests, CI, inspectable graph and benchmark |
| Open geospatial execution | MapLibre GL JS, PMTiles vector tiles, GDAL/OGR supporting validators |
| Reproducibility | reviewed JSONL → graph compiler → style compiler → frozen scores |
| Interoperability | portable property graph, MapLibre style JSON, HTTP JSON/OpenAPI, CLI |
| Inspectability | every map layer carries rule, page, evidence, and graph path metadata |
| Framework independence | no Agno/LangGraph requirement; adapters can call the same NMA APIs |
| Community extension | another country supplies its own documents, reviewed records, profile, and tasks |
| Responsible openness | official PDFs referenced rather than redistributed; uncertainty remains visible |

The contribution is not “an LLM drew a map.” It is an open bridge from authoritative knowledge to
auditable open-source geospatial software.

## Demonstration assets

- `nmaAgentDemo.html`: question, vector map, evidence and graph-path panel;
- `data/knowledge/portrayal-graph.json`: executable knowledge;
- `artifacts/portrayal/maplibre-layers.json`: reproducibly generated vector-tile style layers;
- `benchmark/portrayal/`: public questions, separate ground truth, manifest;
- `artifacts/benchmark/portrayal-results.json`: locally reproduced result and fingerprint;
- earlier RIVERL/GDAL validation workflow as a supporting deterministic tool example.

## Scientific gates before the conference

1. Obtain a local copy of the portrayal PDF and extract/rasterize official symbol cells.
2. Replace or visually compare implementation glyphs and record cartographer acceptance.
3. Have at least two independent experts review the 10 current observations.
4. Expand and seal a held-out benchmark.
5. Run named open-model and PDF-RAG baselines with immutable version metadata.
6. Test the hosted demo in a clean browser with the PMTiles source cached as a fallback.

## Community sprint invitation

- add an OSGeo/QGIS client for the portrayal API;
- load the portable graph into Neo4j or an RDF/SHACL representation;
- add an OGC API Processes or pygeoapi adapter;
- contribute another national feature catalogue and portrayal profile;
- add expert-reviewed symbol-image evaluation;
- expand multilingual benchmark questions and ambiguity cases.

# D24 · NMA demonstration Q&A

Status: review candidate

Validated: 2026-08-07 (Asia/Taipei)

Scope: public technical Q&A only; presentation slides, speaker notes, and PDF remain owner-controlled.

## One-sentence answer

NMA turns a bounded set of authoritative portrayal observations into inspectable graph knowledge,
uses that graph to propose a symbol and evidence path, requires human approval for every derived
symbol or layer action, and then compiles the approved result into an auditable MapLibre layer.

## Questions likely to be asked

### 1. What problem does NMA solve?

National-map rules are written for people, while web-map renderers need executable styles. NMA
demonstrates a traceable bridge from a cited specification page to a feature, portrayal rule,
symbol, approval decision, and rendered layer. It is not presented as autonomous authoritative map
production.

### 2. What does the agent actually do in the demonstration?

The agent interprets the user's feature question, retrieves the matching graph path, presents the
specification-derived symbol baseline, proposes bounded natural-language edits as a new version,
waits for explicit approval or rejection, inspects the Shapefile package, and asks again before it
creates a MapLibre layer over the NLSC Taiwan e-Map basemap.

The authoritative baseline remains immutable. A user edit creates a derived preview; it does not
rewrite the official rule or asset.

### 3. Which LLM is used for the multi-turn conversation?

The local agent server currently defaults to `gpt-5.6-terra` when an OpenAI API key is available.
The model is an intent and tool-routing adapter: it may translate natural language into one of the
bounded application actions, but it does not own the facts, graph traversal, approval state, or
layer execution. Without an API key or when the remote call is unavailable, the demo uses a
deterministic local router for the supported phrases.

Every sensitive transition is checked again by application code. A language-model response alone
cannot approve a symbol or create a layer.

### 4. Is the knowledge graph only a picture?

No. The checked-in portable property graph connects `FeatureType`, `PortrayalRule`, `Symbol`,
`SourceObservation`, and the exact evidence page with typed edges. Retrieval returns the complete
path used by the decision, and compiled MapLibre layers carry the rule ID, document version, page,
and graph identifiers in their metadata.

### 5. Does the graph contain all 42 PMTiles capabilities?

Not yet, and the demo must not imply that it does. The 42-entry catalog inventories what the
existing PMTiles implementation can display:

- 5 entries are evidence-backed;
- 4 entries have graph evidence but an unresolved catalog conflict;
- 28 entries are implementation-only;
- 5 entries are style variants.

Therefore 42 means registered implementation capability, while only 9 entries currently have a
graph-evidence relationship and only 5 are clean evidence-backed examples. Expanding the graph
requires the same source extraction, review, compilation, and validation gates used for the first
subset.

### 6. Why use five different scenes?

They expose different agent abilities through one pipeline:

| Scene | Capability demonstrated | Evidence |
|---|---|---|
| School | versioned retrieval, symbol workshop, approval, and map execution | `9920103`, p. 61 |
| Fire hydrant | exact symbol selection and dimensions | `9350906`, p. 11 |
| Police | alias resolution and labelled portrayal | `9910603`, p. 60 |
| Fish pond | geometry-aware fill, outline, and companion icon | `9740100`, p. 50 |
| Post office | conditional exception and explicit abstention boundary | `9950201`, p. 69 |

The five scenes are not a technical limit. They are the reviewed, frozen demonstration slice.

### 7. What happens after the user approves a symbol?

Approval advances only the derived symbol version. When the user explicitly asks to build a
layer, NMA first inspects the Shapefile sidecars, driver, CRS, geometry, feature count, and field
mapping. It then shows the proposed Shapefile → GDAL/OGR → GeoJSON → MapLibre path. A separate
approval creates the source and layer and records provenance, approved symbol version, feature
code, rule ID, approval source, and basemap.

### 8. Why is the NLSC electronic map used as the basemap?

It gives the Taiwan feature layer an official geographic context while keeping portrayal evidence
and basemap delivery separate. The local full demo streams the NLSC `EMAP` WMTS without bulk
caching. The bounded public Pages release deliberately uses evidence-only mode because PMTiles
redistribution terms have not been confirmed.

### 9. What evidence supports the five answers?

The authoritative source is the 83-page *一千分之一地形圖圖式規格表*, version
`NLSC112V5.4`, dated 2024-02-28. The Drive source was re-opened on 2026-08-07 and its text confirms
the five codes and pages above. The repository also preserves source hashes, reviewed-gate
observations, graph nodes and edges, symbol assets, compiled layers, and deterministic tests.

### 10. How reliable is the result?

The current evidence proves that the bounded architecture behaves as specified and that the same
fact survives from retrieval through portrayal to a map action. It does not prove authority-wide
accuracy. NMA-Bench v0.1 is a 21-task development regression set, not a held-out named-model
evaluation.

### 11. What does NMA do when it lacks evidence?

It abstains or labels the capability `implementation-only`; it does not present an existing
renderer as an authoritative portrayal decision. Unsupported profile or scale combinations also
abstain before a rule is used. Catalog conflicts remain visible rather than being silently merged.

### 12. What is still incomplete?

- independent cartographer and two-expert review;
- a sealed held-out benchmark and named-model comparisons;
- expansion of reviewed graph evidence beyond the current bounded subset;
- confirmation of PMTiles redistribution terms;
- publication of the Agentic v0.3 candidate to the public Pages site;
- a DOI or archival release identifier.

These are declared gates, not hidden capabilities.

## Evidence references

- [Architecture](ARCHITECTURE.md)
- [Benchmark boundary](BENCHMARK.md)
- [Completion audit](COMPLETION-AUDIT.md)
- [Public delivery and link audit](D24-PUBLIC-DELIVERY.md)
- [Authoritative NLSC112V5.4 source](https://drive.google.com/file/d/1KQN1GCwVPFSms3IUi4pmNqM4ru3TYVrZ/view)

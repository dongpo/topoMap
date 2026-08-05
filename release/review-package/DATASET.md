# Dataset, provenance, licence, and schema record

## Release identity

| Field | Value |
|---|---|
| Package | `nma-v0.2-review-package` |
| Demo contract | `1.0` |
| Portrayal profile | `tw-nlsc-1000-NLSC112V5.4` |
| Specification version | `NLSC112V5.4` |
| Map scale | `1:1,000` |
| Frozen scenes | school, fire hydrant, police, fish pond, post office |
| Reviewed observations | 10 |
| Release state | review candidate; not publication-grade authority |

## Asset catalogue

| Asset | Provenance and version | Schema/format | Licence or release status |
|---|---|---|---|
| `data/sources/authoritative-sources.json` | Source URI, pages, dates, and locally verified SHA-256 for the official evidence | JSON record | Metadata included; source documents referenced, not redistributed |
| `data/extraction/portrayal-records.jsonl` | Ten human-reviewed, page-linked observations derived from NLSC112V5.4 | JSON Lines; reviewed observation contract | Review artifact; independent expert and publication review remain required |
| `data/knowledge/portrayal-profile.json` | Versioned implementation boundary for scale 1:1,000 | `schemas/executable-profile.schema.json` | Included for reproducibility under repository code terms |
| `data/knowledge/portrayal-graph.json` | Deterministic compilation of reviewed records plus the executable profile | Portable property-graph JSON | Included for review and reproduction |
| `data/demo/five-scene-demo.json` | Frozen D12–D17 demo inputs, expected outputs, evidence fields, and negative controls | `schemas/five-scene-demo.schema.json`; contract `1.0` | Included for review and reproduction |
| `artifacts/portrayal/maplibre-layers.json` | Deterministically compiled evidence-bearing MapLibre layers | MapLibre style-layer JSON | Included for review and reproduction |
| `assets/symbols/nlsc112v5.4/` | Open SVG/Canvas implementations checked against cited source pages | SVG plus manifest JSON | Apache-2.0 implementation; official PDF crops are not included |
| `benchmark/portrayal/` | Development tasks and separate expected answers | JSON/JSON Lines | Development evidence only; not a sealed held-out evaluation |
| `artifacts/presentation/nma-foss4g-presentation-v0.9.pptx` | D18 five-scene narrative expanded with D20 release, benchmark, roadmap, and paper gates | Office Open XML presentation | Review candidate |

Repository code is Apache-2.0. Synthetic validation fixtures are CC0-1.0. No licence is asserted
for the authoritative PDFs or the existing PMTiles archive.

## Provenance chain

1. The official PDF is identified by URI, version, effective date, local SHA-256, and cited pages.
2. Extraction creates candidates that are never executable by default.
3. Human-reviewed records carry page, source hash, review status, and source text.
4. A deterministic compiler joins reviewed facts to a versioned rendering profile.
5. The agent returns a symbol decision, graph path, evidence record, and execution log.
6. The style compiler emits MapLibre layers with rule, evidence, graph-path, and execution metadata.
7. `VERIFY.py` reruns the five frozen decisions and both abstention controls from the packaged data.

## Five-scene expected outputs

| Scene | Feature code | Action | Evidence page | Primary source layer |
|---|---:|---|---:|---|
| School | `9920103` | `draw_symbol` | 61 | `J01_MARK` |
| Fire hydrant | `9350906` | `draw_symbol` | 11 | `J01_BUILD` |
| Police | `9910603` | `draw_symbol` | 60 | `J01_MARK` |
| Fish pond | `9740100` | `draw_symbol` | 50 | `J01_WATERA` |
| Post office, large detached building | `9950201` | `text_only` | 69 | `J01_MARK` |

The negative controls must abstain for an unsupported 1:5,000 scale and for an unknown profile.

## Exclusions and limitations

- `out1120902.pmtiles` is repository-only until redistribution terms are confirmed.
- The official PDF is not redistributed.
- Browser playback, public hosting, and network availability are outside this portable verifier.
- The ten observations cover only the approved demo slice, not a national specification in full.
- Independent cartographer sign-off and a sealed held-out benchmark remain publication gates.

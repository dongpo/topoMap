# NMA RC1 five-scene runbook

This runbook freezes one demonstration—not five separate products. Every scene uses profile
`tw-nlsc-1000-NLSC112V5.4`, scale 1:1,000, the same reviewed records, portable portrayal graph,
agent, MapLibre compiler, browser runner, and evidence panel.

The executable source of truth is [`data/demo/five-scene-demo.json`](../data/demo/five-scene-demo.json).
It records the exact prompt, feature code, expected decision, primary map layer, evidence page,
timing, asset paths, licence boundary, and output artifacts for all five scenes. The schema is
[`schemas/five-scene-demo.schema.json`](../schemas/five-scene-demo.schema.json).

## Deterministic setup and reset

From a clean checkout with Python 3.11 or later:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
make demo-reset
make demo-scenes
make test
python3 -m http.server 8080
```

Open `http://127.0.0.1:8080/nmaAgentDemo.html`. `make demo-reset` recompiles the graph from reviewed
records and regenerates the evidence-bearing MapLibre style; it does not fetch or replace source
evidence. Re-run the same command before each rehearsal to restore the generated artifacts.

## Frozen live sequence

| Order | Scene | Prompt | Expected proof | Budget |
|---:|---|---|---|---:|
| 1 | School | 依 NLSC112V5.4，小學的地形代碼是什麼？請套用 1:1,000 圖式並顯示證據。 | `9920103`, page 61, `J01_MARK`, school + `MARKNAME1` | 90 s |
| 2 | Fire hydrant | 消防栓的代碼與圖式是什麼？ | `9350906`, page 11, `fire-hydrant`, 2 × 2.5 mm | 30 s |
| 3 | Police | 警察局、分駐所或派出所應如何表示？ | `9910603`, page 60, symbol + name label | 30 s |
| 4 | Fish pond | 養殖池應使用哪個圖式？ | `9740100`, page 50, `J01_WATERA`, fill/outline + fish icon | 30 s |
| 5 | Post office | 大型獨幢郵局有什麼圖式例外？ | `9950201`, page 69, `text_only`; symbol layer hidden, label retained; unsupported scale/profile abstains | 30 s |

Use the remaining 60 seconds of the five-minute segment to introduce the source/review boundary
and close with the bounded claim. NMA demonstrates a reproducible, auditable mechanism; it does not
claim autonomous authoritative map production. The PMTiles file remains an existing demo dataset;
confirm its redistribution terms before a public release.

## Shared output contract

Each selected decision must include the document, profile version, page, evidence text and URI,
source SHA-256, review status, and complete graph nodes/edges. Each primary MapLibre layer must carry
`nma:featureCode`, `nma:featureName`, `nma:ruleId`, `nma:evidence`, `nma:graphPath`, and
`nma:executionLog` metadata. Selected decisions also expose a deterministic execution/provenance
log. For the post-office exception this log records the evaluated condition, requested attributes,
selected `text_only` action, page 69 evidence link, source hash, and review status.

`make demo-scenes` validates these fields, all five exact decisions, their primary map layers, the
single shared profile/graph/runner paths, and both unsupported-scale and unsupported-profile
abstentions. In the browser, `text_only` hides the post symbol layer while retaining the name-label
layer. A sixth scene or a second profile fails the frozen contract.

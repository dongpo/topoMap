# NMA RC1 five-scene soak record

This record covers D14 reliability testing of the feature-complete five-scene baseline. It does
not reopen feature scope. The machine-readable run output is
[`artifacts/soak/five-scene-soak.json`](../artifacts/soak/five-scene-soak.json), and its schema is
[`schemas/five-scene-soak-report.schema.json`](../schemas/five-scene-soak-report.schema.json).

## Protocol

Run from the repository root:

```bash
make demo-soak
python3 -m http.server 8080
```

The automated phase performs 20 repetitions. Every repetition recompiles the frozen portrayal
graph and MapLibre style, executes the five scenes in the fixed order, checks both abstention
controls, and verifies all 14 freeze artifacts. The browser phase requires ten clean reloads of
`http://127.0.0.1:8080/nmaAgentDemo.html`; each reload must execute school, fire hydrant, police,
fish pond, and post office in order with zero console errors or warnings.

## Automated soak result — 2026-08-05

| Measure | Result |
|---|---:|
| Clean-reset repetitions | 20 |
| Passed | 20 |
| Failed | 0 |
| Pass rate | 100% |
| Median total runtime | 17.420 ms |
| P95 total runtime | 18.475 ms |
| Maximum total runtime | 22.048 ms |
| Blocking defects | 0 |

Environment: Python 3.13.5, Darwin arm64. Every run returned five scenes, two negative controls,
and 14 verified artifacts.

## Browser soak result — 2026-08-05

| Measure | Result |
|---|---:|
| Clean-reload rounds | 10 |
| Passed | 10 |
| Failed | 0 |
| Median full-sequence runtime | 1.651 s |
| P95 full-sequence runtime | 1.781 s |
| Maximum full-sequence runtime | 1.781 s |
| Console errors | 0 |
| Console warnings | 0 |

Every round reloaded `nmaAgentDemo.html`, waited for a selected scene, then executed school,
fire hydrant, police, fish pond, and post office in that order. Each result preserved its expected
feature code, PDF page, evidence chain, and action. The post-office result correctly used
`text_only`; its code remains visible in the evidence panel rather than the natural-language result.

## Defect triage

| Observation | Classification | Owner / next action |
|---|---|---|
| Hosted JavaScript, glyph, and PMTiles dependencies | Presentation-impacting | D15 / GEO-71 — package offline dependencies |
| Backup recording and screenshots absent | Presentation-impacting | D16 / GEO-72 — capture backup assets |
| Stable public demo URL not frozen | Deferred | D17 / GEO-73 — stable Demo RC1 gate |
| Independent cartographer sign-off absent | Deferred | Publication gate — expert review before publication claims |

No blocking defect was observed in the automated or browser soak. If a later browser or automated run fails,
it becomes blocking immediately and must record an owner, reproduction, next action, fix evidence,
and a complete rerun before release.

## Recovery sequence

1. Run `make demo-reset`.
2. Run `make demo-freeze`; stop if any fingerprint differs.
3. Run `make demo-scenes`; confirm five scenes and both abstention controls.
4. Restart the static server from the repository root.
5. Open a clean browser tab, reload, and restart at school.

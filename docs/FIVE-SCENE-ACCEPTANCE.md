# NMA RC1 clean-browser acceptance

This record captures the D12 feature-complete browser gate for the frozen five-scene demo. The
test ran on 2026-08-05 from branch `codex/nma-v0.2-authoritative`, using base commit `5fb2c07` plus
the D12 browser-runtime fixes recorded with this document.

## Clean setup

The repository was served without cache from `http://127.0.0.1:8765/` and opened in a new Codex
in-app browser tab. The page loaded the checked-in portrayal graph and frozen demo contract. The
browser tab was recreated after the fixes so earlier console messages could not contaminate the
final result.

## Acceptance matrix

| Scene/control | Expected browser proof | Result |
|---|---|---|
| School | `9920103`, point, `J01_MARK`, page 61, symbol + label | Pass |
| Fire hydrant | `9350906`, point, `J01_BUILD`, page 11, symbol only | Pass |
| Police | `9910603`, point, `J01_MARK`, page 60, symbol + label | Pass |
| Fish pond | `9740100`, polygon, `J01_WATERA`, page 50, compound portrayal | Pass |
| Post office | `9950201`, page 69, `text_only`, symbol hidden, label visible | Pass |
| Unknown feature | Abstain without evidence; log ends at `feature_lookup` | Pass |
| Unsupported scale | Abstain at `scale_guard` in the frozen contract/agent test | Pass |
| Unsupported profile | Abstain at `profile_guard` in the frozen contract/agent test | Pass |
| Map feature click | Return through the shared decision and evidence renderer | Pass |
| Browser console | No errors or warnings after a clean reload and full matrix | Pass |

Unsupported scale and profile are contract/API controls because the frozen live UI intentionally
does not expose profile-switching or scale-override controls. They are exercised by
`make demo-scenes` and the automated browser-contract tests over the same request schema.

## Blocking defects found and fixed

1. Companion symbol layers inherited a polygon `paint` member with an undefined value. MapLibre
   rejected the fish-pond icon layers. The browser compiler now removes `paint` from companion
   symbol layers before adding them.
2. Label layers required a style `glyphs` endpoint. The browser style now declares the pinned
   Protomaps glyph endpoint, allowing school, police, and post-office text layers to load.
3. Visibility updates could target a layer rejected during style validation. The runner now checks
   `map.getLayer(layer.id)` before applying a visibility change.

## Network dependencies and offline gaps at D13

The feature-complete build currently requires:

- `unpkg.com/maplibre-gl@4.7.0` for MapLibre CSS and JavaScript;
- `unpkg.com/pmtiles@4.3.0` for the PMTiles protocol;
- `cdn.protomaps.com/fonts/pbf/` for label glyphs;
- `dongpo.github.io/topoMap/out1120902.pmtiles` for the current remote tile archive;
- a local or hosted HTTP origin for the HTML, graph JSON, and demo-contract JSON.

The repository contained a 9.2 MB local `out1120902.pmtiles`, but the D13 runner still pointed to
the hosted archive and did not cache MapLibre, PMTiles, or glyphs. It was not a complete offline
package. The deterministic five-scene contract, pytest suite, and benchmark were the tested
semantic fallback.

## D15 reliability follow-up

D15 changed the runner to the local PMTiles archive, added a pinned runtime service-worker cache,
and added an evidence-only degraded mode. See [`OFFLINE-RUNTIME.md`](OFFLINE-RUNTIME.md). A cold
cache still needs one online preflight to render the map; without it, the reviewed five-scene
decision and evidence path remains available without interactive map rendering. Recording and
screenshots remain D16 work.

The project does not yet publish `nmaAgentDemo.html` through GitHub Pages, so a stable public demo
URL remains an operational gap rather than a feature-complete browser blocker.

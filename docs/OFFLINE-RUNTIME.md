# NMA Demo RC1 offline and degraded runtime

D15 reduces conference-network dependence without changing the frozen five-scene feature scope.
The machine-readable inventory is
[`data/demo/offline-runtime.json`](../data/demo/offline-runtime.json).

## Runtime layers

| Layer | Strategy | Offline behavior |
|---|---|---|
| Graph, contract, HTML | Repository-local | Available from the local static server |
| Vector tiles | Repository-local `out1120902.pmtiles` | No external network request |
| MapLibre 4.7.0 | Pinned URL + service-worker cache | Reused after online preflight |
| PMTiles JS 4.3.0 | Pinned URL + service-worker cache | Reused after online preflight |
| Protomaps glyph PBF | Cache on use | Previously rendered glyph ranges are reused |
| Evidence-only fallback | Repository-local | Five scenes remain executable without the map runtime |

The service worker stores the local PMTiles archive once and implements byte-range responses from
that cached file. This keeps the documented Python preview command compatible with PMTiles even
when the simple HTTP server does not implement Range requests itself.

## Preflight

Run from the repository root:

```bash
make demo-offline
python3 -m http.server 8080
```

Open `http://127.0.0.1:8080/nmaAgentDemo.html` once while online. Confirm the runtime line reads
`Map ready · local PMTiles · pinned runtime cache enabled`, then disable external networking and
reload. The five scenes should still render using the cached map runtime and local tile archive.

Test the deterministic fallback at
`http://127.0.0.1:8080/nmaAgentDemo.html?mode=degraded`. It deliberately skips MapLibre and
PMTiles JavaScript. School, fire hydrant, police, fish pond, and post office must still return their
feature code/action, evidence page, source hash, graph path, and execution log.

## Verification result — 2026-08-05

| Mode | Result | Console |
|---|---|---:|
| Normal cached runtime + local PMTiles range adapter | Passed | 0 errors, 0 warnings |
| Forced evidence-only fallback | 5/5 scenes passed | 0 errors, 0 warnings |

The normal test rendered the interactive map through the local PMTiles archive. The degraded test
executed school, fire hydrant, police, fish pond, and post office in order and preserved each
expected code, action, PDF page, and evidence chain.

## Remaining non-blocking limitations

- A cold browser cache with no network cannot obtain MapLibre or PMTiles JavaScript. It enters the
  evidence-only fallback; D16/GEO-72 owns the online-preflight runbook and backup capture.
- Confirm redistribution terms for `out1120902.pmtiles` before publishing a distributable offline
  bundle. This is a publication gate, not a live-demo blocker.

# NMA v0.2 stable five-scene Demo RC1

This is the D17 release gate for the frozen school, fire-hydrant, police, fish-pond, and
post-office demonstration. The machine-readable release record is
[`data/demo/stable-rc1.json`](../data/demo/stable-rc1.json), validated with `make demo-rc1`.

## Release identity

- Release: `nma-demo-v0.2-rc1`
- Repository: `dongpo/topoMap`
- Branch: `codex/nma-v0.2-authoritative`
- Frozen executable baseline: `ff408b319a6945a14cd7832ea0597f47b0ce16cf`
- Intended annotated tag: `nma-demo-v0.2-rc1`

The D17 commit adds release evidence and verification only. It does not change the five-scene
runner, graph, source dataset, symbol decisions, or evidence claims.

## Stable gate result

| Gate | Result |
|---|---:|
| Automated clean-reset soak | 20/20 passed; 0 defects |
| Cached live-map browser soak | 10/10 passed; 0 console errors/warnings |
| D15 normal + evidence-only modes | 2/2 passed |
| D16 recorded/screenshot fallback | Human-approved in GEO-72 |
| D16 portable backup checksums | Passed without repository access |
| Unresolved blocking defects | 0 |

The D17 browser test intentionally ran while the origin server was unavailable. The pinned D15
cache reloaded the active map ten times, and every round returned all five exact feature codes,
PDF pages, actions, graph paths, and governance fields. Median full-sequence time was 1.667 seconds;
the maximum was 1.699 seconds. The current automated soak median was 18.235 ms across 20 clean
resets.

## Versioned environment and assets

The RC1 manifest fingerprints the exact demo contract, feature-freeze manifest, executable graph,
HTML runner, service worker, local PMTiles archive, D15 offline manifest, D16 backup manifest and
ZIP, both D17 soak records, live and backup runbooks, `pyproject.toml`, and the CI workflow.

Supported reproduction baseline:

- Python 3.11 or later; local acceptance used Python 3.13.5 on Darwin arm64;
- CI uses `ubuntu-latest`, Python 3.11, and the distribution GDAL package;
- local acceptance used GDAL 3.11.0;
- MapLibre GL JS 4.7.0 and PMTiles JS 4.3.0 are pinned in the D15 runtime cache;
- label glyphs are cached on use after the online preflight.

Run the complete gate from the repository root:

```bash
make demo-reset
make demo-scenes
make demo-freeze
make demo-soak
make demo-offline
make demo-backup
make demo-rc1
make test
```

Use [`FIVE-SCENE-DEMO.md`](FIVE-SCENE-DEMO.md) for the live sequence and
[`../artifacts/presentation/nma-demo-backup/RUNBOOK.md`](../artifacts/presentation/nma-demo-backup/RUNBOOK.md)
for the two-minute fallback ladder.

## Risk disposition

Resolved for RC1:

- cold-cache risk is mitigated by preflight, pinned cache, and evidence-only fallback;
- backup video, screenshots, evidence panels, player, and restart runbook are complete;
- browser repeatability is revalidated against the stable baseline.

Non-blocking release gates remain explicit:

- confirm PMTiles redistribution terms before publishing the portable archive;
- obtain independent cartographer sign-off before publication-grade claims;
- the GitHub Pages workflow deploys from `main`, so the public demo URL remains unavailable until
  PR #1 is merged or a separate deployment is explicitly approved.

These gates do not change RC1 executable behavior or its conference fallback. They must not be
represented as complete when publishing externally.

## Change control after D17

Only a critical defect may change executable behavior. Every such change requires a Linear issue,
reproduction steps, impact statement, approved fix, full automated and browser reruns, updated
fingerprints, a replacement RC tag, and explicit human approval. New scenes, a second portrayal
profile, new factual claims, or unrelated presentation polish are prohibited in RC1.

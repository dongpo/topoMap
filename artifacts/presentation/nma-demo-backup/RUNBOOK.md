# NMA v0.2 presentation backup runbook

This folder mirrors the frozen five-scene D16 build. It is designed to run on the
presentation machine without network or repository access.

## Preflight — before leaving for the venue

1. Copy the entire `nma-demo-backup` folder to the presentation machine.
2. Open `PLAYBACK.html` in Chrome, Edge, Firefox, or Safari.
3. Play the backup video from start to finish and click all five screenshot buttons.
4. Confirm the scene order: School, Fire hydrant, Police, Fish pond, Post office.
5. Confirm the five evidence images open from the `evidence` folder.
6. Run `sh VERIFY-CHECKSUMS.sh` from a terminal if one is available. A terminal is
   not required for playback.

## Normal live start — repository available

From the repository root:

```sh
make demo-reset
make demo-freeze
make demo-scenes
make demo-offline
python3 -m http.server 8080
```

Open `http://127.0.0.1:8080/nmaAgentDemo.html` and confirm the status reads:

`Map ready · local PMTiles · pinned runtime cache enabled`

Run the scenes in the frozen order above. Do not improvise a sixth scene or an
unreviewed factual claim during the presentation.

## Two-minute recovery ladder

1. **Map, tile, or network failure:** keep the local server running and open
   `http://127.0.0.1:8080/nmaAgentDemo.html?mode=degraded`. Confirm the status reads
   `Evidence-only mode · map unavailable · reviewed decisions preserved`.
2. **Local server or repository failure:** open this folder's `PLAYBACK.html` directly,
   press Play, and continue the narration from the matching scene.
3. **Video or browser media failure:** use the five buttons in `PLAYBACK.html` to show
   the frozen screenshots in order.
4. **Browser failure:** open the PNG files in `screenshots` using the operating
   system's image viewer. The `evidence` folder contains the corresponding enlarged
   evidence screens.

The fallback is a presentation mirror, not a separate product mode. It must not be
edited to introduce claims, scene behavior, or evidence that differs from the frozen
build.

## Restart/reset checklist

- Close the failed live tab; do not delete browser data during a presentation.
- Restart the local static server only if the repository is available.
- Reopen the live URL and select School to reset the visible sequence.
- If recovery takes longer than two minutes, stop troubleshooting and use
  `PLAYBACK.html`.
- After the session, record the failure separately; do not alter the D16 bundle.

## Frozen evidence index

| Order | Scene | Code | PDF page | Action |
|---:|---|---:|---:|---|
| 1 | School | 9920103 | 61 | `draw_symbol` |
| 2 | Fire hydrant | 9350906 | 11 | `draw_symbol` |
| 3 | Police | 9910603 | 60 | `draw_symbol` |
| 4 | Fish pond | 9740100 | 50 | `draw_symbol` |
| 5 | Post office | 9950201 | 69 | `text_only` |

Source facts and symbol geometry were visually verified against the locally hashed
NLSC112V5.4 PDF. Independent cartographer sign-off remains pending.

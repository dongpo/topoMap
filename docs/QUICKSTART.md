# NMA v0.2 Stable Demo RC1 quickstart

This guide reproduces only behavior frozen and tested in Stable Demo RC1. It does not publish the
site, merge PR #1, or make publication-grade authority claims.

## 1. Install the reviewed candidate

Requirements: Git and Python 3.11 or later. Poppler/GDAL are not required for the five-scene
portrayal demo; they are needed only for PDF re-extraction or the supporting RIVERL workflow.

```bash
git clone https://github.com/dongpo/topoMap.git
cd topoMap
git switch codex/nma-v0.2-authoritative
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ".[dev]"
```

## 2. Rebuild and verify RC1

```bash
make demo-reset
make demo-rc1
make test
```

Expected result: the deterministic reset and Stable Demo RC1 gate pass with zero unresolved
blocking defects, followed by the Python and formatting checks. The full frozen gate and accepted
environment are recorded in [`STABLE-DEMO-RC1.md`](STABLE-DEMO-RC1.md).

## 3. Start the browser preview

```bash
python -m http.server 8000
```

Open <http://localhost:8000/nmaAgentDemo.html>. Do not open the HTML with a `file://` URL: the
service worker, PMTiles range requests, and pinned runtime cache need an HTTP origin.

On the first online run, select **Preflight online demo** and wait for the ready state. Run the
five cards in order:

| Order | Scene | Frozen result |
|---:|---|---|
| 1 | School | `9920103`, page 61, `draw_symbol` |
| 2 | Fire hydrant | `9350906`, page 11, `draw_symbol` |
| 3 | Police | `9910603`, page 60, `draw_symbol` |
| 4 | Fish pond | `9740100`, page 50, polygon plus companion icon |
| 5 | Post office | `9950201`, page 69, `text_only` for a large detached building |

Each result must show the feature code, decision/action, source page, review status, and complete
graph path. Use [`FIVE-SCENE-DEMO.md`](FIVE-SCENE-DEMO.md) for the exact five-minute narration.

## 4. Recovery and offline behavior

If the live map is unavailable:

1. reload after a successful online preflight to use the pinned cache;
2. switch to the explicit evidence-only mode if map tiles cannot load;
3. use the D16 portable recording/screenshots and its checked-in runbook.

Evidence-only mode is a declared degraded state; it must never appear as a fully live map. See
[`OFFLINE-RUNTIME.md`](OFFLINE-RUNTIME.md) for cache and network details, and
[`../artifacts/presentation/nma-demo-backup/RUNBOOK.md`](../artifacts/presentation/nma-demo-backup/RUNBOOK.md)
for the two-minute fallback ladder.

## 5. Known limits before public release

- The executable subset is 10 reviewed observations for one version/profile and five scenes.
- Independent cartographer review and a sealed held-out benchmark remain open publication gates.
- The PMTiles archive requires redistribution clearance before public hosting.
- GitHub Pages is not the source of truth until the PR is merged or deployment is separately
  approved; validate the local preview and candidate branch first.

These limits are release controls, not hidden failures. The verified RC1 evidence remains in
[`STABLE-DEMO-RC1.md`](STABLE-DEMO-RC1.md).

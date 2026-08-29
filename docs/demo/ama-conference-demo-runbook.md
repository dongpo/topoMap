# AMA conference demo runbook

## Before the session

1. Open the public endpoint and confirm `/health` reports `PASS`, exact model digest
   `845dbda0…b697e`, Ollama `0.32.15`, and GPU preload `true`.
2. Click **Reset**. Confirm the sticky banner says `NO RUN SELECTED` and every stage says `WAITING`.
3. Keep `artifacts/ama-demo/replay/canonical-run/` in the deployed image and verify its manifest.
4. Do not edit the canonical intent.

## Recording or live presentation sequence

1. Reset.
2. Submit the canonical intent and point out the sticky `LIVE CLOUD RUN` banner and fresh run ID.
3. While it runs, show the exact user/normalized/planner distinction.
4. Present the same-question RQ1 cards: LLM-only `2/6`, Text-RAG `3/6`, GraphRAG `6/6` for the
   canonical recorded run. Open details only if time permits.
5. Show the domain KG, retrieved subgraph, and the knowledge-to-action trace.
6. Show 7 resolved and 4 bounded-unresolved constraints, especially unresolved ProductLayer.
7. Read the proposal ID/hash and show proposal validation `PASS`.
8. Show the proposal, authorized, and executed hashes as exactly equal.
9. Show the actual derived map result and immutable source context.
10. Show verification checks and provenance identities.
11. Optionally run the tamper test: changed proposal hash, authorization `DENIED`, no execution,
    no mutation, no output.

The accepted warm AMA cloud run is approximately 16–17 seconds end-to-end. The freshly captured
canonical replay source run was cold and took 49.085 seconds end-to-end, of which 48.519 seconds
was planning. Allow about 3 minutes for the narrated main path and 1 additional minute for the
technical tamper section.

## Failure-safe path

If submission, network, GraphRAG, model, planner, authorization, GIS execution, or verification
fails, stop and read the displayed failure. The UI does not switch modes. Click **Show a previously
verified replay** only after telling the audience:

> Live execution unavailable. Showing a previously verified replay.

Point out the purple `VERIFIED REPLAY` banner and replay identity. Continue the same sequence using
the captured run. Never describe the replay map, timing, proposal, or provenance as fresh.

If replay also fails, keep the explanatory failure state on screen. Do not simulate progress or
use an unlabelled screenshot.

## Reset between audiences

Click **Reset** and confirm:

- no mode is selected;
- stages are `WAITING`;
- proposal, authorization, verification, map, and provenance status are cleared;
- retrieved and action graphs return to their empty prompts; and
- the canonical intent remains available.

Reset is rejected while a live run is active. Wait for the run to complete or fail; do not refresh
and claim a concurrent or previous result as fresh.

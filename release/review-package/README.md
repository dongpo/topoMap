# NMA v0.2 review package

This portable package is the D20 review candidate for National Map Agent v0.2. It reproduces the
five frozen portrayal decisions, verifies their evidence links, and carries presentation v0.9.
It is a review artifact, not a claim of publication-grade cartographic authority.

## Verify in one command

Requirements: Python 3.11 or newer. No third-party Python packages are required.

```bash
python3 VERIFY.py
```

The command verifies every payload checksum, rejects secrets and machine-specific paths, reruns
the school, fire-hydrant, police, fish-pond, and post-office decisions, and checks the two frozen
abstention controls. A passing result reports:

- `status: passed`
- `scene_count: 5`
- `negative_controls: 2`
- `checksum_failures: 0`
- `sensitive_matches: 0`

`make verify` is an equivalent convenience command.

## What is included

- reviewed portrayal records, executable profile, compiled property graph, and MapLibre layers;
- the five-scene contract and the JSON schemas needed to inspect it;
- open symbol implementations and their manifest;
- benchmark task/answer files and the benchmark/research protocols;
- the approved five-scene narrative and FOSS4G presentation v0.9;
- dataset, provenance, licence, roadmap, and paper-skeleton documentation.

See [DATASET.md](DATASET.md) for the exact data boundary and
[PAPER-SKELETON.md](PAPER-SKELETON.md) for the publication path.

## Deliberate release exclusions

`out1120902.pmtiles` is not included because its redistribution terms have not been confirmed.
The official NLSC portrayal PDF is referenced by URI, pages, version, and SHA-256 but is not
redistributed. The verifier therefore checks the auditable five-scene decision/evidence pipeline,
not the browser map archive or a public deployment.

No new demo functionality is introduced by this package. The Stable Demo RC1 implementation and
its approved five-scene sequence remain frozen.

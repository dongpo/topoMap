# ROAD-05 QA and Provenance

## Purpose

ROAD-05 is a read-only, fail-closed verifier for the persisted ROAD-04 execution. It does not
invoke `RoadExecutionEngine`, accept ROAD-04's verdict as an oracle, change the frozen ROAD
semantics, or mutate source/native/runtime geometry. The only persisted ROAD-05 outputs are
deterministic `qa.json` and `provenance.json` records beside the ignored execution state.

## Independent verification path

`nma.road_verification.RoadExecutionVerifier` performs these independent checks:

1. verifies the private archive byte hash and its ignored/untracked/unstaged Git boundary;
2. validates the actual ROAD-01 fixture/evidence, ROAD-02 decision/proposal, and ROAD-03
   approval/authorization with their own canonical contracts;
3. extracts only `K14_ROAD` from the archive into a temporary root;
4. reads and normalizes the three authorized native LineStrings in frozen order;
5. independently projects those features to EPSG:4326 with GDAL/OGR and preserves vertex count;
6. compares reconstructed native and runtime GeoJSON with the persisted ROAD-04 bytes;
7. validates the plan, derived portrayal, bundle, observation, receipt, rollback manifest,
   consumption record, ledger, and tracked ROAD-04 goldens against immutable identities;
8. checks the exact execution artifact set, source/runtime file bindings, road semantics, label
   semantics, shield boundary, and absence of unauthorized geometry operations;
9. emits content-addressed QA and provenance records without generated timestamps or absolute
   paths.

Shared canonical JSON and hash helpers are reused, but ROAD-04's engine, builder methods, and
verdict are not imported.

## Result contracts

`nma.road-qa/1.0` distinguishes:

- `expected-change-verified`;
- `expected-change-missing`;
- `incorrect-change`;
- `unexpected-additional-change`;
- `verification-blocked`.

`nma.road-provenance/1.0` records the actual content-addressed path from the private archive and
reviewed ROAD-01 evidence through the ROAD-04 execution records, ROAD-05 QA, and the verified
artifact set. Records without authored IDs keep `record_id: null`; ROAD-05 does not invent request
or evidence identifiers. Parent hashes preserve the repository's actual binding direction—for
example, the frozen ROAD-02 proposal binds the decision hash.

`nma.road-visual-evidence/1.0` is a separate observation contract. A screenshot hash establishes
which pixels were inspected, but does not become a self-approved golden.

## Visual boundary

The ROAD-04 bundle contains one symbol layer with `symbol-placement: line` and literal `中山街`.
It contains no text offset, halo, font override, overlap override, icon, or paint policy. Its shield
binding remains `9490005`, `road-parallel`, and `semantic_binding_only` with no resolver or asset.

ROAD-05 rendered the actual bundle and runtime GeoJSON in an isolated MapLibre GL JS 4.7.0
harness. The harness supplies only a neutral background and a glyph endpoint needed to observe
the frozen label layer. It does not alter the candidate bundle. The observed render contained one
visible `中山街` label after collision handling, no unrelated features, no extra candidate layer or
source, and no image/shield graphic.

No reviewed independent ROAD visual oracle exists in the repository. Consequently, the exact
pixel status is `evidence_generated_but_no_independent_visual_oracle`. The screenshot proves the
observed render and supports cartographic inspection; it does not independently certify artistic
or pixel-level correctness.

## Offline command

```sh
PYTHONPATH=src python3 scripts/verify_road_execution.py \
  road-exec-33766f336d9cc18eb2ac159e \
  --storage-root artifacts/runtime/road \
  --archive data/datasets/112年多維度SHP成果_0502.zip \
  --visual-evidence artifacts/tmp/road05-visual-evidence.json \
  --screenshot artifacts/tmp/road05-render.png
```

Exit status is `0` only for a fully verified result, `1` for a completed fail-closed result, and `2`
when the requested persisted execution cannot be inspected.

Visual evidence and screenshots are intentionally ignored runtime evidence. They are not committed
goldens. The canonical QA/provenance identities are stable when the same evidence bytes are copied
to another checkout root.

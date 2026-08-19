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

## Authorization-consumption reproducibility

ROAD-05A makes the historical authorization consumption independently reproducible from tracked
state. The canonical fixture is
`data/specifications/nma-road-hero-road-04-authorization-consumption-fixture-v1.0.json`; it is
closed by `schemas/road-authorization-consumption-fixture-v1.0.schema.json` and consumed by the
independent verifier. The fixture contains exactly these generation inputs:

- authorization ID and SHA-256;
- execution ID;
- the one-time, non-secret idempotency key `road04-controlled-execution-v1`;
- receipt ID and SHA-256.

Only the exact idempotency-key string contributes to `idempotency_key_sha256`. It is serialized as
its exact UTF-8 bytes, with no Unicode normalization, prefix, suffix, or line terminator, and is
hashed with SHA-256. This produces
`d4645499a8a897194ed49d7cd19edb6acd96bda5db0611fd82a701a875f343cb`. The prior fresh
reconstruction used the test-only string `road04-session-key`, which produced
`58f2ce5004d848a077f23c4a9af36d81901d753931dd1d6fddbb6f660f7aa8ae`.

The consumption record is built only from the six fixture inputs plus the fixed
`nma.road-authorization-consumption/1.0` schema identifier. Persisted bytes are UTF-8 JSON with
keys sorted lexicographically, `,` and `:` separators, non-ASCII characters emitted directly, and
one trailing LF. Their SHA-256 is
`fb21f714f925922938198ac9299a42ea87aaab89b2860d5518a49f5467571330`. No timestamp,
path, environment variable, random value, runtime ledger, ignored file, or prior execution state is
an input.

The fixture schema and hashing contract are versioned `1.0`. Any change to input fields,
serialization, or hashing requires a new major contract version; compatible explanatory additions
require a minor version. Existing versions remain immutable. `fixture_sha256` is SHA-256 over the
fixture object serialized with the repository canonical JSON function after removing only the
`fixture_sha256` self-hash field; unlike the persisted consumption file, this hash input has no
trailing LF.

Reproduce the identities from a clean checkout with no ROAD runtime artifacts:

```sh
python3 scripts/verify_road_authorization_consumption.py
```

Exit status is `0` only when the fixture self-hash, idempotency identity, reconstructed record, and
canonical consumption-file identity all agree.

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

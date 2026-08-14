# HERO-05 School Hero QA and Provenance

## Repository contract audit

HERO-05 reuses these repository contracts:

- HERO-01: `nma.intent-plan/0.5` from `intent_planning_v05.py`;
- HERO-02: `nma.school-feature-intelligence/0.5`, including proposal JSON-LD `@id`;
- HERO-03 handoff consumed by HERO-04: `nma.symbol-edit-authorization/1.0`;
- HERO-04 plan, bundle, receipt, and observation schemas under
  `nma.school-hero-*/1.0` and `nma.maplibre-runtime-bundle/1.0`;
- runtime identity: `nma.runtime-baseline/0.32`, canonical graph SHA-256, and the
  graph-bound vector index identity.

The audited checkout does not contain a production HERO-03 authorization producer. The
authorization verifier and test fixture are the only local HERO-03 contract evidence. HERO-01
also has no stored request or intent identifier, and HERO-02 evidence items have no evidence
identifier. HERO-05 therefore does not infer those missing records. A verification can pass only
when the authorization contains a content-addressed `upstream_lineage` snapshot with the actual
request, intent, evidence, decision, proposal, and approval payloads. Missing or invalid records
fail closed.

## Persistence boundary

HERO-04 now writes `authorization.json` beside its existing `plan.json`, `receipt.json`,
`bundle.json`, GeoJSON, and derived SVG. HERO-05 is a separate reader of that persisted execution
directory. Verification replays the approved transformation against the hash-bound source archive
and official portrayal asset, then compares the expected GeoJSON, SVG, and MapLibre bundle with
the observed artifacts.

Successful or failed verification writes deterministic `qa.json` and `provenance.json`. Neither
record contains a generated timestamp. Reverification of unchanged inputs produces identical
records.

## QA verdicts

The QA record uses `nma.school-hero-qa/1.0` and returns one of:

- `expected-change-verified`;
- `expected-change-missing`;
- `incorrect-change`;
- `unexpected-additional-change`.

Its checks cover plan/receipt/bundle hashes, input identities, deterministic expected-state
derivation, exact semantic data/portrayal/map state, and unexpected files outside the approved
execution artifact set.

## Provenance verification

The provenance record uses `nma.school-hero-provenance/1.0`. Its chain is:

`request -> intent -> evidence -> decision -> proposal -> approval -> execution -> QA -> artifact`

Verification checks content hashes and parent references for every upstream record, proposal and
approval bindings, execution-to-proposal bindings, persisted artifact hashes, QA success, runtime
contract/revision, canonical graph identity, and vector-to-graph identity.

## Offline command

```sh
python scripts/verify_school_hero_execution.py EXECUTION_ID \
  --storage-root artifacts/runtime/school-hero \
  --archive /authorized/path/to/reviewed-school.zip
```

Exit status is `0` only for a verified result, `1` for a completed fail-closed verification, and
`2` when the persisted execution cannot be inspected.

# CORE-04 Completion Report

## Verdict

PASS

CORE-04 establishes repository-wide closure of the generic canonical JSON plus SHA-256 provider.
Three residual providers were found and replaced at their existing boundaries. `nma.core` is now the
sole generic provider, all downstream imports remain intact, and no ROAD, School Hero, Core, or
other frozen artifact changed.

## Repository identity

- Canonical root:
  `/Users/dongpodeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/topoMap`
- Predecessor SHA: `c661e7b06aa6810362c62809afdfd5345a2e1689`
- Predecessor branch: `core/core-03-school-hero-identity-adoption`
- Working branch: `core/core-04-residual-identity-audit`
- Predecessor local SHA: `c661e7b06aa6810362c62809afdfd5345a2e1689`
- Predecessor remote SHA: `c661e7b06aa6810362c62809afdfd5345a2e1689`
- Predecessor local/remote equality: PASS
- Starting worktree: clean
- Final local SHA: the publication commit containing this report; the exact non-self-referential
  value is recorded in the final task delivery after commit creation.
- Final remote SHA: verified equal to the publication commit after the normal push; the exact value
  is recorded in the final task delivery.
- Final local/remote equality: PASS, verified after publication.
- Final worktree cleanliness: PASS, verified after publication.

A tracked report cannot contain its own commit SHA: writing that SHA changes the report and creates
a different commit. The final delivery therefore carries the authoritative exact local/remote SHA,
consistent with the accepted CORE-01 through CORE-03 reporting convention.

## Outcome type

BOUNDED-CLOSURE

Exactly three existing production/script files contained category 5 residual providers. Closure
required no downstream edits and met the hard three-file cap exactly.

## Candidate audit

`src/nma/core/identity.py` is the immutable reference owner, not a residual candidate. Its
`canonical_json` and `canonical_sha256` definitions are byte-identical to
`nma-core-v0.1-baseline`. The table classifies every meaningful non-Core candidate or homogeneous
candidate group found by the tracked-file AST and semantic audit. Raw SHA-256 of file bytes or raw
UTF-8 text is included where it could otherwise be confused with canonical JSON identity.

| File | Symbol/function | Classification | Evidence | Upstream/downstream consumers | Action/disposition |
| --- | --- | --- | --- | --- | --- |
| `src/nma/road_resolution.py` | `canonical_json`, `canonical_sha256` | 2. Compatibility alias | Explicit re-exports from `nma.core`; both are the exact Core objects. | Core → ROAD-01 → ROAD-02/03/04/05. | No change. |
| `src/nma/road_portrayal_decision.py` | imported `canonical_sha256`; `proposal_sha256`, `decision_sha256` | 1. Canonical Core consumer | Imports through the ROAD-01 compatibility boundary; object identity equals Core. | ROAD proposal and decision construction/verification. | No change. Domain field selection remains local. |
| `src/nma/road_approval.py` | imported `canonical_sha256`; `approval_sha256`, `authorization_sha256` | 1. Canonical Core consumer | Transitive Core provider with approval/authorization self-fields excluded locally. | ROAD approval, authorization, execution, verification. | No change. |
| `src/nma/road_execution.py` | imported `canonical_sha256`; `_hash_record`, geometry/endpoint identities | 1. Canonical Core consumer | Transitive provider is the exact Core object. | ROAD execution, receipts, observations, rollback. | No change. Domain hash bases remain local. |
| `src/nma/road_verification.py` | imported `canonical_json`, `canonical_sha256`; `_record_hash` | 1. Canonical Core consumer | Both imports resolve transitively to Core. | ROAD QA/provenance and frozen verification. | No change. |
| `src/nma/road_authorization_consumption.py` | imported `canonical_json`, `canonical_sha256`; fixture hash | 1. Canonical Core consumer | Both imports resolve transitively to Core. | ROAD authorization-consumption fixture and ledger. | No change. |
| `src/nma/school_hero_execution.py` | `canonical_json`, `canonical_sha256` imports | 1. Canonical Core consumer | Direct imports are exact Core objects. | School authorization, plan, bundle, receipt, observation, rollback. | No change. |
| `src/nma/school_hero_verification.py` | `canonical_json`, `canonical_sha256` imports | 1. Canonical Core consumer | Direct imports are exact Core objects. | School lineage, QA/provenance, artifact verification. | No change. |
| `src/nma/entity_resolution_v10.py` | `_canonical_sha256` | 5. Residual duplicate provider | Predecessor locally performed compact sorted Unicode JSON serialization followed by SHA-256 for arbitrary values. | Imported by v0.101, v0.103, v0.105, v0.107, and v0.108 candidate-pool paths. | Replaced with exact compatibility alias to `nma.core.canonical_sha256`; all downstream files unchanged. |
| `src/nma/entity_resolution_v101.py`, `v103.py`, `v105.py`, `v107.py`, `v108.py` | imported `_canonical_sha256` | 1. Canonical Core consumer | Existing transitive import now resolves to the exact Core object in every module. | Entity candidate pools and resolution support. | No downstream change. |
| `src/nma/neo4j_retrieval_v028.py` | `_sha256` | 5. Residual duplicate provider | Predecessor hashed `_canonical_json(value).encode("utf-8")` for arbitrary values. | Live Neo4j retrieval parity package identity. | Replaced with exact compatibility alias to `nma.core.canonical_sha256`. |
| `scripts/run_nma_runtime_graph_backend_v029.py` | `canonical_sha256` | 5. Residual duplicate provider | Predecessor independently implemented compact sorted Unicode JSON plus SHA-256. | Runtime graph-backend verification report cases. | Replaced with exact compatibility alias to `nma.core.canonical_sha256`; standalone `src` bootstrapping retained. |
| `src/nma/road_execution.py` | local `canonical_json`, `_write_json` | 4. Serialization-only path | Writes deterministic JSON bytes plus LF; it is not used as the ROAD generic hash provider. CORE-02 explicitly preserved this writer. | ROAD persisted execution records. | No change. |
| `src/nma/neo4j_retrieval_v028.py` | `_canonical_json` | 4. Serialization-only path | After `_sha256` closure, used only as a deterministic sort key for edge properties. | Neo4j/canonical graph comparison. | No change. |
| `src/nma/neo4j_roundtrip_v027.py` | `_canonical_json` | 4. Serialization-only path | Used for stable edge ordering and as serialization inside the separately classified row-set identity. | Neo4j projection round-trip. | No change. |
| `src/nma/runtime_graph_backend_v029.py` | `_canonical_json` | 4. Serialization-only path | Used only to order edge property values during graph equality. | Runtime live/canonical graph selection. | No change. |
| `src/nma/bench.py` | `_canonical` | 4. Serialization-only path | Deterministic JSON is used for benchmark value equality, not as a generic identity provider. | Benchmark scoring. | No change. |
| `src/nma/neo4j_projection.py` | `_properties_json` | 4. Serialization-only path | Deterministic property serialization is persisted/sorted; no generic object hash is exposed. | Neo4j row projection. | No change. |
| `src/nma/vector_index.py` | deterministic property JSON in `embedding_text_for_node` | 4. Serialization-only path | Serialization constructs bounded embedding text, not canonical artifact identity. | Vector indexing/retrieval. | No change. |
| `scripts/verify_road_execution.py`, `verify_road_authorization_consumption.py`, `verify_school_hero_execution.py` | sorted/compact `json.dumps` output | 4. Serialization-only path | CLI result printing only; no SHA-256 composition or provider symbol. | Human/CI verification output. | No change. |
| `src/nma/agentic_vs1.py`, `agentic_vs2.py`, `agentic_vs3.py`, `api.py`; `scripts/run_nma_agent_server.py` payload builders | compact JSON request/response serialization | 4. Serialization-only path | Network/tool payload construction has no generic canonical hash provider. | API/runtime integration and intent/execution routing. | No change. |
| `src/nma/neo4j_roundtrip_v027.py` | `_rows_sha256` | 3. Domain-specific identity rule | Hashes the explicitly normalized node or relationship row list; the participating row construction/order is domain-owned. | Offline/live round-trip manifests. | No change. |
| `src/nma/neo4j_projection.py` | relationship `stable_key` | 3. Domain-specific identity rule | Hash basis is the relationship envelope `{source,type,target,properties}`. | Neo4j relationship upsert/deduplication. | No change. |
| `src/nma/qa_review.py` | `real_diagnosis_qa_plan`, `_plan_id` | 3. Domain-specific identity rule | Hashes an explicit reviewed QA plan subset and truncates it into a domain ID. | QA planning and approved repair flow. | No change. |
| `src/nma/real_layer.py` | `_plan_id` | 3. Domain-specific identity rule | Hashes the explicit `PLAN_BASIS_KEYS` subset and applies the real-layer ID prefix. | Derived real-layer planning/execution. | No change. |
| `scripts/run_nma_agent_server.py` | three proposal-store `create` methods | 3. Domain-specific identity rule | Hash input is time-salted plus deterministic proposal/plan text; deliberately not canonical content identity. | Portrayal, real-layer, and QA pending-approval stores. | No change. |
| `src/nma/road_resolution.py`, `road_portrayal_decision.py`, `road_approval.py` | package/proposal/decision/approval/authorization hash-basis functions | 3. Domain-specific identity rule | Each domain function selects/excludes contract-specific fields before delegating to Core. | ROAD trust chain. | No change. |
| `src/nma/road_execution.py`, `road_verification.py` | record, plan, receipt, observation, rollback, QA/provenance rules | 3. Domain-specific identity rule | Self-hash fields, timestamps, and explicitly ignored fields are selected by frozen ROAD contracts. | ROAD execution and verification. | No change. |
| `src/nma/school_hero_execution.py`, `school_hero_verification.py` | authorization, self-hash, lineage, plan/bundle/receipt, QA/provenance rules | 3. Domain-specific identity rule | Authorization excludes `authorization_hash`; record identity binds selected payloads and self-hash fields. | Frozen School execution/verification. | No change. |
| `src/nma/road_authorization_consumption.py`, `road_verification.py` | canonical persisted-file hash functions | 3. Domain-specific identity rule | Hashes Core canonical bytes plus exactly one LF, the frozen on-disk record contract. | ROAD consumption and QA verification. | No change. |
| `src/nma/entity_resolution_v10.py`, `v101.py`–`v108.py`; `src/nma/vector_index.py` | query/segment/text SHA-256 | 3. Domain-specific identity rule | Hashes exact raw UTF-8 query or embedding text bytes, not canonical JSON. | Cache lookup and embedding lineage. | No change. |
| `src/nma/neo4j_projection.py`, `neo4j_retrieval_v028.py`, `vector_index.py` | `canonical_graph_sha256` and graph file checks | 3. Domain-specific identity rule | Hashes exact tracked graph file bytes. | Projection, retrieval, vector-index integrity. | No change. |
| `src/nma/real_layer.py`; `agentic_freeze.py`; `demo_freeze.py`; `demo_backup.py`; `demo_rc1.py`; `historical_release.py`; `bench.py`; `portrayal_bench.py`; build/check scripts | file/member/archive/fingerprint SHA-256 helpers | 3. Domain-specific identity rule | Streaming or exact-byte hashes; no JSON canonicalization provider. | Freeze, source, release, archive, and artifact integrity. | No change. |
| `src/nma/road_execution.py`, `school_hero_execution.py`, `road_authorization_consumption.py` | idempotency-key SHA-256 | 3. Domain-specific identity rule | Hashes exact UTF-8 key bytes under the frozen idempotency contract. | Execution replay/consumption control. | No change. |
| `tests/hero04_support.py`, CORE tests, ROAD/School acceptance tests | imported canonical functions and test-only rehash/file helpers | 1. Canonical Core consumer or 3. Domain-specific test rule | Imports production compatibility providers; test-local hashes construct negative fixtures or compare bytes and cannot serve production. | Test support only. | No production action. |
| all tracked production/scripts | conditional Core import, stub, copy, reconstruction, auto-repair search | 6. Fallback/stub/auto-repair provider | No candidate found: zero `ImportError`/`ModuleNotFoundError` fallback around Core and zero Core reconstruction/copy path. | Repository-wide. | Count remains zero; isolated missing-Core test fails before identity processing. |

The audit also parsed every tracked Python file under `src/nma`, `scripts`, and `tests`, including
`intent_planning_v05.py`, API/runtime integration, execution, verification, approval, receipt,
observation, rollback, QA/provenance, minimal-checkout support, and executable fixtures. Files with
no identity candidate remain in the audited universe and do not need a table row.

## Provider counts

- Residual duplicate count before: **3**
- Residual duplicate count after: **0**
- Fallback/stub/auto-repair provider count before: **0**
- Fallback/stub/auto-repair provider count after: **0**

The focused test parses the exact predecessor versions and current tracked sources. It asserts the
three-member predecessor set and the empty post-closure set rather than relying on a single grep.

## Adoption evidence

- Core provider ownership: PASS. `nma.core.identity` is the only remaining generic canonical JSON
  plus SHA-256 implementation.
- ROAD adoption: PASS. ROAD-01 aliases are exact Core objects; ROAD-02 through ROAD-05 consume the
  same provider transitively.
- School execution adoption: PASS. Execution imports the exact Core functions.
- School verification adoption: PASS. Verification imports the exact Core functions.
- Compatibility aliases: PASS. ROAD-01, entity-resolution v0.10, Neo4j retrieval v0.28, and the
  runtime graph verification script expose their historical names as the exact Core hash object.
- Domain-specific authorization preservation: PASS. ROAD and School excluded-field/binding rules
  remain in their frozen modules and exact focused/historical assertions pass.
- Record self-hash preservation: PASS. ROAD and School record bases remain exact and delegate only
  the final primitive operation to Core.
- Representative identity equality: PASS for Unicode, nested mappings, ordered lists, booleans,
  null, integers, and floats. List order remains significant.

## Fail-closed result

- Missing-Core result: deterministic `ModuleNotFoundError: No module named 'nma.core'` for each of
  the three closed provider boundaries in an isolated checkout.
- Mutation check: PASS. The complete isolated file manifest is identical before and after every
  failed import.
- Auto-repair check: PASS. No `src/nma/core` directory appears and no file is created or changed.
- Fallback-provider check: PASS. Static AST analysis reports zero Core import fallbacks before and
  after closure; runtime failure occurs before identity processing.

## Regression

- CORE-04 focused: `12 passed`, 0 failed, 0 skipped, 0 xfailed.
- CORE-03: `13 passed`, 0 failed, 0 skipped, 0 xfailed.
- CORE-02: `11 passed`, 0 failed, 0 skipped, 0 xfailed.
- CORE-01: `17 passed`, 0 failed, 0 skipped, 0 xfailed.
- Combined CORE-01 through CORE-04: `53 passed`.
- Changed Neo4j/runtime integration regression: `12 passed`.
- ROAD historical: `199 passed`, 0 failed, 0 skipped, 0 xfailed.
- School Hero: `42 passed`, 0 failed, 0 skipped, 0 xfailed.
- ROAD schemas: `15 PASS` under `Draft202012Validator.check_schema`.
- Ruff check: PASS for all four changed/added Python files.
- Ruff format check: PASS for all four changed/added Python files.
- `git diff --check`: PASS.

An additional repository-wide run reported `477 passed, 3 failed`. The three failures are outside
the accepted CORE/ROAD/School gates: PMTiles catalog reproducibility, Agentic v0.3 freeze size, and
Agentic v0.3 pages source size. All three reproduce unchanged in a deliberately isolated checkout
at exact predecessor `c661e7b06aa6810362c62809afdfd5345a2e1689`, with identical error values.
They are therefore documented pre-existing baseline failures, not CORE-04 regressions; CORE-04 did
not modify their sources, manifests, data, or tests.

## Integrity

- Frozen ROAD equality: PASS. Specifications, fixtures, goldens, runtime records, QA/provenance,
  schemas, tests, and production domain modules are byte-identical to the predecessor.
- Frozen School equality: PASS. Fixtures, authoritative data, public data, symbol, schemas,
  acceptance tests, QA/provenance contracts, execution, and verification are byte-identical to the
  predecessor.
- Core source equality: PASS. All three files under `src/nma/core` are byte-identical to immutable
  baseline commit `ce6e90c993cb36782da29d7e24369882eb303476`.
- ROAD tag/freeze equality: PASS. Local and remote ROAD freeze resolve to
  `325c70d5335f57c43a8af85822db25032aa225c3`.
- School freeze equality: PASS. Remote frozen branches remain at
  `75f80d389fe48b6dc33912e45433dc1d7e7b98b5` and
  `56f99eb9ae63272a68accac3041fb10eacefb986`.
- Core tag equality: PASS. Local and remote peeled tag resolves to
  `ce6e90c993cb36782da29d7e24369882eb303476`.
- Private archive: used by ROAD/School regressions; SHA-256 is exactly
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`; ignored,
  untracked, unstaged, and unmodified.

Final changed-file inventory relative to the predecessor:

1. `src/nma/entity_resolution_v10.py` — authorized category 5 provider closure.
2. `src/nma/neo4j_retrieval_v028.py` — authorized category 5 provider closure.
3. `scripts/run_nma_runtime_graph_backend_v029.py` — authorized category 5 provider closure.
4. `tests/test_core04_residual_identity_audit.py` — deterministic repository-wide evidence.
5. `CORE-04-Completion-Report.md` — this report.

No unrelated tracked file changed. Production-file count: **3**.

## Recommendation

READY for CORE-FINAL

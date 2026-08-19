# CORE-01 Completion Report

## 1. Verdict

PASS. CORE-01 introduces a thin, domain-neutral identity and feature-profile boundary without
changing either frozen Hero implementation or any frozen artifact.

## 2. Baseline

- Repository root: `/Users/dongpodeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/topoMap`
- Baseline tag: `nma-road-v1.0-final`
- Baseline commit: `325c70d5335f57c43a8af85822db25032aa225c3`
- Local annotated tag target: `325c70d5335f57c43a8af85822db25032aa225c3`
- Remote annotated tag target: `325c70d5335f57c43a8af85822db25032aa225c3`
- Branch: `core/core-01-thin-contract-layer`
- Starting worktree: clean
- Private source archive: ignored, untracked, unstaged, and SHA-256
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`

## 3. Exact Changed Files

1. `src/nma/core/__init__.py`
2. `src/nma/core/identity.py`
3. `src/nma/core/feature_profile.py`
4. `src/nma/feature_profile_adapters.py`
5. `tests/test_core01_identity.py`
6. `tests/test_core01_feature_profiles.py`
7. `CORE-01-Completion-Report.md`

No additional helper file was required.

## 4. Core API Introduced

- `canonical_json(value) -> bytes`
- `canonical_sha256(value) -> str`
- `validate_sha256(value) -> str`
- immutable `ArtifactReference(id, sha256)`
- immutable `FeatureProfile(geometry_role, identity_payload, source_scope_payload, metadata)`

The public Core names are re-exported from `nma.core`.

## 5. Canonical Serialization Rules

Canonical JSON uses Python JSON serialization with UTF-8 encoding, `ensure_ascii=False`,
`sort_keys=True`, `separators=(",", ":")`, and `allow_nan=False`. The SHA-256 function hashes those
exact canonical bytes and returns a lowercase hexadecimal digest.

## 6. ArtifactReference Semantics

`ArtifactReference` contains only `id` and `sha256`. It is a frozen, slotted value object. Its ID
must be a non-empty string. Its digest must contain exactly 64 lowercase hexadecimal characters;
uppercase, short, and non-hexadecimal values fail closed.

## 7. Feature-Profile Contract

`FeatureProfile` carries only:

- a non-empty geometry role/type string;
- an adapter-defined identity payload;
- an adapter-defined source/scope identity payload; and
- optional opaque metadata.

Payload mappings are copied and recursively frozen. Nested mappings become read-only mapping
views, and nested arrays become tuples. Values are restricted to finite, JSON-compatible data.
Core neither interprets domain keys nor prescribes School/Road proposal, approval, authorization,
plan, execution, QA, or provenance shapes.

## 8. School Adapter

- Profile identity: `school-point`
- Feature identity: `9920103`
- Geometry: `Point`
- Frozen fields referenced: `SCHOOL_PROFILE_ID`, `SCHOOL_FEATURE_CODE`, `SCHOOL_GEOMETRY`, and the
  corresponding frozen `REAL_LAYER_PROFILES` entry's product layer, source-layer IDs, and feature
  name.

The adapter is a read-only view. The frozen School execution implementation does not depend on it.

## 9. Road Adapter

- Class identity: `9420400`
- Route identity: `ROADNUM=縣126|ROADNUM1=|ROADNUM2=|ROADNAME=中山街`
- Geometry: `LineString`
- Ordered segment identity: `K0000004671`, `K0000004913`, `K0000005348`
- Frozen fields referenced: `EXPECTED_IDENTITY` and `EXPECTED_FEATURE_IDS`, plus the frozen K14
  source scope represented by the compatibility view.

The adapter is a read-only view. The frozen Road implementation does not depend on it.

## 10. Canonical Byte/Hash Parity

PASS. Representative Unicode, nested mappings, arrays, booleans, nulls, integers, floats, key
ordering, and compact-separator cases produce exact byte equality with frozen School and Road
canonical serialization and exact SHA-256 equality. NaN and positive/negative infinity fail
consistently in all three implementations.

## 11. Immutability

PASS. Tests verify frozen dataclass fields, defensive copying of caller-owned nested structures,
read-only nested mappings, and immutable nested arrays. Mutating the original input after profile
construction does not change the profile's logical identity or source scope.

## 12. Domain Isolation

PASS. Deterministic source inspection verifies that `src/nma/core` contains none of the seven
specified frozen School/Road literals and imports neither `nma.school_hero_execution` nor any
`nma.road_*` module. All domain constants remain outside Core in the compatibility adapters.

## 13. Focused CORE-01 Tests

`PYTHONPATH=src python3 -m pytest -o addopts='' -q tests/test_core01_identity.py tests/test_core01_feature_profiles.py`

Result: `17 passed`, 0 failed, 0 skipped.

## 14. School Regression

The historical HERO-04 acceptance set (`test_hero04_authorization.py`,
`test_hero04_execution.py`, `test_hero04_maplibre.py`, and `test_hero04_rollback.py`) reports
`11 passed`, 0 failed, 0 skipped.

## 15. Road Regression

The complete frozen ROAD-01 through ROAD-05 suite reports `199 passed`, 0 failed, 0 skipped.

## 16. Schema Validation

All 15 `schemas/road-*.schema.json` files pass `Draft202012Validator.check_schema`. Actual frozen
records and generated acceptance records remain validated by the 199-test ROAD suite.

## 17. Ruff and Format

Ruff check: PASS for all six changed Python files.

Ruff format check: PASS for all six changed Python files.

## 18. Frozen Artifact Comparison

A conservative inventory of 79 tracked School/Road-named sources, schemas, tests, fixtures,
reports, and artifacts was SHA-256 hashed before implementation and again after all tests. The two
inventories are byte-for-byte identical. Direct Git comparison also shows no change to
`src/nma/school_hero_execution.py` or any `src/nma/road_*.py` file. The ignored private archive's
current digest matches the frozen digest recorded at baseline.

## 19. Abstractions Not Generalized

CORE-01 does not introduce universal proposal, approval, authorization, execution-plan,
execution-receipt, QA, provenance, portrayal, rollback, runtime, geometry-processing, source-layer,
route, expected-count, or feature-code schemas. It does not migrate either frozen hash function or
connect the adapters to execution.

A future Polygon/Building adapter can implement the contract without changing `nma.core`: it can
supply its geometry role/type and its own opaque identity, source/scope, and capability payloads.
No Polygon/Building-specific field was added to prove this.

## 20. Final Commit SHA

The authoritative final commit SHA is reported in the task's final response immediately after this
report is committed. A Git commit cannot embed its own SHA in tracked content because changing that
content changes the commit SHA.

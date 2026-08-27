# CORE-03 Completion Report

## Verdict

PASS. CORE-03 adopts the canonical `nma.core` identity provider in School Hero execution and
verification without changing any accepted identity, domain-specific self-hash rule, execution
behavior, frozen artifact, schema, ROAD behavior, or canonical Core source.

## Repository and authorization

- Canonical repository root:
  `/Users/dongpodeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/topoMap`
- Accepted predecessor CORE-02 SHA: `a0cd39b89fa36d072605916559c54c133db8279f`
- Exact baseline SHA: `a0cd39b89fa36d072605916559c54c133db8279f`
- Branch: `core/core-03-school-hero-identity-adoption`
- Baseline local/remote equality: PASS
- Baseline tracked-file inventory: 424 files
- Working tree was clean before branch creation and implementation.

## Exact changed files

1. `src/nma/school_hero_execution.py`
2. `src/nma/school_hero_verification.py`
3. `tests/test_core03_school_hero_identity_adoption.py`
4. `CORE-03-Completion-Report.md`

No conditional historical-test change was required.

## Provider adoption

- Core provider adoption: PASS.
- School Hero execution adoption: PASS. The local generic `canonical_json` and
  `canonical_sha256` implementations were removed and replaced with the canonical `nma.core`
  functions.
- School Hero verification adoption: PASS. Verification consumes generic canonical identity
  primitives directly from `nma.core` while continuing to import School Hero-specific execution
  functions from `school_hero_execution`.
- Authorization identity rule: PASS. The School Hero wrapper still deep-copies the authorization,
  removes `authorization_hash`, and delegates the final canonical hash to Core.
- Record identity rule: PASS. `_hash_record` still copies the domain record and adds the specified
  self-hash field only after delegating its basis hash to Core.
- Generic raw idempotency-key hashing remains intentionally separate because it hashes UTF-8 key
  bytes, not canonical JSON.
- Ruff formatting made mechanical changes only within the two authorized production files and the
  focused test file.

## Exact accepted identity comparison

The before values were captured from the untouched accepted baseline before implementation. The
after values were regenerated from the final formatted candidate using the same private archive,
fixed clock, request, lineage, authorization, and idempotency key. Every comparison is exact.

| Identity | Before | After | Result |
| --- | --- | --- | --- |
| Proposal | `df7032e689158ccd2e34aa9519d2aa3271f683f4f106dcfbf3bbeac239267b8b` | `df7032e689158ccd2e34aa9519d2aa3271f683f4f106dcfbf3bbeac239267b8b` | PASS |
| Approved operations | `b5b177ef36815687065e72c13a9a9ed028b498d6aa77caed706d33eed843faad` | `b5b177ef36815687065e72c13a9a9ed028b498d6aa77caed706d33eed843faad` | PASS |
| Authorization | `2a360eb478f789d8a10512a96af7b06f423c3a413f220b74b101927ec9edcf5d` | `2a360eb478f789d8a10512a96af7b06f423c3a413f220b74b101927ec9edcf5d` | PASS |
| Execution ID | `exec-5a8fd51a1eabb7d78f9f7ad8` | `exec-5a8fd51a1eabb7d78f9f7ad8` | PASS |
| Plan | `62eb1e7472d7d58ecd3452dc4259304fa98c7229201fc1ca7b5444e5f132dd8b` | `62eb1e7472d7d58ecd3452dc4259304fa98c7229201fc1ca7b5444e5f132dd8b` | PASS |
| Derived layer | `935fce691590db4de7251581e7080bef3e4d15208727bee2b5b537b423649f58` | `935fce691590db4de7251581e7080bef3e4d15208727bee2b5b537b423649f58` | PASS |
| Execution receipt file | `8b03047986af34a543a70ffc93ff6839dbcf63558cde6364c9e8751002c9be86` | `8b03047986af34a543a70ffc93ff6839dbcf63558cde6364c9e8751002c9be86` | PASS |
| Runtime bundle | `27d065a70f296c28344d43c24efd1663deba80c80403ecf36d85ff6d23e3eca4` | `27d065a70f296c28344d43c24efd1663deba80c80403ecf36d85ff6d23e3eca4` | PASS |
| Observation | `e2a271d5be59e65766351b1fe6dc4d53fba5ae2b24cd74749cc868043511ad84` | `e2a271d5be59e65766351b1fe6dc4d53fba5ae2b24cd74749cc868043511ad84` | PASS |
| Receipt | `edd96c5bcd3d17850f4e62b622540c02c96aaa65ebc4b2354061d38a7eaa8c6b` | `edd96c5bcd3d17850f4e62b622540c02c96aaa65ebc4b2354061d38a7eaa8c6b` | PASS |
| Rollback | `b4c16401a6408aeb63cdd9e345b34d07c0999882e62f124aee613b5ead53f4aa` | `b4c16401a6408aeb63cdd9e345b34d07c0999882e62f124aee613b5ead53f4aa` | PASS |
| QA | `f0ec3fc6ce25cebe23632793e2de716189f96033ffb8c3ededea1beb501e318d` | `f0ec3fc6ce25cebe23632793e2de716189f96033ffb8c3ededea1beb501e318d` | PASS |
| Provenance | `347dabb85dd11d721c42b0dd359db54390e4e8f030c4171dac8b7ba9f3fa176a` | `347dabb85dd11d721c42b0dd359db54390e4e8f030c4171dac8b7ba9f3fa176a` | PASS |
| Output artifact set | `eb0a42899b36a87a7b1a213f0d9d58c06a5893ad93f545c00d39030d63fd46db` | `eb0a42899b36a87a7b1a213f0d9d58c06a5893ad93f545c00d39030d63fd46db` | PASS |

Lineage payload identities are also exact:

| Kind | Before and after SHA-256 | Result |
| --- | --- | --- |
| Request | `bfbf8cfdc5423b66e145e0461643ed3f922dc8a73ef02952ebce6baba0502ed0` | PASS |
| Intent | `478ad06fc4d9ef265c2a6130b105dc8f990811620393b40da36c7fc1247a2111` | PASS |
| Evidence | `c7dbc47947bc94ef0ff77ba4d94845c42f6f7312d8d8233c6de6135dc15a3889` | PASS |
| Decision | `cdc229c83455c60008b8ca77ae0a8b68f46ac0ed65e2d4cb2801818bea052c71` | PASS |
| Proposal | `df7032e689158ccd2e34aa9519d2aa3271f683f4f106dcfbf3bbeac239267b8b` | PASS |
| Approval | `a24d5d4bc9116f4b711944d141d6cf807e12e42789d782496b2c830c206ab8fa` | PASS |

## Acceptance results

- CORE-03 focused suite: `13 passed`, 0 failed, 0 skipped.
- CORE-02 regression: `11 passed`, 0 failed, 0 skipped.
- CORE-01 regression: `17 passed`, 0 failed, 0 skipped.
- Combined final Core run: `41 passed`, 0 failed, 0 skipped.
- Complete current School Hero suite: `42 passed`, 0 failed, 0 skipped.
- Complete historical ROAD suite: `199 passed`, 0 failed, 0 skipped.
- ROAD schemas: all 15 closed Draft 2020-12 schemas pass metaschema validation; generated and
  accepted records also pass in the 199-test suite.
- School Hero schemas: all 7 applicable closed Draft 2020-12 schemas pass metaschema validation;
  generated artifacts pass the complete School Hero suite.
- Ruff check: PASS for all three authorized Python files.
- Ruff format check: PASS for all three authorized Python files.
- `git diff --check`: PASS.
- Missing-Core fail-closed behavior: PASS. Both School Hero production modules fail with
  deterministic `ModuleNotFoundError: No module named 'nma.core'`; the isolated checkout's file
  manifest is identical before and after both failures.

## Integrity results

- Duplicate-provider audit: PASS. The authorized School Hero production scope defines neither
  generic canonical function, contains no generic canonical-hash composition, and contains no
  import fallback. Only `src/nma/core/identity.py` owns the canonical JSON/hash implementation used
  by School Hero. No Core copy, stub, fork, shim, fallback, generated replacement, or provider
  source copy was created.
- Prior tracked-file integrity: PASS. The baseline contains 424 tracked files. Every pre-existing
  tracked file outside the two authorized production files is byte-identical to the baseline.
- Frozen School Hero artifact integrity: PASS. Tracked School Hero artifacts, inputs, fixtures,
  schemas, acceptance tests, symbols, data, QA/provenance contracts, and runtime inputs are
  byte-identical to the baseline.
- Frozen ROAD artifact integrity: PASS. Tracked ROAD artifacts, fixtures, goldens, schemas,
  acceptance tests, production modules, and reports are byte-identical to the baseline.
- Core source integrity: PASS. `src/nma/core/__init__.py`, `identity.py`, and
  `feature_profile.py` are byte-identical to the accepted baseline.
- Private archive integrity: PASS. The archive remains SHA-exact at
  `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`, ignored,
  untracked, and unstaged.

## Commit and publication

The authoritative final local and remote commit SHA is reported in the task's final response after
this report is committed and the branch is pushed. A tracked report cannot embed its own commit
SHA without changing that SHA. Publication is accepted only when the local and remote branch SHAs
are exactly equal and the final worktree is clean.

## Readiness recommendation

READY. CORE-03 is complete and suitable for acceptance as the bounded School Hero identity-provider
adoption. No additional School Hero redesign, refactor, schema change, or artifact regeneration is
recommended or authorized by this task.

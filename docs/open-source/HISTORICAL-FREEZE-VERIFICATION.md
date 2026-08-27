# Historical freeze verification and canonical CI policy

## Purpose and boundary

AMA has two deliberately different verification classes.

**AMA Canonical CI** asks whether the current maintained research software is healthy, reproducible,
packageable, and safe to merge. It runs at current HEAD with:

```bash
python -m pytest -m "not historical_freeze"
python scripts/run_maintained_ruff.py check
python scripts/run_maintained_ruff.py format
```

**Historical Freeze Integrity** asks whether an immutable NMA release remains exactly what it
claimed to be. Exact HEAD, direct-successor, change-scope, path, manifest, and byte assertions belong
to this class. They are retained under the registered `historical_freeze` marker and in the manually
dispatchable/scheduled historical workflow.

Software CI validates implementation conformance, not GIScience hypotheses. A green canonical
workflow does not validate RQ1, RQ2, or RQ3, and deterministic AMA-Bench development tasks are not
publication-grade scientific results.

## Freeze verification modes

### Exact-release verification

Check out the exact annotated tag, confirm both its tag object and peeled target, then run the test
scope recorded for that release. For example:

```bash
git checkout --detach nma-road-v1.0-final
pytest tests/test_road_resolution_road01.py \
  tests/test_road_portrayal_decision_road02.py \
  tests/test_road_approval_road03.py
```

The `Historical Freeze Integrity` workflow applies this pattern to all nine annotated NMA tags. A
private-data acceptance scope additionally requires its exact authorized archive and compatible
GDAL/OGR tools; absence is reported as a skip, never replaced with a guessed dataset.

### Historical-integrity-from-current verification

Current AMA HEAD verifies that every known annotated tag object exists, has its recorded object ID,
and peels to its recorded commit. In CI it also compares both identities with `origin`:

```bash
python scripts/verify_historical_tag_integrity.py --remote origin
```

Current HEAD is not expected to equal an old release SHA. Historical blobs and manifests remain
readable through the immutable refs, while current development is evaluated by current contracts.

## Test classification

`tests/conftest.py` centrally marks only the node IDs whose assertion inherently depends on a frozen
HEAD, direct successor, historical change scope, or historical current-file bytes. Functional tests
in the same modules remain in canonical CI. Marker registration lives in `pyproject.toml`, so unknown
marker warnings are errors neither locally nor in CI.

The initial clean-tree audit found 23 failing historical assertions. Fixing the maintained
`graphrag.py` lint defect and making the closure changes activated eight additional exact-byte or
stage-worktree assertions that had passed only while the successor tree happened to retain those
specific bytes or was clean. All 31 semantic historical nodes are routed explicitly.

Run the two classes independently:

```bash
make test-current
make test-historical  # expected to be run at the test's documented historical ref
```

The pre-change audit and per-node classification are recorded in
[AMA-REL-00 failure classification](AMA-REL-00-FAILURE-CLASSIFICATION.md).

## Private BUILD/ROAD state

The national mapping archive is intentionally ignored and non-redistributable. Tests that require
its exact bytes carry `private_data` and skip cleanly when it is absent. ROAD-05 no longer copies
`artifacts/runtime/road` from a developer checkout. It executes ROAD-04 once into a session-scoped
temporary directory, copies that deterministic state into each test case, and leaves frozen ROAD
mapping semantics unchanged.

## Maintained lint and formatting policy

`scripts/run_maintained_ruff.py` discovers Python under the maintained and compatibility source,
test, benchmark, contract, and script roots.

- Ruff lint checks every discovered file except one hash-locked legacy compatibility server. Its
  three `F401` imports remain available as versioned module-level compatibility symbols.
- Ruff format checks every file not listed in `config/ruff-legacy-baseline.json`.
- The legacy format list is exact and protected by an aggregate SHA-256 digest. Any byte change to a
  baseline file fails CI; a deliberately modified file must be formatted and removed from the list.
- Newly added Python is automatically checked and formatted. Legacy/frozen files are not mass
  reformatted, and the baseline cannot grow as an incidental change.

At closure the broader repository has 82 hash-locked legacy-format files; 72 are under the former
`src tests benchmark/adapters scripts` command scope. The maintained `src/nma/graphrag.py` `F841`
defect was fixed and that file was formatted. No frozen tag or historical commit was changed.

## Change control

Never retarget or recreate an existing annotated tag, force-push a freeze branch, rewrite a frozen
manifest/report, or weaken an exact-release assertion to make successor HEAD pass. A future AMA
release requires a separate reviewed release decision; this policy does not create `ama-v1.0`.

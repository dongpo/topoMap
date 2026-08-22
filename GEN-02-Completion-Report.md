# GEN-02 — Cross-Domain Contract Conformance Verification

## 1. Verdict

**PASS — CROSS-DOMAIN CONTRACT CONFORMANCE VERIFIED**

The closed GEN-01 contract describes and verifies School Hero, ROAD, and BUILD without changing
the contract or any frozen implementation. The result is **3/3 domains conform**, with zero
generic-contract changes, zero frozen production changes, zero required frozen refactors, and zero
mutation bypasses.

## 2. Canonical repository and branch

- Repository: `https://github.com/dongpo/topoMap.git`
- GEN-01 predecessor branch: `gen/gen-01-generic-contract-interface-closure`
- GEN-02 branch: `gen/gen-02-cross-domain-contract-conformance`
- Starting worktree: clean
- History rewrite, merge, tag, or force-push: none

## 3. Exact GEN-01 predecessor

After canonical-origin verification and a fetch of remote refs and tags, the local and remote
GEN-01 branches both resolved exactly to:

`7bb83f05480f642da23e7a2b244b38c3804d5fb7`

GEN-02 was created directly from that exact commit.

## 4. GEN-01 closure hash

The GEN-01 closure hash was independently reproduced with `nma.core.canonical_sha256` after
excluding `closure_sha256` and equals exactly:

`03b80441bbf317ac2e2b6cd92c3a86309c4cc7465109a3d34b6d24636491c35d`

## 5. GEN-00 predecessor verification

Local and remote GEN-00 both remain at
`b745a98f8d465259a2cb7c2b3af3df112a10ea37`. Its `audit_sha256` independently reproduces as
`2e96f00ada42e22c7dc50387cb1fbf651b6fcbbdff94af796c0fd1985ffe86e3`.

## 6. Final local, upstream, and remote identity

This tracked report follows the repository's non-self-referential finalization convention: a file
cannot contain the SHA of the commit that contains it. The exact final local SHA, upstream SHA,
and canonical remote SHA are therefore recorded in the post-push delivery. Acceptance requires
all three identities to be equal after a normal non-force push.

## 7. GEN-01 artifact immutability

All six GEN-01 artifacts are byte-identical to their blobs at the exact predecessor. Modified
GEN-01 artifacts: **0**.

## 8. Frozen identity verification

| Baseline | Exact identity | Result |
| --- | --- | --- |
| BUILD-FINAL | `nma-build-v1.0-final^{}` → `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7` | exact annotated tag target |
| CORE-FINAL | `nma-core-v1.0-final^{}` → `5eb138ae7686502431587743ebce9ddf92c5a799` | exact annotated tag target |
| ROAD-FINAL | `nma-road-v1.0-final^{}` → `325c70d5335f57c43a8af85822db25032aa225c3` | exact annotated tag target |
| School Hero | `freeze/hero-final-school-hero-56f99eb` → `56f99eb9ae63272a68accac3041fb10eacefb986` | exact canonical remote branch |

Frozen implementation changes: **0**.

## 9. Per-domain results

| Domain | Identity | Lifecycle | Adapter | Ownership | Versioning | Mutation | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| School Hero | CONFORMS | CONFORMS | CONFORMS | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| ROAD | CONFORMS | CONFORMS | CONFORMS | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| BUILD | CONFORMS | CONFORMS | CONFORMS | CONFORMS | CONFORMS | CONFORMS | CONFORMS |

Each machine-readable record binds the GEN-01 commit and closure hash, adapter contract/version,
mandatory capabilities, optional declarations, all ten invariants, domain-owned responsibilities,
mutation boundary, frozen identity, evidence paths, and deterministic record self-hash.

## 10. Invariant matrix

| Invariant | School Hero | ROAD | BUILD | Overall |
| --- | --- | --- | --- | --- |
| GINV-01 canonical identity | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| GINV-02 no identity fallback | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| GINV-03 fail-closed dependencies | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| GINV-04 deterministic identity where promised | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| GINV-05 domain ownership | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| GINV-06 traceable lifecycle | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| GINV-07 no unauthorized mutation | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| GINV-08 explicit versioning | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| GINV-09 capability honesty | CONFORMS | CONFORMS | CONFORMS | CONFORMS |
| GINV-10 frozen compatibility | CONFORMS | CONFORMS | CONFORMS | CONFORMS |

Mandatory invariant failures: **0**. Unresolved mandatory evidence: **0**.

## 11. Capability matrix

All twelve GEN-01 mandatory capabilities conform for all three domains. Optional declarations are:

| Optional capability | School Hero | ROAD | BUILD |
| --- | --- | --- | --- |
| Rollback evidence | CONFORMS_AS_OPTIONAL_CAPABILITY | CONFORMS_AS_OPTIONAL_CAPABILITY | CONFORMS_AS_OPTIONAL_CAPABILITY |
| Activation evidence | NOT_SUPPORTED_BY_DOMAIN | NOT_SUPPORTED_BY_DOMAIN | CONFORMS_AS_OPTIONAL_CAPABILITY |
| Release evidence | NOT_SUPPORTED_BY_DOMAIN | CONFORMS_AS_OPTIONAL_CAPABILITY | CONFORMS_AS_OPTIONAL_CAPABILITY |

Unsupported optional capabilities remain optional and do not reduce conformance. Supported claims
are bound to domain-owned contract evidence.

## 12. Cross-domain contract reuse

Focused tests validate three materially different opaque payload shapes through the same frozen
`nma.generic-lifecycle-envelope/1.0` schema and validate all three capability profiles through the
same frozen `nma.generic-domain-adapter-capability/1.0` schema. No domain-specific contract fork,
stage sequence, payload interpretation, or globally mandatory optional capability is introduced.

## 13. Negative conformance

Deterministic negative tests reject wrong contract versions, wrong identity authority, missing
mandatory fields, false undeclared capability claims, malformed authorization linkage,
unsupported generic fields, injected mutation authority, and incompatible capability
declarations. No schema or assertion was weakened.

## 14. Mutation safety

The conformance artifacts are observational and validation-only. They add no importable production
verifier, dispatcher, executor, mutation authority, or runtime path.

- source mutation: `false`
- writeback: `false`
- automatic repair: `false`
- geometry mutation: `false`
- portrayal mutation: `false`
- production activation: `false`
- authorization bypass: `false`

## 15. Contract and frozen-refactor counts

- GEN-01 contract changes required: **0**
- GEN-01 artifact modifications: **0**
- frozen production changes: **0**
- required frozen refactors: **0**
- production source changes: **0**

## 16. Machine-readable evidence

The three domain records validate against one closed Draft 2020-12 conformance-record schema. The
aggregate matrix validates against its closed Draft 2020-12 schema and reproduces canonical
`matrix_sha256`:

`88f3dbaf756b19045b88cf4e68c431fbc05696873b984b913397677e8fc0f3c1`

## 17. Focused tests

Command:

`PYTHONPATH=src:. python3 -m pytest -q tests/test_cross_domain_contract_conformance_gen02.py`

Result: **16 passed**. The focused suite covers predecessor identity, closure/self-hashes,
contract immutability, all three domain records, all ten invariants, capability honesty,
cross-domain reuse, negative rejection, mutation safety, deterministic evidence, frozen identity,
private-archive hygiene, and exact change scope.

## 18. Regression verification

Canonical results:

- exact GEN-01 detached predecessor: **15 passed**;
- exact GEN-00 detached predecessor: **11 passed**;
- GEN-02 descendant substantive GEN-01 coverage: **14 passed**, with only
  `test_allowed_change_scope_only` deselected;
- GEN-02 descendant substantive GEN-00 coverage: **10 passed**, with only
  `test_gen00_changes_only_four_audit_files_from_frozen_build` deselected;
- Core identity/profile, ROAD and School Core adoption, and School authorization: **46 passed**;
- ROAD-01 resolution, ROAD-02 portrayal decision, and ROAD-03 authorization: **104 passed**;
- BUILD production contract and human policy: **57 passed**, with the two historical
  predecessor-stage dirty/diff assertions deselected;
- public/non-private BUILD-FINAL integrity: **8 passed**, with the private-archive policy replay
  and BUILD-FINAL's own-stage exact-diff assertion deselected.

The exact predecessor suites ran in temporary detached Git worktrees at their mandated commits;
the ignored private archive was exposed through a temporary symlink only for the predecessor's
existing SHA/hygiene assertion, never extracted or inspected, and both worktrees were removed.
The descendant deselections are stage-local scope assertions only; no functional assertion was
weakened or changed. There is no new regression.

## 19. Schema, static, and hash verification

Results:

- Ruff lint: **PASS**;
- Ruff format check: **PASS**;
- new JSON parsing: **PASS**, six files;
- Draft 2020-12 metaschema validation: **PASS**, two schemas;
- schema-instance validation: **PASS**, three records and one aggregate matrix;
- deterministic canonical self-hashes: **PASS**, three records and one matrix;
- GEN-01 predecessor blob equality: **PASS**, six artifacts;
- frozen production/runtime diff: **empty**;
- `git diff --check`: **PASS**;
- exact scope audit: **PASS**, exactly the eight files in section 21.

## 20. Private archive

`data/datasets/112年多維度SHP成果_0502.zip` remains SHA-exact at
`4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`, ignored, untracked,
and unstaged. GEN-02 did not extract it, inspect layer contents, download a replacement, or create a
substitute fixture.

## 21. Exact changed-file list

1. `GEN-02-Completion-Report.md`
2. `data/specifications/nma-gen-02-build-contract-conformance-v1.0.json`
3. `data/specifications/nma-gen-02-cross-domain-contract-conformance-matrix-v1.0.json`
4. `data/specifications/nma-gen-02-road-contract-conformance-v1.0.json`
5. `data/specifications/nma-gen-02-school-hero-contract-conformance-v1.0.json`
6. `schemas/cross-domain-contract-conformance-matrix-v1.0.schema.json`
7. `schemas/domain-contract-conformance-v1.0.schema.json`
8. `tests/test_cross_domain_contract_conformance_gen02.py`

Existing-file modifications: **0**. Production source changes: **0**.

## 22. Final worktree status

The required final state is a clean worktree after commit and push; exact status is recorded in the
post-push delivery.

## 23. Next-gate recommendation

**READY FOR GENERALIZATION FREEZE**

All three existing evidence domains conform with no material unresolved architecture issue.
GEN-02 does not authorize RIVERL, GEN-FINAL, NMA-FINAL, a merge, or a tag.

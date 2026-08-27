# BUILD-FINAL Completion Report

## 1. Final verdict

**PASS — BUILDING PRODUCTION BASELINE FROZEN**

BUILD-FINAL freezes the exact active BUILD-12 Building production baseline. It adds release and
integrity evidence only. It does not change Building behavior, semantics, policy, portrayal,
J13/J17 binding, output profile, PolygonZ derivation, activation behavior, source data, Core, ROAD,
or School Hero.

## 2. Canonical repository

- Origin: `https://github.com/dongpo/topoMap.git`
- Canonical root: `/Users/dongpodeng/Library/Mobile Documents/com~apple~CloudDocs/Projects/topoMap`
- Starting worktree: clean

## 3. BUILD-12 predecessor

- Branch: `build/build-12-controlled-building-production-activation`
- Commit: `fe0f280f52ba374171010e76b1432b3e414ce927`
- Verdict: `PASS — BUILDING PRODUCTION ACTIVATED AND POST-ACTIVATION VERIFIED`

Every supplied starting-gate identity recomputed exactly through the frozen Core provider. Active
state was production true, official portrayal true, and every source mutation, repair, writeback,
and Z-drop permission false. The BUILD-12 post-activation matrix was `20 / 20 PASS`; the controlled
deactivation/reactivation rehearsal was `PASS`.

## 4. Freeze branch

The preparation branch is renamed after the evidence commit exists. The immutable final branch is
`freeze/build-final-<short-FINAL_SHA>`, where the suffix is the first seven hexadecimal characters
of the final commit identified by the annotated release tag.

## 5. FINAL_SHA

`FINAL_SHA` is the exact peeled target of annotated tag `nma-build-v1.0-final`.

The repository follows the established Core/ROAD non-self-referential finalization convention: a
tracked blob cannot contain the SHA of the commit containing that blob. The release tag therefore
provides the in-repository authority, while the exact commit and tag-object identities are recorded
in the final delivery after publication.

## 6. Local/remote branch equality

Publication requires the local final branch, its upstream, and
`refs/heads/freeze/build-final-<short-FINAL_SHA>` on `origin` to resolve to exact `FINAL_SHA`.
Equality is reverified after the normal, non-force push.

## 7. Annotated tag

- Tag: `nma-build-v1.0-final`
- Message: `NMA Building production v1.0 final`
- Type: annotated tag; a lightweight tag is forbidden

## 8. Tag object identity

The tag object is the exact object resolved by `refs/tags/nma-build-v1.0-final`. Its immutable
object SHA is recorded in the final delivery after tag creation.

## 9. Local/remote tag target equality

Publication requires the local peeled tag target and the remote peeled tag target to equal exact
`FINAL_SHA`, and the local and remote annotated tag-object SHAs to be equal. A conflicting existing
tag is a fail-closed stop and is never force-updated.

## 10. Freeze manifest identity

- Path: `data/specifications/nma-build-final-freeze-manifest-v1.0.json`
- Contract: `nma.building-final-freeze/1.0`
- Identity provider: `nma.core.canonical_sha256`
- Hash basis: the complete manifest with `canonical_manifest_sha256` omitted
- Canonical SHA-256: the exact `canonical_manifest_sha256` value in the manifest, independently
  recomputed by the BUILD-FINAL integrity test and fresh-checkout reproduction

No duplicate identity provider, fallback, repair path, or timestamp participates in the identity.

## 11. Activation identity chain

- BUILD-11A authorization:
  `8bae65726aa0c6901927cb3a0a12a875ac766d45ac9e3a793afb23a85effdb0f`
- BUILD-11 readiness:
  `d2ecb53e74f46e279a5672a182b5a9de602c08d4027023d4fb225132bf3d01fb`
- BUILD-10 implementation:
  `2772ce93f81973e1dbbeb2d4ae9bb1307a29dcdcc4a61ca08f382c12b6b3c957`
- Activation ID: `building-activation-03d28cbae50eb2050db4ed08`
- Activation record:
  `6994abb821287aec015e846148b630054d03c826a6d370ceb625816dfa29d08d`
- Activation receipt:
  `d50cd21f5caa0428ae2dbd4f7fd8343b0bfc50e387dbd156b71ecb9a88739cb7`
- Activated baseline:
  `e9ebf1158caef22cb02d98d7ba8bfe4c99df46d4d9e93a47ad234f632a1755b2`

## 12. Production contract identity chain

The manifest binds BUILD-09, BUILD-09E, BUILD-09E1, and BUILD-09E2 evidence lineage, followed by:

- BUILD-09F human production policy:
  `dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1`
- Finalized production contract:
  `5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88`
- BUILD-10 controlled implementation:
  `2772ce93f81973e1dbbeb2d4ae9bb1307a29dcdcc4a61ca08f382c12b6b3c957`

## 13. J13/J17 frozen bindings

- `J13_寶山都市計畫/SHP → J13_BUILD`: source `2968`, derived XY `2968`, annotations
  `2967`, suppressed unsafe placement `1`.
- `J17_新竹科學工業園區特定區計畫(寶山部分)/SHP → J17_BUILD`: source `2839`, derived XY
  `2839`, annotations `2838`, suppressed unsafe placement `1`.

Cross-prefix fallback, global equivalence, automatic substitution, and alternate binding providers
remain forbidden. Unknown and ambiguous packages fail closed.

## 14. Portrayal frozen values

- Annotation: floor count followed by structure; production order `{BUILD_NO}{BUILD_STR}`;
  deterministic local placement with unsafe placement suppression.
- Hatch: official diagonal semantics, `2 mm` spacing, local `45°` angle, procedural canonical
  resource, no missing static SVG dependency.
- Line: official `0.20 mm`; `nma-screen-96dpi-v1`; `96 DPI`; derived
  `0.7559055118110237 px`; `1 px` is not equivalent.
- Colour: official RGB `(0,0,0)`, device `#000000`, opacity `1.0`; `#111111` is forbidden.

## 15. PolygonZ/derived-XY frozen boundary

The exact pipeline is authoritative immutable PolygonZ → non-authoritative, non-writing,
deterministic and separately identified derived XY → portrayal/runtime. Z remains recoverable.
Source repair, writeback, normalization to XY, mutation, and production-reachable legacy destructive
drop-Z remain forbidden.

## 16. Source archive integrity

- Path: `data/datasets/112年多維度SHP成果_0502.zip`
- SHA-256: `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`
- Canonical checkout: present, ignored, untracked, unstaged, byte-exact
- Publication: excluded from Git
- Fresh checkout: no auto-download or substitute fixture; private-source execution fails closed

## 17. Production source integrity

- BUILD-10 implementation file SHA-256:
  `2772ce93f81973e1dbbeb2d4ae9bb1307a29dcdcc4a61ca08f382c12b6b3c957`
- BUILD-12 activation module file SHA-256:
  `a67f79c87072ab23cf546367183a418f60e94baa4fbf48e1d79b93629c4ce484`
- BUILD-FINAL production source changes: none
- BUILD-FINAL source-data changes: none

All policy, contract, readiness, authorization, activation, receipt, baseline, schema, and BUILD-12
evidence file hashes are frozen in the manifest and checked byte-for-byte.

## 18. Core/ROAD/School Hero integrity

- Core final: `nma-core-v1.0-final` →
  `5eb138ae7686502431587743ebce9ddf92c5a799`
- ROAD final: `nma-road-v1.0-final` →
  `325c70d5335f57c43a8af85822db25032aa225c3`
- School Hero canonical freeze:
  `freeze/hero-final-school-hero-56f99eb` →
  `56f99eb9ae63272a68accac3041fb10eacefb986`

The corresponding integrity suites remain unchanged and must pass before publication.

## 19. BUILD historical regression

The BUILD-12 baseline is `682 passed` with five known descendant-scope failures. The canonical
BUILD-FINAL candidate run is `692 passed, 5 inherited failures`: the additive ten-test freeze
integrity module passes in full, and the five exact historical node IDs remain unchanged.
BUILD-FINAL does not weaken or repair them.

## 20. Full-suite result

The BUILD-12 predecessor baseline is `1281 passed, 8 failed`. The canonical BUILD-FINAL candidate
run is `1291 passed, 8 failed`. The ten added passes are the final freeze-integrity tests. The eight
failures comprise the same five historical BUILD descendant-scope assertions and the same three
pre-existing Agentic/demo catalog/freeze drifts. There is no new material Building, Core, ROAD, or
School Hero failure.

After the evidence commit, the clean canonical final checkout is `1292 passed, 7 failed`. Three
worktree-status-based historical scope assertions change disposition on a clean commit: two
subset assertions pass with an empty status, while BUILD-12's exact-parent assertion begins to
reject the later BUILD-FINAL commit. The clean result therefore contains four stage-local
descendant-scope failures plus the same three Agentic/demo failures. This is a scope-assertion
transition only; all BUILD-12 functional, activation, source, Core, ROAD, and School Hero tests pass.

## 21. Known inherited failures

Known inherited/descendant-scope classes are:

1. five stage-local BUILD descendant-scope assertions whose historical scopes intentionally reject
   later BUILD files;
2. the pre-existing PMTiles Agentic demo catalog drift;
3. the pre-existing Agentic v0.3 freeze/source-size drift;
4. the pre-existing Agentic v0.3 Pages candidate-manifest asset drift.

The clean final checkout additionally exercises BUILD-12's exact-parent assertion as an expected
descendant-stage rejection. The manifest records both the five-node pre-commit historical set and
the four-node clean-final historical set explicitly.

No inherited assertion is weakened and no unrelated fix is attempted.

## 22. Fresh-checkout reproduction

After the final branch and annotated tag are pushed, a fresh remote checkout of
`nma-build-v1.0-final` must peel to exact `FINAL_SHA`. It must reproduce manifest identity,
BUILD-09F policy, finalized contract, BUILD-10 implementation, BUILD-11 readiness, BUILD-11A
authorization, BUILD-12 activation identities, frozen file hashes, J13/J17 binding definitions,
portrayal, PolygonZ/XY boundary, active baseline, Core integrity, and all public/non-private tests.

The private archive is not copied into that checkout. Missing-private-source behavior must fail
closed without mutation, download, fixture substitution, or criteria relaxation. Real J13/J17
replay remains separately reproducible only when the exact authorized private archive is supplied.

## 23. Final worktree state

The pre-commit candidate contains exactly three staged evidence files and no unstaged change.
Publication acceptance requires a clean canonical worktree after commit, branch rename, branch
push, tag creation, tag push, and remote/fresh-checkout verification. The private ignored archive
does not appear as tracked, staged, or modified state.

## 24. Post-freeze change policy

The Building production baseline is immutable. The final branch and tag must never be force-moved.
Any future change to Building behavior, semantics, policy, portrayal, binding, output profile,
geometry boundary, activation, production source, or frozen evidence requires a separately
authorized post-freeze issue and a new release identity.

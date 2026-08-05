# NMA v0.2 public-assets release candidate

D21 freezes the repository, bounded public website, runnable review package, and presentation used
for rehearsal. The machine-readable freeze is
[`data/demo/public-assets-rc1.json`](../data/demo/public-assets-rc1.json); run
`make public-assets-rc` to rebuild and verify it.

## Candidate identity

- Release candidate: `nma-public-assets-v0.2-rc1`
- Executable baseline: `nma-demo-v0.2-rc1`
- Repository: `dongpo/topoMap`
- Branch: `codex/nma-v0.2-authoritative`
- Frozen D20 base: `70c71708c8dcbd35204eab710f7bdd0725817ea4`
- Review issue: Linear GEO-77

## Availability audit

| Surface | Candidate state | Evidence |
|---|---|---|
| Public repository | Available | Public repository and draft PR #1; head matched the frozen D20 base when D21 began |
| Runnable assets | Available | Portable ZIP, checksums, verifier, 5/5 scenes, 2/2 abstention controls |
| Presentation RC | Available | 12-slide v0.9 deck; 12/12 source-note blocks; frozen checksum |
| Public website artifact | Ready to deploy | Bounded Pages artifact builds with no missing local links/images and no PMTiles |
| Live GitHub Pages | **Blocking** | On 2026-08-05 the homepage still showed `test`; the demo URL returned GitHub Pages 404 |

Repository readiness is not deployment completion. GEO-77 must remain open until the bounded Pages
artifact is pushed, explicitly approved for deployment, and the live URLs are rechecked.

## Safe public website boundary

The prior Pages workflow uploaded the entire repository, which would also publish the PMTiles
archive before its redistribution terms were confirmed. D21 replaces that path with a curated
artifact built by `scripts/build_public_site.py`.

The public artifact contains:

- the responsive landing page;
- an evidence-only five-scene demo;
- the frozen graph and five-scene contract;
- the architecture image;
- presentation v0.9;
- the portable review ZIP and verification report.

It deliberately excludes `out1120902.pmtiles`, the official source PDF, and repository-only
development/test files. The full live-map RC1 remains the local rehearsal path until the map-data
licence boundary is resolved.

## Verification

```bash
make public-assets-rc
```

The command checks:

- all frozen asset SHA-256 fingerprints;
- the complete Stable Demo RC1 gate;
- the bounded Pages workflow and public-site file list;
- local landing-page links and images;
- review-package integrity and scene count;
- presentation slide count and `[Sources]` notes;
- quickstart install, verification, preview, and demo commands;
- explicit blocking/deferred defect classifications.

The install sequence is also rehearsed from a clean local environment before D21 approval.

## Defect triage

### Blocking

- `pages-not-yet-public-assets-rc1`: the live Pages site is still the old main-branch placeholder.
  After the D21 commit is pushed, deployment requires explicit user approval and a live URL check.

### Deferred

- `pmtiles-redistribution`: confirm redistribution terms or replace the archive with clearly
  licensed public data.
- `cartographer-signoff`: obtain independent review before publication-grade authority claims.
- `sealed-held-out-benchmark`: seal held-out tasks and run named baselines before paper submission.

## Post-freeze policy

After approval, changes are limited to correctness, clarity, reliability, and conference needs.
New scenes, new portrayal profiles, and unsupported factual claims require a new reviewed release
candidate rather than an in-place edit.

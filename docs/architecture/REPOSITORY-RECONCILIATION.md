# AMA canonical repository reconciliation

Audit date: 2026-08-27 (Asia/Taipei). Repository:
`https://github.com/dongpo/topoMap`.

## Starting state

| Ref or state | Exact value |
| --- | --- |
| original local worktree branch | `app/app-standalone-file-layout` |
| original local worktree SHA | `ac350c8fcef6e58d820ee6da456b1d1f0ef012f6` |
| original worktree | not clean: untracked `.DS_Store`, `agent_contracts/`, `artifacts/`, `build_contracts/`, `data/`, `src/` |
| local `main` | `1f3c886b3dcc61a5ee74c46e7cd7a9be5c668a3d` |
| `origin/main` | `0620e75705338f2096a7c9ef9a1f2de185a46577` |
| peeled `nma-v1.0-final` | `eb87bde775333811529efb6f651573ea21cf456b` |
| `origin/contrib/ama-open-research-software` | `00252f32647be08476157237d8025dad9b062ed1` |

The original dirty worktree was not switched or edited. Reconciliation was performed in an
isolated Git worktree on `codex/ama-canonical-reconciliation`.

## History topology

`1f3c886b3dcc61a5ee74c46e7cd7a9be5c668a3d` is the merge base for local `main`,
`origin/main`, and the peeled NMA final tag. It is also the merge base of `origin/main` and the AMA
contribution branch. The peeled `nma-v1.0-final` commit is the merge base of that tag and
`origin/contrib/ama-open-research-software`.

The contribution branch contains four documentation-only commits on the frozen implementation.
Current `origin/main` contains twelve Pages commits on the earlier common ancestor. The canonical
reconciliation therefore retains the contribution branch content and merges `origin/main` as a
second parent. Both public histories remain reachable without rewriting either one.

## Tree comparison

The peeled NMA final tree contains 628 files absent from the starting GitHub `main`. Entire
top-level implementation/evidence trees absent from `main` were `agent_contracts/`, `artifacts/`,
`assets/`, `benchmark/`, `build_contracts/`, `data/`, `release/`, `schemas/`, `src/`, and `tools/`.
It also contained 104 test files versus one on `main`, 24 tag-only scripts, 31 tag-only docs, the
package metadata, licence/citation/contribution files, and historical root reports now surfaced by
the index under `docs/engineering-history/`.

The starting GitHub `main` contained exactly these 30 files absent from `nma-v1.0-final`:

```text
NMA-DEPLOY-GHP-01-Completion-Report.md
build-demo/data/specifications/nma-build-05-authorization-consumption-v1.0.json
build-demo/data/specifications/nma-build-05-golden-execution-package-v1.0.json
build-demo/data/specifications/nma-build-07-golden-evaluation-template-v1.0.json
build-demo/index.html
docs/DEPLOY-GHP-03-UNIFIED-SHAPEFILE-PAGES.md
public/gh-pages/.nojekyll
public/gh-pages/app.css
public/gh-pages/app.js
public/gh-pages/assets/NotoSans-LICENSE.txt
public/gh-pages/assets/NotoSansRegular-0-255.pbf
public/gh-pages/assets/NotoSansRegular-19968-20223.pbf
public/gh-pages/assets/NotoSansRegular-23552-23807.pbf
public/gh-pages/assets/NotoSansRegular-34816-35071.pbf
public/gh-pages/assets/fflate-0.8.3-LICENSE.txt
public/gh-pages/assets/fflate-0.8.3.min.js
public/gh-pages/assets/maplibre-gl-4.7.0-LICENSE.txt
public/gh-pages/assets/maplibre-gl-4.7.0.css
public/gh-pages/assets/maplibre-gl-4.7.0.js
public/gh-pages/assets/shpjs-6.2.0-LICENSE.txt
public/gh-pages/assets/shpjs-6.2.0.min.js
public/gh-pages/data/nma-runtime-knowledge-v0.4.json
public/gh-pages/index.html
public/gh-pages/landing.css
public/gh-pages/landing.js
public/gh-pages/release.json
public/gh-pages/run.html
scripts/build_gh_pages_knowledge_projection.py
scripts/build_gh_pages_release_manifest.py
tests/test_gh_pages_static_demo.py
```

The exact tag-only list is reproducible with:

```bash
comm -23 \
  <(git ls-tree -r --name-only nma-v1.0-final^{}) \
  <(git ls-tree -r --name-only origin/main)
```

## Pages, versions, licence, and CI

GitHub Pages is deployed by `.github/workflows/static.yml` using GitHub Actions. The accepted
starting `main` run `32751420864` succeeded at `0620e75705338f2096a7c9ef9a1f2de185a46577`,
and the public URL returned HTTP 200. The workflow tests and uploads only `public/gh-pages`, so
placing canonical source on `main` does not make source layout and Pages compete.

Starting version identities were mixed but intentionally distinct: README/package/citation
metadata used `0.2`/`0.2.0`; frozen annotated evidence tags used v1.0 names; and v0.3/v0.32 plus
deployment schema identities named bounded historical candidates/artifacts. The reconciliation
keeps package version `0.2.0`, adopts AMA branding, and creates no AMA release tag.

The frozen software line contains Apache-2.0 `LICENSE` and `NOTICE`; synthetic fixtures are CC0-1.0
where marked, while official PDFs and private archives are not redistributed. Starting `main`
lacked `LICENSE`, so GitHub reported no detected repository licence.

The software line contains 104 test files and 1,457 collected tests. Starting CI failed before
pytest at Ruff `F841` in `src/nma/graphrag.py` (unused local `documents`); this was a pre-existing
failure at the frozen tag and contribution branch. Pages acceptance CI on starting `main` passed.

## Reconciliation policy

- Never modify, recreate, or retag a frozen tag.
- Preserve historical evidence content and embedded legacy paths. Keep path-bound frozen reports
  at their original locations, index them under `docs/engineering-history/`, and verify frozen
  payloads against their original snapshots.
- Treat AMA as public branding, not as a new release.
- Keep `national-map-agent`, `nma`, schemas, manifests, and frozen identifiers compatible.
- Keep software conformance separate from scientific validation of RQ1–RQ3.

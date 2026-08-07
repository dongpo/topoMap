# D24 · Public delivery and link audit

Validated: 2026-08-07 (Asia/Taipei)

Candidate commit: `2408b4104f1a7ce43e6c975bd562562ca715d388`

Scope: Q&A, public links, QR targets, and non-slide public copy. Presentation slides, speaker notes,
and PDF are excluded by owner instruction.

## Public entry points

| Entry | Validation result | Evidence and boundary |
|---|---|---|
| [Repository](https://github.com/dongpo/topoMap) | pass | Public repository; default branch is `main`. |
| [Candidate branch](https://github.com/dongpo/topoMap/tree/codex/nma-v0.2-authoritative) | pass | Public; head was `2408b41` when this audit began. This branch contains Agentic v0.3 work. |
| [Draft PR #1](https://github.com/dongpo/topoMap/pull/1) | attention | Open, draft, and mergeable. Latest `verify` run failed only at the formatting check; see release blockers below. |
| [Stable RC1 tag](https://github.com/dongpo/topoMap/tree/nma-demo-v0.2-rc1) | pass | Frozen D17 executable baseline at `19b2341`. |
| [Public landing page](https://dongpo.github.io/topoMap/) | pass | Loaded in a clean browser with the architecture image and no console errors. This is the bounded v0.2 RC1 release. |
| [Public evidence-only demo](https://dongpo.github.io/topoMap/nmaAgentDemo.html?mode=degraded) | pass | All five controls returned their expected code and page; no console errors. PMTiles is intentionally excluded. |
| [Two-minute quickstart](https://github.com/dongpo/topoMap/blob/codex/nma-v0.2-authoritative/docs/QUICKSTART.md) | pass | Present and readable on the candidate branch. |
| [Architecture](https://github.com/dongpo/topoMap/blob/codex/nma-v0.2-authoritative/docs/ARCHITECTURE.md) | pass | Present and readable on the candidate branch. |
| [D24 Q&A](D24-QA.md) | candidate | Repository-local review candidate; becomes public only after push. |
| [NLSC112V5.4 specification](https://drive.google.com/file/d/1KQN1GCwVPFSms3IUi4pmNqM4ru3TYVrZ/view) | pass | Drive connector returned an 83-page PDF titled *一千分之一地形圖圖式規格表 NLSC112V5.4 版_2024-02-28*. |
| Review package and presentation downloads | manifest pass | Paths are present in the bounded D21 release manifest. They were not manually re-downloaded in this audit; presentation content is owner-controlled. |

## Version boundary that must remain visible

The public Pages site is the stable **v0.2 RC1 evidence-only** release. The candidate branch and
local preview contain the newer **Agentic v0.3** conversation, symbol workshop, 42-entry capability
catalog, and supervised layer workflow. D24 does not silently deploy v0.3 or describe it as already
public.

Publishing v0.3 requires a separate bounded deployment approval and a new browser acceptance pass.

## QR deliverables

The QR images are presentation-independent handoff assets. Their exact payloads and checksums are
recorded in [`artifacts/public/d24/qr-manifest.json`](../artifacts/public/d24/qr-manifest.json).

| Asset | Target | Recommended use |
|---|---|---|
| `nma-public-demo.png` | public evidence-only demo | Audience live access to the stable five-scene result |
| `nma-candidate-branch.png` | exact candidate branch | Reviewer access to Agentic v0.3 source and audit trail |

## Release blockers and pending gates

### CI formatting correction completed locally

The latest remote PR workflow still represents candidate commit `2408b41` and is red at
`ruff format --check`. The owner approved the correction on 2026-08-07. The five reported files
were formatted in local commit `4fd6214`, and the remaining three repository-format drifts were
normalized while building the v0.3 freeze:

- `src/nma/demo_offline.py`
- `tests/test_agentic_demo_acceptance.py`
- `tests/test_agentic_demo_graph.py`
- `tests/test_agentic_demo_layers.py`
- `tests/test_agentic_demo_workshop.py`
- `scripts/build_pmtiles_capability_catalog.py`
- `scripts/build_public_site.py`
- `scripts/run_nma_agent_server.py`

Local `ruff check` and `ruff format --check` now pass for `src`, `tests`, `benchmark/adapters`, and
`scripts`. The remote status cannot turn green until the local commits are pushed and Actions runs
against the new head.

### Agentic v0.3 candidate re-freeze completed locally

The Agentic v0.3 freeze now fingerprints 31 current artifacts and verifies A01–A06, five scenes,
the 42-entry catalog, the 44-node/85-edge graph, the supervised school Shapefile, and all three
historical v0.2 release snapshots. The full **101-test** repository suite passes locally.

The freeze is recorded in [`AGENTIC-V0.3-FREEZE.md`](AGENTIC-V0.3-FREEZE.md) and
`data/demo/agentic-v0.3-freeze.json`. It preserves the deployed v0.2 Pages identity and explicitly
records v0.3 as `not-deployed`.

### Publication gates

- `CITATION.cff` is present, but no DOI or archival identifier is recorded.
- Independent cartographer and expert review remain pending.
- The 21-task benchmark is a development set; held-out named-model evaluation remains pending.
- PMTiles redistribution permission remains unconfirmed.
- The public site does not yet host Agentic v0.3.

## Validation methods

- GitHub repository, branch, tag, pull-request, file, and Actions metadata were read through the
  authenticated GitHub connection.
- Public Pages were exercised in the browser; all five stable scene controls and the browser
  console were checked.
- The NLSC Drive source was fetched through the authenticated Drive connection and checked against
  the five cited records.
- Repository manifests and documentation were inspected locally. Absence of a DOI was checked
  across the repository.

## Owner review checklist

- [ ] Approve the D24 Q&A wording.
- [ ] Scan both QR images from a phone or independent scanner.
- [x] Approve and complete the formatting-only CI correction locally.
- [x] Build and verify a separate Agentic v0.3 re-freeze locally.
- [ ] Decide whether Agentic v0.3 should receive a bounded public Pages deployment.
- [ ] Insert selected QR assets into owner-controlled presentation materials, if desired.

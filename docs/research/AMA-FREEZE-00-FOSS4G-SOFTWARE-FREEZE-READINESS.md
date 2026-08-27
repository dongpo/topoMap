# AMA-FREEZE-00 — FOSS4G Software Freeze Readiness

## Verdict

**PASS WITH CLASSIFIED NON-BLOCKING DEBT — READY TO MERGE AND FREEZE**

The accepted commit `b2cb911e81c7455bb525de87921edd932c9def82` is designated the
**FOSS4G SOFTWARE FREEZE CANDIDATE**. This is a release-governance designation only. No release
tag was created, PR #4 was not merged, and no `ama-v1.0` tag exists.

This readiness record is intentionally not committed: the milestone requires the canonical branch
and candidate SHA to remain exactly `b2cb911e81c7455bb525de87921edd932c9def82`.

## Canonical lineage and Git identity

All three required ancestry checks passed:

```text
34c7ef011d2bf7e9c067ac6cac2bc1a1d75dc117
  -> 95ec58515d381a7d694199a526fbad4d5e3e8e25
  -> b2cb911e81c7455bb525de87921edd932c9def82
```

- `95ec585...` has the single parent `34c7ef...`.
- `b2cb911...` has the single parent `95ec585...`.
- `git replace -l` returned no replacement objects.
- Local, fetched upstream, and direct remote refs for each milestone initially matched the accepted
  identities.
- `codex/ama-canonical-reconciliation` was advanced from `34c7ef...` to `b2cb911...` by an exact
  compare-and-swap ref update and a normal fast-forward push. No merge, rebase, squash,
  cherry-pick, force push, or commit rewrite occurred.
- Operator starting checkout (preserved untouched): `app/app-standalone-file-layout` at
  `ac350c8fcef6e58d820ee6da456b1d1f0ef012f6`, with pre-existing untracked user files.
- Canonical branch starting SHA: `34c7ef011d2bf7e9c067ac6cac2bc1a1d75dc117`.
- Final canonical branch and SHA: `codex/ama-canonical-reconciliation` at
  `b2cb911e81c7455bb525de87921edd932c9def82`.
- The isolated canonical validation worktree was clean after validation; ignored build, environment,
  and demo-run outputs were not added to Git.

## PR #4 status

At the final candidate head:

- state: open;
- draft: no;
- head: `codex/ama-canonical-reconciliation` at `b2cb911...`;
- base: `main`;
- mergeable: yes;
- merge state: clean;
- canonical push CI run `33056707051`: success;
- canonical pull-request CI run `33056711077`: success;
- latest deployed Pages workflow run `32751420864`: success;
- PR #4 was not merged.

## Changed-scope audit (`34c7ef...` to `b2cb911...`)

Exact scope: **20 files**, **18 added**, **2 modified**, **3,679 insertions**.

### Provider-neutral LLM runtime

- `src/nma/llm/__init__.py`
- `src/nma/llm/base.py`
- `src/nma/llm/ollama.py`

### RQ1 and RQ2 mechanisms

- `src/nma/research_runtime.py`
- `data/research/ama-demo-02-school-plan-catalog-v1.0.json`

### RQ3 governance bridge

- `src/nma/research_governance_adapter.py`

### Research CLI and demo packaging

- `src/nma/research_cli.py`
- `src/nma/demo_reporting.py`
- `pyproject.toml` (adds only the research-demo entry point; package version remains `0.2.0`)

### Research documentation

- `docs/research/AMA-DEMO-02-PROVIDER-NEUTRAL-LIVE-RUNTIME.md`
- `docs/research/AMA-DEMO-03-RQ-ALIGNED-PACKAGING.md`
- `docs/research/AMA-DEMO-03-RUNBOOK.md`

### Tests and maintained integration support

- `tests/ama_demo02_support.py`
- `tests/conftest.py`
- `tests/test_ama_demo02_rq1.py`
- `tests/test_ama_demo02_rq2.py`
- `tests/test_ama_demo02_rq3.py`
- `tests/test_ama_demo03_rq1_packaging.py`
- `tests/test_ama_demo03_rq2_packaging.py`
- `tests/test_ama_demo03_rq3_packaging.py`

No file fell outside the allowed categories. The delta contains no frozen ROAD, School, or BUILD
semantic change; no Pages asset/workflow change; no historical evidence change; no package or CLI
rename; no version change; and no tag movement.

## RQ1 freeze gate

`python -m nma.research_cli rq1` passed live using local Ollama/Qwen.

- provider: `ollama`;
- model: `qwen2.5:3b`;
- requested and active graph backend: `canonical-json`;
- canonical graph identity: `nma-canonical-graph-v0.4`;
- scenario: non-special-case fire hydrant `9350906`;
- evidence node count: 28;
- citation count: 1;
- evidence IDs valid: pass;
- citation IDs valid: pass;
- unsupported evidence invented: no;
- grounded-answer validation: pass.

GraphRAG executed, evidence reached Qwen, and the grounded answer retained the reviewed
non-executable mapping status.

## RQ2 freeze gate

`python -m nma.research_cli rq2` passed live using the same provider, model, and graph.

- natural-language School request reached Qwen;
- GraphRAG evidence node count: 56, with seven authoritative citations in retrieved context;
- feature/classification `9920103`, `TERRAINID`, Point geometry, source archive identity, six source
  layers, field mapping, operation vocabulary, evidence IDs, and citation IDs all validated;
- no execution authority was embedded;
- deterministic invalid companion changed the field to `INVENTED_FIELD`, was rejected at
  deterministic plan validation, and reached execution: **NO**.

## RQ3 freeze gate and trust boundary

The valid and unsafe commands both passed.

The valid case produced eight distinct authority-class identities: proposal, evaluation, decision
record, Agent Run Record, authorization handoff, existing School authorization, execution, and
verification/receipt. It reached the existing School executor and independent verifier with the
authorization-bound archive digest
`4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`.

The unsafe case failed deterministic plan validation and reported:

- handoff created: no;
- domain authorization consumed: no;
- execution reached: no;
- verification needed: no, because execution did not occur.

Runtime behavior and focused tests proved the invariants:

- LLM can authorize: **NO**;
- evaluation can authorize: **NO**;
- human review alone can authorize domain execution: **NO**;
- Agent Run Record can authorize: **NO**;
- authorization handoff can authorize: **NO**;
- separate domain authorization required: **YES**;
- independent post-execution verification required: **YES**.

## Provider-neutral runtime gate

- No cloud key or OpenAI Responses API was used or required.
- The only configured implementation is local Ollama; unsupported providers fail closed with no
  fallback.
- Provider and model are explicit in console and machine artifacts.
- Provider response/session/tool-call IDs do not cross the adapter and are not canonical AMA
  identities.
- Machine artifacts retain provider/model plus bounded results; hidden reasoning or chain-of-thought
  is not persisted or exposed.
- Formosa-1 remains an extension point only; it was not implemented or integrated.

## Graph backend gate

Canonical JSON passed all four live scenarios. Its trace reported requested backend
`canonical-json`, active backend `canonical-json`, fallback used `false`, and canonical identity
`nma-canonical-graph-v0.4`.

No complete local Neo4j configuration was available. A deterministic activation probe requesting
Neo4j with explicit canonical fallback reported active backend `canonical-json`, fallback used
`true`, and reason `neo4j-settings-incomplete`. This optional absence does not block the freeze;
the fallback is explicit and the active canonical graph remains authoritative.

## Demo runbook gate

The documented clean-checkout sequence was reproduced in an isolated Python 3.11 environment:
project install, local Ollama/Qwen readiness, repository asset checks, RQ1, RQ2, RQ3 valid, and RQ3
unsafe. GDAL/OGR and the exact private School archive were available. No undocumented mutable state
was required beyond the dependencies/assets named in the runbook.

## Public Pages isolation gate

- `public/gh-pages` and `.github/workflows/static.yml` are byte-identical between `34c7ef...` and
  `b2cb911...`.
- The deployment workflow still uploads only `public/gh-pages` (21 tracked files).
- Current static acceptance: 14/14 passed.
- Current public-runtime scan found no Qwen/Ollama/research CLI configuration, cloud key marker, or
  Neo4j credential variable.
- Qwen, Neo4j, private data, local research artifacts, credentials, and the research CLI are not
  part of the public backend or deployed artifact.

## Historical freeze integrity

- annotated tag objects: 9/9 exact locally and remotely;
- peeled targets: 9/9 exact locally and remotely;
- separate exact-release workflow scopes: 9/9 passed, 223 tests total;
- current-tree historical marker discovery: exactly 38 nodes;
- historical assertions and evidence were not edited, weakened, retargeted, or reclassified to hide
  current failures.

## Canonical CI and exact validation counts

| Gate | Result |
| --- | --- |
| AMA-DEMO-02 focused | 13 passed |
| AMA-DEMO-03 focused | 7 passed |
| RQ1 focused | 6 passed |
| RQ2 focused | 6 passed |
| RQ3 focused | 8 passed |
| Live Qwen scenarios | 4/4 passed |
| RQ2 invalid companion | 1/1 rejected before execution |
| RQ3 unsafe scenario | 1/1 rejected before handoff/execution |
| Canonical maintained pytest | 1,457 passed, 1 skipped; 1,458 selected; 38 historical deselected |
| Current Core/Agent/benchmark focused | 169 passed; 9 historical deselected |
| ROAD verifier | 39 passed |
| School execution/verifier | 14 passed |
| Pages acceptance | 14 passed |
| Package build | sdist + wheel built |
| Isolated install/import | `nma` / `national-map-agent==0.2.0` passed |
| Repository CLI smoke | `nma --help`, grounded ask, `nma-bench --help`, research CLI help passed |
| AMA-Bench | 21 tasks; full NMA accuracy/evidence/graph = 1.000/1.000/1.000 |
| Knowledge rebuild | 10 observations -> 44 nodes / 85 edges; byte-identical |
| MapLibre style rebuild | 133 layers; byte-identical |
| PMTiles reproduction | passed |
| Maintained Ruff | passed |
| Maintained Ruff format | 171 files clean |
| Historical tag verification | 9/9 objects and 9/9 peeled targets exact |
| Historical exact-release scopes | 9/9 scopes, 223 tests passed |

Both push- and pull-request-triggered canonical GitHub CI completed successfully at the exact
candidate SHA.

## Remaining classified debt

One non-blocking packaging portability limitation was found beyond the required CI/install/import
gate: the wheel-only `ama-research-demo` entry point cannot start outside a repository checkout
because the long-standing top-level `agent_contracts` package is repository-scoped and is not
included in the wheel. The supported FOSS4G runbook is a clean repository checkout with editable
install, and all four live demos passed through that boundary. The normal wheel build, isolated
`nma` import/version check, and maintained CLI smoke all pass. This debt must not be repaired during
the freeze unless a later, explicit blocker-repair milestone expands the distribution boundary.

Optional Neo4j unavailability is also classified and non-blocking because canonical JSON is healthy
and authoritative.

## Scientific-claim boundary

The software demonstrates executable RQ1 knowledge grounding, RQ2 constrained planning, and RQ3
governance/authorization/verification mechanisms. It does not establish statistical superiority,
GraphRAG superiority, Qwen superiority, human trust, institutional safety, or reduced failure rates.
Publication-grade RQ evaluation remains future work.

RQ1–RQ3 software mechanisms are frozen as engineering evidence only; scientific hypothesis
validation remains post-FOSS4G work.

## FOSS4G freeze recommendation

READY TO MERGE PR #4.

NO FURTHER AMA ARCHITECTURE OR FEATURE DEVELOPMENT BEFORE FOSS4G.

NEXT: MERGE → FRESH-MAIN REPRODUCTION → FOSS4G SOFTWARE FREEZE.

# AMA-FREEZE-01 — FOSS4G Software Freeze Report

## Final verdict

**PASS WITH CLASSIFIED NON-BLOCKING PACKAGING DEBT — FOSS4G SOFTWARE FROZEN**

PR #4 was merged without rewriting accepted history. Merged `main` was reproduced from a fresh
remote checkout, the RQ1–RQ3 live mechanisms and release-critical gates passed, historical releases
remain exact, Pages remains static and isolated, and this report is part of the one permitted
evidence-only freeze commit.

The committed report uses `self` for the evidence commit and the annotated tag object because Git
objects cannot contain their own future object IDs. The normative resolution is the peeled target
of `ama-foss4g-2026-freeze`; the final operator handoff records the resolved commit and tag-object
SHAs after creation and remote verification.

## Merge and Git identity

| Identity | Value |
| --- | --- |
| PR | `#4` |
| Merge method | normal merge commit; no squash or rebase |
| PR head before merge | `b2cb911e81c7455bb525de87921edd932c9def82` |
| Accepted software candidate | `b2cb911e81c7455bb525de87921edd932c9def82` |
| `main` before merge | `0620e75705338f2096a7c9ef9a1f2de185a46577` |
| PR merge commit / merged software predecessor | `a1d6e758408f8bb51a3ed725b86b153ccba32569` |
| `main` immediately after merge | `a1d6e758408f8bb51a3ed725b86b153ccba32569` |
| Candidate tree | `89bd251e886ae8cc02e3e62969b0a98c9419633e` |
| Merged-main tree | `89bd251e886ae8cc02e3e62969b0a98c9419633e` |
| Tree equivalence | PASS |
| Evidence commit | `self` = `ama-foss4g-2026-freeze^{}` |
| Freeze tag | `ama-foss4g-2026-freeze` (annotated) |
| Tag object | resolved after tag creation with `git rev-parse refs/tags/ama-foss4g-2026-freeze` |
| Tag target | `self`, resolved with `git rev-parse refs/tags/ama-foss4g-2026-freeze^{}` |

The merge commit has the two required parents: pre-merge `main` first and the accepted candidate
second. Merged `main` contains the candidate, preserves both histories, and introduces no software
content difference relative to the accepted candidate.

After the merge, local `main`, its upstream, and `origin/main` were equal at `a1d6e758...` and the
isolated main worktree was clean. The evidence commit advances all three together only after these
reproductions pass.

## Fresh-main reproduction identity and readiness

- fresh checkout: `/private/tmp/ama-freeze-fresh-main.uPBJO4/checkout`;
- checkout source: merged remote `main`;
- exact checkout SHA: `a1d6e758408f8bb51a3ed725b86b153ccba32569`;
- Python: 3.11.9 in a newly created virtual environment;
- install: `pip install -e '.[dev]'`;
- import/version: `nma` / `national-map-agent==0.2.0` PASS;
- provider/model: local `ollama` / `qwen2.5:3b`;
- graph: authoritative `canonical-json` / `nma-canonical-graph-v0.4`;
- Neo4j: optional and not required; explicit canonical JSON fallback remains healthy;
- GDAL/OGR: available;
- School archive digest: `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`, exact authorization match;
- readiness: **READY**.

The initial clone used a deliberately narrow single-branch refspec. Two maintained identity tests
correctly required one historical remote branch ref. Fetching the full remote ref namespace—normal
fresh-clone setup, with no content change—made both pass; the complete suite then passed. This was a
checkout-scope observation, not a software defect.

## RQ1 live reproduction

`python -m nma.research_cli rq1` passed:

- non-special-case fire hydrant `9350906`;
- provider-neutral local Qwen, no cloud key and no OpenAI Responses API dependency;
- GraphRAG evidence injected into the answer;
- backend identity visible as canonical JSON;
- 28 evidence nodes and 1 citation;
- evidence IDs valid, citation IDs valid, unsupported evidence invented: no;
- grounded-answer validation: PASS.

## RQ2 live reproduction

`python -m nma.research_cli rq2` passed:

- natural-language School `9920103` request reached local Qwen;
- 56 GraphRAG evidence nodes and seven authoritative retrieved citations;
- feature, `TERRAINID` classification/field mapping, Point geometry, six source layers, source archive,
  allowed operations, evidence IDs, and citation IDs all passed deterministic validation;
- no execution authority was embedded;
- invalid companion injected `INVENTED_FIELD`, was rejected at deterministic plan validation, and
  execution reached: **NO**.

## RQ3 valid and unsafe reproduction

`python -m nma.research_cli rq3 --case valid` passed the complete chain with distinct identities:
request, probabilistic proposal, deterministic evaluation, human decision, Agent Run Record,
non-authorizing handoff, separate existing School authorization, School execution, and independent
verification/receipt.

Trust-boundary facts reproduced at runtime and in tests:

- LLM can authorize: **NO**;
- evaluation can authorize: **NO**;
- human review alone can authorize domain execution: **NO**;
- Agent Run Record can authorize: **NO**;
- authorization handoff can authorize: **NO**;
- separate domain authorization required: **YES**;
- independent verification required: **YES**.

`python -m nma.research_cli rq3 --case unsafe` injected an invalid field and deterministically
reported handoff created **NO**, domain authorization consumed **NO**, and execution reached **NO**.

## Exact current validation results

| Gate | Result |
| --- | --- |
| AMA-DEMO-02 focused | 13 passed |
| AMA-DEMO-03 focused | 7 passed |
| RQ1 focused | 6 passed |
| RQ2 focused | 6 passed |
| RQ3 focused | 8 passed |
| Live Qwen RQ1 | PASS |
| Live Qwen RQ2 | PASS |
| Live Qwen RQ3 valid | PASS |
| RQ2 invalid companion | PASS; rejected before execution |
| RQ3 unsafe | PASS; no handoff/authorization consumption/execution |
| Canonical maintained pytest | 1,457 passed, 1 classified optional skip; 1,458 selected; 38 historical deselected |
| Core/Agent/benchmark focused | 169 passed; 9 historical deselected |
| ROAD verifier | 39 passed; authorization-consumption verifier PASS |
| School execution/verifier | 14 passed; live independent verifier PASS |
| Pages acceptance | 14 passed |
| Package editable install/import | PASS |
| Package build | sdist + wheel PASS |
| Isolated wheel install/import | `nma` / 0.2.0 PASS |
| CLI smoke | `nma --help`, grounded ask, `nma-bench --help`, research CLI help PASS |
| AMA-Bench | 21 tasks; full NMA accuracy/evidence/graph = 1.000/1.000/1.000 |
| KG rebuild | 10 observations → 44 nodes / 85 edges; byte-identical |
| MapLibre style rebuild | 133 layers; byte-identical |
| PMTiles reproduction | PASS |
| Maintained Ruff | PASS |
| Maintained format | 171 files clean |
| Historical tags/targets | 9/9 objects and 9/9 peeled targets exact locally/remotely |
| Historical exact-release scopes | 9/9, 223 tests passed |
| Post-merge canonical CI | PASS, run `33059604199` |
| Post-merge Pages deployment | PASS, run `33059604233` |
| Freeze-integrity verifier | PASS before tag; must PASS with `--require-tag --remote origin` after push |

## Historical integrity

All nine historical annotated tag objects and peeled targets are unchanged and exact locally and
remotely. The exact-release scopes passed by tag with counts `17 + 4 + 2 + 104 + 48 + 10 + 10 +
14 + 14 = 223`. No tag moved, no assertion was weakened, and no historical evidence changed.

## Pages isolation

Pages remains a static GitHub Pages deployment that uploads only `public/gh-pages`. The focused
acceptance suite passed 14/14, and the post-merge deployment passed. The public artifact contains no
live Qwen dependency, Neo4j dependency or credentials, private School data, research backend,
credentials, or mutable runtime artifacts.

## Provider-neutral model boundary

AMA is the architecture; Qwen is the validated replaceable local model. The adapter exposes the
provider/model without promoting provider session IDs or hidden reasoning into AMA identities. No
cloud key or cloud fallback is required. Formosa-1 and additional models/domains were not added.

## Known non-blocking packaging debt

The wheel-only `ama-research-demo` entry point currently expects repository-scoped
`agent_contracts`; an isolated wheel-only invocation reproduced `ModuleNotFoundError:
agent_contracts`. This is the already classified non-blocking limitation. The supported FOSS4G
workflow—clean checkout plus editable install—works fully and reproduced all four live scenarios.
It is not repaired in this freeze.

## Freeze manifest and evidence scope

The manifest is `data/specifications/ama-foss4g-2026-freeze-manifest.json`. It distinguishes the
validated software predecessor `a1d6e758...` from the evidence-only `self` commit resolved by the
peeled tag target. Its canonical self-hash, package/version, required RQ paths/docs, historical tags,
parent identity, exact four-file evidence scope, and tag target are checked by
`scripts/verify_ama_foss4g_freeze.py`.

The evidence commit contains only:

- this report;
- the AMA-FREEZE-00 readiness report;
- the freeze manifest;
- the freeze-identity verifier.

No runtime, RQ mechanism, graph, adapter, planning, governance, domain, package version, or Pages
content changes.

## Fresh-tag reproduction

After the annotated tag is pushed, a new checkout of `ama-foss4g-2026-freeze` must rerun and record:

- editable install and package import/version;
- `nma --help`, `nma-bench --help`, and research-demo help;
- AMA-DEMO-02 focused mechanism tests (13);
- AMA-DEMO-03 focused packaging tests (7);
- one deterministic non-network RQ set;
- historical tag integrity;
- `scripts/verify_ama_foss4g_freeze.py --require-tag --remote origin`.

The resolved checkout identity and exact rerun results are part of the final operator handoff. No
second full live Qwen run is required because tag-target equality supplies the new identity evidence.

## Scientific-claim boundary

RQ1–RQ3 are frozen as executable software mechanisms and engineering evidence.

The FOSS4G freeze does not establish statistical superiority of GraphRAG over vector RAG or LLM-only
approaches.

It does not establish statistically improved reliability or institutional safety.

Publication-grade hypothesis testing remains post-FOSS4G work.

## Development-freeze statement

AMA FOSS4G SOFTWARE DEVELOPMENT IS FROZEN.

NO FURTHER ARCHITECTURE, FEATURE, MODEL, DOMAIN, OR DEMO-SEMANTICS CHANGES BEFORE FOSS4G.

RQ1–RQ3 SOFTWARE MECHANISMS ARE FROZEN AS ENGINEERING EVIDENCE ONLY.

SCIENTIFIC HYPOTHESIS VALIDATION REMAINS POST-FOSS4G WORK.

NEXT SOFTWARE WORK AFTER FOSS4G: PUBLICATION-GRADE EXPERIMENT DESIGN, NOT FEATURE DEVELOPMENT.

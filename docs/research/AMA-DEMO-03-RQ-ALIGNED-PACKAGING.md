# AMA-DEMO-03 RQ-Aligned Research Demo Packaging Audit

## Verdict

`PASS — RQ-ALIGNED RESEARCH DEMOS PACKAGED AND REPRODUCIBLE`

All three local Qwen mechanisms, the RQ2 invalid companion, the RQ3 unsafe stop, the maintained
suite, selected School and ROAD verifier regressions, style checks, and local/remote historical
tag integrity passed. Final remote branch/CI identity remains an operational closure check and is
reported outside this self-referential Git document.

## Git identity and predecessor audit

- Canonical repository remote: `https://github.com/dongpo/topoMap.git`.
- Required predecessor branch: `codex/ama-demo-02-provider-neutral-runtime`.
- Required predecessor SHA: `95ec58515d381a7d694199a526fbad4d5e3e8e25`.
- Local predecessor, configured upstream, and remote branch were equal at audit start.
- All nine historical refs were annotated tag objects and all nine peeled targets matched their
  existing local records before any edit.
- Packaging branch: `codex/ama-demo-03-rq-aligned-packaging`.
- Final Git identity: the packaging branch tip reported by final milestone validation. A Git commit
  cannot contain its own SHA; the exact final SHA, upstream SHA, remote SHA, and equality result
  therefore belong to the external final validation report.

The canonical workspace path was occupied by unrelated branch `app/app-standalone-file-layout` at
`ac350c8fcef6e58d820ee6da456b1d1f0ef012f6` with untracked user/runtime files. No file there was
modified or removed. Work proceeded in the already-existing clean linked worktree
`/private/tmp/ama-canonical-reconciliation`, which is attached to the same canonical Git repository
and was exactly at the required predecessor.

Predecessor GitHub CI run `33053732808` was red only because the new AMA-DEMO-02 RQ3 valid test
attempted to open the intentionally ignored private School archive on a clean GitHub runner. The
test did not enter the established private-data skip registry. AMA-DEMO-03 adds that one node to
the existing registry; it does not change School runtime or authorization semantics.

## Exact three-demo definition

| RQ | Demo | Mechanism shown | Primary scenario |
|---|---|---|---|
| RQ1 | Knowledge Grounding | Qwen interpretation -> typed GraphRAG -> evidence package -> grounded Qwen answer -> deterministic evidence validation | non-special-case fire hydrant `9350906` |
| RQ2 | Constrained Agentic Planning | natural-language intent -> Qwen -> GraphRAG -> reviewed bounded plan -> deterministic validation | School `9920103` derived symbol color |
| RQ3 | Trust and Auditability | Qwen proposal -> deterministic governance -> review -> run record -> handoff -> separate School authorization -> existing execution -> independent verification | School valid and injected-field unsafe cases |

One operator entry point exposes `rq1`, `rq2`, and `rq3`; the unsafe RQ3 case is selected with
`rq3 --case unsafe`. The predecessor's `rq3-unsafe` spelling remains accepted as a hidden
compatibility alias. Existing `nma`, `nma-bench`, package name, module name, and version `0.2.0`
are unchanged.

## Demo 1 call path

1. `nma.research_cli` creates the ignored run directory and provider-neutral adapter.
2. `AMAResearchRuntime.run_rq1` calls the local model for allowlisted entity selection.
3. `CitationIntegrityGraphRetrieverV06` expands only typed canonical graph relations.
4. The unchanged `nma.evidence-package/0.4` package is supplied to the local model.
5. The model returns bounded answer/evidence/citation/exact-claim fields.
6. Existing schema and exact evidence validation fail closed on invented identities or values.
7. `demo_reporting` emits only a thin audit summary plus the validated answer.

## Demo 2 call path

1. `AMAResearchRuntime.propose_rq2` performs the same bounded interpretation and GraphRAG path.
2. The model can select only the existing single reviewed School plan candidate.
3. Existing constant-schema and `validate_bounded_plan` checks preserve feature code, schema,
   geometry, source, operation, evidence, citation, and non-execution fields.
4. Packaging reports each machine invariant independently.
5. Packaging copies the valid candidate, mutates only
   `schema_constraints.feature_code_field` to `INVENTED_FIELD`, and calls the same deterministic
   validator. Rejection before execution is required for demo success.

## Demo 3 call path

1. The unchanged RQ2 mechanism emits the probabilistic bounded proposal.
2. `adapt_live_plan_to_canonical_governance` preserves request/plan/evidence identities.
3. Existing deterministic evaluation and human review emit their distinct records.
4. The existing Agent Run Record and authorization handoff remain non-authorizing.
5. `validate_separate_school_authorization` binds the separately supplied existing School
   authorization without merging identities or authority.
6. `SchoolHeroExecutionEngine` consumes only that authorization and exact local School asset.
7. `SchoolHeroVerifier` independently verifies QA and provenance and emits receipt identities.
8. The unsafe case reuses the AMA-DEMO-02 injected-field boundary and stops before handoff,
   authorization consumption, execution, or verification.

## Stage ownership and mode

| Stage | Owner | Mode |
|---|---|---|
| Qwen interpretation/answer/proposal | configured local Qwen model | LIVE-PROBABILISTIC |
| Graph traversal and evidence validation | AMA deterministic runtime | LIVE-DETERMINISTIC |
| Plan validation and governance evaluation | existing validators/contracts | LIVE-DETERMINISTIC |
| Review decision | named reviewer | HUMAN |
| Agent Run Record and handoff | AMA deterministic governance | LIVE-DETERMINISTIC |
| School authorization and execution | existing School domain mechanism | EXISTING-DOMAIN-AUTHORITY |
| School verifier | independent deterministic verifier | LIVE-DETERMINISTIC |

No proposal, evaluation, human review record, Agent Run Record, or handoff is reported as domain
authorization. The demo derives every printed trust fact from the actual result fields and fails
if the contracts do not prove the required boundary.

## Provider-neutral model boundary

`LLMAdapter` and `LLMResult` remain the only model-facing contracts. `OllamaAdapter` remains the
only configured implementation, has no cloud fallback, and reports provider `ollama` plus the
exact Qwen model ID. AMA is never presented as the model. Formosa-1 may occupy the adapter boundary
later but is not integrated by this milestone.

## Neo4j and canonical JSON roles

Canonical JSON is authoritative and sufficient for demo success. Optional Neo4j is accepted only
after exact nodes/edges parity with the same graph revision. Live output includes database, node
count, edge count, and verified parity. Any configured Neo4j-to-canonical fallback is explicit in
both human and machine artifacts. Arbitrary Cypher remains forbidden.

## Valid and unsafe scenarios

- RQ1 valid: fire hydrant `9350906`, with evidence and citations validated.
- RQ1 invalid regression: invented evidence identity returns non-zero.
- RQ2 valid: School `9920103` reviewed bounded plan.
- RQ2 invalid companion: deterministically injected field is rejected; execution is not reached.
- RQ3 valid: existing School authorization/execution/verifier chain.
- RQ3 unsafe: injected machine field stops before handoff and execution.

## Scientific-claim boundary

- RQ1: This demonstrates an executable KG-grounded LLM mechanism. It does not establish
  statistically improved correctness over LLM-only or RAG.
- RQ2: This demonstrates executable constrained graph-grounded planning. It does not establish
  comparative reliability against LLM-only or vector RAG.
- RQ3: This demonstrates enforcement of the proposed governance/control architecture. It does not
  by itself establish human trust, institutional safety, or statistically lower failure rates.

No artifact claims benchmark or scientific superiority.

## Exact changed-file scope

- `src/nma/demo_reporting.py` — thin summaries, invariant/trust facts, artifact writer.
- `src/nma/research_cli.py` — minimal unified operator command and run orchestration.
- `tests/test_ama_demo03_rq1_packaging.py` — RQ1 packaging and invalid evidence.
- `tests/test_ama_demo03_rq2_packaging.py` — RQ2 packaging and deterministic invalid companion.
- `tests/test_ama_demo03_rq3_packaging.py` — RQ3 stage/trust packaging and unsafe CLI.
- `tests/conftest.py` — register the predecessor RQ3 execution test as private-data-dependent.
- `docs/research/AMA-DEMO-03-RUNBOOK.md` — operator runbook.
- `docs/research/AMA-DEMO-03-RQ-ALIGNED-PACKAGING.md` — this audit.

No research architecture, graph, domain, model adapter, governance contract, frozen semantic,
historical evidence, historical tag, package version, Pages site, or FOSS4G slide changed.

## Test counts

Packaging-focused tests: 7 total.

- RQ1 packaging: 2.
- RQ2 packaging: 2.
- RQ3 packaging: 3.

- AMA-DEMO-02 mechanism tests: 13 passed.
- Live Qwen RQ1: 1/1 passed on `ollama` / `qwen2.5:3b` / canonical JSON.
- Live Qwen RQ2: 1/1 passed on the same provider/model/backend.
- Live Qwen RQ3 valid: 1/1 passed through existing School execution and independent verification.
- RQ2 invalid companion: 1/1 rejected before execution.
- RQ3 unsafe: 1/1 rejected before handoff/execution.
- Canonical maintained pytest: 1,458 selected; 1,457 passed and 1 existing optional test skipped.
- Selected School execution/verifier regression: 12/12 passed.
- ROAD verifier regression: 39/39 passed.
- Historical tag integrity: 9/9 annotated objects and 9/9 peeled targets matched locally/remotely.
- Maintained Ruff: passed.
- Maintained format: passed.

## Known limitations

- Live output depends on the locally installed Qwen model and available compute; model latency is
  not a benchmark result.
- Optional Neo4j is not required; canonical JSON is the supported authoritative fallback.
- RQ3 valid cannot run from redistributable Git bytes alone because the existing authorization is
  intentionally bound to an ignored private School archive and requires GDAL/OGR.
- The School flow is the only packaged end-to-end domain flow. No second domain flow is claimed.
- No LLM-only/RAG/GraphRAG comparison, statistical reliability study, or human-trust study is part
  of this milestone.

## FOSS4G software freeze recommendation

AMA research software is ready to freeze for FOSS4G, with only release/demo operational checks
remaining. No feature, UI, presentation, or publication-experiment work belongs in this milestone.

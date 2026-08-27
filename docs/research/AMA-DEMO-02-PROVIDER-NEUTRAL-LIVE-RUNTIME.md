# AMA-DEMO-02 — Provider-neutral live research runtime

Verdict: **PASS — PROVIDER-NEUTRAL RQ1–RQ3 LIVE RESEARCH MECHANISMS WIRED**

Audit date: 2026-08-27 (Asia/Taipei). This is an engineering mechanism milestone, not a
scientific experiment.

## Baseline identity

AMA-DEMO-02 started from the clean, merge-ready PR #4 head on
`codex/ama-canonical-reconciliation`:

| Identity | Exact value |
| --- | --- |
| predecessor | `34c7ef011d2bf7e9c067ac6cac2bc1a1d75dc117` |
| predecessor subject | `ci(ama): classify detached historical refs` |
| PR #4 state at start | open, non-draft, merge state `CLEAN` |
| PR #4 base | `main` at `0620e75705338f2096a7c9ef9a1f2de185a46577` |
| AMA-DEMO-02 branch | `codex/ama-demo-02-provider-neutral-runtime` |
| package version | `0.2.0` (unchanged) |

The original canonical directory remained on its user-owned dirty
`app/app-standalone-file-layout` worktree and was not switched or edited. Work occurred in the
existing clean reconciliation worktree at `/private/tmp/ama-canonical-reconciliation`.

## Provider-neutral architecture

The maintained runtime owns this boundary:

```text
Qwen or future locally served model
        ↓
LLMAdapter.generate_structured(...)
        ↓
LLMResult(provider, model_id, output, latency_ms, usage, raw_response_hash)
        ↓
AMA research runtime
        ↓
deterministic evidence / plan / governance / domain validators
```

No provider response ID, tool-call ID, call ID, session ID, continuation ID, hidden state, or
chain-of-thought enters an AMA contract. The Ollama adapter uses local `/api/chat` JSON mode and
passes the requested output schema in the bounded prompt context. AMA, not the provider grammar
implementation, validates the returned object against the exact closed schema. The adapter has
no cloud or credential fallback.

The exact contract is:

```python
class LLMAdapter:
    def generate_structured(
        self,
        *,
        task: str,
        instructions: str,
        context: dict,
        output_schema: dict,
    ) -> LLMResult: ...
```

`LLMResult` exposes only `model_id`, `provider`, `output`, `latency_ms`, optional provider-neutral
token `usage`, and `raw_response_hash`. Raw provider envelopes are not persisted by the runtime.

## Local Qwen configuration

The verified local configuration was:

```bash
export AMA_LLM_PROVIDER=ollama
export AMA_LLM_BASE_URL=http://127.0.0.1:11434
export AMA_LLM_MODEL=qwen2.5:3b
ollama serve
```

The model name is configuration, not a hard-coded architectural dependency. No API key is read.
Missing variables, an unsupported provider, an unavailable endpoint, an unavailable model, an
HTTP failure, malformed JSON, or an invalid structured result produces an explicit failure. There
is no silent cloud fallback.

Examples:

```bash
PYTHONPATH=src:. python -m nma.research_cli --repository-root . \
  rq1 'What is the reviewed portrayal rule for fire hydrant 9350906?'

PYTHONPATH=src:. python -m nma.research_cli --repository-root . \
  rq2 'Change elementary school 9920103 color to blue.'

PYTHONPATH=src:. python -m nma.research_cli --repository-root . \
  rq3 'Change elementary school 9920103 color to blue.' \
  --storage-root /tmp/ama-demo02-school \
  --idempotency-key ama-demo02-school-valid
```

The installed `ama-research-demo` entry point exposes the same `rq1`, `rq2`, `rq3`, and
`rq3-unsafe` commands. Output shows provider/model identity, active graph backend, request
identity, evidence or plan identity, governance result, and the complete RQ3 identity links. It
does not print environment values or secrets.

## Formosa-1 extension point

No Formosa-1 integration is claimed. A future adapter must implement the same single
`generate_structured` method, return the same six provider-neutral result fields, accept bounded
JSON context and a closed output schema, and fail explicitly when its local endpoint is
unavailable. It must not expose serving-session or provider response identities.

The RQ1, RQ2, RQ3, bridge, governance, handoff, authorization-binding, execution, and verifier
tests are reusable unchanged. Only adapter transport tests need to vary. A future local server
may use a chat-compatible wire protocol, but its adapter should be named for that protocol (for
example `StructuredChatHTTPAdapter`), not for a cloud provider.

## RQ1 call path

```text
natural-language question
→ local model selects only allowlisted canonical node IDs
→ typed GraphRAG expansion
→ authoritative evidence package and backend trace
→ evidence package injected into the local model
→ grounded structured answer
→ deterministic node / citation / source / exact-claim validation
```

The live acceptance question was the non-School-special-case fire hydrant `9350906` portrayal
rule. Required node, citation, document, and exact property/value references are derived from the
retrieved package and copied into the closed model result. Unknown IDs, invented citations,
absent sources, or changed reviewed values fail closed. A uniquely recognizable citation missing
only its canonical `citation:` prefix may be normalized deterministically and is reported in the
result; no unknown identity is repaired or accepted.

Live Qwen RQ1 passed with canonical JSON backend and evidence package
`evidence-package:sha256:da52e1a22d33a30cf2857f7f9a425a044e98707ba30e8fee9f1e6c469b5c5544`.

## RQ2 call path

```text
natural-language portrayal intent
→ local model selects allowlisted KG entities
→ typed GraphRAG evidence
→ local model receives one reviewed candidate
→ exact deterministic plan validation
→ content-addressed, non-executing proposal
```

The maintained plan catalog contains one bounded School scenario. It binds feature `9920103`,
Point geometry, product layer `MARK`, source layers `J01/J13/J17/K01/K02/K14_MARK`, fields
`TERRAINID`, `MARKID`, and `MARKNAME1`, exact `TERRAINID=9920103` classification, the reviewed
source archive hash, bounded extraction/reprojection/portrayal operations, exact evidence and
citation IDs, explicit approval and authorization requirements, and no production writeback.

The model may reproduce/select that candidate; it may not change it. A changed field, feature
code, geometry, source layer, operation, citation, approval requirement, authorization
requirement, or execution state fails before governance. No arbitrary path, shell command,
Cypher, GDAL call, or tool name is accepted.

Live Qwen RQ2 passed with request
`request:sha256:5c3a02d6ae510b8f28311451dc44bbc7575747d3be8738bafc521cce5ab2f99b`.

## RQ3 call path and ownership

School Hero was selected instead of ROAD because the unchanged canonical Agent planning contract
already represents feature `9920103` portrayal proposals. Mapping a ROAD feature into that
contract would require widening or misrepresenting canonical semantics, which this milestone
forbids.

```text
validated live School plan
→ explicit live/canonical bridge
→ unchanged nma.intent-planning/1.0 intent
→ unchanged nma.evidence-backed-proposal/1.0 proposal
→ deterministic nma.agent-evaluation/1.0
→ explicit accepted nma.agent-decision-record/1.0 review
→ nma.agent-run-record/1.0
→ nma.authorization-handoff-request/1.0 (authorization reference remains null)
→ separately loaded existing nma.symbol-edit-authorization/1.0
→ exact domain-scope binding and existing domain authorization verifier
→ existing SchoolHeroExecutionEngine
→ existing independent SchoolHeroVerifier
→ execution receipt, QA, and provenance
```

The bridge preserves exact request, live plan, evidence package, live citation, canonical
evidence, canonical intent, canonical proposal, domain, operation-class, and scope hashes. It
rejects a request or plan identity change, unsupported canonical representation, incomplete
citation integrity, inferred authorization, or scope change. It does not fabricate a canonical
plan.

The handoff always carries `domain_authorization_reference = null`. The existing School
authorization is loaded only after handoff creation. A separate domain binding checks exact
feature, geometry, profile, source archive, source layers, source filter, field identities,
portrayal operations, execution scope, and no production writeback. The operator supplies a
separate idempotency key; handoff, authorization, idempotency, and execution identities are never
substituted for one another.

The local RQ3 operator atomically emits `bridge.json`, `proposal.json`, `evaluation.json`,
`decision-record.json`, `agent-run-record.json`, and `authorization-handoff.json` under the fixed
`<storage-root>/ama-governance/` directory before domain authorization is loaded. It later emits
the separate domain binding and verified RQ3 result. These fixed-path records are audit/replay
artifacts only; the existing domain engine reads authorization from its separate domain store.

The live Qwen valid scenario passed existing execution and independent verification. Its
inspectable identities included:

| Stage | Identity |
| --- | --- |
| plan | `ama-plan:sha256:1427356768ac312347c67aa93ed32c242063b15825041eed33fabfc119748452` |
| bridge | `ama-governance-bridge:sha256:2a95767d50da3b16475a80ae684b0b1b603a554d45d2442018bd0c8a1c732eb1` |
| proposal | `proposal:sha256:2153e09ce6469b5a97f124c3ac2e98b3b624d5c7173228e3ab97b1e77d56bd63` |
| evaluation | `evaluation:sha256:95a7d6147ad4ffdab6b85ca52d7a74cf693b590c24070d16e7f9ca3de17275fe` |
| decision | `decision-record:sha256:b8abe1a899377f5981c3a2e264f6436e23b580433ffa2b83a22ca220067cb73b` |
| run record | `agent-run:sha256:08baa6477b418c848b88c0fe97d119e98bb63657c7ebb278d0daff087de594e0` |
| handoff | `authorization-handoff:sha256:d016b63fb30dd7b5fa18d7202b0da5d72aaa0417b216e8b55c9bcf391fc6a142` |
| separate authorization | `authorization-school-demo-b4ecdbfc35ecaf73293ed497` |
| execution | `exec-85318ae4a6aa93986cb6f34f` |
| QA SHA-256 | `14dd01766d4351412acf03c7f795ccd3e07d745a8b1f81619c6f5dc561991dfe` |
| provenance SHA-256 | `638058d00bd848313b100c900c2adb11ddd69013e373490918450a0d6cc0d668` |

Scenario B injects `INVENTED_FIELD` into the model result after a real local model call. Exact
plan validation rejects it. No canonical proposal evaluation, decision, run record, handoff,
domain authorization consumption, execution, or verification is reached. This demonstrates that
model output variability cannot directly become execution variability.

## Live and deterministic components

| Component | Ownership |
| --- | --- |
| natural-language entity selection | probabilistic local model, allowlisted output only |
| grounded prose answer | probabilistic local model |
| reviewed candidate reproduction | probabilistic local model, exact closed candidate only |
| graph expansion and backend trace | deterministic AMA runtime |
| node/citation/source/exact-claim validation | deterministic AMA runtime |
| plan validation and plan identity | deterministic AMA runtime |
| canonical intent/proposal adaptation | deterministic bridge plus unchanged contracts |
| evaluation, review record, run record, handoff | unchanged deterministic Agent contracts |
| authorization | separately supplied, existing School domain mechanism |
| execution | existing School domain engine |
| verification and receipt/provenance | existing independent School verifier |

## Neo4j role

The canonical JSON graph remains authoritative. `runtime_graph_backend_v029` may activate a live
Neo4j projection only after its full nodes and edges structurally match the canonical graph
revision. Otherwise it visibly falls back to canonical JSON only when that fallback is explicitly
configured, or fails closed. The backend trace records requested/active backend, graph revision,
identity verification, and fallback state. The model receives allowlisted node IDs and typed graph
expansion only. Arbitrary Cypher remains forbidden.

The live acceptance used `canonical-json`; it did not claim that Neo4j was live.

## Model trust boundary

The LLM is a probabilistic proposal generator and interpreter, never the source of authority.

It may interpret language, select allowlisted entities, produce bounded explanations, and
reproduce a reviewed candidate. It may not assert unsupported authoritative truth, mint graph or
rule identities, create or widen authorization, select arbitrary tools, create paths or commands,
mutate data, execute GDAL, bypass validators, supply idempotency, or mark verification passed.

Evaluation, human review, a run record, and an Agent handoff each remain non-authorizing. Only the
separately supplied domain-owned authorization can become eligible after the existing domain
validator accepts its exact scope.

## Exact changed files

No frozen source, domain engine, verifier, canonical Agent contract, graph, rule, historical
report, tag, Pages asset, or package version was changed.

- `pyproject.toml`
- `data/research/ama-demo-02-school-plan-catalog-v1.0.json`
- `src/nma/llm/__init__.py`
- `src/nma/llm/base.py`
- `src/nma/llm/ollama.py`
- `src/nma/research_cli.py`
- `src/nma/research_governance_adapter.py`
- `src/nma/research_runtime.py`
- `tests/ama_demo02_support.py`
- `tests/test_ama_demo02_rq1.py`
- `tests/test_ama_demo02_rq2.py`
- `tests/test_ama_demo02_rq3.py`
- `docs/research/AMA-DEMO-02-PROVIDER-NEUTRAL-LIVE-RUNTIME.md`

## Validation

| Validation | Result |
| --- | --- |
| AMA-DEMO-02 focused tests | 13 passed |
| RQ1 mechanism tests | 4 passed |
| RQ2 mechanism tests | 4 passed |
| RQ3 mechanism tests | 5 passed |
| live local Qwen mechanisms | 4/4 passed: RQ1, RQ2, valid RQ3, unsafe stop |
| current maintained canonical pytest | 1,450 passed, 1 skipped; 1,451 selected |
| historical annotated tag integrity | 9/9 tag objects and 9/9 peeled targets exact locally and remotely |
| ROAD independent verification suite | 39 passed |
| selected School execution/verifier suite | 14 passed |
| maintained Ruff | passed |
| maintained format check | passed; 167 maintained Python files formatted |

The repository contains 38 explicitly marked historical-freeze assertions. They remain unchanged
and ref-specific; they are not expected to pass in a later integration worktree. Historical
integrity at this milestone is verified separately with
`scripts/verify_historical_tag_integrity.py --remote origin`, which passed all nine immutable tag
records without rewriting any historical evidence.

## Known bounded demo limitations

- Only the Ollama transport adapter is implemented; Formosa-1 is an extension point, not a claim.
- One reviewed School plan and one existing School authorization/execution path are wired.
- The live run used canonical JSON, not a running Neo4j projection.
- The candidate performs derived-layer/derived-portrayal work only and never production writeback.
- Provider JSON conformance is enforced after generation; the model is not trusted to enforce its
  own schema.
- A live model may fail closed and require another operator run. There is no automatic semantic
  repair, alternate provider, or cloud fallback.

## Scientific-claim boundary

AMA-DEMO-02 validates that the proposed RQ1–RQ3 software mechanisms are executable. It does not
establish that KG-grounded LLMs are statistically more accurate, that GraphRAG is superior to
vector RAG, that Qwen is superior to another model, or that AMA is scientifically safer than
alternatives. Publication-grade RQ1–RQ3 evaluation, controlled LLM-only/RAG/GraphRAG comparison,
and statistical safety claims remain future work.

No UI, Pages, slide, dashboard, new domain, new feature type, production backend, additional
model, or publication experiment was added.

# AMA public live demo

AMA-DEMO-02 is a presentation and orchestration layer around the frozen AMA-CLOUD-01 runtime. It
does not modify the knowledge graph, GraphRAG projection, RQ1 validator, constraints, proposal,
authorization, GIS, verification, provenance, or Qwen/Ollama semantics.

## What the audience sees

The page follows the research architecture rather than a chatbot layout:

1. exact user intent, separately showing normalized intent and planner input;
2. the already executed canonical RQ1 comparison for LLM-only, Text-RAG, and GraphRAG;
3. domain KG, query-specific retrieved subgraph, and evidence-to-action trace;
4. resolved, bounded-unresolved, and contradicted constraints plus the canonical proposal;
5. proposal-bound authorization and the proposal/authorized/executed hash invariant;
6. the derived GIS map result;
7. expected-versus-observed verification; and
8. complete provenance.

The mode banner is sticky. `LIVE CLOUD RUN` means the browser submitted the canonical request to
the cloud runtime. `VERIFIED REPLAY` means the page is showing the tracked, hash-manifested package
from a previously accepted cloud run. The UI never changes modes automatically. When a live call
fails it shows the failure, states that no replay has been selected, and offers an explicit replay
button.

The RQ1 panel is labelled `EXECUTED CONTROLLED RECORD`; it is not presented as part of the fresh
RQ2/RQ3 run. The predecessor retained exact run identities and measured latencies but not
wall-clock timestamps for the individual RQ1 records. AMA-DEMO-02 reports the timestamp as `NOT
RECORDED` rather than inventing it.

The GraphRAG answer is displayed in Traditional Chinese (`zh-Hant-TW`). This is an explicitly
labelled presentation translation: the frozen Simplified Chinese answer remains unchanged in the
controlled source record, and its SHA-256 identity, validation result, and research controls remain
visible and unchanged. The graph views render typed edges as directed, color-coded arrows. A
relation legend gives every visible relation type and count; the small domain view also labels its
edges directly, while the denser retrieved and action views rely on the legend to avoid obscuring
nodes.

The execution map renders the derived Point as a recognizable hydrant pictogram inside the selected
result halo. The pictogram is explicitly labelled `NON-AUTHORITATIVE SYMBOLIC PREVIEW`: it helps an
audience distinguish the derived feature from the immutable source point but does not claim to be
the official cartographic glyph. The unresolved glyph trace, line metric, color profile, and
ProductLayer gates remain visible and unchanged.

## Run locally

Prerequisites are Python 3.11, the repository's existing runtime dependencies, Ollama 0.32.15, and
the frozen `qwen2.5:latest` model with digest prefix `845dbda0ea48`.

```sh
export PYTHONPATH=src
export AMA_LLM_BASE_URL=http://127.0.0.1:11434
export AMA_DEPLOYMENT_LABEL=LOCAL
python3 -m nma.ama_live_server \
  --host 127.0.0.1 \
  --port 8086 \
  --storage-root /tmp/ama-demo-runtime
```

Open <http://127.0.0.1:8086>. Local execution is reported by `/ama/config` as `LOCAL/TEST`; the
public-facing `LIVE` label is reserved for `AMA_DEPLOYMENT_LABEL=LIVE CLOUD RUN`.

Relevant environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `AMA_LLM_BASE_URL` | Frozen Ollama endpoint | `http://127.0.0.1:11434` |
| `AMA_DEPLOYMENT_LABEL` | Exact deployment label | `LOCAL` |
| `AMA_RUNS_PER_MINUTE` | Bounded start-rate limit | `6` |
| `AMA_CORS_ORIGIN` | One optional allowed origin | same-origin only |
| `AMA_REQUIRE_GPU` | Require preloaded GPU model at startup | unset locally, `1` in cloud |
| `AMA_GPU_MODEL_PRELOADED` | Set only by the verified cloud entrypoint | `false` |

## LIVE mode

`POST /ama/run` accepts only the exact canonical intent. A run receives fresh retrieval, evidence
projection, constraint, plan, proposal, authorization, execution, verification, and provenance
identities. The UI polls the run record and does not show a map until the backend status is
`PASS`. Authorization remains proposal-bound, and a mismatch between canonical, authorized, and
executed hashes fails closed before mutation.

`POST /ama/reset` is permitted only when no run is active. It removes run-scoped temporary
directories and in-memory records, clears the start-rate window, and does not touch the packaged
fixture or frozen research artifacts. A browser refresh also starts with no run selected, so a
prior result cannot appear as fresh live output.

## REPLAY mode

The canonical replay is in `artifacts/ama-demo/replay/canonical-run/`. Its `manifest.json` identifies
the source cloud endpoint and run, records the original `LIVE` source mode, fixes the visible mode
as `REPLAY`, and includes SHA-256 and byte length for every replay artifact. `run.json` is the
unaltered accepted live record; the API adds presentation-only replay labels when serving it.

The package includes exact intent, RQ1 record, graph retrieval, evidence, constraints, proposal,
authorization, execution, verification, provenance, map result, tamper denial, and all three graph
exports. No new inference or execution occurs in replay mode.

To refresh the package from a fresh successful cloud run:

```sh
PYTHONPATH=src python3 scripts/capture_ama_demo02_replay.py \
  --endpoint https://ama-cloud-01-555420096938.asia-southeast1.run.app
```

The capture script fails closed unless health passes, the request is accepted as `LIVE`, the run
passes, the map is returned, tamper denial passes, and the proposal, authorization, execution, and
map hashes all match.

## Adding a controlled scenario

Do not modify the current scenario in place. First create a separate research task that freezes
and validates the new intent, evidence/retrieval behavior, constraints, proposal, policy,
execution, verification, and redistribution boundary. Only after that task passes should a demo
task add a new named scenario adapter and its own replay directory. Presentation code may select
between frozen scenarios, but must not infer missing ProductLayer bindings, remap classifications,
rewrite validators, or loosen authorization.

## Redistribution boundary

Redistribution is `BOUNDED`. The browser receives only the bounded domain subset, query-specific
evidence projection, controlled RQ1 evidence, proposal/audit records, and derived demo result. The
full KG and restricted source material stay server-side. Source access remains read-only, the
derived output is run-scoped, and no production authority is claimed.

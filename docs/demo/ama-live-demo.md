# AMA live demo

AMA turns one bounded mapping intent into a new, inspectable execution. The default path is
live: the frozen Qwen model composes a plan after the frozen GraphRAG retriever and constraint
resolver run. A new proposal is validated, hash-bound to a short-lived research authorization,
executed by allowlisted deterministic GIS tools, verified, recorded, and rendered from the
current run's GeoJSON.

## Run it

Requirements are Python 3.11, local Ollama, and the exact frozen model `qwen2.5:latest`
(`845dbda0ea48…`, 7.6B, Q4_K_M). Node is not needed.

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
ollama pull qwen2.5:latest
ollama serve
```

In a second terminal:

```bash
. .venv/bin/activate
export AMA_LLM_BASE_URL=http://127.0.0.1:11434
PYTHONPATH=src:. python -m nma.ama_live_server --repository-root . --port 8086
```

Open `http://127.0.0.1:8086`. Keep the supplied canonical preset and select **Run AMA**. The
field shows the exact intent submitted to the backend. Progress comes from backend stage records;
there are no simulated timers. After a verified result, select **Run backend tamper test** to alter
a protected proposal field and observe authorization deny it before mutation.

For command-line acceptance without the browser:

```bash
PYTHONPATH=src:. python scripts/run_ama_live_acceptance.py --repository-root .
```

## What to inspect

- The runtime strip reports intent, retrieval, evidence, constraints, plan, proposal,
  authorization, GIS execution, verification, provenance, and map result.
- Knowledge Context is a bounded view loaded from the canonical graph.
- Live Retrieved Subgraph is produced by the current GraphRAG invocation.
- The constraint table preserves `RESOLVED`, `BOUNDED_UNRESOLVED`, and `CONTRADICTED` meaning.
- The map overlays the immutable input and current run's derived GeoJSON.
- The trace shows fresh run, proposal, authorization, execution, verification, receipt, and
  provenance identities.
- The RQ1 panel is explicitly labelled **CONTROLLED RESEARCH RESULT**; it is supporting frozen
  evidence and not the live execution.

Raw bounded inspection endpoints are documented in the developer guide. Runtime records are
written under `artifacts/ama-live/runtime/` and ignored by Git.

## Safety and failure behavior

AMA-LIVE-01 accepts only the canonical fire-hydrant scenario. An unsupported intent fails instead
of widening semantics or replaying a frozen result. GraphRAG, constraint, model, proposal,
authorization, execution, and verification failures stop the run visibly. The source fixture is
read-only, authoritative rendering stays false, shell/filesystem/model/graph selection are not API
parameters, and outputs are isolated by fresh run ID.

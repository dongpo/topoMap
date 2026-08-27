# Frozen model baseline protocol

## Why this exists

The checked-in offline systems test architecture and scoring, but they are not empirical LLM
baselines. Publishable NMA results require named model snapshots, repeated runs, raw outputs,
latencies, failures, prompts, and retrieval context. `nma-bench-adapter/1.0` provides that boundary
without importing a model SDK into NMA core.

## Protocol

The benchmark starts each adapter with a command argument array—never through a shell—and writes
one JSON request to standard input:

```json
{
  "protocol": "nma-bench-adapter/1.0",
  "system": "plain_llm_qwen3_8b",
  "run_index": 0,
  "task": {"task_id": "K001", "category": "knowledge", "input": "..."},
  "context_mode": "none",
  "context": null
}
```

The adapter must write exactly one JSON object to standard output:

```json
{
  "value": "RIVERL",
  "evidence": [],
  "metadata": {"model": "qwen3:8b", "adapter": "openai-compatible/1.0"}
}
```

Anything else is an adapter failure. Timeouts, nonzero exits, invalid JSON, and invalid response
shapes are recorded per task and score zero rather than terminating the experiment.

The runner removes the task's `expected` field before constructing this request. Ground truth stays
inside the scorer and is never exposed to an adapter.

## Context ablations

- `none`: task only; appropriate for the plain-model baseline.
- `document`: all evidence chunks, useful only for small controlled corpora.
- `document_rag`: deterministic lexical top-k evidence chunks.
- `structured`: the active machine-readable specification.

The full NMA remains the built-in deterministic system because its validation result must come from
GIS tools rather than model text.

## Local FOSS-compatible run

The supplied adapter speaks the widely implemented chat-completions JSON interface and can target a
local Ollama- or vLLM-style server. It uses only Python's standard library.

1. Copy `benchmark/external-baselines.example.json` to
   `benchmark/external-baselines.json`.
2. Choose a frozen model and replace every `REPLACE_WITH_*` value with the real model digest or
   immutable version and server version. The runner rejects missing or placeholder audit metadata.
3. Verify the endpoint and model outside the benchmark.
4. Run:

```bash
PYTHONPATH=src python3 -m nma.bench \
  --root . \
  --external-config benchmark/external-baselines.json \
  --output artifacts/benchmark/model-results.json
```

If authentication is required, set `NMA_MODEL_API_KEY` in the environment. Never place an API key
in the JSON configuration or committed results.

## Publication gate

Do not merge an empirical results table unless:

- model digest and serving software version are non-placeholder values;
- temperature, prompt adapter version, context mode, top-k, and timeout are frozen;
- at least three runs completed with raw per-task outputs retained;
- adapter failures and latency are reported;
- development tasks were not used as prompt examples;
- the result file is generated from the committed benchmark and configuration commit.

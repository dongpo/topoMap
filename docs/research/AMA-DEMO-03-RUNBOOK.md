# AMA-DEMO-03 RQ-Aligned Research Demo Runbook

## Scope

This runbook operates the three already-implemented AMA research mechanisms through one
entry point:

```text
KNOWLEDGE (RQ1) -> ACTION (RQ2) -> TRUST (RQ3)
```

AMA is the provider-neutral architecture and runtime. Qwen is the configured replaceable local
model. A future Formosa-1 adapter can occupy the same boundary, but this milestone does not
implement it.

## Prerequisites

- Python 3.11 or later.
- A local Ollama installation with the configured Qwen model already downloaded.
- The checked-in canonical knowledge graph and vector/runtime assets.
- Optional: a live Neo4j projection matching the exact canonical graph revision.
- RQ3 valid case only: the ignored, non-redistributable School source archive at
  `data/datasets/112年多維度SHP成果_0502.zip`, with the exact hash required by the existing
  School authorization.
- RQ3 valid case only: GDAL/OGR (`ogr2ogr`) and the checked-in existing School authorization.

No cloud credentials or cloud model API are required or supported.

Create an isolated environment from a clean checkout:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

## Start Qwen through Ollama

In one terminal:

```bash
ollama serve
```

In another terminal, confirm the local model name:

```bash
ollama list
```

Set the provider-neutral adapter configuration. Replace the model value with the exact name shown
by `ollama list`:

```bash
export AMA_LLM_PROVIDER=ollama
export AMA_LLM_BASE_URL=http://127.0.0.1:11434
export AMA_LLM_MODEL=qwen2.5:7b
```

The endpoint must not contain embedded credentials. The runtime has no cloud fallback.

## Graph backend

Canonical JSON is the reproducible default:

```bash
export NMA_GRAPH_BACKEND=canonical-json
export NMA_GRAPH_FALLBACK=canonical-json
```

For an optional local Neo4j projection, put the following values in the ignored `.env.local`
file instead of shell history:

```text
NMA_GRAPH_BACKEND=neo4j
NMA_GRAPH_FALLBACK=canonical-json
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=<local-user>
NEO4J_PASSWORD=<local-password>
NEO4J_DATABASE=neo4j
```

The demo verifies the live projection against the canonical graph before use. If Neo4j is
unavailable and canonical fallback is configured, the summary explicitly reports the fallback
and reason. No Neo4j Browser or GUI is needed. If fallback is disabled, activation fails closed.

## Health checks

Check the Ollama endpoint and configured model:

```bash
curl -fsS "$AMA_LLM_BASE_URL/api/tags"
ollama list
```

Check required repository assets without printing their contents:

```bash
test -f data/knowledge/nma-canonical-graph-v0.4.json
test -f data/knowledge/nma-citation-source-registry-v0.6.json
test -f data/runtime/vector/nma-vector-index-v0.32.json
test -f artifacts/runtime/school-hero/authorizations/authorization-school-demo-b4ecdbfc35ecaf73293ed497.json
command -v ogr2ogr
```

For RQ1 and RQ2, missing optional Neo4j with explicit canonical fallback is degraded but runnable.
Missing Ollama/Qwen blocks all three demos. Missing the private School archive or GDAL blocks only
the RQ3 valid execution; it does not block RQ1, RQ2, or the RQ3 unsafe fail-closed case.

## Run RQ1: knowledge grounding

```bash
.venv/bin/python -m nma.research_cli rq1
```

Expected high-level output:

- provider/model and active graph backend identity;
- fire hydrant `9350906` question and resolved entity;
- compact graph paths, evidence count, citations, source revision/page;
- grounded Qwen answer;
- `PASS` for evidence, citations, and grounded-answer validation.

Scientific-claim boundary: this demonstrates an executable KG-grounded LLM mechanism. It does
not establish statistically improved correctness over LLM-only or RAG.

## Run RQ2: constrained planning

```bash
.venv/bin/python -m nma.research_cli rq2
```

Expected high-level output:

- exact School `9920103` intent and authoritative KG context;
- feature, classification, geometry, source layers, field mapping, filter, operations, evidence,
  and citations from the bounded candidate;
- separate `PASS` results for each deterministic invariant;
- a deterministic `INVENTED_FIELD` companion mutation rejected before execution.

Scientific-claim boundary: this demonstrates executable constrained graph-grounded planning. It
does not establish comparative reliability against LLM-only or vector RAG.

## Run RQ3 valid: trust and auditability

First verify that the local private archive has the expected authorization-bound digest without
printing private bytes:

```bash
shasum -a 256 data/datasets/112年多維度SHP成果_0502.zip
```

Then run:

```bash
.venv/bin/python -m nma.research_cli rq3 --case valid
```

Expected high-level output is the complete stage table: request, probabilistic proposal,
deterministic evaluation, human review, Agent Run Record, non-authorizing handoff, separately
existing School authorization, School execution, and independent verification/receipt. The
summary states `NO` for every non-domain authorization source and `YES` for separate domain
authorization and independent verification.

Scientific-claim boundary: this demonstrates enforcement of the proposed governance/control
architecture. It does not by itself establish human trust, institutional safety, or statistically
lower failure rates.

## Run RQ3 unsafe

```bash
.venv/bin/python -m nma.research_cli rq3 --case unsafe
```

The runtime injects one deterministic invalid field into an otherwise provider-produced reviewed
plan. Expected output is `Unsafe proposal detected`, with no handoff, domain authorization
consumption, execution, or verification. This case does not require the private archive because
it stops before the domain boundary.

## Artifacts

Every successful demo writes an ignored run directory under:

```text
artifacts/tmp/research-demo/<run-id>/
  summary.txt
  result.json
```

RQ3 valid additionally writes the existing governance, execution, and verification outputs below
that run directory's `runtime/` folder. Console output is intentionally compact. It never prints
passwords, tokens, credential-bearing configuration, private source bytes, or hidden reasoning.

To choose another ignored output root:

```bash
.venv/bin/python -m nma.research_cli --output-root artifacts/tmp/my-demo-runs rq1
```

## Cleanup

Demo output is disposable and ignored by Git. After reviewing the paths carefully, remove only
the chosen `artifacts/tmp/research-demo/` directory. Do not remove the checked-in authorization,
canonical graph, or private source archive as part of demo cleanup.

## Troubleshooting

- `Missing local model configuration`: set all three `AMA_LLM_*` variables.
- `Local Ollama ... unavailable`: start `ollama serve`, verify the URL, and confirm the configured
  model with `ollama list`.
- `Unsupported AMA_LLM_PROVIDER`: only the already-approved local `ollama` adapter is packaged.
- Neo4j fallback reported: inspect the explicit reason, then either repair the local projection or
  continue with canonical JSON. The fallback is never hidden.
- `separately authorized source archive is unavailable`: place the exact ignored private archive at
  the required path; do not substitute public or synthetic data.
- `ogr2ogr` missing: install GDAL/OGR before the RQ3 valid case.
- authorization expiry/hash/scope failure: do not edit the authorization. Restore the checked-in
  record and exact private asset, then rerun with a fresh ignored output directory.
- any evidence, plan, governance, or verification validation failure is a fail-closed result, not a
  reason to weaken the validator.

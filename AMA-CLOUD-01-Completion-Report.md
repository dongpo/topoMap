# AMA-CLOUD-01 completion report

## Verdict

**PASS.** The frozen AMA-LIVE-01 implementation is deployed as a genuine, publicly reachable Google Cloud Run GPU service. A cold run, three unique warm fresh runs, and a fresh run after service restart all exercised live GraphRAG, the exact Qwen/Ollama planner, constraints, proposal construction, authorization, deterministic GIS execution, verification, provenance, map delivery, and tamper denial. Research semantics are unchanged.

The warm median was 16.227 seconds for planning and 16.617 seconds end-to-end, classifying the service as **GOOD FOR LIVE DEMO**. This is about 25.17× faster for planning and 24.63× faster end-to-end than the Mac mini baseline. No model or semantic optimization is indicated by this acceptance task.

## Identity and deployment

| Item | Accepted value |
|---|---|
| Research freeze | `8411cad14a16d8ce1b8b23ab0f1be1e8b4bc1a4b` |
| AMA-LIVE-01 predecessor | `0bef91d77f941b3dfb5971bb46131c9e35df4f20` |
| Deployed implementation SHA | `7a31c6a55848fe420788f36d498d4de4bd89be26` |
| Branch | `ama-cloud/ama-cloud-01-google-cloud-run` |
| Project / region | `sanguine-era-92109` / `asia-southeast1` |
| Service / accepted restart revision | `ama-cloud-01` / `ama-cloud-01-00004-r4s` |
| Endpoint | <https://ama-cloud-01-555420096938.asia-southeast1.run.app> |
| Image digest | `sha256:be40ed830e1eabc12858286a8e1fe10811e5f69b128e082c87863a1da79b26a9` |
| Resources | NVIDIA L4, 4 vCPU, 16 GiB, concurrency 1, min 0, max 1 |

The selected architecture is a single Cloud Run service containing the bounded frontend/API/orchestrator, GraphRAG/KG, constraints, GIS, authorization, verification, provenance, and Ollama/Qwen runtime. This is technically sufficient and avoids unnecessary services.

## Starting-state gate

The canonical checkout was verified, but its existing `app/app-standalone-file-layout` worktree was not clean: it contained untracked user directories/files unrelated to AMA-CLOUD-01. Work stopped in that checkout and continued from the exact AMA-LIVE-01 predecessor in an isolated Git worktree at `/private/tmp/ama-cloud-01-worktree`; none of the pre-existing files were modified or removed. The task worktree is clean at completion.

The gate also confirmed the exact Ollama/model identity above; the tracked 6.5 MB bounded graph `data/knowledge/nma-canonical-graph-v0.4.json`; the deterministic GeoJSON GIS fixture/executor; optional, non-required Neo4j connectivity; no required secret; no production write target; and no semantic dependency on an absolute Mac path. The only cloud write assumption is an isolated ephemeral root configured as `/tmp/ama-runtime`. Missing model, runtime libraries, schema dependencies, graph/fixture data, or GPU residency all cause startup or execution to fail closed.

## Frozen runtime identity

- Ollama: 0.32.15
- Model: `qwen2.5:latest`
- Digest: `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`
- Family / parameters / quantization: qwen2 / 7.6B / Q4_K_M
- Model blob: 4,683,073,952 bytes
- Context / output reserve / temperature: 8192 / 2048 / 0

The model is baked into the image. Build and startup verify its manifest digest; startup also verifies the Ollama API identity, preloads the model, and checks positive GPU VRAM residency before exposing the API. Model identity passed on every accepted run.

## Runtime evidence

| Measurement | Cold | Warm min | Warm median | Warm max |
|---|---:|---:|---:|---:|
| GraphRAG | 362.365 ms | — | — | — |
| Planning | 49.907 s | 16.171 s | 16.227 s | 16.323 s |
| End-to-end | 50.472 s | 16.576 s | 16.617 s | 16.721 s |

Cold Qwen provider metrics were 1.797 ms model-load bookkeeping, 30.853 seconds prompt evaluation for 2,740 tokens, and 19.020 seconds generation for 786 tokens. On warm runs the prompt cache reduced prompt evaluation to about 22 ms; generation remained 16.12–16.27 seconds. The cold run was individually `USABLE` (30–60 seconds), while warm operation is `GOOD FOR LIVE DEMO` (at most 30 seconds).

The cold proposal hash was `a0c0eb80a7a77c5c95107b6d3185aca1b3477a342e79a43cc2dbd4977b470c42`. Warm proposal hashes were all unique, as were their run/retrieval records. The accepted post-restart browser run generated proposal hash `759c76c84fba7858a239b52e5040d2b8af3b08237393a1149e5a9ecbe4b58235`; its authorized and executed hashes matched.

## Acceptance matrix

| Criterion | Result |
|---|---|
| Public health and exact model ready | PASS |
| Fresh user intent and live GraphRAG | PASS |
| Live Qwen planner and fresh proposal | PASS |
| Constraint resolution | PASS |
| Authorization binding | PASS |
| Actual deterministic GIS execution | PASS |
| Verification and complete provenance | PASS |
| Live map result | PASS |
| Tamper fail-closed | PASS |
| Unauthorized mutation absent | PASS |
| Cold plus three warm fresh runs | PASS |
| Restart and fresh run after restart | PASS |
| Two sequential runs | PASS |
| Failed request handling | PASS |
| Workspace reset | PASS |
| Browser/API integration (`LIVE CLOUD RUN`) | PASS |
| Bounded redistribution | PASS |
| Research semantic freeze | PASS; 0 regressions |

The post-restart tamper record `ama-tamper-test:67984ba07a0f4837bee0074c36d28cd8` was denied with `execution_attempted: false`, `mutation_started: false`, and no output. The immutable source fixture SHA-256 remained `6888bb077c6f7de2183ca1d4b1ca7d4bee934f939be7235520243c6cb4d10611` before and after all accepted operations.

## Reliability, security, and redistribution

Runs use isolated directories under `/tmp/ama-runtime`; the packaged input fixture remains read-only and authoritative mutation is disallowed. A new instance resets ephemeral state. The API permits only bounded demo operations, validates the canonical input, limits bodies to 4096 bytes, requires JSON, permits one active run, limits starts to six per minute, bounds CORS, applies security headers, and exposes no shell, filesystem, model-selection, graph-query, or arbitrary GIS operation.

Redistribution is `BOUNDED`: the full KG and restricted source text remain server-side, while public responses include only the permitted projected evidence required by the demo.

## Deployment findings

The first build configuration was rejected before build because a substitution required YAML quoting. A later image failed readiness because copying only the Ollama executable omitted its bundled server libraries. After including those libraries, the next revision reached the GPU but failed closed before proposal generation because schema-validation dependencies were absent. The final image pins those dependencies and imports them before readiness. No failed attempt performed GIS execution or mutated source data.

The accepted configuration scales to zero and costs approximately USD 1.05 per active hour at published component rates, plus build, network, and image storage. Three audit image versions remain in Artifact Registry; shared layers may be deduplicated.

## Reproducibility and evidence

Exact prerequisites, build/deploy commands, health and acceptance commands, reset behavior, security boundary, and cost notes are in [docs/deployment/ama-google-cloud-run.md](docs/deployment/ama-google-cloud-run.md). Machine-readable runtime and acceptance evidence are in:

- `artifacts/ama-cloud/ama-cloud-01-runtime-manifest.json`
- `artifacts/ama-cloud/ama-cloud-01-acceptance-results.json`

Next recommended work: add an Artifact Registry retention/cleanup policy and streamline immutable image layer caching after the audit retention window. This is operational cost hygiene, not AMA model or semantic performance work.

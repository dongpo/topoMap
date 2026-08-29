# AMA Google Cloud Run deployment

This procedure deploys the frozen AMA-LIVE-01 runtime as one Google Cloud Run GPU service. The container includes the API/frontend, bounded GraphRAG/KG assets, constraints, authorization, deterministic GIS executor, verification, provenance, Ollama 0.32.15, and the exact `qwen2.5:latest` model. It does not alter research semantics.

## Selected architecture

One service is sufficient and is the minimum topology. It avoids a second authenticated network hop and preserves the existing local Ollama boundary inside the container. The Qwen model is baked into the immutable image, verified by digest during build and startup, preloaded into GPU memory, and never downloaded per request.

The deployed configuration is:

| Setting | Value |
|---|---|
| Project | `sanguine-era-92109` |
| Region | `asia-southeast1` |
| Service | `ama-cloud-01` |
| Compute | 4 vCPU, 16 GiB, one NVIDIA L4 (24 GiB) |
| Scaling | min 0, max 1, concurrency 1 |
| Billing | instance-based; CPU is not throttled |
| Timeout | 3600 seconds |
| Filesystem | isolated run directories below `/tmp/ama-runtime` |
| Public URL | <https://ama-cloud-01-555420096938.asia-southeast1.run.app> |

Cloud Run currently supports one L4 GPU per instance in `asia-southeast1`; L4 requires at least 4 vCPU and 16 GiB, and a service can scale to zero. These facts are from the [Cloud Run GPU documentation](https://docs.cloud.google.com/run/docs/configuring/services/gpu). Cloud Run permits requests up to 60 minutes, offers a 32 GiB writable in-memory filesystem, and gives GPU containers up to four minutes to start; see [Cloud Run quotas and limits](https://docs.cloud.google.com/run/quotas).

### Feasibility and storage decision

The L4's 24 GiB VRAM comfortably holds the 4.68 GB Q4_K_M model. The final compressed image is 12.50 GB. Baking the model made startup deterministic and eliminated network/model-registry availability from the service readiness path. Google recommends baking smaller models into the image and describes streaming or Cloud Storage as alternatives for larger models in its [GPU best-practices guidance](https://docs.cloud.google.com/run/docs/configuring/services/gpu-best-practices). Cloud Storage volumes are available, but were unnecessary here; their semantics are documented in [Cloud Storage volume mounts](https://docs.cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts).

The service uses Artifact Registry, which is the supported Cloud Run image source described in the [Artifact Registry integration guide](https://docs.cloud.google.com/artifact-registry/docs/integrate-cloud-run). No credential is embedded in the image.

## Prerequisites

1. Install and authenticate the Google Cloud CLI: `gcloud auth login` and `gcloud auth application-default login` if local application credentials are also needed.
2. Select a billing-enabled Google Cloud project with Cloud Run, Cloud Build, and Artifact Registry permissions.
3. Ensure the regional Cloud Run NVIDIA L4 quota is available. The first deployment in this project exposed a regional non-zonal-redundancy quota of 3 L4 GPUs.
4. Check out branch `ama-cloud/ama-cloud-01-google-cloud-run` and verify the AMA-LIVE-01 predecessor is `0bef91d77f941b3dfb5971bb46131c9e35df4f20`.
5. Build from a clean worktree. Do not change the frozen model name or digest.

## Build and deploy

From the repository root:

```sh
gcloud auth login
gcloud config set project sanguine-era-92109
./scripts/deploy_ama_cloud_run.sh sanguine-era-92109 asia-southeast1
```

The script enables `run.googleapis.com`, `artifactregistry.googleapis.com`, and `cloudbuild.googleapis.com`; creates the regional `ama-cloud` Docker repository when absent; submits `deploy/ama-cloud/cloudbuild.yaml`; and deploys the service with the selected GPU/resources. The image tag is the source Git SHA. The final accepted image is also fixed by digest:

```text
asia-southeast1-docker.pkg.dev/sanguine-era-92109/ama-cloud/ama-cloud-01@sha256:be40ed830e1eabc12858286a8e1fe10811e5f69b128e082c87863a1da79b26a9
```

The startup sequence fails closed unless all of these pass before port 8080 is exposed:

- runtime schema dependencies import;
- Ollama reports version 0.32.15;
- the packaged model manifest and `/api/tags` digest equal `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`;
- `qwen2.5:latest` preloads with context 8192;
- Ollama `/api/ps` reports the exact model resident in GPU VRAM.

## Verify and accept

```sh
curl --fail --silent \
  https://ama-cloud-01-555420096938.asia-southeast1.run.app/health

python3 scripts/run_ama_cloud_acceptance.py \
  --base-url https://ama-cloud-01-555420096938.asia-southeast1.run.app \
  --warm-runs 3 \
  --output artifacts/ama-cloud/ama-cloud-01-acceptance-results.json
```

Open the service URL in a browser. The page must say `LIVE CLOUD RUN`; submit the canonical fresh mapping intent; inspect the live stages, evidence, constraints, proposal, authorization, GIS result, verification, provenance, and map; then run the tamper demonstration.

The accepted health payload reports `status: PASS`, `model_ready: true`, `gpu_model_preloaded: true`, the exact model digest, graph ID, and immutable fixture hash. The acceptance runner rejects reused run IDs or proposal hashes and verifies authorized hash equals executed hash, source fixture stability, live Ollama invocation, and fail-closed tampering.

## Restart, reset, and failure behavior

Deploying a new revision or changing a revision environment variable performs a service restart. Revision `ama-cloud-01-00004-r4s` was created for the restart audit; health and a fresh browser run passed afterward.

Each run receives a new directory under `/tmp/ama-runtime` initialized from the immutable packaged fixture. A fresh instance starts with an empty runtime directory. Only one live run is accepted at a time, and maximum instances is one, so no two executions share mutable state. Invalid input returns 400/415 before a run is created. A tampered proposal is denied before execution and creates no output. Cloud Run ephemeral storage is intentionally not authoritative storage.

## Public and redistribution boundary

The public API permits only the bounded AMA demo routes. There is no shell, arbitrary graph-query, arbitrary model-selection, arbitrary filesystem, or generic GIS endpoint. Bodies are limited to 4096 bytes, only JSON is accepted for mutation routes, socket reads time out, run starts are limited to six per minute per instance, and the default CORS policy is same-origin. Set `AMA_CORS_ORIGIN` to one exact frontend origin only when a separate frontend is required.

Redistribution remains `BOUNDED`. The full KG and restricted source text remain inside the container. Public evidence responses contain only the evidence projection required and permitted for the demonstration.

## Cost note

The service scales to zero, so compute charges accrue while an instance is active, including startup and the configured idle period. At current published component rates, one L4 plus 4 vCPU and 16 GiB is approximately USD 1.05 per active hour before free-tier effects, networking, build, and storage. Keeping minimum instances at zero avoids continuous GPU cost but preserves cold-start latency. See [Cloud Run pricing](https://cloud.google.com/run/pricing) and [minimum instances](https://docs.cloud.google.com/run/docs/configuring/min-instances).

Artifact Registry currently retains three task image versions; shared layers may be deduplicated, but a cleanup policy should be added after the audit retention window. The accepted image alone is 12.50 GB compressed.

## Troubleshooting findings from the first deployment

- An unquoted Cloud Build substitution caused YAML parsing to fail before any build or deployment. The substitution is now quoted.
- Copying only `/bin/ollama` omitted Ollama's bundled `llama-server`; the image now includes `/usr/lib/ollama`, following the layout in the [official Ollama Dockerfile](https://github.com/ollama/ollama/blob/main/Dockerfile).
- The first GPU-ready revision then failed closed before proposal creation because `jsonschema` and `referencing` were not installed. Exact runtime packages are now pinned and imported before readiness.

None of these failed attempts exposed a ready API, executed GIS work, or mutated the authoritative fixture.

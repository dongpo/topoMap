# syntax=docker/dockerfile:1.7

ARG OLLAMA_VERSION=0.32.15
FROM ollama/ollama:${OLLAMA_VERSION} AS ollama-runtime

FROM python:3.11.9-slim-bookworm AS model-builder
ARG FROZEN_MODEL=qwen2.5:latest
ARG FROZEN_MODEL_DIGEST=845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e
COPY --from=ollama-runtime /bin/ollama /usr/local/bin/ollama
RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
ENV OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_MODELS=/opt/ollama/models
RUN set -eu; \
    mkdir -p "${OLLAMA_MODELS}"; \
    ollama serve >/tmp/ollama-build.log 2>&1 & \
    server_pid=$!; \
    trap 'kill "${server_pid}" 2>/dev/null || true' EXIT; \
    ready=0; \
    for attempt in $(seq 1 120); do \
      if curl --fail --silent http://127.0.0.1:11434/api/tags >/dev/null; then ready=1; break; fi; \
      sleep 1; \
    done; \
    test "${ready}" = 1; \
    ollama pull "${FROZEN_MODEL}"; \
    python3 -c 'import hashlib, os, pathlib; p=pathlib.Path(os.environ["OLLAMA_MODELS"])/"manifests/registry.ollama.ai/library/qwen2.5/latest"; observed=hashlib.sha256(p.read_bytes()).hexdigest(); expected=os.environ["FROZEN_MODEL_DIGEST"]; assert observed == expected, f"frozen model digest mismatch: {observed}"'

FROM python:3.11.9-slim-bookworm AS runtime
ARG OLLAMA_VERSION=0.32.15
ARG FROZEN_MODEL_DIGEST=845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e
ARG SOURCE_REVISION=unknown
RUN pip install --no-cache-dir \
      attrs==25.3.0 \
      jsonschema==4.23.0 \
      jsonschema-specifications==2023.12.1 \
      referencing==0.35.1 \
      rpds-py==0.20.0
LABEL org.opencontainers.image.title="topoMap AMA-DEMO-02" \
      org.opencontainers.image.description="Public AMA evidence-to-action demo on frozen AMA-CLOUD-01" \
      org.opencontainers.image.revision="${SOURCE_REVISION}" \
      nma.ama.predecessor="0ebe7193951a8d4f5c5c6d10f3e5de4c71698284" \
      nma.ollama.version="${OLLAMA_VERSION}" \
      nma.model.digest="${FROZEN_MODEL_DIGEST}"
COPY --from=ollama-runtime /bin/ollama /usr/local/bin/ollama
COPY --from=ollama-runtime /usr/lib/ollama /usr/local/lib/ollama
COPY --from=model-builder --chown=65532:65532 /opt/ollama/models /opt/ollama/models
WORKDIR /app
COPY --chown=65532:65532 . /app
RUN useradd --uid 65532 --create-home --home-dir /home/ama --shell /usr/sbin/nologin ama \
    && chmod 0555 /app/scripts/ama_cloud_entrypoint.sh \
    && chmod -R a=rX /opt/ollama/models /app
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    AMA_DEPLOYMENT_LABEL="LIVE CLOUD RUN" \
    AMA_LLM_BASE_URL=http://127.0.0.1:11434 \
    AMA_OLLAMA_VERSION_EXPECTED=0.32.15 \
    AMA_REQUIRE_GPU=1 \
    AMA_RUNS_PER_MINUTE=6 \
    OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_MODELS=/opt/ollama/models \
    OLLAMA_KEEP_ALIVE=-1 \
    OLLAMA_NUM_PARALLEL=1 \
    LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64 \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    NVIDIA_VISIBLE_DEVICES=all \
    HOME=/tmp/ollama-home
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/app/scripts/ama_cloud_entrypoint.sh"]

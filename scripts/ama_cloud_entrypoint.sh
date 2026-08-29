#!/bin/sh
set -eu

expected_version="${AMA_OLLAMA_VERSION_EXPECTED:-0.32.15}"
mkdir -p "${HOME}" /tmp/ama-runtime

ollama serve &
ollama_pid=$!
trap 'kill "${ollama_pid}" 2>/dev/null || true' EXIT INT TERM

ready=0
attempt=1
while [ "${attempt}" -le 180 ]; do
  if python3 -c 'from urllib.request import urlopen; urlopen("http://127.0.0.1:11434/api/tags", timeout=2).read()' >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
  attempt=$((attempt + 1))
done
test "${ready}" = 1

version_output=$(ollama --version 2>&1 || true)
case "${version_output}" in
  *"${expected_version}"*) ;;
  *) echo "Frozen Ollama version check failed: ${version_output}" >&2; exit 1 ;;
esac
export AMA_OLLAMA_VERSION_OBSERVED="${expected_version}"

python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path
from urllib.request import urlopen

expected = "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"
manifest = (
    Path(os.environ["OLLAMA_MODELS"])
    / "manifests/registry.ollama.ai/library/qwen2.5/latest"
)
manifest_digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
if manifest_digest != expected:
    raise SystemExit(f"Frozen model manifest mismatch: {manifest_digest}")
tags = json.loads(urlopen("http://127.0.0.1:11434/api/tags", timeout=10).read())
matches = [item for item in tags.get("models", []) if item.get("name") == "qwen2.5:latest"]
if len(matches) != 1 or matches[0].get("digest") != expected:
    raise SystemExit("Frozen qwen2.5:latest identity is unavailable at startup")

from urllib.request import Request

preload = Request(
    "http://127.0.0.1:11434/api/generate",
    data=json.dumps(
        {
            "model": "qwen2.5:latest",
            "prompt": "",
            "stream": False,
            "keep_alive": -1,
            "options": {"num_ctx": 8192, "num_predict": 1, "temperature": 0},
        }
    ).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
json.loads(urlopen(preload, timeout=180).read())
loaded = json.loads(urlopen("http://127.0.0.1:11434/api/ps", timeout=10).read())
running = [item for item in loaded.get("models", []) if item.get("name") == "qwen2.5:latest"]
if len(running) != 1 or running[0].get("digest") != expected:
    raise SystemExit("Frozen Qwen model did not preload")
if os.environ.get("AMA_REQUIRE_GPU") == "1" and running[0].get("size_vram", 0) <= 0:
    raise SystemExit("Frozen Qwen model is not resident on the Cloud Run GPU")
PY
export AMA_GPU_MODEL_PRELOADED=true

exec python3 -m nma.ama_live_server \
  --repository-root /app \
  --host 0.0.0.0 \
  --port "${PORT:-8080}" \
  --storage-root /tmp/ama-runtime

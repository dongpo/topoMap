from __future__ import annotations

from pathlib import Path
import sys

import pytest

from nma.bench import run_benchmark
from nma.external import ExternalBaseline, load_external_config
from nma.specification import Specification

ROOT = Path(__file__).resolve().parents[1]


def test_full_nma_matches_all_frozen_tasks() -> None:
    result = run_benchmark(ROOT)
    assert result["task_count"] == 31
    assert result["systems"]["full_nma"]["accuracy"] == 1.0
    assert result["systems"]["full_nma"]["provenance_completeness"] == 1.0
    assert len(result["input_provenance"]["fingerprint_sha256"]) == 64
    assert len(result["input_provenance"]["specification_sha256"]) == 64
    dataset_hashes = result["input_provenance"]["dataset_files_sha256"]
    assert len(dataset_hashes) == 20
    assert all(len(value) == 64 for value in dataset_hashes.values())
    assert result["runtime"]["implementation"] == "CPython"
    assert (
        result["systems"]["ungrounded_proxy"]["accuracy"]
        < result["systems"]["full_nma"]["accuracy"]
    )


def test_external_adapter_protocol_supports_repeated_frozen_runs() -> None:
    adapter_code = (
        "import json,sys; request=json.load(sys.stdin); "
        "assert 'expected' not in request['task']; "
        "json.dump({'value':None,'evidence':[]},sys.stdout)"
    )
    result = run_benchmark(
        ROOT,
        systems=[],
        external_systems=[
            {
                "name": "protocol_oracle_test_only",
                "command": [sys.executable, "-c", adapter_code],
                "context_mode": "document_rag",
                "top_k": 2,
                "repetitions": 2,
                "timeout_seconds": 10,
                "metadata": {
                    "model": "protocol-oracle-test-only",
                    "model_version": "test-fixture-v1",
                    "server": "python",
                    "server_version": sys.version.split()[0],
                    "prompt_version": "none-test-only",
                },
            }
        ],
    )
    summary = result["systems"]["protocol_oracle_test_only"]
    assert summary["executions"] == 62
    assert summary["repetitions"] == 2
    assert summary["adapter_failures"] == 0
    assert summary["accuracy"] == 0.0
    assert all(row["actual"] is None for row in result["results"])


def test_external_run_rejects_placeholder_audit_metadata() -> None:
    configuration = load_external_config(ROOT / "benchmark/external-baselines.example.json")[0]
    specification = Specification.load(ROOT / "data/specifications/tnm-demo-2023.json")
    with pytest.raises(ValueError, match="placeholder audit metadata"):
        ExternalBaseline(configuration, specification, ROOT)

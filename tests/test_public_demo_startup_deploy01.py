from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil

import pytest

from nma.public_demo_gateway import PublicDemoConfig, StartupIntegrityValidator


ROOT = Path(__file__).resolve().parents[1]


def test_startup_fails_closed_on_frozen_public_data_authority_matrix() -> None:
    with pytest.raises(ValueError, match="data authority and frozen contract compatibility"):
        StartupIntegrityValidator(PublicDemoConfig.from_environment(ROOT)).validate()


def test_graph_byte_change_fails_readiness(tmp_path: Path) -> None:
    config = PublicDemoConfig.from_environment(ROOT)
    graph_root = tmp_path / "graph"
    graph_root.mkdir()
    source = config.graph_root / "nma-canonical-graph-v0.4.json"
    target = graph_root / source.name
    shutil.copyfile(source, target)
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="GraphRAG asset identity mismatch"):
        StartupIntegrityValidator(replace(config, graph_root=graph_root)).validate()


def test_authorization_byte_or_self_hash_change_fails_readiness(tmp_path: Path) -> None:
    config = PublicDemoConfig.from_environment(ROOT)
    authority = tmp_path / "authority"
    authority.mkdir()
    source = config.authority_root / "authorization-school-demo-b4ecdbfc35ecaf73293ed497.json"
    value = json.loads(source.read_text(encoding="utf-8"))
    value["authorization_hash"] = "0" * 64
    (authority / source.name).write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="authorization identity mismatch"):
        StartupIntegrityValidator(replace(config, authority_root=authority)).validate()


def test_unsafe_modes_and_unknown_demo_environment_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = PublicDemoConfig.from_environment(ROOT)
    with pytest.raises(ValueError, match="BUILD activation"):
        StartupIntegrityValidator(replace(config, build_activation="disabled")).validate()
    monkeypatch.setenv("NMA_DEMO_UPLOAD_ROOT", "/tmp")
    with pytest.raises(ValueError, match="unknown NMA demo"):
        PublicDemoConfig.from_environment(ROOT)

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "artifacts/public/d24/qr-manifest.json"


def test_d24_qr_manifest_matches_public_targets_and_files() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema"] == "nma.d24-qr-manifest/1.0"
    assert manifest["release_boundary"] == "stable-v0.2-public-agentic-v0.3-candidate"
    assert {item["id"] for item in manifest["targets"]} == {
        "public-demo",
        "candidate-branch",
    }

    for item in manifest["targets"]:
        asset = ROOT / item["asset"]
        assert asset.is_file()
        payload = asset.read_bytes()
        assert payload.startswith(b"\x89PNG\r\n\x1a\n")
        assert payload[12:16] == b"IHDR"
        assert hashlib.sha256(payload).hexdigest() == item["sha256"]
        width, height = struct.unpack(">II", payload[16:24])
        assert width == height
        assert width >= 400


def test_d24_docs_state_public_version_and_open_gates_truthfully() -> None:
    qa = (ROOT / "docs/D24-QA.md").read_text(encoding="utf-8")
    delivery = (ROOT / "docs/D24-PUBLIC-DELIVERY.md").read_text(encoding="utf-8")

    assert "gpt-5.6-terra" in qa
    assert "42 means registered implementation capability" in qa
    assert "only 9 entries currently have a" in qa
    assert "v0.2 RC1 evidence-only" in delivery
    assert "Agentic v0.3" in delivery
    assert "no DOI or archival identifier" in delivery
    assert "PMTiles redistribution permission remains unconfirmed" in delivery

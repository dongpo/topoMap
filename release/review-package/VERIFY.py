from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from nma.knowledge import PortrayalGraph  # noqa: E402
from nma.portrayal import PortrayalAgent, compile_maplibre_layers  # noqa: E402


def load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expect(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def verify_manifest() -> tuple[int, list[str]]:
    manifest = load_json("MANIFEST.json")
    failures = []
    for item in manifest["files"]:
        path = ROOT / item["path"]
        if not path.is_file():
            failures.append(f"missing:{item['path']}")
        elif sha256(path) != item["sha256"]:
            failures.append(f"checksum:{item['path']}")

    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and path.name not in {"MANIFEST.json", "CHECKSUMS.sha256"}
    }
    expected = {item["path"] for item in manifest["files"]}
    for path in sorted(actual - expected):
        failures.append(f"unmanifested:{path}")
    return len(manifest["files"]), failures


def sensitive_patterns() -> list[bytes]:
    return [
        ("/" + "Users/").encode(),
        ("/" + "home/").encode(),
        ("C:" + "\\\\Users\\").encode(),
        ("-----BEGIN " + "PRIVATE KEY-----").encode(),
        ("sk-" + "proj-").encode(),
        ("github_" + "pat_").encode(),
        ("gh" + "o_").encode(),
        ("xox" + "b-").encode(),
    ]


def scan_bytes(label: str, value: bytes) -> list[str]:
    return [label for pattern in sensitive_patterns() if pattern in value]


def scan_sensitive_content() -> list[str]:
    findings = []
    for path in sorted(item for item in ROOT.rglob("*") if item.is_file()):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.lower() == ".pptx":
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if name.endswith((".xml", ".rels")):
                        findings.extend(scan_bytes(f"{relative}!{name}", archive.read(name)))
        elif path.suffix.lower() not in {".svg", ".png", ".jpg", ".jpeg"}:
            findings.extend(scan_bytes(relative, path.read_bytes()))
    return sorted(set(findings))


def verify_scenes() -> dict[str, Any]:
    contract = load_json("data/demo/five-scene-demo.json")
    graph = PortrayalGraph.load(ROOT / "data/knowledge/portrayal-graph.json")
    agent = PortrayalAgent(graph)
    layers = compile_maplibre_layers(graph)
    results = []

    for scene in sorted(contract["scenes"], key=lambda item: item["order"]):
        expected = scene["expected"]
        answer = agent.answer(scene["prompt"])
        if expected["feature_code"] not in answer["feature_codes"]:
            raise ValueError(f"{scene['id']}: frozen feature not retrieved")
        if expected["evidence_page"] not in {item["page"] for item in answer["evidence"]}:
            raise ValueError(f"{scene['id']}: frozen evidence page not retrieved")

        decision = agent.select_symbol(
            scene["input"]["feature_code"],
            scale_denominator=contract["profile"]["scale_denominator"],
            profile_id=contract["profile"]["id"],
            attributes=scene["input"].get("attributes", {}),
        ).as_dict()
        expect(decision["status"], "selected", f"{scene['id']} status")
        expect(decision["symbol"]["symbol_id"], expected["symbol_id"], f"{scene['id']} symbol")
        expect(
            decision["symbol"]["selected_action"],
            expected["selected_action"],
            f"{scene['id']} action",
        )
        expect(decision["evidence"]["page"], expected["evidence_page"], f"{scene['id']} page")
        if not decision["graph_path"]["nodes"] or not decision["graph_path"]["edges"]:
            raise ValueError(f"{scene['id']}: empty graph path")
        primary_layer = next(
            (
                layer
                for layer in layers
                if layer.get("source-layer") == expected["primary_source_layer"]
                and layer["metadata"]["nma:featureCode"] == expected["feature_code"]
                and layer["metadata"].get("nma:role") is None
            ),
            None,
        )
        if primary_layer is None:
            raise ValueError(f"{scene['id']}: expected MapLibre layer not compiled")
        results.append(
            {
                "scene": scene["id"],
                "feature_code": decision["feature_code"],
                "action": decision["symbol"]["selected_action"],
                "evidence_page": decision["evidence"]["page"],
                "status": "passed",
            }
        )

    scale_control = agent.select_symbol(
        contract["negative_control"]["feature_code"],
        scale_denominator=contract["negative_control"]["scale_denominator"],
        profile_id=contract["profile"]["id"],
    ).as_dict()
    profile_control = agent.select_symbol(
        contract["negative_control"]["feature_code"],
        scale_denominator=contract["profile"]["scale_denominator"],
        profile_id=contract["negative_control"]["unsupported_profile_id"],
    ).as_dict()
    expect(scale_control["status"], "abstain", "unsupported-scale control")
    expect(profile_control["status"], "abstain", "unsupported-profile control")
    return {"scene_count": len(results), "scenes": results, "negative_controls": 2}


def main() -> int:
    file_count, checksum_failures = verify_manifest()
    sensitive_matches = scan_sensitive_content()
    scene_result = verify_scenes()
    result = {
        "package": "nma-v0.2-review-package",
        "status": "passed" if not checksum_failures and not sensitive_matches else "failed",
        "manifest_file_count": file_count,
        "checksum_failures": len(checksum_failures),
        "checksum_failure_details": checksum_failures,
        "sensitive_matches": len(sensitive_matches),
        "sensitive_match_details": sensitive_matches,
        **scene_result,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

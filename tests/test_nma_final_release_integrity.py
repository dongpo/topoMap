from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from nma.core import canonical_json, canonical_sha256
from nma.school_hero_execution import authorization_sha256


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data/specifications/nma-v1.0-final-release-manifest.json"
DEMO_MANIFEST_PATH = ROOT / "data/specifications/nma-demo-final-freeze-manifest-v1.0.json"
GEN_MANIFEST_PATH = ROOT / "data/specifications/nma-generalization-final-freeze-manifest-v1.0.json"
FIXTURE_RECORD_PATH = ROOT / "data/specifications/nma-demo-controlled-fixture-baseline-v1.0.json"
RETRY_RECORD_PATH = (
    ROOT / "data/specifications/nma-demo-02-retry-controlled-e2e-acceptance-record-v1.0.json"
)
AUTHORIZATION_PATH = (
    ROOT
    / "artifacts/runtime/school-hero/authorizations"
    / "authorization-school-demo-b4ecdbfc35ecaf73293ed497.json"
)
PREDECESSOR_SHA = "05af154a14e781f20b5cf2d3996eac8191875b0f"
ALLOWED_FINAL_FILES = {
    "NMA-FINAL-Completion-Report.md",
    "data/specifications/nma-v1.0-final-release-manifest.json",
    "tests/test_nma_final_release_integrity.py",
}
READ_ONLY_GIT_COMMANDS = {
    "cat-file",
    "diff",
    "merge-base",
    "rev-parse",
    "status",
}


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*arguments: str, check: bool = True) -> str:
    assert arguments and arguments[0] in READ_ONLY_GIT_COMMANDS
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=check,
    )
    return result.stdout.strip()


def _candidate_or_committed_scope() -> set[str]:
    head = _git("rev-parse", "HEAD")
    if head != PREDECESSOR_SHA:
        return set(_git("diff", "--name-only", f"{PREDECESSOR_SHA}..HEAD").splitlines())
    changed: set[str] = set()
    for line in _git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if not line:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed.add(path)
    return changed


def test_nf01_exact_demo_final_predecessor_and_release_scope() -> None:
    manifest = _load(MANIFEST_PATH)
    assert manifest["repository"]["predecessor"] == {
        "branch": "freeze/demo-final-05af154",
        "commit_sha": PREDECESSOR_SHA,
        "annotated_tag": "nma-demo-v1.0-final",
        "tag_object_sha": "794a71ab8fdf56c4504f85521f7a063a9acb63f9",
    }
    head = _git("rev-parse", "HEAD")
    if head != PREDECESSOR_SHA:
        assert _git("rev-parse", "HEAD^") == PREDECESSOR_SHA
    assert _candidate_or_committed_scope() == ALLOWED_FINAL_FILES


def test_nf02_demo_final_identity_and_manifest_hash_are_exact() -> None:
    manifest = _load(MANIFEST_PATH)["frozen_identities"]["demo_final"]
    assert manifest == {
        "commit_sha": PREDECESSOR_SHA,
        "annotated_tag": "nma-demo-v1.0-final",
        "tag_object_sha": "794a71ab8fdf56c4504f85521f7a063a9acb63f9",
        "manifest_path": "data/specifications/nma-demo-final-freeze-manifest-v1.0.json",
        "manifest_self_hash": "a4ef21b45f94118661448ad33bd797566c82e72e5090c553b066675e14fa8001",
    }
    assert _git("cat-file", "-t", "refs/tags/nma-demo-v1.0-final") == "tag"
    assert _git("rev-parse", "refs/tags/nma-demo-v1.0-final") == manifest["tag_object_sha"]
    assert _git("rev-parse", "refs/tags/nma-demo-v1.0-final^{}") == PREDECESSOR_SHA
    source = _load(DEMO_MANIFEST_PATH)
    supplied = source.pop("canonical_manifest_sha256")
    assert supplied == manifest["manifest_self_hash"] == canonical_sha256(source)


def test_nf03_gen_final_identity_and_manifest_hash_are_exact() -> None:
    frozen = _load(MANIFEST_PATH)["frozen_identities"]["gen_final"]
    assert frozen["commit_sha"] == "380cc6ea2a4498ce83690521c933accfd918818e"
    assert frozen["annotated_tag"] == "nma-generalization-v1.0-final"
    assert frozen["tag_object_sha"] == "9ba26ff032e23f0ba5de80d809f08eb6e973bb4f"
    assert frozen["manifest_self_hash"] == (
        "71683e0486b4ff952e41ad9cd98e6e0405c61f07e09d40b553540a0203c874f1"
    )
    assert _git("cat-file", "-t", "refs/tags/nma-generalization-v1.0-final") == "tag"
    assert _git("rev-parse", "refs/tags/nma-generalization-v1.0-final") == frozen["tag_object_sha"]
    assert _git("rev-parse", "refs/tags/nma-generalization-v1.0-final^{}") == frozen["commit_sha"]
    source = _load(GEN_MANIFEST_PATH)
    supplied = source.pop("canonical_manifest_sha256")
    assert supplied == frozen["manifest_self_hash"] == canonical_sha256(source)


def test_nf04_core_identity_is_exact() -> None:
    frozen = _load(MANIFEST_PATH)["frozen_identities"]["core_final"]
    assert frozen == {
        "commit_sha": "5eb138ae7686502431587743ebce9ddf92c5a799",
        "annotated_tag": "nma-core-v1.0-final",
        "tag_object_sha": "5729f2db0fc441b3eb0a22c1f76b0f6af3f368ea",
    }
    assert _git("rev-parse", "refs/tags/nma-core-v1.0-final") == frozen["tag_object_sha"]
    assert _git("rev-parse", "refs/tags/nma-core-v1.0-final^{}") == frozen["commit_sha"]


def test_nf05_school_identity_is_exact() -> None:
    frozen = _load(MANIFEST_PATH)["frozen_identities"]["school_hero"]
    assert frozen == {
        "commit_sha": "56f99eb9ae63272a68accac3041fb10eacefb986",
        "canonical_remote_branch": "freeze/hero-final-school-hero-56f99eb",
    }
    assert _git("merge-base", frozen["commit_sha"], PREDECESSOR_SHA) == frozen["commit_sha"]


def test_nf06_road_identity_is_exact() -> None:
    frozen = _load(MANIFEST_PATH)["frozen_identities"]["road_final"]
    assert frozen == {
        "commit_sha": "325c70d5335f57c43a8af85822db25032aa225c3",
        "annotated_tag": "nma-road-v1.0-final",
        "tag_object_sha": "d60fffa873428d1ba8b308ea0d4d2028ac8431fd",
    }
    assert _git("rev-parse", "refs/tags/nma-road-v1.0-final") == frozen["tag_object_sha"]
    assert _git("rev-parse", "refs/tags/nma-road-v1.0-final^{}") == frozen["commit_sha"]


def test_nf07_build_identity_and_tag_are_exact() -> None:
    frozen = _load(MANIFEST_PATH)["frozen_identities"]["build_final"]
    assert frozen == {
        "commit_sha": "95de5fa3657a2c8ac7847f1ee1010c48ea984cd7",
        "annotated_tag": "nma-build-v1.0-final",
        "tag_object_sha": "1b55ff67fd670a482da74975ce41fa86df5dd71f",
    }
    assert _git("rev-parse", "refs/tags/nma-build-v1.0-final") == frozen["tag_object_sha"]
    assert _git("rev-parse", "refs/tags/nma-build-v1.0-final^{}") == frozen["commit_sha"]


def test_nf08_runtime_identities_are_byte_exact() -> None:
    runtime = _load(MANIFEST_PATH)["runtime"]
    assert runtime["launch_command"] == (
        "PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 8080"
    )
    assert runtime["demo_url"] == "http://127.0.0.1:8080/nmaAgentDemoV1.html?basemap=local"
    assert runtime["unified_api_route"] == "http://127.0.0.1:8080/api/nma/runtime"
    for path, expected in runtime["files"].items():
        assert _file_sha256(ROOT / path) == expected, path


def test_nf09_controlled_fixture_commitments_are_exact() -> None:
    frozen = _load(MANIFEST_PATH)["controlled_fixtures"]
    source = _load(FIXTURE_RECORD_PATH)
    assert frozen["archive"] == {
        "path": "data/datasets/112年多維度SHP成果_0502.zip",
        "sha256": "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
        "size_bytes": 12822898,
        "tracked": False,
        "redistributed": False,
    }
    archive = ROOT / frozen["archive"]["path"]
    if archive.exists():
        assert archive.stat().st_size == frozen["archive"]["size_bytes"]
        assert _file_sha256(archive) == frozen["archive"]["sha256"]
    school = frozen["school"]
    road = frozen["road"]
    assert school["identity"] == source["school"]["controlled_demo_fixture_identity"]
    assert school["aggregate_sha256"] == source["school"]["aggregate_sha256"]
    assert school["terrainid"] == "9920103"
    assert school["feature_count"] == 15
    assert school["feature_distribution"] == [0, 1, 0, 12, 1, 1]
    assert road["identity"] == source["road"]["controlled_demo_fixture_identity"]
    assert road["aggregate_sha256"] == source["road"]["aggregate_sha256"]
    assert road["feature_count"] == 196
    assert road["ordered_segment_ids"] == ["K0000004671", "K0000004913", "K0000005348"]
    assert road["vertex_counts"] == [4, 3, 4]


def test_nf10_school_demo_authorization_is_exact() -> None:
    frozen = _load(MANIFEST_PATH)["school_authorization"]
    authorization = _load(AUTHORIZATION_PATH)
    assert (
        frozen["authorization_id"]
        == authorization["authorization_id"]
        == ("authorization-school-demo-b4ecdbfc35ecaf73293ed497")
    )
    assert (
        frozen["authorization_hash"]
        == authorization_sha256(authorization)
        == ("d5546bd1b2176a4ad287acb1c78740ce79a90db76d05739dc871267d901dac67")
    )
    assert frozen["human_approval"] == "approved"
    assert frozen["execution_id"] == "exec-8d174b62fb63189987eafdb6"


def test_nf11_school_road_build_acceptance_evidence_is_intact() -> None:
    frozen = _load(MANIFEST_PATH)["accepted_scenarios"]
    accepted = _load(RETRY_RECORD_PATH)["scenarios"]
    for domain in ("school", "road", "build"):
        assert frozen[domain]["status"] == accepted[domain]["status"] == "PASS"
        for key, value in frozen[domain].items():
            if key in {"status", "portrayal", "activation_status"}:
                continue
            assert accepted[domain][key] == value, f"{domain}.{key}"
    assert frozen["school"]["feature_count"] == 15
    assert frozen["road"]["execution_id"] == "road-exec-33766f336d9cc18eb2ac159e"
    assert frozen["build"]["activation_status"] == "held-not-requested"


def test_nf12_demo_a1_through_a12_are_preserved() -> None:
    frozen = _load(MANIFEST_PATH)["demo_a1_a12"]
    accepted = _load(RETRY_RECORD_PATH)["demo_a1_a12"]
    assert frozen == accepted
    assert list(frozen) == [f"DEMO-A{i}" for i in range(1, 13)]
    assert set(frozen.values()) == {"PASS"}


def test_nf13_release_safety_invariants_are_fail_closed() -> None:
    manifest = _load(MANIFEST_PATH)
    counts = manifest["counts_and_safety"]
    assert counts == {
        "external_data_substitutions": 0,
        "production_reachable_demo_stubs": 0,
        "frozen_semantic_modifications": 0,
        "controlled_fixture_modifications": 0,
        "runtime_source_changes": 0,
        "core_source_changes": 0,
        "school_source_changes": 0,
        "road_source_changes": 0,
        "build_source_changes": 0,
        "graphrag_changes": 0,
        "mapping_rule_changes": 0,
        "generic_contract_changes": 0,
        "authorization_semantic_changes": 0,
        "build_automatic_activation": False,
    }
    assert manifest["accepted_scenarios"]["build"]["automatic_production_activation"] is False
    runtime_source = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in ("src/nma/unified_runtime.py", "scripts/run_nma_agent_server.py")
    )
    for forbidden in ("class DemoStub", "fake_execution", "fake_qa", "fake_provenance"):
        assert forbidden not in runtime_source
    assert _candidate_or_committed_scope() == ALLOWED_FINAL_FILES


def test_nf14_manifest_self_hash_normative_artifacts_and_release_contract() -> None:
    manifest = _load(MANIFEST_PATH)
    assert manifest["contract"] == "nma.final-release/1.0"
    assert manifest["version"] == "1.0"
    basis = deepcopy(manifest)
    supplied = basis.pop("canonical_manifest_sha256")
    assert supplied == canonical_sha256(basis)
    assert canonical_json(basis) == canonical_json(deepcopy(basis))
    tampered = deepcopy(basis)
    tampered["counts_and_safety"]["external_data_substitutions"] = 1
    assert canonical_sha256(tampered) != supplied
    for artifact in manifest["normative_release_artifacts"]:
        assert _file_sha256(ROOT / artifact["path"]) == artifact["sha256"], artifact["path"]
    for contract in manifest["generic_contract_identities"].values():
        assert _file_sha256(ROOT / contract["path"]) == contract["sha256"], contract["path"]
    assert _candidate_or_committed_scope() == ALLOWED_FINAL_FILES

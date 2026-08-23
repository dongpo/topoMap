from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator

from nma.core import canonical_json, canonical_sha256
from nma.school_hero_execution import authorization_sha256


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data/specifications/nma-demo-final-freeze-manifest-v1.0.json"
RETRY_RECORD_PATH = (
    ROOT / "data/specifications/nma-demo-02-retry-controlled-e2e-acceptance-record-v1.0.json"
)
FIXTURE_RECORD_PATH = ROOT / "data/specifications/nma-demo-controlled-fixture-baseline-v1.0.json"
AUTHORIZATION_PATH = (
    ROOT
    / "artifacts/runtime/school-hero/authorizations"
    / "authorization-school-demo-b4ecdbfc35ecaf73293ed497.json"
)
PREDECESSOR_SHA = "b80ea93e5e750948827bfa46fef9fdc1b1352305"
ACCEPTED_VERDICT = "PASS — NMA CONTROLLED END-TO-END DEMO ACCEPTED"
ALLOWED_FINAL_FILES = {
    "NMA-DEMO-FINAL-Completion-Report.md",
    "data/specifications/nma-demo-final-freeze-manifest-v1.0.json",
    "tests/test_demo_final_controlled_freeze.py",
}
READ_ONLY_GIT_COMMANDS = {
    "cat-file",
    "check-ignore",
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


def test_df01_exact_retry_predecessor_and_change_scope() -> None:
    manifest = _load(MANIFEST_PATH)
    predecessor = manifest["repository"]["predecessor"]
    assert predecessor == {
        "branch": "demo/demo-02-retry-controlled-end-to-end-acceptance",
        "commit_sha": PREDECESSOR_SHA,
        "verdict": ACCEPTED_VERDICT,
    }
    head = _git("rev-parse", "HEAD")
    if head != PREDECESSOR_SHA:
        assert _git("rev-parse", "HEAD^") == PREDECESSOR_SHA
    assert _candidate_or_committed_scope() == ALLOWED_FINAL_FILES


def test_df02_exact_retry_accepted_verdict() -> None:
    report = (ROOT / "NMA-DEMO-02-Retry-Controlled-End-to-End-Acceptance-Report.md").read_text(
        encoding="utf-8"
    )
    retry = _load(RETRY_RECORD_PATH)
    assert retry["verdict"] == ACCEPTED_VERDICT
    assert f"**{ACCEPTED_VERDICT}**" in report
    assert retry["scenarios"]["school"]["status"] == "PASS"
    assert retry["scenarios"]["road"]["status"] == "PASS"
    assert retry["scenarios"]["build"]["status"] == "PASS"


def test_df03_exact_school_controlled_fixture_commitment() -> None:
    manifest = _load(MANIFEST_PATH)["controlled_fixtures"]
    frozen = manifest["school"]
    baseline = _load(FIXTURE_RECORD_PATH)["school"]
    assert frozen["identity"] == baseline["controlled_demo_fixture_identity"]
    assert frozen["aggregate_sha256"] == baseline["aggregate_sha256"]
    assert frozen["terrainid"] == baseline["source_filter"]["value"] == "9920103"
    assert frozen["geometry"] == baseline["geometry_quality"]["declared_geometry"] == "Point"
    assert frozen["crs"] == baseline["crs"]["declared_name"] == "TWD97[2020]_TM121"
    assert (
        frozen["feature_distribution"]
        == [layer["selected_feature_count"] for layer in baseline["layers"]]
        == [0, 1, 0, 12, 1, 1]
    )
    assert frozen["feature_count"] == 15
    assert frozen["valid_geometry"] and frozen["unique_ids"] and frozen["labels_present"]
    assert [layer["layer_id"] for layer in frozen["layers"]] == [
        "J01_MARK",
        "J13_MARK",
        "J17_MARK",
        "K01_MARK",
        "K02_MARK",
        "K14_MARK",
    ]
    expected_components = {
        layer["layer_id"]: {
            component["extension"]: component["sha256"] for component in layer["components"]
        }
        for layer in baseline["layers"]
    }
    assert {
        layer["layer_id"]: layer["components"] for layer in frozen["layers"]
    } == expected_components
    package = ROOT / manifest["package"]["path"]
    if package.exists():
        assert package.stat().st_size == manifest["package"]["size_bytes"] == 12822898
        assert _file_sha256(package) == manifest["package"]["sha256"]
    assert manifest["package"]["tracked"] is False
    assert manifest["package"]["redistributed"] is False


def test_df04_exact_road_fixture_package_and_geometry_commitments() -> None:
    frozen = _load(MANIFEST_PATH)["controlled_fixtures"]["road"]
    baseline = _load(FIXTURE_RECORD_PATH)["road"]
    assert frozen["identity"] == baseline["controlled_demo_fixture_identity"]
    assert frozen["aggregate_sha256"] == baseline["aggregate_sha256"]
    assert frozen["feature_count"] == baseline["layer"]["feature_count"] == 196
    assert frozen["crs"] == baseline["crs"]["declared_name"] == "TWD97[2020]_TM121"
    assert frozen["components"] == {
        component["extension"]: component["sha256"] for component in baseline["layer"]["components"]
    }
    segments = baseline["authorized_segments"]
    assert frozen["ordered_segment_ids"] == [segment["segment_id"] for segment in segments]
    assert frozen["vertex_counts"] == [segment["vertex_count"] for segment in segments] == [4, 3, 4]
    assert frozen["coordinate_array_sha256"] == [
        segment["coordinate_array_sha256"] for segment in segments
    ]
    assert frozen["source_geometry_sha256"] == [
        segment["source_geometry_sha256"] for segment in segments
    ]
    assert all(segment["valid"] and segment["simple"] for segment in segments)
    assert frozen["class_code"] == "9420400"
    assert frozen["route"] == "縣126"
    assert frozen["name"] == "中山街"
    assert frozen["private_coordinate_arrays_published"] is False


def test_df05_exact_school_demo_authorization() -> None:
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
    assert frozen["domain"] == "school"
    assert frozen["canonical_validation_consumption"] == "PASS"
    assert frozen["downstream_execution_id"] == "exec-8d174b62fb63189987eafdb6"


def test_df06_demo_authorization_does_not_impersonate_historical_hero03() -> None:
    frozen = _load(MANIFEST_PATH)["school_authorization"]
    assert frozen["historical_identity_reused"] is False
    assert frozen["authorization_id"] != frozen["historical_hero03_authorization_id"]
    assert frozen["authorization_hash"] != frozen["historical_hero03_authorization_hash"]
    historical = _load(MANIFEST_PATH)["historical_evidence_only"]
    assert historical["canonical_success_predecessors"] is False
    assert set(historical) == {
        "DEMO-01A",
        "DEMO-01B",
        "FAILED-DEMO-02",
        "canonical_success_predecessors",
    }


def test_df07_canonical_runtime_identity_is_byte_exact() -> None:
    runtime = _load(MANIFEST_PATH)["runtime"]
    assert runtime["launch_command"] == (
        "PYTHONPATH=src:. python3 scripts/run_nma_agent_server.py --host 127.0.0.1 --port 8080"
    )
    assert runtime["demo_url"] == "http://127.0.0.1:8080/nmaAgentDemoV1.html?basemap=local"
    assert runtime["unified_api_route"] == "http://127.0.0.1:8080/api/nma/runtime"
    for relative_path, expected_sha256 in runtime["files"].items():
        assert _file_sha256(ROOT / relative_path) == expected_sha256, relative_path


def test_df08_scenario_s_r_b_integrity_is_exact() -> None:
    frozen = _load(MANIFEST_PATH)["scenarios"]
    accepted = _load(RETRY_RECORD_PATH)["scenarios"]
    mapping = {"S": "school", "R": "road", "B": "build"}
    for scenario_id, accepted_id in mapping.items():
        scenario = frozen[scenario_id]
        source = accepted[accepted_id]
        assert scenario["domain"] == accepted_id
        assert scenario["status"] == source["status"] == "PASS"
        for key, value in scenario.items():
            if key in {"domain", "portrayal", "activation_status"}:
                continue
            assert source[key] == value, f"{scenario_id}.{key}"
    assert frozen["S"]["feature_count"] == 15
    assert "4/3/4" in frozen["R"]["portrayal"]
    assert frozen["B"]["activation_status"] == "held-not-requested"


def test_df09_demo_a1_through_a12_remain_fully_accepted() -> None:
    frozen = _load(MANIFEST_PATH)["demo_a1_a12"]
    accepted = _load(RETRY_RECORD_PATH)["demo_a1_a12"]
    assert frozen == accepted
    assert list(frozen) == [
        "DEMO-A1",
        "DEMO-A2",
        "DEMO-A3",
        "DEMO-A4",
        "DEMO-A5",
        "DEMO-A6",
        "DEMO-A7",
        "DEMO-A8",
        "DEMO-A9",
        "DEMO-A10",
        "DEMO-A11",
        "DEMO-A12",
    ]
    assert set(frozen.values()) == {"PASS"}
    assert frozen["DEMO-A6"] == frozen["DEMO-A8"] == "PASS"


def test_df10_external_data_substitution_count_is_zero() -> None:
    manifest = _load(MANIFEST_PATH)
    assert manifest["counts_and_safety"]["external_data_substitutions"] == 0
    assert _load(RETRY_RECORD_PATH)["counts"]["external_data_substitutions"] == 0
    assert manifest["controlled_reproduction_model"] == [
        "canonical repository",
        "exact controlled School fixture package",
        "exact controlled ROAD fixture package",
        "fixture hash verification",
        "accepted School demo authorization",
        "documented runtime launch",
    ]


def test_df11_production_reachable_demo_stub_count_is_zero() -> None:
    manifest = _load(MANIFEST_PATH)
    assert manifest["counts_and_safety"]["production_reachable_demo_stubs"] == 0
    accepted_report = (
        ROOT / "NMA-DEMO-02-Retry-Controlled-End-to-End-Acceptance-Report.md"
    ).read_text(encoding="utf-8")
    assert "Production-reachable demo stubs: **0**" in accepted_report
    runtime_source = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in ("src/nma/unified_runtime.py", "scripts/run_nma_agent_server.py")
    )
    for forbidden in ("class DemoStub", "fake_execution", "fake_qa", "fake_provenance"):
        assert forbidden not in runtime_source


def test_df12_build_automatic_activation_remains_false() -> None:
    manifest = _load(MANIFEST_PATH)
    assert manifest["counts_and_safety"]["build_automatic_activation"] is False
    assert manifest["scenarios"]["B"]["automatic_production_activation"] is False
    assert manifest["scenarios"]["B"]["activation_status"] == "held-not-requested"
    retry = _load(RETRY_RECORD_PATH)
    assert retry["runtime"]["automatic_build_activation"] is False
    assert retry["scenarios"]["build"]["automatic_production_activation"] is False


def test_df13_frozen_architecture_identities_and_tags_are_unchanged() -> None:
    frozen = _load(MANIFEST_PATH)["frozen_architecture"]
    expected = {
        "GEN-FINAL": "380cc6ea2a4498ce83690521c933accfd918818e",
        "CORE-FINAL": "5eb138ae7686502431587743ebce9ddf92c5a799",
        "School-Hero": "56f99eb9ae63272a68accac3041fb10eacefb986",
        "ROAD-FINAL": "325c70d5335f57c43a8af85822db25032aa225c3",
        "BUILD-FINAL": "95de5fa3657a2c8ac7847f1ee1010c48ea984cd7",
    }
    assert {name: value["commit_sha"] for name, value in frozen.items()} == expected
    for value in frozen.values():
        assert _git("merge-base", value["commit_sha"], PREDECESSOR_SHA) == value["commit_sha"]
    for name in ("GEN-FINAL", "CORE-FINAL", "ROAD-FINAL", "BUILD-FINAL"):
        tag = frozen[name]["annotated_tag"]
        assert _git("cat-file", "-t", f"refs/tags/{tag}") == "tag"
        assert _git("rev-parse", f"refs/tags/{tag}") == frozen[name]["tag_object_sha"]
        assert _git("rev-parse", f"refs/tags/{tag}^{{}}") == frozen[name]["commit_sha"]


def test_df14_manifest_self_hash_schema_artifacts_and_no_functional_change() -> None:
    manifest = _load(MANIFEST_PATH)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": [
            "contract",
            "version",
            "status",
            "canonical_manifest_sha256",
            "repository",
            "freeze_claim",
            "authoritative_success_chain",
            "frozen_architecture",
            "controlled_fixtures",
            "school_authorization",
            "runtime",
            "scenarios",
            "demo_a1_a12",
            "counts_and_safety",
            "normative_evidence_artifacts",
            "integrity_test_contract",
        ],
        "properties": {
            "contract": {"const": "nma.demo-final-freeze/1.0"},
            "version": {"const": "1.0"},
            "canonical_manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
    }
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(manifest)
    basis = deepcopy(manifest)
    supplied = basis.pop("canonical_manifest_sha256")
    assert supplied == canonical_sha256(basis)
    assert canonical_json(basis) == canonical_json(deepcopy(basis))
    tampered = deepcopy(basis)
    tampered["counts_and_safety"]["external_data_substitutions"] = 1
    assert canonical_sha256(tampered) != supplied
    for artifact in manifest["normative_evidence_artifacts"]:
        assert _file_sha256(ROOT / artifact["path"]) == artifact["sha256"], artifact["path"]
    zero_change_keys = {
        "runtime_source_changes",
        "school_source_changes",
        "road_source_changes",
        "build_source_changes",
        "graphrag_changes",
        "mapping_rule_changes",
        "controlled_fixture_modifications",
        "frozen_semantic_changes",
        "authorization_semantic_changes",
        "generic_architecture_changes",
    }
    counts = manifest["counts_and_safety"]
    assert {counts[key] for key in zero_change_keys} == {0}
    assert _candidate_or_committed_scope() == ALLOWED_FINAL_FILES

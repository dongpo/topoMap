from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator, ValidationError
import pytest

from build_contracts.human_building_production_policy import (
    BUILD09E2_ARTIFACT_SHA256,
    EXPECTED_BUILD09E2_COMMIT,
    HumanBuildingProductionPolicyError,
    build_finalized_contract,
    build_policy_record,
    finalized_contract_sha256,
    policy_record_sha256,
    validate_finalized_contract,
    validate_policy_record,
)


ROOT = Path(__file__).resolve().parents[1]
RESOLUTION_PATH = (
    ROOT
    / "data/specifications/nma-build-09e2-golden-j13-j17-production-applicability-resolution-v1.0.json"
)
PREDECESSOR_CONTRACT_PATH = (
    ROOT / "data/specifications/nma-build-09e2-successor-building-production-contract-v1.0.json"
)
BUILD09_PATH = (
    ROOT / "data/specifications/nma-build-09-golden-building-production-contract-v1.0.json"
)
POLICY_PATH = (
    ROOT
    / "data/specifications/nma-build-09f-golden-human-building-production-policy-authorization-v1.0.json"
)
CONTRACT_PATH = (
    ROOT / "data/specifications/nma-build-09f-finalized-building-production-contract-v1.0.json"
)
POLICY_SCHEMA_PATH = (
    ROOT / "schemas/building-human-production-policy-authorization-v1.0.schema.json"
)
CONTRACT_SCHEMA_PATH = ROOT / "schemas/building-finalized-production-contract-v1.0.schema.json"

ALLOWED_BUILD09F_FILES = {
    "BUILD-09F-Completion-Report.md",
    "build_contracts/human_building_production_policy.py",
    "data/specifications/nma-build-09f-finalized-building-production-contract-v1.0.json",
    "data/specifications/nma-build-09f-golden-human-building-production-policy-authorization-v1.0.json",
    "schemas/building-finalized-production-contract-v1.0.schema.json",
    "schemas/building-human-production-policy-authorization-v1.0.schema.json",
    "tests/test_human_building_production_policy_build09f.py",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture()
def resolution() -> dict:
    return _load(RESOLUTION_PATH)


@pytest.fixture()
def predecessor_contract() -> dict:
    return _load(PREDECESSOR_CONTRACT_PATH)


@pytest.fixture()
def build09() -> dict:
    return _load(BUILD09_PATH)


@pytest.fixture()
def policy() -> dict:
    return _load(POLICY_PATH)


@pytest.fixture()
def contract() -> dict:
    return _load(CONTRACT_PATH)


def _rehash_policy(value: dict) -> dict:
    value["policy_record_sha256"] = policy_record_sha256(value)
    return value


def _rehash_contract(value: dict) -> dict:
    value["finalized_contract_sha256"] = finalized_contract_sha256(value)
    return value


def _policy_failure(value: dict, resolution: dict, predecessor: dict, build09: dict) -> str:
    with pytest.raises(HumanBuildingProductionPolicyError) as caught:
        validate_policy_record(value, resolution, predecessor, build09)
    return caught.value.code


def _contract_failure(
    value: dict, policy: dict, resolution: dict, predecessor: dict, build09: dict
) -> str:
    with pytest.raises(HumanBuildingProductionPolicyError) as caught:
        validate_finalized_contract(value, policy, resolution, predecessor, build09)
    return caught.value.code


def test_exact_build09e2_predecessor_identity(policy: dict, contract: dict) -> None:
    actual = subprocess.check_output(
        [
            "git",
            "rev-parse",
            "refs/heads/build/build-09e2-j13-j17-production-applicability-resolution",
        ],
        cwd=ROOT,
        text=True,
    ).strip()
    assert actual == EXPECTED_BUILD09E2_COMMIT
    assert policy["predecessor"]["build09e2_commit"] == EXPECTED_BUILD09E2_COMMIT
    assert contract["bindings"]["build09e2_predecessor_commit"] == EXPECTED_BUILD09E2_COMMIT


def test_exact_predecessor_canonical_identities(policy: dict, contract: dict) -> None:
    predecessor = policy["predecessor"]
    assert (
        predecessor["build09_contract_sha256"]
        == "0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c"
    )
    assert (
        predecessor["build09e_evidence_closure_sha256"]
        == "bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed"
    )
    assert (
        predecessor["build09e1_evidence_resolution_sha256"]
        == "f75c44bcb834090277588b3c23cfe48f00e965c947754497f64831d4b47b9b65"
    )
    assert (
        predecessor["build09e2_applicability_resolution_sha256"]
        == "1a4a406da130eb34a7f6871e92230d0c82fe4bcf9e475651418780bedd5d1262"
    )
    assert (
        predecessor["build09e2_successor_contract_sha256"]
        == "71b7f25239eb001454af61358acb67917d9820957ea4aeb2191ff613ee54a043"
    )
    assert (
        predecessor["build08a_authorization_sha256"]
        == "4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8"
    )
    assert (
        contract["bindings"]["build09e2_applicability_resolution_sha256"]
        == predecessor["build09e2_applicability_resolution_sha256"]
    )
    assert (
        contract["bindings"]["build09e2_successor_contract_sha256"]
        == predecessor["build09e2_successor_contract_sha256"]
    )


def test_artifacts_are_exactly_reproducible(
    policy: dict, contract: dict, resolution: dict, predecessor_contract: dict, build09: dict
) -> None:
    built_policy = build_policy_record(resolution, predecessor_contract, build09)
    assert built_policy == policy
    assert (
        build_finalized_contract(built_policy, resolution, predecessor_contract, build09)
        == contract
    )
    assert (
        policy["policy_record_sha256"]
        == "dd15aead073404cd82030104d2603e0dc1461e7a90d972b853d2bcb6d482c8a1"
    )
    assert (
        contract["finalized_contract_sha256"]
        == "5c62664ad4884f83454b2ed1d227d7278e8f6e0ce9f85c1f992db5a429d56c88"
    )


def test_closed_schemas_accept_only_closed_top_level_artifacts(
    policy: dict, contract: dict
) -> None:
    for path, artifact in ((POLICY_SCHEMA_PATH, policy), (CONTRACT_SCHEMA_PATH, contract)):
        schema = _load(path)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(artifact)
        changed = deepcopy(artifact)
        changed["unknown"] = True
        with pytest.raises(ValidationError):
            Draft202012Validator(schema).validate(changed)


def test_official_evidence_findings_remain_closed(policy: dict, contract: dict) -> None:
    closure = policy["official_evidence_closure"]
    assert closure == {
        "additional_evidence_acquisition_justified": False,
        "authoritative_applicability_result": "authoritative-applicability-boundary-not-published",
        "official_evidence_search_closed": True,
        "official_portrayal_semantics_closed": True,
        "remaining_authoritative_evidence_blockers": [],
    }
    assert contract["official_evidence_findings"]["official_evidence_search_closed"] is True


def test_j13_j17_policy_is_version_package_scoped_and_not_global(policy: dict) -> None:
    binding = policy["j13_j17_binding_policy"]
    assert binding["classification"] == "local-version-package-scoped-production-binding"
    assert binding["global_permanent_layer_selected"] is False
    assert binding["global_equivalence_asserted"] is False
    assert binding["package_identity_required"] is True
    assert binding["binding_scope"] == "exact-explicitly-selected-and-verified-source-package"


def test_j13_j17_bindings_are_exact_and_provenance_bound(policy: dict) -> None:
    binding = policy["j13_j17_binding_policy"]
    assert binding["bindings"] == [
        {
            "layer_identity": "J13_BUILD",
            "package_prefix": "J13",
            "package_scope": "J13_寶山都市計畫/SHP",
            "schema_identity_required": True,
        },
        {
            "layer_identity": "J17_BUILD",
            "package_prefix": "J17",
            "package_scope": "J17_新竹科學工業園區特定區計畫(寶山部分)/SHP",
            "schema_identity_required": True,
        },
    ]
    assert binding["provenance_binding_required"] == [
        "source-package-identity",
        "package-scope",
        "exact-layer-identity",
        "schema-identity",
    ]
    assert binding["automatic_cross_prefix_substitution_allowed"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("package_layer_mismatch_behavior", "substitute"),
        ("unsupported_package_prefix_behavior", "accept"),
    ],
)
def test_package_mismatch_and_unsupported_prefix_fail_closed(
    field: str,
    value: str,
    policy: dict,
    resolution: dict,
    predecessor_contract: dict,
    build09: dict,
) -> None:
    changed = deepcopy(policy)
    changed["j13_j17_binding_policy"][field] = value
    _rehash_policy(changed)
    assert _policy_failure(changed, resolution, predecessor_contract, build09) == "policy_mismatch"
    assert policy["j13_j17_binding_policy"][field] == "fail-closed"


def test_cross_package_layer_mismatch_fails_closed(
    policy: dict, resolution: dict, predecessor_contract: dict, build09: dict
) -> None:
    changed = deepcopy(policy)
    changed["j13_j17_binding_policy"]["bindings"][0]["layer_identity"] = "J17_BUILD"
    _rehash_policy(changed)
    assert _policy_failure(changed, resolution, predecessor_contract, build09) == "policy_mismatch"


def test_hatch_angle_is_local_and_spacing_is_official(policy: dict) -> None:
    hatch = policy["hatch_policy"]
    assert hatch["official_diagonal_semantics"] is True
    assert hatch["official_spacing_mm"] == 2.0
    assert hatch["local_angle_degrees"] == 45
    assert hatch["angle_authority"] == "local-production-policy"
    assert "official" not in hatch["angle_authority"]


def test_hatch_resource_is_procedural_deterministic_and_asset_optional(policy: dict) -> None:
    hatch = policy["hatch_policy"]
    assert hatch["hatch_resource_policy"] == "procedural-canonical"
    assert (
        hatch["spacing_scale_boundary"] == "physical-at-defined-cartographic-output-profile-scale"
    )
    assert hatch["line_colour_semantics"] == (
        "official-black-unless-another-officially-supported-mapping-applies"
    )
    assert hatch["deterministic_procedural_rendering_required"] is True
    assert hatch["asset_file_required"] is False
    assert hatch["missing_building_hatch_tile_dependency_blocks_architecture"] is False
    assert hatch["asset_created_or_deployed"] is False


def test_annotation_content_is_official_and_placement_is_local(policy: dict) -> None:
    annotation = policy["annotation_policy"]
    assert annotation["content_authority"] == "official-portrayal-semantics"
    assert annotation["content_rule"] == "floor count followed by structure"
    assert annotation["field_binding_rule"] == "{BUILD_NO}{BUILD_STR}"
    assert annotation["annotation_placement_authority"] == "local-production-policy"
    assert annotation["preferred_placement"] == "inside-polygon"
    assert annotation["anchor"] == "deterministic-interior-or-representative-point"
    assert annotation["outside_polygon_fallback_authorized"] is False
    assert annotation["unsafe_label_behavior"] == "suppress"


def test_official_line_width_and_conversion_are_exact(policy: dict) -> None:
    line = policy["line_output_profile_policy"]
    assert line["official_physical_width"] == {"unit": "mm", "value": 0.2, "value_text": "0.20"}
    assert line["conversion_formula"] == "device_px = physical_mm * output_dpi / 25.4"
    assert line["output_dpi"] == 96
    assert line["device_pixel_assumption_declared"] is True
    assert line["derived_device_width_px"] == 0.2 * 96 / 25.4
    assert line["derived_device_width_px"] == pytest.approx(0.7559055)
    assert line["official_css_px"] is None
    assert line["official_one_css_px_rule"] is False


def test_colour_device_representation_preserves_official_rgb(policy: dict) -> None:
    colour = policy["colour_policy"]
    assert colour["official_semantic_name"] == "black"
    assert colour["official_original_representation"] == "RGB (0,0,0)"
    assert colour["official_rgb_components"] == [0, 0, 0]
    assert colour["canonical_device_representation"] == "rgb(0, 0, 0)"
    assert colour["optional_hex_serialization"] == "#000000"
    assert colour["hex_authority"] == "derived-device-serialization"
    assert colour["official_hex_definition"] is None
    assert colour["rejected_device_representation"] == "#111111"


def test_opacity_is_local_output_profile_policy(policy: dict) -> None:
    opacity = policy["opacity_policy"]
    assert opacity["value"] == 1.0
    assert opacity["authority"] == "local-output-profile-policy"
    assert opacity["applies_to"] == ["building-line", "building-hatch"]


def test_polygonz_p2_architecture_is_preserved(policy: dict, build09: dict) -> None:
    polygonz = policy["polygonz_derived_xy_policy"]
    predecessor = build09["polygonz_derived_xy_contract"]
    for key in predecessor:
        assert polygonz[key] == predecessor[key]
    assert polygonz["source_representation"]["authoritative"] is True
    assert polygonz["source_representation"]["immutable"] is True
    assert polygonz["source_representation"]["z_values_preserved_and_recoverable"] is True
    assert polygonz["derived_xy_representation"]["non_writing"] is True
    assert polygonz["legacy_drop_z_path"]["classification"] == "incompatible"
    assert polygonz["legacy_drop_z_path"]["reuse_as_is_allowed"] is False
    assert polygonz["implementation_in_build09f"] is False


def test_activation_and_mutation_remain_forbidden(policy: dict, contract: dict) -> None:
    authorization = policy["production_implementation_authorization"]
    assert authorization["controlled_production_implementation_design_allowed"] is True
    assert authorization["controlled_production_implementation_allowed"] is True
    for key in (
        "production_activation_allowed",
        "official_portrayal_activation_allowed",
        "source_mutation_allowed",
        "source_z_drop_allowed",
        "unbounded_runtime_wiring_allowed",
    ):
        assert authorization[key] is False
        assert contract[key] is False
    assert policy["scope"]["production_behavior_implemented"] is False
    assert policy["scope"]["source_data_or_geometry_modified"] is False


def test_all_five_gates_are_p2_and_build10_ready(policy: dict, contract: dict) -> None:
    expected_ids = ["hatch", "annotation", "j13-j17", "line-colour", "polygonz-derived-xy"]
    assert [gate["gate_id"] for gate in policy["five_gate_readiness"]] == expected_ids
    assert {gate["state"] for gate in policy["five_gate_readiness"]} == {"P2-production-candidate"}
    assert contract["final_gates"] == policy["five_gate_readiness"]
    assert contract["status"] == "production-candidate"
    assert policy["build10_readiness"] == contract["build10_readiness"] == "READY-FOR-BUILD-10"
    assert policy["verdict"] == "PASS — HUMAN BUILDING PRODUCTION POLICY RESOLVED; BUILD-10 READY"


def test_tampered_policy_identity_fails(
    policy: dict, resolution: dict, predecessor_contract: dict, build09: dict
) -> None:
    changed = deepcopy(policy)
    changed["opacity_policy"]["value"] = 0.5
    assert (
        _policy_failure(changed, resolution, predecessor_contract, build09)
        == "policy_hash_mismatch"
    )


def test_tampered_finalized_contract_identity_fails(
    contract: dict, policy: dict, resolution: dict, predecessor_contract: dict, build09: dict
) -> None:
    changed = deepcopy(contract)
    changed["production_activation_allowed"] = True
    assert (
        _contract_failure(changed, policy, resolution, predecessor_contract, build09)
        == "contract_hash_mismatch"
    )


@pytest.mark.parametrize(
    ("path", "unknown"),
    [
        (("hatch_policy", "angle_authority"), "official"),
        (("j13_j17_binding_policy", "classification"), "global-equivalent"),
        (("opacity_policy", "authority"), "official"),
        (("build10_readiness",), "UNKNOWN"),
    ],
)
def test_unknown_policy_states_fail(
    path: tuple[str, ...],
    unknown: str,
    policy: dict,
    resolution: dict,
    predecessor_contract: dict,
    build09: dict,
) -> None:
    changed = deepcopy(policy)
    cursor = changed
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = unknown
    _rehash_policy(changed)
    assert _policy_failure(changed, resolution, predecessor_contract, build09) == "policy_mismatch"


def test_unknown_gate_state_fails_even_when_rehashed(
    contract: dict, policy: dict, resolution: dict, predecessor_contract: dict, build09: dict
) -> None:
    changed = deepcopy(contract)
    changed["final_gates"][0]["state"] = "production-active"
    _rehash_contract(changed)
    assert (
        _contract_failure(changed, policy, resolution, predecessor_contract, build09)
        == "contract_mismatch"
    )


def test_predecessor_build09e2_artifacts_remain_byte_identical(policy: dict) -> None:
    assert policy["predecessor"]["frozen_build09e2_artifact_sha256"] == BUILD09E2_ARTIFACT_SHA256
    assert {
        path: _sha256(ROOT / path) for path in BUILD09E2_ARTIFACT_SHA256
    } == BUILD09E2_ARTIFACT_SHA256


def test_build09f_scope_is_exact_and_contains_no_runtime_source_or_asset_change() -> None:
    output = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, text=True
    )
    changed = {line[3:] for line in output.splitlines() if line}
    assert changed == ALLOWED_BUILD09F_FILES
    assert all(not path.startswith(("src/", "assets/", "data/datasets/")) for path in changed)
    assert "src/nma/real_layer.py" not in changed

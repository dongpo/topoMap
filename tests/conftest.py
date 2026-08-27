from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
PRIVATE_BUILD_ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"


# These assertions describe the exact commit/scope/bytes of a frozen milestone. They remain
# runnable, but a successor branch is not that milestone and must not be required to impersonate
# it. Keep this list node-specific so functional tests in the same modules remain in canonical CI.
HISTORICAL_FREEZE_NODE_IDS = {
    "tests/test_agent_evaluation_governance_agent04.py::test_production_runtime_and_dependency_boundary_are_byte_identical",
    "tests/test_agent_provenance_auditability_agent05.py::test_production_runtime_and_dependency_boundary_are_byte_identical",
    "tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries",
    "tests/test_agentic_freeze.py::test_agentic_freeze_rejects_unrecorded_current_drift",
    "tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate",
    "tests/test_authorization_handoff_boundary_agent06.py::test_production_runtime_dependencies_and_frozen_core_are_byte_identical",
    "tests/test_build_human_official_production_scope_authorization_build08a.py::test_previous_build_and_forbidden_artifacts_remain_unchanged",
    "tests/test_building_production_contract_build09.py::test_exact_build08a_predecessor_identity",
    "tests/test_building_production_contract_build09.py::test_previous_build_frozen_artifacts_and_runtime_remain_unchanged",
    "tests/test_building_production_activation_build12.py::test_exact_build11a_predecessor_is_the_branch_parent",
    "tests/test_building_production_freeze_final.py::test_build_final_diff_is_evidence_only",
    "tests/test_core04_residual_identity_audit.py::test_change_scope_is_exactly_three_existing_production_files",
    "tests/test_core04_residual_identity_audit.py::test_residual_provider_and_fallback_counts_close_exactly",
    "tests/test_core04_residual_identity_audit.py::test_remaining_json_hash_rules_are_domain_specific_and_fully_classified",
    "tests/test_core04_residual_identity_audit.py::test_every_unauthorized_predecessor_file_and_frozen_ref_is_unchanged",
    "tests/test_cross_domain_contract_conformance_gen02.py::test_gen01_contract_and_all_frozen_implementations_are_unchanged",
    "tests/test_cross_domain_contract_conformance_gen02.py::test_exact_predecessor_closure_and_gen00_identities",
    "tests/test_cross_domain_contract_conformance_gen02.py::test_verification_artifacts_cannot_authorize_or_perform_mutation",
    "tests/test_demo_final_controlled_freeze.py::test_df01_exact_retry_predecessor_and_change_scope",
    "tests/test_demo_final_controlled_freeze.py::test_df14_manifest_self_hash_schema_artifacts_and_no_functional_change",
    "tests/test_evidence_semantic_boundary_agent03.py::test_production_runtime_dependencies_and_public_graph_are_byte_identical",
    "tests/test_feature_production_generalization_gen00.py::test_gen00_changes_only_four_audit_files_from_frozen_build",
    "tests/test_feature_production_generalization_gen00.py::test_build_final_identity_and_manifest_are_exact",
    "tests/test_generalization_architecture_freeze_final.py::test_exact_generalization_chain_and_direct_predecessor_linkage",
    "tests/test_generalization_architecture_freeze_final.py::test_contract_immutability_and_exact_evidence_only_scope",
    "tests/test_generic_contract_interface_closure_gen01.py::test_frozen_implementations_and_gen00_are_unchanged",
    "tests/test_generic_contract_interface_closure_gen01.py::test_allowed_change_scope_only",
    "tests/test_human_building_production_activation_authorization_build11a.py::test_build11a_changed_file_scope_is_exact_and_production_sources_are_untouched",
    "tests/test_human_building_production_policy_build09f.py::test_build09f_scope_is_exact_and_contains_no_runtime_source_or_asset_change",
    "tests/test_human_building_production_policy_build09f.py::test_exact_build09e2_predecessor_identity",
    "tests/test_intent_planning_contract_agent02.py::test_canonical_public_runtime_and_dependency_boundary_are_byte_identical",
    "tests/test_j13_j17_production_applicability_build09e2.py::test_exact_build09e1_predecessor_sha",
    "tests/test_nma_final_release_integrity.py::test_nf01_exact_demo_final_predecessor_and_release_scope",
    "tests/test_nma_final_release_integrity.py::test_nf13_release_safety_invariants_are_fail_closed",
    "tests/test_nma_final_release_integrity.py::test_nf14_manifest_self_hash_normative_artifacts_and_release_contract",
    "tests/test_official_evidence_closure_build09e.py::test_exact_build09_predecessor_identity",
    "tests/test_official_evidence_closure_build09e.py::test_previous_artifacts_runtime_and_source_scope_remain_unchanged",
    "tests/test_targeted_official_evidence_resolution_build09e1.py::test_exact_build09e_predecessor_identity",
}

PRIVATE_DATA_FILE_PREFIXES = (
    "tests/test_building_production_activation_build12.py::",
    "tests/test_building_production_verification_build11.py::",
    "tests/test_human_building_production_activation_authorization_build11a.py::",
    "tests/test_road_verification_road05.py::",
)
PRIVATE_DATA_NODE_IDS = {
    "tests/test_ama_demo02_rq3.py::test_rq3_valid_scenario_executes_existing_engine_then_independent_verifier",
    "tests/test_build_demo_execution_build05.py::test_changed_archive_is_rejected_and_leaves_claim",
    "tests/test_build_demo_execution_build05.py::test_controlled_execution_reproduces_golden_package_and_blocks_replay",
    "tests/test_cross_domain_contract_conformance_gen02.py::test_private_archive_remains_sha_exact_ignored_untracked_and_unstaged",
    "tests/test_demo_auth01_school_authorization.py::test_wrong_fixture_fails_before_execution",
    "tests/test_generic_contract_interface_closure_gen01.py::test_frozen_identities_and_private_archive_boundary",
    "tests/test_j13_j17_production_applicability_build09e2.py::test_source_archive_remains_unchanged",
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    historical = pytest.mark.historical_freeze
    private_data = pytest.mark.private_data
    missing_private_data = pytest.mark.skip(
        reason="The exact ignored private BUILD/ROAD archive is not present."
    )
    for item in items:
        if item.nodeid in HISTORICAL_FREEZE_NODE_IDS:
            item.add_marker(historical)
        if item.nodeid in PRIVATE_DATA_NODE_IDS or item.nodeid.startswith(
            PRIVATE_DATA_FILE_PREFIXES
        ):
            item.add_marker(private_data)
            if not PRIVATE_BUILD_ARCHIVE.is_file():
                item.add_marker(missing_private_data)

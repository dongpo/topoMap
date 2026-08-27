# AMA-REL-00 pre-change failure classification

Audit target: `codex/ama-canonical-reconciliation` at
`16393e7ec7361a8b0602d30d456274a0e567a6e0`.

The supplied starting report said `1446 passed, 29 failed, 1 skipped`. A clean reproduction with
Python 3.11.9, the exact ignored archive, GDAL/OGR, and the ignored ROAD state produced **24 failed**
node IDs. The repository's pytest `lastfailed` cache independently contained the same 24 IDs. The
table classifies every reproducible failure; the count discrepancy is preserved below rather than
filled with invented test names.

| Test | Failure class | Historical/current | Root cause | Release blocker? | Recommended action |
| --- | --- | --- | --- | --- | --- |
| `test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible` | `CURRENT_REPRODUCIBILITY_DEFECT` | Current | Generator omitted the reviewed `flagpole_horizontal_alignment` parameter added to the tracked catalog by `021b26d`; all other catalog content matched. | Yes | Add the missing generator field; require exact reproduction. |
| `test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries` | `HISTORICAL_BYTE_IDENTITY` | Historical | The v0.3 manifest fingerprints the pre-AMA README and candidate artifacts. | No, in historical route | Mark the exact snapshot assertion; run at its recorded ref. |
| `test_agentic_freeze.py::test_agentic_freeze_rejects_unrecorded_current_drift` | `HISTORICAL_BYTE_IDENTITY` | Historical | The intended SHA tamper check first encounters successor README size drift. | No, in historical route | Mark with the same exact-snapshot context. |
| `test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate` | `HISTORICAL_BYTE_IDENTITY` | Historical | The historical Pages candidate manifest fingerprints the older PMTiles catalog. | No, in historical route | Run at the historical candidate ref; do not update its golden bytes. |
| `test_build_human_official_production_scope_authorization_build08a.py::test_previous_build_and_forbidden_artifacts_remain_unchanged` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Compares successor HEAD's full diff with BUILD-08A's five-file stage scope. | No, in historical route | Mark node-specific exact-scope assertion. |
| `test_building_production_activation_build12.py::test_exact_build11a_predecessor_is_the_branch_parent` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires HEAD or HEAD parent to be BUILD-11A. | No, in historical route | Run at BUILD-12 context. |
| `test_building_production_freeze_final.py::test_build_final_diff_is_evidence_only` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Requires BUILD-FINAL's evidence-only diff. | No, in historical route | Run at `nma-build-v1.0-final`. |
| `test_core04_residual_identity_audit.py::test_residual_provider_and_fallback_counts_close_exactly` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Successor Pages scripts did not exist at the CORE-03 predecessor. | No, in historical route | Keep CORE-04 audit at its exact ref. |
| `test_core04_residual_identity_audit.py::test_remaining_json_hash_rules_are_domain_specific_and_fully_classified` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Successor Pages scripts add JSON-main functions outside the frozen CORE-04 inventory. | No, in historical route | Keep frozen inventory unchanged. |
| `test_core04_residual_identity_audit.py::test_every_unauthorized_predecessor_file_and_frozen_ref_is_unchanged` | `HISTORICAL_BYTE_IDENTITY` | Historical | Current Pages workflow bytes differ from CORE-03. | No, in historical route | Verify at CORE-04/final ref. |
| `test_cross_domain_contract_conformance_gen02.py::test_gen01_contract_and_all_frozen_implementations_are_unchanged` | `HISTORICAL_BYTE_IDENTITY` | Historical | Successor unified runtime legitimately postdates GEN-01. | No, in historical route | Keep exact GEN-02 assertion. |
| `test_cross_domain_contract_conformance_gen02.py::test_verification_artifacts_cannot_authorize_or_perform_mutation` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Compares all successor changes with GEN-02's closed stage scope. | No, in historical route | Run at GEN-02. |
| `test_demo_final_controlled_freeze.py::test_df01_exact_retry_predecessor_and_change_scope` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires DEMO retry commit as HEAD or direct parent. | No, in historical route | Run at `nma-demo-v1.0-final`. |
| `test_demo_final_controlled_freeze.py::test_df14_manifest_self_hash_schema_artifacts_and_no_functional_change` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Requires DEMO-FINAL's closed file scope. | No, in historical route | Preserve and route. |
| `test_feature_production_generalization_gen00.py::test_gen00_changes_only_four_audit_files_from_frozen_build` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Requires GEN-00's four-file audit diff. | No, in historical route | Run at GEN-00. |
| `test_generalization_architecture_freeze_final.py::test_exact_generalization_chain_and_direct_predecessor_linkage` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires GEN-02 as HEAD or direct parent. | No, in historical route | Run at generalization final. |
| `test_generalization_architecture_freeze_final.py::test_contract_immutability_and_exact_evidence_only_scope` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Requires GEN-FINAL's evidence-only diff. | No, in historical route | Preserve and route. |
| `test_generic_contract_interface_closure_gen01.py::test_frozen_implementations_and_gen00_are_unchanged` | `HISTORICAL_BYTE_IDENTITY` | Historical | Successor unified runtime postdates GEN-00/GEN-01. | No, in historical route | Run at GEN-01. |
| `test_generic_contract_interface_closure_gen01.py::test_allowed_change_scope_only` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Requires GEN-01's closed change scope. | No, in historical route | Preserve and route. |
| `test_human_building_production_activation_authorization_build11a.py::test_build11a_changed_file_scope_is_exact_and_production_sources_are_untouched` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Current HEAD is not the BUILD-11A stage commit. | No, in historical route | Run at BUILD-11A. |
| `test_human_building_production_policy_build09f.py::test_build09f_scope_is_exact_and_contains_no_runtime_source_or_asset_change` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Current HEAD is not the BUILD-09F stage commit. | No, in historical route | Run at BUILD-09F. |
| `test_nma_final_release_integrity.py::test_nf01_exact_demo_final_predecessor_and_release_scope` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires DEMO-FINAL as HEAD or direct parent. | No, in historical route | Run at `nma-v1.0-final`. |
| `test_nma_final_release_integrity.py::test_nf13_release_safety_invariants_are_fail_closed` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Requires NMA-FINAL's exact release scope. | No, in historical route | Preserve and route. |
| `test_nma_final_release_integrity.py::test_nf14_manifest_self_hash_normative_artifacts_and_release_contract` | `HISTORICAL_SCOPE_IDENTITY` | Historical | Requires NMA-FINAL's exact manifest/file scope. | No, in historical route | Preserve and route. |

## Reported-count reconciliation and isolation evidence

One additional failure described in the supplied report—ROAD verification against reused persisted
runtime state—is classified `TEST_ISOLATION_DEFECT`, current test infrastructure, and release
blocking. Its node ID was not present in the clean reproduction/cache. ROAD-05 previously copied
ignored `artifacts/runtime/road`; it now executes ROAD-04 into a fresh session temp directory and
passes repeated clean runs.

The four remaining reported failure slots had no supplied node IDs and did not recur. Removing the
private archive produced many `ENVIRONMENT_DEPENDENT` errors (not four); restoring it returned the
stable 24-node result. They are therefore recorded as an unreproduced count discrepancy, not
misclassified as historical. The canonical suite explicitly skips exact private-data scopes when
the non-redistributable archive is absent.

After the current lint fix and closure files were added, eight further assertions activated: five
historical Agent/evidence tests pin the old `graphrag.py` bytes, and three BUILD/Core tests pin a
historical stage's dirty-worktree/change scope. They were not pre-change failures, but their
semantics are historical, so the final central classifier contains 31 exact node IDs.

The first detached GitHub Actions run exposed seven more `HISTORICAL_HEAD_IDENTITY` nodes that had
passed in the long-lived audit clone only because its local namespace retained the old predecessor
branches. Each calls `git rev-parse` on a historical `refs/heads/build/...`, `refs/heads/gen/...`, or
`freeze/build-final-...` ref and compares it with a recorded old commit. A detached canonical
checkout correctly has no obligation to manufacture those local branch refs. The assertions remain
unchanged and runnable in their historical repository context; the central classifier therefore
contains 38 exact node IDs:

| Test | Failure class | Historical/current | Root cause | Release blocker? | Recommended action |
| --- | --- | --- | --- | --- | --- |
| `test_building_production_contract_build09.py::test_exact_build08a_predecessor_identity` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires the BUILD-08A predecessor branch as a local `refs/heads` ref. | No, in historical route | Run in the BUILD lineage context. |
| `test_cross_domain_contract_conformance_gen02.py::test_exact_predecessor_closure_and_gen00_identities` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires local GEN-00/GEN-01 branch refs as well as their old commits. | No, in historical route | Run in the GEN-02 lineage context. |
| `test_feature_production_generalization_gen00.py::test_build_final_identity_and_manifest_are_exact` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires the historical BUILD-FINAL freeze branch in the local namespace. | No, in historical route | Run in the GEN-00/frozen BUILD context. |
| `test_human_building_production_policy_build09f.py::test_exact_build09e2_predecessor_identity` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires the BUILD-09E2 predecessor branch as a local ref. | No, in historical route | Run in the BUILD-09F lineage context. |
| `test_j13_j17_production_applicability_build09e2.py::test_exact_build09e1_predecessor_sha` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires the BUILD-09E1 predecessor branch as a local ref. | No, in historical route | Run in the BUILD-09E2 lineage context. |
| `test_official_evidence_closure_build09e.py::test_exact_build09_predecessor_identity` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires the BUILD-09 predecessor branch as a local ref. | No, in historical route | Run in the BUILD-09E lineage context. |
| `test_targeted_official_evidence_resolution_build09e1.py::test_exact_build09e_predecessor_identity` | `HISTORICAL_HEAD_IDENTITY` | Historical | Requires the BUILD-09E predecessor branch as a local ref. | No, in historical route | Run in the BUILD-09E1 lineage context. |

Wheel validation also exposed a separate `TEST_ISOLATION_DEFECT`: a BUILD-FINAL source scan walked
the ignored generated `build/lib` copy and reported a duplicate identity provider. The scan now
excludes the standard `build` output directory while continuing to inspect all repository sources.

## Lint classification

| Location | Failure class | Resolution |
| --- | --- | --- |
| `src/nma/graphrag.py` unused `documents` | `CURRENT_LINT` | Removed dead local and formatted the maintained file. |
| Three unused versioned class imports in `scripts/run_nma_agent_server.py` | `LEGACY_LINT` | Exact file and `F401` debt are hash-locked in the one-file lint baseline. |
| Legacy formatting set | `LEGACY_LINT` | Exact paths and aggregate bytes are locked; new/modified non-baseline Python must format cleanly. |

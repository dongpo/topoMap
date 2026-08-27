"""BUILD-09 evidence-bound Building production contract candidate.

This module designs and validates a production boundary.  It does not read the
private source archive, create a runtime, render a map, write derived geometry,
or authorize production or official portrayal activation.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from build_contracts.official_production_scope_authorization import (
    EVIDENCE_AUTHORITY_CLASSES,
    validate_official_production_scope_authorization,
)
from nma.core import canonical_sha256


CONTRACT_SCHEMA = "nma.building-production-contract-candidate/1.0"
CONTRACT_VERSION = "build-09/1.0"
EXPECTED_BUILD08A_COMMIT = "6e62481530228c76c250ff0e0119752c83f655a4"
EXPECTED_BUILD08A_AUTHORIZATION_SHA256 = (
    "4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8"
)
EXPECTED_BUILD08_REVIEW_SHA256 = "b48337a6bb8cf1e6cffc54e0bbfe14383f62c1dcfdca54bf706c0ab045b42484"

SUPPORT_CLASSES = [
    "officially-supported",
    "implementation-supported",
    "local-policy-candidate",
    "demo-only",
    "contradicted",
    "indeterminate",
]
READINESS_STATES = ["P0-demo-only", "P1-evidence-supported", "P2-production-candidate"]
GATE_IDS = [
    "hatch-angle-transcription",
    "building-annotation-placement",
    "real-build-schema-binding",
    "line-and-color-profile",
    "j13-polygonz-runtime-policy",
]


class BuildingProductionContractError(ValueError):
    """BUILD-09 rejected unsupported semantics, identity, or authority."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildingProductionContractError(message, code=code)


def _evidence_references() -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": "build08a-authorization-boundary",
            "authority_class": "reviewed-project-evidence",
            "path": "data/specifications/nma-build-08a-golden-human-official-production-scope-authorization-v1.0.json",
            "file_sha256": "a100ef01036207453992981d48c713a619b006c44f10e453cf3e69fcec6799ba",
            "source_identity": EXPECTED_BUILD08A_AUTHORIZATION_SHA256,
            "claim_scope": "BUILD-09 evidence/design authority and non-activation boundaries",
        },
        {
            "evidence_id": "doc01-explicit-building-portrayal",
            "authority_class": "authoritative-official",
            "path": "data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json",
            "file_sha256": "9ba4f3c5e9dd2acec78ab56bf9fce270efac9b8343937459a6f4b3f16830a512",
            "source_identity": "sha256:1f9c4457d7ced86f2b7681e21be9ad3b7b7ae364981ab995ef27b468e0fa2620#page=8",
            "claim_scope": "explicit row: surveyed boundary, hatch, 2 mm spacing, floor/structure annotation, line 2 and colour 7",
        },
        {
            "evidence_id": "doc01-reviewed-visual-transcription",
            "authority_class": "reviewed-project-evidence",
            "path": "data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json",
            "file_sha256": "9ba4f3c5e9dd2acec78ab56bf9fce270efac9b8343937459a6f4b3f16830a512",
            "source_identity": "portrayal-recipe:doc01:9310100:review-v1",
            "claim_scope": "manual visual orientation, observed black, candidate resource, and tracked J17 observation",
        },
        {
            "evidence_id": "doc09-build-product-schema",
            "authority_class": "authoritative-schema",
            "path": "data/specifications/taiwan-temap-build-v0.4.json",
            "file_sha256": "8b94fbbf06d411ab5afb6d2644abc6bff552bb2a828c13aa0aed21a36f0826f0",
            "source_identity": "sha256:b3c26f6e2766e9e6fac2a85f935b88e45741708ef6def79213b4c18a2cdb3683#revision=114.12.04",
            "claim_scope": "logical BUILD layer, Polygon role, and documented ID/SOURCE/MDATE fields without observed-field equivalence",
        },
        {
            "evidence_id": "build00a-j13-fixture-observation",
            "authority_class": "reviewed-project-evidence",
            "path": "data/specifications/nma-build-fixture-manifest-v1.0.json",
            "file_sha256": "a5b089f7b8fac0ca4b6959594c27bdfe4a9be478c2e965f513d63bacbf92463d",
            "source_identity": "build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a",
            "claim_scope": "exact-archive J13 fields, PolygonZ geometry, counts, and DEMO-fixture quality selection only",
        },
        {
            "evidence_id": "build01-j13-redacted-observation",
            "authority_class": "reviewed-project-evidence",
            "path": "data/specifications/nma-build-source-observation-v1.0.json",
            "file_sha256": "35dd7f9fe8750240b44e12466beef68c52234cd3bbd1dd5affb94f9940eda91a",
            "source_identity": "build-observation:sha256:8fdbb3bdea8ffe715e7d76eed7c5034bd62226ba649be2206cf7a9e07b853bac",
            "claim_scope": "redacted J13 PolygonZ identity and immutable geometry commitments",
        },
        {
            "evidence_id": "build07-demo-evaluation",
            "authority_class": "human-demo-evaluation",
            "path": "data/specifications/nma-build-07-accepted-user-evaluation-v1.0.json",
            "file_sha256": "7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d",
            "source_identity": "ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c",
            "claim_scope": "DEMO usability acceptance only; no official or production semantics",
        },
        {
            "evidence_id": "existing-real-layer-path",
            "authority_class": "implementation-evidence",
            "path": "src/nma/real_layer.py",
            "file_sha256": "d9eb720b5f84c35b63df8c9cd828a7530497d4b71f502117bdf7470148d890e9",
            "source_identity": "nma.real_layer/0.4",
            "claim_scope": "J17 runtime profile, null label binding, and destructive-dimensionality conflict",
        },
    ]


def _field_semantics() -> list[dict[str, Any]]:
    return [
        {
            "field": "ID",
            "documented_source_meaning": "polygon serial number (多邊形序號)",
            "authority_class": "authoritative-schema",
            "nma_semantic_concept": "authoritative-source-feature-identifier",
            "role": "feature-identity",
            "allowed_use": "feature identity only for a source proven to conform to Document 09 revision 114.12.04",
            "production_implication": "not present in tracked J13/J17 observations; no BUILD_ID equivalence is authorized",
        },
        {
            "field": "SOURCE",
            "documented_source_meaning": "data construction code (資料建置代碼)",
            "authority_class": "authoritative-schema",
            "nma_semantic_concept": "source-provenance-code",
            "role": "metadata",
            "allowed_use": "source metadata only for a Document 09 conformant dataset",
            "production_implication": "absent in tracked J13/J17 observations and must not be invented",
        },
        {
            "field": "MDATE",
            "documented_source_meaning": "survey/production year-month (測製年月)",
            "authority_class": "authoritative-schema",
            "nma_semantic_concept": "source-production-date",
            "role": "metadata",
            "allowed_use": "metadata; never feature identity, annotation, classification, or portrayal",
            "production_implication": "same-name Text(8) field is observed, but value/domain validation remains required",
        },
        {
            "field": "BUILD_ID",
            "documented_source_meaning": "observed nonblank unique String(16) identifier in the exact archived BUILD members",
            "authority_class": "reviewed-project-evidence",
            "nma_semantic_concept": "dataset-scoped-source-record-identifier",
            "role": "feature-identity",
            "allowed_use": "exact-archive provenance and deterministic record addressing only",
            "production_implication": "cannot satisfy official ID semantics without authoritative mapping evidence",
        },
        {
            "field": "TERRAINID",
            "documented_source_meaning": "observed dataset classification selector containing 9310100 and other codes",
            "authority_class": "reviewed-project-evidence",
            "nma_semantic_concept": "dataset-scoped-building-classification",
            "role": "building-classification",
            "allowed_use": "exact-archive candidate filtering for NMA concept 9310100 only",
            "production_implication": "not a global official feature-code field binding",
        },
        {
            "field": "BUILD_NO",
            "documented_source_meaning": "reviewed exact-archive binding for building floor count",
            "authority_class": "reviewed-project-evidence",
            "nma_semantic_concept": "building-floor-count",
            "role": "label-content",
            "allowed_use": "first component of exact-archive floor/structure annotation candidate",
            "production_implication": "content binding is evidence-supported but not an official field definition",
        },
        {
            "field": "BUILD_STR",
            "documented_source_meaning": "reviewed exact-archive binding for building structure code",
            "authority_class": "reviewed-project-evidence",
            "nma_semantic_concept": "building-structure-code",
            "role": "label-content",
            "allowed_use": "second component of exact-archive floor/structure annotation candidate",
            "production_implication": "code domain and official field binding still require evidence",
        },
        {
            "field": "BUILD_H",
            "documented_source_meaning": "no repository-accessible authoritative meaning established",
            "authority_class": "unknown",
            "nma_semantic_concept": "unbound-source-metadata",
            "role": "metadata",
            "allowed_use": "opaque passthrough only; no semantic, annotation, classification, or portrayal use",
            "production_implication": "semantic use fails closed pending evidence",
        },
        {
            "field": "GROUP_ID",
            "documented_source_meaning": "no repository-accessible authoritative meaning established",
            "authority_class": "unknown",
            "nma_semantic_concept": "unbound-source-metadata",
            "role": "metadata",
            "allowed_use": "opaque passthrough only; no identity, grouping, annotation, or portrayal use",
            "production_implication": "semantic use fails closed pending evidence",
        },
    ]


def _portrayal_properties() -> list[dict[str, Any]]:
    return [
        {
            "property": "representation",
            "value": "feature-following-hatched-polygon",
            "authority_class": "authoritative-official",
            "support": "officially-supported",
            "production_note": "official row requires surveyed boundary plus hatch",
        },
        {
            "property": "hatch-orientation-semantic",
            "value": "diagonal rising from lower-left to upper-right",
            "authority_class": "reviewed-project-evidence",
            "support": "implementation-supported",
            "production_note": "manual visual transcription; numeric angle is not implied",
        },
        {
            "property": "hatch-angle-degrees",
            "value": 45.0,
            "authority_class": "local-policy-candidate",
            "support": "local-policy-candidate",
            "production_note": "retained only as a candidate derived from the accepted DEMO; not official",
        },
        {
            "property": "hatch-spacing-mm",
            "value": 2.0,
            "authority_class": "authoritative-official",
            "support": "officially-supported",
            "production_note": "physical output spacing; renderer conversion must be scale-aware",
        },
        {
            "property": "fill-background",
            "value": "transparent",
            "authority_class": "local-policy-candidate",
            "support": "local-policy-candidate",
            "production_note": "official evidence does not define a solid background fill",
        },
        {
            "property": "outline",
            "value": {"enabled": True, "line_code": "2", "color_code": "7"},
            "authority_class": "authoritative-official",
            "support": "officially-supported",
            "production_note": "codes are official references; numeric rendering is separate",
        },
        {
            "property": "line-width-css-px",
            "value": 1.0,
            "authority_class": "local-policy-candidate",
            "support": "local-policy-candidate",
            "production_note": "web-output candidate inherited from DEMO, not line-code 2 definition",
        },
        {
            "property": "color-hex",
            "value": "#111111",
            "authority_class": "local-policy-candidate",
            "support": "local-policy-candidate",
            "production_note": "web-output candidate; official color code 7 has no device-independent value here",
        },
        {
            "property": "opacity",
            "value": 1.0,
            "authority_class": "local-policy-candidate",
            "support": "local-policy-candidate",
            "production_note": "web-output candidate only",
        },
        {
            "property": "z-order",
            "value": None,
            "authority_class": "unknown",
            "support": "indeterminate",
            "production_note": "no repository-accessible official ordering rule",
        },
        {
            "property": "annotation-style",
            "value": None,
            "authority_class": "unknown",
            "support": "indeterminate",
            "production_note": "content is evidenced; font, size, halo, and priority are not",
        },
    ]


def _contract_basis() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "schema_version": CONTRACT_SCHEMA,
        "status": "partial-production-candidate",
        "created_on": "2026-08-21",
        "predecessor": {
            "build08a_branch": "build/build-08a-human-official-production-scope-resolution",
            "build08a_completion_commit": EXPECTED_BUILD08A_COMMIT,
            "build08a_authorization_sha256": EXPECTED_BUILD08A_AUTHORIZATION_SHA256,
            "build08a_authorization_file_sha256": "a100ef01036207453992981d48c713a619b006c44f10e453cf3e69fcec6799ba",
            "build08_review_sha256": EXPECTED_BUILD08_REVIEW_SHA256,
            "build08_review_file_sha256": "be9ee241d358ba4c426ed7756345b899dffaa2e010f5f66abbe4b24ad7355b1b",
            "build08_completion_commit": "666a12adf4a1b369168480e13b2b65107429d935",
            "build07_completion_commit": "153037a165683e0a2b39d36620c688955ca935fd",
        },
        "scope": {
            "target": "Building evidence semantics and production-contract design",
            "private_source_accessed": False,
            "production_execution_performed": False,
            "runtime_created_or_modified": False,
            "source_data_or_geometry_modified": False,
            "production_active": False,
        },
        "evidence_policy": {
            "authority_classes": list(EVIDENCE_AUTHORITY_CLASSES),
            "support_classes": list(SUPPORT_CLASSES),
            "demo_or_human_demo_can_establish_official_semantics": False,
            "implementation_alone_can_establish_official_portrayal": False,
            "unsupported_inference_allowed": False,
        },
        "evidence_references": _evidence_references(),
        "authoritative_source_layer_contract": {
            "resolution": "indeterminate",
            "selected_layer_id": None,
            "logical_product_layer": "BUILD",
            "nma_building_concept": {
                "feature_code": "9310100",
                "name": "永久性建物(建築區)",
                "geometry_role": "Polygon",
            },
            "dataset_version_scope": {
                "official_product_schema_revision": "114.12.04",
                "official_portrayal_revision": "NLSC112V5.4",
                "observed_archive_name": "112年多維度SHP成果_0502.zip",
                "observed_archive_sha256": "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
                "cross_version_equivalence_asserted": False,
            },
            "candidate_observations": [
                {
                    "layer_id": "J13_BUILD",
                    "geometry_type": "PolygonZ",
                    "fields": [
                        "BUILD_ID",
                        "TERRAINID",
                        "BUILD_STR",
                        "BUILD_NO",
                        "BUILD_H",
                        "GROUP_ID",
                        "MDATE",
                    ],
                    "record_count": 2968,
                    "authority_class": "reviewed-project-evidence",
                    "production_authority": False,
                    "bounded_status": "quality-selected-demo-fixture-only",
                },
                {
                    "layer_id": "J17_BUILD",
                    "geometry_type": "PolygonZ",
                    "fields": [
                        "BUILD_ID",
                        "TERRAINID",
                        "BUILD_STR",
                        "BUILD_NO",
                        "BUILD_H",
                        "GROUP_ID",
                        "MDATE",
                    ],
                    "record_count": 2839,
                    "authority_class": "reviewed-project-evidence",
                    "production_authority": False,
                    "bounded_status": "legacy-runtime-observation-only",
                },
            ],
            "global_equivalence_assumed": False,
            "resolution_reason": "official evidence defines logical BUILD but does not bind J13_BUILD or J17_BUILD as the intended production identity or define their relationship",
            "production_implication": "a later contract must bind an exact source family/version and layer naming rule before selecting either candidate",
        },
        "geometry_contract": {
            "authoritative_source_geometry": "PolygonZ",
            "nma_geometry_role": "Polygon",
            "source_z_authoritative": True,
            "source_geometry_immutable": True,
            "geometry_repair_allowed": False,
        },
        "field_semantic_bindings": _field_semantics(),
        "annotation_contract": {
            "status": "local-policy-candidate",
            "content_semantics": {
                "value": "floor count followed by structure code",
                "authority_class": "authoritative-official",
                "support": "officially-supported",
            },
            "source_field_binding": {
                "fields": ["BUILD_NO", "BUILD_STR"],
                "format": "{BUILD_NO}{BUILD_STR}",
                "separator": "",
                "authority_class": "reviewed-project-evidence",
                "support": "implementation-supported",
                "scope": "exact observed archive only",
                "official_field_binding": False,
            },
            "placement_policy": {
                "anchor": "polygon-pole-of-inaccessibility",
                "inside_polygon_required": True,
                "outside_displacement_allowed": False,
                "authority_class": "local-policy-candidate",
                "support": "local-policy-candidate",
            },
            "collision_suppression_policy": {
                "rule": "suppress-if-no-interior-fit-or-higher-priority-collision",
                "authority_class": "local-policy-candidate",
                "support": "local-policy-candidate",
            },
            "runtime_rendering_responsibility": {
                "consumer": "future-authorized-rendering-adapter",
                "input": "derived non-authoritative XY portrayal view plus bound annotation attributes",
                "single_label_field_required": False,
                "current_null_label_field_reused": False,
                "runtime_implementation_or_activation_allowed": False,
            },
        },
        "portrayal_contract": {
            "status": "partial-production-candidate",
            "target_output_profile": "MapLibre web candidate",
            "properties": _portrayal_properties(),
            "official_portrayal_activation_allowed": False,
        },
        "hatch_resource_contract": {
            "status": "design-contract-only-not-deployable",
            "semantic_role": "feature-clipped repeating building hatch",
            "exact_asset_required": False,
            "acceptable_implementation": "procedural-definition-or-independently-reviewed-equivalent-versioned-asset",
            "current_candidate_asset": "assets/symbols/nlsc112v5.4/review-candidates/building-hatch-tile-v1.svg",
            "current_candidate_asset_present": False,
            "current_candidate_asset_deployable": False,
            "orientation_semantic": "diagonal rising from lower-left to upper-right",
            "numeric_angle_degrees": 45.0,
            "numeric_angle_authority_class": "local-policy-candidate",
            "spacing_mm": 2.0,
            "spacing_authority_class": "authoritative-official",
            "repeat_behavior": "seamless renderer-space repetition clipped to each source-derived polygon",
            "scale_policy": "preserve 2 mm physical output spacing through target-profile conversion",
            "background_behavior": "transparent local-policy-candidate",
            "color_binding": {
                "line_code": "2",
                "color_code": "7",
                "numeric_profile_status": "unresolved",
            },
            "asset_identity_requirements": [
                "versioned resource id",
                "canonical SHA-256",
                "parameter manifest",
                "renderer compatibility result",
            ],
            "review_provenance_requirements": [
                "official row citation",
                "independent visual comparison",
                "target-output-profile approval",
            ],
            "asset_created_or_deployed": False,
        },
        "polygonz_derived_xy_contract": {
            "status": "production-candidate-design-only",
            "pipeline": [
                "authoritative-PolygonZ",
                "immutable-source-representation",
                "derived-non-writing-XY-portrayal-view",
                "rendering-adapter",
            ],
            "source_representation": {
                "authoritative": True,
                "immutable": True,
                "z_values_preserved_and_recoverable": True,
                "write_handle_exposed_to_deriver": False,
            },
            "derived_xy_representation": {
                "authoritative": False,
                "non_writing": True,
                "source_mutation_capability": False,
                "purpose": "portrayal-only",
                "materialization": "ephemeral-or-content-addressed-read-only-cache",
                "geometry_repair_permitted": False,
                "rendering_consumes_derived_only": True,
            },
            "provenance_binding_required": [
                "source archive SHA-256",
                "selected source layer and component SHA-256 values",
                "source feature identity",
                "source PolygonZ geometry hash including Z",
                "derivation algorithm and version",
                "source and output CRS",
                "derived XY content hash",
            ],
            "legacy_drop_z_path": {
                "classification": "incompatible",
                "disposition": "bypassed-by-future-non-writing-derived-view-adapter",
                "reuse_as_is_allowed": False,
            },
            "source_mutation_authority": False,
            "production_execution_allowed": False,
        },
        "readiness": [
            {
                "gate_id": "hatch-angle-transcription",
                "classification": "P1-evidence-supported",
                "reason": "official hatch and spacing plus reviewed orientation exist; numeric angle and reviewed deployable resource remain local/unresolved",
            },
            {
                "gate_id": "building-annotation-placement",
                "classification": "P1-evidence-supported",
                "reason": "official content semantics and reviewed field candidates exist; binding, placement, collision, and style are not official",
            },
            {
                "gate_id": "real-build-schema-binding",
                "classification": "P1-evidence-supported",
                "reason": "both observations and logical BUILD schema are explicit, but no evidence authoritatively selects or relates J13 and J17",
            },
            {
                "gate_id": "line-and-color-profile",
                "classification": "P1-evidence-supported",
                "reason": "official line/color code references exist; numeric web mappings remain local-policy candidates",
            },
            {
                "gate_id": "j13-polygonz-runtime-policy",
                "classification": "P2-production-candidate",
                "reason": "source authority, immutable Z preservation, non-writing XY derivation, provenance, renderer boundary, and legacy-path disposition are explicit",
            },
        ],
        "unresolved_items": [
            "authoritative J13_BUILD/J17_BUILD relationship and exact production layer binding",
            "authoritative mappings for observed BUILD_ID/TERRAINID/BUILD_NO/BUILD_STR/BUILD_H/GROUP_ID fields",
            "official numeric hatch angle or approved local production convention",
            "reviewed procedural or asset-backed hatch implementation",
            "approved annotation source binding, placement, collision, and styling policy",
            "device-independent line-code 2 and color-code 7 rendering profile",
            "building z-order relative to other production layers",
        ],
        "local_policy_candidates": [
            "45-degree numeric hatch angle",
            "transparent hatch background",
            "1 CSS px and #111111 at opacity 1 for MapLibre web output",
            "polygon pole-of-inaccessibility annotation anchor",
            "suppress on no interior fit or higher-priority collision; never displace outside",
            "procedural hatch or independently reviewed equivalent asset",
        ],
        "production_readiness_classification": "partial-production-candidate",
        "source_mutation_policy": {
            "source_mutation_allowed": False,
            "source_geometry_repair_allowed": False,
            "source_z_dimension_removal_allowed": False,
            "derived_output_writeback_allowed": False,
        },
        "runtime_activation_policy": {
            "production_activation_allowed": False,
            "production_runtime_creation_allowed": False,
            "official_portrayal_activation_allowed": False,
            "contract_status_production_active_allowed": False,
            "later_separate_authorization_required": True,
        },
        "next_stage_recommendation": "BUILD-09E — Official Evidence Closure",
    }


def building_production_contract_sha256(contract: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(contract))
    basis.pop("contract_sha256", None)
    return canonical_sha256(basis)


def _validate_semantic_boundaries(contract: Mapping[str, Any]) -> None:
    source = contract.get("authoritative_source_layer_contract", {})
    if source.get("resolution") == "indeterminate" and source.get("selected_layer_id") is not None:
        _fail("An indeterminate J13/J17 result cannot select a layer.", "forced_layer_selection")
    if source.get("global_equivalence_assumed") is not False:
        _fail("J13/J17 global equivalence is unsupported.", "global_layer_equivalence")

    evidence_classes = contract.get("evidence_policy", {}).get("authority_classes", [])
    if evidence_classes != EVIDENCE_AUTHORITY_CLASSES:
        _fail("Evidence authority classes changed or are unknown.", "evidence_classes_invalid")
    for reference in contract.get("evidence_references", []):
        if reference.get("authority_class") not in EVIDENCE_AUTHORITY_CLASSES:
            _fail("An evidence reference has an unknown authority class.", "evidence_class_unknown")
    for field in contract.get("field_semantic_bindings", []):
        if field.get("authority_class") not in EVIDENCE_AUTHORITY_CLASSES:
            _fail("A field has an unknown authority class.", "field_authority_unknown")
        if not all(
            field.get(key)
            for key in (
                "documented_source_meaning",
                "nma_semantic_concept",
                "allowed_use",
                "production_implication",
            )
        ):
            _fail("Every field semantic binding must be explicit.", "field_semantics_undocumented")

    for item in contract.get("portrayal_contract", {}).get("properties", []):
        if item.get("authority_class") not in EVIDENCE_AUTHORITY_CLASSES:
            _fail(
                "A portrayal property has an unknown authority class.",
                "portrayal_authority_unknown",
            )
        if item.get("support") not in SUPPORT_CLASSES:
            _fail("A portrayal property has an unknown support state.", "portrayal_support_unknown")
        if (
            item.get("authority_class")
            in {"demo-evidence", "human-demo-evaluation", "implementation-evidence"}
            and item.get("support") == "officially-supported"
        ):
            _fail(
                "DEMO or implementation evidence cannot establish official portrayal.",
                "portrayal_authority_escalation",
            )

    annotation = contract.get("annotation_contract", {})
    if annotation.get("source_field_binding", {}).get("fields") != ["BUILD_NO", "BUILD_STR"]:
        _fail("Annotation content fields are not explicit.", "annotation_binding_invalid")
    for key in ("placement_policy", "collision_suppression_policy"):
        if annotation.get(key, {}).get("authority_class") not in EVIDENCE_AUTHORITY_CLASSES:
            _fail("Annotation policy authority is not explicit.", "annotation_authority_invalid")

    hatch = contract.get("hatch_resource_contract", {})
    if (
        hatch.get("current_candidate_asset_present") is False
        and hatch.get("current_candidate_asset_deployable") is not False
    ):
        _fail("A missing hatch asset cannot be deployable.", "missing_hatch_deployable")
    if hatch.get("asset_created_or_deployed") is not False:
        _fail("BUILD-09 cannot create or deploy the hatch asset.", "hatch_asset_activated")

    z_contract = contract.get("polygonz_derived_xy_contract", {})
    source_representation = z_contract.get("source_representation", {})
    derived = z_contract.get("derived_xy_representation", {})
    if source_representation.get("z_values_preserved_and_recoverable") is not True:
        _fail("Authoritative source Z must remain recoverable.", "source_z_not_preserved")
    if (
        derived.get("non_writing") is not True
        or derived.get("source_mutation_capability") is not False
    ):
        _fail("Derived XY must be non-writing.", "derived_xy_writing")
    if z_contract.get("legacy_drop_z_path", {}).get("reuse_as_is_allowed") is not False:
        _fail("The destructive drop-Z path cannot be reused as-is.", "destructive_drop_z")

    readiness = contract.get("readiness", [])
    if [item.get("gate_id") for item in readiness] != GATE_IDS:
        _fail("All five inherited gates must be represented exactly.", "gate_set_invalid")
    if any(item.get("classification") not in READINESS_STATES for item in readiness):
        _fail("A readiness state is unknown.", "readiness_state_unknown")

    mutation = contract.get("source_mutation_policy", {})
    if any(value is not False for value in mutation.values()):
        _fail(
            "Source mutation and destructive normalization remain forbidden.",
            "source_mutation_enabled",
        )
    activation = contract.get("runtime_activation_policy", {})
    for key in (
        "production_activation_allowed",
        "production_runtime_creation_allowed",
        "official_portrayal_activation_allowed",
        "contract_status_production_active_allowed",
    ):
        if activation.get(key) is not False:
            _fail(
                "Production or official portrayal activation remains forbidden.",
                "activation_enabled",
            )
    if contract.get("status") == "production-active":
        _fail("BUILD-09 cannot emit production-active.", "production_active")


def build_building_production_contract(
    authorization: Mapping[str, Any],
    build08_review: Mapping[str, Any],
    evaluation_template: Mapping[str, Any],
    evaluation_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the exact non-activating BUILD-09 partial production candidate."""

    validate_official_production_scope_authorization(
        authorization, build08_review, evaluation_template, evaluation_record
    )
    if authorization.get("authorization_sha256") != EXPECTED_BUILD08A_AUTHORIZATION_SHA256:
        _fail("The BUILD-08A authorization identity changed.", "authorization_hash_mismatch")
    contract = _contract_basis()
    contract["contract_sha256"] = building_production_contract_sha256(contract)
    return validate_building_production_contract(
        contract, authorization, build08_review, evaluation_template, evaluation_record
    )


def validate_building_production_contract(
    contract: Mapping[str, Any],
    authorization: Mapping[str, Any],
    build08_review: Mapping[str, Any],
    evaluation_template: Mapping[str, Any],
    evaluation_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate identity, evidence semantics, non-mutation, and non-activation."""

    validate_official_production_scope_authorization(
        authorization, build08_review, evaluation_template, evaluation_record
    )
    if not isinstance(contract, Mapping):
        _fail("The BUILD-09 contract must be an object.", "contract_invalid")
    actual = deepcopy(dict(contract))
    _validate_semantic_boundaries(actual)
    expected = _contract_basis()
    expected["contract_sha256"] = building_production_contract_sha256(expected)
    if set(actual) != set(expected):
        _fail("The BUILD-09 contract fields are not closed.", "contract_fields_invalid")
    if actual.get("contract_sha256") != building_production_contract_sha256(actual):
        _fail("The BUILD-09 contract identity is invalid.", "contract_hash_mismatch")
    if actual != expected:
        _fail(
            "The BUILD-09 evidence or semantics differ from the reviewed contract.",
            "contract_mismatch",
        )
    return actual


__all__ = [
    "BuildingProductionContractError",
    "CONTRACT_SCHEMA",
    "CONTRACT_VERSION",
    "EXPECTED_BUILD08A_AUTHORIZATION_SHA256",
    "EXPECTED_BUILD08A_COMMIT",
    "GATE_IDS",
    "READINESS_STATES",
    "SUPPORT_CLASSES",
    "build_building_production_contract",
    "building_production_contract_sha256",
    "validate_building_production_contract",
]

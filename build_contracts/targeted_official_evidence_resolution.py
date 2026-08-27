"""BUILD-09E1 targeted official evidence resolution.

This module records three evidence boundaries only: J13/J17 production binding,
line code 2, and colour code 7.  It cannot activate production portrayal, choose
local output-profile values, mutate source geometry, or remove source Z values.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from nma.core import canonical_sha256


RESOLUTION_SCHEMA = "nma.building-targeted-official-evidence-resolution/1.0"
RESOLUTION_VERSION = "build-09e1/1.0"
SUCCESSOR_SCHEMA = "nma.building-successor-production-contract-candidate/1.0"
SUCCESSOR_VERSION = "build-09e1-successor/1.0"
EXPECTED_BUILD09E_COMMIT = "e46ea5eb10f6a177ab084d6ca8743c1011f4c1fd"
EXPECTED_BUILD09E_CLOSURE_SHA256 = (
    "bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed"
)
EXPECTED_BUILD09_CONTRACT_SHA256 = (
    "0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c"
)
EXPECTED_BUILD08A_AUTHORIZATION_SHA256 = (
    "4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8"
)

J13_J17_OUTCOMES = [
    "J13-authoritative-production-binding",
    "J17-authoritative-production-binding",
    "version-scoped-dual-binding",
    "different-semantic-roles",
    "official-binding-not-published-or-not-available",
    "indeterminate",
]
LINE_CODE_2_OUTCOMES = [
    "official-physical-width-established",
    "official-symbolic-line-class",
    "official-code-output-profile-dependent",
    "official-code-only",
    "indeterminate",
]
COLOUR_CODE_7_OUTCOMES = [
    "official-device-value-established",
    "official-semantic-black",
    "official-palette-entry",
    "official-code-output-profile-dependent",
    "official-code-only",
    "indeterminate",
]
READINESS_DECISIONS = [
    "READY-FOR-HUMAN-POLICY-GATE",
    "J13-J17-BINDING-STILL-BLOCKING",
    "PORTRAYAL-CODE-EVIDENCE-STILL-BLOCKING",
    "TARGETED-OFFICIAL-EVIDENCE-STILL-MISSING",
]
VERDICTS = [
    "PASS — TARGETED OFFICIAL EVIDENCE CLOSED; HUMAN PRODUCTION POLICY GATE READY",
    "PASS — PORTRAYAL EVIDENCE CLOSED; J13/J17 PRODUCTION BINDING STILL MISSING",
    "PASS — J13/J17 RESOLVED; PORTRAYAL CODE EVIDENCE STILL MISSING",
    "PASS — TARGETED EVIDENCE CLOSURE PARTIAL; OFFICIAL EVIDENCE STILL MISSING",
    "FAIL — TARGETED OFFICIAL EVIDENCE BOUNDARY NOT ESTABLISHED",
]
GATE_STATES = [
    "P2-production-candidate",
    "version-scoped-production-candidate",
    "local-policy-required",
    "local-output-profile-policy-required",
    "HOLD-indeterminate",
]
TRACE_ARROWS = [
    "official_specification",
    "specification_version",
    "dataset_product_package",
    "geographic_product_scope",
    "layer_code",
    "layer_title_meaning",
    "geometry",
    "field_schema",
    "building_semantic_role",
    "nma_production_applicability",
]
PROMOTION_DENIED_AUTHORITIES = {
    "implementation-evidence",
    "demo-evidence",
    "human-demo-evaluation",
}


class TargetedOfficialEvidenceResolutionError(ValueError):
    """BUILD-09E1 rejected an identity, evidence, or safety boundary."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise TargetedOfficialEvidenceResolutionError(message, code=code)


def _input_sha256(value: Mapping[str, Any], identity_key: str) -> str:
    basis = deepcopy(dict(value))
    basis.pop(identity_key, None)
    return canonical_sha256(basis)


def targeted_official_evidence_resolution_sha256(record: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(record))
    basis.pop("targeted_official_evidence_resolution_sha256", None)
    return canonical_sha256(basis)


def successor_production_contract_sha256(contract: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(contract))
    basis.pop("successor_production_contract_sha256", None)
    return canonical_sha256(basis)


def _arrow(value: str | None, *evidence_ids: str) -> dict[str, Any]:
    return {"value": value, "evidence_ids": list(evidence_ids)}


def _evidence_items() -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": "build09e-frozen-evidence-closure",
            "source": "data/specifications/nma-build-09e-golden-official-evidence-closure-v1.0.json",
            "authority_class": "frozen-reviewed-project-evidence",
            "claim": "BUILD-09E closed annotation, hatch, and PolygonZ findings and limited the remaining official gaps to exactly J13/J17, line code 2, and colour code 7",
            "identity": "record:bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed; file-sha256:f65862c85ce2ed9e9ea7b2217d4d3a2cd6abf863c2532ab79cf803aa0860e673",
        },
        {
            "evidence_id": "nlsc112v5.4-building-portrayal-row",
            "source": "01-一千分之一地形圖圖式規格表.pdf; Drive file 1KQN1GCwVPFSms3IUi4pmNqM4ru3TYVrZ; page 8",
            "authority_class": "authoritative-official-specification",
            "claim": "permanent Building 9310100 uses line code 2 and colour code 7, with 2 mm hatch spacing and floor-then-structure annotation",
            "identity": "NLSC112V5.4; effective:2024-02-28; sha256:1f9c4457d7ced86f2b7681e21be9ad3b7b7ae364981ab995ef27b468e0fa2620#page=8",
        },
        {
            "evidence_id": "nlsc112-18-portrayal-code-table",
            "source": "多維度圖式研究案報告(修訂版).pdf; Drive file 1C-2N1JDxr9JHc6s2b2AvHJ1HwxndCXRy; printed page 10; PDF page 22; Figure 2-3",
            "authority_class": "authoritative-versioned-source-documentation",
            "claim": "Figure 2-3 defines line code 2 as 0.20 mm and colour code 7 as black with RGB value (R-G-B) (0,0,0)",
            "identity": "NLSC-112-18; commissioned-by:內政部國土測繪中心; report-date:112-11-20; drive-size:12003802; drive-modified:2024-01-25T08:59:54.631Z; sha256:0f8931be648077d6775d1c866376fef775bb3f8568448f94d30493d56b945fda#pdf-page=22",
        },
        {
            "evidence_id": "multidimensional-layer-v4-build-schema",
            "source": "多維度繪製圖層V4.xlsx; Drive file 1C12PmP-8ZZtZbHVKRAKv0mmWE22kgzEw",
            "authority_class": "authoritative-versioned-source-documentation",
            "claim": "V4 defines the logical polygon layer (三)建物BUILD(面), terrain codes 9310100/9310200/9310300, and fields BUILD_ID,TERRAINID,BUILD_STR,BUILD_NO,BUILD_H,GROUP_ID,MDATE; it does not publish a J13/J17 package-member production binding",
            "identity": "V4; decision-date:2023-11-10; drive-size:569257; drive-modified:2024-01-25T08:59:54.631Z; sha256:d3f065a57d10c306e9e4e686641c07ddf2fb5a6d3638b68ec4d3ea533839f308",
        },
        {
            "evidence_id": "multidimensional-source-package-members",
            "source": "data/datasets/112年多維度SHP成果_0502.zip",
            "authority_class": "authoritative-metadata",
            "claim": "J13_BUILD and J17_BUILD are distinct source members in different geographic/project scopes with PolygonZ and the observed BUILD field set; member presence does not establish NMA production applicability",
            "identity": "sha256:4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
        },
        {
            "evidence_id": "build00a-demo-and-current-runtime",
            "source": "data/specifications/nma-build-fixture-manifest-v1.0.json; src/nma/real_layer.py",
            "authority_class": "implementation-and-demo-evidence",
            "claim": "J13 DEMO selection and J17 runtime history are corroborative only and cannot create an official production binding",
            "identity": "BUILD-00A fixture plus BUILD-09E predecessor implementation boundary",
        },
    ]


def _available_product_trace() -> dict[str, Any]:
    return {
        "official_specification": _arrow(
            "多維度繪製圖層V4.xlsx", "multidimensional-layer-v4-build-schema"
        ),
        "specification_version": _arrow(
            "V4; decision date 2023-11-10", "multidimensional-layer-v4-build-schema"
        ),
        "dataset_product_package": _arrow(
            "multidimensional spatial-information base-map layer definition",
            "multidimensional-layer-v4-build-schema",
        ),
        "geographic_product_scope": _arrow(
            "logical product schema; no J13/J17 member scope is assigned",
            "multidimensional-layer-v4-build-schema",
            "multidimensional-source-package-members",
        ),
        "layer_code": _arrow("BUILD", "multidimensional-layer-v4-build-schema"),
        "layer_title_meaning": _arrow(
            "(三)建物BUILD(面)", "multidimensional-layer-v4-build-schema"
        ),
        "geometry": _arrow(
            "面 (polygon); observed package members are PolygonZ",
            "multidimensional-layer-v4-build-schema",
            "multidimensional-source-package-members",
        ),
        "field_schema": _arrow(
            "BUILD_ID,TERRAINID,BUILD_STR,BUILD_NO,BUILD_H,GROUP_ID,MDATE",
            "multidimensional-layer-v4-build-schema",
            "multidimensional-source-package-members",
        ),
        "building_semantic_role": _arrow(
            "Building polygons for permanent, under-construction, and temporary buildings",
            "multidimensional-layer-v4-build-schema",
            "nlsc112v5.4-building-portrayal-row",
        ),
        "nma_production_applicability": _arrow(
            "not-published-or-not-available for J13_BUILD versus J17_BUILD",
            "multidimensional-layer-v4-build-schema",
            "multidimensional-source-package-members",
        ),
    }


def _resolution_basis(
    build09e_closure: Mapping[str, Any], build09_contract: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "contract_version": RESOLUTION_VERSION,
        "schema_version": RESOLUTION_SCHEMA,
        "status": "evidence-hold",
        "created_on": "2026-08-21",
        "predecessor": {
            "build09e_branch": "build/build-09e-official-evidence-closure",
            "build09e_commit": EXPECTED_BUILD09E_COMMIT,
            "build09e_evidence_closure_sha256": EXPECTED_BUILD09E_CLOSURE_SHA256,
            "build09_contract_sha256": EXPECTED_BUILD09_CONTRACT_SHA256,
            "build08a_authorization_sha256": EXPECTED_BUILD08A_AUTHORIZATION_SHA256,
            "frozen_build09e_artifact_sha256": {
                "BUILD-09E-Completion-Report.md": "ee6cce5dd2202edf5e1970bc889340f16f8979f8a1a4d829b0f5672e95612d24",
                "build_contracts/official_evidence_closure.py": "46e5f4364e1cf58cae248ea3333fd04b6acedffced7de44137b2cdff93140fa1",
                "data/specifications/nma-build-09e-golden-official-evidence-closure-v1.0.json": "f65862c85ce2ed9e9ea7b2217d4d3a2cd6abf863c2532ab79cf803aa0860e673",
                "schemas/building-official-evidence-closure-v1.0.schema.json": "ac317bb47a8ab6481de215d4d01184d6a05bc84ebfed8de804a1c18508afe937",
                "tests/test_official_evidence_closure_build09e.py": "d231e8a2beb9f83baefaf2233852f098d4e88edc098fce526447483bbfb144ec",
            },
        },
        "closed_vocabularies": {
            "j13_j17_outcomes": list(J13_J17_OUTCOMES),
            "line_code_2_outcomes": list(LINE_CODE_2_OUTCOMES),
            "colour_code_7_outcomes": list(COLOUR_CODE_7_OUTCOMES),
            "readiness_decisions": list(READINESS_DECISIONS),
            "verdicts": list(VERDICTS),
            "gate_states": list(GATE_STATES),
        },
        "evidence_items": _evidence_items(),
        "frozen_build09e_results": {
            "annotation_closure": deepcopy(build09e_closure["annotation_closure"]),
            "hatch_spacing": deepcopy(build09e_closure["hatch_closure"]["spacing"]),
            "hatch_angle": deepcopy(build09e_closure["hatch_closure"]["angle"]),
            "hatch_pattern_orientation": deepcopy(
                build09e_closure["hatch_closure"]["pattern_orientation"]
            ),
            "hatch_resource": deepcopy(build09e_closure["hatch_closure"]["resource"]),
            "polygonz_derived_xy": deepcopy(build09_contract["polygonz_derived_xy_contract"]),
        },
        "j13_j17_resolution": {
            "outcome": "official-binding-not-published-or-not-available",
            "selected_layer_id": None,
            "authoritative_binding_traces": [],
            "available_product_trace": _available_product_trace(),
            "source_member_scopes": [
                {
                    "layer_id": "J13_BUILD",
                    "scope": "Baoshan urban-plan package member",
                    "authority": "authoritative-metadata-only",
                },
                {
                    "layer_id": "J17_BUILD",
                    "scope": "Hsinchu Science Park special-plan (Baoshan portion) package member",
                    "authority": "authoritative-metadata-only",
                },
            ],
            "forced_equivalence_authorized": False,
            "selection_rule": "selection-forbidden-until-an-authoritative-versioned-package-manifest-binds-J13_BUILD-or-J17_BUILD-to-the-NMA-production-contract",
            "unavailable_material_boundary": "No available authoritative specification, schema, legend, metadata manifest, or versioned source document publishes the required J13/J17-to-NMA production applicability arrow; private source archives were not accessed or inferred.",
        },
        "line_code_2_resolution": {
            "outcome": "official-physical-width-established",
            "official_code": "2",
            "official_symbolic_name": "2號線",
            "physical_width": {"value_text": "0.20", "value": 0.2, "unit": "mm"},
            "source_representation": "圖式線號 table; 單位:mm公釐; code 2; 規格 0.20",
            "evidence_ids": [
                "nlsc112v5.4-building-portrayal-row",
                "nlsc112-18-portrayal-code-table",
            ],
            "css_px": None,
            "device_conversion_authorized": False,
            "authority_boundary": "official physical/cartographic width is 0.20 mm; device/CSS conversion is not prescribed by the cited table",
        },
        "colour_code_7_resolution": {
            "outcome": "official-device-value-established",
            "official_code": "7",
            "semantic_name": "黑色",
            "original_representation": {
                "representation": "RGB值 (R-G-B)",
                "value_text": "(0,0,0)",
                "components": [0, 0, 0],
            },
            "official_hex": None,
            "evidence_ids": [
                "nlsc112v5.4-building-portrayal-row",
                "nlsc112-18-portrayal-code-table",
            ],
            "authority_boundary": "official table defines semantic black and the original RGB (R-G-B) value (0,0,0); no HEX notation is stated",
        },
        "output_profile_requirement": {
            "status": "local-output-profile-policy-required",
            "required": True,
            "pipeline": [
                "official-portrayal-semantics",
                "authorized-local-output-profile",
                "MapLibre-device-representation",
            ],
            "must_preserve": [
                "line code 2 physical width 0.20 mm",
                "colour code 7 original RGB (R-G-B) value (0,0,0)",
            ],
            "local_values_selected": False,
            "local_decisions": [
                "physical-mm-to-CSS-pixel conversion",
                "screen scale and DPI assumptions",
                "MapLibre colour serialization without claiming an official HEX value",
                "opacity and antialiasing behavior",
            ],
        },
        "remaining_authoritative_evidence_gaps": [
            "versioned J13/J17 package-member production applicability binding"
        ],
        "local_policy_required_items": [
            "numeric hatch angle within official diagonal semantics",
            "hatch rendering resource or procedure",
            "annotation placement, collision, scale, separator, and typography algorithm",
            "line code 2 physical-mm output-profile conversion",
            "MapLibre serialization of the official colour code 7 RGB representation",
            "opacity and antialiasing parameters",
        ],
        "five_gate_state": [
            {
                "gate_id": "hatch-angle-asset",
                "state": "local-policy-required",
                "reason": "BUILD-09E official diagonal and 2 mm spacing findings remain frozen; numeric angle and resource remain local",
            },
            {
                "gate_id": "annotation-placement-binding",
                "state": "local-policy-required",
                "reason": "BUILD-09E content and placement semantics remain frozen; the production placement algorithm remains local",
            },
            {
                "gate_id": "j13-j17-schema-identity",
                "state": "HOLD-indeterminate",
                "reason": "logical BUILD is versioned, but the available authority does not publish J13/J17 NMA production applicability",
            },
            {
                "gate_id": "line-colour-portrayal",
                "state": "local-output-profile-policy-required",
                "reason": "official 0.20 mm and RGB (0,0,0) boundaries are closed; renderer conversion remains a human output-profile policy",
            },
            {
                "gate_id": "polygonz-derived-xy",
                "state": "P2-production-candidate",
                "reason": "immutable PolygonZ and non-writing derived XY architecture is unchanged",
            },
        ],
        "successor_production_contract_candidate": {
            "created": True,
            "path": "data/specifications/nma-build-09e1-successor-building-production-contract-candidate-v1.0.json",
            "status": "evidence-hold",
            "reason": "line and colour blockers are materially closed; J13/J17 production applicability still prevents activation",
        },
        "build10_readiness": "J13-J17-BINDING-STILL-BLOCKING",
        "verdict": "PASS — PORTRAYAL EVIDENCE CLOSED; J13/J17 PRODUCTION BINDING STILL MISSING",
        "conflicting_authoritative_evidence": [],
        "scope": {
            "production_runtime_modified": False,
            "official_portrayal_activated": False,
            "source_data_or_geometry_modified": False,
            "source_z_removed": False,
            "hatch_asset_created": False,
            "local_output_values_selected": False,
        },
        "source_mutation_policy": deepcopy(build09_contract["source_mutation_policy"]),
        "runtime_activation_policy": deepcopy(build09_contract["runtime_activation_policy"]),
        "next_stage_recommendation": "another targeted continuation only for the exact J13/J17 production-binding evidence gap; do not reopen portrayal evidence and do not begin BUILD-10",
    }


def _validate_trace(trace: Mapping[str, Any]) -> None:
    if len(trace) != len(TRACE_ARROWS) or set(trace) != set(TRACE_ARROWS):
        _fail("The authoritative trace arrows are incomplete.", "trace_incomplete")
    for arrow in TRACE_ARROWS:
        step = trace.get(arrow, {})
        if not isinstance(step, Mapping) or not step.get("value") or not step.get("evidence_ids"):
            _fail("Every authoritative trace arrow needs identified evidence.", "trace_incomplete")


def validate_j13_j17_resolution(value: Mapping[str, Any]) -> None:
    outcome = value.get("outcome")
    if outcome not in J13_J17_OUTCOMES:
        _fail("The J13/J17 evidence state is unknown.", "j13_j17_outcome_unknown")
    selected = value.get("selected_layer_id")
    traces = value.get("authoritative_binding_traces", [])
    if outcome in {
        "J13-authoritative-production-binding",
        "J17-authoritative-production-binding",
    }:
        expected = "J13_BUILD" if outcome.startswith("J13") else "J17_BUILD"
        if selected != expected or len(traces) != 1:
            _fail("A single-layer binding needs one complete trace.", "binding_without_trace")
        if traces[0].get("authority_class") in PROMOTION_DENIED_AUTHORITIES:
            _fail("Implementation or DEMO evidence cannot create a binding.", "secondary_binding")
        _validate_trace(traces[0].get("trace", {}))
    elif outcome in {"version-scoped-dual-binding", "different-semantic-roles"}:
        if selected is not None or len(traces) != 2:
            _fail(
                "A scoped/role result needs two explicit traces and no global layer.",
                "scoped_binding_invalid",
            )
        layers = {item.get("layer_id") for item in traces}
        if layers != {"J13_BUILD", "J17_BUILD"}:
            _fail("Scoped traces must identify J13 and J17 exactly.", "scoped_binding_invalid")
        for item in traces:
            if item.get("authority_class") in PROMOTION_DENIED_AUTHORITIES:
                _fail(
                    "Implementation or DEMO evidence cannot create a binding.", "secondary_binding"
                )
            _validate_trace(item.get("trace", {}))
    elif outcome == "official-binding-not-published-or-not-available":
        if selected is not None or traces:
            _fail(
                "Unavailable official binding cannot select a layer.",
                "unpublished_binding_selected",
            )
        product_trace = value.get("available_product_trace", {})
        _validate_trace(product_trace)
        applicability = product_trace["nma_production_applicability"]["value"]
        if applicability != "not-published-or-not-available for J13_BUILD versus J17_BUILD":
            _fail("The published/unavailable boundary changed.", "unpublished_boundary_changed")
        if value.get("forced_equivalence_authorized") is not False:
            _fail("J13/J17 equivalence cannot be forced.", "forced_equivalence")
    elif selected is not None or traces:
        _fail("Indeterminate evidence cannot select a layer.", "binding_without_trace")


def validate_line_code_2_resolution(value: Mapping[str, Any]) -> None:
    outcome = value.get("outcome")
    if outcome not in LINE_CODE_2_OUTCOMES:
        _fail("The line-code-2 evidence state is unknown.", "line_outcome_unknown")
    if value.get("official_code") != "2":
        _fail("The official line code changed.", "line_code_changed")
    if value.get("css_px") is not None:
        _fail("Line code 2 cannot become CSS pixels without a separate rule.", "unsupported_css_px")
    width = value.get("physical_width")
    if outcome == "official-physical-width-established":
        if not isinstance(width, Mapping) or not width.get("value_text") or not width.get("unit"):
            _fail(
                "Official physical width must preserve value and unit.", "physical_width_incomplete"
            )
    elif width is not None:
        _fail(
            "Only the physical-width outcome may carry a physical width.", "line_boundary_mismatch"
        )
    if outcome == "official-symbolic-line-class" and not value.get("official_symbolic_name"):
        _fail("A symbolic line class needs its official name.", "symbolic_class_incomplete")
    if outcome == "official-code-output-profile-dependent" and not value.get(
        "output_profile_dependency"
    ):
        _fail(
            "An output-profile-dependent code needs an explicit boundary.",
            "profile_boundary_missing",
        )


def validate_colour_code_7_resolution(value: Mapping[str, Any]) -> None:
    outcome = value.get("outcome")
    if outcome not in COLOUR_CODE_7_OUTCOMES:
        _fail("The colour-code-7 evidence state is unknown.", "colour_outcome_unknown")
    if value.get("official_code") != "7":
        _fail("The official colour code changed.", "colour_code_changed")
    if value.get("official_hex") is not None:
        _fail(
            "The source evidence states RGB, not an official HEX value.", "unsupported_official_hex"
        )
    representation = value.get("original_representation")
    if outcome == "official-device-value-established" and not isinstance(representation, Mapping):
        _fail("A device-value outcome needs the original representation.", "device_value_missing")
    if outcome == "official-semantic-black":
        if value.get("semantic_name") not in {"black", "黑色"} or representation is not None:
            _fail("Semantic black cannot imply a device value.", "semantic_black_overreach")
    if outcome == "official-palette-entry" and not value.get("palette_reference"):
        _fail("A palette entry needs its official palette reference.", "palette_reference_missing")
    if outcome == "official-code-output-profile-dependent" and not value.get(
        "output_profile_dependency"
    ):
        _fail("An output-profile colour needs an explicit boundary.", "profile_boundary_missing")


def _validate_frozen_boundaries(
    record: Mapping[str, Any],
    build09e_closure: Mapping[str, Any],
    build09_contract: Mapping[str, Any],
) -> None:
    frozen = record.get("frozen_build09e_results", {})
    expected = {
        "annotation_closure": build09e_closure.get("annotation_closure"),
        "hatch_spacing": build09e_closure.get("hatch_closure", {}).get("spacing"),
        "hatch_angle": build09e_closure.get("hatch_closure", {}).get("angle"),
        "hatch_pattern_orientation": build09e_closure.get("hatch_closure", {}).get(
            "pattern_orientation"
        ),
        "hatch_resource": build09e_closure.get("hatch_closure", {}).get("resource"),
        "polygonz_derived_xy": build09_contract.get("polygonz_derived_xy_contract"),
    }
    if frozen != expected:
        _fail("A closed BUILD-09E finding regressed.", "frozen_finding_changed")
    if any(record.get("source_mutation_policy", {}).values()):
        _fail("Source mutation or destructive Z removal was enabled.", "source_mutation_enabled")
    activation = record.get("runtime_activation_policy", {})
    for key in (
        "production_activation_allowed",
        "production_runtime_creation_allowed",
        "official_portrayal_activation_allowed",
        "contract_status_production_active_allowed",
    ):
        if activation.get(key) is not False:
            _fail("Production or official portrayal activation was enabled.", "activation_enabled")


def build_targeted_official_evidence_resolution(
    build09e_closure: Mapping[str, Any],
    build09_contract: Mapping[str, Any],
    build08a_authorization: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        build09e_closure.get("official_evidence_closure_sha256") != EXPECTED_BUILD09E_CLOSURE_SHA256
        or _input_sha256(build09e_closure, "official_evidence_closure_sha256")
        != EXPECTED_BUILD09E_CLOSURE_SHA256
    ):
        _fail("The BUILD-09E evidence identity changed.", "build09e_identity_mismatch")
    if (
        build09_contract.get("contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256
        or _input_sha256(build09_contract, "contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256
    ):
        _fail("The BUILD-09 contract identity changed.", "build09_identity_mismatch")
    if (
        build08a_authorization.get("authorization_sha256") != EXPECTED_BUILD08A_AUTHORIZATION_SHA256
        or _input_sha256(build08a_authorization, "authorization_sha256")
        != EXPECTED_BUILD08A_AUTHORIZATION_SHA256
    ):
        _fail("The BUILD-08A authorization identity changed.", "build08a_identity_mismatch")
    record = _resolution_basis(build09e_closure, build09_contract)
    record["targeted_official_evidence_resolution_sha256"] = (
        targeted_official_evidence_resolution_sha256(record)
    )
    return validate_targeted_official_evidence_resolution(
        record, build09e_closure, build09_contract, build08a_authorization
    )


def validate_targeted_official_evidence_resolution(
    record: Mapping[str, Any],
    build09e_closure: Mapping[str, Any],
    build09_contract: Mapping[str, Any],
    build08a_authorization: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        _fail("The BUILD-09E1 record must be an object.", "record_invalid")
    if build09e_closure.get("official_evidence_closure_sha256") != EXPECTED_BUILD09E_CLOSURE_SHA256:
        _fail("The BUILD-09E evidence identity changed.", "build09e_identity_mismatch")
    if build09_contract.get("contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256:
        _fail("The BUILD-09 contract identity changed.", "build09_identity_mismatch")
    if build08a_authorization.get("authorization_sha256") != EXPECTED_BUILD08A_AUTHORIZATION_SHA256:
        _fail("The BUILD-08A authorization identity changed.", "build08a_identity_mismatch")
    actual = deepcopy(dict(record))
    vocab = actual.get("closed_vocabularies", {})
    if vocab != {
        "j13_j17_outcomes": J13_J17_OUTCOMES,
        "line_code_2_outcomes": LINE_CODE_2_OUTCOMES,
        "colour_code_7_outcomes": COLOUR_CODE_7_OUTCOMES,
        "readiness_decisions": READINESS_DECISIONS,
        "verdicts": VERDICTS,
        "gate_states": GATE_STATES,
    }:
        _fail("A closed evidence vocabulary changed.", "unknown_evidence_state")
    validate_j13_j17_resolution(actual.get("j13_j17_resolution", {}))
    validate_line_code_2_resolution(actual.get("line_code_2_resolution", {}))
    validate_colour_code_7_resolution(actual.get("colour_code_7_resolution", {}))
    _validate_frozen_boundaries(actual, build09e_closure, build09_contract)
    if actual.get("build10_readiness") not in READINESS_DECISIONS:
        _fail("The BUILD-10 readiness state is unknown.", "unknown_evidence_state")
    if actual.get("verdict") not in VERDICTS:
        _fail("The verdict is unknown.", "unknown_evidence_state")
    if actual.get("targeted_official_evidence_resolution_sha256") != (
        targeted_official_evidence_resolution_sha256(actual)
    ):
        _fail("The BUILD-09E1 record hash is invalid.", "resolution_hash_mismatch")
    expected = _resolution_basis(build09e_closure, build09_contract)
    expected["targeted_official_evidence_resolution_sha256"] = (
        targeted_official_evidence_resolution_sha256(expected)
    )
    if set(actual) != set(expected):
        _fail("The BUILD-09E1 fields are not closed.", "record_fields_invalid")
    if actual != expected:
        _fail("The BUILD-09E1 record differs from the reviewed resolution.", "record_mismatch")
    return actual


def _successor_basis(
    resolution: Mapping[str, Any],
    build09_contract: Mapping[str, Any],
    build09e_closure: Mapping[str, Any],
) -> dict[str, Any]:
    frozen = resolution["frozen_build09e_results"]
    return {
        "contract_version": SUCCESSOR_VERSION,
        "schema_version": SUCCESSOR_SCHEMA,
        "status": "evidence-hold",
        "created_on": "2026-08-21",
        "bindings": {
            "build09_contract_sha256": EXPECTED_BUILD09_CONTRACT_SHA256,
            "build09e_evidence_closure_sha256": EXPECTED_BUILD09E_CLOSURE_SHA256,
            "build09e1_evidence_resolution_sha256": resolution[
                "targeted_official_evidence_resolution_sha256"
            ],
        },
        "production_binding": {
            "outcome": resolution["j13_j17_resolution"]["outcome"],
            "selected_layer_id": None,
            "selection_authorized": False,
        },
        "official_portrayal_semantics": {
            "annotation": deepcopy(frozen["annotation_closure"]),
            "hatch_spacing": deepcopy(frozen["hatch_spacing"]),
            "hatch_angle": deepcopy(frozen["hatch_angle"]),
            "hatch_resource": deepcopy(frozen["hatch_resource"]),
            "line_code_2": deepcopy(resolution["line_code_2_resolution"]),
            "colour_code_7": deepcopy(resolution["colour_code_7_resolution"]),
        },
        "output_profile_requirement": deepcopy(resolution["output_profile_requirement"]),
        "polygonz_derived_xy_contract": deepcopy(build09_contract["polygonz_derived_xy_contract"]),
        "source_mutation_policy": deepcopy(build09_contract["source_mutation_policy"]),
        "runtime_activation_policy": deepcopy(build09_contract["runtime_activation_policy"]),
        "production_activation_forbidden": True,
        "official_portrayal_activation_forbidden": True,
        "remaining_authoritative_evidence_gaps": deepcopy(
            resolution["remaining_authoritative_evidence_gaps"]
        ),
        "local_policy_required_items": deepcopy(resolution["local_policy_required_items"]),
    }


def build_successor_production_contract_candidate(
    resolution: Mapping[str, Any],
    build09_contract: Mapping[str, Any],
    build09e_closure: Mapping[str, Any],
) -> dict[str, Any]:
    contract = _successor_basis(resolution, build09_contract, build09e_closure)
    contract["successor_production_contract_sha256"] = successor_production_contract_sha256(
        contract
    )
    return validate_successor_production_contract_candidate(
        contract, resolution, build09_contract, build09e_closure
    )


def validate_successor_production_contract_candidate(
    contract: Mapping[str, Any],
    resolution: Mapping[str, Any],
    build09_contract: Mapping[str, Any],
    build09e_closure: Mapping[str, Any],
) -> dict[str, Any]:
    if resolution.get(
        "targeted_official_evidence_resolution_sha256"
    ) != targeted_official_evidence_resolution_sha256(resolution):
        _fail("The BUILD-09E1 evidence binding is invalid.", "resolution_hash_mismatch")
    if (
        build09_contract.get("contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256
        or _input_sha256(build09_contract, "contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256
    ):
        _fail("The BUILD-09 contract binding is invalid.", "build09_identity_mismatch")
    if (
        build09e_closure.get("official_evidence_closure_sha256") != EXPECTED_BUILD09E_CLOSURE_SHA256
        or _input_sha256(build09e_closure, "official_evidence_closure_sha256")
        != EXPECTED_BUILD09E_CLOSURE_SHA256
    ):
        _fail("The BUILD-09E evidence binding is invalid.", "build09e_identity_mismatch")
    if contract.get("status") == "production-active":
        _fail("The successor cannot be production-active.", "activation_enabled")
    if contract.get("successor_production_contract_sha256") != (
        successor_production_contract_sha256(contract)
    ):
        _fail("The successor contract hash is invalid.", "successor_hash_mismatch")
    expected = _successor_basis(resolution, build09_contract, build09e_closure)
    expected["successor_production_contract_sha256"] = successor_production_contract_sha256(
        expected
    )
    if dict(contract) != expected:
        _fail("The successor contract differs from the reviewed candidate.", "successor_mismatch")
    return deepcopy(dict(contract))


__all__ = [
    "COLOUR_CODE_7_OUTCOMES",
    "EXPECTED_BUILD08A_AUTHORIZATION_SHA256",
    "EXPECTED_BUILD09_CONTRACT_SHA256",
    "EXPECTED_BUILD09E_CLOSURE_SHA256",
    "EXPECTED_BUILD09E_COMMIT",
    "GATE_STATES",
    "J13_J17_OUTCOMES",
    "LINE_CODE_2_OUTCOMES",
    "READINESS_DECISIONS",
    "TargetedOfficialEvidenceResolutionError",
    "VERDICTS",
    "build_successor_production_contract_candidate",
    "build_targeted_official_evidence_resolution",
    "successor_production_contract_sha256",
    "targeted_official_evidence_resolution_sha256",
    "validate_colour_code_7_resolution",
    "validate_j13_j17_resolution",
    "validate_line_code_2_resolution",
    "validate_successor_production_contract_candidate",
    "validate_targeted_official_evidence_resolution",
]

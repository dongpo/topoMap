"""BUILD-09E deterministic official-evidence closure.

This module records evidence and validates production-contract boundaries.  It
does not create a renderer, read or mutate source geometry, or activate either
production or official portrayal.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from nma.core import canonical_sha256


CLOSURE_SCHEMA = "nma.building-official-evidence-closure/1.0"
CLOSURE_VERSION = "build-09e/1.0"
EXPECTED_BUILD09_COMMIT = "23b4f042ee14934b01d6215277e3e0881767a580"
EXPECTED_BUILD09_CONTRACT_SHA256 = (
    "0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c"
)
EXPECTED_BUILD08A_AUTHORIZATION_SHA256 = (
    "4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8"
)

AUTHORITY_CLASSES = [
    "authoritative-official",
    "authoritative-schema",
    "authoritative-metadata",
    "documented-source-semantics",
    "frozen-project-evidence",
    "implementation-evidence",
    "demo-evidence",
    "human-demo-evaluation",
    "local-policy-required",
    "unknown",
]
COMPONENT_OUTCOMES = [
    "officially-supported",
    "documented-source-semantics",
    "local-policy-required",
    "local-policy-required-with-official-diagonal-semantics",
    "implementation-only",
    "indeterminate",
    "contradicted",
]
READINESS_STATES = [
    "P1-evidence-supported",
    "P2-production-candidate",
    "local-policy-required",
    "HOLD-indeterminate",
    "HOLD-conflicting-authority",
]
LAYER_OUTCOMES = [
    "J13-authoritative-production-candidate",
    "J17-authoritative-production-candidate",
    "version-scoped-dual-contract-required",
    "different-semantic-roles",
    "indeterminate",
]
PROMOTION_DENIED_CLASSES = {
    "implementation-evidence",
    "demo-evidence",
    "human-demo-evaluation",
}
TRACE_STEPS = [
    "official-specification/version",
    "layer-code",
    "layer-meaning",
    "geometry-type",
    "field-set",
    "dataset-version",
    "NMA-production-contract",
]


class OfficialEvidenceClosureError(ValueError):
    """BUILD-09E rejected evidence, identity, state, or boundary changes."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise OfficialEvidenceClosureError(message, code=code)


def _evidence_items() -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": "build09-frozen-production-contract",
            "source": "data/specifications/nma-build-09-golden-building-production-contract-v1.0.json",
            "version_date": "build-09/1.0; 2026-08-21",
            "provenance": "frozen reviewed project artifact at the exact BUILD-09 commit",
            "authority_class": "frozen-project-evidence",
            "claim": "five inherited gates, PolygonZ P2 contract, non-activation, and non-mutation boundaries",
            "confidence": "exact",
            "conflicts": [],
            "identity": "sha256:87355baed4c8277218cafb4bf98114a2d24e8a706fc55540a24b445c60cc7112; contract:0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c",
        },
        {
            "evidence_id": "doc01-building-portrayal-row",
            "source": "data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json; Drive file 1KQN1GCwVPFSms3IUi4pmNqM4ru3TYVrZ page 8",
            "version_date": "NLSC112V5.4; effective 2024-02-28",
            "provenance": "official NLSC specification registered in data/sources/authoritative-sources.json and frozen reviewed transcription",
            "authority_class": "authoritative-official",
            "claim": "9310100 Building is surveyed as a real polygon, hatched at 2 mm spacing, annotated floor then structure, with line code 2 and colour code 7",
            "confidence": "high",
            "conflicts": [],
            "identity": "sha256:1f9c4457d7ced86f2b7681e21be9ad3b7b7ae364981ab995ef27b468e0fa2620#page=8",
        },
        {
            "evidence_id": "doc02-annotation-rules",
            "source": "Drive file 1W9hkUsVM49dsV8pgXZtGn5hChoe38GkR",
            "version_date": "內政部; 2022-12",
            "provenance": "official source registered as 02-一千分之一數值航測地形圖測製作業規定.pdf",
            "authority_class": "authoritative-official",
            "claim": "Building annotations record structure and floors; general annotations are centered in or near the feature, must not cover it, and avoid mapped features, control points, and grid lines",
            "confidence": "high",
            "conflicts": [],
            "identity": "drive-file-id:1W9hkUsVM49dsV8pgXZtGn5hChoe38GkR; tracked-registry-sha256:319e533ce6268c88dfd84d9a2b2e2f38f5fdb409bf0197981693147adaacaaa2",
        },
        {
            "evidence_id": "doc09-current-build-schema",
            "source": "data/specifications/taiwan-temap-build-v0.4.json; Drive file 1vKllnQfSlK2nA_HdxtgvUtPvZWn5lxMz",
            "version_date": "revision 114.12.04",
            "provenance": "official current Taiwan electronic-map layer documentation and tracked deterministic extraction",
            "authority_class": "authoritative-schema",
            "claim": "logical BUILD is Polygon with ID, MDATE, and SOURCE; official package naming does not select J13_BUILD or J17_BUILD",
            "confidence": "high",
            "conflicts": [
                "observed multidimensional archive fields and layer names are not the current documented BUILD schema"
            ],
            "identity": "sha256:b3c26f6e2766e9e6fac2a85f935b88e45741708ef6def79213b4c18a2cdb3683#revision=114.12.04",
        },
        {
            "evidence_id": "multidimensional-build-field-workbook",
            "source": "Drive file 1oGPC2GCZiKeLK_P4WNOmA5KbSsqePHvm",
            "version_date": "多維度繪製圖層V3.xlsx; modified 2024-01-25",
            "provenance": "source-package workbook in the NLSC multidimensional project materials; not promoted to current official schema",
            "authority_class": "documented-source-semantics",
            "claim": "BUILD_NO means floor count and BUILD_STR means structure, supporting the observed archive field binding without proving J13/J17 production authority",
            "confidence": "medium",
            "conflicts": ["field set differs from Document 09 revision 114.12.04"],
            "identity": "drive-file-id:1oGPC2GCZiKeLK_P4WNOmA5KbSsqePHvm; size:490287; modified:2024-01-25T02:38:00Z",
        },
        {
            "evidence_id": "multidimensional-source-package",
            "source": "data/datasets/112年多維度SHP成果_0502.zip",
            "version_date": "112-year package; filename revision 0502",
            "provenance": "tracked immutable source package; member paths and shapefile metadata only",
            "authority_class": "authoritative-metadata",
            "claim": "J13_BUILD and J17_BUILD are separate geographic/project-area members with common observed fields and PolygonZ geometry; package presence does not select production authority",
            "confidence": "high",
            "conflicts": [],
            "identity": "sha256:4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
        },
        {
            "evidence_id": "build00a-fixture-selection",
            "source": "data/specifications/nma-build-fixture-manifest-v1.0.json",
            "version_date": "build-00a/1.0",
            "provenance": "frozen project fixture evidence",
            "authority_class": "frozen-project-evidence",
            "claim": "J13 was selected only as a quality-valid DEMO fixture; J17 had one invalid geometry",
            "confidence": "exact",
            "conflicts": [],
            "identity": "sha256:a5b089f7b8fac0ca4b6959594c27bdfe4a9be478c2e965f513d63bacbf92463d",
        },
        {
            "evidence_id": "implementation-and-demo-boundary",
            "source": "src/nma/real_layer.py; data/specifications/nma-build-07-accepted-user-evaluation-v1.0.json",
            "version_date": "current BUILD-09 predecessor; BUILD-07 accepted record",
            "provenance": "implementation history and human DEMO evaluation, explicitly secondary",
            "authority_class": "implementation-evidence",
            "claim": "J17 runtime history and accepted DEMO choices cannot promote any official semantic or portrayal gate",
            "confidence": "exact-boundary",
            "conflicts": [],
            "identity": "demo-record:ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c",
        },
    ]


def _closure_basis(build09_contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "closure_version": CLOSURE_VERSION,
        "schema_version": CLOSURE_SCHEMA,
        "status": "evidence-hold",
        "created_on": "2026-08-21",
        "predecessor": {
            "build09_branch": "build/build-09-official-building-production-contract",
            "build09_commit": EXPECTED_BUILD09_COMMIT,
            "build09_contract_sha256": EXPECTED_BUILD09_CONTRACT_SHA256,
            "build09_contract_file_sha256": "87355baed4c8277218cafb4bf98114a2d24e8a706fc55540a24b445c60cc7112",
            "build08a_authorization_sha256": EXPECTED_BUILD08A_AUTHORIZATION_SHA256,
            "build08a_authorization_file_sha256": "a100ef01036207453992981d48c713a619b006c44f10e453cf3e69fcec6799ba",
            "build08_review_sha256": "b48337a6bb8cf1e6cffc54e0bbfe14383f62c1dcfdca54bf706c0ab045b42484",
            "build08_review_file_sha256": "be9ee241d358ba4c426ed7756345b899dffaa2e010f5f66abbe4b24ad7355b1b",
            "build07_record_sha256": "ea44212b1e3bc7e430bf77ac306f1a8d29896221152484f28c3f99ae4daf466c",
            "build07_record_file_sha256": "7b95e8130f4842310ef5c2ff6abb20d24211b803e5e2f412e4cce7ab245ed46d",
        },
        "evidence_policy": {
            "priority": [
                "original-official-specifications",
                "official-source-schema",
                "versioned-layer-definitions",
                "official-portrayal-and-legends",
                "official-code-tables",
                "authoritative-metadata",
                "tracked-source-package-documentation",
                "frozen-derived-project-evidence",
                "implementation-history",
                "demo-context",
            ],
            "authority_classes": list(AUTHORITY_CLASSES),
            "component_outcomes": list(COMPONENT_OUTCOMES),
            "readiness_states": list(READINESS_STATES),
            "demo_can_promote": False,
            "human_demo_acceptance_can_promote": False,
            "implementation_alone_can_promote": False,
            "silent_conflict_resolution_allowed": False,
        },
        "evidence_items": _evidence_items(),
        "j13_j17_closure": {
            "outcome": "indeterminate",
            "selected_layer_id": None,
            "authoritative_traces": [],
            "version_contracts": [],
            "source_package_finding": "J13 is the Baoshan urban-plan member and J17 is the Hsinchu Science Park special-plan (Baoshan portion) member; this establishes different geographic scopes, not different Building semantics or production precedence",
            "required_trace": list(TRACE_STEPS),
            "missing": "an authoritative versioned definition binding J13_BUILD and/or J17_BUILD through layer meaning, geometry, fields, dataset version, and the NMA production contract",
        },
        "annotation_closure": {
            "content": {
                "outcome": "officially-supported",
                "rule": "floor count followed by structure",
            },
            "field_binding": {
                "outcome": "documented-source-semantics",
                "rule": "{BUILD_NO}{BUILD_STR}",
                "scope": "112 multidimensional source package only",
            },
            "placement": {
                "outcome": "local-policy-required",
                "official_semantics": "center in or near the feature at an appropriate location; do not cover the feature; avoid mapped features, control points, and grid lines",
                "unofficial_detail": "exact anchor algorithm",
            },
            "collision_suppression": {
                "outcome": "local-policy-required",
                "official_semantics": "avoid interference with features and other annotations",
                "unofficial_detail": "priority, fit, and suppression algorithm",
            },
            "scale_visibility": {
                "outcome": "local-policy-required",
                "official_semantics": None,
                "unofficial_detail": "web zoom thresholds",
            },
            "formatting_order": {
                "outcome": "documented-source-semantics",
                "rule": "floor then structure; exact typography and separator remain local policy",
            },
        },
        "hatch_closure": {
            "spacing": {"outcome": "officially-supported", "value": 2.0, "unit": "mm"},
            "angle": {
                "outcome": "local-policy-required-with-official-diagonal-semantics",
                "value_degrees": None,
                "forbidden_inference": "diagonal does not establish 45 degrees",
            },
            "line_thickness": {
                "outcome": "indeterminate",
                "line_code": "2",
                "physical_unit_system": "mm",
                "value": None,
            },
            "color_relationship": {
                "outcome": "officially-supported",
                "color_code": "7",
                "device_independent_value": None,
            },
            "pattern_orientation": {
                "outcome": "officially-supported",
                "semantic": "diagonal rising from lower-left to upper-right",
                "numeric_angle": None,
            },
            "resource": {
                "outcome": "local-policy-required",
                "exact_asset_required": False,
                "allowed_form": "procedural-or-independently-reviewed-equivalent",
                "created_or_deployed": False,
            },
        },
        "line_color_closure": {
            "line_code_2": {
                "outcome": "indeterminate",
                "official_code": "2",
                "official_unit_system": "mm",
                "physical_width": None,
                "css_px": None,
            },
            "colour_code_7": {
                "outcome": "officially-supported",
                "official_code": "7",
                "official_value": None,
                "documented_named_context": "black",
                "rgb_hex": None,
            },
            "rendering_conversion": {
                "outcome": "local-policy-required",
                "documented_conversion_rule": None,
                "one_css_px_authorized": False,
                "number_111111_authorized": False,
                "physical_units_must_be_preserved": True,
            },
        },
        "polygonz_derived_xy_preservation": deepcopy(
            build09_contract["polygonz_derived_xy_contract"]
        ),
        "readiness": [
            {
                "gate_id": "hatch-angle-transcription",
                "state": "local-policy-required",
                "reason": "official 2 mm and diagonal semantics are closed; numeric angle and resource form are isolated local policies",
            },
            {
                "gate_id": "building-annotation-placement",
                "state": "local-policy-required",
                "reason": "content and source-package fields are supported; exact placement, collision, scale, and typography remain explicit local policies",
            },
            {
                "gate_id": "real-build-schema-binding",
                "state": "HOLD-indeterminate",
                "reason": "no authoritative trace selects or version-scopes J13/J17",
            },
            {
                "gate_id": "line-and-color-profile",
                "state": "HOLD-indeterminate",
                "reason": "official codes are established but the exact line-code-2 width and device-independent rendering profile are absent",
            },
            {
                "gate_id": "j13-polygonz-runtime-policy",
                "state": "P2-production-candidate",
                "reason": "BUILD-09 immutable PolygonZ and non-writing derived-XY contract is preserved byte-for-semantics",
            },
        ],
        "local_policy_required": [
            "numeric hatch angle consistent with official diagonal semantics",
            "procedural versus independently reviewed hatch resource",
            "annotation anchor, collision/suppression, scale visibility, separator, and typography",
            "physical-to-renderer conversion after an authoritative line-code-2 width is obtained",
            "device color choice only after an authorized output profile is approved",
        ],
        "missing_authoritative_evidence": [
            "versioned J13/J17 layer definition and NMA production binding",
            "exact physical width represented by line code 2",
            "device-independent value or authorized output-profile conversion for colour code 7",
        ],
        "conflicting_authoritative_evidence": [],
        "successor_production_contract": {
            "created": False,
            "sha256": None,
            "reason": "unresolved production semantics make a successor contract premature",
        },
        "build10_readiness_decision": "OFFICIAL-EVIDENCE-STILL-MISSING",
        "verdict": "PASS — EVIDENCE CLOSURE PARTIAL; OFFICIAL EVIDENCE STILL MISSING",
        "scope": {
            "production_runtime_modified": False,
            "source_data_or_geometry_modified": False,
            "hatch_asset_created": False,
            "successor_contract_created": False,
        },
        "source_mutation_policy": deepcopy(build09_contract["source_mutation_policy"]),
        "runtime_activation_policy": deepcopy(build09_contract["runtime_activation_policy"]),
        "next_stage_recommendation": "bounded continuation for only the J13/J17 authoritative trace, line-code-2 physical mapping, and colour-code-7 output-value/conversion evidence",
    }


def official_evidence_closure_sha256(record: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(record))
    basis.pop("official_evidence_closure_sha256", None)
    return canonical_sha256(basis)


def validate_layer_resolution(layer: Mapping[str, Any]) -> None:
    """Validate an indeterminate, single-layer, or version-scoped layer decision."""

    outcome = layer.get("outcome")
    if outcome not in LAYER_OUTCOMES:
        _fail("The J13/J17 outcome is unknown.", "layer_outcome_unknown")
    selected = layer.get("selected_layer_id")
    traces = layer.get("authoritative_traces", [])
    versions = layer.get("version_contracts", [])
    if outcome == "indeterminate":
        if selected is not None or traces or versions:
            _fail(
                "Indeterminate J13/J17 cannot select or imply authority.",
                "layer_selection_without_trace",
            )
        return
    if outcome in {
        "J13-authoritative-production-candidate",
        "J17-authoritative-production-candidate",
    }:
        expected = "J13_BUILD" if outcome.startswith("J13") else "J17_BUILD"
        if selected != expected or len(traces) != 1:
            _fail(
                "A selected layer requires exactly one complete authoritative trace.",
                "layer_selection_without_trace",
            )
        _validate_trace(traces[0])
        return
    if selected is not None or len(versions) < 2:
        _fail(
            "Dual or role-scoped outcomes require explicit contracts and no global selection.",
            "version_scope_incomplete",
        )
    for version in versions:
        if version.get("layer_id") not in {"J13_BUILD", "J17_BUILD"}:
            _fail("A version contract has an unknown layer.", "version_scope_incomplete")
        _validate_trace(version.get("authoritative_trace", {}))


def _validate_trace(trace: Mapping[str, Any]) -> None:
    if list(trace) != TRACE_STEPS or not all(trace.get(step) for step in TRACE_STEPS):
        _fail("The authoritative layer trace is incomplete.", "authoritative_trace_incomplete")
    if (
        trace.get("NMA-production-contract") == "demo"
        or trace.get("official-specification/version") in PROMOTION_DENIED_CLASSES
    ):
        _fail(
            "Secondary evidence cannot establish a production layer trace.",
            "secondary_evidence_promotion",
        )


def _validate_boundaries(record: Mapping[str, Any], build09_contract: Mapping[str, Any]) -> None:
    policy = record.get("evidence_policy", {})
    if policy.get("authority_classes") != AUTHORITY_CLASSES:
        _fail("Evidence authority classes changed or are unknown.", "authority_state_unknown")
    if (
        policy.get("component_outcomes") != COMPONENT_OUTCOMES
        or policy.get("readiness_states") != READINESS_STATES
    ):
        _fail("Evidence outcome or readiness states changed.", "authority_state_unknown")
    for item in record.get("evidence_items", []):
        authority = item.get("authority_class")
        if authority not in AUTHORITY_CLASSES:
            _fail("An evidence item has an unknown authority class.", "authority_state_unknown")
    for section in ("annotation_closure", "hatch_closure"):
        for component in record.get(section, {}).values():
            if component.get("outcome") not in COMPONENT_OUTCOMES:
                _fail("A component outcome is unknown.", "authority_state_unknown")
    for item in record.get("readiness", []):
        if item.get("state") not in READINESS_STATES:
            _fail("A readiness state is unknown.", "authority_state_unknown")
    validate_layer_resolution(record.get("j13_j17_closure", {}))
    if record.get("polygonz_derived_xy_preservation") != build09_contract.get(
        "polygonz_derived_xy_contract"
    ):
        _fail("The BUILD-09 PolygonZ/derived-XY P2 boundary changed.", "polygonz_boundary_changed")
    if record.get("source_mutation_policy") != build09_contract.get(
        "source_mutation_policy"
    ) or any(record.get("source_mutation_policy", {}).values()):
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
    line = record.get("line_color_closure", {})
    if line.get("line_code_2", {}).get("css_px") is not None:
        _fail(
            "Line code 2 cannot become CSS pixels without evidence.", "unsupported_line_conversion"
        )
    colour = line.get("colour_code_7", {})
    if colour.get("rgb_hex") is not None:
        _fail(
            "Colour code 7 cannot become RGB/HEX without evidence.", "unsupported_color_conversion"
        )
    angle = record.get("hatch_closure", {}).get("angle", {})
    if angle.get("value_degrees") is not None:
        _fail(
            "Diagonal semantics cannot become a numeric angle without evidence.",
            "unsupported_angle_conversion",
        )
    if (
        record.get("conflicting_authoritative_evidence")
        and record.get("build10_readiness_decision") != "AUTHORITY-CONFLICT-UNRESOLVED"
    ):
        _fail("Authoritative conflicts cannot resolve silently.", "authority_conflict_silenced")


def build_official_evidence_closure(
    build09_contract: Mapping[str, Any], build08a_authorization: Mapping[str, Any]
) -> dict[str, Any]:
    """Build the exact non-activating BUILD-09E evidence-closure record."""

    if (
        build09_contract.get("contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256
        or official_evidence_closure_input_sha256(build09_contract, "contract_sha256")
        != EXPECTED_BUILD09_CONTRACT_SHA256
    ):
        _fail("The BUILD-09 production contract identity changed.", "build09_identity_mismatch")
    if (
        build08a_authorization.get("authorization_sha256") != EXPECTED_BUILD08A_AUTHORIZATION_SHA256
        or official_evidence_closure_input_sha256(build08a_authorization, "authorization_sha256")
        != EXPECTED_BUILD08A_AUTHORIZATION_SHA256
    ):
        _fail("The BUILD-08A authorization identity changed.", "build08a_identity_mismatch")
    record = _closure_basis(build09_contract)
    record["official_evidence_closure_sha256"] = official_evidence_closure_sha256(record)
    return validate_official_evidence_closure(record, build09_contract, build08a_authorization)


def official_evidence_closure_input_sha256(value: Mapping[str, Any], identity_key: str) -> str:
    basis = deepcopy(dict(value))
    basis.pop(identity_key, None)
    return canonical_sha256(basis)


def validate_official_evidence_closure(
    record: Mapping[str, Any],
    build09_contract: Mapping[str, Any],
    build08a_authorization: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate BUILD-09E identity, evidence closure, and frozen boundaries."""

    if not isinstance(record, Mapping):
        _fail("The BUILD-09E record must be an object.", "record_invalid")
    if build09_contract.get("contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256:
        _fail("The BUILD-09 production contract identity changed.", "build09_identity_mismatch")
    if build08a_authorization.get("authorization_sha256") != EXPECTED_BUILD08A_AUTHORIZATION_SHA256:
        _fail("The BUILD-08A authorization identity changed.", "build08a_identity_mismatch")
    actual = deepcopy(dict(record))
    _validate_boundaries(actual, build09_contract)
    if actual.get("official_evidence_closure_sha256") != official_evidence_closure_sha256(actual):
        _fail("The BUILD-09E evidence identity is invalid.", "closure_hash_mismatch")
    expected = _closure_basis(build09_contract)
    expected["official_evidence_closure_sha256"] = official_evidence_closure_sha256(expected)
    if set(actual) != set(expected):
        _fail("The BUILD-09E record fields are not closed.", "record_fields_invalid")
    if actual != expected:
        _fail("The BUILD-09E evidence differs from the reviewed closure.", "record_mismatch")
    return actual


__all__ = [
    "AUTHORITY_CLASSES",
    "CLOSURE_SCHEMA",
    "CLOSURE_VERSION",
    "COMPONENT_OUTCOMES",
    "EXPECTED_BUILD08A_AUTHORIZATION_SHA256",
    "EXPECTED_BUILD09_COMMIT",
    "EXPECTED_BUILD09_CONTRACT_SHA256",
    "LAYER_OUTCOMES",
    "OfficialEvidenceClosureError",
    "READINESS_STATES",
    "TRACE_STEPS",
    "build_official_evidence_closure",
    "official_evidence_closure_sha256",
    "validate_layer_resolution",
    "validate_official_evidence_closure",
]

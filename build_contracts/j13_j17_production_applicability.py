"""BUILD-09E2 J13/J17 production-applicability evidence closure.

This module closes the official evidence search without selecting a production
layer.  It records that J13_BUILD and J17_BUILD are same-delivery Building
members in different geographic/project packages, while the official corpus
does not prescribe which member an NMA application must consume.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from nma.core import canonical_sha256


RESOLUTION_SCHEMA = "nma.building-j13-j17-production-applicability-resolution/1.0"
RESOLUTION_VERSION = "build-09e2/1.0"
SUCCESSOR_SCHEMA = "nma.building-human-policy-production-contract/1.0"
SUCCESSOR_VERSION = "build-09e2-successor/1.0"

EXPECTED_BUILD09E1_BRANCH = "build/build-09e1-targeted-official-binding-portrayal-resolution"
EXPECTED_BUILD09E1_COMMIT = "ee4bbc1bf4dc5d70032dcd3129801039f3813a36"
EXPECTED_BUILD09E1_RESOLUTION_SHA256 = (
    "f75c44bcb834090277588b3c23cfe48f00e965c947754497f64831d4b47b9b65"
)
EXPECTED_BUILD09_CONTRACT_SHA256 = (
    "0b9e0cc9c98274f9efcbed451905fa21857c33f0ec9472254fa6e3b803c24a0c"
)
EXPECTED_BUILD09E_CLOSURE_SHA256 = (
    "bfee262f17b5bc99ff8e55f6b284917cf5507aaa80b0e3bae2454e35da4fbaed"
)
EXPECTED_BUILD08A_AUTHORIZATION_SHA256 = (
    "4eedc443d4f1d5c0af36e696fc67fd0101f6936d78edba19d5c20d41ab2b8da8"
)

APPLICABILITY_OUTCOMES = [
    "J13-authoritative-production-binding",
    "J17-authoritative-production-binding",
    "version-scoped-dual-binding",
    "different-semantic-roles",
    "authoritative-applicability-boundary-not-published",
    "authoritative-evidence-unavailable",
    "indeterminate",
]
READINESS_DECISIONS = [
    "READY-FOR-BUILD-09F",
    "AUTHORITATIVE-EVIDENCE-ACQUISITION-REQUIRED",
    "J13-J17-AUTHORITY-STILL-INDETERMINATE",
]
VERDICTS = [
    "PASS — J13/J17 AUTHORITATIVE PRODUCTION BINDING RESOLVED; HUMAN POLICY GATE READY",
    "PASS — OFFICIAL J13/J17 APPLICABILITY BOUNDARY CLOSED; HUMAN PRODUCTION BINDING POLICY REQUIRED",
    "PASS — SPECIFIC AUTHORITATIVE EVIDENCE UNAVAILABLE; ACQUISITION REQUIRED",
    "PASS — J13/J17 AUTHORITY REMAINS INDETERMINATE",
    "FAIL — J13/J17 PRODUCTION APPLICABILITY BOUNDARY NOT ESTABLISHED",
]
GATE_STATES = [
    "P2-production-candidate",
    "version-scoped-production-candidate",
    "human-production-binding-policy-required",
    "evidence-HOLD",
    "local-policy-required",
    "local-output-profile-policy-required",
]
HYPOTHESIS_RESULTS = [
    "evidenced-differentiator",
    "not-supported-as-differentiator",
    "not-established",
    "not-applicable",
]
TRACE_EDGES = [
    "official_authority",
    "document_specification",
    "version_date",
    "dataset_product",
    "package",
    "geographic_product_scope",
    "layer_code",
    "official_layer_title",
    "geometry_type",
    "official_field_schema",
    "building_semantic_meaning",
    "production_applicability",
]
PROMOTION_DENIED_AUTHORITIES = {
    "implementation-evidence",
    "demo-evidence",
    "human-demo-evaluation",
}


class J13J17ProductionApplicabilityError(ValueError):
    """BUILD-09E2 rejected an identity, evidence, or safety boundary."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise J13J17ProductionApplicabilityError(message, code=code)


def _input_sha256(value: Mapping[str, Any], identity_key: str) -> str:
    basis = deepcopy(dict(value))
    basis.pop(identity_key, None)
    return canonical_sha256(basis)


def applicability_resolution_sha256(record: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(record))
    basis.pop("applicability_resolution_sha256", None)
    return canonical_sha256(basis)


def successor_contract_sha256(contract: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(contract))
    basis.pop("successor_contract_sha256", None)
    return canonical_sha256(basis)


def _edge(value: Any, *evidence_ids: str) -> dict[str, Any]:
    return {
        "status": "missing" if value is None else "established",
        "value": value,
        "evidence_ids": list(evidence_ids),
    }


def _member_trace(layer_id: str, package: str, scope: str) -> dict[str, Any]:
    archive_evidence = "official-112-multidimensional-shp-delivery"
    workbook_evidence = "official-v4-layer-workbook"
    return {
        "layer_id": layer_id,
        "authority_class": "authoritative-official-corpus",
        "trace": {
            "official_authority": _edge(
                "內政部國土測繪中心 (NLSC)", workbook_evidence, archive_evidence
            ),
            "document_specification": _edge("多維度繪製圖層V4.xlsx", workbook_evidence),
            "version_date": _edge(
                "V4; decision date 2023-11-10; source delivery year 112",
                workbook_evidence,
                archive_evidence,
            ),
            "dataset_product": _edge(
                "112年多維度SHP成果_0502; multidimensional spatial-information base-map delivery",
                archive_evidence,
            ),
            "package": _edge(package, archive_evidence),
            "geographic_product_scope": _edge(scope, archive_evidence),
            "layer_code": _edge(layer_id, archive_evidence),
            "official_layer_title": _edge(
                "(三)建物BUILD(面) — logical BUILD polygon title; no member-specific title is published",
                workbook_evidence,
                archive_evidence,
            ),
            "geometry_type": _edge(
                "official logical geometry 面 (polygon); delivered member geometry PolygonZ",
                workbook_evidence,
                archive_evidence,
            ),
            "official_field_schema": _edge(
                "BUILD_ID Text(16), TERRAINID Text(8), BUILD_STR Text(3), BUILD_NO Integer(3), BUILD_H Double(6,2), GROUP_ID LongInteger(16), MDATE Text(8)",
                workbook_evidence,
                archive_evidence,
            ),
            "building_semantic_meaning": _edge(
                "BUILD polygon carrier for permanent, under-construction, and temporary Building terrain classes 9310100/9310200/9310300",
                workbook_evidence,
                archive_evidence,
            ),
            "production_applicability": _edge(None),
        },
        "missing_edges": ["production_applicability"],
    }


def _evidence_items() -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": "build09e1-frozen-targeted-resolution",
            "authority_class": "frozen-reviewed-project-evidence",
            "source": "data/specifications/nma-build-09e1-golden-targeted-official-evidence-resolution-v1.0.json",
            "identity": "record:f75c44bcb834090277588b3c23cfe48f00e965c947754497f64831d4b47b9b65",
            "claim": "BUILD-09E1 froze line code 2 at 0.20 mm, colour code 7 at black/RGB (0,0,0), all earlier portrayal findings, and isolated J13/J17 applicability as the only authoritative evidence question",
        },
        {
            "evidence_id": "official-v4-layer-workbook",
            "authority_class": "authoritative-versioned-source-documentation",
            "source": "多維度繪製圖層V4.xlsx; Drive file 1C12PmP-8ZZtZbHVKRAKv0mmWE22kgzEw",
            "identity": "V4; decision-date:2023-11-10; drive-size:569257; drive-modified:2024-01-25T08:59:54.631Z; sha256:d3f065a57d10c306e9e4e686641c07ddf2fb5a6d3638b68ec4d3ea533839f308",
            "claim": "The original V4 workbook publishes logical BUILD geometry, fields, terrain classes, and semantics, and contains no J13_BUILD or J17_BUILD member binding",
        },
        {
            "evidence_id": "official-112-multidimensional-shp-delivery",
            "authority_class": "authoritative-source-delivery-metadata",
            "source": "data/datasets/112年多維度SHP成果_0502.zip",
            "identity": "sha256:4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
            "claim": "One delivery contains J13_BUILD under J13_寶山都市計畫 and J17_BUILD under J17_新竹科學工業園區特定區計畫(寶山部分); both are SHP PolygonZ members with the V4 BUILD field schema",
        },
        {
            "evidence_id": "build00a-j13-j17-quality-observations",
            "authority_class": "reviewed-project-evidence",
            "source": "data/specifications/nma-build-fixture-manifest-v1.0.json",
            "identity": "file-sha256:a5b089f7b8fac0ca4b6959594c27bdfe4a9be478c2e965f513d63bacbf92463d",
            "claim": "J13 DEMO selection was quality-bounded and J17 rejection reflected one invalid geometry; neither decision establishes official production applicability",
        },
        {
            "evidence_id": "legacy-j17-runtime-observation",
            "authority_class": "implementation-evidence",
            "source": "src/nma/real_layer.py",
            "identity": "file-sha256:d9eb720b5f84c35b63df8c9cd828a7530497d4b71f502117bdf7470148d890e9",
            "claim": "The legacy runtime names J17_BUILD, but implementation history cannot establish official applicability",
        },
    ]


def _hypotheses() -> list[dict[str, str]]:
    return [
        {
            "hypothesis": "specification-version",
            "result": "not-supported-as-differentiator",
            "reason": "both members are observed in one 112 delivery and governed by the same inspected V4 logical BUILD definition",
        },
        {
            "hypothesis": "source-dataset-version",
            "result": "not-supported-as-differentiator",
            "reason": "both member families occur in the same content-addressed archive",
        },
        {
            "hypothesis": "geographic-package",
            "result": "evidenced-differentiator",
            "reason": "J13 is the Baoshan urban-plan package and J17 is the Hsinchu Science Park special-plan (Baoshan portion) package",
        },
        {
            "hypothesis": "product-package",
            "result": "evidenced-differentiator",
            "reason": "the prefixes identify distinct official project/package members rather than alternative names for one global layer",
        },
        {
            "hypothesis": "scale-product-family",
            "result": "not-supported-as-differentiator",
            "reason": "no separate scale or product-family assignment is published for J13 versus J17 in the inspected corpus",
        },
        {
            "hypothesis": "delivery-format",
            "result": "not-supported-as-differentiator",
            "reason": "both are SHP PolygonZ members in the same delivery",
        },
        {
            "hypothesis": "semantic-role",
            "result": "not-supported-as-differentiator",
            "reason": "both carry the same BUILD schema and terrain-class semantics; similarity does not imply global equivalence",
        },
        {
            "hypothesis": "historical-schema-evolution",
            "result": "not-established",
            "reason": "no reviewed evidence assigns J13 or J17 to a historical schema transition",
        },
        {
            "hypothesis": "other-evidenced-boundary",
            "result": "not-applicable",
            "reason": "no additional deterministic boundary is published in the authorized corpus",
        },
    ]


def _resolution_basis(
    build09e1: Mapping[str, Any],
    build09e: Mapping[str, Any],
    build09: Mapping[str, Any],
) -> dict[str, Any]:
    frozen_e1_hashes = {
        "BUILD-09E1-Completion-Report.md": "41e0a092a26d5d5ca2029d0c707f06608b236262df02037e3f46f835463f050c",
        "build_contracts/targeted_official_evidence_resolution.py": "8c2644887e9d88c79e10f1a558297ab6cf1cf39d3ce6e7a18b9e3e6b9dfdf414",
        "data/specifications/nma-build-09e1-golden-targeted-official-evidence-resolution-v1.0.json": "bf49fbdbabd38d8913d7b37a706084850ab52b5fcbbb35cfa07ec686c4ed7232",
        "data/specifications/nma-build-09e1-successor-building-production-contract-candidate-v1.0.json": "bd790073ca7c9170c0d1e8445634d1d770e366f9ff4edf9c83ccda432feb5405",
        "schemas/building-targeted-official-evidence-resolution-v1.0.schema.json": "33deabc25c5e0d1da2e05ae8ecbb19e17703d657d17a761ae71b1aea720bbfd2",
        "schemas/building-successor-production-contract-candidate-v1.0.schema.json": "0edc1a84c8c3382a1cb35bdb554fe3cc20696b9bd209518c8d77d78c528b6674",
        "tests/test_targeted_official_evidence_resolution_build09e1.py": "c1d679fd2de2ba418cb72de31201619cb163810fcebfe6cccce5d6bfc6bc6203",
    }
    return {
        "contract_version": RESOLUTION_VERSION,
        "schema_version": RESOLUTION_SCHEMA,
        "status": "official-evidence-search-closed-human-policy-required",
        "created_on": "2026-08-21",
        "predecessor": {
            "build09e1_branch": EXPECTED_BUILD09E1_BRANCH,
            "build09e1_commit": EXPECTED_BUILD09E1_COMMIT,
            "build09e1_evidence_resolution_sha256": EXPECTED_BUILD09E1_RESOLUTION_SHA256,
            "build09_contract_sha256": EXPECTED_BUILD09_CONTRACT_SHA256,
            "build09e_evidence_closure_sha256": EXPECTED_BUILD09E_CLOSURE_SHA256,
            "build08a_authorization_sha256": EXPECTED_BUILD08A_AUTHORIZATION_SHA256,
            "frozen_build09e1_artifact_sha256": frozen_e1_hashes,
        },
        "closed_vocabularies": {
            "applicability_outcomes": list(APPLICABILITY_OUTCOMES),
            "readiness_decisions": list(READINESS_DECISIONS),
            "verdicts": list(VERDICTS),
            "gate_states": list(GATE_STATES),
            "hypothesis_results": list(HYPOTHESIS_RESULTS),
        },
        "evidence_items": _evidence_items(),
        "claim_separation": {
            "layer_existence": "established",
            "layer_semantics": "established-within-versioned-logical-BUILD-and-delivered-package-scope",
            "production_applicability": "not-published",
            "existence_implies_applicability": False,
            "semantic_similarity_implies_equivalence": False,
        },
        "j13_evidence_trace": _member_trace(
            "J13_BUILD", "J13_寶山都市計畫/SHP", "Baoshan urban-plan project area"
        ),
        "j17_evidence_trace": _member_trace(
            "J17_BUILD",
            "J17_新竹科學工業園區特定區計畫(寶山部分)/SHP",
            "Hsinchu Science Park special-plan project area (Baoshan portion)",
        ),
        "version_package_scope_hypotheses": _hypotheses(),
        "authoritative_applicability_resolution": {
            "outcome": "authoritative-applicability-boundary-not-published",
            "selected_layer_id": None,
            "selection_rule": None,
            "different_semantic_roles": None,
            "official_evidence_search_closed": True,
            "human_production_binding_policy_required": True,
            "additional_authoritative_evidence_acquisition_justified": False,
            "concrete_required_artifact": None,
            "reason": "the official corpus publishes a logical BUILD schema and distinct geographic package members but no application-level rule selecting J13_BUILD or J17_BUILD for NMA production",
        },
        "missing_edges": [
            "J13_BUILD -> NMA production applicability",
            "J17_BUILD -> NMA production applicability",
        ],
        "later_human_policy_shape": {
            "policy_value_selected": False,
            "allowed_choices": [
                "J13_BUILD for an explicitly supported source package/version",
                "J17_BUILD for an explicitly supported source package/version",
                "deterministic version/package/scope routing between J13_BUILD and J17_BUILD",
                "one supported production source package with all other packages rejected fail-closed",
            ],
        },
        "frozen_non_j13_j17_findings": {
            "annotation_closure": deepcopy(
                build09e1["frozen_build09e_results"]["annotation_closure"]
            ),
            "hatch_spacing": deepcopy(build09e1["frozen_build09e_results"]["hatch_spacing"]),
            "hatch_angle": deepcopy(build09e1["frozen_build09e_results"]["hatch_angle"]),
            "hatch_pattern_orientation": deepcopy(
                build09e1["frozen_build09e_results"]["hatch_pattern_orientation"]
            ),
            "hatch_resource": deepcopy(build09e1["frozen_build09e_results"]["hatch_resource"]),
            "line_code_2_resolution": deepcopy(build09e1["line_code_2_resolution"]),
            "colour_code_7_resolution": deepcopy(build09e1["colour_code_7_resolution"]),
            "output_profile_requirement": deepcopy(build09e1["output_profile_requirement"]),
            "polygonz_derived_xy": deepcopy(build09["polygonz_derived_xy_contract"]),
        },
        "five_gate_readiness": [
            {
                "gate_id": "hatch-angle-asset",
                "state": "local-policy-required",
                "reason": "official diagonal semantics and 2 mm spacing remain frozen; numeric angle and resource remain local",
            },
            {
                "gate_id": "annotation-placement-binding",
                "state": "local-policy-required",
                "reason": "official content semantics remain frozen; exact placement and collision behavior remain local",
            },
            {
                "gate_id": "j13-j17-identity",
                "state": "human-production-binding-policy-required",
                "reason": "the official applicability boundary is closed without an NMA application selection",
            },
            {
                "gate_id": "line-colour-portrayal",
                "state": "local-output-profile-policy-required",
                "reason": "official 0.20 mm and black RGB (0,0,0) are closed; output conversion remains local",
            },
            {
                "gate_id": "polygonz-derived-xy",
                "state": "P2-production-candidate",
                "reason": "immutable recoverable PolygonZ and non-writing derived XY remain frozen",
            },
        ],
        "build09f_readiness": "READY-FOR-BUILD-09F",
        "production_activation_status": "forbidden",
        "official_portrayal_activation_status": "forbidden",
        "source_mutation_status": "forbidden",
        "runtime_activation_policy": deepcopy(build09["runtime_activation_policy"]),
        "source_mutation_policy": deepcopy(build09["source_mutation_policy"]),
        "successor_production_contract": {
            "created": True,
            "path": "data/specifications/nma-build-09e2-successor-building-production-contract-v1.0.json",
            "status": "human-policy-hold",
            "reason": "human-production-binding-policy-required is now the only J13/J17 blocker",
        },
        "verdict": "PASS — OFFICIAL J13/J17 APPLICABILITY BOUNDARY CLOSED; HUMAN PRODUCTION BINDING POLICY REQUIRED",
        "next_stage_recommendation": "BUILD-09F — Human Building Production Policy Resolution; do not begin BUILD-10",
        "scope": {
            "production_runtime_modified": False,
            "production_behavior_implemented": False,
            "official_portrayal_activated": False,
            "source_data_or_geometry_modified": False,
            "source_z_removed": False,
            "portrayal_asset_created_or_deployed": False,
            "j13_j17_policy_value_selected": False,
        },
    }


def _validate_trace(value: Mapping[str, Any]) -> None:
    if set(value.get("trace", {})) != set(TRACE_EDGES):
        _fail("The J13/J17 evidence trace is incomplete.", "trace_incomplete")
    missing = set(value.get("missing_edges", []))
    for name, edge in value["trace"].items():
        if not isinstance(edge, Mapping) or edge.get("status") not in {"established", "missing"}:
            _fail("A trace edge has an unknown state.", "trace_invalid")
        if edge["status"] == "established":
            if edge.get("value") is None or not edge.get("evidence_ids") or name in missing:
                _fail("An established trace edge lacks evidence.", "trace_invalid")
        elif edge.get("value") is not None or edge.get("evidence_ids") or name not in missing:
            _fail("A missing trace edge was implicitly bridged.", "trace_invalid")


def validate_applicability_outcome(value: Mapping[str, Any]) -> None:
    outcome = value.get("outcome")
    if outcome not in APPLICABILITY_OUTCOMES:
        _fail("The applicability outcome is unknown.", "unknown_resolution_state")
    selected = value.get("selected_layer_id")
    traces = value.get("authoritative_binding_traces", [])
    if outcome in {
        "J13-authoritative-production-binding",
        "J17-authoritative-production-binding",
    }:
        expected = "J13_BUILD" if outcome.startswith("J13") else "J17_BUILD"
        if selected != expected or len(traces) != 1:
            _fail("A single binding needs one authoritative trace.", "binding_invalid")
    elif outcome in {"version-scoped-dual-binding", "different-semantic-roles"}:
        if selected is not None or {item.get("layer_id") for item in traces} != {
            "J13_BUILD",
            "J17_BUILD",
        }:
            _fail("A dual/role outcome needs both scoped traces.", "binding_invalid")
        if outcome == "version-scoped-dual-binding" and not value.get("selection_rule"):
            _fail("Dual binding needs a deterministic selection rule.", "selection_rule_missing")
        if outcome == "different-semantic-roles" and not value.get("semantic_distinction"):
            _fail("Different roles need an explicit distinction.", "semantic_distinction_missing")
    elif outcome == "authoritative-applicability-boundary-not-published":
        if selected is not None or value.get("selection_rule") is not None:
            _fail("The unpublished boundary cannot select policy.", "policy_value_selected")
        if value.get("official_evidence_search_closed") is not True:
            _fail("The unpublished boundary must close the official search.", "search_not_closed")
        if value.get("human_production_binding_policy_required") is not True:
            _fail("The unpublished boundary must require human policy.", "human_policy_missing")
        if value.get("additional_authoritative_evidence_acquisition_justified") is not False:
            _fail("A closed unpublished boundary cannot request acquisition.", "boundary_conflated")
        if value.get("concrete_required_artifact") is not None:
            _fail(
                "An unpublished boundary cannot invent a required artifact.", "boundary_conflated"
            )
    elif outcome == "authoritative-evidence-unavailable":
        if selected is not None or not value.get("concrete_required_artifact"):
            _fail("Unavailable evidence needs a concrete required artifact.", "artifact_missing")
        if value.get("official_evidence_search_closed") is not False:
            _fail("Unavailable evidence cannot close the search.", "boundary_conflated")
        if value.get("additional_authoritative_evidence_acquisition_justified") is not True:
            _fail("Unavailable evidence must justify acquisition.", "boundary_conflated")
    elif outcome == "indeterminate":
        if selected is not None or value.get("official_evidence_search_closed") is not False:
            _fail("Indeterminate authority cannot select or close.", "boundary_conflated")
    for trace in traces:
        if trace.get("authority_class") in PROMOTION_DENIED_AUTHORITIES:
            _fail("DEMO/runtime evidence cannot establish authority.", "secondary_binding")
        _validate_trace(trace)


def _validate_frozen(
    record: Mapping[str, Any], build09e1: Mapping[str, Any], build09: Mapping[str, Any]
) -> None:
    expected = {
        "annotation_closure": build09e1["frozen_build09e_results"]["annotation_closure"],
        "hatch_spacing": build09e1["frozen_build09e_results"]["hatch_spacing"],
        "hatch_angle": build09e1["frozen_build09e_results"]["hatch_angle"],
        "hatch_pattern_orientation": build09e1["frozen_build09e_results"][
            "hatch_pattern_orientation"
        ],
        "hatch_resource": build09e1["frozen_build09e_results"]["hatch_resource"],
        "line_code_2_resolution": build09e1["line_code_2_resolution"],
        "colour_code_7_resolution": build09e1["colour_code_7_resolution"],
        "output_profile_requirement": build09e1["output_profile_requirement"],
        "polygonz_derived_xy": build09["polygonz_derived_xy_contract"],
    }
    if record.get("frozen_non_j13_j17_findings") != expected:
        _fail("A frozen non-J13/J17 finding changed.", "frozen_finding_changed")
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


def _verify_inputs(
    build09e1: Mapping[str, Any],
    build09e: Mapping[str, Any],
    build09: Mapping[str, Any],
    build08a: Mapping[str, Any],
) -> None:
    checks = [
        (
            build09e1,
            "targeted_official_evidence_resolution_sha256",
            EXPECTED_BUILD09E1_RESOLUTION_SHA256,
            "build09e1_identity_mismatch",
        ),
        (
            build09e,
            "official_evidence_closure_sha256",
            EXPECTED_BUILD09E_CLOSURE_SHA256,
            "build09e_identity_mismatch",
        ),
        (build09, "contract_sha256", EXPECTED_BUILD09_CONTRACT_SHA256, "build09_identity_mismatch"),
        (
            build08a,
            "authorization_sha256",
            EXPECTED_BUILD08A_AUTHORIZATION_SHA256,
            "build08a_identity_mismatch",
        ),
    ]
    for artifact, key, expected, code in checks:
        if artifact.get(key) != expected or _input_sha256(artifact, key) != expected:
            _fail("A predecessor evidence identity changed.", code)


def build_applicability_resolution(
    build09e1: Mapping[str, Any],
    build09e: Mapping[str, Any],
    build09: Mapping[str, Any],
    build08a: Mapping[str, Any],
) -> dict[str, Any]:
    _verify_inputs(build09e1, build09e, build09, build08a)
    record = _resolution_basis(build09e1, build09e, build09)
    record["applicability_resolution_sha256"] = applicability_resolution_sha256(record)
    return validate_applicability_resolution(record, build09e1, build09e, build09, build08a)


def validate_applicability_resolution(
    record: Mapping[str, Any],
    build09e1: Mapping[str, Any],
    build09e: Mapping[str, Any],
    build09: Mapping[str, Any],
    build08a: Mapping[str, Any],
) -> dict[str, Any]:
    _verify_inputs(build09e1, build09e, build09, build08a)
    if not isinstance(record, Mapping):
        _fail("The BUILD-09E2 record must be an object.", "record_invalid")
    if record.get("closed_vocabularies") != {
        "applicability_outcomes": APPLICABILITY_OUTCOMES,
        "readiness_decisions": READINESS_DECISIONS,
        "verdicts": VERDICTS,
        "gate_states": GATE_STATES,
        "hypothesis_results": HYPOTHESIS_RESULTS,
    }:
        _fail("A closed vocabulary changed.", "unknown_resolution_state")
    _validate_trace(record.get("j13_evidence_trace", {}))
    _validate_trace(record.get("j17_evidence_trace", {}))
    validate_applicability_outcome(record.get("authoritative_applicability_resolution", {}))
    if record.get("build09f_readiness") not in READINESS_DECISIONS:
        _fail("The BUILD-09F readiness state is unknown.", "unknown_resolution_state")
    if record.get("verdict") not in VERDICTS:
        _fail("The verdict is unknown.", "unknown_resolution_state")
    if any(
        item.get("result") not in HYPOTHESIS_RESULTS
        for item in record.get("version_package_scope_hypotheses", [])
    ):
        _fail("A hypothesis result is unknown.", "unknown_resolution_state")
    _validate_frozen(record, build09e1, build09)
    if record.get("applicability_resolution_sha256") != applicability_resolution_sha256(record):
        _fail("The BUILD-09E2 record hash is invalid.", "resolution_hash_mismatch")
    expected = _resolution_basis(build09e1, build09e, build09)
    expected["applicability_resolution_sha256"] = applicability_resolution_sha256(expected)
    if dict(record) != expected:
        _fail("The BUILD-09E2 record differs from the reviewed resolution.", "record_mismatch")
    return deepcopy(dict(record))


def _successor_basis(
    resolution: Mapping[str, Any], build09e1: Mapping[str, Any], build09: Mapping[str, Any]
) -> dict[str, Any]:
    frozen = resolution["frozen_non_j13_j17_findings"]
    return {
        "contract_version": SUCCESSOR_VERSION,
        "schema_version": SUCCESSOR_SCHEMA,
        "status": "human-policy-hold",
        "created_on": "2026-08-21",
        "bindings": {
            "build09e1_predecessor_commit": EXPECTED_BUILD09E1_COMMIT,
            "build09e1_evidence_resolution_sha256": EXPECTED_BUILD09E1_RESOLUTION_SHA256,
            "build09_contract_sha256": EXPECTED_BUILD09_CONTRACT_SHA256,
            "build09e_evidence_closure_sha256": EXPECTED_BUILD09E_CLOSURE_SHA256,
            "build08a_authorization_sha256": EXPECTED_BUILD08A_AUTHORIZATION_SHA256,
            "build09e2_applicability_resolution_sha256": resolution[
                "applicability_resolution_sha256"
            ],
        },
        "production_binding_policy": {
            "state": "human-production-binding-policy-required",
            "selected_layer_id": None,
            "selection_rule": None,
            "policy_value_selected": False,
            "official_evidence_search_closed": True,
        },
        "remaining_authoritative_evidence_blockers": [],
        "human_policy_required_items": [
            "J13/J17 production binding for supported source version/package/scope",
            "numeric hatch angle within official diagonal semantics",
            "hatch resource or procedural implementation",
            "annotation placement and collision algorithm",
            "line 0.20 mm to MapLibre/device conversion",
            "official black RGB (0,0,0) to output-profile representation",
        ],
        "official_portrayal_semantics": {
            "annotation": deepcopy(frozen["annotation_closure"]),
            "hatch_spacing": deepcopy(frozen["hatch_spacing"]),
            "hatch_angle": deepcopy(frozen["hatch_angle"]),
            "hatch_resource": deepcopy(frozen["hatch_resource"]),
            "line_code_2": deepcopy(frozen["line_code_2_resolution"]),
            "colour_code_7": deepcopy(frozen["colour_code_7_resolution"]),
        },
        "output_profile_requirement": deepcopy(frozen["output_profile_requirement"]),
        "polygonz_derived_xy_contract": deepcopy(build09["polygonz_derived_xy_contract"]),
        "runtime_activation_policy": deepcopy(build09["runtime_activation_policy"]),
        "source_mutation_policy": deepcopy(build09["source_mutation_policy"]),
        "production_activation_forbidden": True,
        "official_portrayal_activation_forbidden": True,
        "next_stage": "BUILD-09F — Human Building Production Policy Resolution",
    }


def build_successor_contract(
    resolution: Mapping[str, Any], build09e1: Mapping[str, Any], build09: Mapping[str, Any]
) -> dict[str, Any]:
    if (
        build09e1.get("targeted_official_evidence_resolution_sha256")
        != EXPECTED_BUILD09E1_RESOLUTION_SHA256
        or _input_sha256(build09e1, "targeted_official_evidence_resolution_sha256")
        != EXPECTED_BUILD09E1_RESOLUTION_SHA256
    ):
        _fail("The BUILD-09E1 evidence binding is invalid.", "build09e1_identity_mismatch")
    if (
        build09.get("contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256
        or _input_sha256(build09, "contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256
    ):
        _fail("The BUILD-09 contract binding is invalid.", "build09_identity_mismatch")
    contract = _successor_basis(resolution, build09e1, build09)
    contract["successor_contract_sha256"] = successor_contract_sha256(contract)
    return validate_successor_contract(contract, resolution, build09e1, build09)


def validate_successor_contract(
    contract: Mapping[str, Any],
    resolution: Mapping[str, Any],
    build09e1: Mapping[str, Any],
    build09: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        build09e1.get("targeted_official_evidence_resolution_sha256")
        != EXPECTED_BUILD09E1_RESOLUTION_SHA256
        or _input_sha256(build09e1, "targeted_official_evidence_resolution_sha256")
        != EXPECTED_BUILD09E1_RESOLUTION_SHA256
    ):
        _fail("The BUILD-09E1 evidence binding is invalid.", "build09e1_identity_mismatch")
    if (
        build09.get("contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256
        or _input_sha256(build09, "contract_sha256") != EXPECTED_BUILD09_CONTRACT_SHA256
    ):
        _fail("The BUILD-09 contract binding is invalid.", "build09_identity_mismatch")
    if resolution.get("applicability_resolution_sha256") != applicability_resolution_sha256(
        resolution
    ):
        _fail("The BUILD-09E2 evidence binding is invalid.", "resolution_hash_mismatch")
    if contract.get("status") == "production-active":
        _fail("The successor cannot be production-active.", "activation_enabled")
    binding = contract.get("production_binding_policy", {})
    if binding.get("selected_layer_id") is not None or binding.get("selection_rule") is not None:
        _fail("BUILD-09E2 cannot select a human policy value.", "policy_value_selected")
    if contract.get("successor_contract_sha256") != successor_contract_sha256(contract):
        _fail("The successor hash is invalid.", "successor_hash_mismatch")
    expected = _successor_basis(resolution, build09e1, build09)
    expected["successor_contract_sha256"] = successor_contract_sha256(expected)
    if dict(contract) != expected:
        _fail("The successor differs from the reviewed contract.", "successor_mismatch")
    return deepcopy(dict(contract))


__all__ = [
    "APPLICABILITY_OUTCOMES",
    "EXPECTED_BUILD08A_AUTHORIZATION_SHA256",
    "EXPECTED_BUILD09E1_COMMIT",
    "EXPECTED_BUILD09E1_RESOLUTION_SHA256",
    "EXPECTED_BUILD09E_CLOSURE_SHA256",
    "EXPECTED_BUILD09_CONTRACT_SHA256",
    "GATE_STATES",
    "HYPOTHESIS_RESULTS",
    "J13J17ProductionApplicabilityError",
    "READINESS_DECISIONS",
    "TRACE_EDGES",
    "VERDICTS",
    "applicability_resolution_sha256",
    "build_applicability_resolution",
    "build_successor_contract",
    "successor_contract_sha256",
    "validate_applicability_outcome",
    "validate_applicability_resolution",
    "validate_successor_contract",
]

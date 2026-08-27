"""BUILD-03A human-approved, DEMO-scoped building gate resolutions.

The recorded choices close the five BUILD gates only for a derived DEMO
candidate.  They do not alter official evidence, grant production authority,
wire a runtime, or issue an execution capability.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from build_contracts.gate_review import validate_gate_review
from nma.core import canonical_sha256


RESOLUTION_SCHEMA = "nma.build-gate-resolution/1.0"
RESOLUTION_VERSION = "build-03a/1.0"
APPROVAL_DECISION = "approved-demo-scope-with-45-degree-adjustable-hatch"
EXPECTED_REVIEW_SHA256 = (
    "4177a2cc29738ad7b1bc6f00f2c10c724fec3c475e57dee45ad2e8e1f105cbdd"
)
EXPECTED_PROPOSAL_SHA256 = (
    "1e588ea2d7752ce7b02c28d6117c4deb1d6c8995dcbace14cfcb542eca847749"
)
EXPECTED_DECISION_SHA256 = (
    "624fafe1f84164f6f28396d21153a3ed0f9795ead87b6e9c605115b35ee3c846"
)
EXPECTED_BUILD01_PACKAGE_SHA256 = (
    "59b6f972046dbe9af295de414525230b03ed6da4f0e78374076b5cc4a2cdd7de"
)
EXPECTED_FIXTURE_ID = (
    "build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a"
)
EXPECTED_FEATURE_REFERENCE = (
    "build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f"
)

HUMAN_APPROVAL = {
    "actor_type": "human-project-owner",
    "decision": APPROVAL_DECISION,
    "recorded_on": "2026-08-20",
    "statement_zh_tw": (
        "核准 BUILD-03A 建議決議。剖面線角度先以45度，DEMO提供使用者調整，"
        "凡語意不清者，都是DEMO的項目。"
    ),
    "all_five_gate_decisions_explicit": True,
}

SCOPE_POLICY = {
    "target": "derived MapLibre web DEMO portrayal candidate",
    "ambiguous_semantics_are_demo_only": True,
    "demo_choices_are_official_source_facts": False,
    "demo_choices_are_production_authority": False,
    "user_adjustable_fields": ["hatch.numeric_angle_degrees"],
    "official_portrayal_baseline_mutated": False,
}

GATE_DECISIONS = [
    {
        "gate_id": "hatch-angle-transcription",
        "status": "resolved-for-demo-scope",
        "plain_language_zh_tw": (
            "官方圖只畫出左下往右上的斜線，沒有記載可直接轉錄的數字角度。"
        ),
        "recommended_resolution_zh_tw": (
            "保留左下往右上的語意方向，不把未記載的數字角度當成官方事實。"
        ),
        "approved_resolution_zh_tw": (
            "DEMO先以45度呈現並允許使用者調整；45度是DEMO預設值，不是官方來源事實。"
        ),
        "evidence_boundary": "human-approved-demo-default-not-source-transcription",
    },
    {
        "gate_id": "building-annotation-placement",
        "status": "resolved-for-demo-scope",
        "plain_language_zh_tw": (
            "規則要求顯示樓層與結構，但沒有說明文字位置及碰撞時的處理方式。"
        ),
        "recommended_resolution_zh_tw": (
            "使用建物內部最佳點；文字放不下或與較高優先標註碰撞時隱藏，不移到建物外。"
        ),
        "approved_resolution_zh_tw": (
            "依建議作為DEMO配置；這項不明確的配置不得成為正式生產規則。"
        ),
        "evidence_boundary": "human-approved-demo-placement-not-official-policy",
    },
    {
        "gate_id": "real-build-schema-binding",
        "status": "resolved-for-demo-scope",
        "plain_language_zh_tw": (
            "實際J13資料有BUILD_NO與BUILD_STR，但文件的簡化欄位描述不同。"
        ),
        "recommended_resolution_zh_tw": (
            "只使用J13的BUILD_NO與BUILD_STR產生註記，不宣稱與文件ID或SOURCE全域等價。"
        ),
        "approved_resolution_zh_tw": "依建議核准，且權限只限已驗證的J13 DEMO資料範圍。",
        "evidence_boundary": "j13-bounded-fields-no-global-schema-equivalence",
    },
    {
        "gate_id": "line-and-color-profile",
        "status": "resolved-for-demo-scope",
        "plain_language_zh_tw": (
            "官方只給線型代碼2與顏色代碼7，沒有提供網頁顯示所需的實際寬度與色值。"
        ),
        "recommended_resolution_zh_tw": (
            "DEMO採MapLibre web設定：1 CSS px實線、#111111、完全不透明；2 mm間距按96 CSS px/in換算。"
        ),
        "approved_resolution_zh_tw": (
            "依建議作為DEMO顯示設定；不得回寫為官方線型或顏色定義。"
        ),
        "evidence_boundary": "human-approved-demo-profile-not-official-code-definition",
    },
    {
        "gate_id": "j13-polygonz-runtime-policy",
        "status": "resolved-for-demo-scope",
        "plain_language_zh_tw": (
            "來源建物是含Z值的PolygonZ，但現有MapLibre顯示路徑是二維。"
        ),
        "recommended_resolution_zh_tw": (
            "來源與正式證據保留PolygonZ；只有衍生DEMO視圖使用XY，且不得回寫、修復或改變來源。"
        ),
        "approved_resolution_zh_tw": "依建議核准，XY使用僅限衍生DEMO顯示邊界。",
        "evidence_boundary": "source-polygonz-preserved-demo-view-xy-only",
    },
]

RESOLVED_DEMO_PORTRAYAL = {
    "representation_kind": "feature-following-hatched-polygon",
    "geometry_policy": {
        "source_geometry_type": "PolygonZ",
        "authoritative_z_preserved": True,
        "demo_view_dimensions": "XY",
        "demo_xy_projection_writes_back": False,
        "source_z_dimension_drop_authorized": False,
        "geometry_repair_authorized": False,
    },
    "boundary_profile": {
        "profile_id": "nma-maplibre-web-demo-v1",
        "line_code": "2",
        "style": "solid",
        "width_css_px": 1.0,
        "color_code": "7",
        "color_hex": "#111111",
        "opacity": 1.0,
        "demo_only": True,
    },
    "hatch": {
        "orientation_semantic": "diagonal rising from lower-left to upper-right",
        "numeric_angle_degrees": 45.0,
        "angle_user_adjustable": True,
        "spacing_mm": 2.0,
        "spacing_css_px": "7.559055118110236",
        "conversion_policy": "96-css-px-per-inch/25.4-mm-per-inch",
        "demo_only": True,
    },
    "annotation": {
        "content_fields": ["BUILD_NO", "BUILD_STR"],
        "format": "{BUILD_NO}{BUILD_STR}",
        "anchor_policy": "polygon-pole-of-inaccessibility",
        "collision_policy": "suppress-if-no-interior-fit-or-higher-priority-collision",
        "outside_displacement_allowed": False,
        "demo_only": True,
    },
    "schema_binding": {
        "layer_id": "J13_BUILD",
        "feature_code": "9310100",
        "annotation_fields": ["BUILD_NO", "BUILD_STR"],
        "id_source_global_equivalence_asserted": False,
        "other_layer_authority_inherited": False,
        "demo_only": True,
    },
}

RESOLUTION_EFFECT = {
    "all_gates_resolved_for_demo_scope": True,
    "production_gates_resolved": False,
    "demo_candidate_eligible_for_later_authorization": True,
    "execution_authorization_issued": False,
}

EXPECTED_BOUNDARIES = {
    "execution_allowed": False,
    "runtime_wiring_allowed": False,
    "source_mutation_allowed": False,
    "geometry_repair_allowed": False,
    "source_z_dimension_drop_allowed": False,
    "production_activation_allowed": False,
    "raw_source_disclosure_allowed": False,
    "redistribution_allowed": False,
    "demo_policy_promotion_allowed": False,
}


class BuildGateResolutionError(ValueError):
    """BUILD-03A rejected an invalid resolution or authority expansion."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str) -> None:
    raise BuildGateResolutionError(message, code=code)


def _exact(value: Any, expected: Any, *, label: str, code: str) -> None:
    if value != expected:
        _fail(f"{label} does not match the frozen BUILD-03A decision.", code)


def _bindings() -> dict[str, Any]:
    return {
        "review_sha256": EXPECTED_REVIEW_SHA256,
        "proposal_sha256": EXPECTED_PROPOSAL_SHA256,
        "decision_sha256": EXPECTED_DECISION_SHA256,
        "build01_package_sha256": EXPECTED_BUILD01_PACKAGE_SHA256,
        "fixture_id": EXPECTED_FIXTURE_ID,
        "feature_reference": EXPECTED_FEATURE_REFERENCE,
    }


def _resolution_template() -> dict[str, Any]:
    return {
        "resolution_version": RESOLUTION_VERSION,
        "schema_version": RESOLUTION_SCHEMA,
        "bindings": _bindings(),
        "human_approval": deepcopy(HUMAN_APPROVAL),
        "scope_policy": deepcopy(SCOPE_POLICY),
        "gate_decisions": deepcopy(GATE_DECISIONS),
        "resolved_demo_portrayal": deepcopy(RESOLVED_DEMO_PORTRAYAL),
        "resolution_effect": deepcopy(RESOLUTION_EFFECT),
        "boundaries": deepcopy(EXPECTED_BOUNDARIES),
    }


def resolution_sha256(resolution: Mapping[str, Any]) -> str:
    basis = deepcopy(dict(resolution))
    basis.pop("resolution_sha256", None)
    return canonical_sha256(basis)


def _validate_predecessors(
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> None:
    validate_gate_review(review, proposal, decision)
    _exact(
        review.get("review_sha256"),
        EXPECTED_REVIEW_SHA256,
        label="BUILD-03 review identity",
        code="review_hash_mismatch",
    )


def validate_gate_resolution(
    resolution: Mapping[str, Any],
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the exact human-approved DEMO resolution and no-authority effect."""

    _validate_predecessors(review, proposal, decision)
    if not isinstance(resolution, Mapping):
        _fail("The BUILD-03A resolution must be an object.", "resolution_invalid")
    expected = _resolution_template()
    expected["resolution_sha256"] = resolution_sha256(expected)
    if set(resolution) != set(expected):
        _fail(
            "The BUILD-03A resolution fields are not closed.",
            "resolution_schema_invalid",
        )
    for field, value in expected.items():
        _exact(
            resolution.get(field),
            value,
            label=f"Resolution field {field}",
            code="resolution_invalid",
        )
    if resolution.get("resolution_sha256") != resolution_sha256(resolution):
        _fail("The BUILD-03A resolution hash is invalid.", "resolution_hash_mismatch")
    return deepcopy(dict(resolution))


def prepare_build_gate_resolution(
    review: Mapping[str, Any],
    proposal: Mapping[str, Any],
    decision: Mapping[str, Any],
    human_decision: str | None,
) -> dict[str, Any] | None:
    """Record the approved DEMO policies without issuing execution authority."""

    _validate_predecessors(review, proposal, decision)
    if human_decision is None:
        return None
    if human_decision != APPROVAL_DECISION:
        _fail(
            "The exact DEMO-scoped human decision is required.",
            "decision_scope_mismatch",
        )
    resolution = _resolution_template()
    resolution["resolution_sha256"] = resolution_sha256(resolution)
    return validate_gate_resolution(resolution, review, proposal, decision)


__all__ = [
    "APPROVAL_DECISION",
    "BuildGateResolutionError",
    "EXPECTED_BOUNDARIES",
    "GATE_DECISIONS",
    "HUMAN_APPROVAL",
    "RESOLVED_DEMO_PORTRAYAL",
    "SCOPE_POLICY",
    "prepare_build_gate_resolution",
    "resolution_sha256",
    "validate_gate_resolution",
]

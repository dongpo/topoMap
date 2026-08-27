from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from nma.road_approval import (
    EXPECTED_DECISION_SHA256,
    EXPECTED_PROPOSAL_SHA256,
    RESTRICTED_PERMISSIONS,
    RoadApprovalError,
    approval_sha256,
    authorization_sha256,
    authorize_road_portrayal,
    validate_approval,
    validate_authorization,
)
from nma.road_portrayal_decision import (
    DERIVED_TARGET,
    EXPECTED_ARCHIVE_SHA256,
    EXPECTED_EVIDENCE_IDS,
    EXPECTED_FIXTURE_SHA256,
    EXPECTED_PORTRAYAL,
    EXPECTED_ROUTE_IDENTITY,
    EXPECTED_SOURCE_IDS,
    EXPECTED_UPSTREAM_PACKAGE_SHA256,
    RoadPortrayalDecisionError,
    decision_sha256,
    proposal_sha256,
)
import nma.road_approval as road03


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def decision() -> dict[str, Any]:
    return json.loads(
        (
            ROOT / "data/specifications/nma-road-hero-road-02-golden-decision-v1.0.json"
        ).read_text(encoding="utf-8")
    )


@pytest.fixture()
def proposal() -> dict[str, Any]:
    return json.loads(
        (
            ROOT / "data/specifications/nma-road-hero-road-02-golden-proposal-v1.0.json"
        ).read_text(encoding="utf-8")
    )


def _fails(call: Callable[[], Any]) -> ValueError:
    with pytest.raises((RoadApprovalError, RoadPortrayalDecisionError)) as caught:
        call()
    return caught.value


def _golden(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    approval, authorization = authorize_road_portrayal(proposal, decision, "approved")
    assert approval is not None
    assert authorization is not None
    return approval, authorization


def _rehash_approval(value: dict[str, Any]) -> dict[str, Any]:
    value["approval_sha256"] = approval_sha256(value)
    return value


def _rehash_authorization(value: dict[str, Any]) -> dict[str, Any]:
    value["authorization_sha256"] = authorization_sha256(value)
    return value


def test_at01_at02_frozen_proposal_and_decision_validation(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    approval, authorization = _golden(proposal, decision)
    assert proposal["proposal_sha256"] == EXPECTED_PROPOSAL_SHA256
    assert decision["decision_sha256"] == EXPECTED_DECISION_SHA256
    validate_approval(approval, proposal, decision)
    validate_authorization(authorization, approval, proposal, decision)

    changed_proposal = deepcopy(proposal)
    changed_proposal["proposal"]["requested_changes"]["road_name_annotation"] = "中山路"
    changed_proposal["proposal_sha256"] = proposal_sha256(changed_proposal)
    _fails(lambda: authorize_road_portrayal(changed_proposal, decision, "approved"))

    changed_decision = deepcopy(decision)
    changed_decision["decision"]["road_name"] = "中山路"
    changed_decision["decision_sha256"] = decision_sha256(changed_decision)
    _fails(lambda: authorize_road_portrayal(proposal, changed_decision, "approved"))


def test_at03_golden_human_approval_binds_complete_scope(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    approval, _ = _golden(proposal, decision)
    assert approval["human_decision"] == "approved"
    assert approval["actor_type"] == "human"
    assert approval["bindings"] == {
        "proposal_sha256": EXPECTED_PROPOSAL_SHA256,
        "decision_sha256": EXPECTED_DECISION_SHA256,
        "road01_package_sha256": EXPECTED_UPSTREAM_PACKAGE_SHA256,
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "fixture_sha256": EXPECTED_FIXTURE_SHA256,
        "ordered_source_ids": list(EXPECTED_SOURCE_IDS),
        "route_identity": EXPECTED_ROUTE_IDENTITY,
        "class_code": "9420400",
        "evidence_ids": list(EXPECTED_EVIDENCE_IDS),
        "requested_portrayal": EXPECTED_PORTRAYAL,
        "execution_target": DERIVED_TARGET,
    }


def test_at04_at05_rejection_and_missing_approval_never_authorize(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    rejection, authorization = authorize_road_portrayal(proposal, decision, "rejected")
    assert rejection is not None
    assert rejection["authorization_effect"] == {
        "execution_authorization_eligible": False,
        "execution_authorization_denied": True,
    }
    assert authorization is None
    assert authorize_road_portrayal(proposal, decision, None) == (None, None)
    _fails(lambda: authorize_road_portrayal(proposal, decision, "yes"))


def test_at06_golden_authorization_is_a_restricted_capability_grant(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    approval, authorization = _golden(proposal, decision)
    assert authorization["approval_sha256"] == approval["approval_sha256"]
    assert authorization["capability"] == {
        "execution_allowed": True,
        "execution_target": DERIVED_TARGET,
        "allowed_changes": EXPECTED_PORTRAYAL,
    }
    assert authorization["permissions"] == RESTRICTED_PERMISSIONS


def test_at07_proposal_hash_is_non_transferable(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    approval, authorization = _golden(proposal, decision)
    changed = deepcopy(proposal)
    changed["proposal"]["action"] += " changed"
    changed["proposal_sha256"] = proposal_sha256(changed)
    _fails(lambda: validate_approval(approval, changed, decision))
    _fails(lambda: validate_authorization(authorization, approval, changed, decision))


@pytest.mark.parametrize(
    ("binding", "expected"),
    [
        ("road01_package_sha256", EXPECTED_UPSTREAM_PACKAGE_SHA256),
        ("source_archive_sha256", EXPECTED_ARCHIVE_SHA256),
        ("fixture_sha256", EXPECTED_FIXTURE_SHA256),
    ],
)
def test_at08_through_at10_integrity_bindings_fail_closed(
    proposal: dict[str, Any],
    decision: dict[str, Any],
    binding: str,
    expected: str,
) -> None:
    approval, _ = _golden(proposal, decision)
    assert approval["bindings"][binding] == expected
    changed = deepcopy(approval)
    changed["bindings"][binding] = "0" * 64
    _rehash_approval(changed)
    _fails(lambda: validate_approval(changed, proposal, decision))


@pytest.mark.parametrize("change", ["missing", "extra", "replacement", "reorder"])
def test_at11_ordered_source_scope_fails_closed(
    proposal: dict[str, Any], decision: dict[str, Any], change: str
) -> None:
    approval, _ = _golden(proposal, decision)
    changed = deepcopy(approval)
    ids = changed["bindings"]["ordered_source_ids"]
    if change == "missing":
        ids.pop()
    elif change == "extra":
        ids.append("K0000009999")
    elif change == "replacement":
        ids[1] = "K0000009999"
    else:
        ids.reverse()
    _rehash_approval(changed)
    _fails(lambda: validate_approval(changed, proposal, decision))


@pytest.mark.parametrize(
    ("binding", "value"),
    [
        ("route_identity", "ROADNUM=縣127|ROADNUM1=|ROADNUM2=|ROADNAME=中山街"),
        ("class_code", "9420300"),
    ],
)
def test_at12_at13_route_and_class_bindings_fail_closed(
    proposal: dict[str, Any], decision: dict[str, Any], binding: str, value: str
) -> None:
    approval, _ = _golden(proposal, decision)
    changed = deepcopy(approval)
    changed["bindings"][binding] = value
    _rehash_approval(changed)
    _fails(lambda: validate_approval(changed, proposal, decision))


@pytest.mark.parametrize("change", ["remove", "substitute", "add"])
def test_at14_evidence_binding_cannot_expand_authority(
    proposal: dict[str, Any], decision: dict[str, Any], change: str
) -> None:
    approval, _ = _golden(proposal, decision)
    changed = deepcopy(approval)
    evidence = changed["bindings"]["evidence_ids"]
    if change == "remove":
        evidence.pop()
    elif change == "substitute":
        evidence[-1] = "UNREVIEWED-EVIDENCE"
    else:
        evidence.append("UNRELATED-EXECUTABLE-EVIDENCE")
    _rehash_approval(changed)
    _fails(lambda: validate_approval(changed, proposal, decision))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("shield_code", "9490004"),
        ("shield_orientation", "north-up"),
        ("road_name_annotation", "中山路"),
        ("graphic_element_roles", [2]),
    ],
)
def test_at15_portrayal_binding_fails_closed(
    proposal: dict[str, Any], decision: dict[str, Any], field: str, value: Any
) -> None:
    approval, authorization = _golden(proposal, decision)
    changed_approval = deepcopy(approval)
    changed_approval["bindings"]["requested_portrayal"][field] = value
    _rehash_approval(changed_approval)
    _fails(lambda: validate_approval(changed_approval, proposal, decision))

    changed_authorization = deepcopy(authorization)
    changed_authorization["capability"]["allowed_changes"][field] = value
    _rehash_authorization(changed_authorization)
    _fails(
        lambda: validate_authorization(
            changed_authorization, approval, proposal, decision
        )
    )


@pytest.mark.parametrize(
    "target",
    ["authoritative ROAD", "ROADA", "MapLibre runtime directly", "road-edge geometry"],
)
def test_at16_execution_target_is_closed(
    proposal: dict[str, Any], decision: dict[str, Any], target: str
) -> None:
    approval, authorization = _golden(proposal, decision)
    changed = deepcopy(authorization)
    changed["capability"]["execution_target"] = target
    _rehash_authorization(changed)
    _fails(lambda: validate_authorization(changed, approval, proposal, decision))


@pytest.mark.parametrize(
    "permission",
    [
        "source_mutation_allowed",
        "topology_repair_allowed",
        "roada_execution_allowed",
        "road_edge_derivation_allowed",
    ],
)
def test_at17_through_at20_permission_escalation_fails_closed(
    proposal: dict[str, Any], decision: dict[str, Any], permission: str
) -> None:
    approval, authorization = _golden(proposal, decision)
    changed = deepcopy(authorization)
    changed["permissions"][permission] = True
    _rehash_authorization(changed)
    _fails(lambda: validate_authorization(changed, approval, proposal, decision))


@pytest.mark.parametrize(
    "operation",
    ["buffer ROAD", "derive width", "polygonize road", "generate carriageway edge"],
)
def test_at20_road_edge_operation_requests_fail_closed(
    proposal: dict[str, Any], decision: dict[str, Any], operation: str
) -> None:
    approval, authorization = _golden(proposal, decision)
    changed = deepcopy(authorization)
    changed["capability"]["allowed_changes"][operation] = True
    _rehash_authorization(changed)
    _fails(lambda: validate_authorization(changed, approval, proposal, decision))


def test_at21_runtime_guard_has_no_runtime_result(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    _, authorization = _golden(proposal, decision)
    serialized = json.dumps(authorization, ensure_ascii=False).casefold()
    for forbidden in ["runtime layer", "rendered", "coordinates", "placement_result"]:
        assert forbidden not in serialized


def test_at22_approval_schema_and_golden_artifacts(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    approval, _ = _golden(proposal, decision)
    rejection, _ = authorize_road_portrayal(proposal, decision, "rejected")
    schema = json.loads(
        (ROOT / "schemas/road-approval-v1.0.schema.json").read_text(encoding="utf-8")
    )
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(approval)
    assert rejection is not None and set(schema["required"]) == set(rejection)
    frozen_rejection = json.loads(
        (
            ROOT / "data/specifications/nma-road-hero-road-03-golden-rejection-v1.0.json"
        ).read_text(encoding="utf-8")
    )
    assert rejection == frozen_rejection
    missing = deepcopy(approval)
    missing["bindings"].pop("proposal_sha256")
    _rehash_approval(missing)
    _fails(lambda: validate_approval(missing, proposal, decision))


@pytest.mark.parametrize(
    ("container", "field"),
    [
        (None, "approval_sha256"),
        ("bindings", "proposal_sha256"),
        ("bindings", "fixture_sha256"),
        ("bindings", "ordered_source_ids"),
        (None, "permissions"),
    ],
)
def test_at23_authorization_schema_required_bindings(
    proposal: dict[str, Any],
    decision: dict[str, Any],
    container: str | None,
    field: str,
) -> None:
    approval, authorization = _golden(proposal, decision)
    schema = json.loads(
        (
            ROOT / "schemas/road-execution-authorization-v1.0.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    changed = deepcopy(authorization)
    if container is None:
        changed.pop(field)
    else:
        changed[container].pop(field)
    if "authorization_sha256" in changed:
        _rehash_authorization(changed)
    _fails(lambda: validate_authorization(changed, approval, proposal, decision))


def test_at24_at25_approval_and_authorization_are_deterministic(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    first = _golden(proposal, decision)
    second = _golden(proposal, decision)
    assert first == second
    assert first[0]["approval_sha256"] == approval_sha256(first[0])
    assert first[1]["authorization_sha256"] == authorization_sha256(first[1])


def test_at26_rejection_identity_is_deterministic(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    first = authorize_road_portrayal(proposal, decision, "rejected")
    second = authorize_road_portrayal(proposal, decision, "rejected")
    assert first == second
    assert first[0] is not None and first[0]["approval_sha256"] == approval_sha256(first[0])
    assert first[1] is None


@pytest.mark.parametrize("change", ["source", "route", "evidence", "portrayal", "fixture"])
def test_at27_approval_non_transferability(
    proposal: dict[str, Any],
    decision: dict[str, Any],
    change: str,
) -> None:
    approval, _ = _golden(proposal, decision)
    changed = deepcopy(proposal)
    if change == "source":
        changed["bindings"]["ordered_source_ids"] = ["K0000004671"]
    elif change == "route":
        changed["bindings"]["route_identity"] = "changed-route"
    elif change == "evidence":
        changed["bindings"]["evidence_ids"] = ["changed-evidence"]
    elif change == "portrayal":
        changed["proposal"]["requested_changes"]["shield_code"] = "changed"
    else:
        changed["bindings"]["fixture_sha256"] = "0" * 64
    changed["proposal_sha256"] = proposal_sha256(changed)
    _fails(lambda: validate_approval(approval, changed, decision))


def test_at28_authorization_non_transferability(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    approval, authorization = _golden(proposal, decision)
    altered = deepcopy(proposal)
    altered["proposal"]["requested_changes"]["shield_code"] = "9490004"
    altered["proposal_sha256"] = proposal_sha256(altered)
    _fails(lambda: validate_authorization(authorization, approval, altered, decision))


def test_at29_authorization_is_not_an_execution_result(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    _, authorization = _golden(proposal, decision)
    serialized = json.dumps(authorization, ensure_ascii=False).casefold()
    for forbidden in [
        "execution_status",
        "runtime_result",
        "output_layer",
        "rendered_artifact",
        "receipt",
        "rollback_manifest",
    ]:
        assert forbidden not in serialized


def test_golden_artifacts_match_frozen_files(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    approval, authorization = _golden(proposal, decision)
    frozen_approval = json.loads(
        (
            ROOT / "data/specifications/nma-road-hero-road-03-golden-approval-v1.0.json"
        ).read_text(encoding="utf-8")
    )
    frozen_authorization = json.loads(
        (
            ROOT
            / "data/specifications/nma-road-hero-road-03-golden-authorization-v1.0.json"
        ).read_text(encoding="utf-8")
    )
    assert approval == frozen_approval
    assert authorization == frozen_authorization


def test_at33_scope_guard_is_capability_only() -> None:
    source = inspect.getsource(road03).casefold()
    assert "subprocess" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "shapely" not in source
    assert ".write_" not in source
    assert "open(" not in source
    assert "buffer(" not in source
    assert "polygonize(" not in source

from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path
import re
from typing import Any, Mapping

import pytest

from nma.road_portrayal_decision import (
    ACTION,
    DERIVED_TARGET,
    EXPECTED_ARCHIVE_SHA256,
    EXPECTED_BOUNDARIES,
    EXPECTED_EVIDENCE_IDS,
    EXPECTED_FIXTURE_SHA256,
    EXPECTED_PORTRAYAL,
    EXPECTED_ROUTE_IDENTITY,
    EXPECTED_SOURCE_IDS,
    EXPECTED_UPSTREAM_PACKAGE_SHA256,
    RoadPortrayalDecisionError,
    decision_sha256,
    prepare_road_portrayal,
    proposal_sha256,
    validate_decision,
    validate_proposal,
)
from nma.road_resolution import resolve_road_request
import nma.road_portrayal_decision as road02


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_REQUEST = (
    "Resolve County Highway 126 / 中山街 in the reviewed K14 road dataset and prepare "
    "the evidence-grounded road portrayal package for the exact contiguous source segment set."
)


@pytest.fixture()
def upstream() -> dict[str, Any]:
    return resolve_road_request(GOLDEN_REQUEST)


def _fails(callable_) -> RoadPortrayalDecisionError:
    with pytest.raises(RoadPortrayalDecisionError) as caught:
        callable_()
    return caught.value


def _assert_schema(value: Any, schema: Mapping[str, Any], root: Mapping[str, Any]) -> None:
    if "$ref" in schema:
        reference = schema["$ref"]
        assert reference.startswith("#/$defs/")
        _assert_schema(value, root["$defs"][reference.rsplit("/", 1)[1]], root)
        return
    if "const" in schema:
        assert value == schema["const"]
    value_type = schema.get("type")
    if value_type == "object":
        assert isinstance(value, dict)
        properties = schema.get("properties", {})
        assert set(schema.get("required", [])) <= set(value)
        if schema.get("additionalProperties") is False:
            assert set(value) <= set(properties)
        for key, child in properties.items():
            if key in value:
                _assert_schema(value[key], child, root)
    elif value_type == "string":
        assert isinstance(value, str)
        if "pattern" in schema:
            assert re.fullmatch(schema["pattern"], value)


def test_at01_at02_golden_input_generates_exact_decision(upstream: dict[str, Any]) -> None:
    decision, proposal = prepare_road_portrayal(upstream)

    assert upstream["package_sha256"] == EXPECTED_UPSTREAM_PACKAGE_SHA256
    assert decision["decision"] == {
        "action": ACTION,
        "execution_target": DERIVED_TARGET,
        "road_class": "9420400",
        "route_number": "縣126",
        "road_name": "中山街",
        "requested_portrayal": EXPECTED_PORTRAYAL,
    }
    assert proposal["proposal"]["action"] == ACTION


@pytest.mark.parametrize("change", ["missing", "added", "replaced", "reordered"])
def test_at03_exact_ordered_source_scope_fails_closed(
    upstream: dict[str, Any], change: str
) -> None:
    changed = deepcopy(upstream)
    ids = changed["segment_set"]["ordered_feature_ids"]
    if change == "missing":
        ids.pop()
        changed["segment_set"]["count"] = 2
    elif change == "added":
        ids.append("K0000009999")
        changed["segment_set"]["count"] = 4
    elif change == "replaced":
        ids[1] = "K0000009999"
    else:
        ids.reverse()
    _fails(lambda: prepare_road_portrayal(changed))


def test_at04_upstream_hash_binds_both_artifacts(upstream: dict[str, Any]) -> None:
    decision, proposal = prepare_road_portrayal(upstream)
    assert decision["bindings"]["upstream_package_sha256"] == EXPECTED_UPSTREAM_PACKAGE_SHA256
    assert proposal["bindings"]["upstream_package_sha256"] == EXPECTED_UPSTREAM_PACKAGE_SHA256

    changed = deepcopy(upstream)
    changed["package_sha256"] = "0" * 64
    assert _fails(lambda: prepare_road_portrayal(changed)).code == "upstream_hash_mismatch"


@pytest.mark.parametrize(
    ("path", "expected", "error_code"),
    [
        (("source", "archive_sha256"), EXPECTED_ARCHIVE_SHA256, "upstream_hash_mismatch"),
        (("fixture", "sha256"), EXPECTED_FIXTURE_SHA256, "upstream_hash_mismatch"),
    ],
)
def test_at05_at06_archive_and_fixture_binding(
    upstream: dict[str, Any], path: tuple[str, str], expected: str, error_code: str
) -> None:
    decision, proposal = prepare_road_portrayal(upstream)
    binding_key = "source_archive_sha256" if path[0] == "source" else "fixture_sha256"
    assert decision["bindings"][binding_key] == expected
    assert proposal["bindings"][binding_key] == expected

    changed = deepcopy(upstream)
    changed[path[0]][path[1]] = "0" * 64
    assert _fails(lambda: prepare_road_portrayal(changed)).code == error_code


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("route_number", "縣127"),
        ("road_name", "中山路"),
        ("canonical_identity", "ROADNUM=縣126|ROADNUM1=|ROADNUM2=|ROADNAME="),
    ],
)
def test_at07_route_identity_fails_closed(
    upstream: dict[str, Any], field: str, value: str
) -> None:
    changed = deepcopy(upstream)
    changed["road_identity"][field] = value
    _fails(lambda: prepare_road_portrayal(changed))


def test_at08_class_binding_fails_closed(upstream: dict[str, Any]) -> None:
    changed = deepcopy(upstream)
    changed["road_identity"]["class_code"] = "9420300"
    _fails(lambda: prepare_road_portrayal(changed))


@pytest.mark.parametrize("evidence_id", EXPECTED_EVIDENCE_IDS)
def test_at09_removing_each_evidence_id_fails_closed(
    upstream: dict[str, Any], evidence_id: str
) -> None:
    changed = deepcopy(upstream)
    changed["evidence"]["evidence_ids"].remove(evidence_id)
    assert _fails(lambda: prepare_road_portrayal(changed)).code == "evidence_mismatch"


def test_at09_unknown_evidence_id_fails_closed(upstream: dict[str, Any]) -> None:
    changed = deepcopy(upstream)
    changed["evidence"]["evidence_ids"][-1] = "UNKNOWN-EVIDENCE"
    assert _fails(lambda: prepare_road_portrayal(changed)).code == "evidence_mismatch"


def test_at10_through_at17_closed_target_and_boundaries(upstream: dict[str, Any]) -> None:
    decision, proposal = prepare_road_portrayal(upstream)

    assert decision["decision"]["execution_target"] == DERIVED_TARGET
    assert proposal["proposal"]["execution_target"] == DERIVED_TARGET
    assert decision["boundaries"] == EXPECTED_BOUNDARIES
    assert proposal["boundaries"] == EXPECTED_BOUNDARIES

    for forbidden_target in [
        "authoritative ROAD",
        "ROADA",
        "road-edge geometry",
        "MapLibre runtime state",
    ]:
        changed = deepcopy(proposal)
        changed["proposal"]["execution_target"] = forbidden_target
        _fails(lambda changed=changed: validate_proposal(changed, decision))

    for permission in [
        "execution_allowed",
        "source_mutation_allowed",
        "topology_repair_allowed",
        "roada_execution_allowed",
        "road_edge_derivation_allowed",
    ]:
        changed = deepcopy(proposal)
        changed["boundaries"][permission] = True
        _fails(lambda changed=changed: validate_proposal(changed, decision))

    changed = deepcopy(proposal)
    changed["boundaries"]["authorization_required"] = False
    _fails(lambda: validate_proposal(changed, decision))


def test_at18_at19_golden_artifacts_validate_against_closed_schemas(
    upstream: dict[str, Any]
) -> None:
    decision, proposal = prepare_road_portrayal(upstream)
    decision_schema = json.loads(
        (ROOT / "schemas/road-portrayal-decision-v1.0.schema.json").read_text(encoding="utf-8")
    )
    proposal_schema = json.loads(
        (ROOT / "schemas/road-portrayal-proposal-v1.0.schema.json").read_text(encoding="utf-8")
    )
    _assert_schema(decision, decision_schema, decision_schema)
    _assert_schema(proposal, proposal_schema, proposal_schema)
    validate_decision(decision)
    validate_proposal(proposal, decision)

    missing_decision_integrity = deepcopy(decision)
    missing_decision_integrity.pop("decision_sha256")
    _fails(lambda: validate_decision(missing_decision_integrity))
    missing_proposal_integrity = deepcopy(proposal)
    missing_proposal_integrity.pop("fixture_sha256", None)
    missing_proposal_integrity["bindings"].pop("fixture_sha256")
    _fails(lambda: validate_proposal(missing_proposal_integrity, decision))


def test_at20_at21_artifact_hashes_are_deterministic(upstream: dict[str, Any]) -> None:
    run_1 = prepare_road_portrayal(upstream)
    run_2 = prepare_road_portrayal(upstream)

    assert run_1[0]["decision_sha256"] == run_2[0]["decision_sha256"]
    assert run_1[1]["proposal_sha256"] == run_2[1]["proposal_sha256"]
    assert run_1[0]["decision_sha256"] == decision_sha256(run_1[0])
    assert run_1[1]["proposal_sha256"] == proposal_sha256(run_1[1])


def test_at20_at21_generated_artifacts_match_frozen_golden_files(
    upstream: dict[str, Any]
) -> None:
    decision, proposal = prepare_road_portrayal(upstream)
    frozen_decision = json.loads(
        (
            ROOT
            / "data/specifications/nma-road-hero-road-02-golden-decision-v1.0.json"
        ).read_text(encoding="utf-8")
    )
    frozen_proposal = json.loads(
        (
            ROOT
            / "data/specifications/nma-road-hero-road-02-golden-proposal-v1.0.json"
        ).read_text(encoding="utf-8")
    )
    assert decision == frozen_decision
    assert proposal == frozen_proposal


def test_at22_semantically_equivalent_serialization_is_deterministic(
    upstream: dict[str, Any]
) -> None:
    reordered = json.loads(
        json.dumps(upstream, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    reordered["evidence"]["evidence_ids"].reverse()

    assert prepare_road_portrayal(upstream) == prepare_road_portrayal(reordered)


@pytest.mark.parametrize(
    "permission",
    ["execution_allowed", "source_mutation_allowed", "topology_repair_allowed"],
)
def test_at23_tampered_upstream_permissions_fail_closed(
    upstream: dict[str, Any], permission: str
) -> None:
    changed = deepcopy(upstream)
    changed["permissions"][permission] = True
    _fails(lambda: prepare_road_portrayal(changed))


def test_at24_exact_proposal_content(upstream: dict[str, Any]) -> None:
    _, proposal = prepare_road_portrayal(upstream)
    assert proposal["proposal"]["requested_changes"] == EXPECTED_PORTRAYAL
    assert set(proposal["proposal"]["requested_changes"]) == {
        "shield_code",
        "shield_orientation",
        "road_name_annotation",
        "graphic_element_roles",
    }


def test_at25_no_executed_shield_placement(upstream: dict[str, Any]) -> None:
    decision, proposal = prepare_road_portrayal(upstream)
    serialized = json.dumps([decision, proposal], ensure_ascii=False).casefold()
    assert "coordinates" not in serialized
    assert "execution_receipt" not in serialized
    assert "placement_result" not in serialized
    assert proposal["proposal"]["requested_changes"]["shield_orientation"] == "road-parallel"


def test_at28_module_has_no_execution_or_geometry_capability() -> None:
    source = inspect.getsource(road02).casefold()
    assert "maplibre" not in source
    assert "subprocess" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "shapely" not in source
    assert ".write_" not in source
    assert "open(" not in source
    assert "buffer(" not in source
    assert "polygonize(" not in source


def test_frozen_bindings_are_exact(upstream: dict[str, Any]) -> None:
    decision, proposal = prepare_road_portrayal(upstream)
    expected = {
        "upstream_package_sha256": EXPECTED_UPSTREAM_PACKAGE_SHA256,
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "fixture_sha256": EXPECTED_FIXTURE_SHA256,
        "ordered_source_ids": list(EXPECTED_SOURCE_IDS),
        "route_identity": EXPECTED_ROUTE_IDENTITY,
        "class_code": "9420400",
        "evidence_ids": list(EXPECTED_EVIDENCE_IDS),
    }
    assert decision["bindings"] == expected
    assert proposal["bindings"] == {**expected, "decision_sha256": decision["decision_sha256"]}

from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError
import pytest
from referencing import Registry, Resource

import build_contracts.portrayal_decision as build02
from build_contracts.portrayal_decision import (
    ACTION,
    BUILD_GATE_IDS,
    BuildPortrayalDecisionError,
    DERIVED_TARGET,
    EXPECTED_BOUNDARIES,
    EXPECTED_PORTRAYAL,
    decision_sha256,
    prepare_build_portrayal,
    proposal_sha256,
    validate_decision,
    validate_portrayal_evidence,
    validate_proposal,
)
from build_contracts.resolution import resolve_build_request


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = (
    ROOT / "data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json"
)
DECISION_SCHEMA_PATH = ROOT / "schemas/build-portrayal-decision-v1.0.schema.json"
PROPOSAL_SCHEMA_PATH = ROOT / "schemas/build-portrayal-proposal-v1.0.schema.json"
GOLDEN_DECISION_PATH = (
    ROOT / "data/specifications/nma-build-02-golden-decision-v1.0.json"
)
GOLDEN_PROPOSAL_PATH = (
    ROOT / "data/specifications/nma-build-02-golden-proposal-v1.0.json"
)
GOLDEN_REQUEST = (
    "Resolve the J13 building polygon class 9310100 by the accepted deterministic rule "
    "and prepare its redacted evidence package."
)


@pytest.fixture()
def upstream() -> dict[str, Any]:
    return resolve_build_request(GOLDEN_REQUEST)


@pytest.fixture()
def evidence() -> dict[str, Any]:
    return json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))


def _fails(callable_, code: str | None = None) -> BuildPortrayalDecisionError:
    with pytest.raises(BuildPortrayalDecisionError) as caught:
        callable_()
    if code is not None:
        assert caught.value.code == code
    return caught.value


def test_golden_input_generates_exact_decision_and_proposal(upstream: dict[str, Any]) -> None:
    decision, proposal = prepare_build_portrayal(upstream)

    assert decision == json.loads(GOLDEN_DECISION_PATH.read_text(encoding="utf-8"))
    assert proposal == json.loads(GOLDEN_PROPOSAL_PATH.read_text(encoding="utf-8"))
    assert decision["decision_sha256"] == (
        "624fafe1f84164f6f28396d21153a3ed0f9795ead87b6e9c605115b35ee3c846"
    )
    assert proposal["proposal_sha256"] == (
        "1e588ea2d7752ce7b02c28d6117c4deb1d6c8995dcbace14cfcb542eca847749"
    )


def test_closed_schemas_are_meta_valid_and_accept_both_artifacts(
    upstream: dict[str, Any],
) -> None:
    decision, proposal = prepare_build_portrayal(upstream)
    decision_schema = json.loads(DECISION_SCHEMA_PATH.read_text(encoding="utf-8"))
    proposal_schema = json.loads(PROPOSAL_SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(decision_schema)
    Draft202012Validator.check_schema(proposal_schema)
    assert decision_schema["additionalProperties"] is False
    assert proposal_schema["additionalProperties"] is False
    registry = Registry().with_resource(
        decision_schema["$id"], Resource.from_contents(decision_schema)
    )
    Draft202012Validator(decision_schema).validate(decision)
    Draft202012Validator(proposal_schema, registry=registry).validate(proposal)

    changed = deepcopy(proposal)
    changed["authorization"] = {"approved": True}
    with pytest.raises(ValidationError):
        Draft202012Validator(proposal_schema, registry=registry).validate(changed)


def test_exact_build01_and_core_content_bindings(upstream: dict[str, Any]) -> None:
    decision, proposal = prepare_build_portrayal(upstream)
    bindings = decision["bindings"]

    assert bindings == {
        "upstream_package_sha256": "59b6f972046dbe9af295de414525230b03ed6da4f0e78374076b5cc4a2cdd7de",
        "source_archive_sha256": "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
        "fixture_id": "build-fixture:sha256:7411d8eb06ee70bc24ce7003de0b344a1874c3d606b91571e5913ba766f1162a",
        "observation_id": "build-observation:sha256:8fdbb3bdea8ffe715e7d76eed7c5034bd62226ba649be2206cf7a9e07b853bac",
        "feature_reference": "build-feature:sha256:14ea3d0010f07e672ba549bd9a1963eec97f5029cbb68e3aea6cc908b241801f",
        "attribute_commitment_sha256": "ddfa112586b9c2bc3a61bdf2638b7994ba1200bfce5d8ad34988f2a24da96078",
        "geometry_commitment_sha256": "23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f",
        "profile_identity_sha256": "5f560c8fde92b7ed590c8f4d1292ae69743e033b2bbf43b837b083b5c611dc09",
        "source_scope_sha256": "a4e3eff87f1df770e01c3675fe883335b4416c405922d22b129e85fc4a44065b",
        "portrayal_record_set_id": "nma-portrayal-recipe-review-batch-01-v0.4",
        "portrayal_record_set_sha256": "70ef0c8e8e86ed5d2a2a4a588b41086f3fd20fb6987138e3897b71378f4b294a",
        "portrayal_recipe_sha256": "450ee18fe87ea2a7f1d783747ee22ae927c73a2f46424f65900f28f9981f2e20",
        "source_document_sha256": "1f9c4457d7ced86f2b7681e21be9ad3b7b7ae364981ab995ef27b468e0fa2620",
        "source_rule_id": "portrayal-rule:doc01:9310100",
        "evidence_section_id": "section:doc01-portrayal:p8",
    }
    assert proposal["bindings"] == {
        **bindings,
        "decision_sha256": decision["decision_sha256"],
    }


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("source", "layer_id", "J17_BUILD"),
        ("resolution", "feature_reference", "build-feature:sha256:" + "0" * 64),
        ("identity_evidence", "attribute_commitment_sha256", "0" * 64),
        ("geometry_evidence", "geometry_commitment_sha256", "0" * 64),
        ("geometry_evidence", "z_dimension_present", False),
        ("observation", "id", "build-observation:sha256:" + "0" * 64),
        ("privacy", "raw_geometry_disclosed", True),
        ("permissions", "execution_authorized", True),
    ],
)
def test_changed_upstream_evidence_or_permission_fails_closed(
    upstream: dict[str, Any], section: str, field: str, value: object
) -> None:
    changed = deepcopy(upstream)
    changed[section][field] = value

    _fails(lambda: prepare_build_portrayal(changed), "upstream_hash_mismatch")


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ("document", "evidence_hash_mismatch"),
        ("recipe", "evidence_hash_mismatch"),
        ("gate", "evidence_hash_mismatch"),
        ("status", "evidence_hash_mismatch"),
        ("extra-recipe", "evidence_hash_mismatch"),
    ],
)
def test_portrayal_evidence_tampering_fails_closed(
    upstream: dict[str, Any], evidence: dict[str, Any], change: str, code: str
) -> None:
    changed = deepcopy(evidence)
    recipe = next(item for item in changed["recipes"] if item["feature_code"] == "9310100")
    if change == "document":
        changed["source"]["sha256"] = "0" * 64
    elif change == "recipe":
        recipe["source_constraints"]["component_dimensions_mm"]["hatch_spacing"] = 3.0
    elif change == "gate":
        recipe["activation_gates"].pop()
    elif change == "status":
        recipe["activation_gates"][0]["status"] = "approved"
    else:
        changed["recipes"].append(deepcopy(recipe))

    _fails(
        lambda: prepare_build_portrayal(upstream, portrayal_record_set=changed), code
    )


def test_official_portrayal_is_bounded_and_preserves_unresolved_values(
    upstream: dict[str, Any],
) -> None:
    decision, proposal = prepare_build_portrayal(upstream)

    assert decision["decision"] == {
        "action": ACTION,
        "execution_target": DERIVED_TARGET,
        "feature_code": "9310100",
        "feature_name": "永久性建物(建築區)",
        "requested_portrayal": EXPECTED_PORTRAYAL,
        "review_gates": {
            "required_gate_ids": list(BUILD_GATE_IDS),
            "status": "pending-human-review",
            "all_gates_resolved": False,
        },
    }
    assert proposal["proposal"]["requested_changes"] == EXPECTED_PORTRAYAL
    assert proposal["proposal"]["requested_changes"]["hatch"][
        "numeric_angle_degrees"
    ] is None
    assert proposal["proposal"]["requested_changes"]["annotation"][
        "placement_policy"
    ] == "unresolved-pending-human-review"


def test_all_open_gates_remain_pending_and_cannot_be_claimed_resolved(
    upstream: dict[str, Any],
) -> None:
    decision, proposal = prepare_build_portrayal(upstream)
    gates = proposal["proposal"]["review_gates"]

    assert gates["required_gate_ids"] == list(BUILD_GATE_IDS)
    assert gates["status"] == "pending-human-review"
    assert gates["all_gates_resolved"] is False

    changed = deepcopy(proposal)
    changed["proposal"]["review_gates"]["status"] = "approved"
    changed["proposal"]["review_gates"]["all_gates_resolved"] = True
    changed["proposal_sha256"] = proposal_sha256(changed)
    _fails(lambda: validate_proposal(changed, decision), "proposal_invalid")


@pytest.mark.parametrize("boundary", sorted(EXPECTED_BOUNDARIES))
def test_authority_cannot_be_expanded(
    upstream: dict[str, Any], boundary: str
) -> None:
    decision, proposal = prepare_build_portrayal(upstream)
    changed = deepcopy(proposal)
    changed["boundaries"][boundary] = not EXPECTED_BOUNDARIES[boundary]
    changed["proposal_sha256"] = proposal_sha256(changed)

    _fails(lambda: validate_proposal(changed, decision), "proposal_invalid")


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("geometry_policy", "dimension_drop_authorized"), True),
        (("geometry_policy", "geometry_repair_authorized"), True),
        (("hatch", "numeric_angle_degrees"), 45.0),
        (("hatch", "spacing_mm"), 2.5),
        (("annotation", "placement_policy"), "centroid"),
    ],
)
def test_unreviewed_portrayal_choices_cannot_be_invented(
    upstream: dict[str, Any], path: tuple[str, str], value: object
) -> None:
    decision, proposal = prepare_build_portrayal(upstream)
    changed = deepcopy(proposal)
    changed["proposal"]["requested_changes"][path[0]][path[1]] = value
    changed["proposal_sha256"] = proposal_sha256(changed)

    _fails(lambda: validate_proposal(changed, decision), "proposal_invalid")


def test_artifact_hashes_are_deterministic_and_non_transferable(
    upstream: dict[str, Any],
) -> None:
    first = prepare_build_portrayal(upstream)
    second = prepare_build_portrayal(upstream)

    assert first == second
    assert first[0]["decision_sha256"] == decision_sha256(first[0])
    assert first[1]["proposal_sha256"] == proposal_sha256(first[1])

    changed_decision = deepcopy(first[0])
    changed_decision["decision"]["feature_name"] = "changed"
    changed_decision["decision_sha256"] = decision_sha256(changed_decision)
    _fails(lambda: validate_decision(changed_decision), "decision_invalid")


def test_key_order_and_equivalent_request_wording_are_deterministic(
    upstream: dict[str, Any], evidence: dict[str, Any]
) -> None:
    equivalent_upstream = resolve_build_request(
        "Prepare redacted evidence for J13 BUILD polygon 9310100."
    )
    reordered_evidence = json.loads(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )

    assert upstream["package_sha256"] == equivalent_upstream["package_sha256"]
    assert prepare_build_portrayal(upstream) == prepare_build_portrayal(
        equivalent_upstream, portrayal_record_set=reordered_evidence
    )


def test_inputs_are_not_mutated(
    upstream: dict[str, Any], evidence: dict[str, Any]
) -> None:
    before_upstream = deepcopy(upstream)
    before_evidence = deepcopy(evidence)

    prepare_build_portrayal(upstream, portrayal_record_set=evidence)

    assert upstream == before_upstream
    assert evidence == before_evidence


def test_no_private_geometry_or_raw_attributes_are_disclosed(
    upstream: dict[str, Any],
) -> None:
    decision, proposal = prepare_build_portrayal(upstream)
    serialized = json.dumps([decision, proposal], ensure_ascii=False).casefold()

    assert "2bxkp71rbn" not in serialized
    assert "coordinates" not in serialized
    assert "geometry_wkb_hex" not in serialized
    assert "source_example" not in serialized
    assert proposal["boundaries"]["raw_source_disclosure_allowed"] is False
    assert proposal["boundaries"]["redistribution_allowed"] is False


def test_module_has_no_execution_geometry_or_runtime_capability() -> None:
    source = inspect.getsource(build02).casefold()

    assert "subprocess" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "shapely" not in source
    assert "maplibre" not in source
    assert ".write_" not in source
    assert "authorization_id" not in source
    assert "idempotency" not in source


def test_build01_predecessor_and_legacy_j17_boundary_are_exact(
    upstream: dict[str, Any],
) -> None:
    _, proposal = prepare_build_portrayal(upstream)

    assert proposal["bindings"]["upstream_package_sha256"] == upstream["package_sha256"]
    assert proposal["boundaries"]["legacy_j17_runtime_binding_allowed"] is False
    assert proposal["proposal"]["review_gates"]["required_gate_ids"][-1] == (
        "j13-polygonz-runtime-policy"
    )


def test_direct_evidence_validator_accepts_only_the_frozen_record_set(
    evidence: dict[str, Any],
) -> None:
    before = deepcopy(evidence)

    assert validate_portrayal_evidence(evidence) == before
    assert evidence == before

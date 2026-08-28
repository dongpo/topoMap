from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from nma.core.identity import canonical_sha256
from nma.llm.base import LLMAdapter, LLMResult
from nma.rq2_demo import (
    MANDATORY_POSTCONDITIONS,
    MANDATORY_PRECONDITIONS,
    RQ2Planner,
    artifact_identity,
    assemble_proposal,
    bind_proposal_hash,
    evidence_identities,
    execute_proposal,
    mutate_and_rehash,
    proposal_hash,
    resolve_constraints,
    retrieve_rq2_evidence,
    sha256_file,
    validate_proposal,
    validate_rq3_handoff,
    verify_execution,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads((ROOT / "data/evaluation/rq2-demo-01-protocol.json").read_text("utf-8"))
INTENT = PROTOCOL["canonical_intent"]
FIXTURE_PATH = ROOT / PROTOCOL["fixture"]
FIXTURE = {
    **artifact_identity(PROTOCOL["fixture"], PROTOCOL["fixture_sha256"]),
    "path": PROTOCOL["fixture"],
    "feature_selector": PROTOCOL["feature_selector"],
}
ALLOWLIST_SHA = sha256_file(ROOT / "data/specifications/rq2-tool-allowlist-v1.0.json")
MODEL_IDENTITY = "ollama:qwen2.5:latest@sha256:" + PROTOCOL["model"]["ollama_digest"]


def _knowledge() -> tuple[dict, dict, dict]:
    retrieval = retrieve_rq2_evidence(ROOT, INTENT)
    constraints = resolve_constraints(retrieval)
    identities = evidence_identities(ROOT, retrieval)
    return retrieval, constraints, identities


def _semantic_values(constraints: dict) -> dict:
    by_id = {
        item["constraint_id"]: item
        for item in constraints["resolved"]
        + constraints["unresolved"]
        + constraints["contradicted"]
    }
    return {
        "classification": by_id["constraint:classification.feature_code"]["expected_value"],
        "geometry": by_id["constraint:geometry.type"]["expected_value"],
        "line_style": by_id["constraint:portrayal.line_code"]["expected_value"],
        "color_code": by_id["constraint:portrayal.color_code"]["expected_value"],
        "observed_color": by_id["constraint:portrayal.observed_color"]["expected_value"],
        "product_layer": None,
        "source_authority_handled": True,
    }


def _draft(constraints: dict, *, constrained: bool = True) -> dict:
    refs = sorted(item["constraint_id"] for group in constraints.values() for item in group)
    step_specs = [
        ("step:read-feature", "read_feature", "rq2.feature.read/1.0"),
        (
            "step:validate-authority",
            "validate_source_authority",
            "rq2.source-authority.validate/1.0",
        ),
        (
            "step:validate-geometry",
            "validate_geometry_type",
            "rq2.geometry.validate/1.0",
        ),
        (
            "step:derive-representation",
            "derive_target_representation",
            "rq2.representation.derive/1.0",
        ),
        (
            "step:write-derived",
            "write_derived_artifact",
            "rq2.artifact.write-derived/1.0",
        ),
        ("step:verify", "verify_postconditions", "rq2.postconditions.verify/1.0"),
    ]
    steps = [
        {
            "step_id": step_id,
            "operation": operation,
            "tool": tool,
            "trace_basis": (
                ["user_intent", "knowledge_constraint", "verification_requirement"]
                if constrained
                else ["user_intent", "deterministic_execution_requirement"]
            ),
        }
        for step_id, operation, tool in step_specs
    ]
    semantic = _semantic_values(constraints)
    if not constrained:
        semantic = {
            "classification": "fire_hydrant",
            "geometry": "Point",
            "line_style": None,
            "color_code": None,
            "observed_color": "red",
            "product_layer": None,
            "source_authority_handled": False,
        }
    return {
        "normalized_goal": "Create an isolated symbolic derived feature and verify it.",
        "execution_status": ("PROCEED_WITH_BOUNDED_UNRESOLVED" if constrained else "PROCEED"),
        "reason_codes": (
            ["BOUNDED_UNRESOLVED_GUARDS"] if constrained else ["PLANNER_PROPOSED_EXECUTION"]
        ),
        "semantic_values": semantic,
        "steps": steps,
        "precondition_ids": [
            *MANDATORY_PRECONDITIONS,
            *(["knowledge_snapshot_known"] if constrained else []),
        ],
        "expected_postcondition_ids": list(MANDATORY_POSTCONDITIONS),
        "constraint_refs": refs if constrained else [],
    }


def _proposal(*, constrained: bool = True) -> tuple[dict, dict, dict]:
    retrieval, constraints, identities = _knowledge()
    if not constrained:
        proposal = assemble_proposal(
            architecture="llm-only",
            intent=INTENT,
            draft=_draft(constraints, constrained=False),
            model_identity=MODEL_IDENTITY,
            fixture=FIXTURE,
            created_at=PROTOCOL["created_at"],
            allowlist_sha256=ALLOWLIST_SHA,
        )
        return proposal, retrieval, constraints
    evidence_refs = sorted(
        {
            ref
            for group in constraints.values()
            for item in group
            for ref in item["source_evidence_refs"]
        }
    )
    proposal = assemble_proposal(
        architecture="knowledge-constrained",
        intent=INTENT,
        draft=_draft(constraints),
        model_identity=MODEL_IDENTITY,
        fixture=FIXTURE,
        created_at=PROTOCOL["created_at"],
        allowlist_sha256=ALLOWLIST_SHA,
        constraints=constraints,
        evidence_refs=evidence_refs,
        retrieval_identity=identities["retrieval_identity"],
        knowledge_snapshot_identity=identities["knowledge_snapshot_identity"],
    )
    return proposal, retrieval, constraints


class RecordingAdapter(LLMAdapter):
    def __init__(self, outputs: list[dict]):
        self.outputs = outputs
        self.contexts: list[dict] = []

    def generate_structured(self, *, task, instructions, context, output_schema):
        self.contexts.append(deepcopy(context))
        output = self.outputs[len(self.contexts) - 1]
        return LLMResult(
            model_id="qwen2.5:latest",
            provider="test",
            output=deepcopy(output),
            latency_ms=1,
            usage={"input_tokens": 10, "output_tokens": 10},
            raw_response_hash="a" * 64,
            context_budget={"remaining_input_margin": 100},
        )


def test_fixture_schemas_and_constraint_resolution_are_frozen():
    assert sha256_file(FIXTURE_PATH) == PROTOCOL["fixture_sha256"]
    retrieval, constraints, _ = _knowledge()
    assert retrieval["status"] == "retrieved"
    types = {item["type"] for group in constraints.values() for item in group}
    assert types == {
        "classification",
        "geometry",
        "portrayal",
        "source_authority",
        "relationship_binding",
        "execution_guard",
    }
    product_layer = next(
        item
        for item in constraints["unresolved"]
        if item["constraint_id"] == "constraint:relationship.product_layer"
    )
    assert product_layer["expected_value"] is None
    assert product_layer["execution_effect"] == "guard"


def test_same_llm_path_has_no_baseline_evidence_leakage():
    _, constraints, _ = _knowledge()
    adapter = RecordingAdapter([_draft(constraints, constrained=False), _draft(constraints)])
    planner = RQ2Planner(adapter)
    planner.compose(
        intent=INTENT,
        fixture=FIXTURE,
        architecture="llm-only",
        constraints=None,
    )
    planner.compose(
        intent=INTENT,
        fixture=FIXTURE,
        architecture="knowledge-constrained",
        constraints=constraints,
    )
    assert adapter.contexts[0]["knowledge_constraints"] == []
    assert adapter.contexts[1]["knowledge_constraints"]
    assert adapter.contexts[0]["operation_catalog"] == adapter.contexts[1]["operation_catalog"]


def test_valid_constrained_proposal_hash_and_rq3_handoff():
    proposal, retrieval, constraints = _proposal()
    validation = validate_proposal(
        ROOT,
        proposal,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=FIXTURE,
    )
    assert validation["status"] == "PASS", validation
    assert proposal_hash(proposal) == proposal["proposal_hash"]
    reloaded = json.loads(json.dumps(proposal, ensure_ascii=False, sort_keys=True))
    assert proposal_hash(reloaded) == proposal["proposal_hash"]
    assert validate_rq3_handoff(ROOT, proposal)["status"] == "PASS"


def test_hash_tamper_is_rejected():
    proposal, retrieval, constraints = _proposal()
    proposal["intent"]["normalized_goal"] = "tampered"
    validation = validate_proposal(
        ROOT,
        proposal,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=FIXTURE,
    )
    assert "PROPOSAL_HASH_MISMATCH" in validation["failure_taxonomy"]


def test_unknown_tool_and_omitted_constraint_fail_closed():
    proposal, retrieval, constraints = _proposal()
    unknown = mutate_and_rehash(
        proposal,
        lambda value: value["plan"][0].__setitem__("tool", "rq2.unknown.command/1.0"),
    )
    unknown_result = validate_proposal(
        ROOT,
        unknown,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=FIXTURE,
    )
    assert "UNKNOWN_TOOL" in unknown_result["failure_taxonomy"]

    omitted = deepcopy(proposal)
    for step in omitted["plan"]:
        step["constraint_refs"] = [
            ref for ref in step["constraint_refs"] if ref != "constraint:geometry.type"
        ]
        for group in ("preconditions", "expected_postconditions"):
            for condition in step[group]:
                condition["constraint_refs"] = [
                    ref for ref in condition["constraint_refs"] if ref != "constraint:geometry.type"
                ]
    omitted["provenance_seed"]["plan_identity"] = canonical_sha256(omitted["plan"])
    omitted = bind_proposal_hash(omitted)
    omitted_result = validate_proposal(
        ROOT,
        omitted,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=FIXTURE,
    )
    assert "CONSTRAINT_OMITTED_FROM_PLAN" in omitted_result["failure_taxonomy"]


def test_fabricated_product_layer_is_rejected():
    proposal, retrieval, constraints = _proposal()
    fabricated = mutate_and_rehash(
        proposal,
        lambda value: value["expected_final_state"]["derived_artifact"][
            "semantic_values"
        ].__setitem__("product_layer", "invented"),
    )
    result = validate_proposal(
        ROOT,
        fabricated,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=FIXTURE,
    )
    assert "UNRESOLVED_BINDING_GUESSED" in result["failure_taxonomy"]


def test_execution_and_verification_distinguish_tool_success(tmp_path):
    proposal, retrieval, constraints = _proposal()
    validation = validate_proposal(
        ROOT,
        proposal,
        expected_constraints=constraints,
        retrieval_package=retrieval,
        fixture=FIXTURE,
    )
    good_root = tmp_path / "good"
    execution = execute_proposal(
        ROOT,
        proposal,
        validation,
        fixture_path=FIXTURE_PATH,
        output_root=good_root,
        retrieval_package=retrieval,
    )
    verification = verify_execution(
        proposal, execution, fixture_path=FIXTURE_PATH, output_root=good_root
    )
    assert execution["status"] == "PASS"
    assert verification["status"] == "PASS", verification

    bad_root = tmp_path / "bad"
    bad_execution = execute_proposal(
        ROOT,
        proposal,
        validation,
        fixture_path=FIXTURE_PATH,
        output_root=bad_root,
        retrieval_package=retrieval,
        fault="classification_mismatch",
    )
    bad_verification = verify_execution(
        proposal, bad_execution, fixture_path=FIXTURE_PATH, output_root=bad_root
    )
    assert bad_execution["status"] == "PASS"
    assert bad_verification["status"] == "FAIL"
    assert "POSTCONDITION_VIOLATION" in bad_verification["failure_taxonomy"]


def test_baseline_is_schema_valid_but_cannot_pass_authority_gate(tmp_path):
    proposal, _, _ = _proposal(constrained=False)
    validation = validate_proposal(
        ROOT,
        proposal,
        expected_constraints=None,
        retrieval_package=None,
        fixture=FIXTURE,
    )
    assert validation["status"] == "PASS", validation
    execution = execute_proposal(
        ROOT,
        proposal,
        validation,
        fixture_path=FIXTURE_PATH,
        output_root=tmp_path / "baseline",
        retrieval_package=None,
    )
    assert execution["status"] == "BLOCKED"
    assert execution["mutation_started"] is False
    assert not (tmp_path / "baseline").exists()


def test_all_mandatory_preconditions_are_exercised_by_fixture_draft():
    _, constraints, _ = _knowledge()
    represented = set(_draft(constraints)["precondition_ids"])
    assert set(MANDATORY_PRECONDITIONS) <= represented

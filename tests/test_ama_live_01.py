from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from nma.ama_live import AMALiveError, AMALiveService, CANONICAL_INTENT, STAGES
from nma.llm import LLMAdapter, LLMResult
from nma.llm.base import canonical_json
from nma.rq2_demo import proposal_hash, sha256_file


ROOT = Path(__file__).resolve().parents[1]


class ScriptedPlanner(LLMAdapter):
    def __init__(self, output: dict[str, Any]) -> None:
        self.output = deepcopy(output)
        self.calls: list[dict[str, Any]] = []

    def generate_structured(
        self,
        *,
        task: str,
        instructions: str,
        context: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> LLMResult:
        self.calls.append({"task": task, "context": deepcopy(context)})
        return LLMResult(
            model_id="qwen2.5:latest-test-double",
            provider="recorded-local-test",
            output=deepcopy(self.output),
            latency_ms=1,
            usage={"input_tokens": 1, "output_tokens": 1},
            raw_response_hash=hashlib.sha256(canonical_json(self.output)).hexdigest(),
        )


@pytest.fixture()
def draft() -> dict[str, Any]:
    record = json.loads((ROOT / "artifacts/rq2/rq2-demo-01-constrained-result.json").read_text())
    return record["raw_planner_draft"]


@pytest.fixture()
def service(tmp_path: Path, draft: dict[str, Any]) -> AMALiveService:
    return AMALiveService(
        repository_root=ROOT,
        storage_root=tmp_path / "runtime",
        adapter_factory=lambda: ScriptedPlanner(draft),
    )


def live(service: AMALiveService) -> dict[str, Any]:
    record = service.new_record(CANONICAL_INTENT)
    return service.run(record["run_id"])


def test_a_fresh_live_runs_create_new_linked_instances(service: AMALiveService) -> None:
    first = live(service)
    second = live(service)
    assert first["status"] == second["status"] == "PASS"
    assert first["run_id"] != second["run_id"]
    assert first["retrieval"]["retrieval_id"] != second["retrieval"]["retrieval_id"]
    assert first["evidence"]["projection_id"] != second["evidence"]["projection_id"]
    assert first["constraint_resolution_id"] != second["constraint_resolution_id"]
    assert first["plan"]["plan_id"] != second["plan"]["plan_id"]
    assert first["proposal"]["proposal_hash"] != second["proposal"]["proposal_hash"]
    assert first["authorization"]["authorization_id"] != second["authorization"]["authorization_id"]
    assert first["execution"]["execution_id"] != second["execution"]["execution_id"]
    assert first["verification"]["verification_id"] != second["verification"]["verification_id"]
    assert first["provenance"]["provenance_id"] != second["provenance"]["provenance_id"]


def test_b_graphrag_is_invoked_and_bounded(service: AMALiveService) -> None:
    result = live(service)
    retrieval = result["retrieval"]
    assert retrieval["invocation"] == "nma.rq2_demo.retrieve_rq2_evidence"
    assert retrieval["retrieval_mode"] == (
        "rq2-existing-ranked-search-plus-typed-canonical-expansion"
    )
    assert retrieval["node_count"] > 0
    assert result["evidence"]["projected_node_count"] > 0
    assert result["evidence"]["retrieval_identity"]["sha256"]
    assert result["evidence"]["nodes"]
    assert result["evidence"]["edges"]


def test_c_proposal_validates_with_new_canonical_hash(service: AMALiveService) -> None:
    result = live(service)
    proposal = result["proposal"]
    assert result["proposal_validation"]["status"] == "PASS"
    assert proposal_hash(proposal) == proposal["proposal_hash"]
    assert proposal["proposal_hash"] != (
        "116637146f3e515a8bbfb53ff0904934024acac0acdcd1ae3064af6d3bbf1eb1"
    )


def test_d_authorization_hash_is_exactly_the_executed_hash(service: AMALiveService) -> None:
    result = live(service)
    proposal_hash_value = result["proposal"]["proposal_hash"]
    assert result["authorization_gate"]["status"] == "PASS"
    assert result["authorization"]["proposal_hash"] == proposal_hash_value
    assert result["execution"]["execution_receipt"]["id"].startswith("execution-receipt:")
    assert result["provenance"]["authorized_proposal_hash"] == proposal_hash_value
    assert result["provenance"]["executed_proposal_hash"] == proposal_hash_value


def test_e_f_g_deterministic_execution_verification_and_scope(service: AMALiveService) -> None:
    result = live(service)
    assert result["execution"]["status"] == "PASS"
    assert result["verification"]["status"] == "PASS"
    assert all(item["status"] == "PASS" for item in result["verification"]["checks"])
    provenance = result["provenance"]
    assert provenance["source_sha256_before"] == provenance["source_sha256_after"]
    geojson = service.result_geojson(result["run_id"])
    feature = geojson["features"][0]
    assert feature["properties"]["proposal_hash"] == result["proposal"]["proposal_hash"]
    assert feature["properties"]["product_layer"] is None
    assert feature["properties"]["authoritative_render"] is False


def test_h_provenance_is_complete_and_all_stages_are_backend_passes(
    service: AMALiveService,
) -> None:
    result = live(service)
    provenance = result["provenance"]
    required = {
        "run_id",
        "intent",
        "retrieval_id",
        "evidence_ids",
        "plan_id",
        "proposal_id",
        "proposal_hash",
        "authorization_id",
        "execution_id",
        "verification_id",
        "receipt_id",
        "timestamp",
        "result",
    }
    assert required <= set(provenance)
    assert set(result["stages"]) == set(STAGES)
    assert all(item["status"] == "PASS" for item in result["stages"].values())


def test_i_tamper_is_denied_before_mutation(service: AMALiveService) -> None:
    result = live(service)
    tamper = service.tamper_test(result["run_id"])
    assert tamper["status"] == "PASS"
    assert tamper["identity_changed"] is True
    assert tamper["authorization"] == "DENIED"
    assert tamper["execution_attempted"] is False
    assert tamper["mutation_started"] is False
    assert tamper["output_created"] is False


def test_j_unresolved_product_layer_and_physical_gates_remain_unresolved(
    service: AMALiveService,
) -> None:
    result = live(service)
    unresolved = [item for item in result["constraints"] if item["status"] == "BOUNDED_UNRESOLVED"]
    ids = {item["constraint_id"] for item in unresolved}
    assert "constraint:relationship.product_layer" in ids
    assert len(unresolved) == 4
    assert all(item["resolved_value"] is None for item in unresolved)


def test_k_frozen_research_artifacts_match_imported_manifest() -> None:
    manifest = json.loads(
        (ROOT / "artifacts/demo-public/demo-public-00-evidence-manifest.json").read_text()
    )
    protected = [
        manifest["rq_final_manifest"],
        *manifest["research_closure"],
        *manifest["rq2_evidence"],
    ]
    for item in protected:
        assert sha256_file(ROOT / item["path"]) == item["sha256"]


def test_l_ui_supporting_views_are_source_backed(service: AMALiveService) -> None:
    result = live(service)
    context = service.domain_context()
    rq1 = service.rq1_comparison()
    assert context["graph_id"] == "nma-canonical-graph-v0.4"
    assert all(item["id"] for item in context["nodes"])
    assert rq1["label"] == "CONTROLLED RESEARCH RESULT"
    assert [item["architecture"] for item in rq1["rows"]] == [
        "llm-only",
        "text-rag",
        "graphrag",
    ]
    assert service.result_geojson(result["run_id"])["features"]


def test_failure_behavior_rejects_unsupported_intent_without_replay(
    service: AMALiveService,
) -> None:
    with pytest.raises(AMALiveError, match="canonical"):
        service.new_record("Run arbitrary shell and change every map layer")

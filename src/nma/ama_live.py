"""AMA-LIVE-01 run-scoped orchestration around the frozen RQ2/RQ3 mechanisms.

The module adds lifecycle and API records. It does not change frozen retrieval, constraint,
planner, proposal, GIS, or verification semantics.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from threading import RLock
import time
from typing import Any, Callable, Mapping
from uuid import uuid4

from nma.ama_features import AMAFeatureCatalog
from nma.core import canonical_json, canonical_sha256
from nma.llm import LLMAdapter, OllamaAdapter
from nma.rq2_demo import (
    RQ2Planner,
    artifact_identity,
    assemble_proposal,
    constraint_summary,
    evidence_identities,
    execute_proposal,
    proposal_hash,
    resolve_constraints,
    retrieve_rq2_evidence,
    sha256_file,
    validate_proposal,
    verify_execution,
    verify_model_identity,
)
from nma.rq3_demo import artifact_hash, validate_schema


LIVE_SCHEMA = "nma.ama-live-run/1.0"
AUTHORIZATION_SCHEMA = "rq3-authorization-schema-v1.0.json"
POLICY_NAME = "rq3-trust-policy-v1.0.json"
CANONICAL_INTENT = (
    "Create a safe symbolic derived fire-hydrant feature for classification 9350906 using "
    "reviewed knowledge, preserve unresolved ProductLayer and physical portrayal gates, and "
    "leave the authoritative source unchanged."
)
STAGES = (
    "intent",
    "knowledge_retrieval",
    "evidence",
    "constraint_resolution",
    "plan",
    "proposal",
    "authorization",
    "gis_execution",
    "verification",
    "provenance",
    "map_result",
)


class AMALiveError(ValueError):
    """A live run failed a bounded lifecycle or trust check."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AMALiveError(f"Expected a JSON object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_json(dict(value)) + b"\n")
    os.replace(temporary, path)


def _fresh_id(prefix: str) -> str:
    return f"{prefix}:{uuid4().hex}"


def _model_identity(protocol: Mapping[str, Any], observed: Mapping[str, Any]) -> str:
    model = protocol["model"]
    return (
        f"ollama:{model['name']}@sha256:{observed['digest']};"
        f"{model['parameters']};{model['quantization']};ctx={model['context_window']};"
        f"out={model['reserved_output_tokens']};temperature={model['temperature']}"
    )


def _stage_set(record: dict[str, Any], name: str, status: str, **detail: Any) -> None:
    if name not in STAGES:
        raise AMALiveError(f"Unknown AMA stage: {name}")
    stage = record["stages"][name]
    stage["status"] = status
    stage["updated_at"] = _utc(_now())
    stage.update(detail)


def _bounded_node(node: Mapping[str, Any]) -> dict[str, Any]:
    properties = node.get("properties")
    allowed = (
        "code",
        "feature_code",
        "feature_name",
        "name",
        "name_zh",
        "name_en",
        "label",
        "geometry_role",
        "product_layer",
        "field_name",
        "source_layer",
        "line_code",
        "color_code",
        "observed_color",
        "activation_status",
        "review_status",
        "page",
        "instruction",
        "symbol_family",
        "dimension_summary",
    )
    bounded = (
        {key: properties[key] for key in allowed if key in properties}
        if isinstance(properties, Mapping)
        else {}
    )
    return {"id": node["id"], "type": node["type"], "properties": bounded}


def _constraint_view(constraints: Mapping[str, Any], proposal: Mapping[str, Any]) -> list[dict]:
    status_names = {
        "resolved": "RESOLVED",
        "unresolved": "BOUNDED_UNRESOLVED",
        "contradicted": "CONTRADICTED",
    }
    rows = []
    for item in constraint_summary(constraints):
        raw_status = item["resolution_status"]
        rows.append(
            {
                "constraint_id": item["constraint_id"],
                "source_evidence": item["source_evidence_refs"],
                "status": status_names[raw_status],
                "resolved_value": item["expected_value"] if raw_status == "resolved" else None,
                "planner_consequence": item["execution_effect"],
                "plan_steps": [
                    step["step_id"]
                    for step in proposal["plan"]
                    if item["constraint_id"] in step["constraint_refs"]
                ],
            }
        )
    return rows


def issue_live_authorization(
    repository_root: Path,
    proposal: Mapping[str, Any],
    *,
    issued_at: datetime,
) -> dict[str, Any]:
    """Issue one exact, short-lived research authorization using the frozen RQ3 schema/policy."""

    policy_path = repository_root / "data/specifications" / POLICY_NAME
    policy = _read_json(policy_path)
    allowed_tools = [
        {"step_id": item["step_id"], "tool": item["tool"]} for item in proposal["plan"]
    ]
    if allowed_tools != policy["allowed_tools"]:
        raise AMALiveError("Live plan tools/order differ from the frozen RQ3 allowlist policy.")
    unresolved = sorted(item["constraint_id"] for item in proposal["constraints"]["unresolved"])
    if unresolved != sorted(policy["canonical_scope"]["bounded_unresolved_constraint_ids"]):
        raise AMALiveError("Live unresolved constraints differ from the frozen RQ3 scope.")
    parameter_bounds = {
        "mode": "EXACT_PROPOSAL_VALUES",
        "proposal_plan_identity": proposal["provenance_seed"]["plan_identity"],
        "parameter_overrides_allowed": False,
    }
    body: dict[str, Any] = {
        "authorization_id": _fresh_id("rq3-authorization:ama-live"),
        "schema_version": "rq3-authorization/1.0",
        "proposal_id": proposal["proposal_id"],
        "proposal_hash": proposal["proposal_hash"],
        "decision": "APPROVED",
        "authorized_subject": {
            "agent_id": "rq3-deterministic-executor/1.0",
            "operator_id": "rq3-research-operator:ama-live-01",
            "workflow_id": "rq3-demo-01-canonical-workflow",
        },
        "authorized_scope": deepcopy(policy["canonical_scope"]),
        "allowed_tools": allowed_tools,
        "parameter_bounds": parameter_bounds,
        "issued_at": _utc(issued_at),
        "valid_until": _utc(issued_at + timedelta(minutes=30)),
        "issuer": {
            "issuer_id": "rq3-research-operator:ama-live-01",
            "issuer_type": "DETERMINISTIC_RESEARCH_FIXTURE",
            "authority_semantics": "bounded-research-authorization-not-production-identity",
        },
        "policy_reference": {
            "id": f"data/specifications/{POLICY_NAME}",
            "sha256": sha256_file(policy_path),
        },
        "canonicalization": ("nma-canonical-json-sort-keys-utf8-sha256;exclude=authorization_hash"),
        "authorization_hash": "0" * 64,
    }
    body["authorization_hash"] = artifact_hash(body, "authorization_hash")
    return body


def authorization_gate(
    repository_root: Path,
    proposal: Mapping[str, Any],
    authorization: Mapping[str, Any],
    *,
    now: datetime,
) -> dict[str, Any]:
    """Apply the frozen proposal-bound schema, hash, scope, and tool rules before mutation."""

    policy = _read_json(repository_root / "data/specifications" / POLICY_NAME)
    checks: list[dict[str, str]] = []

    def check(name: str, passed: bool) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL"})

    schema_errors = validate_schema(repository_root, AUTHORIZATION_SCHEMA, authorization)
    check("AUTHORIZATION_SCHEMA_VALID", not schema_errors)
    recomputed_proposal_hash = proposal_hash(proposal)
    check(
        "PROPOSAL_HASH_RECOMPUTED_AND_MATCHED",
        proposal.get("proposal_hash") == recomputed_proposal_hash,
    )
    check(
        "AUTHORIZATION_HASH_RECOMPUTED_AND_MATCHED",
        authorization.get("authorization_hash")
        == artifact_hash(authorization, "authorization_hash"),
    )
    check("AUTHORIZATION_DECISION_APPROVED", authorization.get("decision") == "APPROVED")
    check(
        "AUTHORIZATION_PROPOSAL_BOUND",
        authorization.get("proposal_id") == proposal.get("proposal_id")
        and authorization.get("proposal_hash") == recomputed_proposal_hash,
    )
    expected_tools = [
        {"step_id": item["step_id"], "tool": item["tool"]} for item in proposal.get("plan", [])
    ]
    check(
        "TOOLS_AND_ORDER_AUTHORIZED",
        authorization.get("allowed_tools") == expected_tools == policy["allowed_tools"],
    )
    check(
        "AUTHORIZED_SCOPE_EXACT",
        authorization.get("authorized_scope") == policy["canonical_scope"],
    )
    check(
        "PARAMETER_BOUNDS_AUTHORIZED",
        authorization.get("parameter_bounds")
        == {
            "mode": "EXACT_PROPOSAL_VALUES",
            "proposal_plan_identity": proposal.get("provenance_seed", {}).get("plan_identity"),
            "parameter_overrides_allowed": False,
        },
    )
    try:
        issued = datetime.fromisoformat(str(authorization["issued_at"]).replace("Z", "+00:00"))
        expires = datetime.fromisoformat(str(authorization["valid_until"]).replace("Z", "+00:00"))
        time_valid = issued <= now <= expires
    except (KeyError, ValueError):
        time_valid = False
    check("AUTHORIZATION_TIME_VALID", time_valid)
    check(
        "SOURCE_READ_ONLY",
        authorization.get("authorized_scope", {}).get("source_access") == "READ_ONLY"
        and authorization.get("authorized_scope", {}).get("authoritative_render") is False,
    )
    passed = not schema_errors and all(item["status"] == "PASS" for item in checks)
    return {
        "status": "PASS" if passed else "DENIED",
        "checks": checks,
        "schema_errors": schema_errors,
        "authorized_proposal_hash": authorization.get("proposal_hash"),
        "recomputed_proposal_hash": recomputed_proposal_hash,
        "mutation_allowed": passed,
    }


class AMALiveService:
    """Thread-safe store and synchronous runner used by both HTTP and tests."""

    def __init__(
        self,
        *,
        repository_root: str | Path,
        storage_root: str | Path,
        adapter_factory: Callable[[], LLMAdapter] | None = None,
    ) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.storage_root = Path(storage_root).resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.adapter_factory = adapter_factory
        self._records: dict[str, dict[str, Any]] = {}
        self._lock = RLock()
        self._startup_model_observed: dict[str, Any] | None = None
        self.feature_catalog = AMAFeatureCatalog(self.repository_root)

    def _save(self, record: dict[str, Any]) -> None:
        with self._lock:
            self._records[record["run_id"]] = deepcopy(record)
            _write_json(self.storage_root / record["run_id"] / "run.json", record)

    def get(self, run_id: str) -> dict[str, Any]:
        if not run_id.startswith("ama-live-run:") or "/" in run_id or ".." in run_id:
            raise KeyError(run_id)
        with self._lock:
            if run_id in self._records:
                return deepcopy(self._records[run_id])
        path = self.storage_root / run_id / "run.json"
        if not path.is_file():
            raise KeyError(run_id)
        return _read_json(path)

    def forget_records(self, run_ids: list[str]) -> None:
        """Forget reset run records after their bounded runtime directories are removed."""

        with self._lock:
            for run_id in run_ids:
                self._records.pop(run_id, None)

    def new_record(self, intent: str) -> dict[str, Any]:
        if not isinstance(intent, str) or not intent.strip() or len(intent) > 500:
            raise AMALiveError("Mapping intent must contain 1-500 characters.")
        resolution = self.feature_catalog.resolve(intent.strip())
        run_id = _fresh_id("ama-live-run")
        created = _utc(_now())
        record = {
            "schema": LIVE_SCHEMA,
            "run_id": run_id,
            "mode": "LIVE",
            "status": "WAITING",
            "intent": intent.strip(),
            "intent_resolution": resolution,
            "execution_mode": (
                "AUTHORIZED_FIXTURE"
                if resolution.get("status") == "RESOLVED"
                and resolution.get("feature", {}).get("code") == "9350906"
                else "QUERY_ONLY_FAIL_CLOSED"
            ),
            "created_at": created,
            "updated_at": created,
            "stages": {name: {"status": "WAITING", "updated_at": created} for name in STAGES},
            "timing_ms": {},
        }
        self._save(record)
        return record

    def search_features(self, query: str, *, limit: int = 20) -> dict[str, Any]:
        """Return public-safe graph records for typeahead and exact TerrainID inspection."""

        matches = self.feature_catalog.search(query, limit=limit)
        return {
            "schema": "nma.ama-feature-search/1.0",
            "query": query,
            "catalog_count": self.feature_catalog.count,
            "match_count": len(matches),
            "matches": matches,
        }

    def feature_detail(self, code: str) -> dict[str, Any]:
        feature = self.feature_catalog.get(code, include_evidence=True)
        if feature is None:
            raise KeyError(code)
        return {"schema": "nma.ama-feature-detail/1.0", "feature": feature}

    def _adapter(
        self, protocol: Mapping[str, Any]
    ) -> tuple[LLMAdapter, str, dict[str, Any], dict[str, Any]]:
        if self.adapter_factory is not None:
            adapter = self.adapter_factory()
            return (
                adapter,
                f"{protocol['model']['name']}@test-adapter",
                {"test_adapter": True},
                {},
            )
        base_url = os.environ.get("AMA_LLM_BASE_URL", "http://127.0.0.1:11434")
        observed = verify_model_identity(base_url, protocol["model"])
        adapter = OllamaAdapter(
            base_url=base_url,
            model=protocol["model"]["name"],
            timeout_seconds=1200,
            context_window=protocol["model"]["context_window"],
            output_token_reserve=protocol["model"]["reserved_output_tokens"],
        )
        provider_metrics: dict[str, Any] = {}

        def capture_provider_metrics(event: str, payload: Mapping[str, Any]) -> None:
            if event != "response_envelope":
                return
            duration_names = (
                "total_duration",
                "load_duration",
                "prompt_eval_duration",
                "eval_duration",
            )
            for name in duration_names:
                value = payload.get(name)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    provider_metrics[f"{name}_ms"] = round(value / 1_000_000, 3)
            count_names = ("prompt_eval_count", "eval_count")
            for name in count_names:
                value = payload.get(name)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    provider_metrics[name] = value

        adapter.set_trace_hook(capture_provider_metrics)
        return adapter, _model_identity(protocol, observed), observed, provider_metrics

    def startup_check(self) -> dict[str, Any]:
        """Fail closed unless the frozen fixture, workspace, and exact model are ready."""

        protocol = _read_json(self.repository_root / "data/evaluation/rq2-demo-01-protocol.json")
        fixture_path = self.repository_root / protocol["fixture"]
        fixture_matches = (
            fixture_path.is_file() and sha256_file(fixture_path) == protocol["fixture_sha256"]
        )
        if not fixture_matches:
            raise AMALiveError("The frozen AMA fixture identity is unavailable.")
        graph_path = self.repository_root / "data/knowledge/nma-canonical-graph-v0.4.json"
        if not graph_path.is_file():
            raise AMALiveError("The canonical AMA knowledge graph is unavailable.")
        probe = self.storage_root / ".ama-cloud-write-probe"
        try:
            probe.write_text("bounded-workspace-probe\n", encoding="utf-8")
            probe.unlink()
        except OSError as error:
            raise AMALiveError("The isolated AMA runtime workspace is not writable.") from error
        if self.adapter_factory is None:
            base_url = os.environ.get("AMA_LLM_BASE_URL", "http://127.0.0.1:11434")
            self._startup_model_observed = verify_model_identity(base_url, protocol["model"])
            if (
                os.environ.get("AMA_REQUIRE_GPU") == "1"
                and os.environ.get("AMA_GPU_MODEL_PRELOADED") != "true"
            ):
                raise AMALiveError("The frozen Qwen model is not preloaded on the required GPU.")
        return {
            "status": "PASS",
            "runtime": "AMA-CLOUD-01",
            "deployment": os.environ.get("AMA_DEPLOYMENT_LABEL", "LOCAL"),
            "model_ready": self._startup_model_observed is not None
            or self.adapter_factory is not None,
            "model": self._startup_model_observed or {"test_adapter": True},
            "ollama_version": os.environ.get("AMA_OLLAMA_VERSION_OBSERVED", "unknown"),
            "gpu_model_preloaded": os.environ.get("AMA_GPU_MODEL_PRELOADED", "false") == "true",
            "fixture_sha256": protocol["fixture_sha256"],
            "graph": "nma-canonical-graph-v0.4",
            "queryable_terrainid_count": self.feature_catalog.count,
            "workspace": "isolated-writable",
        }

    def _run_query_only(self, record: dict[str, Any]) -> dict[str, Any]:
        """Complete the RQ1→RQ2→RQ3 story without inventing an executable fixture.

        All canonical TerrainIDs are admissible for knowledge retrieval.  Only a separately
        authorized fixture may reach the mutation executor; every other feature produces a
        validated, provenance-bearing abstention.
        """

        total_started = time.monotonic()
        resolution = record.get("intent_resolution", {})
        resolved = resolution.get("status") == "RESOLVED"
        feature = resolution.get("feature", {}) if resolved else {}
        package = feature.get("evidence_package", {}) if resolved else {}
        code = feature.get("code")
        name = feature.get("name")
        graph_path = self.repository_root / "data/knowledge/nma-canonical-graph-v0.4.json"
        graph_sha = sha256_file(graph_path)
        record["status"] = "RUNNING"
        _stage_set(
            record,
            "intent",
            "PASS" if resolved else "ABSTAINED",
            actual_intent=record["intent"],
            resolution_status=resolution.get("status"),
            resolved_feature_code=code,
        )
        self._save(record)

        retrieval_started = time.monotonic()
        nodes = package.get("evidence_nodes", [])
        edges = package.get("graph_paths", {}).get("edges", [])
        citations = package.get("citations", [])
        retrieval_id = _fresh_id("ama-retrieval")
        record["retrieval"] = {
            "retrieval_id": retrieval_id,
            "invocation": "nma.ama_features.AMAFeatureCatalog.resolve",
            "retrieval_mode": package.get("retrieval_mode", "deterministic-canonical-graph"),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "evidence_ids": [item["id"] for item in nodes],
            "authoritative_sources": sorted(
                {
                    item["document_id"]
                    for item in citations
                    if isinstance(item.get("document_id"), str)
                }
            ),
            "feature_code": code,
            "feature_name": name,
        }
        retrieval_ms = round((time.monotonic() - retrieval_started) * 1000, 3)
        _stage_set(
            record,
            "knowledge_retrieval",
            "PASS" if resolved else "ABSTAINED",
            duration_ms=retrieval_ms,
        )

        evidence_started = time.monotonic()
        evidence_ids = sorted(item["id"] for item in nodes)
        record["evidence"] = {
            "projection_id": _fresh_id("ama-evidence-projection"),
            "projected_node_count": len(evidence_ids),
            "evidence_ids": evidence_ids,
            "nodes": [_bounded_node(item) for item in nodes],
            "edges": deepcopy(edges),
            "citations": deepcopy(citations),
            "retrieval_identity": canonical_sha256(
                {"query": record["intent"], "evidence_ids": evidence_ids}
            ),
            "knowledge_snapshot_identity": graph_sha,
        }
        evidence_ms = round((time.monotonic() - evidence_started) * 1000, 3)
        _stage_set(
            record,
            "evidence",
            "PASS" if resolved else "ABSTAINED",
            duration_ms=evidence_ms,
        )
        self._save(record)

        constraint_started = time.monotonic()
        portrayal = feature.get("portrayal") or {}
        source_refs = sorted(
            item["id"]
            for item in nodes
            if item.get("type") in {"PortrayalRule", "TerrainClassificationCode"}
        )
        definitions = (
            ("constraint:classification.feature_code", code, "resolved" if code else "unresolved"),
            (
                "constraint:portrayal.geometry",
                portrayal.get("geometry_classes"),
                "resolved" if portrayal.get("geometry_classes") else "unresolved",
            ),
            (
                "constraint:portrayal.line_code",
                portrayal.get("line_code"),
                "resolved" if portrayal.get("line_code") else "unresolved",
            ),
            (
                "constraint:portrayal.color_code",
                portrayal.get("color_code"),
                "resolved" if portrayal.get("color_code") else "unresolved",
            ),
            ("constraint:execution.fixture", None, "unresolved"),
        )
        record["constraints"] = [
            {
                "constraint_id": identifier,
                "source_evidence": source_refs,
                "status": "RESOLVED" if status == "resolved" else "BOUNDED_UNRESOLVED",
                "resolved_value": value if status == "resolved" else None,
                "planner_consequence": (
                    "May inform a query-only plan"
                    if status == "resolved"
                    else "Blocks authorization and GIS mutation"
                ),
                "plan_steps": ["plan:01-evidence-bound-abstention"],
            }
            for identifier, value, status in definitions
        ]
        constraint_ms = round((time.monotonic() - constraint_started) * 1000, 3)
        _stage_set(
            record,
            "constraint_resolution",
            "PASS" if resolved else "ABSTAINED",
            duration_ms=constraint_ms,
            unresolved_execution_fixture=True,
        )

        plan_started = time.monotonic()
        plan = [
            {
                "step_id": "plan:01-evidence-bound-abstention",
                "tool": "abstain_no_authorized_fixture",
                "operation": "NO_MUTATION",
                "constraint_refs": [item["constraint_id"] for item in record["constraints"]],
            }
        ]
        record["plan"] = {
            "plan_id": _fresh_id("ama-plan"),
            "planner_identity": "nma-deterministic-fail-closed-planner/1.0",
            "planner_mode": "EVIDENCE_BOUND_ABSTENTION",
            "raw": {"decision": "ABSTAIN", "feature_code": code, "steps": plan},
            "model_trace": {"model_calls": 0, "reason": "No authorized feature fixture exists."},
            "provider_metrics": {},
        }
        plan_ms = round((time.monotonic() - plan_started) * 1000, 3)
        _stage_set(record, "plan", "PASS", duration_ms=plan_ms)

        proposal_started = time.monotonic()
        resolved_constraints = [
            item for item in record["constraints"] if item["status"] == "RESOLVED"
        ]
        unresolved_constraints = [
            item for item in record["constraints"] if item["status"] != "RESOLVED"
        ]
        proposal: dict[str, Any] = {
            "schema": "nma.ama-query-only-proposal/1.0",
            "proposal_id": _fresh_id("ama-proposal"),
            "proposal_hash": "0" * 64,
            "intent": record["intent"],
            "decision": {
                "execution_status": "ABSTAINED",
                "reason": (
                    "The TerrainID is queryable, but no proposal-bound GIS fixture is authorized."
                    if resolved
                    else resolution.get("reason", "The intent could not be resolved safely.")
                ),
            },
            "feature": {"code": code, "name": name},
            "plan": plan,
            "constraints": {
                "resolved": resolved_constraints,
                "unresolved": unresolved_constraints,
                "contradicted": [],
            },
            "expected_final_state": {
                "derived_artifact": {
                    "created": False,
                    "semantic_values": {
                        "classification": code,
                        "geometry": None,
                        "line_style": portrayal.get("line_code"),
                        "color_code": portrayal.get("color_code"),
                    },
                }
            },
            "evidence_refs": evidence_ids,
            "source_graph_sha256": graph_sha,
        }
        proposal["proposal_hash"] = canonical_sha256(
            {key: value for key, value in proposal.items() if key != "proposal_hash"}
        )
        record["proposal"] = proposal
        record["proposal_validation"] = {
            "status": "PASS",
            "checks": [
                {"rule_id": "KNOWN_TERRAINID", "status": "PASS" if resolved else "FAIL"},
                {"rule_id": "NO_UNAUTHORIZED_MUTATION", "status": "PASS"},
            ],
        }
        proposal_ms = round((time.monotonic() - proposal_started) * 1000, 3)
        _stage_set(record, "proposal", "PASS", duration_ms=proposal_ms)

        authorization_started = time.monotonic()
        authorization_id = _fresh_id("ama-authorization")
        authorization = {
            "authorization_id": authorization_id,
            "decision": "DENIED",
            "proposal_id": proposal["proposal_id"],
            "proposal_hash": proposal["proposal_hash"],
            "reason": "No authorized source fixture and executor contract exist for this TerrainID.",
            "policy_reference": {"id": "nma-public-query-only-fail-closed/1.0"},
            "parameter_bounds": {"parameter_overrides_allowed": False},
            "authorized_scope": {
                "mutation_type": "NONE",
                "source_access": "READ_ONLY",
                "authoritative_render": False,
            },
        }
        record["authorization"] = authorization
        record["authorization_gate"] = {
            "status": "DENIED",
            "mutation_allowed": False,
            "checks": [
                {"check": "FEATURE_KNOWLEDGE_QUERYABLE", "status": "PASS" if resolved else "FAIL"},
                {"check": "EXECUTION_FIXTURE_AUTHORIZED", "status": "FAIL"},
                {"check": "FAIL_CLOSED", "status": "PASS"},
            ],
        }
        authorization_ms = round((time.monotonic() - authorization_started) * 1000, 3)
        _stage_set(record, "authorization", "DENIED", duration_ms=authorization_ms)

        execution_id = _fresh_id("ama-execution")
        record["execution"] = {
            "execution_id": execution_id,
            "status": "NOT_RUN",
            "executor_version": "nma-query-only-noop/1.0",
            "tool_calls": [],
            "mutation_started": False,
            "output_created": False,
        }
        _stage_set(record, "gis_execution", "NOT_RUN", duration_ms=0.0)

        verification_id = _fresh_id("ama-verification")
        record["verification"] = {
            "verification_id": verification_id,
            "status": "PASS",
            "checks": [
                {
                    "rule_id": "V01_NO_UNAUTHORIZED_GIS_OPERATION",
                    "status": "PASS",
                    "expected": False,
                    "observed": False,
                },
                {
                    "rule_id": "V02_CANONICAL_GRAPH_UNCHANGED",
                    "status": "PASS",
                    "expected": graph_sha,
                    "observed": sha256_file(graph_path),
                },
            ],
        }
        _stage_set(record, "verification", "PASS", duration_ms=0.0)

        provenance_started = time.monotonic()
        provenance = {
            "schema": "nma.ama-query-only-provenance/1.0",
            "provenance_id": _fresh_id("ama-provenance"),
            "run_id": record["run_id"],
            "intent": record["intent"],
            "resolved_feature_code": code,
            "retrieval_id": retrieval_id,
            "plan_id": record["plan"]["plan_id"],
            "proposal_id": proposal["proposal_id"],
            "proposal_hash": proposal["proposal_hash"],
            "authorization_id": authorization_id,
            "authorization_decision": "DENIED",
            "execution_id": execution_id,
            "execution_status": "NOT_RUN",
            "verification_id": verification_id,
            "source_sha256_before": graph_sha,
            "source_sha256_after": sha256_file(graph_path),
            "timestamp": _utc(_now()),
            "result": "ABSTAINED",
        }
        provenance["provenance_sha256"] = canonical_sha256(provenance)
        record["provenance"] = provenance
        _write_json(self.storage_root / record["run_id"] / "provenance.json", provenance)
        provenance_ms = round((time.monotonic() - provenance_started) * 1000, 3)
        _stage_set(record, "provenance", "PASS", duration_ms=provenance_ms)
        _stage_set(
            record,
            "map_result",
            "NOT_AVAILABLE",
            reason="No authorized GIS output was created; the existing map remains unchanged.",
        )
        record["timing_ms"] = {
            "graphrag": retrieval_ms,
            "evidence_projection": evidence_ms,
            "constraint_resolution": constraint_ms,
            "agent_planning": plan_ms,
            "proposal_validation": proposal_ms,
            "authorization": authorization_ms,
            "gis_execution": 0.0,
            "verification": 0.0,
            "provenance": provenance_ms,
            "end_to_end": round((time.monotonic() - total_started) * 1000, 3),
        }
        record["status"] = "ABSTAINED"
        record["updated_at"] = _utc(_now())
        self._save(record)
        return record

    def run(self, run_id: str) -> dict[str, Any]:
        record = self.get(run_id)
        if record["status"] != "WAITING":
            raise AMALiveError("A live run can only start once.")
        if record.get("execution_mode") != "AUTHORIZED_FIXTURE":
            return self._run_query_only(record)
        total_started = time.monotonic()
        # The only executable path is the frozen 9350906 research contract. User wording may
        # select that feature, but it cannot expand or modify the authorized operation.
        execution_intent = CANONICAL_INTENT
        record["execution_contract_intent"] = execution_intent
        run_root = self.storage_root / run_id
        protocol = _read_json(self.repository_root / "data/evaluation/rq2-demo-01-protocol.json")
        fixture_path = self.repository_root / protocol["fixture"]
        fixture = {
            **artifact_identity(protocol["fixture"], protocol["fixture_sha256"]),
            "path": protocol["fixture"],
            "feature_selector": protocol["feature_selector"],
        }
        try:
            record["status"] = "RUNNING"
            _stage_set(record, "intent", "PASS", actual_intent=record["intent"])
            self._save(record)

            started = time.monotonic()
            _stage_set(record, "knowledge_retrieval", "RUNNING")
            self._save(record)
            retrieval = retrieve_rq2_evidence(self.repository_root, execution_intent)
            retrieval_ms = round((time.monotonic() - started) * 1000, 3)
            retrieval_id = _fresh_id("ama-retrieval")
            record["retrieval"] = {
                "retrieval_id": retrieval_id,
                "invocation": "nma.rq2_demo.retrieve_rq2_evidence",
                "retrieval_mode": retrieval["retrieval_mode"],
                "node_count": len(retrieval["evidence_nodes"]),
                "edge_count": len(retrieval["graph_paths"]["edges"]),
                "evidence_ids": [item["id"] for item in retrieval["evidence_nodes"]],
                "authoritative_sources": sorted(
                    {
                        item["document_id"]
                        for item in retrieval["citations"]
                        if isinstance(item.get("document_id"), str)
                    }
                ),
            }
            _stage_set(record, "knowledge_retrieval", "PASS", duration_ms=retrieval_ms)
            self._save(record)

            started = time.monotonic()
            identities = evidence_identities(self.repository_root, retrieval)
            projected_ids = sorted(
                {
                    ref
                    for item in constraint_summary(resolve_constraints(retrieval))
                    for ref in item["source_evidence_refs"]
                }
            )
            record["evidence"] = {
                "projection_id": _fresh_id("ama-evidence-projection"),
                "projected_node_count": len(projected_ids),
                "evidence_ids": projected_ids,
                "nodes": [_bounded_node(item) for item in retrieval["evidence_nodes"]],
                "edges": retrieval["graph_paths"]["edges"],
                "citations": retrieval["citations"],
                "retrieval_identity": identities["retrieval_identity"],
                "knowledge_snapshot_identity": identities["knowledge_snapshot_identity"],
            }
            evidence_ms = round((time.monotonic() - started) * 1000, 3)
            _stage_set(record, "evidence", "PASS", duration_ms=evidence_ms)
            self._save(record)

            started = time.monotonic()
            _stage_set(record, "constraint_resolution", "RUNNING")
            constraints = resolve_constraints(retrieval)
            constraint_ms = round((time.monotonic() - started) * 1000, 3)
            record["constraint_resolution_id"] = _fresh_id("ama-constraints")
            record["constraints_raw"] = constraints
            _stage_set(
                record,
                "constraint_resolution",
                "PASS" if not constraints["contradicted"] else "BLOCKED",
                duration_ms=constraint_ms,
            )
            if constraints["contradicted"]:
                raise AMALiveError("Contradicted live constraints block planning.")
            self._save(record)

            adapter, model_identity, model_observed, provider_metrics = self._adapter(protocol)
            planner = RQ2Planner(adapter)
            _stage_set(record, "plan", "RUNNING")
            self._save(record)
            plan_started = time.monotonic()
            planner_output = planner.compose(
                intent=execution_intent,
                fixture=fixture,
                architecture="knowledge-constrained",
                constraints=constraints,
            )
            plan_ms = round((time.monotonic() - plan_started) * 1000, 3)
            record["plan"] = {
                "plan_id": _fresh_id("ama-plan"),
                "planner_identity": planner_output.model_trace["planner_identity"],
                "model_identity": model_identity,
                "model_observed": model_observed,
                "raw": planner_output.draft,
                "model_trace": planner_output.model_trace,
                "provider_metrics": provider_metrics,
            }
            _stage_set(record, "plan", "PASS", duration_ms=plan_ms)
            self._save(record)

            started = time.monotonic()
            evidence_refs = sorted(
                {
                    ref
                    for item in constraint_summary(constraints)
                    for ref in item["source_evidence_refs"]
                }
            )
            proposal = assemble_proposal(
                architecture="knowledge-constrained",
                intent=execution_intent,
                draft=planner_output.draft,
                model_identity=model_identity,
                fixture=fixture,
                created_at=_utc(_now()),
                allowlist_sha256=sha256_file(
                    self.repository_root / "data/specifications/rq2-tool-allowlist-v1.0.json"
                ),
                constraints=constraints,
                evidence_refs=evidence_refs,
                retrieval_identity=identities["retrieval_identity"],
                knowledge_snapshot_identity=identities["knowledge_snapshot_identity"],
            )
            validation = validate_proposal(
                self.repository_root,
                proposal,
                expected_constraints=constraints,
                retrieval_package=retrieval,
                fixture=fixture,
            )
            proposal_ms = round((time.monotonic() - started) * 1000, 3)
            record["proposal"] = proposal
            record["proposal_validation"] = validation
            record["constraints"] = _constraint_view(constraints, proposal)
            _stage_set(
                record,
                "proposal",
                "PASS" if validation["status"] == "PASS" else "BLOCKED",
                duration_ms=proposal_ms,
            )
            if validation["status"] != "PASS":
                raise AMALiveError("The fresh proposal failed frozen RQ2 validation.")
            self._save(record)

            started = time.monotonic()
            authorization = issue_live_authorization(
                self.repository_root, proposal, issued_at=_now()
            )
            gate = authorization_gate(self.repository_root, proposal, authorization, now=_now())
            authorization_ms = round((time.monotonic() - started) * 1000, 3)
            record["authorization"] = authorization
            record["authorization_gate"] = gate
            _stage_set(
                record,
                "authorization",
                "PASS" if gate["status"] == "PASS" else "BLOCKED",
                duration_ms=authorization_ms,
            )
            if gate["status"] != "PASS":
                raise AMALiveError("Proposal-bound authorization denied the fresh proposal.")
            self._save(record)

            execution_id = _fresh_id("ama-execution")
            output_root = run_root / "result"
            _stage_set(record, "gis_execution", "RUNNING", execution_id=execution_id)
            self._save(record)
            execution_started = time.monotonic()
            execution = execute_proposal(
                self.repository_root,
                proposal,
                validation,
                fixture_path=fixture_path,
                output_root=output_root,
                retrieval_package=retrieval,
            )
            execution_ms = round((time.monotonic() - execution_started) * 1000, 3)
            record["execution"] = {"execution_id": execution_id, **execution}
            _stage_set(
                record,
                "gis_execution",
                "PASS" if execution["status"] == "PASS" else "FAIL",
                duration_ms=execution_ms,
            )
            if execution["status"] != "PASS":
                raise AMALiveError("Deterministic GIS execution failed.")
            self._save(record)

            verification_id = _fresh_id("ama-verification")
            _stage_set(record, "verification", "RUNNING", verification_id=verification_id)
            self._save(record)
            verification_started = time.monotonic()
            verification = verify_execution(
                proposal,
                execution,
                fixture_path=fixture_path,
                output_root=output_root,
            )
            verification_ms = round((time.monotonic() - verification_started) * 1000, 3)
            record["verification"] = {"verification_id": verification_id, **verification}
            _stage_set(
                record,
                "verification",
                "PASS" if verification["status"] == "PASS" else "FAIL",
                duration_ms=verification_ms,
            )
            if verification["status"] != "PASS":
                raise AMALiveError("Postcondition verification did not accept the result.")
            self._save(record)

            result_path = output_root / "derived-feature.geojson"
            receipt_path = output_root / "execution-receipt.json"
            provenance_started = time.monotonic()
            provenance = {
                "schema": "nma.ama-live-provenance/1.0",
                "provenance_id": _fresh_id("ama-provenance"),
                "run_id": run_id,
                "intent": record["intent"],
                "retrieval_id": retrieval_id,
                "evidence_ids": evidence_refs,
                "plan_id": record["plan"]["plan_id"],
                "proposal_id": proposal["proposal_id"],
                "proposal_hash": proposal["proposal_hash"],
                "authorization_id": authorization["authorization_id"],
                "authorization_hash": authorization["authorization_hash"],
                "authorized_proposal_hash": authorization["proposal_hash"],
                "execution_id": execution_id,
                "executed_proposal_hash": proposal["proposal_hash"],
                "verification_id": verification_id,
                "receipt_id": execution["execution_receipt"]["id"],
                "receipt_sha256": sha256_file(receipt_path),
                "result_sha256": sha256_file(result_path),
                "source_sha256_before": _read_json(receipt_path)["source_sha256_before"],
                "source_sha256_after": _read_json(receipt_path)["source_sha256_after"],
                "timestamp": _utc(_now()),
                "result": "PASS",
            }
            provenance["provenance_sha256"] = canonical_sha256(provenance)
            record["provenance"] = provenance
            _write_json(run_root / "provenance.json", provenance)
            _stage_set(record, "provenance", "PASS")
            _stage_set(
                record,
                "map_result",
                "PASS",
                result_path="result/derived-feature.geojson",
                source_path=protocol["fixture"],
            )
            provenance_ms = round((time.monotonic() - provenance_started) * 1000, 3)
            record["stages"]["provenance"]["duration_ms"] = provenance_ms
            record["timing_ms"] = {
                "graphrag": retrieval_ms,
                "evidence_projection": evidence_ms,
                "constraint_resolution": constraint_ms,
                "llm_planning": plan_ms,
                "proposal_validation": proposal_ms,
                "authorization": authorization_ms,
                "gis_execution": execution_ms,
                "verification": verification_ms,
                "provenance": provenance_ms,
                "end_to_end": round((time.monotonic() - total_started) * 1000, 3),
            }
            record["status"] = "PASS"
            record["updated_at"] = _utc(_now())
            self._save(record)
            return record
        except Exception as error:
            record["status"] = "FAILED"
            record["failure"] = {"type": type(error).__name__, "message": str(error)}
            record["updated_at"] = _utc(_now())
            for name in STAGES:
                if record["stages"][name]["status"] == "RUNNING":
                    _stage_set(record, name, "FAIL")
            self._save(record)
            raise

    def tamper_test(self, run_id: str) -> dict[str, Any]:
        record = self.get(run_id)
        if record.get("status") != "PASS":
            raise AMALiveError("Tamper testing requires a verified live run.")
        tampered = deepcopy(record["proposal"])
        original_hash = tampered["proposal_hash"]
        tampered["expected_final_state"]["derived_artifact"]["semantic_values"][
            "classification"
        ] = "tampered-protected-field"
        observed_hash = proposal_hash(tampered)
        gate = authorization_gate(
            self.repository_root,
            tampered,
            record["authorization"],
            now=_now(),
        )
        tamper_root = self.storage_root / run_id / "tamper-result"
        result = {
            "schema": "nma.ama-live-tamper-test/1.0",
            "tamper_test_id": _fresh_id("ama-tamper-test"),
            "protected_field": (
                "expected_final_state.derived_artifact.semantic_values.classification"
            ),
            "authorized_proposal_hash": original_hash,
            "tampered_recomputed_hash": observed_hash,
            "identity_changed": observed_hash != original_hash,
            "authorization": gate["status"],
            "execution_attempted": False,
            "mutation_started": False,
            "output_created": tamper_root.exists(),
            "status": (
                "PASS"
                if gate["status"] == "DENIED"
                and observed_hash != original_hash
                and not tamper_root.exists()
                else "FAIL"
            ),
            "checks": gate["checks"],
        }
        record["tamper_test"] = result
        self._save(record)
        return result

    def result_geojson(self, run_id: str) -> dict[str, Any]:
        record = self.get(run_id)
        if record.get("status") != "PASS":
            raise KeyError(run_id)
        return _read_json(self.storage_root / run_id / "result/derived-feature.geojson")

    def source_geojson(self) -> dict[str, Any]:
        protocol = _read_json(self.repository_root / "data/evaluation/rq2-demo-01-protocol.json")
        return _read_json(self.repository_root / protocol["fixture"])

    def domain_context(self) -> dict[str, Any]:
        graph = _read_json(self.repository_root / "data/knowledge/nma-canonical-graph-v0.4.json")
        wanted = {
            "classification:doc01:9350906",
            "portrayal-rule:doc01:9350906",
            "portrayal-recipe:doc01:9350906:review-v1",
            "portrayal-geometry:Point",
            "line-style:doc01:2",
            "portrayal-color:doc01:7",
        }
        nodes = [_bounded_node(item) for item in graph["nodes"] if item["id"] in wanted]
        ids = {item["id"] for item in nodes}
        edges = [item for item in graph["edges"] if item["source"] in ids and item["target"] in ids]
        return {"graph_id": graph["graph_id"], "nodes": nodes, "edges": edges}

    def rq1_comparison(self) -> dict[str, Any]:
        results = _read_json(self.repository_root / "rq1-compare-01-results.json")
        rows = []
        for architecture in ("llm-only", "text-rag", "graphrag"):
            item = results["aggregate"][architecture]
            rows.append(
                {
                    "architecture": architecture,
                    "requirement_accuracy": item["requirement_accuracy"]["mean"],
                    "coverage": item["coverage"]["mean"],
                    "latency_ms": item["total_latency_ms"]["mean"],
                }
            )
        return {
            "label": "CONTROLLED RESEARCH RESULT",
            "source": "rq1-compare-01-results.json",
            "rows": rows,
        }

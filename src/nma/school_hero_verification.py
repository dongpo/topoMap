from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
from typing import Any

from nma.core import canonical_json, canonical_sha256
from nma.real_layer import execute_real_layer, file_sha256
from nma.school_hero_execution import (
    ExecutionAuthorizationStore,
    SchoolHeroExecutionEngine,
    _materialize_asset,
    _real_layer_plan,
    authorization_sha256,
)


QA_SCHEMA = "nma.school-hero-qa/1.0"
PROVENANCE_SCHEMA = "nma.school-hero-provenance/1.0"
LINEAGE_SCHEMA = "nma.school-hero-upstream-lineage/1.0"
RUNTIME_CONTRACT = "nma.runtime-baseline/0.32"
RUNTIME_REVISION = RUNTIME_CONTRACT
SERVER_REVISION = "f03-school-hero-centered-edit-2026-08-12.4"
LINEAGE_KINDS = ("request", "intent", "evidence", "decision", "proposal", "approval")
CORE_ARTIFACTS = (
    "authorization.json",
    "plan.json",
    "receipt.json",
    "bundle.json",
    "data/school-point.geojson",
    "assets/school.svg",
)
GENERATED_ARTIFACTS = {"qa.json", "provenance.json", "rollback.json"}


class SchoolHeroVerificationError(ValueError):
    """The persisted HERO-04 execution cannot be inspected safely."""


def build_lineage_record(
    kind: str,
    identifier: str,
    payload: Any,
    *,
    parent_kind: str | None = None,
    parent_id: str | None = None,
) -> dict[str, Any]:
    """Build one content-addressed upstream record without inventing its payload."""

    if kind not in LINEAGE_KINDS:
        raise SchoolHeroVerificationError(f"Unsupported School Hero lineage kind: {kind}")
    parent = None
    if parent_kind is not None or parent_id is not None:
        if parent_kind not in LINEAGE_KINDS or not isinstance(parent_id, str) or not parent_id:
            raise SchoolHeroVerificationError("A complete lineage parent reference is required.")
        parent = {"kind": parent_kind, "id": parent_id}
    return {
        "kind": kind,
        "id": identifier,
        "parent": parent,
        "payload": deepcopy(payload),
        "payload_sha256": canonical_sha256(payload),
    }


def build_upstream_lineage(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap the six existing upstream records in their required logical order."""

    return {"schema": LINEAGE_SCHEMA, "records": deepcopy(records)}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SchoolHeroVerificationError(f"Unreadable JSON artifact: {path}") from error
    if not isinstance(value, dict):
        raise SchoolHeroVerificationError(f"JSON artifact is not an object: {path}")
    return value


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = deepcopy(value)
    result.pop(key, None)
    return result


def _check(
    checks: list[dict[str, Any]],
    identifier: str,
    passed: bool,
    *,
    expected: Any,
    observed: Any,
) -> bool:
    checks.append(
        {
            "id": identifier,
            "status": "passed" if passed else "failed",
            "expected": expected,
            "observed": observed,
        }
    )
    return passed


def _record_hash_is_valid(record: Any) -> bool:
    return (
        isinstance(record, dict)
        and isinstance(record.get("payload_sha256"), str)
        and record["payload_sha256"] == canonical_sha256(record.get("payload"))
    )


def _lineage_checks(
    authorization: dict[str, Any], checks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    lineage = authorization.get("upstream_lineage")
    records = lineage.get("records") if isinstance(lineage, dict) else None
    valid_shape = (
        isinstance(lineage, dict)
        and lineage.get("schema") == LINEAGE_SCHEMA
        and isinstance(records, list)
        and [item.get("kind") for item in records if isinstance(item, dict)] == list(LINEAGE_KINDS)
        and len(records) == len(LINEAGE_KINDS)
    )
    _check(
        checks,
        "complete_upstream_lineage",
        valid_shape,
        expected=list(LINEAGE_KINDS),
        observed=(
            [item.get("kind") for item in records if isinstance(item, dict)]
            if isinstance(records, list)
            else None
        ),
    )
    if not valid_shape:
        return []

    identifiers: dict[str, str] = {}
    unique_ids = True
    for record in records:
        kind = record.get("kind")
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in identifiers.values():
            unique_ids = False
        else:
            identifiers[kind] = identifier
    _check(
        checks,
        "unique_lineage_identifiers",
        unique_ids and len(identifiers) == len(LINEAGE_KINDS),
        expected="six non-empty unique identifiers",
        observed=identifiers,
    )

    hash_failures = [record.get("kind") for record in records if not _record_hash_is_valid(record)]
    _check(
        checks,
        "lineage_payload_hashes",
        not hash_failures,
        expected=[],
        observed=hash_failures,
    )

    invalid_references: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        expected_parent = (
            None
            if index == 0
            else {"kind": LINEAGE_KINDS[index - 1], "id": records[index - 1].get("id")}
        )
        if record.get("parent") != expected_parent:
            invalid_references.append(
                {
                    "kind": record.get("kind"),
                    "expected": expected_parent,
                    "observed": record.get("parent"),
                }
            )
    _check(
        checks,
        "valid_lineage_references",
        not invalid_references,
        expected=[],
        observed=invalid_references,
    )

    by_kind = {record["kind"]: record for record in records}
    intent_payload = by_kind["intent"].get("payload")
    _check(
        checks,
        "intent_contract",
        isinstance(intent_payload, dict) and intent_payload.get("schema") == "nma.intent-plan/0.5",
        expected="nma.intent-plan/0.5",
        observed=intent_payload.get("schema") if isinstance(intent_payload, dict) else None,
    )
    proposal = by_kind["proposal"]
    proposal_matches = (
        proposal.get("id") == authorization.get("proposal_id")
        and proposal.get("payload") == authorization.get("proposal_payload")
        and proposal.get("payload_sha256") == authorization.get("proposal_payload_sha256")
    )
    _check(
        checks,
        "lineage_proposal_binding",
        proposal_matches,
        expected={
            "id": authorization.get("proposal_id"),
            "payload_sha256": authorization.get("proposal_payload_sha256"),
        },
        observed={"id": proposal.get("id"), "payload_sha256": proposal.get("payload_sha256")},
    )
    decision = by_kind["decision"]
    _check(
        checks,
        "lineage_decision_binding",
        decision.get("payload") == authorization.get("validation_result"),
        expected=canonical_sha256(authorization.get("validation_result")),
        observed=decision.get("payload_sha256"),
    )
    approval = by_kind["approval"]
    approval_payload = approval.get("payload")
    approval_matches = (
        approval.get("id") == authorization.get("authorization_id")
        and approval_payload == authorization.get("human_approval")
        and isinstance(approval_payload, dict)
        and approval_payload.get("proposal_id") == authorization.get("proposal_id")
        and approval_payload.get("proposal_payload_sha256")
        == authorization.get("proposal_payload_sha256")
    )
    _check(
        checks,
        "approval_proposal_binding",
        approval_matches,
        expected={
            "approval_id": authorization.get("authorization_id"),
            "proposal_id": authorization.get("proposal_id"),
            "proposal_payload_sha256": authorization.get("proposal_payload_sha256"),
        },
        observed={
            "approval_id": approval.get("id"),
            "proposal_id": (
                approval_payload.get("proposal_id") if isinstance(approval_payload, dict) else None
            ),
            "proposal_payload_sha256": (
                approval_payload.get("proposal_payload_sha256")
                if isinstance(approval_payload, dict)
                else None
            ),
        },
    )
    return records


def _allowed_artifact(relative: str) -> bool:
    return (
        relative in CORE_ARTIFACTS
        or relative in GENERATED_ARTIFACTS
        or (relative.startswith("observations/") and relative.endswith(".json"))
    )


class SchoolHeroVerifier:
    """Deterministically verify one persisted HERO-04 state transition and its lineage."""

    def __init__(
        self,
        *,
        storage_root: str | Path,
        archive_path: str | Path,
        official_symbol_path: str | Path,
        repository_root: str | Path,
    ) -> None:
        self.storage_root = Path(storage_root)
        self.archive_path = Path(archive_path)
        self.official_symbol_path = Path(official_symbol_path)
        self.repository_root = Path(repository_root)

    def _execution_root(self, execution_id: str) -> Path:
        root = self.storage_root / "executions" / execution_id
        if not root.is_dir():
            raise SchoolHeroVerificationError(f"Execution not found: {execution_id}")
        return root

    def _runtime_identity(self, checks: list[dict[str, Any]]) -> dict[str, Any]:
        baseline_path = self.repository_root / "data/runtime/nma-runtime-baseline-v0.32.json"
        baseline = _load_json(baseline_path)
        graph_entry = baseline.get("canonical_graph", {})
        vector_entry = baseline.get("vector_index", {})
        agent_entry = baseline.get("agent_server", {})
        graph_path = self.repository_root / str(graph_entry.get("path", ""))
        vector_path = self.repository_root / str(vector_entry.get("required_path", ""))
        graph_actual = file_sha256(graph_path) if graph_path.is_file() else None
        vector_actual = file_sha256(vector_path) if vector_path.is_file() else None
        vector_payload = _load_json(vector_path) if vector_path.is_file() else {}
        graph_payload = _load_json(graph_path) if graph_path.is_file() else {}
        _check(
            checks,
            "runtime_contract",
            baseline.get("schema") == RUNTIME_CONTRACT
            and agent_entry.get("runtime_contract") == RUNTIME_CONTRACT
            and agent_entry.get("runtime_revision") == RUNTIME_REVISION,
            expected={"contract": RUNTIME_CONTRACT, "revision": RUNTIME_REVISION},
            observed={
                "contract": agent_entry.get("runtime_contract"),
                "revision": agent_entry.get("runtime_revision"),
            },
        )
        _check(
            checks,
            "canonical_graph_identity",
            graph_actual == graph_entry.get("sha256"),
            expected=graph_entry.get("sha256"),
            observed=graph_actual,
        )
        _check(
            checks,
            "vector_identity",
            vector_actual == vector_entry.get("sha256")
            and vector_payload.get("canonical_graph_sha256") == graph_actual,
            expected={
                "sha256": vector_entry.get("sha256"),
                "canonical_graph_sha256": graph_actual,
            },
            observed={
                "sha256": vector_actual,
                "canonical_graph_sha256": vector_payload.get("canonical_graph_sha256"),
            },
        )
        return {
            "runtime_contract": RUNTIME_CONTRACT,
            "runtime_revision": RUNTIME_REVISION,
            "server_revision": SERVER_REVISION,
            "canonical_graph": {
                "id": graph_payload.get("graph_id"),
                "sha256": graph_actual,
            },
            "vector_index": {
                "id": vector_payload.get("index_id"),
                "sha256": vector_actual,
                "canonical_graph_sha256": vector_payload.get("canonical_graph_sha256"),
            },
        }

    def verify(self, execution_id: str, *, persist: bool = True) -> dict[str, Any]:
        root = self._execution_root(execution_id)
        missing = [relative for relative in CORE_ARTIFACTS if not (root / relative).is_file()]
        if missing:
            raise SchoolHeroVerificationError(
                "Execution is missing required artifacts: " + ", ".join(missing)
            )
        authorization = _load_json(root / "authorization.json")
        plan = _load_json(root / "plan.json")
        receipt = _load_json(root / "receipt.json")
        bundle = _load_json(root / "bundle.json")
        observed_data = _load_json(root / "data/school-point.geojson")

        qa_checks: list[dict[str, Any]] = []
        provenance_checks: list[dict[str, Any]] = []
        auth_hash_valid = authorization.get("authorization_hash") == authorization_sha256(
            authorization
        )
        _check(
            provenance_checks,
            "authorization_hash",
            auth_hash_valid,
            expected=authorization_sha256(authorization),
            observed=authorization.get("authorization_hash"),
        )
        _check(
            qa_checks,
            "plan_hash",
            plan.get("plan_sha256") == canonical_sha256(_without(plan, "plan_sha256")),
            expected=canonical_sha256(_without(plan, "plan_sha256")),
            observed=plan.get("plan_sha256"),
        )
        _check(
            qa_checks,
            "receipt_hash",
            receipt.get("receipt_sha256") == canonical_sha256(_without(receipt, "receipt_sha256")),
            expected=canonical_sha256(_without(receipt, "receipt_sha256")),
            observed=receipt.get("receipt_sha256"),
        )
        _check(
            qa_checks,
            "bundle_hash",
            bundle.get("bundle_sha256") == canonical_sha256(_without(bundle, "bundle_sha256")),
            expected=canonical_sha256(_without(bundle, "bundle_sha256")),
            observed=bundle.get("bundle_sha256"),
        )

        source_actual = file_sha256(self.archive_path) if self.archive_path.is_file() else None
        baseline_actual = (
            file_sha256(self.official_symbol_path) if self.official_symbol_path.is_file() else None
        )
        input_identity = {
            "source_archive": {
                "path": str(self.archive_path),
                "sha256": source_actual,
            },
            "portrayal_baseline": {
                "id": authorization.get("baseline_identity", {}).get("id"),
                "path": str(self.official_symbol_path),
                "sha256": baseline_actual,
            },
        }
        input_matches = source_actual == authorization.get(
            "source_archive_sha256"
        ) and baseline_actual == authorization.get("baseline_identity", {}).get("sha256")
        _check(
            qa_checks,
            "input_artifact_identity",
            input_matches,
            expected={
                "source_archive_sha256": authorization.get("source_archive_sha256"),
                "baseline_sha256": authorization.get("baseline_identity", {}).get("sha256"),
            },
            observed={
                "source_archive_sha256": source_actual,
                "baseline_sha256": baseline_actual,
            },
        )

        engine = SchoolHeroExecutionEngine(
            storage_root=self.storage_root,
            archive_path=self.archive_path,
            official_symbol_path=self.official_symbol_path,
            authorization_store=ExecutionAuthorizationStore(self.storage_root / "authorizations"),
        )
        expected_plan = engine.build_plan(authorization, execution_id)
        _check(
            qa_checks,
            "approved_execution_plan",
            plan == expected_plan,
            expected=expected_plan,
            observed=plan,
        )

        expected_data: dict[str, Any] | None = None
        expected_asset: dict[str, Any] | None = None
        expected_bundle: dict[str, Any] | None = None
        expected_svg_hash: str | None = None
        expected_data_hash: str | None = None
        if input_matches:
            try:
                with tempfile.TemporaryDirectory(prefix="nma-hero05-verify-") as temporary:
                    temporary_root = Path(temporary)
                    expected_observation = execute_real_layer(
                        _real_layer_plan(expected_plan),
                        approval={
                            "decision": "approved",
                            "plan_id": _real_layer_plan(expected_plan)["plan_id"],
                        },
                        archive_path=self.archive_path,
                        output_dir=temporary_root / "data",
                    )
                    expected_data_path = Path(expected_observation["output_path"])
                    expected_data = _load_json(expected_data_path)
                    expected_data_hash = file_sha256(expected_data_path)
                    expected_asset = _materialize_asset(
                        self.official_symbol_path,
                        temporary_root / "assets/school.svg",
                        authorization.get("approved_operations", []),
                    )
                    expected_svg_hash = expected_asset["asset_sha256"]
                    expected_bundle = engine._build_bundle(
                        execution_id, expected_plan, expected_asset
                    )
            except Exception as error:  # fail closed; the exact reason is evidence
                _check(
                    qa_checks,
                    "expected_state_derivation",
                    False,
                    expected="deterministic expected state",
                    observed={"error": type(error).__name__, "message": str(error)},
                )
        else:
            _check(
                qa_checks,
                "expected_state_derivation",
                False,
                expected="verified input artifacts",
                observed="input identity mismatch",
            )

        if expected_data is not None and expected_asset is not None and expected_bundle is not None:
            _check(
                qa_checks,
                "expected_state_derivation",
                True,
                expected="deterministic expected state",
                observed="derived",
            )
            _check(
                qa_checks,
                "observed_data_state",
                observed_data == expected_data,
                expected={"sha256": expected_data_hash, "feature_count": 15},
                observed={
                    "sha256": file_sha256(root / "data/school-point.geojson"),
                    "feature_count": len(observed_data.get("features", [])),
                },
            )
            actual_svg_hash = file_sha256(root / "assets/school.svg")
            _check(
                qa_checks,
                "observed_portrayal_state",
                actual_svg_hash == expected_svg_hash,
                expected={
                    "sha256": expected_svg_hash,
                    "values": expected_asset.get("values"),
                },
                observed={"sha256": actual_svg_hash},
            )
            _check(
                qa_checks,
                "observed_map_state",
                bundle == expected_bundle,
                expected=expected_bundle,
                observed=bundle,
            )

        execution_binding = (
            plan.get("execution_id") == execution_id == receipt.get("execution_id")
            and plan.get("authorization_id") == authorization.get("authorization_id")
            and plan.get("authorization_hash") == authorization.get("authorization_hash")
            and receipt.get("authorization")
            == {
                "authorization_id": authorization.get("authorization_id"),
                "authorization_hash": authorization.get("authorization_hash"),
            }
            and receipt.get("proposal")
            == {
                "proposal_id": authorization.get("proposal_id"),
                "revision": authorization.get("proposal_revision"),
                "proposal_hash": authorization.get("proposal_payload_sha256"),
            }
        )
        _check(
            provenance_checks,
            "execution_proposal_binding",
            execution_binding,
            expected={
                "execution_id": execution_id,
                "authorization_id": authorization.get("authorization_id"),
                "proposal_id": authorization.get("proposal_id"),
                "proposal_hash": authorization.get("proposal_payload_sha256"),
            },
            observed={
                "plan_execution_id": plan.get("execution_id"),
                "receipt_execution_id": receipt.get("execution_id"),
                "plan_authorization_id": plan.get("authorization_id"),
                "receipt_authorization": receipt.get("authorization"),
                "receipt_proposal": receipt.get("proposal"),
            },
        )
        output_binding = (
            receipt.get("output", {}).get("geojson_hash")
            == file_sha256(root / "data/school-point.geojson")
            and receipt.get("portrayal", {}).get("asset_hash")
            == file_sha256(root / "assets/school.svg")
            and receipt.get("map", {}).get("bundle_hash") == bundle.get("bundle_sha256")
        )
        _check(
            provenance_checks,
            "execution_artifact_hashes",
            output_binding,
            expected={
                "geojson_hash": receipt.get("output", {}).get("geojson_hash"),
                "asset_hash": receipt.get("portrayal", {}).get("asset_hash"),
                "bundle_hash": receipt.get("map", {}).get("bundle_hash"),
            },
            observed={
                "geojson_hash": file_sha256(root / "data/school-point.geojson"),
                "asset_hash": file_sha256(root / "assets/school.svg"),
                "bundle_hash": bundle.get("bundle_sha256"),
            },
        )

        actual_files = sorted(
            path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
        )
        unexpected_files = [
            relative for relative in actual_files if not _allowed_artifact(relative)
        ]
        _check(
            qa_checks,
            "unexpected_modifications",
            not unexpected_files,
            expected=[],
            observed=unexpected_files,
        )

        core_hashes = {relative: file_sha256(root / relative) for relative in CORE_ARTIFACTS}
        output_identity = {
            "artifact_set_sha256": canonical_sha256(core_hashes),
            "artifacts": core_hashes,
        }
        target_identity = {
            "feature": deepcopy(authorization.get("feature_identity")),
            "profile_id": plan.get("profile_id"),
            "source_id": bundle.get("source", {}).get("id"),
            "layer_id": bundle.get("layer", {}).get("id"),
            "asset_path": "assets/school.svg",
        }
        expected_transition = {
            "input": input_identity,
            "target": target_identity,
            "proposal_id": authorization.get("proposal_id"),
            "proposal_payload_sha256": authorization.get("proposal_payload_sha256"),
            "approved_operations": deepcopy(authorization.get("approved_operations")),
            "data_sha256": expected_data_hash,
            "portrayal_sha256": expected_svg_hash,
            "bundle_sha256": (
                expected_bundle.get("bundle_sha256") if expected_bundle is not None else None
            ),
        }
        observed_transition = {
            "input": input_identity,
            "target": target_identity,
            "data_sha256": file_sha256(root / "data/school-point.geojson"),
            "portrayal_sha256": file_sha256(root / "assets/school.svg"),
            "bundle_sha256": bundle.get("bundle_sha256"),
            "output": output_identity,
        }
        qa_passed = all(check["status"] == "passed" for check in qa_checks)
        failed_ids = [check["id"] for check in qa_checks if check["status"] == "failed"]
        if "unexpected_modifications" in failed_ids:
            classification = "unexpected-additional-change"
        elif "observed_portrayal_state" in failed_ids and baseline_actual == file_sha256(
            root / "assets/school.svg"
        ):
            classification = "expected-change-missing"
        elif failed_ids:
            classification = "incorrect-change"
        else:
            classification = "expected-change-verified"
        qa_base = {
            "schema": QA_SCHEMA,
            "qa_id": "qa-"
            + canonical_sha256({"execution_id": execution_id, "artifact_set": output_identity})[
                :24
            ],
            "execution_id": execution_id,
            "status": "passed" if qa_passed else "failed",
            "classification": classification,
            "expected_transition": expected_transition,
            "observed_transition": observed_transition,
            "checks": qa_checks,
        }
        qa = {**qa_base, "qa_sha256": canonical_sha256(qa_base)}

        lineage_records = _lineage_checks(authorization, provenance_checks)
        runtime_identity = self._runtime_identity(provenance_checks)
        _check(
            provenance_checks,
            "qa_binding",
            qa_passed,
            expected="passed",
            observed=qa["status"],
        )
        provenance_passed = all(check["status"] == "passed" for check in provenance_checks)
        chain = [
            {
                "kind": record.get("kind"),
                "id": record.get("id"),
                "sha256": record.get("payload_sha256"),
            }
            for record in lineage_records
        ]
        chain.extend(
            [
                {
                    "kind": "execution",
                    "id": execution_id,
                    "sha256": receipt.get("receipt_sha256"),
                },
                {"kind": "qa", "id": qa["qa_id"], "sha256": qa["qa_sha256"]},
                {
                    "kind": "artifact",
                    "id": "artifact-set:" + execution_id,
                    "sha256": output_identity["artifact_set_sha256"],
                },
            ]
        )
        provenance_base = {
            "schema": PROVENANCE_SCHEMA,
            "provenance_id": "provenance-"
            + canonical_sha256(
                {
                    "execution_id": execution_id,
                    "qa_sha256": qa["qa_sha256"],
                    "artifact_set_sha256": output_identity["artifact_set_sha256"],
                }
            )[:24],
            "execution_id": execution_id,
            "status": "verified" if provenance_passed else "failed",
            "chain": chain,
            "runtime_identity": runtime_identity,
            "input_artifact_identity": input_identity,
            "output_artifact_identity": output_identity,
            "checks": provenance_checks,
        }
        provenance = {
            **provenance_base,
            "provenance_sha256": canonical_sha256(provenance_base),
        }
        result = {
            "status": "verified" if qa_passed and provenance_passed else "failed",
            "qa": qa,
            "provenance": provenance,
        }
        if persist:
            (root / "qa.json").write_bytes(canonical_json(qa) + b"\n")
            (root / "provenance.json").write_bytes(canonical_json(provenance) + b"\n")
        return result

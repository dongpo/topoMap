from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from nma.real_layer import extract_reviewed_source_layers, file_sha256
from nma.specification import Specification
from nma.validator import Validator


QA_PLAN_SCHEMA = "nma.qa-repair-plan/0.4"
QA_OBSERVATION_SCHEMA = "nma.qa-repair-observation/0.4"
SHAPEFILE_PARTS = (".shp", ".shx", ".dbf", ".prj", ".cpg")
PLAN_KEYS = (
    "schema",
    "profile_id",
    "dataset_kind",
    "source_components",
    "specification_sha256",
    "before_status",
    "before_issue_keys",
    "safe_repairs",
    "manual_review_issue_keys",
    "evidence_node_ids",
    "citation_ids",
)


class QAReviewError(ValueError):
    """A VS4 QA proposal or repair crossed its reviewed boundary."""


QA_PROFILES: dict[str, dict[str, Any]] = {
    "riverl-controlled-defect": {
        "dataset": "data/datasets/authoritative/riverl-defective/RIVERL.shp",
        "specification": "data/specifications/taiwan-5000-riverl-112.json",
        "dataset_kind": "controlled-synthetic-defect-fixture",
        "layer": "RIVERL",
        "expected_before_issue_keys": [
            "TW-RIVERL-DOMAIN-001|index:1|TERRAINID",
            "TW-RIVERL-FORMAT-001|index:1|RIVERLNAME",
            "TW-RIVERL-REQUIRED-001|index:1|RIVERLID",
            "TW-RIVERL-TOPO-001|J0000000003@index:2|-",
        ],
        "expected_safe_issue_keys": [
            "TW-RIVERL-FORMAT-001|index:1|RIVERLNAME",
        ],
        "evidence_node_ids": [
            "quality-item:doc03-213",
            "quality-item:doc10-06",
            "quality-rule:doc03-all-errors-corrected",
            "quality-rule:doc03-failure-full-correction",
        ],
        "boundary": (
            "This dataset is a controlled synthetic defect fixture used to verify the QA and "
            "repair loop. It is not presented as an observed defect in the uploaded archive."
        ),
    }
}

REAL_QA_DIAGNOSTIC_PROFILES: dict[str, dict[str, Any]] = {
    "mark-real-point": {
        "source_layer_ids": [
            "J01_MARK",
            "J13_MARK",
            "J17_MARK",
            "K01_MARK",
            "K02_MARK",
            "K14_MARK",
        ],
        "specification": "data/specifications/taiwan-temap-mark-v0.4.json",
        "geometry_role": "Point",
        "expected_features": 1464,
        "expected_issues": 30,
        "evidence_query": "MARK doc10-08 doc03-213 all-errors-corrected",
        "evidence_node_ids": [
            "quality-item:doc10-08",
            "quality-item:doc03-213",
            "quality-rule:doc03-all-errors-corrected"
        ],
        "boundary": (
            "All six real MARK sources consistently omit Document 09 MARKTYPE1, MARKTYPE2, "
            "MARKNAME2, ADDRESS and TEL while exposing TERRAINID. No equivalence, field "
            "invention or automatic repair is asserted."
        ),
    },
    "build-real-polygon": {
        "source_layer_ids": ["J17_BUILD"],
        "specification": "data/specifications/taiwan-temap-build-v0.4.json",
        "geometry_role": "Polygon",
        "expected_features": 2839,
        "expected_issues": 2,
        "evidence_query": "BUILD doc10-06 doc03-213 all-errors-corrected",
        "evidence_node_ids": [
            "quality-item:doc10-06",
            "quality-item:doc03-213",
            "quality-rule:doc03-all-errors-corrected"
        ],
        "boundary": (
            "The real J17 BUILD source exposes BUILD_ID, TERRAINID, BUILD_STR, BUILD_NO, BUILD_H "
            "and GROUP_ID, while Document 09 specifies ID and SOURCE. No equivalence, field "
            "invention or automatic repair is asserted."
        ),
    },
}


def real_diagnosis_qa_plan(
    diagnosis: dict[str, Any], *, evidence_package: dict[str, Any]
) -> dict[str, Any]:
    profile = REAL_QA_DIAGNOSTIC_PROFILES[diagnosis["profile_id"]]
    evidence = _validate_evidence(profile, evidence_package)
    issues = []
    for item in diagnosis["reports"]:
        for issue in item["report"]["issues"]:
            issues.append(
                {
                    **issue,
                    "issue_key": f"{item['source_layer']}::{issue['issue_key']}",
                    "source_layer": item["source_layer"],
                }
            )
    basis = {
        "profile_id": diagnosis["profile_id"],
        "source_archive_sha256": diagnosis["source_archive_sha256"],
        "specification_sha256": diagnosis["specification_sha256"],
        "issue_keys": diagnosis["issue_keys"],
        "evidence_node_ids": evidence["evidence_node_ids"],
        "citation_ids": evidence["citation_ids"],
    }
    plan_id = "qa-diagnosis:" + hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:20]
    return {
        "schema": "nma.qa-diagnosis-plan/0.4",
        "plan_id": plan_id,
        "profile_id": diagnosis["profile_id"],
        "dataset_kind": diagnosis["dataset_kind"],
        "geometry_role": diagnosis["geometry_role"],
        "boundary": diagnosis["boundary"],
        "before_status": "failed" if diagnosis["issue_keys"] else "passed",
        "before_report": {
            "status": "failed" if diagnosis["issue_keys"] else "passed",
            "summary": diagnosis["summary"],
            "issues": issues,
        },
        "safe_repairs": [],
        "manual_review_issue_keys": diagnosis["manual_review_issue_keys"],
        "evidence_node_ids": evidence["evidence_node_ids"],
        "citation_ids": evidence["citation_ids"],
        "source_mutation_performed": False,
        "automatic_acceptance": False,
        "approval": {"required": False, "reason": "no-safe-repair-available"},
    }


def diagnose_real_vector_profile(
    *,
    profile_id: str,
    archive_path: str | Path,
    expected_archive_sha256: str,
    project_root: str | Path,
) -> dict[str, Any]:
    profile = REAL_QA_DIAGNOSTIC_PROFILES.get(profile_id)
    if not profile:
        raise QAReviewError(f"Unknown real QA diagnostic profile: {profile_id}")
    archive = Path(archive_path)
    if file_sha256(archive) != expected_archive_sha256:
        raise QAReviewError("The real QA archive checksum does not match the reviewed source.")
    specification_path = _rooted(project_root, profile["specification"])
    specification = Specification.load(specification_path)
    reports = []
    with tempfile.TemporaryDirectory(prefix=f"nma-{profile_id}-qa-") as temporary:
        paths, components = extract_reviewed_source_layers(
            archive, profile["source_layer_ids"], Path(temporary)
        )
        for path in paths:
            report = Validator(specification).validate_path(path)
            reports.append({"source_layer": path.stem, "report": report})
    total_features = sum(item["report"]["summary"]["features"] for item in reports)
    aggregate_issue_keys = sorted(
        f"{item['source_layer']}::{issue['issue_key']}"
        for item in reports
        for issue in item["report"]["issues"]
    )
    safe_issue_keys = sorted(
        f"{item['source_layer']}::{issue['issue_key']}"
        for item in reports
        for issue in item["report"]["issues"]
        if issue.get("repair", {}).get("mode") == "safe"
    )
    if total_features != profile["expected_features"]:
        raise QAReviewError("The real QA feature population changed.")
    if len(aggregate_issue_keys) != profile["expected_issues"]:
        raise QAReviewError("The real QA issue population changed.")
    if safe_issue_keys:
        raise QAReviewError("A real QA profile unexpectedly exposed a safe automatic repair.")
    return {
        "schema": "nma.real-source-qa-diagnosis/0.4",
        "status": "diagnosed-read-only",
        "profile_id": profile_id,
        "dataset_kind": "verified-private-real-source",
        "geometry_role": profile["geometry_role"],
        "source_archive": archive.name,
        "source_archive_sha256": expected_archive_sha256,
        "source_layers": profile["source_layer_ids"],
        "source_components": components,
        "specification": str(specification_path),
        "specification_sha256": file_sha256(specification_path),
        "reports": reports,
        "summary": {
            "source_layers": len(reports),
            "features": total_features,
            "rules_evaluated": sum(
                item["report"]["summary"]["rules_evaluated"] for item in reports
            ),
            "issues": len(aggregate_issue_keys),
            "errors": sum(item["report"]["summary"]["errors"] for item in reports),
            "warnings": sum(item["report"]["summary"]["warnings"] for item in reports),
            "safe_repairs_available": 0,
        },
        "issue_keys": aggregate_issue_keys,
        "safe_repair_issue_keys": [],
        "manual_review_issue_keys": aggregate_issue_keys,
        "source_mutated": False,
        "repair_proposed": False,
        "automatic_acceptance": False,
        "boundary": profile["boundary"],
    }


def diagnose_real_j17_river(
    *,
    archive_path: str | Path,
    expected_archive_sha256: str,
    specification_path: str | Path,
) -> dict[str, Any]:
    """Run the same deterministic RIVERL rules on the verified private J17 source, read-only."""

    archive = Path(archive_path)
    if file_sha256(archive) != expected_archive_sha256:
        raise QAReviewError("The real QA archive checksum does not match the reviewed source.")
    specification = Path(specification_path)
    with tempfile.TemporaryDirectory(prefix="nma-real-j17-qa-") as temporary:
        paths, components = extract_reviewed_source_layers(
            archive, ["J17_RIVERL"], Path(temporary)
        )
        report = Validator(Specification.load(specification)).validate_path(paths[0])
    return {
        "schema": "nma.real-source-qa-diagnosis/0.4",
        "status": "diagnosed-read-only",
        "dataset_kind": "verified-private-real-source",
        "source_archive": archive.name,
        "source_archive_sha256": expected_archive_sha256,
        "source_layers": ["J17_RIVERL"],
        "source_components": components,
        "specification_sha256": file_sha256(specification),
        "report": report,
        "safe_repair_issue_keys": [
            item["issue_key"]
            for item in report["issues"]
            if item.get("repair", {}).get("mode") == "safe"
        ],
        "manual_review_issue_keys": [
            item["issue_key"]
            for item in report["issues"]
            if item.get("repair", {}).get("mode") != "safe"
        ],
        "source_mutated": False,
        "repair_proposed": False,
        "automatic_acceptance": False,
        "boundary": (
            "The observed RIVERID versus specified RIVERLID difference is a real dataset-schema "
            "finding requiring authority review; it is not automatically renamed or repaired."
        ),
    }


def _rooted(root: str | Path, relative: str) -> Path:
    root_path = Path(root).resolve()
    path = (root_path / relative).resolve()
    if root_path not in path.parents:
        raise QAReviewError("The QA profile escaped the project root.")
    return path


def _component_records(source: Path) -> list[dict[str, Any]]:
    records = []
    for extension in SHAPEFILE_PARTS:
        component = source.with_suffix(extension)
        if extension in {".shp", ".shx", ".dbf", ".prj"} and not component.is_file():
            raise QAReviewError(f"The QA source is missing {component.name}.")
        if component.is_file():
            records.append(
                {
                    "extension": extension,
                    "filename": component.name,
                    "size_bytes": component.stat().st_size,
                    "sha256": file_sha256(component),
                }
            )
    return records


def _validate_evidence(profile: dict[str, Any], evidence_package: Any) -> dict[str, Any]:
    if not isinstance(evidence_package, dict) or evidence_package.get("status") != "retrieved":
        raise QAReviewError("A retrieved canonical GraphRAG evidence package is required.")
    nodes = {
        item.get("id")
        for item in evidence_package.get("evidence_nodes", [])
        if isinstance(item, dict)
    }
    missing = set(profile["evidence_node_ids"]) - nodes
    if missing:
        raise QAReviewError("Missing reviewed QA nodes: " + ", ".join(sorted(missing)))
    citations = [
        item
        for item in evidence_package.get("citations", [])
        if isinstance(item, dict) and item.get("citation_id")
    ]
    if not citations:
        raise QAReviewError("QA requires source citations.")
    return {
        "evidence_node_ids": profile["evidence_node_ids"],
        "citation_ids": [item["citation_id"] for item in citations],
    }


def _plan_id(plan: dict[str, Any]) -> str:
    try:
        basis = {key: plan[key] for key in PLAN_KEYS}
    except KeyError as error:
        raise QAReviewError(f"The QA plan is missing {error.args[0]}.") from error
    digest = hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return "qa-plan:" + digest[:20]


def propose_qa_review(
    *, profile_id: str, project_root: str | Path, evidence_package: dict[str, Any]
) -> dict[str, Any]:
    profile = QA_PROFILES.get(profile_id)
    if not profile:
        raise QAReviewError(f"Unknown reviewed QA profile: {profile_id}")
    evidence = _validate_evidence(profile, evidence_package)
    source = _rooted(project_root, profile["dataset"])
    specification_path = _rooted(project_root, profile["specification"])
    report = Validator(Specification.load(specification_path)).validate_path(source)
    issue_keys = sorted(item["issue_key"] for item in report["issues"])
    if issue_keys != sorted(profile["expected_before_issue_keys"]):
        raise QAReviewError("The controlled QA ground truth changed.")
    safe_repairs = []
    for issue in report["issues"]:
        repair = issue.get("repair", {})
        if repair.get("mode") != "safe":
            continue
        if repair.get("operation") != "trim" or issue.get("feature_index") is None:
            raise QAReviewError("The QA fixture contains an unreviewed safe repair operation.")
        before = issue.get("actual")
        if not isinstance(before, str):
            raise QAReviewError("The reviewed trim operation requires a string value.")
        safe_repairs.append(
            {
                "issue_key": issue["issue_key"],
                "operation": "trim",
                "feature_index": issue["feature_index"],
                "field": issue["field"],
                "before": before,
                "after": before.strip(),
            }
        )
    if sorted(item["issue_key"] for item in safe_repairs) != sorted(
        profile["expected_safe_issue_keys"]
    ):
        raise QAReviewError("The reviewed safe-repair set changed.")
    safe_keys = {item["issue_key"] for item in safe_repairs}
    plan_basis = {
        "schema": QA_PLAN_SCHEMA,
        "profile_id": profile_id,
        "dataset_kind": profile["dataset_kind"],
        "source_components": _component_records(source),
        "specification_sha256": file_sha256(specification_path),
        "before_status": report["status"],
        "before_issue_keys": issue_keys,
        "safe_repairs": safe_repairs,
        "manual_review_issue_keys": sorted(set(issue_keys) - safe_keys),
        "evidence_node_ids": evidence["evidence_node_ids"],
        "citation_ids": evidence["citation_ids"],
    }
    plan_id = _plan_id(plan_basis)
    return {
        **plan_basis,
        "plan_id": plan_id,
        "status": "proposed",
        "dataset": str(source),
        "specification": str(specification_path),
        "before_report": report,
        "boundary": profile["boundary"],
        "approval": {"required": True, "decision": "pending", "plan_id": plan_id},
        "source_mutation_performed": False,
        "automatic_acceptance": False,
    }


def _dbf_encoding(source: Path) -> str:
    cpg = source.with_suffix(".cpg")
    if not cpg.is_file():
        return "utf-8"
    label = cpg.read_text(encoding="ascii", errors="ignore").strip().lower()
    return {"utf-8": "utf-8", "utf8": "utf-8", "950": "cp950", "big5": "cp950"}.get(
        label, label or "utf-8"
    )


def _patch_dbf_trim(dbf_path: Path, repairs: list[dict[str, Any]], *, encoding: str) -> None:
    data = bytearray(dbf_path.read_bytes())
    if len(data) < 33:
        raise QAReviewError("The derived DBF header is invalid.")
    header_length = int.from_bytes(data[8:10], "little")
    record_length = int.from_bytes(data[10:12], "little")
    record_count = int.from_bytes(data[4:8], "little")
    fields: dict[str, tuple[int, int, str]] = {}
    offset = 1
    cursor = 32
    while cursor + 32 <= header_length and data[cursor] != 0x0D:
        descriptor = data[cursor : cursor + 32]
        name = bytes(descriptor[:11]).split(b"\x00", 1)[0].decode("ascii")
        field_type = chr(descriptor[11])
        width = descriptor[16]
        fields[name] = (offset, width, field_type)
        offset += width
        cursor += 32
    for repair in repairs:
        field = repair["field"]
        if field not in fields:
            raise QAReviewError(f"The derived DBF is missing {field}.")
        field_offset, width, field_type = fields[field]
        if field_type != "C":
            raise QAReviewError("Only DBF character fields may use the reviewed trim repair.")
        index = int(repair["feature_index"])
        if index < 0 or index >= record_count:
            raise QAReviewError("The reviewed DBF record index is out of range.")
        start = header_length + index * record_length + field_offset
        end = start + width
        current = bytes(data[start:end]).rstrip(b" ").decode(encoding)
        if current != repair["before"]:
            raise QAReviewError("The DBF value changed after the QA proposal.")
        replacement = repair["after"].encode(encoding)
        if len(replacement) > width:
            raise QAReviewError("The repaired DBF value exceeds the fixed field width.")
        data[start:end] = replacement.ljust(width, b" ")
    dbf_path.write_bytes(data)


def execute_qa_repair(
    plan: dict[str, Any],
    *,
    approval: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != QA_PLAN_SCHEMA:
        raise QAReviewError("A valid QA proposal is required.")
    if plan.get("plan_id") != _plan_id(plan):
        raise QAReviewError("The QA plan changed after inspection.")
    if approval != {"decision": "approved", "plan_id": plan["plan_id"]}:
        raise QAReviewError("Explicit approval for this exact QA plan is required.")
    source = Path(plan["dataset"])
    specification_path = Path(plan["specification"])
    if _component_records(source) != plan["source_components"]:
        raise QAReviewError("The QA source changed after the proposal.")
    if file_sha256(specification_path) != plan["specification_sha256"]:
        raise QAReviewError("The QA specification changed after the proposal.")
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    target = output_root / source.name
    for component in plan["source_components"]:
        source_part = source.with_suffix(component["extension"])
        target_part = target.with_suffix(component["extension"])
        shutil.copy2(source_part, target_part)
    _patch_dbf_trim(
        target.with_suffix(".dbf"),
        plan["safe_repairs"],
        encoding=_dbf_encoding(source),
    )
    after = Validator(Specification.load(specification_path)).validate_path(target)
    after_keys = sorted(item["issue_key"] for item in after["issues"])
    safe_keys = sorted(item["issue_key"] for item in plan["safe_repairs"])
    expected_after = sorted(set(plan["before_issue_keys"]) - set(safe_keys))
    if after_keys != expected_after:
        raise QAReviewError("Reinspection did not match the approved repair boundary.")
    output_components = _component_records(target)
    source_hashes = {item["extension"]: item["sha256"] for item in plan["source_components"]}
    output_hashes = {item["extension"]: item["sha256"] for item in output_components}
    unchanged_parts = sorted(
        extension
        for extension in source_hashes
        if extension != ".dbf" and source_hashes[extension] == output_hashes[extension]
    )
    if set(unchanged_parts) != set(source_hashes) - {".dbf"}:
        raise QAReviewError("The bounded attribute repair changed another Shapefile component.")
    audit = {
        "schema": QA_OBSERVATION_SCHEMA,
        "status": "reinspected-after-approved-repair",
        "plan_id": plan["plan_id"],
        "dataset_kind": plan["dataset_kind"],
        "source_components": plan["source_components"],
        "output_components": output_components,
        "repairs_applied": [
            {**item, "approved": True, "reversible": True} for item in plan["safe_repairs"]
        ],
        "before": {
            "status": plan["before_status"],
            "issue_keys": plan["before_issue_keys"],
        },
        "after": {"status": after["status"], "issue_keys": after_keys, "report": after},
        "resolved_issue_keys": safe_keys,
        "remaining_manual_review_issue_keys": plan["manual_review_issue_keys"],
        "new_issue_keys": [],
        "source_mutated": False,
        "derived_output": str(target),
        "rollback": "discard the derived output; the source Shapefile remains byte-identical",
        "automatic_acceptance": False,
    }
    audit_path = output_root / "qa-audit.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {**audit, "audit_path": str(audit_path), "audit_sha256": file_sha256(audit_path)}

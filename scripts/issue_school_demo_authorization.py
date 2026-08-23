#!/usr/bin/env python3
"""Issue the one bounded DEMO-AUTH-01 School authorization through HERO-03 machinery."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from nma.core import canonical_sha256
from nma.intent_planning_v05 import plan_intent
from nma.real_layer import file_sha256
from nma.school_hero_execution import (
    ExecutionAuthorizationStore,
    ExecutionAuthorizationVerifier,
    authorization_sha256,
)
from nma.school_hero_verification import build_lineage_record, build_upstream_lineage


ROOT = Path(__file__).resolve().parents[1]
CONTROLLED_BASELINE_PATH = (
    ROOT / "data/specifications/nma-demo-controlled-fixture-baseline-v1.0.json"
)
DEFAULT_ARCHIVE_PATH = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
DEFAULT_AUTHORIZATION_ROOT = ROOT / "artifacts/runtime/school-hero/authorizations"
OFFICIAL_SYMBOL_PATH = ROOT / "assets/symbols/nlsc112v5.4/school.svg"

AUTHORIZATION_SCHEMA = "nma.symbol-edit-authorization/1.0"
CONTROLLED_FIXTURE_IDENTITY = (
    "nma-demo-fixture:school:sha256:"
    "77802b44b97c6687bc626d257e14b57c3d7427949a65942fa721d05bb79fc12d"
)
CONTROLLED_FIXTURE_SHA256 = "77802b44b97c6687bc626d257e14b57c3d7427949a65942fa721d05bb79fc12d"
CONTROLLED_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
OFFICIAL_SYMBOL_SHA256 = "bb3a683f8f4a4250845fec71f678feddd8b50b97d77ceddb65ed5f38f5e0af86"
HISTORICAL_AUTHORIZATION_ID = "authorization-school-blue"
SCHOOL_FEATURE_CODE = "9920103"
SOURCE_LAYERS = ["J01_MARK", "J13_MARK", "J17_MARK", "K01_MARK", "K02_MARK", "K14_MARK"]
EXPECTED_LAYER_COUNTS = [0, 1, 0, 12, 1, 1]
EXECUTION_SCOPE = ["derived-real-layer", "derived-portrayal", "candidate-maplibre-layer"]
ISSUED_AT = "2026-08-23T00:00:00Z"
EXPIRES_AT = "2030-01-01T00:00:00Z"
REQUEST_TEXT = "Change the school 9920103 derived symbol color to blue."


class SchoolDemoAuthorizationIssuanceError(ValueError):
    """The bounded DEMO-AUTH-01 issuance request failed closed."""


def _controlled_binding() -> dict[str, Any]:
    return {
        "purpose": "controlled-school-demo",
        "domain": "school",
        "fixture_identity": CONTROLLED_FIXTURE_IDENTITY,
        "fixture_aggregate_sha256": CONTROLLED_FIXTURE_SHA256,
        "fixture_role": "controlled-demo-input",
        "source_archive_sha256": CONTROLLED_ARCHIVE_SHA256,
        "source_layers": deepcopy(SOURCE_LAYERS),
        "source_filter": {
            "field": "TERRAINID",
            "operator": "equals",
            "value": SCHOOL_FEATURE_CODE,
        },
        "expected_layer_feature_counts": deepcopy(EXPECTED_LAYER_COUNTS),
        "expected_feature_count": 15,
        "geometry_role": "Point",
        "operation_class": "school-symbol-derived-layer-portrayal",
        "execution_scope": deepcopy(EXECUTION_SCOPE),
        "bounded_demo_execution": True,
        "production_writeback": False,
        "repair": False,
        "production_activation": False,
    }


def _verify_controlled_baseline() -> dict[str, Any]:
    try:
        baseline = json.loads(CONTROLLED_BASELINE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SchoolDemoAuthorizationIssuanceError(
            "The DEMO-FIXTURE-00 baseline is unavailable or unreadable."
        ) from error
    school = baseline.get("school", {})
    observed_layers = [layer.get("layer_id") for layer in school.get("layers", [])]
    observed_counts = [layer.get("selected_feature_count") for layer in school.get("layers", [])]
    expected = _controlled_binding()
    if (
        school.get("controlled_demo_fixture_identity") != CONTROLLED_FIXTURE_IDENTITY
        or school.get("aggregate_sha256") != CONTROLLED_FIXTURE_SHA256
        or baseline.get("fixture_authority", {}).get("package_sha256") != CONTROLLED_ARCHIVE_SHA256
        or observed_layers != SOURCE_LAYERS
        or observed_counts != EXPECTED_LAYER_COUNTS
        or school.get("source_filter") != expected["source_filter"]
        or school.get("geometry_quality", {}).get("selected_feature_count") != 15
        or school.get("geometry_quality", {}).get("declared_geometry") != "Point"
    ):
        raise SchoolDemoAuthorizationIssuanceError(
            "The DEMO-FIXTURE-00 School identity or six-layer/15-feature contract changed."
        )
    return baseline


def build_school_demo_authorization(
    *, human_approved: bool, archive_sha256: str = CONTROLLED_ARCHIVE_SHA256
) -> dict[str, Any]:
    """Build only the exact human-approved DEMO-AUTH-01 capability."""

    if human_approved is not True:
        raise SchoolDemoAuthorizationIssuanceError(
            "Explicit human approval is required; authorization was not issued."
        )
    if archive_sha256 != CONTROLLED_ARCHIVE_SHA256:
        raise SchoolDemoAuthorizationIssuanceError(
            "The supplied archive is not the controlled DEMO-FIXTURE-00 package."
        )
    _verify_controlled_baseline()
    if file_sha256(OFFICIAL_SYMBOL_PATH) != OFFICIAL_SYMBOL_SHA256:
        raise SchoolDemoAuthorizationIssuanceError("The frozen School portrayal baseline changed.")

    binding = _controlled_binding()
    feature = {"code": SCHOOL_FEATURE_CODE, "geometry_role": "Point"}
    baseline_identity = {
        "id": "official-school-symbol-v5.4",
        "sha256": OFFICIAL_SYMBOL_SHA256,
    }
    operations = [{"action": "set_color", "target": "symbol", "value": {"color": "#1565c0"}}]
    proposal_basis = {
        "revision": "demo-auth-01",
        "feature_identity": feature,
        "baseline_identity": baseline_identity,
        "operations": operations,
        "demo_binding": binding,
    }
    proposal_id = "proposal-school-demo-" + canonical_sha256(proposal_basis)[:24]
    proposal_payload = {"proposal_id": proposal_id, **proposal_basis}
    proposal_hash = canonical_sha256(proposal_payload)
    identity = {
        "proposal_id": proposal_id,
        "proposal_revision": proposal_payload["revision"],
        "proposal_payload_sha256": proposal_hash,
        "feature_identity": feature,
        "baseline_identity": baseline_identity,
    }
    validation_result = {
        "status": "passed",
        **identity,
        "controlled_fixture_identity": CONTROLLED_FIXTURE_IDENTITY,
        "demo_scope_sha256": canonical_sha256(binding),
    }
    human_approval = {
        "decision": "approved",
        "actor_type": "human",
        "approved_operations_sha256": canonical_sha256(operations),
        **identity,
        "approved_fixture_identity": CONTROLLED_FIXTURE_IDENTITY,
        "approved_demo_scope_sha256": canonical_sha256(binding),
        "production_writeback_approved": False,
    }
    authorization_identity_basis = {
        "schema": AUTHORIZATION_SCHEMA,
        "purpose": binding["purpose"],
        "fixture_identity": CONTROLLED_FIXTURE_IDENTITY,
        "proposal_payload_sha256": proposal_hash,
        "human_approval": human_approval,
        "execution_scope": EXECUTION_SCOPE,
        "issued_at": ISSUED_AT,
        "expires_at": EXPIRES_AT,
    }
    authorization_id = (
        "authorization-school-demo-" + canonical_sha256(authorization_identity_basis)[:24]
    )
    if authorization_id == HISTORICAL_AUTHORIZATION_ID:
        raise SchoolDemoAuthorizationIssuanceError(
            "The demo authorization may not impersonate historical HERO-03 authority."
        )

    request_payload = {
        "text": REQUEST_TEXT,
        "automatic_execution": False,
        "controlled_fixture_identity": CONTROLLED_FIXTURE_IDENTITY,
        "production_writeback": False,
    }
    intent_payload = plan_intent(REQUEST_TEXT)
    evidence_payload = {
        "schema": "nma.demo-fixture-evidence/1.0",
        "record_path": CONTROLLED_BASELINE_PATH.relative_to(ROOT).as_posix(),
        "record_sha256": file_sha256(CONTROLLED_BASELINE_PATH),
        "controlled_fixture_identity": CONTROLLED_FIXTURE_IDENTITY,
        "fixture_aggregate_sha256": CONTROLLED_FIXTURE_SHA256,
        "source_layers": deepcopy(SOURCE_LAYERS),
        "selected_feature_counts": deepcopy(EXPECTED_LAYER_COUNTS),
        "selected_feature_count": 15,
        "feature_code": SCHOOL_FEATURE_CODE,
        "geometry_role": "Point",
        "graphrag_node_ids": [
            "code-value:landmark-type:9920103",
            "portrayal-rule:doc01:9920103",
            "portrayal-recipe:doc01:9920103:review-v1",
            "product-layer:MARK",
        ],
        "external_data_substitution": False,
    }
    request_id = "request:" + canonical_sha256(request_payload)[:20]
    intent_id = "intent:" + canonical_sha256(intent_payload)[:20]
    evidence_id = "evidence:" + canonical_sha256(evidence_payload)[:20]
    decision_id = "decision:" + canonical_sha256(validation_result)[:20]
    records = [
        build_lineage_record("request", request_id, request_payload),
        build_lineage_record(
            "intent", intent_id, intent_payload, parent_kind="request", parent_id=request_id
        ),
        build_lineage_record(
            "evidence",
            evidence_id,
            evidence_payload,
            parent_kind="intent",
            parent_id=intent_id,
        ),
        build_lineage_record(
            "decision",
            decision_id,
            validation_result,
            parent_kind="evidence",
            parent_id=evidence_id,
        ),
        build_lineage_record(
            "proposal",
            proposal_id,
            proposal_payload,
            parent_kind="decision",
            parent_id=decision_id,
        ),
        build_lineage_record(
            "approval",
            authorization_id,
            human_approval,
            parent_kind="proposal",
            parent_id=proposal_id,
        ),
    ]
    authorization = {
        "schema": AUTHORIZATION_SCHEMA,
        "authorization_id": authorization_id,
        "authorization_hash": "0" * 64,
        "status": "ready_for_execution",
        "execution_performed": False,
        "proposal_id": proposal_id,
        "proposal_revision": proposal_payload["revision"],
        "proposal_payload": proposal_payload,
        "proposal_payload_sha256": proposal_hash,
        "feature_identity": feature,
        "baseline_identity": baseline_identity,
        "validation_result": validation_result,
        "human_approval": human_approval,
        "approved_operations": operations,
        "portrayal_reference": {
            "asset_path": "assets/symbols/nlsc112v5.4/school.svg",
            "baseline_identity": baseline_identity,
            "approved_operations_sha256": canonical_sha256(operations),
        },
        "source_archive_sha256": CONTROLLED_ARCHIVE_SHA256,
        "execution_scope": deepcopy(EXECUTION_SCOPE),
        "issued_at": ISSUED_AT,
        "expires_at": EXPIRES_AT,
        "invalidation_status": "valid",
        "demo_binding": binding,
        "upstream_lineage": build_upstream_lineage(records),
    }
    authorization["authorization_hash"] = authorization_sha256(authorization)
    ExecutionAuthorizationVerifier().verify(authorization)
    return authorization


def issue_school_demo_authorization(
    *, archive_path: Path, output_root: Path, human_approved: bool
) -> Path:
    if not archive_path.is_file():
        raise SchoolDemoAuthorizationIssuanceError(
            "The controlled School fixture package is not available."
        )
    authorization = build_school_demo_authorization(
        human_approved=human_approved,
        archive_sha256=file_sha256(archive_path),
    )
    return ExecutionAuthorizationStore(output_root).save(authorization)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_AUTHORIZATION_ROOT)
    parser.add_argument(
        "--human-approved",
        action="store_true",
        help="Explicitly record the repository-supported human approval decision.",
    )
    args = parser.parse_args()
    try:
        output = issue_school_demo_authorization(
            archive_path=args.archive,
            output_root=args.output_root,
            human_approved=args.human_approved,
        )
    except SchoolDemoAuthorizationIssuanceError as error:
        parser.error(str(error))
    authorization = json.loads(output.read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "authorization_id": authorization["authorization_id"],
                "authorization_hash": authorization["authorization_hash"],
                "controlled_fixture_identity": CONTROLLED_FIXTURE_IDENTITY,
                "output": str(output),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

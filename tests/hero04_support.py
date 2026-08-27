from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

from nma.real_layer import file_sha256
from nma.school_hero_execution import (
    ExecutionAuthorizationStore,
    SchoolHeroExecutionEngine,
    authorization_sha256,
    canonical_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_SYMBOL = ROOT / "assets/symbols/nlsc112v5.4/school.svg"
EXPECTED_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"


def private_archive() -> Path:
    configured = os.environ.get("NMA_HERO04_PRIVATE_ARCHIVE")
    return (
        Path(configured)
        if configured
        else ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
    )


def make_authorization(
    *,
    archive_sha256: str = EXPECTED_ARCHIVE_SHA256,
    expires_at: str = "2030-01-01T00:00:00Z",
    status: str = "ready_for_execution",
    scope: list[str] | None = None,
    upstream_lineage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    feature = {"code": "9920103", "geometry_role": "Point"}
    baseline = {"id": "official-school-symbol-v5.4", "sha256": file_sha256(OFFICIAL_SYMBOL)}
    operations = [
        {"action": "set_color", "target": "symbol", "value": {"color": "#1565c0"}}
    ]
    payload = {
        "proposal_id": "proposal-school-blue",
        "revision": 4,
        "feature_identity": feature,
        "baseline_identity": baseline,
        "operations": operations,
    }
    proposal_hash = canonical_sha256(payload)
    identity = {
        "proposal_id": payload["proposal_id"],
        "proposal_revision": payload["revision"],
        "proposal_payload_sha256": proposal_hash,
        "feature_identity": feature,
        "baseline_identity": baseline,
    }
    authorization = {
        "schema": "nma.symbol-edit-authorization/1.0",
        "authorization_id": "authorization-school-blue",
        "authorization_hash": "0" * 64,
        "status": status,
        "execution_performed": False,
        "proposal_id": payload["proposal_id"],
        "proposal_revision": payload["revision"],
        "proposal_payload": payload,
        "proposal_payload_sha256": proposal_hash,
        "feature_identity": feature,
        "baseline_identity": baseline,
        "validation_result": {"status": "passed", **identity},
        "human_approval": {
            "decision": "approved",
            "actor_type": "human",
            "approved_operations_sha256": canonical_sha256(operations),
            **identity,
        },
        "approved_operations": operations,
        "portrayal_reference": {
            "asset_path": "assets/symbols/nlsc112v5.4/school.svg",
            "baseline_identity": baseline,
            "approved_operations_sha256": canonical_sha256(operations),
        },
        "source_archive_sha256": archive_sha256,
        "execution_scope": scope
        or ["derived-real-layer", "derived-portrayal", "candidate-maplibre-layer"],
        "issued_at": "2026-08-14T00:00:00Z",
        "expires_at": expires_at,
        "invalidation_status": "valid",
    }
    if upstream_lineage is not None:
        authorization["upstream_lineage"] = upstream_lineage
    authorization["authorization_hash"] = authorization_sha256(authorization)
    return authorization


def make_engine(
    storage_root: Path, *, archive_path: Path | None = None
) -> SchoolHeroExecutionEngine:
    store = ExecutionAuthorizationStore(storage_root / "authorizations")
    return SchoolHeroExecutionEngine(
        storage_root=storage_root,
        archive_path=archive_path or private_archive(),
        official_symbol_path=OFFICIAL_SYMBOL,
        authorization_store=store,
        now=lambda: datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc),
    )

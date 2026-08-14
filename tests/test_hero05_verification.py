from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from hero04_support import OFFICIAL_SYMBOL, ROOT, make_authorization, make_engine
from nma.agents.school_agent import analyze_administrative_area
from nma.intent_planning_v05 import plan_intent
from nma.real_layer import REAL_LAYER_PROFILES, file_sha256
from nma.school_hero_execution import authorization_sha256, canonical_sha256
from nma.school_hero_verification import (
    LINEAGE_KINDS,
    SchoolHeroVerifier,
    build_lineage_record,
    build_upstream_lineage,
)


pytestmark = pytest.mark.skipif(
    not shutil.which("ogr2ogr"), reason="GDAL/OGR is required for the HERO-05 execution test."
)


def _write_reviewed_test_archive(root: Path) -> Path:
    source = json.loads(
        (ROOT / "data/fixtures-source/school-points/school-points.geojson").read_text(
            encoding="utf-8"
        )
    )
    layer_ids = REAL_LAYER_PROFILES["school-point"]["source_layer_ids"]
    counts = [3, 3, 3, 2, 2, 2]
    shapefiles = root / "shapefiles"
    shapefiles.mkdir(parents=True)
    cursor = 0
    for layer_id, count in zip(layer_ids, counts, strict=True):
        features = []
        for offset in range(count):
            feature = deepcopy(source["features"][(cursor + offset) % len(source["features"])])
            feature["properties"]["MARKID"] = f"{layer_id}-{offset + 1}"
            feature["properties"]["MARKNAME1"] = f"Reviewed {layer_id} school {offset + 1}"
            features.append(feature)
        cursor += count
        geojson = root / f"{layer_id}.geojson"
        geojson.write_text(
            json.dumps(
                {"type": "FeatureCollection", "name": layer_id, "features": features},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                shutil.which("ogr2ogr") or "ogr2ogr",
                "-f",
                "ESRI Shapefile",
                str(shapefiles / f"{layer_id}.shp"),
                str(geojson),
                "-nln",
                layer_id,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    archive = root / "reviewed-school-test.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as target:
        for layer_id in layer_ids:
            for component in sorted(shapefiles.glob(f"{layer_id}.*")):
                sheet = layer_id.split("_", 1)[0]
                target.write(component, f"{sheet}/SHP/{component.name}")
    return archive


def _authorization_with_real_lineage(archive: Path) -> dict[str, Any]:
    request_payload = {
        "text": "Change the school 9920103 derived symbol color to blue.",
        "automatic_execution": False,
    }
    intent_payload = plan_intent(request_payload["text"])
    evidence_payload = analyze_administrative_area(
        "North District", observed_at=datetime(2026, 8, 14, tzinfo=timezone.utc)
    )
    authorization = make_authorization(archive_sha256=file_sha256(archive))
    decision_payload = authorization["validation_result"]
    proposal_payload = authorization["proposal_payload"]
    approval_payload = authorization["human_approval"]

    request_id = "request:" + canonical_sha256(request_payload)[:20]
    intent_id = "intent:" + canonical_sha256(intent_payload)[:20]
    evidence_id = "evidence:" + canonical_sha256(evidence_payload)[:20]
    decision_id = "decision:" + canonical_sha256(decision_payload)[:20]
    records = [
        build_lineage_record("request", request_id, request_payload),
        build_lineage_record(
            "intent",
            intent_id,
            intent_payload,
            parent_kind="request",
            parent_id=request_id,
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
            decision_payload,
            parent_kind="evidence",
            parent_id=evidence_id,
        ),
        build_lineage_record(
            "proposal",
            authorization["proposal_id"],
            proposal_payload,
            parent_kind="decision",
            parent_id=decision_id,
        ),
        build_lineage_record(
            "approval",
            authorization["authorization_id"],
            approval_payload,
            parent_kind="proposal",
            parent_id=authorization["proposal_id"],
        ),
    ]
    authorization["upstream_lineage"] = build_upstream_lineage(records)
    authorization["authorization_hash"] = authorization_sha256(authorization)
    return authorization


@pytest.fixture(scope="module")
def canonical_execution(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    root = tmp_path_factory.mktemp("hero05-canonical")
    archive = _write_reviewed_test_archive(root)
    storage = root / "runtime"
    engine = make_engine(storage, archive_path=archive)
    authorization = _authorization_with_real_lineage(archive)
    engine.authorization_store.save(authorization)
    receipt = engine.execute_by_id(
        {
            "authorization_id": authorization["authorization_id"],
            "idempotency_key": "hero05-canonical-execution",
        }
    )
    return {
        "archive": archive,
        "storage": storage,
        "execution_id": receipt["execution_id"],
    }


def _copy_and_verifier(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> tuple[Path, SchoolHeroVerifier]:
    storage = tmp_path / "runtime"
    shutil.copytree(canonical_execution["storage"], storage)
    return storage, SchoolHeroVerifier(
        storage_root=storage,
        archive_path=canonical_execution["archive"],
        official_symbol_path=OFFICIAL_SYMBOL,
        repository_root=ROOT,
    )


def _check(result: dict[str, Any], identifier: str) -> dict[str, Any]:
    checks = [*result["qa"]["checks"], *result["provenance"]["checks"]]
    return next(item for item in checks if item["id"] == identifier)


def test_hero05_schemas_are_closed_draft_2020_12() -> None:
    for name in [
        "school-hero-qa-v1.0.schema.json",
        "school-hero-provenance-v1.0.schema.json",
    ]:
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False


def test_canonical_school_hero_execution_qa_and_provenance_pass(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> None:
    storage, verifier = _copy_and_verifier(canonical_execution, tmp_path)
    result = verifier.verify(canonical_execution["execution_id"])
    root = storage / "executions" / canonical_execution["execution_id"]

    assert result["status"] == "verified"
    assert result["qa"]["status"] == "passed"
    assert result["qa"]["classification"] == "expected-change-verified"
    assert result["provenance"]["status"] == "verified"
    assert [item["kind"] for item in result["provenance"]["chain"]] == [
        *LINEAGE_KINDS,
        "execution",
        "qa",
        "artifact",
    ]
    assert result["qa"]["expected_transition"]["data_sha256"] == result["qa"][
        "observed_transition"
    ]["data_sha256"]
    assert result["qa"]["expected_transition"]["portrayal_sha256"] == result["qa"][
        "observed_transition"
    ]["portrayal_sha256"]
    assert (root / "qa.json").is_file()
    assert (root / "provenance.json").is_file()


def test_artifact_tampering_fails_closed(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> None:
    storage, verifier = _copy_and_verifier(canonical_execution, tmp_path)
    asset = storage / "executions" / canonical_execution["execution_id"] / "assets/school.svg"
    asset.write_text(asset.read_text(encoding="utf-8") + "<!-- tampered -->\n", encoding="utf-8")

    result = verifier.verify(canonical_execution["execution_id"], persist=False)

    assert result["status"] == "failed"
    assert _check(result, "observed_portrayal_state")["status"] == "failed"
    assert _check(result, "execution_artifact_hashes")["status"] == "failed"


def test_approval_proposal_mismatch_fails_closed(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> None:
    storage, verifier = _copy_and_verifier(canonical_execution, tmp_path)
    path = storage / "executions" / canonical_execution["execution_id"] / "authorization.json"
    authorization = json.loads(path.read_text(encoding="utf-8"))
    approval = authorization["upstream_lineage"]["records"][-1]
    approval["payload"]["proposal_id"] = "proposal-another-school"
    approval["payload_sha256"] = canonical_sha256(approval["payload"])
    authorization["human_approval"] = deepcopy(approval["payload"])
    authorization["authorization_hash"] = authorization_sha256(authorization)
    path.write_text(json.dumps(authorization, sort_keys=True), encoding="utf-8")

    result = verifier.verify(canonical_execution["execution_id"], persist=False)

    assert result["status"] == "failed"
    assert _check(result, "approval_proposal_binding")["status"] == "failed"
    assert _check(result, "execution_proposal_binding")["status"] == "failed"


def test_execution_state_transition_different_from_proposal_fails_qa(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> None:
    storage, verifier = _copy_and_verifier(canonical_execution, tmp_path)
    path = storage / "executions" / canonical_execution["execution_id"] / "bundle.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))
    bundle["layer"]["paint"]["icon-color"] = "#c62828"
    bundle["bundle_sha256"] = canonical_sha256(
        {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    )
    path.write_text(json.dumps(bundle, sort_keys=True), encoding="utf-8")

    result = verifier.verify(canonical_execution["execution_id"], persist=False)

    assert result["status"] == "failed"
    assert result["qa"]["status"] == "failed"
    assert _check(result, "observed_map_state")["status"] == "failed"


def test_expected_portrayal_change_missing_is_distinguished(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> None:
    storage, verifier = _copy_and_verifier(canonical_execution, tmp_path)
    asset = storage / "executions" / canonical_execution["execution_id"] / "assets/school.svg"
    shutil.copyfile(OFFICIAL_SYMBOL, asset)

    result = verifier.verify(canonical_execution["execution_id"], persist=False)

    assert result["status"] == "failed"
    assert result["qa"]["classification"] == "expected-change-missing"
    assert _check(result, "observed_portrayal_state")["status"] == "failed"


def test_execution_wrong_proposal_reference_fails_provenance(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> None:
    storage, verifier = _copy_and_verifier(canonical_execution, tmp_path)
    path = storage / "executions" / canonical_execution["execution_id"] / "receipt.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    receipt["proposal"]["proposal_id"] = "proposal-another-school"
    receipt["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )
    path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")

    result = verifier.verify(canonical_execution["execution_id"], persist=False)

    assert result["status"] == "failed"
    assert _check(result, "execution_proposal_binding")["status"] == "failed"


def test_missing_provenance_reference_fails_closed(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> None:
    storage, verifier = _copy_and_verifier(canonical_execution, tmp_path)
    path = storage / "executions" / canonical_execution["execution_id"] / "authorization.json"
    authorization = json.loads(path.read_text(encoding="utf-8"))
    authorization["upstream_lineage"]["records"] = [
        record
        for record in authorization["upstream_lineage"]["records"]
        if record["kind"] != "evidence"
    ]
    authorization["authorization_hash"] = authorization_sha256(authorization)
    path.write_text(json.dumps(authorization, sort_keys=True), encoding="utf-8")

    result = verifier.verify(canonical_execution["execution_id"], persist=False)

    assert result["status"] == "failed"
    assert _check(result, "complete_upstream_lineage")["status"] == "failed"


def test_invalid_lineage_reference_fails_closed(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> None:
    storage, verifier = _copy_and_verifier(canonical_execution, tmp_path)
    path = storage / "executions" / canonical_execution["execution_id"] / "authorization.json"
    authorization = json.loads(path.read_text(encoding="utf-8"))
    authorization["upstream_lineage"]["records"][2]["parent"]["id"] = "intent:missing"
    authorization["authorization_hash"] = authorization_sha256(authorization)
    path.write_text(json.dumps(authorization, sort_keys=True), encoding="utf-8")

    result = verifier.verify(canonical_execution["execution_id"], persist=False)

    assert result["status"] == "failed"
    assert _check(result, "valid_lineage_references")["status"] == "failed"


def test_unexpected_additional_modification_fails_qa(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> None:
    storage, verifier = _copy_and_verifier(canonical_execution, tmp_path)
    root = storage / "executions" / canonical_execution["execution_id"]
    (root / "outside-approved-target.json").write_text("{}\n", encoding="utf-8")

    result = verifier.verify(canonical_execution["execution_id"], persist=False)

    assert result["status"] == "failed"
    assert result["qa"]["classification"] == "unexpected-additional-change"
    assert _check(result, "unexpected_modifications")["status"] == "failed"


def test_verification_is_deterministic(
    canonical_execution: dict[str, Any], tmp_path: Path
) -> None:
    _, verifier = _copy_and_verifier(canonical_execution, tmp_path)

    first = verifier.verify(canonical_execution["execution_id"])
    second = verifier.verify(canonical_execution["execution_id"])

    assert first == second

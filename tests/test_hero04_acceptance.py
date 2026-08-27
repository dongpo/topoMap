import json
from pathlib import Path
import shutil

import pytest

from hero04_support import ROOT, make_authorization, make_engine, private_archive
from nma.real_layer import file_sha256


PROTECTED = [
    ROOT / "assets/symbols/nlsc112v5.4/school.svg",
    ROOT / "data/knowledge/portrayal-graph.json",
    ROOT / "data/knowledge/portrayal-profile.json",
    ROOT / "data/knowledge/nma-canonical-graph-v0.4.json",
]


def test_hero04_schemas_are_closed_draft_2020_12() -> None:
    names = [
        "school-hero-execution-plan-v1.0.schema.json",
        "maplibre-runtime-bundle-v1.0.schema.json",
        "school-hero-execution-receipt-v1.0.schema.json",
        "runtime-layer-observation-v1.0.schema.json",
        "rollback-manifest-v1.0.schema.json",
    ]
    for name in names:
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False


@pytest.mark.skipif(
    not private_archive().is_file() or not shutil.which("ogr2ogr"),
    reason="The private reviewed archive and GDAL are required.",
)
def test_end_to_end_receipt_governance_and_authoritative_integrity(tmp_path: Path) -> None:
    protected_before = {path: file_sha256(path) for path in PROTECTED}
    archive_before = file_sha256(private_archive())
    engine = make_engine(tmp_path)
    receipt = engine.execute(make_authorization(), "acceptance-key-001")
    bundle = engine.get_bundle(receipt["execution_id"])
    data = engine.get_data(receipt["execution_id"])
    observation = engine.observe(
        receipt["execution_id"],
        {
            "state": "activate",
            "client_session": "browser-acceptance",
            "source_ids": [bundle["source"]["id"]],
            "layer_ids": [bundle["layer"]["id"]],
            "observed_feature_count": 15,
            "runtime_version": "4.7.0",
            "status": "verified",
        },
    )
    assert receipt["schema"] == "nma.school-hero-execution-receipt/1.0"
    assert receipt["output"]["feature_count"] == len(data["features"]) == 15
    assert receipt["governance"] == {
        "data_execution_performed": True,
        "authoritative_source_mutation_performed": False,
        "official_portrayal_activation_performed": False,
        "pmtiles_rebuild_performed": False,
        "publication_performed": False,
    }
    assert observation["final_qa"] is False
    assert file_sha256(private_archive()) == archive_before
    assert {path: file_sha256(path) for path in PROTECTED} == protected_before

from pathlib import Path
import shutil

import pytest

from hero04_support import make_authorization, make_engine, private_archive
from nma.real_layer import file_sha256


pytestmark = pytest.mark.skipif(
    not private_archive().is_file() or not shutil.which("ogr2ogr"),
    reason="The private reviewed archive and GDAL are required.",
)


def test_rollback_is_idempotent_traceable_and_preserves_receipt(tmp_path: Path) -> None:
    engine = make_engine(tmp_path)
    receipt = engine.execute(make_authorization(), "rollback-key-001")
    receipt_path = tmp_path / "executions" / receipt["execution_id"] / "receipt.json"
    before = file_sha256(receipt_path)
    first = engine.rollback_execution(receipt["execution_id"], client_session="browser-01")
    second = engine.rollback_execution(receipt["execution_id"], client_session="browser-01")
    assert first == second
    assert [item["action"] for item in first["actions"]] == [
        "remove-layer",
        "remove-source",
        "remove-image",
    ]
    assert first["receipt_preserved"] is True
    assert file_sha256(receipt_path) == before

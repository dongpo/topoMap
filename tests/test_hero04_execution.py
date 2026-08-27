from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil

import pytest

from hero04_support import make_authorization, make_engine, private_archive
from nma.real_layer import RealLayerError
from nma.school_hero_execution import SchoolHeroExecutionError


pytestmark = pytest.mark.skipif(
    not private_archive().is_file() or not shutil.which("ogr2ogr"),
    reason="The private reviewed archive and GDAL are required.",
)


def test_atomic_promotion_and_idempotency(tmp_path: Path) -> None:
    engine = make_engine(tmp_path)
    authorization = make_authorization()
    first = engine.execute(authorization, "atomic-key-001")
    second = engine.execute(authorization, "atomic-key-001")
    assert first == second
    assert not (tmp_path / ".staging" / first["execution_id"]).exists()
    execution = tmp_path / "executions" / first["execution_id"]
    assert (execution / "receipt.json").is_file()
    assert (execution / "bundle.json").is_file()
    assert (execution / "data/school-point.geojson").is_file()
    assert (execution / "assets/school.svg").is_file()
    with pytest.raises(SchoolHeroExecutionError, match="another idempotency"):
        engine.execute(authorization, "different-key-002")


def test_concurrent_same_request_executes_once(tmp_path: Path) -> None:
    engine = make_engine(tmp_path)
    authorization = make_authorization()
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(
            pool.map(lambda _: engine.execute(authorization, "concurrency-key"), range(2))
        )
    assert receipts[0] == receipts[1]
    assert len(list((tmp_path / "executions").iterdir())) == 1


def test_failed_execution_cleans_staging(monkeypatch, tmp_path: Path) -> None:
    engine = make_engine(tmp_path)
    monkeypatch.setattr(
        "nma.school_hero_execution.execute_real_layer",
        lambda *args, **kwargs: (_ for _ in ()).throw(RealLayerError("forced failure")),
    )
    with pytest.raises(SchoolHeroExecutionError, match="forced failure"):
        engine.execute(make_authorization(), "failure-key-001")
    assert not list((tmp_path / ".staging").glob("*"))
    assert not (tmp_path / "executions").exists()

import importlib.util
from pathlib import Path
import sys

import pytest

from hero04_support import make_authorization, make_engine
from nma.school_hero_execution import SchoolHeroExecutionError


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "scripts/run_nma_agent_server.py"


def load_server():
    spec = importlib.util.spec_from_file_location("hero04_api_server", SERVER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("forbidden", ["proposal_id", "decision", "source_path", "SQL", "filter", "output_path"])
def test_execution_api_rejects_client_execution_parameters(tmp_path: Path, forbidden: str) -> None:
    engine = make_engine(tmp_path)
    engine.authorization_store.save(make_authorization())
    with pytest.raises(SchoolHeroExecutionError, match="only"):
        engine.execute_by_id(
            {
                "authorization_id": "authorization-school-blue",
                "idempotency_key": "bounded-api-key",
                forbidden: "forbidden",
            }
        )


def test_server_declares_all_hero04_routes() -> None:
    server = load_server()
    source = SERVER_PATH.read_text(encoding="utf-8")
    assert "/api/school-hero/executions" in source
    assert "/(bundle|data)" in source
    assert "/observations" in source
    assert "/rollback" in source
    assert server.SCHOOL_HERO_EXECUTIONS.authorization_store is server.SCHOOL_HERO_AUTHORIZATIONS

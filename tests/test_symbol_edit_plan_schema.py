import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "symbol-edit-plan.schema.json"


def test_v04_symbol_edit_plan_schema_is_closed_and_bounded() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    operations = schema["properties"]["operations"]
    assert operations["minItems"] == 1
    assert operations["maxItems"] == 8
    operation = operations["items"]
    assert operation["additionalProperties"] is False
    assert set(operation["required"]) == set(operation["properties"])
    assert "raw_svg" not in operation["properties"]["action"]["enum"]

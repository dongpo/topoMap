from __future__ import annotations

import json
from pathlib import Path

from ama_demo02_support import SCHOOL_REQUEST, school_adapter
from nma import research_cli


def _run(monkeypatch, output: Path) -> tuple[int, dict, str]:
    monkeypatch.setattr(research_cli, "adapter_from_environment", school_adapter)
    exit_code = research_cli.main(
        [
            "--repository-root",
            str(Path(__file__).resolve().parents[1]),
            "--output-root",
            str(output),
            "rq2",
            SCHOOL_REQUEST,
        ]
    )
    artifact = json.loads(next(output.glob("*/result.json")).read_text(encoding="utf-8"))
    summary = next(output.glob("*/summary.txt")).read_text(encoding="utf-8")
    return exit_code, artifact, summary


def test_rq2_cli_packages_exact_bounded_plan_fields_and_invariant_results(
    monkeypatch, tmp_path: Path
) -> None:
    exit_code, artifact, summary = _run(monkeypatch, tmp_path / "research-demo")
    assert exit_code == 0
    plan = artifact["plan"]
    assert plan["feature_domain"] == {"code": "9920103", "geometry_role": "Point"}
    assert plan["classification"] == {"field": "TERRAINID", "code": "9920103"}
    assert plan["geometry"]["input"] == plan["geometry"]["output"] == "Point"
    assert plan["field_mapping"]["feature_code_field"] == "TERRAINID"
    assert plan["source_layers"] == [
        "J01_MARK",
        "J13_MARK",
        "J17_MARK",
        "K01_MARK",
        "K02_MARK",
        "K14_MARK",
    ]
    assert all(artifact["validation"].values())
    assert artifact["plan_validation"] == "PASS"
    assert "PLAN VALIDATION: PASS" in summary


def test_rq2_cli_companion_mutation_is_deterministically_rejected_before_execution(
    monkeypatch, tmp_path: Path
) -> None:
    _, artifact, summary = _run(monkeypatch, tmp_path / "research-demo")
    invalid = artifact["invalid_plan_companion"]
    assert invalid["invalid_field"] == ("schema_constraints.feature_code_field=INVENTED_FIELD")
    assert invalid["rejection_stage"] == "deterministic-plan-validation"
    assert invalid["rejected"] is True
    assert invalid["execution_reached"] is False
    assert "Execution reached: NO" in summary

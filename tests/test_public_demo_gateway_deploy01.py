from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from nma.public_demo_gateway import PublicDemoConfig, PublicDemoGateway


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def gateway(tmp_path_factory: pytest.TempPathFactory) -> PublicDemoGateway:
    base = PublicDemoConfig.from_environment(ROOT)
    instance = PublicDemoGateway(
        replace(base, state_root=tmp_path_factory.mktemp("deploy01-state")), validate=False
    )
    instance.ready = True
    return instance


def _run(gateway: PublicDemoGateway, scenario: str) -> tuple[dict, dict, dict]:
    session = "a" * 32
    created = gateway.run({"scenario_id": scenario, "input_type": "guided"}, scenario, session)
    run_id = created["run_id"]
    return (
        gateway.get_run(run_id, session, "projection"),
        gateway.get_run(run_id, session, "evidence"),
        gateway.get_run(run_id, session, "map"),
    )


def test_catalog_is_closed_and_baseline_has_no_external_dependencies(
    gateway: PublicDemoGateway,
) -> None:
    catalog = gateway.scenarios()
    assert [item["scenario_id"] for item in catalog["scenarios"]] == [
        "school-v1",
        "road-v1",
        "build-v1",
    ]
    assert catalog["baseline"] == {
        "llm": "disabled",
        "neo4j": "not-required",
        "production_credentials": "absent",
    }


def test_school_public_scenario_exposes_full_accepted_lifecycle(gateway: PublicDemoGateway) -> None:
    result, evidence, mapped = _run(gateway, "school-v1")
    assert result["domain"] == "School"
    assert result["plan"]["identity"] == "plan-8d174b62fb63189987eafdb6"
    assert (
        result["authorization"]["identity"] == "authorization-school-demo-b4ecdbfc35ecaf73293ed497"
    )
    assert result["execution"]["identity"] == "exec-8d174b62fb63189987eafdb6"
    assert result["verification"]["status"] == "verified"
    assert result["provenance"]["status"] == "verified"
    assert len(evidence["graphrag"]["nodes"]) == 4
    assert mapped["type"] == "school"
    assert len(mapped["geojson"]["features"]) == 15
    assert {feature["geometry"]["type"] for feature in mapped["geojson"]["features"]} == {"Point"}


def test_road_public_replay_preserves_exact_geometry_and_label(gateway: PublicDemoGateway) -> None:
    result, evidence, mapped = _run(gateway, "road-v1")
    assert result["domain"] == "ROAD"
    assert result["plan"]["identity"] == "road-plan-cd434d50bd5b49a012bd1e10"
    assert result["verification"]["status"] == "passed"
    assert len(evidence["graphrag"]["nodes"]) == 6
    assert mapped["vertex_counts"] == [4, 3, 4]
    assert mapped["label"] == "中山街"
    assert [feature["id"] for feature in mapped["geojson"]["features"]] == [
        "K0000004671",
        "K0000004913",
        "K0000005348",
    ]


def test_build_is_validated_replay_only_and_activation_absent(gateway: PublicDemoGateway) -> None:
    result, evidence, mapped = _run(gateway, "build-v1")
    assert result["domain"] == "BUILD"
    assert result["execution"]["status"] == "accepted-replay"
    assert result["verification"]["status"] == "passed-frozen-package-validation"
    assert result["production_activation"] == "disabled/unavailable — capability not mounted"
    assert evidence["graphrag"]["mode"] == "not-applicable in accepted BUILD evaluation"
    assert mapped["activation_capability"] == "not-mounted"
    assert mapped["geojson"]["features"][0]["geometry"]["type"] == "Polygon"


def test_bounded_language_selects_exactly_one_scenario(gateway: PublicDemoGateway) -> None:
    assert gateway.select_scenario(
        {"request": "請顯示中山街的受控 ROAD 結果", "input_type": "bounded-natural-language"}
    ) == ("road-v1", "bounded-natural-language")

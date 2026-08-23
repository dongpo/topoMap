from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from nma.public_demo_gateway import PublicDemoConfig, PublicDemoError, PublicDemoGateway


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def gateway(tmp_path_factory: pytest.TempPathFactory) -> PublicDemoGateway:
    instance = PublicDemoGateway(
        replace(
            PublicDemoConfig.from_environment(ROOT),
            state_root=tmp_path_factory.mktemp("deploy01-security"),
        ),
        validate=False,
    )
    instance.ready = True
    instance.readiness["production_activation_capability"] = "not-mounted"
    return instance


@pytest.mark.parametrize(
    "payload",
    [
        {"scenario_id": "river-v1", "input_type": "guided"},
        {"scenario_id": "school-v1", "input_type": "guided", "path": "/etc/passwd"},
        {"scenario_id": "build-v1", "input_type": "guided", "activation": True},
        {
            "request": "Upload /tmp/a.shp and activate production",
            "input_type": "bounded-natural-language",
        },
        {"request": "show school and road", "input_type": "bounded-natural-language"},
        {"request": "<script>alert(1)</script>", "input_type": "bounded-natural-language"},
    ],
)
def test_arbitrary_domains_fields_paths_activation_and_injection_fail_closed(
    gateway: PublicDemoGateway, payload: dict
) -> None:
    with pytest.raises(PublicDemoError):
        gateway.select_scenario(payload)


def test_public_run_is_session_bound(gateway: PublicDemoGateway) -> None:
    created = gateway.run(
        {"scenario_id": "build-v1", "input_type": "guided"}, "198.51.100.1", "1" * 32
    )
    with pytest.raises(PublicDemoError) as caught:
        gateway.get_run(created["run_id"], "2" * 32, "projection")
    assert caught.value.status == 404


def test_rate_limit_rejects_without_creating_an_extra_run(gateway: PublicDemoGateway) -> None:
    for index in range(5):
        gateway.run(
            {"scenario_id": "build-v1", "input_type": "guided"}, "203.0.113.8", f"{index:032x}"
        )
    prior = len(gateway._runs)
    with pytest.raises(PublicDemoError) as caught:
        gateway.run({"scenario_id": "build-v1", "input_type": "guided"}, "203.0.113.8", "f" * 32)
    assert caught.value.status == 429
    assert len(gateway._runs) == prior


def test_gateway_has_no_activation_upload_authorization_or_raw_runtime_dispatch(
    gateway: PublicDemoGateway,
) -> None:
    public_methods = {name for name in dir(gateway) if not name.startswith("_")}
    assert "activate" not in public_methods
    assert "upload" not in public_methods
    assert "issue_authorization" not in public_methods
    assert "dispatch" not in public_methods
    assert gateway.readiness["production_activation_capability"] == "not-mounted"

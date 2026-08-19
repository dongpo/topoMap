from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nma.road_execution import FrozenRoadInputs, RoadExecutionEngine, _write_json


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/datasets/112年多維度SHP成果_0502.zip"
SPECIFICATIONS = ROOT / "data/specifications"


def main() -> None:
    inputs = FrozenRoadInputs(ROOT)
    authorization = json.loads(inputs.authorization.read_text(encoding="utf-8"))
    with TemporaryDirectory(prefix="nma-road04-goldens-") as temporary:
        storage = Path(temporary)
        engine = RoadExecutionEngine(
            storage_root=storage,
            archive_path=ARCHIVE,
            frozen_inputs=inputs,
            now=lambda: datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc),
        )
        receipt = engine.execute(authorization, "road04-golden-key")
        execution_id = receipt["execution_id"]
        execution = storage / "executions" / execution_id
        bundle = engine.get_bundle(execution_id)
        observation = engine.observe(
            execution_id,
            {
                "state": "verify",
                "client_session": "road04-verification",
                "source_ids": [bundle["source"]["id"]],
                "layer_ids": [item["id"] for item in bundle["layers"]],
                "observed_feature_count": 3,
                "runtime_version": "maplibre-reviewed-line-mechanism/1",
                "status": "verified",
            },
        )
        sources = {
            "nma-road-hero-road-04-golden-plan-v1.0.json": execution / "plan.json",
            "nma-road-hero-road-04-golden-derived-portrayal-v1.0.json": (
                execution / "derived-portrayal.json"
            ),
            "nma-road-hero-road-04-golden-runtime-bundle-v1.0.json": execution / "bundle.json",
            "nma-road-hero-road-04-golden-receipt-v1.0.json": execution / "receipt.json",
            "nma-road-hero-road-04-golden-rollback-manifest-v1.0.json": (
                execution / "rollback-manifest.json"
            ),
        }
        for name, source in sources.items():
            _write_json(
                SPECIFICATIONS / name,
                json.loads(source.read_text(encoding="utf-8")),
            )
        _write_json(
            SPECIFICATIONS / "nma-road-hero-road-04-golden-observation-v1.0.json",
            observation,
        )
        print(execution_id)
        print(receipt["receipt_sha256"])
        print(observation["observation_sha256"])


if __name__ == "__main__":
    main()

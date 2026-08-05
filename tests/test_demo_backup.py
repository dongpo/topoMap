import json
from pathlib import Path

from nma.demo_backup import check_demo_backup


ROOT = Path(__file__).resolve().parents[1]


def test_portable_backup_covers_five_frozen_scenes() -> None:
    result = check_demo_backup()

    assert result == {
        "backup_version": "nma-demo-d16-v1",
        "status": "passed",
        "scene_count": 5,
        "screenshot_count": 5,
        "evidence_screenshot_count": 5,
        "video_format": "video/x-msvideo; codecs=mjpeg",
        "no_repository_required": True,
        "asset_count": 14,
    }


def test_backup_manifest_preserves_frozen_order_and_fallback_ladder() -> None:
    manifest = json.loads(
        (ROOT / "artifacts/presentation/nma-demo-backup/MANIFEST.json").read_text()
    )

    assert [scene["id"] for scene in manifest["scenes"]] == [
        "school",
        "fire-hydrant",
        "police",
        "fish-pond",
        "post-office",
    ]
    assert manifest["video"] == {
        "duration_seconds": 20,
        "frames": 20,
        "height": 720,
        "seconds_per_scene": 4,
        "width": 1280,
    }
    assert manifest["portability"]["no_network_required"] is True
    assert manifest["portability"]["primary_entrypoint"] == "PLAYBACK.html"
    assert manifest["fallback_order"] == ["live", "degraded", "video", "screenshots"]

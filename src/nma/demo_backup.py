from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .paths import resolve_asset


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check_avi(path: Path, *, expected_frames: int) -> None:
    payload = path.read_bytes()
    if payload[:4] != b"RIFF" or payload[8:12] != b"AVI ":
        raise ValueError("D16 backup video is not a RIFF AVI file")
    if b"MJPG" not in payload:
        raise ValueError("D16 backup video is not Motion JPEG")
    movie_start = payload.index(b"movi") + 4
    movie_end = payload.index(b"idx1", movie_start) - 4
    cursor = movie_start
    frame_count = 0
    while cursor < movie_end:
        tag = payload[cursor : cursor + 4]
        size = int.from_bytes(payload[cursor + 4 : cursor + 8], "little")
        frame = payload[cursor + 8 : cursor + 8 + size]
        if tag != b"00dc" or not frame.startswith(b"\xff\xd8") or not frame.endswith(b"\xff\xd9"):
            raise ValueError("D16 backup video contains an invalid Motion JPEG frame")
        frame_count += 1
        cursor += 8 + size + (size % 2)
    if frame_count != expected_frames:
        raise ValueError("D16 backup video frame index is incomplete")


def check_demo_backup(
    manifest_path: str | Path = "artifacts/presentation/nma-demo-backup/MANIFEST.json",
) -> dict[str, object]:
    manifest_file = resolve_asset(manifest_path)
    manifest = json.loads(manifest_file.read_text())
    root = manifest_file.parent
    assets = manifest["assets"]
    failures: list[dict[str, str]] = []

    for asset in assets:
        path = root / asset["path"]
        if not path.is_file():
            failures.append({"path": asset["path"], "reason": "missing"})
            continue
        actual = _sha256(path)
        if actual != asset["sha256"]:
            failures.append({"path": asset["path"], "reason": "sha256-mismatch"})

    video_assets = [asset for asset in assets if asset["role"] == "backup-video"]
    screenshots = [asset for asset in assets if asset["role"] == "scene-screenshot"]
    evidence = [asset for asset in assets if asset["role"] == "evidence-screenshot"]
    if len(video_assets) != 1:
        failures.append({"path": "assets", "reason": "expected-one-backup-video"})
    if len(screenshots) != 5:
        failures.append({"path": "assets", "reason": "expected-five-scene-screenshots"})
    if len(evidence) != 5:
        failures.append({"path": "assets", "reason": "expected-five-evidence-screenshots"})

    if failures:
        raise ValueError(f"D16 backup verification failed: {failures}")

    _check_avi(root / video_assets[0]["path"], expected_frames=manifest["video"]["frames"])

    return {
        "backup_version": manifest["backup_version"],
        "status": "passed",
        "scene_count": len(manifest["scenes"]),
        "screenshot_count": len(screenshots),
        "evidence_screenshot_count": len(evidence),
        "video_format": video_assets[0]["media_type"],
        "no_repository_required": manifest["portability"]["no_repository_required"],
        "asset_count": len(assets),
    }

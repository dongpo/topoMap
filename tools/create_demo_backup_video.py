from __future__ import annotations

import argparse
import io
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SCENES = (
    ("School", "9920103", 61, "01-school.png"),
    ("Fire hydrant", "9350906", 11, "02-fire-hydrant.png"),
    ("Police", "9910603", 60, "03-police.png"),
    ("Fish pond", "9740100", 50, "04-fish-pond.png"),
    ("Post office", "9950201", 69, "05-post-office.png"),
)


def _chunk(tag: bytes, payload: bytes) -> bytes:
    padding = b"\0" if len(payload) % 2 else b""
    return tag + struct.pack("<I", len(payload)) + payload + padding


def _list_chunk(kind: bytes, payload: bytes) -> bytes:
    return _chunk(b"LIST", kind + payload)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def _render_frame(path: Path, caption: str, *, width: int, height: int) -> bytes:
    source = Image.open(path).convert("RGB")
    stage = Image.new("RGB", (width, height), "#f5f7f4")
    source.thumbnail((width, height), Image.Resampling.LANCZOS)
    stage.paste(source, ((width - source.width) // 2, (height - source.height) // 2))
    draw = ImageDraw.Draw(stage)
    draw.rectangle((0, height - 72, width, height), fill="#101b14")
    draw.text((28, height - 51), caption, fill="white", font=_font(28))
    output = io.BytesIO()
    stage.save(output, format="JPEG", quality=90, optimize=True)
    return output.getvalue()


def create_mjpeg_avi(
    screenshots: Path,
    output: Path,
    *,
    width: int = 1280,
    height: int = 720,
    fps: int = 1,
    seconds_per_scene: int = 4,
) -> None:
    encoded_scenes = []
    for index, (name, code, page, filename) in enumerate(SCENES, start=1):
        caption = f"{index}/5  {name}  code {code}  evidence p.{page}"
        encoded_scenes.append(
            _render_frame(screenshots / filename, caption, width=width, height=height)
        )

    frames = [
        frame
        for scene_frame in encoded_scenes
        for frame in [scene_frame] * (fps * seconds_per_scene)
    ]
    max_frame = max(map(len, frames))
    total_bytes = sum(map(len, frames))
    duration_seconds = len(frames) / fps

    main_header = struct.pack(
        "<IIIIIIIIII4I",
        1_000_000 // fps,
        int(total_bytes / duration_seconds),
        0,
        0x10,
        len(frames),
        0,
        1,
        max_frame,
        width,
        height,
        0,
        0,
        0,
        0,
    )
    stream_header = struct.pack(
        "<4s4sIHHIIIIIIIIhhhh",
        b"vids",
        b"MJPG",
        0,
        0,
        0,
        0,
        1,
        fps,
        0,
        len(frames),
        max_frame,
        0xFFFFFFFF,
        0,
        0,
        0,
        width,
        height,
    )
    bitmap_header = struct.pack(
        "<IiiHH4sIiiII",
        40,
        width,
        height,
        1,
        24,
        b"MJPG",
        max_frame,
        0,
        0,
        0,
        0,
    )
    stream_list = _list_chunk(
        b"strl", _chunk(b"strh", stream_header) + _chunk(b"strf", bitmap_header)
    )
    header_list = _list_chunk(b"hdrl", _chunk(b"avih", main_header) + stream_list)

    movie_payload = bytearray()
    index_payload = bytearray()
    for frame in frames:
        offset = 4 + len(movie_payload)
        movie_payload.extend(_chunk(b"00dc", frame))
        index_payload.extend(struct.pack("<4sIII", b"00dc", 0x10, offset, len(frame)))
    movie_list = _list_chunk(b"movi", bytes(movie_payload))
    riff_payload = b"AVI " + header_list + movie_list + _chunk(b"idx1", bytes(index_payload))
    output.write_bytes(b"RIFF" + struct.pack("<I", len(riff_payload)) + riff_payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the frozen D16 five-scene MJPEG video")
    parser.add_argument("--screenshots", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    create_mjpeg_avi(args.screenshots, args.output)
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

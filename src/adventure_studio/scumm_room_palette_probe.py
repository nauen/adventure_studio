"""Native SCUMM-v6 256-color room bitmap verification.

Builds three independent ScummC-v6 games and checks actual stock-ScummVM
pixels at all 256 authored palette-index locations. The two negative games
deliberately swap or duplicate palette entries and must fail the same check.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

from .image_pipeline import IndexedImage
from .scumm_assets import scrolling_fixture
from .scumm_project import canonical_json, parse_document
from .scumm_room_visual_probe import render_native_room
from .story_document import parse_story_document
from .story_fixture_image import DeterministicStoryImageProvider
from .story_to_scumm import compile_story_to_scumm


GRID_X = 16
GRID_Y = 16
CELL_SIZE = 8
GRID_SIDE = 16
SCREEN_ORIGIN_X = 192
SCREEN_ORIGIN_Y = 184
SCREEN_SCALE = 2


def room_palette_256() -> tuple[tuple[int, int, int], ...]:
    """Return 256 unique RGB entries while retaining the known sky colors."""
    colors = list(scrolling_fixture().palette)
    red_green = (0, 36, 73, 109, 146, 182, 219, 255)
    blue = (0, 64, 128, 192, 255)
    for red in red_green:
        for green in red_green:
            for blue_value in blue:
                rgb = (red, green, blue_value)
                if any(max(abs(a - b) for a, b in zip(rgb, existing)) <= 24
                       for existing in colors):
                    continue
                colors.append(rgb)
                if len(colors) == 256:
                    break
            if len(colors) == 256:
                break
        if len(colors) == 256:
            break
    if len(colors) != 256 or len(set(colors)) != 256:
        raise RuntimeError("The native room palette must contain 256 unique, distinguishable colors")
    minimum_distance = min(
        max(abs(a - b) for a, b in zip(colors[left], colors[right]))
        for left in range(256) for right in range(left + 1, 256)
    )
    if minimum_distance <= 24:
        raise RuntimeError("Palette controls need color separation above renderer quantization")
    return tuple(colors)


def authored_palette_room(variant: str = "correct"):
    """Create a 640x200 room using every palette index in a visible 16x16 grid."""
    if variant not in {"correct", "swapped", "duplicate"}:
        raise ValueError("Unknown room palette control")
    original = scrolling_fixture()
    palette = list(room_palette_256())
    if variant == "swapped":
        palette[16], palette[17] = palette[17], palette[16]
    elif variant == "duplicate":
        palette[255] = palette[254]

    pixels = bytearray(original.pixels)
    width = original.geometry.room_width
    for index in range(256):
        column, row = index % GRID_SIDE, index // GRID_SIDE
        left = GRID_X + column * CELL_SIZE
        top = GRID_Y + row * CELL_SIZE
        for y in range(top, top + CELL_SIZE):
            start = y * width + left
            pixels[start:start + CELL_SIZE] = bytes([index]) * CELL_SIZE
    return replace(original, pixels=bytes(pixels), palette=tuple(palette),
                   demo_walk_to_x=None, demo_walk_to_y=None,
                   ego_start_x=60, ego_start_y=180)


def _sample_location(index: int, offset_x: int, offset_y: int) -> tuple[int, int]:
    column, row = index % GRID_SIDE, index // GRID_SIDE
    source_x = GRID_X + column * CELL_SIZE + offset_x
    source_y = GRID_Y + row * CELL_SIZE + offset_y
    return (SCREEN_ORIGIN_X + SCREEN_SCALE * source_x,
            SCREEN_ORIGIN_Y + SCREEN_SCALE * source_y)


def verify_palette_screenshot(screenshot: Path, expected_palette: tuple[tuple[int, int, int], ...]) -> dict:
    """Verify every palette index at its authored room coordinate in ScummVM."""
    if len(expected_palette) != 256 or len(set(expected_palette)) != 256:
        raise ValueError("Expected palette must contain 256 unique RGB entries")
    from PIL import Image

    with Image.open(screenshot) as source:
        image = source.convert("RGB")
        if image.width < 1024 or image.height < 768:
            raise RuntimeError(f"Unexpected ScummVM screenshot dimensions: {image.size}")
        observations = []
        mismatches = []
        for index, expected in enumerate(expected_palette):
            samples = [image.getpixel(_sample_location(index, ox, oy))
                       for ox, oy in ((2, 2), (4, 4), (6, 6))]
            counts = Counter(samples)
            observed, count = counts.most_common(1)[0]
            row = {"index": index, "expected": list(expected),
                   "observed": list(observed), "matching_samples": count}
            observations.append(row)
            if count < 2 or any(abs(a - b) > 3 for a, b in zip(observed, expected)):
                mismatches.append(row)
    if mismatches:
        raise RuntimeError(
            f"Native room palette mismatch at {len(mismatches)} of 256 indices: "
            f"{mismatches[:8]}"
        )
    return {"palette_entries": 256, "verified_indices": 256,
            "sample_points_per_index": 3, "passed": True,
            "observations": observations}


class _PaletteStoryImageProvider:
    """Feed the real Story compiler one deterministic indexed room image."""

    def __init__(self, variant: str) -> None:
        self.variant = variant
        self.fallback = DeterministicStoryImageProvider()

    def generate(self, request):
        if request.asset_id == "scene-harbor-main":
            room = authored_palette_room(self.variant)
            if (request.width, request.height) != (
                    room.geometry.room_width, room.geometry.room_height):
                raise ValueError("Story requested unexpected Harbor bitmap geometry")
            return IndexedImage(room.pixels, room.palette, request.width,
                                request.height, "native-room-palette-256")
        return self.fallback.generate(request)


def _author_story_project(variant: str) -> tuple[str, object]:
    """Compile the Story with the indexed provider, then JSON-v1 round-trip it."""
    story_path = Path(__file__).resolve().parents[2] / "examples" / "mini_story_chain.json"
    story = parse_story_document(story_path.read_text(encoding="utf-8"))
    document = compile_story_to_scumm(story, _PaletteStoryImageProvider(variant))
    room = next((item for item in document.rooms if item.name == "Harbor"), None)
    if room is None:
        raise RuntimeError("Story compiler did not produce the Harbor room")
    room = replace(room, demo_walk_to_x=None, demo_walk_to_y=None,
                   ego_start_x=60, ego_start_y=180)
    document = replace(document, rooms=tuple(
        room if item.name == "Harbor" else item for item in document.rooms
    ))
    raw = canonical_json(document)
    roundtrip = parse_document(raw)
    if roundtrip != document:
        raise RuntimeError("Room palette changed during the JSON-v1 roundtrip")
    story_room = next(item for item in roundtrip.rooms if item.name == "Harbor")
    expected = authored_palette_room(variant)
    if story_room.pixels != expected.pixels or story_room.palette != expected.palette:
        raise RuntimeError("Story image provider lost room pixels or palette")
    return raw, story_room


def run(upstream: Path, generated: Path, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    expected_palette = room_palette_256()
    results = {}
    for variant in ("correct", "swapped", "duplicate"):
        story_raw, story_room = _author_story_project(variant)
        rendered = render_native_room(
            story_room, upstream, generated, destination,
            f"room-palette-{variant}", allow_static_scene=True,
            scene_capture_seconds=6.0,
        )
        root = destination / f"room-palette-{variant}"
        (root / "project.json").write_text(story_raw, encoding="utf-8")
        screenshot = destination / f"room-palette-{variant}-screenshots" / "scummvm-end.png"
        if variant == "correct":
            palette_result = verify_palette_screenshot(screenshot, expected_palette)
            results[variant] = {"stock_scummvm_started": True,
                                "palette": palette_result,
                                "native_room_frame_report": rendered["frame_report"]}
        else:
            try:
                verify_palette_screenshot(screenshot, expected_palette)
            except RuntimeError as error:
                results[variant] = {"stock_scummvm_started": True,
                                    "negative_control_rejected": True,
                                    "failure": str(error),
                                    "native_room_frame_report": rendered["frame_report"]}
            else:
                raise RuntimeError(f"The {variant} palette negative control was not rejected")

    results["native_room_palette_256_verified"] = True
    (destination / "native-room-palette-256-report.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_room_palette_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])),
                     indent=2, sort_keys=True))

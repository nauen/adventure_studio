"""Produce a reproducible SCUMM v6 palette-cycling research fixture.

Input is an existing bounded two-room story. This is an opt-in visual probe;
normal story builds must not gain synthetic water or extra palette entries.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from .palette_animation import PaletteCycle
from .scumm_project import GameDocument, canonical_json, export_document
from .story_document import parse_story_document
from .story_to_scumm import compile_story_to_scumm


WATER_PALETTE = ((12, 70, 160), (25, 110, 200), (55, 150, 235), (110, 195, 255))


def add_water_cycle(game: GameDocument, *, wide_water: bool = False) -> GameDocument:
    if len(game.rooms) < 2 or game.rooms[0].geometry.room_width != 640:
        raise ValueError("Water probe requires a bounded multi-room story")
    room = game.rooms[0]
    if room.palette_cycles or len(room.palette) > 252:
        raise ValueError("Probe room needs four unreserved palette entries")
    first = len(room.palette)
    pixels = bytearray(room.pixels)
    width = room.geometry.room_width
    # A purpose-built indexed ramp. The base bitmap never changes in runtime;
    # palette rotation creates the apparent movement.
    for y in range(125, 150 if wide_water else 145):
        for x in range(45, 300 if wide_water else 135):
            pixels[y * width + x] = first + (x // 4 + y // 3) % 4
    water = PaletteCycle("Water", first, first + 3, 2)
    # Keep the camera fixed for the palette probe. Move the existing puzzle
    # hotspots into its initial 320px viewport; otherwise the key and exit
    # remain off-screen at their normal scrolling-room coordinates.
    visible_hotspots = tuple(
        replace(hotspot, x=220 if hotspot.pickup else 270)
        if hotspot.pickup or hotspot.exit_destination is not None else hotspot
        for hotspot in room.hotspots
    )
    new_room = replace(room, pixels=bytes(pixels), palette=room.palette + WATER_PALETTE,
                       palette_cycles=(water,), demo_walk_to_x=None,
                       hotspots=visible_hotspots)
    return replace(game, rooms=(new_room, *game.rooms[1:]))


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.palette_demo STORY.json OUTPUT_DIRECTORY")
        return 2
    story = parse_story_document(Path(sys.argv[1]).read_text(encoding="utf-8"))
    game = add_water_cycle(compile_story_to_scumm(story))
    directory = Path(sys.argv[2])
    export_document(game, directory / "resources")
    (directory / "project.json").write_text(canonical_json(game), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

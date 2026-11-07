"""Build a nine-object SCUMM room to exercise real inventory page controls."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from .scumm_assets import RoomHotspot, destination_fixture, scrolling_fixture, write_game_sources
from .scumm_project import GameDocument, canonical_json


INVENTORY_COLORS = (
    (245, 70, 75), (245, 170, 55), (245, 245, 65),
    (100, 235, 65), (65, 240, 210), (75, 145, 245),
    (200, 95, 245), (245, 95, 195), (160, 225, 110),
)


def build_inventory_paging_demo(directory: Path) -> Path:
    base = scrolling_fixture()
    objects = tuple(
        RoomHotspot(
            f"Item{index}", f"item {index}", f"Inventory page sample {index}.",
            335 + index * 26, 100, 16, 16, True,
            bytes((len(base.palette) + index) if x in (0, 15) or y in (0, 15) else 1
                  for y in range(16) for x in range(16)),
        )
        for index in range(len(INVENTORY_COLORS))
    )
    room = replace(base, hotspots=objects, palette=base.palette + INVENTORY_COLORS,
                   use_rules=())
    game = GameDocument("InventoryPagingGame", (room, destination_fixture()))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "project.json").write_text(canonical_json(game), encoding="utf-8")
    write_game_sources(game.rooms, directory / "resources")
    return directory


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m adventure_studio.scumm_inventory_paging_demo OUTPUT_DIRECTORY")
        return 2
    print(build_inventory_paging_demo(Path(sys.argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""R07: compile an authored object-local OBIM Z-mask into stock ScummVM."""

from __future__ import annotations

from dataclasses import replace
import json
import sys
from pathlib import Path

from .scumm_assets import RoomHotspot, destination_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_fixture import native_room
from .scumm_room_visual_probe import render_native_room
from .studio_sequences import import_object_zmask


def run_object_zmask_probe(upstream: Path, generated: Path, destination: Path) -> dict:
    from PIL import Image

    destination.mkdir(parents=True, exist_ok=True)
    base = native_room(occlusion=False, far_scale=255)
    # Place a decorative foreground object across the actual Actor's costume
    # while leaving the existing walkboxes and room-level ZP01 unchanged.
    object_width, object_height = 64, 64
    fence = RoomHotspot("Fence", "foreground", "A railing.", 510, 60,
                        object_width, object_height, False,
                        bytes(object_width * object_height))
    base = replace(base, hotspots=(*base.hotspots, fence))
    project = canonical_json(GameDocument("object_zmask", (base, destination_fixture())))
    image = Image.new("L", (object_width, object_height), color=255)
    mask = destination / "foreground-object-mask.png"
    image.save(mask)
    authored = import_object_zmask(project, "Harbor", "Fence", str(mask))
    room = parse_document(authored).rooms[0]
    assert next(o for o in room.hotspots if o.id == "Fence").object_zmask_pixels == bytes([1]) * (object_width * object_height)
    (destination / "authored-object-mask-project.json").write_text(authored, encoding="utf-8")
    control = render_native_room(base, upstream, generated, destination, "object-clear")
    masked = render_native_room(room, upstream, generated, destination, "object-masked")
    clear_pixels, masked_pixels = control["dark_costume_pixels"], masked["dark_costume_pixels"]
    if clear_pixels < 100 or masked_pixels > clear_pixels // 3:
        raise RuntimeError(f"Native object-local Z mask did not occlude Actor: "
                           f"clear={clear_pixels}, masked={masked_pixels}")
    report = {"authoring": "Studio PNG → RoomHotspot/JSON → ScummC OBIM IM01/ZP01 → stock ScummVM",
              "clear": control, "masked": masked,
              "removed_actor_pixels": clear_pixels - masked_pixels,
              "object_zmask_visually_verified": True}
    (destination / "object-zmask-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_object_zmask_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_object_zmask_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                          Path(sys.argv[3])), indent=2))

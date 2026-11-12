"""R07.1: native object-image Z-mask authored through Studio JSON and compiled as IM01."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

from .scumm_assets import RoomHotspot, destination_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_fixture import native_room
from .scumm_room_visual_probe import render_native_room
from .studio_sequences import import_object_zplane


def run_object_zmask_probe(upstream: Path, generated: Path, destination: Path) -> dict:
    from PIL import Image

    destination.mkdir(parents=True, exist_ok=True)
    room = native_room(occlusion=False, far_scale=255)
    # Native room-zplane remains completely clear. Only the object's IM01
    # mask changes between variants; the sprite and actor route are identical.
    foreground = RoomHotspot(
        "Curtain", "the curtain", "A foreground curtain.",
        520, 60, 64, 48, sprite_pixels=bytes([2]) * (64 * 48),
    )
    room = replace(room, hotspots=(*room.hotspots, foreground))
    base = canonical_json(GameDocument("object_zmask", (room, destination_fixture())))
    png = destination / "curtain-mask.png"
    variants = {}
    for label, level in (("masked", 255), ("clear", 0)):
        Image.new("L", (64, 48), level).save(png)
        raw = import_object_zplane(base, "Harbor", "Curtain", str(png))
        path = destination / f"{label}-project.json"
        path.write_text(raw, encoding="utf-8")
        authored = parse_document(path.read_text(encoding="utf-8")).rooms[0]
        obj = next(item for item in authored.hotspots if item.id == "Curtain")
        assert obj.object_zplane_pixels == bytes([int(level != 0)]) * (64 * 48)
        variants[label] = render_native_room(
            authored, upstream, generated, destination, label
        )
    clear = variants["clear"]["dark_costume_pixels"]
    masked = variants["masked"]["dark_costume_pixels"]
    if clear < 100 or masked > clear // 3:
        raise RuntimeError(
            f"Native OBIM/IM01 object mask did not occlude actor: clear={clear}, masked={masked}"
        )
    report = {
        "authoring": "Studio PNG -> project JSON -> object states IM01 ZP01 -> stock ScummVM",
        "variants": variants,
        "comparison": {"clear_costume_pixels": clear, "masked_costume_pixels": masked,
                       "native_object_zmask_verified": True},
    }
    (destination / "object-zmask-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_object_zmask_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(
        run_object_zmask_probe(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])),
        indent=2,
    ))

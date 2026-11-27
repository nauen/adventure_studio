"""Native IM03/ZP03: independently linked opaque, clear and wrong-BOXD games."""
from dataclasses import replace
import json
from pathlib import Path
import sys

from PIL import Image

from .scumm_assets import RoomHotspot, ZPlane, destination_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_fixture import native_room
from .scumm_room_visual_probe import render_native_room
from .studio_sequences import import_object_third_image, import_object_zplane


def run(upstream, generated, destination):
    destination.mkdir(parents=True, exist_ok=True)
    room = native_room(occlusion=False, far_scale=255)
    size = 64 * 48
    curtain = RoomHotspot("Curtain", "the curtain", "A three-state curtain.",
                         390, 60, 64, 48, sprite_pixels=bytes([2])*size,
                         open_sprite_pixels=bytes([2])*size)
    room = replace(room, hotspots=(*room.hotspots, curtain),
                   zplanes=(*room.zplanes, ZPlane(2, bytes(room.geometry.room_width *
                                                           room.geometry.room_height)),
                            ZPlane(3, bytes(room.geometry.room_width * room.geometry.room_height))))
    raw = canonical_json(GameDocument("IM03Mask3", (room, destination_fixture())))
    third = destination / "third.png"
    Image.new("RGB", (64, 48), room.palette[2]).save(third)
    raw = import_object_third_image(raw, "Harbor", "Curtain", str(third))
    clear = destination / "clear.png"
    Image.new("L", (64, 48), 0).save(clear)
    for state in (1, 2, 3):
        raw = import_object_zplane(raw, "Harbor", "Curtain", str(clear), state, 1)
    raw = import_object_zplane(raw, "Harbor", "Curtain", str(clear), 3, 2)
    results = {}
    for label, level, box in (("masked", 255, 3), ("clear", 0, 3), ("wrongbox", 255, 2)):
        png = destination / f"{label}-mask.png"
        Image.new("L", (64, 48), level).save(png)
        doc = parse_document(import_object_zplane(raw, "Harbor", "Curtain", str(png), 3, 3))
        authored = replace(doc.rooms[0], walkboxes=(doc.rooms[0].walkboxes[0],
                           replace(doc.rooms[0].walkboxes[1], mask=box)))
        exact = canonical_json(replace(doc, rooms=(authored, *doc.rooms[1:])))
        (destination / f"{label}-project.json").write_text(exact, encoding="utf-8")
        authored = parse_document(exact).rooms[0]
        obj = next(h for h in authored.hotspots if h.id == "Curtain")
        if (obj.object_zplane_pixels != bytes(size) or obj.open_object_zplane_pixels != bytes(size)
                or obj.third_object_zplane_pixels != bytes(size)
                or obj.third_object_zplane2_pixels != bytes(size)
                or obj.third_object_zplane3_pixels != bytes([int(level != 0)])*size
                or authored.walkboxes[1].mask != box):
            raise RuntimeError("Independent IM03 mask or BOXD lost in JSON")
        results[label] = render_native_room(authored, upstream, generated, destination, label,
            crop="140x105+450+305", initial_object_state3="Curtain",
            scene_capture_seconds=12.0, scene_walk_target_x=412)
    masked, transparent, wrongbox = (results[k]["dark_costume_pixels"]
                                     for k in ("masked", "clear", "wrongbox"))
    report = {"variants": results, "masked_actor_pixels": masked,
              "transparent_actor_pixels": transparent, "wrongbox_actor_pixels": wrongbox,
              "native_im03_zp03_verified": min(transparent, wrongbox) >= 100 and
                                           masked <= min(transparent, wrongbox)//3}
    (destination / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not report["native_im03_zp03_verified"]:
        raise RuntimeError(f"IM03 ZP03 failed: {masked}/{transparent}/{wrongbox}")
    return report


if __name__ == "__main__":
    print(json.dumps(run(*(Path(x) for x in sys.argv[1:])), indent=2))

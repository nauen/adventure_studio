"""R07.1: native object-image Z-mask authored through Studio JSON and compiled as IM01."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

from .scumm_assets import RoomHotspot, ZPlane, destination_fixture
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
        390, 60, 64, 48, sprite_pixels=bytes([2]) * (64 * 48),
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
    # R07.2: use a real two-state object; change only its *second*
    # independently authored image Z-mask. Native fixture starts in object
    # state 2, using the product-exported IM02 and its ZP01 in stock ScummVM.
    two_state = replace(foreground, open_sprite_pixels=foreground.sprite_pixels)
    second_room = replace(room, hotspots=tuple(
        two_state if item.id == "Curtain" else item for item in room.hotspots
    ))
    second_base = canonical_json(GameDocument(
        "second_state_zmask", (second_room, destination_fixture())
    ))
    first_mask = destination / "curtain-first-state-clear.png"
    Image.new("L", (64, 48), 0).save(first_mask)
    second_base = import_object_zplane(second_base, "Harbor", "Curtain", str(first_mask), 1)
    second_variants = {}
    for label, level in (("secondmasked", 255), ("secondclear", 0)):
        Image.new("L", (64, 48), level).save(png)
        raw = import_object_zplane(second_base, "Harbor", "Curtain", str(png), 2)
        (destination / f"{label}-project.json").write_text(raw, encoding="utf-8")
        authored = parse_document(raw).rooms[0]
        obj = next(item for item in authored.hotspots if item.id == "Curtain")
        if obj.object_zplane_pixels != bytes(64 * 48):
            raise RuntimeError("Second-state import modified first object Z-mask")
        if obj.open_object_zplane_pixels != bytes([int(level != 0)]) * (64 * 48):
            raise RuntimeError("Second-state object Z-mask lost in project JSON")
        # The old six-second end frame catches different intermediate
        # positions in separately launched stock-ScummVM games. Wait until
        # the actor has finished its native approach before comparing IM02.
        second_variants[label] = render_native_room(
            authored, upstream, generated, destination, label,
            initial_object_state2="Curtain", scene_capture_seconds=12.0,
        )
    second_clear = second_variants["secondclear"]["dark_costume_pixels"]
    second_masked = second_variants["secondmasked"]["dark_costume_pixels"]
    if second_clear < 100 or second_masked > second_clear // 3:
        raise RuntimeError(
            "Native OBIM/IM02 second-state object Z-mask did not occlude actor: "
            f"clear={second_clear}, masked={second_masked}"
        )
    # R07.3: two separate IM01 ZPxx planes, composed in the actual
    # ScummC object sprite, against transparent and wrong-BOXD-index games.
    # Keep the room's own ZP02 transparent to isolate object-image masking.
    mask_room = replace(
        room, zplanes=(room.zplanes[0],
                        ZPlane(2, bytes(room.geometry.room_width * room.geometry.room_height))),
        walkboxes=(room.walkboxes[0], replace(room.walkboxes[1], mask=2)))
    z02_base = canonical_json(GameDocument(
        "im01_second_zplane", (mask_room, destination_fixture())))
    Image.new("L", (64, 48), 0).save(first_mask)
    z02_base = import_object_zplane(z02_base, "Harbor", "Curtain", str(first_mask), 1)
    two_planes = {}
    for label, level, actor_mask in (("im01-zp02-masked", 255, 2),
                                     ("im01-zp02-clear", 0, 2),
                                     ("im01-zp02-wrongbox", 255, 1)):
        Image.new("L", (64, 48), level).save(png)
        raw = import_object_zplane(z02_base, "Harbor", "Curtain", str(png), 1, 2)
        document = parse_document(raw)
        authored = document.rooms[0]
        if actor_mask == 1:
            authored = replace(authored, walkboxes=(
                authored.walkboxes[0], replace(authored.walkboxes[1], mask=1)))
        # Store the exact final Studio project used by ScummC, including the
        # negative control's changed BOXD index, never an earlier pre-edit JSON.
        project = canonical_json(replace(document, rooms=(authored, *document.rooms[1:])))
        (destination / f"{label}-project.json").write_text(project, encoding="utf-8")
        if parse_document(project).rooms[0].walkboxes != authored.walkboxes:
            raise RuntimeError("Object ZP02 negative-control JSON differs from linked BOXD")
        obj = next(h for h in authored.hotspots if h.id == "Curtain")
        if obj.object_zplane_pixels != bytes(64 * 48):
            raise RuntimeError("IM01 ZP02 PNG import altered independent ZP01")
        if obj.object_zplane2_pixels != bytes([int(level != 0)]) * (64 * 48):
            raise RuntimeError("IM01 ZP02 PNG lost in JSON roundtrip")
        two_planes[label] = render_native_room(
            authored, upstream, generated, destination, label)
    layer2_masked = two_planes["im01-zp02-masked"]["dark_costume_pixels"]
    layer2_clear = two_planes["im01-zp02-clear"]["dark_costume_pixels"]
    layer2_wrong = two_planes["im01-zp02-wrongbox"]["dark_costume_pixels"]
    if min(layer2_clear, layer2_wrong) < 100 or layer2_masked > min(layer2_clear, layer2_wrong) // 3:
        raise RuntimeError(
            f"IM01 ZP02 native actor occlusion failed: layer2_masked={layer2_masked}, "
            f"transparent={layer2_clear}, wrongbox={layer2_wrong}")
    # R07.4: export actual opened-state IM02 with independent ZP02.
    # Both room planes transparent, so only the object IM02 mask can
    # occlude an Actor assigned to BOX plane 2.
    open_room = replace(
        second_room, zplanes=(room.zplanes[0],
                               ZPlane(2, bytes(room.geometry.room_width *
                                               room.geometry.room_height))),
        walkboxes=(room.walkboxes[0], replace(room.walkboxes[1], mask=2)))
    open_project = canonical_json(GameDocument(
        "im02_second_zplane", (open_room, destination_fixture())))
    Image.new("L", (64, 48), 0).save(first_mask)
    open_project = import_object_zplane(open_project, "Harbor", "Curtain",
                                        str(first_mask), 1, 1)
    open_project = import_object_zplane(open_project, "Harbor", "Curtain",
                                        str(first_mask), 2, 1)
    open_variants = {}
    for label, level, box_mask in (("im02-zp02-masked", 255, 2),
                                    ("im02-zp02-clear", 0, 2),
                                    ("im02-zp02-wrongbox", 255, 1)):
        Image.new("L", (64, 48), level).save(png)
        edited = import_object_zplane(open_project, "Harbor", "Curtain",
                                       str(png), 2, 2)
        document = parse_document(edited)
        authored = document.rooms[0]
        if box_mask == 1:
            authored = replace(authored, walkboxes=(
                authored.walkboxes[0], replace(authored.walkboxes[1], mask=1)))
        exact = canonical_json(replace(document, rooms=(authored, *document.rooms[1:])))
        (destination / f"{label}-project.json").write_text(exact, encoding="utf-8")
        authored = parse_document(exact).rooms[0]
        obj = next(h for h in authored.hotspots if h.id == "Curtain")
        if obj.open_object_zplane_pixels != bytes(64 * 48):
            raise RuntimeError("IM02 ZP02 changed existing IM02 ZP01")
        if obj.open_object_zplane2_pixels != bytes([int(level != 0)]) * (64 * 48):
            raise RuntimeError("IM02 ZP02 lost in Studio JSON roundtrip")
        if obj.object_zplane_pixels != bytes(64 * 48):
            raise RuntimeError("IM02 ZP02 changed independent IM01 mask")
        if authored.walkboxes[1].mask != box_mask:
            raise RuntimeError("IM02 ZP02 control JSON differs from native BOXD")
        open_variants[label] = render_native_room(
            authored, upstream, generated, destination, label,
            initial_object_state2="Curtain")
    im02_masked = open_variants["im02-zp02-masked"]["dark_costume_pixels"]
    im02_clear = open_variants["im02-zp02-clear"]["dark_costume_pixels"]
    im02_wrong = open_variants["im02-zp02-wrongbox"]["dark_costume_pixels"]
    if min(im02_clear, im02_wrong) < 100 or im02_masked > min(im02_clear, im02_wrong) // 3:
        raise RuntimeError(
            f"IM02 ZP02 native occlusion failed: masked={im02_masked}, "
            f"clear={im02_clear}, wrongbox={im02_wrong}")
    # R07.8: fourth independent opened-state mask in productive IM02.
    # Clear RMIM layers and seven unaffected object planes isolate IM02 ZP04.
    open4_room = replace(second_room,
        zplanes=(room.zplanes[0],
                 ZPlane(2, bytes(room.geometry.room_width * room.geometry.room_height)),
                 ZPlane(3, bytes(room.geometry.room_width * room.geometry.room_height)),
                 ZPlane(4, bytes(room.geometry.room_width * room.geometry.room_height))),
        walkboxes=(room.walkboxes[0], replace(room.walkboxes[1], mask=4)))
    open4_project = canonical_json(GameDocument(
        "im02_fourth_zplane", (open4_room, destination_fixture())))
    Image.new("L", (64, 48), 0).save(first_mask)
    for state, layer in ((1, 1), (1, 2), (1, 3), (1, 4),
                         (2, 1), (2, 2), (2, 3)):
        open4_project = import_object_zplane(
            open4_project, "Harbor", "Curtain", str(first_mask), state, layer)
    open4_variants = {}
    for label, level, box_mask in (("im02-zp04-masked", 255, 4),
                                   ("im02-zp04-clear", 0, 4),
                                   ("im02-zp04-wrongbox", 255, 3)):
        Image.new("L", (64, 48), level).save(png)
        edited = import_object_zplane(open4_project, "Harbor", "Curtain", str(png), 2, 4)
        document = parse_document(edited)
        authored = document.rooms[0]
        if box_mask != 4:
            authored = replace(authored, walkboxes=(
                authored.walkboxes[0], replace(authored.walkboxes[1], mask=box_mask)))
        exact = canonical_json(replace(document, rooms=(authored, *document.rooms[1:])))
        (destination / f"{label}-project.json").write_text(exact, encoding="utf-8")
        authored = parse_document(exact).rooms[0]
        obj = next(h for h in authored.hotspots if h.id == "Curtain")
        other_planes = (obj.object_zplane_pixels, obj.object_zplane2_pixels,
                        obj.object_zplane3_pixels, obj.object_zplane4_pixels,
                        obj.open_object_zplane_pixels, obj.open_object_zplane2_pixels,
                        obj.open_object_zplane3_pixels)
        if any(plane != bytes(64 * 48) for plane in other_planes):
            raise RuntimeError("IM02 ZP04 changed another independent object plane")
        if obj.open_object_zplane4_pixels != bytes([int(level != 0)]) * (64 * 48):
            raise RuntimeError("IM02 ZP04 lost in JSON roundtrip")
        if authored.walkboxes[1].mask != box_mask:
            raise RuntimeError("IM02 ZP04 negative-control BOXD differs from JSON")
        open4_variants[label] = render_native_room(
            authored, upstream, generated, destination, label,
            initial_object_state2="Curtain")
    im02_zp04_masked = open4_variants["im02-zp04-masked"]["dark_costume_pixels"]
    im02_zp04_clear = open4_variants["im02-zp04-clear"]["dark_costume_pixels"]
    im02_zp04_wrong = open4_variants["im02-zp04-wrongbox"]["dark_costume_pixels"]
    if (min(im02_zp04_clear, im02_zp04_wrong) < 100
            or im02_zp04_masked > min(im02_zp04_clear, im02_zp04_wrong) // 3):
        raise RuntimeError(
            f"IM02 ZP04 native occlusion failed: masked={im02_zp04_masked}, "
            f"transparent={im02_zp04_clear}, wrongbox={im02_zp04_wrong}")
    # R07.7: four independent base-image masks in the productive IM01;
    # all four RMIM masks transparent, BOXD4 is the only occlusion source.
    layer4_room = replace(second_room,
        zplanes=(room.zplanes[0],
                 ZPlane(2, bytes(room.geometry.room_width * room.geometry.room_height)),
                 ZPlane(3, bytes(room.geometry.room_width * room.geometry.room_height)),
                 ZPlane(4, bytes(room.geometry.room_width * room.geometry.room_height))),
        walkboxes=(room.walkboxes[0], replace(room.walkboxes[1], mask=4)))
    layer4_project = canonical_json(GameDocument(
        "im01_fourth_zplane", (layer4_room, destination_fixture())))
    Image.new("L", (64, 48), 0).save(first_mask)
    for state, layer in ((1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)):
        layer4_project = import_object_zplane(
            layer4_project, "Harbor", "Curtain", str(first_mask), state, layer)
    layer4_variants = {}
    for label, level, box_mask in (("im01-zp04-masked", 255, 4),
                                   ("im01-zp04-clear", 0, 4),
                                   ("im01-zp04-wrongbox", 255, 3)):
        Image.new("L", (64, 48), level).save(png)
        edited = import_object_zplane(layer4_project, "Harbor", "Curtain", str(png), 1, 4)
        document = parse_document(edited)
        authored = document.rooms[0]
        if box_mask != 4:
            authored = replace(authored, walkboxes=(
                authored.walkboxes[0], replace(authored.walkboxes[1], mask=box_mask)))
        exact = canonical_json(replace(document, rooms=(authored, *document.rooms[1:])))
        (destination / f"{label}-project.json").write_text(exact, encoding="utf-8")
        authored = parse_document(exact).rooms[0]
        obj = next(h for h in authored.hotspots if h.id == "Curtain")
        unaffected = (obj.object_zplane_pixels, obj.object_zplane2_pixels,
                      obj.object_zplane3_pixels, obj.open_object_zplane_pixels,
                      obj.open_object_zplane2_pixels, obj.open_object_zplane3_pixels)
        if any(value != bytes(64 * 48) for value in unaffected):
            raise RuntimeError("IM01 ZP04 changed any independent earlier image mask")
        if obj.object_zplane4_pixels != bytes([int(level != 0)]) * (64 * 48):
            raise RuntimeError("IM01 ZP04 lost in project JSON roundtrip")
        if authored.walkboxes[1].mask != box_mask:
            raise RuntimeError("IM01 ZP04 control game BOXD index differs from JSON")
        layer4_variants[label] = render_native_room(
            authored, upstream, generated, destination, label)
    im01_zp04_masked = layer4_variants["im01-zp04-masked"]["dark_costume_pixels"]
    im01_zp04_clear = layer4_variants["im01-zp04-clear"]["dark_costume_pixels"]
    im01_zp04_wrong = layer4_variants["im01-zp04-wrongbox"]["dark_costume_pixels"]
    if (min(im01_zp04_clear, im01_zp04_wrong) < 100
            or im01_zp04_masked > min(im01_zp04_clear, im01_zp04_wrong) // 3):
        raise RuntimeError(
            f"IM01 ZP04 native occlusion failed: masked={im01_zp04_masked}, "
            f"transparent={im01_zp04_clear}, wrongbox={im01_zp04_wrong}")
    # R07.6: native IM02/ZP03 with transparent room masks and independent images.
    open3_room = replace(second_room, zplanes=(room.zplanes[0],
        ZPlane(2, bytes(room.geometry.room_width * room.geometry.room_height)),
        ZPlane(3, bytes(room.geometry.room_width * room.geometry.room_height))),
        walkboxes=(room.walkboxes[0], replace(room.walkboxes[1], mask=3)))
    open3_project = canonical_json(GameDocument(
        "im02_third_zplane", (open3_room, destination_fixture())))
    Image.new("L", (64, 48), 0).save(first_mask)
    for state, layer in ((1, 1), (1, 2), (1, 3), (2, 1), (2, 2)):
        open3_project = import_object_zplane(
            open3_project, "Harbor", "Curtain", str(first_mask), state, layer)
    open3_variants = {}
    for label, level, box_mask in (("im02-zp03-masked", 255, 3),
                                   ("im02-zp03-clear", 0, 3),
                                   ("im02-zp03-wrongbox", 255, 2)):
        Image.new("L", (64, 48), level).save(png)
        edited = import_object_zplane(open3_project, "Harbor", "Curtain", str(png), 2, 3)
        document = parse_document(edited)
        authored = document.rooms[0]
        if box_mask != 3:
            authored = replace(authored, walkboxes=(
                authored.walkboxes[0], replace(authored.walkboxes[1], mask=box_mask)))
        exact = canonical_json(replace(document, rooms=(authored, *document.rooms[1:])))
        (destination / f"{label}-project.json").write_text(exact, encoding="utf-8")
        authored = parse_document(exact).rooms[0]
        obj = next(h for h in authored.hotspots if h.id == "Curtain")
        independent = (obj.object_zplane_pixels, obj.object_zplane2_pixels,
                       obj.object_zplane3_pixels, obj.open_object_zplane_pixels,
                       obj.open_object_zplane2_pixels)
        if any(value != bytes(64 * 48) for value in independent):
            raise RuntimeError("IM02 ZP03 modified independent ZP01/ZP02 or IM01")
        if obj.open_object_zplane3_pixels != bytes([int(level != 0)]) * (64 * 48):
            raise RuntimeError("IM02 ZP03 lost in JSON roundtrip")
        if authored.walkboxes[1].mask != box_mask:
            raise RuntimeError("IM02 ZP03 negative control disagrees with BOXD")
        open3_variants[label] = render_native_room(
            authored, upstream, generated, destination, label,
            initial_object_state2="Curtain")
    im02_zp03_masked = open3_variants["im02-zp03-masked"]["dark_costume_pixels"]
    im02_zp03_clear = open3_variants["im02-zp03-clear"]["dark_costume_pixels"]
    im02_zp03_wrong = open3_variants["im02-zp03-wrongbox"]["dark_costume_pixels"]
    if (min(im02_zp03_clear, im02_zp03_wrong) < 100
            or im02_zp03_masked > min(im02_zp03_clear, im02_zp03_wrong) // 3):
        raise RuntimeError(
            f"IM02 ZP03 native occlusion failed: masked={im02_zp03_masked}, "
            f"transparent={im02_zp03_clear}, wrongbox={im02_zp03_wrong}")
    # R07.5: third independent base-image Z-plane; all room Z-planes are
    # transparent. Only the productive IM01/ZP03 can occlude BOX index 3.
    layer3_room = replace(
        room,
        zplanes=(room.zplanes[0],
                 ZPlane(2, bytes(room.geometry.room_width * room.geometry.room_height)),
                 ZPlane(3, bytes(room.geometry.room_width * room.geometry.room_height))),
        walkboxes=(room.walkboxes[0], replace(room.walkboxes[1], mask=3)))
    layer3_project = canonical_json(GameDocument(
        "im01_third_zplane", (layer3_room, destination_fixture())))
    Image.new("L", (64, 48), 0).save(first_mask)
    layer3_project = import_object_zplane(layer3_project, "Harbor", "Curtain",
                                          str(first_mask), 1, 1)
    layer3_project = import_object_zplane(layer3_project, "Harbor", "Curtain",
                                          str(first_mask), 1, 2)
    layer3_variants = {}
    for label, level, box_mask in (("im01-zp03-masked", 255, 3),
                                   ("im01-zp03-clear", 0, 3),
                                   ("im01-zp03-wrongbox", 255, 2)):
        Image.new("L", (64, 48), level).save(png)
        edited = import_object_zplane(layer3_project, "Harbor", "Curtain", str(png), 1, 3)
        document = parse_document(edited)
        authored = document.rooms[0]
        if box_mask != 3:
            authored = replace(authored, walkboxes=(
                authored.walkboxes[0], replace(authored.walkboxes[1], mask=box_mask)))
        exact = canonical_json(replace(document, rooms=(authored, *document.rooms[1:])))
        (destination / f"{label}-project.json").write_text(exact, encoding="utf-8")
        authored = parse_document(exact).rooms[0]
        obj = next(h for h in authored.hotspots if h.id == "Curtain")
        if obj.object_zplane_pixels != bytes(64 * 48) or obj.object_zplane2_pixels != bytes(64 * 48):
            raise RuntimeError("IM01 ZP03 modified independent ZP01/ZP02")
        if obj.object_zplane3_pixels != bytes([int(level != 0)]) * (64 * 48):
            raise RuntimeError("IM01 ZP03 lost in JSON roundtrip")
        if authored.walkboxes[1].mask != box_mask:
            raise RuntimeError("IM01 ZP03 wrongbox control differs from JSON")
        layer3_variants[label] = render_native_room(
            authored, upstream, generated, destination, label)
    layer3_masked = layer3_variants["im01-zp03-masked"]["dark_costume_pixels"]
    layer3_clear = layer3_variants["im01-zp03-clear"]["dark_costume_pixels"]
    layer3_wrong = layer3_variants["im01-zp03-wrongbox"]["dark_costume_pixels"]
    if min(layer3_clear, layer3_wrong) < 100 or layer3_masked > min(layer3_clear, layer3_wrong) // 3:
        raise RuntimeError(
            f"IM01 ZP03 native occlusion failed: masked={layer3_masked}, "
            f"transparent={layer3_clear}, wrongbox={layer3_wrong}")
    report = {
        "im02_fourth_zplane": {
            "variants": open4_variants,
            "masked_actor_pixels": im02_zp04_masked,
            "transparent_actor_pixels": im02_zp04_clear,
            "wrongbox_actor_pixels": im02_zp04_wrong,
            "native_im02_zp04_passed": True,
        },
        "im01_fourth_zplane": {
            "variants": layer4_variants,
            "masked_actor_pixels": im01_zp04_masked,
            "transparent_actor_pixels": im01_zp04_clear,
            "wrongbox_actor_pixels": im01_zp04_wrong,
            "native_im01_zp04_passed": True,
        },
        "im02_third_zplane": {
            "variants": open3_variants,
            "masked_actor_pixels": im02_zp03_masked,
            "transparent_actor_pixels": im02_zp03_clear,
            "wrongbox_actor_pixels": im02_zp03_wrong,
            "native_im02_zp03_passed": True,
        },
        "im01_third_zplane": {
            "variants": layer3_variants,
            "masked_actor_pixels": layer3_masked,
            "transparent_actor_pixels": layer3_clear,
            "wrongbox_actor_pixels": layer3_wrong,
            "native_im01_zp03_passed": True,
        },
        "im02_second_zplane": {
            "variants": open_variants,
            "masked_actor_pixels": im02_masked,
            "transparent_actor_pixels": im02_clear,
            "wrongbox_actor_pixels": im02_wrong,
            "native_im02_zp02_passed": True,
        },
        "im01_second_zplane": {
            "variants": two_planes,
            "masked_actor_pixels": layer2_masked,
            "transparent_actor_pixels": layer2_clear,
            "wrongbox_actor_pixels": layer2_wrong,
            "native_im01_zp02_passed": True,
        },
        "authoring": "Studio PNG -> project JSON -> object states IM01 ZP01 -> stock ScummVM",
        "variants": variants,
        "second_image_state": {
            "variants": second_variants,
            "clear_costume_pixels": second_clear,
            "masked_costume_pixels": second_masked,
            "native_second_state_zmask_verified": True,
        },
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

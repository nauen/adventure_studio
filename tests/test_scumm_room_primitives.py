"""Native-source compatibility checks for v6 mask and walkbox assets."""

import struct
import tempfile
import unittest
from importlib.util import find_spec
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_assets import (ScaleCurve, ZPlane, _native_box_file,
                                          destination_fixture, scrolling_fixture,
                                          scummc_room_source, write_room_sources)
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document
from adventure_studio.scumm_room_fixture import native_room, perspective_room
from adventure_studio.studio_sequences import author_room_walkbox, author_room_box_connections, author_room_scale_curve, compose_story_project
from adventure_studio.studio_sequences import import_room_zplane, author_room_walkbox_zplane


class RoomNativePrimitiveTests(unittest.TestCase):
    def test_free_walkbox_polygon_authors_json_and_boxd(self):
        room = scrolling_fixture()
        raw = canonical_json(GameDocument("walkbox", (room, destination_fixture())))
        updated = author_room_walkbox(raw, "Harbor", 1,
                                      "20,75; 130,70; 145,145; 10,150")
        authored = parse_document(updated).rooms[0]
        self.assertEqual(authored.walkboxes[0].corners,
                         ((20, 75), (130, 70), (145, 145), (10, 150)))
        with tempfile.TemporaryDirectory() as directory:
            write_room_sources(authored, Path(directory))
            data = (Path(directory) / "Harbor.box").read_bytes()
            self.assertEqual(struct.unpack_from("<8h", data, 9),
                             (20, 75, 130, 70, 145, 145, 10, 150))
        with self.assertRaisesRegex(ValueError, "lückenlos"):
            author_room_walkbox(updated, "Harbor", 3,
                                "20,75; 130,70; 145,145; 10,150")
        with self.assertRaisesRegex(ValueError, "konvex"):
            author_room_walkbox(updated, "Harbor", 1,
                                "20,75; 130,70; 30,90; 10,150")
        with self.assertRaisesRegex(ValueError, "innerhalb"):
            author_room_walkbox(updated, "Harbor", 1,
                                "20,75; 700,70; 145,145; 10,150")

    def test_replace_walkbox_preserves_routes_and_story_composition(self):
        room = native_room()
        raw = canonical_json(GameDocument("walkbox", (room, destination_fixture())))
        updated = author_room_walkbox(raw, "Harbor", 1,
                                      "0,70; 110,70; 110,150; 0,150")
        authored = parse_document(updated).rooms[0]
        self.assertEqual(authored.box_routes, room.box_routes)
        self.assertEqual(authored.scale_slots, room.scale_slots)
        with self.assertRaisesRegex(ValueError, "BOXM"):
            author_room_walkbox(updated, "Harbor", 3,
                                "120,70; 200,70; 200,150; 120,150")
        story = (Path(__file__).resolve().parents[1] / "examples" /
                 "mini_story_chain.json").read_text(encoding="utf-8")
        composed = parse_document(compose_story_project(story, updated))
        harbor = next(item for item in composed.rooms if item.name == "Harbor")
        self.assertEqual(harbor.walkboxes, authored.walkboxes)
        self.assertEqual(harbor.box_routes, authored.box_routes)

    def test_boxm_connections_author_next_hops_and_export(self):
        raw = canonical_json(GameDocument("boxm_routes",
                                          (scrolling_fixture(), destination_fixture())))
        for index, corners in ((1, "0,70; 110,70; 110,150; 0,150"),
                               (2, "110,70; 240,70; 240,150; 110,150"),
                               (3, "240,70; 639,70; 639,150; 240,150")):
            raw = author_room_walkbox(raw, "Harbor", index, corners)
        updated = author_room_box_connections(raw, "Harbor", "1-2; 2-3")
        room = parse_document(updated).rooms[0]
        self.assertEqual(room.box_routes[1][3], 2)
        self.assertEqual(room.box_routes[3][1], 2)
        self.assertEqual(room.box_routes[2][1], 1)
        self.assertEqual(room.box_routes[1][0], None)
        self.assertEqual(room.box_routes[0][0], 0)
        self.assertEqual(author_room_box_connections(updated, "Harbor", "2-3; 1-2"), updated)
        with tempfile.TemporaryDirectory() as directory:
            write_room_sources(room, Path(directory))
            binary = (Path(directory) / "Harbor.box").read_bytes()
            boxd_size = struct.unpack_from(">I", binary, 4)[0]
            self.assertEqual(binary[boxd_size:boxd_size + 4], b"BOXM")
            self.assertIn(bytes((2, 3, 2)), binary[boxd_size:])
        story = (Path(__file__).resolve().parents[1] / "examples" /
                 "mini_story_chain.json").read_text(encoding="utf-8")
        composed = parse_document(compose_story_project(story, updated))
        self.assertEqual(next(r for r in composed.rooms if r.name == "Harbor").box_routes,
                         room.box_routes)

        disconnected = parse_document(author_room_box_connections(updated, "Harbor", "")).rooms[0]
        self.assertIsNone(disconnected.box_routes[1][2])
        self.assertEqual(disconnected.box_routes[1][1], 1)
        with self.assertRaisesRegex(ValueError, "gemeinsame Kante"):
            author_room_box_connections(updated, "Harbor", "1-3")
        with self.assertRaisesRegex(ValueError, "Ungültige"):
            author_room_box_connections(updated, "Harbor", "1-4")
        with self.assertRaisesRegex(ValueError, "ohne Selbstverbindung"):
            author_room_box_connections(updated, "Harbor", "2-2")
        self.assertEqual(parse_document(updated).rooms[0].walkboxes, room.walkboxes)

    def test_studio_authored_scal_json_story_and_native_box_encoding(self):
        base = native_room(occlusion=False, far_scale=255)
        raw = canonical_json(GameDocument("studio_scal", (base, destination_fixture())))
        updated = author_room_scale_curve(raw, "Harbor", 1, 80, 70, 255, 155, "1,2")
        room = parse_document(updated).rooms[0]
        self.assertEqual(room.scale_curves, (ScaleCurve(1, 80, 70, 255, 155),))
        self.assertEqual(tuple(box.scale_slot for box in room.walkboxes), (1, 1))
        self.assertEqual(room.box_routes, base.box_routes)
        self.assertIsNone(room.scale_slots)
        binary = _native_box_file(room)
        self.assertEqual(struct.unpack_from("<H", binary, 27)[0], 0x8000)
        self.assertEqual(struct.unpack_from("<H", binary, 48)[0], 0x8000)
        scal = binary.index(b"SCAL")
        self.assertEqual(struct.unpack_from("<HHHH", binary, scal + 8),
                         (80, 70, 255, 155))
        story = (Path(__file__).resolve().parents[1] / "examples" /
                 "mini_story_chain.json").read_text(encoding="utf-8")
        composed = parse_document(compose_story_project(story, updated))
        self.assertEqual(next(r for r in composed.rooms if r.name == "Harbor").scale_curves,
                         room.scale_curves)
        self.assertEqual(author_room_scale_curve(updated, "Harbor", 1, 80, 70, 255, 155, "1,2"),
                         updated)
        second = author_room_scale_curve(updated, "Harbor", 2, 120, 80, 220, 145, "2")
        assigned = parse_document(second).rooms[0]
        self.assertEqual(tuple(box.scale_slot for box in assigned.walkboxes), (1, 2))
        self.assertEqual([c.slot for c in assigned.scale_curves], [1, 2])

    def test_studio_scal_rejects_invalid_and_nonzero_raw_curves(self):
        base = native_room()
        raw = canonical_json(GameDocument("bad_scal", (base, destination_fixture())))
        with self.assertRaisesRegex(ValueError, "Slot"):
            author_room_scale_curve(raw, "Harbor", 5, 80, 70, 255, 155, "1")
        with self.assertRaisesRegex(ValueError, "Skalierung"):
            author_room_scale_curve(raw, "Harbor", 1, 0, 70, 255, 155, "1")
        with self.assertRaisesRegex(ValueError, "eindeutig"):
            author_room_scale_curve(raw, "Harbor", 1, 80, 70, 255, 155, "1,1")
        with self.assertRaisesRegex(ValueError, "eindeutig"):
            author_room_scale_curve(raw, "Harbor", 1, 80, 70, 255, 155, "3")
        with self.assertRaisesRegex(ValueError, "nicht still"):
            dirty = replace(base, scale_slots=b"\x01" + bytes(31))
            author_room_scale_curve(
                canonical_json(GameDocument("dirty", (dirty, destination_fixture()))),
                "Harbor", 1, 80, 70, 255, 155, "1")

    @unittest.skipUnless(find_spec("PIL"), "PNG authoring requires optional studio Pillow")
    def test_authored_png_mask_roundtrips_to_native_room_assets(self):
        from PIL import Image

        room = native_room(occlusion=False)
        raw = canonical_json(GameDocument("authored", (room, destination_fixture())))
        width, height = room.geometry.room_width, room.geometry.room_height
        with tempfile.TemporaryDirectory() as directory:
            png = Path(directory) / "author-mask.png"
            mask = Image.new("RGBA", (width, height), (0, 0, 0, 255))
            mask.putpixel((10, 20), (255, 255, 255, 255))
            mask.putpixel((11, 20), (255, 255, 255, 0))
            mask.save(png)
            updated = import_room_zplane(raw, room.name, 1, str(png))
            stored = parse_document(updated).rooms[0]
            self.assertEqual(stored.zplanes[0].pixels[20 * width + 10], 1)
            self.assertEqual(stored.zplanes[0].pixels[20 * width + 11], 0)
            self.assertEqual(sum(stored.zplanes[0].pixels), 1)
            write_room_sources(stored, Path(directory))
            self.assertIn('zplane = { "HarborZ01.bmp" };',
                          (Path(directory) / "Harbor.scc").read_text())
            self.assertTrue((Path(directory) / "HarborZ01.bmp").exists())
            with self.assertRaisesRegex(ValueError, "lückenlos"):
                import_room_zplane(updated, room.name, 3, str(png))
            mask.resize((width // 2, height)).save(png)
            with self.assertRaisesRegex(ValueError, "exakt"):
                import_room_zplane(updated, room.name, 2, str(png))

    @unittest.skipUnless(find_spec("PIL"), "PNG authoring requires optional studio Pillow")
    def test_two_png_zplanes_can_be_selected_per_walkbox_without_losing_routes(self):
        from PIL import Image

        base = native_room(occlusion=False)
        raw = canonical_json(GameDocument("multi_z", (base, destination_fixture())))
        width, height = base.geometry.room_width, base.geometry.room_height
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.png"
            second = Path(directory) / "second.png"
            Image.new("L", (width, height), color=0).save(first)
            mask = Image.new("L", (width, height), color=0)
            mask.putpixel((540, 90), 255)
            mask.save(second)
            raw = import_room_zplane(raw, "Harbor", 1, str(first))
            raw = import_room_zplane(raw, "Harbor", 2, str(second))
            raw = author_room_walkbox_zplane(raw, "Harbor", 2, 2)
            room = parse_document(raw).rooms[0]
            self.assertEqual(len(room.zplanes), 2)
            self.assertEqual(tuple(box.mask for box in room.walkboxes), (0, 2))
            self.assertEqual(room.zplanes[1].pixels[90 * width + 540], 1)
            self.assertEqual(room.box_routes, base.box_routes)
            write_room_sources(room, Path(directory))
            source = (Path(directory) / "Harbor.scc").read_text()
            self.assertIn('"HarborZ01.bmp", "HarborZ02.bmp"', source)
            self.assertTrue((Path(directory) / "HarborZ02.bmp").exists())
            binary = (Path(directory) / "Harbor.box").read_bytes()
            # 21-byte native box records: box 0 is reserved, box 2 starts at byte 30.
            self.assertEqual(binary[30 + 16], 2)
            story = (Path(__file__).resolve().parents[1] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            composed = parse_document(compose_story_project(story, raw))
            self.assertEqual(next(r for r in composed.rooms if r.name == "Harbor").zplanes,
                             room.zplanes)
            self.assertEqual(next(r for r in composed.rooms if r.name == "Harbor").walkboxes,
                             room.walkboxes)
            with self.assertRaisesRegex(ValueError, "vorhandene PNG"):
                author_room_walkbox_zplane(raw, "Harbor", 2, 3)
            with self.assertRaisesRegex(ValueError, "vorhandene Walkbox"):
                author_room_walkbox_zplane(raw, "Harbor", 3, 2)
            self.assertEqual(author_room_walkbox_zplane(raw, "Harbor", 2, 2), raw)

    @unittest.skipUnless(find_spec("PIL"), "PNG authoring requires optional studio Pillow")
    def test_studio_object_zmask_json_story_and_native_obim_source(self):
        from PIL import Image

        from adventure_studio.studio_sequences import import_object_zmask
        base = scrolling_fixture()
        document = GameDocument("object_zmask", (base, destination_fixture()))
        raw = canonical_json(document)
        door = next(obj for obj in base.hotspots if obj.id == "Door")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = Image.new("RGBA", (door.width, door.height), (0, 0, 0, 255))
            image.putpixel((3, 5), (255, 255, 255, 255))
            image.putpixel((4, 5), (255, 255, 255, 0))
            png = root / "door-mask.png"
            image.save(png)
            updated = import_object_zmask(raw, "Harbor", "Door", str(png))
            stored = parse_document(updated).rooms[0]
            masked = next(obj for obj in stored.hotspots if obj.id == "Door")
            self.assertEqual(masked.object_zmask_pixels[5 * door.width + 3], 1)
            self.assertEqual(masked.object_zmask_pixels[5 * door.width + 4], 0)
            self.assertEqual(len(masked.object_zmask_pixels), 256)
            self.assertEqual(next(obj for obj in stored.hotspots if obj.id == "Key").object_zmask_pixels, None)
            self.assertIn('"Door.bmp", { "DoorZ01.bmp" }', scummc_room_source(stored))
            write_room_sources(stored, root)
            self.assertTrue((root / "DoorZ01.bmp").is_file())
            story = (Path(__file__).resolve().parents[1] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            composed = parse_document(compose_story_project(story, updated))
            self.assertEqual(next(obj for obj in composed.rooms[0].hotspots
                                  if obj.id == "Door").object_zmask_pixels,
                             masked.object_zmask_pixels)
            with self.assertRaisesRegex(ValueError, "nicht aufhebbares"):
                import_object_zmask(raw, "Harbor", "Key", str(png))
            image.resize((8, 8)).save(png)
            with self.assertRaisesRegex(ValueError, "exakt"):
                import_object_zmask(raw, "Harbor", "Door", str(png))

    def test_project_json_roundtrip_preserves_native_assets(self):
        document = GameDocument("native", (native_room(), destination_fixture()))
        self.assertEqual(parse_document(canonical_json(document)), document)

    def test_emitted_scummc_source_and_bmp_and_box_chunks(self):
        room = native_room()
        source = scummc_room_source(room)
        self.assertIn('zplane = { "HarborZ01.bmp" };', source)
        self.assertIn('boxd = "Harbor.box";', source)
        with tempfile.TemporaryDirectory() as directory:
            write_room_sources(room, Path(directory))
            mask = (Path(directory) / "HarborZ01.bmp").read_bytes()
            self.assertEqual(struct.unpack_from("<ii", mask, 18),
                             (room.geometry.room_width, room.geometry.room_height))
            self.assertEqual(struct.unpack_from("<I", mask, 46)[0], 2)
            data = (Path(directory) / "Harbor.box").read_bytes()
            self.assertEqual(data[:4], b"boxd")
            boxd_length = struct.unpack_from(">I", data, 4)[0]
            self.assertEqual(boxd_length, 8 + 21 * 2)
            self.assertEqual(data[boxd_length:boxd_length + 4], b"BOXM")
            boxm_length = struct.unpack_from(">I", data, boxd_length + 4)[0]
            self.assertEqual(data[boxd_length + boxm_length:boxd_length + boxm_length + 4], b"SCAL")
            self.assertEqual(struct.unpack_from(">I", data, boxd_length + boxm_length + 4)[0], 40)

    def test_invalid_zplane_and_routes_fail_before_writing(self):
        room = native_room()
        with self.assertRaisesRegex(ValueError, "Z-plane"):
            scummc_room_source(replace(room, zplanes=(ZPlane(2, b"\x00"),)))
        with self.assertRaisesRegex(ValueError, "BOXM"):
            _native_box_file(replace(room, box_routes=((0,),)))
        with self.assertRaisesRegex(ValueError, "SCAL"):
            _native_box_file(replace(room, scale_slots=b"bad"))

    def test_control_variants_isolate_mask_and_scale(self):
        masked = native_room()
        clear = native_room(occlusion=False)
        fullscale = native_room(occlusion=False, far_scale=255)
        self.assertEqual(masked.walkboxes, clear.walkboxes)
        self.assertNotEqual(masked.zplanes[0].pixels, clear.zplanes[0].pixels)
        self.assertEqual(clear.zplanes, fullscale.zplanes)
        self.assertEqual(fullscale.walkboxes[-1].scale, 255)
        self.assertEqual(clear.walkboxes[-1].scale, 180)
        self.assertIn("setActorFollowBoxes();", scummc_room_source(masked))
        self.assertNotIn("setActorIgnoreBoxes();", scummc_room_source(masked))
        self.assertIn("setActorIgnoreBoxes();", scummc_room_source(scrolling_fixture()))

    def test_native_scal_curve_and_box_reference_are_encoded(self):
        room = perspective_room(target_y=145)
        binary = _native_box_file(room)
        self.assertEqual(struct.unpack_from("<H", binary, 27)[0], 0x8000)
        self.assertEqual(struct.unpack_from("<H", binary, 48)[0], 0x8000)
        scal = binary.index(b"SCAL")
        self.assertEqual(struct.unpack_from(">I", binary, scal + 4)[0], 40)
        self.assertEqual(struct.unpack_from("<HHHH", binary, scal + 8),
                         (80, 70, 255, 155))
        self.assertEqual(binary[scal + 16:scal + 40], bytes(24))
        self.assertIn("walkActorTo(VAR_EGO, 540, 145);", scummc_room_source(room))
        document = GameDocument("curve", (room, destination_fixture()))
        self.assertEqual(parse_document(canonical_json(document)), document)

    def test_rejects_invalid_native_scal_curve_contracts(self):
        room = perspective_room()
        with self.assertRaisesRegex(ValueError, "undefined SCAL curve"):
            _native_box_file(replace(room, scale_curves=()))
        with self.assertRaisesRegex(ValueError, "Invalid SCAL curve"):
            _native_box_file(replace(room, scale_curves=(ScaleCurve(1, 80, 130, 255, 70),)))
        with self.assertRaisesRegex(ValueError, "Raw SCAL"):
            _native_box_file(replace(room, scale_slots=bytes(32)))
        with self.assertRaisesRegex(ValueError, "Demo walk Y"):
            scummc_room_source(replace(room, demo_walk_to_y=999))

    def test_legacy_json_omits_new_optional_fields(self):
        room = scrolling_fixture()
        json_text = canonical_json(GameDocument("legacy", (room, destination_fixture())))
        self.assertNotIn('"zplanes"', json_text)
        self.assertNotIn('"walkboxes"', json_text)
        self.assertEqual(parse_document(json_text).rooms[0], room)

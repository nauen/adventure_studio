"""Native-source compatibility checks for v6 mask and walkbox assets."""

import struct
import tempfile
import unittest
from importlib.util import find_spec
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_assets import (ScaleCurve, ZPlane, _native_box_file,
                                          destination_fixture, scrolling_fixture,
                                          scummc_room_source, write_game_sources,
                                          write_room_sources)
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document
from adventure_studio.scumm_room_fixture import native_room, perspective_room
from adventure_studio.studio_sequences import author_room_walkbox, author_room_box_connections, author_room_scale_curve, compose_story_project
from adventure_studio.studio_sequences import import_room_zplane, author_room_walkbox_zplane


class RoomNativePrimitiveTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "PNG authoring requires optional studio Pillow")
    def test_object_zmask_png_json_story_and_native_im01(self):
        from PIL import Image
        from adventure_studio.studio_sequences import import_object_zplane

        room = scrolling_fixture()
        raw = canonical_json(GameDocument("object_mask", (room, destination_fixture())))
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            png = directory / "object-mask.png"
            Image.new("L", (16, 16), color=255).save(png)
            updated = import_object_zplane(raw, "Harbor", "Door", str(png))
            authored = parse_document(updated).rooms[0]
            door = next(h for h in authored.hotspots if h.id == "Door")
            self.assertEqual(door.object_zplane_pixels, bytes([1]) * 256)
            write_room_sources(authored, directory)
            source = (directory / "Harbor.scc").read_text()
            self.assertIn('"Door.bmp", { "DoorZ01.bmp" }', source)
            self.assertTrue((directory / "DoorZ01.bmp").exists())
            story = (Path(__file__).resolve().parents[1] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            composed = parse_document(compose_story_project(story, updated))
            saved = next(h for r in composed.rooms if r.name == "Harbor"
                         for h in r.hotspots if h.id == "Door")
            self.assertEqual(saved.object_zplane_pixels, door.object_zplane_pixels)
            Image.new("L", (8, 8), color=255).save(png)
            with self.assertRaisesRegex(ValueError, "exakt"):
                import_object_zplane(updated, "Harbor", "Door", str(png))
            with self.assertRaisesRegex(ValueError, "Objektbild"):
                import_object_zplane(raw, "Harbor", "missing", str(png))

    @unittest.skipUnless(find_spec("PIL"), "PNG authoring requires optional studio Pillow")
    def test_second_object_state_zmask_roundtrip_and_native_im02(self):
        from PIL import Image
        from adventure_studio.studio_sequences import import_object_zplane

        room = scrolling_fixture()
        raw = canonical_json(GameDocument("two_state_mask", (room, destination_fixture())))
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            png = directory / "door-mask.png"
            Image.new("L", (16, 16), color=255).save(png)
            first = import_object_zplane(raw, "Harbor", "Door", str(png), 1)
            Image.new("L", (16, 16), color=0).save(png)
            second = import_object_zplane(first, "Harbor", "Door", str(png), 2)
            saved = next(h for h in parse_document(second).rooms[0].hotspots if h.id == "Door")
            self.assertEqual(saved.object_zplane_pixels, bytes([1]) * 256)
            self.assertEqual(saved.open_object_zplane_pixels, bytes(256))
            write_room_sources(parse_document(second).rooms[0], directory)
            source = (directory / "Harbor.scc").read_text()
            self.assertIn('"Door.bmp", { "DoorZ01.bmp" }', source)
            self.assertIn('"DoorOpen.bmp", { "DoorOpenZ01.bmp" }', source)
            self.assertTrue((directory / "DoorZ01.bmp").is_file())
            self.assertTrue((directory / "DoorOpenZ01.bmp").is_file())
            story = (Path(__file__).parent / "fixtures" / "mini_story_chain.json").read_text(encoding="utf-8")
            composed = parse_document(compose_story_project(story, second))
            persisted = next(h for r in composed.rooms if r.name == "Harbor"
                             for h in r.hotspots if h.id == "Door")
            self.assertEqual(persisted.open_object_zplane_pixels, saved.open_object_zplane_pixels)
            with self.assertRaisesRegex(ValueError, "Bildzustand 2"):
                import_object_zplane(first, "Harbor", "Key", str(png), 2)
            with self.assertRaisesRegex(ValueError, "Bildzustand 1 oder 2"):
                import_object_zplane(first, "Harbor", "Door", str(png), 3)
            Image.new("L", (8, 8), color=255).save(png)
            with self.assertRaisesRegex(ValueError, "exakt"):
                import_object_zplane(first, "Harbor", "Door", str(png), 2)

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
                                      "0,70; 120,70; 120,150; 0,150")
        authored = parse_document(updated).rooms[0]
        self.assertEqual(authored.box_routes, room.box_routes)
        self.assertEqual(authored.scale_slots, room.scale_slots)
        extended = author_room_walkbox(updated, "Harbor", 3,
                                       "120,150; 200,150; 200,199; 120,199")
        extra = parse_document(extended).rooms[0]
        self.assertEqual(extra.box_routes[:3],
                         tuple(row + (None,) for row in authored.box_routes))
        self.assertEqual(extra.box_routes[3], (None, None, None, 3))
        self.assertEqual(extra.walkboxes[:2], authored.walkboxes)
        self.assertEqual(extra.scale_slots, authored.scale_slots)
        with tempfile.TemporaryDirectory() as directory:
            write_room_sources(extra, Path(directory))
            binary = (Path(directory) / "Harbor.box").read_bytes()
            offset = struct.unpack_from(">I", binary, 4)[0]
            self.assertEqual(binary[offset:offset + 4], b"BOXM")
        linked = parse_document(author_room_box_connections(
            extended, "Harbor", "1-2; 2-3")).rooms[0]
        self.assertEqual(linked.box_routes[1][3], 2)
        self.assertEqual(linked.box_routes[3][1], 2)
        self.assertEqual(linked.box_routes[1][2], authored.box_routes[1][2])
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

    def test_branching_four_box_alternative_paths_survive_native_export(self):
        from adventure_studio.scumm_boxm_routing_probe import verify_branching_boxm

        raw = canonical_json(GameDocument("branching_routes",
                                          (scrolling_fixture(), destination_fixture())))
        for index, corners in (
                (1, "0,70; 110,70; 110,150; 0,150"),
                (2, "110,70; 240,70; 240,110; 110,110"),
                (3, "110,110; 240,110; 240,150; 110,150"),
                (4, "240,70; 639,70; 639,150; 240,150")):
            raw = author_room_walkbox(raw, "Harbor", index, corners)
        upper = author_room_box_connections(raw, "Harbor", "1-2; 2-4")
        lower = author_room_box_connections(raw, "Harbor", "1-3; 3-4")
        upper_room = parse_document(upper).rooms[0]
        lower_room = parse_document(lower).rooms[0]
        self.assertEqual(upper_room.box_routes[1][4], 2)
        self.assertEqual(lower_room.box_routes[1][4], 3)
        self.assertEqual(upper_room.box_routes[4][1], 2)
        self.assertEqual(lower_room.box_routes[4][1], 3)
        self.assertEqual(len(upper_room.walkboxes), 4)
        self.assertEqual(parse_document(canonical_json(parse_document(upper))).rooms[0],
                         upper_room)
        story = (Path(__file__).resolve().parents[1] / "examples" /
                 "mini_story_chain.json").read_text(encoding="utf-8")
        saved = next(room for room in
                     parse_document(compose_story_project(story, lower)).rooms
                     if room.name == "Harbor")
        self.assertEqual(saved.box_routes, lower_room.box_routes)
        with tempfile.TemporaryDirectory() as directory:
            write_room_sources(upper_room, Path(directory))
            binary_upper = (Path(directory) / "Harbor.box").read_bytes()
            write_room_sources(lower_room, Path(directory))
            binary_lower = (Path(directory) / "Harbor.box").read_bytes()
            self.assertNotEqual(binary_upper, binary_lower)
            self.assertIn(b"BOXM", binary_upper)
            self.assertIn(b"BOXM", binary_lower)
        with self.assertRaisesRegex(ValueError, "gemeinsame Kante"):
            author_room_box_connections(raw, "Harbor", "1-4")
        def scene(reached, matrix):
            return {"frame_report": {"scroll_color_signature_passed": reached},
                    "route_matrix": [list(row) for row in matrix]}
        blocked = parse_document(author_room_box_connections(raw, "Harbor", "")).rooms[0]
        result = verify_branching_boxm(
            scene(True, upper_room.box_routes), scene(True, lower_room.box_routes),
            scene(False, blocked.box_routes), 100)
        self.assertTrue(result["native_branching_boxm_passed"])
        with self.assertRaisesRegex(RuntimeError, "Both alternative"):
            verify_branching_boxm(scene(True, upper_room.box_routes),
                                  scene(False, lower_room.box_routes),
                                  scene(False, blocked.box_routes), 100)

    def test_five_box_t_branch_two_goals_persist_and_export(self):
        from adventure_studio.scumm_boxm_routing_probe import verify_two_goal_t_branch

        raw = canonical_json(GameDocument(
            "two_goal_t_branch", (scrolling_fixture(), destination_fixture())))
        for index, corners in (
                (1, "0,70; 110,70; 110,150; 0,150"),
                (2, "110,70; 240,70; 240,150; 110,150"),
                (3, "240,70; 360,70; 360,150; 240,150"),
                (4, "360,70; 639,70; 639,110; 360,110"),
                (5, "360,110; 639,110; 639,150; 360,150")):
            raw = author_room_walkbox(raw, "Harbor", index, corners)
        connected = author_room_box_connections(raw, "Harbor", "1-2; 2-3; 3-4; 3-5")
        blocked = author_room_box_connections(raw, "Harbor", "1-2; 2-3; 3-4")
        room = parse_document(connected).rooms[0]
        blocked_room = parse_document(blocked).rooms[0]
        self.assertEqual(len(room.walkboxes), 5)
        self.assertEqual(room.box_routes[1][4], 2)
        self.assertEqual(room.box_routes[1][5], 2)
        self.assertEqual(room.box_routes[3][4], 4)
        self.assertEqual(room.box_routes[3][5], 5)
        self.assertIsNone(blocked_room.box_routes[1][5])
        self.assertEqual(blocked_room.box_routes[1][4], 2)
        self.assertEqual(parse_document(canonical_json(parse_document(connected))).rooms[0],
                         room)
        story = (Path(__file__).resolve().parents[1] / "examples" /
                 "mini_story_chain.json").read_text(encoding="utf-8")
        saved = next(r for r in parse_document(compose_story_project(story, connected)).rooms
                     if r.name == "Harbor")
        self.assertEqual(saved.box_routes, room.box_routes)
        with tempfile.TemporaryDirectory() as directory:
            write_room_sources(room, Path(directory))
            first = (Path(directory) / "Harbor.box").read_bytes()
            write_room_sources(blocked_room, Path(directory))
            second = (Path(directory) / "Harbor.box").read_bytes()
            self.assertIn(b"BOXM", first)
            self.assertNotEqual(first, second)
        proof = verify_two_goal_t_branch(
            [list(r) for r in room.box_routes],
            [list(r) for r in blocked_room.box_routes], 140, 130, 120, 0)
        self.assertTrue(proof["native_two_goal_t_branch_passed"])
        with self.assertRaisesRegex(RuntimeError, "navigation absent"):
            verify_two_goal_t_branch(
                [list(r) for r in room.box_routes],
                [list(r) for r in blocked_room.box_routes], 140, 130, 120, 110)

    def test_six_box_cycle_alternate_studio_routes_native_export(self):
        from adventure_studio.scumm_boxm_routing_probe import verify_cyclic_six_box_detour

        raw = canonical_json(GameDocument(
            "six_box_cycle", (scrolling_fixture(), destination_fixture())))
        for index, corners in (
                (1, "0,70; 110,70; 110,150; 0,150"),
                (2, "110,70; 240,70; 240,110; 110,110"),
                (3, "110,110; 240,110; 240,150; 110,150"),
                (4, "240,70; 360,70; 360,110; 240,110"),
                (5, "240,110; 360,110; 360,150; 240,150"),
                (6, "360,70; 639,70; 639,150; 360,150")):
            raw = author_room_walkbox(raw, "Harbor", index, corners)
        alternatives = (
            ("cycle-intact", "1-2; 2-4; 4-6; 1-3; 3-5; 5-6", 2, True),
            ("cycle-upper-blocked", "1-2; 4-6; 1-3; 3-5; 5-6", 3, True),
            ("cycle-lower-blocked", "1-2; 2-4; 4-6; 1-3; 5-6", 2, True),
            ("cycle-both-blocked", "1-2; 4-6; 1-3; 5-6", None, False),
        )
        variants = {}
        binary_variants = set()
        for name, connections, first_hop, reached in alternatives:
            authored = author_room_box_connections(raw, "Harbor", connections)
            room = parse_document(authored).rooms[0]
            self.assertEqual(len(room.walkboxes), 6)
            self.assertEqual(room.box_routes[1][6], first_hop)
            self.assertEqual(room.box_routes[6][1], (4 if first_hop == 2 else
                                                      5 if first_hop == 3 else None))
            self.assertEqual(parse_document(canonical_json(parse_document(authored))).rooms[0],
                             room)
            with tempfile.TemporaryDirectory() as directory:
                write_room_sources(room, Path(directory))
                data = (Path(directory) / "Harbor.box").read_bytes()
                self.assertIn(b"BOXM", data)
                binary_variants.add(data)
            variants[name] = {"route_matrix": [list(row) for row in room.box_routes],
                              "frame_report": {"scroll_color_signature_passed": reached}}
            if name == "cycle-upper-blocked":
                story = (Path(__file__).resolve().parents[1] / "examples" /
                         "mini_story_chain.json").read_text(encoding="utf-8")
                composed = parse_document(compose_story_project(story, authored))
                self.assertEqual(next(r for r in composed.rooms if r.name == "Harbor").box_routes,
                                 room.box_routes)
        self.assertEqual(len(binary_variants), len(alternatives))
        verified = verify_cyclic_six_box_detour(variants, 180)
        self.assertTrue(verified["native_six_box_cycle_detour_passed"])
        with self.assertRaisesRegex(RuntimeError, "Actor reached"):
            invalid = dict(variants)
            invalid["cycle-both-blocked"] = {
                **variants["cycle-both-blocked"],
                "frame_report": {"scroll_color_signature_passed": True}}
            verify_cyclic_six_box_detour(invalid, 180)
        with self.assertRaisesRegex(ValueError, "gemeinsame Kante"):
            author_room_box_connections(raw, "Harbor", "1-6")

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
    def test_third_png_zplane_json_boxd_story_and_native_source(self):
        from PIL import Image
        from adventure_studio.scumm_multi_zplane_probe import verify_three_layer_occlusion

        room = native_room(occlusion=False)
        raw = canonical_json(GameDocument("three_zplanes", (room, destination_fixture())))
        width, height = room.geometry.room_width, room.geometry.room_height
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            for index in (1, 2, 3):
                png = directory / f"zplane-{index}.png"
                Image.new("L", (width, height), color=255 if index == 3 else 0).save(png)
                raw = import_room_zplane(raw, "Harbor", index, str(png))
            raw = author_room_walkbox_zplane(raw, "Harbor", 2, 3)
            authored = parse_document(raw).rooms[0]
            self.assertEqual(len(authored.zplanes), 3)
            self.assertEqual(tuple(p.index for p in authored.zplanes), (1, 2, 3))
            self.assertEqual(authored.walkboxes[1].mask, 3)
            self.assertEqual(authored.box_routes, room.box_routes)
            write_room_sources(authored, directory)
            self.assertIn('"HarborZ01.bmp", "HarborZ02.bmp", "HarborZ03.bmp"',
                          (directory / "Harbor.scc").read_text())
            self.assertTrue((directory / "HarborZ03.bmp").exists())
            self.assertEqual((directory / "Harbor.box").read_bytes()[30 + 16], 3)
            story = (Path(__file__).resolve().parents[1] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            composed = parse_document(compose_story_project(story, raw))
            saved = next(item for item in composed.rooms if item.name == "Harbor")
            self.assertEqual(saved.zplanes, authored.zplanes)
            self.assertEqual(saved.walkboxes, authored.walkboxes)
        self.assertTrue(verify_three_layer_occlusion(1200, 0, 0, 0)
                        ["three_layers_visually_verified"])
        with self.assertRaisesRegex(RuntimeError, "Third Z-plane occlusion absent"):
            verify_three_layer_occlusion(1200, 0, 0, 1100)

    @unittest.skipUnless(find_spec("PIL"), "PNG authoring requires optional studio Pillow")
    def test_fourth_png_zplane_json_boxd_story_and_native_source(self):
        from PIL import Image
        from adventure_studio.scumm_multi_zplane_probe import verify_four_layer_occlusion

        room = native_room(occlusion=False)
        raw = canonical_json(GameDocument("four_zplanes", (room, destination_fixture())))
        width, height = room.geometry.room_width, room.geometry.room_height
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            for index in (1, 2, 3, 4):
                png = directory / f"zplane-{index}.png"
                Image.new("L", (width, height), color=255 if index == 4 else 0).save(png)
                raw = import_room_zplane(raw, "Harbor", index, str(png))
            raw = author_room_walkbox_zplane(raw, "Harbor", 2, 4)
            authored = parse_document(raw).rooms[0]
            self.assertEqual(tuple(p.index for p in authored.zplanes), (1, 2, 3, 4))
            self.assertEqual(authored.walkboxes[1].mask, 4)
            self.assertEqual(authored.box_routes, room.box_routes)
            write_room_sources(authored, directory)
            self.assertIn('"HarborZ01.bmp", "HarborZ02.bmp", "HarborZ03.bmp", "HarborZ04.bmp"',
                          (directory / "Harbor.scc").read_text())
            self.assertTrue((directory / "HarborZ04.bmp").exists())
            self.assertEqual((directory / "Harbor.box").read_bytes()[30 + 16], 4)
            story = (Path(__file__).resolve().parents[1] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            saved = next(item for item in
                         parse_document(compose_story_project(story, raw)).rooms
                         if item.name == "Harbor")
            self.assertEqual(saved.zplanes, authored.zplanes)
            self.assertEqual(saved.walkboxes, authored.walkboxes)
        self.assertTrue(verify_four_layer_occlusion(1200, 0, 0, 0, 0)
                        ["four_layers_visually_verified"])
        with self.assertRaisesRegex(RuntimeError, "Fourth Z-plane occlusion absent"):
            verify_four_layer_occlusion(1200, 0, 0, 0, 1100)

    def test_stock_v6_export_rejects_fifth_zplane_without_losing_studio_data(self):
        room = native_room(occlusion=False)
        width, height = room.geometry.room_width, room.geometry.room_height
        planes = tuple(ZPlane(index, bytes([index % 2]) * (width * height))
                       for index in range(1, 6))
        five = replace(room, zplanes=planes,
                       walkboxes=(room.walkboxes[0],
                                  replace(room.walkboxes[1], mask=5)))
        saved = canonical_json(GameDocument("authored_five_zplanes",
                                            (five, destination_fixture())))
        restored = parse_document(saved).rooms[0]
        self.assertEqual(restored.zplanes, planes)
        self.assertEqual(restored.walkboxes[1].mask, 5)
        self.assertEqual(parse_document(canonical_json(parse_document(saved))).rooms[0],
                         restored)
        with self.assertRaisesRegex(ValueError, "Stock ScummVM SCUMM v6.*ZP05"):
            scummc_room_source(restored)
        with self.assertRaisesRegex(ValueError, "ZP05"):
            _native_box_file(restored)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            with self.assertRaisesRegex(ValueError, "ZP05"):
                write_room_sources(restored, directory)
            self.assertEqual(list(directory.iterdir()), [])
            with self.assertRaisesRegex(ValueError, "ZP05"):
                write_game_sources((destination_fixture(), restored), directory)
            self.assertEqual(list(directory.iterdir()), [])

        four = replace(restored, zplanes=planes[:4],
                       walkboxes=(room.walkboxes[0],
                                  replace(room.walkboxes[1], mask=4)))
        self.assertIn('"HarborZ04.bmp"', scummc_room_source(four))
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            write_room_sources(four, directory)
            self.assertTrue((directory / "HarborZ04.bmp").is_file())
            self.assertEqual((directory / "Harbor.box").read_bytes()[30 + 16], 4)
        unsupported_box = replace(four,
                                  walkboxes=(four.walkboxes[0],
                                             replace(four.walkboxes[1], mask=5)))
        with self.assertRaisesRegex(ValueError, "walkbox 2.*ZP05"):
            scummc_room_source(unsupported_box)
        with self.assertRaisesRegex(ValueError, "walkbox 2.*ZP05"):
            _native_box_file(unsupported_box)

    @unittest.skipUnless(find_spec("PIL"), "PNG authoring requires optional studio Pillow")
    def test_simultaneous_two_zplanes_on_connected_walkboxes_json_story_and_boxd(self):
        from PIL import Image
        from adventure_studio.scumm_simultaneous_zplane_probe import verify_simultaneous_masks

        room = scrolling_fixture()
        raw = canonical_json(GameDocument("two_masks_one_room",
                                          (room, destination_fixture())))
        for index, corners in (
                (1, "0,70; 240,70; 240,150; 0,150"),
                (2, "240,70; 400,70; 400,150; 240,150"),
                (3, "400,70; 639,70; 639,150; 400,150")):
            raw = author_room_walkbox(raw, "Harbor", index, corners)
        raw = author_room_box_connections(raw, "Harbor", "1-2; 2-3")
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            for index in (1, 2):
                png = root / f"independent-{index}.png"
                Image.new("L", (room.geometry.room_width, room.geometry.room_height),
                          color=255 if index == 1 else 0).save(png)
                raw = import_room_zplane(raw, "Harbor", index, str(png))
            raw = author_room_walkbox_zplane(raw, "Harbor", 2, 1)
            raw = author_room_walkbox_zplane(raw, "Harbor", 3, 2)
            authored = parse_document(raw).rooms[0]
            self.assertEqual(len(authored.zplanes), 2)
            self.assertEqual([box.mask for box in authored.walkboxes], [0, 1, 2])
            self.assertEqual(authored.box_routes[1][3], 2)
            self.assertEqual(authored.box_routes[3][1], 2)
            self.assertEqual(parse_document(canonical_json(parse_document(raw))).rooms[0],
                             authored)
            story = (Path(__file__).resolve().parents[1] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            saved = next(r for r in parse_document(compose_story_project(story, raw)).rooms
                         if r.name == "Harbor")
            self.assertEqual(saved.zplanes, authored.zplanes)
            self.assertEqual(saved.walkboxes, authored.walkboxes)
            write_room_sources(saved, root)
            source = (root / "Harbor.scc").read_text(encoding="utf-8")
            self.assertIn('"HarborZ01.bmp", "HarborZ02.bmp"', source)
            self.assertEqual((root / "Harbor.box").read_bytes()[30 + 16], 1)
            self.assertEqual((root / "Harbor.box").read_bytes()[30 + 21 + 16], 2)
            self.assertTrue((root / "HarborZ01.bmp").is_file())
            self.assertTrue((root / "HarborZ02.bmp").is_file())

        def frame(mid, far, ret):
            return {"walkbox_masks": [0, 1, 2],
                    "frame_report": {"scroll_color_signature_passed": True},
                    "middle_pixels": mid, "far_pixels": far, "return_pixels": ret}
        variants = {"both": frame(0, 0, 0),
                    "first-only": frame(0, 1200, 1200),
                    "second-only": frame(1200, 0, 0),
                    "clear": frame(1200, 1200, 1200)}
        self.assertTrue(verify_simultaneous_masks(variants)
                        ["native_simultaneous_room_masks_passed"])
        failed = dict(variants)
        failed["both"] = frame(1200, 0, 0)
        with self.assertRaisesRegex(RuntimeError, "not selective"):
            verify_simultaneous_masks(failed)

    @unittest.skipUnless(find_spec("PIL"), "PNG authoring requires optional studio Pillow")
    def test_three_simultaneous_png_walkboxes_roundtrip_boxd_and_native_comparison(self):
        from PIL import Image
        from adventure_studio.scumm_three_simultaneous_zplane_probe import verify_simultaneous_three_masks

        room = scrolling_fixture()
        raw = canonical_json(GameDocument("three_masks_same_game",
                                          (room, destination_fixture())))
        for index, corners in (
                (1, "0,70; 160,70; 160,150; 0,150"),
                (2, "160,70; 320,70; 320,150; 160,150"),
                (3, "320,70; 400,70; 400,150; 320,150"),
                (4, "400,70; 639,70; 639,150; 400,150")):
            raw = author_room_walkbox(raw, "Harbor", index, corners)
        raw = author_room_box_connections(raw, "Harbor", "1-2; 2-3; 3-4")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in (1, 2, 3):
                png = root / f"zplane-{index}.png"
                Image.new("L", (room.geometry.room_width, room.geometry.room_height),
                          color=255 if index == 2 else 0).save(png)
                raw = import_room_zplane(raw, "Harbor", index, str(png))
                raw = author_room_walkbox_zplane(raw, "Harbor", index + 1, index)
            authored = parse_document(raw).rooms[0]
            self.assertEqual([box.mask for box in authored.walkboxes], [0, 1, 2, 3])
            self.assertEqual(authored.box_routes[1][4], 2)
            self.assertEqual(authored.box_routes[4][1], 3)
            self.assertEqual(parse_document(canonical_json(parse_document(raw))).rooms[0],
                             authored)
            story = (Path(__file__).resolve().parents[1] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            composed = parse_document(compose_story_project(story, raw))
            saved = next(r for r in composed.rooms if r.name == "Harbor")
            self.assertEqual(saved.zplanes, authored.zplanes)
            self.assertEqual(saved.walkboxes, authored.walkboxes)
            write_room_sources(saved, root)
            self.assertIn('"HarborZ01.bmp", "HarborZ02.bmp", "HarborZ03.bmp"',
                          (root / "Harbor.scc").read_text(encoding="utf-8"))
            native = (root / "Harbor.box").read_bytes()
            self.assertEqual([native[30 + 21 * index + 16] for index in range(4)],
                             [0, 1, 2, 3])
            self.assertTrue(all((root / f"HarborZ{index:02d}.bmp").is_file()
                                for index in (1, 2, 3)))

        def frame(second, third, fourth, third_return=0, fourth_return=0):
            return {"walkbox_masks": [0, 1, 2, 3],
                    "frame_report": {"scroll_color_signature_passed": True},
                    "second_pixels": second, "third_pixels": third,
                    "fourth_pixels": fourth,
                    "third_return_pixels": third_return,
                    "fourth_return_pixels": fourth_return}
        variants = {
            "all": frame(0, 0, 0, 0, 0),
            "first-only": frame(1200 // 12, 1200, 1200, 1200, 1200),
            "second-only": frame(1200, 0, 1200, 0, 1200),
            "third-only": frame(1200, 1200, 0, 1200, 0),
            "clear": frame(1200, 1200, 1200, 1200, 1200),
        }
        self.assertTrue(verify_simultaneous_three_masks(variants)
                        ["native_simultaneous_three_room_masks_passed"])
        missing = dict(variants)
        missing["all"] = frame(1200, 0, 0, 0, 0)
        with self.assertRaisesRegex(RuntimeError, "Three simultaneous masks failed"):
            verify_simultaneous_three_masks(missing)

    @unittest.skipUnless(find_spec("PIL"), "PNG authoring requires optional studio Pillow")
    def test_four_simultaneous_png_walkboxes_roundtrip_boxd_and_native_comparison(self):
        from PIL import Image
        from adventure_studio.scumm_four_simultaneous_zplane_probe import verify_simultaneous_four_masks

        room = scrolling_fixture()
        raw = canonical_json(GameDocument("four_masks_same_game",
                                          (room, destination_fixture())))
        for index, corners in (
                (1, "0,70; 160,70; 160,150; 0,150"),
                (2, "160,70; 320,70; 320,150; 160,150"),
                (3, "320,70; 400,70; 400,150; 320,150"),
                (4, "400,70; 520,70; 520,150; 400,150"),
            (5, "520,70; 639,70; 639,150; 520,150")):
            raw = author_room_walkbox(raw, "Harbor", index, corners)
        raw = author_room_box_connections(raw, "Harbor", "1-2; 2-3; 3-4; 4-5")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in (1, 2, 3, 4):
                png = root / f"zplane-{index}.png"
                Image.new("L", (room.geometry.room_width, room.geometry.room_height),
                          color=255 if index == 4 else 0).save(png)
                raw = import_room_zplane(raw, "Harbor", index, str(png))
                raw = author_room_walkbox_zplane(raw, "Harbor", index + 1, index)
            authored = parse_document(raw).rooms[0]
            self.assertEqual([box.mask for box in authored.walkboxes], [0, 1, 2, 3, 4])
            self.assertEqual(authored.box_routes[1][5], 2)
            self.assertEqual(authored.box_routes[5][1], 4)
            self.assertEqual(parse_document(canonical_json(parse_document(raw))).rooms[0],
                             authored)
            story = (Path(__file__).resolve().parents[1] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            composed = parse_document(compose_story_project(story, raw))
            saved = next(r for r in composed.rooms if r.name == "Harbor")
            self.assertEqual(saved.zplanes, authored.zplanes)
            self.assertEqual(saved.walkboxes, authored.walkboxes)
            write_room_sources(saved, root)
            self.assertIn('"HarborZ01.bmp", "HarborZ02.bmp", "HarborZ03.bmp", "HarborZ04.bmp"',
                          (root / "Harbor.scc").read_text(encoding="utf-8"))
            native = (root / "Harbor.box").read_bytes()
            self.assertEqual([native[30 + 21 * index + 16] for index in range(5)],
                             [0, 1, 2, 3, 4])
            self.assertTrue(all((root / f"HarborZ{index:02d}.bmp").is_file()
                                for index in (1, 2, 3, 4)))

        def frame(second, third, fourth, fifth, fourth_return=0, fifth_return=0):
            return {"walkbox_masks": [0, 1, 2, 3, 4],
                    "frame_report": {"scroll_color_signature_passed": True},
                    "second_pixels": second, "third_pixels": third,
                    "fourth_pixels": fourth, "fifth_pixels": fifth,
                    "fourth_return_pixels": fourth_return,
                    "fifth_return_pixels": fifth_return}
        variants = {
            "all": frame(0, 0, 0, 0, 0, 0),
            "first-only": frame(0, 1200, 1200, 1200, 1200, 1200),
            "second-only": frame(1200, 0, 1200, 1200, 1200, 1200),
            "third-only": frame(1200, 1200, 0, 1200, 0, 1200),
            "fourth-only": frame(1200, 1200, 1200, 0, 1200, 0),
            "clear": frame(1200, 1200, 1200, 1200, 1200, 1200),
        }
        self.assertTrue(verify_simultaneous_four_masks(variants)
                        ["native_simultaneous_four_room_masks_passed"])
        missing = dict(variants)
        missing["all"] = frame(1200, 0, 0, 0, 0, 0)
        with self.assertRaisesRegex(RuntimeError, "Four simultaneous masks failed"):
            verify_simultaneous_four_masks(missing)

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

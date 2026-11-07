"""Native-source compatibility checks for v6 mask and walkbox assets."""

import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_assets import (Walkbox, ZPlane, _native_box_file,
                                          destination_fixture, scrolling_fixture,
                                          scummc_room_source, write_room_sources)
from adventure_studio.scumm_project import GameDocument, canonical_json, parse_document


def native_room():
    original = scrolling_fixture()
    w, h = original.geometry.room_width, original.geometry.room_height
    mask = bytes(1 if x > w // 2 and 50 < y < 110 else 0
                 for y in range(h) for x in range(w))
    boxes = (Walkbox(((0, 70), (120, 70), (120, 150), (0, 150))),
             Walkbox(((120, 70), (240, 70), (240, 150), (120, 150)), scale=180))
    # Index zero is reserved.  Travel between the two authored boxes uses
    # a first-hop route through the destination box.
    routes = ((0, None, None), (None, 1, 2), (None, 1, 2))
    return replace(original, zplanes=(ZPlane(1, mask),), walkboxes=boxes,
                   box_routes=routes, scale_slots=bytes(32))


class RoomNativePrimitiveTests(unittest.TestCase):
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

    def test_legacy_json_omits_new_optional_fields(self):
        room = scrolling_fixture()
        json_text = canonical_json(GameDocument("legacy", (room, destination_fixture())))
        self.assertNotIn('"zplanes"', json_text)
        self.assertNotIn('"walkboxes"', json_text)
        self.assertEqual(parse_document(json_text).rooms[0], room)

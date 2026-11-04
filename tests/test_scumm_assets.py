import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_assets import RoomHotspot, indexed_bmp, scrolling_fixture, scummc_room_source, write_room_sources


class ScummAssetsTests(unittest.TestCase):
    def test_indexed_bmp_header_and_scroll_width(self):
        bmp = indexed_bmp(scrolling_fixture())
        self.assertEqual(bmp[:2], b"BM")
        self.assertEqual(struct.unpack_from("<ii", bmp, 18), (640, 200))
        self.assertEqual(struct.unpack_from("<H", bmp, 28)[0], 8)
        self.assertEqual(len(bmp), struct.unpack_from("<I", bmp, 2)[0])

    def test_scummc_room_source(self):
        source = scummc_room_source(scrolling_fixture())
        self.assertIn("room Harbor", source)
        self.assertIn("object Key", source)
        self.assertIn("case LookAt:", source)
        self.assertIn("case PickUp:", source)
        self.assertIn('states = { { 0, 0, "Key.bmp" } };', source)
        self.assertIn("class = { Pickable };", source)
        self.assertIn("pickupObject(objA,VAR_ROOM)", source)
        self.assertIn("cameraFollowActor(VAR_EGO)", source)
        self.assertIn("setActorStanding()", source)
        self.assertIn("walkActorTo(VAR_EGO, 540, 100)", source)

    def test_generated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            bmp, scc = write_room_sources(scrolling_fixture(), Path(tmp))
            self.assertGreater(bmp.stat().st_size, 128_000)
            self.assertIn("room Harbor", scc.read_text(encoding="utf-8"))
            sprite = Path(tmp) / "Key.bmp"
            self.assertTrue(sprite.is_file())
            self.assertEqual(struct.unpack_from("<ii", sprite.read_bytes(), 18), (16, 12))

    def test_rejects_invalid_dimensions_and_names(self):
        room = scrolling_fixture()
        with self.assertRaisesRegex(ValueError, "identifier"):
            indexed_bmp(replace(room, name='x"; evil()'))
        with self.assertRaisesRegex(ValueError, "Pixel buffer"):
            indexed_bmp(replace(room, pixels=b""))
        with self.assertRaisesRegex(ValueError, "palette"):
            indexed_bmp(replace(room, palette=((1, 2, 3),)))
        with self.assertRaisesRegex(ValueError, "Demo walk"):
            scummc_room_source(replace(room, demo_walk_to_x=700))
        self.assertNotIn("walkActorTo(VAR_EGO", scummc_room_source(replace(room, demo_walk_to_x=None)))

    def test_rejects_hotspot_injection_and_out_of_bounds(self):
        room = scrolling_fixture()
        with self.assertRaisesRegex(ValueError, "text character"):
            scummc_room_source(replace(room, hotspots=(RoomHotspot("Key", 'key"; evil()', "bad", 0, 0, 10, 10),)))
        with self.assertRaisesRegex(ValueError, "outside room"):
            scummc_room_source(replace(room, hotspots=(replace(room.hotspots[0], x=639),)))
        with self.assertRaisesRegex(ValueError, "sprite pixel buffer"):
            scummc_room_source(replace(room, hotspots=(replace(room.hotspots[0], sprite_pixels=b""),)))
        with self.assertRaisesRegex(ValueError, "sprite references"):
            scummc_room_source(replace(room, hotspots=(replace(room.hotspots[0], sprite_pixels=b"\xff" * 192),)))


if __name__ == "__main__":
    unittest.main()

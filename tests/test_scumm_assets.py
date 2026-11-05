import json
import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_assets import RoomHotspot, UseRule, destination_fixture, indexed_bmp, scrolling_fixture, scummc_room_source, write_game_sources, write_room_sources


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
        self.assertIn("state = 1;", source)
        self.assertIn("class = { Pickable };", source)
        self.assertIn("pickupObject(objA,VAR_ROOM)", source)
        self.assertIn("setObjectState(objA,0)", source)
        self.assertIn("ResRoom::KeyIcon", source)
        self.assertIn("object Door", source)
        self.assertIn("case Use:", source)
        self.assertIn("if(objB == Key)", source)
        self.assertIn('sntcPrepo[0] = "with"', source)
        self.assertIn('egoSay("The door is unlocked.")', source)
        self.assertIn("room Cellar;", source)
        self.assertIn("startRoom(Cellar)", source)
        self.assertIn("if(getObjectState(objA) == 2)", source)
        self.assertIn("setObjectState(objA,2)", source)
        self.assertIn('"DoorOpen.bmp"', source)
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
            self.assertEqual(struct.unpack_from("<ii", sprite.read_bytes(), 18), (16, 16))
            icon = Path(tmp) / "Inv_Key.bmp"
            self.assertEqual(struct.unpack_from("<ii", icon.read_bytes(), 18), (40, 16))
            door = Path(tmp) / "Door.bmp"
            self.assertEqual(struct.unpack_from("<ii", door.read_bytes(), 18), (16, 16))
            open_door = Path(tmp) / "DoorOpen.bmp"
            self.assertEqual(struct.unpack_from("<ii", open_door.read_bytes(), 18), (16, 16))

    def test_destination_room_is_a_distinct_generated_resource(self):
        room = destination_fixture()
        self.assertEqual(room.geometry.room_width, 320)
        self.assertEqual(room.pixels[0], 5)
        with tempfile.TemporaryDirectory() as tmp:
            bmp, source = write_room_sources(room, Path(tmp))
            self.assertEqual(struct.unpack_from("<ii", bmp.read_bytes(), 18), (320, 200))
            self.assertIn("room Cellar", source.read_text(encoding="utf-8"))
            self.assertIn("local script entry()", source.read_text(encoding="utf-8"))
            self.assertIn("putActorAt(VAR_EGO, 60, 100, Cellar)", source.read_text(encoding="utf-8"))
            self.assertIn('egoSay("You reached the cellar. Puzzle solved!")', source.read_text(encoding="utf-8"))
            self.assertIn("object Stairs", source.read_text(encoding="utf-8"))
            self.assertIn("startRoom(Harbor)", source.read_text(encoding="utf-8"))

    def test_game_export_validates_all_room_references_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            with self.assertRaisesRegex(ValueError, "Unknown exit destination"):
                write_game_sources((scrolling_fixture(),), target)
            self.assertEqual(list(target.iterdir()), [])
            with self.assertRaisesRegex(ValueError, "Duplicate room"):
                write_game_sources((scrolling_fixture(), scrolling_fixture()), target)
            self.assertEqual(len(write_game_sources((scrolling_fixture(), destination_fixture()), target)), 2)
            self.assertTrue((target / "Cellar.scc").exists())
            goal = json.loads((target / "game-goal.json").read_text(encoding="utf-8"))
            self.assertEqual(goal["condition"], "enter_room")
            self.assertEqual(goal["room_id"], "Cellar")
            self.assertEqual(goal["fixture_probe_rgb"], [120, 70, 180])
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "exactly one goal"):
                write_game_sources((scrolling_fixture(), replace(destination_fixture(), goal_text=None)), Path(tmp))

    def test_use_rules_reject_invalid_references_and_duplicates(self):
        room = scrolling_fixture()
        for rules in (
            (UseRule("Missing", "Door", "No."),),
            (UseRule("Key", "Missing", "No."),),
            (UseRule("Key", "Key", "No."),),
            (UseRule("Key", "Door", "OK."), UseRule("Key", "Door", "Again.")),
            (UseRule("Key", "Door", "No.", requires_inventory=("Unknown",)),),
            (UseRule("Key", "Door", "No.", requires_inventory=("Key",)),),
        ):
            with self.subTest(rules=rules), self.assertRaises(ValueError):
                scummc_room_source(replace(room, use_rules=rules))
        with self.assertRaisesRegex(ValueError, "text character"):
            scummc_room_source(replace(room, use_rules=(UseRule("Key", "Door", 'oops";'),)))
        with self.assertRaisesRegex(ValueError, "destination room"):
            scummc_room_source(replace(room, use_rules=(UseRule("Key", "Door", "OK", destination_room='bad;code'),)))
        with self.assertRaisesRegex(ValueError, "cannot hide and open"):
            scummc_room_source(replace(room, use_rules=(UseRule("Key", "Door", "OK", hide_target=True, open_target=True),)))

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
        with self.assertRaisesRegex(ValueError, "sprite dimensions"):
            scummc_room_source(replace(room, hotspots=(replace(room.hotspots[0], height=12),)))
        with self.assertRaisesRegex(ValueError, "sprite references"):
            scummc_room_source(replace(room, hotspots=(replace(room.hotspots[0], sprite_pixels=b"\xff" * 256),)))


if __name__ == "__main__":
    unittest.main()

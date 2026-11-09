import unittest
from pathlib import Path

from adventure_studio.palette_demo import WATER_PALETTE, add_water_cycle
from adventure_studio.scumm_assets import scummc_room_source
from adventure_studio.scumm_project import canonical_json, parse_document
from adventure_studio.story_document import parse_story_document
from adventure_studio.story_to_scumm import compile_story_to_scumm


class PaletteDemoTests(unittest.TestCase):
    @staticmethod
    def game():
        raw = Path(__file__).resolve().parents[1] / "examples" / "mini_story.json"
        return compile_story_to_scumm(parse_story_document(raw.read_text(encoding="utf-8")))

    def test_adds_indexed_water_without_changing_normal_fixture(self):
        original = self.game()
        demo = add_water_cycle(original)
        self.assertEqual(demo.rooms[0].palette[-4:], WATER_PALETTE)
        self.assertEqual(len(demo.rooms[0].palette_cycles), 1)
        self.assertNotEqual(original.rooms[0].pixels, demo.rooms[0].pixels)
        self.assertEqual(original.rooms[0].palette_cycles, ())
        self.assertEqual(demo.rooms[0].demo_walk_to_x, None)
        self.assertEqual(demo.rooms[1], original.rooms[1])
        self.assertEqual({hotspot.id: hotspot.x for hotspot in demo.rooms[0].hotspots
                          if hotspot.pickup or hotspot.exit_destination is not None},
                         {"Key": 220, "Door": 270})
        self.assertEqual({hotspot.id: hotspot.x for hotspot in original.rooms[0].hotspots
                          if hotspot.pickup or hotspot.exit_destination is not None},
                         {"Key": 355, "Door": 450})

    def test_scumm_source_declares_cycle_and_roundtrips_json(self):
        demo = add_water_cycle(self.game())
        self.assertEqual(parse_document(canonical_json(demo)), demo)
        source = scummc_room_source(demo.rooms[0])
        self.assertIn("cycle Water = {2,0,9,12};", source)
        self.assertEqual(source, scummc_room_source(demo.rooms[0]))

    def test_rejects_cycle_tampering(self):
        from dataclasses import replace
        from adventure_studio.palette_animation import PaletteCycle
        from adventure_studio.scumm_assets import indexed_bmp
        demo = add_water_cycle(self.game())
        broken = replace(demo.rooms[0], palette_cycles=(PaletteCycle("Water", 0, 2, 2),))
        with self.assertRaisesRegex(ValueError, "protected"):
            indexed_bmp(broken)
        broken = replace(demo.rooms[0], palette_cycles=(PaletteCycle("Water", 9, 12, 20000),))
        with self.assertRaisesRegex(ValueError, "SCUMM v6"):
            indexed_bmp(broken)
        # Palette-cycle ranges must not recolor room objects or inventory art.
        broken = replace(demo.rooms[0], palette_cycles=(PaletteCycle("Water", 3, 5, 2),))
        with self.assertRaisesRegex(ValueError, "protected"):
            indexed_bmp(broken)


if __name__ == "__main__":
    unittest.main()

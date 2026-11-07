import json
import unittest
from pathlib import Path

from adventure_studio.studio_service import change_position, item_position, report_text
from adventure_studio.story import Placement
from adventure_studio.story_document import canonical_story_json, parse_story_document
from adventure_studio.story_to_scumm import compile_story_to_scumm


SAMPLE = (Path(__file__).resolve().parents[1] / "examples/mini_story_chain.json").read_text(encoding="utf-8")


class StudioPositionTests(unittest.TestCase):
    def test_v1_story_stays_byte_identical_when_not_positioned(self):
        original = parse_story_document(SAMPLE)
        self.assertEqual(original.placements, ())
        self.assertEqual(json.loads(canonical_story_json(original))["format_version"], 1)
        self.assertEqual(compile_story_to_scumm(original), compile_story_to_scumm(parse_story_document(SAMPLE)))

    def test_position_change_creates_v3_roundtrip_and_moves_hotspot(self):
        old_x, old_y = item_position(SAMPLE, "Key")
        result = change_position(SAMPLE, "Key", 270, 130)
        data = json.loads(result.story_json)
        self.assertEqual(data["format_version"], 3)
        story = parse_story_document(result.story_json)
        self.assertEqual(story.placements, (Placement("Key", 270, 130),))
        self.assertEqual(item_position(result.story_json, "Key"), (270, 130))
        self.assertNotEqual((old_x, old_y), (270, 130))
        self.assertIn("hinzugefügt: placement Key", report_text(result.report))
        self.assertEqual(canonical_story_json(story), result.story_json)

    def test_invalid_positions_fail_without_changing_story(self):
        for x, y in ((-1, 50), (20, -1), (20, True), (True, 20)):
            with self.subTest(x=x, y=y), self.assertRaises(ValueError):
                change_position(SAMPLE, "Key", x, y)
        with self.assertRaises(ValueError):
            change_position(SAMPLE, "Missing", 50, 50)

    def test_goal_room_decoration_has_narrower_geometry(self):
        from adventure_studio.studio_service import add_decoration

        decorated = add_decoration(SAMPLE, "Archive", "Lamp", "Lamp", "Old lamp")
        authored = change_position(decorated.story_json, "Lamp", 410, 120)
        self.assertIn("geometry", authored.report.export_warning)
        self.assertEqual(item_position(authored.story_json, "Lamp"), (410, 120))
        with self.assertRaisesRegex(ValueError, "geometry"):
            compile_story_to_scumm(parse_story_document(authored.story_json))
        self.assertEqual(item_position(change_position(decorated.story_json, "Lamp", 100, 120).story_json, "Lamp"),
                         (100, 120))

    def test_fixture_boundaries_do_not_limit_story_coordinates(self):
        for x, y in ((630, 100), (20, 190), (1000, 300)):
            with self.subTest(x=x, y=y):
                edited = change_position(SAMPLE, "Key", x, y)
                self.assertEqual(item_position(edited.story_json, "Key"), (x, y))
                self.assertIn("geometry", edited.report.export_warning)
                with self.assertRaisesRegex(ValueError, "geometry"):
                    compile_story_to_scumm(parse_story_document(edited.story_json))

    def test_consolidation_removes_placement_with_unused_pickup(self):
        from dataclasses import replace
        from adventure_studio.story import Item
        from adventure_studio.story_changes import PutEntity, edit_story

        original = parse_story_document(SAMPLE)
        with_unused = replace(original, items=(*original.items,
                                              Item("Extra", "Extra", "Unused pickup", "Harbor")),
                              placements=(Placement("Extra", 80, 80),))
        updated, report = edit_story(with_unused, (PutEntity("scene", original.scenes[0]),))
        self.assertFalse(any(item.id == "Extra" for item in updated.items))
        self.assertEqual(updated.placements, ())
        self.assertIn("Extra", report.consolidated)
        self.assertTrue(any(change.kind == "placement" and change.id == "Extra"
                            and change.after is None for change in report.changes))


if __name__ == "__main__":
    unittest.main()

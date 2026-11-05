import unittest
from pathlib import Path

from adventure_studio.studio_service import (
    add_decoration, change_item, change_scene, describe_story, report_text, scene_preview,
)
from adventure_studio.story_document import parse_story_document


SAMPLE = (Path(__file__).resolve().parents[1] / "examples/mini_story_chain.json").read_text(encoding="utf-8")


class StudioServiceTests(unittest.TestCase):
    def test_scene_edit_is_validated_and_reports_exact_change(self):
        original = parse_story_document(SAMPLE)
        result = change_scene(SAMPLE, "Harbor", "Neuer Hafen", "Ein unruhiger Ort")
        updated = parse_story_document(result.story_json)
        self.assertEqual(updated.scenes[0].title, "Neuer Hafen")
        self.assertEqual(updated.scenes[0].description, "Ein unruhiger Ort")
        self.assertEqual(original.scenes[0].title, "Hafenhaus")
        self.assertIn("geändert: scene Harbor", report_text(result.report))
        self.assertEqual(change_scene(result.story_json, "Harbor", "Neuer Hafen", "Ein unruhiger Ort").report.changes, ())

    def test_item_change_and_new_fridge_decoration(self):
        renamed = change_item(SAMPLE, "Key", "Alter Schlüssel", "Liegt am Boden")
        result = add_decoration(renamed.story_json, "Harbor", "Fridge", "Kaputter Kühlschrank",
                                "Enthält eine verschimmelte Ananas")
        story = parse_story_document(result.story_json)
        fridge = next(item for item in story.items if item.id == "Fridge")
        self.assertEqual(fridge.role, "decoration")
        self.assertIn("hinzugefügt: item Fridge", report_text(result.report))
        width, height, pixels, palette, hotspots = scene_preview(result.story_json, "Harbor")
        self.assertEqual((width, height), (640, 200))
        self.assertEqual(len(pixels), width * height)
        self.assertTrue(any("Kuhlschrank" in label for label, *_ in hotspots))

    def test_rejects_invalid_edit_without_mutating_input(self):
        with self.assertRaises(ValueError):
            change_scene(SAMPLE, "Missing", "X", "Y")
        with self.assertRaises(ValueError):
            change_item(SAMPLE, "Key", "", "Y")
        with self.assertRaises(ValueError):
            add_decoration(SAMPLE, "Harbor", "../path", "X", "Y")
        with self.assertRaises(ValueError):
            add_decoration(SAMPLE, "Harbor", "Key", "X", "Y")
        self.assertTrue(describe_story(SAMPLE).playable_path)


if __name__ == "__main__":
    unittest.main()

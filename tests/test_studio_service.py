import json
import unittest
from pathlib import Path

from adventure_studio.studio_service import (
    accept_proposal, add_decoration, change_item, change_puzzle, change_scene,
    describe_story, prepare_proposal, report_text, scene_preview, translation_draft, validate_translation_draft,
)
from adventure_studio.story_document import parse_story_document


SAMPLE = (Path(__file__).resolve().parents[1] / "examples/mini_story_chain.json").read_text(encoding="utf-8")


class StudioServiceTests(unittest.TestCase):
    def test_export_five_language_translation_draft_from_story(self):
        draft = json.loads(translation_draft(SAMPLE))
        self.assertEqual(draft["languages"], ["de", "en", "fr", "ja", "pl"])
        self.assertGreater(len(draft["lines"]), 0)
        self.assertTrue(any(line["id"].endswith(".label") for line in draft["lines"]))
        for line in draft["lines"]:
            self.assertIsInstance(line["translations"]["en"], str)
            self.assertIsNone(line["translations"]["de"])
        self.assertEqual(translation_draft(SAMPLE), translation_draft(SAMPLE))
        german = json.loads(translation_draft(SAMPLE, "de"))
        self.assertEqual(german["source_language"], "de")
        self.assertIsNone(german["lines"][0]["translations"]["en"])
        self.assertIsInstance(german["lines"][0]["translations"]["de"], str)

    def test_draft_preserves_authored_umlauts_and_accepts_validated_source(self):
        changed = change_item(SAMPLE, "Key", "Alter Schlüssel", "Ein rostiger Schlüssel")
        draft = json.loads(translation_draft(changed.story_json, "de"))
        key = next(line for line in draft["lines"]
                   if line["id"] == "room.harbor.object.key.label")
        self.assertEqual(key["translations"]["de"], "Alter Schlüssel")
        for line in draft["lines"]:
            source = line["translations"]["de"]
            for language in draft["languages"]:
                line["translations"][language] = source
        checked = validate_translation_draft(changed.story_json, json.dumps(draft, ensure_ascii=False))
        self.assertIn("Alter Schlüssel", checked)

    def test_completed_translations_require_story_and_charset_coverage(self):
        draft = json.loads(translation_draft(SAMPLE))
        for line in draft["lines"]:
            for language in draft["languages"]:
                line["translations"][language] = line["translations"]["en"]
        complete = json.dumps(draft, ensure_ascii=False)
        validated = validate_translation_draft(SAMPLE, complete)
        self.assertEqual(json.loads(validated), draft)
        changed = json.loads(complete)
        changed["lines"][0]["translations"]["en"] = "Wrong source"
        with self.assertRaisesRegex(ValueError, "Source translation differs"):
            validate_translation_draft(SAMPLE, json.dumps(changed))
        changed = json.loads(complete)
        changed["lines"].pop()
        with self.assertRaisesRegex(ValueError, "translation IDs mismatch"):
            validate_translation_draft(SAMPLE, json.dumps(changed))

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

    def test_puzzle_requirements_are_checked_against_story_solver(self):
        original = parse_story_document(SAMPLE)
        original_puzzle = original.puzzles[0]
        result = change_puzzle(SAMPLE, original_puzzle.id, "Tür mit Schlüssel", ("Key",))
        self.assertEqual(parse_story_document(result.story_json).puzzles[0].requires, ("Key",))
        self.assertEqual(describe_story(SAMPLE).puzzles[0][0], original_puzzle.id)
        with self.assertRaises(ValueError):
            change_puzzle(SAMPLE, original_puzzle.id, "Falsche Forderung", ("Missing",))

    def test_preview_must_be_confirmed_against_unchanged_base(self):
        edit = change_scene(SAMPLE, "Harbor", "Neuer Hafen", "Ein stilles Haus")
        proposal = prepare_proposal(SAMPLE, edit)
        self.assertEqual(accept_proposal(SAMPLE, proposal), edit.story_json)
        concurrent = change_item(SAMPLE, "Key", "Schlüssel", "Ein anderer Schlüssel")
        with self.assertRaisesRegex(ValueError, "changed since preview"):
            accept_proposal(concurrent.story_json, proposal)


if __name__ == "__main__":
    unittest.main()

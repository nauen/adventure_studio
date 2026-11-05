import json
import unittest

from adventure_studio.localization import LanguageCatalog, LocalizedLine
from adventure_studio.scumm_assets import destination_fixture, scrolling_fixture
from adventure_studio.scumm_project import GameDocument
from adventure_studio.story_localization import (
    story_text_inventory, story_translation_template, story_translation_template_json,
    validate_story_catalog,
)


class StoryLocalizationTests(unittest.TestCase):
    @staticmethod
    def document():
        return GameDocument("HarborGame", (scrolling_fixture(), destination_fixture()))

    def test_inventory_covers_room_objects_responses_and_goal(self):
        inventory = story_text_inventory(self.document())
        self.assertEqual(inventory["room.harbor.object.key.label"], "the key")
        self.assertEqual(inventory["room.harbor.object.door.description"], "A locked door.")
        self.assertEqual(inventory["room.harbor.use.0.response"], "The door is unlocked.")
        self.assertEqual(inventory["room.cellar.goal"], "You reached the cellar. Puzzle solved!")
        self.assertEqual(list(inventory), sorted(inventory))
        self.assertEqual(inventory, story_text_inventory(self.document()))

    def test_five_language_draft_is_deterministic_and_explicitly_incomplete(self):
        document = self.document()
        draft = story_translation_template(document)
        self.assertEqual(draft["languages"], ["de", "en", "fr", "ja", "pl"])
        self.assertEqual(draft["source_language"], "en")
        self.assertEqual(len(draft["lines"]), len(story_text_inventory(document)))
        for line in draft["lines"]:
            self.assertEqual(line["translations"]["en"], story_text_inventory(document)[line["id"]])
            self.assertIsNone(line["translations"]["de"])
            self.assertIsNone(line["translations"]["ja"])
        serialized = story_translation_template_json(document)
        self.assertEqual(json.loads(serialized), draft)
        self.assertEqual(serialized, story_translation_template_json(document))
        with self.assertRaisesRegex(ValueError, "Invalid translation values"):
            from adventure_studio.localization import parse_catalog
            parse_catalog(serialized)
        with self.assertRaisesRegex(ValueError, "Invalid translation template languages"):
            story_translation_template(document, languages=("en", "de"))

    def test_catalog_requires_exact_ids_and_matching_source(self):
        inventory = story_text_inventory(self.document())
        lines = tuple(LocalizedLine(key, (("de", text), ("en", text)))
                      for key, text in inventory.items())
        catalog = LanguageCatalog("en", ("de", "en"), lines)
        validate_story_catalog(self.document(), catalog)
        with self.assertRaisesRegex(ValueError, "translation IDs mismatch"):
            validate_story_catalog(self.document(),
                                   LanguageCatalog("en", ("de", "en"), lines[1:]))
        changed = list(lines)
        first = changed[0]
        changed[0] = LocalizedLine(first.id, (("de", "Andere Übersetzung"), ("en", "Wrong source")))
        with self.assertRaisesRegex(ValueError, "Source translation differs"):
            validate_story_catalog(self.document(),
                                   LanguageCatalog("en", ("de", "en"), tuple(changed)))


if __name__ == "__main__":
    unittest.main()

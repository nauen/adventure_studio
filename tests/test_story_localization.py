import json
import unittest
from pathlib import Path

from adventure_studio.localization import LanguageCatalog, LocalizedLine
from adventure_studio.scumm_assets import destination_fixture, scrolling_fixture, scummc_room_source
from adventure_studio.scumm_project import GameDocument
from adventure_studio.dialogue_demo import dialogue_fixture
from adventure_studio.story_document import parse_story_document
from adventure_studio.story_to_scumm import compile_story_to_scumm
from adventure_studio.story_language_fixture import fixture_catalog
from adventure_studio.localization import charset_plan, canonical_catalog_json
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
        self.assertEqual(inventory["room.harbor.object.door.locked"], "The door is locked.")
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

    def test_opt_in_scumm_speech_uses_runtime_language_dispatch(self):
        document = self.document()
        inventory = story_text_inventory(document)
        lines = []
        for key, value in inventory.items():
            german = "Grüße, Abenteurer!" if key == "room.harbor.use.0.response" else value
            lines.append(LocalizedLine(key, (("de", german), ("en", value))))
        catalog = LanguageCatalog("en", ("de", "en"), tuple(lines))
        validate_story_catalog(document, catalog)
        regular = scummc_room_source(scrolling_fixture())
        localized = scummc_room_source(scrolling_fixture(), catalog)
        self.assertIn('egoSay("The door is unlocked.")', regular)
        self.assertIn("GameLanguage ==", localized)
        self.assertIn("/* de */", localized)
        self.assertIn("/* en */", localized)
        self.assertIn("setObjectName(Key", localized)
        self.assertNotIn("setObjectName(Key", regular)
        self.assertIn("local script watchLanguage()", localized)
        self.assertIn("if(observedLanguage != GameLanguage)", localized)
        self.assertIn("breakScript();", localized)
        self.assertIn("watchLanguage();", localized)
        self.assertNotIn("watchLanguage", regular)
        self.assertIn(r"\x", localized)
        incomplete = LanguageCatalog("en", ("de", "en"), tuple(line for line in lines if line.id != "room.harbor.use.0.response"))
        with self.assertRaisesRegex(ValueError, "Missing or stale SCUMM translation"):
            scummc_room_source(scrolling_fixture(), incomplete)

    def test_opt_in_dialogue_dispatch_from_story_model(self):
        example = (Path(__file__).resolve().parents[1] / "examples/mini_story.json").read_text(encoding="utf-8")
        game = compile_story_to_scumm(parse_story_document(dialogue_fixture(example, choices=True)))
        inventory = story_text_inventory(game)
        catalog = LanguageCatalog("en", ("de", "en"), tuple(
            LocalizedLine(key, (("de", value), ("en", value)))
            for key, value in inventory.items()
        ))
        harbor = next(room for room in game.rooms if room.name == "Harbor")
        rendered = scummc_room_source(harbor, catalog)
        self.assertIn("case TalkTo:", rendered)
        self.assertIn("GameLanguage ==", rendered)
        self.assertIn("dialogue", " ".join(inventory.keys()))
        self.assertGreater(rendered.count("/* de */"), 3)

    def test_five_language_scumm_fixture_has_real_probes_and_complete_coverage(self):
        document = self.document()
        catalog = fixture_catalog(document)
        validate_story_catalog(document, catalog)
        self.assertEqual(catalog.languages, ("de", "en", "fr", "ja", "pl"))
        lines = {line.id: dict(line.translations) for line in catalog.lines}
        self.assertEqual(lines["room.harbor.use.0.response"]["de"], "Die Tür ist offen.")
        self.assertEqual(lines["room.harbor.object.key.label"]["de"], "der Schlüssel")
        self.assertEqual(lines["room.harbor.object.door.label"]["ja"], "扉")
        self.assertEqual(lines["room.harbor.object.door.description"]["pl"], "Zamknięte drzwi.")
        self.assertIn("地下室", lines["room.cellar.goal"]["ja"])
        self.assertNotEqual(lines["room.cellar.goal"]["pl"], lines["room.cellar.goal"]["en"])
        self.assertTrue(all(line[language] != line["en"]
                            for line in lines.values() for language in ("de", "fr", "ja", "pl")))
        harbor = scummc_room_source(scrolling_fixture(), catalog)
        cellar = scummc_room_source(destination_fixture(), catalog)
        self.assertIn("setObjectName(Key", harbor)
        self.assertIn("setObjectName(Door", harbor)
        self.assertIn("/* ja */", cellar)
        self.assertIn("/* pl */", harbor)
        self.assertLessEqual(len(charset_plan(catalog).extra_glyphs), 126)
        self.assertEqual(canonical_catalog_json(catalog), canonical_catalog_json(fixture_catalog(document)))

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


import tempfile
import unittest
from pathlib import Path

from adventure_studio.localization import LanguageCatalog, LocalizedLine
from adventure_studio.scumm_assets import destination_fixture, scrolling_fixture, scummc_room_source
from adventure_studio.scumm_language_buttons import (
    button_names, button_room_source, button_sprite, button_state_source,
    write_button_sprites,
)
from adventure_studio.story_language_fixture import fixture_catalog
from adventure_studio.scumm_project import GameDocument


class GraphicalLanguageButtonsTests(unittest.TestCase):
    @staticmethod
    def catalog():
        return fixture_catalog(GameDocument("HarborGame",
                                            (scrolling_fixture(), destination_fixture())))

    def test_five_clickable_buttons_have_stable_language_codes(self):
        catalog = self.catalog()
        self.assertEqual([name for name, _lang, _code in button_names(catalog)],
                         ["LangDe", "LangEn", "LangFr", "LangJa", "LangPl"])
        source = button_room_source("Harbor", catalog)
        self.assertIn('"HarborLangDe.bmp"', source)
        self.assertIn('"HarborLangDeActive.bmp"', source)
        self.assertEqual(source.count("case WalkTo:"), 5)
        self.assertIn("w = 32;", source)
        self.assertIn("GameLanguage = 27233;", source)
        self.assertIn("setObjectState(LangPl,2);", button_state_source(catalog))

    def test_sprite_resources_are_deterministic_per_room(self):
        catalog = self.catalog()
        room = scrolling_fixture()
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            files = write_button_sprites(room, catalog, directory)
            self.assertEqual(len(files), 10)
            self.assertTrue(all(path.read_bytes()[:2] == b"BM" for path in files))
            first = tuple(path.read_bytes() for path in files)
            self.assertEqual(first, tuple(path.read_bytes()
                                          for path in write_button_sprites(room, catalog, directory)))
            self.assertNotEqual(button_sprite("de", 1, 3, True),
                                button_sprite("de", 1, 3, False))
            self.assertEqual(len(button_sprite("de", 1, 3, False)), 32 * 16)
            write_button_sprites(destination_fixture(), catalog, directory)
            self.assertTrue((directory / "CellarLangJaActive.bmp").is_file())

    def test_opt_in_emits_live_room_objects_but_default_is_unchanged(self):
        room = scrolling_fixture()
        catalog = self.catalog()
        regular = scummc_room_source(room, catalog)
        with_buttons = scummc_room_source(room, catalog, graphical_language_buttons=True)
        self.assertNotIn("object LangDe {", regular)
        self.assertIn("object LangDe {", with_buttons)
        self.assertLess(with_buttons.index("object LangDe {"),
                        with_buttons.index("local script watchLanguage()"))
        self.assertIn("setObjectState(LangDe,2);", with_buttons)
        with self.assertRaisesRegex(ValueError, "require a language catalog"):
            scummc_room_source(room, graphical_language_buttons=True)


if __name__ == "__main__":
    unittest.main()

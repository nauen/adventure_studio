import json
import unittest

from adventure_studio.localization import (
    LanguageCatalog, LocalizedLine, canonical_catalog_json, charset_plan,
    encode_scumm_literal, parse_catalog, scumm_language_dispatch,
)


LANGUAGES = ("de", "en", "fr", "ja", "pl")


def sample():
    return LanguageCatalog("de", LANGUAGES, (
        LocalizedLine("keeper.greeting", (
            ("de", "Guten Abend, Fremder!"),
            ("en", "Good evening, stranger!"),
            ("fr", "Bonsoir, étranger !"),
            ("ja", "こんばんは、旅人！"),
            ("pl", "Dobry wieczór, wędrowcze!"))),
        LocalizedLine("door.locked", (
            ("de", "Die Tür ist verschlossen."),
            ("en", "The door is locked."),
            ("fr", "La porte est fermée."),
            ("ja", "扉は閉まっています。"),
            ("pl", "Drzwi są zamknięte."))),
    ))


class LocalizationTests(unittest.TestCase):
    def test_five_languages_have_deterministic_complete_bytes(self):
        catalog = sample()
        plan = charset_plan(catalog)
        self.assertEqual(len(plan.extra_glyphs), len({c for line in catalog.lines
                        for _, value in line.translations for c in value if ord(c) > 126}))
        self.assertEqual(canonical_catalog_json(parse_catalog(canonical_catalog_json(catalog))),
                         canonical_catalog_json(catalog))
        for line in catalog.lines:
            for _, text in line.translations:
                encoded = encode_scumm_literal(text, plan)
                self.assertTrue(encoded.startswith('"') and encoded.endswith('"'))
                self.assertNotIn("\n", encoded)
        self.assertIn(r"\x", encode_scumm_literal("ż", plan) if any(g == "ż" for g, _ in plan.extra_glyphs)
                      else encode_scumm_literal("ó", plan))
        self.assertIn(r"\x", encode_scumm_literal("扉", plan))

    def test_scumm_dispatch_has_stable_codes_and_source_language_fallback(self):
        catalog = sample()
        code = scumm_language_dispatch(catalog, "keeper.greeting")
        for language in LANGUAGES:
            stable = int.from_bytes(language.encode("ascii"), "big")
            self.assertIn(f"GameLanguage == {stable}", code)
        self.assertEqual(code.count("egoSay("), 6)  # 5 languages + default
        self.assertIn("else egoSay(\"Guten Abend, Fremder!\");", code)
        self.assertIn(r"\x", code)  # French, Polish and Japanese encoded explicitly
        with self.assertRaisesRegex(ValueError, "Unknown translation ID"):
            scumm_language_dispatch(catalog, "missing")

    def test_missing_translation_and_invalid_control_fail_closed(self):
        raw = json.loads(canonical_catalog_json(sample()))
        del raw["lines"][0]["translations"]["ja"]
        with self.assertRaisesRegex(ValueError, "Missing or unordered translation"):
            parse_catalog(json.dumps(raw))
        raw["lines"][0]["translations"]["ja"] = '"; evil()'
        with self.assertRaisesRegex(ValueError, "control/escape"):
            parse_catalog(json.dumps(raw))

    def test_more_than_127_non_ascii_glyphs_is_explicitly_unsupported(self):
        letters = "".join(chr(code) for code in range(0x300, 0x300 + 128))
        catalog = LanguageCatalog("de", ("de",), (
            LocalizedLine("sample", (("de", letters),)),))
        with self.assertRaisesRegex(ValueError, "capacity exceeded"):
            charset_plan(catalog)

    def test_unknown_format_or_duplicate_id_is_rejected(self):
        raw = json.loads(canonical_catalog_json(sample()))
        raw["format_version"] = 9
        with self.assertRaisesRegex(ValueError, "version"):
            parse_catalog(json.dumps(raw))
        duplicated = sample()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            charset_plan(LanguageCatalog("de", LANGUAGES, (duplicated.lines[0], duplicated.lines[0])))


if __name__ == "__main__":
    unittest.main()

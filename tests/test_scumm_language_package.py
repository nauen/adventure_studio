import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_language_package import build_language_package
from adventure_studio.localization import parse_catalog


CATALOG = json.dumps({
    "format_version": 1, "source_language": "de", "languages": ["de", "ja", "pl"],
    "lines": [{"id": "a.hello", "translations": {
        "de": "Grüße", "ja": "こんにちは", "pl": "Cześć"}}],
})


class LanguagePackageTests(unittest.TestCase):
    def test_build_publishes_canonical_catalog_font_and_checksums(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tool = root / "char"
            tool.write_bytes(b"test executable")

            def fake_probe(catalog_path, latin, cjk, converter, stage):
                self.assertEqual(parse_catalog(catalog_path.read_text()).languages, ("de", "ja", "pl"))
                (stage / "multilingual-font.char").write_bytes(b"CHAR fixture")
                (stage / "multilingual-font.bmp").write_bytes(b"BMP fixture")
                (stage / "font-probe-report.json").write_text("{}")
                return {"charset_slots": 220, "glyph_map": {"41": "A"}}

            with patch("adventure_studio.scumm_language_package.build_probe", side_effect=fake_probe):
                manifest = build_language_package(CATALOG, root, root, tool, root / "resources")
            resources = root / "resources"
            self.assertEqual(manifest["languages"], ["de", "ja", "pl"])
            self.assertEqual(manifest["glyph_map"], {"41": "A"})
            self.assertEqual((resources / "multilingual-font.char").read_bytes(), b"CHAR fixture")
            self.assertEqual(json.loads((resources / "language-package.json").read_text()), manifest)

    def test_failed_probe_does_not_publish_half_built_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tool = root / "char"
            tool.write_bytes(b"test executable")
            with patch("adventure_studio.scumm_language_package.build_probe",
                       side_effect=ValueError("Glyph coverage missing")):
                with self.assertRaisesRegex(ValueError, "Glyph coverage missing"):
                    build_language_package(CATALOG, root, root, tool, root / "resources")
            self.assertFalse((root / "resources").exists())


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from adventure_studio.localization import LanguageCatalog, LocalizedLine
from adventure_studio.scumm_font import render_scumm_font_bitmap
from adventure_studio.scumm_font_probe import verify_char_resource


class ScummFontTests(unittest.TestCase):
    @staticmethod
    def font():
        from pathlib import Path
        font = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        return font

    def test_latin_charset_bitmap_has_3_colors_and_stable_glyph_positions(self):
        try:
            from PIL import Image
            import fontTools
        except ImportError:
            self.skipTest("Optional font dependencies are unavailable")
        if not self.font().is_file():
            self.skipTest("DejaVu font is unavailable")
        catalog = LanguageCatalog("de", ("de", "pl"), (
            LocalizedLine("hello", (("de", "Grüße"), ("pl", "Cześć, żółw"))),))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "font.bmp"
            mapping = render_scumm_font_bitmap(catalog, self.font(), self.font(), path)
            image = Image.open(path)
            self.assertEqual(image.mode, "P")
            bmp = path.read_bytes()
            self.assertEqual(int.from_bytes(bmp[46:50], "little"), 3)
            self.assertEqual(image.getpixel((0, 1)), 2)
            self.assertEqual(image.getpixel((2, 1)), 2)
            self.assertEqual(image.getpixel((3, 1)), 0)
            self.assertEqual(image.getpixel((13, 1)), 0)
            self.assertEqual(image.getpixel((14, 1)), 2)
            self.assertEqual(image.getpixel((0, 14)), 2)
            self.assertNotEqual(image.getpixel((1, 14)), 2)
            self.assertEqual(image.getpixel((0, 15)), 0)
            self.assertEqual(image.getpixel((0, 16)), 2)
            # Emulate ScummC's top-border scanner: one run per glyph slot,
            # including empty positions required for byte-index stability.
            starts = []
            for y in range(1, image.height):
                x = 0
                while x < image.width:
                    if image.getpixel((x, y)) != 2 or image.getpixel((x, y - 1)) == 2:
                        x += 1
                        continue
                    starts.append((x, y))
                    while x < image.width and image.getpixel((x, y)) == 2:
                        x += 1
            self.assertEqual(len(starts), max(mapping) + 1)
            # Frames must encode proportional advances, not a fixed cell width.
            def frame_width(code):
                x = (code % 16) * 14
                y = (code // 16) * 15 + 1
                width = 0
                while image.getpixel((x + width, y)) == 2:
                    width += 1
                return width

            self.assertLess(frame_width(ord("i")), frame_width(ord("W")))
            self.assertLess(frame_width(ord(" ")), frame_width(ord("W")))
            self.assertEqual(mapping[ord("A")], "A")
            self.assertIn("ż", mapping.values())
            self.assertGreater(path.stat().st_size, 200)

    def test_japanese_missing_glyph_must_fail_not_display_tofu(self):
        try:
            from PIL import Image
            import fontTools
        except ImportError:
            self.skipTest("Optional font dependencies are unavailable")
        if not self.font().is_file():
            self.skipTest("DejaVu font is unavailable")
        catalog = LanguageCatalog("ja", ("ja",), (
            LocalizedLine("hello", (("ja", "扉は閉まっています。"),)),))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Font coverage missing"):
                render_scumm_font_bitmap(catalog, self.font(), self.font(),
                                         Path(directory) / "font.bmp")

    def test_compiled_charset_integrity_detects_missing_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.char"
            # CHAR size + fixed header + 2 glyph pointers + placeholder data.
            data = bytearray(43)
            data[:4] = b"CHAR"
            data[4:8] = len(data).to_bytes(4, "big")
            data[31:33] = (2).to_bytes(2, "little")
            data[33:37] = (12).to_bytes(4, "little")
            path.write_bytes(data)
            self.assertTrue(verify_char_resource(path, {0})["all_slots_present"])
            with self.assertRaisesRegex(ValueError, "Missing compiled glyph"):
                verify_char_resource(path, {1})


if __name__ == "__main__":
    unittest.main()

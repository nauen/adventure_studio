import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_language_runtime_probe import (
    LANGUAGE_PROBE_KEYS,
    compare_fixed_language_gui_across_rooms, compare_screenshots,
    language_runtime_probe, verify_language_button_change,
    verify_room_transition, verify_capture_visible,
    verify_fixed_language_gui_across_rooms,
)


class LanguageRuntimeProbeTests(unittest.TestCase):
    def test_all_five_languages_are_selected_before_room_change(self):
        self.assertEqual(LANGUAGE_PROBE_KEYS,
                         (("1", "de"), ("2", "en"), ("3", "fr"),
                          ("4", "ja"), ("5", "pl")))

    def test_post_room_language_comparison_requires_visible_change(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Optional Pillow dependency is unavailable")
        with tempfile.TemporaryDirectory() as temp:
            japanese = Path(temp) / "ja_after_room.png"
            polish = Path(temp) / "pl_returned_after_room.png"
            Image.new("RGB", (60, 40), (20, 20, 20)).save(japanese)
            Image.new("RGB", (60, 40), (20, 20, 20)).save(polish)
            self.assertEqual(compare_screenshots(japanese, polish)["changed_pixels"], 0)
            varied = Image.new("RGB", (60, 40), (20, 20, 20))
            varied.paste((220, 130, 80), (10, 10, 50, 20))
            varied.save(polish)
            self.assertEqual(compare_screenshots(japanese, polish)["changed_pixels"], 400)

    def test_screen_fixed_gui_region_ignores_room_pixels(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Optional Pillow dependency is unavailable")
        with tempfile.TemporaryDirectory() as temp:
            before = Path(temp) / "before.png"
            after = Path(temp) / "after.png"
            Image.new("RGB", (1024, 768), (15, 15, 15)).save(before)
            picture = Image.new("RGB", (1024, 768), (15, 15, 15))
            picture.paste((210, 90, 40), (192, 184, 832, 458))
            picture.save(after)
            self.assertEqual(compare_fixed_language_gui_across_rooms(before, after)["changed_pixels"], 0)
            self.assertTrue(verify_fixed_language_gui_across_rooms(
                before, after)["screen_fixed_gui_stable_across_rooms"])
            picture.paste((210, 90, 40), (210, 474, 230, 486))
            picture.save(after)
            self.assertEqual(compare_fixed_language_gui_across_rooms(before, after)["changed_pixels"], 240)
            with self.assertRaisesRegex(ValueError, "changed across rooms"):
                verify_fixed_language_gui_across_rooms(before, after)
            # A regression only in the far-right PL control must also fail.
            rightmost = Image.new("RGB", (1024, 768), (15, 15, 15))
            rightmost.paste((210, 90, 40), (420, 474, 440, 486))
            rightmost.save(after)
            self.assertEqual(compare_fixed_language_gui_across_rooms(before, after)["changed_pixels"], 240)
            with self.assertRaisesRegex(ValueError, "changed across rooms"):
                verify_fixed_language_gui_across_rooms(before, after)
            Image.new("RGB", (100, 100), (15, 15, 15)).save(after)
            with self.assertRaisesRegex(ValueError, "dimensions are incompatible"):
                compare_fixed_language_gui_across_rooms(before, after)

    def test_blank_capture_rejected_even_when_file_exists(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Optional Pillow dependency is unavailable")
        with tempfile.TemporaryDirectory() as temp:
            frame = Path(temp) / "capture.png"
            Image.new("RGB", (640, 480), (50, 50, 50)).save(frame)
            self.assertGreater(frame.stat().st_size, 1000)
            with self.assertRaisesRegex(ValueError, "Blank or low-contrast"):
                verify_capture_visible(frame)
            varied = Image.new("RGB", (640, 480), (50, 50, 50))
            for x in range(20, 600):
                varied.paste((200, 150, 100), (x, 20, x + 1, 250))
            varied.save(frame)
            self.assertEqual(verify_capture_visible(frame)["dimensions"], [640, 480])
            self.assertEqual(verify_capture_visible(frame)["contrast_spread"], 150)

    def test_room_transition_requires_large_visible_pixel_change(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Optional Pillow dependency is unavailable")
        with tempfile.TemporaryDirectory() as temp:
            before = Path(temp) / "before.png"
            after = Path(temp) / "after.png"
            Image.new("RGB", (100, 100), (30, 80, 140)).save(before)
            Image.new("RGB", (100, 100), (30, 80, 140)).save(after)
            with self.assertRaisesRegex(ValueError, "not visually confirmed"):
                verify_room_transition(before, after)
            changed = Image.new("RGB", (100, 100), (30, 80, 140))
            for x in range(20, 100):
                for y in range(100):
                    changed.putpixel((x, y), (150, 30, 80))
            changed.save(after)
            report = verify_room_transition(before, after)
            self.assertTrue(report["room_transition_visually_confirmed"])
            self.assertEqual(report["room_transition_changed_pixels"], 8000)
            self.assertAlmostEqual(report["room_transition_changed_ratio"], 0.8)
            self.assertEqual(compare_screenshots(before, after),
                             {"changed_pixels": 8000, "changed_ratio": 0.8})

    def test_language_diagnostics_do_not_claim_character_recognition(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Optional Pillow dependency is unavailable")
        with tempfile.TemporaryDirectory() as temp:
            before = Path(temp) / "de.png"
            after = Path(temp) / "ja.png"
            Image.new("RGB", (12, 12), (0, 0, 0)).save(before)
            Image.new("RGB", (12, 12), (0, 0, 0)).save(after)
            self.assertEqual(compare_screenshots(before, after),
                             {"changed_pixels": 0, "changed_ratio": 0.0})

    def test_graphical_selection_checks_only_badge_region(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Optional Pillow dependency is unavailable")
        with tempfile.TemporaryDirectory() as temp:
            before = Path(temp) / "before.png"
            after = Path(temp) / "after.png"
            Image.new("RGB", (1024, 768), (10, 20, 30)).save(before)
            picture = Image.new("RGB", (1024, 768), (10, 20, 30))
            for x in range(210, 230):
                for y in range(194, 210):
                    picture.putpixel((x, y), (100, 220, 30))
            picture.save(after)
            self.assertGreaterEqual(verify_language_button_change(before, after)["changed_pixels"], 300)
            with self.assertRaisesRegex(ValueError, "did not visibly change"):
                verify_language_button_change(before, before)
            fixed = Image.new("RGB", (1024, 768), (10, 20, 30))
            for x in range(215, 235):
                for y in range(463, 480):
                    fixed.putpixel((x, y), (100, 220, 30))
            fixed.save(after)
            self.assertGreaterEqual(verify_language_button_change(
                before, after, screen_fixed=True)["changed_pixels"], 300)

    def test_missing_display_fails_without_spawning_engine(self):
        with patch.dict("os.environ", {"DISPLAY": ""}):
            with self.assertRaisesRegex(RuntimeError, "Xvfb DISPLAY"):
                language_runtime_probe(Path("/not-a-game"), Path("/not-an-output"))

    def test_missing_linked_game_fails_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict("os.environ", {"DISPLAY": ":77"}):
                with self.assertRaisesRegex(ValueError, "Missing SCUMM game data"):
                    language_runtime_probe(root, root / "output")
            self.assertFalse((root / "output").exists())


if __name__ == "__main__":
    unittest.main()


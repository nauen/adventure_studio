import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_language_runtime_probe import language_runtime_probe, verify_room_transition


class LanguageRuntimeProbeTests(unittest.TestCase):
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

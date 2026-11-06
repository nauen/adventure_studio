import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_save_load_probe import (
    save_load_menu_probe, verify_save_menu_open,
)


class SaveLoadMenuProbeTests(unittest.TestCase):
    def test_menu_gate_rejects_unchanged_frame_and_accepts_substantial_change(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as directory:
            before = Path(directory) / "before.png"
            after = Path(directory) / "after.png"
            Image.new("RGB", (100, 100), (20, 70, 110)).save(before)
            Image.new("RGB", (100, 100), (20, 70, 110)).save(after)
            with self.assertRaisesRegex(ValueError, "did not visibly open"):
                verify_save_menu_open(before, after)
            changed = Image.new("RGB", (100, 100), (20, 70, 110))
            changed.paste((170, 90, 30), (20, 20, 70, 70))
            changed.save(after)
            self.assertEqual(verify_save_menu_open(before, after)["changed_pixels"], 2500)

    def test_missing_display_is_rejected_without_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict("os.environ", {"DISPLAY": ""}):
                with self.assertRaisesRegex(RuntimeError, "Xvfb DISPLAY"):
                    save_load_menu_probe(root, root / "output")
            self.assertFalse((root / "output").exists())

    def test_missing_game_is_rejected_without_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict("os.environ", {"DISPLAY": ":77"}):
                with self.assertRaisesRegex(ValueError, "Missing SCUMM game data"):
                    save_load_menu_probe(root, root / "output")
            self.assertFalse((root / "output").exists())


if __name__ == "__main__":
    unittest.main()

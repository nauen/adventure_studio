import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_save_load_probe import (
    save_load_menu_probe, verify_save_menu_open, verify_global_menu_ready,
    verify_loaded_room, verify_loaded_language_selection,
)


class SaveLoadMenuProbeTests(unittest.TestCase):
    def test_loaded_language_highlight_matches_saved_selection(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            default, selected, loaded = (root / name for name in
                                         ("default.png", "selected.png", "loaded.png"))
            for screenshot in (default, selected, loaded):
                Image.new("RGB", (1024, 768), (20, 70, 110)).save(screenshot)
            for screenshot in (selected, loaded):
                image = Image.open(screenshot).convert("RGB")
                image.paste((240, 150, 20), (200, 465, 220, 475))
                image.save(screenshot)
            result = verify_loaded_language_selection(default, selected, loaded)
            self.assertTrue(result["load_restored_language_verified"])
            with self.assertRaisesRegex(ValueError, "not restored"):
                verify_loaded_language_selection(default, selected, default)
            with self.assertRaisesRegex(ValueError, "did not visibly change"):
                verify_loaded_language_selection(selected, selected, loaded)

    def test_loaded_room_must_match_saved_room_and_differ_from_bootstrap(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initial, saved, loaded = (root / name for name in
                                      ("initial.png", "saved.png", "loaded.png"))
            Image.new("RGB", (100, 100), (20, 70, 110)).save(initial)
            Image.new("RGB", (100, 100), (170, 90, 30)).save(saved)
            Image.new("RGB", (100, 100), (170, 90, 30)).save(loaded)
            self.assertTrue(verify_loaded_room(saved, initial, loaded)
                            ["load_restored_room_verified"])
            Image.new("RGB", (100, 100), (20, 70, 110)).save(loaded)
            with self.assertRaisesRegex(ValueError, "differs substantially"):
                verify_loaded_room(saved, initial, loaded)
            Image.new("RGB", (100, 100), (170, 90, 30)).save(initial)
            Image.new("RGB", (100, 100), (170, 90, 30)).save(loaded)
            with self.assertRaisesRegex(ValueError, "initial bootstrap"):
                verify_loaded_room(saved, initial, loaded)

    def test_global_menu_requires_orange_panel_in_fixed_viewport(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as directory:
            shot = Path(directory) / "menu.png"
            Image.new("RGB", (1024, 768), (65, 129, 189)).save(shot)
            with self.assertRaisesRegex(ValueError, "not fully rendered"):
                verify_global_menu_ready(shot)
            menu = Image.new("RGB", (1024, 768), (65, 129, 189))
            menu.paste((205, 101, 0), (395, 210, 500, 550))
            menu.save(shot)
            self.assertTrue(verify_global_menu_ready(shot)["menu_rendered"])

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

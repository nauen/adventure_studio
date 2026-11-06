import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_save_load_probe import save_load_menu_probe


class SaveLoadMenuProbeTests(unittest.TestCase):
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

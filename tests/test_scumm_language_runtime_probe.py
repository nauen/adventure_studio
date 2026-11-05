import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_language_runtime_probe import language_runtime_probe


class LanguageRuntimeProbeTests(unittest.TestCase):
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

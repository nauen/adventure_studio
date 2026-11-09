import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess, TimeoutExpired

from adventure_studio.scumm_probe import check_game_files, detect


class ProbeTests(unittest.TestCase):
    def test_missing_game_files(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(check_game_files(Path(directory))[0])
            self.assertFalse(detect(Path(directory)).detected)

    def test_matching_nonempty_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "game.000").write_bytes(b"index")
            (path / "game.001").write_bytes(b"data")
            self.assertTrue(check_game_files(path)[0])
            with patch("adventure_studio.scumm_probe.subprocess.run", return_value=CompletedProcess([], 0, "No games found", "")):
                self.assertFalse(detect(path).detected)

    def test_detection_requires_recognized_scumm_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "game.000").write_bytes(b"index")
            (path / "game.001").write_bytes(b"data")
            with patch("adventure_studio.scumm_probe.subprocess.run", return_value=CompletedProcess([], 0, "scumm:tentacle  Day of the Tentacle", "")):
                result = detect(path)
                self.assertTrue(result.detected)
                self.assertEqual(result.game_id, "scumm:tentacle")

    def test_unavailable_runtime_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "game.000").write_bytes(b"index")
            (path / "game.001").write_bytes(b"data")
            with patch("adventure_studio.scumm_probe.subprocess.run", side_effect=FileNotFoundError("missing")):
                self.assertFalse(detect(path).detected)

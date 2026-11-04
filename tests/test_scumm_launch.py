"""Validation tests for the experimental ScummVM launch probe."""

import tempfile
import unittest
from pathlib import Path

from adventure_studio.scumm_launch import launch_smoke, parse_changed_pixels


class ScummLaunchTests(unittest.TestCase):
    def test_absolute_error_metric_parser(self):
        self.assertEqual(parse_changed_pixels(" 12004 \n"), 12004)
        self.assertEqual(parse_changed_pixels("0"), 0)
        for invalid in ("", "120 (120)", "NaN", "-1", "12.3"):
            with self.subTest(metric=invalid), self.assertRaises(ValueError):
                parse_changed_pixels(invalid)
    def test_missing_fixture_rejected_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            with self.assertRaisesRegex(ValueError, "Missing isolated"):
                launch_smoke(path, path / "out")

    def test_unbounded_duration_rejected_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "tentacle.000").write_bytes(b"0")
            (path / "tentacle.001").write_bytes(b"1")
            with self.assertRaisesRegex(ValueError, "duration"):
                launch_smoke(path, path / "out", seconds=21)


if __name__ == "__main__":
    unittest.main()

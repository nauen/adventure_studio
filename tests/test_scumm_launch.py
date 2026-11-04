"""Validation tests for the experimental ScummVM launch probe."""

import tempfile
import unittest
from pathlib import Path

from adventure_studio.scumm_launch import close_rgb, launch_smoke, parse_changed_pixels, parse_srgb_pixel


class ScummLaunchTests(unittest.TestCase):
    def test_color_marker_parser_and_tolerance(self):
        self.assertEqual(parse_srgb_pixel("srgb(65,129,189)"), (65, 129, 189))
        self.assertEqual(parse_srgb_pixel("gray(0)"), (0, 0, 0))
        self.assertTrue(close_rgb((65, 129, 189), (70, 130, 190)))
        self.assertTrue(close_rgb((246, 173, 90), (240, 175, 95)))
        self.assertFalse(close_rgb((65, 129, 189), (240, 175, 95)))
        for invalid in ("", "srgb(256,0,0)", "gray(256)", "srgb(1.5,2,3)", "rgb(1,2,3)"):
            with self.subTest(pixel=invalid), self.assertRaises(ValueError):
                parse_srgb_pixel(invalid)
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

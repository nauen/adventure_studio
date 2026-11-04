"""Validation tests for the experimental ScummVM launch probe."""

import tempfile
import unittest
from pathlib import Path

from adventure_studio.scumm_launch import close_rgb, count_gold_pixels, count_green_pixels, launch_smoke, parse_changed_pixels, parse_key_bounds, parse_srgb_pixel


class ScummLaunchTests(unittest.TestCase):
    def test_key_click_geometry(self):
        self.assertEqual(parse_key_bounds("28x8+338+204"), (544, 392))
        for invalid in ("", "1x1-1+2", "20x20+630+0", "0x1+1+1"):
            with self.subTest(bounds=invalid), self.assertRaises(ValueError):
                parse_key_bounds(invalid)
    def test_key_pixel_histogram(self):
        histogram = "   250: (246,173,90) #F6AD5A srgb(246,173,90)\n   112: (255,222,74) #FFDE4A srgb(255,222,74)\n"
        self.assertEqual(count_gold_pixels(histogram), 112)
        self.assertEqual(count_gold_pixels(" 250: (246,173,90) #F6AD5A\n"), 0)

    def test_door_pixel_histogram(self):
        histogram = "  80: (60,220,90) #3CDC5A srgb(60,220,90)\n  90: (255,220,75) #FFDC4B srgb(255,220,75)\n"
        self.assertEqual(count_green_pixels(histogram), 80)
        self.assertEqual(count_green_pixels(" 80: (95,60,35) #5F3C23\n"), 0)
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

    def test_goal_manifest_required_for_runtime_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "tentacle.000").write_bytes(b"0")
            (path / "tentacle.001").write_bytes(b"1")
            with self.assertRaisesRegex(ValueError, "goal manifest"):
                launch_smoke(path, path / "out")


if __name__ == "__main__":
    unittest.main()

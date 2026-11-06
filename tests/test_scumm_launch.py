"""Validation tests for the experimental ScummVM launch probe."""

import tempfile
import unittest
from unittest.mock import patch
from subprocess import CompletedProcess
from pathlib import Path

from adventure_studio.scumm_launch import close_rgb, colored_item_center, count_color_pixels, count_cyan_pixels, count_gold_pixels, count_green_pixels, key_center, launch_smoke, parse_changed_pixels, parse_key_bounds, parse_srgb_pixel


class ScummLaunchTests(unittest.TestCase):
    def test_inventory_icon_locator_excludes_verbs_and_sentence_text(self):
        with patch("adventure_studio.scumm_launch.subprocess.run",
                   return_value=CompletedProcess([], 0, stdout="32x32+104+4", stderr="")) as run:
            self.assertEqual(colored_item_center(Path("/tmp"), "recipe-second", (225, 80, 180),
                                                 inventory=True), (648, 520))
            self.assertEqual(run.call_args.args[0][3], "304x40+528+500")

    def test_key_click_geometry(self):
        self.assertEqual(parse_key_bounds("28x8+338+204"), (544, 392))
        for invalid in ("", "1x1-1+2", "20x20+630+0", "0x1+1+1"):
            with self.subTest(bounds=invalid), self.assertRaises(ValueError):
                parse_key_bounds(invalid)
    def test_retry_capture_frame_can_locate_key(self):
        with patch("adventure_studio.scumm_launch.subprocess.run",
                   return_value=CompletedProcess([], 0, stdout="28x8+338+204", stderr="")):
            self.assertEqual(key_center(Path("/tmp"), "pre-pickup-retry"), (544, 392))
    def test_key_pixel_histogram(self):
        histogram = "   250: (246,173,90) #F6AD5A srgb(246,173,90)\n   112: (255,222,74) #FFDE4A srgb(255,222,74)\n"
        self.assertEqual(count_gold_pixels(histogram), 112)
        self.assertEqual(count_gold_pixels(" 250: (246,173,90) #F6AD5A\n"), 0)
        self.assertEqual(count_color_pixels(" 90: (225,80,180) #E150B4\n", (225, 80, 180)), 90)
        self.assertEqual(count_color_pixels(" 90: (225,80,180) #E150B4\n", (255, 220, 75)), 0)

    def test_door_pixel_histogram(self):
        histogram = "  80: (60,220,90) #3CDC5A srgb(60,220,90)\n  90: (255,220,75) #FFDC4B srgb(255,220,75)\n"
        self.assertEqual(count_green_pixels(histogram), 80)
        self.assertEqual(count_green_pixels(" 80: (95,60,35) #5F3C23\n"), 0)
        self.assertEqual(count_cyan_pixels(" 80: (50,220,220) #32DCDC srgb(50,220,220)\n"), 80)
        self.assertEqual(count_cyan_pixels(histogram), 0)
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

    def test_recipe_mode_requires_real_game_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            with self.assertRaisesRegex(ValueError, "Missing isolated"):
                launch_smoke(path, path / "out", verify_recipe=True)

    def test_reverse_recipe_mode_requires_recipe_and_maps_cli_flag(self):
        from adventure_studio.scumm_launch import main
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "requires recipe mode"):
                launch_smoke(root, root / "out", reverse_recipe=True)
            with patch("sys.argv", ["scumm_launch", str(root), str(root / "out"),
                                    "--recipe-reverse-only"]):
                with patch("adventure_studio.scumm_launch.launch_smoke") as launch:
                    self.assertEqual(main(), 0)
                    self.assertTrue(launch.call_args.kwargs["verify_recipe"])
                    self.assertTrue(launch.call_args.kwargs["reverse_recipe"])
                    self.assertFalse(launch.call_args.kwargs["verify_return"])

    def test_static_scene_exception_requires_full_chain_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            with self.assertRaisesRegex(ValueError, "only for the chain"):
                launch_smoke(path, path / "out", allow_static_scene=True)


if __name__ == "__main__":
    unittest.main()


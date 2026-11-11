import subprocess
import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_room_visual_probe import (black_costume_pixels,
                                                     run_visual_comparison, verify_visual_effects)


class NativeRoomVisualProbeTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "PNG probe requires optional Pillow")
    def test_comparison_uses_validated_png_project_authoring(self):
        def captured(room, upstream, generated, destination, label):
            occluded = sum(room.zplanes[0].pixels)
            if label == "masked":
                self.assertGreater(occluded, 0)
            else:
                self.assertEqual(occluded, 0)
            return {"dark_costume_pixels": {"masked": 0, "unmasked": 488,
                                             "fullscale": 1476}[label]}

        with tempfile.TemporaryDirectory() as directory, patch(
                "adventure_studio.scumm_room_visual_probe.render_native_room",
                side_effect=captured) as renderer:
            root = Path(directory)
            result = run_visual_comparison(root, root, root / "comparison")
            self.assertEqual(renderer.call_count, 3)
            self.assertTrue(result["comparison"]["occlusion_passed"])
            self.assertTrue((root / "comparison" / "masked-authored-zplane.png").exists())

    def test_proven_native_mask_and_box_scale_counts(self):
        result = verify_visual_effects(0, 488, 1476)
        self.assertTrue(result["occlusion_passed"])
        self.assertEqual(result["occlusion_pixels_removed"], 488)
        self.assertTrue(result["walkbox_constant_scale_passed"])

    def test_rejects_missing_visual_effects(self):
        with self.assertRaisesRegex(RuntimeError, "mask"):
            verify_visual_effects(480, 488, 1476)
        with self.assertRaisesRegex(RuntimeError, "scale"):
            verify_visual_effects(0, 488, 600)
        with self.assertRaisesRegex(ValueError, "counts"):
            verify_visual_effects(-1, 488, 1476)

    def test_dark_costume_histogram_excludes_bright_background(self):
        histogram = ("  125: (0,0,0) #000000 black\n"
                     "  75: (8,8,8) #080808 dark\n"
                     "  500: (246,173,90) #F6AD5A orange\n"
                     "  12: (30,30,30) #1E1E1E charcoal\n")
        with patch("adventure_studio.scumm_room_visual_probe.subprocess.run",
                   return_value=subprocess.CompletedProcess([], 0, histogram, "")) as runner:
            self.assertEqual(black_costume_pixels(Path("frame.png")), 200)
            self.assertIn("140x105+535+305", runner.call_args.args[0])

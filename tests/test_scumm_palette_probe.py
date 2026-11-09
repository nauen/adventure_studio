import unittest

from adventure_studio.palette_demo import WATER_PALETTE
from adventure_studio.scumm_palette_probe import analyze_palette_frames


class ScummPaletteProbeTests(unittest.TestCase):
    def test_detects_cycling_with_static_sky(self):
        sky = (70, 130, 190)
        samples = [(WATER_PALETTE[0], sky), (WATER_PALETTE[1], sky), (WATER_PALETTE[2], sky)]
        self.assertTrue(analyze_palette_frames(samples)["passed"])

    def test_rejects_stalled_animation_and_moving_background(self):
        sky = (70, 130, 190)
        self.assertFalse(analyze_palette_frames([(WATER_PALETTE[0], sky)] * 3)["passed"])
        self.assertFalse(analyze_palette_frames([
            (WATER_PALETTE[0], sky), (WATER_PALETTE[1], (200, 50, 50))])["passed"])


if __name__ == "__main__":
    unittest.main()

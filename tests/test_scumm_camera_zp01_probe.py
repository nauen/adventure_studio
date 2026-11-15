"""Deterministic checks for world-X camera evidence interpretation."""

from __future__ import annotations

import unittest

try:
    from PIL import Image
except ImportError:
    Image = None

from adventure_studio.scumm_camera_zp01_probe import (
    camera_from_sky, costume_pixels, select_phases, verify_world_mask,
)


def sky_frame(camera_x: int, dark_actor: bool = False) -> Image.Image:
    image = Image.new("RGB", (1024, 768), (95, 60, 35))
    pixels = image.load()
    boundary = 192 + 2 * (480 - camera_x)
    for y in range(184, 484):
        for x in range(192, 832):
            pixels[x, y] = ((70, 130, 190) if x < boundary
                            else (240, 175, 95))
    if dark_actor:
        actor_x = 192 + 2 * (390 - camera_x + 160)
        for y in range(320, 380):
            for x in range(max(192, actor_x - 7), min(832, actor_x + 8)):
                pixels[x, y] = (0, 0, 0)
    return image


class CameraZP01EvidenceTests(unittest.TestCase):
    @unittest.skipIf(Image is None, "Pillow is an optional Studio dependency")
    def test_sky_boundary_recovers_world_camera_x(self):
        for x in (160, 240, 350, 400, 480):
            with self.subTest(camera=x):
                image = sky_frame(x, True)
                self.assertEqual(camera_from_sky(image), x)
                if x >= 240:
                    self.assertGreater(costume_pixels(image, 390, x), 100)

    def test_missing_return_phase_fails_closed(self):
        frames = [
            {"world_x": 390, "camera_x": cam, "seconds": i,
             "frame": str(i), "actor_dark_pixels": 0}
            for i, cam in enumerate((160, 350, 480))
        ]
        with self.assertRaisesRegex(RuntimeError, "Missing"):
            select_phases(frames)

    def test_wrong_walkbox_control_is_not_silently_accepted(self):
        def trace(pixels):
            return {"frames": [
                {"world_x": 390, "camera_x": cam, "seconds": i,
                 "frame": str(i), "actor_dark_pixels": pixels}
                for i, cam in enumerate((160, 350, 480, 350, 160))
            ]}
        variants = {"masked": trace(0), "transparent": trace(200),
                    "wrong-box": trace(200)}
        report = verify_world_mask(variants)
        self.assertTrue(report["native_world_anchored_zp01_pan_and_return_passed"])
        variants["wrong-box"] = trace(0)
        with self.assertRaisesRegex(RuntimeError, "invisible"):
            verify_world_mask(variants)


if __name__ == "__main__":
    unittest.main()

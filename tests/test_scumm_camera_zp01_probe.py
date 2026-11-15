"""Deterministic checks for world-X camera evidence interpretation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

from adventure_studio.scumm_camera_zp01_probe import (
    camera_from_sky, costume_pixels, export_actor_phase_crops,
    read_frames, select_phases, verify_world_mask,
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

    @unittest.skipIf(Image is None, "Pillow is an optional Studio dependency")
    def test_timestamped_native_frames_produce_inspectable_actor_phase_crops(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            times = []
            for index, camera in enumerate((160, 350, 480, 350, 160)):
                name = f"sample-{index:02d}"
                sky_frame(camera, dark_actor=True).save(
                    directory / f"scummvm-{name}.png")
                times.append({"frame": name, "elapsed_seconds": index * 0.5})
            (directory / "camera-frame-times.json").write_text(
                json.dumps(times), encoding="utf-8")
            frames = read_frames(directory)
            self.assertEqual([row["camera_x"] for row in frames],
                             [160, 350, 480, 350, 160])
            phase_crops = export_actor_phase_crops(directory, frames)
            self.assertEqual(set(phase_crops),
                             {"before", "outgoing", "far", "returning", "returned"})
            self.assertFalse(phase_crops["before"]["actor_in_viewport"])
            self.assertFalse(phase_crops["returned"]["actor_in_viewport"])
            for phase in ("outgoing", "far", "returning"):
                evidence = phase_crops[phase]
                self.assertTrue(evidence["actor_in_viewport"])
                self.assertGreater(evidence["dark_pixels"], 100)
                with Image.open(directory / evidence["actor_crop"]) as crop:
                    self.assertEqual(crop.height, 88)
                    self.assertGreater(crop.width, 0)

    def test_missing_return_phase_fails_closed(self):
        frames = [
            {"world_x": 390, "camera_x": cam, "seconds": i,
             "frame": str(i), "actor_dark_pixels": 0}
            for i, cam in enumerate((160, 350, 480))
        ]
        with self.assertRaisesRegex(RuntimeError, "Missing"):
            select_phases(frames)

    def test_full_return_is_required_even_with_mid_pan_samples(self):
        def trace(camera_positions):
            return {"frames": [
                {"world_x": 390, "camera_x": camera,
                 "screen_x": 192 + 2 * (390 - camera + 160),
                 "seconds": index, "frame": str(index),
                 "actor_dark_pixels": 0}
                for index, camera in enumerate(camera_positions)
            ]}
        # A frame at camera 430 is 100 screen pixels from camera 480;
        # completed native 160->480->160 travel must still be observed.
        from adventure_studio.scumm_camera_zp01_probe import select_phases
        phases = select_phases(trace((160, 430, 480, 430, 160))["frames"])
        self.assertEqual(phases["returned"]["camera_x"], 160)
        with self.assertRaisesRegex(RuntimeError, "completed-return"):
            select_phases(trace((160, 430, 480, 430))["frames"])

    def test_native_camera_cannot_claim_roundtrip_without_authored_endpoints(self):
        def samples(camera_positions):
            return [{"world_x": 390, "camera_x": camera,
                     "screen_x": 192 + 2 * (390 - camera + 160),
                     "seconds": index, "frame": str(index),
                     "actor_dark_pixels": 200}
                    for index, camera in enumerate(camera_positions)]
        with self.assertRaisesRegex(RuntimeError, "far side"):
            select_phases(samples((160, 350, 450, 350, 160)))
        with self.assertRaisesRegex(RuntimeError, "completed-return"):
            select_phases(samples((160, 350, 480, 350, 185)))
        with self.assertRaisesRegex(RuntimeError, "before"):
            select_phases(samples((185, 350, 480, 350, 160)))
        self.assertEqual(
            select_phases(samples((160, 350, 480, 350, 160)))["far"]["camera_x"],
            480)

    def test_return_selection_uses_distant_visible_actor_position(self):
        def trace(pixels):
            return {"frames": [
                {"world_x": 390, "camera_x": camera,
                 "screen_x": 192 + 2 * (390 - camera + 160),
                 "seconds": index, "frame": str(index),
                 "actor_dark_pixels": pixels}
                for index, camera in enumerate(
                    (160, 330, 400, 480, 430, 340, 160))
            ]}
        phases = select_phases(trace(200)["frames"])
        self.assertEqual(phases["outgoing"]["camera_x"], 330)
        self.assertEqual(phases["returning"]["camera_x"], 340)
        variants = {"masked": trace(0), "transparent": trace(200),
                    "wrong-box": trace(200)}
        result = verify_world_mask(variants)
        self.assertTrue(result["native_world_anchored_zp01_pan_and_return_passed"])

    def test_visible_positions_must_disprove_a_screen_fixed_mask(self):
        def trace(pixels):
            return {"frames": [
                {"world_x": 390, "camera_x": camera,
                 "screen_x": 192 + 2 * (390 - camera + 160),
                 "seconds": index, "frame": str(index),
                 "actor_dark_pixels": pixels}
                for index, camera in enumerate((160, 430, 480, 430, 160))
            ]}
        # The complete round-trip and offscreen-to-far displacement are
        # genuine, but the visible Actor moved only 100 screen pixels.
        # A stationary 110-pixel-wide mask could fake this comparison.
        variants = {"masked": trace(0), "transparent": trace(200),
                    "wrong-box": trace(200)}
        with self.assertRaisesRegex(RuntimeError, "screen-fixed"):
            verify_world_mask(variants)

    def test_wrong_walkbox_control_is_not_silently_accepted(self):
        def trace(pixels):
            return {"frames": [
                {"world_x": 390, "camera_x": cam,
                 "screen_x": 192 + 2 * (390 - cam + 160), "seconds": i,
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

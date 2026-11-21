"""R06 four-mask camera-pan evidence interpretation tests."""
from __future__ import annotations

import unittest

from adventure_studio.scumm_four_mask_camera_probe import (
    _TARGETS,
    _save_phase_crops,
    select_actor_phases,
    verify_four_mask_camera,
)


def trace(world_x: int, outgoing_x: int, returning_x: int,
          pixels: int) -> list[dict]:
    cameras = (160, outgoing_x, 480, returning_x, 160)
    return [{
        "frame": str(index),
        "seconds": index * 0.5,
        "camera_x": camera,
        "world_x": world_x,
        "screen_x": round(192 + 2 * (world_x - camera + 160)),
        "actor_dark_pixels": pixels,
    } for index, camera in enumerate(cameras)]


def complete_groups(masked_pixels: int = 0, control_pixels: int = 240) -> dict:
    groups = {}
    for plane, box, world_x, outgoing_x, returning_x in _TARGETS:
        expected = [0, 1, 2, 3, 4]
        wrong = list(expected)
        wrong[box - 1] = 0
        wrong[0] = plane
        groups[plane] = {
            "masked": {
                "frames": trace(world_x, outgoing_x, returning_x, masked_pixels),
                "world_x": world_x, "walkbox_masks": expected,
                "frame_report": {"scroll_color_signature_passed": True},
            },
            "transparent": {
                "frames": trace(world_x, outgoing_x, returning_x, control_pixels),
                "world_x": world_x, "walkbox_masks": expected,
                "frame_report": {"scroll_color_signature_passed": True},
            },
            "wrong-box": {
                "frames": trace(world_x, outgoing_x, returning_x, control_pixels),
                "world_x": world_x, "walkbox_masks": wrong,
                "frame_report": {"scroll_color_signature_passed": True},
            },
        }
    return groups


try:
    from PIL import Image
except ImportError:
    Image = None


class FourMaskCameraProbeTests(unittest.TestCase):
    def test_four_independent_planes_are_measured_during_both_pan_directions(self):
        result = verify_four_mask_camera(complete_groups())
        self.assertTrue(result["native_four_masks_world_anchored_camera_pan_and_return_passed"])
        self.assertEqual(set(result["pixel_comparisons"]), {"ZP01", "ZP02", "ZP03", "ZP04"})
        for plane in result["pixel_comparisons"].values():
            self.assertEqual(set(plane["pixel_comparisons"]), {"outgoing", "returning"})

    def test_missing_completed_return_fails_closed(self):
        rows = trace(360, 360, 300, 0)[:-1]
        with self.assertRaisesRegex(RuntimeError, "completed camera-return"):
            select_actor_phases(rows, 360, 360, 300)

    def test_actor_must_be_visible_on_both_sides_of_camera_turn(self):
        rows = trace(360, 360, 300, 0)
        rows[3]["screen_x"] = 900
        with self.assertRaisesRegex(RuntimeError, "not visible"):
            select_actor_phases(rows, 360, 360, 300)

    def test_screen_fixed_mask_cannot_explain_both_visible_pan_positions(self):
        rows = trace(360, 460, 320, 0)
        with self.assertRaisesRegex(RuntimeError, "screen-fixed mask on outgoing"):
            select_actor_phases(rows, 360, 460, 320)

    def test_wrong_box_control_must_leave_actor_visible(self):
        groups = complete_groups()
        groups[3]["wrong-box"]["frames"] = trace(540, 400, 400, 0)
        with self.assertRaisesRegex(RuntimeError, "ZP04/wrong-box control"):
            verify_four_mask_camera(groups)

    def test_each_target_requires_its_independent_walkbox_assignment(self):
        groups = complete_groups()
        groups[2]["masked"]["walkbox_masks"][2] = 0
        with self.assertRaisesRegex(RuntimeError, "assignments changed"):
            verify_four_mask_camera(groups)

    @unittest.skipIf(Image is None, "Pillow is an optional Studio dependency")
    def test_offscreen_camera_phases_keep_valid_viewport_crops(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            phases = {}
            for name, screen_x in (("before", 952), ("outgoing", 512),
                                   ("far", 32), ("returning", 632),
                                   ("returned", 952)):
                frame = name
                Image.new("RGB", (1024, 768), (20, 30, 40)).save(
                    directory / f"scummvm-{frame}.png")
                phases[name] = {
                    "frame": frame, "screen_x": screen_x, "camera_x": 160,
                    "world_x": 380, "actor_dark_pixels": 0, "seconds": 1.0,
                }
            crops = _save_phase_crops(directory, [], phases)
            self.assertEqual(set(crops), set(phases))
            for name, screen_x in (("before", 952), ("outgoing", 512),
                                   ("far", 32), ("returning", 632),
                                   ("returned", 952)):
                with Image.open(directory / crops[name]["actor_crop"]) as crop:
                    self.assertEqual(crop.size, (61 if 192 <= screen_x <= 831 else 60, 88))


if __name__ == "__main__":
    unittest.main()

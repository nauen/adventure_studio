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
                "frame_report": {"scroll_expected": False,
                                 "scroll_color_signature_passed": False,
                                 "frame_variation_passed": True,
                                 "changed_pixels": 3928},
            },
            "transparent": {
                "frames": trace(world_x, outgoing_x, returning_x, control_pixels),
                "world_x": world_x, "walkbox_masks": expected,
                "frame_report": {"scroll_expected": False,
                                 "scroll_color_signature_passed": False,
                                 "frame_variation_passed": True,
                                 "changed_pixels": 3928},
            },
            "wrong-box": {
                "frames": trace(world_x, outgoing_x, returning_x, control_pixels),
                "world_x": world_x, "walkbox_masks": wrong,
                "frame_report": {"scroll_expected": False,
                                 "scroll_color_signature_passed": False,
                                 "frame_variation_passed": True,
                                 "changed_pixels": 3928},
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

    def test_each_actor_target_stays_inside_viewport_on_return(self):
        for plane, box, world_x, outgoing_x, returning_x in _TARGETS:
            phases = select_actor_phases(
                trace(world_x, outgoing_x, returning_x, 0),
                world_x, outgoing_x, returning_x)
            self.assertGreaterEqual(phases["returning"]["screen_x"], 192, f"ZP{plane:02d}")
            self.assertLessEqual(phases["returning"]["screen_x"], 831, f"ZP{plane:02d}")
        self.assertEqual(_TARGETS[2][4], 352)

    def test_discrete_native_camera_samples_between_requested_targets(self):
        # Recorded stock-ScummVM camera positions have ~40-unit gaps.
        # A target between adjacent observed frames is valid evidence if
        # the actor remains visible and both directions are separated.
        for plane, box, world_x, outgoing_x, returning_x in _TARGETS:
            cameras = (160, 176, 208, 248, 288, 328, 368, 400, 440,
                       480, 456, 416, 384, 344, 304, 264, 224, 160)
            rows = [{
                "frame": str(i), "seconds": i * 0.5,
                "camera_x": camera, "world_x": world_x,
                "screen_x": round(192 + 2 * (world_x - camera + 160)),
                "actor_dark_pixels": 0,
            } for i, camera in enumerate(cameras)]
            result = select_actor_phases(rows, world_x, outgoing_x, returning_x)
            self.assertGreater(
                abs(result["outgoing"]["screen_x"] - result["returning"]["screen_x"]),
                110, f"ZP{plane:02d}")

    def test_independent_native_capture_phases_allow_one_camera_step(self):
        groups = complete_groups()
        # Real captures of ZP01 used 368/384/392 on the outgoing pan.
        # All three screen positions are valid and remain visible.
        for name, camera in (("masked", 368), ("transparent", 384),
                             ("wrong-box", 392)):
            frame = groups[1][name]["frames"][1]
            frame["camera_x"] = camera
            frame["screen_x"] = round(192 + 2 * (240 - camera + 160))
        self.assertTrue(verify_four_mask_camera(groups)[
            "native_four_masks_world_anchored_camera_pan_and_return_passed"])

    def test_control_selection_uses_comparable_real_camera_samples(self):
        rows = trace(380, 360, 272, 240)
        reference = select_actor_phases(trace(380, 392, 272, 0), 380, 360, 272)
        rows[1]["camera_x"] = 328
        rows[1]["screen_x"] = round(192 + 2 * (380 - 328 + 160))
        rows.insert(2, {"frame": "matched", "seconds": .75, "camera_x": 400,
                        "world_x": 380, "screen_x": 472, "actor_dark_pixels": 240})
        selected = select_actor_phases(rows, 380, 360, 272, reference=reference)
        self.assertEqual(selected["outgoing"]["frame"], "matched")
        rows.pop(2)
        with self.assertRaisesRegex(RuntimeError, "Camera phase mismatch"):
            select_actor_phases(rows, 380, 360, 272, reference=reference)

    def test_returning_uses_real_separated_frame_not_just_nearest(self):
        world_x = 479
        camera_positions = (160, 400, 440, 480, 472, 432, 400, 368, 336, 160)
        rows = [{
            "frame": str(i), "seconds": i * 0.5,
            "camera_x": camera, "world_x": world_x,
            "screen_x": round(192 + 2 * (world_x - camera + 160)),
            "actor_dark_pixels": 0,
        } for i, camera in enumerate(camera_positions)]
        phases = select_actor_phases(rows, world_x, 420, 352)
        self.assertEqual(phases["outgoing"]["camera_x"], 400)
        self.assertEqual(phases["returning"]["camera_x"], 336)
        self.assertGreater(abs(phases["outgoing"]["screen_x"]
                               - phases["returning"]["screen_x"]), 110)

    def test_native_roundtrip_requires_real_frame_variation(self):
        groups = complete_groups()
        groups[1]["masked"]["frame_report"]["changed_pixels"] = 0
        with self.assertRaisesRegex(RuntimeError, "no rendered frame variation"):
            verify_four_mask_camera(groups)

    def test_missing_native_camera_segment_still_fails_closed(self):
        world_x, outgoing_x, returning_x = 380, 420, 320
        rows = trace(world_x, 160, returning_x, 0)
        with self.assertRaisesRegex(RuntimeError, "Missing camera sample for outgoing"):
            select_actor_phases(rows, world_x, outgoing_x, returning_x)

    def test_missing_completed_return_fails_closed(self):
        rows = trace(360, 360, 300, 0)[:-1]
        with self.assertRaisesRegex(RuntimeError, "completed camera-return"):
            select_actor_phases(rows, 360, 360, 300)

    def test_actor_must_be_visible_on_both_sides_of_camera_turn(self):
        rows = trace(360, 360, 300, 0)
        rows[3]["screen_x"] = 900
        with self.assertRaisesRegex(RuntimeError, "not visible"):
            select_actor_phases(rows, 360, 360, 300)

    def test_native_camera_pair_uses_second_valid_outbound_sample(self):
        # Closest outgoing X=360 is too close to returning X=312.
        # The next *real* outgoing frame X=392 gives 80 world units
        # of parallax while satisfying the ±40 target window.
        rows = trace(380, 360, 312, 0)
        rows.insert(1, {
            "frame": "alternative-outbound",
            "seconds": 0.25, "camera_x": 392, "world_x": 380,
            "screen_x": round(192 + 2 * (380 - 392 + 160)),
            "actor_dark_pixels": 0,
        })
        chosen = select_actor_phases(rows, 380, 360, 312)
        self.assertEqual(chosen["outgoing"]["camera_x"], 392)
        self.assertEqual(chosen["returning"]["camera_x"], 312)
        self.assertGreater(
            abs(chosen["outgoing"]["screen_x"] - chosen["returning"]["screen_x"]),
            110,
        )

    def test_screen_fixed_mask_cannot_explain_both_visible_pan_positions(self):
        rows = trace(360, 420, 400, 0)
        with self.assertRaisesRegex(RuntimeError, "screen-fixed"):
            select_actor_phases(rows, 360, 420, 400)

    def test_wrong_box_control_must_leave_actor_visible(self):
        groups = complete_groups()
        groups[4]["wrong-box"]["frames"] = trace(505, 460, 380, 0)
        with self.assertRaisesRegex(RuntimeError, "ZP04/wrong-box/"):
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

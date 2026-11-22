"""Fail-closed and product-path checks for the R08 native concave route."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_concave_walkbox_probe import (
    run_concave_walkbox_probe, verify_concave_route,
)


class ConcaveNativeProbeTests(unittest.TestCase):
    def test_missing_bend_and_missing_actor_fail_closed(self):
        success = {"route_matrix": [
            [0, None, None, None],
            [None, 1, 2, 2],
            [None, 1, 2, 3],
            [None, 2, 2, 3],
        ], "frame_report": {"scroll_color_signature_passed": True}}
        control = {"frame_report": {"scroll_color_signature_passed": True}}
        blocked = {"route_matrix": [
            [0, None, None, None],
            [None, 1, 2, None],
            [None, 1, 2, None],
            [None, None, None, 3],
        ], "frame_report": {"scroll_color_signature_passed": False}}
        self.assertTrue(verify_concave_route(
            success, control, blocked, 150)["native_r08_concave_walkbox_passed"])
        for changed, independent, negative, pixels in (
            ({**success, "frame_report": {"scroll_color_signature_passed": False}},
             control, blocked, 150),
            (success, {"frame_report": {"scroll_color_signature_passed": False}},
             blocked, 150),
            (success, control, {**blocked, "frame_report": {
                "scroll_color_signature_passed": True}}, 150),
            (success, control, blocked, 0),
            ({**success, "route_matrix": blocked["route_matrix"]},
             control, blocked, 150),
        ):
            with self.subTest(pixels=pixels, first=changed["route_matrix"][1][3]), self.assertRaises(RuntimeError):
                verify_concave_route(changed, independent, negative, pixels)

    def test_three_independently_authored_native_games(self):
        labels = []

        def render(room, upstream, generated, destination, label, **kwargs):
            labels.append(label)
            if label == "concave-connected":
                self.assertEqual(room.box_routes[1][3], 2)
            if label == "concave-disconnected":
                self.assertIsNone(room.box_routes[1][3])
            return {"frame_report": {
                "scroll_color_signature_passed": label != "concave-disconnected"}}

        with tempfile.TemporaryDirectory() as tmp, patch(
                "adventure_studio.scumm_concave_walkbox_probe.render_native_room",
                side_effect=render), patch(
                "adventure_studio.scumm_concave_walkbox_probe.black_costume_pixels",
                return_value=150):
            root = Path(tmp)
            result = run_concave_walkbox_probe(root, root, root / "native")
            self.assertTrue(result["comparison"]["native_r08_concave_walkbox_passed"])
            self.assertEqual(labels, [
                "concave-connected", "concave-disconnected", "convex-control"])
            self.assertEqual(len(result["concave-connected"]["walkbox_corners"]), 3)
            for label in labels:
                self.assertTrue((root / "native" / f"{label}-project.json").is_file())


if __name__ == "__main__":
    unittest.main()

"""Deterministic negative and positive acceptance contract for native triangle BOXD."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_triangle_walkbox_probe import (
    run_triangle_walkbox_probe, verify_triangle_walkbox)


class TriangleWalkboxProbeTests(unittest.TestCase):
    def test_requires_reachable_triangle_and_rectangle_plus_blocked_triangle(self):
        reached = {"frame_report": {"scroll_color_signature_passed": True}}
        blocked = {"frame_report": {"scroll_color_signature_passed": False}}
        self.assertTrue(verify_triangle_walkbox(reached, blocked, reached, 150)
                        ["native_r08_triangle_walkbox_passed"])
        for wide, narrow, control, actor in (
            (blocked, blocked, reached, 150),
            (reached, reached, reached, 150),
            (reached, blocked, blocked, 150),
            (reached, blocked, reached, 0)):
            with self.assertRaises(RuntimeError):
                verify_triangle_walkbox(wide, narrow, control, actor)

    def test_three_json_exports_reach_native_renderer_independently(self):
        observed = {}

        def render(room, upstream, generated, output, label, **kwargs):
            observed[label] = room.walkboxes[0].corners
            return {"frame_report": {
                "scroll_color_signature_passed": label != "narrow-triangle"},
                "dark_costume_pixels": 150}

        with tempfile.TemporaryDirectory() as directory, patch(
                "adventure_studio.scumm_triangle_walkbox_probe.render_native_room",
                side_effect=render), patch(
                "adventure_studio.scumm_triangle_walkbox_probe.black_costume_pixels",
                return_value=150):
            root = Path(directory)
            report = run_triangle_walkbox_probe(root, root, root / "evidence")
            self.assertTrue(report["comparison"]["native_r08_triangle_walkbox_passed"])
            self.assertEqual(observed["wide-triangle"],
                             ((0, 70), (639, 100), (0, 150), (0, 150)))
            self.assertEqual(observed["narrow-triangle"],
                             ((0, 70), (110, 100), (0, 150), (0, 150)))
            self.assertEqual(observed["rectangle-control"],
                             ((0, 70), (639, 70), (639, 150), (0, 150)))
            for label in observed:
                self.assertTrue((root / "evidence" / f"{label}-project.json").is_file())

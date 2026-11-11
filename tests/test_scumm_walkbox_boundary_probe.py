"""Deterministic contract for authored walking-area comparison."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_walkbox_boundary_probe import (run_walkbox_probe,
                                                          verify_walkbox_boundary)


class WalkboxBoundaryProbeTests(unittest.TestCase):
    def test_accepts_reachable_control_and_constrained_actor(self):
        full = {"frame_report": {"scroll_color_signature_passed": True}}
        limited = {"frame_report": {"scroll_color_signature_passed": False}}
        self.assertTrue(verify_walkbox_boundary(full, limited, 200)
                        ["native_walkbox_boundary_passed"])
        with self.assertRaisesRegex(RuntimeError, "Full-width"):
            verify_walkbox_boundary(limited, limited, 200)
        with self.assertRaisesRegex(RuntimeError, "cross"):
            verify_walkbox_boundary(full, full, 200)
        with self.assertRaisesRegex(RuntimeError, "visibly"):
            verify_walkbox_boundary(full, limited, 0)

    def test_probe_builds_two_distinct_authored_json_boxd_variants(self):
        captured = {}

        def render(room, upstream, generated, destination, label, **kwargs):
            captured[label] = room.walkboxes[0].corners
            return {"frame_report": {"scroll_color_signature_passed": label == "free"},
                    "dark_costume_pixels": 150}

        with tempfile.TemporaryDirectory() as directory, patch(
                "adventure_studio.scumm_walkbox_boundary_probe.render_native_room",
                side_effect=render), patch(
                "adventure_studio.scumm_walkbox_boundary_probe.black_costume_pixels",
                return_value=200):
            root = Path(directory)
            result = run_walkbox_probe(root, root, root / "evidence")
            self.assertEqual(captured["limited"][1], (110, 70))
            self.assertEqual(captured["free"][1], (639, 70))
            self.assertTrue(result["comparison"]["native_walkbox_boundary_passed"])
            self.assertTrue((root / "evidence" / "native-walkbox-boundary-report.json").exists())

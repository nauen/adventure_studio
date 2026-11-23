"""R06 #270: fail-closed typed camera focus handoff before native gameplay."""
from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from adventure_studio.scumm_project import (
    FollowActorCameraStep, PanCameraStep, canonical_json, parse_document,
)
from adventure_studio.scumm_two_actor_camera_handoff_probe import (
    assert_native_camera_handoff, author_native_camera_handoff_project,
    verify_native_camera_focus_handoff,
)


class CameraHandoffTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.document = parse_document(
            author_native_camera_handoff_project(Path(self.directory.name))
        )

    def test_productive_json_v1_roundtrip_retains_both_actor_focus_changes(self):
        document = parse_document(canonical_json(self.document))
        result = assert_native_camera_handoff(document)
        self.assertTrue(result["native_two_actor_camera_handoff_authored"])
        self.assertEqual(
            result["camera_actor_sequence"],
            ["ForegroundWalker", "BackgroundWalker"],
        )
        self.assertFalse(result["native_visual_handoff_verified"])
        self.assertFalse(result["complete_r06_270_acceptance"])

    def test_missing_second_focus_fails_closed(self):
        sequence = self.document.interaction_sequences[-1]
        updated = replace(sequence, steps=tuple(
            item for item in sequence.steps
            if item != FollowActorCameraStep("BackgroundWalker")
        ))
        document = replace(self.document, interaction_sequences=(
            *self.document.interaction_sequences[:-1], updated
        ))
        with self.assertRaisesRegex(RuntimeError, "handoff"):
            assert_native_camera_handoff(document)

    def test_focus_after_wait_fails_closed(self):
        sequence = self.document.interaction_sequences[-1]
        steps = list(sequence.steps)
        focus = steps.pop(4)
        steps.insert(6, focus)
        updated = replace(sequence, steps=tuple(steps))
        with self.assertRaisesRegex(RuntimeError, "overlap"):
            assert_native_camera_handoff(replace(
                self.document, interaction_sequences=(
                    *self.document.interaction_sequences[:-1], updated
                )))

    def test_missing_far_camera_target_fails_closed(self):
        sequence = self.document.interaction_sequences[-1]
        updated = replace(sequence, steps=tuple(
            PanCameraStep(440) if item == PanCameraStep(480) else item
            for item in sequence.steps
        ))
        with self.assertRaisesRegex(RuntimeError, "handoff"):
            assert_native_camera_handoff(replace(
                self.document, interaction_sequences=(
                    *self.document.interaction_sequences[:-1], updated
                )))

    def test_genuine_screen_pixel_handoff_requires_both_actors_moving(self):
        positions_a = (300, 320, 340, 360, 380, 400)
        positions_b = (380, 400, 420, 440, 460, 480)
        cameras = (300, 320, 340, 360, 460, 480)
        def evidence(cameras, positions_b=positions_b):
            traces = {}
            for name, positions in (
                ("ForegroundWalker", positions_a),
                ("BackgroundWalker", positions_b),
            ):
                traces[name] = [
                    {"frame": str(i), "seconds": i * 0.4,
                     "world_x": x,
                     "screen_x": 192 + 2 * (x - cameras[i] + 160)}
                    for i, x in enumerate(positions)
                ]
            camera = [
                {"frame": str(i), "seconds": i * 0.4, "camera_x": x}
                for i, x in enumerate(cameras)
            ]
            return traces, camera
        tracks, camera = evidence(cameras)
        actual = verify_native_camera_focus_handoff(tracks, camera)
        self.assertTrue(actual["native_camera_focus_switch_verified"])
        self.assertLess(actual["before"]["seconds"], actual["after"]["seconds"])
        with self.assertRaisesRegex(RuntimeError, "visibly switch"):
            tracks, camera = evidence(positions_a)
            verify_native_camera_focus_handoff(tracks, camera)
        with self.assertRaisesRegex(RuntimeError, "simultaneous"):
            tracks, camera = evidence(cameras, (380,) * len(positions_b))
            verify_native_camera_focus_handoff(tracks, camera)

    def test_indistinguishable_actor_start_positions_rejected(self):
        a = next(actor for actor in self.document.actors
                 if actor.id == "ForegroundWalker")
        merged = replace(
            self.document,
            actors=tuple(
                replace(actor, x=a.x)
                if actor.id == "BackgroundWalker" else actor
                for actor in self.document.actors
            ),
        )
        with self.assertRaisesRegex(RuntimeError, "separately visible"):
            assert_native_camera_handoff(merged)

    def test_missing_second_actor_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "lost an authored native Actor"):
            assert_native_camera_handoff(replace(
                self.document,
                actors=tuple(actor for actor in self.document.actors
                             if actor.id != "BackgroundWalker")
            ))


if __name__ == "__main__":
    unittest.main()

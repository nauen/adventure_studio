"""R06 #274 authoring and focus-handoff screenshot contract tests."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from importlib.util import find_spec
import unittest

from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_opposing_handoff_probe import (
    author_opposing_camera_handoff_project, assert_opposing_camera_handoff,
    verify_opposing_focus_switch,
)


class OpposingFocusHandoffTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Studio PNG authoring requires Pillow")
    def test_all_three_native_controls_author_handoff_with_unique_costumes(self):
        seen = set()
        with TemporaryDirectory() as directory:
            for variant in ("masked", "transparent", "wrong-box"):
                document = parse_document(author_opposing_camera_handoff_project(
                    Path(directory) / variant, variant=variant))
                self.assertTrue(assert_opposing_camera_handoff(
                    document, variant=variant)["opposing_native_walks_and_handoff_authored"])
                name = document.costumes[-1].name
                self.assertNotIn(name, seen)
                seen.add(name)
                self.assertTrue(all(a.costume == name for a in document.actors
                                    if a.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Studio PNG authoring requires Pillow")
    def test_handoff_cannot_be_removed_without_failing_authoring(self):
        with TemporaryDirectory() as directory:
            document = parse_document(author_opposing_camera_handoff_project(
                Path(directory) / "masked"))
            sequence = next(s for s in document.interaction_sequences
                            if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"))
            sequence = replace(sequence, steps=sequence.steps[:4] + sequence.steps[5:])
            changed = replace(document, interaction_sequences=tuple(
                sequence if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close") else s
                for s in document.interaction_sequences))
            with self.assertRaisesRegex(RuntimeError, "focus switch missing"):
                assert_opposing_camera_handoff(changed)

    def test_visual_focus_requires_true_opposing_motion_and_camera_shift(self):
        xs_a = [240, 260, 285, 310, 340, 365, 390, 415]
        xs_b = [540, 520, 495, 470, 440, 415, 390, 365]
        camera = [240, 260, 280, 300, 320, 345, 365, 385]
        tracks = {}
        for actor, xs in zip(ACTOR_IDS, (xs_a, xs_b)):
            tracks[actor] = [
                {"frame": str(i), "seconds": float(i), "world_x": x,
                 "screen_x": 192 + 2 * (x - camera[i] + 160)}
                for i, x in enumerate(xs)
            ]
        cameras = [{"frame": str(i), "seconds": float(i), "camera_x": x}
                   for i, x in enumerate(camera)]
        # All numbers in this test are synthetic contract inputs, never claimed
        # as gameplay evidence. Only run_opposing_camera_handoff may accept V.
        with self.assertRaisesRegex(RuntimeError, "visibly switch focus"):
            verify_opposing_focus_switch(tracks, cameras)
        fixed = [{**r, "camera_x": 300} for r in cameras]
        with self.assertRaises(RuntimeError):
            verify_opposing_focus_switch(tracks, fixed)
        bad = {ACTOR_IDS[0]: tracks[ACTOR_IDS[0]],
               ACTOR_IDS[1]: [{**r, "world_x": 540} for r in tracks[ACTOR_IDS[1]]]}
        with self.assertRaisesRegex(RuntimeError, "No simultaneous"):
            verify_opposing_focus_switch(bad, cameras)


if __name__ == "__main__":
    unittest.main()

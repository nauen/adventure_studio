"""Regression guards for R06 #272 native opposing Actor routes."""
from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from importlib.util import find_spec

from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_two_actor_four_mask_probe import (ACTOR_IDS, verify_two_actor_native_camera_roundtrip)
from adventure_studio.scumm_opposing_actor_probe import (
    STARTS, DESTINATIONS, author_opposing_native_actor_project,
    assert_opposing_native_actor_project, verify_opposing_native_motion,
)


class OpposingNativeActorTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Native Studio PNG export needs Pillow")
    def test_three_independently_authorable_native_control_games(self):
        with tempfile.TemporaryDirectory() as directory:
            costume_names = set()
            for variant in ("masked", "transparent", "wrong-box"):
                document = parse_document(author_opposing_native_actor_project(
                    Path(directory) / variant, variant=variant))
                costume = document.costumes[-1].name
                self.assertNotIn(costume, costume_names)
                self.assertTrue(costume.startswith("R06Opposing"))
                costume_names.add(costume)
                self.assertTrue(all(actor.costume == costume for actor in document.actors
                                    if actor.id in ACTOR_IDS))
                verdict = assert_opposing_native_actor_project(document, variant=variant)
                self.assertEqual(document.rooms[0].camera_cues[-1].x, 400)
                self.assertTrue(verdict["native_opposing_walks_authored"])
                self.assertFalse(verdict["native_opposing_gameplay_verified"])
                actors = {actor.id: actor for actor in document.actors}
                for actor_id in ACTOR_IDS:
                    self.assertEqual((actors[actor_id].x, actors[actor_id].y), STARTS[actor_id])
                actions = next(s for s in document.interaction_sequences
                               if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"))
                for i, actor_id in enumerate(ACTOR_IDS):
                    self.assertEqual((actions.steps[i].x, actions.steps[i].y),
                                     DESTINATIONS[actor_id])

    @unittest.skipUnless(find_spec("PIL"), "Native Studio PNG export needs Pillow")
    def test_reject_lost_reverse_walk_or_mask(self):
        with tempfile.TemporaryDirectory() as directory:
            document = parse_document(author_opposing_native_actor_project(
                Path(directory) / "masked"))
            room = document.rooms[0]
            missing_zp = replace(document, rooms=(replace(room, zplanes=room.zplanes[:3]),
                                                   *document.rooms[1:]))
            with self.assertRaisesRegex(RuntimeError, "four room Z-planes"):
                assert_opposing_native_actor_project(missing_zp)
            with self.assertRaisesRegex(RuntimeError, "camera-visible"):
                assert_opposing_native_actor_project(
                    replace(document, rooms=(
                        replace(room, camera_cues=(
                            *room.camera_cues[:-1],
                            replace(room.camera_cues[-1], x=320),
                        )),
                        *document.rooms[1:],
                    )))
            actors = tuple(replace(a, x=200) if a.id == ACTOR_IDS[1] else a
                           for a in document.actors)
            with self.assertRaisesRegex(RuntimeError, "start position"):
                assert_opposing_native_actor_project(replace(document, actors=actors))
            sequences = tuple(
                replace(s, steps=s.steps[:1])
                if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")
                else s for s in document.interaction_sequences
            )
            with self.assertRaisesRegex(RuntimeError, "opposite native walk"):
                assert_opposing_native_actor_project(replace(document, interaction_sequences=sequences))

    def test_native_camera_follow_accepts_leftward_start_but_rejects_static_camera(self):
        # A starts left of camera X=400: true native follow may first pan LEFT.
        # Both endpoint checks and genuine pre-pan displacement remain mandatory.
        xs = (400, 385, 360, 345, 390, 480, 400, 270, 160)
        frames = [{"frame": f"scummvm-{i}", "seconds": i * 0.125,
                   "camera_x": x} for i, x in enumerate(xs)]
        verdict = verify_two_actor_native_camera_roundtrip(
            frames, expected_start=400, prepan_direction="either")
        self.assertTrue(verdict["native_camera_roundtrip_verified"])
        with self.assertRaisesRegex(RuntimeError, "right before far pan"):
            verify_two_actor_native_camera_roundtrip(
                frames, expected_start=400, prepan_direction="right")
        no_follow = [{**f, "camera_x": 400} if i < 5 else f
                     for i, f in enumerate(frames)]
        with self.assertRaisesRegex(RuntimeError, "before far pan"):
            verify_two_actor_native_camera_roundtrip(
                no_follow, expected_start=400, prepan_direction="either")
        no_return = [{**f, "camera_x": 300} if i == len(frames) - 1 else f
                     for i, f in enumerate(frames)]
        with self.assertRaisesRegex(RuntimeError, "return to X=160"):
            verify_two_actor_native_camera_roundtrip(
                no_return, expected_start=400, prepan_direction="either")

    @staticmethod
    def _native_tracks(reverse=True):
        # Synthetic rows are used *only* for negative/contract tests;
        # native completion is exclusively set by the ScummVM runner.
        xs_a = [195, 245, 280, 335, 360, 425, 450, 520, 550]
        xs_b = list(reversed(xs_a)) if reverse else xs_a
        return {
            actor: [
                {"frame": f"frame-{index}", "seconds": float(index),
                 "camera_x": 320, "world_x": x, "screen_x": 192 + 2 * (x - 160)}
                for index, x in enumerate(xs)
            ]
            for actor, xs in zip(ACTOR_IDS, (xs_a, xs_b))
        }

    def test_opposing_motion_requires_independent_reverse_frames(self):
        report = verify_opposing_native_motion(self._native_tracks())
        self.assertTrue(report["native_opposing_motion_verified"])
        with self.assertRaisesRegex(RuntimeError, "right to left|simultaneous"):
            verify_opposing_native_motion(self._native_tracks(reverse=False))
        bad = self._native_tracks()
        bad[ACTOR_IDS[1]] = bad[ACTOR_IDS[1]][:3]
        with self.assertRaisesRegex(RuntimeError, "Too few native frames"):
            verify_opposing_native_motion(bad)
        bad = self._native_tracks()
        bad[ACTOR_IDS[0]] = bad[ACTOR_IDS[0]][:1] * 9
        with self.assertRaisesRegex(RuntimeError, "Too few native frames"):
            verify_opposing_native_motion(bad)


if __name__ == "__main__":
    unittest.main()

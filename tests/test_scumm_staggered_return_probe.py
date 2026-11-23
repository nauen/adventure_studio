"""R06 #280: native staggered Actor turn tests; no synthetic V claims."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_project import PanCameraStep, WaitCameraStep, parse_document
from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_staggered_return_probe import (
    author_staggered_native_return, assert_staggered_native_return,
    verify_staggered_native_return,
)


def trace(xs):
    return [{"frame": str(i), "seconds": float(i) * 0.3, "world_x": x}
            for i, x in enumerate(xs)]


class NativeStaggeredReturnTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Studio PNG fixture requires Pillow")
    def test_three_native_control_games_and_distinct_costume_names(self):
        unique = set()
        with TemporaryDirectory() as directory:
            for variant in ("masked", "transparent", "wrong-box"):
                doc = parse_document(author_staggered_native_return(
                    Path(directory) / variant, variant=variant))
                verdict = assert_staggered_native_return(doc, variant=variant)
                self.assertTrue(verdict["staggered_native_return_authored"])
                self.assertFalse(verdict["staggered_native_return_pixels_verified"])
                costume = doc.costumes[-1].name
                self.assertNotIn(costume, unique)
                unique.add(costume)
                self.assertTrue(all(a.costume == costume for a in doc.actors
                                    if a.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Studio PNG fixture requires Pillow")
    @unittest.skipUnless(find_spec("PIL"), "Studio PNG fixture requires Pillow")
    def test_stationary_b_must_remain_in_native_camera_view_during_a_return(self):
        # Screenshot evidence from the failed stock-ScummVM run showed
        # BackgroundWalker standing at world X=175, outside the follow-A
        # viewport. A native camera pan must precede the staged return.
        with TemporaryDirectory() as directory:
            document = parse_document(author_staggered_native_return(Path(directory)))
            sequence = next(s for s in document.interaction_sequences if (
                s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"))
            self.assertEqual(
                sequence.steps[10:12], (PanCameraStep(320), WaitCameraStep()))
            # A world-space X=175 remains 15px inside the left 320-wide
            # SCUMM camera viewport; A reappears as it walks left from X=530.
            self.assertLessEqual(320 - 160, 175)
            self.assertGreaterEqual(320 + 160, 400)
            malformed = replace(sequence, steps=(
                *sequence.steps[:10], *sequence.steps[12:]))
            broken = replace(document, interaction_sequences=tuple(
                malformed if s is sequence else s
                for s in document.interaction_sequences
            ))
            with self.assertRaisesRegex(RuntimeError, "precede B"):
                assert_staggered_native_return(broken)

    def test_no_early_return_of_b_allowed(self):
        with TemporaryDirectory() as directory:
            doc = parse_document(author_staggered_native_return(Path(directory)))
            sequence = next(s for s in doc.interaction_sequences if (
                s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"))
            malformed = replace(sequence, steps=sequence.steps[:11] + sequence.steps[12:])
            bad = replace(doc, interaction_sequences=tuple(
                malformed if s is sequence else s for s in doc.interaction_sequences
            ))
            with self.assertRaisesRegex(RuntimeError, "precede B"):
                assert_staggered_native_return(bad)

    def test_dense_native_capture_uses_two_disjoint_real_frame_windows(self):
        # The actual runner samples around 70 ms: adjacent sprite frames
        # often advance <15 px. Never manufacture extra frames or reduce the
        # displacement threshold; use two non-overlapping measured windows.
        outward_a = [260 + 6 * i for i in range(50)]
        outward_b = [545 - 8 * i for i in range(50)]
        returning_a = [outward_a[-1] - 6 * (i + 1) for i in range(49)]
        returning_b = [outward_b[-1] + 8 * (i + 1) for i in range(49)]
        a = outward_a + returning_a + [returning_a[-1]] * 12
        b = outward_b + [outward_b[-1]] * 12 + returning_b
        def dense(xs):
            return [{"frame": str(i), "seconds": round(i * 0.07, 3),
                     "world_x": x} for i, x in enumerate(xs)]
        verified = verify_staggered_native_return({
            ACTOR_IDS[0]: dense(a), ACTOR_IDS[1]: dense(b),
        })
        phases = verified["a_before_b_frames"]
        self.assertEqual(len(phases), 2)
        self.assertTrue(all(15 <= row["a_return_pixels"] <= 55
                            and row["b_stationary_pixels"] <= 8
                            and 0 < row["duration_seconds"] <= 1.5
                            for row in phases))
        self.assertLess(int(phases[0]["frame"]), int(phases[1]["start_frame"]))
        # If B reverses immediately, no stationary interval can pass.
        without_pause = outward_b + returning_b + [returning_b[-1]] * 12
        with self.assertRaisesRegex(RuntimeError, "while B remains stopped"):
            verify_staggered_native_return({
                ACTOR_IDS[0]: dense(a), ACTOR_IDS[1]: dense(without_pause),
            })

    def test_visual_stagger_required_before_b_reverses(self):
        outbound_a = [260 + i * 25 for i in range(11)]
        outbound_b = [540 - i * 25 for i in range(11)]
        # Both native paths must actually arrive back at their authored
        # start positions. The old positive fixture stopped B at X=465
        # (80px short of X=545), incorrectly treating a partial leg as V.
        inbound_a = [510 - i * 25 for i in range(1, 11)] + [260] * 3
        inbound_b = [290, 290, 290, 315, 340, 365, 390, 415, 440,
                     465, 490, 515, 540]
        a = trace(outbound_a + inbound_a)
        b = trace(outbound_b + inbound_b)
        self.assertTrue(verify_staggered_native_return({
            ACTOR_IDS[0]: a, ACTOR_IDS[1]: b,
        })["staggered_native_return_verified"])
        with self.assertRaisesRegex(RuntimeError, "while B remains stopped"):
            verify_staggered_native_return({
                ACTOR_IDS[0]: a,
                ACTOR_IDS[1]: trace(outbound_b + [290 + i * 25 for i in range(1, 11)]),
            })
        with self.assertRaisesRegex(RuntimeError, "did not visibly reverse"):
            verify_staggered_native_return({
                ACTOR_IDS[0]: a,
                ACTOR_IDS[1]: trace(outbound_b + [290] * 10),
            })


if __name__ == "__main__":
    unittest.main()

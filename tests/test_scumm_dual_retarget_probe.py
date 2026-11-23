"""R06 #292: real native dual Actor destination changes, never scripted V."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_dual_retarget_probe import (
    author_native_dual_retarget, assert_native_dual_retarget,
    verify_native_dual_retarget,
)


def evidence(a_x, b_x):
    if len(a_x) != len(b_x):
        raise ValueError("Native visual regression tracks must be aligned")
    cameras = [{"frame": str(i), "seconds": i * .3, "camera_x": 400}
               for i in range(len(a_x))]
    tracks = {
        actor: [{"frame": str(i), "seconds": i * .3, "world_x": x}
                for i, x in enumerate(xs)]
        for actor, xs in ((ACTOR_IDS[0], a_x), (ACTOR_IDS[1], b_x))
    }
    return tracks, cameras


class NativeDualRetargetTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Native Studio PNG requires Pillow")
    def test_three_native_games_author_independent_two_actor_retargets(self):
        unique = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                document = parse_document(author_native_dual_retarget(
                    Path(root) / variant, variant=variant))
                result = assert_native_dual_retarget(document, variant=variant)
                self.assertTrue(result["dual_native_retargets_authored"])
                self.assertFalse(result["dual_native_retargets_pixels_verified"])
                costume = document.costumes[-1].name
                self.assertNotIn(costume, unique)
                unique.add(costume)
                self.assertTrue(all(a.costume == costume for a in document.actors
                                    if a.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Native Studio PNG requires Pillow")
    def test_second_actor_a_command_must_preempt_without_wait(self):
        with TemporaryDirectory() as root:
            document = parse_document(author_native_dual_retarget(Path(root)))
            sequence = next(s for s in document.interaction_sequences
                            if (s.room, s.hotspot_id, s.verb)
                            == ("Harbor", "Key", "Close"))
            broken = replace(sequence, steps=(
                *sequence.steps[:27], *sequence.steps[28:],
            ))
            changed = replace(document, interaction_sequences=tuple(
                broken if s is sequence else s
                for s in document.interaction_sequences
            ))
            with self.assertRaisesRegex(RuntimeError, "both native Actors"):
                assert_native_dual_retarget(changed)

    def test_both_independent_native_visual_reversals_are_required(self):
        a = ([395] * 4 + [410, 425, 440, 455, 455,
             435, 415, 395, 375, 355, 335, 315, 295, 275, 260])
        b = ([395] * 4 + [380, 365, 350, 335, 335,
             350, 365, 380, 395, 410, 425, 440, 455, 470, 485])
        tracks, cameras = evidence(a, b)
        self.assertTrue(verify_native_dual_retarget(
            tracks, cameras)["native_dual_actor_retarget_verified"])
        with self.assertRaisesRegex(RuntimeError, "never visibly started rightward"):
            verify_native_dual_retarget(*evidence(
                [395] * 9 + a[9:], b))
        with self.assertRaisesRegex(RuntimeError, "never reversed"):
            verify_native_dual_retarget(*evidence(
                a[:9] + [455] * 10, b))
        with self.assertRaisesRegex(RuntimeError, "never visibly took first leftward"):
            verify_native_dual_retarget(*evidence(
                a, [395] * 9 + b[9:]))
        with self.assertRaisesRegex(RuntimeError, "Too few native screenshot frames"):
            verify_native_dual_retarget(*evidence(a[:8], b[:8]))


if __name__ == "__main__":
    unittest.main()

"""R06 #294: productive native A-to-B retarget camera focus acceptance tests."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_dual_focus_probe import (
    author_native_dual_retarget_focus, assert_native_dual_retarget_focus,
    verify_native_dual_retarget_focus,
)


def observed(a_x, b_x, camera_x):
    """Synthetic rejection-fixture data, never native V acceptance."""
    if len(a_x) != len(b_x) or len(a_x) != len(camera_x):
        raise ValueError("Screenshot fixture lanes must have equal lengths")
    actors = {
        actor: [
            {"frame": str(i), "seconds": i * .3, "world_x": x,
             "screen_x": 512 + 2 * (x - camera_x[i])}
            for i, x in enumerate(xs)
        ]
        for actor, xs in ((ACTOR_IDS[0], a_x), (ACTOR_IDS[1], b_x))
    }
    cameras = [{"frame": str(i), "seconds": i * .3, "camera_x": x}
               for i, x in enumerate(camera_x)]
    return actors, cameras


class NativeDualFocusTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Native Studio PNG authoring requires Pillow")
    def test_three_separate_games_author_correctly_ordered_native_focus(self):
        unique = set()
        with TemporaryDirectory() as directory:
            for variant in ("masked", "transparent", "wrong-box"):
                doc = parse_document(author_native_dual_retarget_focus(
                    Path(directory) / variant, variant=variant))
                result = assert_native_dual_retarget_focus(doc, variant=variant)
                self.assertTrue(result["native_dual_retarget_camera_handoff_authored"])
                self.assertFalse(result["native_dual_retarget_camera_handoff_pixels_verified"])
                name = doc.costumes[-1].name
                self.assertNotIn(name, unique)
                unique.add(name)
                self.assertTrue(all(a.costume == name for a in doc.actors
                                    if a.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Native Studio PNG authoring requires Pillow")
    def test_camera_must_follow_a_before_b_native_retarget(self):
        with TemporaryDirectory() as directory:
            doc = parse_document(author_native_dual_retarget_focus(Path(directory)))
            target = next(s for s in doc.interaction_sequences
                          if (s.room, s.hotspot_id, s.verb)
                          == ("Harbor", "Key", "Close"))
            broken = replace(target, steps=(
                *target.steps[:29], *target.steps[30:34],
                target.steps[29], *target.steps[34:],
            ))
            wrong = replace(doc, interaction_sequences=tuple(
                broken if s is target else s for s in doc.interaction_sequences))
            with self.assertRaisesRegex(RuntimeError, "Both native focus commands"):
                assert_native_dual_retarget_focus(wrong)

    def test_visual_camera_follows_actors_during_distinct_real_walking_phases(self):
        # A reverses first; B reverses later. The native code must reproduce
        # this from independently captured stock ScummVM screenshots.
        a = ([395] * 4 + [410, 425, 440, 455, 455,
             435, 415, 395, 375, 355, 335, 315, 295, 275, 260])
        b = ([395] * 4 + [380, 365, 350, 335, 335,
             350, 365, 380, 395, 410, 425, 440, 455, 470, 485])
        cameras = [395, 395, 395, 395, 390, 390, 390, 390, 390,
                   425, 415, 395, 375, 355, 340, 360, 390, 420, 445]
        traces, frames = observed(a, b, cameras)
        self.assertTrue(verify_native_dual_retarget_focus(
            traces, frames)["native_dual_retarget_camera_handoff_verified"])
        with self.assertRaisesRegex(RuntimeError, "never focused Actor A"):
            verify_native_dual_retarget_focus(
                *observed(a, b, b))
        with self.assertRaisesRegex(RuntimeError, "never switched focus"):
            wrong_focus = [425] * 11 + [250] * (len(a) - 11)
            verify_native_dual_retarget_focus(*observed(a, b, wrong_focus))
        with self.assertRaisesRegex(RuntimeError, "No measured native camera displacement"):
            # Still get actual A-focused and B-focused walking phases, but
            # the focus switch has less than 24px real camera displacement.
            insufficient = [400] * len(a)
            insufficient[9:11] = [415, 415]
            insufficient[16:18] = [420, 420]
            verify_native_dual_retarget_focus(*observed(a, b, insufficient))


if __name__ == "__main__":
    unittest.main()

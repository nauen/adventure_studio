"""R06 #278: native two-Actor reversal must be authored and pixel-proven."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_return_walk_probe import (
    author_native_return_walk_project, assert_native_return_walk_authoring,
    verify_two_actor_native_return,
)


def screenshot_trace(xs):
    return [{"frame": str(i), "seconds": float(i), "world_x": x}
            for i, x in enumerate(xs)]


class NativeReturnWalkTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Native Studio PNG export requires Pillow")
    def test_all_three_games_have_distinct_costumes_and_two_real_return_walks(self):
        names = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                document = parse_document(author_native_return_walk_project(
                    Path(root) / variant, variant=variant))
                verdict = assert_native_return_walk_authoring(
                    document, variant=variant)
                self.assertTrue(verdict["native_two_actor_return_walks_authored"])
                self.assertFalse(verdict["native_two_actor_return_pixels_verified"])
                name = document.costumes[-1].name
                self.assertNotIn(name, names)
                names.add(name)
                self.assertTrue(all(actor.costume == name for actor in document.actors
                                    if actor.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Native Studio PNG export requires Pillow")
    def test_missing_second_return_or_teleport_fails_authoring(self):
        with TemporaryDirectory() as root:
            document = parse_document(author_native_return_walk_project(Path(root)))
            key = next(s for s in document.interaction_sequences
                       if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"))
            broken = replace(key, steps=key.steps[:11] + key.steps[12:])
            changed = replace(document, interaction_sequences=tuple(
                broken if s is key else s for s in document.interaction_sequences
            ))
            with self.assertRaisesRegex(RuntimeError, "return walks"):
                assert_native_return_walk_authoring(changed)

    def test_real_return_endpoint_after_native_camera_occlusion(self):
        # Regression from stock-ScummVM run 45149721563, artifact
        # native-r06-return-walk: B is visibly walking at X335..439,
        # briefly obscured by camera pan, and visibly at home X544/545.
        # Contract-only data: acceptance still requires actual PNG frames.
        a = [260, 285, 310, 335, 360, 385, 410, 435, 460, 485, 510,
             510, 485, 460, 435, 410, 385, 360, 335, 310, 285, 260]
        b = [545, 520, 495, 470, 445, 420, 395, 370, 345, 320, 295,
             295, 335, 359, 383, 415, 439, 544, 545, 545, 545, 545]
        seconds = [i * 0.12 for i in range(17)] + [
            2.94, 3.06, 3.18, 3.30, 3.42]
        def track(xs):
            return [{"frame": str(i), "seconds": seconds[i], "world_x": x}
                    for i, x in enumerate(xs)]
        tracks = {ACTOR_IDS[0]: track(a), ACTOR_IDS[1]: track(b)}
        self.assertTrue(verify_two_actor_native_return(
            tracks)["native_two_actor_return_verified"])
        # A sudden invisible jump to home in a single 120ms frame must
        # never count as a genuine full return leg.
        teleported = [dict(row) for row in tracks[ACTOR_IDS[1]]]
        teleported[17]["seconds"] = 2.16
        for later in teleported[18:]:
            later["seconds"] -= 0.78
        with self.assertRaisesRegex(RuntimeError, "both 120px legs"):
            verify_two_actor_native_return({
                ACTOR_IDS[0]: tracks[ACTOR_IDS[0]],
                ACTOR_IDS[1]: teleported,
            })

    def test_visual_two_leg_contract_requires_both_real_directions(self):
        first = [260, 285, 310, 335, 360, 385, 410, 435, 460, 485, 510,
                 510, 490, 470, 450, 430, 410, 390, 370, 350, 330, 310, 290, 270]
        second = [540, 515, 490, 465, 440, 415, 390, 365, 340, 315, 290,
                  290, 310, 330, 350, 370, 390, 410, 430, 450, 470, 490, 510, 530]
        tracks = {ACTOR_IDS[0]: screenshot_trace(first),
                  ACTOR_IDS[1]: screenshot_trace(second)}
        self.assertTrue(verify_two_actor_native_return(
            tracks)["native_two_actor_return_verified"])
        with self.assertRaisesRegex(RuntimeError, "Insufficient genuine native return frames"):
            verify_two_actor_native_return({
                ACTOR_IDS[0]: screenshot_trace(first[:11]),
                ACTOR_IDS[1]: tracks[ACTOR_IDS[1]],
            })
        with self.assertRaisesRegex(RuntimeError, "both 120px legs"):
            verify_two_actor_native_return({
                ACTOR_IDS[0]: screenshot_trace(first[:12] + [490, 470, 450] + [450] * 9),
                ACTOR_IDS[1]: tracks[ACTOR_IDS[1]],
            })
        # An instantaneous scripted teleport is not an actual walk frame.
        with self.assertRaisesRegex(RuntimeError, "did not visibly reverse"):
            verify_two_actor_native_return({
                ACTOR_IDS[0]: screenshot_trace(first[:11] + [260] * 13),
                ACTOR_IDS[1]: tracks[ACTOR_IDS[1]],
            })


if __name__ == "__main__":
    unittest.main()

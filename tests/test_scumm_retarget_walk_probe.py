"""R06 #290 native mid-walk retargeting: authoring and visual contracts."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_retarget_walk_probe import (
    author_native_walk_retarget, assert_native_walk_retarget,
    verify_native_walk_retarget,
)


def observations(xs, *, manual_tour=True):
    # Real R06 retargeting happens only AFTER two stationary Actors are
    # observed during the native X395 -> X480 -> X395 inspection.
    camera_tour = [395, 415, 440, 465, 480, 480, 460, 435, 410, 395]
    cameras = camera_tour + [395] * len(xs) if manual_tour else [395] * len(xs)
    positions = [395] * len(camera_tour) + list(xs) if manual_tour else list(xs)
    times = [{"frame": str(i), "seconds": i * .3, "camera_x": x}
             for i, x in enumerate(cameras)]
    tracks = {
        actor: [{"frame": str(i), "seconds": i * .3,
                 "world_x": x if actor == ACTOR_IDS[1] else 395}
                for i, x in enumerate(positions)]
        for actor in ACTOR_IDS
    }
    return tracks, times


class NativeWalkRetargetTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Studio PNG importer needs Pillow")
    def test_all_three_games_author_native_walk_retarget_without_wait(self):
        names = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                doc = parse_document(author_native_walk_retarget(
                    Path(root) / variant, variant=variant))
                verdict = assert_native_walk_retarget(doc, variant=variant)
                self.assertTrue(verdict["native_walk_retarget_authored"])
                self.assertFalse(verdict["native_walk_retarget_pixels_verified"])
                name = doc.costumes[-1].name
                self.assertNotIn(name, names)
                names.add(name)
                self.assertTrue(all(a.costume == name for a in doc.actors
                                    if a.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Studio PNG importer needs Pillow")
    def test_second_walk_must_interrupt_the_first_without_wait(self):
        with TemporaryDirectory() as root:
            doc = parse_document(author_native_walk_retarget(Path(root)))
            key = next(s for s in doc.interaction_sequences
                       if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"))
            broken = replace(key, steps=key.steps[:29] + key.steps[30:])
            wrong = replace(doc, interaction_sequences=tuple(
                broken if s is key else s for s in doc.interaction_sequences
            ))
            with self.assertRaisesRegex(RuntimeError, "interrupt active movement"):
                assert_native_walk_retarget(wrong)

    def test_framebuffer_acquisition_bounds_preserve_speed_limit(self):
        xs = [395, 395, 395, 395, 380, 365, 350, 335, 335,
              350, 402, 417, 432, 447, 462, 477, 492, 507]
        tracks, cameras = observations(xs)
        # The 52px movement is only 130ms apart by completion timestamps,
        # but the first actual framebuffer acquisition began 60ms earlier.
        first, second = cameras[19], cameras[20]
        first["seconds"] = second["seconds"] - .13
        for row in cameras:
            row["capture_started_seconds"] = row["seconds"] - .06
            row["capture_finished_seconds"] = row["seconds"]
        self.assertTrue(verify_native_walk_retarget(tracks, cameras)
                        ["native_actor_walk_retarget_verified"])
        for row in cameras:
            row.pop("capture_started_seconds")
            row.pop("capture_finished_seconds")
        with self.assertRaisesRegex(RuntimeError, "implausible teleport"):
            verify_native_walk_retarget(tracks, cameras)

    def test_visual_requires_left_then_right_without_teleport(self):
        xs = [395, 395, 395, 395, 380, 365, 350, 335, 335,
              350, 365, 380, 395, 410, 425, 440, 455, 470, 485, 500, 515]
        tracks, camera = observations(xs)
        self.assertTrue(verify_native_walk_retarget(
            tracks, camera)["native_actor_walk_retarget_verified"])
        with self.assertRaisesRegex(RuntimeError, "did not visibly remain at meeting"):
            # Previous left/right walks must not count without the native
            # rendezvous inspection that precedes the retarget interaction.
            verify_native_walk_retarget(*observations(xs, manual_tour=False))
        with self.assertRaisesRegex(RuntimeError, "implausible teleport"):
            # Several bounded left and right steps do not excuse a single
            # impossible world-space jump at the actual retarget point.
            verify_native_walk_retarget(*observations(
                [395, 395, 395, 395, 380, 365, 350, 335, 335,
                 500, 515, 530, 545, 560, 575, 590, 605]))
        with self.assertRaisesRegex(RuntimeError, "never visibly took first leftward"):
            verify_native_walk_retarget(*observations([395] * 9 + xs[9:]))
        with self.assertRaisesRegex(RuntimeError, "never reversed"):
            verify_native_walk_retarget(*observations(
                [395, 380, 365, 350, 335] + [335] * 16))
        with self.assertRaisesRegex(RuntimeError, "did not continue 90px"):
            verify_native_walk_retarget(*observations(
                xs[:9] + [350, 365, 380] + [380] * 9))


if __name__ == "__main__":
    unittest.main()

"""R06 #286: camera inspection requires measured movement and stationary Actors."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_meeting_camera_probe import (
    author_native_meeting_camera_tour, assert_native_meeting_camera_tour,
    verify_native_meeting_camera_tour,
)


class NativeMeetingCameraTourTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Native Studio mask PNGs require Pillow")
    def test_three_controls_have_unique_native_costumes_and_four_camera_opcodes(self):
        names = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                doc = parse_document(author_native_meeting_camera_tour(
                    Path(root) / variant, variant=variant))
                guard = assert_native_meeting_camera_tour(doc, variant=variant)
                self.assertTrue(guard["native_meeting_camera_tour_authored"])
                self.assertFalse(guard["native_meeting_camera_tour_pixels_verified"])
                costume = doc.costumes[-1].name
                self.assertNotIn(costume, names)
                names.add(costume)
                self.assertTrue(all(a.costume == costume for a in doc.actors
                                    if a.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Native Studio mask PNGs require Pillow")
    def test_camera_tour_must_finish_before_actor_return_release(self):
        with TemporaryDirectory() as root:
            doc = parse_document(author_native_meeting_camera_tour(Path(root)))
            target = next(s for s in doc.interaction_sequences
                          if (s.room, s.hotspot_id, s.verb)
                          == ("Harbor", "Key", "Close"))
            broken = replace(target, steps=(
                *target.steps[:20], *target.steps[24:28],
                *target.steps[20:24], *target.steps[28:],
            ))
            changed = replace(doc, interaction_sequences=tuple(
                broken if s is target else s for s in doc.interaction_sequences
            ))
            with self.assertRaisesRegex(RuntimeError, "inspection pan"):
                assert_native_meeting_camera_tour(changed)

    def test_native_camera_must_travel_out_and_back_with_both_actors_still(self):
        frames = [str(i) for i in range(14)]
        camera_x = [400, 410, 430, 450, 470, 480, 480,
                    465, 445, 425, 405, 395, 395, 395]
        camera = [{"frame": frame, "seconds": i * .3, "camera_x": x}
                  for i, (frame, x) in enumerate(zip(frames, camera_x))]
        tracks = {actor: [{"frame": frame, "seconds": i * .3, "world_x": 395}
                          for i, frame in enumerate(frames)]
                  for actor in ACTOR_IDS}
        self.assertTrue(verify_native_meeting_camera_tour(
            tracks, camera)["native_meeting_camera_tour_verified"])
        with self.assertRaisesRegex(RuntimeError, "never reached X480"):
            verify_native_meeting_camera_tour(
                tracks, [{**r, "camera_x": min(r["camera_x"], 430)}
                         for r in camera])
        with self.assertRaisesRegex(RuntimeError, "never returned to X395"):
            verify_native_meeting_camera_tour(
                tracks, [{**r, "camera_x": max(r["camera_x"], 450)}
                         for r in camera])
        moving = {ACTOR_IDS[0]: [
            {**r, "world_x": 395 + i * 20} for i, r
            in enumerate(tracks[ACTOR_IDS[0]])
        ], ACTOR_IDS[1]: tracks[ACTOR_IDS[1]]}
        with self.assertRaisesRegex(RuntimeError, "remain at meeting"):
            verify_native_meeting_camera_tour(moving, camera)
        with self.assertRaisesRegex(RuntimeError, "Both independent"):
            verify_native_meeting_camera_tour(
                {ACTOR_IDS[0]: tracks[ACTOR_IDS[0]]}, camera)


if __name__ == "__main__":
    unittest.main()

"""R06 #282 authoring guard and screenshot-only rendezvous rejection tests."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import PanCameraStep, WaitCameraStep, parse_document
from adventure_studio.scumm_rendezvous_probe import (
    author_two_actor_rendezvous_project, assert_two_actor_rendezvous,
    verify_native_rendezvous,
)


def synthetic_trace(xs):
    return [{"frame": str(i), "seconds": i * 0.25, "world_x": x}
            for i, x in enumerate(xs)]


class TwoActorRendezvousTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Studio PNG authoring requires Pillow")
    def test_all_three_genuine_native_game_controls_have_two_stage_choreography(self):
        names = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                doc = parse_document(author_two_actor_rendezvous_project(
                    Path(root) / variant, variant=variant))
                result = assert_two_actor_rendezvous(doc, variant=variant)
                self.assertEqual(
                    doc.interaction_sequences[-1].steps[10:12],
                    (PanCameraStep(320), WaitCameraStep()),
                )
                self.assertTrue(result["two_actor_native_rendezvous_authored"])
                self.assertFalse(result["two_actor_native_rendezvous_pixels_verified"])
                name = doc.costumes[-1].name
                self.assertNotIn(name, names)
                names.add(name)
                self.assertTrue(all(a.costume == name for a in doc.actors
                                    if a.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Studio PNG authoring requires Pillow")
    def test_missing_departure_rejected(self):
        with TemporaryDirectory() as root:
            doc = parse_document(author_two_actor_rendezvous_project(Path(root)))
            seq = next(s for s in doc.interaction_sequences
                       if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"))
            broken = replace(seq, steps=seq.steps[:19] + seq.steps[20:])
            changed = replace(doc, interaction_sequences=tuple(
                broken if s is seq else s for s in doc.interaction_sequences
            ))
            with self.assertRaisesRegex(RuntimeError, "commands missing"):
                assert_two_actor_rendezvous(changed)

    def test_independent_native_walk_frames_are_not_discarded_by_lane_occlusion(self):
        # Pixel-derived actor tracks can have distinct missing frames as
        # SCUMM masks and camera movement occlude one lane at a time.
        # The rendezvous itself must STILL be jointly visible.
        a = [530, 510, 490, 470, 450, 430, 410, 395, 395, 395, 395, 395,
             395, 380, 365, 345, 325, 305, 285, 265]
        b = [175, 175, 175, 195, 220, 245, 270, 295, 320, 345, 370, 395,
             395, 395, 420, 445, 470, 495, 520, 545]
        a_rows = [row for i, row in enumerate(synthetic_trace(a))
                  if i not in (2, 4, 6)]
        b_rows = [row for i, row in enumerate(synthetic_trace(b))
                  if i not in (14, 16, 18)]
        for i in range(3):
            meeting = {"frame": f"joint-meet-{i}",
                       "seconds": 3.02 + 0.02 * i, "world_x": 395}
            a_rows.append(dict(meeting))
            b_rows.append(dict(meeting))
        verdict = verify_native_rendezvous({
            ACTOR_IDS[0]: a_rows, ACTOR_IDS[1]: b_rows,
        })
        self.assertTrue(verdict["native_two_actor_rendezvous_verified"])
        self.assertTrue(verdict["meeting_frame"].startswith("joint-meet")
                        or verdict["meeting_frame"] in ("11", "12", "13"))

    def test_meeting_requires_two_actor_approach_and_departure_from_real_frames(self):
        # Synthetic values are ONLY for rejection/regression tests, never the
        # proof used by the native runner.
        a = [530, 510, 490, 470, 450, 430, 410, 395, 395, 395, 395, 395,
             395, 380, 365, 345, 325, 305, 285, 265]
        b = [175, 175, 175, 195, 220, 245, 270, 295, 320, 345, 370, 395,
             395, 395, 420, 445, 470, 495, 520, 545]
        tracks = {ACTOR_IDS[0]: synthetic_trace(a),
                  ACTOR_IDS[1]: synthetic_trace(b)}
        self.assertTrue(verify_native_rendezvous(
            tracks)["native_two_actor_rendezvous_verified"])
        with self.assertRaisesRegex(RuntimeError, "never met"):
            verify_native_rendezvous({
                ACTOR_IDS[0]: synthetic_trace(a),
                ACTOR_IDS[1]: synthetic_trace([175] * len(b)),
            })
        with self.assertRaisesRegex(RuntimeError, "did not visibly approach"):
            verify_native_rendezvous({
                ACTOR_IDS[0]: synthetic_trace(a[:14] + [395] * 6),
                ACTOR_IDS[1]: synthetic_trace(b),
            })
        with self.assertRaisesRegex(RuntimeError, "Insufficient"):
            verify_native_rendezvous({
                ACTOR_IDS[0]: synthetic_trace(a[:7]),
                ACTOR_IDS[1]: synthetic_trace(b[:7]),
            })


if __name__ == "__main__":
    unittest.main()

"""R06 #284: visual rendezvous hold and delayed native Actor release guards."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import DelayStep, PanCameraStep, WaitCameraStep, WalkActorStep, parse_document
from adventure_studio.scumm_meeting_release_probe import (
    author_native_staggered_departure, assert_native_staggered_departure,
    verify_native_rendezvous_release,
)


def screenshot_rows(xs):
    return [{"frame": str(i), "seconds": i * 0.25, "world_x": x}
            for i, x in enumerate(xs)]


class NativeMeetingReleaseTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Studio PNG authoring requires Pillow")
    def test_three_unique_native_controls_with_hold_and_release(self):
        names = set()
        with TemporaryDirectory() as directory:
            for variant in ("masked", "transparent", "wrong-box"):
                document = parse_document(author_native_staggered_departure(
                    Path(directory) / variant, variant=variant))
                result = assert_native_staggered_departure(
                    document, variant=variant)
                sequence = next(seq for seq in document.interaction_sequences
                                if (seq.room, seq.hotspot_id, seq.verb)
                                == ("Harbor", "Key", "Close"))
                self.assertEqual(sequence.steps[10:12],
                                 (PanCameraStep(320), WaitCameraStep()))
                self.assertEqual(sequence.steps[20:23], (
                    WalkActorStep(ACTOR_IDS[0], 260, 85),
                    DelayStep(2),
                    WalkActorStep(ACTOR_IDS[1], 545, 135),
                ))
                self.assertTrue(result["native_staggered_release_authored"])
                self.assertFalse(result["native_staggered_release_pixels_verified"])
                costume = document.costumes[-1].name
                self.assertNotIn(costume, names)
                names.add(costume)
                self.assertTrue(all(a.costume == costume for a in document.actors
                                    if a.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Studio PNG authoring requires Pillow")
    def test_delay_between_native_departures_is_required(self):
        with TemporaryDirectory() as directory:
            document = parse_document(author_native_staggered_departure(
                Path(directory)))
            target = next(s for s in document.interaction_sequences
                          if (s.room, s.hotspot_id, s.verb)
                          == ("Harbor", "Key", "Close"))
            broken = replace(target, steps=(*target.steps[:21], *target.steps[22:]))
            changed = replace(document, interaction_sequences=tuple(
                broken if s is target else s for s in document.interaction_sequences))
            with self.assertRaisesRegex(RuntimeError, "staggered release missing"):
                assert_native_staggered_departure(changed)

    def test_native_release_contract_rejects_uncontrolled_departure(self):
        # Synthetic contract inputs are never presented as runtime acceptance.
        a = ([530, 510, 490, 470, 450, 430, 410, 395]
             + [395] * 11
             + [375, 355, 335, 315, 295, 275, 260]
             + [260] * 8)
        b = ([175, 175, 175, 195, 220, 245, 270, 295, 320, 345, 370, 395]
             + [395] * 14
             + [415, 435, 455, 475, 495, 515, 535, 545])
        tracks = {ACTOR_IDS[0]: screenshot_rows(a),
                  ACTOR_IDS[1]: screenshot_rows(b)}
        self.assertTrue(verify_native_rendezvous_release(
            tracks)["native_rendezvous_staggered_release_verified"])
        immediate_b = b[:19] + [415, 435, 455, 475, 495, 515, 535, 545] + [545] * 7
        with self.assertRaisesRegex(RuntimeError, "stationary B"):
            verify_native_rendezvous_release({
                ACTOR_IDS[0]: screenshot_rows(a),
                ACTOR_IDS[1]: screenshot_rows(immediate_b),
            })
        with self.assertRaisesRegex(RuntimeError, "did not visibly approach and depart"):
            verify_native_rendezvous_release({
                ACTOR_IDS[0]: screenshot_rows(a),
                ACTOR_IDS[1]: screenshot_rows(b[:26] + [395] * 8),
            })


if __name__ == "__main__":
    unittest.main()

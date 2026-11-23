"""R06 #276 native reciprocal camera focus must survive authoring and evidence gates."""
from __future__ import annotations

import unittest
from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory

from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_reciprocal_focus_probe import (
    author_reciprocal_focus_project, assert_reciprocal_focus_authoring,
    verify_native_reciprocal_focus,
)


class NativeReciprocalFocusTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Studio PNG authoring requires Pillow")
    def test_three_separate_costumes_and_native_follow_commands(self):
        names = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                document = parse_document(author_reciprocal_focus_project(
                    Path(root) / variant, variant=variant))
                report = assert_reciprocal_focus_authoring(document, variant=variant)
                self.assertTrue(report["reciprocal_native_focus_authored"])
                self.assertFalse(report["native_reciprocal_visual_verified"])
                costume = document.costumes[-1].name
                self.assertNotIn(costume, names)
                names.add(costume)
                self.assertTrue(all(actor.costume == costume for actor in document.actors
                                    if actor.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Studio PNG authoring requires Pillow")
    def test_second_focus_return_must_be_before_actor_waits(self):
        with TemporaryDirectory() as root:
            doc = parse_document(author_reciprocal_focus_project(Path(root)))
            key_sequence = next(s for s in doc.interaction_sequences
                                if (s.room, s.hotspot_id, s.verb)
                                == ("Harbor", "Key", "Close"))
            broken = replace(key_sequence, steps=(
                *key_sequence.steps[:6], *key_sequence.steps[8:],
                *key_sequence.steps[6:8],
            ))
            bad = replace(doc, interaction_sequences=tuple(
                broken if s is key_sequence else s for s in doc.interaction_sequences
            ))
            with self.assertRaisesRegex(RuntimeError, "must precede both waits"):
                assert_reciprocal_focus_authoring(bad)

    def test_high_frequency_real_frame_contract_keeps_reciprocal_focus_strict(self):
        # Synthetic inputs exercise only the verifier; they are NOT V evidence.
        # Each adjacent frame moves 3px, below the >=5px requirement.
        # Genuine frame pairs within 0.4s still show simultaneous movement.
        frames = [str(i) for i in range(24)]
        xs_a = [260 + 3 * i for i in range(24)]
        xs_b = [540 - 3 * i for i in range(24)]
        cameras_x = [xs_a[i] if i < 8 or i >= 16 else xs_b[i]
                     for i in range(24)]
        tracks = {
            actor: [{"frame": frames[i], "world_x": x,
                     "screen_x": 512 + 2 * (x - cameras_x[i])}
                    for i, x in enumerate(xs)]
            for actor, xs in zip(ACTOR_IDS, (xs_a, xs_b))
        }
        cameras = [{"frame": frames[i], "seconds": round(i * 0.1, 3),
                    "camera_x": cameras_x[i]} for i in range(24)]
        verdict = verify_native_reciprocal_focus(tracks, cameras)
        self.assertTrue(verdict["native_reciprocal_focus_verified"])
        self.assertLess(verdict["a_first"]["seconds"], verdict["b_middle"]["seconds"])
        self.assertLess(verdict["b_middle"]["seconds"], verdict["a_return"]["seconds"])
        with self.assertRaisesRegex(RuntimeError, "reciprocal A-B-A focus"):
            fixed_tracks = {
                actor: [{**entry, "screen_x": 512 + 2 * (entry["world_x"] - 260)}
                        for entry in rows]
                for actor, rows in tracks.items()
            }
            verify_native_reciprocal_focus(fixed_tracks, [
                {**row, "camera_x": 260} for row in cameras
            ])
        no_b = {ACTOR_IDS[0]: tracks[ACTOR_IDS[0]],
                ACTOR_IDS[1]: [{**row, "world_x": 540}
                               for row in tracks[ACTOR_IDS[1]]]}
        with self.assertRaisesRegex(RuntimeError, "Not enough simultaneous"):
            verify_native_reciprocal_focus(no_b, cameras)

    def test_visual_verifier_rejects_missing_actor_or_stationary_camera(self):
        frames = [str(i) for i in range(8)]
        a = [260, 275, 290, 310, 330, 350, 370, 390]
        b = [540, 525, 510, 490, 470, 450, 430, 410]
        tracks = {name: [
            {"frame": frames[i], "world_x": x,
             "screen_x": 192 + 2 * (x - 300 + 160)}
            for i, x in enumerate(xs)]
            for name, xs in zip(ACTOR_IDS, (a, b))}
        cameras = [{"frame": frame, "seconds": float(i), "camera_x": 300}
                   for i, frame in enumerate(frames)]
        with self.assertRaisesRegex(RuntimeError, "reciprocal A-B-A focus"):
            verify_native_reciprocal_focus(tracks, cameras)
        with self.assertRaisesRegex(RuntimeError, "requires two Actor tracks"):
            verify_native_reciprocal_focus({ACTOR_IDS[0]: tracks[ACTOR_IDS[0]]}, cameras)
        stationary = {ACTOR_IDS[0]: tracks[ACTOR_IDS[0]],
                      ACTOR_IDS[1]: [{**row, "world_x": 540}
                                     for row in tracks[ACTOR_IDS[1]]]}
        with self.assertRaisesRegex(RuntimeError, "Not enough simultaneous"):
            verify_native_reciprocal_focus(stationary, cameras)


if __name__ == "__main__":
    unittest.main()

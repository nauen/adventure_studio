"""R06 #288: strict native camera return-to-follow contract regression tests."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_camera_resume_probe import (
    author_native_camera_follow_resume, assert_native_camera_follow_resume,
    verify_native_camera_follow_resume,
)


def evidence(camera_x, b_x):
    cameras = [
        {"frame": str(i), "seconds": i * .3, "camera_x": x}
        for i, x in enumerate(camera_x)
    ]
    tracks = {
        ACTOR_IDS[0]: [
            {"frame": str(i), "seconds": i * .3, "world_x": 395}
            for i in range(len(camera_x))
        ],
        ACTOR_IDS[1]: [
            {"frame": str(i), "seconds": i * .3, "world_x": x}
            for i, x in enumerate(b_x)
        ],
    }
    return tracks, cameras


class NativeCameraResumeTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Native Studio PNG authoring requires Pillow")
    def test_three_native_controls_author_actual_follow_after_second_walk(self):
        names = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                document = parse_document(author_native_camera_follow_resume(
                    Path(root) / variant, variant=variant))
                result = assert_native_camera_follow_resume(
                    document, variant=variant)
                self.assertTrue(result["native_post_pan_follow_authored"])
                self.assertFalse(result["native_post_pan_follow_pixels_verified"])
                costume = document.costumes[-1].name
                self.assertNotIn(costume, names)
                names.add(costume)
                self.assertTrue(all(a.costume == costume for a in document.actors
                                    if a.id in ACTOR_IDS))

    @unittest.skipUnless(find_spec("PIL"), "Native Studio PNG authoring requires Pillow")
    def test_follow_after_wait_or_before_walk_is_not_accepted(self):
        with TemporaryDirectory() as root:
            document = parse_document(author_native_camera_follow_resume(Path(root)))
            sequence = next(s for s in document.interaction_sequences
                            if (s.room, s.hotspot_id, s.verb)
                            == ("Harbor", "Key", "Close"))
            wrong = replace(sequence, steps=(
                *sequence.steps[:28],
                sequence.steps[29], sequence.steps[28],
                *sequence.steps[30:],
            ))
            altered = replace(document, interaction_sequences=tuple(
                wrong if s is sequence else s for s in document.interaction_sequences
            ))
            with self.assertRaisesRegex(RuntimeError, "must follow its return command"):
                assert_native_camera_follow_resume(altered)

    def test_screenshot_proof_rejects_static_camera_missing_b_and_no_manual_return(self):
        camera_x = [395, 415, 440, 465, 480, 480, 460, 435, 410, 395,
                    395, 400, 408, 420, 435, 455, 470, 480]
        b = [395] * 10 + [395, 415, 435, 455, 475, 495, 515, 535]
        tracks, cameras = evidence(camera_x, b)
        report = verify_native_camera_follow_resume(tracks, cameras)
        self.assertTrue(report["native_camera_follow_resume_verified"])
        # Stock ScummVM may mask A during the decisive B-follow frames.
        # Dropping these unrelated A detections must not discard genuine
        # timestamp-aligned B motion and native camera movement.
        foreground_visible_early = {
            ACTOR_IDS[0]: [row for row in tracks[ACTOR_IDS[0]]
                           if int(row["frame"]) <= 10],
            ACTOR_IDS[1]: tracks[ACTOR_IDS[1]],
        }
        self.assertTrue(verify_native_camera_follow_resume(
            foreground_visible_early, cameras)["native_camera_follow_resume_verified"])
        with self.assertRaisesRegex(RuntimeError, "did not reacquire"):
            verify_native_camera_follow_resume(
                tracks, [{**row, "camera_x": 395 if i >= 10 else row["camera_x"]}
                         for i, row in enumerate(cameras)])
        with self.assertRaisesRegex(RuntimeError, "did not visibly resume"):
            verify_native_camera_follow_resume(
                {ACTOR_IDS[0]: tracks[ACTOR_IDS[0]],
                 ACTOR_IDS[1]: [{**row, "world_x": 395}
                                for row in tracks[ACTOR_IDS[1]]]}, cameras)
        with self.assertRaisesRegex(RuntimeError, "manual-pan roundtrip"):
            verify_native_camera_follow_resume(
                tracks, [{**row, "camera_x": 480 if i >= 6
                          else row["camera_x"]}
                         for i, row in enumerate(cameras)])
        with self.assertRaisesRegex(RuntimeError, "needs two Actor tracks"):
            verify_native_camera_follow_resume(
                {ACTOR_IDS[1]: tracks[ACTOR_IDS[1]]}, cameras)


if __name__ == "__main__":
    unittest.main()

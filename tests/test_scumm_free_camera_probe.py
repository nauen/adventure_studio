"""R06 #300: real free-camera release after four independent actor focus phases."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_free_camera_probe import (
    author_native_camera_release, assert_native_camera_release,
    verify_native_camera_release,
)
from test_scumm_dual_focus_return_probe import BASE_CAMERA, visual_trace


class NativeFreeCameraTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Stock Studio costume authoring requires Pillow")
    def test_three_independent_native_games_include_follow_release_and_stage_pan(self):
        unique = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                doc = parse_document(author_native_camera_release(
                    Path(root) / variant, variant=variant))
                accepted = assert_native_camera_release(doc, variant=variant)
                self.assertTrue(accepted["native_follow_release_authored"])
                self.assertFalse(accepted["native_follow_release_pixels_verified"])
                name = doc.costumes[-1].name
                self.assertNotIn(name, unique)
                unique.add(name)

    @unittest.skipUnless(find_spec("PIL"), "Stock Studio costume authoring requires Pillow")
    def test_missing_or_premature_fixed_pan_fails_closed(self):
        with TemporaryDirectory() as root:
            doc = parse_document(author_native_camera_release(Path(root)))
            target = next(s for s in doc.interaction_sequences
                          if (s.room, s.hotspot_id, s.verb)
                          == ("Harbor", "Key", "Close"))
            for steps in (
                (*target.steps[:41], *target.steps[45:]),
                (*target.steps[:38], *target.steps[41:45],
                 *target.steps[38:41], *target.steps[45:]),
            ):
                wrong = replace(doc, interaction_sequences=tuple(
                    replace(s, steps=tuple(steps)) if s is target else s
                    for s in doc.interaction_sequences
                ))
                with self.assertRaisesRegex(RuntimeError, "Free native camera"):
                    assert_native_camera_release(wrong)

    def test_measured_camera_returns_to_fixed_stage_after_native_fourth_follow(self):
        before = BASE_CAMERA + [275, 265, 260] + [485, 485, 485]
        result = verify_native_camera_release(
            *visual_trace(before + [395, 395, 395]))
        self.assertTrue(result["native_follow_camera_released"])
        self.assertGreaterEqual(result["camera_shift"], 48)
        with self.assertRaisesRegex(RuntimeError, "never returned to free stage"):
            verify_native_camera_release(
                *visual_trace(before + [485, 485, 485]))
        with self.assertRaises(RuntimeError):
            tracks, cameras = visual_trace(before + [395, 395, 395])
            verify_native_camera_release(
                {ACTOR_IDS[0]: tracks[ACTOR_IDS[0]]}, cameras)


if __name__ == "__main__":
    unittest.main()

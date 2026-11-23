"""R06 #298: four native A/B/A/B focus transfers and pixel-based negative controls."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_four_focus_probe import (
    author_native_four_focus, assert_native_four_focus, verify_native_four_focus,
)
from test_scumm_dual_focus_return_probe import BASE_CAMERA, visual_trace


class NativeFourFocusTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Native Studio costume importer needs Pillow")
    def test_each_native_game_contains_a_fourth_follow_after_return_to_a(self):
        unique = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                doc = parse_document(author_native_four_focus(
                    Path(root) / variant, variant=variant))
                verdict = assert_native_four_focus(doc, variant=variant)
                self.assertTrue(verdict["native_four_focus_authored"])
                self.assertFalse(verdict["native_four_focus_pixels_verified"])
                costume = doc.costumes[-1].name
                self.assertNotIn(costume, unique)
                unique.add(costume)

    @unittest.skipUnless(find_spec("PIL"), "Native Studio costume importer needs Pillow")
    def test_missing_or_early_fourth_native_follow_fails_closed(self):
        with TemporaryDirectory() as root:
            doc = parse_document(author_native_four_focus(Path(root)))
            target = next(s for s in doc.interaction_sequences
                          if (s.room, s.hotspot_id, s.verb)
                          == ("Harbor", "Key", "Close"))
            for damaged in (
                (*target.steps[:38], *target.steps[41:]),
                (*target.steps[:35], *target.steps[38:41], *target.steps[35:38],
                 *target.steps[41:]),
            ):
                wrong = replace(doc, interaction_sequences=tuple(
                    replace(s, steps=tuple(damaged)) if s is target else s
                    for s in doc.interaction_sequences))
                with self.assertRaisesRegex(RuntimeError, "Fourth native B focus"):
                    assert_native_four_focus(wrong)

    def test_native_camera_must_visibly_reacquire_b_after_a(self):
        base = BASE_CAMERA + [275, 265, 260]
        result = verify_native_four_focus(
            *visual_trace(base + [485, 485, 485]))
        self.assertTrue(result["native_a_b_a_b_focus_verified"])
        self.assertGreaterEqual(result["camera_shift_from_a"], 48)
        with self.assertRaisesRegex(RuntimeError, "never returned to Actor B"):
            verify_native_four_focus(*visual_trace(base + [260, 260, 260]))
        with self.assertRaises(RuntimeError):
            traces, cameras = visual_trace(base + [485, 485, 485])
            verify_native_four_focus({ACTOR_IDS[0]: traces[ACTOR_IDS[0]]}, cameras)


if __name__ == "__main__":
    unittest.main()

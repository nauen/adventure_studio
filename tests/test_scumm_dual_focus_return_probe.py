"""R06 #296: native A->B->A focus and genuine screenshot acceptance contracts."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_dual_focus_return_probe import (
    author_native_dual_focus_return, assert_native_dual_focus_return,
    verify_native_dual_focus_return,
)


def visual_trace(cameras):
    a = ([395] * 4 + [410, 425, 440, 455, 455,
         435, 415, 395, 375, 355, 335, 315, 295, 275, 260]
         + [260] * (len(cameras) - 19))
    b = ([395] * 4 + [380, 365, 350, 335, 335,
         350, 365, 380, 395, 410, 425, 440, 455, 470, 485]
         + [485] * (len(cameras) - 19))
    frames = [{"frame": str(i), "seconds": i * .3, "camera_x": x}
              for i, x in enumerate(cameras)]
    traces = {
        actor: [{"frame": str(i), "seconds": i * .3,
                 "world_x": x, "screen_x": 512 + 2 * (x - cameras[i])}
                for i, x in enumerate(xs)]
        for actor, xs in ((ACTOR_IDS[0], a), (ACTOR_IDS[1], b))
    }
    return traces, frames


BASE_CAMERA = [395, 395, 395, 395, 390, 390, 390, 390, 390,
               425, 415, 395, 375, 355, 340, 360, 390, 420, 445]


class NativeTripleFocusTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Studio authoring needs Pillow")
    def test_all_three_variants_author_real_third_follow(self):
        costumes = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                document = parse_document(author_native_dual_focus_return(
                    Path(root) / variant, variant=variant))
                result = assert_native_dual_focus_return(
                    document, variant=variant)
                self.assertTrue(result["native_triple_focus_authored"])
                self.assertFalse(result["native_triple_focus_pixels_verified"])
                costume = document.costumes[-1].name
                self.assertNotIn(costume, costumes)
                costumes.add(costume)

    @unittest.skipUnless(find_spec("PIL"), "Studio authoring needs Pillow")
    def test_early_or_missing_native_third_follow_rejected(self):
        with TemporaryDirectory() as root:
            doc = parse_document(author_native_dual_focus_return(Path(root)))
            target = next(s for s in doc.interaction_sequences
                          if (s.room, s.hotspot_id, s.verb)
                          == ("Harbor", "Key", "Close"))
            broken = replace(target, steps=(
                *target.steps[:35], *target.steps[36:]))
            changed = replace(doc, interaction_sequences=tuple(
                broken if s is target else s for s in doc.interaction_sequences))
            with self.assertRaisesRegex(RuntimeError, "must follow B"):
                assert_native_dual_focus_return(changed)

    def test_pixel_contract_requires_later_native_a_reacquisition(self):
        tracks, cameras = visual_trace(BASE_CAMERA + [275, 265, 260])
        result = verify_native_dual_focus_return(tracks, cameras)
        self.assertTrue(result["native_a_b_a_focus_verified"])
        self.assertGreaterEqual(result["camera_shift_from_b"], 48)
        with self.assertRaisesRegex(RuntimeError, "did not reacquire Actor A"):
            verify_native_dual_focus_return(
                *visual_trace(BASE_CAMERA + [445, 445, 445]))
        with self.assertRaises(RuntimeError):
            verify_native_dual_focus_return(
                {ACTOR_IDS[0]: tracks[ACTOR_IDS[0]]}, cameras)


if __name__ == "__main__":
    unittest.main()

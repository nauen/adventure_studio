"""R06 #302: two genuine Actors cross during the stationary stage camera shot."""
from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from adventure_studio.scumm_opposing_actor_probe import ACTOR_IDS
from adventure_studio.scumm_project import parse_document
from adventure_studio.scumm_stage_crossover_probe import (
    author_native_stage_crossover, assert_native_stage_crossover,
    verify_native_stage_crossover,
)
from test_scumm_dual_focus_return_probe import BASE_CAMERA, visual_trace


def crossing_evidence(*, crossover=True, camera_fixed=True):
    # A-B-A-B camera focus, then three genuine stage frames before crossing.
    camera = BASE_CAMERA + [275, 265, 260] + [485, 485, 485]
    camera += [395] * 15
    tracks, frames = visual_trace(camera)
    a = [260, 260, 260, 280, 310, 340, 380, 420, 460, 500, 545, 545, 545, 545, 545]
    b = [485, 485, 485, 465, 435, 405, 365, 325, 285, 260, 260, 260, 260, 260, 260]
    if not crossover:
        b = [485] * len(b)
    if not camera_fixed:
        for row in frames[-12:]:
            row["camera_x"] = 455
    # Synthetic fixtures are rejection-unit-tests only. Native V uses
    # screenshot tracking in run_native_stage_crossover().
    for idx, (ax, bx) in enumerate(zip(a, b), start=25):
        tracks[ACTOR_IDS[0]][idx]["world_x"] = ax
        tracks[ACTOR_IDS[1]][idx]["world_x"] = bx
        for actor, world in ((ACTOR_IDS[0], ax), (ACTOR_IDS[1], bx)):
            tracks[actor][idx]["screen_x"] = 512 + 2 * (world - frames[idx]["camera_x"])
    return tracks, frames


class NativeStageCrossoverTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("PIL"), "Studio costume authoring needs Pillow")
    def test_independent_native_games_author_concurrent_actor_crossing(self):
        unique = set()
        with TemporaryDirectory() as root:
            for variant in ("masked", "transparent", "wrong-box"):
                doc = parse_document(author_native_stage_crossover(
                    Path(root) / variant, variant=variant))
                result = assert_native_stage_crossover(doc, variant=variant)
                self.assertTrue(result["two_native_stage_crossing_walks_authored"])
                self.assertFalse(result["two_native_stage_crossing_walks_pixels_verified"])
                name = doc.costumes[-1].name
                self.assertNotIn(name, unique)
                unique.add(name)

    @unittest.skipUnless(find_spec("PIL"), "Studio costume authoring needs Pillow")
    def test_missing_or_serial_walk_fails_native_authoring(self):
        with TemporaryDirectory() as root:
            doc = parse_document(author_native_stage_crossover(Path(root)))
            target = next(s for s in doc.interaction_sequences
                          if (s.room, s.hotspot_id, s.verb)
                          == ("Harbor", "Key", "Close"))
            for broken in (
                (*target.steps[:46], *target.steps[47:]),
                (*target.steps[:46], target.steps[47],
                 target.steps[46], *target.steps[48:]),
            ):
                invalid = replace(doc, interaction_sequences=tuple(
                    replace(s, steps=tuple(broken)) if s is target else s
                    for s in doc.interaction_sequences))
                with self.assertRaisesRegex(RuntimeError, "Both native Actors must cross"):
                    assert_native_stage_crossover(invalid)

    def test_pixel_contract_demands_real_two_actor_crossover_with_fixed_camera(self):
        result = verify_native_stage_crossover(*crossing_evidence())
        self.assertTrue(result["native_stage_crossover_verified"])
        self.assertGreaterEqual(len(result["simultaneous_actor_frames"]), 2)
        with self.assertRaisesRegex(RuntimeError, "did not cross 140px"):
            verify_native_stage_crossover(*crossing_evidence(crossover=False))
        with self.assertRaises(RuntimeError):
            verify_native_stage_crossover(*crossing_evidence(camera_fixed=False))


if __name__ == "__main__":
    unittest.main()

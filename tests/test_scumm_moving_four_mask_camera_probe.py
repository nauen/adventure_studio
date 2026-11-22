"""R06 moving-actor native evidence must reject stationary camera-only footage."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from adventure_studio.scumm_project import parse_document

from adventure_studio.scumm_four_mask_camera_probe import (
    verify_moving_actor_crosses_four_masks,
    _author_project,
)


def frame(seconds, world_x, camera_x):
    return {"seconds": seconds, "world_x": world_x, "camera_x": camera_x}


class MovingActorEvidenceTests(unittest.TestCase):
    def test_product_authoring_preserves_native_walk_and_four_masks(self):
        with TemporaryDirectory() as temporary:
            project, masks, _ = _author_project(
                Path(temporary), 1, "masked", 170, moving_actor=True)
            room = next(room for room in parse_document(project).rooms
                        if room.name == "Harbor")
            self.assertEqual(room.demo_walk_to_x, 535)
            self.assertEqual(room.ego_start_x, 170)
            self.assertEqual(masks, [0, 1, 2, 3, 4])
            self.assertEqual(len(room.zplanes), 4)
            self.assertEqual(len(room.walkboxes), 5)

    def test_observed_four_zones_and_camera_return(self):
        rows = [frame(0, 170, 160), frame(1, 245, 210),
                frame(2, 345, 320), frame(3, 435, 430),
                frame(4, 530, 480), frame(5, 535, 380),
                frame(6, 535, 160)]
        result = verify_moving_actor_crosses_four_masks(rows)
        self.assertTrue(result["native_moving_actor_four_mask_path_observed"])
        self.assertEqual([x["zplane"] for x in result["visited_zplanes"]],
                         [1, 2, 3, 4])

    def test_stationary_actor_is_not_walking(self):
        rows = [frame(0, 240, 160), frame(1, 240, 480),
                frame(2, 240, 160)]
        with self.assertRaisesRegex(RuntimeError, "never entered"):
            verify_moving_actor_crosses_four_masks(rows)

    def test_no_camera_return_is_not_native_completion(self):
        rows = [frame(0, 170, 160), frame(1, 245, 210),
                frame(2, 345, 320), frame(3, 435, 430),
                frame(4, 530, 480)]
        with self.assertRaisesRegex(RuntimeError, "did not complete"):
            verify_moving_actor_crosses_four_masks(rows)


if __name__ == "__main__":
    unittest.main()

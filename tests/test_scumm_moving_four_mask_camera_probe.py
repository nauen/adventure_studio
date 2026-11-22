"""R06 moving-actor native evidence must reject stationary camera-only footage."""
import unittest

from adventure_studio.scumm_four_mask_camera_probe import (
    verify_moving_actor_crosses_four_masks,
)


def frame(seconds, world_x, camera_x):
    return {"seconds": seconds, "world_x": world_x, "camera_x": camera_x}


class MovingActorEvidenceTests(unittest.TestCase):
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

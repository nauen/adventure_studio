import unittest

from adventure_studio.scumm_scal_probe import expected_vertical_scale, verify_perspective_progression


class ScummScaleCurveMathTests(unittest.TestCase):
    def test_scummvm_vertical_integer_interpolation(self):
        self.assertEqual(expected_vertical_scale(70), 80)
        self.assertEqual(expected_vertical_scale(100), 141)
        self.assertEqual(expected_vertical_scale(125), 193)
        self.assertEqual(expected_vertical_scale(145), 234)
        self.assertEqual(expected_vertical_scale(155), 255)

    def test_interpolator_clamps_to_native_actor_range(self):
        self.assertEqual(expected_vertical_scale(0), 1)
        self.assertEqual(expected_vertical_scale(199), 255)
        with self.assertRaises(ValueError):
            expected_vertical_scale(100, y1=120, y2=90)

    def test_native_perspective_acceptance_bands(self):
        self.assertTrue(verify_perspective_progression((724, 1020, 1124))["perspective_scaling_passed"])
        for counts in ((0, 286, 1016), (800, 800, 1200), (800, 1000, 1000)):
            with self.subTest(counts=counts), self.assertRaises(RuntimeError):
                verify_perspective_progression(counts)
        with self.assertRaises(ValueError):
            verify_perspective_progression((0, 1, -1))

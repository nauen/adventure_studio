import unittest

from adventure_studio.scumm_scal_probe import expected_vertical_scale


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

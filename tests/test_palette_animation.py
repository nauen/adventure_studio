import unittest

from adventure_studio.palette_animation import PaletteCycle, palette_at_tick, validate_cycles


PALETTE = ((0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255))


class PaletteAnimationTests(unittest.TestCase):
    def test_cycle_is_deterministic_and_periodic(self):
        cycles = (PaletteCycle("water", 1, 3, 2),)
        self.assertEqual(palette_at_tick(PALETTE, cycles, 0), PALETTE)
        self.assertEqual(palette_at_tick(PALETTE, cycles, 1), PALETTE)
        self.assertEqual(palette_at_tick(PALETTE, cycles, 2)[1:4],
                         (PALETTE[3], PALETTE[1], PALETTE[2]))
        self.assertEqual(palette_at_tick(PALETTE, cycles, 6), PALETTE)
        self.assertEqual(palette_at_tick(PALETTE, cycles, 2)[0], PALETTE[0])

    def test_reverse_cycle(self):
        self.assertEqual(palette_at_tick(PALETTE, (PaletteCycle("water", 1, 3, 1, True),), 1)[1:4],
                         (PALETTE[2], PALETTE[3], PALETTE[1]))

    def test_cycles_cannot_touch_protected_or_other_ranges(self):
        with self.assertRaisesRegex(ValueError, "protected"):
            validate_cycles(PALETTE, (PaletteCycle("water", 1, 3, 1),), frozenset({2}))
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            validate_cycles(PALETTE, (PaletteCycle("a", 1, 2, 1), PaletteCycle("b", 2, 4, 1)))

    def test_invalid_cycles_rejected(self):
        for cycle in (PaletteCycle("bad", 1, 5, 1), PaletteCycle("bad", 2, 2, 1),
                      PaletteCycle("bad", 1, 2, 0), PaletteCycle("bad", True, 2, 1)):
            with self.subTest(cycle=cycle), self.assertRaises(ValueError):
                validate_cycles(PALETTE, (cycle,))


if __name__ == "__main__":
    unittest.main()

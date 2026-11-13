"""Fail-closed native route comparison for an R09 gate after room reentry."""

import unittest

from adventure_studio.scumm_gate_room_return_probe import verify_return_routes


class NativeGateRoomReturnTests(unittest.TestCase):
    def setUp(self):
        self.open = [360.0] * 9
        self.closed = [400.0] * 9

    def test_open_shortcut_and_closed_detour_both_survive_reentry(self):
        result = verify_return_routes(
            self.open, self.closed, self.open, self.closed, self.open)
        self.assertTrue(result["native_gate_room_return_routes_passed"])
        self.assertEqual(result["closed_vs_always_open"], [40.0] * 9)

    def test_rejects_open_sprite_with_walkbox_reset_to_closed(self):
        with self.assertRaisesRegex(RuntimeError, "Open gate shortcut"):
            verify_return_routes(self.closed, self.closed,
                                 self.open, self.closed, self.open)

    def test_rejects_closed_sprite_with_shortcut_still_open(self):
        with self.assertRaisesRegex(RuntimeError, "Closed gate detour"):
            verify_return_routes(self.open, self.open,
                                 self.open, self.closed, self.open)

    def test_rejects_missing_route_samples(self):
        with self.assertRaisesRegex(ValueError, "nine"):
            verify_return_routes(self.open[:8], self.closed,
                                 self.open, self.closed, self.open)

    def test_tolerates_later_camera_scroll_but_not_early_shortcut(self):
        late_phase = self.closed[:6] + [375.0, 372.0, 370.0]
        self.assertTrue(verify_return_routes(
            self.open, late_phase, self.open, self.closed,
            self.open)["native_gate_room_return_routes_passed"])


if __name__ == "__main__":
    unittest.main()

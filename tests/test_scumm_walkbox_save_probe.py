"""Fail-closed route metrics for stock-ScummVM R09 Save/Load evidence."""

import unittest

from adventure_studio.scumm_walkbox_save_probe import verify_loaded_gate_routes


class ReversibleGateSaveLoadTests(unittest.TestCase):
    def setUp(self):
        self.shortcut = [360.0] * 9
        self.detour = [400.0] * 9

    def test_saved_open_shortcut_and_post_load_close_detour(self):
        report = verify_loaded_gate_routes(
            self.shortcut, self.detour, self.shortcut, self.detour, self.shortcut)
        self.assertTrue(report["native_gate_save_load_routes_passed"])
        self.assertEqual(report["loaded_closed_vs_always_open_deltas"], [40.0] * 9)

    def test_accepts_proven_initial_detour_with_late_camera_phase_difference(self):
        post_load = [402.5, 411.0, 412.0, 412.5, 412.0, 396.0, 370.0, 369.0, 368.0]
        reference = [412.5, 413.0, 412.0, 410.5, 410.0, 406.0, 405.0, 403.0, 400.0]
        self.assertTrue(verify_loaded_gate_routes(
            self.shortcut, post_load, self.shortcut, reference,
            self.shortcut)["native_gate_save_load_routes_passed"])

    def test_rejects_open_shortcut_during_post_load_detour_window(self):
        post_load = [360.0] * 6 + [400.0] * 3
        with self.assertRaisesRegex(RuntimeError, "detour"):
            verify_loaded_gate_routes(
                self.shortcut, post_load, self.shortcut, self.detour, self.shortcut)

    def test_rejects_loaded_gate_that_reset_to_initially_closed_route(self):
        with self.assertRaisesRegex(RuntimeError, "shortcut"):
            verify_loaded_gate_routes(
                self.detour, self.detour, self.shortcut, self.detour, self.shortcut)

    def test_rejects_false_positive_sprite_without_native_detour(self):
        with self.assertRaisesRegex(RuntimeError, "detour"):
            verify_loaded_gate_routes(
                self.shortcut, self.shortcut, self.shortcut, self.detour, self.shortcut)

    def test_rejects_unaligned_actor_frame_counts(self):
        with self.assertRaisesRegex(ValueError, "nine"):
            verify_loaded_gate_routes(
                self.shortcut[:8], self.detour, self.shortcut,
                self.detour, self.shortcut)


if __name__ == "__main__":
    unittest.main()

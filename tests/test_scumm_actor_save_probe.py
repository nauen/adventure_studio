"""Fail-closed contracts for the native Actor save/reload gameplay gate."""

import unittest

from adventure_studio.scumm_actor_save_probe import verify_actor_state


class ActorSaveStateTests(unittest.TestCase):
    def test_hidden_key_and_open_door_are_required_together(self):
        for phase in ("before save", "after load", "after loaded room return"):
            verify_actor_state({"key_pixels": 0, "open_door_pixels": 40}, phase)
            verify_actor_state({"key_pixels": 9, "open_door_pixels": 100}, phase)
            for key, door in ((10, 40), (0, 39), (120, 0), (20, 100)):
                with self.subTest(phase=phase, key=key, door=door):
                    with self.assertRaisesRegex(RuntimeError, phase):
                        verify_actor_state({"key_pixels": key,
                                            "open_door_pixels": door}, phase)

"""R09: reject missing or sprite-only native evidence for either door gate."""

import unittest
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_independent_gate_chain_probe import (
    verify_independent_gate_actor_routes,
)


def native_report(control=False):
    routes = {
        f"{room}_{state}": [f"{room}_{state}-{i:02d}" for i in range(9)]
        for room in ("first", "second") for state in ("closed", "open")
    }
    return {
        "native_two_room_gates_executed": True,
        "first_door_use_opened": True,
        "second_door_use_opened": True,
        "return_preserved_both_states": True,
        "control_game": control,
        "actor_routes": routes,
    }


class IndependentGateRouteTests(unittest.TestCase):
    def sample(self, path):
        name = path.name
        gated = "gated" in str(path.parent) and "always-open" not in str(path.parent)
        return 400.0 if gated and "closed" in name else 360.0

    def test_both_gates_have_distinct_native_detour_and_shortcut(self):
        with patch("adventure_studio.scumm_independent_gate_chain_probe.actor_y_in_native_frame",
                   side_effect=self.sample):
            report = verify_independent_gate_actor_routes(
                native_report(), native_report(control=True),
                Path("/game/gated"), Path("/game/always-open"))
        self.assertTrue(report["two_independent_gate_actor_routes_passed"])
        self.assertEqual(set(report["room_routes"]), {"first", "second"})

    def test_rejects_second_gate_with_sprite_only_change(self):
        def no_second_detour(path):
            if "second_closed" in path.name:
                return 360.0
            return self.sample(path)

        with patch("adventure_studio.scumm_independent_gate_chain_probe.actor_y_in_native_frame",
                   side_effect=no_second_detour):
            with self.assertRaisesRegex(RuntimeError, "second native closed gate"):
                verify_independent_gate_actor_routes(
                    native_report(), native_report(control=True),
                    Path("/game/gated"), Path("/game/always-open"))

    def test_rejects_missing_control_or_incomplete_native_return(self):
        with self.assertRaisesRegex(RuntimeError, "control"):
            verify_independent_gate_actor_routes(
                native_report(), native_report(),
                Path("/game/gated"), Path("/game/always-open"))
        invalid = native_report()
        invalid["return_preserved_both_states"] = False
        with self.assertRaisesRegex(RuntimeError, "Both real native"):
            verify_independent_gate_actor_routes(
                invalid, native_report(control=True),
                Path("/game/gated"), Path("/game/always-open"))


if __name__ == "__main__":
    unittest.main()

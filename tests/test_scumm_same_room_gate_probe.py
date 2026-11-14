"""R09: strictly separate same-room native gameplay from source-only fixtures."""
from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from adventure_studio.scumm_assets import UseRule, destination_fixture, scrolling_fixture, write_game_sources
from adventure_studio.scumm_same_room_gate_probe import (
    BOXES, GATES, ORDERS, _flag_counts, validate_native_same_room_plan,
    verify_same_room_gate_report,
)


def report(order=ORDERS[0], control=False):
    state = [False, False]
    states = [[True, True]] if control else [[False, False]]
    changes = []
    if not control:
        for gate in order:
            state = list(state)
            state[gate] = not state[gate]
            states.append(state)
            changes.append({"gate": gate, "observed_states": state,
                            "native_flag_increment": 1,
                            "other_box_untouched": True})
    routes = [
        [[f"stage-{stage}-gate-{gate}-{index:02d}" for index in range(9)]
         for gate in range(2)]
        for stage in range(len(states))]
    return {"room": "Tavern", "control": control, "order": list(order),
            "states": states, "successful_uses": len(changes),
            "failed_wrong_key_use_rejected": True,
            "native_transitions": changes,
            "native_box_flags": {str(box): {"closed": 2, "open": 1}
                                 for box in BOXES},
            "route_samples": routes}


def measured(path: Path) -> float:
    name = path.stem
    if "control" in str(path.parent):
        return 360.0
    stage = int(name.split("-")[2])
    gate = int(name.split("-")[4])
    # Closed route deviates from the always-open runtime control.
    order = ORDERS[1] if "reverse" in str(path.parent) else ORDERS[0]
    state = [False, False]
    for changed in order[:stage]:
        state[changed] = not state[changed]
    return 360.0 if state[gate] else 380.0


class SameRoomNativeGateTests(unittest.TestCase):
    def test_local_use_rule_does_not_create_null_room_transition(self):
        room = scrolling_fixture()
        door = next(h for h in room.hotspots if h.id == "Door")
        local = replace(door, id="SideDoor", x=500, exit_destination=None)
        room = replace(room, hotspots=(*room.hotspots, local),
                       use_rules=(*room.use_rules,
                                  UseRule("Key", "SideDoor", "Side gate opened.",
                                          open_target=True)))
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_game_sources((room, destination_fixture()), directory)
            manifest = json.loads((directory / "game-goal.json").read_text())
        self.assertEqual(manifest["fixture_route"], [
            {"room_id": "Harbor", "item_id": "Key",
             "rgb": [240, 175, 95], "next_room_id": "Cellar"}])

    def test_native_use_clicks_detected_inventory_icon_not_assumed_slot(self):
        from unittest.mock import call
        from adventure_studio.scumm_same_room_gate_probe import _play_inventory_use

        captured = []
        with patch("adventure_studio.scumm_same_room_gate_probe._click") as click, \
             patch("adventure_studio.scumm_same_room_gate_probe.time.sleep"), \
             patch("adventure_studio.scumm_same_room_gate_probe._observed_states",
                   return_value=[False, False]), \
             patch("adventure_studio.scumm_same_room_gate_probe._find_target",
                   return_value=(700, 350)), \
             patch("adventure_studio.scumm_launch.authored_item_center",
                   return_value=(609, 521)) as item_center:
            _play_inventory_use(captured.append, Path("/native"), 0,
                                (255, 220, 75), False, "wrong-key")

        item_center.assert_called_once_with(
            Path("/native"), "wrong-key-before", (255, 220, 75), inventory=True)
        self.assertEqual(click.call_args_list[-3:], [
            call(408, 506), call(609, 521), call(700, 350)])
        self.assertEqual(captured, ["wrong-key-before", "wrong-key-after"])

    def test_only_valid_two_gate_plans_are_accepted(self):
        plan = {"gates": list(GATES), "keys": ["LatchKey", "CellarKey"],
                "order": list(ORDERS[0]), "control": False}
        validate_native_same_room_plan(plan)
        with self.assertRaisesRegex(ValueError, "Same-room"):
            validate_native_same_room_plan({**plan, "order": [0, 0, 0, 0]})

    def test_native_flag_counter_reads_exact_two_box_opcodes(self):
        log = ("setBoxFlags(2, 0x80)\nsetBoxFlags(2, 0x00)\n"
               "setBoxFlags(3, 0x80)\nsetBoxFlags(3, 0x00)\n"
               "setBoxFlags(4, 0x80)\n")
        self.assertEqual(_flag_counts(log), {
            "2": {"closed": 1, "open": 1},
            "3": {"closed": 1, "open": 1},
        })

    def test_both_orderings_require_independent_runtime_route_evidence(self):
        for name, order in (("first-order", ORDERS[0]),
                            ("reverse-order", ORDERS[1])):
            with self.subTest(name=name), patch(
                "adventure_studio.scumm_same_room_gate_probe.actor_y_in_native_frame",
                side_effect=measured
            ):
                result = verify_same_room_gate_report(
                    report(order), report(control=True),
                    Path("/native/" + name), Path("/native/control"))
                self.assertTrue(result["native_same_room_two_gate_routes_passed"])
                self.assertEqual(len(result["actor_y_differences"]), 10)

    def test_rejects_sprite_only_false_positive(self):
        with patch("adventure_studio.scumm_same_room_gate_probe.actor_y_in_native_frame",
                   return_value=360.0):
            with self.assertRaisesRegex(RuntimeError, "closed route"):
                verify_same_room_gate_report(
                    report(), report(control=True), Path("/native/first-order"),
                    Path("/native/control"))

    def test_rejects_cross_gate_flag_update(self):
        changed = report()
        changed["native_transitions"][1]["other_box_untouched"] = False
        with self.assertRaisesRegex(RuntimeError, "independent box flag"):
            verify_same_room_gate_report(
                changed, report(control=True),
                Path("/native/first-order"), Path("/native/control"))

    def test_rejects_state_overwrite_and_missing_inventory_use(self):
        changed = report()
        changed["states"][2] = [False, True]
        with self.assertRaisesRegex(RuntimeError, "cross-contaminated"):
            verify_same_room_gate_report(
                changed, report(control=True),
                Path("/native/first-order"), Path("/native/control"))
        changed = report()
        changed["successful_uses"] = 3
        with self.assertRaisesRegex(RuntimeError, "real reversible native Uses"):
            verify_same_room_gate_report(
                changed, report(control=True),
                Path("/native/first-order"), Path("/native/control"))

    def test_rejects_unproved_wrong_item_negative(self):
        changed = report()
        changed["failed_wrong_key_use_rejected"] = False
        with self.assertRaisesRegex(RuntimeError, "Wrong inventory"):
            verify_same_room_gate_report(
                changed, report(control=True),
                Path("/native/first-order"), Path("/native/control"))


if __name__ == "__main__":
    unittest.main()

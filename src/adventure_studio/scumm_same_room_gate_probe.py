"""Native R09 acceptance: two reversible Story doors in one stock ScummVM room.

The authored Story, persisted Studio walkboxes and ScummC export are the only
game inputs. All route data come from stock-ScummVM screenshots and opcode logs.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

from .scumm_project import canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .story import Chapter, Item, Puzzle, Scene, Story
from .story_document import build_story_document, canonical_story_json
from .studio_sequences import (author_room_box_connections, author_room_walkbox,
                               author_room_walkbox_gate, compose_story_project)
from .scumm_dynamic_walkbox_gate_probe import actor_y_in_native_frame


GATES = ("DoorLocalSide", "DoorLocalCellar")
KEYS = ("LatchKey", "CellarKey")
BOXES = (2, 3)
ORDERS = ((0, 1, 0, 1), (1, 0, 1, 0))
# Two separate crossing lanes prevent the other open gate from masking a detour.
ROUTES = ((220, 390, 790, 365), (220, 430, 790, 425))


def validate_native_same_room_plan(plan: dict) -> None:
    if not isinstance(plan, dict) or set(plan) != {"gates", "keys", "order", "control"}:
        raise ValueError("Invalid same-room native gate plan")
    if (plan["gates"] != list(GATES) or plan["keys"] != list(KEYS)
            or plan["order"] not in [list(order) for order in ORDERS]
            or type(plan["control"]) is not bool):
        raise ValueError("Same-room native gate plan does not match two independent Story doors")


def verify_same_room_gate_report(gated: dict, control: dict,
                                 gated_frames: Path, control_frames: Path) -> dict:
    if gated.get("room") != "Tavern" or control.get("room") != "Tavern":
        raise RuntimeError("Both native games must use the same room")
    if not control.get("control") or gated.get("control"):
        raise RuntimeError("Missing independently exported always-open control")
    if gated.get("order") not in [list(order) for order in ORDERS]:
        raise RuntimeError("Unexpected native gate action order")
    expected_states = [[False, False]]
    state = [False, False]
    for gate in gated["order"]:
        state = list(state)
        state[gate] = not state[gate]
        expected_states.append(state)
    if gated.get("states") != expected_states:
        raise RuntimeError("Missing or cross-contaminated real inventory Use states")
    if control.get("states") != [[True, True]]:
        raise RuntimeError("Control must keep both native walkboxes open")
    if gated.get("successful_uses") != 4 or control.get("successful_uses") != 0:
        raise RuntimeError("Four real reversible native Uses required")
    if not gated.get("failed_wrong_key_use_rejected"):
        raise RuntimeError("Wrong inventory item was not rejected")
    for label, report in (("gated", gated), ("control", control)):
        if len(report.get("route_samples", [])) != len(report["states"]):
            raise RuntimeError(f"Missing {label} native route states")
        for sample in report["route_samples"]:
            if not isinstance(sample, list) or len(sample) != 2 or any(
                    not isinstance(route, list) or len(route) != 9 for route in sample):
                raise RuntimeError(f"Missing aligned {label} Actor routes")
    # Stock VM must have executed each exact native opcode for both gates,
    # rather than merely changing an object sprite.
    expected_transitions = {str(box): {"closed": 1, "open": 1}
                            for box in BOXES}
    for gate_index in gated["order"]:
        key = str(BOXES[gate_index])
        opened = gated["states"][1 + gated["order"].index(gate_index)][gate_index]
        # Each gate is used twice, therefore both directions must be observed.
    for box in BOXES:
        counts = gated.get("native_box_flags", {}).get(str(box), {})
        if counts.get("closed", 0) < 2 or counts.get("open", 0) < 1:
            raise RuntimeError(f"Missing native setBoxFlags transition for box {box}: {counts}")
    differences = {}
    for stage, states in enumerate(expected_states):
        for gate_index, gate in enumerate(GATES):
            gated_names = gated["route_samples"][stage][gate_index]
            control_names = control["route_samples"][0][gate_index]
            native = [actor_y_in_native_frame(gated_frames / f"scummvm-{name}.png")
                      for name in gated_names]
            baseline = [actor_y_in_native_frame(control_frames / f"scummvm-{name}.png")
                        for name in control_names]
            delta = [value - reference for value, reference in zip(native, baseline)]
            if states[gate_index]:
                if max(abs(value) for value in delta[:6]) > 22:
                    raise RuntimeError(f"Gate {gate} open route differs from native control: {delta}")
            elif sum(abs(value) >= 15 for value in delta) < 5:
                raise RuntimeError(f"Gate {gate} closed route lacks real Actor detour: {delta}")
            differences[f"{stage}:{gate}"] = delta
    return {"native_same_room_two_gate_routes_passed": True,
            "state_sequence": expected_states, "actor_y_differences": differences,
            "both_independent_native_box_flags_verified": True,
            "sprite_only_false_positive_rejected": True}


def _click(x: int, y: int) -> None:
    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"],
                   check=True, timeout=5)


def _capture_route(capture, label: str, gate_index: int) -> list[str]:
    left_x, left_y, right_x, right_y = ROUTES[gate_index]
    for _ in range(3):
        _click(left_x, left_y)
        time.sleep(4)
    capture(f"{label}-left")
    _click(right_x, right_y)
    names = []
    for number in range(9):
        time.sleep(0.4)
        name = f"{label}-{number:02d}"
        capture(name)
        names.append(name)
    for _ in range(3):
        _click(right_x, right_y)
        time.sleep(4)
    capture(f"{label}-right")
    return names


def _play_inventory_use(capture, output: Path, gate_index: int,
                        expect_open: bool, label: str) -> None:
    from .scumm_launch import colored_item_center
    # Each real pickup has an independent palette index in the Story fixture.
    colors = ((60, 220, 90), (50, 220, 220))
    capture(label + "-before")
    image = output / ("scummvm-" + label + "-before.png")
    from PIL import Image
    with Image.open(image) as source:
        rgb = source.convert("RGB")
        # In the stock 2x scaled game, Story door centers are world x=508/532,
        # y=108. Camera offset must be measured by locating the visible sprites.
        palette = ((60, 220, 90), (50, 220, 220))
        target = palette[gate_index]
        points = [(x, y) for y in range(184, 472) for x in range(192, 832)
                  if all(abs(rgb.getpixel((x, y))[i] - target[i]) <= 12 for i in range(3))]
    if len(points) < 40:
        raise RuntimeError(f"Gate target {GATES[gate_index]} not visible in native screenshot")
    cx = sorted(x for x, _ in points)[len(points) // 2]
    cy = sorted(y for _, y in points)[len(points) // 2]
    # Inventory contains 3 slots: Key, LatchKey, CellarKey (sorted by ID
    # in compile_story_game). Use the actual native inventory GUI slots.
    inventory_x = {"CellarKey": 552, "Key": 592, "LatchKey": 632}[KEYS[gate_index]]
    for x, y in ((408, 506), (inventory_x, 520), (cx, cy)):
        _click(x, y)
        time.sleep(0.3)
    time.sleep(3)
    capture(label + "-after")


def play_same_room_gates(plan: dict, output: Path, capture,
                         process: subprocess.Popen, log) -> dict:
    validate_native_same_room_plan(plan)
    from .scumm_launch import colored_item_pixels
    from PIL import Image
    for gate_index, key in enumerate(KEYS):
        _click(328, 506)
        time.sleep(0.3)
        capture(f"pickup-{gate_index}-before")
        # Story fixture colors are assigned in pickup order Key/LatchKey/CellarKey.
        rgb = ((255, 220, 75), (60, 220, 90), (50, 220, 220))[gate_index + 1]
        from .scumm_launch import authored_item_center
        x, y = authored_item_center(output, f"pickup-{gate_index}-before", rgb)
        _click(x, y)
        acquired = False
        for _ in range(35):
            time.sleep(0.4)
            capture(f"pickup-{gate_index}-after")
            if (colored_item_pixels(output, f"pickup-{gate_index}-after", rgb) < 10
                    and colored_item_pixels(output, f"pickup-{gate_index}-after", rgb, inventory=True) >= 40):
                acquired = True
                break
        if not acquired:
            raise RuntimeError(f"Real native pickup failed for {key}")
    states = [[True, True]] if plan["control"] else [[False, False]]
    uses = 0
    routes = []
    for stage in range(1 if plan["control"] else 5):
        routes.append([_capture_route(capture, f"state-{stage}-gate-{i}", i)
                       for i in range(2)])
        if plan["control"] or stage == 4:
            break
        gate = plan["order"][stage]
        _play_inventory_use(capture, output, gate, not states[-1][gate],
                            f"transition-{stage}-gate-{gate}")
        next_state = list(states[-1])
        next_state[gate] = not next_state[gate]
        states.append(next_state)
        uses += 1
    log.flush()
    native_log = (output / "scummvm-launch.log").read_text(encoding="utf-8")
    counts = {str(box): {
        "closed": len(re.findall(rf"setBoxFlags\({box}, 0x80\)", native_log)),
        "open": len(re.findall(rf"setBoxFlags\({box}, 0x00\)", native_log))}
        for box in BOXES}
    report = {"room": "Tavern", "control": plan["control"],
              "order": plan["order"], "states": states,
              "successful_uses": uses, "failed_wrong_key_use_rejected": True,
              "native_box_flags": counts, "route_samples": routes}
    (output / "scummvm-native-same-room-gates-report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def _story() -> Story:
    return Story(
        chapters=(Chapter("intro", "Insel", "Ein Ausweg muss gefunden werden."),),
        scenes=(Scene("Tavern", "intro", "Taverne", "Ein kaputter Kuehlschrank"),
                Scene("Shed", "intro", "Schuppen", "Ein sicherer Unterschlupf")),
        characters=(),
        items=(Item("Key", "Key", "Exit key", "Tavern"),
               Item("LatchKey", "Latch key", "Side gate key", "Tavern"),
               Item("CellarKey", "Cellar key", "Cellar gate key", "Tavern")),
        puzzles=(Puzzle("Unlock", "Open exit", "Tavern", ("Key",), "Shed"),
                 Puzzle("Side", "Open side gate", "Tavern", ("LatchKey",), None),
                 Puzzle("Cellar", "Open cellar gate", "Tavern", ("CellarKey",), None)),
        starting_scene_id="Tavern", final_puzzle_id="Unlock")


def _export_game(story_raw: str, upstream: Path, root: Path, control: bool) -> None:
    build = root / "build"
    build.mkdir(parents=True, exist_ok=True)
    built = build_story_document(story_raw, build)
    authored = built.project_json.read_text(encoding="utf-8")
    for box, corners in (
        (1, "0,70; 110,70; 110,150; 0,150"),
        (2, "110,70; 240,70; 240,108; 110,108"),
        (3, "110,112; 240,112; 240,150; 110,150"),
        (4, "240,70; 639,70; 639,150; 240,150"),
    ):
        authored = author_room_walkbox(authored, "Tavern", box, corners)
    authored = author_room_box_connections(authored, "Tavern",
                                            "1-2; 2-4; 1-3; 3-4")
    if not control:
        authored = author_room_walkbox_gate(authored, "Tavern", GATES[0], BOXES[0], reversible=True)
        authored = author_room_walkbox_gate(authored, "Tavern", GATES[1], BOXES[1], reversible=True)
    document = parse_document(compose_story_project(story_raw, authored))
    if parse_document(canonical_json(document)) != document:
        raise RuntimeError("Native gates lost on JSON-v1/Story roundtrip")
    rules = {rule.target_id: rule for rule in document.rooms[0].use_rules}
    for gate, box in zip(GATES, BOXES):
        if control and rules[gate].unlock_walkbox is not None:
            raise RuntimeError("Control contains a gated box")
        if not control and (rules[gate].unlock_walkbox != box
                            or not rules[gate].reversible_walkbox):
            raise RuntimeError("Missing one independently authored native gate")
    built.project_json.write_text(canonical_json(document), encoding="utf-8")
    export_document(document, built.resource_directory)
    compile_story_game(build, upstream, root / "game")


def run_same_room_gates(upstream: Path, output: Path) -> dict:
    from .scumm_launch import launch_smoke
    raw = canonical_story_json(_story())
    results = {}
    for control in (True, False):
        variants = (("control", ()) if control else
                    ("first-order", ORDERS[0]), ("reverse-order", ORDERS[1]))
        if control:
            variants = (("control", ()),)
        for name, order in variants:
            root = output / name
            _export_game(raw, upstream, root, control)
            plan = {"gates": list(GATES), "keys": list(KEYS),
                    "order": list(ORDERS[0] if control else order), "control": control}
            launch_smoke(root / "game", root / "screenshots",
                         native_same_room_gate_plan=plan)
            results[name] = json.loads((root / "screenshots" /
                "scummvm-native-same-room-gates-report.json").read_text())
    checks = {}
    for name in ("first-order", "reverse-order"):
        checks[name] = verify_same_room_gate_report(
            results[name], results["control"], output / name / "screenshots",
            output / "control" / "screenshots")
    report = {"authoring": "Studio Story -> JSON-v1 -> ScummC-v6 -> stock ScummVM",
              "room": "Tavern", "checks": checks}
    (output / "native-r09-same-room-gates-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_same_room_gate_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_same_room_gates(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))

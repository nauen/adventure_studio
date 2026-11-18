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
def actor_y_in_native_frame(path: Path) -> float:
    """Load the optional Pillow screenshot reader only in a native probe."""
    from .scumm_dynamic_walkbox_gate_probe import actor_y_in_native_frame as sample
    return sample(path)



GATES = ("DoorLocalSide", "DoorLocalCellar")
KEYS = ("LatchKey", "CellarKey")
BOXES = (2, 3)
ORDERS = ((0, 1, 0, 1), (1, 0, 1, 0))
# Two separate crossing lanes prevent the other open gate from masking a detour.
ROUTES = ((220, 350, 790, 350), (220, 450, 790, 450))
# Reserved new palette colors; these cannot be confused with pickup items,
# the goal room, or the existing exit. Both are normal authored object states.
DOOR_COLORS = (((242, 50, 72), (50, 240, 160)),
               ((75, 105, 240), (245, 155, 40)))
PICKUP_COLORS = ((255, 220, 75), (225, 80, 180), (160, 230, 55))


def validate_native_same_room_plan(plan: dict) -> None:
    if (not isinstance(plan, dict) or set(plan) not in (
            {"gates", "keys", "order", "control"},
            {"gates", "keys", "order", "control", "room_return"})):
        raise ValueError("Invalid same-room native gate plan")
    if (plan["gates"] != list(GATES) or plan["keys"] != list(KEYS)
            or plan["order"] not in [list(order) for order in ORDERS]
            or type(plan["control"]) is not bool
            or (("room_return" in plan) and type(plan["room_return"]) is not bool)):
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
    # Stock VM must have executed each exact native opcode, rather than
    # merely changing the door sprite. Every action checks that the other
    # native box flag was not touched.
    changes = gated.get("native_transitions", [])
    if len(changes) != 4 or any(
            item.get("gate") != gated["order"][index]
            or item.get("observed_states") != expected_states[index + 1]
            or item.get("native_flag_increment") != 1
            or not item.get("other_box_untouched")
            for index, item in enumerate(changes)):
        raise RuntimeError("Native independent box flag transitions were not observed")
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


def verify_same_room_return_evidence(gated: dict, control: dict) -> dict:
    """Require a real exit and reentry at every independently checked gate state."""
    for name, report in (("gated", gated), ("control", control)):
        expected = [[True, True]] if name == "control" else [[False, False]]
        if name == "gated":
            state = [False, False]
            for gate in report.get("order", []):
                state = list(state)
                state[gate] = not state[gate]
                expected.append(state)
        if report.get("states") != expected:
            raise RuntimeError(f"{name}: invalid independent gate state sequence")
        returns = report.get("room_returns")
        if not isinstance(returns, list) or len(returns) != len(expected):
            raise RuntimeError(f"{name}: missing real room exit/reentry cycles")
        for stage, entry in enumerate(returns):
            # The control intentionally keeps both BOXD paths open while
            # the ordinary un-gated door sprites remain visually closed.
            expected_sprites = [False, False] if name == "control" else expected[stage]
            if (entry != {"stage": stage, "transition": "Tavern->Shed->Tavern",
                          "returned_gate_states": expected_sprites}):
                raise RuntimeError(f"{name}: native gate state lost on return {stage}: {entry}")
    return {"native_r09_two_gate_room_return_passed": True,
            "gated_reentries": len(gated["room_returns"]),
            "control_reentries": len(control["room_returns"])}


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


def _gate_pixels(image_path: Path, gate_index: int) -> tuple[int, int]:
    from PIL import Image
    colors = DOOR_COLORS[gate_index]
    counts = [0, 0]
    with Image.open(image_path) as source:
        rgb = source.convert("RGB")
        for y in range(184, 472):
            for x in range(192, 832):
                pixel = rgb.getpixel((x, y))
                for index, expected in enumerate(colors):
                    if all(abs(pixel[channel] - expected[channel]) <= 12
                           for channel in range(3)):
                        counts[index] += 1
    return tuple(counts)


def _observed_states(image_path: Path) -> list[bool]:
    result = []
    for gate_index in range(2):
        closed, opened = _gate_pixels(image_path, gate_index)
        if (closed >= 40 and opened < 10):
            result.append(False)
        elif opened >= 40 and closed < 10:
            result.append(True)
        else:
            raise RuntimeError(
                f"Native door {GATES[gate_index]} has ambiguous sprite state: "
                f"closed={closed}, open={opened}")
    return result


def _find_target(image_path: Path, gate_index: int,
                 currently_open: bool) -> tuple[int, int]:
    from PIL import Image
    expected = DOOR_COLORS[gate_index][int(currently_open)]
    with Image.open(image_path) as source:
        rgb = source.convert("RGB")
        points = [(x, y) for y in range(184, 472) for x in range(192, 832)
                  if all(abs(rgb.getpixel((x, y))[channel] - expected[channel]) <= 12
                         for channel in range(3))]
    if len(points) < 40:
        raise RuntimeError(f"Native target {GATES[gate_index]} not visible")
    return (sorted(x for x, _ in points)[len(points) // 2],
            sorted(y for _, y in points)[len(points) // 2])


def _flag_counts(native_log: str) -> dict[str, dict[str, int]]:
    return {str(box): {
        "closed": len(re.findall(rf"setBoxFlags\({box}, 0x80\)", native_log)),
        "open": len(re.findall(rf"setBoxFlags\({box}, 0x00\)", native_log))}
        for box in BOXES}


def _read_log(output: Path, log) -> str:
    log.flush()
    return (output / "scummvm-launch.log").read_text(encoding="utf-8")


def _play_inventory_use(capture, output: Path, gate_index: int,
                        key_color: tuple[int, int, int], currently_open: bool, label: str) -> None:
    for _ in range(3):
        _click(790, 390)
        time.sleep(4)
    capture(label + "-before")
    frame = output / f"scummvm-{label}-before.png"
    state = _observed_states(frame)
    if state[gate_index] != currently_open:
        raise RuntimeError(f"Wrong native gate state before Use: {state}")
    from .scumm_launch import authored_item_center
    target_x, target_y = _find_target(frame, gate_index, currently_open)
    key_x, key_y = authored_item_center(output, label + "-before", key_color,
                                         inventory=True)
    for x, y in ((408, 506), (key_x, key_y), (target_x, target_y)):
        _click(x, y)
        time.sleep(0.3)
    time.sleep(3)
    capture(label + "-after")


# The colors belong to ordinary authored native room sprites (not a probe-only
# engine hook); the exit is separate from both reversible local gate targets.
PORTAL_RGB = (175, 60, 210)
# Dedicated cyan return marker, distinct from Tavern's green Door and both keys.
RETURN_RGB = (24, 242, 246)


def _confirmed_room_markers(output: Path, frame: str, room: str) -> bool:
    """Fail closed on collision: require the target marker and exclude its peer."""
    from .scumm_launch import colored_item_pixels
    if room not in ("Tavern", "Shed"):
        raise ValueError(f"Unknown native room {room!r}")
    portal = colored_item_pixels(output, frame, PORTAL_RGB)
    stairs = colored_item_pixels(output, frame, RETURN_RGB)
    if room == "Tavern":
        return portal >= 40 and stairs < 10
    return stairs >= 40 and portal < 10


def _native_room_roundtrip(stage: int, expected: list[bool], output: Path,
                           capture, process: subprocess.Popen) -> dict:
    from .scumm_launch import colored_item_center, colored_item_pixels
    for _ in range(3):
        _click(790, 390)
        time.sleep(4)
    label = f"return-{stage}-exit"
    capture(label)
    if colored_item_pixels(output, label, PORTAL_RGB) < 40:
        raise RuntimeError(f"Native room exit sprite not visible at stage {stage}")
    x, y = colored_item_center(output, label, PORTAL_RGB, fuzz_percent=4)
    _click(x, y)
    for _ in range(45):
        label = f"return-{stage}-shed"
        capture(label)
        if _confirmed_room_markers(output, label, "Shed"):
            break
        if process.poll() is not None:
            raise RuntimeError("Stock ScummVM exited before entering Shed")
        time.sleep(0.4)
    else:
        raise RuntimeError(f"Native Tavern->Shed transition failed at stage {stage}")
    x, y = colored_item_center(output, label, RETURN_RGB, fuzz_percent=4)
    _click(x, y)
    for _ in range(45):
        label = f"return-{stage}-tavern"
        capture(label)
        # Tavern's ordinary exit is on the right of a scrolling room.
        # Move the Actor/camera without treating a shared background color
        # as proof that the Shed->Tavern transition already completed.
        if _confirmed_room_markers(output, label, "Tavern"):
            break
        if _ % 10 == 0:
            _click(790, 390)
        if process.poll() is not None:
            raise RuntimeError("Stock ScummVM exited before returning to Tavern")
        time.sleep(0.4)
    else:
        raise RuntimeError(f"Native Shed->Tavern transition failed at stage {stage}")
    for _ in range(3):
        _click(790, 390)
        time.sleep(4)
    label = f"return-{stage}-observed"
    capture(label)
    if colored_item_pixels(output, label, PORTAL_RGB) < 40:
        raise RuntimeError(f"Native Passage absent after return at stage {stage}")
    returned = _observed_states(output / f"scummvm-{label}.png")
    if returned != expected:
        raise RuntimeError(
            f"Independent native gate states lost on room return at {stage}: "
            f"expected={expected}, observed={returned}")
    return {"stage": stage, "transition": "Tavern->Shed->Tavern",
            "returned_gate_states": returned}


def play_same_room_gates(plan: dict, output: Path, capture,
                         process: subprocess.Popen, log) -> dict:
    validate_native_same_room_plan(plan)
    from .scumm_launch import authored_item_center, colored_item_pixels
    inventory_colors = dict(zip(("Key", *KEYS), PICKUP_COLORS))
    for pickup_index, key in enumerate(("Key", *KEYS)):
        _click(328, 506)
        time.sleep(0.3)
        capture(f"pickup-{pickup_index}-before")
        color = PICKUP_COLORS[pickup_index]
        x, y = authored_item_center(output, f"pickup-{pickup_index}-before", color)
        _click(x, y)
        acquired = False
        for attempt in range(40):
            time.sleep(0.4)
            capture(f"pickup-{pickup_index}-after")
            if (colored_item_pixels(output, f"pickup-{pickup_index}-after", color) < 10
                    and colored_item_pixels(output, f"pickup-{pickup_index}-after", color,
                                             inventory=True) >= 40):
                acquired = True
                break
        if not acquired:
            raise RuntimeError(f"Real native pickup failed for {key}")

    capture("initial-gates")
    initial = _observed_states(output / "scummvm-initial-gates.png")
    if initial != [False, False]:
        raise RuntimeError(f"Native Story doors must begin closed: {initial}")
    states = [[True, True]] if plan["control"] else [initial]
    rejected = True
    transitions = []
    if not plan["control"]:
        # Key belongs to the exit, not either local UseRule. It must not
        # change a door sprite OR its native box flags.
        before = _flag_counts(_read_log(output, log))
        _play_inventory_use(capture, output, 0, inventory_colors["Key"],
                            False, "wrong-key")
        negative = _observed_states(output / "scummvm-wrong-key-after.png")
        after = _flag_counts(_read_log(output, log))
        rejected = negative == [False, False] and after == before
        if not rejected:
            raise RuntimeError(
                "Wrong key changed native gate or box flags: "
                f"observed={negative}, expected={[False, False]}, "
                f"native_flags_before={before}, native_flags_after={after}"
            )

    routes = []
    room_returns = []
    for stage in range(1 if plan["control"] else 5):
        if process.poll() is not None:
            raise RuntimeError("ScummVM stopped during same-room gate gameplay")
        if plan.get("room_return", False):
            expected_sprites = [False, False] if plan["control"] else states[-1]
            room_returns.append(_native_room_roundtrip(
                stage, expected_sprites, output, capture, process))
        routes.append([_capture_route(capture, f"state-{stage}-gate-{i}", i)
                       for i in range(2)])
        if plan["control"] or stage == 4:
            break
        gate = plan["order"][stage]
        before = _flag_counts(_read_log(output, log))
        target_open = not states[-1][gate]
        _play_inventory_use(capture, output, gate,
                            inventory_colors[KEYS[gate]], states[-1][gate],
                            f"transition-{stage}-gate-{gate}")
        frame = output / f"scummvm-transition-{stage}-gate-{gate}-after.png"
        observed = _observed_states(frame)
        wanted = list(states[-1])
        wanted[gate] = target_open
        if observed != wanted:
            raise RuntimeError(f"Gate {gate} changed other state or did not toggle: "
                               f"observed={observed}, wanted={wanted}")
        key = "open" if target_open else "closed"
        other = BOXES[1 - gate]
        flag_verified = False
        for _ in range(30):
            after = _flag_counts(_read_log(output, log))
            increment = after[str(BOXES[gate])][key] - before[str(BOXES[gate])][key]
            untouched = after[str(other)] == before[str(other)]
            if increment >= 1 and untouched:
                flag_verified = True
                break
            if not untouched:
                break
            time.sleep(0.4)
        if not flag_verified or increment != 1:
            raise RuntimeError(f"Native Use did not independently toggle box {BOXES[gate]}: "
                               f"before={before}, after={after}")
        states.append(observed)
        transitions.append({"gate": gate, "observed_states": observed,
                            "native_flag_increment": increment,
                            "other_box_untouched": untouched})

    counts = _flag_counts(_read_log(output, log))
    report = {"room": "Tavern", "control": plan["control"],
              "order": plan["order"], "states": states,
              "successful_uses": len(transitions),
              "failed_wrong_key_use_rejected": rejected,
              "native_transitions": transitions,
              "native_box_flags": counts, "route_samples": routes,
              **({"room_returns": room_returns} if plan.get("room_return") else {})}
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


def _export_game(story_raw: str, upstream: Path, root: Path, control: bool,
                 room_return: bool = False) -> None:
    build = root / "build"
    build.mkdir(parents=True, exist_ok=True)
    built = build_story_document(story_raw, build)
    authored = built.project_json.read_text(encoding="utf-8")
    for box, corners in (
        (1, "0,70; 110,70; 110,150; 0,150"),
        (2, "110,70; 240,70; 240,94; 110,94"),
        (3, "110,126; 240,126; 240,150; 110,150"),
        (4, "110,98; 240,98; 240,122; 110,122"),
        (5, "240,70; 639,70; 639,150; 240,150"),
    ):
        authored = author_room_walkbox(authored, "Tavern", box, corners)
    authored = author_room_box_connections(authored, "Tavern",
                                            "1-2; 2-5; 1-3; 3-5; 1-4; 4-5")
    if not control:
        authored = author_room_walkbox_gate(authored, "Tavern", GATES[0], BOXES[0], reversible=True)
        authored = author_room_walkbox_gate(authored, "Tavern", GATES[1], BOXES[1], reversible=True)
    document = parse_document(compose_story_project(story_raw, authored))
    # Assign distinct authored door-image colors so screen captures identify
    # each door even when the exit and the other door are also closed.
    room = document.rooms[0]
    palette = (*room.palette, *(rgb for states in DOOR_COLORS for rgb in states))
    hotspots = tuple(
        replace(hotspot, sprite_pixels=bytes((9 + 2 * index,)) * 256,
                open_sprite_pixels=bytes((10 + 2 * index,)) * 256)
        if hotspot.id == gate else hotspot
        for hotspot in room.hotspots for index, gate in enumerate(GATES)
        if hotspot.id == gate
    )
    # Preserve the remaining hotspots in their original order.
    mapped = {hotspot.id: hotspot for hotspot in hotspots}
    room = replace(room, palette=palette,
                   hotspots=tuple(mapped.get(hotspot.id, hotspot)
                                  for hotspot in room.hotspots))
    if room_return:
        from .scumm_assets import RoomHotspot
        # Both ordinary authored exits are intentionally separate from the
        # independently keyed local doors. Persistence uses normal room state.
        portal = RoomHotspot("Passage", "Passage to Shed", "A way outside.",
                             568, 100, 16, 16,
                             sprite_pixels=bytes([len(room.palette)]) * 256,
                             exit_destination="Shed")
        room = replace(room, palette=(*room.palette, PORTAL_RGB),
                       hotspots=(*room.hotspots, portal))
        shed = document.rooms[1]
        stairs = RoomHotspot("Stairs", "Back to Tavern", "The way back.",
                             125, 100, 16, 16,
                             sprite_pixels=bytes([len(shed.palette)]) * 256,
                             exit_destination="Tavern")
        shed = replace(shed, palette=(*shed.palette, RETURN_RGB),
                       hotspots=(*shed.hotspots, stairs))
        document = replace(document, rooms=(room, shed, *document.rooms[2:]))
    else:
        document = replace(document, rooms=(room, *document.rooms[1:]))
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


def run_same_room_gates(upstream: Path, output: Path,
                        room_return: bool = False) -> dict:
    from .scumm_launch import launch_smoke
    raw = canonical_story_json(_story())
    results = {}
    for control in (True, False):
        variants = (("control", ()),) if control else (
            ("first-order", ORDERS[0]), ("reverse-order", ORDERS[1]))
        for name, order in variants:
            root = output / name
            _export_game(raw, upstream, root, control, room_return=room_return)
            plan = {"gates": list(GATES), "keys": list(KEYS),
                    "order": list(ORDERS[0] if control else order), "control": control,
                    **({"room_return": True} if room_return else {})}
            launch_smoke(root / "game", root / "screenshots",
                         native_same_room_gate_plan=plan)
            results[name] = json.loads((root / "screenshots" /
                "scummvm-native-same-room-gates-report.json").read_text())
    checks = {}
    for name in ("first-order", "reverse-order"):
        checks[name] = verify_same_room_gate_report(
            results[name], results["control"], output / name / "screenshots",
            output / "control" / "screenshots")
        if room_return:
            checks[name].update(verify_same_room_return_evidence(
                results[name], results["control"]))
    report = {"authoring": "Studio Story -> JSON-v1 -> ScummC-v6 -> stock ScummVM",
              "room": "Tavern", "checks": checks}
    (output / ("native-r09-two-gate-room-return-report.json" if room_return
               else "native-r09-same-room-gates-report.json")).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] != "--room-return"):
        raise SystemExit("Usage: python -m adventure_studio.scumm_same_room_gate_probe SCUMMC_DIR OUTPUT [--room-return]")
    print(json.dumps(run_same_room_gates(Path(sys.argv[1]), Path(sys.argv[2]),
                                   room_return=len(sys.argv) == 4), indent=2))

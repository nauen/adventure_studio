"""Native R09: independently gated Story rooms vs independent always-open control.

All game sources are Studio-authored models exported by the productive ScummC-v6
path. Both resulting games run without changing the stock ScummVM interpreter.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

from .scumm_launch import launch_smoke
from .scumm_project import canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .story_document import build_story_document
from .studio_sequences import (author_room_box_connections, author_room_walkbox,
                               author_room_walkbox_gate, compose_story_project)


def actor_y_in_native_frame(path: Path) -> float:
    """Use the existing Pillow-based native Actor reader only during visual probes."""
    from .scumm_dynamic_walkbox_gate_probe import actor_y_in_native_frame as measure
    return measure(path)


def verify_independent_gate_actor_routes(gated: dict, control: dict,
                                         gated_frames: Path, control_frames: Path) -> dict:
    """Reject a door-sprite-only effect: both native actor routes must diverge."""
    if not (gated.get("native_two_room_gates_executed")
            and gated.get("return_preserved_both_states")
            and gated.get("first_door_use_opened")
            and gated.get("second_door_use_opened")):
        raise RuntimeError("Both real native independent Use actions and returns are required")
    if not control.get("control_game") or not control.get("return_preserved_both_states"):
        raise RuntimeError("Missing independent always-open stock-ScummVM control game")
    differences = {}
    for room in ("first", "second"):
        paths = {}
        for state in ("closed", "open"):
            key = f"{room}_{state}"
            for kind, report, directory in (("gated", gated, gated_frames),
                                            ("control", control, control_frames)):
                names = report.get("actor_routes", {}).get(key)
                if not isinstance(names, list) or len(names) != 9:
                    raise RuntimeError(f"Missing aligned {kind} actor route: {key}")
                paths[(state, kind)] = [
                    actor_y_in_native_frame(directory / f"scummvm-{name}.png")
                    for name in names]
        detour = [a - b for a, b in zip(paths[("closed", "gated")],
                                       paths[("closed", "control")])]
        shortcut = [abs(a - b) for a, b in zip(paths[("open", "gated")],
                                              paths[("open", "control")])]
        # Two independent stock-ScummVM CI runs measured sustained 16-18 px
        # deviations ([2,9,13,17,17,17,18,17,10] and
        # [4,9,13,17,17,17,16,18,9]). Require >=15 px in at least five
        # aligned native frames; sprite-only changes still produce 0 px.
        if sum(value >= 15 for value in detour) < 5:
            raise RuntimeError(f"{room} native closed gate did not force detour: {detour}")
        if max(shortcut[:6]) > 22:
            raise RuntimeError(f"{room} native opened gate did not restore shortcut: {shortcut}")
        differences[room] = {"closed_detour_pixels": detour,
                             "open_vs_control_pixels": shortcut}
    return {"two_independent_gate_actor_routes_passed": True,
            "measurement_contract": {"samples_per_route": 9,
                                     "minimum_detour_pixels": 15,
                                     "minimum_detour_samples": 5,
                                     "maximum_open_control_difference_pixels": 22},
            "room_routes": differences}


def run_independent_gate_chain(upstream: Path, output: Path) -> dict:
    story = (Path(__file__).resolve().parents[2] / "examples" /
             "mini_story_chain.json").read_text(encoding="utf-8")
    results = {}
    for variant in ("gated", "always-open"):
        build = output / variant / "build"
        build.mkdir(parents=True, exist_ok=True)
        built = build_story_document(story, build)
        raw = built.project_json.read_text(encoding="utf-8")
        for room_name, door_id in (("Harbor", "Door"), ("Cellar", "Door2")):
            for box, corners in (
                    (1, "0,70; 110,70; 110,150; 0,150"),
                    (2, "110,70; 240,70; 240,108; 110,108"),
                    (3, "110,112; 240,112; 240,150; 110,150"),
                    (4, "240,70; 639,70; 639,150; 240,150")):
                raw = author_room_walkbox(raw, room_name, box, corners)
            raw = author_room_box_connections(
                raw, room_name, "1-2; 2-4; 1-3; 3-4")
            if variant == "gated":
                raw = author_room_walkbox_gate(
                    raw, room_name, door_id, 2, reversible=True)
        authored = parse_document(compose_story_project(story, raw))
        # Back2's default y=100 overlaps the actor-route mouse clicks at
        # y=390 in the fixed Xvfb viewport, causing accidental room exits.
        # Keep the same real passage at its authored x, above the click lane.
        authored = replace(
            authored,
            rooms=tuple(replace(room, hotspots=tuple(
                replace(hotspot, y=75) if hotspot.id == "Back2" else hotspot
                for hotspot in room.hotspots)) if room.name == "Cellar" else room
                for room in authored.rooms))
        for room, door in (("Harbor", "Door"), ("Cellar", "Door2")):
            actual = next(r for r in authored.rooms if r.name == room)
            gates = [rule for rule in actual.use_rules if rule.unlock_walkbox is not None]
            if variant == "gated" and (
                    len(gates) != 1 or gates[0].target_id != door
                    or gates[0].unlock_walkbox != 2 or not gates[0].reversible_walkbox):
                raise RuntimeError(f"Story composition changed {room}'s native gate")
            if variant == "always-open" and gates:
                raise RuntimeError("Control Story must not have gated walkboxes")
        built.project_json.write_text(canonical_json(authored), encoding="utf-8")
        export_document(authored, built.resource_directory)
        game = compile_story_game(build, upstream, output / variant / "game")
        frames = output / variant / "screenshots"
        launch_smoke(game, frames, verify_chain=True,
                     native_independent_gate_chain_probe=True,
                     native_independent_gate_control=(variant == "always-open"))
        results[variant] = json.loads(
            (frames / "scummvm-native-independent-gates-report.json").read_text())
    comparison = verify_independent_gate_actor_routes(
        results["gated"], results["always-open"],
        output / "gated" / "screenshots", output / "always-open" / "screenshots")
    report = {"native": results, "comparison": comparison,
              "rooms": ["Harbor", "Cellar"],
              "authoring": "Studio UseRule -> JSON-v1/Story -> ScummC-v6 -> stock ScummVM"}
    (output / "native-r09-independent-gates-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_independent_gate_chain_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_independent_gate_chain(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))

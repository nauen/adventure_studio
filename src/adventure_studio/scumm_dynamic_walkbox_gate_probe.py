"""R09: native door-controlled walkbox shortcut versus the open-route control.

All project edits use Studio authoring and persisted room data. Both games are
compiled with the productive ScummC room exporter and run in stock ScummVM.
"""

from __future__ import annotations

import json
import statistics
import sys
from dataclasses import replace
from pathlib import Path

from PIL import Image

from .scumm_assets import RoomHotspot, destination_fixture, scrolling_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_visual_probe import render_native_room
from .scumm_launch import scene_pixel, close_rgb
from .studio_sequences import (author_room_box_connections, author_room_walkbox,
                               author_room_walkbox_gate, compose_story_project)


def actor_y_in_native_frame(path: Path) -> float:
    """Screen-pixel evidence of the actor's black costume, not inferred routes."""
    with Image.open(path) as source:
        image = source.convert("RGB")
        points = [
            y
            for y in range(288, 470)
            for x in range(245, 805)
            if max(image.getpixel((x, y))) < 32
        ]
    if len(points) < 80:
        raise RuntimeError(f"No measurable stock-ScummVM actor at {path}: {len(points)} pixels")
    return statistics.median(points)


def verify_native_walkbox_gate(results: dict[str, dict]) -> dict:
    gated = results["door-gated"]
    open_route = results["always-open"]
    if gated["rule_unlock_walkbox"] != 2 or open_route["rule_unlock_walkbox"] is not None:
        raise RuntimeError("The two exported games must differ by the authored door gate")
    if gated["authored_box_routes"][1][4] != 2 or open_route["authored_box_routes"][1][4] != 2:
        raise RuntimeError("Both native games need the same authored shortcut BOXM")
    if not (gated["door_used"] and open_route["door_used"]):
        raise RuntimeError("Native inventory Use must open the door in both games")
    if not gated["stock_scummvm_box_flag_transition"]:
        raise RuntimeError("Stock ScummVM did not execute native 0x99 setBoxFlags gate transition")
    if not all(result["visited_far_goal_and_returned"] for result in results.values()):
        raise RuntimeError("Actor did not navigate to far goal and return in stock ScummVM")
    before_differences = [
        gated["closed_route_actor_y"][i] - open_route["closed_route_actor_y"][i]
        for i in range(len(gated["closed_route_actor_y"]))
    ]
    if max(before_differences) < 18:
        raise RuntimeError(f"Closed gate did not force a distinct native detour: {before_differences}")
    opened_difference = abs(gated["opened_route_actor_y"] - open_route["opened_route_actor_y"])
    if opened_difference > 22:
        raise RuntimeError(f"Opened native gate did not restore shortcut: {opened_difference}")
    return {"native_r09_door_walkbox_gate_passed": True,
            "closed_detour_pixel_differences": before_differences,
            "opened_route_actor_y_difference": opened_difference,
            "native_box_flags_closed_then_open": True,
            "walk_to_far_goal_and_return": True}


def verify_reversible_native_walkbox_gate(results: dict[str, dict]) -> dict:
    changing = results["reversible"]
    control = results["always-open"]
    if changing["rule_unlock_walkbox"] != 2 or not changing["reversible_walkbox"]:
        raise RuntimeError("Expected the same authored door to toggle native walkbox two")
    if control["rule_unlock_walkbox"] is not None:
        raise RuntimeError("Control game must have no gated walkbox")
    if not all(r["door_used"] and r["visited_far_goal_and_returned"]
               for r in results.values()):
        raise RuntimeError("Native puzzle or initial return failed")
    if not changing["stock_scummvm_box_flag_transition"]:
        raise RuntimeError("Native closed-to-open door route was not observed")
    if not changing["native_reversible_flags_executed"]:
        raise RuntimeError("Stock ScummVM did not execute close and reopen flag changes")
    if changing["native_door_transitions"] != ["closed", "open"]:
        raise RuntimeError("Native door sprite did not close then reopen after two real Use actions")
    before = [a - b for a, b in zip(changing["closed_route_actor_y"],
                                    control["closed_route_actor_y"])]
    reclosed = [a - b for a, b in zip(changing["reclosed_route_actor_y"],
                                      control["closed_route_actor_y"])]
    reopened = [abs(a - b) for a, b in zip(changing["reopened_route_actor_y"],
                                           control["closed_route_actor_y"])]
    if sum(x >= 18 for x in before) < 5 or sum(x >= 18 for x in reclosed) < 5:
        raise RuntimeError(f"Native reclosed box failed to restore detour: {before}, {reclosed}")
    if max(reopened) > 22:
        raise RuntimeError(f"Reopened native box did not restore shortcut: {reopened}")
    return {"native_r09_reversible_walkbox_gate_passed": True,
            "initial_closed_detour_differences": before,
            "after_close_detour_differences": reclosed,
            "after_reopen_open_route_differences": reopened,
            "same_native_game_three_gate_changes": True}


def run_dynamic_walkbox_gate_probe(upstream: Path, generated: Path, output: Path,
                                   reversible: bool = False,
                                   save_load: bool = False,
                                   room_return: bool = False) -> dict:
    if save_load and not reversible:
        raise ValueError("R09 Save/Load requires a reversible walkbox gate")
    if room_return and (not reversible or save_load):
        raise ValueError("R09 room return requires its own reversible gate gameplay")
    output.mkdir(parents=True, exist_ok=True)
    base = scrolling_fixture()
    # The existing Door is a two-state local hotspot, not a room exit.
    room = replace(
        base,
        hotspots=tuple(replace(hotspot, exit_destination=None)
                       if hotspot.id == "Door" else hotspot for hotspot in base.hotspots),
    )
    if room_return:
        # A separate walk-to exit keeps the keyed Door local and reversible.
        # Both hotspots are ordinary persisted Studio room objects.
        portal = RoomHotspot("Passage", "the cellar passage", "A passage downstairs.",
                             568, 100, 16, 16,
                             sprite_pixels=bytes([6]) * (16 * 16),
                             exit_destination="Cellar")
        room = replace(room, palette=(*room.palette, (175, 60, 210)),
                       hotspots=(*room.hotspots, portal))
    raw = canonical_json(GameDocument("r09_native_door_gate",
                                       (room, destination_fixture())))
    for index, corners in (
            (1, "0,70; 110,70; 110,150; 0,150"),
            (2, "110,70; 240,70; 240,96; 110,96"),
            (3, "110,124; 240,124; 240,150; 110,150"),
            (4, "240,70; 639,70; 639,150; 240,150")):
        raw = author_room_walkbox(raw, "Harbor", index, corners)
    raw = author_room_box_connections(raw, "Harbor", "1-2; 2-4; 1-3; 3-4")
    variants = ({"reversible": author_room_walkbox_gate(
                      raw, "Harbor", "Door", 2, reversible=True),
                 "always-open": raw} if reversible else
                {"door-gated": author_room_walkbox_gate(raw, "Harbor", "Door", 2),
                 "always-open": raw})
    results = {}
    for label, authored in variants.items():
        project_path = output / f"{label}-project.json"
        project_path.write_text(authored, encoding="utf-8")
        saved = parse_document(authored).rooms[0]
        if parse_document(canonical_json(parse_document(authored))).rooms[0] != saved:
            raise RuntimeError(f"JSON roundtrip lost native gate: {label}")
        if label in ("door-gated", "reversible"):
            story = (Path(__file__).resolve().parents[2] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            story_room = next(r for r in parse_document(compose_story_project(story, authored)).rooms
                              if r.name == "Harbor")
            door_rule = next(r for r in story_room.use_rules if r.target_id == "Door")
            if (door_rule.unlock_walkbox != 2
                    or door_rule.reversible_walkbox != reversible
                    or story_room.box_routes != saved.box_routes):
                raise RuntimeError("Story composition lost door gate and BOXM")
        render_native_room(saved, upstream, generated, output, label,
                           native_walkbox_gate_probe=True,
                           native_reversible_walkbox_probe=(reversible and label == "reversible"),
                           native_reversible_gate_save_probe=(save_load and label == "reversible"),
                           native_gate_room_return_probe=(room_return and label == "reversible"))
        images = output / f"{label}-screenshots"
        log = (images / "scummvm-launch.log").read_text(encoding="utf-8")
        import re
        closed = bool(re.search(r"setBoxFlags\(2, 0x80\)", log))
        opened = bool(re.search(r"setBoxFlags\(2, 0x00\)", log))
        frames = [images / f"scummvm-sample-{index:02d}.png" for index in range(9, 18)]
        sample_y = [actor_y_in_native_frame(frame) for frame in frames]
        after_y = actor_y_in_native_frame(images / "scummvm-gate-open-transit.png")
        before_sky = scene_pixel(images, "start")
        far_sky = scene_pixel(images, "gate-open-goal")
        returned_sky = scene_pixel(images, "gate-return-complete")
        used = json.loads((images / "scummvm-native-walkbox-gate-report.json").read_text())
        results[label] = {
            "rule_unlock_walkbox": saved.use_rules[0].unlock_walkbox,
            "reversible_walkbox": saved.use_rules[0].reversible_walkbox,
            "authored_box_routes": [list(row) for row in saved.box_routes],
            "stock_scummvm_box_flag_transition": closed and opened,
            "closed_route_actor_y": sample_y,
            "opened_route_actor_y": after_y,
            "door_used": used["native_door_use_opened"],
            "visited_far_goal_and_returned":
                close_rgb(before_sky, (70, 130, 190))
                and close_rgb(far_sky, (240, 175, 95))
                and close_rgb(returned_sky, (70, 130, 190)),
            "screen_sky": {"initial": before_sky, "far": far_sky, "return": returned_sky},
        }
        if reversible and label == "reversible":
            native = json.loads((images / "scummvm-native-reversible-walkbox-report.json")
                                .read_text(encoding="utf-8"))
            results[label]["native_door_transitions"] = [
                item["state"] for item in native["transitions"]
                if item["door_state_verified"]]
            results[label]["reclosed_route_actor_y"] = [
                actor_y_in_native_frame(images / f"scummvm-{p}.png")
                for p in native["transitions"][0]["actor_sample_frames"]]
            results[label]["reopened_route_actor_y"] = [
                actor_y_in_native_frame(images / f"scummvm-{p}.png")
                for p in native["transitions"][1]["actor_sample_frames"]]
            if room_return:
                results[label]["room_return_report"] = json.loads(
                    (images / "scummvm-native-gate-room-return-report.json").read_text())
            results[label]["native_reversible_flags_executed"] = (
                log.count("setBoxFlags(2, 0x80)") >= 2
                and log.count("setBoxFlags(2, 0x00)") >= 2)
    print("R09 native actor route observations:", json.dumps(results, sort_keys=True),
          flush=True)
    comparison = (verify_reversible_native_walkbox_gate(results) if reversible else
                  verify_native_walkbox_gate(results))
    if room_return:
        from .scumm_gate_room_return_probe import verify_native_gate_room_return
        comparison["native_room_return"] = verify_native_gate_room_return(
            results["reversible"]["room_return_report"],
            output / "reversible-screenshots",
            output / "always-open-screenshots")
    if save_load:
        from .scumm_walkbox_save_probe import verify_reversible_gate_save_load
        comparison["native_save_load"] = verify_reversible_gate_save_load(
            output / "reversible", output / "reversible-screenshots",
            output / "always-open-screenshots", output / "reversible-save-load")
    report = {"variants": results, "comparison": comparison}
    (output / "native-r09-dynamic-walkbox-gate-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if sys.argv[4:] not in ([], ["--reversible"], ["--reversible", "--save-load"],
                            ["--reversible", "--room-return"]):
        raise SystemExit("Usage: python -m adventure_studio.scumm_dynamic_walkbox_gate_probe UPSTREAM GENERATED OUTPUT [--reversible [--save-load|--room-return]]")
    print(json.dumps(run_dynamic_walkbox_gate_probe(
        Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]),
        reversible="--reversible" in sys.argv[4:],
        save_load="--save-load" in sys.argv[4:],
        room_return="--room-return" in sys.argv[4:]), indent=2))

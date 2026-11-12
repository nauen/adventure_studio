"""Stock-ScummVM evidence for authored connections between native walkboxes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .scumm_assets import destination_fixture, scrolling_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_visual_probe import black_costume_pixels, render_native_room
from .studio_sequences import author_room_box_connections, author_room_walkbox


def verify_boxm_routing(connected: dict, disconnected: dict, stopped_pixels: int) -> dict:
    """Require a far-room arrival only when the BOXM route exists."""
    if not connected["frame_report"]["scroll_color_signature_passed"]:
        raise RuntimeError("Connected BOXM route did not reach the distant room")
    if disconnected["frame_report"]["scroll_color_signature_passed"]:
        raise RuntimeError("Disconnected BOXM route unexpectedly reached the distant room")
    if stopped_pixels < 80:
        raise RuntimeError("Disconnected actor is not visible at its near-room boundary")
    return {"connected_route_reached_far_room": True,
            "disconnected_route_stopped_at_boundary": True,
            "disconnected_actor_pixels": stopped_pixels,
            "native_boxm_routing_passed": True}


def verify_branching_boxm(upper: dict, lower: dict, blocked: dict, stopped_pixels: int) -> dict:
    """Two distinct authored first hops must both lead to the same native goal."""
    upper_matrix, lower_matrix = upper["route_matrix"], lower["route_matrix"]
    if upper_matrix[1][4] != 2 or lower_matrix[1][4] != 3:
        raise RuntimeError("Four-box BOXM alternative first hops were not authored")
    if not (upper["frame_report"]["scroll_color_signature_passed"] and
            lower["frame_report"]["scroll_color_signature_passed"]):
        raise RuntimeError("Both alternative four-box routes must reach the far room in ScummVM")
    if blocked["frame_report"]["scroll_color_signature_passed"] or stopped_pixels < 80:
        raise RuntimeError("Unconnected four-box control reached the goal or lost the actor")
    return {"upper_first_hop": 2, "lower_first_hop": 3,
            "both_alternative_native_routes_reached_goal": True,
            "blocked_route_stopped_at_boundary": True,
            "blocked_actor_pixels": stopped_pixels,
            "native_branching_boxm_passed": True}


def verify_two_goal_t_branch(connected_routes: list[list[int | None]],
                             disconnected_routes: list[list[int | None]],
                             upper_start: int, lower_reached: int,
                             upper_return: int, blocked_lower: int) -> dict:
    """Check native actor pixels at both destinations, not just BOXM data."""
    if (len(connected_routes) != 6 or connected_routes[1][4] != 2
            or connected_routes[1][5] != 2
            or connected_routes[3][4] != 4 or connected_routes[3][5] != 5):
        raise RuntimeError("Authored five-box T junction does not route to both goals")
    if disconnected_routes[1][5] is not None or disconnected_routes[1][4] != 2:
        raise RuntimeError("The negative control did not disconnect only the lower goal")
    if any(type(v) is not int or v < 0 for v in
           (upper_start, lower_reached, upper_return, blocked_lower)):
        raise ValueError("Invalid measured native actor pixel count")
    if (min(upper_start, lower_reached, upper_return) < 80
            or blocked_lower > lower_reached // 3):
        raise RuntimeError(
            "Two-goal T-branch navigation absent in stock ScummVM: "
            f"upper={upper_start}, lower={lower_reached}, "
            f"return={upper_return}, blocked={blocked_lower}")
    return {"upper_goal_pixels": upper_start,
            "lower_goal_pixels": lower_reached,
            "upper_return_pixels": upper_return,
            "blocked_lower_goal_pixels": blocked_lower,
            "native_two_goal_t_branch_passed": True}


def run_boxm_probe(upstream: Path, generated: Path, destination: Path) -> dict:
    """Studio connection text -> JSON -> ScummC BOXM -> real ScummVM movement."""
    destination.mkdir(parents=True, exist_ok=True)
    original = canonical_json(GameDocument("boxm_probe",
                                           (scrolling_fixture(), destination_fixture())))
    raw = author_room_walkbox(original, "Harbor", 1,
                              "0,70; 110,70; 110,150; 0,150")
    raw = author_room_walkbox(raw, "Harbor", 2,
                              "110,70; 639,70; 639,150; 110,150")
    results = {}
    for name, links in (("connected", "1-2"), ("disconnected", "")):
        edited = author_room_box_connections(raw, "Harbor", links)
        room = parse_document(edited).rooms[0]
        results[name] = {
            "authored_connections": links,
            "route_matrix": [list(row) for row in room.box_routes],
            **render_native_room(room, upstream, generated, destination, name,
                                 allow_static_scene=name == "disconnected"),
        }
    pixels = black_costume_pixels(destination / "disconnected-screenshots" /
                                 "scummvm-end.png", crop="250x155+200+300")
    results["comparison"] = verify_boxm_routing(
        results["connected"], results["disconnected"], pixels)
    # R08.2: create two already connected walkboxes, then append a third
    # through the exact Studio authoring path. Its first state must be isolated
    # without invalidating existing BOXM next hops. Linking it is explicit.
    network = author_room_walkbox(original, "Harbor", 1,
                                  "0,70; 110,70; 110,150; 0,150")
    network = author_room_walkbox(network, "Harbor", 2,
                                  "110,70; 240,70; 240,150; 110,150")
    network = author_room_box_connections(network, "Harbor", "1-2")
    old_routes = parse_document(network).rooms[0].box_routes
    extended = author_room_walkbox(network, "Harbor", 3,
                                   "240,70; 639,70; 639,150; 240,150")
    isolated = parse_document(extended).rooms[0].box_routes
    if isolated[:3] != tuple(row + (None,) for row in old_routes) or isolated[3] != (None, None, None, 3):
        raise RuntimeError("R08.2 append changed previously authored BOXM paths")
    results["extension"] = {"old_routes": [list(row) for row in old_routes],
                            "isolated_routes": [list(row) for row in isolated]}
    for state, links in (("extended-connected", "1-2; 2-3"),
                         ("extended-isolated", "1-2")):
        edited = author_room_box_connections(extended, "Harbor", links)
        room = parse_document(edited).rooms[0]
        results["extension"][state] = {
            "authored_connections": links,
            "route_matrix": [list(row) for row in room.box_routes],
            **render_native_room(room, upstream, generated, destination, state,
                                 allow_static_scene=state == "extended-isolated"),
        }
    extension_pixels = black_costume_pixels(
        destination / "extended-isolated-screenshots" / "scummvm-end.png",
        crop="250x155+200+300")
    results["extension"]["native_comparison"] = verify_boxm_routing(
        results["extension"]["extended-connected"],
        results["extension"]["extended-isolated"], extension_pixels)
    # R09: the existing Studio model and BOXM authoring accept a real fork.
    # Either path (1→2→4 or 1→3→4) must let the native actor reach the same
    # distant goal. With neither path, the actor stops at the near boundary.
    fork = canonical_json(GameDocument("forked_boxm",
                                        (scrolling_fixture(), destination_fixture())))
    for index, corners in (
            (1, "0,70; 110,70; 110,150; 0,150"),
            (2, "110,70; 240,70; 240,110; 110,110"),
            (3, "110,110; 240,110; 240,150; 110,150"),
            (4, "240,70; 639,70; 639,150; 240,150")):
        fork = author_room_walkbox(fork, "Harbor", index, corners)
    results["branching"] = {}
    for label, links in (("branch-upper", "1-2; 2-4"),
                         ("branch-lower", "1-3; 3-4"),
                         ("branch-blocked", "")):
        edited = author_room_box_connections(fork, "Harbor", links)
        project_file = destination / f"{label}-project.json"
        project_file.write_text(edited, encoding="utf-8")
        room = parse_document(project_file.read_text(encoding="utf-8")).rooms[0]
        results["branching"][label] = {
            "authored_connections": links,
            "route_matrix": [list(row) for row in room.box_routes],
            **render_native_room(room, upstream, generated, destination, label,
                                 allow_static_scene=label == "branch-blocked"),
        }
    stopped = black_costume_pixels(
        destination / "branch-blocked-screenshots" / "scummvm-end.png",
        crop="250x155+200+300")
    results["branching"]["native_comparison"] = verify_branching_boxm(
        results["branching"]["branch-upper"],
        results["branching"]["branch-lower"],
        results["branching"]["branch-blocked"], stopped)
    # R09: author a single five-box T junction with two *different* goals.
    # Both walking targets are clicked in the same running, unmodified game.
    # The lower branch is disconnected for the negative control only.
    t_project = canonical_json(GameDocument(
        "two_goal_t_branch", (scrolling_fixture(), destination_fixture())))
    for index, corners in (
            (1, "0,70; 110,70; 110,150; 0,150"),
            (2, "110,70; 240,70; 240,150; 110,150"),
            (3, "240,70; 360,70; 360,150; 240,150"),
            (4, "360,70; 639,70; 639,110; 360,110"),
            (5, "360,110; 639,110; 639,150; 360,150")):
        t_project = author_room_walkbox(t_project, "Harbor", index, corners)
    results["two_goals"] = {}
    for label, links in (
            ("two-goals-connected", "1-2; 2-3; 3-4; 3-5"),
            ("two-goals-blocked", "1-2; 2-3; 3-4")):
        edited = author_room_box_connections(t_project, "Harbor", links)
        project_path = destination / f"{label}-project.json"
        project_path.write_text(edited, encoding="utf-8")
        room = parse_document(project_path.read_text(encoding="utf-8")).rooms[0]
        results["two_goals"][label] = {
            "connections": links,
            "route_matrix": [list(row) for row in room.box_routes],
            **render_native_room(room, upstream, generated, destination, label,
                                 scene_walk_clicks=(("lower-goal", 630, 449),
                                                    ("upper-return", 630, 364))
                                 if label == "two-goals-connected"
                                 else (("lower-goal", 630, 449),)),
        }
    upper_start = black_costume_pixels(
        destination / "two-goals-connected-screenshots" / "scummvm-end.png",
        crop="110x75+575+312")
    lower_reached = black_costume_pixels(
        destination / "two-goals-connected-screenshots" / "scummvm-lower-goal.png",
        crop="110x65+575+390")
    upper_return = black_costume_pixels(
        destination / "two-goals-connected-screenshots" / "scummvm-upper-return.png",
        crop="110x75+575+312")
    blocked_lower = black_costume_pixels(
        destination / "two-goals-blocked-screenshots" / "scummvm-lower-goal.png",
        crop="110x65+575+390")
    results["two_goals"]["native_comparison"] = verify_two_goal_t_branch(
        results["two_goals"]["two-goals-connected"]["route_matrix"],
        results["two_goals"]["two-goals-blocked"]["route_matrix"],
        upper_start, lower_reached, upper_return, blocked_lower)
    (destination / "native-boxm-routing-report.json").write_text(
        json.dumps(results, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_boxm_routing_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_boxm_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                  Path(sys.argv[3])), indent=2))

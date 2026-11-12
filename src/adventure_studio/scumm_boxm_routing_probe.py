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
    (destination / "native-boxm-routing-report.json").write_text(
        json.dumps(results, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_boxm_routing_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_boxm_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                  Path(sys.argv[3])), indent=2))

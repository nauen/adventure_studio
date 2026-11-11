"""Stock-ScummVM evidence for a freely authored BOXD walking boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .scumm_assets import destination_fixture, scrolling_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_visual_probe import black_costume_pixels, render_native_room
from .studio_sequences import author_room_walkbox


def verify_walkbox_boundary(free: dict, limited: dict, limited_actor_pixels: int) -> dict:
    """Require a reachable full-room walk and an actor stopped in the left box."""
    if not free["frame_report"]["scroll_color_signature_passed"]:
        raise RuntimeError("Full-width authored Walkbox did not let the actor reach the far room")
    if limited["frame_report"]["scroll_color_signature_passed"]:
        raise RuntimeError("Restricted Walkbox let the actor cross the room boundary")
    if limited_actor_pixels < 80:
        raise RuntimeError("Restricted actor not visibly present near the Walkbox boundary")
    return {"free_walk_reached_far_room": True,
            "restricted_walk_stayed_in_left_room": True,
            "restricted_actor_pixels": limited_actor_pixels,
            "native_walkbox_boundary_passed": True}


def run_walkbox_probe(upstream: Path, generated: Path, destination: Path) -> dict:
    """Studio-style polygon authoring → JSON → BOXD → stock ScummVM images."""
    destination.mkdir(parents=True, exist_ok=True)
    raw = canonical_json(GameDocument("walkbox_probe",
                                  (scrolling_fixture(), destination_fixture())))
    variants = (("free", "0,70; 639,70; 639,150; 0,150", False),
                ("limited", "0,70; 110,70; 110,150; 0,150", True))
    results = {}
    for label, corners, allow_static in variants:
        authored = author_room_walkbox(raw, "Harbor", 1, corners)
        room = parse_document(authored).rooms[0]
        results[label] = {
            "walkbox_corners": [list(point) for point in room.walkboxes[0].corners],
            **render_native_room(room, upstream, generated, destination, label,
                                 allow_static_scene=allow_static),
        }
    actor_pixels = black_costume_pixels(
        destination / "limited-screenshots" / "scummvm-end.png",
        crop="250x155+200+300")
    results["comparison"] = verify_walkbox_boundary(results["free"],
                                                       results["limited"], actor_pixels)
    (destination / "native-walkbox-boundary-report.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_walkbox_boundary_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_walkbox_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                       Path(sys.argv[3])), indent=2))

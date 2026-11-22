"""Native R08 concave aggregate built from convex Studio-authored BOXD walkboxes.

Three independently compiled stock-ScummVM games exercise the only supported
SCUMM-v6 representation: convex boxes joined by explicit BOXM connections.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .scumm_assets import destination_fixture, scrolling_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_visual_probe import black_costume_pixels, render_native_room
from .studio_sequences import author_room_box_connections, author_room_walkbox


def verify_concave_route(connected: dict, convex: dict, blocked: dict,
                         blocked_actor_pixels: int) -> dict:
    """Both positive games reach the far side; the disconnected one must not."""
    matrix = connected["route_matrix"]
    negative = blocked["route_matrix"]
    if len(matrix) != 4 or any(len(row) != 4 for row in matrix):
        raise RuntimeError("R08 needs exactly three valid convex BOXD walkboxes")
    if matrix[1][3] != 2 or matrix[3][1] != 2:
        raise RuntimeError("Concave aggregate is missing its explicit native BOXM bend")
    if negative[1][3] is not None:
        raise RuntimeError("Disconnected native control still reaches the far segment")
    if not connected["frame_report"]["scroll_color_signature_passed"]:
        raise RuntimeError("Native Actor did not traverse the connected L-shaped corridor")
    if not convex["frame_report"]["scroll_color_signature_passed"]:
        raise RuntimeError("Independent convex native control did not reach the far side")
    if blocked["frame_report"]["scroll_color_signature_passed"]:
        raise RuntimeError("Disconnected native control unexpectedly reached the far side")
    if type(blocked_actor_pixels) is not int or blocked_actor_pixels < 80:
        raise RuntimeError("Disconnected Actor missing at the near-side boundary")
    return {
        "native_concave_aggregate_reached_far_side": True,
        "independent_convex_control_reached_far_side": True,
        "disconnected_control_stayed_near": True,
        "blocked_actor_pixels": blocked_actor_pixels,
        "native_r08_concave_walkbox_passed": True,
    }


def run_concave_walkbox_probe(upstream: Path, generated: Path, output: Path) -> dict:
    """Studio authoring -> JSON -> ScummC BOXD/BOXM -> stock ScummVM."""
    output.mkdir(parents=True, exist_ok=True)
    raw = canonical_json(GameDocument(
        "r08_concave_walkbox", (scrolling_fixture(), destination_fixture())))
    for index, corners in (
        (1, "0,70; 220,70; 220,150; 0,150"),
        (2, "180,110; 260,110; 260,150; 180,150"),
        (3, "260,70; 639,70; 639,150; 260,150"),
    ):
        raw = author_room_walkbox(raw, "Harbor", index, corners)
    variants = (
        ("concave-connected", author_room_box_connections(raw, "Harbor", "1-2; 2-3")),
        ("concave-disconnected", author_room_box_connections(raw, "Harbor", "1-2")),
        ("convex-control", author_room_walkbox(
            canonical_json(GameDocument(
                "r08_convex_control", (scrolling_fixture(), destination_fixture()))),
            "Harbor", 1, "0,70; 639,70; 639,150; 0,150")),
    )
    results = {}
    for label, authored in variants:
        restored = parse_document(canonical_json(parse_document(authored)))
        room = restored.rooms[0]
        (output / f"{label}-project.json").write_text(
            canonical_json(restored), encoding="utf-8")
        results[label] = {
            "walkbox_corners": [[list(point) for point in box.corners]
                                for box in room.walkboxes],
            "route_matrix": [list(row) for row in room.box_routes],
            **render_native_room(
                room, upstream, generated, output, label,
                allow_static_scene=label == "concave-disconnected"),
        }
    blocked_pixels = black_costume_pixels(
        output / "concave-disconnected-screenshots" / "scummvm-end.png",
        crop="250x155+200+300",
    )
    results["comparison"] = verify_concave_route(
        results["concave-connected"], results["convex-control"],
        results["concave-disconnected"], blocked_pixels)
    (output / "native-r08-concave-walkbox-report.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(
            "Usage: python -m adventure_studio.scumm_concave_walkbox_probe "
            "UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_concave_walkbox_probe(
        Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])), indent=2))

"""R08 triangular BOXD product-path acceptance in unmodified stock ScummVM."""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

from .scumm_assets import _native_box_file, destination_fixture, scrolling_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_visual_probe import black_costume_pixels, render_native_room
from .studio_sequences import author_room_walkbox


def verify_triangle_walkbox(wide: dict, narrow: dict, rectangle: dict,
                            narrow_actor_pixels: int) -> dict:
    """Require triangle success, triangle stop, and independent rectangle success."""
    states = {key: value["frame_report"]["scroll_color_signature_passed"]
              for key, value in (("wide", wide), ("narrow", narrow),
                                 ("rectangle", rectangle))}
    if not states["wide"] or not states["rectangle"]:
        raise RuntimeError("Stock ScummVM Actor did not reach the far room in positive controls")
    if states["narrow"]:
        raise RuntimeError("Stock ScummVM Actor crossed the narrow triangular walking boundary")
    if type(narrow_actor_pixels) is not int or narrow_actor_pixels < 80:
        raise RuntimeError("Narrow triangular control Actor is not visibly present")
    return {"wide_triangle_reached_far_room": True,
            "narrow_triangle_blocked_actor": True,
            "rectangle_control_reached_far_room": True,
            "narrow_actor_pixels": narrow_actor_pixels,
            "native_r08_triangle_walkbox_passed": True}


def run_triangle_walkbox_probe(upstream: Path, generated: Path, output: Path) -> dict:
    """Export three distinct Studio projects, then run the actual native games."""
    output.mkdir(parents=True, exist_ok=True)
    original = canonical_json(GameDocument(
        "r08_triangle_walkbox", (scrolling_fixture(), destination_fixture())))
    variants = (
        ("wide-triangle", "0,70; 639,100; 0,150"),
        ("narrow-triangle", "0,70; 110,100; 0,150"),
        ("rectangle-control", "0,70; 639,70; 639,150; 0,150"),
    )
    results: dict[str, dict] = {}
    for label, corners in variants:
        authored = author_room_walkbox(original, "Harbor", 1, corners)
        imported = parse_document(canonical_json(parse_document(authored)))
        room = next(item for item in imported.rooms if item.name == "Harbor")
        vertices = room.walkboxes[0].corners
        if len(corners.split(";")) == 3 and vertices[2] != vertices[3]:
            raise RuntimeError("Triangle last vertex was not preserved by JSON reimport")
        expected = tuple(number for vertex in vertices for number in vertex)
        if struct.unpack_from("<8h", _native_box_file(room), 9) != expected:
            raise RuntimeError("Productive ScummC BOXD input changed authored triangle")
        (output / f"{label}-project.json").write_text(
            canonical_json(imported), encoding="utf-8")
        results[label] = {
            "corners": [list(vertex) for vertex in vertices],
            "native_boxd_coordinates": list(expected),
            **render_native_room(room, upstream, generated, output, label,
                                 allow_static_scene=label == "narrow-triangle"),
        }
    pixels = black_costume_pixels(
        output / "narrow-triangle-screenshots" / "scummvm-end.png",
        crop="250x155+200+300")
    results["comparison"] = verify_triangle_walkbox(
        results["wide-triangle"], results["narrow-triangle"],
        results["rectangle-control"], pixels)
    (output / "native-r08-triangle-walkbox-report.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_triangle_walkbox_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_triangle_walkbox_probe(
        Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])), indent=2))

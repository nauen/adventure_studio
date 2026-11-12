"""R06: simultaneous independent ZP01/ZP02 masks on adjacent native walkboxes.

The existing Studio authors two PNG masks and assigns them to *different*
connected walkboxes in the same room. Real stock ScummVM gameplay walks
between their distinct masked locations in one running export, contrasted
against three independently linked control games.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .scumm_assets import destination_fixture, scrolling_fixture
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_visual_probe import black_costume_pixels, render_native_room
from .studio_sequences import (
    author_room_box_connections, author_room_walkbox, author_room_walkbox_zplane,
    compose_story_project, import_room_zplane,
)


def verify_simultaneous_masks(variants: dict[str, dict]) -> dict:
    """Require selective actor occlusion at two separate places in one game."""
    required = ("both", "first-only", "second-only", "clear")
    if set(variants) != set(required):
        raise ValueError("Need combined masks and all three independent controls")
    for name in required:
        row = variants[name]
        if row["walkbox_masks"] != [0, 1, 2]:
            raise RuntimeError("Both distinct mask indices must survive Studio export")
        if not row["frame_report"]["scroll_color_signature_passed"]:
            raise RuntimeError(f"Actor did not reach the distant room: {name}")
        if any(type(row[k]) is not int or row[k] < 0
               for k in ("middle_pixels", "far_pixels", "return_pixels")):
            raise ValueError("Invalid native actor costume pixel count")
    both, first, second, clear = (variants[k] for k in required)
    # Both transparent control locations must show an actual actor.
    if clear["middle_pixels"] < 100 or clear["far_pixels"] < 100:
        raise RuntimeError("Actors missing from the two transparent control targets")
    # ZP01 occludes *only* the middle box; ZP02 occludes *only* the far box.
    if not (both["middle_pixels"] <= clear["middle_pixels"] // 3
            and first["middle_pixels"] <= clear["middle_pixels"] // 3
            and second["middle_pixels"] >= clear["middle_pixels"] * 2 // 3
            and both["far_pixels"] <= clear["far_pixels"] // 3
            and second["far_pixels"] <= clear["far_pixels"] // 3
            and first["far_pixels"] >= clear["far_pixels"] * 2 // 3
            and both["return_pixels"] <= clear["return_pixels"] // 3
            and first["return_pixels"] >= clear["return_pixels"] * 2 // 3):
        raise RuntimeError(
            "Simultaneous stock-ScummVM ZP01/ZP02 occlusion not selective: "
            + json.dumps({k: {p: variants[k][p] for p in
                               ("middle_pixels", "far_pixels", "return_pixels")}
                          for k in required}, sort_keys=True))
    return {
        "native_simultaneous_room_masks_passed": True,
        "middle_box_uses_zp01": True,
        "far_box_uses_zp02": True,
        "both_masks_occlude_in_one_running_game": True,
        "clear_middle_actor_pixels": clear["middle_pixels"],
        "clear_far_actor_pixels": clear["far_pixels"],
        "both_middle_actor_pixels": both["middle_pixels"],
        "both_far_actor_pixels": both["far_pixels"],
        "both_return_actor_pixels": both["return_pixels"],
    }


def run_simultaneous_mask_probe(upstream: Path, generated: Path, destination: Path) -> dict:
    from PIL import Image

    destination.mkdir(parents=True, exist_ok=True)
    base = scrolling_fixture()
    width, height = base.geometry.room_width, base.geometry.room_height
    project = canonical_json(GameDocument("simultaneous_room_masks",
                                           (base, destination_fixture())))
    for index, corners in (
            (1, "0,70; 240,70; 240,150; 0,150"),
            (2, "240,70; 400,70; 400,150; 240,150"),
            (3, "400,70; 639,70; 639,150; 400,150")):
        project = author_room_walkbox(project, "Harbor", index, corners)
    project = author_room_box_connections(project, "Harbor", "1-2; 2-3")
    zpngs = (destination / "middle-zp01.png", destination / "far-zp02.png")
    transparent = bytes(width * height)
    for index, path in enumerate(zpngs, 1):
        Image.frombytes("L", (width, height), transparent).save(path)
        project = import_room_zplane(project, "Harbor", index, str(path))
    project = author_room_walkbox_zplane(project, "Harbor", 2, 1)
    project = author_room_walkbox_zplane(project, "Harbor", 3, 2)
    # The masks overlap the torso while the actor walks at world y=100.
    middle = bytes(255 if 240 <= x < 400 and 60 < y < 110 else 0
                   for y in range(height) for x in range(width))
    far = bytes(255 if x >= 400 and 60 < y < 110 else 0
                for y in range(height) for x in range(width))
    results = {"authoring": "Studio two independent PNGs -> RoomAsset/JSON/Story "
                            "-> SCUMM-v6 ZP01/ZP02 + BOXD masks 1/2 -> stock ScummVM",
               "variants": {}}
    for label, first_enabled, second_enabled in (
            ("both", True, True), ("first-only", True, False),
            ("second-only", False, True), ("clear", False, False)):
        raw = project
        for index, path in enumerate(zpngs, 1):
            enabled = first_enabled if index == 1 else second_enabled
            pixels = (middle if index == 1 else far) if enabled else transparent
            Image.frombytes("L", (width, height), pixels).save(path)
            raw = import_room_zplane(raw, "Harbor", index, str(path))
        project_path = destination / f"{label}-project.json"
        project_path.write_text(raw, encoding="utf-8")
        room = parse_document(project_path.read_text(encoding="utf-8")).rooms[0]
        if len(room.zplanes) != 2 or [box.mask for box in room.walkboxes] != [0, 1, 2]:
            raise RuntimeError("Studio did not persist two independent walkbox masks")
        if parse_document(canonical_json(parse_document(raw))).rooms[0] != room:
            raise RuntimeError("Room masks did not survive JSON roundtrip")
        results["variants"][label] = {
            "walkbox_masks": [box.mask for box in room.walkboxes],
            "mask_enabled": [first_enabled, second_enabled],
            **render_native_room(room, upstream, generated, destination, label,
                                 scene_walk_clicks=(("middle-goal", 422, 390),
                                                    ("far-return", 630, 390))),
        }
        images = destination / f"{label}-screenshots"
        results["variants"][label].update({
            "middle_pixels": black_costume_pixels(
                images / "scummvm-middle-goal.png", "130x95+360+305"),
            "far_pixels": black_costume_pixels(
                images / "scummvm-end.png", "110x85+575+305"),
            "return_pixels": black_costume_pixels(
                images / "scummvm-far-return.png", "110x85+575+305"),
        })
        if label == "both":
            story = (Path(__file__).resolve().parents[2] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            composed = parse_document(compose_story_project(story, raw))
            saved = next(r for r in composed.rooms if r.name == "Harbor")
            if saved.zplanes != room.zplanes or saved.walkboxes != room.walkboxes:
                raise RuntimeError("Story composition lost simultaneous room masks")
    results["comparison"] = verify_simultaneous_masks(results["variants"])
    (destination / "native-simultaneous-mask-report.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_simultaneous_zplane_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_simultaneous_mask_probe(
        Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])), indent=2))

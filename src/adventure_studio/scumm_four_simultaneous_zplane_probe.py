"""R06: simultaneous independent ZP01/ZP02/ZP03/ZP04 masks on connected walkboxes.

The existing Studio authors four PNG masks and assigns them to *different*
connected walkboxes in the same room. Real stock ScummVM gameplay walks
between their distinct masked locations in one running export, contrasted
against five independently linked control games.
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



def verify_simultaneous_four_masks(variants: dict[str, dict]) -> dict:
    """Each independent layer must occlude only its own destination in one game."""
    positions = ("second", "third", "fourth", "fifth")
    required = {"all", "clear", "first-only", "second-only", "third-only", "fourth-only"}
    if set(variants) != required:
        raise ValueError("Need four simultaneous masks and five independent controls")
    for label, row in variants.items():
        if row["walkbox_masks"] != [0, 1, 2, 3, 4]:
            raise RuntimeError(f"Native BOXD mask assignments lost: {label}")
        if not row["frame_report"]["scroll_color_signature_passed"]:
            raise RuntimeError(f"Actor did not reach the distant room: {label}")
        for position in positions + ("fourth_return", "fifth_return"):
            value = row[position + "_pixels"]
            if type(value) is not int or value < 0:
                raise ValueError(f"Invalid actor pixels: {label} / {position}")
    clear, all_masked = variants["clear"], variants["all"]
    for index, position in enumerate(positions):
        unmasked = clear[position + "_pixels"]
        if unmasked < 100:
            raise RuntimeError(f"No visible actor at transparent {position} goal")
        for layer in range(4):
            label = ("first-only", "second-only", "third-only", "fourth-only")[layer]
            pixels = variants[label][position + "_pixels"]
            if layer == index and pixels > unmasked // 3:
                raise RuntimeError(f"{label} failed to occlude {position}: {pixels}/{unmasked}")
            if layer != index and pixels < unmasked * 2 // 3:
                raise RuntimeError(f"{label} leaked occlusion into {position}: {pixels}/{unmasked}")
        if all_masked[position + "_pixels"] > unmasked // 3:
            raise RuntimeError(f"Four simultaneous masks failed at {position}")
    for position, owner in (("fourth_return", "third-only"), ("fifth_return", "fourth-only")):
        unmasked = clear[position + "_pixels"]
        if unmasked < 100:
            raise RuntimeError(f"Actor did not return to the {position} control goal")
        if (all_masked[position + "_pixels"] > unmasked // 3
                or variants[owner][position + "_pixels"] > unmasked // 3):
            raise RuntimeError(f"Occlusion failed after return to {position}")
    return {
        "native_simultaneous_four_room_masks_passed": True,
        "walkbox_masks": [0, 1, 2, 3, 4],
        "actor_visited_four_masked_goals_and_returned": True,
        "actor_pixels": {label: {position: row[position + "_pixels"]
                       for position in positions + ("fourth_return", "fifth_return")}
                         for label, row in variants.items()},
    }


def run_simultaneous_four_mask_probe(upstream: Path, generated: Path,
                                       destination: Path) -> dict:
    from PIL import Image

    destination.mkdir(parents=True, exist_ok=True)
    base = scrolling_fixture()
    width, height = base.geometry.room_width, base.geometry.room_height
    project = canonical_json(GameDocument("simultaneous_four_room_masks",
                                           (base, destination_fixture())))
    for index, corners in (
            (1, "0,70; 160,70; 160,150; 0,150"),
            (2, "160,70; 320,70; 320,150; 160,150"),
            (3, "320,70; 400,70; 400,150; 320,150"),
            (4, "400,70; 520,70; 520,150; 400,150"),
            (5, "520,70; 639,70; 639,150; 520,150")):
        project = author_room_walkbox(project, "Harbor", index, corners)
    project = author_room_box_connections(project, "Harbor", "1-2; 2-3; 3-4; 4-5")
    pngs = tuple(destination / f"mask-zp{index:02d}.png" for index in (1, 2, 3, 4))
    transparent = bytes(width * height)
    for index, path in enumerate(pngs, 1):
        Image.frombytes("L", (width, height), transparent).save(path)
        project = import_room_zplane(project, "Harbor", index, str(path))
        project = author_room_walkbox_zplane(project, "Harbor", index + 1, index)
    mask_regions = ((160, 320), (320, 400), (400, 520), (520, width))
    opaque = tuple(bytes(255 if start <= x < end and 60 < y < 110 else 0
                         for y in range(height) for x in range(width))
                   for start, end in mask_regions)
    variants = {}
    for label, enabled in (
            ("all", (True, True, True, True)),
            ("first-only", (True, False, False, False)),
            ("second-only", (False, True, False, False)),
            ("third-only", (False, False, True, False)),
            ("fourth-only", (False, False, False, True)),
            ("clear", (False, False, False, False))):
        raw = project
        for index, path in enumerate(pngs, 1):
            Image.frombytes("L", (width, height),
                            opaque[index - 1] if enabled[index - 1] else transparent).save(path)
            raw = import_room_zplane(raw, "Harbor", index, str(path))
        project_path = destination / f"{label}-project.json"
        project_path.write_text(raw, encoding="utf-8")
        room = parse_document(project_path.read_text(encoding="utf-8")).rooms[0]
        if (len(room.zplanes) != 4
                or [box.mask for box in room.walkboxes] != [0, 1, 2, 3, 4]):
            raise RuntimeError("Four independently authored native walkbox masks lost")
        if parse_document(canonical_json(parse_document(raw))).rooms[0] != room:
            raise RuntimeError("Four-mask JSON roundtrip changed the authored room")
        if label == "all":
            story = (Path(__file__).resolve().parents[2] / "examples" /
                     "mini_story_chain.json").read_text(encoding="utf-8")
            saved = next(r for r in parse_document(compose_story_project(story, raw)).rooms
                         if r.name == "Harbor")
            if saved.zplanes != room.zplanes or saved.walkboxes != room.walkboxes:
                raise RuntimeError("Story composition lost four mask assignments")
        row = {"walkbox_masks": [box.mask for box in room.walkboxes],
               "mask_enabled": list(enabled),
               **render_native_room(
                   room, upstream, generated, destination, label,
                   scene_walk_clicks=(("second-goal", 245, 390),
                                      ("third-goal", 460, 390),
                                      ("fourth-goal", 630, 390),
                                      ("fifth-goal", 790, 390),
                                      ("fourth-crossing", 630, 390),
                                      ("fourth-return", 630, 390),
                                      ("fifth-crossing", 790, 390),
                                      ("fifth-return", 790, 390)))}
        images = destination / f"{label}-screenshots"
        row.update({
            "second_pixels": black_costume_pixels(
                images / "scummvm-second-goal.png", "610x95+210+305"),
            "third_pixels": black_costume_pixels(
                images / "scummvm-third-goal.png", "610x95+210+305"),
            "fourth_pixels": black_costume_pixels(
                images / "scummvm-fourth-goal.png", "610x95+210+305"),
            "fifth_pixels": black_costume_pixels(
                images / "scummvm-fifth-goal.png", "610x95+210+305"),
            "fourth_return_pixels": black_costume_pixels(
                images / "scummvm-fourth-return.png", "610x95+210+305"),
            "fifth_return_pixels": black_costume_pixels(
                images / "scummvm-fifth-return.png", "610x95+210+305"),
        })
        variants[label] = row
    print("Native four-mask scene pixel observations:", json.dumps({name: {key: value for key, value in row.items() if key.endswith("_pixels")} for name, row in variants.items()}, sort_keys=True), flush=True)
    report = {
        "authoring": "Studio four PNGs -> RoomAsset/JSON/Story -> ScummC ZP01/ZP02/ZP03/ZP04 + BOXD masks 1/2/3/4 -> stock ScummVM",
        "variants": variants,
        "comparison": verify_simultaneous_four_masks(variants),
    }
    (destination / "native-four-simultaneous-mask-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_four_simultaneous_zplane_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_simultaneous_four_mask_probe(
        Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])), indent=2))

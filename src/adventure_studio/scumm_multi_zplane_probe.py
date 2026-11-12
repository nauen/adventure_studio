"""R06: prove four stock-v6 masks and refuse an unsupported fifth export."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .scumm_assets import destination_fixture, write_room_sources
from .scumm_project import GameDocument, canonical_json, parse_document
from .scumm_room_fixture import native_room
from .scumm_room_visual_probe import render_native_room
from .studio_sequences import import_room_zplane, author_room_walkbox_zplane


def verify_two_layer_occlusion(clear: int, first: int, second: int) -> dict:
    """Both independently selected masks must remove visible actor pixels."""
    if any(type(v) is not int or v < 0 for v in (clear, first, second)):
        raise ValueError("Invalid native Z-plane pixel count")
    if clear < 100 or first > clear // 3 or second > clear // 3:
        raise RuntimeError(
            f"Multi-layer Z-plane occlusion absent in stock ScummVM: "
            f"clear={clear}, first={first}, second={second}")
    return {"clear_costume_pixels": clear, "first_layer_pixels": first,
            "second_layer_pixels": second, "both_layers_visually_verified": True}


def verify_three_layer_occlusion(clear: int, first: int, second: int, third: int) -> dict:
    """A third independently selected native BOXD mask must hide the same actor."""
    previous = verify_two_layer_occlusion(clear, first, second)
    if type(third) is not int or third < 0 or third > clear // 3:
        raise RuntimeError(
            f"Third Z-plane occlusion absent in stock ScummVM: "
            f"clear={clear}, first={first}, second={second}, third={third}")
    return {**previous, "third_layer_pixels": third,
            "three_layers_visually_verified": True}


def verify_four_layer_occlusion(clear: int, first: int, second: int,
                                third: int, fourth: int) -> dict:
    """The fourth Studio-authored BOXD mask must hide the actor independently."""
    previous = verify_three_layer_occlusion(clear, first, second, third)
    if type(fourth) is not int or fourth < 0 or fourth > clear // 3:
        raise RuntimeError(
            f"Fourth Z-plane occlusion absent in stock ScummVM: "
            f"clear={clear}, first={first}, second={second}, "
            f"third={third}, fourth={fourth}")
    return {**previous, "fourth_layer_pixels": fourth,
            "four_layers_visually_verified": True}


def run_multi_zplane_probe(upstream: Path, generated: Path, destination: Path) -> dict:
    from PIL import Image

    destination.mkdir(parents=True, exist_ok=True)
    base = native_room(occlusion=False, far_scale=255)
    width, height = base.geometry.room_width, base.geometry.room_height
    project = canonical_json(GameDocument("multi_zplane", (base, destination_fixture())))
    # All four layers come from independently imported PNG files, not a binary fixture.
    transparent = bytes(width * height)
    opaque = bytes(255 if x > width // 2 and 60 < y < 110 else 0
                   for y in range(height) for x in range(width))
    pngs = tuple(destination / f"layer-{index}-mask.png" for index in (1, 2, 3, 4))
    for index, path in enumerate(pngs, start=1):
        Image.frombytes("L", (width, height), transparent).save(path)
        project = import_room_zplane(project, "Harbor", index, str(path))
    results = {
        "authoring": "PNG1+PNG2+PNG3+PNG4 → Studio model/JSON → ScummC ZP01/ZP02/ZP03/ZP04 + BOXD → stock ScummVM",
        "variants": {},
    }
    # One opaque plane at a time. All other PNG layers remain transparent;
    # each selected native BOXD mask must independently hide the same actor.
    for label, layer, opaque_index in (
            ("first", 1, 1), ("second", 2, 2),
            ("third", 3, 3), ("fourth", 4, 4), ("clear", 4, 0)):
        raw = project
        for index, path in enumerate(pngs, start=1):
            Image.frombytes("L", (width, height),
                            opaque if index == opaque_index else transparent).save(path)
            raw = import_room_zplane(raw, "Harbor", index, str(path))
        raw = author_room_walkbox_zplane(raw, "Harbor", 2, layer)
        project_path = destination / f"{label}-project.json"
        project_path.write_text(raw, encoding="utf-8")
        room = parse_document(project_path.read_text(encoding="utf-8")).rooms[0]
        assert len(room.zplanes) == 4
        assert room.walkboxes[1].mask == layer
        results["variants"][label] = {
            "selected_zplane": layer,
            **render_native_room(room, upstream, generated, destination, label),
        }
    results["comparison"] = verify_four_layer_occlusion(
        results["variants"]["clear"]["dark_costume_pixels"],
        results["variants"]["first"]["dark_costume_pixels"],
        results["variants"]["second"]["dark_costume_pixels"],
        results["variants"]["third"]["dark_costume_pixels"],
        results["variants"]["fourth"]["dark_costume_pixels"])
    # R06 stock-v6 compatibility contract: a fifth Studio PNG remains
    # editable, but the native exporter must fail before creating assets.
    # The four preceding variants are still tested in unmodified ScummVM.
    fifth_png = destination / "layer-5-mask.png"
    Image.frombytes("L", (width, height), opaque).save(fifth_png)
    fifth = import_room_zplane(project, "Harbor", 5, str(fifth_png))
    fifth = author_room_walkbox_zplane(fifth, "Harbor", 2, 5)
    (destination / "fifth-refused-project.json").write_text(fifth, encoding="utf-8")
    fifth_room = parse_document(fifth).rooms[0]
    if len(fifth_room.zplanes) != 5 or fifth_room.walkboxes[1].mask != 5:
        raise RuntimeError("Fifth room mask was not preserved in Studio authoring")
    refused_dir = destination / "fifth-refused-native-assets"
    try:
        write_room_sources(fifth_room, refused_dir)
    except ValueError as error:
        if "ZP05" not in str(error):
            raise
        if refused_dir.exists():
            raise RuntimeError("Unsupported fifth Z-plane wrote partial native assets")
        results["stock_v6_export_guard"] = {
            "fifth_studio_png_preserved": True,
            "fifth_native_export_refused": True,
            "native_assets_written": False,
            "rejection": str(error),
        }
    else:
        raise RuntimeError("Stock-v6 exporter accepted unsupported fifth Z-plane")
    (destination / "multi-zplane-report.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_multi_zplane_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_multi_zplane_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                            Path(sys.argv[3])), indent=2))

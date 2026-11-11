"""R06.2: prove two Studio-authored ZPxx layers selectably occlude in stock ScummVM."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .scumm_assets import destination_fixture
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


def run_multi_zplane_probe(upstream: Path, generated: Path, destination: Path) -> dict:
    from PIL import Image

    destination.mkdir(parents=True, exist_ok=True)
    base = native_room(occlusion=False, far_scale=255)
    width, height = base.geometry.room_width, base.geometry.room_height
    project = canonical_json(GameDocument("multi_zplane", (base, destination_fixture())))
    # Two independent PNG files, not a hardcoded mask fixture.
    transparent = bytes(width * height)
    opaque = bytes(255 if x > width // 2 and 60 < y < 110 else 0
                   for y in range(height) for x in range(width))
    first_png = destination / "first-mask.png"
    second_png = destination / "second-mask.png"
    Image.frombytes("L", (width, height), opaque).save(first_png)
    Image.frombytes("L", (width, height), transparent).save(second_png)
    project = import_room_zplane(project, "Harbor", 1, str(first_png))
    project = import_room_zplane(project, "Harbor", 2, str(second_png))
    results = {"authoring": "PNG1+PNG2 → Studio model/JSON → ScummC ZP01/ZP02 + BOXD → stock ScummVM",
               "variants": {}}
    for label, layer, layer1, layer2 in (
            ("first", 1, opaque, transparent),
            ("second", 2, transparent, opaque),
            ("clear", 2, transparent, transparent)):
        Image.frombytes("L", (width, height), layer1).save(first_png)
        Image.frombytes("L", (width, height), layer2).save(second_png)
        raw = import_room_zplane(project, "Harbor", 1, str(first_png))
        raw = import_room_zplane(raw, "Harbor", 2, str(second_png))
        raw = author_room_walkbox_zplane(raw, "Harbor", 2, layer)
        project_path = destination / f"{label}-project.json"
        project_path.write_text(raw, encoding="utf-8")
        room = parse_document(project_path.read_text(encoding="utf-8")).rooms[0]
        assert len(room.zplanes) == 2
        assert room.walkboxes[1].mask == layer
        results["variants"][label] = {
            "selected_zplane": layer,
            **render_native_room(room, upstream, generated, destination, label),
        }
    results["comparison"] = verify_two_layer_occlusion(
        results["variants"]["clear"]["dark_costume_pixels"],
        results["variants"]["first"]["dark_costume_pixels"],
        results["variants"]["second"]["dark_costume_pixels"])
    (destination / "multi-zplane-report.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_multi_zplane_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_multi_zplane_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                            Path(sys.argv[3])), indent=2))

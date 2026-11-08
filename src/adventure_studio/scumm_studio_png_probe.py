"""Compile a Costume authored with the actual Studio PNG operations in stock ScummVM."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

from .scumm_assets import destination_fixture, scrolling_fixture
from .scumm_launch import launch_smoke
from .scumm_project import GameDocument, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game
from .studio_actors import add_actor, add_costume_frame, create_costume, set_costume_animation


def run_studio_png_probe(upstream: Path, destination: Path) -> dict:
    """Use production Studio imports, project JSON and the native compiler path."""
    from PIL import Image, ImageDraw

    build = destination / "build"
    build.mkdir(parents=True, exist_ok=True)
    png_paths = []
    for name, color in (("pose", (245, 40, 75, 255)),
                        ("wave", (40, 245, 120, 255))):
        image = Image.new("RGBA", (24, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((7, 8, 16, 31), fill=color)
        draw.rectangle((3 if name == "pose" else 17, 12,
                        6 if name == "pose" else 20, 22), fill=color)
        path = build / f"{name}.png"
        image.save(path)
        png_paths.append(path)

    raw = canonical_json(GameDocument("StudioPngPlayback", (
        scrolling_fixture(), destination_fixture())))
    raw = create_costume(raw, str(png_paths[0]), "StudioPngCostume")
    raw = add_costume_frame(raw, "StudioPngCostume", str(png_paths[1]), "WavePose")
    for direction in ("N", "E", "S", "W"):
        raw = set_costume_animation(raw, "StudioPngCostume", "wave", 28,
                                    direction, "Pose0, WavePose, Pose0, WavePose", True)
    raw = add_actor(raw, "StudioPngActor", "StudioPngCostume", "Harbor",
                    430, 110, "S", "Studio PNG Actor")
    document = parse_document(raw)
    document = replace(document, actors=(replace(document.actors[0],
                                                  initial_animation="wave"),))
    encoded = canonical_json(document)
    (build / "project.json").write_text(encoded, encoding="utf-8")
    export_document(parse_document(encoded), build / "resources")
    game = compile_story_game(build, upstream, destination / "game")
    launch_smoke(game, destination / "screenshots", scene_only=True)
    report = {
        "studio_png_frames": 2,
        "native_costume_compiled": True,
        "stock_scummvm_launched": True,
        "animation_source": "StudioPngCostume.scost",
        "animation_playback_visually_verified": False,
    }
    (destination / "studio-png-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_studio_png_probe SCUMMC_DIR OUTPUT_DIR")
    print(run_studio_png_probe(Path(sys.argv[1]), Path(sys.argv[2])))

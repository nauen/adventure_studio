"""Controlled native ScummVM comparison for Z masking and box scaling.

Research-only executable: compiles three real ScummC room variants, launches
each in unmodified ScummVM and records reproducible image measurements.
Measurements are diagnostic until stable, source-backed pass bands exist.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .scumm_assets import write_room_sources
from .scumm_binary import verify_room_binary
from .scumm_launch import launch_smoke
from .scumm_room_fixture import native_room
from .scumm_toolchain import _tool


def black_costume_pixels(screenshot: Path) -> int:
    """Count dark costume pixels in the fixed end-of-walk scene crop.

    This region excludes ScummVM's dark letterbox, verb labels and cursor.
    It is a measurement, not a proof of occlusion by itself.
    """
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", "140x105+535+305", "+repage",
         "-format", "%c", "histogram:info:"],
        capture_output=True, text=True, check=True, timeout=15,
    )
    total = 0
    for line in result.stdout.splitlines():
        match = re.match(r"^\s*(\d+):\s*\((\d+),(\d+),(\d+)\)", line)
        if match:
            count, red, green, blue = map(int, match.groups())
            if max(red, green, blue) <= 12:
                total += count
    return total


def run_visual_comparison(upstream: Path, generated: Path, destination: Path) -> dict:
    """Build and capture mask-on, mask-off and differently scaled variants."""
    compiler = _tool(upstream, "scc")
    linker = _tool(upstream, "sld")
    road = upstream / "examples" / "road"
    goal_manifest = generated / "game-goal.json"
    if not goal_manifest.is_file():
        raise ValueError("Native visual probe requires the generated game-goal manifest")
    destination.mkdir(parents=True, exist_ok=True)
    results = {}
    variants = (("masked", True, 180), ("unmasked", False, 180),
                ("fullscale", False, 255))
    for label, occlusion, scale in variants:
        root = destination / label
        root.mkdir(parents=True, exist_ok=True)
        room = native_room(occlusion=occlusion, far_scale=scale)
        write_room_sources(room, root)
        shutil.copyfile(goal_manifest, root / "game-goal.json")
        subprocess.run([
            str(compiler), "-V", "6", "-I", str(upstream / "include"),
            "-I", str(generated), "-I", str(road), "-R", str(root),
            "-o", str(root / "Harbor.roobj"), str(root / "Harbor.scc"),
        ], check=True, timeout=120)
        subprocess.run([
            str(linker), "-o", str(root / "tentacle"), "-key", "0x69",
            str(generated / "bootstrap.roobj"), str(root / "Harbor.roobj"),
            str(generated / "Cellar.roobj"),
        ], cwd=road, check=True, timeout=120)
        binary = (root / "tentacle.001").read_bytes()
        verify_room_binary(binary, xor_key=0x69)
        images = destination / f"{label}-screenshots"
        launch_smoke(root, images, scene_only=True)
        end = images / "scummvm-end.png"
        results[label] = {
            "mask_enabled": occlusion,
            "box_scale": scale,
            "dark_costume_pixels": black_costume_pixels(end),
            "frame_report": json.loads((images / "scummvm-frame-report.json").read_text()),
        }
    results["comparison"] = {
        "occlusion_difference": results["unmasked"]["dark_costume_pixels"] -
                                results["masked"]["dark_costume_pixels"],
        "scale_difference": results["fullscale"]["dark_costume_pixels"] -
                            results["unmasked"]["dark_costume_pixels"],
        "status": "diagnostic; differences require visual review before acceptance",
    }
    (destination / "native-room-visual-comparison.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_room_visual_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_visual_comparison(Path(sys.argv[1]), Path(sys.argv[2]),
                                           Path(sys.argv[3])), indent=2))

"""Compile two native v6 camera tracks and compare their stock-ScummVM views."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from .scumm_assets import CameraCue
from .scumm_room_fixture import native_room
from .scumm_room_visual_probe import render_native_room


def changed_camera_pixels(first: Path, second: Path) -> int:
    """ImageMagick AE measures exact whole-screen pixel differences."""
    result = subprocess.run(["compare", "-metric", "AE", str(first), str(second), "null:"],
                            capture_output=True, text=True, timeout=20)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"Cannot compare native camera screens: {result.stderr}")
    try:
        return int(result.stderr.strip())
    except ValueError as exc:
        raise RuntimeError("Invalid ImageMagick camera metric") from exc


def verify_camera_pan(differences: int) -> None:
    if type(differences) is not int or differences < 10000:
        raise RuntimeError(f"Native camera did not visibly change the composition: {differences}")


def run_camera_probe(upstream: Path, generated: Path, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    base = replace(native_room(occlusion=False), demo_walk_to_x=None)
    scenes = {
        "camera_static": (CameraCue("set", 160),),
        "camera_panned": (CameraCue("set", 160), CameraCue("pan", 480), CameraCue("wait")),
    }
    results = {}
    for name, cues in scenes.items():
        results[name] = render_native_room(replace(base, camera_cues=cues), upstream,
                                           generated, destination, name,
                                           allow_static_scene=True)
    differences = changed_camera_pixels(
        destination / "camera_static-screenshots" / "scummvm-end.png",
        destination / "camera_panned-screenshots" / "scummvm-end.png",
    )
    verify_camera_pan(differences)
    results["comparison"] = {"changed_pixels": differences, "native_camera_pan_passed": True}
    (destination / "native-camera-pan-report.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_camera_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_camera_probe(Path(sys.argv[1]), Path(sys.argv[2]),
                                      Path(sys.argv[3])), indent=2))

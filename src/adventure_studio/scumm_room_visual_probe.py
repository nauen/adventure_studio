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

from .scumm_assets import RoomAsset, destination_fixture, write_room_sources
from .scumm_binary import verify_room_binary
from .scumm_launch import launch_smoke
from .scumm_room_fixture import native_room
from .scumm_project import GameDocument, canonical_json, parse_document
from .studio_sequences import import_room_zplane
from .scumm_toolchain import _tool


def black_costume_pixels(screenshot: Path, crop: str = "140x105+535+305") -> int:
    """Count dark costume pixels in the fixed end-of-walk scene crop.

    This region excludes ScummVM's dark letterbox, verb labels and cursor.
    It is a measurement, not a proof of occlusion by itself.
    """
    if not re.fullmatch(r"\d+x\d+\+\d+\+\d+", crop):
        raise ValueError("Invalid costume crop geometry")
    result = subprocess.run(
        ["convert", str(screenshot), "-crop", crop, "+repage",
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


def verify_visual_effects(masked: int, unmasked: int, fullscale: int) -> dict:
    """Accept only a strong, controlled occlusion and actor-size difference.

    The fixture's colored background and fixed crop have already been checked
    independently by launch_smoke; this compares only the costume silhouette.
    """
    if any(type(value) is not int or value < 0 for value in (masked, unmasked, fullscale)):
        raise ValueError("Invalid costume histogram counts")
    if unmasked < 100:
        raise RuntimeError("Unmasked actor not visible enough for a mask comparison")
    if masked > unmasked // 3:
        raise RuntimeError("Z-plane mask did not visibly occlude the actor")
    if fullscale < (unmasked * 3) // 2:
        raise RuntimeError("Walkbox scale did not visibly increase costume size")
    return {
        "occlusion_pixels_removed": unmasked - masked,
        "scale_pixels_added": fullscale - unmasked,
        "occlusion_passed": True,
        "walkbox_constant_scale_passed": True,
    }


def render_native_room(room: RoomAsset, upstream: Path, generated: Path,
                       destination: Path, label: str, *, crop: str = "140x105+535+305",
                       allow_static_scene: bool = False,
                       initial_object_state2: str | None = None,
                       scene_walk_clicks: tuple[tuple[str, int, int], ...] = (),
                       native_walkbox_gate_probe: bool = False,
                       native_reversible_walkbox_probe: bool = False,
                       native_reversible_gate_save_probe: bool = False,
                       native_gate_room_return_probe: bool = False) -> dict:
    """Compile, link, run and measure exactly one independently authored room."""
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", label):
        raise ValueError("Invalid native visual probe label")
    compiler = _tool(upstream, "scc")
    linker = _tool(upstream, "sld")
    road = upstream / "examples" / "road"
    goal_manifest = generated / "game-goal.json"
    if not goal_manifest.is_file():
        raise ValueError("Native visual probe requires the generated game-goal manifest")
    root = destination / label
    root.mkdir(parents=True, exist_ok=True)
    write_room_sources(room, root)
    if initial_object_state2 is not None:
        # Native visual fixture only: select the second, product-exported
        # object image state at room entry without automating a puzzle click.
        # The generated IM02 sprite/Z-plane and the SCUMM VM are unmodified.
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", initial_object_state2):
            raise ValueError("Invalid fixture object id")
        script = root / f"{room.name}.scc"
        source = script.read_text(encoding="utf-8")
        pattern = (r"(    object " + re.escape(initial_object_state2)
                   + r" \{\n(?:[^\n]*\n)*?        states = [^\n]+;\n)"
                   + r"        state = 1;")
        changed, count = re.subn(pattern, r"\g<1>        state = 2;", source, count=1)
        if count != 1:
            raise ValueError("Second-state fixture requires an exported two-state object")
        script.write_text(changed, encoding="utf-8")
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
    verify_room_binary((root / "tentacle.001").read_bytes(), xor_key=0x69)
    images = destination / f"{label}-screenshots"
    launch_smoke(root, images, scene_only=not native_walkbox_gate_probe,
                 verify_return=False, allow_static_scene=allow_static_scene,
                 sample_scene_frames=native_walkbox_gate_probe,
                 native_walkbox_gate_probe=native_walkbox_gate_probe,
                 native_reversible_walkbox_probe=native_reversible_walkbox_probe,
                 native_reversible_gate_save_probe=native_reversible_gate_save_probe,
                 native_gate_room_return_probe=native_gate_room_return_probe,
                 scene_walk_clicks=scene_walk_clicks)
    return {
        "dark_costume_pixels": black_costume_pixels(images / "scummvm-end.png", crop),
        "frame_report": json.loads((images / "scummvm-frame-report.json").read_text()),
    }


def run_visual_comparison(upstream: Path, generated: Path, destination: Path) -> dict:
    """Build and capture mask-on, mask-off and differently scaled variants."""
    destination.mkdir(parents=True, exist_ok=True)
    results = {}
    variants = (("masked", True, 180), ("unmasked", False, 180),
                ("fullscale", False, 255))
    for label, occlusion, scale in variants:
        # Exercise the *authored* project path, not just the native ZPlane
        # fixture: PNG → JSON model → ScummC ZPxx → stock ScummVM pixels.
        from PIL import Image

        base = native_room(occlusion=False, far_scale=scale)
        width, height = base.geometry.room_width, base.geometry.room_height
        pixels = bytes(255 if occlusion and x > width // 2 and 60 < y < 110 else 0
                       for y in range(height) for x in range(width))
        png = destination / f"{label}-authored-zplane.png"
        Image.frombytes("L", (width, height), pixels).save(png)
        project = canonical_json(GameDocument("authored_mask", (base, destination_fixture())))
        authored = import_room_zplane(project, base.name, 1, str(png))
        room = parse_document(authored).rooms[0]
        results[label] = {
            "mask_enabled": occlusion,
            "box_scale": scale,
            "mask_authoring": "PNG → native project JSON → ZPxx",
            **render_native_room(room, upstream, generated, destination, label),
        }
    results["comparison"] = verify_visual_effects(
        results["masked"]["dark_costume_pixels"],
        results["unmasked"]["dark_costume_pixels"],
        results["fullscale"]["dark_costume_pixels"],
    )
    (destination / "native-room-visual-comparison.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m adventure_studio.scumm_room_visual_probe UPSTREAM GENERATED OUTPUT")
    print(json.dumps(run_visual_comparison(Path(sys.argv[1]), Path(sys.argv[2]),
                                           Path(sys.argv[3])), indent=2))

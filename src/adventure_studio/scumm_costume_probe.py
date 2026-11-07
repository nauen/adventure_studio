"""Generate a source-independent v6 Costume with two explicit COUNT events."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import shutil

from .scumm_binary import verify_room_binary
from .scumm_launch import launch_smoke

from .scumm_costume import (CostumeAnimation, CostumeAsset, CostumeDirection,
                            CostumeFrame, write_costume_sources)
from .scumm_toolchain import _tool


def gesture_fixture() -> CostumeAsset:
    palette = tuple((i * 3 % 256, i * 5 % 256, i * 7 % 256) for i in range(48))
    frames = []
    for index in range(3):
        pixels = bytes(17 if (4 + index <= x < 12 + index and 4 <= y < 20)
                       else 16 for y in range(24) for x in range(16))
        frames.append(CostumeFrame(f"Pose{index}", 16, 24, pixels, -8, -23))
    base_directions = tuple(CostumeDirection(d, ("Pose0", "Pose1", "Pose2"))
                            for d in ("N", "E", "S", "W"))
    stand_directions = tuple(CostumeDirection(d, ("Pose0",))
                             for d in ("N", "E", "S", "W"))
    return CostumeAsset("NativeGesture", palette, tuple(frames), (
        CostumeAnimation("walk", base_directions),
        CostumeAnimation("stand", stand_directions),
        CostumeAnimation("init", stand_directions),
        CostumeAnimation("gesture", (CostumeDirection(
            "S", ("Pose0", "COUNT", "Pose1", "COUNT", "Pose2"), loop=False),), 24),
    ))


def run_costume_probe(upstream: Path, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    costume = gesture_fixture()
    source, frames = write_costume_sources(costume, destination)
    output = destination / "NativeGesture.cost"
    subprocess.run([str(_tool(upstream, "cost")), "-o", str(output),
                    "-I", str(destination), str(source)], check=True, timeout=120)
    data = output.read_bytes()
    if len(data) < 20 or data[:4] != b"COST" or int.from_bytes(data[4:8], "big") != len(data):
        raise RuntimeError("ScummC did not produce a valid outer COST chunk")
    result = {"native_cost_compiler_passed": True, "size": len(data),
              "frame_count": len(frames), "explicit_count_commands": 2,
              "linked_in_scummvm": False}
    (destination / "native-costume-report.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def run_costume_playback(upstream: Path, generated: Path, destination: Path) -> dict:
    """Link Studio-authored COST into the stock ScummVM visual game fixture."""
    destination.mkdir(parents=True, exist_ok=True)
    costume = run_costume_probe(upstream, destination)
    source = (generated / "bootstrap.scc").read_text(encoding="utf-8")
    marker = 'cost egoCost = "devil.cost";'
    if source.count(marker) != 1:
        raise ValueError("Unexpected external SCUMM bootstrap costume declaration")
    (destination / "bootstrap.scc").write_text(
        source.replace(marker, 'cost egoCost = "NativeGesture.cost";', 1), encoding="utf-8")
    road = upstream / "examples" / "road"
    # The independent bootstrap still loads fonts, cursor and inventory art
    # from the upstream GPL fixture; only its COST is replaced in this probe.
    shutil.copyfile(destination / "NativeGesture.cost", road / "NativeGesture.cost")
    subprocess.run([str(_tool(upstream, "scc")), "-V", "6", "-I", str(upstream / "include"),
                    "-I", str(generated), "-I", str(road), "-R", str(road),
                    "-o", str(destination / "bootstrap.roobj"),
                    str(destination / "bootstrap.scc")], check=True, timeout=120)
    subprocess.run([str(_tool(upstream, "sld")), "-o", str(destination / "tentacle"),
                    "-key", "0x69", str(destination / "bootstrap.roobj"),
                    str(generated / "Harbor.roobj"), str(generated / "Cellar.roobj")],
                   cwd=road, check=True, timeout=120)
    verify_room_binary((destination / "tentacle.001").read_bytes(), xor_key=0x69)
    shutil.copyfile(generated / "game-goal.json", destination / "game-goal.json")
    launch_smoke(destination, destination / "screenshots", scene_only=True)
    report = {**costume, "linked_in_scummvm": True}
    (destination / "native-costume-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) == 3:
        result = run_costume_probe(Path(sys.argv[1]), Path(sys.argv[2]))
    elif len(sys.argv) == 4:
        result = run_costume_playback(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        raise SystemExit("Usage: python -m adventure_studio.scumm_costume_probe UPSTREAM [GENERATED] OUTPUT")
    print(json.dumps(result, indent=2))

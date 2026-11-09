"""Generate a source-independent v6 Costume with two explicit COUNT events."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import shutil

from .scumm_binary import verify_room_binary
from .scumm_launch import launch_smoke, visible_key_pixels
from .scumm_room_visual_probe import black_costume_pixels

from .scumm_costume import (CostumeAnimation, CostumeAsset, CostumeDirection,
                            CostumeFrame)
from .scumm_assets import scrolling_fixture, destination_fixture
from .scumm_project import GameDocument, canonical_json, parse_document, export_document
from .scumm_toolchain import _tool


def gesture_fixture() -> CostumeAsset:
    palette = tuple((0, 0, 0) if i in (16, 17, 18)
                    else (i * 3 % 256, i * 5 % 256, i * 7 % 256) for i in range(48))
    frames = []
    for index in range(3):
        pixels = bytes(2 if (4 + index <= x < 12 + index and 4 <= y < 20)
                       else 1 for y in range(24) for x in range(16))
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
    # The native compilation probe exercises the same JSON-backed resource
    # export used by projects, rather than a fixture-only direct COST writer.
    game = GameDocument("NativeCostumeProbe", (scrolling_fixture(), destination_fixture()),
                        (costume,))
    export_document(parse_document(canonical_json(game)), destination)
    source = destination / f"{costume.name}.scost"
    frames = tuple(destination / f"{costume.name}_{frame.id}.bmp" for frame in costume.frames)
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
    # Camera follow and the actor's walk can shift the onscreen X between
    # captures. Cover the whole playfield band, not one fixed actor X.
    silhouette = black_costume_pixels(destination / "screenshots" / "scummvm-end.png",
                                      "240x75+520+260")
    if silhouette < 1200:
        raise RuntimeError(f"Native authored costume silhouette not visible: {silhouette}")
    report = {**costume, "linked_in_scummvm": True,
              "visible_costume_pixels": silhouette, "visual_costume_passed": True}
    (destination / "native-costume-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run_costume_count_gameplay(upstream: Path, generated: Path, destination: Path) -> dict:
    """Verify native COUNT events gate a real object state change in ScummVM."""
    # Deliberately isolate this from the general action schema until the
    # runtime semantics of the exact v6 getter are shown by gameplay.
    playback = destination / "costume-game"
    destination.mkdir(parents=True, exist_ok=True)
    run_costume_playback(upstream, generated, playback)
    source = (generated / "Harbor.scc").read_text(encoding="utf-8")
    marker = "        ResRoom::showCursor();\n"
    if source.count(marker) != 1:
        raise ValueError("Unexpected room entry structure for COUNT evidence")
    road = upstream / "examples" / "road"
    def run_variant(target: Path, required_events: int) -> int:
        target.mkdir(parents=True, exist_ok=True)
        injection = (
            "        delaySeconds(2);\n"
            "        setCameraAt(480);\n"
            "        putActorAt(VAR_EGO, 430, 100, Harbor);\n"
            "        animateActor(VAR_EGO, 24);\n"
            f"        while(getActorAnimCounter1(VAR_EGO) < {required_events}) {{\n"
            "            breakScript();\n"
            "        }\n"
            "        setObjectState(Key, 0);\n"
        )
        (target / "Harbor.scc").write_text(source.replace(marker, marker + injection, 1),
                                            encoding="utf-8")
        subprocess.run([str(_tool(upstream, "scc")), "-V", "6", "-I", str(upstream / "include"),
                        "-I", str(generated), "-I", str(road), "-R", str(generated),
                        "-o", str(target / "Harbor.roobj"), str(target / "Harbor.scc")],
                       check=True, timeout=120)
        subprocess.run([str(_tool(upstream, "sld")), "-o", str(target / "tentacle"),
                        "-key", "0x69", str(playback / "bootstrap.roobj"),
                        str(target / "Harbor.roobj"), str(generated / "Cellar.roobj")],
                       cwd=road, check=True, timeout=120)
        verify_room_binary((target / "tentacle.001").read_bytes(), xor_key=0x69)
        shutil.copyfile(generated / "game-goal.json", target / "game-goal.json")
        launch_smoke(target, target / "screenshots", scene_only=True,
                     allow_static_scene=True)
        return visible_key_pixels(target / "screenshots")

    remaining_key_pixels = run_variant(destination, 2)
    if remaining_key_pixels >= 40:
        raise RuntimeError(f"COUNT-gated object state did not hide key: {remaining_key_pixels}")
    unreachable = destination / "three_count_control"
    control_key_pixels = run_variant(unreachable, 3)
    if control_key_pixels < 40:
        raise RuntimeError(f"Three-COUNT negative control unexpectedly hid key: {control_key_pixels}")
    result = {"native_count_gate_passed": True,
              "remaining_key_pixels": remaining_key_pixels,
              "control_key_pixels": control_key_pixels,
              "expected_count_events": 2}
    (destination / "native-count-gameplay-report.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    if len(sys.argv) == 3:
        result = run_costume_probe(Path(sys.argv[1]), Path(sys.argv[2]))
    elif len(sys.argv) == 4:
        result = run_costume_playback(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    elif len(sys.argv) == 5 and sys.argv[1] == "--count":
        result = run_costume_count_gameplay(Path(sys.argv[2]), Path(sys.argv[3]),
                                             Path(sys.argv[4]))
    else:
        raise SystemExit("Usage: python -m adventure_studio.scumm_costume_probe UPSTREAM [GENERATED] OUTPUT")
    print(json.dumps(result, indent=2))

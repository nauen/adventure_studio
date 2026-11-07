"""Native research acceptance: multiple project-authored Actors share a COST."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from .scumm_assets import destination_fixture, scrolling_fixture
from .scumm_costume_probe import gesture_fixture
from .scumm_launch import launch_smoke
from .scumm_launch import visible_key_pixels
from .scumm_binary import verify_room_binary
from .scumm_project import ActorAsset, GameDocument, canonical_json, export_document, parse_document
from .scumm_toolchain import _tool, compile_story_game


def actor_count_room_source(source: str, required: int) -> str:
    """Add a native COUNT observer to the isolated generated-room fixture."""
    marker = "        ResRoom::showCursor();\n"
    if source.count(marker) != 1 or type(required) is not int or required not in (2, 3):
        raise ValueError("Invalid native Actor COUNT probe source or event threshold")
    injection = (
        "        delaySeconds(2);\n"
        "        setCameraAt(480);\n"
        f"        while(getActorAnimCounter1(Companion) < {required}) {{\n"
        "            breakScript();\n"
        "        }\n"
        "        setObjectState(Key, 0);\n"
    )
    return source.replace(marker, marker + injection, 1)


def run_actor_probe(upstream: Path, destination: Path) -> dict:
    build = destination / "build"
    resources = build / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    costume = replace(gesture_fixture(), name="StudioCompanionCostume")
    document = GameDocument("NativeActorProbe", (scrolling_fixture(), destination_fixture()),
                            (costume,), (
                                ActorAsset("Companion", costume.name, "Harbor", 410, 110, "S", "Companion",
                                           "gesture"),
                                ActorAsset("Guide", costume.name, "Harbor", 470, 110, "E", "Guide"),
                            ))
    encoded = canonical_json(document)
    (build / "project.json").write_text(encoded, encoding="utf-8")
    export_document(parse_document(encoded), resources)
    game = compile_story_game(build, upstream, destination / "game")
    launch_smoke(game, destination / "screenshots", scene_only=True)
    result = {"native_actor_link_passed": True, "stock_scummvm_launch_passed": True,
              "actor_count": len(document.actors), "shared_costume_count": len(document.costumes),
              "actors": [actor.id for actor in document.actors],
              "initial_animation_compiled": True,
              "animation_gameplay_verified": False}
    (destination / "native-actor-report.json").write_text(json.dumps(result, indent=2) + "\n",
                                                             encoding="utf-8")
    return result


def run_actor_count_probe(upstream: Path, destination: Path) -> dict:
    """Prove two authored-Actor COUNT events, with a three-event control."""
    base = destination / "base"
    run_actor_probe(upstream, base)
    resources = base / "build" / "resources"
    source = (resources / "Harbor.scc").read_text(encoding="utf-8")
    road = upstream / "examples" / "road"

    def run_variant(target: Path, required: int) -> int:
        target.mkdir(parents=True, exist_ok=True)
        room_source = target / "Harbor.scc"
        room_source.write_text(actor_count_room_source(source, required), encoding="utf-8")
        room_object = target / "Harbor.roobj"
        subprocess.run([str(_tool(upstream, "scc")), "-V", "6",
                        "-I", str(upstream / "include"), "-I", str(resources),
                        "-I", str(road), "-R", str(resources),
                        "-o", str(room_object), str(room_source)], check=True, timeout=120)
        subprocess.run([str(_tool(upstream, "sld")), "-o", str(target / "tentacle"),
                        "-key", "0x69", str(resources / "bootstrap.roobj"),
                        str(room_object), str(resources / "Cellar.roobj")],
                       cwd=road, check=True, timeout=120)
        verify_room_binary((target / "tentacle.001").read_bytes(), xor_key=0x69)
        shutil.copyfile(resources / "game-goal.json", target / "game-goal.json")
        launch_smoke(target, target / "screenshots", scene_only=True,
                     allow_static_scene=True)
        return visible_key_pixels(target / "screenshots")

    positive = run_variant(destination / "two_counts", 2)
    control = run_variant(destination / "three_counts", 3)
    if positive >= 40:
        raise RuntimeError(f"Authored Actor's two COUNT events did not hide key: {positive}")
    if control < 40:
        raise RuntimeError(f"Three-COUNT control unexpectedly hid key: {control}")
    report = {"authored_actor_count_verified": True, "expected_events": 2,
              "positive_key_pixels": positive, "control_key_pixels": control}
    (destination / "actor-count-report.json").write_text(json.dumps(report, indent=2) + "\n",
                                                               encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) == 3:
        print(run_actor_probe(Path(sys.argv[1]), Path(sys.argv[2])))
    elif len(sys.argv) == 4 and sys.argv[1] == "--count":
        print(run_actor_count_probe(Path(sys.argv[2]), Path(sys.argv[3])))
    else:
        raise SystemExit("Usage: python -m adventure_studio.scumm_actor_probe [--count] SCUMMC_DIR OUTPUT_DIR")

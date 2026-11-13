"""R09: two independent authored door/BOXM gates in one stock-ScummVM game.

The Story provides both rooms and inventory puzzles. Studio adds a separate
reversible native walkbox to each room, then uses the productive ScummC export.
The existing real mouse-driven two-door chain verifies both native Use actions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .scumm_launch import launch_smoke
from .scumm_project import export_document, parse_document
from .scumm_toolchain import compile_story_game
from .story_document import build_story_document
from .studio_sequences import (author_room_box_connections, author_room_walkbox,
                               author_room_walkbox_gate, compose_story_project)


def run_independent_gate_chain(upstream: Path, output: Path) -> dict:
    story = (Path(__file__).resolve().parents[2] / "examples" /
             "mini_story_chain.json").read_text(encoding="utf-8")
    build = output / "build"
    build.mkdir(parents=True, exist_ok=True)
    built = build_story_document(story, build)
    raw = built.project_json.read_text(encoding="utf-8")
    for room_name, door_id in (("Harbor", "Door"), ("Cellar", "Door2")):
        for box, corners in (
                (1, "0,70; 110,70; 110,150; 0,150"),
                (2, "110,70; 240,70; 240,108; 110,108"),
                (3, "110,112; 240,112; 240,150; 110,150"),
                (4, "240,70; 639,70; 639,150; 240,150")):
            raw = author_room_walkbox(raw, room_name, box, corners)
        raw = author_room_box_connections(
            raw, room_name, "1-2; 2-4; 1-3; 3-4")
        raw = author_room_walkbox_gate(
            raw, room_name, door_id, 2, reversible=True)
    authored = parse_document(compose_story_project(story, raw))
    for room, door in (("Harbor", "Door"), ("Cellar", "Door2")):
        actual = next(r for r in authored.rooms if r.name == room)
        gates = [rule for rule in actual.use_rules if rule.unlock_walkbox is not None]
        if len(gates) != 1 or gates[0].target_id != door or (
                gates[0].unlock_walkbox != 2 or not gates[0].reversible_walkbox):
            raise RuntimeError(f"Story composition changed {room}'s authored native gate")
    built.project_json.write_text(raw, encoding="utf-8")
    export_document(parse_document(raw), built.resource_directory)
    game = compile_story_game(build, upstream, output / "game")
    frames = output / "screenshots"
    launch_smoke(game, frames, verify_chain=True,
                 native_independent_gate_chain_probe=True)
    native = json.loads((frames / "scummvm-native-independent-gates-report.json").read_text())
    if not (native["native_two_room_gates_executed"]
            and native["return_preserved_both_states"]):
        raise RuntimeError("Independent native gates did not survive the real chain")
    report = {"native_two_room_gate_gameplay": native,
              "rooms": ["Harbor", "Cellar"],
              "authoring": "Studio UseRule -> JSON-v1/Story -> ScummC-v6 -> stock ScummVM"}
    (output / "native-r09-independent-gates-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_independent_gate_chain_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_independent_gate_chain(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))

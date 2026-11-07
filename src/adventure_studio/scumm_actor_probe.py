"""Native research acceptance: multiple project-authored Actors share a COST."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

from .scumm_assets import destination_fixture, scrolling_fixture
from .scumm_costume_probe import gesture_fixture
from .scumm_launch import launch_smoke
from .scumm_project import ActorAsset, GameDocument, canonical_json, export_document, parse_document
from .scumm_toolchain import compile_story_game


def run_actor_probe(upstream: Path, destination: Path) -> dict:
    build = destination / "build"
    resources = build / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    costume = replace(gesture_fixture(), name="StudioCompanionCostume")
    document = GameDocument("NativeActorProbe", (scrolling_fixture(), destination_fixture()),
                            (costume,), (
                                ActorAsset("Companion", costume.name, "Harbor", 410, 110, "W", "Companion"),
                                ActorAsset("Guide", costume.name, "Harbor", 470, 110, "E", "Guide"),
                            ))
    encoded = canonical_json(document)
    (build / "project.json").write_text(encoded, encoding="utf-8")
    export_document(parse_document(encoded), resources)
    game = compile_story_game(build, upstream, destination / "game")
    launch_smoke(game, destination / "screenshots", scene_only=True)
    result = {"native_actor_link_passed": True, "stock_scummvm_launch_passed": True,
              "actor_count": len(document.actors), "shared_costume_count": len(document.costumes),
              "actors": [actor.id for actor in document.actors]}
    (destination / "native-actor-report.json").write_text(json.dumps(result, indent=2) + "\n",
                                                             encoding="utf-8")
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_actor_probe SCUMMC_DIR OUTPUT_DIR")
    print(run_actor_probe(Path(sys.argv[1]), Path(sys.argv[2])))

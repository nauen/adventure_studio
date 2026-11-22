"""R06 #268: stock-ScummVM smoke for two authored Actors and four room Z-planes.

This is the first native integration stage, NOT proof that both Actors move
independently or that each is occluded throughout a camera round-trip.
Those additional gameplay conditions require separate captured evidence.
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

from .scumm_costume_probe import gesture_fixture
from .scumm_four_mask_camera_probe import _author_project
from .scumm_launch import launch_smoke
from .scumm_project import (ActorAsset, InteractionSequence, WalkActorStep, WaitActorStep,
                            canonical_json, export_document, parse_document)
from .scumm_toolchain import compile_story_game


ACTOR_IDS = ("ForegroundWalker", "BackgroundWalker")
ACTOR_STARTS = ((270, 110), (430, 115))


def author_two_actor_four_mask_project(output: Path) -> str:
    """Use productive Studio Z-plane/camera authoring, then add typed Actors."""
    output.mkdir(parents=True, exist_ok=True)
    raw, assignments, _ = _author_project(output, 1, "masked", 170,
                                          moving_actor=True)
    document = parse_document(raw)
    costume = replace(gesture_fixture(), name="R06TwoActorCostume")
    actors = tuple(ActorAsset(name, costume.name, "Harbor", x, y, "S", name)
                   for name, (x, y) in zip(ACTOR_IDS, ACTOR_STARTS))
    choreography = InteractionSequence(
        "Harbor", "Key", "Close", (
            WalkActorStep(ACTOR_IDS[0], 530, 110),
            WalkActorStep(ACTOR_IDS[1], 180, 115),
            WaitActorStep(ACTOR_IDS[0]),
            WaitActorStep(ACTOR_IDS[1]),
        ))
    document = replace(document, costumes=(*document.costumes, costume),
                       actors=(*document.actors, *actors),
                       interaction_sequences=(*document.interaction_sequences, choreography))
    result = canonical_json(document)
    parsed = parse_document(result)
    assert_native_two_actor_authoring(parsed, assignments)
    return result


def assert_native_two_actor_authoring(document, expected_masks=(0, 1, 2, 3, 4)) -> dict:
    """Fail closed before export if the independent actor bindings are lost."""
    room = next((room for room in document.rooms if room.name == "Harbor"), None)
    if room is None or len(room.zplanes) != 4 or len(room.walkboxes) != 5:
        raise RuntimeError("R06 requires four Z-planes and five connected walkboxes")
    if [box.mask for box in room.walkboxes] != list(expected_masks):
        raise RuntimeError("R06 four native BOXD mask assignments changed")
    by_id = {actor.id: actor for actor in document.actors}
    if any(name not in by_id for name in ACTOR_IDS):
        raise RuntimeError("R06 independent Actors missing from JSON-v1")
    if len(set(ACTOR_IDS)) != 2 or any(
            (by_id[name].room, by_id[name].x, by_id[name].y) !=
            ("Harbor", x, y)
            for name, (x, y) in zip(ACTOR_IDS, ACTOR_STARTS)):
        raise RuntimeError("R06 independent Actor world positions changed")
    if len({(by_id[name].x, by_id[name].y) for name in ACTOR_IDS}) != 2:
        raise RuntimeError("R06 Actors are not independently positioned")
    names = {costume.name for costume in document.costumes}
    if any(by_id[name].costume not in names for name in ACTOR_IDS):
        raise RuntimeError("R06 Actors have unresolved native COST bindings")
    if room.demo_walk_to_x != 535 or len(room.camera_cues) != 8:
        raise RuntimeError("R06 moving ego/camera plan was lost")
    choreography = [sequence for sequence in document.interaction_sequences
                    if (sequence.room, sequence.hotspot_id, sequence.verb) ==
                    ("Harbor", "Key", "Close")]
    expected_steps = (
        WalkActorStep(ACTOR_IDS[0], 530, 110),
        WalkActorStep(ACTOR_IDS[1], 180, 115),
        WaitActorStep(ACTOR_IDS[0]),
        WaitActorStep(ACTOR_IDS[1]),
    )
    if len(choreography) != 1 or choreography[0].steps != expected_steps:
        raise RuntimeError("Independent native Actor walk commands missing")
    return {"four_zplanes": True, "native_actor_count": len(ACTOR_IDS),
            "actor_ids": list(ACTOR_IDS), "distinct_actor_positions": True,
            "camera_roundtrip_authored": True,
            "two_native_actor_walks_authored": True,
            "independent_actor_motion_verified": False,
            "per_actor_native_occlusion_verified": False}


def run(upstream: Path, output: Path) -> dict:
    """Compile and launch the *same* authored room in stock ScummVM."""
    output.mkdir(parents=True, exist_ok=True)
    build = output / "build"
    resources = build / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    project = author_two_actor_four_mask_project(output)
    (build / "project.json").write_text(project, encoding="utf-8")
    document = parse_document(project)
    authoring = assert_native_two_actor_authoring(document)
    export_document(document, resources)
    game = compile_story_game(build, upstream, output / "game")
    launch_smoke(game, output / "screenshots", scene_only=True,
                 allow_static_scene=True)
    report = {"product_path": "Studio PNG -> JSON-v1/Story -> ScummC-v6 -> stock ScummVM",
              "native_link_and_launch_passed": True, "authoring": authoring,
              "complete_r06_268_acceptance": False}
    (output / "native-r06-two-actor-four-mask-report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_two_actor_four_mask_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))

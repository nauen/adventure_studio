"""R06 #272: independently authored opposing native Actor routes.

Only real stock-ScummVM screenshots can establish completion. This module
does not redefine the existing R06 four-mask visibility thresholds.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_project import (
    WalkActorStep, WaitActorStep, FollowActorCameraStep, PanCameraStep,
    WaitCameraStep, DelayStep, canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    ACTOR_IDS, author_two_actor_four_mask_project,
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip,
    measure_two_actor_native_mask_comparison,
)


STARTS = {ACTOR_IDS[0]: (260, 85), ACTOR_IDS[1]: (545, 135)}
DESTINATIONS = {ACTOR_IDS[0]: (530, 85), ACTOR_IDS[1]: (175, 135)}


def author_opposing_native_actor_project(output: Path, *, variant: str = "masked") -> str:
    """Keep native ZP01–ZP04/BOXD and author real opposite-direction walks."""
    project = parse_document(author_two_actor_four_mask_project(output, variant=variant))
    # Geometry CI reuses its upstream ScummC fixture across native probes.
    # Each game must have a distinct COST resource filename and Actor binding.
    original_costume = project.costumes[-1]
    unique_costume = "R06Opposing" + variant.replace("-", "").title() + "Costume"
    project = replace(
        project,
        costumes=(*project.costumes[:-1],
                  replace(original_costume, name=unique_costume)),
    )
    actors = tuple(
        replace(actor, costume=unique_costume,
                x=STARTS[actor.id][0], y=STARTS[actor.id][1])
        if actor.id in STARTS else actor for actor in project.actors
    )
    sequences = []
    for sequence in project.interaction_sequences:
        if (sequence.room, sequence.hotspot_id, sequence.verb) != ("Harbor", "Key", "Close"):
            sequences.append(sequence)
            continue
        sequences.append(replace(sequence, steps=(
            WalkActorStep(ACTOR_IDS[0], *DESTINATIONS[ACTOR_IDS[0]]),
            WalkActorStep(ACTOR_IDS[1], *DESTINATIONS[ACTOR_IDS[1]]),
            FollowActorCameraStep(ACTOR_IDS[0]),
            WaitActorStep(ACTOR_IDS[0]),
            WaitActorStep(ACTOR_IDS[1]),
            PanCameraStep(480), WaitCameraStep(), DelayStep(2),
            PanCameraStep(160), WaitCameraStep(),
        )))
    # Native screenshots proved that camera X=320 cropped the right-hand
    # Actor's 545px starting position. At X=400 both independent costumes
    # are visible before input, and the four native mask zones still lie
    # along each real engine walk. Preserve the full authored pan/return.
    rooms = tuple(
        replace(room, camera_cues=(
            *room.camera_cues[:-1],
            replace(room.camera_cues[-1], x=400),
        )) if room.name == "Harbor" else room
        for room in project.rooms
    )
    document = replace(project, rooms=rooms, actors=actors,
                       interaction_sequences=tuple(sequences))
    verdict = assert_opposing_native_actor_project(document, variant=variant)
    if verdict["native_opposing_gameplay_verified"]:
        raise AssertionError("Authoring must never claim real native gameplay")
    return canonical_json(document)


def assert_opposing_native_actor_project(document, *, variant: str = "masked") -> dict:
    """Reject a lost mask, actor route or opposite-direction choreography."""
    if variant not in ("masked", "transparent", "wrong-box"):
        raise ValueError("Unknown R06 opposing-route native control")
    room = next((r for r in document.rooms if r.name == "Harbor"), None)
    masks = [1, 0, 0, 0, 0] if variant == "wrong-box" else [0, 1, 2, 3, 4]
    if room is None or len(room.zplanes) != 4 or len(room.walkboxes) != 5:
        raise RuntimeError("R06 opposing routes require exactly four room Z-planes")
    if [box.mask for box in room.walkboxes] != masks:
        raise RuntimeError("R06 opposing routes lost native BOXD mask binding")
    if (not room.camera_cues or room.camera_cues[-1].operation != "set"
            or room.camera_cues[-1].x != 400):
        raise RuntimeError("R06 opposing Actor starts must both be camera-visible")
    actor_by_id = {actor.id: actor for actor in document.actors}
    if any(actor not in actor_by_id for actor in ACTOR_IDS):
        raise RuntimeError("R06 opposing routes lost native Actor")
    for name in ACTOR_IDS:
        actor = actor_by_id[name]
        if (actor.room, actor.x, actor.y) != ("Harbor", *STARTS[name]):
            raise RuntimeError("R06 opposing Actor start position was changed")
    sequences = [
        sequence for sequence in document.interaction_sequences
        if (sequence.room, sequence.hotspot_id, sequence.verb) == ("Harbor", "Key", "Close")
    ]
    expected = (
        WalkActorStep(ACTOR_IDS[0], *DESTINATIONS[ACTOR_IDS[0]]),
        WalkActorStep(ACTOR_IDS[1], *DESTINATIONS[ACTOR_IDS[1]]),
        FollowActorCameraStep(ACTOR_IDS[0]),
        WaitActorStep(ACTOR_IDS[0]), WaitActorStep(ACTOR_IDS[1]),
        PanCameraStep(480), WaitCameraStep(), DelayStep(2),
        PanCameraStep(160), WaitCameraStep(),
    )
    if len(sequences) != 1 or sequences[0].steps != expected:
        raise RuntimeError("R06 two independent, opposite native walk commands missing")
    if not (STARTS[ACTOR_IDS[0]][0] < DESTINATIONS[ACTOR_IDS[0]][0]
            and STARTS[ACTOR_IDS[1]][0] > DESTINATIONS[ACTOR_IDS[1]][0]):
        raise RuntimeError("Actor routes do not move in opposite world directions")
    return {
        "native_opposing_walks_authored": True,
        "four_native_room_masks_authored": True,
        "native_opposing_gameplay_verified": False,
    }


def verify_opposing_native_motion(traces: dict) -> dict:
    """Require pixel-measured simultaneous opposite motion across four zones."""
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Two separately tracked native Actors required")
    tracks = {
        actor: sorted(traces[actor], key=lambda row: row["seconds"])
        for actor in ACTOR_IDS
    }
    zones = ((160, 320), (320, 400), (400, 500), (500, 640))
    for actor in ACTOR_IDS:
        rows = tracks[actor]
        if len(rows) < 8 or len({row["frame"] for row in rows}) != len(rows):
            raise RuntimeError(f"Too few native frames for {actor}")
        world = [row["world_x"] for row in rows]
        if max(world) - min(world) < 250:
            raise RuntimeError(f"Actor {actor} did not traverse the room")
        visits = [next((row["seconds"] for row in rows if left <= row["world_x"] < right), None)
                  for left, right in zones]
        if any(t is None for t in visits):
            raise RuntimeError(f"Actor {actor} did not visit all four ZP mask regions")
        if actor == ACTOR_IDS[0] and visits != sorted(visits):
            raise RuntimeError("First Actor did not walk left to right")
        if actor == ACTOR_IDS[1] and visits != sorted(visits, reverse=True):
            raise RuntimeError("Second Actor did not walk right to left")
    by_frame = {
        actor: {row["frame"]: row for row in tracks[actor]}
        for actor in ACTOR_IDS
    }
    shared = sorted(set(by_frame[ACTOR_IDS[0]]) & set(by_frame[ACTOR_IDS[1]]),
                    key=lambda frame: by_frame[ACTOR_IDS[0]][frame]["seconds"])
    simultaneous = []
    for first, second in zip(shared, shared[1:]):
        before_a, after_a = (by_frame[ACTOR_IDS[0]][first],
                             by_frame[ACTOR_IDS[0]][second])
        before_b, after_b = (by_frame[ACTOR_IDS[1]][first],
                             by_frame[ACTOR_IDS[1]][second])
        if (after_a["world_x"] - before_a["world_x"] >= 5
                and before_b["world_x"] - after_b["world_x"] >= 5):
            simultaneous.append(second)
    if len(simultaneous) < 3:
        raise RuntimeError("No simultaneous opposite native Actor movement")
    return {"native_opposing_motion_verified": True,
            "simultaneous_opposing_frames": simultaneous,
            "actor_frame_counts": {actor: len(tracks[actor]) for actor in ACTOR_IDS}}


def run_native_opposing_actor_probe(upstream: Path, output: Path) -> dict:
    """Compile three independent control games and measure stock-ScummVM pixels."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "native_opposing_gameplay_verified": False,
              "complete_r06_272_acceptance": False}
    report_path = output / "native-r06-opposing-report.json"

    def persist():
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        authored = author_opposing_native_actor_project(root, variant=variant)
        (build / "project.json").write_text(authored, encoding="utf-8")
        document = parse_document(authored)
        assert_opposing_native_actor_project(document, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True)
        report["variants"][variant] = {"linked_and_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    traces = track_native_actor_lanes(transparent)
    report["native_opposing_motion"] = verify_opposing_native_motion(traces)
    report["camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_mask_comparison"] = measure_two_actor_native_mask_comparison(output, traces)
    report["native_opposing_gameplay_verified"] = True
    report["complete_r06_272_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_opposing_actor_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_opposing_actor_probe(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))

"""R06 #270: explicitly authored native camera hand-off between two walking Actors.

The authoring guard proves typed JSON-v1/Story camera commands, not native
visual completion. A stock-ScummVM gameplay run and negative controls remain
mandatory for final acceptance.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_project import (
    DelayStep, FollowActorCameraStep, InteractionSequence,
    PanCameraStep, WaitActorStep, WaitCameraStep, WalkActorStep,
    canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    ACTOR_IDS, author_two_actor_four_mask_project,
    track_native_actor_lanes, verify_two_actor_native_walks,
    measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip,
    measure_two_actor_native_mask_comparison,
)


def author_native_camera_handoff_project(output: Path, *, variant: str = "masked") -> str:
    """Extend the productive R06 two-Actor/4-ZP project with a true focus switch."""
    if variant not in ("masked", "transparent", "wrong-box"):
        raise ValueError("Unknown native R06 camera-handoff control")
    original = parse_document(author_two_actor_four_mask_project(output, variant=variant))
    # The parent R06 test compiles into the same upstream ScummC fixture in
    # this geometry CI job. Native COST filenames must not collide with files
    # linked by the earlier test; each variant also needs its own COST name.
    original_costume = original.costumes[-1]
    unique_costume = "R06Handoff" + variant.replace("-", "").title() + "Costume"
    original = replace(
        original,
        costumes=(*original.costumes[:-1],
                  replace(original_costume, name=unique_costume)),
        actors=tuple(
            replace(actor, costume=unique_costume,
                    x=(205 if actor.id == ACTOR_IDS[0] else 175)
                    if actor.id in ACTOR_IDS else actor.x)
            if actor.costume == original_costume.name else actor
            for actor in original.actors
        ),
    )
    sequence = next(sequence for sequence in original.interaction_sequences
                    if (sequence.room, sequence.hotspot_id, sequence.verb)
                    == ("Harbor", "Key", "Close"))
    steps = (
        WalkActorStep(ACTOR_IDS[0], 365, 85),
        WalkActorStep(ACTOR_IDS[1], 325, 135),
        FollowActorCameraStep(ACTOR_IDS[0]),
        DelayStep(1),
        FollowActorCameraStep(ACTOR_IDS[1]),
        WaitActorStep(ACTOR_IDS[0]),
        WaitActorStep(ACTOR_IDS[1]),
        DelayStep(2),
        WalkActorStep(ACTOR_IDS[0], 445, 85),
        WalkActorStep(ACTOR_IDS[1], 415, 135),
        WaitActorStep(ACTOR_IDS[0]),
        WaitActorStep(ACTOR_IDS[1]),
        DelayStep(2),
        WalkActorStep(ACTOR_IDS[0], 530, 85),
        WalkActorStep(ACTOR_IDS[1], 540, 135),
        WaitActorStep(ACTOR_IDS[0]),
        WaitActorStep(ACTOR_IDS[1]),
        DelayStep(2),
        PanCameraStep(480),
        WaitCameraStep(),
        DelayStep(2),
        PanCameraStep(160),
        WaitCameraStep(),
    )
    handoff = replace(sequence, steps=steps)
    document = replace(
        original,
        interaction_sequences=tuple(
            handoff if item is sequence else item
            for item in original.interaction_sequences
        ),
    )
    encoded = canonical_json(document)
    assert_native_camera_handoff(parse_document(encoded), variant=variant)
    return encoded


def assert_native_camera_handoff(document, *, variant: str = "masked") -> dict:
    """Reject lost follow commands and nonoverlapping/missing native actor walks."""
    # Existing R06 authoring checks all masks, costumes, actors and BOXD links;
    # this stage changes the action sequence intentionally and validates it here.
    room = next((room for room in document.rooms if room.name == "Harbor"), None)
    expected_masks = [1, 0, 0, 0, 0] if variant == "wrong-box" else [0, 1, 2, 3, 4]
    if variant not in ("masked", "transparent", "wrong-box"):
        raise ValueError("Unknown native R06 camera-handoff control")
    if room is None or len(room.zplanes) != 4 or [b.mask for b in room.walkboxes] != expected_masks:
        raise RuntimeError("R06 handoff requires all four native ZP mask assignments")
    actors = {actor.id: actor for actor in document.actors}
    if any(actor not in actors for actor in ACTOR_IDS):
        raise RuntimeError("R06 camera handoff lost an authored native Actor")
    sequences = [
        sequence for sequence in document.interaction_sequences
        if (sequence.room, sequence.hotspot_id, sequence.verb)
        == ("Harbor", "Key", "Close")
    ]
    if len(sequences) != 1:
        raise RuntimeError("R06 camera handoff requires one native Close/Key interaction")
    steps = sequences[0].steps
    expected = (
        WalkActorStep(ACTOR_IDS[0], 365, 85),
        WalkActorStep(ACTOR_IDS[1], 325, 135),
        FollowActorCameraStep(ACTOR_IDS[0]),
        DelayStep(1),
        FollowActorCameraStep(ACTOR_IDS[1]),
        WaitActorStep(ACTOR_IDS[0]),
        WaitActorStep(ACTOR_IDS[1]),
        DelayStep(2),
        WalkActorStep(ACTOR_IDS[0], 445, 85),
        WalkActorStep(ACTOR_IDS[1], 415, 135),
        WaitActorStep(ACTOR_IDS[0]),
        WaitActorStep(ACTOR_IDS[1]),
        DelayStep(2),
        WalkActorStep(ACTOR_IDS[0], 530, 85),
        WalkActorStep(ACTOR_IDS[1], 540, 135),
        WaitActorStep(ACTOR_IDS[0]),
        WaitActorStep(ACTOR_IDS[1]),
        DelayStep(2),
        PanCameraStep(480),
        WaitCameraStep(),
        DelayStep(2),
        PanCameraStep(160),
        WaitCameraStep(),
    )
    if steps != expected:
        raise RuntimeError("R06 native camera handoff transition or actor overlap missing")
    if not 160 <= actors[ACTOR_IDS[0]].x < 320 or not 160 <= actors[ACTOR_IDS[1]].x < 320:
        raise RuntimeError("R06 actors must start left of four ZPs")
    if abs(actors[ACTOR_IDS[0]].x - actors[ACTOR_IDS[1]].x) < 25:
        raise RuntimeError("R06 camera handoff requires separately visible Actor X positions")
    return {
        "native_two_actor_camera_handoff_authored": True,
        "handoff_while_both_walk_commands_active": True,
        "camera_actor_sequence": list(ACTOR_IDS),
        "four_zplanes_assigned": True,
        "native_visual_handoff_verified": False,
        "complete_r06_270_acceptance": False,
    }



def verify_native_camera_focus_handoff(traces: dict, camera_frames: list[dict]) -> dict:
    """Require visual hand-off from Actor A to B while both still walk.

    Genuine pixel-tracked actor screen coordinates are compared to the stock
    ScummVM viewport centre, never to authored camera target metadata.
    """
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Native R06 camera handoff requires two Actor tracks")
    by_actor = {
        actor: {row["frame"]: row for row in traces[actor]}
        for actor in ACTOR_IDS
    }
    camera_by_frame = {row["frame"]: row for row in camera_frames}
    common = sorted(
        set(by_actor[ACTOR_IDS[0]]) & set(by_actor[ACTOR_IDS[1]])
        & set(camera_by_frame),
        key=lambda frame: camera_by_frame[frame]["seconds"],
    )
    moving = []
    previous = None
    for frame in common:
        a = by_actor[ACTOR_IDS[0]][frame]
        b = by_actor[ACTOR_IDS[1]][frame]
        camera = camera_by_frame[frame]
        if previous is not None:
            before_a, before_b = previous
            if a["world_x"] - before_a["world_x"] >= 5 and (
                    b["world_x"] - before_b["world_x"] >= 5):
                moving.append({
                    "frame": frame,
                    "seconds": camera["seconds"],
                    "camera_x": camera["camera_x"],
                    "actor_a_screen_x": a["screen_x"],
                    "actor_b_screen_x": b["screen_x"],
                    "a_center_distance": abs(a["screen_x"] - 512),
                    "b_center_distance": abs(b["screen_x"] - 512),
                })
        previous = (a, b)
    if len(moving) < 3:
        raise RuntimeError("R06 camera handoff lacks simultaneous native Actor movement")
    before = next(
        (row for row in moving
         if row["a_center_distance"] + 40 < row["b_center_distance"]),
        None,
    )
    after = next(
        (row for row in moving
         if before is not None and row["seconds"] > before["seconds"]
         and row["b_center_distance"] + 40 < row["a_center_distance"]),
        None,
    )
    if before is None or after is None:
        raise RuntimeError("R06 native camera focus did not visibly switch from Actor A to B")
    return {
        "native_camera_focus_switch_verified": True,
        "handoff_while_both_actors_moving": True,
        "before": before, "after": after,
    }


def run_native_camera_handoff(upstream: Path, output: Path) -> dict:
    """Compile and play all three genuine stock-ScummVM handoff games.

    Motion, mask controls and camera round-trip are measured on screenshot
    pixels. The distinct *focus switch* is not yet visually accepted.
    """
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    result = {
        "project_path": "Studio PNG -> JSON-v1/Story -> ScummC-v6 -> stock ScummVM",
        "variants": {},
        "native_handoff_compiled": False,
        "native_camera_focus_switch_verified": False,
        "complete_r06_270_acceptance": False,
    }
    report_path = output / "native-r06-camera-handoff-report.json"

    def persist():
        report_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        project = author_native_camera_handoff_project(root, variant=variant)
        (build / "project.json").write_text(project, encoding="utf-8")
        document = parse_document(project)
        bindings = assert_native_camera_handoff(document, variant=variant)
        export_document(document, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True)
        result["variants"][variant] = {"native_game_started": True, "bindings": bindings}
        persist()

    transparent = output / "transparent" / "screenshots"
    tracks = track_native_actor_lanes(transparent)
    result["independent_actor_motion"] = verify_two_actor_native_walks(tracks)
    result["native_actor_tracks"] = tracks
    result["camera_roundtrips"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"))
        for variant in ("masked", "transparent", "wrong-box")
    }
    result["native_mask_comparison"] = measure_two_actor_native_mask_comparison(output, tracks)
    result["native_camera_focus_evidence"] = verify_native_camera_focus_handoff(
        tracks, measure_two_actor_native_camera_trace(transparent))
    result["native_camera_focus_switch_verified"] = True
    result["native_handoff_compiled"] = True
    result["complete_r06_270_acceptance"] = True
    persist()
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python -m adventure_studio.scumm_two_actor_camera_handoff_probe "
            "SCUMMC_DIR OUTPUT"
        )
    print(json.dumps(run_native_camera_handoff(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))

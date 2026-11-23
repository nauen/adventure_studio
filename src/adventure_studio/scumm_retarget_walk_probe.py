"""R06 #290: interrupt a native Actor walk with a different destination.

A second native WalkActorStep redirects moving Actor B without WaitActor.
Only genuine stock-ScummVM screenshot world-coordinate reversals pass V.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_camera_resume_probe import (
    author_native_camera_follow_resume, assert_native_camera_follow_resume,
    verify_native_camera_follow_resume,
)
from .scumm_meeting_camera_probe import verify_native_meeting_camera_tour
from .scumm_meeting_release_probe import verify_native_rendezvous_release
from .scumm_opposing_actor_probe import ACTOR_IDS
from .scumm_project import (
    DelayStep, WalkActorStep, canonical_json, parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip, measure_two_actor_native_mask_comparison,
)


def author_native_walk_retarget(output: Path, *, variant: str = "masked") -> str:
    """Redirect B left mid-walk, then to its right-hand home, before following."""
    document = parse_document(author_native_camera_follow_resume(
        output, variant=variant))
    old = document.costumes[-1]
    name = "R06RetargetWalk" + variant.replace("-", "").title() + "Costume"
    document = replace(
        document,
        costumes=(*document.costumes[:-1], replace(old, name=name)),
        actors=tuple(replace(a, costume=name) if a.id in ACTOR_IDS else a
                     for a in document.actors),
    )
    sequences = []
    for s in document.interaction_sequences:
        if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close"):
            # Parent at index 27 begins B's rightward return and follows B
            # at 28. Here B first walks LEFT toward X260, then native SCUMM
            # redirects its still active walk to X545 without WaitActor.
            sequences.append(replace(s, steps=(
                *s.steps[:28],
                WalkActorStep(ACTOR_IDS[1], 260, 135),
                DelayStep(1),
                WalkActorStep(ACTOR_IDS[1], 545, 135),
                *s.steps[29:],
            )))
        else:
            sequences.append(s)
    changed = replace(document, interaction_sequences=tuple(sequences))
    assert_native_walk_retarget(changed, variant=variant)
    return canonical_json(changed)


def assert_native_walk_retarget(document, *, variant: str = "masked") -> dict:
    """Demand two different native destinations and no WaitActor between them."""
    target = [s for s in document.interaction_sequences
              if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(target) != 1:
        raise RuntimeError("Native retarget requires one real interaction")
    steps = target[0].steps
    if (len(steps) != 39 or steps[28:31] != (
            WalkActorStep(ACTOR_IDS[1], 260, 135),
            DelayStep(1),
            WalkActorStep(ACTOR_IDS[1], 545, 135))):
        raise RuntimeError("R06 native B walk retarget must interrupt active movement")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(
            *s.steps[:28],
            WalkActorStep(ACTOR_IDS[1], 545, 135),
            *s.steps[31:],
        )) if s is target[0] else s for s in document.interaction_sequences
    ))
    assert_native_camera_follow_resume(parent, variant=variant)
    return {"native_walk_retarget_authored": True,
            "native_walk_retarget_pixels_verified": False}


def verify_native_walk_retarget(traces: dict, cameras: list[dict]) -> dict:
    """Demand B moves left, reverses, then moves right in actual native frames."""
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("R06 retarget needs two tracked native Actors")
    by_actor = {actor: {row["frame"]: row for row in traces[actor]}
                for actor in ACTOR_IDS}
    camera_by_frame = {row["frame"]: row for row in cameras}
    shared = sorted(set(by_actor[ACTOR_IDS[1]]) & set(camera_by_frame),
                    key=lambda frame: camera_by_frame[frame]["seconds"])
    if len(shared) < 12:
        raise RuntimeError("Too few native screenshot frames for B redirection")
    positions = by_actor[ACTOR_IDS[1]]
    segments = []
    for first, second in zip(shared, shared[1:]):
        delta = positions[second]["world_x"] - positions[first]["world_x"]
        delta_t = camera_by_frame[second]["seconds"] - camera_by_frame[first]["seconds"]
        if 0 < delta_t <= 1.5:
            segments.append({"from": first, "to": second,
                             "seconds": camera_by_frame[second]["seconds"],
                             "delta": delta,
                             "world_x": positions[second]["world_x"]})
    left = [row for row in segments if -55 <= row["delta"] <= -5
            and 270 <= row["world_x"] <= 415]
    if len(left) < 3:
        raise RuntimeError("Native Actor B never visibly took first leftward walk")
    turning = next((
        row for row in left
        if len([r for r in left if r["seconds"] <= row["seconds"]]) >= 3
        and len([r for r in segments if r["seconds"] > row["seconds"]
                 and 5 <= r["delta"] <= 55]) >= 3
    ), None)
    if turning is None:
        raise RuntimeError("Native Actor B never reversed its walk after retarget")
    right = [row for row in segments if row["seconds"] > turning["seconds"]
             and 5 <= row["delta"] <= 55]
    if max(r["world_x"] for r in right) - turning["world_x"] < 90:
        raise RuntimeError("Native retargeted Actor B did not continue 90px to the right")
    return {"native_actor_walk_retarget_verified": True,
            "leftward_frames": left, "retarget_frame": turning,
            "rightward_frames": right}


def run_native_walk_retarget(upstream: Path, output: Path) -> dict:
    """Link and observe three independent stock ScummVM control games."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_290_acceptance": False}
    path = output / "native-r06-retarget-report.json"

    def persist():
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        authored = author_native_walk_retarget(root, variant=variant)
        (build / "project.json").write_text(authored, encoding="utf-8")
        doc = parse_document(authored)
        assert_native_walk_retarget(doc, variant=variant)
        export_document(doc, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True,
                     native_two_actor_capture_frames=300)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    tracks = track_native_actor_lanes(transparent)
    cameras = measure_two_actor_native_camera_trace(transparent)
    report["native_retarget"] = verify_native_walk_retarget(tracks, cameras)
    report["native_camera_follow_resume"] = verify_native_camera_follow_resume(
        tracks, cameras)
    report["native_meeting_camera"] = verify_native_meeting_camera_tour(
        tracks, cameras)
    report["native_meeting_release"] = verify_native_rendezvous_release(tracks)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_mask_controls"] = measure_two_actor_native_mask_comparison(
        output, tracks)
    report["complete_r06_290_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_retarget_walk_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_walk_retarget(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))

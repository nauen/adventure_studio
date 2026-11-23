"""R06 #292: two independently interrupted native Actor walks in opposite directions.

This fixture extends the stock-ScummVM mid-walk retarget example with a
second Actor's own genuine native walk reversal. Scripts alone never pass V.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_retarget_walk_probe import (
    author_native_walk_retarget, assert_native_walk_retarget,
    verify_native_walk_retarget,
)
from .scumm_camera_resume_probe import verify_native_camera_follow_resume
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


def author_native_dual_retarget(output: Path, *, variant: str = "masked") -> str:
    """Change A's active rightward destination to left while B separately reverses."""
    document = parse_document(author_native_walk_retarget(output, variant=variant))
    original = document.costumes[-1]
    name = "R06DualRetarget" + variant.replace("-", "").title() + "Costume"
    document = replace(
        document,
        costumes=(*document.costumes[:-1], replace(original, name=name)),
        actors=tuple(replace(a, costume=name) if a.id in ACTOR_IDS else a
                     for a in document.actors),
    )
    sequences = []
    for sequence in document.interaction_sequences:
        if (sequence.room, sequence.hotspot_id, sequence.verb) == (
                "Harbor", "Key", "Close"):
            # The preceding camera tour ends at index 24. Before B's
            # independently retargeted route, A now receives an active
            # rightward walk then a new leftward target, with no WaitActor.
            steps = sequence.steps
            sequences.append(replace(sequence, steps=(
                *steps[:26],
                WalkActorStep(ACTOR_IDS[0], 530, 85),
                DelayStep(1),
                WalkActorStep(ACTOR_IDS[0], 260, 85),
                *steps[27:],
            )))
        else:
            sequences.append(sequence)
    result = replace(document, interaction_sequences=tuple(sequences))
    assert_native_dual_retarget(result, variant=variant)
    return canonical_json(result)


def assert_native_dual_retarget(document, *, variant: str = "masked") -> dict:
    """Require two separately issued native midwalk target changes, not waits."""
    target = [s for s in document.interaction_sequences
              if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(target) != 1:
        raise RuntimeError("R06 dual retarget requires one native Key interaction")
    steps = target[0].steps
    a_change = (
        WalkActorStep(ACTOR_IDS[0], 530, 85),
        DelayStep(1),
        WalkActorStep(ACTOR_IDS[0], 260, 85),
    )
    b_change = (
        WalkActorStep(ACTOR_IDS[1], 260, 135),
        DelayStep(1),
        WalkActorStep(ACTOR_IDS[1], 545, 135),
    )
    if len(steps) != 41 or steps[26:29] != a_change or steps[30:33] != b_change:
        raise RuntimeError("R06 both native Actors must retarget while moving")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(
            *s.steps[:26], WalkActorStep(ACTOR_IDS[0], 260, 85), *s.steps[29:],
        )) if s is target[0] else s for s in document.interaction_sequences
    ))
    assert_native_walk_retarget(parent, variant=variant)
    return {"dual_native_retargets_authored": True,
            "dual_native_retargets_pixels_verified": False}


def verify_native_dual_retarget(traces: dict, cameras: list[dict]) -> dict:
    """Prove B's own retarget and A's opposite reversal from real visual frames."""
    b_verified = verify_native_walk_retarget(traces, cameras)
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("Two independent visual Actor tracks required")
    camera = {r["frame"]: r for r in cameras}
    a = {r["frame"]: r for r in traces[ACTOR_IDS[0]]}
    shared = sorted(set(a) & set(camera), key=lambda f: camera[f]["seconds"])
    if len(shared) < 14:
        raise RuntimeError("Not enough native Actor A reversal screenshots")
    motions = []
    for before, after in zip(shared, shared[1:]):
        dt = camera[after]["seconds"] - camera[before]["seconds"]
        dx = a[after]["world_x"] - a[before]["world_x"]
        if 0 < dt <= 1.5 and abs(dx) <= 55:
            motions.append({"frame": after, "seconds": camera[after]["seconds"],
                            "dx": dx, "world_x": a[after]["world_x"]})
    # Actor A must leave the rendezvous X395 to the right before it is
    # interrupted and walks home toward X260. Require 3 genuine native
    # motion samples in each direction and >=45px extent before the turn.
    forward = [r for r in motions if 5 <= r["dx"] <= 55
               and 400 <= r["world_x"] <= 550]
    if len(forward) < 3:
        raise RuntimeError("Actor A never visibly started rightward native walk")
    turn = next((r for r in forward
                 if len([q for q in forward if q["seconds"] <= r["seconds"]]) >= 3
                 and len([q for q in motions if q["seconds"] > r["seconds"]
                          and -55 <= q["dx"] <= -5]) >= 3), None)
    if turn is None:
        raise RuntimeError("Actor A never reversed native walk after retarget")
    backward = [r for r in motions if r["seconds"] > turn["seconds"]
                and -55 <= r["dx"] <= -5]
    if turn["world_x"] - min(r["world_x"] for r in backward) < 90:
        raise RuntimeError("Actor A did not complete a measurable leftward return")
    return {"native_dual_actor_retarget_verified": True,
            "actor_a_forward": forward, "actor_a_turn": turn,
            "actor_a_backward": backward, "actor_b_retarget": b_verified}


def run_native_dual_retarget(upstream: Path, output: Path) -> dict:
    """Compile and run masked, transparent and wrong-box stock ScummVM controls."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game
    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_292_acceptance": False}
    path = output / "native-r06-dual-retarget-report.json"

    def persist():
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        authored = author_native_dual_retarget(root, variant=variant)
        (build / "project.json").write_text(authored, encoding="utf-8")
        document = parse_document(authored)
        assert_native_dual_retarget(document, variant=variant)
        export_document(document, resources)
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
    report["native_dual_retarget"] = verify_native_dual_retarget(tracks, cameras)
    report["native_camera_resume"] = verify_native_camera_follow_resume(tracks, cameras)
    report["native_tour"] = verify_native_meeting_camera_tour(tracks, cameras)
    report["native_rendezvous_release"] = verify_native_rendezvous_release(tracks)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["native_mask_controls"] = measure_two_actor_native_mask_comparison(
        output, tracks)
    report["complete_r06_292_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m adventure_studio.scumm_dual_retarget_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_dual_retarget(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))

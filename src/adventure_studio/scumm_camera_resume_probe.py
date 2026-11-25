"""R06 #288: return from scripted camera inspection to native Actor-B follow.

Actual proof is taken from time-stamped stock-ScummVM screenshot frames.
The presence of a FollowActorCameraStep by itself never marks V as passed.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import sys

from .scumm_meeting_camera_probe import (
    author_native_meeting_camera_tour, assert_native_meeting_camera_tour,
    verify_native_meeting_camera_tour,
)
from .scumm_meeting_release_probe import verify_native_rendezvous_release
from .scumm_opposing_actor_probe import ACTOR_IDS
from .scumm_project import (
    FollowActorCameraStep, WalkActorStep, canonical_json,
    parse_document, export_document,
)
from .scumm_two_actor_four_mask_probe import (
    track_native_actor_lanes, measure_two_actor_native_camera_trace,
    verify_two_actor_native_camera_roundtrip,
    measure_two_actor_native_mask_comparison,
)


def author_native_camera_follow_resume(output: Path, *, variant: str = "masked") -> str:
    """Re-acquire B with the native follow opcode directly after B starts walking."""
    document = parse_document(author_native_meeting_camera_tour(
        output, variant=variant))
    costume = document.costumes[-1]
    unique = "R06CameraResume" + variant.replace("-", "").title() + "Costume"
    document = replace(
        document,
        costumes=(*document.costumes[:-1], replace(costume, name=unique)),
        actors=tuple(replace(actor, costume=unique)
                     if actor.id in ACTOR_IDS else actor for actor in document.actors),
    )
    sequences = []
    for sequence in document.interaction_sequences:
        if (sequence.room, sequence.hotspot_id, sequence.verb) == (
                "Harbor", "Key", "Close"):
            # Parent: tour at indices 20..25, A returns at 26,
            # B's return at 28. Native follow starts immediately after B's
            # second WalkActorStep, before either WaitActorStep.
            sequences.append(replace(sequence, steps=(
                *sequence.steps[:29],
                FollowActorCameraStep(ACTOR_IDS[1]),
                *sequence.steps[29:],
            )))
        else:
            sequences.append(sequence)
    result = replace(document, interaction_sequences=tuple(sequences))
    assert_native_camera_follow_resume(result, variant=variant)
    return canonical_json(result)


def assert_native_camera_follow_resume(document, *, variant: str = "masked") -> dict:
    """Reject missing, early or post-wait native camera follow commands."""
    sequences = [s for s in document.interaction_sequences
                 if (s.room, s.hotspot_id, s.verb) == ("Harbor", "Key", "Close")]
    if len(sequences) != 1:
        raise RuntimeError("R06 camera resume requires one native interaction")
    sequence = sequences[0]
    steps = sequence.steps
    if (len(steps) != 37
            or steps[28] != WalkActorStep(ACTOR_IDS[1], 545, 135)
            or steps[29] != FollowActorCameraStep(ACTOR_IDS[1])):
        raise RuntimeError("Native camera follow of walking Actor B must follow its return command")
    parent = replace(document, interaction_sequences=tuple(
        replace(s, steps=(*s.steps[:29], *s.steps[30:]))
        if s is sequence else s for s in document.interaction_sequences
    ))
    assert_native_meeting_camera_tour(parent, variant=variant)
    return {"native_post_pan_follow_authored": True,
            "native_post_pan_follow_pixels_verified": False}


def verify_native_camera_follow_resume(traces: dict, camera_frames: list[dict]) -> dict:
    """Require B world motion and observed camera motion AFTER scripted inspection."""
    if set(traces) != set(ACTOR_IDS):
        raise RuntimeError("R06 native camera reacquisition needs two Actor tracks")
    by_actor = {
        actor: {row["frame"]: row for row in traces[actor]}
        for actor in ACTOR_IDS
    }
    cameras = {row["frame"]: row for row in camera_frames}
    # A can be genuinely occluded while B moves and the camera follows.
    # The earlier two-Actor meeting is checked by verify_native_meeting_camera_tour;
    # camera reacquisition needs timestamp-aligned B costume and camera pixels,
    # not an unrelated simultaneous detection of A.
    shared = sorted(
        set(by_actor[ACTOR_IDS[1]]) & set(cameras),
        key=lambda frame: cameras[frame]["seconds"],
    )
    if len(shared) < 12:
        raise RuntimeError("Too few genuine native camera-reacquisition frames")
    # The manual camera inspection must reach X480 and return near X395
    # BEFORE any following phase can count as reacquisition.
    far = next((i for i, frame in enumerate(shared)
                if cameras[frame]["camera_x"] >= 475), None)
    returned = next((i for i in range(far + 1, len(shared))
                     if abs(cameras[shared[i]]["camera_x"] - 395) <= 12),
                    None) if far is not None else None
    if returned is None:
        raise RuntimeError("No observed native manual-pan roundtrip before Actor follow")
    phase = []
    for first, second in zip(shared[returned:], shared[returned + 1:]):
        b0, b1 = by_actor[ACTOR_IDS[1]][first], by_actor[ACTOR_IDS[1]][second]
        c0, c1 = cameras[first], cameras[second]
        delta = b1["world_x"] - b0["world_x"]
        if (5 <= delta <= 55 and
                0 < c1["seconds"] - c0["seconds"] <= 1.5):
            phase.append({
                "frame": second, "seconds": c1["seconds"],
                "actor_b_world_delta": delta,
                "camera_x": c1["camera_x"],
            })
    if len(phase) < 3:
        raise RuntimeError("Native Actor B did not visibly resume rightward walking")
    camera_positions = [row["camera_x"] for row in phase]
    if max(camera_positions) - min(camera_positions) < 24:
        raise RuntimeError("Native follow camera did not reacquire moving Actor B")
    return {"native_camera_follow_resume_verified": True,
            "camera_range": max(camera_positions) - min(camera_positions),
            "observed_b_walk_frames": phase,
            "manual_tour_return_frame": shared[returned]}


def run_native_camera_follow_resume(upstream: Path, output: Path) -> dict:
    """Build/launch three independent stock-ScummVM native games and check pixels."""
    from .scumm_launch import launch_smoke
    from .scumm_toolchain import compile_story_game

    output.mkdir(parents=True, exist_ok=True)
    report = {"variants": {}, "complete_r06_288_acceptance": False}
    path = output / "native-r06-camera-resume-report.json"

    def persist():
        path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")

    for variant in ("masked", "transparent", "wrong-box"):
        root = output / variant
        build = root / "build"
        resources = build / "resources"
        resources.mkdir(parents=True, exist_ok=True)
        authored = author_native_camera_follow_resume(root, variant=variant)
        (build / "project.json").write_text(authored, encoding="utf-8")
        doc = parse_document(authored)
        assert_native_camera_follow_resume(doc, variant=variant)
        export_document(doc, resources)
        game = compile_story_game(build, upstream, root / "game")
        launch_smoke(game, root / "screenshots", seconds=6,
                     scene_only=True, allow_static_scene=True,
                     native_two_actor_walk_probe=True,
                     native_two_actor_capture_frames=480,
                     native_two_actor_capture_interval=0.02)
        report["variants"][variant] = {"stock_scummvm_started": True}
        persist()

    transparent = output / "transparent" / "screenshots"
    tracks = track_native_actor_lanes(transparent)
    cameras = measure_two_actor_native_camera_trace(transparent)
    # Persist raw aligned measurements even when a later acceptance gate fails.
    report["transparent_actor_tracks"] = tracks
    report["transparent_camera_frames"] = cameras
    persist()
    report["camera_follow_resume"] = verify_native_camera_follow_resume(
        tracks, cameras)
    report["previous_manual_tour"] = verify_native_meeting_camera_tour(
        tracks, cameras)
    persist()
    report["staggered_release"] = verify_native_rendezvous_release(tracks)
    report["native_camera_roundtrip"] = {
        variant: verify_two_actor_native_camera_roundtrip(
            measure_two_actor_native_camera_trace(output / variant / "screenshots"),
            expected_start=400, prepan_direction="either")
        for variant in ("masked", "transparent", "wrong-box")
    }
    report["four_mask_controls"] = measure_two_actor_native_mask_comparison(
        output, tracks)
    report["complete_r06_288_acceptance"] = True
    persist()
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python -m adventure_studio.scumm_camera_resume_probe SCUMMC_DIR OUTPUT")
    print(json.dumps(run_native_camera_follow_resume(
        Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
